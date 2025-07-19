"""
FastAPI dependencies for authentication
Reference: https://fastapi.tiangolo.com/tutorial/dependencies/
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.shared.database import get_session
from app.auth.service import auth_service
from app.auth.models import User

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)]
) -> User:
    """
    FastAPI dependency to get current authenticated user.
    
    Single Responsibility: Current user retrieval from token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = auth_service.verify_token(token)
    if token_data is None or token_data.username is None:
        raise credentials_exception
    
    user = await auth_service.get_user_by_username(session, token_data.username)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    FastAPI dependency to get current active user.
    
    Single Responsibility: Active user validation
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
