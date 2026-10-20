from collections import defaultdict
from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from novoya_api.planning.domain.errors import InvalidPlan, PlanNotFound
from novoya_api.planning.domain.plan import Plan, PlanItem, PlanStatus
from novoya_api.planning.infrastructure.db.models import PlanItemModel, PlanModel
from novoya_api.shared.domain.errors import InvalidTransition


class SqlPlanRepository:
    """PlanRepository on PostgreSQL. Maps the entity to rows; the caller commits.

    save() writes the plan row only, and only if its status is still the one this request
    read: a late request-quote must not overwrite an agent's take. Item prices go through
    save_item(), so two tabs pricing different lines cannot wipe each other. A removal
    locks the plan row and counts kept items in the database, so two tabs cannot drop
    the last item.
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
        return self._to_plan(row, items)

    async def list_by_status(self, status: PlanStatus) -> list[Plan]:
        rows = (
            await self._session.scalars(
                select(PlanModel)
                .where(PlanModel.status == status.value)
                .order_by(PlanModel.updated_at, PlanModel.id)
            )
        ).all()
        if not rows:
            return []
        ids = [row.id for row in rows]
        item_rows = await self._session.scalars(
            select(PlanItemModel)
            .where(PlanItemModel.plan_id.in_(ids))
            .order_by(PlanItemModel.day, PlanItemModel.id)
        )
        by_plan: dict[UUID, list[PlanItemModel]] = defaultdict(list)
        for item in item_rows:
            by_plan[item.plan_id].append(item)
        return [self._to_plan(row, by_plan[row.id]) for row in rows]

    def _to_plan(self, row: PlanModel, items: Iterable[PlanItemModel]) -> Plan:
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

    async def save_item(self, plan: Plan, item_id: UUID) -> None:
        read_status = self._read_status[plan.id]  # KeyError: save_item() without get() or add()
        item = next((entry for entry in plan.items if entry.id == item_id), None)
        if item is None:
            raise PlanNotFound("no such item")
        if item.removed:
            # Lock this plan so two removals run one after the other; then count in the database.
            await self._session.execute(
                select(PlanModel.id).where(PlanModel.id == plan.id).with_for_update()
            )
            others_kept = await self._session.scalar(
                select(func.count())
                .select_from(PlanItemModel)
                .where(
                    PlanItemModel.plan_id == plan.id,
                    PlanItemModel.id != item.id,
                    PlanItemModel.removed.is_(False),
                )
            )
            if others_kept == 0:
                raise InvalidPlan("a plan needs at least one item")
        result = await self._session.execute(
            update(PlanModel)
            .where(PlanModel.id == plan.id, PlanModel.status == read_status)
            .values(updated_at=plan.updated_at)
            .execution_options(synchronize_session=False)
        )
        if result.rowcount != 1:
            raise InvalidTransition("the plan changed meanwhile, reload it")
        written = await self._session.execute(
            update(PlanItemModel)
            .where(PlanItemModel.id == item.id, PlanItemModel.plan_id == plan.id)
            .values(negotiated_price=item.negotiated_price, removed=item.removed)
            .execution_options(synchronize_session=False)
        )
        if written.rowcount != 1:
            raise PlanNotFound("no such item")
