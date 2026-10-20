"""Agent quote-queue HTTP: ListQuoteQueue, TakePlan and SetItemPrice on fakes."""

from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient

from novoya_api.accounts.application.dto import CurrentUserView
from novoya_api.accounts.domain.role import Role
from novoya_api.accounts.domain.value_objects import Email, UserId
from novoya_api.accounts.public import current_user
from novoya_api.main import create_app
from novoya_api.planning.application.dto import OfferContact, TripBrief
from novoya_api.planning.application.use_cases.get_agent_plan import GetAgentPlan
from novoya_api.planning.application.use_cases.list_quote_queue import ListQuoteQueue
from novoya_api.planning.application.use_cases.set_item_price import SetItemPrice
from novoya_api.planning.application.use_cases.take_plan import TakePlan
from novoya_api.planning.domain.plan import DraftItem, Plan, PlanStatus
from novoya_api.planning.presentation.http.dependencies import (
    get_get_agent_plan,
    get_list_quote_queue,
    get_set_item_price,
    get_take_plan,
)
from novoya_api.shared.domain.value_objects import Locale

AGENT_ID = UUID("00000000-0000-0000-0000-0000000000aa")
OTHER_AGENT = UUID("00000000-0000-0000-0000-0000000000ab")
WISH_ID = UUID("00000000-0000-0000-0000-0000000000a1")
NOW = datetime(2026, 10, 19, 9, 0, tzinfo=UTC)
HOTEL_ID = UUID("00000000-0000-0000-0000-0000000000b1")
HOTEL = OfferContact(
    HOTEL_ID,
    "hotel",
    "Sea view hotel",
    "Rooms over the bay",
    "Elounda Bay House",
    "stay@elounda.example",
    "+30 28210 00001",
)
TRIP = TripBrief(
    WISH_ID,
    "A week in Chania",
    "Greece",
    "Chania",
    Decimal("1500.00"),
    "EUR",
    2,
    date(2026, 5, 10),
    date(2026, 5, 17),
)


class FakePlans:
    def __init__(self, plan: Plan) -> None:
        self.plan = plan

    async def get(self, plan_id: UUID) -> Plan | None:
        return self.plan if self.plan.id == plan_id else None

    async def list_by_status(self, status: PlanStatus) -> list[Plan]:
        return [self.plan] if self.plan.status is status else []

    async def save(self, plan: Plan) -> None:
        self.plan = plan


class FakeCatalog:
    async def contacts_for(self, offer_ids: list[UUID]) -> list[OfferContact]:
        return [HOTEL] if HOTEL_ID in offer_ids else []


class FakeTrips:
    async def for_wish_ids(self, wish_ids: list[UUID]) -> dict[UUID, TripBrief]:
        return {WISH_ID: TRIP} if WISH_ID in wish_ids else {}


class FakeUow:
    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


class FixedClock:
    def now(self) -> datetime:
        return NOW


def signed_in_as(role: Role, user_id: UUID = AGENT_ID) -> CurrentUserView:
    return CurrentUserView(
        user_id=UserId(user_id),
        email=Email("agent@example.com"),
        name=None,
        role=role,
        locale=Locale.EN,
        session_id=user_id,
    )


@pytest.fixture
def plan() -> Plan:
    plan = Plan.propose(
        WISH_ID, True, "A week by the sea", [DraftItem(HOTEL_ID, 1, 2, None)], 3, NOW
    )
    plan.request_quote(NOW)
    return plan


@pytest.fixture
def app(plan):
    plans, catalog, trips = FakePlans(plan), FakeCatalog(), FakeTrips()
    app = create_app()
    app.dependency_overrides[get_list_quote_queue] = lambda: ListQuoteQueue(plans, trips)
    app.dependency_overrides[get_take_plan] = lambda: TakePlan(
        plans, catalog, trips, FakeUow(), FixedClock()
    )
    app.dependency_overrides[get_get_agent_plan] = lambda: GetAgentPlan(plans, catalog, trips)
    app.dependency_overrides[get_set_item_price] = lambda: SetItemPrice(
        plans, catalog, trips, FakeUow(), FixedClock()
    )
    app.dependency_overrides[current_user] = lambda: signed_in_as(Role.AGENT)
    return app


