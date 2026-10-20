from typing import Protocol
from uuid import UUID

from novoya_api.planning.domain.plan import Plan


class PlanRepository(Protocol):
    async def add(self, plan: Plan) -> None: ...

    async def get(self, plan_id: UUID) -> Plan | None: ...

    async def save(self, plan: Plan) -> None: ...
