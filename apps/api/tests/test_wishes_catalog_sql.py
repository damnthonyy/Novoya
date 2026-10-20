"""The wishes catalog adapter and the travel tools against the seed catalog in a real
PostgreSQL, reading through the caller's session.

Uses the database fixtures of test_catalog_sql.py: skipped when Postgres does not answer.
"""

from datetime import UTC, datetime
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from novoya_api.catalog import public
from novoya_api.catalog.infrastructure.seed.data import OFFERS, PARTNERS
from novoya_api.catalog.infrastructure.seed.run import seed_catalog
from novoya_api.planning.infrastructure.llm.tools import travel_tools
from novoya_api.shared.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from novoya_api.wishes.application.ports.destination_reader import DestinationReading
from novoya_api.wishes.application.use_cases.send_wish import SendWish, SendWishCommand
from novoya_api.wishes.domain.panel import Panel
from novoya_api.wishes.domain.wish import Destination, WishStatus
from novoya_api.wishes.infrastructure.catalog import PartnerCatalog
from novoya_api.wishes.infrastructure.llm.panel_builder import TagsFromOffersBuilder
from tests.accounts.fakes import NoopRateLimiter
from tests.test_catalog_sql import database_url, session  # noqa: F401  (fixtures)

pytestmark = pytest.mark.usefixtures("session")

USER_ID = UUID("00000000-0000-0000-0000-000000000001")
NOW = datetime(2026, 10, 18, 9, 0, tzinfo=UTC)

BIARRITZ = Destination("France", "Biarritz")
CHANIA = Destination("Greece", "Chania")
MARRAKECH = Destination("Morocco", "Marrakech")
LISBON = Destination("Portugal", "Lisbon")

ACTIVE_PARTNERS = {partner["id"] for partner in PARTNERS if partner["active"]}


def seed_tags(country: str, city: str | None = None) -> list[str]:
    """Tags of the listed seed offers there (active offer of an active partner), sorted."""
    return sorted(
        {
            tag
            for offer in OFFERS
            if offer["active"]
            and offer["partner_id"] in ACTIVE_PARTNERS
            and offer["country"] == country
            and (city is None or offer["city"] == city)
            for tag in offer["tags"]
        }
    )


@pytest.fixture(autouse=True)
def only_the_given_session(monkeypatch):
    """catalog.public must read through the caller's session, never open its own."""

    def no_sessionmaker():
        raise AssertionError("catalog.public opened its own session")

    monkeypatch.setattr(public, "get_sessionmaker", no_sessionmaker)


class FixedClock:
    def now(self) -> datetime:
        return NOW


class FakeReader:
    def __init__(self, reading: DestinationReading) -> None:
        self.reading = reading

    async def read(self, text, covered) -> DestinationReading:
        return self.reading


class FakeWishes:
    def __init__(self) -> None:
        self.added = []

    async def add(self, wish) -> None:
        self.added.append(wish)


class FakeUnitOfWork:
    async def commit(self) -> None:
        pass

    async def rollback(self) -> None:
        pass


def send_wish(session, reading: DestinationReading) -> SendWish:  # noqa: F811
    return SendWish(
        wishes=FakeWishes(),
        catalog=PartnerCatalog(session),
        reader=FakeReader(reading),
        panel_builder=TagsFromOffersBuilder(),
        rate_limiter=NoopRateLimiter(),
        uow=FakeUnitOfWork(),
        clock=FixedClock(),
    )


# PartnerCatalog


async def test_partner_catalog_covers_the_seed_destinations(session):  # noqa: F811
    await seed_catalog()

    covered = await PartnerCatalog(session).covered_destinations()

    assert covered == [BIARRITZ, CHANIA, MARRAKECH]


async def test_partner_catalog_tags_at_a_city_are_the_seed_tags_there(session):  # noqa: F811
    await seed_catalog()

    tags = await PartnerCatalog(session).tags_at(CHANIA)

    assert tags == seed_tags("Greece", "Chania")
    assert tags


async def test_partner_catalog_tags_at_a_country_cover_the_whole_country(session):  # noqa: F811
    await seed_catalog()

    tags = await PartnerCatalog(session).tags_at(Destination("Greece"))

    assert tags == seed_tags("Greece")


async def test_partner_catalog_hides_tags_of_an_inactive_partner(session):  # noqa: F811
    await seed_catalog()

    tags = await PartnerCatalog(session).tags_at(MARRAKECH)

    assert tags == seed_tags("Morocco", "Marrakech")
    assert "style:package" not in tags


