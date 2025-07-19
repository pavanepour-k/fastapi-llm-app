"""
Chat HTTP endpoints for session management
Reference: https://fastapi.tiangolo.com/tutorial/bigger-applications/
"""

from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.shared.database import get_session
from app.auth.dependencies import get_current_active_user
from app.auth.models import User
from app.chat.schemas import ChatSessionCreate, ChatSessionResponse
from app.chat.models import ChatSession, ChatMessage

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_chat_sessions(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """
    Get user's chat sessions.
    
    Single Responsibility: Chat session listing
    """
    statement = select(ChatSession).where(
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.updated_at.desc())
    
    result = await session.execute(statement)
    sessions = result.scalars().all()
    
    return [ChatSessionResponse.model_validate(s) for s in sessions]


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    session_create: ChatSessionCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """
    Create new chat session.
    
    Single Responsibility: Chat session creation
    """
    chat_session = ChatSession(
        title=session_create.title,
        user_id=current_user.id
    )
    
    session.add(chat_session)
    await session.commit()
    await session.refresh(chat_session)
    
    return ChatSessionResponse.model_validate(chat_session)


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """
    Get messages for a chat session.
    
    Single Responsibility: Message history retrieval
    """
    statement = select(ChatMessage).join(ChatSession).where(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).order_by(ChatMessage.created_at)
    
    result = await session.execute(statement)
    messages = result.scalars().all()
    
    return [{"id": str(m.id), "content": m.content, "is_user": m.is_user, "created_at": m.created_at} for m in messages]

