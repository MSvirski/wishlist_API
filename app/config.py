from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Объявляем переменные БЕЗ дефолтных значений — тогда Pydantic
    # автоматически потребует их наличия в .env или переменных окружения.
    SECRET_KEY: str
    DB_CONNECTION_STRING: str
    TEST_DATABASE_URL: str

    # Переменные с дефолтными значениями (не обязательные)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Настройка автоматического чтения файла .env
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


# Инициализируем объект настроек.
# Если SECRET_KEY или DB_CONNECTION_STRING не найдены, приложение упадет ЗДЕСЬ с понятной ошибкой ValidationError.
settings = Settings()
