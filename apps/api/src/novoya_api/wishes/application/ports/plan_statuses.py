from collections.abc import Sequence
from typing import Protocol
from uuid import UUID


class PlanStatuses(Protocol):
    async def locked_wish_ids(self, wish_ids: Sequence[UUID]) -> set[UUID]:
        """The wishes among these whose plan has left proposed (requested, negotiating,
        quoted, accepted or rejected): the agency works from their answers, so they stay."""
        ...
