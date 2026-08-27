from pydantic import BaseModel, ConfigDict, EmailStr


# Базовая схема для пользователя (то, что общее для ввода и вывода)
class UserBase(BaseModel):
    username: str
    email: EmailStr

# Схема, которую мы ждем при регистрации (клиент присылает имя, email и пароль)
class UserCreate(UserBase):
    password: str

# Схема, которую мы будем отдавать клиенту обратно
class UserResponse(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: str | None = None
