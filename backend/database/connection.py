"""
Database connection utilities for Situated Learning System
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine
import os
from typing import AsyncGenerator

# Create the declarative base
Base = declarative_base()

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:password1234@localhost:5432/situated_learning_db")

# Convert to async URL for async operations
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Create async engine
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create sync engine for migrations
sync_engine = create_engine(
    DATABASE_URL,
    echo=False,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Create sync session factory
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    expire_on_commit=False,
)

# Alias for compatibility
SessionLocal = SyncSessionLocal

class Database:
    """Database connection manager"""
    
    def __init__(self):
        self.engine = async_engine
        self.session_factory = AsyncSessionLocal
    
    async def connect(self):
        """Initialize database connection"""
        # Connection is already established via global engine
        print("Database engine initialized")
    
    async def disconnect(self):
        """Close database connection"""
        if self.engine:
            await self.engine.dispose()
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session"""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

# Global database instance
database = Database()

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def get_sync_db():
    """Get sync database session for migrations"""
    db = SyncSessionLocal()
    try:
        return db
    finally:
        db.close()

async def init_db():
    """Initialize database tables"""
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Database initialization failed: {e}")
        raise

def init_sync_db():
    """Initialize database tables (sync version for migrations)"""
    Base.metadata.create_all(bind=sync_engine)
