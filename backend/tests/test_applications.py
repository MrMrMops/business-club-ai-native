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


def create_publication(
    client,
    token,
):
    response = client.post(
        "/publications",
        headers=auth_headers(token),
        json={
            "type": "startup",
            "title": "AI Startup",
            "description":
                "An AI startup for students.",
            "looking_for":
                "Python backend developer",
        },
    )

    return response.json()["id"]


def test_full_application_flow(client):
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

    publication_id = create_publication(
        client,
        nikita_token,
    )

    apply_response = client.post(
        "/publications/{}/applications".format(
            publication_id
        ),
        headers=auth_headers(
            polina_token
        ),
        json={
            "message":
                "I have FastAPI experience.",
        },
    )

    assert apply_response.status_code == 201

    application = apply_response.json()

    assert application["status"] == "pending"

    application_id = application["id"]

    received_response = client.get(
        "/applications/received",
        headers=auth_headers(
            nikita_token
        ),
    )

    assert received_response.status_code == 200
    assert len(received_response.json()) == 1

    accept_response = client.patch(
        "/applications/{}/accept".format(
            application_id
        ),
        headers=auth_headers(
            nikita_token
        ),
    )

    assert accept_response.status_code == 200
    assert (
        accept_response.json()["status"]
        == "accepted"
    )

    sent_response = client.get(
        "/applications/sent",
        headers=auth_headers(
            polina_token
        ),
    )

    assert sent_response.status_code == 200

    sent_application = (
        sent_response.json()[0]
    )

    assert (
        sent_application["status"]
        == "accepted"
    )


def test_user_cannot_apply_twice(client):
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

    publication_id = create_publication(
        client,
        nikita_token,
    )

    payload = {
        "message":
            "I want to join this project.",
    }

    first_response = client.post(
        "/publications/{}/applications".format(
            publication_id
        ),
        headers=auth_headers(
            polina_token
        ),
        json=payload,
    )

    second_response = client.post(
        "/publications/{}/applications".format(
            publication_id
        ),
        headers=auth_headers(
            polina_token
        ),
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_author_cannot_apply_to_own_publication(
    client,
):
    token = create_user_and_token(
        client,
        "Nikita",
        "nikita@example.com",
    )

    publication_id = create_publication(
        client,
        token,
    )

    response = client.post(
        "/publications/{}/applications".format(
            publication_id
        ),
        headers=auth_headers(token),
        json={
            "message":
                "Applying to my own project.",
        },
    )

    assert response.status_code == 400


def test_other_user_cannot_accept_application(
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

    alex_token = create_user_and_token(
        client,
        "Alex",
        "alex@example.com",
    )

    publication_id = create_publication(
        client,
        nikita_token,
    )

    apply_response = client.post(
        "/publications/{}/applications".format(
            publication_id
        ),
        headers=auth_headers(
            polina_token
        ),
        json={
            "message":
                "I want to participate.",
        },
    )

    application_id = (
        apply_response.json()["id"]
    )

    response = client.patch(
        "/applications/{}/accept".format(
            application_id
        ),
        headers=auth_headers(
            alex_token
        ),
    )

    assert response.status_code == 403


def test_processed_application_cannot_be_processed_again(
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

    publication_id = create_publication(
        client,
        nikita_token,
    )

    apply_response = client.post(
        "/publications/{}/applications".format(
            publication_id
        ),
        headers=auth_headers(
            polina_token
        ),
        json={
            "message":
                "I want to participate.",
        },
    )

    application_id = (
        apply_response.json()["id"]
    )

    first_response = client.patch(
        "/applications/{}/accept".format(
            application_id
        ),
        headers=auth_headers(
            nikita_token
        ),
    )

    second_response = client.patch(
        "/applications/{}/reject".format(
            application_id
        ),
        headers=auth_headers(
            nikita_token
        ),
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409