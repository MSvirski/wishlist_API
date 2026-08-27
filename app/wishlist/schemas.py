from pydantic import BaseModel, ConfigDict, Field

from .models import PriorityEnum


# Базовые поля для желания
class WishBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="Название подарка")
    description: str | None = Field(None, max_length=500, description="Описание или детали")
    link: str | None = Field(None, description="Ссылка на предмет")
    priority: PriorityEnum = Field(PriorityEnum.MEDIUM, description="Приоритет важности")

# Схема для создания (запроса)
class WishCreate(WishBase):
    pass

# Схема для ответа (Response) — сервер добавляет ID, статус брони и id владельца
class WishResponse(WishBase):
    id: int
    user_id: int
    booked_by_user_id: int | None = None # Будет отдавать ID юзера или null

    model_config = ConfigDict(from_attributes=True)
