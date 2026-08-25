import os

from dotenv import load_dotenv
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta, timezone

load_dotenv()

# Говорим passlib использовать алгоритм bcrypt для хэширования
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Функция, которая принимает чистый пароль и возвращает хэш
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Функция для проверки соответствия чистого пароля и хэша из базы
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


SECRET_KEY = os.getenv("SECRET_KEY", "default_fallback_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Функция для создания JWT-токена
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    # Устанавливаем время истечения токена (текущее время UTC + 30 минут)
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    # Кодируем данные в токен с помощью секретного ключа
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt