"""The client's preferences against a real PostgreSQL (#165): only their own wishes are read,
newest first; a removed preference stays removed; two removals at once both land; a wish
whose plan left proposed is locked.

Uses the database fixture of test_catalog_sql.py: skipped when Postgres does not answer.
"""

import asyncio
from datetime import timedelta
from uuid import UUID, uuid4

from novoya_api.accounts.infrastructure.db.models import UserModel
from novoya_api.planning.infrastructure.db.models import PlanModel
from novoya_api.shared.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from novoya_api.wishes.application.use_cases.preferences import RemovePreference
from novoya_api.wishes.domain.answers import SelectedTag
from novoya_api.wishes.infrastructure.db.repository import SqlWishRepository
from novoya_api.wishes.infrastructure.plan_statuses import PlanningPlanStatuses
from novoya_api.wishes.public import preferences
from tests.test_catalog_sql import database_url  # noqa: F401  (fixture)
from tests.test_wishes_preferences import FixedClock
from tests.test_wishes_repository_sql import (
    ANSWERS,
    LATER,
    NOW,
    add_wish,
    engine,  # noqa: F401  (fixture)
    new_session,
    read_wish,
    shown_wish,
    user_id,  # noqa: F401  (fixture)
)


async def other_user(engine) -> UUID:  # noqa: F811
    async with new_session(engine) as session:
        user = UserModel(id=uuid4(), email=f"{uuid4()}@example.com", created_at=NOW)
        session.add(user)
        await session.commit()
        return user.id


def planned_wish(owner, created=NOW):
    wish = shown_wish(owner)
    wish.created_at = created
    wish.answer(ANSWERS, LATER)
    wish.mark_planned(LATER)
    return wish


async def add_plan(engine, wish_id, status) -> None:  # noqa: F811
    async with new_session(engine) as session:
        session.add(
            PlanModel(
                id=uuid4(),
                wish_id=wish_id,
                status=status,
                based_on_preferences=True,
                summary="A week by the sea",
                created_at=LATER,
                updated_at=LATER,
            )
        )
        await session.commit()


def remover(session) -> RemovePreference:
    return RemovePreference(
        SqlWishRepository(session),
        PlanningPlanStatuses(session),
        SqlAlchemyUnitOfWork(session),
        FixedClock(),
    )


async def test_list_for_user_reads_only_that_users_wishes_newest_first(engine, user_id):  # noqa: F811
    old = planned_wish(user_id, NOW - timedelta(days=2))
    new = shown_wish(user_id)
    middle = planned_wish(user_id, NOW - timedelta(days=1))
    theirs = planned_wish(await other_user(engine))
    for wish in (old, new, middle, theirs):
        await add_wish(engine, wish)

    async with new_session(engine) as session:
        listed = await SqlWishRepository(session).list_for_user(user_id)

    assert [wish.id for wish in listed] == [new.id, middle.id, old.id]


async def test_public_preferences_are_section_and_tag(engine, user_id):  # noqa: F811
    await add_wish(engine, planned_wish(user_id))
    await add_wish(engine, planned_wish(await other_user(engine)))

    async with new_session(engine) as session:
        assert await preferences(user_id, session=session) == ("style:beach", "food:seafood")


async def test_a_removed_preference_is_saved(engine, user_id):  # noqa: F811
    mine = planned_wish(user_id)
    theirs = planned_wish(await other_user(engine))
    await add_wish(engine, mine)
    await add_wish(engine, theirs)
    await add_plan(engine, mine.id, "proposed")

    async with new_session(engine) as session:
        await remover(session)(user_id, "style", "beach")

    read = await read_wish(engine, mine.id)
    assert read.answers.selected_tags == (SelectedTag("food", "seafood"),)
    assert read.answers.budget_max == ANSWERS.budget_max
    assert (await read_wish(engine, theirs.id)).answers == ANSWERS


async def test_plan_statuses_lock_the_wishes_whose_plan_left_proposed(engine, user_id):  # noqa: F811
    proposed, requested, quoted, no_plan = (planned_wish(user_id) for _ in range(4))
    for wish in (proposed, requested, quoted, no_plan):
        await add_wish(engine, wish)
    await add_plan(engine, proposed.id, "proposed")
    await add_plan(engine, requested.id, "requested")
    await add_plan(engine, quoted.id, "quoted")

    ids = [proposed.id, requested.id, quoted.id, no_plan.id]
    async with new_session(engine) as session:
        locked = await PlanningPlanStatuses(session).locked_wish_ids(ids)

    assert locked == {requested.id, quoted.id}


async def test_a_wish_sent_to_the_agency_keeps_its_tag(engine, user_id):  # noqa: F811
    open_wish, sent = planned_wish(user_id), planned_wish(user_id)
    await add_wish(engine, open_wish)
    await add_wish(engine, sent)
    await add_plan(engine, sent.id, "negotiating")

    async with new_session(engine) as session:
        await remover(session)(user_id, "style", "beach")

    assert (await read_wish(engine, open_wish.id)).answers.selected_tags == (
        SelectedTag("food", "seafood"),
    )
    assert (await read_wish(engine, sent.id)).answers == ANSWERS


async def test_two_removals_at_once_both_land(engine, user_id):  # noqa: F811
    wish = planned_wish(user_id)
    await add_wish(engine, wish)

    async with new_session(engine) as first, new_session(engine) as second:
        # The first removal reads and locks the rows, then the second one starts.
        first_wishes = SqlWishRepository(first)
        (held,) = await first_wishes.list_for_user(user_id, lock=True)
        racing = asyncio.create_task(remover(second)(user_id, "food", "seafood"))
        await asyncio.sleep(0.3)
        assert not racing.done()  # it waits for the lock

        held.remove_tag("style", "beach", LATER)
        await first_wishes.save(held)
        await first.commit()
        await asyncio.wait_for(racing, timeout=5)

    assert (await read_wish(engine, wish.id)).answers.selected_tags == ()
