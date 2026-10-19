from novoya_api.catalog.application.ports import OfferRepository
from novoya_api.catalog.domain import Offer


class ListOffers:
    """Every offer, including inactive ones, so an agent can reactivate them."""

    def __init__(self, offers: OfferRepository) -> None:
        self._offers = offers

    async def __call__(self) -> list[Offer]:
        return [offer for offer, _partner in await self._offers.list_with_partners()]
