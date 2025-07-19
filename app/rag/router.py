"""
RAG endpoints for document upload and querying
"""

import os
import uuid
from typing import Annotated, List
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.database import get_session
from app.auth.dependencies import get_current_active_user
from app.auth.models import User
from app.rag.service import rag_service
from app.rag.chunking import document_processor
from app.shared.config import settings

router = APIRouter()

# Ensure upload directory exists
upload_dir = Path(settings.upload_dir)
upload_dir.mkdir(exist_ok=True)


async def process_document_background(file_path: Path, filename: str, user_id: str):
    """
    Background task for document processing.
    
    Single Responsibility: Asynchronous document processing
    """
    try:
        # Process document into chunks
        chunks = await document_processor.process_file(file_path, filename)
        
        # Add metadata
        for chunk in chunks:
            chunk["metadata"]["user_id"] = user_id
        
        # Add to vector store
        success = await rag_service.add_documents_to_knowledge_base(chunks)
        
        if success:
            print(f"Successfully processed {filename} with {len(chunks)} chunks")
        else:
            print(f"Failed to process {filename}")
            
    except Exception as e:
        print(f"Error processing document {filename}: {e}")
    finally:
        # Clean up temporary file
        if file_path.exists():
            file_path.unlink()


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File()],
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """
    Upload and process document for RAG.
    
    Single Responsibility: Document upload handling
    """
    # Validate file type
    allowed_types = {".pdf", ".txt", ".doc", ".docx"}
    file_extension = Path(file.filename).suffix.lower()
    
    if file_extension not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file_extension} not supported. Allowed: {allowed_types}"
        )
    
    # Validate file size
    content = await file.read()
    if len(content) > settings.max_file_size:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed size of {settings.max_file_size} bytes"
        )
    
    # Save file temporarily
    temp_filename = f"{uuid.uuid4()}_{file.filename}"
    temp_path = upload_dir / temp_filename
    
    with open(temp_path, "wb") as temp_file:
        temp_file.write(content)
    
    # Process document in background
    background_tasks.add_task(
        process_document_background,
        temp_path,
        file.filename,
        str(current_user.id)
    )
    
    return {
        "message": f"Document {file.filename} uploaded successfully and is being processed",
        "filename": file.filename,
        "size": len(content)
    }


@router.post("/query")
async def query_documents(
    query: Annotated[str, Form()],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Query documents using RAG.
    
    Single Responsibility: RAG query execution
    """
    try:
        result = await rag_service.query_with_rag(query, k=5)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_knowledge_base_stats(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Get knowledge base statistics.
    
    Single Responsibility: Statistics retrieval
    """
    return rag_service.get_knowledge_base_stats()
