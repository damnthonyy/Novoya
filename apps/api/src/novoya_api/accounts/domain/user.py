from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from novoya_api.accounts.domain.errors import (
    AccountDisabled,
    CannotChangeOwnRole,
    EmailNotVerified,
)
from novoya_api.accounts.domain.role import Role
from novoya_api.accounts.domain.role_change import RoleChange
from novoya_api.accounts.domain.value_objects import Email, UserId
from novoya_api.shared.domain.value_objects import Locale


class UserStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


def _clip(value: str | None, max_len: int) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()[:max_len]
    return cleaned or None


def _display_name(first_name: str | None, last_name: str | None) -> str | None:
    parts = [part for part in (first_name, last_name) if part]
    return " ".join(parts) or None


@dataclass(slots=True)
class User:
    """A person with an account. Ways to sign in (password, Google) are kept apart."""

    id: UserId
    email: Email
    name: str | None
    first_name: str | None
    last_name: str | None
    role: Role
    locale: Locale
    status: UserStatus
    email_verified_at: datetime | None
    created_at: datetime

    @classmethod
    def register(
        cls,
        email: Email,
        first_name: str | None,
        last_name: str | None,
        locale: Locale,
        now: datetime,
    ) -> "User":
        """A new account is always a client. Only an admin can change the role afterwards."""
        given = _clip(first_name, 100)
        family = _clip(last_name, 100)
        return cls(
            UserId.new(),
            email,
            _display_name(given, family),
            given,
            family,
            Role.CLIENT,
            locale,
            UserStatus.ACTIVE,
            None,
            now,
        )

    @property
    def is_email_verified(self) -> bool:
        return self.email_verified_at is not None

    @property
    def is_active(self) -> bool:
        return self.status is UserStatus.ACTIVE

    def fill_in_name(self, name: str | None) -> None:
        """Take the provider's name only when we have none: a name chosen at sign-up wins."""
        if self.name is None and name and name.strip():
            self.name = name.strip()[:200]

    def fill_in_from_provider(
        self,
        *,
        first_name: str | None,
        last_name: str | None,
        name: str | None,
    ) -> None:
        """Take the provider's names only when we have none: a name chosen at sign-up wins."""
        if self.first_name is None:
            self.first_name = _clip(first_name, 100)
        if self.last_name is None:
            self.last_name = _clip(last_name, 100)
        if self.name is None:
            self.name = _display_name(self.first_name, self.last_name)
        self.fill_in_name(name)

    def verify_email(self, now: datetime) -> None:
        if self.email_verified_at is None:
            self.email_verified_at = now

    def ensure_can_sign_in(self, *, require_verified_email: bool) -> None:
        if not self.is_active:
            raise AccountDisabled("this account is disabled")
        if require_verified_email and not self.is_email_verified:
            raise EmailNotVerified("verify your email address before signing in")

    def change_role(
        self, new_role: Role, *, changed_by: "UserId | None", now: datetime
    ) -> RoleChange | None:
        """Change the role and return the log line, or None if the role is the same.

        changed_by: the admin making the change, or None for the grant-role command.
        Whether the caller may change roles is checked before (require_admin, or server access).
        """
        if changed_by == self.id:
            raise CannotChangeOwnRole("an admin cannot change their own role")
        if new_role is not Role.CLIENT and not self.is_email_verified:
            raise EmailNotVerified("only a verified email address can get the agent or admin role")
        if new_role is self.role:
            return None
        change = RoleChange.record(self.id, self.role, new_role, changed_by, now)
        self.role = new_role
        return change
