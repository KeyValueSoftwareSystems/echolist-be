import hashlib
import os
import time
from typing import List, Optional
from pinecone import Pinecone, ServerlessSpec, PodSpec 
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_pinecone import PineconeVectorStore 
from fastapi import HTTPException, status
from dotenv import load_dotenv

load_dotenv()

class AIService:
    def __init__(self):
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.pinecone_env = os.getenv("PINECONE_ENV")
        self.index_name = os.getenv("PINECONE_INDEX_NAME")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        if not self.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY environment variable is required")
        if not self.index_name:
             raise ValueError("PINECONE_INDEX_NAME environment variable is required")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required for OpenAI embeddings")
        
        self.pc = Pinecone(api_key=self.pinecone_api_key)
        
        # if self.index_name not in self.pc.list_indexes():
        #     print(f"Creating Pinecone index: {self.index_name}...")
        #     self.pc.create_index(name=self.index_name, dimension=1536, metric="cosine", spec=ServerlessSpec(cloud="aws", region="us-east-1"))
        #     print(f"Pinecone index '{self.index_name}' created.")
        # else:
        #     print(f"Pinecone index '{self.index_name}' already exists.")
            
        self.embedding_model = OpenAIEmbeddings(openai_api_key=self.openai_api_key, model="text-embedding-3-small")
        
        self.vectordb = PineconeVectorStore(
            index_name=self.index_name,
            embedding=self.embedding_model,
            pinecone_api_key=self.pinecone_api_key, 
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100
        )
    
    def hash_text(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()
    
    def vectorize_and_store(self, text: str, metadata: dict = {}) -> dict:
        try:
            hash_id = self.hash_text(text)
            
            while not self.pc.describe_index(self.index_name).status['ready']:
                print(f"Waiting for index '{self.index_name}' to bAe ready...")
                time.sleep(1)

            index = self.pc.Index(self.index_name)
            
            query_results = index.query(
                vector=[0.0] * 1536,
                top_k=1,
                filter={"original_hash_id": {"$eq": hash_id}},
                include_metadata=False
            )
            
            if query_results and query_results.matches:
                return {
                    "message": "Original text already exists (based on hash), skipping.",
                    "chunks_count": 0,
                    "hash_id": hash_id
                }

            chunks = self.text_splitter.split_text(text)
            
            docs = [
                Document(
                    page_content=chunk,
                    metadata={
                        **metadata,
                        "chunk_index": idx,
                        "original_hash_id": hash_id
                    }
                )
                for idx, chunk in enumerate(chunks)
            ]
            self.vectordb.add_documents(docs)
            
            return {
                "message": f"Stored {len(docs)} chunks successfully.",
                "chunks_count": len(docs),
                "hash_id": hash_id
            }
            
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error vectorizing text: {str(e)}"
            )
    
    def query_text(self, query: str, k: int = 3) -> List[dict]:
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
            
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error querying text: {str(e)}"
            )

ai_service = None

def get_ai_service():
    global ai_service
    if ai_service is None:
        ai_service = AIService()
    return ai_service