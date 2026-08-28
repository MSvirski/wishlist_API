import os

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db

from .models import User
from .schemas import TokenData

load_dotenv()

# Указываем путь, где Swagger будет запрашивать токен при авторизации
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось валидировать токен доступа",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
        # Извлекаем ID из токена
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id_str)
    except JWTError:
        raise credentials_exception

    # Ищем пользователя в БД по его уникальному ID
    # Конвертируем строку обратно в int перед запросом
    query = select(User).where(User.id == int(token_data.user_id))
    result = await db.execute(query)
    user = result.scalars().one_or_none()

    if user is None:
        raise credentials_exception

    return user

