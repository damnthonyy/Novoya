from dataclasses import dataclass
from uuid import UUID

from novoya_api.shared.application.clock import Clock
from novoya_api.shared.application.unit_of_work import UnitOfWork
from novoya_api.wishes.application.ports.wish_repository import WishRepository
from novoya_api.wishes.domain.answers import Answers
from novoya_api.wishes.domain.errors import WishNotFound
from novoya_api.wishes.domain.wish import Wish


@dataclass(frozen=True)
class AnswerPanelCommand:
    user_id: UUID
    wish_id: UUID
    answers: Answers


class AnswerPanel:
    """Save the client's panel answers on their wish, which becomes answered.

    Only the owner can answer; another user's wish is reported as not found, so its
    existence does not leak. The plan is built from the answered wish (#29)."""

    def __init__(self, wishes: WishRepository, uow: UnitOfWork, clock: Clock) -> None:
        self._wishes = wishes
        self._uow = uow
        self._clock = clock

    async def __call__(self, cmd: AnswerPanelCommand) -> Wish:
        wish = await self._wishes.get(cmd.wish_id)
        if wish is None or wish.user_id != cmd.user_id:
            raise WishNotFound("no such wish")
        wish.answer(cmd.answers, self._clock.now())
        await self._wishes.save(wish)
        await self._uow.commit()
        return wish
