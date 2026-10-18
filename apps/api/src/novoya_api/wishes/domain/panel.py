from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

DEFAULT_SECTION = "preferences"


@dataclass(frozen=True, slots=True)
class Tag:
    id: str
    label: str
    preselected: bool = False


@dataclass(frozen=True, slots=True)
class PanelSection:
    id: str
    title: str
    multi: bool
    tags: tuple[Tag, ...]


@dataclass(frozen=True, slots=True)
class Panel:
    """The preference panel: sections of tags to pick, then budget, travellers and dates.

    The frontend renders it from to_dict() and never needs to know which sections exist."""

    sections: tuple[PanelSection, ...]
    ask_budget: bool = True
    ask_persons: bool = True
    ask_dates: bool = True

    @classmethod
    def from_tags(cls, tags: Iterable[str]) -> "Panel":
        """The fallback panel, built from the tags of the offers at the destination.

        Tags are "section:tag" ("style:beach"); a tag without a section goes to
        "preferences"."""
        grouped: dict[str, list[str]] = {}
        for raw in tags:
            section, _, tag = raw.strip().lower().rpartition(":")
            section, tag = section.strip() or DEFAULT_SECTION, tag.strip()
            if tag and tag not in grouped.setdefault(section, []):
                grouped[section].append(tag)
        return cls(
            sections=tuple(
                PanelSection(
                    id=section,
                    title=_label(section),
                    multi=True,
                    tags=tuple(Tag(id=tag, label=_label(tag)) for tag in section_tags),
                )
                for section, section_tags in grouped.items()
                if section_tags
            )
        )

    def to_dict(self) -> dict[str, Any]:
        """The JSON shape of ARCHITECTURE.md section 3."""
        return {
            "sections": [
                {
                    "id": section.id,
                    "title": section.title,
                    "multi": section.multi,
                    "tags": [
                        {"id": tag.id, "label": tag.label, "preselected": tag.preselected}
                        for tag in section.tags
                    ],
                }
                for section in self.sections
            ],
            "ask_budget": self.ask_budget,
            "ask_persons": self.ask_persons,
            "ask_dates": self.ask_dates,
        }


def _label(identifier: str) -> str:
    text = identifier.replace("_", " ").replace("-", " ")
    return text[:1].upper() + text[1:]
