from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .models import WishItem
from .schemas import WishCreate


class WishService:
    @staticmethod
    async def create_wish(db: AsyncSession, wish_data: WishCreate, user_id: int) -> WishItem:
        new_item = WishItem(
            title=wish_data.title,
            description=wish_data.description,
            link=wish_data.link,
            priority=wish_data.priority,
            user_id=user_id
        )
        db.add(new_item)
        await db.commit()      # Асинхронный коммит
        await db.refresh(new_item)
        return new_item

    @staticmethod
    async def get_user_wishes(db: AsyncSession, user_id: int):
        # Асинхронный синтаксис запросов SQLAlchemy 2.0
        query = select(WishItem).where(WishItem.user_id == user_id)
        result = await db.execute(query)
        return result.scalars().all()
