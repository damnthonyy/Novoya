"""What other modules may use from catalog. Nothing else in catalog may be imported.

- covered_destinations() -> destinations with at least one listed offer
- tags_at(country, city) -> tags of listed offers there (city None = the whole country)

Country and city matching is case-insensitive. Prefer the names returned by
covered_destinations() (English Title Case) so the LLM and the panel stay consistent.

Planned:
- search_offers(destination, tags, persons, dates) -> list of OfferView
- get_offers(ids) -> list of OfferView, only active ones (to check a plan)
OfferView carries partner name and contact; other modules decide who may see them.
"""

from novoya_api.catalog.application.use_cases.list_destinations import ListDestinations
from novoya_api.catalog.application.use_cases.list_tags_at import ListTagsAt
from novoya_api.catalog.infrastructure.db.repositories import SqlOfferRepository
from novoya_api.shared.infrastructure.db.session import get_sessionmaker


async def covered_destinations() -> list[tuple[str, str]]:
    """Destinations with at least one listed offer. Names are English Title Case."""
    async with get_sessionmaker()() as session:
        return await ListDestinations(SqlOfferRepository(session))()


async def tags_at(country: str, city: str | None) -> list[str]:
    """Tags of listed offers at this destination, as section:tag. city None = the whole country."""
    async with get_sessionmaker()() as session:
        return await ListTagsAt(SqlOfferRepository(session))(country, city)
