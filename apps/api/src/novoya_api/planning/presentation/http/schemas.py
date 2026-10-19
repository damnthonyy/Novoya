from uuid import UUID

from pydantic import BaseModel

from novoya_api.planning.application.dto import PlanView


class PlanItemResponse(BaseModel):
    id: UUID
    offer_id: UUID
    day: int
    quantity: int
    note: str | None
    kind: str
    title: str
    description: str


class Plan(BaseModel):
    """The plan day by day. No price until it is quoted, and never a partner name."""

    id: UUID
    wish_id: UUID
    status: str
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
