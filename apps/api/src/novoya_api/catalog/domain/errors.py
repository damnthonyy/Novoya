from novoya_api.shared.domain.errors import InvalidInput, NotFound


class InvalidPartner(InvalidInput):
    """A partner field is empty or not a usable contact email."""

    code = "invalid_partner"


class PartnerNotFound(NotFound):
    code = "partner_not_found"


class OfferNotFound(NotFound):
    code = "offer_not_found"
