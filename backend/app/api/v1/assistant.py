from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models import User
from app.schemas import AssistantChatRequest, AssistantChatResponse
from app.services.assistant import answer_assistant_query
from app.api.deps import get_current_user

router = APIRouter(prefix="/assistant", tags=["Assistant"])

@router.post("/chat", response_model=AssistantChatResponse)
async def chat_with_assistant(
    payload: AssistantChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    history_dicts = [{"role": m.role, "content": m.content} for m in (payload.history or [])]
    result = await answer_assistant_query(
        db=db,
        user_id=current_user.id,
        user_query=payload.message,
        chat_history=history_dicts
    )
    return result
