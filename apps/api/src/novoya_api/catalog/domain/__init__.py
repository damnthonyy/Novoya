"""Domain: Partner, Offer (tags, person limits, availability, featured, active, no price).
Pure Python.

Rules: inactive partners hide their offers; an offer fits a group size and dates or not.
"""

from novoya_api.catalog.domain.kinds import OfferKind, PartnerKind
from novoya_api.catalog.domain.offer import InvalidOffer, Offer
from novoya_api.catalog.domain.partner import Partner

__all__ = [
    "InvalidOffer",
    "Offer",
    "OfferKind",
    "Partner",
    "PartnerKind",
]
