from typing import Annotated

from fastapi import APIRouter, Depends

from novoya_api.catalog.application.use_cases.list_destinations import ListDestinations
from novoya_api.catalog.presentation.http.dependencies import get_list_destinations
from novoya_api.catalog.presentation.http.schemas import DestinationResponse

router = APIRouter(tags=["catalog"])


@router.get("/destinations", operation_id="listDestinations")
async def list_destinations(
    use_case: Annotated[ListDestinations, Depends(get_list_destinations)],
) -> list[DestinationResponse]:
    """Countries and cities with at least one listed offer. Read from the database each time."""
    return [DestinationResponse(country=country, city=city) for country, city in await use_case()]
