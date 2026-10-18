from datetime import date
from uuid import uuid4

import pytest

from novoya_api.catalog.domain import InvalidOffer, Offer, OfferKind, Partner, PartnerKind

SEASON_START = date(2026, 4, 1)
SEASON_END = date(2026, 10, 31)


def _partner(**overrides: object) -> Partner:
    values: dict[str, object] = {
        "id": uuid4(),
        "name": "Test partner",
        "kind": PartnerKind.HOTEL,
        "country": "Greece",
        "city": "Chania",
        "contact_email": "p@example.com",
        "contact_phone": "+30 000",
        "active": True,
    }
    values.update(overrides)
    return Partner(**values)  # type: ignore[arg-type]


def _offer(**overrides: object) -> Offer:
    partner_id = overrides.get("partner_id", uuid4())
    values: dict[str, object] = {
        "id": uuid4(),
        "partner_id": partner_id,
        "kind": OfferKind.HOTEL,
        "title": "Test stay",
        "description": "A room",
        "country": "Greece",
        "city": "Chania",
        "min_persons": 2,
        "max_persons": 4,
        "available_from": SEASON_START,
        "available_to": SEASON_END,
        "tags": ("style:beach", "rythm:calm"),
        "featured": False,
        "active": True,
    }
    values.update(overrides)
    return Offer(**values)  # type: ignore[arg-type]


def test_offer_fits_when_persons_and_dates_are_inside_limits():
    offer = _offer()
    assert offer.fits(persons=2, start=date(2026, 5, 1), end=date(2026, 5, 8)) is True
    assert offer.fits(persons=4, start=SEASON_START, end=SEASON_END) is True


def test_offer_rejects_too_few_persons():
    offer = _offer(min_persons=2, max_persons=4)
    assert offer.fits(persons=1, start=date(2026, 5, 1), end=date(2026, 5, 8)) is False


def test_offer_rejects_too_many_persons():
    offer = _offer(min_persons=2, max_persons=4)
    assert offer.fits(persons=5, start=date(2026, 5, 1), end=date(2026, 5, 8)) is False


def test_offer_rejects_trip_starting_before_availability():
    offer = _offer()
    assert offer.fits(persons=2, start=date(2026, 3, 20), end=date(2026, 5, 8)) is False


def test_offer_rejects_trip_ending_after_availability():
    offer = _offer()
    assert offer.fits(persons=2, start=date(2026, 5, 1), end=date(2026, 11, 2)) is False


def test_offer_rejects_inverted_trip_dates():
    offer = _offer()
    assert offer.fits(persons=2, start=date(2026, 5, 8), end=date(2026, 5, 1)) is False


def test_invalid_person_limits_are_rejected():
    with pytest.raises(InvalidOffer):
        _offer(min_persons=4, max_persons=2)


def test_inactive_partner_hides_offers():
    partner = _partner(active=False)
    offer = _offer(partner_id=partner.id, active=True)
    assert offer.is_listed_with(partner) is False


def test_inactive_offer_is_not_listed():
    partner = _partner(active=True)
    offer = _offer(partner_id=partner.id, active=False)
    assert offer.is_listed_with(partner) is False
    assert offer.fits(persons=2, start=date(2026, 5, 1), end=date(2026, 5, 8)) is True
