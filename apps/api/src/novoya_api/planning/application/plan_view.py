from uuid import UUID

from novoya_api.planning.application.dto import OfferSummary, PlanItemView, PlanView
from novoya_api.planning.domain.plan import Plan


def plan_as_view(plan: Plan, offers: dict[UUID, OfferSummary]) -> PlanView:
    """The plan as the client sees it: no price, no partner, no removed items."""
    items: list[PlanItemView] = []
    for item in plan.items:
        if item.removed:
            continue
        offer = offers.get(item.offer_id)
        if offer is None:
            continue
        items.append(
            PlanItemView(
                id=item.id,
                offer_id=item.offer_id,
                day=item.day,
                quantity=item.quantity,
                note=item.note,
                kind=offer.kind,
                title=offer.title,
                description=offer.description,
            )
        )
    return PlanView(
        id=plan.id,
        wish_id=plan.wish_id,
        status=plan.status.value,
        based_on_preferences=plan.based_on_preferences,
        summary=plan.summary,
        items=tuple(items),
    )
