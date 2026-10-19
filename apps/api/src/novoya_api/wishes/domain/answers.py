from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from novoya_api.wishes.domain.errors import InvalidAnswers
from novoya_api.wishes.domain.panel import Panel

# The budget is in euros (#27): quotes are in EUR, so the agent compares like with like.
CURRENCY = "EUR"


@dataclass(frozen=True, slots=True)
class SelectedTag:
    """A tag the client clicked, stored as {"section": "style", "tag": "beach"}."""

    section: str
    tag: str


@dataclass(frozen=True, slots=True)
class Answers:
    """What the client chose on the panel: the tags, then budget, travellers and dates.

    No tags is a valid answer: the plan then starts from featured offers."""

    selected_tags: tuple[SelectedTag, ...]
    budget_max: Decimal
    currency: str
    persons: int
    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        if self.budget_max <= 0:
            raise InvalidAnswers("the budget must be more than 0")
        if self.currency != CURRENCY:
            raise InvalidAnswers(f"the budget must be in {CURRENCY}")
        if self.persons < 1:
            raise InvalidAnswers("at least 1 traveller is needed")
        if self.end_date <= self.start_date:
            raise InvalidAnswers("the end date must be after the start date")
        if len(set(self.selected_tags)) != len(self.selected_tags):
            raise InvalidAnswers("a tag is selected twice")

    def check_against(self, panel: Panel) -> None:
        """Every tag must come from the panel shown, at most one in a single-choice section."""
        picked: defaultdict[str, int] = defaultdict(int)
        for selected in self.selected_tags:
            section = panel.section(selected.section)
            if section is None or selected.tag not in {tag.id for tag in section.tags}:
                raise InvalidAnswers(f"{selected.section}:{selected.tag} was not in the panel")
            picked[section.id] += 1
            if not section.multi and picked[section.id] > 1:
                raise InvalidAnswers(f"only one tag can be picked in {section.id}")
