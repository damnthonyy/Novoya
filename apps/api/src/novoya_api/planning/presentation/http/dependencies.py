"""Composition root of the planning module: plugs the adapters into the use cases.

In each module, this file is the only place outside infrastructure that may import
infrastructure. Tests replace these dependencies with fakes.
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from novoya_api.accounts.public import CurrentUserView, require_client
from novoya_api.planning.application.use_cases.get_plan import GetPlan
from novoya_api.planning.infrastructure.catalog import PartnerOffers
from novoya_api.planning.infrastructure.db.repository import SqlPlanRepository
from novoya_api.planning.infrastructure.wish_owners import WishOwners
from novoya_api.shared.infrastructure.db.session import get_session


def get_current_user_id(user: Annotated[CurrentUserView, Depends(require_client)]) -> UUID:
    """The signed-in client: 401 without a session, 403 for an agent (the admin passes)."""
    return user.user_id.value


def get_get_plan(session: Annotated[AsyncSession, Depends(get_session)]) -> GetPlan:
    return GetPlan(
        plans=SqlPlanRepository(session),
        catalog=PartnerOffers(session),
        wishes=WishOwners(session),
    )
