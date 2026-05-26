import io
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.models.schemas import ChatRequest
from app.services.rag_service import grounded_chat, get_chat_history

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
def chat(request: ChatRequest):
    result = grounded_chat(
        notebook_id=request.notebook_id,
        message=request.message,
        source_ids=request.source_ids or None,
        model_key=request.model_key,
    )
    return result


@router.get("/history/{notebook_id}")
def chat_history(notebook_id: int):
    return get_chat_history(notebook_id)
