"""The client's preferences against a real PostgreSQL (#165): only their own wishes are read,
newest first; a removed preference stays removed; two removals at once both land; a wish
whose plan left proposed is locked.

Uses the database fixture of test_catalog_sql.py: skipped when Postgres does not answer.
"""

import asyncio
from datetime import timedelta
from uuid import UUID, uuid4

import pytest

from novoya_api.accounts.infrastructure.db.models import UserModel
from novoya_api.planning.infrastructure.db.models import PlanModel
from novoya_api.planning.infrastructure.wish_owners import WishOwners
from novoya_api.planning.presentation.http.dependencies import get_request_quote
from novoya_api.shared.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from novoya_api.wishes.application.use_cases.preferences import (
    ListPreferences,
    RemovePreference,
)
from novoya_api.wishes.domain.answers import Answers, SelectedTag
from novoya_api.wishes.domain.errors import PreferenceLocked
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


# The open wish picked only the beach.
OPEN_ANSWERS = Answers(
    selected_tags=(SelectedTag("style", "beach"),),
    budget_max=ANSWERS.budget_max,
    currency=ANSWERS.currency,
    persons=ANSWERS.persons,
    start_date=ANSWERS.start_date,
    end_date=ANSWERS.end_date,
)


def planned_wish(owner, created=NOW):
    wish = shown_wish(owner)
    wish.created_at = created
    wish.answer(ANSWERS, LATER)
    wish.mark_planned(LATER)
    return wish


async def add_plan(engine, wish_id, status) -> UUID:  # noqa: F811
    plan_id = uuid4()
    async with new_session(engine) as session:
        session.add(
            PlanModel(
                id=plan_id,
                wish_id=wish_id,
                status=status,
                based_on_preferences=True,
                summary="A week by the sea",
                created_at=LATER,
                updated_at=LATER,
            )
        )
        await session.commit()
    return plan_id


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


async def test_plan_statuses_lock_the_wishes_the_agency_works_from(engine, user_id):  # noqa: F811
    statuses = ["proposed", "requested", "negotiating", "quoted", "accepted", "rejected"]
    wishes = {status: planned_wish(user_id) for status in statuses}
    no_plan = planned_wish(user_id)
    for wish in [*wishes.values(), no_plan]:
        await add_wish(engine, wish)
    for status, wish in wishes.items():
        await add_plan(engine, wish.id, status)

    async with new_session(engine) as session:
        locked = await PlanningPlanStatuses(session).locked_wish_ids(
            [wish.id for wish in [*wishes.values(), no_plan]]
        )

    # A rejected plan frees its wish's tags; proposed or no plan was never locked.
    assert locked == {wishes[s].id for s in ("requested", "negotiating", "quoted", "accepted")}


async def test_a_wish_with_two_plans_is_locked_when_one_is_with_the_agency(engine, user_id):  # noqa: F811
    requested_too, rejected_too = planned_wish(user_id), planned_wish(user_id)
    await add_wish(engine, requested_too)
    await add_wish(engine, rejected_too)
    await add_plan(engine, requested_too.id, "proposed")
    await add_plan(engine, requested_too.id, "requested")
    await add_plan(engine, rejected_too.id, "rejected")
    await add_plan(engine, rejected_too.id, "proposed")

    async with new_session(engine) as session:
        locked = await PlanningPlanStatuses(session).locked_wish_ids(
            [requested_too.id, rejected_too.id]
        )

    assert locked == {requested_too.id}


async def test_removable_comes_from_the_real_plan_statuses(engine, user_id):  # noqa: F811
    sent, open_wish = planned_wish(user_id), shown_wish(user_id)
    open_wish.answer(OPEN_ANSWERS, LATER)
    await add_wish(engine, sent)
    await add_wish(engine, open_wish)
    await add_plan(engine, sent.id, "quoted")

    async with new_session(engine) as session:
        found = await ListPreferences(SqlWishRepository(session), PlanningPlanStatuses(session))(
            user_id
        )

    removable = {(s.id, t.id): t.removable for s in found for t in s.tags}
    assert removable == {
        ("style", "beach"): True,  # also on the open wish
        ("food", "seafood"): False,  # only on the quoted one
    }


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


async def plan_status(engine, plan_id) -> str:  # noqa: F811
    async with new_session(engine) as session:
        return (await session.get(PlanModel, plan_id)).status


async def test_a_quote_request_waits_for_a_removal_in_progress(engine, user_id):  # noqa: F811
    wish = planned_wish(user_id)
    await add_wish(engine, wish)
    plan_id = await add_plan(engine, wish.id, "proposed")

    async with new_session(engine) as removal, new_session(engine) as request:
        # The removal has read the wish (locked) and seen a proposed plan.
        removal_wishes = SqlWishRepository(removal)
        (held,) = await removal_wishes.list_for_user(user_id, lock=True)
        assert await PlanningPlanStatuses(removal).locked_wish_ids([wish.id]) == set()
        racing = asyncio.create_task(get_request_quote(request)(plan_id, user_id))
        await asyncio.sleep(0.3)
        assert not racing.done()  # the quote request waits for the removal

        held.remove_tag("style", "beach", LATER)
        await removal_wishes.save(held)
        await removal.commit()
        await asyncio.wait_for(racing, timeout=5)

    # The removal ran on a proposed plan, then the plan was requested.
    assert (await read_wish(engine, wish.id)).answers.selected_tags == (
        SelectedTag("food", "seafood"),
    )
    assert await plan_status(engine, plan_id) == "requested"


async def test_a_removal_after_a_quote_request_in_progress_is_locked(engine, user_id):  # noqa: F811
    wish = planned_wish(user_id)
    await add_wish(engine, wish)
    plan_id = await add_plan(engine, wish.id, "proposed")

    async with new_session(engine) as request, new_session(engine) as removal:
        # The quote request holds the wish (FOR SHARE) and moves its plan to requested.
        # The same reads RequestQuote does, through the adapter get_request_quote builds.
        assert await WishOwners(request, lock=True).owner_id(wish.id) == user_id
        plan = await request.get(PlanModel, plan_id)
        plan.status = "requested"
        await request.flush()
        racing = asyncio.create_task(remover(removal)(user_id, "style", "beach"))
        await asyncio.sleep(0.3)
        assert not racing.done()  # the removal waits for the quote request

        await request.commit()
        with pytest.raises(PreferenceLocked):  # it sees the requested plan
            await asyncio.wait_for(racing, timeout=5)

    assert (await read_wish(engine, wish.id)).answers == ANSWERS
