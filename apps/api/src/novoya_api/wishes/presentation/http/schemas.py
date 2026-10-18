from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, StringConstraints

from novoya_api.wishes.application.use_cases.send_wish import SendWishResult
from novoya_api.wishes.domain.panel import Panel
from novoya_api.wishes.domain.wish import Destination


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
