"""SQL repositories, seed and catalog migration, against a real PostgreSQL.

Needs docker compose db (or the CI service); skipped when Postgres does not answer.
Uses novoya_test so the development database is never emptied.
"""

import asyncio
import os
from collections.abc import AsyncIterator, Iterator
from datetime import date
from pathlib import Path
from uuid import uuid4

import pytest
from alembic.config import Config
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from alembic import command
from novoya_api.catalog.infrastructure.db.models import OfferRow, PartnerRow
from novoya_api.catalog.infrastructure.db.repositories import SqlOfferRepository
from novoya_api.catalog.infrastructure.seed.data import OFFERS, PARTNERS
from novoya_api.catalog.infrastructure.seed.run import seed_catalog
from novoya_api.catalog.public import covered_destinations, tags_at
from novoya_api.config import get_settings
from novoya_api.shared.infrastructure.db.session import close_db, get_engine, get_sessionmaker

API_DIR = Path(__file__).parent.parent
TABLES = "offers, partners"


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
    dev_url = get_settings().database_url
    if not asyncio.run(database_answers(dev_url)):
        pytest.skip("PostgreSQL is not running (docker compose up db)")
    url = dev_url.rsplit("/", 1)[0] + "/novoya_test"
    asyncio.run(create_test_database(dev_url, "novoya_test"))

    previous = os.environ.get("NOVOYA_DATABASE_URL")
    os.environ["NOVOYA_DATABASE_URL"] = url
    previous_env = os.environ.get("NOVOYA_ENV")
    os.environ["NOVOYA_ENV"] = "development"
    clear_cached_settings()
    config = Config(str(API_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(API_DIR / "alembic"))
    command.upgrade(config, "head")
    yield url

    if previous is None:
        del os.environ["NOVOYA_DATABASE_URL"]
    else:
        os.environ["NOVOYA_DATABASE_URL"] = previous
    if previous_env is None:
        os.environ.pop("NOVOYA_ENV", None)
    else:
        os.environ["NOVOYA_ENV"] = previous_env
    clear_cached_settings()


@pytest.fixture
async def session(database_url) -> AsyncIterator[AsyncSession]:
    # seed_catalog / public.py use a process-wide engine; pytest-asyncio uses one loop per test.
    await close_db()
    engine = create_async_engine(database_url, poolclass=NullPool)
    async with engine.begin() as connection:
        await connection.execute(text(f"TRUNCATE {TABLES} CASCADE"))
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        yield session
    await engine.dispose()
    await close_db()


async def test_seed_can_run_twice_without_wiping_other_rows(session, database_url):
    extra = PartnerRow(
        id=uuid4(),
        name="Hand-added hotel",
        kind="hotel",
        country="Italy",
        city="Rome",
        contact_email="rome@example.com",
        contact_phone="+39 000",
        active=True,
    )
    session.add(extra)
    await session.commit()

    await seed_catalog()
    await seed_catalog()

    session.expire_all()
    partners = (await session.scalars(select(PartnerRow))).all()
    names = {row.name for row in partners}
    assert "Hand-added hotel" in names
    assert len(partners) == len(PARTNERS) + 1
    offers = (await session.scalars(select(OfferRow))).all()
    assert len(offers) == len(OFFERS)


async def test_sql_tags_at_filters_by_city_and_ignores_case(session):
    await seed_catalog()
    offers = SqlOfferRepository(session)
    chania = await offers.list_at("greece", "chania")
    morocco = await offers.list_at("Morocco", None)
    assert chania
    assert all(offer.city == "Chania" for offer, _partner in chania)
    assert morocco
    assert all(offer.country == "Morocco" for offer, _partner in morocco)


async def test_public_functions_read_listed_seed_offers(session, database_url):
    await seed_catalog()
    destinations = await covered_destinations()
    assert destinations == [
        ("France", "Biarritz"),
        ("Greece", "Chania"),
        ("Morocco", "Marrakech"),
    ]
    tags = await tags_at("morocco", "marrakech")
    assert "accommodation:riad" in tags
    assert "style:package" not in tags


async def test_database_rejects_invalid_person_limits(session):
    partner = PartnerRow(
        id=uuid4(),
        name="Limits",
        kind="hotel",
        country="Greece",
        city="Chania",
        contact_email="l@example.com",
        contact_phone="+30 000",
        active=True,
    )
    session.add(partner)
    await session.flush()
    session.add(
        OfferRow(
            id=uuid4(),
            partner_id=partner.id,
            kind="hotel",
            title="Bad limits",
            description="x",
            country="Greece",
            city="Chania",
            min_persons=0,
            max_persons=2,
            available_from=date(2026, 4, 1),
            available_to=date(2026, 10, 31),
            tags=["style:beach"],
            featured=False,
            active=True,
        )
    )
    with pytest.raises(IntegrityError):
        await session.flush()
    await session.rollback()


async def test_database_rejects_inverted_availability_dates(session):
    partner = PartnerRow(
        id=uuid4(),
        name="Dates",
        kind="hotel",
        country="Greece",
        city="Chania",
        contact_email="d@example.com",
        contact_phone="+30 000",
        active=True,
    )
    session.add(partner)
    await session.flush()
    session.add(
        OfferRow(
            id=uuid4(),
            partner_id=partner.id,
            kind="hotel",
            title="Bad dates",
            description="x",
            country="Greece",
            city="Chania",
            min_persons=1,
            max_persons=2,
            available_from=date(2026, 10, 31),
            available_to=date(2026, 4, 1),
            tags=["style:beach"],
            featured=False,
            active=True,
        )
    )
    with pytest.raises(IntegrityError):
        await session.flush()
    await session.rollback()


def test_catalog_migration_up_and_down(database_url):
    config = Config(str(API_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(API_DIR / "alembic"))
    command.downgrade(config, "92f81d9a6b75")
    command.upgrade(config, "head")
