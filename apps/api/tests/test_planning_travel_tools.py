"""The travel tools the plan generator gives the model, with a fake catalog: no database."""

import json
from datetime import date
from types import SimpleNamespace
from uuid import uuid4

import pytest

from novoya_api.catalog.domain import OfferKind
from novoya_api.planning.infrastructure.llm.tools import (
    MAX_OFFERS,
    SEARCH_OFFERS,
    _SearchArguments,
    travel_tools,
)
from novoya_api.shared.infrastructure.llm.errors import ToolError
from novoya_api.shared.infrastructure.llm.orchestrator import Orchestrator
from tests.test_llm_orchestrator import FakeClient, answer, tool_calls

COVERED = [("Greece", "Chania"), ("Morocco", "Marrakech")]


def offer_view(**overrides):
    values = {
        "id": uuid4(),
        "kind": OfferKind.HOTEL,
        "title": "Sea-view room",
        "description": "Calm week by the water.",
        "country": "Greece",
        "city": "Chania",
        "min_persons": 1,
        "max_persons": 3,
        "tags": ("style:beach", "rhythm:calm"),
        "featured": True,
        "partner_name": "Elounda Bay House",
        "partner_contact_email": "stay@elounda.example",
        "partner_contact_phone": "+30 28210 00001",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class FakeCatalog:
    def __init__(self, offers=()) -> None:
        self.offers = list(offers)
        self.searches: list[tuple] = []

    async def covered_destinations(self):
        return list(COVERED)

    async def search_offers(self, country, city, tags, persons, start, end):
        self.searches.append((country, city, tags, persons, start, end))
        return list(self.offers)


def tools_by_name(catalog: FakeCatalog):
    tools = travel_tools(
        covered_destinations=catalog.covered_destinations,
        search_offers=catalog.search_offers,
    )
    return {tool.name: tool for tool in tools}


SEARCH = {
    "country": "Greece",
    "city": "Chania",
    "tags": ["style:beach"],
    "persons": 2,
    "start_date": "2026-05-10",
    "end_date": "2026-05-17",
}


# Definitions


def test_there_are_two_tools_with_function_definitions():
    tools = tools_by_name(FakeCatalog())
    assert set(tools) == {"covered_destinations", "search_offers"}
    for tool in tools.values():
        definition = tool.definition()
        assert definition["type"] == "function"
        assert definition["function"]["name"] == tool.name
        assert definition["function"]["description"]
        assert definition["function"]["parameters"]["type"] == "object"
        json.dumps(definition)  # sent as JSON to OpenRouter


def test_covered_destinations_takes_no_argument():
    parameters = tools_by_name(FakeCatalog())["covered_destinations"].parameters
    assert parameters["properties"] == {}
    assert parameters["additionalProperties"] is False


def test_search_offers_schema_lists_every_argument_and_no_budget():
    parameters = tools_by_name(FakeCatalog())["search_offers"].parameters
    assert set(parameters["properties"]) == {
        "country",
        "city",
        "tags",
        "persons",
        "start_date",
        "end_date",
    }
    assert set(parameters["required"]) == {"country", "persons", "start_date", "end_date"}
    assert parameters["additionalProperties"] is False
    assert parameters["properties"]["tags"]["items"] == {"type": "string"}
    assert parameters["properties"]["persons"]["minimum"] == 1
    assert parameters["properties"]["start_date"]["format"] == "date"


def test_search_offers_schema_and_validation_accept_the_same_arguments():
    parameters = SEARCH_OFFERS["parameters"]
    assert set(parameters["properties"]) == set(_SearchArguments.model_fields)
    required = {
        name for name, field in _SearchArguments.model_fields.items() if field.is_required()
    }
    assert set(parameters["required"]) == required


# covered_destinations


async def test_covered_destinations_returns_country_and_city():
    result = await tools_by_name(FakeCatalog())["covered_destinations"].handler()
    assert result == {
        "destinations": [
            {"country": "Greece", "city": "Chania"},
            {"country": "Morocco", "city": "Marrakech"},
        ]
    }


# search_offers


async def test_search_offers_passes_typed_arguments_to_the_catalog():
    catalog = FakeCatalog()
    await tools_by_name(catalog)["search_offers"].handler(**SEARCH)
    assert catalog.searches == [
        ("Greece", "Chania", ["style:beach"], 2, date(2026, 5, 10), date(2026, 5, 17))
    ]


async def test_search_offers_city_and_tags_are_optional():
    catalog = FakeCatalog()
    arguments = {key: SEARCH[key] for key in ("country", "persons", "start_date", "end_date")}
    await tools_by_name(catalog)["search_offers"].handler(**arguments)
    assert catalog.searches[0][:3] == ("Greece", None, [])


async def test_search_offers_never_sends_partner_name_or_contact_to_the_model():
    stay = offer_view()
    result = await tools_by_name(FakeCatalog([stay]))["search_offers"].handler(**SEARCH)
    assert result == {
        "offers": [
            {
                "offer_id": str(stay.id),
                "kind": "hotel",
                "title": "Sea-view room",
                "description": "Calm week by the water.",
                "country": "Greece",
                "city": "Chania",
                "min_persons": 1,
                "max_persons": 3,
                "tags": ["style:beach", "rhythm:calm"],
                "featured": True,
            }
        ]
    }
    assert "Elounda" not in json.dumps(result)
    assert "example" not in json.dumps(result)


async def test_search_offers_returns_at_most_max_offers_best_first():
    offers = [offer_view(title=f"Offer {n}") for n in range(MAX_OFFERS + 5)]
    result = await tools_by_name(FakeCatalog(offers))["search_offers"].handler(**SEARCH)
    assert [item["title"] for item in result["offers"]] == [f"Offer {n}" for n in range(MAX_OFFERS)]


async def test_search_offers_outside_the_covered_destinations_tells_the_model_to_check():
    catalog = FakeCatalog()
    with pytest.raises(ToolError, match="covered_destinations"):
        await tools_by_name(catalog)["search_offers"].handler(
            **{**SEARCH, "country": "Japan", "city": "Kyoto"}
        )
    assert catalog.searches == []


async def test_search_offers_accepts_a_covered_country_without_city_ignoring_case():
    catalog = FakeCatalog()
    await tools_by_name(catalog)["search_offers"].handler(
        **{**SEARCH, "country": "morocco", "city": None}
    )
    assert catalog.searches[0][:2] == ("morocco", None)


@pytest.mark.parametrize(
    "change",
    [
        {"persons": 0},
        {"persons": "two"},
        {"start_date": "10/05/2026"},
        {"start_date": "2026-05-17", "end_date": "2026-05-10"},
        {"tags": "style:beach"},
        {"budget": 2000},
        {"country": ""},
    ],
)
async def test_search_offers_rejects_bad_arguments_with_a_message_for_the_model(change):
    catalog = FakeCatalog()
    with pytest.raises(ToolError):
        await tools_by_name(catalog)["search_offers"].handler(**{**SEARCH, **change})
    assert catalog.searches == []


# With the orchestrator


async def test_the_orchestrator_runs_search_offers_and_sends_the_offers_back():
    stay = offer_view()
    client = FakeClient(
        tool_calls(("call-1", "search_offers", json.dumps(SEARCH))),
        answer("Day 1: sea-view room."),
    )
    orchestrator = Orchestrator(client, ["model-a"])
    tools = list(tools_by_name(FakeCatalog([stay])).values())

    text = await orchestrator.run([{"role": "user", "content": "A calm week in Chania"}], tools)

    assert text == "Day 1: sea-view room."
    first, second = client.completions.calls
    assert {tool["function"]["name"] for tool in first["tools"]} == {
        "covered_destinations",
        "search_offers",
    }
    tool_message = second["messages"][-1]
    assert tool_message["role"] == "tool"
    assert json.loads(tool_message["content"])["offers"][0]["offer_id"] == str(stay.id)
