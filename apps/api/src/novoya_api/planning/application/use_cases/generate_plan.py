from uuid import UUID

from novoya_api.planning.application.dto import OfferSummary, PlanItemView, PlanRequest, PlanView
from novoya_api.planning.application.ports.offer_catalog import OfferCatalog
from novoya_api.planning.application.ports.plan_repository import PlanRepository
from novoya_api.planning.application.ports.plan_writer import PlanWriter
from novoya_api.planning.domain.errors import NoOfferFits
from novoya_api.planning.domain.plan import DraftItem, Plan, keep_valid, tidy
from novoya_api.shared.application.clock import Clock
from novoya_api.shared.application.unit_of_work import UnitOfWork

FALLBACK_SUMMARY = (
    "A first plan built from our partners' offers that fit your group and dates. "
    "An agent will adjust it with you when you ask for a quote."
)


class GeneratePlan:
    """Build the proposed plan of an answered wish and add it. The caller commits.

    The read ends before the model writes, so no connection is held while it thinks: call it
    before the caller writes anything, and keep the caller's state outside the session.

    The writer may use an LLM, but the catalog decides what is allowed: every item must
    point to a listed offer that fits the travellers and the whole trip. When the writer
    fails, or none of its items is allowed, the plan is built from the best fitting offers,
    so a client always gets a plan."""

    def __init__(
        self,
        catalog: OfferCatalog,
        writer: PlanWriter,
        plans: PlanRepository,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._catalog = catalog
        self._writer = writer
        self._plans = plans
        self._uow = uow
        self._clock = clock

    async def __call__(self, request: PlanRequest) -> PlanView:
        # Checked first so the client gets 422 without waiting for a model run.
        if not await self._fitting(request, ()):
            raise NoOfferFits("no listed offer fits the travellers and dates")
        # Nothing to save yet: end the read so the connection is not held while the model writes.
        await self._uow.rollback()

        draft = await self._writer.write(request)
        # The model may take a minute: read the catalog again, so an offer deactivated or
        # booked out meanwhile is neither kept nor used by the fallback.
        allowed = await self._fitting(request, ())
        if not allowed:
            raise NoOfferFits("no listed offer fits the travellers and dates")
        ranked = await self._fitting(request, request.tags) if request.tags else []
        offers = {offer.id: offer for offer in [*allowed, *ranked]}
        hotels = {offer.id for offer in offers.values() if offer.kind == "hotel"}

        valid = keep_valid(draft.items, set(offers), request.trip_days) if draft else []
        items = tidy(valid, hotels, request.trip_days)
        # The model's summary describes all its items: keep it only if none was rejected or cut.
        summary = draft.summary if draft and items == list(draft.items) else FALLBACK_SUMMARY
        if not items:
            summary = FALLBACK_SUMMARY
            items = _fallback_items(ranked, allowed, request.trip_days)

        plan = Plan.propose(
            request.wish_id,
            bool(request.tags),
            summary,
            items,
            request.trip_days,
            self._clock.now(),
        )
        await self._plans.add(plan)
        return _view(plan, offers)

    async def _fitting(self, request: PlanRequest, tags: tuple[str, ...]) -> list[OfferSummary]:
        return await self._catalog.fitting_offers(
            request.country,
            request.city,
            tags,
            request.persons,
            request.start_date,
            request.end_date,
        )


def _fallback_items(
    ranked: list[OfferSummary], allowed: list[OfferSummary], trip_days: int
) -> list[DraftItem]:
    """A hotel for every night, then one other offer a day, best first. The hotel may come
    from any fitting offer: a trip needs a bed even when no hotel matches the tags."""
    items: list[DraftItem] = []
    hotel = next((offer for offer in [*ranked, *allowed] if offer.kind == "hotel"), None)
    if hotel:
        items.append(DraftItem(hotel.id, 1, max(1, trip_days - 1), None))
    others = [offer for offer in ranked or allowed if offer.kind != "hotel"][:trip_days]
    items.extend(DraftItem(offer.id, day, 1, None) for day, offer in enumerate(others, start=1))
    return items


def _view(plan: Plan, offers: dict[UUID, OfferSummary]) -> PlanView:
    return PlanView(
        id=plan.id,
        wish_id=plan.wish_id,
        status=plan.status.value,
        based_on_preferences=plan.based_on_preferences,
        summary=plan.summary,
        items=tuple(
            PlanItemView(
                id=item.id,
                offer_id=item.offer_id,
                day=item.day,
                quantity=item.quantity,
                note=item.note,
                kind=offers[item.offer_id].kind,
                title=offers[item.offer_id].title,
                description=offers[item.offer_id].description,
            )
            for item in plan.items
        ),
    )
