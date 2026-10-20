from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from novoya_api.planning.application.use_cases.get_plan import GetPlan
from novoya_api.planning.application.use_cases.request_quote import RequestQuote
from novoya_api.planning.presentation.http.dependencies import (
    get_current_user_id,
    get_get_plan,
    get_request_quote,
)
from novoya_api.planning.presentation.http.schemas import Plan
from novoya_api.shared.presentation.http.errors import ErrorResponse

ERRORS = {status_code: {"model": ErrorResponse} for status_code in (401, 403, 404)}

router = APIRouter(prefix="/plans", tags=["planning"], responses=ERRORS)


@router.get("/{plan_id}", operation_id="getPlan")
async def get_plan(
    plan_id: UUID,
    reader_id: Annotated[UUID, Depends(get_current_user_id)],
    use_case: Annotated[GetPlan, Depends(get_get_plan)],
) -> Plan:
    """The plan day by day. Never a price: the quote has it. Never the partners' names.
    404 if it is missing or not the caller's, so the id stays hidden."""
    return Plan.of(await use_case(plan_id, reader_id))


@router.post(
    "/{plan_id}/request-quote",
    operation_id="requestQuote",
    responses={409: {"model": ErrorResponse}},
)
async def request_quote(
    plan_id: UUID,
    client_id: Annotated[UUID, Depends(get_current_user_id)],
    use_case: Annotated[RequestQuote, Depends(get_request_quote)],
) -> Plan:
    """Ask an agent to price this plan. proposed becomes requested. Never a price here.
    404 if it is missing or not the caller's. 409 if it is not proposed."""
    return Plan.of(await use_case(plan_id, client_id))
