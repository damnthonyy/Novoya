from datetime import date
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints

from novoya_api.wishes.application.use_cases.send_wish import SendWishResult
from novoya_api.wishes.domain.answers import Answers, SelectedTag
from novoya_api.wishes.domain.panel import Panel
from novoya_api.wishes.domain.wish import Destination, Wish


class SendWishRequest(BaseModel):
    # No control characters: PostgreSQL rejects NUL, and the rest is never part of a wish.
    text: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=1,
            max_length=1000,
            pattern=r"^[^\x00-\x08\x0b\x0c\x0e-\x1f\x7f]*$",
        ),
    ]


class DestinationOut(BaseModel):
    country: str
    city: str | None

    @classmethod
    def of(cls, destination: Destination) -> "DestinationOut":
        return cls(country=destination.country, city=destination.city)


class TagOut(BaseModel):
    id: str
    label: str
    preselected: bool


class PanelSectionOut(BaseModel):
    id: str
    title: str
    multi: bool
    tags: list[TagOut]


class PanelOut(BaseModel):
    """The preference panel (ARCHITECTURE.md section 3). Render it with generic components."""

    sections: list[PanelSectionOut]
    ask_budget: bool
    ask_persons: bool
    ask_dates: bool

    @classmethod
    def of(cls, panel: Panel) -> "PanelOut":
        return cls.model_validate(panel.to_dict())


class WishResponse(BaseModel):
    """panel_shown: show the panel. not_covered: we don't go there, offer the suggestions.
    draft: the text names no place, ask where, with the suggestions as choices."""

    id: UUID
    status: Literal["draft", "not_covered", "panel_shown"]
    destination: DestinationOut | None
    panel: PanelOut | None
    suggestions: list[DestinationOut]

    @classmethod
    def of(cls, result: SendWishResult) -> "WishResponse":
        wish = result.wish
        return cls(
            id=wish.id,
            status=wish.status.value,
            destination=DestinationOut.of(wish.destination) if wish.destination else None,
            panel=PanelOut.of(wish.panel) if wish.panel else None,
            suggestions=[DestinationOut.of(d) for d in result.suggestions],
        )


PanelId = Annotated[str, StringConstraints(min_length=1, max_length=100)]


class SelectedTagIn(BaseModel):
    """A tag of the panel, by the ids it was shown with."""

    section: PanelId
    tag: PanelId


class AnswerPanelRequest(BaseModel):
    """The panel answers. Every tag must come from the panel shown; no tags is allowed."""

    selected_tags: Annotated[list[SelectedTagIn], Field(max_length=100)]
    # Fits the budget_max column, NUMERIC(10, 2).
    budget_max: Annotated[Decimal, Field(gt=0, max_digits=10, decimal_places=2)]
    currency: Literal["EUR"] = "EUR"  # quotes are in euros (#27)
    persons: Annotated[int, Field(ge=1, le=50)]
    start_date: date
    end_date: date  # after start_date: checked by the domain, 422 invalid_answers

    def to_answers(self) -> Answers:
        return Answers(
            selected_tags=tuple(SelectedTag(t.section, t.tag) for t in self.selected_tags),
            budget_max=self.budget_max,
            currency=self.currency,
            persons=self.persons,
            start_date=self.start_date,
            end_date=self.end_date,
        )


class SelectedTagOut(BaseModel):
    section: str
    tag: str


class AnswersOut(BaseModel):
    selected_tags: list[SelectedTagOut]
    budget_max: Decimal
    currency: str
    persons: int
    start_date: date
    end_date: date

    @classmethod
    def of(cls, answers: Answers) -> "AnswersOut":
        return cls(
            selected_tags=[
                SelectedTagOut(section=t.section, tag=t.tag) for t in answers.selected_tags
            ],
            budget_max=answers.budget_max,
            currency=answers.currency,
            persons=answers.persons,
            start_date=answers.start_date,
            end_date=answers.end_date,
        )


# TEMPORARY until #29: ARCHITECTURE.md says POST /wishes/{id}/answers returns the proposed
# plan, but plan generation is #29. Until then the route returns the answered wish; #29
# replaces this response with the plan.
class AnsweredWishResponse(BaseModel):
    """The wish with the answers saved. The plan is built from it (#29)."""

    id: UUID
    status: Literal["answered"]
    destination: DestinationOut
    answers: AnswersOut

    @classmethod
    def of(cls, wish: Wish) -> "AnsweredWishResponse":
        assert wish.destination is not None and wish.answers is not None  # answered
        return cls(
            id=wish.id,
            status=wish.status.value,
            destination=DestinationOut.of(wish.destination),
            answers=AnswersOut.of(wish.answers),
        )
