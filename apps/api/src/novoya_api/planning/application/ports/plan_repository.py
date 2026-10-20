from typing import Protocol
from uuid import UUID

from novoya_api.planning.domain.plan import Plan, PlanStatus


class PlanRepository(Protocol):
    async def add(self, plan: Plan) -> None: ...

    async def get(self, plan_id: UUID) -> Plan | None: ...

    async def list_by_status(self, status: PlanStatus) -> list[Plan]: ...

    async def save(self, plan: Plan) -> None:
        """Writes the plan row (status, assignee, timestamps). Not the items.

        Raises InvalidTransition if another request changed the status since get()."""
        ...

    async def save_item(self, plan: Plan, item_id: UUID) -> None:
        """Writes one item's price or removed flag, and the plan's updated_at.

        Other items stay as they are in the database. Raises InvalidTransition if the
        status changed since get()."""
        ...
