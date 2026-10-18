from novoya_api.catalog.application.ports import PartnerRepository


class ListDestinations:
    """Destinations where at least one partner is active. English Title Case names."""

    def __init__(self, partners: PartnerRepository) -> None:
        self._partners = partners

    async def __call__(self) -> list[tuple[str, str]]:
        destinations = {
            (partner.country, partner.city)
            for partner in await self._partners.list_all()
            if partner.lists_offers()
        }
        return sorted(destinations)
