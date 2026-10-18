"""SearchOffers with a fake repository: which offers the LLM tools may see, and in what order."""

from datetime import date

from novoya_api.catalog.application.use_cases.search_offers import SearchOffers
from novoya_api.catalog.domain import OfferKind
from tests.test_catalog_public import FakeOffers, _offer, _partner

MAY_START = date(2026, 5, 10)
MAY_END = date(2026, 5, 17)


async def search(
    pairs, country="Portugal", city="Lisbon", tags=(), persons=2, start=None, end=None
):
    return await SearchOffers(FakeOffers(pairs))(
        country, city, list(tags), persons, start or MAY_START, end or MAY_END
    )


async def test_returns_listed_offers_at_the_destination_with_their_partner():
    hotel = _partner(name="Elounda Bay House")
    stay = _offer(hotel, title="Sea view room")
    found = await search([(stay, hotel)])
    assert len(found) == 1
    view = found[0]
    assert view.id == stay.id
    assert view.title == "Sea view room"
    assert view.kind is OfferKind.HOTEL
    assert view.tags == stay.tags
    assert view.partner_name == "Elounda Bay House"
    assert view.partner_contact_email == hotel.contact_email


async def test_hides_inactive_partner_and_inactive_offer():
    open_hotel = _partner()
    closed_hotel = _partner(active=False)
    listed = _offer(open_hotel)
    hidden_by_partner = _offer(closed_hotel)
    inactive = _offer(open_hotel, active=False)
    pairs = [(listed, open_hotel), (hidden_by_partner, closed_hotel), (inactive, open_hotel)]
    assert [view.id for view in await search(pairs)] == [listed.id]


async def test_filters_by_city_or_the_whole_country_ignoring_case():
    chania = _partner(country="Greece", city="Chania")
    athens = _partner(country="Greece", city="Athens")
    lisbon = _partner(country="Portugal", city="Lisbon")
    pairs = [(_offer(chania), chania), (_offer(athens), athens), (_offer(lisbon), lisbon)]
    in_chania = await search(pairs, country="greece", city="chania")
    in_greece = await search(pairs, country="Greece", city=None)
    assert {view.city for view in in_chania} == {"Chania"}
    assert {view.city for view in in_greece} == {"Chania", "Athens"}


async def test_keeps_only_offers_that_fit_the_group_size():
    hotel = _partner()
    couple = _offer(hotel, min_persons=1, max_persons=2)
    family = _offer(hotel, min_persons=3, max_persons=6)
    pairs = [(couple, hotel), (family, hotel)]
    assert [view.id for view in await search(pairs, persons=2)] == [couple.id]
    assert [view.id for view in await search(pairs, persons=4)] == [family.id]
    assert await search(pairs, persons=7) == []


async def test_keeps_only_offers_available_for_the_whole_trip():
    hotel = _partner()
    summer = _offer(hotel, available_from=date(2026, 6, 1), available_to=date(2026, 8, 31))
    season = _offer(hotel, available_from=date(2026, 4, 1), available_to=date(2026, 10, 31))
    pairs = [(summer, hotel), (season, hotel)]
    found = await search(pairs, start=date(2026, 5, 25), end=date(2026, 6, 5))
    assert [view.id for view in found] == [season.id]


async def test_dates_in_the_wrong_order_find_nothing():
    hotel = _partner()
    assert await search([(_offer(hotel), hotel)], start=MAY_END, end=MAY_START) == []


async def test_tags_keep_offers_with_at_least_one_of_them_ignoring_case():
    hotel = _partner()
    beach = _offer(hotel, tags=("style:beach", "rhythm:calm"))
    culture = _offer(hotel, tags=("style:culture",))
    food = _offer(hotel, tags=("food:local",))
    pairs = [(beach, hotel), (culture, hotel), (food, hotel)]
    found = await search(pairs, tags=["STYLE:Beach", "style:culture"])
    assert {view.id for view in found} == {beach.id, culture.id}


async def test_offers_matching_more_tags_come_first_then_featured():
    hotel = _partner()
    one_tag = _offer(hotel, title="B", tags=("style:beach",))
    one_tag_featured = _offer(hotel, title="C", tags=("style:beach",), featured=True)
    two_tags = _offer(hotel, title="A", tags=("style:beach", "rhythm:calm"))
    pairs = [(one_tag, hotel), (one_tag_featured, hotel), (two_tags, hotel)]
    found = await search(pairs, tags=["style:beach", "rhythm:calm"])
    assert [view.id for view in found] == [two_tags.id, one_tag_featured.id, one_tag.id]


async def test_without_tags_every_fitting_offer_comes_back_featured_first():
    hotel = _partner()
    plain = _offer(hotel, title="A plain room", tags=("style:city",))
    featured = _offer(hotel, title="Z featured room", featured=True)
    found = await search([(plain, hotel), (featured, hotel)], tags=[])
    assert [view.id for view in found] == [featured.id, plain.id]


async def test_unknown_destination_finds_nothing():
    hotel = _partner(country="Greece", city="Chania")
    assert await search([(_offer(hotel), hotel)], country="Japan", city="Kyoto") == []
