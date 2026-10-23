from dataclasses import dataclass
from uuid import UUID

from novoya_api.shared.application.clock import Clock
from novoya_api.shared.application.unit_of_work import UnitOfWork
from novoya_api.wishes.application.ports.wish_repository import WishRepository


@dataclass(frozen=True)
class PreferenceTag:
    id: str
    label: str


@dataclass(frozen=True)
class PreferenceSection:
    """One panel section and the tags the client picked in it, across their wishes."""

    id: str
    title: str
    tags: tuple[PreferenceTag, ...]


class ListPreferences:
    """The tags the client picked on the panels of their own wishes, grouped by section.

    A tag picked on several wishes shows once. Sections and tags keep the order of the
    newest wish first; the titles and labels are the ones its panel showed."""

    def __init__(self, wishes: WishRepository) -> None:
        self._wishes = wishes

    async def __call__(self, user_id: UUID) -> list[PreferenceSection]:
        titles: dict[str, str] = {}
        tags: dict[str, dict[str, str]] = {}
        for wish in await self._wishes.list_for_user(user_id):
            if wish.answers is None:
                continue
            for selected in wish.answers.selected_tags:
                panel_section = wish.panel.section(selected.section) if wish.panel else None
                titles.setdefault(
                    selected.section,
                    panel_section.title if panel_section else _label(selected.section),
                )
                shown = panel_section.tags if panel_section else ()
                label = next((t.label for t in shown if t.id == selected.tag), None)
                tags.setdefault(selected.section, {}).setdefault(
                    selected.tag, label or _label(selected.tag)
                )
        return [
            PreferenceSection(
                section,
                titles[section],
                tuple(PreferenceTag(tag, label) for tag, label in section_tags.items()),
            )
            for section, section_tags in tags.items()
        ]


class RemovePreference:
    """Withdraw one preference: the tag leaves every wish of this client that has answers
    (answered or planned), in one transaction. Other clients' wishes are never read. Plans
    already built are not rebuilt. A tag the client does not have changes nothing."""

    def __init__(self, wishes: WishRepository, uow: UnitOfWork, clock: Clock) -> None:
        self._wishes = wishes
        self._uow = uow
        self._clock = clock

    async def __call__(self, user_id: UUID, section: str, tag: str) -> None:
        now = self._clock.now()
        changed = False
        for wish in await self._wishes.list_for_user(user_id):
            answers = wish.answers
            if answers is None or not any(
                t.section == section and t.tag == tag for t in answers.selected_tags
            ):
                continue
            wish.remove_tag(section, tag, now)
            await self._wishes.save(wish)
            changed = True
        if changed:
            await self._uow.commit()


def _label(identifier: str) -> str:
    text = identifier.replace("_", " ").replace("-", " ")
    return text[:1].upper() + text[1:]
