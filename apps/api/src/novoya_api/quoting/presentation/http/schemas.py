from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from novoya_api.quoting.application.dto import AdminQuoteView, QuoteView


class SendQuoteRequest(BaseModel):
    """The quote's language, chosen by the agent. Without it, the client's language."""

    locale: Literal["en", "fr"] | None = None


class Quote(BaseModel):
    """A sent quote. total is in currency (always EUR); the PDF is at GET /quotes/{id}/pdf.
    email_sent is false when the client's email did not go out: POST
    /agent/quotes/{id}/email sends it again."""

    id: UUID
    number: str
    plan_id: UUID
    total: Decimal
    currency: str
    locale: Literal["en", "fr"]
    sent_at: datetime
    valid_until: datetime
    email_sent: bool

    @classmethod
    def of(cls, view: QuoteView) -> "Quote":
        return cls.model_validate(view, from_attributes=True)


QuoteStatusName = Literal["sent", "expired", "accepted", "rejected"]


class QuoteClient(BaseModel):
    """Who the quote is for: name and email, as on the admin users page."""

    id: UUID
    name: str | None
    email: str


class AdminQuote(BaseModel):
    """One quote in the admin overview. status: sent (waiting for the client), expired (no
    answer within the week), accepted or rejected. The PDF is at GET /quotes/{id}/pdf."""

    id: UUID
    number: str
    plan_id: UUID
    status: QuoteStatusName
    total: Decimal
    currency: str
    locale: Literal["en", "fr"]
    sent_at: datetime
    valid_until: datetime
    country: str | None
    city: str | None
    start_date: date | None
    end_date: date | None
    client: QuoteClient | None

    @classmethod
    def of(cls, view: AdminQuoteView) -> "AdminQuote":
        client = view.client
        return cls(
            id=view.id,
            number=view.number,
            plan_id=view.plan_id,
            status=view.status,
            total=view.total,
            currency=view.currency,
            locale=view.locale,
            sent_at=view.sent_at,
            valid_until=view.valid_until,
            country=view.trip.country,
            city=view.trip.city,
            start_date=view.trip.start_date,
            end_date=view.trip.end_date,
            client=QuoteClient(id=client.user_id, name=client.name, email=client.email)
            if client
            else None,
        )
