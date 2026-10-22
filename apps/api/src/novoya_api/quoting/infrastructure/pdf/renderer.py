"""The quote PDF: a Jinja2 HTML template rendered with WeasyPrint, in English or French."""

import base64
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from babel.dates import format_date
from babel.numbers import format_currency
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from weasyprint import HTML
from weasyprint.urls import URLFetcher

from novoya_api.quoting.application.dto import QuoteDocument
from novoya_api.quoting.domain.quote import AGENCY_TIMEZONE
from novoya_api.shared.domain.value_objects import Locale

TEMPLATES = Path(__file__).parent / "templates"
# Novoya is the project; the quote comes from the agency. Confirmed values of
# apps/web/brand/agency.json; logo.svg is the agency's final logo.
AGENCY = {
    "name": "DÉTOUR Voyages",
    "website": "www.detour-voyages.fr",
    "email": "contact@detour-voyages.fr",
    "phone": "+33 2 40 00 00 00",
}
LOGO = (
    "data:image/svg+xml;base64," + base64.b64encode((TEMPLATES / "logo.svg").read_bytes()).decode()
)

LABELS: dict[Locale, dict[str, str]] = {
    Locale.EN: {
        "quote": "Quote",
        "number": "Number",
        "issued": "Issued on",
        "valid_until": "Valid until",
        "client": "Client",
        "your_agent": "Your travel agent",
        "destination": "Destination",
        "dates": "Dates",
        "travellers": "Travellers",
        "your_wish": "Your wish",
        "your_trip": "Your trip, day by day",
        "day": "Day",
        "item": "What is booked",
        "quantity": "Qty",
        "price": "Price",
        "extra": "Extra",
        "included": "Included",
        "unavailable": "No longer listed",
        "total": "Total",
        "your_budget": "Your maximum budget",
        "not_included_title": "Not included",
        "not_included": "Flights, meals and drinks not listed above, tips and travel insurance.",
        "how_to_answer_title": "How to answer",
        "how_to_answer": "Sign in to your DÉTOUR account to accept or reject this quote "
        "before {date}. After that date, the prices may change.",
        "questions": "A question? Write to your travel agent:",
        "or_call": "or call the agency:",
    },
    Locale.FR: {
        "quote": "Devis",
        "number": "Numéro",
        "issued": "Émis le",
        "valid_until": "Valable jusqu'au",
        "client": "Client",
        "your_agent": "Votre conseiller voyage",
        "destination": "Destination",
        "dates": "Dates",
        "travellers": "Voyageurs",
        "your_wish": "Votre souhait",
        "your_trip": "Votre voyage, jour par jour",
        "day": "Jour",
        "item": "Prestation réservée",
        "quantity": "Qté",
        "price": "Prix",
        "extra": "Option",
        "included": "Inclus",
        "unavailable": "Plus au catalogue",
        "total": "Total",
        "your_budget": "Votre budget maximum",
        "not_included_title": "Non compris",
        "not_included": "Les vols, les repas et boissons non indiqués ci-dessus, les "
        "pourboires et l'assurance voyage.",
        "how_to_answer_title": "Comment répondre",
        "how_to_answer": "Connectez-vous à votre compte DÉTOUR pour accepter ou refuser ce "
        "devis avant le {date}. Après cette date, les prix peuvent changer.",
        "questions": "Une question ? Écrivez à votre conseiller :",
        "or_call": "ou appelez l'agence :",
    },
}


class WeasyPrintRenderer:
    """QuoteRenderer with Jinja2 and WeasyPrint. Euros and dates in the quote's language."""

    def __init__(self) -> None:
        self._env = Environment(
            loader=FileSystemLoader(TEMPLATES),
            autoescape=select_autoescape(["html"]),
            undefined=StrictUndefined,
        )

    def html(self, document: QuoteDocument) -> str:
        locale = document.quote.locale
        env = self._env.overlay()
        env.filters["money"] = lambda amount: _money(amount, locale)
        env.filters["day"] = lambda value: _day(value, locale)
        plan = document.plan
        return env.get_template("quote.html").render(
            locale=locale.value,
            t=LABELS[locale],
            agency=AGENCY,
            logo=LOGO,
            quote=document.quote,
            plan=plan,
            items=[
                {
                    "day": item.day,
                    "date": _date_of_day(plan.start_date, item.day),
                    "title": item.title,
                    "description": item.description,
                    "quantity": item.quantity,
                    "price": item.price,
                }
                for item in plan.items
            ],
            client=document.client,
            agent=document.agent,
            destination=", ".join(part for part in (plan.city, plan.country) if part) or "–",
            tags=[_tag_label(tag) for tag in plan.tags],
            answer_url=document.answer_url,
        )

    def render(self, document: QuoteDocument) -> bytes:
        # The CSS is inline and the logo a data: URI, so the quote fetches nothing else: text
        # a client or a partner wrote can never read a local file or call a server.
        fetcher = URLFetcher(allowed_protocols={"data"})
        return HTML(
            string=self.html(document), base_url=str(TEMPLATES), url_fetcher=fetcher
        ).write_pdf()


def _money(amount: Decimal, locale: Locale) -> str:
    return format_currency(amount, "EUR", locale=locale.value)


def _day(value: date | datetime, locale: Locale) -> str:
    plain = value.astimezone(AGENCY_TIMEZONE).date() if isinstance(value, datetime) else value
    return format_date(plain, format="long", locale=locale.value)


def _date_of_day(start: date | None, day: int) -> date | None:
    """Day 1 is the departure."""
    return start + timedelta(days=day - 1) if start else None


def _tag_label(tag: str) -> str:
    """ "style:beach-bars" -> "beach bars": the client clicked the tag, not the section."""
    return tag.rpartition(":")[2].replace("-", " ").replace("_", " ")
