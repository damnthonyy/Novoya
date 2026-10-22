"""What other modules may use from quoting. Nothing else in quoting may be imported.

- delete_for_user(user_id): erases the quotes sent to this client, with their PDF. Call it
  before planning.public.delete_for_user: a quote points to its plan. The caller commits.
- quotes_for_plans(plan_ids) -> {plan id: quote id}: the quote of each of these plans, for
  the client's list of trips. Plans not quoted yet are left out.
"""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from novoya_api.quoting.infrastructure.db.repository import SqlQuoteRepository

__all__ = ["delete_for_user", "quotes_for_plans"]


async def delete_for_user(user_id: UUID, *, session: AsyncSession) -> None:
    """Erase the quotes of this client, PDFs included. The caller commits."""
    await SqlQuoteRepository(session).delete_for_client(user_id)


async def quotes_for_plans(plan_ids: Sequence[UUID], *, session: AsyncSession) -> dict[UUID, UUID]:
    """The id of the quote of each of these plans, keyed by plan id. Unquoted plans are left out."""
    return await SqlQuoteRepository(session).ids_for_plans(plan_ids)
