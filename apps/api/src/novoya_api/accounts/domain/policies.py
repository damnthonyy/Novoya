from dataclasses import dataclass

from novoya_api.accounts.domain.errors import WeakPassword
from novoya_api.accounts.domain.value_objects import Email, PlainPassword

# The most common passwords that pass the length rule. Not exhaustive: it stops the obvious ones.
COMMON_PASSWORDS = frozenset(
    {
        "123456789012",
        "1234567890123",
        "password1234",
        "password12345",
        "passwordpassword",
        "qwertyuiopas",
        "azertyuiopqs",
        "motdepasse123",
        "iloveyou1234",
        "adminadmin123",
        "000000000000",
        "111111111111",
    }
)


@dataclass(frozen=True, slots=True)
class PasswordPolicy:
    """NIST SP 800-63B: length matters, composition rules do not."""

    min_length: int = 12
    max_length: int = 128  # hashing a huge password costs CPU: a denial of service vector

    def validate(self, password: PlainPassword, email: Email) -> None:
        value = password.value
        if len(value) < self.min_length:
            raise WeakPassword(f"the password needs at least {self.min_length} characters")
        if len(value) > self.max_length:
            raise WeakPassword(f"the password may have at most {self.max_length} characters")
        if value.lower() in COMMON_PASSWORDS:
            raise WeakPassword("this password is too common")
        local_part = email.value.split("@")[0]
        if len(local_part) >= 4 and local_part in value.lower():
            raise WeakPassword("the password must not contain the email address")
