from uuid import UUID

from novoya_api.planning.application.dto import PlanView
from novoya_api.planning.application.plan_view import plan_as_view
from novoya_api.planning.application.ports.offer_catalog import OfferCatalog
from novoya_api.planning.application.ports.plan_repository import PlanRepository
from novoya_api.planning.application.ports.wish_ownership import WishOwnership
from novoya_api.planning.domain.errors import PlanNotFound
from novoya_api.shared.application.clock import Clock
from novoya_api.shared.application.unit_of_work import UnitOfWork


class RequestQuote:
    """The owner asks for a quote. proposed becomes requested. Anyone else looks like not found."""

    def __init__(
        self,
        plans: PlanRepository,
        catalog: OfferCatalog,
        wishes: WishOwnership,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._plans = plans
        self._catalog = catalog
        self._wishes = wishes
        self._uow = uow
        self._clock = clock

    async def __call__(self, plan_id: UUID, client_id: UUID) -> PlanView:
        plan = await self._plans.get(plan_id)
        if plan is None:
            raise PlanNotFound("no such plan")
        owner_id = await self._wishes.owner_id(plan.wish_id)
        if owner_id is None or owner_id != client_id:
            raise PlanNotFound("no such plan")
        plan.request_quote(self._clock.now())
        await self._plans.save(plan)
        kept_ids = [item.offer_id for item in plan.items if not item.removed]
        offers = {offer.id: offer for offer in await self._catalog.summaries_for(kept_ids)}
        await self._uow.commit()
        return plan_as_view(plan, offers)
