"""The SQL repositories, the migration and the grant-role command, against a real PostgreSQL.

Needs the PostgreSQL of docker compose (or the CI service); skipped when it does not answer.
They run in a separate database, novoya_test, created if needed: the migrations are applied
once, then each test starts from empty tables.
"""

import asyncio
import os
from collections.abc import AsyncIterator, Iterator
from datetime import timedelta
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from alembic import command
from novoya_api.accounts.application.services.one_time_tokens import consume_token
from novoya_api.accounts.application.use_cases.change_user_role import (
    ChangeUserRole,
    ChangeUserRoleCommand,
)
from novoya_api.accounts.domain.auth_session import AuthSession
from novoya_api.accounts.domain.credentials import PasswordCredential
from novoya_api.accounts.domain.errors import (
    EmailAlreadyUsed,
    InvalidOrExpiredToken,
    LastAdminRequired,
)
from novoya_api.accounts.domain.one_time_token import OneTimeToken, TokenPurpose
from novoya_api.accounts.domain.role import Role
from novoya_api.accounts.domain.value_objects import Email, PasswordHash
from novoya_api.accounts.infrastructure.db.repositories import (
    SqlOneTimeTokenRepository,
    SqlPasswordCredentialRepository,
    SqlRoleChangeRepository,
    SqlSessionRepository,
    SqlUserRepository,
)
from novoya_api.accounts.infrastructure.security import SecureTokenGenerator
from novoya_api.accounts.presentation import cli
from novoya_api.accounts.presentation.http.dependencies import build_store
from novoya_api.config import get_settings
from novoya_api.shared.infrastructure.db.session import get_engine, get_sessionmaker
from tests.accounts.fakes import FrozenClock, make_user

API_DIR = Path(__file__).parent.parent.parent
TABLES = "role_changes, one_time_tokens, sessions, password_credentials, users"
NOW = FrozenClock().now()


async def database_answers(url: str) -> bool:
    engine = create_async_engine(url, poolclass=NullPool)
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
    finally:
        await engine.dispose()


async def create_test_database(url: str, name: str) -> None:
    engine = create_async_engine(url, poolclass=NullPool, isolation_level="AUTOCOMMIT")
    async with engine.connect() as connection:
        exists = await connection.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": name}
        )
        if not exists:
            await connection.execute(text(f'CREATE DATABASE "{name}"'))
    await engine.dispose()


def clear_cached_settings() -> None:
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_sessionmaker.cache_clear()


