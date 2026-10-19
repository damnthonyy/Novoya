from novoya_api.shared.domain.errors import InvalidInput


class InvalidPlan(InvalidInput):  # 422
    """The plan breaks a rule, for example an item on a day outside the trip."""

    code = "invalid_plan"


class NoOfferFits(InvalidInput):  # 422
    """No listed offer fits the travellers and the dates: there is nothing to plan with."""

    code = "no_offer_fits"
