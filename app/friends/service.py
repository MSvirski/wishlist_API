from typing import List

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.friends import schemas
from app.friends.models import Friendship, FriendshipStatus


class FriendshipService:


    @staticmethod
    async def send_request(
        sender: User,
        payload: schemas.FriendRequestCreate,
        db: AsyncSession
    ) -> User:
        # Проверяем, не пытается ли пользователь добавить самого себя
        if sender.username == payload.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя отправить запрос в друзья самому себе"
            )

        # Ищем пользователя по username
        query_friend = select(User).where(User.username == payload.username)
        result_friend = await db.execute(query_friend)
        friend = result_friend.scalars().one_or_none()

        if not friend:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь с таким именем не найден"
            )

        # Проверяем существующие отношения
        query_existing = select(Friendship).where(
            ((Friendship.user_id == sender.id) & (Friendship.friend_id == friend.id)) |
            ((Friendship.user_id == friend.id) & (Friendship.friend_id == sender.id))
        )
        result_existing = await db.execute(query_existing)
        existing_relation = result_existing.scalars().one_or_none()

        if existing_relation:
            if existing_relation.relation == FriendshipStatus.ACCEPTED:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Вы уже друзья")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Запрос уже существует")

        # Создаем новую запись
        new_request = Friendship(
            user_id=sender.id,
            friend_id=friend.id,
            relation=FriendshipStatus.PENDING
        )
        db.add(new_request)
        await db.commit()
        return friend

    @staticmethod
    async def get_incoming_requests(user_id: int, db: AsyncSession) -> List[User]:
        query = (
            select(User)
            .join(Friendship, Friendship.user_id == User.id)
            .where(Friendship.friend_id == user_id)
            .where(Friendship.relation == FriendshipStatus.PENDING)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_outgoing_requests(user_id: int, db: AsyncSession) -> List[User]:
        query = (
            select(User)
            .join(Friendship, Friendship.friend_id == User.id)
            .where(Friendship.user_id == user_id)
            .where(Friendship.relation == FriendshipStatus.PENDING)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def accept_request(sender_id: int, recipient_id: int, db: AsyncSession) -> None:
        query = select(Friendship).where(
            (Friendship.user_id == sender_id) &
            (Friendship.friend_id == recipient_id) &
            (Friendship.relation == FriendshipStatus.PENDING)
        )
        result = await db.execute(query)
        request = result.scalars().one_or_none()

        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Входящий запрос от этого пользователя не найден"
            )

        request.relation = FriendshipStatus.ACCEPTED
        await db.commit()

    @staticmethod
    async def decline_or_cancel_request(user_id: int, current_user_id: int, db: AsyncSession) -> None:
        query = select(Friendship).where(
            (Friendship.relation == FriendshipStatus.PENDING) & (
                ((Friendship.user_id == user_id) & (Friendship.friend_id == current_user_id)) |
                ((Friendship.user_id == current_user_id) & (Friendship.friend_id == user_id))
            )
        )
        result = await db.execute(query)
        request = result.scalars().one_or_none()

        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Активный запрос между вами и этим пользователем не найден"
            )

        await db.delete(request)
        await db.commit()

    @staticmethod
    async def get_confirmed_friends(user_id: int, db: AsyncSession) -> List[User]:
        """Получение списка подтвержденных друзей (двусторонняя связь)"""
        stmt = select(Friendship).where(
            or_(Friendship.user_id == user_id, Friendship.friend_id == user_id),
            Friendship.relation == FriendshipStatus.ACCEPTED
        )
        result = await db.execute(stmt)
        friendships = result.scalars().all()

        friend_ids = [f.friend_id if f.user_id == user_id else f.user_id for f in friendships]

        if not friend_ids:
            return []

        users_stmt = select(User).where(User.id.in_(friend_ids))
        users_result = await db.execute(users_stmt)
        return list(users_result.scalars().all())
