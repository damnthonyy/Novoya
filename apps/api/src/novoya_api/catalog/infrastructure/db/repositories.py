"""Repositories of the catalog module. They map rows to entities: no ORM object leaves this file."""

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


class SqlPartnerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[Partner]:
        rows = (await self._session.scalars(select(PartnerRow))).all()
        return [partner_to_entity(row) for row in rows]


class SqlOfferRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_with_partners(self) -> list[tuple[Offer, Partner]]:
        stmt = select(OfferRow, PartnerRow).join(PartnerRow, OfferRow.partner_id == PartnerRow.id)
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
