from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from novoya_api.config import get_settings


@lru_cache
def get_engine() -> AsyncEngine:
    # hide_parameters: database errors never print the values (wish texts, emails) in logs.
    return create_async_engine(
        get_settings().database_url, pool_pre_ping=True, hide_parameters=True
    )


@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """One session per request."""
    async with get_sessionmaker()() as session:
        yield session


async def close_db() -> None:
    """Close the pool so a CLI command can leave without 'Event loop is closed'."""
    if get_engine.cache_info().currsize:
        await get_engine().dispose()
    get_engine.cache_clear()
    get_sessionmaker.cache_clear()
