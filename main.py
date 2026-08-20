from fastapi import FastAPI, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

import models
import schemas
from database import engine, get_db
# Импортируем функцию проверки пароля и создания токена
from fastapi.security import OAuth2PasswordRequestForm  # <-- Добавили импорт
from security import get_password_hash, verify_password, create_access_token



models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="WishlistApp")


@app.get("/")
def read_root():
    return {"message": "База данных PostgreSQL успешно подключена! Перейдите по адресу http://localhost:8000/docs#/"}


# Эндпоинт для регистрации
@app.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # 1. Проверяем, существует ли уже пользователь с таким email
    db_user_email = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже зарегистрирован"
        )

    # 2. Проверяем, существует ли уже пользователь с таким именем (username)
    db_user_name = db.query(models.User).filter(models.User.username == user.username).first()
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
    db.commit()
    db.refresh(new_user)

    # Благодаря response_model=schemas.UserResponse, FastAPI сам вернет только id, username и email
    return new_user


# Эндпоинт для входа (логина) и получения токена
@app.post("/token", response_model=schemas.Token)
def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)
):
    # 1. Ищем пользователя в базе по username
    user = db.query(models.User).filter(models.User.username == form_data.username).first()

    # 2. Если пользователя нет или пароль не совпадает — кидаем ошибку
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Если всё правильно, создаем токен (зашиваем туда username)
    access_token = create_access_token(data={"sub": user.username})

    # 4. Возвращаем токен клиенту
    return {"access_token": access_token, "token_type": "bearer"}
