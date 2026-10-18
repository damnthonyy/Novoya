from novoya_api.shared.domain.errors import DomainError


class InvalidWish(DomainError):
    """The wish cannot be used, for example an empty text."""
