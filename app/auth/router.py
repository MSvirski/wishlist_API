from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm  # <-- Добавили импорт
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from app.database import get_db

from . import models, schemas
from .security import create_access_token, get_password_hash, verify_password

router = APIRouter()

# Эндпоинт для регистрации
@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # 1. Проверяем, существует ли уже пользователь с таким email
    query = select(models.User).where(models.User.email == user.email)
    result = await db.execute(query)
    db_user_email = result.scalars().one_or_none()

    if db_user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже зарегистрирован"
        )

    # 2. Проверяем, существует ли уже пользователь с таким именем (username)
    query = select(models.User).where(models.User.username == user.username)
    result = await db.execute(query)
    db_user_name = result.scalars().one_or_none()
    if db_user_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким именем уже зарегистрирован"
        )

    # 3. Хэшируем пароль перед сохранением
    hashed_pwd = get_password_hash(user.password)

    # 4. Создаем объект модели SQLAlchemy
    new_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_pwd
    )

    # 5. Сохраняем в базу данных
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Благодаря response_model=schemas.UserResponse, FastAPI сам вернет только id, username и email
    return new_user


# Точка входа для получения токена
@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db)
):
    # 1. Ищем пользователя строго по EMAIL (в поле form_data.username в Swagger вводится почта)
    query = select(models.User).where(models.User.email == form_data.username)
    result = await db.execute(query)
    user = result.scalars().one_or_none()

    # 2. Проверка существования и пароля
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Зашиваем в токен ID пользователя, приведенный к строке
    access_token = create_access_token(data={"sub": str(user.id)})

    return {"access_token": access_token, "token_type": "bearer"}
