from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.database import get_db
from app.friends import schemas
from app.friends.service import FriendshipService

router = APIRouter()


# 1. ОТПРАВКА ЗАПРОСА ПО USERNAME
@router.post("/request", status_code=status.HTTP_201_CREATED)
async def send_friend_request_by_username(
        payload: schemas.FriendRequestCreate,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    friend = await FriendshipService.send_request(current_user, payload, db)
    return {"detail": f"Запрос в друзья пользователю {friend.username} успешно отправлен"}


# 2. ПОЛУЧЕНИЕ СПИСКА ВХОДЯЩИХ ЗАПРОСОВ
@router.get("/requests/incoming", response_model=List[schemas.UserFriendInfo])
async def get_incoming_requests(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    return await FriendshipService.get_incoming_requests(current_user.id, db)


# 3. ПОЛУЧЕНИЕ СПИСКА ИСХОДЯЩИХ ЗАПРОСОВ
@router.get("/requests/outgoing", response_model=List[schemas.UserFriendInfo])
async def get_outgoing_requests(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    return await FriendshipService.get_outgoing_requests(current_user.id, db)


# 4. ПРИНЯТИЕ ЗАПРОСА В ДРУЗЬЯ
@router.post("/accept/{sender_id}")
async def accept_friend_request(
        sender_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    await FriendshipService.accept_request(sender_id, current_user.id, db)
    return {"detail": "Запрос принят. Вы теперь друзья!"}


# 5. ОТКЛОНЕНИЕ ЗАПРОСА / УДАЛЕНИЕ ЗАЯВКИ
@router.post("/decline/{user_id}")
async def decline_or_cancel_request(
        user_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    await FriendshipService.decline_or_cancel_request(user_id, current_user.id, db)
    return {"detail": "Запрос успешно отклонен или отменен"}


# 6. СПИСОК ВСЕХ ПОДТВЕРЖДЕННЫХ ДРУЗЕЙ
@router.get("", response_model=List[schemas.UserFriendInfo])
async def get_my_friends(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    return await FriendshipService.get_confirmed_friends(current_user.id, db)
