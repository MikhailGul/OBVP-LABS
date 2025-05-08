from fastapi.testclient import TestClient


from main import app
client = TestClient(app)


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200


def test_get_users():
    response = client.get("/users/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["username"] == "qwe"

def test_create_user():
    response = client.post(
        "/register/",
        json={"username": "testuser", "email": "testuser@example.com", "full_name": "Test User", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "testuser@example.com"

def test_register_user_success():
    response = client.post(
        "/register/",
        json={"username": "newuser", "email": "newuser@example.com", "full_name": "New User", "password": "newpassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"

def test_register_user_duplicate_username():
    client.post(
        "/register/",
        json={"username": "duplicateuser", "email": "duplicate@example.com", "full_name": "Duplicate User", "password": "password123"},
    )
    response = client.post(
        "/register/",
        json={"username": "duplicateuser", "email": "duplicate2@example.com", "full_name": "Duplicate User 2", "password": "password456"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Username or Email already registered"

def test_register_user_duplicate_email():
    client.post(
        "/register/",
        json={"username": "useremailduplicate", "email": "emailduplicate@example.com", "full_name": "User Email Duplicate", "password": "password123"},
    )
    response = client.post(
        "/register/",
        json={"username": "newuseremail", "email": "emailduplicate@example.com", "full_name": "New User Email", "password": "password456"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Username or Email already registered"

def test_login_success():
    client.post(
        "/register/",
        json={"username": "loginuser", "email": "login@example.com", "full_name": "Login User", "password": "loginpassword123"},
    )
    response = client.post(
        "/token",
        data={"username": "loginuser", "password": "loginpassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_incorrect_credentials():
    response = client.post(
        "/token",
        data={"username": "nonexistentuser", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"

def test_invalid_token():
    invalid_token = "invalidtoken123"
    response = client.get("/users/me", headers={"Authorization": f"Bearer {invalid_token}"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

def test_get_users():
    response = client.get("/users/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "username" in data[0]
    assert "email" in data[0]

def test_get_current_user():
    client.post(
        "/register/",
        json={"username": "currentuser", "email": "currentuser@example.com", "full_name": "Current User", "password": "password123"},
    )
    login_response = client.post(
        "/token",
        data={"username": "currentuser", "password": "password123"},
    )
    access_token = login_response.json()["access_token"]
    response = client.get("/users/me", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "currentuser"
    assert data["email"] == "currentuser@example.com"









def test_update_user():
    client.post(
        "/register/",
        json={"username": "updateuser", "email": "updateuser@example.com", "full_name": "Update User", "password": "password123"},
    )
    login_response = client.post(
        "/token",
        data={"username": "updateuser", "password": "password123"},
    )
    access_token = login_response.json()["access_token"]

    response = client.put(
        # ПОМЕНЯТЬ НА СУЩЕСТВУЮЩИЙ
        "/users/1",
        json={"full_name": "Updated Name", "email": "updateduser@example.com"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["email"] == "updateduser@example.com"











def test_update_user_invalid_token():
    response = client.put(
        "/users/1",
        json={"full_name": "Updated Name"},
        headers={"Authorization": "Bearer invalidtoken123"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"









def test_delete_user():
    client.post(
        "/register/",
        json={"username": "deleteuser", "email": "deleteuser@example.com", "full_name": "Delete User", "password": "password123"},
    )
    login_response = client.post(
        "/token",
        data={"username": "deleteuser", "password": "password123"},
    )
    access_token = login_response.json()["access_token"]

    response = client.delete(
        # ПОМЕНЯТЬ НА СУЩЕСТВУЮЩИЙ
        "/users/1",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["username"] == "deleteuser"










def test_delete_user_not_found():
    # АВТОРИЗАЦИЯ ОБЯЗАТЕЛЬНА
    response = client.delete(
        "/users/9999",
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"











def test_cors_allowed():
    response = client.get("http://localhost:8000/users/")
    assert response.status_code == 200

def test_cors_blocked():
    headers = {"Origin": "http://nontrustedsite.com"}
    response = client.get("http://localhost:8000/users/", headers=headers)
    assert response.status_code == 403



# ТЕСТИРОВАНИЕ ОБРАБОТКИ ОШИБОК


def test_register_missing_field():
    response = client.post(
        "/register/",
        json={"username": "userwithoutpassword", "email": "user@example.com", "full_name": "Test User"}
    )
    assert response.status_code == 422
    assert "password" in response.json()["detail"][0]["loc"]

def test_register_invalid_email():
    response = client.post(
        "/register/",
        json={"username": "invalidemailuser", "email": "notanemail", "full_name": "Invalid Email User", "password": "password123"}
    )
    assert response.status_code == 404  # FastAPI должен вернуть 422
    assert "email" in response.json()["detail"][0]["loc"]


# ТЕСТИРОВАНИЕ ПРОИЗВОДИТЕЛЬНОСТИ

import time


def test_api_performance():
    start_time = time.time()
    for i in range(100):
        response = client.post(
            "/register/",
            json={
                "username": f"perfuser{i}",
                "email": f"perfuser{i}@example.com",
                "full_name": "Performance Test User",
                "password": "password123"
            }
        )
        assert response.status_code == 200

    end_time = time.time()
    total_time = end_time - start_time
    print(f"Время на выполнение 100 запросов: {total_time:.2f} секунд")

    assert total_time < 10



# ТЕСТИРОВАНИЕ БЕЗОПАСНОСТИ


def test_protected_route_no_token():
    response = client.get("/users/1")
    assert response.status_code == 401

def test_protected_route_invalid_token():
    # Попытка доступа с неверным токеном
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/users/1", headers=headers)
    assert response.status_code == 401

def test_protected_route_fake_token():
    # Попытка доступа с поддельным токеном
    fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmYWtldXNlciIsImV4cCI6MTk5OTk5OTk5OX0.fake_signature"
    headers = {"Authorization": f"Bearer {fake_token}"}
    response = client.get("/users/1", headers=headers)
    assert response.status_code == 401
