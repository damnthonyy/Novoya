from dataclasses import dataclass
from uuid import UUID

from novoya_api.catalog.domain.errors import InvalidPartner
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
    contact_phone: str | None  # DÉTOUR partners have none: the agent writes to the email
    active: bool

    def __post_init__(self) -> None:
        if self.contact_phone is not None and not self.contact_phone.strip():
            object.__setattr__(self, "contact_phone", None)
        if not self.name.strip():
            raise InvalidPartner("name is empty")
        if not self.contact_email.strip() or "@" not in self.contact_email:
            raise InvalidPartner("contact email is invalid")

    def lists_offers(self) -> bool:
        return self.active


def normalize_place(name: str) -> str:
    """English Title Case so destinations stay one spelling (greece -> Greece)."""
    words = " ".join(name.split())
    if not words:
        raise InvalidPartner("place is empty")
    return words.title()  # same as the seed: Saint-Tropez, L'Isle-Sur-La-Sorgue
