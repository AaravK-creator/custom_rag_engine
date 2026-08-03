from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatRequest, ChatResponse, ChatHistoryResponse
from app.services.rag_pipeline import answer_query
from app.services import chat_history

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        result = answer_query(request.query, request.session_id)
    except RuntimeError as e:
        # e.g. Ollama not running
        raise HTTPException(status_code=503, detail=str(e))

    return ChatResponse(**result)


@router.get("/chat/history/{session_id}", response_model=ChatHistoryResponse)
async def get_history(session_id: str):
    history = chat_history.get_session_history(session_id)
    return ChatHistoryResponse(session_id=session_id, history=history)
