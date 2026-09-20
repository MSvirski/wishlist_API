from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import settings


# Функция, которая принимает чистый пароль и возвращает хэш
def get_password_hash(password: str) -> str:
    """Хэширует пароль пользователя."""
    # Переводим строку в байты
    pwd_bytes = password.encode('utf-8')
    # Генерируем "соль"
    salt = bcrypt.gensalt()
    # Хэшируем и переводим обратно в строку для хранения в БД
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8')

# Функция для проверки соответствия чистого пароля и хэша из базы
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет соответствие чистого пароля хэшу из базы данных."""
    pwd_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    # Метод сам извлечет соль из хэша и сравнит их
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)


# Функция для создания JWT-токена
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    # Устанавливаем время истечения токена (текущее время UTC + 30 минут)
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    # Кодируем данные в токен с помощью секретного ключа
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
