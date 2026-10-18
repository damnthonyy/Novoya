import re

from novoya_api.catalog.domain.kinds import OfferKind, PartnerKind
from novoya_api.catalog.infrastructure.seed.data import OFFERS, PARTNERS

SECTION_TAG = re.compile(r"^[a-z]+:[a-z0-9-]+$")


def test_seed_covers_at_least_three_destinations():
    destinations = {(row["country"], row["city"]) for row in PARTNERS}
    assert len(destinations) >= 3


def test_seed_has_an_offer_of_every_kind():
    kinds = {row["kind"] for row in OFFERS}
    assert kinds == set(OfferKind)


def test_seed_offers_all_have_tags():
    assert all(row["tags"] for row in OFFERS)


def test_seed_tags_use_section_prefix():
    for row in OFFERS:
        assert all(SECTION_TAG.match(tag) for tag in row["tags"]), row["tags"]


def test_seed_places_are_english_title_case():
    for row in [*PARTNERS, *OFFERS]:
        assert row["country"] == row["country"].title()
        assert row["city"] == row["city"].title()
        assert row["country"].isascii()
        assert row["city"].isascii()


def test_seed_partners_have_contact_phone():
    assert all(row["contact_phone"] for row in PARTNERS)


def test_seed_has_every_partner_kind():
    kinds = {row["kind"] for row in PARTNERS}
    assert kinds == set(PartnerKind)


def test_seed_offers_have_no_price_field():
    for row in OFFERS:
        assert "price" not in row
        assert "negotiated_price" not in row
