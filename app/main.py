from fastapi import FastAPI

from app.auth.router import router as auth_router

from .auth import models
from .database import engine

# Импортируем функцию проверки пароля и создания токена


models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="WishlistApp")

@app.get("/")
def read_root():
    return {"message": "База данных PostgreSQL успешно подключена! Перейдите по адресу http://localhost:8000/docs#/"}

# Подключаем роутеры с красивыми префиксами и тегами для Swagger
app.include_router(auth_router, prefix="/auth", tags=["Авторизация"])
