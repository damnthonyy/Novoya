from collections.abc import Sequence
from datetime import datetime
from typing import Protocol
from uuid import UUID

from novoya_api.quoting.domain.quote import Quote

ADMIN_PAGE = 50
ADMIN_CAP = 100


class QuoteRepository(Protocol):
    async def add(self, quote: Quote) -> None:
        """Adds the quote with its PDF. One quote per plan: a second one fails."""
        ...

    async def get(self, quote_id: UUID) -> Quote | None: ...

    async def search(
        self,
        plan_ids: Sequence[UUID] | None,
        expired: bool | None,
        now: datetime,
        *,
        limit: int = ADMIN_PAGE,
        offset: int = 0,
    ) -> list[Quote]:
        """Every client's quotes, newest first, without their PDF. plan_ids None means every
        plan; expired True keeps those past valid_until at `now`, False the others."""
        ...
