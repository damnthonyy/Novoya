import inspect
from datetime import date
from uuid import uuid4

from novoya_api.catalog.application.use_cases.list_destinations import ListDestinations
from novoya_api.catalog.application.use_cases.list_tags_at import ListTagsAt
from novoya_api.catalog.domain import Offer, OfferKind, Partner, PartnerKind
from novoya_api.catalog.public import covered_destinations, tags_at

SEASON_START = date(2026, 4, 1)
SEASON_END = date(2026, 10, 31)


def _partner(**overrides: object) -> Partner:
    values: dict[str, object] = {
        "id": uuid4(),
        "name": "Test partner",
        "kind": PartnerKind.HOTEL,
        "country": "Portugal",
        "city": "Lisbon",
        "contact_email": "p@example.com",
        "contact_phone": "+351 000",
        "active": True,
    }
    values.update(overrides)
    return Partner(**values)  # type: ignore[arg-type]


def _offer(partner: Partner, **overrides: object) -> Offer:
    values: dict[str, object] = {
        "id": uuid4(),
        "partner_id": partner.id,
        "kind": OfferKind.HOTEL,
        "title": "Test stay",
        "description": "A room",
        "country": partner.country,
        "city": partner.city,
        "min_persons": 2,
        "max_persons": 4,
        "available_from": SEASON_START,
        "available_to": SEASON_END,
        "tags": ("style:beach", "rhythm:calm"),
        "featured": False,
        "active": True,
    }
    values.update(overrides)
    return Offer(**values)  # type: ignore[arg-type]


class FakeOffers:
    def __init__(self, pairs: list[tuple[Offer, Partner]]) -> None:
        self._pairs = pairs

    async def list_with_partners(self) -> list[tuple[Offer, Partner]]:
        return list(self._pairs)

    async def list_listed_destinations(self) -> list[tuple[str, str]]:
        destinations = {
            (offer.country, offer.city)
            for offer, partner in self._pairs
            if offer.is_listed_with(partner)
        }
        return sorted(destinations)

    async def list_at(self, country: str, city: str | None) -> list[tuple[Offer, Partner]]:
        found: list[tuple[Offer, Partner]] = []
        for offer, partner in self._pairs:
            if offer.country.lower() != country.lower():
                continue
            if city is not None and offer.city.lower() != city.lower():
                continue
            found.append((offer, partner))
        return found


async def test_covered_destinations_need_a_listed_offer():
    lisbon = _partner(country="Portugal", city="Lisbon")
    porto = _partner(country="Portugal", city="Porto")
    closed = _partner(country="Spain", city="Seville", active=False)
    empty = _partner(country="France", city="Biarritz")
    pairs = [
        (_offer(lisbon), lisbon),
        (_offer(porto), porto),
        (_offer(closed), closed),
        (_offer(empty, active=False), empty),
    ]
    destinations = await ListDestinations(FakeOffers(pairs))()
    assert destinations == [("Portugal", "Lisbon"), ("Portugal", "Porto")]


async def test_covered_destinations_are_unique_and_sorted():
    a = _partner(country="Morocco", city="Marrakech")
    b = _partner(country="Greece", city="Chania")
    c = _partner(country="Morocco", city="Marrakech")
    pairs = [(_offer(a), a), (_offer(b), b), (_offer(c), c)]
    destinations = await ListDestinations(FakeOffers(pairs))()
    assert destinations == [("Greece", "Chania"), ("Morocco", "Marrakech")]


async def test_tags_at_returns_listed_offer_tags():
    hotel = _partner(country="Greece", city="Chania")
    stay = _offer(hotel, tags=("style:beach", "rhythm:calm"))
    walk = _offer(hotel, kind=OfferKind.GUIDE, tags=("style:culture", "food:local"))
    tags = await ListTagsAt(FakeOffers([(stay, hotel), (walk, hotel)]))("Greece", "Chania")
    assert tags == ["food:local", "rhythm:calm", "style:beach", "style:culture"]


async def test_tags_at_hides_inactive_partner_and_inactive_offer():
    open_hotel = _partner(country="Morocco", city="Marrakech", active=True)
    closed_agency = _partner(country="Morocco", city="Marrakech", active=False)
    riad = _offer(open_hotel, tags=("accommodation:riad", "style:culture"))
    desk = _offer(closed_agency, tags=("style:package",))
    inactive = _offer(open_hotel, active=False, tags=("style:hidden",))
    listed = [(riad, open_hotel), (desk, closed_agency), (inactive, open_hotel)]
    tags = await ListTagsAt(FakeOffers(listed))("Morocco", "Marrakech")
    assert tags == ["accommodation:riad", "style:culture"]
    assert "style:package" not in tags
    assert "style:hidden" not in tags


async def test_tags_at_city_none_covers_the_whole_country():
    lisbon = _partner(country="Portugal", city="Lisbon")
    porto = _partner(country="Portugal", city="Porto")
    stay = _offer(lisbon, tags=("style:culture",))
    surf = _offer(porto, tags=("style:beach",))
    tags = await ListTagsAt(FakeOffers([(stay, lisbon), (surf, porto)]))("Portugal", None)
    assert tags == ["style:beach", "style:culture"]


async def test_tags_at_matches_country_and_city_ignoring_case():
    hotel = _partner(country="Greece", city="Chania")
    stay = _offer(hotel, tags=("style:beach",))
    tags = await ListTagsAt(FakeOffers([(stay, hotel)]))("greece", "chania")
    assert tags == ["style:beach"]


def test_public_module_exposes_the_two_functions_wishes_needs():
    assert inspect.iscoroutinefunction(covered_destinations)
    assert inspect.iscoroutinefunction(tags_at)
    assert list(inspect.signature(covered_destinations).parameters) == []
    assert list(inspect.signature(tags_at).parameters) == ["country", "city"]
    annotations = inspect.signature(tags_at).parameters
    assert annotations["city"].annotation == (str | None)
