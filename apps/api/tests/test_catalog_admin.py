"""Admin partners and offers: use cases on fakes, HTTP with a signed-in agent."""

from collections.abc import AsyncIterator
from datetime import date
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from novoya_api.accounts.application.dto import CurrentUserView
from novoya_api.accounts.domain.role import Role
from novoya_api.accounts.domain.value_objects import Email, UserId
from novoya_api.accounts.public import current_user
from novoya_api.catalog.application.use_cases.create_offer import CreateOffer, CreateOfferCommand
from novoya_api.catalog.application.use_cases.create_partner import (
    CreatePartner,
    CreatePartnerCommand,
)
from novoya_api.catalog.application.use_cases.list_offers import ListOffers
from novoya_api.catalog.application.use_cases.list_partners import ListPartners
from novoya_api.catalog.application.use_cases.update_offer import UpdateOffer, UpdateOfferCommand
from novoya_api.catalog.application.use_cases.update_partner import (
    UpdatePartner,
    UpdatePartnerCommand,
)
from novoya_api.catalog.domain import (
    InvalidOffer,
    Offer,
    OfferKind,
    OfferNotFound,
    Partner,
    PartnerKind,
    PartnerNotFound,
)
from novoya_api.catalog.presentation.http.dependencies import (
    get_create_offer,
    get_create_partner,
    get_list_offers,
    get_list_partners,
    get_update_offer,
    get_update_partner,
)
from novoya_api.main import create_app
from novoya_api.shared.domain.value_objects import Locale

USER_ID = UUID("00000000-0000-0000-0000-000000000001")
SEASON = (date(2026, 4, 1), date(2026, 10, 31))


class FakeUow:
    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        pass


class FakePartners:
    def __init__(self, partners: list[Partner] | None = None) -> None:
        self.by_id = {partner.id: partner for partner in partners or []}

    async def list_all(self) -> list[Partner]:
        return sorted(self.by_id.values(), key=lambda partner: (partner.name, str(partner.id)))

    async def get(self, partner_id: UUID) -> Partner | None:
        return self.by_id.get(partner_id)

    async def add(self, partner: Partner) -> None:
        self.by_id[partner.id] = partner

    async def save(self, partner: Partner) -> None:
        self.by_id[partner.id] = partner


class FakeOffers:
    def __init__(self, offers: list[Offer] | None = None) -> None:
        self.by_id = {offer.id: offer for offer in offers or []}
        self.partners: FakePartners | None = None

    async def list_with_partners(self) -> list[tuple[Offer, Partner]]:
        assert self.partners is not None
        pairs = []
        for offer in self.by_id.values():
            partner = self.partners.by_id[offer.partner_id]
            pairs.append((offer, partner))
        return sorted(pairs, key=lambda item: (item[0].title, str(item[0].id)))

    async def list_listed_destinations(self) -> list[tuple[str, str]]:
        return []

    async def list_at(self, country: str, city: str | None) -> list[tuple[Offer, Partner]]:
        return []

    async def get(self, offer_id: UUID) -> Offer | None:
        return self.by_id.get(offer_id)

    async def add(self, offer: Offer) -> None:
        self.by_id[offer.id] = offer

    async def save(self, offer: Offer) -> None:
        self.by_id[offer.id] = offer


def _partner(**overrides: object) -> Partner:
    values: dict[str, object] = {
        "id": uuid4(),
        "name": "Elounda Bay House",
        "kind": PartnerKind.HOTEL,
        "country": "Greece",
        "city": "Chania",
        "contact_email": "stay@elounda.example",
        "contact_phone": "+30 28210 00001",
        "active": True,
    }
    values.update(overrides)
    return Partner(**values)  # type: ignore[arg-type]


def _offer(partner: Partner, **overrides: object) -> Offer:
    values: dict[str, object] = {
        "id": uuid4(),
        "partner_id": partner.id,
        "kind": OfferKind.HOTEL,
        "title": "Sea room",
        "description": "A room",
        "country": "Greece",
        "city": "Chania",
        "min_persons": 2,
        "max_persons": 4,
        "available_from": SEASON[0],
        "available_to": SEASON[1],
        "tags": ("style:beach",),
        "featured": False,
        "active": True,
    }
    values.update(overrides)
    return Offer(**values)  # type: ignore[arg-type]


NEW_PARTNER = CreatePartnerCommand(
    name="  New Riad ",
    kind=PartnerKind.HOTEL,
    country="morocco",
    city="marrakech",
    contact_email="  hello@riad.example ",
    contact_phone=" +212 000 ",
)


