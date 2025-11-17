"""FastAPI Health check and session management routes"""
from fastapi import APIRouter, HTTPException
from models.schemas import HealthResponse, MessageResponse
from config import sessions

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="Legal Document Processor",
        version="3.0.0",
        framework="FastAPI"
    )


@router.delete("/session/{session_id}", response_model=MessageResponse)
async def cancel_session(session_id: str):
    """Cancel and delete a session"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    del sessions[session_id]
    return MessageResponse(
        success=True,
        message="Session cancelled successfully"
    )
