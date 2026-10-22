from uuid import UUID

from novoya_api.quoting.application.dto import QuoteEmail, QuoteTrip
from novoya_api.quoting.application.ports.notifier import QuoteNotifier
from novoya_api.quoting.application.ports.people import People
from novoya_api.quoting.application.ports.plans import PlanQuoting
from novoya_api.quoting.application.ports.quote_repository import QuoteRepository
from novoya_api.quoting.domain.errors import QuoteEmailNotSent, QuoteNotFound
from novoya_api.shared.domain.errors import PermissionDenied


class ResendQuoteEmail:
    """Sends the "your quote is ready" email again, when the first one did not go out. Only
    the agent who sent the quote, or an admin, may do it."""

    def __init__(
        self,
        quotes: QuoteRepository,
        plans: PlanQuoting,
        people: People,
        notifier: QuoteNotifier,
        frontend_url: str,
    ) -> None:
        self._quotes = quotes
        self._plans = plans
        self._people = people
        self._notifier = notifier
        self._frontend_url = frontend_url.rstrip("/")

    async def __call__(self, quote_id: UUID, caller_id: UUID, admin: bool) -> None:
        quote = await self._quotes.get(quote_id)
        if quote is None:
            raise QuoteNotFound("no such quote")
        if not admin and quote.agent_id != caller_id:
            raise PermissionDenied("only the agent who sent the quote, or an admin")
        client = await self._people.get(quote.client_id)
        if client is None:
            raise QuoteNotFound("the client is gone")
        trip = await self._plans.trip(quote.plan_id) or QuoteTrip(None, None, None, None)
        email = QuoteEmail(
            client.email,
            client.name,
            quote.locale,
            trip,
            f"{self._frontend_url}/quotes/{quote.id}",
        )
        if not await self._notifier.send_quote_ready(email):
            raise QuoteEmailNotSent("the email server did not take the email, try again later")
