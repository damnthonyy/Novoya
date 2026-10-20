from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from novoya_api.planning.domain.errors import InvalidPlan
from novoya_api.shared.domain.errors import InvalidTransition


class PlanStatus(StrEnum):
    PROPOSED = "proposed"
    REQUESTED = "requested"
    NEGOTIATING = "negotiating"
    QUOTED = "quoted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class DraftItem:
    """An item the model (or the fallback) proposes, not yet checked against the catalog."""

    offer_id: UUID
    day: int
    quantity: int
    note: str | None


@dataclass(frozen=True, slots=True)
class PlanItem:
    """One offer on one day of the trip. No price until an agent negotiates it."""

    id: UUID
    offer_id: UUID
    day: int
    quantity: int
    note: str | None
    negotiated_price: Decimal | None = None
    removed: bool = False


def keep_valid(drafts: Sequence[DraftItem], allowed: set[UUID], trip_days: int) -> list[DraftItem]:
    """The drafts that point to an allowed offer, on a day of the trip, in their order.

    The model chooses the offer ids, so an id it invented or an offer that does not fit the
    group or the dates never reaches the plan."""
    return [
        draft
        for draft in drafts
        if draft.offer_id in allowed and 1 <= draft.day <= trip_days and draft.quantity >= 1
    ]


def tidy(drafts: Sequence[DraftItem], hotels: set[UUID], trip_days: int) -> list[DraftItem]:
    """The valid drafts without repeats, and hotel nights that are each booked once.

    The model repeats itself: an offer is kept once a day, a hotel once in the whole trip. A
    hotel night runs from its day to the next, so the nights are 1 to trip_days - 1. A hotel
    keeps its free nights from its day on, up to the first night another hotel already has,
    and is dropped when its first night is taken: an agent would otherwise quote nights no
    one sleeps."""
    kept: list[DraftItem] = []
    seen: set[tuple[UUID, int | None]] = set()
    booked: set[int] = set()
    for draft in drafts:
        key = (draft.offer_id, None if draft.offer_id in hotels else draft.day)
        if key in seen:
            continue
        seen.add(key)
        if draft.offer_id in hotels:
            nights = 0
            for night in range(draft.day, min(draft.day + draft.quantity, trip_days)):
                if night in booked:
                    break
                nights += 1
            if nights == 0:
                continue
            booked.update(range(draft.day, draft.day + nights))
            draft = replace(draft, quantity=nights)
        kept.append(draft)
    return kept


@dataclass(slots=True)
class Plan:
    """The trip built from partner offers, day by day. It starts proposed, with no price:
    the client asks for a quote, then an agent negotiates each item."""

    id: UUID
    wish_id: UUID
    status: PlanStatus
    based_on_preferences: bool
    summary: str
    items: tuple[PlanItem, ...]
    created_at: datetime
    updated_at: datetime
    assigned_agent_id: UUID | None = None

    @classmethod
    def propose(
        cls,
        wish_id: UUID,
        based_on_preferences: bool,
        summary: str,
        drafts: Sequence[DraftItem],
        trip_days: int,
        now: datetime,
    ) -> "Plan":
        if not drafts:
            raise InvalidPlan("a plan needs at least one item")
        for draft in drafts:
            if not 1 <= draft.day <= trip_days:
                raise InvalidPlan(f"day {draft.day} is outside the {trip_days}-day trip")
            if draft.quantity < 1:
                raise InvalidPlan("the quantity must be at least 1")
        items = tuple(
            PlanItem(uuid4(), draft.offer_id, draft.day, draft.quantity, draft.note)
            for draft in sorted(drafts, key=lambda draft: draft.day)
        )
        return cls(
            uuid4(), wish_id, PlanStatus.PROPOSED, based_on_preferences, summary, items, now, now
        )

    def request_quote(self, now: datetime) -> None:
        """The client asks an agent to price this plan. Only from proposed."""
        if self.status is not PlanStatus.PROPOSED:
            raise InvalidTransition("the plan is not proposed")
        self.status = PlanStatus.REQUESTED
        self.updated_at = now
