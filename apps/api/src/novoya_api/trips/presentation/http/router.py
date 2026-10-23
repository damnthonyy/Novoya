from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response

from novoya_api.shared.presentation.http.errors import ErrorResponse
from novoya_api.trips.application.use_cases.list_my_trips import ListMyTrips
from novoya_api.trips.presentation.http.dependencies import get_client_id, get_list_my_trips
from novoya_api.trips.presentation.http.schemas import Trip

ERRORS = {status_code: {"model": ErrorResponse} for status_code in (401, 403)}

router = APIRouter(prefix="/me", tags=["trips"], responses=ERRORS)


@router.get("/trips", operation_id="listMyTrips")
async def list_my_trips(
    client_id: Annotated[UUID, Depends(get_client_id)],
    use_case: Annotated[ListMyTrips, Depends(get_list_my_trips)],
    response: Response,
) -> list[Trip]:
    """The signed-in client's wishes, newest first, each with its status and the ids of its
    plan and its quote when they exist. Only their own wishes. 401 without a session, 403 for
    an agent."""
    trips = [Trip.of(view) for view in await use_case(client_id)]
    # Personal data: no shared or browser cache keeps it.
    response.headers["Cache-Control"] = "private, no-store"
    return trips
