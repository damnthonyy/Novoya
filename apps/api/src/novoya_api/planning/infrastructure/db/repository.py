from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from novoya_api.planning.domain.plan import Plan, PlanItem, PlanStatus
from novoya_api.planning.infrastructure.db.models import PlanItemModel, PlanModel


class SqlPlanRepository:
    """PlanRepository on PostgreSQL. Maps the entity to rows; the caller commits."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, plan: Plan) -> None:
        self._session.add(
            PlanModel(
                id=plan.id,
                wish_id=plan.wish_id,
                status=plan.status.value,
                based_on_preferences=plan.based_on_preferences,
                summary=plan.summary,
                assigned_agent_id=plan.assigned_agent_id,
                created_at=plan.created_at,
                updated_at=plan.updated_at,
            )
        )
        # The plan row first: plan_items points to it, and the unit of work does not know.
        await self._session.flush()
        self._session.add_all(
            PlanItemModel(
                id=item.id,
                plan_id=plan.id,
                offer_id=item.offer_id,
                day=item.day,
                quantity=item.quantity,
                note=item.note,
                negotiated_price=item.negotiated_price,
                removed=item.removed,
            )
            for item in plan.items
        )

    async def get(self, plan_id: UUID) -> Plan | None:
        row = await self._session.get(PlanModel, plan_id)
        if row is None:
            return None
        items = await self._session.scalars(
            select(PlanItemModel)
            .where(PlanItemModel.plan_id == plan_id)
            .order_by(PlanItemModel.day, PlanItemModel.id)
        )
        return Plan(
            id=row.id,
            wish_id=row.wish_id,
            status=PlanStatus(row.status),
            based_on_preferences=row.based_on_preferences,
            summary=row.summary,
            items=tuple(
                PlanItem(
                    id=item.id,
                    offer_id=item.offer_id,
                    day=item.day,
                    quantity=item.quantity,
                    note=item.note,
                    negotiated_price=item.negotiated_price,
                    removed=item.removed,
                )
                for item in items
            ),
            created_at=row.created_at,
            updated_at=row.updated_at,
            assigned_agent_id=row.assigned_agent_id,
        )
