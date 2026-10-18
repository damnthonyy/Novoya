"""POST /wishes is tested with the use case built on fakes: no database, no model."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient

from novoya_api.accounts.domain.role import Role
from novoya_api.accounts.domain.value_objects import Email, UserId
from novoya_api.accounts.public import CurrentUserView, current_user
from novoya_api.main import create_app
from novoya_api.shared.domain.value_objects import Locale
from novoya_api.shared.infrastructure.llm.errors import LLMError
from novoya_api.wishes.application.ports.destination_reader import DestinationReading
from novoya_api.wishes.application.use_cases.send_wish import SendWish
from novoya_api.wishes.domain.wish import Destination
from novoya_api.wishes.infrastructure.catalog import StaticCatalog
from novoya_api.wishes.infrastructure.llm.destination_reader import NameMatchingReader
from novoya_api.wishes.presentation.http import dependencies
from novoya_api.wishes.presentation.http.dependencies import get_current_user_id, get_send_wish

USER_ID = UUID("00000000-0000-0000-0000-000000000001")
NOW = datetime(2026, 10, 18, 9, 0, tzinfo=UTC)


class FixedClock:
    def now(self) -> datetime:
        return NOW


LISBON = Destination("Portugal", "Lisbon")


class FakeReader:
    def __init__(self) -> None:
        self.reading = DestinationReading(destination=None, suggestions=[])

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


@pytest.fixture
def reader() -> FakeReader:
    return FakeReader()


@pytest.fixture
def wishes() -> FakeWishes:
    return FakeWishes()


@pytest.fixture
def app(reader, wishes):
    app = create_app()
    send_wish = SendWish(
        wishes=wishes,
        catalog=StaticCatalog(),
        reader=reader,
        uow=FakeUnitOfWork(),
        clock=FixedClock(),
    )
    app.dependency_overrides[get_send_wish] = lambda: send_wish
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    return app


@pytest.fixture
async def client(app) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_covered_wish_returns_201_with_the_panel(reader, wishes, client):
    reader.reading = DestinationReading(destination=LISBON, suggestions=[])

    response = await client.post("/wishes", json={"text": "A week in Lisbon"})

    assert response.status_code == 201
    body = response.json()
    assert UUID(body["id"]) == wishes.added[0].id
    assert body["status"] == "panel_shown"
    assert body["destination"] == {"country": "Portugal", "city": "Lisbon"}
    assert body["panel"] == wishes.added[0].panel.to_dict()
    assert body["panel"]["sections"]
    assert body["suggestions"] == []


async def test_wish_is_saved_for_the_current_user(reader, wishes, client):
    reader.reading = DestinationReading(destination=LISBON, suggestions=[])

    await client.post("/wishes", json={"text": "A week in Lisbon"})

    assert [wish.user_id for wish in wishes.added] == [USER_ID]


async def test_uncovered_wish_returns_201_with_suggestions_and_no_panel(reader, client):
    reader.reading = DestinationReading(
        destination=Destination("Spain", "Madrid"), suggestions=[LISBON]
    )

    response = await client.post("/wishes", json={"text": "A week in Madrid"})

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "not_covered"
    assert body["destination"] == {"country": "Spain", "city": "Madrid"}
    assert body["panel"] is None
    assert body["suggestions"] == [{"country": "Portugal", "city": "Lisbon"}]


async def test_wish_without_destination_returns_a_draft_and_every_covered_destination(client):
    covered = await StaticCatalog().covered_destinations()

    response = await client.post("/wishes", json={"text": "Somewhere warm"})

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "draft"
    assert body["destination"] is None
    assert body["panel"] is None
    assert body["suggestions"] == [{"country": d.country, "city": d.city} for d in covered]


async def test_text_of_1000_characters_is_accepted(client):
    response = await client.post("/wishes", json={"text": "a" * 1000})

    assert response.status_code == 201


@pytest.mark.parametrize(
    "text",
    ["", "   ", "a" * 1001, "Lisbon\u0000", "Lisbon\u0007 in May"],
    ids=["empty", "blank", "too_long", "nul", "control"],
)
async def test_invalid_text_returns_422(wishes, client, text):
    response = await client.post("/wishes", json={"text": text})

    assert response.status_code == 422
    assert wishes.added == []


async def test_missing_text_returns_422(client):
    response = await client.post("/wishes", json={})

    assert response.status_code == 422


async def test_without_a_signed_in_user_returns_401(app, wishes, client):
    del app.dependency_overrides[get_current_user_id]

    response = await client.post("/wishes", json={"text": "A week in Lisbon"})

    assert response.status_code == 401
    assert wishes.added == []


def test_send_wish_route_is_documented(app):
    operation = app.openapi()["paths"]["/wishes"]["post"]

    assert operation["operationId"] == "sendWish"
    assert operation["tags"] == ["wishes"]
    assert "201" in operation["responses"]


def test_without_an_api_key_the_reader_matches_names(monkeypatch):
    def no_key(**kwargs):
        raise LLMError("NOVOYA_OPENROUTER_API_KEY is not set")

    monkeypatch.setattr(dependencies, "get_orchestrator", no_key)

    assert isinstance(dependencies.get_destination_reader(), NameMatchingReader)


def signed_in_as(role: Role) -> CurrentUserView:
    return CurrentUserView(
        user_id=UserId(USER_ID),
        email=Email("someone@example.com"),
        name=None,
        role=role,
        locale=Locale.EN,
        session_id=USER_ID,
    )


@pytest.mark.parametrize(
    ("role", "status"), [(Role.CLIENT, 201), (Role.ADMIN, 201), (Role.AGENT, 403)]
)
async def test_only_clients_and_admins_send_wishes(app, wishes, client, role, status):
    del app.dependency_overrides[get_current_user_id]
    app.dependency_overrides[current_user] = lambda: signed_in_as(role)

    response = await client.post("/wishes", json={"text": "A week in Lisbon"})

    assert response.status_code == status
    assert [wish.user_id for wish in wishes.added] == ([USER_ID] if status == 201 else [])
