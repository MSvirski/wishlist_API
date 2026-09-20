import pytest
from httpx import AsyncClient

from app.auth.security import create_access_token


# Вспомогательная функция, чтобы не дублировать код генерации заголовков
def get_auth_header(user_id: int) -> dict:
    token = create_access_token(data={"sub": str(user_id)})
    return {"Authorization": f"Bearer {token}"}


# --- ТЕСТЫ ОТПРАВКИ ЗАПРОСА В ДРУЗЬЯ ---

@pytest.mark.asyncio
async def test_send_friend_request_success(ac: AsyncClient, test_users):
    """Успешная отправка запроса в друзья по username."""
    alice, *_ = test_users
    headers = get_auth_header(alice.id)  # Запрос делает Алиса

    payload = {"username": "bob"}
    response = await ac.post("/friends/request", json=payload, headers=headers)

    assert response.status_code == 201
    assert "успешно отправлен" in response.json()["detail"]


@pytest.mark.asyncio
async def test_send_friend_request_to_self(ac: AsyncClient, test_users):
    """Ошибка при попытке отправить запрос самому себе."""
    alice, *_ = test_users
    headers = get_auth_header(alice.id)

    payload = {"username": "alice"}
    response = await ac.post("/friends/request", json=payload, headers=headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "Нельзя отправить запрос в друзья самому себе"


@pytest.mark.asyncio
async def test_send_friend_request_user_not_found(ac: AsyncClient, test_users):
    """Ошибка 404, если пользователя с таким username не существует."""
    alice, *_ = test_users
    headers = get_auth_header(alice.id)

    payload = {"username": "non_existent_user"}
    response = await ac.post("/friends/request", json=payload, headers=headers)

    assert response.status_code == 404
    assert "не найден" in response.json()["detail"]


@pytest.mark.asyncio
async def test_send_friend_request_duplicate(ac: AsyncClient, test_users):
    """Ошибка 400 при повторной отправке запроса."""
    alice, *_  = test_users
    headers = get_auth_header(alice.id)
    payload = {"username": "bob"}

    await ac.post("/friends/request", json=payload, headers=headers)
    response = await ac.post("/friends/request", json=payload, headers=headers)

    assert response.status_code == 400
    assert "Запрос уже существует" in response.json()["detail"]


# --- ТЕСТЫ ПОЛУЧЕНИЯ СПИСКОВ ЗАПРОСОВ ---

@pytest.mark.asyncio
async def test_get_incoming_and_outgoing_requests(ac: AsyncClient, test_users):
    """Проверка корректности списков входящих и исходящих запросов."""
    alice, bob, *_  = test_users
    alice_headers = get_auth_header(alice.id)
    bob_headers = get_auth_header(bob.id)

    # Алиса отправляет запрос Бобу
    await ac.post("/friends/request", json={"username": "bob"}, headers=alice_headers)

    # Проверяем исходящие у Алисы
    outgoing_res = await ac.get("/friends/requests/outgoing", headers=alice_headers)
    assert outgoing_res.status_code == 200
    assert len(outgoing_res.json()) == 1
    assert outgoing_res.json()[0]["username"] == "bob"

    # Проверяем входящие у Боба
    incoming_res = await ac.get("/friends/requests/incoming", headers=bob_headers)
    assert incoming_res.status_code == 200
    assert len(incoming_res.json()) == 1
    assert incoming_res.json()[0]["username"] == "alice"


# --- ТЕСТ ПРИНЯТИЕ ЗАПРОСА В ДРУЗЬЯ ---

@pytest.mark.asyncio
async def test_accept_friend_request_success(ac: AsyncClient, test_users):
    """Успешное принятие запроса в друзья."""
    alice, bob, *_ = test_users
    alice_headers = get_auth_header(alice.id)
    bob_headers = get_auth_header(bob.id)

    # Алиса отправляет запрос
    await ac.post("/friends/request", json={"username": "bob"}, headers=alice_headers)

    # Боб принимает запрос от Алисы
    response = await ac.post(f"/friends/accept/{alice.id}", headers=bob_headers)

    assert response.status_code == 200
    assert response.json()["detail"] == "Запрос принят. Вы теперь друзья!"

    incoming_res = await ac.get("/friends/requests/incoming", headers=bob_headers)
    assert len(incoming_res.json()) == 0


@pytest.mark.asyncio
async def test_accept_friend_request_not_found(ac: AsyncClient, test_users):
    """Ошибка 404 при попытке принять несуществующий запрос."""
    alice, *_  = test_users
    headers = get_auth_header(alice.id)

    response = await ac.post("/friends/accept/9999", headers=headers)

    assert response.status_code == 404
    assert "Входящий запрос от этого пользователя не найден" in response.json()["detail"]


# --- ТЕСТЫ ОТКЛОНЕНИЯ И ОТМЕНЫ ЗАПРОСОВ ---

@pytest.mark.asyncio
async def test_decline_incoming_request_by_recipient(ac: AsyncClient, test_users):
    """Получатель успешно отклоняет входящий запрос."""
    alice, bob, *_  = test_users
    alice_headers = get_auth_header(alice.id)
    bob_headers = get_auth_header(bob.id)

    await ac.post("/friends/request", json={"username": "bob"}, headers=alice_headers)

    # Боб отклоняет запрос Алисы
    response = await ac.post(f"/friends/decline/{alice.id}", headers=bob_headers)
    assert response.status_code == 200
    assert "успешно отклонен или отменен" in response.json()["detail"]


@pytest.mark.asyncio
async def test_cancel_outgoing_request_by_sender(ac: AsyncClient, test_users):
    """Отправитель успешно отменяет свой собственный исходящий запрос."""
    alice, bob, *_ = test_users
    alice_headers = get_auth_header(alice.id)

    await ac.post("/friends/request", json={"username": "bob"}, headers=alice_headers)

    # Алиса передумала и отменяет свой запрос к Бобу
    response = await ac.post(f"/friends/decline/{bob.id}", headers=alice_headers)
    assert response.status_code == 200
    assert "успешно отклонен или отменен" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_my_friends_bilateral(ac: AsyncClient, test_users):
    """
    Проверка эндпоинта GET /friends.
    Убеждаемся, что возвращаются только подтвержденные (ACCEPTED) друзья,
    независимо от того, кто отправил запрос (user_id или friend_id).
    """
    # 1. Создаем тестовых пользователей в базе данных
    alice, bob, otherUser1, otherUser2, otherUser3, *_  = test_users
    aliceHeaders = get_auth_header(alice.id)
    bobHeaders = get_auth_header(bob.id)
    otherUser1Headers = get_auth_header(otherUser1.id)
    otherUser2Headers = get_auth_header(otherUser2.id)

    # Алиса отправяет запросы в друзья
    await ac.post("/friends/request", json={"username": "bob"}, headers=aliceHeaders)
    await ac.post("/friends/request", json={"username": "otherUser1"}, headers=aliceHeaders)
    await ac.post("/friends/request", json={"username": "otherUser2"}, headers=aliceHeaders)
    await ac.post("/friends/request", json={"username": "otherUser3"}, headers=aliceHeaders)


    # Кто-то принял, кто-то отклонил или заигнорил
    await ac.post(f"/friends/accept/{alice.id}", headers=bobHeaders)
    await ac.post(f"/friends/accept/{alice.id}", headers=otherUser1Headers)
    await ac.post(f"/friends/decline/{alice.id}", headers=otherUser2Headers)


    # 4. Делаем запрос к новому эндпоинту
    response = await ac.get("/friends", headers=aliceHeaders)

    # 5. Проверяем результаты
    assert response.status_code == 200

    friends_list = response.json()
    assert len(friends_list) == 2  # Должно быть ровно 2 друга

    # Проверяем, что юзернеймы друзей присутствуют в ответе
    usernames = [user["username"] for user in friends_list]
    assert "bob" in usernames
    assert "otherUser1" in usernames
    assert "otherUser2" not in usernames
    assert "otherUser3" not in usernames
