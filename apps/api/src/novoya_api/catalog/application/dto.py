from dataclasses import dataclass
from uuid import UUID

from novoya_api.catalog.domain import Offer, OfferKind, Partner


@dataclass(frozen=True, slots=True)
class OfferView:
    """A listed offer, as other modules see it. No price: an agent negotiates that per trip.

    It carries the partner's name and contact; other modules decide who may see them."""

    id: UUID
    kind: OfferKind
    title: str
    description: str
    country: str
    city: str
    min_persons: int
    max_persons: int
    tags: tuple[str, ...]
    featured: bool
    partner_name: str
    partner_contact_email: str
    partner_contact_phone: str

    @classmethod
    def of(cls, offer: Offer, partner: Partner) -> "OfferView":
        return cls(
            id=offer.id,
            kind=offer.kind,
            title=offer.title,
            description=offer.description,
            country=offer.country,
            city=offer.city,
            min_persons=offer.min_persons,
            max_persons=offer.max_persons,
            tags=offer.tags,
            featured=offer.featured,
            partner_name=partner.name,
            partner_contact_email=partner.contact_email,
            partner_contact_phone=partner.contact_phone,
        )
