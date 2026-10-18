from typing import Protocol

from novoya_api.wishes.domain.wish import Destination


class Catalog(Protocol):
    """What wishes needs from the partner catalog."""

    async def covered_destinations(self) -> list[Destination]:
        """Destinations with at least one active partner."""
        ...

    async def tags_at(self, destination: Destination) -> list[str]:
        """Tags ("section:tag") of the active offers there; the whole country without a city."""
        ...
