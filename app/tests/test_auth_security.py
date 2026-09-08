import os
import time
from datetime import datetime, timezone, timedelta
import pytest
import jwt

from app.auth.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
# --- ТЕСТЫ ХЭШИРОВАНИЯ ПАРОЛЕЙ ---

def test_get_password_hash_returns_string():
    """Проверяет, что функция возвращает строку (а не байты) и она не пустая."""
    password = "my_secret_password"
    hashed = get_password_hash(password)

    assert isinstance(hashed, str)
    assert len(hashed) > 0
    assert hashed != password  # Хэш не должен быть равен чистому паролю


def test_get_password_hash_salts_are_unique():
    """Проверяет, что для одного и того же пароля генерируются разные хэши (из-за соли)."""
    password = "same_password"
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)

    assert hash1 != hash2


def test_verify_password_success():
    """Проверяет успешное совпадение правильного пароля и хэша."""
    password = "correct_password"
    hashed = get_password_hash(password)

    assert verify_password(password, hashed) is True


def test_verify_password_wrong_password():
    """Проверяет, что функция возвращает False при неверном пароле."""
    password = "correct_password"
    wrong_password = "wrong_password"
    hashed = get_password_hash(password)

    assert verify_password(wrong_password, hashed) is False


# --- ТЕСТЫ JWT-ТОКЕНОВ ---

def test_create_access_token_success():
    """Проверяет корректное создание токена и валидность зашитых в него данных."""
    payload = {"sub": "user_123", "role": "admin"}
    token = create_access_token(payload)

    assert isinstance(token, str)

    # Декодируем токен для проверки содержимого
    secret = os.getenv("SECRET_KEY")
    decoded_data = jwt.decode(token, secret, algorithms=[ALGORITHM])

    assert decoded_data["sub"] == "user_123"
    assert decoded_data["role"] == "admin"
    assert "exp" in decoded_data


def test_create_access_token_expiration_time():
    """Проверяет, что время жизни токена устанавливается правильно (примерно +30 минут)."""
    payload = {"sub": "user_id"}

    now = datetime.now(timezone.utc)
    token = create_access_token(payload)

    secret = os.getenv("SECRET_KEY")
    decoded_data = jwt.decode(token, secret, algorithms=[ALGORITHM])

    # Переводим exp из timestamp обратно в datetime
    expire_datetime = datetime.fromtimestamp(decoded_data["exp"], tz=timezone.utc)

    # Ожидаемое время
    expected_expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # Проверяем разницу (допускаем погрешность в пару секунд на время выполнения теста)
    time_delta = abs((expire_datetime - expected_expire).total_seconds())
    assert time_delta < 5


def test_create_access_token_expired():
    """Проверяет, что библиотека jwt выбрасывает ошибку, если токен просрочен."""
    # Для этого теста временно подменим время жизни на отрицательное (токен сразу просрочен)
    payload = {"sub": "user_id"}

    # Копируем логику вашей функции, но со сдвигом в прошлое
    to_encode = payload.copy()
    expire = datetime.now(timezone.utc) - timedelta(minutes=1)  # Токен устарел минуту назад
    to_encode.update({"exp": expire})

    secret = os.getenv("SECRET_KEY")
    expired_token = jwt.encode(to_encode, secret, algorithm=ALGORITHM)

    # Ожидаем, что библиотека jwt выбросит ошибку при попытке декодировать
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(expired_token, secret, algorithms=[ALGORITHM])


def test_create_access_token_invalid_signature():
    """Проверяет, что jwt.decode падает, если токен подписан другим ключом."""
    payload = {"sub": "user_123"}
    # Создаем токен с правильным ключом
    token = create_access_token(payload)

    # Пытаемся декодировать его с ДРУГИМ (неверным) ключом
    wrong_secret = "completely_different_secret_key1234"
    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(token, wrong_secret, algorithms=[ALGORITHM])


def test_decode_malformed_token():
    """Проверяет реакцию на сломанный токен."""
    broken_token = "not.a.valid.jwt.token"
    with pytest.raises(jwt.DecodeError):
        jwt.decode(broken_token, "test_super_secret_key_123456789", algorithms=[ALGORITHM])


@pytest.mark.parametrize("bad_password", ["", " ", "longstr" * 100])
def test_get_password_hash_edge_cases(bad_password):
    """Проверяет хэширование пустых, коротких и экстремально длинных паролей."""
    hashed = get_password_hash(bad_password)
    assert isinstance(hashed, str)
    assert verify_password(bad_password, hashed) is True
