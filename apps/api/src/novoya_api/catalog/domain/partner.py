from dataclasses import dataclass
from uuid import UUID

from novoya_api.catalog.domain.kinds import PartnerKind


@dataclass(frozen=True)
class Partner:
    """A prestataire. Inactive partners never contribute offers to a plan."""

    id: UUID
    name: str
    kind: PartnerKind
    country: str
    city: str
    contact_email: str
    contact_phone: str
    active: bool

    def lists_offers(self) -> bool:
        return self.active
