from pydantic import BaseModel, EmailStr

# Базовая схема для пользователя (то, что общее для ввода и вывода)
class UserBase(BaseModel):
    username: str
    email: EmailStr

# Схема, которую мы ждем при регистрации (клиент присылает имя, email и пароль)
class UserCreate(UserBase):
    password: str

# Схема, которую мы будем отдавать клиенту обратно (пароль возвращать нельзя!)
class UserResponse(UserBase):
    id: int

    # Этот подкласс нужен, чтобы Pydantic умел читать данные прямо из моделей SQLAlchemy
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None
