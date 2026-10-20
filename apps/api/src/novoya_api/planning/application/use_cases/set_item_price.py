from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from novoya_api.planning.application.agent_view import agent_plan_as_view
from novoya_api.planning.application.dto import AgentPlanView
from novoya_api.planning.application.ports.offer_catalog import OfferCatalog
from novoya_api.planning.application.ports.plan_repository import PlanRepository
from novoya_api.planning.application.ports.trip_briefs import TripBriefs
from novoya_api.planning.domain.errors import InvalidPlan, PlanNotFound
from novoya_api.shared.application.clock import Clock
from novoya_api.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class SetItemCommand:
    plan_id: UUID
    item_id: UUID
    agent_id: UUID
    negotiated_price: Decimal | None
    removed: bool | None


class SetItemPrice:
    """The assigned agent sets a negotiated price, drops an item, or puts it back."""

    def __init__(
        self,
        plans: PlanRepository,
        catalog: OfferCatalog,
        trips: TripBriefs,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._plans = plans
        self._catalog = catalog
        self._trips = trips
        self._uow = uow
        self._clock = clock

    async def __call__(self, cmd: SetItemCommand) -> AgentPlanView:
        plan = await self._plans.get(cmd.plan_id)
        if plan is None:
            raise PlanNotFound("no such plan")
        now = self._clock.now()
        if cmd.negotiated_price is not None and cmd.removed is not None:
            raise InvalidPlan("set a price or set removed, not both")
        if cmd.removed is True:
            plan.remove_item(cmd.item_id, cmd.agent_id, now)
        elif cmd.removed is False:
            plan.restore_item(cmd.item_id, cmd.agent_id, now)
        elif cmd.negotiated_price is None:
            raise InvalidPlan("set a price or set removed, not both")
        else:
            plan.set_item_price(cmd.item_id, cmd.agent_id, cmd.negotiated_price, now)
        await self._plans.save_item(plan, cmd.item_id)
        fresh = await self._plans.get(cmd.plan_id)
        if fresh is None:
            raise PlanNotFound("no such plan")
        offer_ids = [item.offer_id for item in fresh.items]
        offers = {offer.id: offer for offer in await self._catalog.contacts_for(offer_ids)}
        briefs = await self._trips.for_wish_ids([fresh.wish_id])
        view = agent_plan_as_view(fresh, offers, briefs.get(fresh.wish_id))
        await self._uow.commit()
        return view
