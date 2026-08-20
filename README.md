# 🔐 FastAPI JWT Authentication Service

Современный и безопасный микросервис авторизации и аутентификации пользователей. Написан на **FastAPI** с использованием **SQLAlchemy 2.0** и полноценным развертыванием в **Docker Compose**.

## 🚀 Стек технологий
* **Backend:** Python 3.11, FastAPI, Pydantic v2
* **Database:** PostgreSQL 15, SQLAlchemy (ORM)
* **Security:** JWT (JSON Web Tokens), PyJWT, Passlib (Bcrypt hashing)
* **DevOps:** Docker, Docker Compose

## ✨ Ключевые фичи
* **Безопасное хэширование:** Пароли не хранятся в чистом виде, используется алгоритм `Bcrypt` с солью.
* **JWT-авторизация:** Выдача временных Access-токенов (Bearer) для защиты эндпоинтов.
* **Строгая валидация:** Входящие данные проверяются через Pydantic (включая валидацию синтаксиса Email).
* **Связь один запрос — одна сессия:** Реализован паттерн Dependency Injection для безопасного управления пулом соединений БД без утечек памяти.
* **Полная контейнеризация:** Запуск всего окружения (App + DB) одной командой.

## 🛠 Архитектура проекта
```text
pet_fastAPI/
├── database.py     # Настройка подключения к PostgreSQL и фабрики сессий
├── models.py       # Описание таблиц базы данных (SQLAlchemy)
├── schemas.py      # Схемы валидации данных на вход и выход (Pydantic)
├── security.py     # Логика хэширования паролей и генерации JWT
├── main.py         # Эндпоинты (маршруты) веб-сервера и логика API
├── requirements.txt# Зависимости проекта
├── Dockerfile      # Инструкция сборки контейнера приложения
└── docker-compose.yml # Оркестрация контейнеров приложения и БД
```

## 💻 Быстрый запуск (через Docker Compose)

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com
   cd pet_fastAPI
   ```

2. Создайте файл `.env` в корневой папке и укажите секретный ключ:
   ```text
   SECRET_KEY=super_secret_random_string_here
   ```

3. Запустите сборку и проект:
   ```bash
   docker compose up --build
   ```

Сервер автоматически поднимется на порту `8000`, а PostgreSQL запустится внутри изолированной сети Docker.

## 📝 Документация API
После запуска проекта интерактивная документация (Swagger UI) доступна по адресу:
👉 **http://localhost:8000/docs**

### Основные эндпоинты:
* `POST /register` — Регистрация нового пользователя (возвращает данные без пароля).
* `POST /token` — Аутентификация по OAuth2 Password Form (возвращает JWT Access Token).
