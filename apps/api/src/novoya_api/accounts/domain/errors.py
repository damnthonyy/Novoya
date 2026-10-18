"""Errors of the accounts module. Each one extends a shared error, which sets its HTTP status."""

from novoya_api.shared.domain.errors import (
    Conflict,
    InvalidInput,
    NotFound,
    PermissionDenied,
    TooManyRequests,
    Unauthenticated,
)


class SessionInvalid(Unauthenticated):
    """No session cookie, or the session is expired, revoked or its account disabled."""

    code = "unauthenticated"


class InvalidCredentials(Unauthenticated):
    """Wrong email or password. Same error whether the email exists or not."""

    code = "invalid_credentials"


class NotAllowed(PermissionDenied):
    """The user's role may not use this route."""

    code = "forbidden"


class EmailNotVerified(PermissionDenied):
    code = "email_not_verified"


class AccountDisabled(PermissionDenied):
    code = "account_disabled"


class UserNotFound(NotFound):
    code = "user_not_found"


class EmailAlreadyUsed(Conflict):
    code = "email_already_used"


class CannotChangeOwnRole(Conflict):
    code = "cannot_change_own_role"


class LastAdminRequired(Conflict):
    """The last admin cannot lose the admin role: nobody could manage roles any more."""

    code = "last_admin_required"


class InvalidEmail(InvalidInput):
    code = "invalid_email"


class WeakPassword(InvalidInput):
    code = "weak_password"


class InvalidOrExpiredToken(InvalidInput):
    code = "invalid_token"


class NoPasswordSet(InvalidInput):
    """The account has no password, for example a Google-only account."""

    code = "no_password_set"


class TooManyAttempts(TooManyRequests):
    code = "too_many_attempts"