@pytest.fixture(scope="module")
def database_url() -> Iterator[str]:
    """A separate database, novoya_test, so the tests never empty the development one."""
    dev_url = get_settings().database_url
    if not asyncio.run(database_answers(dev_url)):
        pytest.skip("PostgreSQL is not running (docker compose up db)")
    url = dev_url.rsplit("/", 1)[0] + "/novoya_test"
    asyncio.run(create_test_database(dev_url, "novoya_test"))

    # Everything that reads the settings (Alembic, the grant-role command) uses that database.
    previous = os.environ.get("NOVOYA_DATABASE_URL")
    os.environ["NOVOYA_DATABASE_URL"] = url
    clear_cached_settings()
    config = Config(str(API_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(API_DIR / "alembic"))
    command.upgrade(config, "head")
    yield url

    if previous is None:
        del os.environ["NOVOYA_DATABASE_URL"]
    else:
        os.environ["NOVOYA_DATABASE_URL"] = previous
    clear_cached_settings()


@pytest.fixture
async def session(database_url) -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(database_url, poolclass=NullPool)
    async with engine.begin() as connection:
        await connection.execute(text(f"TRUNCATE {TABLES} CASCADE"))
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        yield session
    await engine.dispose()


async def test_users_are_stored_and_found_by_email(session):
    users = SqlUserRepository(session)
    alice = make_user("alice@example.com")
    await users.add(alice)
    await session.commit()

    found = await users.get_by_email(Email("ALICE@example.com"))
    assert found == alice
    assert await users.get(alice.id) == alice


async def test_the_database_refuses_a_second_account_with_the_same_email(session):
    users = SqlUserRepository(session)
    await users.add(make_user("alice@example.com"))
    with pytest.raises(EmailAlreadyUsed):
        await users.add(make_user("alice@example.com"))


async def test_users_are_saved_counted_and_searched(session):
    users = SqlUserRepository(session)
    admin = make_user("admin@x.io", role=Role.ADMIN, now=NOW)
    agent = make_user("agent@x.io", now=NOW + timedelta(minutes=1))
    await users.add(admin)
    await users.add(agent)
    agent.change_role(Role.AGENT, changed_by=admin.id, now=NOW)
    await users.save(agent)
    await session.commit()

    assert await users.count_active_with_role(Role.ADMIN) == 1
    assert [u.email.value for u in await users.search(None, None, 10, 0)] == [
        "agent@x.io",
        "admin@x.io",
    ]
    assert [u.email.value for u in await users.search("AGENT", None, 10, 0)] == ["agent@x.io"]
    assert [u.email.value for u in await users.search(None, Role.ADMIN, 10, 0)] == ["admin@x.io"]


async def test_role_changes_are_logged_with_their_source(session):
    users, changes = SqlUserRepository(session), SqlRoleChangeRepository(session)
    user = make_user()
    await users.add(user)
    await changes.add(user.change_role(Role.ADMIN, changed_by=None, now=NOW))
    await session.commit()

    row = (await session.execute(text("SELECT source, changed_by FROM role_changes"))).one()
    assert tuple(row) == ("cmd_grant_role", None)


async def test_password_credentials_are_upserted(session):
    users, credentials = SqlUserRepository(session), SqlPasswordCredentialRepository(session)
    user = make_user()
    await users.add(user)
    await credentials.upsert(PasswordCredential(user.id, PasswordHash("first"), NOW))
    await credentials.upsert(PasswordCredential(user.id, PasswordHash("second"), NOW))
    await session.commit()
    assert (await credentials.get(user.id)).password_hash == PasswordHash("second")


async def test_sessions_come_with_their_user_and_are_revoked(session):
    users, sessions = SqlUserRepository(session), SqlSessionRepository(session)
    user = make_user()
    await users.add(user)
    ttl = timedelta(days=7), timedelta(days=30)
    kept = AuthSession.open(user.id, "a" * 64, NOW, *ttl, user_agent="laptop")
    other = AuthSession.open(user.id, "b" * 64, NOW, *ttl, user_agent="phone")
    await sessions.add(kept)
    await sessions.add(other)
    await session.commit()

    found_session, found_user = await sessions.get_with_user("a" * 64)
    assert found_session.id == kept.id
    assert found_user.email == user.email

    await sessions.revoke_all_for_user(user.id, NOW, except_session_id=kept.id)
    await session.commit()
    assert (await sessions.get("a" * 64)).revoked_at is None
    assert (await sessions.get("b" * 64)).revoked_at == NOW


async def test_one_time_tokens_are_invalidated(session):
    users, tokens = SqlUserRepository(session), SqlOneTimeTokenRepository(session)
    user = make_user()
    await users.add(user)
    token = OneTimeToken.issue(user.id, TokenPurpose.PASSWORD_RESET, "c" * 64, NOW)
    await tokens.add(token)
    await session.commit()

    assert await tokens.get("c" * 64, TokenPurpose.EMAIL_VERIFICATION) is None
    await tokens.invalidate_all(user.id, TokenPurpose.PASSWORD_RESET, NOW)
    await session.commit()
    assert (await tokens.get("c" * 64, TokenPurpose.PASSWORD_RESET)).used_at == NOW


def test_grant_role_command(database_url, capsys):
    async def add_user() -> None:
        engine = create_async_engine(database_url, poolclass=NullPool)
        async with engine.begin() as connection:
            await connection.execute(text(f"TRUNCATE {TABLES} CASCADE"))
        async with async_sessionmaker(engine)() as session:
            await SqlUserRepository(session).add(make_user("boss@x.io"))
            await session.commit()
        await engine.dispose()

    asyncio.run(add_user())
    assert cli.main(["grant-role", "--email", "boss@x.io", "--role", "admin"]) == 0
    assert "boss@x.io is now admin" in capsys.readouterr().out
    assert cli.main(["grant-role", "--email", "nobody@x.io", "--role", "admin"]) == 1
    assert "user_not_found" in capsys.readouterr().err


# Two requests at the same time: two sessions, the second must wait for the first.


@pytest.fixture
async def sessions(database_url) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(database_url, poolclass=NullPool)
    async with engine.begin() as connection:
        await connection.execute(text(f"TRUNCATE {TABLES} CASCADE"))
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


async def blocked(task: asyncio.Task) -> bool:
    await asyncio.sleep(0.3)
    return not task.done()


async def test_two_admins_demoting_each_other_at_once_keep_one_admin(sessions):
    a = make_user("a@x.io", role=Role.ADMIN)
    b = make_user("b@x.io", role=Role.ADMIN)
    async with sessions() as setup:
        store = build_store(setup)
        await store.users.add(a)
        await store.users.add(b)
        await setup.commit()

    async with sessions() as first, sessions() as second:
        users = SqlUserRepository(first)
        assert await users.count_active_with_role(Role.ADMIN) == 2  # A's request, admins locked
        store = build_store(second)
        demote_a = ChangeUserRole(store.users, store.role_changes, store.uow, FrozenClock())
        b_demotes_a = asyncio.create_task(
            demote_a(ChangeUserRoleCommand(a.id, Role.CLIENT, changed_by=b.id))
        )
        assert await blocked(b_demotes_a)

        target = await users.get(b.id)
        target.change_role(Role.CLIENT, changed_by=a.id, now=NOW)
        await users.save(target)
        await first.commit()

        with pytest.raises(LastAdminRequired):
            await b_demotes_a


async def test_a_reset_link_used_by_two_requests_at_once_works_once(sessions):
    generator = SecureTokenGenerator()
    raw = generator.generate()
    alice = make_user("alice@example.com")
    async with sessions() as setup:
        store = build_store(setup)
        await store.users.add(alice)
        await store.tokens.add(
            OneTimeToken.issue(alice.id, TokenPurpose.PASSWORD_RESET, generator.hash(raw), NOW)
        )
        await setup.commit()

    async with sessions() as first, sessions() as second:
        purpose = TokenPurpose.PASSWORD_RESET
        await consume_token(SqlOneTimeTokenRepository(first), generator, raw, purpose, NOW)
        again = asyncio.create_task(
            consume_token(SqlOneTimeTokenRepository(second), generator, raw, purpose, NOW)
        )
        assert await blocked(again)
        await first.commit()

        with pytest.raises(InvalidOrExpiredToken):
            await again
