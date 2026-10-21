"""DÉTOUR import into a real PostgreSQL, from a made-up sqlite file.

Needs docker compose db (or the CI service); skipped when Postgres does not answer.
Uses novoya_test, like test_catalog_sql.py, so the development database is never emptied.
"""

import asyncio
import tempfile
from collections.abc import AsyncIterator
from datetime import date
from pathlib import Path
from uuid import uuid4

import pytest
from alembic.config import Config
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from alembic import command
from novoya_api.catalog.infrastructure.db.models import ExtraRow, OfferRow, PartnerRow, ReviewRow
from novoya_api.catalog.infrastructure.db.repositories import (
    SqlExtraRepository,
    SqlReviewRepository,
)
from novoya_api.catalog.infrastructure.detour.mapping import DetourImportError, detour_id
from novoya_api.catalog.infrastructure.detour.run import import_detour
from novoya_api.catalog.infrastructure.seed.run import seed_catalog
from novoya_api.catalog.public import covered_destinations, search_offers
from novoya_api.shared.infrastructure.db.session import close_db
from tests.detour_fixture import CHANIA, CHANIA_STAY, CHANIA_TRANSFER, DetourFile, sample_detour
from tests.test_catalog_sql import (
    API_DIR,
    database_url,  # noqa: F401  (fixture)
)

TABLES = "reviews, extras, offers, partners"


@pytest.fixture
async def session(database_url) -> AsyncIterator[AsyncSession]:  # noqa: F811
    # import_detour / public.py use a process-wide engine; pytest-asyncio uses one loop per test.
    await close_db()
    engine = create_async_engine(database_url, poolclass=NullPool)
    async with engine.begin() as connection:
        await connection.execute(text(f"TRUNCATE {TABLES} CASCADE"))
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        yield session
    await engine.dispose()
    await close_db()


@pytest.fixture
def source(tmp_path) -> Path:
    return sample_detour(tmp_path / "detour.sqlite")


async def counts(session: AsyncSession) -> dict[str, int]:
    return {
        row.__tablename__: await session.scalar(select(func.count()).select_from(row))
        for row in (PartnerRow, OfferRow, ReviewRow, ExtraRow)
    }


async def test_import_reports_and_stores_the_counts(session, source):
    reported = await import_detour(source)

    assert (reported.partners, reported.offers, reported.reviews, reported.extras) == (3, 3, 3, 3)
    assert await counts(session) == {"partners": 3, "offers": 3, "reviews": 3, "extras": 3}


async def test_importing_twice_keeps_the_counts(session, source):
    await import_detour(source)
    first = await counts(session)

    await import_detour(source)

    assert await counts(session) == first


async def test_imported_partners_are_marked_detour_and_have_no_phone(session, source):
    await import_detour(source)

    partner = await session.get(PartnerRow, detour_id("partenaires", "P001"))

    assert partner.source == "detour"
    assert partner.contact_phone is None


async def test_a_changed_row_is_updated(session, source):
    await import_detour(source)
    with DetourFile(source) as detour:
        detour.execute("UPDATE offres SET prix_unitaire_eur = 90 WHERE id = ?", (CHANIA_STAY,))

    await import_detour(source)

    offer = await session.get(OfferRow, detour_id("offres", CHANIA_STAY))
    await session.refresh(offer)
    assert offer.price_eur == 90


async def test_a_review_no_longer_publishable_is_deleted(session, source):
    await import_detour(source)
    with DetourFile(source) as detour:
        detour.execute("UPDATE consentements SET statut = 'retire' WHERE avis_id = 'A001'")

    await import_detour(source)

    assert await session.get(ReviewRow, detour_id("avis", "A001")) is None
    assert await session.get(ReviewRow, detour_id("avis", "A002")) is not None


async def test_an_invalid_row_rolls_back_the_whole_import(session, source):
    await import_detour(source)
    with DetourFile(source) as detour:
        detour.execute("UPDATE offres SET prix_unitaire_eur = 90 WHERE id = ?", (CHANIA_STAY,))
        detour.offer("F099", "P001", CHANIA, capacite=0)

    with pytest.raises(DetourImportError):
        await import_detour(source)

    offer = await session.get(OfferRow, detour_id("offres", CHANIA_STAY))
    await session.refresh(offer)
    assert offer.price_eur == 85
    assert await counts(session) == {"partners": 3, "offers": 3, "reviews": 3, "extras": 3}


async def test_an_invalid_file_writes_nothing(session, source):
    with DetourFile(source) as detour:
        detour.offer("F099", "P001", CHANIA, capacite=0)

    with pytest.raises(DetourImportError):
        await import_detour(source)

    assert await counts(session) == {"partners": 0, "offers": 0, "reviews": 0, "extras": 0}


async def test_imported_destinations_with_an_active_partner_are_covered(session, source):
    await import_detour(source)

    covered = await covered_destinations()

    assert ("Greece", "Chania") in covered
    assert ("France", "Saint-Jean de Luz") not in covered  # its only partner is inactive


async def test_seed_refuses_once_detour_data_is_imported(session, source):
    await import_detour(source)

    with pytest.raises(RuntimeError, match="detour"):
        await seed_catalog()