async def test_partner_catalog_has_no_tags_for_an_uncovered_destination(session):  # noqa: F811
    await seed_catalog()

    assert await PartnerCatalog(session).tags_at(LISBON) == []


# SendWish on the seed


async def test_a_wish_for_a_seed_destination_shows_the_panel_of_its_tags(session):  # noqa: F811
    await seed_catalog()
    use_case = send_wish(session, DestinationReading(destination=CHANIA, suggestions=[]))

    result = await use_case(SendWishCommand(user_id=USER_ID, text="A calm week in Chania"))

    assert result.wish.status == WishStatus.PANEL_SHOWN
    assert result.wish.destination == CHANIA
    assert result.wish.panel == Panel.from_tags(seed_tags("Greece", "Chania"))


async def test_a_wish_outside_the_seed_is_not_covered(session):  # noqa: F811
    await seed_catalog()
    use_case = send_wish(session, DestinationReading(destination=LISBON, suggestions=[]))

    result = await use_case(SendWishCommand(user_id=USER_ID, text="A week in Lisbon"))

    assert result.wish.status == WishStatus.NOT_COVERED
    assert result.wish.panel is None
    assert set(result.suggestions) <= {BIARRITZ, CHANIA, MARRAKECH}
    assert result.suggestions


# Travel tools on the caller's session


async def test_travel_tools_with_a_session_list_the_seed_destinations(session):  # noqa: F811
    await seed_catalog()
    tools = {tool.name: tool for tool in travel_tools(session=session)}

    result = await tools["covered_destinations"].handler()

    assert result == {
        "destinations": [
            {"country": "France", "city": "Biarritz"},
            {"country": "Greece", "city": "Chania"},
            {"country": "Morocco", "city": "Marrakech"},
        ]
    }


async def test_travel_tools_with_a_session_search_the_seed_offers(session):  # noqa: F811
    await seed_catalog()
    tools = {tool.name: tool for tool in travel_tools(session=session)}

    result = await tools["search_offers"].handler(
        country="Greece", city="Chania", persons=2, start_date="2026-05-10", end_date="2026-05-17"
    )

    assert {offer["city"] for offer in result["offers"]} == {"Chania"}
    assert len(result["offers"]) == 2


class SessionWatchingReader:
    """Notes whether the request session still holds a transaction while the model reads."""

    def __init__(self, session: AsyncSession, reading: DestinationReading) -> None:  # noqa: F811
        self.session = session
        self.reading = reading
        self.in_transaction: bool | None = None

    async def read(self, text, covered) -> DestinationReading:
        self.in_transaction = self.session.in_transaction()
        return self.reading


async def test_the_request_session_holds_no_transaction_while_the_reader_runs(session):  # noqa: F811
    await seed_catalog()
    reader = SessionWatchingReader(session, DestinationReading(destination=CHANIA, suggestions=[]))
    use_case = SendWish(
        wishes=FakeWishes(),
        catalog=PartnerCatalog(session),
        reader=reader,
        panel_builder=TagsFromOffersBuilder(),
        rate_limiter=NoopRateLimiter(),
        uow=SqlAlchemyUnitOfWork(session),
        clock=FixedClock(),
    )

    result = await use_case(SendWishCommand(user_id=USER_ID, text="A week in Chania"))

    assert reader.in_transaction is False
    assert result.wish.status == WishStatus.PANEL_SHOWN


class SessionWatchingBuilder:
    """Notes whether the request session still holds a transaction while the panel is built."""

    def __init__(self, session: AsyncSession) -> None:  # noqa: F811
        self.session = session
        self.in_transaction: bool | None = None

    async def build(self, text, destination, tags) -> Panel:
        self.in_transaction = self.session.in_transaction()
        return Panel.from_tags(tags)


async def test_the_request_session_holds_no_transaction_while_the_builder_runs(session):  # noqa: F811
    await seed_catalog()
    builder = SessionWatchingBuilder(session)
    use_case = SendWish(
        wishes=FakeWishes(),
        catalog=PartnerCatalog(session),
        reader=FakeReader(DestinationReading(destination=CHANIA, suggestions=[])),
        panel_builder=builder,
        rate_limiter=NoopRateLimiter(),
        uow=SqlAlchemyUnitOfWork(session),
        clock=FixedClock(),
    )

    result = await use_case(SendWishCommand(user_id=USER_ID, text="A week in Chania"))

    assert builder.in_transaction is False
    assert result.wish.status == WishStatus.PANEL_SHOWN
