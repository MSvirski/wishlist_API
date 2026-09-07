from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm  # <-- Добавили импорт
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db

from . import models, schemas
from .security import create_access_token, get_password_hash, verify_password

router = APIRouter()

# Эндпоинт для регистрации

@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    # Приводим email к нижнему регистру для исключения дубликатов вида User@Mail.com и user@mail.com
    email_lower = user.email.lower()

    # 1. Быстрая пре-проверка на существование
    query_email = select(models.User).where(models.User.email == email_lower)
    result_email = await db.execute(query_email)
    if result_email.scalars().one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже зарегистрирован"
        )

    query_username = select(models.User).where(models.User.username == user.username)
    result_username = await db.execute(query_username)
    if result_username.scalars().one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким именем уже зарегистрирован"
        )

    # 2. Хэшируем пароль
    hashed_pwd = get_password_hash(user.password)

    # 3. Создаем объект модели (записываем уже нормализованный email)
    new_user = models.User(
        username=user.username,
        email=email_lower,
        hashed_password=hashed_pwd
    )

    # 4. Сохраняем в базу данных
    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
    except IntegrityError as e:
        # Если два запроса проскочили SELECT одновременно, Postgres на этапе COMMIT
        # выбросит ошибку уникальности unique=True. Ловим её здесь.
        await db.rollback()  # откатываем сломанную транзакцию

        # Проверяем, по какому именно полю произошла ошибка уникальности
        error_msg = str(e.orig)
        if "email" in error_msg:
            detail_msg = "Пользователь с таким email уже зарегистрирован (конфликт параллельных запросов)"
        elif "username" in error_msg:
            detail_msg = "Пользователь с таким именем уже зарегистрирован (конфликт параллельных запросов)"
        else:
            detail_msg = "Данные уже используются"

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail_msg
        )

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
