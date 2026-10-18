"""Repositories of the accounts module, with SQLAlchemy.

They map rows to entities and back: no ORM object leaves this file. They never commit; the
use case does, through the UnitOfWork that shares their session.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from novoya_api.accounts.domain.auth_session import AuthSession
from novoya_api.accounts.domain.credentials import PasswordCredential
from novoya_api.accounts.domain.errors import EmailAlreadyUsed
from novoya_api.accounts.domain.one_time_token import OneTimeToken, TokenPurpose
from novoya_api.accounts.domain.role import Role
from novoya_api.accounts.domain.role_change import RoleChange
from novoya_api.accounts.domain.user import User, UserStatus
from novoya_api.accounts.domain.value_objects import Email, PasswordHash, UserId
from novoya_api.accounts.infrastructure.db.models import (
    OneTimeTokenModel,
    PasswordCredentialModel,
    RoleChangeModel,
    SessionModel,
    UserModel,
)
from novoya_api.shared.domain.value_objects import Locale


def user_to_entity(row: UserModel) -> User:
    return User(
        id=UserId(row.id),
        email=Email(row.email),
        name=row.name,
        role=Role(row.role),
        locale=Locale(row.locale),
        status=UserStatus(row.status),
        email_verified_at=row.email_verified_at,
        created_at=row.created_at,
    )


def copy_user(user: User, row: UserModel) -> None:
    row.email = user.email.value
    row.name = user.name
    row.role = user.role.value
    row.locale = user.locale.value
    row.status = user.status.value
    row.email_verified_at = user.email_verified_at


class SqlUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, user_id: UserId) -> User | None:
        row = await self._session.get(UserModel, user_id.value)
        return user_to_entity(row) if row else None

    async def get_by_email(self, email: Email) -> User | None:
        row = await self._session.scalar(select(UserModel).where(UserModel.email == email.value))
        return user_to_entity(row) if row else None

    async def add(self, user: User) -> None:
        row = UserModel(id=user.id.value, created_at=user.created_at)
        copy_user(user, row)
        self._session.add(row)
        try:
            await self._session.flush()  # two sign-ups at once: the unique index decides
        except IntegrityError as exc:
            raise EmailAlreadyUsed("this email address already has an account") from exc

    async def save(self, user: User) -> None:
        row = await self._session.get(UserModel, user.id.value)
        if row is not None:
            copy_user(user, row)

    async def count_active_with_role(self, role: Role) -> int:
        count = await self._session.scalar(
            select(func.count())
            .select_from(UserModel)
            .where(UserModel.role == role.value, UserModel.status == UserStatus.ACTIVE.value)
        )
        return count or 0

    async def search(
        self, query: str | None, role: Role | None, limit: int, offset: int
    ) -> list[User]:
        statement = select(UserModel)
        if query:
            pattern = f"%{query.strip()}%"
            statement = statement.where(
                or_(UserModel.email.ilike(pattern), UserModel.name.ilike(pattern))
            )
        if role is not None:
            statement = statement.where(UserModel.role == role.value)
        statement = statement.order_by(UserModel.created_at.desc()).limit(limit).offset(offset)
        rows = await self._session.scalars(statement)
        return [user_to_entity(row) for row in rows]


class SqlRoleChangeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, change: RoleChange) -> None:
        self._session.add(
            RoleChangeModel(
                id=change.id,
                user_id=change.user_id.value,
                old_role=change.old_role.value,
                new_role=change.new_role.value,
                source=change.source,
                changed_by=change.changed_by.value if change.changed_by else None,
                changed_at=change.changed_at,
            )
        )


class SqlPasswordCredentialRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, user_id: UserId) -> PasswordCredential | None:
        row = await self._session.get(PasswordCredentialModel, user_id.value)
        if row is None:
            return None
        return PasswordCredential(
            UserId(row.user_id), PasswordHash(row.password_hash), row.updated_at
        )

    async def upsert(self, credential: PasswordCredential) -> None:
        row = await self._session.get(PasswordCredentialModel, credential.user_id.value)
        if row is None:
            row = PasswordCredentialModel(user_id=credential.user_id.value)
            self._session.add(row)
        row.password_hash = credential.password_hash.value
        row.updated_at = credential.updated_at


def session_to_entity(row: SessionModel) -> AuthSession:
    return AuthSession(
        id=row.id,
        user_id=UserId(row.user_id),
        token_hash=row.token_hash,
        created_at=row.created_at,
        last_seen_at=row.last_seen_at,
        idle_expires_at=row.idle_expires_at,
        absolute_expires_at=row.absolute_expires_at,
        revoked_at=row.revoked_at,
        user_agent=row.user_agent,
    )


class SqlSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, token_hash: str) -> AuthSession | None:
        row = await self._session.scalar(
            select(SessionModel).where(SessionModel.token_hash == token_hash)
        )
        return session_to_entity(row) if row else None

    async def get_with_user(self, token_hash: str) -> tuple[AuthSession, User] | None:
        result = await self._session.execute(
            select(SessionModel, UserModel)
            .join(UserModel, UserModel.id == SessionModel.user_id)
            .where(SessionModel.token_hash == token_hash)
        )
        found = result.first()
        if found is None:
            return None
        return session_to_entity(found[0]), user_to_entity(found[1])

    async def add(self, session: AuthSession) -> None:
        self._session.add(
            SessionModel(
                id=session.id,
                user_id=session.user_id.value,
                token_hash=session.token_hash,
                created_at=session.created_at,
                last_seen_at=session.last_seen_at,
                idle_expires_at=session.idle_expires_at,
                absolute_expires_at=session.absolute_expires_at,
                revoked_at=session.revoked_at,
                user_agent=session.user_agent,
            )
        )

    async def save(self, session: AuthSession) -> None:
        row = await self._session.get(SessionModel, session.id)
        if row is not None:
            row.last_seen_at = session.last_seen_at
            row.idle_expires_at = session.idle_expires_at
            row.revoked_at = session.revoked_at

    async def revoke_all_for_user(
        self, user_id: UserId, now: datetime, except_session_id: UUID | None = None
    ) -> None:
        statement = (
            update(SessionModel)
            .where(SessionModel.user_id == user_id.value, SessionModel.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        if except_session_id is not None:
            statement = statement.where(SessionModel.id != except_session_id)
        await self._session.execute(statement)


def token_to_entity(row: OneTimeTokenModel) -> OneTimeToken:
    return OneTimeToken(
        id=row.id,
        user_id=UserId(row.user_id),
        purpose=TokenPurpose(row.purpose),
        token_hash=row.token_hash,
        expires_at=row.expires_at,
        used_at=row.used_at,
        created_at=row.created_at,
    )


class SqlOneTimeTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, token_hash: str, purpose: TokenPurpose) -> OneTimeToken | None:
        row = await self._session.scalar(
            select(OneTimeTokenModel).where(
                OneTimeTokenModel.token_hash == token_hash,
                OneTimeTokenModel.purpose == purpose.value,
            )
        )
        return token_to_entity(row) if row else None

    async def add(self, token: OneTimeToken) -> None:
        self._session.add(
            OneTimeTokenModel(
                id=token.id,
                user_id=token.user_id.value,
                purpose=token.purpose.value,
                token_hash=token.token_hash,
                expires_at=token.expires_at,
                used_at=token.used_at,
                created_at=token.created_at,
            )
        )

    async def save(self, token: OneTimeToken) -> None:
        row = await self._session.get(OneTimeTokenModel, token.id)
        if row is not None:
            row.used_at = token.used_at

    async def invalidate_all(self, user_id: UserId, purpose: TokenPurpose, now: datetime) -> None:
        await self._session.execute(
            update(OneTimeTokenModel)
            .where(
                OneTimeTokenModel.user_id == user_id.value,
                OneTimeTokenModel.purpose == purpose.value,
                OneTimeTokenModel.used_at.is_(None),
            )
            .values(used_at=now)
        )
