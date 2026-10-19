from sqlalchemy.ext.asyncio import AsyncSession

from novoya_api.catalog.public import covered_destinations, tags_at
from novoya_api.wishes.domain.wish import Destination


class PartnerCatalog:
    """The partner catalog, read through catalog.public with the request's session, so a
    wish takes one connection from the pool, not one per catalog call."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def covered_destinations(self) -> list[Destination]:
        covered = await covered_destinations(session=self._session)
        return [Destination(country, city) for country, city in covered]

    async def tags_at(self, destination: Destination) -> list[str]:
        return await tags_at(destination.country, destination.city, session=self._session)