async def test_reviews_at_a_destination_are_newest_first(session, source):
    await import_detour(source)

    reviews = await SqlReviewRepository(session).list_at("Greece", "Chania", 100)

    assert [review.id for review in reviews] == [
        detour_id("avis", "A004"),
        detour_id("avis", "A001"),
    ]
    assert reviews[1].author == "Zélie Q."


async def test_reviews_are_limited(session, source):
    await import_detour(source)

    reviews = await SqlReviewRepository(session).list_at(None, None, 2)

    assert len(reviews) == 2


async def test_only_active_extras_are_listed(session, source):
    await import_detour(source)
    retired = await session.get(ExtraRow, detour_id("preferences", "O002"))
    retired.active = False
    await session.commit()

    extras = await SqlExtraRepository(session).list_active()

    assert {extra.id for extra in extras} == {
        detour_id("preferences", "O001"),
        detour_id("preferences", "O003"),
    }
    assert [
        extra.constraints for extra in extras if extra.id == detour_id("preferences", "O001")
    ] == [("Selon disponibilité", "Demande à l'avance")]


async def test_database_accepts_a_partner_without_a_phone(session):
    session.add(
        PartnerRow(
            id=uuid4(),
            name="No phone",
            kind="hotel",
            country="Greece",
            city="Chania",
            contact_email="nophone@example.com",
            contact_phone=None,
            active=True,
        )
    )
    await session.commit()


async def test_rows_missing_from_a_later_export_are_deactivated_not_deleted(session, source):
    await import_detour(source)
    with DetourFile(source) as detour:
        detour.execute(
            "DELETE FROM offres_mois_disponibles WHERE parent_id = ?", (CHANIA_TRANSFER,)
        )
        detour.execute("DELETE FROM offres WHERE id = ?", (CHANIA_TRANSFER,))
        detour.execute("DELETE FROM partenaires WHERE id = 'P002'")
        detour.execute("DELETE FROM preferences_contraintes WHERE parent_id = 'O003'")
        detour.execute("DELETE FROM preferences WHERE id = 'O003'")

    reported = await import_detour(source)

    assert (reported.partners, reported.offers, reported.extras) == (2, 2, 2)
    transfer = await session.get(
        OfferRow, detour_id("offres", CHANIA_TRANSFER), populate_existing=True
    )
    shuttle = await session.get(
        PartnerRow, detour_id("partenaires", "P002"), populate_existing=True
    )
    guide = await session.get(ExtraRow, detour_id("preferences", "O003"), populate_existing=True)
    assert (transfer.active, shuttle.active, guide.active) == (False, False, False)
    assert (
        await session.get(OfferRow, detour_id("offres", CHANIA_STAY), populate_existing=True)
    ).active is True
    listed = await search_offers("Greece", "Chania", [], 2, date(2027, 3, 1), date(2027, 3, 5))
    assert detour_id("offres", CHANIA_TRANSFER) not in {offer.id for offer in listed}
    assert detour_id("preferences", "O003") not in {
        extra.id for extra in await SqlExtraRepository(session).list_active()
    }


async def test_a_row_back_in_the_export_is_active_again(session, source):
    await import_detour(source)
    with DetourFile(source) as detour:
        detour.execute("DELETE FROM preferences_contraintes WHERE parent_id = 'O003'")
        detour.execute("DELETE FROM preferences WHERE id = 'O003'")
    await import_detour(source)
    with DetourFile(source) as detour:
        detour.preference("O003", tarification="sur_devis")

    await import_detour(source)

    assert (
        await session.get(ExtraRow, detour_id("preferences", "O003"), populate_existing=True)
    ).active is True


async def test_a_hand_added_partner_is_never_deactivated_by_the_import(session, source):
    hand_added = PartnerRow(
        id=uuid4(),
        name="Hand-added hotel",
        kind="hotel",
        country="Italy",
        city="Rome",
        contact_email="rome@example.com",
        contact_phone="+39 000",
        active=True,
    )
    session.add(hand_added)
    await session.commit()

    await import_detour(source)

    assert (await session.get(PartnerRow, hand_added.id, populate_existing=True)).active is True


def test_downgrade_gives_imported_partners_a_placeholder_phone(database_url):  # noqa: F811
    asyncio.run(_import_then_downgrade(database_url))


async def _import_then_downgrade(url: str) -> None:
    await close_db()
    engine = create_async_engine(url, poolclass=NullPool)
    async with engine.begin() as connection:
        await connection.execute(text(f"TRUNCATE {TABLES} CASCADE"))
    await engine.dispose()
    with tempfile.TemporaryDirectory() as folder:
        await import_detour(sample_detour(Path(folder) / "detour.sqlite"))
    await close_db()

    config = Config(str(API_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(API_DIR / "alembic"))
    await asyncio.to_thread(command.downgrade, config, "b7e4a91c2d08")
    try:
        engine = create_async_engine(url, poolclass=NullPool)
        async with engine.connect() as connection:
            phones = (await connection.execute(text("SELECT contact_phone FROM partners"))).all()
        await engine.dispose()
        assert {phone for (phone,) in phones} == {"-"}
    finally:
        await asyncio.to_thread(command.upgrade, config, "head")
