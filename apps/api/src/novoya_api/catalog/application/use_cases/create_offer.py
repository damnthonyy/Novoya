from dataclasses import dataclass
from datetime import date
from uuid import UUID, uuid4

from novoya_api.catalog.application.ports import OfferRepository, PartnerRepository
from novoya_api.catalog.domain import (
    Offer,
    OfferKind,
    PartnerNotFound,
    normalize_place,
    normalize_tags,
)
from novoya_api.shared.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class CreateOfferCommand:
    partner_id: UUID
    kind: OfferKind
    title: str
    description: str
    country: str
    city: str
    min_persons: int
    max_persons: int
    available_from: date
    available_to: date
    tags: tuple[str, ...]
    featured: bool = False
    active: bool = True


class CreateOffer:
    def __init__(
        self, offers: OfferRepository, partners: PartnerRepository, uow: UnitOfWork
    ) -> None:
        self._offers = offers
        self._partners = partners
        self._uow = uow

    async def __call__(self, cmd: CreateOfferCommand) -> Offer:
        if await self._partners.get(cmd.partner_id) is None:
            raise PartnerNotFound("no such partner")
        offer = Offer(
            id=uuid4(),
            partner_id=cmd.partner_id,
            kind=cmd.kind,
            title=cmd.title.strip(),
            description=cmd.description.strip(),
            country=normalize_place(cmd.country),
            city=normalize_place(cmd.city),
            min_persons=cmd.min_persons,
            max_persons=cmd.max_persons,
            available_from=cmd.available_from,
            available_to=cmd.available_to,
            tags=normalize_tags(cmd.tags),
            featured=cmd.featured,
            active=cmd.active,
        )
        await self._offers.add(offer)
        await self._uow.commit()
        return offer
