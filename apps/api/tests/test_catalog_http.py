from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from novoya_api.catalog.presentation.http.dependencies import get_list_destinations
from novoya_api.main import create_app


class FakeListDestinations:
    def __init__(self, places: list[tuple[str, str]]) -> None:
        self.places = places

    async def __call__(self) -> list[tuple[str, str]]:
        return list(self.places)


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_destinations_returns_covered_places(app, client):
    app.dependency_overrides[get_list_destinations] = lambda: FakeListDestinations(
        [("France", "Biarritz"), ("Greece", "Chania"), ("Morocco", "Marrakech")]
    )
    response = await client.get("/destinations")
    assert response.status_code == 200
    assert response.json() == [
        {"country": "France", "city": "Biarritz"},
        {"country": "Greece", "city": "Chania"},
        {"country": "Morocco", "city": "Marrakech"},
    ]


async def test_destinations_can_be_empty(app, client):
    app.dependency_overrides[get_list_destinations] = lambda: FakeListDestinations([])
    response = await client.get("/destinations")
    assert response.status_code == 200
    assert response.json() == []


async def test_destinations_updates_when_coverage_changes(app, client):
    fake = FakeListDestinations([("Greece", "Chania"), ("Morocco", "Marrakech")])
    app.dependency_overrides[get_list_destinations] = lambda: fake

    first = await client.get("/destinations")
    assert [row["city"] for row in first.json()] == ["Chania", "Marrakech"]

    fake.places = [("Greece", "Chania")]
    second = await client.get("/destinations")
    assert second.json() == [{"country": "Greece", "city": "Chania"}]
