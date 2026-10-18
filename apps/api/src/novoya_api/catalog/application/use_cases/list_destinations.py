from novoya_api.catalog.application.ports import OfferRepository


class ListDestinations:
    """Destinations that have at least one listed offer (active offer of an active partner)."""

    def __init__(self, offers: OfferRepository) -> None:
        self._offers = offers

    async def __call__(self) -> list[tuple[str, str]]:
        destinations = {
            (offer.country, offer.city)
            for offer, partner in await self._offers.list_with_partners()
            if offer.is_listed_with(partner)
        }
        return sorted(destinations)
