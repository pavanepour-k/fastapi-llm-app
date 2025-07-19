"""
Database models using SQLModel for type safety and async support
Reference: https://sqlmodel.tiangolo.com/
"""

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
import uuid


class User(SQLModel, table=True):
    """
    User model with authentication fields.
    
    Single Responsibility: User data representation and database mapping
    """
    
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(index=True, unique=True, min_length=3, max_length=50)
    email: str = Field(index=True, unique=True)
    full_name: str = Field(max_length=100)
    hashed_password: str
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    chat_sessions: List["ChatSession"] = Relationship(back_populates="user")
    documents: List["Document"] = Relationship(back_populates="owner")


class ChatSession(SQLModel, table=True):
    """
    Chat session model for organizing conversations.
    
    Single Responsibility: Chat session data representation
    """
    
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(max_length=200)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Foreign key
    user_id: uuid.UUID = Field(foreign_key="user.id")
    
    # Relationships
    user: User = Relationship(back_populates="chat_sessions")
    messages: List["ChatMessage"] = Relationship(back_populates="session")


class ChatMessage(SQLModel, table=True):
    """
    Individual chat message model.
    
    Single Responsibility: Message data representation
    """
    
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    content: str
    is_user: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Foreign key
    session_id: uuid.UUID = Field(foreign_key="chatsession.id")
    
    # Relationships
    session: ChatSession = Relationship(back_populates="messages")


class Document(SQLModel, table=True):
    """
    Uploaded document model for RAG.
    
    Single Responsibility: Document metadata representation
    """
    
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    filename: str
    content_type: str
    file_size: int
    processed: bool = Field(default=False)
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Foreign key
    owner_id: uuid.UUID = Field(foreign_key="user.id")
    
    # Relationships
    owner: User = Relationship(back_populates="documents")
