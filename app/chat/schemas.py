"""
Chat-related Pydantic schemas
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class ChatSessionCreate(BaseModel):
    """
    Schema for creating chat sessions.
    
    Single Responsibility: Chat session creation validation
    """
    title: str = Field(min_length=1, max_length=200)


class ChatSessionResponse(BaseModel):
    """
    Schema for chat session responses.
    
    Single Responsibility: Chat session data serialization
    """
    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime


class ChatMessageCreate(BaseModel):
    """
    Schema for creating chat messages.
    
    Single Responsibility: Message creation validation
    """
    content: str = Field(min_length=1, max_length=4000)
    session_id: uuid.UUID


class ChatMessageResponse(BaseModel):
    """
    Schema for chat message responses.
    
    Single Responsibility: Message data serialization
    """
    id: uuid.UUID
    content: str
    is_user: bool
    created_at: datetime
