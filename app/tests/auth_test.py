from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_signup():

    response = client.post(
        "/users/register",
        json={
            "username": "user3",
            "email": "user3@gmail.com",
            "password": "123456",
            "role": "user"
        }
    )

    assert response.status_code == 201


def test_login():

    response = client.post(
        "/users/login",
        data={
            "username": "user1",
            "password": "123456"
        }
    )

    assert response.status_code == 200
    assert "access_token" in response.json()