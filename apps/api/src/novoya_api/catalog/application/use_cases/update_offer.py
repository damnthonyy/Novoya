from dataclasses import dataclass, replace
from datetime import date
from uuid import UUID

from novoya_api.catalog.application.ports import OfferRepository
from novoya_api.catalog.domain import (
    Offer,
    OfferKind,
    OfferNotFound,
    normalize_place,
    normalize_tags,
)
from novoya_api.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class UpdateOfferCommand:
    offer_id: UUID
    kind: OfferKind | None = None
    title: str | None = None
    description: str | None = None
    country: str | None = None
    city: str | None = None
    min_persons: int | None = None
    max_persons: int | None = None
    available_from: date | None = None
    available_to: date | None = None
    tags: tuple[str, ...] | None = None
    featured: bool | None = None
    active: bool | None = None


class UpdateOffer:
    def __init__(self, offers: OfferRepository, uow: UnitOfWork) -> None:
        self._offers = offers
        self._uow = uow

    async def __call__(self, cmd: UpdateOfferCommand) -> Offer:
        offer = await self._offers.get(cmd.offer_id)
        if offer is None:
            raise OfferNotFound("no such offer")
        updated = replace(
            offer,
            kind=cmd.kind if cmd.kind is not None else offer.kind,
            title=cmd.title.strip() if cmd.title is not None else offer.title,
            description=(
                cmd.description.strip() if cmd.description is not None else offer.description
            ),
            country=normalize_place(cmd.country) if cmd.country is not None else offer.country,
            city=normalize_place(cmd.city) if cmd.city is not None else offer.city,
            min_persons=cmd.min_persons if cmd.min_persons is not None else offer.min_persons,
            max_persons=cmd.max_persons if cmd.max_persons is not None else offer.max_persons,
            available_from=(
                cmd.available_from if cmd.available_from is not None else offer.available_from
            ),
            available_to=cmd.available_to if cmd.available_to is not None else offer.available_to,
            tags=normalize_tags(cmd.tags) if cmd.tags is not None else offer.tags,
            featured=cmd.featured if cmd.featured is not None else offer.featured,
            active=cmd.active if cmd.active is not None else offer.active,
        )
        await self._offers.save(updated)
        await self._uow.commit()
        return updated
