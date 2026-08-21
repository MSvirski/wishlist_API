# 🔐 WISHLIST API(v0.0.1)
 
На данный момент представляет собой микросервис авторизации и аутентификации пользователей.

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
## 💻 Быстрый запуск (через curl)
1. Скачивает проект в $HOME/Desktop/wishlist_app и автоматически запускает контейнеры:
   ```bash
   curl -sSL https://raw.githubusercontent.com/MSvirski/wishlist_API/refs/heads/main/autorun.sh | bash -s -- up
   ```
2. Для остановки контейнеров используйте:
   ```bash
   curl -sSL https://raw.githubusercontent.com/MSvirski/wishlist_API/refs/heads/main/autorun.sh | bash -s -- down
   ```
3. Для полного удаления всех компонентов программы используйте:
   ```bash
   curl -sSL https://raw.githubusercontent.com/MSvirski/wishlist_API/refs/heads/main/autorun.sh | bash -s -- down   
   ```
## 💻 Быстрый запуск (через Docker Compose)

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/MSvirski/wishlist_API.git
   cd wishlist_API
   ```

2. Скопируйте файл `.env` из примера, и при необходимости измените значения:
   ```text
   cp .env.example .env
   ```

3. Запустите сборку и проект:
   ```bash
   sudo docker compose up --build
   ```

Сервер автоматически поднимется на порту `8000`, а PostgreSQL запустится внутри изолированной сети Docker.

## 📝 Документация API
После запуска проекта интерактивная документация (Swagger UI) доступна по адресу:
👉 **http://localhost:8000/docs**

### Основные эндпоинты:
* `POST /register` — Регистрация нового пользователя (возвращает данные без пароля).
* `POST /token` — Аутентификация по OAuth2 Password Form (возвращает JWT Access Token).
