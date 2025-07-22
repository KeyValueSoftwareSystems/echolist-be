from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from typing import List, Optional
from sqlalchemy.orm import Session

from app.schemas.schemas import TextPayload, VectorizeResponse, QueryResponse, QueryResult
from app.api.ai.service import get_ai_service
from app.core.security import get_current_active_user
from app.models.models import User, Section
from app.db.database import get_db

router = APIRouter(
    prefix="/ai",
    tags=["ai"],
    responses={404: {"description": "Not found"}},
)

@router.post("/vectorize", response_model=VectorizeResponse)
def vectorize_and_store(
    payload: TextPayload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Vectorize text and store in Pinecone vector database, with optional section classification."""
    try:
        # Add user context to metadata
        print('current_user: ', current_user)
        metadata = {
            **payload.metadata,
            "user_id": current_user.user_id,
            "username": current_user.username
        }
        
        # Fetch all sections for the current user for classification
        sections = db.query(Section).filter(
            Section.owner_user_id == current_user.user_id
        ).all()

        sections_data = None
        if sections:
            sections_data = [
                {
                    "section_id": section.section_id,
                    "section_name": section.section_name,
                    "template_description": section.template_description
                }
                for section in sections
            ]
        
        ai_service = get_ai_service()
        result = ai_service.vectorize_and_store(payload.text, metadata, sections_data)
        return VectorizeResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to vectorize text: {str(e)}"
        )

@router.post("/ask/text", response_model=QueryResponse)
def query_text(
    q: str = Query(..., description="Query text to search for"),
    k: int = Query(3, description="Number of results to return", ge=1, le=10),
    current_user: User = Depends(get_current_active_user)
):
    """Query the vector database for similar texts."""
    try:
        ai_service = get_ai_service()
        results = ai_service.query_text(q, k)
        
        # Convert to QueryResult objects
        query_results = [
            QueryResult(
                text=result["text"],
                metadata=result["metadata"],
                score=result["score"]
            )
            for result in results
        ]
        # print("query_results: ", query_results)
        results_response = QueryResponse(results=query_results, query=q)
        print("results: ", results_response)
        summary = ai_service.summarize_texts_with_llm([result.text for result in query_results])
        results_response.summary = summary
        return results_response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query text: {str(e)}"
        )

@router.post("/ask/voice", response_model=QueryResponse)
async def query_voice(
    audio_file: UploadFile = File(...),
    k: int = Query(3, description="Number of results to return", ge=1, le=10),
    current_user: User = Depends(get_current_active_user)
):
    """Convert voice to text and query the vector database for similar texts."""
    try:
        from app.services.audio_service import transcribe_audio
        
        # Read the audio file content
        audio_content = await audio_file.read()
        
        # Transcribe the audio to text
        try:
            transcribed_text = transcribe_audio(audio_content)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to transcribe audio: {str(e)}"
            )
        
        # Query the vector database with the transcribed text
        ai_service = get_ai_service()
        results = ai_service.query_text(transcribed_text, k)
        
        # Convert to QueryResult objects
        query_results = [
            QueryResult(
                text=result["text"],
                metadata=result["metadata"],
                score=result["score"]
            )
            for result in results
        ]
        
        return QueryResponse(results=query_results, query=transcribed_text)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process voice query: {str(e)}"
        )

@router.get("/health")
def health_check():
    """Health check endpoint for AI service."""
    return {"status": "healthy", "service": "ai"} 