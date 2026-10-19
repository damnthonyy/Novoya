"""Domain: Partner, Offer (tags, person limits, availability, featured, active, no price).
Pure Python.

Rules: inactive partners hide their offers; an offer fits a group size and dates or not.
"""

from novoya_api.catalog.domain.errors import InvalidPartner, OfferNotFound, PartnerNotFound
from novoya_api.catalog.domain.kinds import OfferKind, PartnerKind
from novoya_api.catalog.domain.offer import InvalidOffer, Offer, normalize_tags
from novoya_api.catalog.domain.partner import Partner, normalize_place

__all__ = [
    "InvalidOffer",
    "InvalidPartner",
    "Offer",
    "OfferKind",
    "OfferNotFound",
    "Partner",
    "PartnerKind",
    "PartnerNotFound",
    "normalize_place",
    "normalize_tags",
]
