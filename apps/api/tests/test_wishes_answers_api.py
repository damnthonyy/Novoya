"""POST /wishes/{id}/answers is tested with the use case built on fakes: no database."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from novoya_api.accounts.domain.role import Role
from novoya_api.accounts.public import current_user
from novoya_api.main import create_app
from novoya_api.wishes.application.use_cases.answer_panel import AnswerPanel
from novoya_api.wishes.domain.panel import Panel, PanelSection, Tag
from novoya_api.wishes.domain.wish import Destination, Wish, WishStatus
from novoya_api.wishes.presentation.http.dependencies import get_answer_panel, get_current_user_id
from tests.test_wishes_api import signed_in_as

USER_ID = UUID("00000000-0000-0000-0000-000000000001")
OTHER_ID = UUID("00000000-0000-0000-0000-000000000002")
CREATED = datetime(2026, 10, 19, 9, 0, tzinfo=UTC)
NOW = datetime(2026, 10, 19, 9, 5, tzinfo=UTC)
PANEL = Panel(
    sections=(
        PanelSection("style", "Style", True, (Tag("beach", "Beach"), Tag("city", "City"))),
        PanelSection("rhythm", "Rhythm", False, (Tag("slow", "Slow"), Tag("busy", "Busy"))),
    )
)
BODY = {
    "selected_tags": [{"section": "style", "tag": "beach"}, {"section": "rhythm", "tag": "slow"}],
    "budget_max": "1500.50",
    "currency": "EUR",
    "persons": 2,
    "start_date": "2026-11-02",
    "end_date": "2026-11-09",
}


class FixedClock:
    def now(self) -> datetime:
        return NOW


class FakeWishes:
    def __init__(self) -> None:
        self.by_id: dict[UUID, Wish] = {}
        self.saved: list[Wish] = []

    def put(self, wish: Wish) -> Wish:
        self.by_id[wish.id] = wish
        return wish

    async def get(self, wish_id: UUID) -> Wish | None:
        return self.by_id.get(wish_id)

    async def save(self, wish: Wish) -> None:
        self.saved.append(wish)


class FakeUnitOfWork:
    async def commit(self) -> None:
        pass


def shown_wish(user_id: UUID = USER_ID) -> Wish:
    wish = Wish.create(user_id, "A week in Lisbon", CREATED)
    wish.show_panel(Destination("Portugal", "Lisbon"), PANEL, CREATED)
    return wish


@pytest.fixture
def wishes() -> FakeWishes:
    return FakeWishes()


@pytest.fixture
def app(wishes):
    app = create_app()
    use_case = AnswerPanel(wishes=wishes, uow=FakeUnitOfWork(), clock=FixedClock())
    app.dependency_overrides[get_answer_panel] = lambda: use_case
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    return app


@pytest.fixture
async def client(app) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def answer(client: AsyncClient, wish_id: UUID, **changes):
    return await client.post(f"/wishes/{wish_id}/answers", json=BODY | changes)


async def test_answers_are_saved_and_the_wish_is_returned_answered(wishes, client):
    wish = wishes.put(shown_wish())

    response = await answer(client, wish.id)

    assert response.status_code == 200
    assert response.json() == {
        "id": str(wish.id),
        "status": "answered",
        "destination": {"country": "Portugal", "city": "Lisbon"},
        "answers": BODY,
    }
    assert wishes.saved == [wish]
    assert wish.status is WishStatus.ANSWERED


async def test_no_tags_is_a_valid_answer(wishes, client):
    wish = wishes.put(shown_wish())

    response = await answer(client, wish.id, selected_tags=[])

    assert response.status_code == 200
    assert response.json()["answers"]["selected_tags"] == []


async def test_currency_defaults_to_eur(wishes, client):
    wish = wishes.put(shown_wish())
    body = {key: value for key, value in BODY.items() if key != "currency"}

    response = await client.post(f"/wishes/{wish.id}/answers", json=body)

    assert response.status_code == 200
    assert response.json()["answers"]["currency"] == "EUR"


@pytest.mark.parametrize(
    "selected_tags",
    [
        [{"section": "style", "tag": "mountain"}],
        [{"section": "food", "tag": "beach"}],
        [{"section": "rhythm", "tag": "slow"}, {"section": "rhythm", "tag": "busy"}],
    ],
    ids=["unknown tag", "unknown section", "two tags in a single-choice section"],
)
async def test_tags_not_allowed_by_the_panel_return_422_invalid_answers(
    wishes, client, selected_tags
):
    wish = wishes.put(shown_wish())

    response = await answer(client, wish.id, selected_tags=selected_tags)

    assert response.status_code == 422
    assert response.json()["code"] == "invalid_answers"
    assert wishes.saved == []
    assert wish.status is WishStatus.PANEL_SHOWN


async def test_end_date_before_start_date_returns_422_invalid_answers(wishes, client):
    wish = wishes.put(shown_wish())

    response = await answer(client, wish.id, end_date="2026-11-01")

    assert response.status_code == 422
    assert response.json()["code"] == "invalid_answers"


@pytest.mark.parametrize(
    "changes",
    [
        {"budget_max": "0"},
        {"budget_max": "-5"},
        {"budget_max": "12.345"},
        {"budget_max": "100000000"},
        {"currency": "USD"},
        {"persons": 0},
        {"persons": 51},
        {"start_date": "next monday"},
        {"selected_tags": [{"section": "", "tag": "beach"}]},
    ],
)
async def test_malformed_answers_return_422(wishes, client, changes):
    wish = wishes.put(shown_wish())

    response = await answer(client, wish.id, **changes)

    assert response.status_code == 422
    assert response.json()["code"] == "invalid_input"
    assert wishes.saved == []


async def test_another_users_wish_returns_404(wishes, client):
    wish = wishes.put(shown_wish(user_id=OTHER_ID))

    response = await answer(client, wish.id)

    assert response.status_code == 404
    assert response.json()["code"] == "wish_not_found"
    assert wish.status is WishStatus.PANEL_SHOWN


async def test_an_unknown_wish_returns_404(client):
    response = await answer(client, uuid4())

    assert response.status_code == 404
    assert response.json()["code"] == "wish_not_found"


async def test_answering_twice_returns_409(wishes, client):
    wish = wishes.put(shown_wish())
    await answer(client, wish.id)

    response = await answer(client, wish.id)

    assert response.status_code == 409
    assert response.json()["code"] == "invalid_transition"


async def test_a_wish_without_a_panel_returns_409(wishes, client):
    wish = wishes.put(Wish.create(USER_ID, "Somewhere warm", CREATED))

    response = await answer(client, wish.id)

    assert response.status_code == 409


async def test_without_a_signed_in_user_returns_401(app, wishes, client):
    del app.dependency_overrides[get_current_user_id]
    wish = wishes.put(shown_wish())

    response = await answer(client, wish.id)

    assert response.status_code == 401
    assert wishes.saved == []


@pytest.mark.parametrize(
    ("role", "status"), [(Role.CLIENT, 200), (Role.ADMIN, 200), (Role.AGENT, 403)]
)
async def test_only_clients_and_admins_answer(app, wishes, client, role, status):
    del app.dependency_overrides[get_current_user_id]
    app.dependency_overrides[current_user] = lambda: signed_in_as(role)
    wish = wishes.put(shown_wish())

    response = await answer(client, wish.id)

    assert response.status_code == status


def test_answer_panel_route_is_documented_with_the_shared_error_responses(app):
    operation = app.openapi()["paths"]["/wishes/{wish_id}/answers"]["post"]

    assert operation["operationId"] == "answerPanel"
    assert operation["tags"] == ["wishes"]
    assert "200" in operation["responses"]
    for status in ("401", "403", "404", "409", "422"):
        ref = operation["responses"][status]["content"]["application/json"]["schema"]["$ref"]
        assert ref == "#/components/schemas/ErrorResponse", status
