from novoya_api.shared.domain.errors import InvalidInput


class InvalidWish(InvalidInput):  # 422
    """The wish cannot be used, for example an empty text."""

    code = "invalid_wish"


class InvalidAnswers(InvalidInput):  # 422
    """The panel answers break a rule, for example a tag the panel did not show."""

    code = "invalid_answers"
