import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.database import Base, get_db
from app.main import app

# Настройка тестовой БД
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL"
)

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


# Фикстура для транзакционной изоляции (Rollback после каждого теста)
@pytest.fixture
async def db_session():
    """Создает изолированную сессию для теста и откатывает её в конце."""
    async with engine_test.connect() as connection:
        # Открываем внешнюю транзакцию в соединении
        transaction = await connection.begin()

        # Создаем сессию, привязанную к этому соединению
        async with AsyncSessionTest(bind=connection) as session:
            yield session  # Сессия передается в тест или в override_get_db

            # Закрываем сессию явным образом
            await session.close()

        # Откатываем ВСЕ изменения, сделанные в рамках этого теста
        await transaction.rollback()

# 4. Асинхронный тестовый клиент с автоматической подменой зависимостей
@pytest.fixture
async def ac(db_session):
    """Тестовый клиент, который использует транзакционную сессию db_session."""

    # Функция-подмена подставляет ровно ту сессию, которая сейчас будет откачена
    async def override_get_db():
        yield db_session
    # Включаем подмену базы данных для роутов
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    # Сбрасываем подмену
    app.dependency_overrides.clear()
