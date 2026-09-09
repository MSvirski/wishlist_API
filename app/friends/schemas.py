from pydantic import BaseModel, ConfigDict, EmailStr  # <-- Добавили импорт ConfigDict

from app.friends.models import FriendshipStatus


# Схема для отправки запроса по username
class FriendRequestCreate(BaseModel):
    username: str

# Схема для отображения пользователя в списках заявок/друзей
class UserFriendInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # <-- Новый синтаксис Pydantic V2

    id: int
    username: str
    email: EmailStr

# Схема ответа, показывающая детали заявки
class FriendRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # <-- Новый синтаксис Pydantic V2

    user_id: int
    friend_id: int
    relation: FriendshipStatus
