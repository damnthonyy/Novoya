"""What other modules may use from catalog. Nothing else in catalog may be imported.

- covered_destinations() -> destinations with at least one active partner
- tags_at(country, city) -> tags of listed offers there (city None = the whole country)

Planned:
- search_offers(destination, tags, persons, dates) -> list of OfferView
- get_offers(ids) -> list of OfferView, only active ones (to check a plan)
OfferView carries partner name and contact; other modules decide who may see them.
"""

from novoya_api.catalog.application.use_cases.list_destinations import ListDestinations
from novoya_api.catalog.application.use_cases.list_tags_at import ListTagsAt
from novoya_api.catalog.infrastructure.db.repositories import (
    SqlOfferRepository,
    SqlPartnerRepository,
)
from novoya_api.shared.infrastructure.db.session import get_sessionmaker


async def covered_destinations() -> list[tuple[str, str]]:
    """Destinations where at least one partner is active. Names are English Title Case."""
    async with get_sessionmaker()() as session:
        return await ListDestinations(SqlPartnerRepository(session))()


async def tags_at(country: str, city: str | None) -> list[str]:
    """Tags of listed offers at this destination, as section:tag. city None = the whole country."""
    async with get_sessionmaker()() as session:
        return await ListTagsAt(SqlOfferRepository(session))(country, city)
