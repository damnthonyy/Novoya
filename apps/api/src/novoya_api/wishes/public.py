"""What other modules may use from wishes. Nothing else in wishes may be imported.

- owner_id(wish_id) -> the user who sent the wish, or None when there is none

Planned:
- get_wish(wish_id) -> WishView (text, destination, selected tags, budget, travellers, dates)
- mark_planned(wish_id)
- delete_for_user(user_id)
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from novoya_api.wishes.infrastructure.db.repository import SqlWishRepository


async def owner_id(wish_id: UUID, *, session: AsyncSession) -> UUID | None:
    """The user who sent this wish. None when the wish is missing."""
    wish = await SqlWishRepository(session).get(wish_id)
    return None if wish is None else wish.user_id
