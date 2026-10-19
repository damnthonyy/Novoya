"""GET /plans/{id} is tested with GetPlan on fakes: no database."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient

from novoya_api.accounts.application.dto import CurrentUserView
from novoya_api.accounts.domain.role import Role
from novoya_api.accounts.domain.value_objects import Email, UserId
from novoya_api.accounts.public import current_user
from novoya_api.main import create_app
from novoya_api.planning.application.dto import OfferSummary
from novoya_api.planning.application.use_cases.get_plan import GetPlan
from novoya_api.planning.domain.plan import DraftItem, Plan
from novoya_api.planning.presentation.http.dependencies import get_current_user_id, get_get_plan
from novoya_api.shared.domain.value_objects import Locale

USER_ID = UUID("00000000-0000-0000-0000-000000000001")
OTHER_ID = UUID("00000000-0000-0000-0000-000000000002")
WISH_ID = UUID("00000000-0000-0000-0000-0000000000a1")
NOW = datetime(2026, 10, 19, 9, 0, tzinfo=UTC)
HOTEL_ID = UUID("00000000-0000-0000-0000-0000000000b1")
HOTEL = OfferSummary(HOTEL_ID, "hotel", "Sea view hotel", "Rooms over the bay", (), False)


class FakePlans:
    def __init__(self, plan: Plan) -> None:
        self.plan = plan

    async def get(self, plan_id: UUID) -> Plan | None:
        return self.plan if self.plan.id == plan_id else None


class FakeCatalog:
    async def summaries_for(self, offer_ids: list[UUID]) -> list[OfferSummary]:
        return [HOTEL] if HOTEL_ID in offer_ids else []


class FakeWishes:
    async def owner_id(self, wish_id: UUID) -> UUID | None:
        return USER_ID if wish_id == WISH_ID else None


def signed_in_as(role: Role, user_id: UUID = USER_ID) -> CurrentUserView:
    return CurrentUserView(
        user_id=UserId(user_id),
        email=Email("someone@example.com"),
        name=None,
        role=role,
        locale=Locale.EN,
        session_id=user_id,
    )


@pytest.fixture
def plan() -> Plan:
    return Plan.propose(
        WISH_ID, True, "A week by the sea", [DraftItem(HOTEL_ID, 1, 2, None)], 3, NOW
    )


@pytest.fixture
def app(plan):
    app = create_app()
    app.dependency_overrides[get_get_plan] = lambda: GetPlan(
        FakePlans(plan), FakeCatalog(), FakeWishes()
    )
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    return app


@pytest.fixture
async def client(app) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_the_owner_reads_the_plan(plan, client):
    response = await client.get(f"/plans/{plan.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(plan.id)
    assert body["wish_id"] == str(WISH_ID)
    assert body["status"] == "proposed"
    assert body["based_on_preferences"] is True
    assert body["summary"] == "A week by the sea"
    assert body["items"][0]["title"] == "Sea view hotel"
    assert "negotiated_price" not in body["items"][0]
    assert "partner_name" not in body
    assert "partner_name" not in body["items"][0]


async def test_without_a_session_returns_401(plan):
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.get(f"/plans/{plan.id}")).status_code == 401


async def test_an_agent_gets_403(app, plan, client):
    del app.dependency_overrides[get_current_user_id]
    app.dependency_overrides[current_user] = lambda: signed_in_as(Role.AGENT)

    assert (await client.get(f"/plans/{plan.id}")).status_code == 403


async def test_another_client_gets_404(app, plan, client):
    app.dependency_overrides[get_current_user_id] = lambda: OTHER_ID

    response = await client.get(f"/plans/{plan.id}")

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


async def test_an_unknown_plan_gets_404(client):
    response = await client.get(f"/plans/{UUID('00000000-0000-0000-0000-0000000000ff')}")

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_get_plan_documents_the_shared_error_responses(app):
    spec = app.openapi()
    responses = spec["paths"]["/plans/{plan_id}"]["get"]["responses"]
    created = responses["200"]["content"]["application/json"]["schema"]["$ref"]
    assert created == "#/components/schemas/Plan"
    for status in ("401", "403", "404"):
        ref = responses[status]["content"]["application/json"]["schema"]["$ref"]
        assert ref == "#/components/schemas/ErrorResponse", status
    assert spec["paths"]["/plans/{plan_id}"]["get"]["operationId"] == "getPlan"
    answers = spec["paths"]["/wishes/{wish_id}/answers"]["post"]["responses"]["201"]
    assert answers["content"]["application/json"]["schema"]["$ref"] == (
        "#/components/schemas/PlanResponse"
    )
