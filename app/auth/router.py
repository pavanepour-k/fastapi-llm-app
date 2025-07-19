"""
Authentication endpoints following FastAPI OAuth2 patterns
Reference: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
"""

from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.database import get_session
from app.auth.service import auth_service
from app.auth.schemas import UserCreate, UserResponse, Token
from app.auth.dependencies import get_current_active_user
from app.auth.models import User
from app.shared.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """
    OAuth2 token endpoint for user authentication.
    
    Single Responsibility: User login and token generation
    """
    user = await auth_service.authenticate_user(
        session, form_data.username, form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = auth_service.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_create: UserCreate,
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """
    User registration endpoint.
    
    Single Responsibility: New user account creation
    """
    # Check if user already exists
    existing_user = await auth_service.get_user_by_username(
        session, user_create.username
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    user = await auth_service.create_user(session, user_create)
    return UserResponse.model_validate(user)


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Get current user information.
    
    Single Responsibility: Current user data retrieval
    """
    return UserResponse.model_validate(current_user)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    Serve login page.
    
    Single Responsibility: Login form rendering
    """
    return templates.TemplateResponse("auth/login.html", {"request": request})
