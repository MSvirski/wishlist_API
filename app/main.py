from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.friends.router import router as friends_router
from app.wishlist.router import router as wishlist_router

from .database import Base, engine


# 1. Создаем асинхронный lifespan-контекст, который выполнится ОДИН раз строго при старте сервера
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Асинхронно открываем соединение от движка
    async with engine.begin() as conn:
        # Заставляем SQLAlchemy создать все таблицы асинхронно
        await conn.run_sync(Base.metadata.create_all)
    yield  # Здесь приложение начинает работать и принимать запросы
    # Тут можно написать код, который выполнится при выключении сервера (если нужно)

# 2. Передаем lifespan в инициализацию FastAPI
app = FastAPI(title="Wishlist API", version="1.0.0", lifespan=lifespan)

@app.get("/")
def read_root():
    return {"message": "База данных PostgreSQL успешно подключена! Перейдите по адресу http://localhost:8000/docs#/"}

# Подключаем роутеры
app.include_router(auth_router, prefix="/auth", tags=["Авторизация"])
app.include_router(wishlist_router, prefix="/wishes", tags=["🎁 Списки желаний"])
app.include_router(friends_router, prefix="/friends", tags=["Друзья"])
