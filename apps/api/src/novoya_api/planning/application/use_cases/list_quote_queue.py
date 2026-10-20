from novoya_api.planning.application.agent_view import queue_entry_as_view
from novoya_api.planning.application.dto import QueueEntryView
from novoya_api.planning.application.ports.plan_repository import PlanRepository
from novoya_api.planning.application.ports.trip_briefs import TripBriefs
from novoya_api.planning.domain.plan import PlanStatus


class ListQuoteQueue:
    """Plans waiting for a quote, oldest request first, with the wish the client sent."""

    def __init__(self, plans: PlanRepository, trips: TripBriefs) -> None:
        self._plans = plans
        self._trips = trips

    async def __call__(self, status: PlanStatus = PlanStatus.REQUESTED) -> list[QueueEntryView]:
        waiting = await self._plans.list_by_status(status)
        trips = await self._trips.for_wish_ids([plan.wish_id for plan in waiting])
        return [queue_entry_as_view(plan, trips.get(plan.wish_id)) for plan in waiting]
