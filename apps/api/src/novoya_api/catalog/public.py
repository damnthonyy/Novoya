"""What other modules may use from catalog. Nothing else in catalog may be imported.

- covered_destinations() -> destinations with at least one listed offer
- tags_at(country, city) -> tags of listed offers there (city None = the whole country)
- search_offers(country, city, tags, persons, start, end) -> listed offers that fit, as
  OfferView. OfferView carries partner name and contact; other modules decide who may see them.

Country and city matching is case-insensitive. Prefer the names returned by
covered_destinations() (English Title Case) so the LLM and the panel stay consistent.

Inside a request, pass the request's session: each call then reads through it instead of
taking a second connection from the pool.

Planned:
- get_offers(ids) -> list of OfferView, only active ones (to check a plan)
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from novoya_api.catalog.application.dto import OfferView
from novoya_api.catalog.application.use_cases.list_destinations import ListDestinations
from novoya_api.catalog.application.use_cases.list_tags_at import ListTagsAt
from novoya_api.catalog.application.use_cases.search_offers import SearchOffers
from novoya_api.catalog.infrastructure.db.repositories import SqlOfferRepository
from novoya_api.shared.infrastructure.db.session import get_sessionmaker


async def covered_destinations(*, session: AsyncSession | None = None) -> list[tuple[str, str]]:
    """Destinations with at least one listed offer. Names are English Title Case."""
    async with _reading(session) as reading:
        return await ListDestinations(SqlOfferRepository(reading))()


async def tags_at(
    country: str, city: str | None, *, session: AsyncSession | None = None
) -> list[str]:
    """Tags of listed offers at this destination, as section:tag. city None = the whole country."""
    async with _reading(session) as reading:
        return await ListTagsAt(SqlOfferRepository(reading))(country, city)


async def search_offers(
    country: str,
    city: str | None,
    tags: list[str],
    persons: int,
    start: date,
    end: date,
    *,
    session: AsyncSession | None = None,
) -> list[OfferView]:
    """Listed offers at this destination that fit the group and the whole trip, best first.

    With tags, an offer needs at least one of them (section:tag); without, all fitting offers
    come back. city None = the whole country."""
    async with _reading(session) as reading:
        return await SearchOffers(SqlOfferRepository(reading))(
            country, city, tags, persons, start, end
        )


@asynccontextmanager
async def _reading(session: AsyncSession | None) -> AsyncIterator[AsyncSession]:
    """The caller's session, or a session of our own that is closed afterwards."""
    if session is not None:
        yield session
        return
    async with get_sessionmaker()() as own:
        yield own
