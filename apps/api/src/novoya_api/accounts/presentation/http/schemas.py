from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, SecretStr

from novoya_api.accounts.application.dto import AccountView
from novoya_api.accounts.domain.role import Role
from novoya_api.accounts.domain.user import User

RoleName = Literal["client", "agent", "admin"]


class RegisterRequest(BaseModel):
    email: str = Field(max_length=254)
    password: SecretStr
    name: str | None = Field(default=None, max_length=200)
    locale: Literal["en", "fr"] | None = None  # defaults to the browser language


class SignInRequest(BaseModel):
    email: str = Field(max_length=254)
    password: SecretStr


class TokenRequest(BaseModel):
    token: str = Field(max_length=200)


class EmailRequest(BaseModel):
    email: str = Field(max_length=254)


class ResetPasswordRequest(BaseModel):
    token: str = Field(max_length=200)
    new_password: SecretStr


class ChangePasswordRequest(BaseModel):
    current_password: SecretStr
    new_password: SecretStr


class ChangeRoleRequest(BaseModel):
    role: RoleName


class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str | None
    role: RoleName
    locale: Literal["en", "fr"]
    status: Literal["active", "disabled"]
    email_verified: bool
    created_at: datetime

    @classmethod
    def of(cls, user: User) -> "UserResponse":
        return cls(
            id=user.id.value,
            email=user.email.value,
            name=user.name,
            role=user.role.value,
            locale=user.locale.value,
            status=user.status.value,
            email_verified=user.is_email_verified,
            created_at=user.created_at,
        )


class MeResponse(UserResponse):
    sign_in_methods: list[Literal["password", "google"]]

    @classmethod
    def of_account(cls, account: AccountView) -> "MeResponse":
        methods: list[Literal["password", "google"]] = ["password"] if account.has_password else []
        return cls(**UserResponse.of(account.user).model_dump(), sign_in_methods=methods)


def role_of(name: RoleName | None) -> Role | None:
    return Role(name) if name else None
