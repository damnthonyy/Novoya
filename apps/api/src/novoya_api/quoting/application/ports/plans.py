from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from novoya_api.quoting.application.dto import QuotedPlan, QuotePlanFacts, QuoteTrip


class PlanQuoting(Protocol):
    async def quote(self, plan_id: UUID, agent_id: UUID) -> QuotedPlan:
        """Marks the plan quoted in the current transaction and returns its priced items.

        Raises when the plan is missing, not the agent's, not negotiating or not fully
        priced; nothing is written then."""
        ...

    async def trip(self, plan_id: UUID) -> QuoteTrip | None:
        """Where and when the plan's trip goes. None when the plan is gone."""
        ...

    async def find_ids(
        self, statuses: Sequence[str], query: str | None, user_ids: Sequence[UUID]
    ) -> list[UUID]:
        """The plans with one of these statuses (any when empty) whose destination contains
        `query`, or whose client is one of `user_ids` (any plan when `query` is None)."""
        ...

    async def facts(self, plan_ids: Sequence[UUID]) -> dict[UUID, QuotePlanFacts]: ...
