import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.database import Base, get_db
from app.main import app

# Настройка тестовой БД
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:qwerty123@db-test:5432/pet_wishlist_test_db"

engine_test = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,  # <--- КРИТИЧЕСКИ ВАЖНО ДЛЯ ТЕСТОВ
)

AsyncSessionTest = async_sessionmaker(bind=engine_test, class_=AsyncSession, expire_on_commit=False)


# Асинхронная фикстура в рамках одного цикла событий
@pytest.fixture(autouse=True, scope="session")
async def prepare_database():
    # Создаем таблицы
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield  # Здесь выполняются тесты

    # Удаляем таблицы в том же цикле событий без всяких конфликтов
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# 3. функция для подмены сессии в FastAPI (использовать тестовую БД вместо основной)
async def override_get_db():
    async with AsyncSessionTest() as session:
        yield session


# 4. Асинхронный тестовый клиент с автоматической подменой зависимостей
@pytest.fixture
async def ac():
    # Включаем подмену базы данных для роутов
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    # Сбрасываем подмену
    app.dependency_overrides.clear()
