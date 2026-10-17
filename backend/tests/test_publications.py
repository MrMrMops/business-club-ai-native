def create_user_and_token(
    client,
    name,
    email,
):
    password = "password123"

    client.post(
        "/auth/register",
        json={
            "name": name,
            "email": email,
            "password": password,
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    return response.json()[
        "access_token"
    ]


def auth_headers(token):
    return {
        "Authorization":
            "Bearer {}".format(token)
    }


def test_create_publication(client):
    token = create_user_and_token(
        client,
        "Nikita",
        "nikita@example.com",
    )

    response = client.post(
        "/publications",
        headers=auth_headers(token),
        json={
            "type": "startup",
            "title": "AI Case Trainer",
            "description":
                "Service for case competition training.",
            "looking_for":
                "Backend developer",
        },
    )

    assert response.status_code == 201

    publication = response.json()

    assert publication["title"] == (
        "AI Case Trainer"
    )
    assert publication["type"] == "startup"
    assert publication["status"] == "active"


def test_user_cannot_edit_other_users_publication(
    client,
):
    nikita_token = create_user_and_token(
        client,
        "Nikita",
        "nikita@example.com",
    )

    polina_token = create_user_and_token(
        client,
        "Polina",
        "polina@example.com",
    )

    publication_response = client.post(
        "/publications",
        headers=auth_headers(
            nikita_token
        ),
        json={
            "type": "startup",
            "title": "AI Startup",
            "description":
                "A sufficiently long description.",
            "looking_for":
                "Backend developer",
        },
    )

    publication_id = (
        publication_response.json()["id"]
    )

    response = client.patch(
        "/publications/{}".format(
            publication_id
        ),
        headers=auth_headers(
            polina_token
        ),
        json={
            "title":
                "Someone else's title",
        },
    )

    assert response.status_code == 403


def test_closed_publication_not_in_feed(
    client,
):
    token = create_user_and_token(
        client,
        "Nikita",
        "nikita@example.com",
    )

    publication_response = client.post(
        "/publications",
        headers=auth_headers(token),
        json={
            "type": "vacancy",
            "title": "Backend Developer",
            "description":
                "We are looking for a backend developer.",
            "looking_for":
                "Python developer",
        },
    )

    publication_id = (
        publication_response.json()["id"]
    )

    close_response = client.patch(
        "/publications/{}".format(
            publication_id
        ),
        headers=auth_headers(token),
        json={
            "status": "closed",
        },
    )

    assert close_response.status_code == 200

    feed_response = client.get(
        "/publications"
    )

    assert feed_response.status_code == 200
    assert feed_response.json() == []