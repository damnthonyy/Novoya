"""The plans repository against a real PostgreSQL: a plan reads back as it was added.

Uses the database fixture of test_catalog_sql.py: skipped when Postgres does not answer.
"""

from collections.abc import AsyncIterator
from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from novoya_api.accounts.infrastructure.db.models import UserModel
from novoya_api.catalog.infrastructure.db.models import OfferRow, PartnerRow
from novoya_api.planning.domain.plan import DraftItem, Plan, PlanItem, PlanStatus
from novoya_api.planning.infrastructure.db.repository import SqlPlanRepository
from novoya_api.shared.domain.errors import InvalidTransition
from novoya_api.wishes.domain.wish import Wish
from novoya_api.wishes.infrastructure.db.repository import SqlWishRepository
from tests.test_catalog_sql import database_url  # noqa: F401  (fixture)

NOW = datetime(2026, 10, 19, 9, 0, tzinfo=UTC)


@pytest.fixture
async def engine(database_url) -> AsyncIterator[AsyncEngine]:  # noqa: F811
    engine = create_async_engine(database_url, poolclass=NullPool)
    async with engine.begin() as connection:
        await connection.execute(
            text("TRUNCATE plan_items, plans, wishes, offers, partners CASCADE")
        )
    yield engine
    await engine.dispose()


def new_session(engine: AsyncEngine) -> AsyncSession:
    return async_sessionmaker(engine, expire_on_commit=False)()


@pytest.fixture
async def wish_id(engine) -> UUID:
    async with new_session(engine) as session:
        user = UserModel(id=uuid4(), email=f"{uuid4()}@example.com", created_at=NOW)
        session.add(user)
        await session.flush()
        wish = Wish.create(user.id, "A week in Chania", NOW)
        await SqlWishRepository(session).add(wish)
        await session.commit()
        return wish.id


@pytest.fixture
async def offer_ids(engine) -> tuple[UUID, UUID]:
    partner = PartnerRow(
        id=uuid4(),
        name="Chania hotel",
        kind="hotel",
        country="Greece",
        city="Chania",
        contact_email="stay@example.com",
        contact_phone="+30 000",
        active=True,
    )
    offers = [
        OfferRow(
            id=uuid4(),
            partner_id=partner.id,
            kind=kind,
            title=title,
            description=title,
            country="Greece",
            city="Chania",
            min_persons=1,
            max_persons=4,
            available_from=date(2026, 4, 1),
            available_to=date(2026, 10, 31),
            tags=["style:beach"],
            featured=False,
            active=True,
        )
        for kind, title in [("hotel", "Sea view room"), ("activity", "Boat trip")]
    ]
    async with new_session(engine) as session:
        session.add(partner)
        await session.flush()
        session.add_all(offers)
        await session.commit()
    return offers[0].id, offers[1].id


async def add_plan(engine: AsyncEngine, plan: Plan) -> None:
    async with new_session(engine) as session:
        await SqlPlanRepository(session).add(plan)
        await session.commit()


async def read_plan(engine: AsyncEngine, plan_id: UUID) -> Plan | None:
    async with new_session(engine) as session:
        return await SqlPlanRepository(session).get(plan_id)


async def test_get_reads_back_a_proposed_plan_with_its_items(engine, wish_id, offer_ids):
    hotel, boat = offer_ids
    plan = Plan.propose(
        wish_id,
        True,
        "Sun and sea",
        [DraftItem(hotel, 1, 7, None), DraftItem(boat, 3, 2, "Bring a hat")],
        8,
        NOW,
    )
    await add_plan(engine, plan)

    read = await read_plan(engine, plan.id)

    assert read == plan
    assert read.status is PlanStatus.PROPOSED
    assert all(item.negotiated_price is None for item in read.items)
    assert all(item.removed is False for item in read.items)


async def test_get_returns_the_items_ordered_by_day(engine, wish_id, offer_ids):
    hotel, boat = offer_ids
    late = PlanItem(uuid4(), boat, 5, 1, None)
    early = PlanItem(uuid4(), hotel, 1, 7, None)
    plan = Plan(
        id=uuid4(),
        wish_id=wish_id,
        status=PlanStatus.PROPOSED,
        based_on_preferences=False,
        summary="Unordered",
        items=(late, early),
        created_at=NOW,
        updated_at=NOW,
    )
    await add_plan(engine, plan)

    read = await read_plan(engine, plan.id)

    assert read == replace(plan, items=(early, late))


async def test_get_returns_none_for_an_unknown_plan(engine):
    assert await read_plan(engine, uuid4()) is None


async def test_save_writes_requested_status(engine, wish_id, offer_ids):
    hotel, _boat = offer_ids
    later = datetime(2026, 10, 19, 10, 0, tzinfo=UTC)
    plan = Plan.propose(wish_id, True, "Sun and sea", [DraftItem(hotel, 1, 7, None)], 8, NOW)
    await add_plan(engine, plan)

    async with new_session(engine) as session:
        repo = SqlPlanRepository(session)
        loaded = await repo.get(plan.id)
        loaded.request_quote(later)
        await repo.save(loaded)
        await session.commit()

    read = await read_plan(engine, plan.id)
    assert read is not None
    assert read.status is PlanStatus.REQUESTED
    assert read.updated_at == later
    assert all(item.negotiated_price is None for item in read.items)


async def test_save_writes_item_prices_and_removed(engine, wish_id, offer_ids):
    hotel, _boat = offer_ids
    plan = Plan.propose(wish_id, True, "Sun and sea", [DraftItem(hotel, 1, 7, None)], 8, NOW)
    await add_plan(engine, plan)

    async with new_session(engine) as session:
        repo = SqlPlanRepository(session)
        loaded = await repo.get(plan.id)
        loaded.items = (replace(loaded.items[0], negotiated_price=Decimal("120.00"), removed=True),)
        await repo.save(loaded)
        await session.commit()

    read = await read_plan(engine, plan.id)
    assert read is not None
    assert read.items[0].negotiated_price == Decimal("120.00")
    assert read.items[0].removed is True


async def test_save_of_a_stale_read_does_not_wipe_an_agent_take(engine, wish_id, offer_ids):
    hotel, _boat = offer_ids
    later = datetime(2026, 10, 19, 10, 0, tzinfo=UTC)
    agent_id = uuid4()
    plan = Plan.propose(wish_id, True, "Sun and sea", [DraftItem(hotel, 1, 7, None)], 8, NOW)
    await add_plan(engine, plan)
    async with new_session(engine) as session:
        session.add(UserModel(id=agent_id, email=f"{agent_id}@example.com", created_at=NOW))
        await session.commit()

    async with new_session(engine) as first:
        first_repo = SqlPlanRepository(first)
        stale = await first_repo.get(plan.id)

        async with new_session(engine) as second:
            second_repo = SqlPlanRepository(second)
            current = await second_repo.get(plan.id)
            await second.commit()
            current.request_quote(later)
            await second_repo.save(current)
            await second.commit()

        async with new_session(engine) as agent_session:
            agent_repo = SqlPlanRepository(agent_session)
            taken = await agent_repo.get(plan.id)
            taken.status = PlanStatus.NEGOTIATING
            taken.assigned_agent_id = agent_id
            await agent_repo.save(taken)
            await agent_session.commit()

        stale.request_quote(later)
        with pytest.raises(InvalidTransition):
            await first_repo.save(stale)

    read = await read_plan(engine, plan.id)
    assert read is not None
    assert read.status is PlanStatus.NEGOTIATING
    assert read.assigned_agent_id == agent_id
