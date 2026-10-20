from typing import Protocol
from uuid import UUID

from novoya_api.planning.domain.plan import Plan, PlanStatus


class PlanRepository(Protocol):
    async def add(self, plan: Plan) -> None: ...

    async def get(self, plan_id: UUID) -> Plan | None: ...

    async def list_by_status(self, status: PlanStatus) -> list[Plan]: ...

    async def save(self, plan: Plan) -> None:
        """Writes the plan and its items.

        Raises InvalidTransition if another request changed the plan since get()."""
        ...
