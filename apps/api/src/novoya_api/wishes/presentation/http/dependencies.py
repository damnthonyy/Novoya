"""Composition root of the wishes module: plugs the adapters into the use cases.

In each module, this file is the only place outside infrastructure that may import
infrastructure. Tests replace these dependencies with fakes.
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from novoya_api.accounts.public import CurrentUserView, require_client
from novoya_api.shared.infrastructure.db.session import get_session
from novoya_api.shared.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from novoya_api.shared.infrastructure.llm.client import get_orchestrator
from novoya_api.shared.infrastructure.llm.errors import LLMError
from novoya_api.shared.infrastructure.system_clock import SystemClock
from novoya_api.wishes.application.ports.destination_reader import DestinationReader
from novoya_api.wishes.application.use_cases.answer_panel import AnswerPanel
from novoya_api.wishes.application.use_cases.send_wish import SendWish
from novoya_api.wishes.infrastructure.catalog import StaticCatalog
from novoya_api.wishes.infrastructure.db.repository import SqlWishRepository
from novoya_api.wishes.infrastructure.llm.destination_reader import (
    LlmDestinationReader,
    NameMatchingReader,
)


def get_current_user_id(user: Annotated[CurrentUserView, Depends(require_client)]) -> UUID:
    """The signed-in client: 401 without a session, 403 for an agent (the admin passes)."""
    return user.user_id.value


def get_destination_reader() -> DestinationReader:
    try:
        # Short: the client waits for this answer, and name matching is the fallback. The
        # reader's deadline covers the answer and its retry.
        return LlmDestinationReader(get_orchestrator(deadline_seconds=20), deadline_seconds=20)
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
        uow=SqlAlchemyUnitOfWork(session),
        clock=SystemClock(),
    )


def get_answer_panel(session: Annotated[AsyncSession, Depends(get_session)]) -> AnswerPanel:
    return AnswerPanel(
        wishes=SqlWishRepository(session),
        uow=SqlAlchemyUnitOfWork(session),
        clock=SystemClock(),
    )
