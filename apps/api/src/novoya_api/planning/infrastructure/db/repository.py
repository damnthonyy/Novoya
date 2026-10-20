from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from novoya_api.planning.domain.plan import Plan, PlanItem, PlanStatus
from novoya_api.planning.infrastructure.db.models import PlanItemModel, PlanModel
from novoya_api.shared.domain.errors import InvalidTransition


class SqlPlanRepository:
    """PlanRepository on PostgreSQL. Maps the entity to rows; the caller commits.

    save() updates the row only if its status is still the one this request read: a late
    request-quote must not overwrite an agent's take, and two clicks must not both pass.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._read_status: dict[UUID, str] = {}

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
        self._read_status[plan.id] = plan.status.value

    async def get(self, plan_id: UUID) -> Plan | None:
        row = await self._session.get(PlanModel, plan_id)
        if row is None:
            return None
        items = await self._session.scalars(
            select(PlanItemModel)
            .where(PlanItemModel.plan_id == plan_id)
            .order_by(PlanItemModel.day, PlanItemModel.id)
        )
        self._read_status[row.id] = row.status
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

    async def save(self, plan: Plan) -> None:
        read_status = self._read_status[plan.id]  # KeyError: save() without get() or add()
        result = await self._session.execute(
            update(PlanModel)
            .where(PlanModel.id == plan.id, PlanModel.status == read_status)
            .values(
                status=plan.status.value,
                based_on_preferences=plan.based_on_preferences,
                summary=plan.summary,
                assigned_agent_id=plan.assigned_agent_id,
                updated_at=plan.updated_at,
            )
            .execution_options(synchronize_session=False)
        )
        if result.rowcount != 1:
            raise InvalidTransition("the plan changed meanwhile, reload it")
        self._read_status[plan.id] = plan.status.value
        for item in plan.items:
            await self._session.execute(
                update(PlanItemModel)
                .where(PlanItemModel.id == item.id, PlanItemModel.plan_id == plan.id)
                .values(
                    day=item.day,
                    quantity=item.quantity,
                    note=item.note,
                    negotiated_price=item.negotiated_price,
                    removed=item.removed,
                )
                .execution_options(synchronize_session=False)
            )
