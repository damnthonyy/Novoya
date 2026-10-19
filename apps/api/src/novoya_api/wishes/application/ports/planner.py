from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from novoya_api.wishes.domain.wish import Wish


@dataclass(frozen=True)
class ProposedItem:
    id: UUID
    offer_id: UUID
    day: int
    quantity: int
    note: str | None
    kind: str
    title: str
    description: str


@dataclass(frozen=True)
class ProposedPlan:
    """The plan built from an answered wish: no price, no partner name."""

    id: UUID
    wish_id: UUID
    status: str
    based_on_preferences: bool
    summary: str
    items: tuple[ProposedItem, ...]


class Planner(Protocol):
    async def propose(self, wish: Wish) -> ProposedPlan:
        """Build and add the plan of an answered wish; the caller commits. Raises a domain
        error (422) when no offer fits the travellers and dates."""
        ...
