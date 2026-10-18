from sqlalchemy.ext.asyncio import AsyncSession

from novoya_api.wishes.domain.wish import Wish
from novoya_api.wishes.infrastructure.db.models import WishModel


class SqlWishRepository:
    """WishRepository on PostgreSQL. Maps the entity to a row; the use case commits."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, wish: Wish) -> None:
        self._session.add(
            WishModel(
                id=wish.id,
                user_id=wish.user_id,
                text=wish.text,
                destination_country=wish.destination.country if wish.destination else None,
                destination_city=wish.destination.city if wish.destination else None,
                status=wish.status.value,
                panel_json=wish.panel.to_dict() if wish.panel else None,
                created_at=wish.created_at,
                updated_at=wish.updated_at,
            )
        )