# Use cases


async def test_create_partner_title_cases_the_place_and_strips_fields():
    partners = FakePartners()
    created = await CreatePartner(partners, FakeUow())(NEW_PARTNER)

    assert created.name == "New Riad"
    assert created.country == "Morocco"
    assert created.city == "Marrakech"
    assert created.contact_email == "hello@riad.example"
    assert partners.by_id[created.id] == created


async def test_list_partners_includes_inactive_ones():
    closed = _partner(name="Closed", active=False)
    partners = FakePartners([closed, _partner(name="Open")])

    listed = await ListPartners(partners)()

    assert [partner.name for partner in listed] == ["Closed", "Open"]


async def test_update_partner_can_deactivate_without_touching_offers():
    partner = _partner()
    partners = FakePartners([partner])

    updated = await UpdatePartner(partners, FakeUow())(
        UpdatePartnerCommand(partner_id=partner.id, active=False)
    )

    assert updated.active is False
    assert updated.name == partner.name


async def test_update_missing_partner_is_not_found():
    with pytest.raises(PartnerNotFound):
        await UpdatePartner(FakePartners(), FakeUow())(UpdatePartnerCommand(partner_id=uuid4()))


async def test_create_offer_needs_an_existing_partner():
    with pytest.raises(PartnerNotFound):
        await CreateOffer(FakeOffers(), FakePartners(), FakeUow())(
            CreateOfferCommand(
                partner_id=uuid4(),
                kind=OfferKind.HOTEL,
                title="Stay",
                description="A room",
                country="Greece",
                city="Chania",
                min_persons=1,
                max_persons=2,
                available_from=SEASON[0],
                available_to=SEASON[1],
                tags=("style:beach",),
            )
        )


async def test_create_offer_normalizes_tags_and_place():
    partner = _partner()
    offers = FakeOffers()
    offers.partners = FakePartners([partner])

    created = await CreateOffer(offers, offers.partners, FakeUow())(
        CreateOfferCommand(
            partner_id=partner.id,
            kind=OfferKind.HOTEL,
            title="Stay",
            description="A room",
            country="greece",
            city="chania",
            min_persons=2,
            max_persons=4,
            available_from=SEASON[0],
            available_to=SEASON[1],
            tags=("STYLE:Beach", "style:beach"),
        )
    )

    assert created.country == "Greece"
    assert created.tags == ("style:beach",)


async def test_create_offer_rejects_inverted_person_limits():
    partner = _partner()
    with pytest.raises(InvalidOffer):
        await CreateOffer(FakeOffers(), FakePartners([partner]), FakeUow())(
            CreateOfferCommand(
                partner_id=partner.id,
                kind=OfferKind.HOTEL,
                title="Stay",
                description="A room",
                country="Greece",
                city="Chania",
                min_persons=4,
                max_persons=2,
                available_from=SEASON[0],
                available_to=SEASON[1],
                tags=(),
            )
        )


async def test_update_offer_can_deactivate():
    partner = _partner()
    offer = _offer(partner)
    offers = FakeOffers([offer])
    offers.partners = FakePartners([partner])

    updated = await UpdateOffer(offers, FakeUow())(
        UpdateOfferCommand(offer_id=offer.id, active=False)
    )

    assert updated.active is False
    assert updated.title == offer.title


async def test_update_missing_offer_is_not_found():
    with pytest.raises(OfferNotFound):
        await UpdateOffer(FakeOffers(), FakeUow())(UpdateOfferCommand(offer_id=uuid4()))


async def test_list_offers_includes_inactive_ones():
    partner = _partner()
    hidden = _offer(partner, title="Hidden", active=False)
    shown = _offer(partner, title="Shown")
    offers = FakeOffers([hidden, shown])
    offers.partners = FakePartners([partner])

    listed = await ListOffers(offers)()

    assert [offer.title for offer in listed] == ["Hidden", "Shown"]


# HTTP


def signed_in_as(role: Role) -> CurrentUserView:
    return CurrentUserView(
        user_id=UserId(USER_ID),
        email=Email("agent@example.com"),
        name=None,
        role=role,
        locale=Locale.EN,
        session_id=USER_ID,
    )


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


