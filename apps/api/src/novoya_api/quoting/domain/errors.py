from novoya_api.shared.domain.errors import InvalidInput, NotFound, Unavailable


class InvalidQuote(InvalidInput):  # 422
    """The quote breaks a rule, for example a total of 0."""

    code = "invalid_quote"


class QuoteNotFound(NotFound):  # 404
    """No quote with this id, or it is not the caller's. Same code so the id stays hidden."""


class QuoteEmailNotSent(Unavailable):  # 503
    """The email server did not take the quote email. The quote is saved; try again later."""

    code = "email_not_sent"