@pytest.fixture
async def client(app) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_the_agent_lists_the_quote_queue(plan, client):
    response = await client.get("/agent/plans", params={"status": "requested"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == str(plan.id)
    assert body[0]["wish_text"] == "A week in Chania"
    assert body[0]["city"] == "Chania"
    assert body[0]["persons"] == 2
    assert "partner_name" not in body[0]
    assert "items" not in body[0]


async def test_the_agent_takes_a_requested_plan(plan, client):
    response = await client.post(f"/agent/plans/{plan.id}/take")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "negotiating"
    assert body["assigned_agent_id"] == str(AGENT_ID)
    assert body["items"][0]["partner_name"] == "Elounda Bay House"
    assert body["items"][0]["partner_contact_email"] == "stay@elounda.example"
    assert body["total"] == "0"
    assert body["over_budget"] is False
    assert body["budget_max"] == "1500.00"


async def test_taking_a_plan_twice_returns_409(plan, client):
    assert (await client.post(f"/agent/plans/{plan.id}/take")).status_code == 200
    response = await client.post(f"/agent/plans/{plan.id}/take")
    assert response.status_code == 409
    assert response.json()["code"] == "invalid_transition"


async def test_the_assigned_agent_sets_a_price(plan, client):
    await client.post(f"/agent/plans/{plan.id}/take")
    response = await client.patch(
        f"/agent/plans/{plan.id}/items/{plan.items[0].id}",
        json={"negotiated_price": "120.00"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["items"][0]["negotiated_price"] == "120.00"
    assert body["total"] == "120.00"
    assert body["over_budget"] is False


async def test_a_client_gets_403_on_agent_routes(plan):
    app = create_app()
    app.dependency_overrides[current_user] = lambda: signed_in_as(Role.CLIENT)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.get("/agent/plans")).status_code == 403
        assert (await client.post(f"/agent/plans/{plan.id}/take")).status_code == 403
        assert (
            await client.patch(
                f"/agent/plans/{plan.id}/items/{plan.items[0].id}",
                json={"negotiated_price": "10.00"},
            )
        ).status_code == 403


async def test_without_a_session_returns_401(plan):
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.get("/agent/plans")).status_code == 401
        assert (await client.post(f"/agent/plans/{plan.id}/take")).status_code == 401


async def test_another_agent_cannot_price_the_plan(app, plan, client):
    await client.post(f"/agent/plans/{plan.id}/take")
    app.dependency_overrides[current_user] = lambda: signed_in_as(Role.AGENT, OTHER_AGENT)

    response = await client.patch(
        f"/agent/plans/{plan.id}/items/{plan.items[0].id}",
        json={"negotiated_price": "10.00"},
    )

    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"


def test_agent_routes_are_documented(app):
    spec = app.openapi()
    queue = spec["paths"]["/agent/plans"]["get"]
    assert queue["operationId"] == "listQuoteQueue"
    take = spec["paths"]["/agent/plans/{plan_id}/take"]["post"]
    assert take["operationId"] == "takePlan"
    item = spec["paths"]["/agent/plans/{plan_id}/items/{item_id}"]["patch"]
    assert item["operationId"] == "setPlanItem"
    for status in ("401", "403", "404"):
        ref = queue["responses"][status]["content"]["application/json"]["schema"]["$ref"]
        assert ref == "#/components/schemas/ErrorResponse", status
    assert "409" in take["responses"]
    client_item = spec["components"]["schemas"]["PlanItemResponse"]["properties"]
    assert "negotiated_price" not in client_item
    assert "partner_name" not in client_item
    agent_item = spec["components"]["schemas"]["AgentPlanItem"]["properties"]
    assert "negotiated_price" in agent_item
    assert "partner_name" in agent_item
