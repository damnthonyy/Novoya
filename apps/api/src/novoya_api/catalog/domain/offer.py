from dataclasses import dataclass
from datetime import date
from uuid import UUID

from novoya_api.catalog.domain.kinds import OfferKind
from novoya_api.catalog.domain.partner import Partner
from novoya_api.shared.domain.errors import DomainError


class InvalidOffer(DomainError):
    """Person limits or availability dates are inconsistent."""


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