def _as_agent(app, partners: FakePartners, offers: FakeOffers | None = None) -> None:
    offers = offers or FakeOffers()
    offers.partners = partners
    uow = FakeUow()
    app.dependency_overrides[current_user] = lambda: signed_in_as(Role.AGENT)
    app.dependency_overrides[get_list_partners] = lambda: ListPartners(partners)
    app.dependency_overrides[get_create_partner] = lambda: CreatePartner(partners, uow)
    app.dependency_overrides[get_update_partner] = lambda: UpdatePartner(partners, uow)
    app.dependency_overrides[get_list_offers] = lambda: ListOffers(offers)
    app.dependency_overrides[get_create_offer] = lambda: CreateOffer(offers, partners, uow)
    app.dependency_overrides[get_update_offer] = lambda: UpdateOffer(offers, uow)


async def test_admin_partners_without_a_session_returns_401(client):
    assert (await client.get("/admin/partners")).status_code == 401
    assert (await client.get("/admin/offers")).status_code == 401


async def test_admin_catalog_rejects_a_client(app, client):
    app.dependency_overrides[current_user] = lambda: signed_in_as(Role.CLIENT)

    assert (await client.get("/admin/partners")).status_code == 403
    assert (await client.get("/admin/offers")).status_code == 403


async def test_admin_can_create_list_and_deactivate_a_partner(app, client):
    partners = FakePartners()
    _as_agent(app, partners)

    created = await client.post(
        "/admin/partners",
        json={
            "name": "New Riad",
            "kind": "hotel",
            "country": "morocco",
            "city": "marrakech",
            "contact_email": "hello@riad.example",
            "contact_phone": "+212 000",
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body["country"] == "Morocco"
    assert body["city"] == "Marrakech"

    listed = await client.get("/admin/partners")
    assert listed.status_code == 200
    assert [row["id"] for row in listed.json()] == [body["id"]]

    patched = await client.patch(f"/admin/partners/{body['id']}", json={"active": False})
    assert patched.status_code == 200
    assert patched.json()["active"] is False


async def test_admin_offer_create_needs_a_partner(app, client):
    _as_agent(app, FakePartners())

    response = await client.post(
        "/admin/offers",
        json={
            "partner_id": str(uuid4()),
            "kind": "hotel",
            "title": "Stay",
            "description": "A room",
            "country": "Greece",
            "city": "Chania",
            "min_persons": 2,
            "max_persons": 4,
            "available_from": "2026-04-01",
            "available_to": "2026-10-31",
            "tags": ["style:beach"],
        },
    )
    assert response.status_code == 404
    assert response.json()["code"] == "partner_not_found"


async def test_admin_offer_rejects_inverted_person_limits(app, client):
    partner = _partner()
    _as_agent(app, FakePartners([partner]))

    response = await client.post(
        "/admin/offers",
        json={
            "partner_id": str(partner.id),
            "kind": "hotel",
            "title": "Stay",
            "description": "A room",
            "country": "Greece",
            "city": "Chania",
            "min_persons": 4,
            "max_persons": 2,
            "available_from": "2026-04-01",
            "available_to": "2026-10-31",
            "tags": ["style:beach"],
        },
    )
    assert response.status_code == 422
    assert response.json()["code"] == "invalid_offer"


async def test_admin_can_create_and_deactivate_an_offer(app, client):
    partner = _partner()
    _as_agent(app, FakePartners([partner]))

    created = await client.post(
        "/admin/offers",
        json={
            "partner_id": str(partner.id),
            "kind": "hotel",
            "title": "Stay",
            "description": "A room",
            "country": "greece",
            "city": "chania",
            "min_persons": 2,
            "max_persons": 4,
            "available_from": "2026-04-01",
            "available_to": "2026-10-31",
            "tags": ["STYLE:Beach"],
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body["tags"] == ["style:beach"]
    assert body["country"] == "Greece"

    patched = await client.patch(f"/admin/offers/{body['id']}", json={"active": False})
    assert patched.status_code == 200
    assert patched.json()["active"] is False


def test_admin_catalog_routes_are_documented(app):
    paths = app.openapi()["paths"]
    assert paths["/admin/partners"]["get"]["operationId"] == "listPartners"
    assert paths["/admin/partners"]["post"]["operationId"] == "createPartner"
    assert paths["/admin/partners/{partner_id}"]["patch"]["operationId"] == "updatePartner"
    assert paths["/admin/offers"]["get"]["operationId"] == "listOffers"
    assert paths["/admin/offers"]["post"]["operationId"] == "createOffer"
    assert paths["/admin/offers/{offer_id}"]["patch"]["operationId"] == "updateOffer"
    responses = paths["/admin/partners"]["get"]["responses"]
    for status in ("401", "403", "422"):
        ref = responses[status]["content"]["application/json"]["schema"]["$ref"]
        assert ref == "#/components/schemas/ErrorResponse", status
