"""The client's preferences against a real PostgreSQL (#165): only their own wishes are read,
and a removed preference stays removed.

Uses the database fixture of test_catalog_sql.py: skipped when Postgres does not answer.
"""

from uuid import uuid4

from novoya_api.accounts.infrastructure.db.models import UserModel
from novoya_api.shared.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from novoya_api.wishes.application.use_cases.preferences import RemovePreference
from novoya_api.wishes.domain.answers import SelectedTag
from novoya_api.wishes.infrastructure.db.repository import SqlWishRepository
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


async def other_user(engine) -> object:  # noqa: F811
    async with new_session(engine) as session:
        user = UserModel(id=uuid4(), email=f"{uuid4()}@example.com", created_at=NOW)
        session.add(user)
        await session.commit()
        return user.id


def planned_wish(owner):
    wish = shown_wish(owner)
    wish.answer(ANSWERS, LATER)
    wish.mark_planned(LATER)
    return wish


async def test_list_for_user_reads_only_that_users_wishes(engine, user_id):  # noqa: F811
    mine, unanswered = planned_wish(user_id), shown_wish(user_id)
    theirs = planned_wish(await other_user(engine))
    for wish in (mine, unanswered, theirs):
        await add_wish(engine, wish)

    async with new_session(engine) as session:
        listed = await SqlWishRepository(session).list_for_user(user_id)

    assert {wish.id for wish in listed} == {mine.id, unanswered.id}


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

    async with new_session(engine) as session:
        remove = RemovePreference(
            SqlWishRepository(session), SqlAlchemyUnitOfWork(session), FixedClock()
        )
        await remove(user_id, "style", "beach")

    read = await read_wish(engine, mine.id)
    assert read.answers.selected_tags == (SelectedTag("food", "seafood"),)
    assert read.answers.budget_max == ANSWERS.budget_max
    assert (await read_wish(engine, theirs.id)).answers == ANSWERS
