from httpx import AsyncClient


# 1. ТЕСТ РЕГИСТРАЦИИ (успешная регистрация)
async def test_register_user_success(ac: AsyncClient):
    response = await ac.post(
        "/auth/register",
        json={"username": "Kevin", "email": "tester@example.com", "password": "securepassword123"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "tester@example.com"
    assert "id" in data

# 2. ТЕСТ РЕГИСТРАЦИИ (Проверяем уникальность email)
async def test_register_user_duplicate_email(ac: AsyncClient):
    response = await ac.post(
     "/auth/register",
      json={"username": "Ivan", "email": "tester@example.com", "password": "anotherpassword777"}
   )
    assert response.status_code == 400
    # Проверяем текст ошибки
    assert response.json()["detail"] == "Пользователь с таким email уже зарегистрирован"
