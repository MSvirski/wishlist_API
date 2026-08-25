import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
load_dotenv()


DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# Строка подключения: postgresql://логин:пароль@хост:порт/имя_базы
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@db:5432/{DB_NAME}"

# Движок для работы с PostgreSQL. Держит пул соединений для оперативного доступа к БД
engine = create_engine(DATABASE_URL)

# Фабрика сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()

# Зависимость для получения сессии БД в эндпоинтах. Дает сессию к БД когда она понадобится, и закрет ее по завершению
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
