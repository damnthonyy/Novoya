from sqlalchemy import delete

from novoya_api.catalog.infrastructure.db.models import OfferRow, PartnerRow
from novoya_api.catalog.infrastructure.seed.data import OFFERS, PARTNERS
from novoya_api.shared.infrastructure.db.session import get_sessionmaker


async def seed_catalog() -> None:
    """Replace partners and offers with the shared seed catalog."""
    async with get_sessionmaker()() as session:
        await session.execute(delete(OfferRow))
        await session.execute(delete(PartnerRow))
        session.add_all(PartnerRow(**row) for row in PARTNERS)
        session.add_all(OfferRow(**row) for row in OFFERS)
        await session.commit()
