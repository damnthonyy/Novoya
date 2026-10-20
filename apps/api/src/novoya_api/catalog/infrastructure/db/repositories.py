"""Repositories of the catalog module. They map rows to entities: no ORM object leaves this file."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from novoya_api.catalog.domain import Offer, OfferKind, Partner, PartnerKind
from novoya_api.catalog.infrastructure.db.models import OfferRow, PartnerRow


def partner_to_entity(row: PartnerRow) -> Partner:
    return Partner(
        id=row.id,
        name=row.name,
        kind=PartnerKind(row.kind),
        country=row.country,
        city=row.city,
        contact_email=row.contact_email,
        contact_phone=row.contact_phone,
        active=row.active,
    )


def offer_to_entity(row: OfferRow) -> Offer:
    return Offer(
        id=row.id,
        partner_id=row.partner_id,
        kind=OfferKind(row.kind),
        title=row.title,
        description=row.description,
        country=row.country,
        city=row.city,
        min_persons=row.min_persons,
        max_persons=row.max_persons,
        available_from=row.available_from,
        available_to=row.available_to,
        tags=tuple(row.tags),
        featured=row.featured,
        active=row.active,
    )


def _apply_partner(row: PartnerRow, partner: Partner) -> None:
    row.name = partner.name
    row.kind = partner.kind.value
    row.country = partner.country
    row.city = partner.city
    row.contact_email = partner.contact_email
    row.contact_phone = partner.contact_phone
    row.active = partner.active


def _apply_offer(row: OfferRow, offer: Offer) -> None:
    row.partner_id = offer.partner_id
    row.kind = offer.kind.value
    row.title = offer.title
    row.description = offer.description
    row.country = offer.country
    row.city = offer.city
    row.min_persons = offer.min_persons
    row.max_persons = offer.max_persons
    row.available_from = offer.available_from
    row.available_to = offer.available_to
    row.tags = list(offer.tags)
    row.featured = offer.featured
    row.active = offer.active


class SqlPartnerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[Partner]:
        stmt = select(PartnerRow).order_by(PartnerRow.name, PartnerRow.id)
        rows = (await self._session.scalars(stmt)).all()
        return [partner_to_entity(row) for row in rows]

    async def get(self, partner_id: UUID) -> Partner | None:
        row = await self._session.get(PartnerRow, partner_id)
        return partner_to_entity(row) if row is not None else None

    async def add(self, partner: Partner) -> None:
        row = PartnerRow(id=partner.id)
        _apply_partner(row, partner)
        self._session.add(row)

    async def save(self, partner: Partner) -> None:
        row = await self._session.get(PartnerRow, partner.id)
        assert row is not None
        _apply_partner(row, partner)


class SqlOfferRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_with_partners(self) -> list[tuple[Offer, Partner]]:
        stmt = (
            select(OfferRow, PartnerRow)
            .join(PartnerRow, OfferRow.partner_id == PartnerRow.id)
            .order_by(OfferRow.title, OfferRow.id)
        )
        rows = (await self._session.execute(stmt)).all()
        return [(offer_to_entity(offer), partner_to_entity(partner)) for offer, partner in rows]

    async def list_listed_destinations(self) -> list[tuple[str, str]]:
        stmt = (
            select(OfferRow.country, OfferRow.city)
            .join(PartnerRow, OfferRow.partner_id == PartnerRow.id)
            .where(OfferRow.active.is_(True), PartnerRow.active.is_(True))
            .distinct()
            .order_by(OfferRow.country, OfferRow.city)
        )
        return [(country, city) for country, city in (await self._session.execute(stmt)).all()]

    async def list_at(self, country: str, city: str | None) -> list[tuple[Offer, Partner]]:
        stmt = (
            select(OfferRow, PartnerRow)
            .join(PartnerRow, OfferRow.partner_id == PartnerRow.id)
            .where(func.lower(OfferRow.country) == country.lower())
        )
        if city is not None:
            stmt = stmt.where(func.lower(OfferRow.city) == city.lower())
        rows = (await self._session.execute(stmt)).all()
        return [(offer_to_entity(offer), partner_to_entity(partner)) for offer, partner in rows]

    async def get(self, offer_id: UUID) -> Offer | None:
        row = await self._session.get(OfferRow, offer_id)
        return offer_to_entity(row) if row is not None else None

    async def list_by_ids(self, ids: Sequence[UUID]) -> list[tuple[Offer, Partner]]:
        if not ids:
            return []
        stmt = (
            select(OfferRow, PartnerRow)
            .join(PartnerRow, OfferRow.partner_id == PartnerRow.id)
            .where(OfferRow.id.in_(ids))
        )
        found = {
            offer.id: (offer_to_entity(offer), partner_to_entity(partner))
            for offer, partner in (await self._session.execute(stmt)).all()
        }
        return [found[offer_id] for offer_id in ids if offer_id in found]

    async def add(self, offer: Offer) -> None:
        row = OfferRow(id=offer.id)
        _apply_offer(row, offer)
        self._session.add(row)

    async def save(self, offer: Offer) -> None:
        row = await self._session.get(OfferRow, offer.id)
        assert row is not None
        _apply_offer(row, offer)
