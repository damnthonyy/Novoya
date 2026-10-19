from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from novoya_api.accounts.public import require_agent
from novoya_api.catalog.application.use_cases.create_offer import CreateOffer, CreateOfferCommand
from novoya_api.catalog.application.use_cases.create_partner import (
    CreatePartner,
    CreatePartnerCommand,
)
from novoya_api.catalog.application.use_cases.list_destinations import ListDestinations
from novoya_api.catalog.application.use_cases.list_offers import ListOffers
from novoya_api.catalog.application.use_cases.list_partners import ListPartners
from novoya_api.catalog.application.use_cases.update_offer import UpdateOffer, UpdateOfferCommand
from novoya_api.catalog.application.use_cases.update_partner import (
    UpdatePartner,
    UpdatePartnerCommand,
)
from novoya_api.catalog.domain import OfferKind, PartnerKind
from novoya_api.catalog.presentation.http.dependencies import (
    get_create_offer,
    get_create_partner,
    get_list_destinations,
    get_list_offers,
    get_list_partners,
    get_update_offer,
    get_update_partner,
)
from novoya_api.catalog.presentation.http.schemas import (
    CreateOfferRequest,
    CreatePartnerRequest,
    DestinationResponse,
    OfferResponse,
    PartnerResponse,
    UpdateOfferRequest,
    UpdatePartnerRequest,
)
from novoya_api.shared.presentation.http.errors import ErrorResponse

ERRORS = {status_code: {"model": ErrorResponse} for status_code in (401, 403, 404, 422)}

destinations_router = APIRouter(tags=["catalog"])
partners_router = APIRouter(
    prefix="/admin/partners",
    tags=["admin"],
    responses=ERRORS,
    dependencies=[Depends(require_agent)],
)
offers_router = APIRouter(
    prefix="/admin/offers",
    tags=["admin"],
    responses=ERRORS,
    dependencies=[Depends(require_agent)],
)


@destinations_router.get("/destinations", operation_id="listDestinations")
async def list_destinations(
    use_case: Annotated[ListDestinations, Depends(get_list_destinations)],
) -> list[DestinationResponse]:
    """Countries and cities with at least one listed offer. Read from the database each time."""
    return [DestinationResponse(country=country, city=city) for country, city in await use_case()]


@partners_router.get("", operation_id="listPartners")
async def list_partners(
    use_case: Annotated[ListPartners, Depends(get_list_partners)],
) -> list[PartnerResponse]:
    """All partners, including inactive ones. Agents only."""
    return [PartnerResponse.of(partner) for partner in await use_case()]


@partners_router.post("", operation_id="createPartner", status_code=status.HTTP_201_CREATED)
async def create_partner(
    body: CreatePartnerRequest,
    use_case: Annotated[CreatePartner, Depends(get_create_partner)],
) -> PartnerResponse:
    """Add a partner. Agents only."""
    partner = await use_case(
        CreatePartnerCommand(
            name=body.name,
            kind=PartnerKind(body.kind),
            country=body.country,
            city=body.city,
            contact_email=body.contact_email,
            contact_phone=body.contact_phone,
            active=body.active,
        )
    )
    return PartnerResponse.of(partner)


@partners_router.patch("/{partner_id}", operation_id="updatePartner")
async def update_partner(
    partner_id: UUID,
    body: UpdatePartnerRequest,
    use_case: Annotated[UpdatePartner, Depends(get_update_partner)],
) -> PartnerResponse:
    """Change a partner. Deactivating it hides its offers from search. Agents only."""
    partner = await use_case(
        UpdatePartnerCommand(
            partner_id=partner_id,
            name=body.name,
            kind=PartnerKind(body.kind) if body.kind is not None else None,
            country=body.country,
            city=body.city,
            contact_email=body.contact_email,
            contact_phone=body.contact_phone,
            active=body.active,
        )
    )
    return PartnerResponse.of(partner)


@offers_router.get("", operation_id="listOffers")
async def list_offers(
    use_case: Annotated[ListOffers, Depends(get_list_offers)],
) -> list[OfferResponse]:
    """All offers, including inactive ones. Agents only."""
    return [OfferResponse.of(offer) for offer in await use_case()]


@offers_router.post("", operation_id="createOffer", status_code=status.HTTP_201_CREATED)
async def create_offer(
    body: CreateOfferRequest,
    use_case: Annotated[CreateOffer, Depends(get_create_offer)],
) -> OfferResponse:
    """Add an offer for an existing partner. Agents only."""
    offer = await use_case(
        CreateOfferCommand(
            partner_id=body.partner_id,
            kind=OfferKind(body.kind),
            title=body.title,
            description=body.description,
            country=body.country,
            city=body.city,
            min_persons=body.min_persons,
            max_persons=body.max_persons,
            available_from=body.available_from,
            available_to=body.available_to,
            tags=tuple(body.tags),
            featured=body.featured,
            active=body.active,
        )
    )
    return OfferResponse.of(offer)


@offers_router.patch("/{offer_id}", operation_id="updateOffer")
async def update_offer(
    offer_id: UUID,
    body: UpdateOfferRequest,
    use_case: Annotated[UpdateOffer, Depends(get_update_offer)],
) -> OfferResponse:
    """Change an offer. Agents only."""
    offer = await use_case(
        UpdateOfferCommand(
            offer_id=offer_id,
            kind=OfferKind(body.kind) if body.kind is not None else None,
            title=body.title,
            description=body.description,
            country=body.country,
            city=body.city,
            min_persons=body.min_persons,
            max_persons=body.max_persons,
            available_from=body.available_from,
            available_to=body.available_to,
            tags=tuple(body.tags) if body.tags is not None else None,
            featured=body.featured,
            active=body.active,
        )
    )
    return OfferResponse.of(offer)


router = APIRouter()
router.include_router(destinations_router)
router.include_router(partners_router)
router.include_router(offers_router)
