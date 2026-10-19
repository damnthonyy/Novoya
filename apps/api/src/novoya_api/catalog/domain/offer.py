import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from novoya_api.catalog.domain.kinds import OfferKind
from novoya_api.catalog.domain.partner import Partner
from novoya_api.shared.domain.errors import InvalidInput


class InvalidOffer(InvalidInput):
    """Person limits, dates or tags are inconsistent."""

    code = "invalid_offer"


@dataclass(frozen=True)
class Offer:
    """A partner product. No price: an agent negotiates that per trip."""

    id: UUID
    partner_id: UUID
    kind: OfferKind
    title: str
    description: str
    country: str
    city: str
    min_persons: int
    max_persons: int
    available_from: date
    available_to: date
    tags: tuple[str, ...]
    featured: bool
    active: bool

    def __post_init__(self) -> None:
        if self.min_persons < 1 or self.max_persons < self.min_persons:
            raise InvalidOffer("person limits must be at least 1 and min <= max")
        if self.available_from > self.available_to:
            raise InvalidOffer("available_from must be on or before available_to")
        for tag in self.tags:
            if not _is_catalog_tag(tag):
                raise InvalidOffer("tags must be section:tag")

    def is_listed_with(self, partner: Partner) -> bool:
        """Inactive partners hide their offers; inactive offers are unused."""
        if partner.id != self.partner_id:
            raise InvalidOffer("offer does not belong to this partner")
        return partner.lists_offers() and self.active

    def fits(self, persons: int, start: date, end: date) -> bool:
        """True when the group size and trip dates sit inside the offer's limits."""
        if start > end:
            return False
        if persons < self.min_persons or persons > self.max_persons:
            return False
        if start < self.available_from or end > self.available_to:
            return False
        return True


def normalize_tags(tags: Iterable[str]) -> tuple[str, ...]:
    """Lowercase section:tag, no duplicates. Empty tags are allowed."""
    kept: list[str] = []
    for raw in tags:
        tag = raw.strip().lower()
        if not tag:
            continue
        if not _is_catalog_tag(tag):
            raise InvalidOffer("tags must be section:tag")
        if tag not in kept:
            kept.append(tag)
    return tuple(kept)


# Same ids as the panel builder accepts (wishes/infrastructure/llm/panel_builder.py, Slug).
_ID = r"[a-z0-9]+(?:[_-][a-z0-9]+)*"
_CATALOG_TAG = re.compile(rf"{_ID}:{_ID}")


def _is_catalog_tag(tag: str) -> bool:
    return _CATALOG_TAG.fullmatch(tag) is not None
