from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# ── Lazy engine — only created when first DB call happens.
# This lets the server start cleanly even when asyncpg / psycopg2 wheels
# are unavailable (e.g. Python 3.14 before binary wheels are published).
# All template, ML, chat, and risk evaluation routes work without a
# live PostgreSQL connection.

_engine: Optional[object] = None
_AsyncSessionLocal: Optional[object] = None


def _get_engine():
    global _engine
    if _engine is None:
        from sqlalchemy.ext.asyncio import create_async_engine
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=(settings.APP_ENV == "development"),
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
    return _engine


def _get_session_factory():
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
        _AsyncSessionLocal = async_sessionmaker(
            bind=_get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _AsyncSessionLocal


class Base(DeclarativeBase):
    """All SQLAlchemy models inherit from this."""
    pass


async def get_db():  # type: ignore[return]
    factory = _get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
