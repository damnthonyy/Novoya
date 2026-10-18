from sqlalchemy.dialects.postgresql import insert

from novoya_api.catalog.infrastructure.db.models import OfferRow, PartnerRow
from novoya_api.catalog.infrastructure.seed.data import OFFERS, PARTNERS
from novoya_api.config import get_settings
from novoya_api.shared.infrastructure.db.session import get_sessionmaker


def _values(rows: list[dict]) -> list[dict]:
    payload: list[dict] = []
    for row in rows:
        item = dict(row)
        kind = item.get("kind")
        if hasattr(kind, "value"):
            item["kind"] = kind.value
        payload.append(item)
    return payload


def _upsert(model: type, rows: list[dict]):
    payload = _values(rows)
    stmt = insert(model).values(payload)
    updates = {key: getattr(stmt.excluded, key) for key in payload[0] if key != "id"}
    return stmt.on_conflict_do_update(index_elements=["id"], set_=updates)


async def seed_catalog() -> None:
    """Insert or refresh the shared seed catalog. Never deletes other partners or offers."""
    if get_settings().env != "development":
        raise RuntimeError("catalog seed only runs when NOVOYA_ENV is development")
    async with get_sessionmaker()() as session:
        await session.execute(_upsert(PartnerRow, PARTNERS))
        await session.execute(_upsert(OfferRow, OFFERS))
        await session.commit()
