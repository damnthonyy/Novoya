from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from novoya_api.catalog.public import OfferKind
from novoya_api.planning.application.dto import AgentPlanView, PlanView, QueueEntryView
from novoya_api.planning.domain.plan import PlanStatus


class PlanItemResponse(BaseModel):
    id: UUID
    offer_id: UUID
    day: int
    quantity: int
    note: str | None
    kind: OfferKind | None
    title: str | None
    description: str | None
    available: bool


class Plan(BaseModel):
    """The plan day by day. Never a price: the quote has it. Never a partner name."""

    id: UUID
    wish_id: UUID
    status: PlanStatus
    based_on_preferences: bool
    summary: str
    items: list[PlanItemResponse]

    @classmethod
    def of(cls, plan: PlanView) -> "Plan":
        return cls(
            id=plan.id,
            wish_id=plan.wish_id,
            status=plan.status,
            based_on_preferences=plan.based_on_preferences,
            summary=plan.summary,
            items=[
                PlanItemResponse.model_validate(item, from_attributes=True) for item in plan.items
            ],
        )


class QueueEntry(BaseModel):
    """A plan waiting for a quote. Wish text, place, dates, travellers and budget. No prices."""

    id: UUID
    wish_id: UUID
    status: PlanStatus
    summary: str
    updated_at: datetime
    wish_text: str
    country: str | None
    city: str | None
    persons: int | None
    start_date: date | None
    end_date: date | None
    budget_max: Decimal | None
    currency: str | None

    @classmethod
    def of(cls, entry: QueueEntryView) -> "QueueEntry":
        return cls.model_validate(entry, from_attributes=True)


class AgentPlanItem(BaseModel):
    """One day for the assigned agent: negotiated price, and the partner to call."""

    id: UUID
    offer_id: UUID
    day: int
    quantity: int
    note: str | None
    kind: OfferKind | None
    title: str | None
    description: str | None
    available: bool
    negotiated_price: Decimal | None
    removed: bool
    partner_name: str | None
    partner_contact_email: str | None
    partner_contact_phone: str | None


class AgentPlan(BaseModel):
    """The plan as the assigned agent sees it. Prices, partners, running total and budget."""

    id: UUID
    wish_id: UUID
    status: PlanStatus
    summary: str
    assigned_agent_id: UUID | None
    items: list[AgentPlanItem]
    total: Decimal
    budget_max: Decimal | None
    currency: str | None
    over_budget: bool
    wish_text: str | None
    country: str | None
    city: str | None
    persons: int | None
    start_date: date | None
    end_date: date | None

    @classmethod
    def of(cls, plan: AgentPlanView) -> "AgentPlan":
        return cls(
            id=plan.id,
            wish_id=plan.wish_id,
            status=plan.status,
            summary=plan.summary,
            assigned_agent_id=plan.assigned_agent_id,
            items=[AgentPlanItem.model_validate(item, from_attributes=True) for item in plan.items],
            total=plan.total,
            budget_max=plan.budget_max,
            currency=plan.currency,
            over_budget=plan.over_budget,
            wish_text=plan.wish_text,
            country=plan.country,
            city=plan.city,
            persons=plan.persons,
            start_date=plan.start_date,
            end_date=plan.end_date,
        )


class SetPlanItemRequest(BaseModel):
    """Set a negotiated price in EUR, or set removed. True drops the item, false puts it back."""

    negotiated_price: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    removed: bool | None = None
