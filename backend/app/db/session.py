"""Async SQLAlchemy engine, session factory, and declarative base.

Provides the core database infrastructure for Supabase PostgreSQL.
All ORM models inherit from ``Base``.  FastAPI routes obtain a session
via the ``get_db_session`` dependency.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# -- Async engine bound to the configured DATABASE_URL --
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)

# -- Session factory --
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session.

    Usage::

        @router.get("/example")
        async def example(db: AsyncSession = Depends(get_db_session)):
            ...
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
