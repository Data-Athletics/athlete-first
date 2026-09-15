from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any, ClassVar

from sqlalchemy import URL, DateTime, Integer, NullPool, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.config import app_settings, db_settings

# ----------------------------------------
# PostgreSQL Singleton
# ----------------------------------------


class PostgresClient:
    """
    Singleton containing the database client connection.
    Ensures there is only one connection at a time.
    """

    # Different instances of the connection
    _instances: ClassVar[dict[URL, "PostgresClient"]] = {}

    # Common database engine instance
    db_engine: AsyncEngine

    # Database session factory instance
    session_factory: async_sessionmaker[AsyncSession]

    def __new__(cls, db_uri: URL = db_settings.url) -> "PostgresClient":
        """
        Override __new__ to implement the Singletone pattern.
        Returns the existing instance if it exists, otherwise creates a new one.
        """

        if db_uri not in cls._instances:
            # Create a new instance if one doesn't exist yet
            instance = super().__new__(cls)

            extra_engine_kwargs = {}
            if app_settings.env == "dev":
                # Improves concurrency errors in test mode
                extra_engine_kwargs["poolclass"] = NullPool

            # Create the database engine
            instance.db_engine = create_async_engine(
                db_uri, echo=db_settings.echo, **extra_engine_kwargs
            )

            # Create the session factory
            factory_kwargs = {
                "autocommit": False,
                "autoflush": False,
                "expire_on_commit": False,
                "bind": instance.db_engine,
            }
            instance.session_factory = async_sessionmaker(
                **factory_kwargs,
                class_=AsyncSession,
            )

            # Add the client to the dictionary of instances
            cls._instances[db_uri] = instance

        return cls._instances[db_uri]


# ----------------------------------------
# Database Utilities
# ----------------------------------------


def get_engine() -> AsyncEngine:
    """
    Returns the database engine instance for a given database name.
    """
    return PostgresClient(db_settings.url).db_engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Returns the database session factory instance for a given database name.
    """
    return PostgresClient(db_settings.url).session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides an async generator that yields a database session and ensures
    its proper closer after usage.
    """

    async with get_session_factory()() as db_session:
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise
        finally:
            await db_session.close()


class ModelBase(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    type_annotation_map = {dict[str, Any]: JSONB}

    # Default fields
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )
