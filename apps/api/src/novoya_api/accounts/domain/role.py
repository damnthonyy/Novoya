from enum import StrEnum


class Role(StrEnum):
    """What a user may do. Stored on the user; only an admin changes it."""

    CLIENT = "client"
    AGENT = "agent"  # agency staff: quote queue, prices, partners and offers
    ADMIN = "admin"  # everything, plus managing users and their roles
