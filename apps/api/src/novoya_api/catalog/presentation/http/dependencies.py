"""Composition root of the catalog module: plugs the adapters into the use cases.

In each module, this file is the only place outside infrastructure that may import
infrastructure. Tests replace these dependencies with fakes.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from novoya_api.catalog.application.use_cases.list_destinations import ListDestinations
from novoya_api.catalog.infrastructure.db.repositories import SqlOfferRepository
from novoya_api.shared.infrastructure.db.session import get_session


def get_list_destinations(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ListDestinations:
    return ListDestinations(SqlOfferRepository(session))
