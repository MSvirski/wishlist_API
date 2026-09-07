import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

# Строка подключения: postgresql://логин:пароль@хост:порт/имя_базы
DATABASE_URL = os.getenv("DB_CONNECTION_STRING")

# 1. Используем асинхронное свойство database_url_async (с протоколом postgresql+asyncpg://)
engine = create_async_engine(DATABASE_URL, echo=True)

# 2. Создаем фабрику асинхронных сессий
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)

# 3. Современный базовый класс для моделей SQLAlchemy 2.0
class Base(DeclarativeBase):
    pass

# 4. Асинхронная зависимость для получения сессии БД в эндпоинтах
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
