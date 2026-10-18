"""Composition root of the wishes module: plugs the adapters into the use cases.

In each module, this file is the only place outside infrastructure that may import
infrastructure. Tests replace these dependencies with fakes.
"""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from novoya_api.shared.infrastructure.db.session import get_session
from novoya_api.shared.infrastructure.llm.client import get_orchestrator
from novoya_api.shared.infrastructure.llm.errors import LLMError
from novoya_api.wishes.application.ports.destination_reader import DestinationReader
from novoya_api.wishes.application.use_cases.send_wish import SendWish
from novoya_api.wishes.infrastructure.catalog import StaticCatalog
from novoya_api.wishes.infrastructure.db.repository import SqlUnitOfWork, SqlWishRepository
from novoya_api.wishes.infrastructure.llm.destination_reader import (
    LlmDestinationReader,
    NameMatchingReader,
)


def get_current_user_id() -> UUID:
    """The signed-in client. Until sign-in lands (#63) nobody is signed in; it then becomes
    accounts.public.require_client."""
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "sign in first")


def get_destination_reader() -> DestinationReader:
    try:
        # Short: the client waits for this answer, and name matching is the fallback.
        return LlmDestinationReader(get_orchestrator(deadline_seconds=20))
    except LLMError:
        return NameMatchingReader()  # no API key: the app still works


def get_send_wish(
    session: Annotated[AsyncSession, Depends(get_session)],
    reader: Annotated[DestinationReader, Depends(get_destination_reader)],
) -> SendWish:
    return SendWish(
        wishes=SqlWishRepository(session),
        catalog=StaticCatalog(),
        reader=reader,
        uow=SqlUnitOfWork(session),
        now=lambda: datetime.now(UTC),
    )
