"""SendWish is tested with fake ports: a scripted reader, an in-memory catalog and repository."""

from datetime import UTC, datetime
from uuid import UUID

import pytest

from novoya_api.wishes.application.ports.destination_reader import DestinationReading
from novoya_api.wishes.application.use_cases.send_wish import (
    SendWish,
    SendWishCommand,
    SendWishResult,
)
from novoya_api.wishes.domain.errors import InvalidWish
from novoya_api.wishes.domain.panel import Panel
from novoya_api.wishes.domain.wish import Destination, WishStatus

USER_ID = UUID("00000000-0000-0000-0000-000000000001")
NOW = datetime(2026, 10, 18, 9, 0, tzinfo=UTC)


class FixedClock:
    def now(self) -> datetime:
        return NOW


LISBON = Destination("Portugal", "Lisbon")
PORTO = Destination("Portugal", "Porto")
MARRAKECH = Destination("Morocco", "Marrakech")
ATHENS = Destination("Greece", "Athens")
ROME = Destination("Italy", "Rome")
MADRID = Destination("Spain", "Madrid")
COVERED = [LISBON, PORTO, MARRAKECH, ATHENS, ROME]
LISBON_TAGS = ["style:beach", "style:city", "food:seafood"]


class FakeCatalog:
    def __init__(self, covered, tags) -> None:
        self.covered = covered
        self.tags = tags
        self.tags_asked: list[Destination] = []
        self.calls = 0

    async def covered_destinations(self) -> list[Destination]:
        self.calls += 1
        return list(self.covered)

    async def tags_at(self, destination: Destination) -> list[str]:
        self.calls += 1
        self.tags_asked.append(destination)
        return list(self.tags)


class FakeReader:
    def __init__(self, reading: DestinationReading) -> None:
        self.reading = reading
        self.calls: list[tuple[str, list[Destination]]] = []

    async def read(self, text, covered) -> DestinationReading:
        self.calls.append((text, list(covered)))
        return self.reading


class FakeWishes:
    def __init__(self, events: list[str]) -> None:
        self.events = events
        self.added = []

    async def add(self, wish) -> None:
        self.events.append("add")
        self.added.append(wish)


class FakeUnitOfWork:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    async def commit(self) -> None:
        self.events.append("commit")


class Setup:
    def __init__(self, reading: DestinationReading, covered=COVERED, tags=LISBON_TAGS) -> None:
        self.events: list[str] = []
        self.wishes = FakeWishes(self.events)
        self.catalog = FakeCatalog(covered, tags)
        self.reader = FakeReader(reading)
        self.uow = FakeUnitOfWork(self.events)
        self.send_wish = SendWish(
            wishes=self.wishes,
            catalog=self.catalog,
            reader=self.reader,
            uow=self.uow,
            clock=FixedClock(),
        )


async def send(setup: Setup, text: str = "  A week in Lisbon  ") -> SendWishResult:
    return await setup.send_wish(SendWishCommand(user_id=USER_ID, text=text))


# Every case


async def test_wish_is_created_for_the_user_with_stripped_text_and_clock_time():
    setup = Setup(DestinationReading(destination=LISBON, suggestions=[]))

    result = await send(setup)

    assert result.wish.user_id == USER_ID
    assert result.wish.text == "A week in Lisbon"
    assert result.wish.created_at == NOW
    assert result.wish.updated_at == NOW


async def test_reader_gets_the_stripped_text_and_the_covered_destinations():
    setup = Setup(DestinationReading(destination=LISBON, suggestions=[]))

    await send(setup)

    assert setup.reader.calls == [("A week in Lisbon", COVERED)]


@pytest.mark.parametrize(
    "reading",
    [
        DestinationReading(destination=LISBON, suggestions=[]),
        DestinationReading(destination=MADRID, suggestions=[]),
        DestinationReading(destination=None, suggestions=[]),
    ],
    ids=["covered", "not_covered", "no_destination"],
)
async def test_wish_is_added_once_then_committed_once(reading):
    setup = Setup(reading)

    result = await send(setup)

    assert setup.events == ["add", "commit"]
    assert setup.wishes.added == [result.wish]


# Covered destination


async def test_covered_destination_shows_the_panel_of_its_tags():
    setup = Setup(DestinationReading(destination=LISBON, suggestions=[PORTO]))

    result = await send(setup)

    assert result.wish.status is WishStatus.PANEL_SHOWN
    assert result.wish.destination == LISBON
    assert result.wish.panel == Panel.from_tags(LISBON_TAGS)
    assert result.suggestions == []


