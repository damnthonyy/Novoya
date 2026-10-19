from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from novoya_api.planning.application.use_cases.get_plan import GetPlan
from novoya_api.planning.presentation.http.dependencies import get_current_user_id, get_get_plan
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
    """The plan day by day. No prices until it is quoted, and never the partners' names.
    404 if it is missing or not the caller's, so the id stays hidden."""
    return Plan.of(await use_case(plan_id, reader_id))
