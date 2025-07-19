"""
Async database connection management using SQLModel and SQLAlchemy
Reference: https://sqlmodel.tiangolo.com/tutorial/create-db-and-table/
"""

import contextlib
from typing import AsyncIterator
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import SQLModel
from app.shared.config import settings


class DatabaseSessionManager:
    """
    Manages database connections and sessions with proper lifecycle management.
    
    Single Responsibility: Database session lifecycle management
    Reference: https://fastapi.tiangolo.com/tutorial/sql-databases/
    """
    
    def __init__(self, host: str, engine_kwargs: dict = None):
        if engine_kwargs is None:
            engine_kwargs = {}
            
        self._engine = create_async_engine(host, **engine_kwargs)
        self._sessionmaker = async_sessionmaker(
            autocommit=False,
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,  # Important for async operations
        )

    async def close(self):
        """Close database engine connections."""
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")
        await self._engine.dispose()

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """
        Context manager for database sessions with automatic rollback on errors.
        
        Single Responsibility: Session context management
        """
        if self._sessionmaker is None:
            raise Exception("DatabaseSessionManager is not initialized")
        
        session = self._sessionmaker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def init_db(self):
        """Initialize database tables."""
        async with self._engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)


# Global session manager instance
sessionmanager = DatabaseSessionManager(
    settings.database_url,
    {"echo": settings.debug, "pool_pre_ping": True}
)


async def get_session() -> AsyncSession:
    """
    Dependency for FastAPI to get database sessions.
    
    Single Responsibility: Provide database session to endpoints
    """
    async with sessionmanager.session() as session:
        yield session
