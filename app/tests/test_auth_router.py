import pytest
from httpx import AsyncClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


# ТЕСТ РЕГИСТРАЦИИ (Проверяем уникальность email)
async def test_register_user_duplicate_email(ac: AsyncClient):
    response = await ac.post(
     "/auth/register",
      json={"username": "Ivan", "email": "tester@example.com", "password": "anotherpassword777"}
   )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "tester@example.com"
    assert "id" in data
    response = await ac.post(
        "/auth/register",
        json={"username": "Ivan", "email": "tester@example.com", "password": "anotherpassword777"}
    )
    assert response.status_code == 400
    # Проверяем текст ошибки
    assert response.json()["detail"] == "Пользователь с таким email уже зарегистрирован"




# ... (остальной код) ...

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error_type, detail_substring",
    [
        ("email", "email уже зарегистрирован (конфликт параллельных запросов)"),
        ("username", "Пользователь с таким именем уже зарегистрирован"),
        ("other", "Данные уже используются")
    ],
    ids=["integrity_email", "integrity_username", "integrity_other"]
)
# Игнорируем предупреждение SQLAlchemy об уже закрытой транзакции только для этого теста
@pytest.mark.filterwarnings("ignore:transaction already deassociated:sqlalchemy.exc.SAWarning")
async def test_register_user_integrity_error_handling(ac: AsyncClient, monkeypatch, error_type, detail_substring):
    """Проверка обработки IntegrityError (симуляция race condition)."""

    async def mock_commit(*args, **kwargs):
        orig_error = Exception(f"duplicate key value violates unique constraint '{error_type}'")
        raise IntegrityError("insert ...", params={}, orig=orig_error)

    monkeypatch.setattr(AsyncSession, "commit", mock_commit)

    payload = {"username": "race_user", "email": "race@mail.com", "password": "password123"}
    response = await ac.post("auth/register", json=payload)

    assert response.status_code == 409
    assert detail_substring in response.json()["detail"]


# --- ТЕСТЫ ЭНДПОИНТА /token ---


async def test_login_success(ac: AsyncClient):
    """Успешная авторизация пользователя и получение JWT-токена."""
    user_payload = {"username": "loginuser", "email": "login@mail.com", "password": "correct_password"}
    await ac.post("auth/register", json=user_payload)

    login_data = {
        "username": "login@mail.com",
        "password": "correct_password"
    }
    response = await ac.post("auth/token", data=login_data)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.parametrize(
    "username, password",
    [
        ("wrong@mail.com", "correct_password"),
        ("login@mail.com", "wrong_password"),
    ],
    ids=["wrong_email", "wrong_password"]
)
async def test_login_unauthorized(ac: AsyncClient, username, password):
    """Ошибка 401 Unauthorized при неверном email или пароле."""
    user_payload = {"username": "loginuser", "email": "login@mail.com", "password": "correct_password"}
    await ac.post("auth/register", json=user_payload)

    login_data = {"username": username, "password": password}
    response = await ac.post("auth/token", data=login_data)

    assert response.status_code == 401
    assert response.json()["detail"] == "Неверный email или пароль"
