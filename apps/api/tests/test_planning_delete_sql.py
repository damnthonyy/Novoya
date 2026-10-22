"""planning.public.delete_for_wishes against a real PostgreSQL: the plans of the given wishes
go with their items, the plans of other wishes stay.

Uses the fixtures of test_planning_repository_sql.py: skipped when Postgres does not answer.
"""

from uuid import UUID, uuid4

from sqlalchemy import func, select

from novoya_api.accounts.infrastructure.db.models import UserModel
from novoya_api.planning import public as planning_public
from novoya_api.planning.domain.plan import DraftItem, Plan
from novoya_api.planning.infrastructure.db.models import PlanItemModel, PlanModel
from novoya_api.wishes.domain.wish import Wish
from novoya_api.wishes.infrastructure.db.repository import SqlWishRepository
from tests.test_planning_repository_sql import (  # noqa: F401  (fixtures)
    NOW,
    add_plan,
    database_url,
    engine,
    new_session,
    offer_ids,
)


async def add_wish(engine) -> UUID:  # noqa: F811
    async with new_session(engine) as session:
        user = UserModel(id=uuid4(), email=f"{uuid4()}@example.com", created_at=NOW)
        session.add(user)
        await session.flush()
        wish = Wish.create(user.id, "A week in Chania", NOW)
        await SqlWishRepository(session).add(wish)
        await session.commit()
        return wish.id


async def add_plan_with_two_items(engine, wish_id: UUID, offer_ids) -> Plan:  # noqa: F811
    hotel, boat = offer_ids
    plan = Plan.propose(
        wish_id,
        True,
        "Sun and sea",
        [DraftItem(hotel, 1, 7, None), DraftItem(boat, 3, 2, None)],
        8,
        NOW,
    )
    await add_plan(engine, plan)
    return plan


async def count_rows(engine, model) -> int:  # noqa: F811
    async with new_session(engine) as session:
        return await session.scalar(select(func.count()).select_from(model))


async def test_delete_for_wishes_erases_their_plans_and_items_only(engine, offer_ids):  # noqa: F811
    leaving = await add_wish(engine)
    staying = await add_wish(engine)
    await add_plan_with_two_items(engine, leaving, offer_ids)
    kept = await add_plan_with_two_items(engine, staying, offer_ids)

    async with new_session(engine) as session:
        await planning_public.delete_for_wishes([leaving], session=session)
        await session.commit()

    assert await count_rows(engine, PlanModel) == 1
    assert await count_rows(engine, PlanItemModel) == 2
    async with new_session(engine) as session:
        remaining = await session.scalar(select(PlanModel.id))
    assert remaining == kept.id


async def test_delete_for_wishes_with_no_wish_erases_nothing(engine, offer_ids):  # noqa: F811
    wish = await add_wish(engine)
    await add_plan_with_two_items(engine, wish, offer_ids)

    async with new_session(engine) as session:
        await planning_public.delete_for_wishes([], session=session)
        await session.commit()

    assert await count_rows(engine, PlanModel) == 1
    assert await count_rows(engine, PlanItemModel) == 2
