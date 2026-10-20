from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class PlanRequest:
    """What the plan is built from: the answered wish. Tags are "section:tag"."""

    wish_id: UUID
    text: str
    country: str
    city: str | None
    tags: tuple[str, ...]
    persons: int
    start_date: date
    end_date: date
    budget_max: Decimal

    @property
    def trip_days(self) -> int:
        """The first and the last day both count."""
        return (self.end_date - self.start_date).days + 1


@dataclass(frozen=True)
class OfferSummary:
    """A listed offer as planning needs it: no partner and no price."""

    id: UUID
    kind: str
    title: str
    description: str
    tags: tuple[str, ...]
    featured: bool


@dataclass(frozen=True)
class PlanItemView:
    """One day on the plan. available is false when the offer is gone from the catalog."""

    id: UUID
    offer_id: UUID
    day: int
    quantity: int
    note: str | None
    kind: str | None
    title: str | None
    description: str | None
    available: bool


@dataclass(frozen=True)
class PlanView:
    """The plan as the client sees it: never a price (the quote has it), never a partner name."""

    id: UUID
    wish_id: UUID
    status: str
    based_on_preferences: bool
    summary: str
    items: tuple[PlanItemView, ...]
