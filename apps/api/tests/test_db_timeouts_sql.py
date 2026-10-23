"""Database timeouts against a real PostgreSQL (novoya_test, like test_catalog_sql.py).

Skipped when Postgres does not answer.
"""

from uuid import uuid4

import pytest
from sqlalchemy import delete, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.pool import NullPool

from novoya_api.catalog.infrastructure.db.models import PartnerRow
from novoya_api.config import Settings
from novoya_api.shared.infrastructure.db.session import build_engine
from novoya_api.shared.presentation.http.errors import handle_database_error
from tests.test_catalog_sql import database_url  # noqa: F401  (fixture)


async def test_every_session_has_the_timeouts(database_url):  # noqa: F811
    engine = build_engine(Settings(_env_file=None, database_url=database_url), poolclass=NullPool)
    try:
        async with engine.connect() as connection:
            shown = {
                name: await connection.scalar(text(f"SHOW {name}"))
                for name in (
                    "lock_timeout",
                    "statement_timeout",
                    "idle_in_transaction_session_timeout",
                )
            }
    finally:
        await engine.dispose()

    assert shown == {
        "lock_timeout": "5s",
        "statement_timeout": "30s",
        "idle_in_transaction_session_timeout": "1min",
    }


async def test_a_row_lock_held_too_long_ends_in_lock_not_available_then_503(database_url):  # noqa: F811
    settings = Settings(_env_file=None, database_url=database_url, db_lock_timeout_ms=200)
    engine = build_engine(settings, poolclass=NullPool)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    partner_id = uuid4()
    try:
        async with sessions() as setup:
            setup.add(
                PartnerRow(
                    id=partner_id,
                    name="Locked hotel",
                    kind="hotel",
                    country="Italy",
                    city="Rome",
                    contact_email="locked@example.com",
                    contact_phone="+39 000",
                    active=True,
                )
            )
            await setup.commit()

        async with sessions() as holder, sessions() as waiter:
            locked = select(PartnerRow.id).where(PartnerRow.id == partner_id).with_for_update()
            assert await holder.scalar(locked) == partner_id

            # The holder never lets go: without lock_timeout this would wait forever.
            with pytest.raises(DBAPIError) as raised:
                await waiter.scalar(locked)
            await holder.rollback()

        assert raised.value.orig.sqlstate == "55P03"
        response = await handle_database_error(None, raised.value)
        assert response.status_code == 503
        assert response.headers["Retry-After"]
    finally:
        async with sessions() as cleanup:
            await cleanup.execute(delete(PartnerRow).where(PartnerRow.id == partner_id))
            await cleanup.commit()
        await engine.dispose()
