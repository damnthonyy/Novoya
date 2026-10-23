from collections.abc import Sequence
from typing import Protocol
from uuid import UUID


class PlanStatuses(Protocol):
    async def locked_wish_ids(self, wish_ids: Sequence[UUID]) -> set[UUID]:
        """The wishes among these with a plan requested, negotiating, quoted or accepted:
        the agency works from their answers, so they stay. Proposed and rejected plans do
        not lock."""
        ...
