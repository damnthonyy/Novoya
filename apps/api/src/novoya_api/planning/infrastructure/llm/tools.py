"""The travel tools: the model's only way to read the catalog (#20).

The model chooses the arguments, so every handler validates them and raises ToolError with a
message the model can act on. The model and its provider are third parties: offers go out
without partner name or contact.
"""

from collections.abc import Awaitable, Callable
from datetime import date
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError

from novoya_api.catalog.public import covered_destinations as catalog_destinations
from novoya_api.catalog.public import search_offers as catalog_search
from novoya_api.shared.infrastructure.llm.errors import ToolError
from novoya_api.shared.infrastructure.llm.orchestrator import Tool

MAX_OFFERS = 20  # keeps the tool result, and so the next prompt, small

CoveredDestinations = Callable[[], Awaitable[list[tuple[str, str]]]]
SearchOffers = Callable[..., Awaitable[list[Any]]]

COVERED_DESTINATIONS = {
    "name": "covered_destinations",
    "description": (
        "List the destinations where Novoya has partners, as country and city. Novoya can "
        "only plan trips there. Use these exact names when you call search_offers."
    ),
    "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
}

SEARCH_OFFERS = {
    "name": "search_offers",
    "description": (
        "Find the partner offers (hotels, guides, transport, activities) at a covered "
        "destination that fit the group size and the whole trip. Offers matching more tags "
        "come first, then featured ones. Offers have no price. Only use offers returned here, "
        f"by their offer_id. At most {MAX_OFFERS} offers are returned."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "country": {"type": "string", "description": "Country, as in covered_destinations"},
            "city": {
                "type": ["string", "null"],
                "description": "City, as in covered_destinations. Null for the whole country",
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    'Tags the traveller picked, as "section:tag" (for example "style:beach"). '
                    "An offer needs at least one. Empty for no preference"
                ),
            },
            "persons": {"type": "integer", "minimum": 1, "description": "Number of travellers"},
            "start_date": {"type": "string", "format": "date", "description": "YYYY-MM-DD"},
            "end_date": {"type": "string", "format": "date", "description": "YYYY-MM-DD"},
        },
        "required": ["country", "persons", "start_date", "end_date"],
        "additionalProperties": False,
    },
}

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class _SearchArguments(BaseModel):
    """What search_offers accepts. Keep it in line with SEARCH_OFFERS["parameters"]."""

    model_config = ConfigDict(extra="forbid")

    country: Name
    city: Name | None = None
    tags: list[Annotated[str, StringConstraints(max_length=100)]] = Field(default=[], max_length=50)
    persons: int = Field(ge=1, le=100)
    start_date: date
    end_date: date


def travel_tools(
    covered_destinations: CoveredDestinations = catalog_destinations,
    search_offers: SearchOffers = catalog_search,
) -> list[Tool]:
    """covered_destinations and search_offers, reading the catalog through catalog.public."""

    async def list_covered() -> dict[str, Any]:
        covered = await covered_destinations()
        return {"destinations": [{"country": c, "city": city} for c, city in covered]}

    async def search(**arguments: Any) -> dict[str, Any]:
        query = _parse_search(arguments)
        if not _is_covered(query.country, query.city, await covered_destinations()):
            raise ToolError(
                "Novoya has no partner at this destination. "
                "Call covered_destinations and use one of its destinations."
            )
        offers = await search_offers(
            query.country, query.city, query.tags, query.persons, query.start_date, query.end_date
        )
        return {"offers": [_offer_for_model(offer) for offer in offers[:MAX_OFFERS]]}

    return [
        Tool(**COVERED_DESTINATIONS, handler=list_covered),
        Tool(**SEARCH_OFFERS, handler=search),
    ]


def _parse_search(arguments: dict[str, Any]) -> _SearchArguments:
    try:
        query = _SearchArguments.model_validate(arguments)
    except ValidationError as error:
        # Only field names and pydantic's messages: the model's own input is not echoed back.
        problems = "; ".join(
            f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}"
            for item in error.errors(include_input=False, include_url=False)
        )
        raise ToolError(f"invalid arguments: {problems}") from error
    if query.start_date > query.end_date:
        raise ToolError("start_date must be on or before end_date")
    return query


def _is_covered(country: str, city: str | None, covered: list[tuple[str, str]]) -> bool:
    return any(
        country.lower() == c.lower() and (city is None or city.lower() == place.lower())
        for c, place in covered
    )


def _offer_for_model(offer: Any) -> dict[str, Any]:
    return {
        "offer_id": str(offer.id),
        "kind": str(offer.kind),
        "title": offer.title,
        "description": offer.description,
        "country": offer.country,
        "city": offer.city,
        "min_persons": offer.min_persons,
        "max_persons": offer.max_persons,
        "tags": list(offer.tags),
        "featured": offer.featured,
    }
