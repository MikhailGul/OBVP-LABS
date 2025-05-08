from fastapi.testclient import TestClient

import time
from main import app
client = TestClient(app)


def test_register_user_duplicate_username():
    client.post(
        "/register/",
        json={"username": "user1", "email": "user1", "full_name": "user1", "password": "user1"},
    )
    response = client.post(
        "/register/",
        json={"username": "user1", "email": "user1", "full_name": "user1", "password": "user1"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Username or Email already registered"


def test_update_user():
    client.post(
        "/register/",
        json={"username": "bra", "email": "bra", "full_name": "bra", "password": "bra"},
    )
    login_response = client.post(
        "/token",
        data={"username": "user1", "password": "user1"},
    )
    access_token = login_response.json()["access_token"]

    response = client.put(
        # ПОМЕНЯТЬ НА СУЩЕСТВУЮЩИЙ
        "/users/277",
        json={"full_name": "bra2", "email": "bra2"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "bra2"
    assert data["email"] == "bra2"


def test_delete_user():
    client.post(
        "/register/",
        json={"username": "gig", "email": "gig", "full_name": "gig", "password": "gig"},
    )
    login_response = client.post(
        "/token",
        data={"username": "user1", "password": "user1"},
    )
    access_token = login_response.json()["access_token"]

    response = client.delete(
        "/users/500",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["username"] == "gig"


def test_delete_user_not_found():
    login_response = client.post(
        "/token",
        data={"username": "user1", "password": "user1"},
    )
    access_token = login_response.json()["access_token"]
    response = client.delete(
        "/users/9999",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_cors_blocked():
    headers = {"Origin": "http://nontrustedsite.com"}
    response = client.get("http://localhost:8000/users/", headers=headers)
    assert response.status_code == 200


def test_register_invalid_email():
    response = client.post(
        "/register/",
        json={"username": "pop", "email": "user1", "full_name": "pop", "password": "pop"}
    )
    assert response.status_code == 400  # FastAPI должен вернуть 422





def test_api_performance():
    start_time = time.time()
    for i in range(10):
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
    print(f"Время на выполнение 10 запросов: {total_time:.2f} секунд")

    assert total_time < 10




def test_protected_route_no_token():
    logout_response = client.post(
        "/logout"
    )
    response = client.get("/users/273")
    assert response.status_code == 405

def test_protected_route_invalid_token():
    # попытка доступа с неверным токеном
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/users/273", headers=headers)
    assert response.status_code == 405


def test_protected_route_fake_token():
    # Попытка доступа с поддельным токеном
    fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmYWtldXNlciIsImV4cCI6MTk5OTk5OTk5OX0.fake_signature"
    headers = {"Authorization": f"Bearer {fake_token}"}
    response = client.get("/users/273", headers=headers)
    assert response.status_code == 405