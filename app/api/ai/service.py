import hashlib
import os
from typing import List, Optional
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from fastapi import HTTPException, status


class AIService:
    def __init__(self):
        # Initialize Pinecone
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.pinecone_env = os.getenv("PINECONE_ENV", "us-west1-gcp")
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "text-chunks")
        
        if not self.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY environment variable is required")
        
        # Initialize Pinecone
        pinecone.init(api_key=self.pinecone_api_key, environment=self.pinecone_env)
        
        # Create index if not exists
        if self.index_name not in pinecone.list_indexes():
            pinecone.create_index(name=self.index_name, dimension=1536, metric="cosine")
        
        # Initialize components
        self.embedding_model = OpenAIEmbeddings()
        self.vectordb = Pinecone.from_existing_index(
            index_name=self.index_name,
            embedding=self.embedding_model
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100
        )
    
    def hash_text(self, text: str) -> str:
        """Generate MD5 hash for text to identify duplicates."""
        return hashlib.md5(text.encode()).hexdigest()
    
    def vectorize_and_store(self, text: str, metadata: dict = {}) -> dict:
        """Vectorize text and store in Pinecone."""
        try:
            # Split text into chunks
            chunks = self.text_splitter.split_text(text)
            hash_id = self.hash_text(text)
            
            # Check for duplicates
            existing = self.vectordb.similarity_search(text, k=1)
            if existing and existing[0].page_content == text:
                return {
                    "message": "Text already exists, skipping.",
                    "chunks_count": 0,
                    "hash_id": hash_id
                }
            
            # Prepare documents
            docs = [
                Document(
                    page_content=chunk,
                    metadata={**metadata, "chunk_index": idx, "hash_id": hash_id}
                )
                for idx, chunk in enumerate(chunks)
            ]
            
            # Add to vector database
            self.vectordb.add_documents(docs)
            
            return {
                "message": f"Stored {len(docs)} chunks successfully.",
                "chunks_count": len(docs),
                "hash_id": hash_id
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error vectorizing text: {str(e)}"
            )
    
    def query_text(self, query: str, k: int = 3) -> List[dict]:
        """Query the vector database for similar texts."""
        try:
            results = self.vectordb.similarity_search_with_score(query, k=k)
            
            return [
                {
                    "text": result[0].page_content,
                    "metadata": result[0].metadata,
                    "score": result[1]
                }
                for result in results
            ]
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error querying text: {str(e)}"
            )

# Global service instance - will be initialized when first accessed
ai_service = None

def get_ai_service():
    """Get or create the AI service instance."""
    global ai_service
    if ai_service is None:
        ai_service = AIService()
    return ai_service 