from sqlalchemy import and_, func, not_, select
from sqlalchemy.ext.asyncio import AsyncSession

from novoya_api.catalog.application.dto import CatalogCounts, RowCounts
from novoya_api.catalog.infrastructure.db.models import ExtraRow, OfferRow, PartnerRow, ReviewRow


async def count_catalog(session: AsyncSession) -> CatalogCounts:
    """One query per table: only counts are read."""
    partners, offers, extras = [
        await _rows(session, model) for model in (PartnerRow, OfferRow, ExtraRow)
    ]
    hidden, published = (
        await session.execute(
            select(
                func.count().filter(ReviewRow.hidden),
                func.count().filter(not_(ReviewRow.hidden)),
            )
        )
    ).one()
    return CatalogCounts(partners, offers, extras, published, hidden)


async def _rows(session: AsyncSession, model: type[PartnerRow | OfferRow | ExtraRow]) -> RowCounts:
    active, hidden, inactive = (
        await session.execute(
            select(
                func.count().filter(and_(model.active, not_(model.hidden))),
                func.count().filter(model.hidden),
                func.count().filter(and_(not_(model.active), not_(model.hidden))),
            )
        )
    ).one()
    return RowCounts(active, hidden, inactive)
