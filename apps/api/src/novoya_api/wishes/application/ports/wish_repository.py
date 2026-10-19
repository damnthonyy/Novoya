from typing import Protocol
from uuid import UUID

from novoya_api.wishes.domain.wish import Wish


class WishRepository(Protocol):
    async def add(self, wish: Wish) -> None: ...

    async def get(self, wish_id: UUID) -> Wish | None: ...

    async def save(self, wish: Wish) -> None:
        """Raises InvalidTransition if another request changed the wish since get()."""
        ...
