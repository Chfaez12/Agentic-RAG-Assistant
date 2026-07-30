from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def get_token(username, password):

    response = client.post(
        "/users/login",
        data={
            "username": username,
            "password": password
        }
    )

    return response.json()["access_token"]


def test_create_post():

    token = get_token("user1", "123456")

    response = client.post(
        "/posts/",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "title": "First Post",
            "content": "FastAPI Testing"
        }
    )

    assert response.status_code == 200


def test_cannot_edit_someone_else_post():

    client.post(
        "/users/register",
        json={
            "username": "user5",
            "email": "user5@gmail.com",
            "password": "123456",
            "role": "user"
        }
    )

    user2_token = get_token("user5", "123456")

    response = client.put(
        "/posts/4",
        headers={
            "Authorization": f"Bearer {user2_token}"
        },
        json={
            "title": "Hacked",
            "content": "Trying to edit"
        }
    )

    assert response.status_code == 401    