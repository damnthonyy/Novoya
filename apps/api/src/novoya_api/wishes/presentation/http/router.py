from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from novoya_api.shared.presentation.http.errors import ErrorResponse
from novoya_api.wishes.application.use_cases.answer_panel import AnswerPanel, AnswerPanelCommand
from novoya_api.wishes.application.use_cases.send_wish import SendWish, SendWishCommand
from novoya_api.wishes.presentation.http.dependencies import (
    get_answer_panel,
    get_current_user_id,
    get_send_wish,
)
from novoya_api.wishes.presentation.http.schemas import (
    AnswerPanelRequest,
    PlanResponse,
    SendWishRequest,
    WishResponse,
)

# Every error body is {code, detail} (shared handler), not FastAPI's default 422 list.
ERRORS = {status_code: {"model": ErrorResponse} for status_code in (401, 403, 422)}

router = APIRouter(prefix="/wishes", tags=["wishes"], responses=ERRORS)


@router.post("", operation_id="sendWish", status_code=status.HTTP_201_CREATED)
async def send_wish(
    body: SendWishRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    use_case: Annotated[SendWish, Depends(get_send_wish)],
) -> WishResponse:
    """Send the trip the client wants, in their words. Returns the panel when we cover the
    destination, suggestions when we don't, and asks where when the text names no place."""
    return WishResponse.of(await use_case(SendWishCommand(user_id=user_id, text=body.text)))


@router.post(
    "/{wish_id}/answers",
    operation_id="answerPanel",
    status_code=status.HTTP_201_CREATED,
    responses={status_code: {"model": ErrorResponse} for status_code in (404, 409)},
)
async def answer_panel(
    wish_id: UUID,
    body: AnswerPanelRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    use_case: Annotated[AnswerPanel, Depends(get_answer_panel)],
) -> PlanResponse:
    """Save the tags the client picked, their budget in EUR, travellers and dates, and return
    the proposed plan built from partner offers. 404 if the wish is not theirs; 409 if it is
    already answered, shows no panel or is being answered by another request; 422 for a tag
    the panel did not show, and 422 no_offer_fits when no offer fits the travellers and
    dates."""
    command = AnswerPanelCommand(user_id=user_id, wish_id=wish_id, answers=body.to_answers())
    return PlanResponse.of((await use_case(command)).plan)
