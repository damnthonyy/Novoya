from typing import Protocol

from novoya_api.wishes.domain.wish import Wish


class WishRepository(Protocol):
    async def add(self, wish: Wish) -> None: ...
