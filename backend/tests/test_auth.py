def test_register_and_login(client):
    register_response = client.post(
        "/auth/register",
        json={
            "name": "Nikita",
            "email": "nikita@example.com",
            "password": "password123",
        },
    )

    assert register_response.status_code == 201

    user = register_response.json()

    assert user["name"] == "Nikita"
    assert user["email"] == "nikita@example.com"
    assert "password_hash" not in user

    login_response = client.post(
        "/auth/login",
        json={
            "email": "nikita@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    data = login_response.json()

    assert data["token_type"] == "bearer"
    assert data["access_token"]


def test_duplicate_email_is_rejected(client):
    payload = {
        "name": "Nikita",
        "email": "nikita@example.com",
        "password": "password123",
    }

    first_response = client.post(
        "/auth/register",
        json=payload,
    )

    second_response = client.post(
        "/auth/register",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_wrong_password_is_rejected(client):
    client.post(
        "/auth/register",
        json={
            "name": "Nikita",
            "email": "nikita@example.com",
            "password": "password123",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "nikita@example.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401