async def test_covered_destination_uses_the_catalog_spelling():
    setup = Setup(
        DestinationReading(destination=Destination("portugal", " lisbon"), suggestions=[])
    )

    result = await send(setup)

    assert result.wish.destination == LISBON
    assert setup.catalog.tags_asked == [LISBON]


async def test_covered_country_keeps_no_city_in_the_catalog_spelling():
    setup = Setup(DestinationReading(destination=Destination("PORTUGAL"), suggestions=[]))

    result = await send(setup)

    assert result.wish.destination == Destination("Portugal")
    assert setup.catalog.tags_asked == [Destination("Portugal")]


async def test_covered_country_without_city_shows_the_panel():
    portugal = Destination("Portugal")
    setup = Setup(DestinationReading(destination=portugal, suggestions=[]))

    result = await send(setup)

    assert result.wish.status is WishStatus.PANEL_SHOWN
    assert result.wish.destination == portugal
    assert setup.catalog.tags_asked == [portugal]


# Destination not covered


async def test_uncovered_destination_marks_the_wish_not_covered():
    setup = Setup(DestinationReading(destination=MADRID, suggestions=[LISBON]))

    result = await send(setup)

    assert result.wish.status is WishStatus.NOT_COVERED
    assert result.wish.destination == MADRID
    assert result.wish.panel is None
    assert setup.catalog.tags_asked == []


async def test_uncovered_destination_suggests_the_covered_reader_suggestions():
    setup = Setup(DestinationReading(destination=MADRID, suggestions=[PORTO, ROME]))

    result = await send(setup)

    assert result.suggestions == [PORTO, ROME]


async def test_suggestions_drop_uncovered_ones_and_use_the_covered_spelling():
    suggestions = [Destination("spain", "barcelona"), Destination(" portugal", "PORTO ")]
    setup = Setup(DestinationReading(destination=MADRID, suggestions=suggestions))

    result = await send(setup)

    assert result.suggestions == [PORTO]


async def test_suggestions_are_deduplicated():
    suggestions = [PORTO, Destination("portugal", "porto"), MARRAKECH]
    setup = Setup(DestinationReading(destination=MADRID, suggestions=suggestions))

    result = await send(setup)

    assert result.suggestions == [PORTO, MARRAKECH]


async def test_suggestions_are_capped_at_three():
    suggestions = [ROME, ATHENS, MARRAKECH, PORTO]
    setup = Setup(DestinationReading(destination=MADRID, suggestions=suggestions))

    result = await send(setup)

    assert result.suggestions == [ROME, ATHENS, MARRAKECH]


async def test_suggestion_without_city_is_replaced_by_the_covered_destination():
    setup = Setup(DestinationReading(destination=MADRID, suggestions=[Destination("Morocco")]))

    result = await send(setup)

    assert result.suggestions == [MARRAKECH]


async def test_no_covered_suggestion_falls_back_to_the_first_three_covered():
    suggestions = [Destination("Spain", "Barcelona")]
    setup = Setup(DestinationReading(destination=MADRID, suggestions=suggestions))

    result = await send(setup)

    assert result.suggestions == [LISBON, PORTO, MARRAKECH]


async def test_no_suggestion_at_all_falls_back_to_the_first_three_covered():
    setup = Setup(DestinationReading(destination=MADRID, suggestions=[]))

    result = await send(setup)

    assert result.suggestions == [LISBON, PORTO, MARRAKECH]


# No destination


async def test_no_destination_keeps_a_draft_and_suggests_every_covered_destination():
    setup = Setup(DestinationReading(destination=None, suggestions=[PORTO]))

    result = await send(setup, "Somewhere warm")

    assert result.wish.status is WishStatus.DRAFT
    assert result.wish.destination is None
    assert result.wish.panel is None
    assert result.suggestions == COVERED
    assert setup.catalog.tags_asked == []


# Blank text


@pytest.mark.parametrize("text", ["", "   "])
async def test_blank_text_raises_before_reading_and_saves_nothing(text):
    setup = Setup(DestinationReading(destination=LISBON, suggestions=[]))

    with pytest.raises(InvalidWish):
        await send(setup, text)

    assert setup.reader.calls == []
    assert setup.catalog.calls == 0
    assert setup.events == []
