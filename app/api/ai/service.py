import hashlib
import os
import time
from typing import List, Optional
from pinecone import Pinecone, ServerlessSpec, PodSpec 
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_pinecone import PineconeVectorStore 
from fastapi import HTTPException, status
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

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
    
    def vectorize_and_store(self, text: str, metadata: dict = {}, sections_data: List[dict] = None) -> dict:
        try:
            hash_id = self.hash_text(text)
            while not self.pc.describe_index(self.index_name).status['ready']:
                print(f"Waiting for index '{self.index_name}' to be ready...")
                time.sleep(1)

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
            
            # Classify text if sections data is provided
            classification_result = None
            print("sections_data: ", sections_data)
            if sections_data:
                classification_result = self.classify_text_with_llm(text, sections_data)
                print(classification_result)
            
            return {
                "message": f"Stored {len(docs)} chunks successfully.",
                "chunks_count": len(docs),
                "hash_id": hash_id,
                "classification": classification_result
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

    def classify_text_with_llm(self, text_to_classify: str, sections_data: List[dict]) -> dict:
        """Classifies text into a section using an LLM based on provided section details."""
        try:
            llm = ChatOpenAI(openai_api_key=self.openai_api_key, model="gpt-4o-mini", temperature=0)

            sections_str = ""
            for i, section in enumerate(sections_data):
                sections_str += f"{i+1}. Section Name: '{section.get('section_name', 'N/A')}'\n"
                sections_str += f"   Description: '{section.get('template_description', section.get('section_name', 'N/A'))}'\n"
                sections_str += f"   Section ID: {section.get('section_id', 'N/A')}\n"

            prompt = (
                f"New Text to Classify: \"{text_to_classify}\"\n\n"
                f"Existing Sections:\n{sections_str}\n"
                "Identify which of the 'Existing Sections' the 'New Text to Classify' best belongs to. "
                "If it doesn't fit any, state 'None'. "
                "Your response must be a JSON object with two fields: 'predicted_section_name' (string) and 'section_id' (integer, or null if 'None'). "
                "Strictly adhere to the section names and IDs provided. If no section matches, set 'predicted_section_name' to 'None' and 'section_id' to null. "
                "Do not include any other text or explanation in your response.\n\n"
            )
            
            messages = [HumanMessage(content=prompt)]
            response = llm.invoke(messages)
            
            # Attempt to parse JSON response from LLM
            import json
            try:
                llm_output = json.loads(response.content)
                predicted_section_name = llm_output.get("predicted_section_name")
                section_id = llm_output.get("section_id")

                # Optional: Add confidence if the LLM model supports it or if we calculate it
                # For now, we'll return fixed 1.0 if a match is found, else 0.0
                confidence_score = 1.0 if predicted_section_name != "None" else 0.0
                
                return {
                    "predicted_section_name": predicted_section_name,
                    "confidence_score": confidence_score,
                    "section_id": section_id
                }
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="LLM response was not valid JSON or could not be parsed."
                )

        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error classifying text with LLM: {str(e)}"
            )

    def summarize_texts_with_llm(self, texts: List[str]) -> str:
        print("texts: ", texts)
        """Summarizes a list of texts using an LLM."""
        try:
            llm = ChatOpenAI(openai_api_key=self.openai_api_key, model="gpt-4o-mini", temperature=0.5)

            combined_text = "\n\n".join(texts)

            prompt = (
                f"Please provide a concise summary of the following texts:\n\n{combined_text}"
            )
            
            messages = [HumanMessage(content=prompt)]
            response = llm.invoke(messages)
            
            return response.content
            
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error summarizing texts with LLM: {str(e)}"
            )


ai_service = None

def get_ai_service():
    global ai_service
    if ai_service is None:
        ai_service = AIService()
    return ai_service