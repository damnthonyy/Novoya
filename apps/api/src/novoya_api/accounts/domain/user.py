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


@dataclass(slots=True)
class User:
    """A person with an account. Ways to sign in (password, Google) are kept apart."""

    id: UserId
    email: Email
    name: str | None
    role: Role
    locale: Locale
    status: UserStatus
    email_verified_at: datetime | None
    created_at: datetime

    @classmethod
    def register(cls, email: Email, name: str | None, locale: Locale, now: datetime) -> "User":
        """A new account is always a client. Only an admin can change the role afterwards."""
        return cls(UserId.new(), email, name, Role.CLIENT, locale, UserStatus.ACTIVE, None, now)

    @property
    def is_email_verified(self) -> bool:
        return self.email_verified_at is not None

    @property
    def is_active(self) -> bool:
        return self.status is UserStatus.ACTIVE

    def rename(self, name: str | None) -> None:
        """Take the name the provider knows; keep ours when it sends none."""
        if name and name.strip():
            self.name = name.strip()[:200]

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
