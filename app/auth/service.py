"""
Authentication business logic using JWT tokens
Reference: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from passlib.context import CryptContext
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.schemas import UserCreate, TokenData
from app.shared.config import settings


class AuthService:
    """
    Authentication service handling user operations and JWT tokens.
    
    Single Responsibility: User authentication and authorization
    """
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain password against its hash.
        
        Single Responsibility: Password verification
        """
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """
        Generate password hash.
        
        Single Responsibility: Password hashing
        """
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """
        Create JWT access token.
        
        Single Responsibility: Token creation
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.access_token_expire_minutes
            )
        
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """
        Verify and decode JWT token.
        
        Single Responsibility: Token verification
        """
        try:
            payload = jwt.decode(
                token, settings.secret_key, algorithms=[settings.algorithm]
            )
            username: str = payload.get("sub")
            if username is None:
                return None
            return TokenData(username=username)
        except jwt.PyJWTError:
            return None
    
    async def get_user_by_username(
        self, session: AsyncSession, username: str
    ) -> Optional[User]:
        """
        Retrieve user by username from database.
        
        Single Responsibility: User retrieval
        """
        statement = select(User).where(User.username == username)
        result = await session.execute(statement)
        return result.scalar_one_or_none()
    
    async def authenticate_user(
        self, session: AsyncSession, username: str, password: str
    ) -> Optional[User]:
        """
        Authenticate user with username and password.
        
        Single Responsibility: User authentication
        """
        user = await self.get_user_by_username(session, username)
        if not user or not self.verify_password(password, user.hashed_password):
            return None
        return user
    
    async def create_user(self, session: AsyncSession, user_create: UserCreate) -> User:
        """
        Create new user account.
        
        Single Responsibility: User creation
        """
        hashed_password = self.get_password_hash(user_create.password)
        user = User(
            username=user_create.username,
            email=user_create.email,
            full_name=user_create.full_name,
            hashed_password=hashed_password,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


# Global auth service instance
auth_service = AuthService()
