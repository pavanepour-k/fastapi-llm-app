"""
Pydantic models for request/response validation
Reference: https://docs.pydantic.dev/latest/
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import uuid


class UserCreate(BaseModel):
    """
    Schema for user creation requests.
    
    Single Responsibility: User creation data validation
    """
    
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(max_length=100)
    password: str = Field(min_length=8)


class UserResponse(BaseModel):
    """
    Schema for user data responses (excludes sensitive data).
    
    Single Responsibility: Safe user data serialization
    """
    
    id: uuid.UUID
    username: str
    email: str
    full_name: str
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    """
    Schema for authentication token responses.
    
    Single Responsibility: Token data structure
    """
    
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """
    Schema for token payload data.
    
    Single Responsibility: Token payload validation
    """
    
    username: Optional[str] = None


class ChatMessageCreate(BaseModel):
    """
    Schema for creating new chat messages.
    
    Single Responsibility: Message creation validation
    """
    
    content: str = Field(min_length=1, max_length=4000)


class ChatMessageResponse(BaseModel):
    """
    Schema for chat message responses.
    
    Single Responsibility: Message data serialization
    """
    
    id: uuid.UUID
    content: str
    is_user: bool
    created_at: datetime
