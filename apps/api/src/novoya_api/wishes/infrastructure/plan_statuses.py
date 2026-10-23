from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from novoya_api.planning.public import plan_statuses

# The plans the agency works from: their wish's answers stay. A proposed plan is the client's
# alone, and a rejected one is over, so neither holds the tags.
LOCKING = frozenset({"requested", "negotiating", "quoted", "accepted"})


class PlanningPlanStatuses:
    """PlanStatuses through planning.public, in the request's session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def locked_wish_ids(self, wish_ids: Sequence[UUID]) -> set[UUID]:
        found = await plan_statuses(wish_ids, session=self._session)
        return {
            wish_id
            for wish_id, statuses in found.items()
            if any(status in LOCKING for status in statuses)
        }
