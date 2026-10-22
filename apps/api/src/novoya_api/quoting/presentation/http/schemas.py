from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from novoya_api.quoting.application.dto import QuoteView


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
