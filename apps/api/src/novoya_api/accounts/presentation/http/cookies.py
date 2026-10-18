"""The session cookie: an opaque token, HttpOnly, SameSite=Lax.

In production (HTTPS) it is Secure and named with the __Host- prefix, which also forbids a
Domain attribute, so a subdomain cannot overwrite it. Locally (HTTP) it is plain.
"""

from fastapi import Request, Response

from novoya_api.accounts.domain.value_objects import SessionToken
from novoya_api.config import Settings


def cookie_name(settings: Settings) -> str:
    return "__Host-novoya_session" if settings.session_cookie_secure else "novoya_session"


def read_session_cookie(request: Request, settings: Settings) -> SessionToken | None:
    value = request.cookies.get(cookie_name(settings))
    return SessionToken(value) if value else None


def set_session_cookie(response: Response, token: SessionToken, settings: Settings) -> None:
    response.set_cookie(
        cookie_name(settings),
        token.value,
        max_age=settings.session_absolute_ttl_days * 24 * 3600,
        path="/",
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite="lax",
    )


def clear_session_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        cookie_name(settings),
        path="/",
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite="lax",
    )


# The OAuth state cookie ties a provider sign-in to the browser that started it (login CSRF).
# SameSite=Lax is enough: the provider sends the browser back with a top-level GET.

STATE_COOKIE_SECONDS = 600  # as long as the state itself


def state_cookie_name(settings: Settings) -> str:
    return "__Host-novoya_oauth_state" if settings.session_cookie_secure else "novoya_oauth_state"


def read_state_cookie(request: Request, settings: Settings) -> str | None:
    return request.cookies.get(state_cookie_name(settings)) or None


def set_state_cookie(response: Response, state: str, settings: Settings) -> None:
    response.set_cookie(
        state_cookie_name(settings),
        state,
        max_age=STATE_COOKIE_SECONDS,
        path="/",
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite="lax",
    )


def clear_state_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        state_cookie_name(settings),
        path="/",
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite="lax",
    )
