from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Замените путь ниже на ваш реальный импорт зависимости аутентификации
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.database import get_db
from app.friends import schemas
from app.friends.models import Friendship, FriendshipStatus

router = APIRouter()


# 1. ОТПРАВКА ЗАПРОСА ПО USERNAME
@router.post("/request", status_code=status.HTTP_201_CREATED)
async def send_friend_request_by_username(
        payload: schemas.FriendRequestCreate,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    # Проверяем, не пытается ли пользователь добавить самого себя
    if current_user.username == payload.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя отправить запрос в друзья самому себе"
        )

    # Ищем пользователя, кому отправляют запрос, по username
    query_friend = select(User).where(User.username == payload.username)
    result_friend = await db.execute(query_friend)
    friend = result_friend.scalars().one_or_none()

    if not friend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь с таким именем не найден"
        )

    # Проверяем, существуют ли уже какие-либо отношения между ними
    query_existing = select(Friendship).where(
        ((Friendship.user_id == current_user.id) & (Friendship.friend_id == friend.id)) |
        ((Friendship.user_id == friend.id) & (Friendship.friend_id == current_user.id))
    )
    result_existing = await db.execute(query_existing)
    existing_relation = result_existing.scalars().one_or_none()

    if existing_relation:
        if existing_relation.relation == FriendshipStatus.ACCEPTED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Вы уже друзья")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Запрос уже существует или ожидает ответа")

    # Создаем новую запись
    new_request = Friendship(
        user_id=current_user.id,
        friend_id=friend.id,
        relation=FriendshipStatus.PENDING
    )
    db.add(new_request)
    await db.commit()

    return {"detail": f"Запрос в друзья пользователю {friend.username} успешно отправлен"}


# 2. ПОЛУЧЕНИЕ СПИСКА ВХОДЯЩИХ ЗАПРОСОВ (Кто хочет со мной дружить)
@router.get("/requests/incoming", response_model=List[schemas.UserFriendInfo])
async def get_incoming_requests(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    # Ищем пользователей, которые отправили нам (friend_id == current_user.id) запрос со статусом PENDING
    query = (
        select(User)
        .join(Friendship, Friendship.user_id == User.id)
        .where(Friendship.friend_id == current_user.id)
        .where(Friendship.relation == FriendshipStatus.PENDING)
    )
    result = await db.execute(query)
    return result.scalars().all()


# 3. ПОЛУЧЕНИЕ СПИСКА ИСХОДЯЩИХ ЗАПРОСОВ (Кому я отправил запрос)
@router.get("/requests/outgoing", response_model=List[schemas.UserFriendInfo])
async def get_outgoing_requests(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    # Ищем пользователей, кому мы (user_id == current_user.id) отправили запрос со статусом PENDING
    query = (
        select(User)
        .join(Friendship, Friendship.friend_id == User.id)
        .where(Friendship.user_id == current_user.id)
        .where(Friendship.relation == FriendshipStatus.PENDING)
    )
    result = await db.execute(query)
    return result.scalars().all()


# 4. ПРИНЯТИЕ ЗАПРОСА В ДРУЗЬЯ (По ID отправителя)
@router.post("/accept/{sender_id}")
async def accept_friend_request(
        sender_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    query = select(Friendship).where(
        (Friendship.user_id == sender_id) &
        (Friendship.friend_id == current_user.id) &
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
    return {"detail": "Запрос принят. Вы теперь друзья!"}


# 5. ОТКЛОНЕНИЕ ЗАПРОСА / УДАЛЕНИЕ ЗАЯВКИ
@router.post("/decline/{user_id}")
async def decline_or_cancel_request(
        user_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """
    Эндпоинт "два в одном":
    - Отклоняет входящий запрос (если вам прислали, а вы не хотите дружить)
    - Отменяет исходящий запрос (если вы передумали дружить)
    """
    query = select(Friendship).where(
        (Friendship.relation == FriendshipStatus.PENDING) & (
                ((Friendship.user_id == user_id) & (Friendship.friend_id == current_user.id)) |  # Входящий
                ((Friendship.user_id == current_user.id) & (Friendship.friend_id == user_id))  # Исходящий
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
    return {"detail": "Запрос успешно отклонен или отменен"}
