"""What other modules may use from catalog. Nothing else in catalog may be imported.

- covered_destinations() -> destinations with at least one listed offer
- tags_at(country, city) -> tags of listed offers there (city None = the whole country)
- search_offers(country, city, tags, persons, start, end) -> listed offers that fit, as
  OfferView. OfferView carries partner name and contact; other modules decide who may see them.

Country and city matching is case-insensitive. Prefer the names returned by
covered_destinations() (English Title Case) so the LLM and the panel stay consistent.

Planned:
- get_offers(ids) -> list of OfferView, only active ones (to check a plan)
"""

from datetime import date

from novoya_api.catalog.application.dto import OfferView
from novoya_api.catalog.application.use_cases.list_destinations import ListDestinations
from novoya_api.catalog.application.use_cases.list_tags_at import ListTagsAt
from novoya_api.catalog.application.use_cases.search_offers import SearchOffers
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


async def search_offers(
    country: str, city: str | None, tags: list[str], persons: int, start: date, end: date
) -> list[OfferView]:
    """Listed offers at this destination that fit the group and the whole trip, best first.

    With tags, an offer needs at least one of them (section:tag); without, all fitting offers
    come back. city None = the whole country."""
    async with get_sessionmaker()() as session:
        return await SearchOffers(SqlOfferRepository(session))(
            country, city, tags, persons, start, end
        )
