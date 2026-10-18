from typing import Protocol

from novoya_api.catalog.domain import Offer, Partner


class PartnerRepository(Protocol):
    async def list_all(self) -> list[Partner]:
        """Every partner, active or not. The use case decides who is listed."""
        ...


class OfferRepository(Protocol):
    async def list_with_partners(self) -> list[tuple[Offer, Partner]]:
        """Every offer with its partner. The use case decides which are listed."""
        ...

    async def list_listed_destinations(self) -> list[tuple[str, str]]:
        """Distinct country, city of listed offers, sorted.

        Listed means an active offer of an active partner.
        """
        ...

    async def list_at(self, country: str, city: str | None) -> list[tuple[Offer, Partner]]:
        """Offers at this destination, with their partner. city None means the whole country."""
        ...
