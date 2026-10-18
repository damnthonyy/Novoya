from novoya_api.shared.domain.errors import InvalidInput


class InvalidWish(InvalidInput):  # 422
    """The wish cannot be used, for example an empty text."""

    code = "invalid_wish"
