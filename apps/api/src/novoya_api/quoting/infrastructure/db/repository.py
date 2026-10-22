from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer

from novoya_api.quoting.domain.quote import Quote
from novoya_api.quoting.infrastructure.db.models import QuoteModel
from novoya_api.shared.domain.value_objects import Locale


class SqlQuoteRepository:
    """QuoteRepository on PostgreSQL. The PDF is stored with the quote (ADR 0013)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, quote: Quote) -> None:
        # uq_quotes_plan_id is the last guard against a second quote for the plan; the plan's
        # own status check (409) normally stops it first.
        self._session.add(
            QuoteModel(
                id=quote.id,
                number=quote.number,
                plan_id=quote.plan_id,
                client_id=quote.client_id,
                agent_id=quote.agent_id,
                total_price=quote.total,
                currency=quote.currency,
                locale=quote.locale.value,
                sent_at=quote.sent_at,
                valid_until=quote.valid_until,
                pdf=quote.pdf,
            )
        )
        await self._session.flush()

    async def get(self, quote_id: UUID) -> Quote | None:
        row = await self._session.get(QuoteModel, quote_id)
        if row is None:
            return None
        return _to_quote(row, row.pdf)

    async def search(
        self,
        plan_ids: Sequence[UUID] | None,
        expired: bool | None,
        now: datetime,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Quote]:
        # A list never needs the PDF (about 23 KB a quote): it stays in the database.
        statement = select(QuoteModel).options(defer(QuoteModel.pdf))
        if plan_ids is not None:
            statement = statement.where(QuoteModel.plan_id.in_(plan_ids))
        if expired is True:
            statement = statement.where(QuoteModel.valid_until < now)
        elif expired is False:
            statement = statement.where(QuoteModel.valid_until >= now)
        rows = await self._session.scalars(
            statement.order_by(QuoteModel.sent_at.desc(), QuoteModel.id).limit(limit).offset(offset)
        )
        return [_to_quote(row, b"") for row in rows]

    async def delete_for_client(self, client_id: UUID) -> None:
        """Erase this client's quotes; the PDF is a column, so it goes too. The caller commits."""
        await self._session.execute(
            delete(QuoteModel)
            .where(QuoteModel.client_id == client_id)
            .execution_options(synchronize_session=False)
        )


def _to_quote(row: QuoteModel, pdf: bytes) -> Quote:
    return Quote(
        id=row.id,
        number=row.number,
        plan_id=row.plan_id,
        client_id=row.client_id,
        agent_id=row.agent_id,
        total=row.total_price,
        currency=row.currency,
        locale=Locale(row.locale),
        sent_at=row.sent_at,
        valid_until=row.valid_until,
        pdf=pdf,
    )
