"""
Pytest configuration and fixtures for testing
Reference: https://fastapi.tiangolo.com/tutorial/testing/
"""

import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.main import app
from app.shared.database import get_session
from app.shared.config import settings

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop():
    """
    Create an instance of the default event loop for the test session.
    
    Single Responsibility: Test event loop management
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """
    Create test database engine.
    
    Single Responsibility: Test database engine creation
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False}
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create test database session.
    
    Single Responsibility: Test session creation
    """
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session


@pytest.fixture
async def client(test_session) -> AsyncGenerator[AsyncClient, None]:
    """
    Create test HTTP client.
    
    Single Responsibility: Test client creation
    """
    async def override_get_session():
        yield test_session
    
    app.dependency_overrides[get_session] = override_get_session
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
async def authenticated_client(client, test_session):
    """
    Create authenticated test client.
    
    Single Responsibility: Authenticated client creation
    """
    from app.auth.service import auth_service
    from app.auth.models import User
    
    # Create test user
    test_user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password=auth_service.get_password_hash("testpassword")
    )
    
    test_session.add(test_user)
    await test_session.commit()
    await test_session.refresh(test_user)
    
    # Create token
    token = auth_service.create_access_token(data={"sub": test_user.username})
    
    # Set authorization header
    client.headers["Authorization"] = f"Bearer {token}"
    
    return client
