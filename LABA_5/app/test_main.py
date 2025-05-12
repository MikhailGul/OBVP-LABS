import pytest
from fastapi.testclient import TestClient
from app.main import app, Base, engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import time

client = TestClient(app)

# Создание нового сеанса базы данных для каждого теста ПОТОМУ ЧТО БЕЗ ЭТОГО У МЕНЯ НИЧЁ НЕ ХОТЕЛО РАБОТАТЬ!!!!
# @pytest.fixture(scope="function", autouse=True)
# def setup_db():
#     Base.metadata.create_all(bind=engine)
#     yield
#     Base.metadata.drop_all(bind=engine)

# Получаем токен
def get_access_token():
    register_test_user()  # Убедимся, что пользователь точно есть
    response = client.post("/token", data={"username": "testuser", "password": "testpassword"})
    assert response.status_code == 200
    return response.json()["access_token"]

# Тестируем получение списка пользователей
def test_get_users():
    access_token = get_access_token()
    response = client.get(
        "/users/",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(user["username"] == "testuser" for user in data)


# Добавляем второй тест для создания пользователя
def test_create_user():
    # Попытка создать пользователя
    response = client.post("/users/", json={
        "username": "newuser11",
        "email": "newuser11@example.com",
        "full_name": "New User",
        "password": "newpassword"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newuser"