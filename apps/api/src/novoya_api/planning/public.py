"""What other modules may use from planning. Nothing else in planning may be imported.

- generate_plan(request) -> PlanView: builds the proposed plan of an answered wish and adds
  it to the caller's session; the caller commits. It ends the session's read transaction
  before the model runs, so call it before writing anything in that session. Raises
  NoOfferFits (422) when no listed offer fits the travellers and dates.
- delete_for_wishes(wish_ids): erases the plans of these wishes (items and extras go with
  them). Erase plans before wishes. The caller commits.

Planned:
- get_priced_plan(plan_id) -> PricedPlanView (items with negotiated prices, for the quote)
- mark_quoted(plan_id), mark_accepted(plan_id), mark_rejected(plan_id) (called by quoting)
"""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from novoya_api.planning.application.dto import PlanItemView, PlanRequest, PlanView
from novoya_api.planning.application.ports.plan_writer import PlanWriter
from novoya_api.planning.application.use_cases.generate_plan import GeneratePlan
from novoya_api.planning.domain.errors import NoOfferFits
from novoya_api.planning.infrastructure.catalog import PartnerOffers
from novoya_api.planning.infrastructure.db.repository import SqlPlanRepository
from novoya_api.planning.infrastructure.llm.plan_writer import LlmPlanWriter, NoModelPlanWriter
from novoya_api.planning.infrastructure.llm.tools import travel_tools
from novoya_api.shared.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from novoya_api.shared.infrastructure.llm.client import get_orchestrator
from novoya_api.shared.infrastructure.llm.errors import LLMError
from novoya_api.shared.infrastructure.system_clock import SystemClock

__all__ = [
    "NoOfferFits",
    "PlanItemView",
    "PlanRequest",
    "PlanView",
    "delete_for_wishes",
    "generate_plan",
]

# The client waits for the plan; the fallback covers a slow model.
DEADLINE_SECONDS = 60


async def generate_plan(request: PlanRequest, *, session: AsyncSession) -> PlanView:
    """The proposed plan of an answered wish, added to `session`. The caller commits."""
    use_case = GeneratePlan(
        catalog=PartnerOffers(session),
        writer=_writer(),
        plans=SqlPlanRepository(session),
        uow=SqlAlchemyUnitOfWork(session),
        clock=SystemClock(),
    )
    return await use_case(request)


def _writer() -> PlanWriter:
    try:
        orchestrator = get_orchestrator(deadline_seconds=DEADLINE_SECONDS)
    except LLMError:
        return NoModelPlanWriter()  # no API key: the plan is built from the catalog
    # No session: each tool call reads in a short session of its own, so no connection is held
    # while the model thinks between calls.
    return LlmPlanWriter(orchestrator, travel_tools(), DEADLINE_SECONDS)


async def delete_for_wishes(wish_ids: Sequence[UUID], *, session: AsyncSession) -> None:
    """Erase the plans of these wishes. Do it before erasing the wishes. The caller commits."""
    await SqlPlanRepository(session).delete_for_wishes(wish_ids)
