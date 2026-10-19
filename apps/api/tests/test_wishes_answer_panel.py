"""AnswerPanel is tested with fake ports: an in-memory repository and unit of work."""

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from novoya_api.shared.domain.errors import InvalidTransition, NotFound
from novoya_api.wishes.application.use_cases.answer_panel import AnswerPanel, AnswerPanelCommand
from novoya_api.wishes.domain.answers import Answers, SelectedTag
from novoya_api.wishes.domain.errors import InvalidAnswers, WishNotFound
from novoya_api.wishes.domain.panel import Panel
from novoya_api.wishes.domain.wish import Destination, Wish, WishStatus

OWNER = UUID("00000000-0000-0000-0000-000000000001")
OTHER = UUID("00000000-0000-0000-0000-000000000002")
CREATED = datetime(2026, 10, 19, 9, 0, tzinfo=UTC)
NOW = datetime(2026, 10, 19, 9, 5, tzinfo=UTC)
PANEL = Panel.from_tags(["style:beach", "style:city"])
ANSWERS = Answers(
    selected_tags=(SelectedTag("style", "beach"),),
    budget_max=Decimal("1500"),
    currency="EUR",
    persons=2,
    start_date=date(2026, 11, 2),
    end_date=date(2026, 11, 9),
)


class FixedClock:
    def now(self) -> datetime:
        return NOW


class FakeWishes:
    def __init__(self, events: list[str], wishes: list[Wish]) -> None:
        self.events = events
        self.by_id = {wish.id: wish for wish in wishes}
        self.saved: list[Wish] = []

    async def get(self, wish_id: UUID) -> Wish | None:
        return self.by_id.get(wish_id)

    async def save(self, wish: Wish) -> None:
        self.events.append("save")
        self.saved.append(wish)


class FakeUnitOfWork:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    async def commit(self) -> None:
        self.events.append("commit")


class Setup:
    def __init__(self, *wishes: Wish) -> None:
        self.events: list[str] = []
        self.wishes = FakeWishes(self.events, list(wishes))
        self.answer_panel = AnswerPanel(
            wishes=self.wishes, uow=FakeUnitOfWork(self.events), clock=FixedClock()
        )

    async def answer(self, wish_id: UUID, user_id: UUID = OWNER, answers: Answers = ANSWERS):
        return await self.answer_panel(
            AnswerPanelCommand(user_id=user_id, wish_id=wish_id, answers=answers)
        )


def shown_wish() -> Wish:
    wish = Wish.create(OWNER, "A week in Lisbon", CREATED)
    wish.show_panel(Destination("Portugal", "Lisbon"), PANEL, CREATED)
    return wish


async def test_the_owner_answers_and_the_wish_is_saved_then_committed():
    wish = shown_wish()
    setup = Setup(wish)

    result = await setup.answer(wish.id)

    assert result is wish
    assert result.status is WishStatus.ANSWERED
    assert result.answers == ANSWERS
    assert result.updated_at == NOW
    assert setup.wishes.saved == [wish]
    assert setup.events == ["save", "commit"]


async def test_an_unknown_wish_raises_wish_not_found():
    setup = Setup(shown_wish())

    with pytest.raises(WishNotFound):
        await setup.answer(uuid4())
    assert setup.events == []


async def test_another_users_wish_raises_wish_not_found_and_is_left_untouched():
    wish = shown_wish()
    setup = Setup(wish)

    with pytest.raises(WishNotFound):
        await setup.answer(wish.id, user_id=OTHER)
    assert wish.status is WishStatus.PANEL_SHOWN
    assert setup.events == []


async def test_wish_not_found_is_a_404_not_found():
    assert issubclass(WishNotFound, NotFound)
    assert WishNotFound.code == "wish_not_found"


async def test_a_tag_not_in_the_panel_is_rejected_and_nothing_is_saved():
    wish = shown_wish()
    setup = Setup(wish)
    answers = Answers(
        selected_tags=(SelectedTag("style", "mountain"),),
        budget_max=Decimal("1500"),
        currency="EUR",
        persons=2,
        start_date=date(2026, 11, 2),
        end_date=date(2026, 11, 9),
    )

    with pytest.raises(InvalidAnswers):
        await setup.answer(wish.id, answers=answers)
    assert setup.events == []


async def test_answering_twice_raises_invalid_transition():
    wish = shown_wish()
    setup = Setup(wish)
    await setup.answer(wish.id)

    with pytest.raises(InvalidTransition):
        await setup.answer(wish.id)
    assert setup.events == ["save", "commit"]
