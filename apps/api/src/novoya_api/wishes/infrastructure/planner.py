from dataclasses import asdict

from sqlalchemy.ext.asyncio import AsyncSession

from novoya_api.planning.public import PlanRequest, generate_plan
from novoya_api.wishes.application.ports.planner import ProposedItem, ProposedPlan
from novoya_api.wishes.domain.wish import Wish


class PartnerPlanner:
    """Planner through planning.public, in the request's session, so the plan and the
    planned wish are committed together."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def propose(self, wish: Wish) -> ProposedPlan:
        assert wish.destination is not None and wish.answers is not None  # answered
        answers = wish.answers
        request = PlanRequest(
            wish_id=wish.id,
            text=wish.text,
            country=wish.destination.country,
            city=wish.destination.city,
            tags=tuple(f"{t.section}:{t.tag}" for t in answers.selected_tags),
            persons=answers.persons,
            start_date=answers.start_date,
            end_date=answers.end_date,
            budget_max=answers.budget_max,
        )
        plan = await generate_plan(request, session=self._session)
        return ProposedPlan(
            id=plan.id,
            wish_id=plan.wish_id,
            status=plan.status,
            based_on_preferences=plan.based_on_preferences,
            summary=plan.summary,
            items=tuple(ProposedItem(**asdict(item)) for item in plan.items),
        )
