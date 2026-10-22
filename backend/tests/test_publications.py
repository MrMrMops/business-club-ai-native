import pytest


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


@pytest.mark.parametrize("publication_status", ["active", "closed"])
def test_user_cannot_delete_other_users_publication(
    client,
    publication_status,
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
        headers=auth_headers(nikita_token),
        json={
            "type": "startup",
            "title": "AI Startup",
            "description": "A sufficiently long description.",
            "looking_for": "Backend developer",
        },
    )
    publication_id = publication_response.json()["id"]

    assert client.patch(
        f"/publications/{publication_id}",
        headers=auth_headers(nikita_token),
        json={"status": publication_status},
    ).status_code == 200

    response = client.delete(
        "/publications/{}".format(publication_id),
        headers=auth_headers(polina_token),
    )

    assert response.status_code == 403
    assert client.get(
        "/publications/{}".format(publication_id)
    ).status_code == 200


def test_anonymous_user_cannot_delete_publication(
    client,
):
    nikita_token = create_user_and_token(
        client,
        "Nikita",
        "nikita@example.com",
    )
    publication_response = client.post(
        "/publications",
        headers=auth_headers(nikita_token),
        json={
            "type": "startup",
            "title": "AI Startup",
            "description": "A sufficiently long description.",
            "looking_for": "Backend developer",
        },
    )

    response = client.delete(
        "/publications/{}".format(
            publication_response.json()["id"]
        )
    )

    assert response.status_code == 401


@pytest.mark.parametrize("publication_status", ["active", "closed"])
@pytest.mark.parametrize("application_action", [None, "accept", "reject"])
def test_author_deletes_publication_and_its_applications(
    client,
    publication_status,
    application_action,
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
        headers=auth_headers(nikita_token),
        json={
            "type": "startup",
            "title": "AI Startup",
            "description": "A sufficiently long description.",
            "looking_for": "Backend developer",
        },
    )
    publication_id = publication_response.json()["id"]

    application_response = client.post(
        "/publications/{}/applications".format(
            publication_id
        ),
        headers=auth_headers(polina_token),
        json={"message": "I would like to help."},
    )
    assert application_response.status_code == 201

    if application_action is not None:
        assert client.patch(
            f"/applications/{application_response.json()['id']}/{application_action}",
            headers=auth_headers(nikita_token),
        ).status_code == 200

    other = client.post("/publications", headers=auth_headers(nikita_token), json={
        "type": "vacancy",
        "title": "Keep this publication",
        "description": "This unrelated publication must remain.",
        "looking_for": "Developer",
    })
    assert other.status_code == 201
    other_id = other.json()["id"]
    other_application = client.post(
        f"/publications/{other_id}/applications",
        headers=auth_headers(polina_token),
        json={"message": "Keep this application too."},
    )
    assert other_application.status_code == 201

    assert client.patch(
        f"/publications/{publication_id}",
        headers=auth_headers(nikita_token),
        json={"status": publication_status},
    ).status_code == 200

    response = client.delete(
        "/publications/{}".format(publication_id),
        headers=auth_headers(nikita_token),
    )

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(
        "/publications/{}".format(publication_id)
    ).status_code == 404
    assert client.get(
        "/applications/sent",
        headers=auth_headers(polina_token),
    ).json() == [other_application.json()]
    assert client.get(
        "/applications/received",
        headers=auth_headers(nikita_token),
    ).json() == [{
        **other_application.json(),
        "applicant_name": "Polina",
        "matched_skills": [],
        "explanation": "Кандидат пока не указал навыки",
    }]
    assert client.get(f"/publications/{other_id}").status_code == 200
    assert client.get("/users/me", headers=auth_headers(nikita_token)).status_code == 200
    assert client.get("/users/me", headers=auth_headers(polina_token)).status_code == 200
    assert client.delete(
        f"/publications/{publication_id}",
        headers=auth_headers(nikita_token),
    ).status_code == 404


def test_publication_author_name_is_current_and_private_fields_are_excluded(client):
    token = create_user_and_token(client, "Никита Шестаков", "author@example.com")
    headers = auth_headers(token)
    created = client.post("/publications", headers=headers, json={
        "type": "startup",
        "title": "Author name test",
        "description": "Testing the public author name.",
        "looking_for": "Developer",
    })
    assert created.status_code == 201
    publication_id = created.json()["id"]
    expected_fields = {
        "id", "author_id", "author_name", "type", "title", "description",
        "looking_for", "status", "created_at", "updated_at",
    }
    assert created.json()["author_name"] == "Никита Шестаков"
    assert set(created.json()) == expected_fields
    assert client.patch("/users/me", headers=headers, json={
        "name": "Новое имя", "bio": "Private biography", "skills": "Private skills",
    }).status_code == 200
    detail = client.get(f"/publications/{publication_id}").json()
    feed = client.get("/publications").json()[0]
    mine = client.get("/users/me/publications", headers=headers).json()[0]
    updated = client.patch(
        f"/publications/{publication_id}", headers=headers,
        json={"title": "Updated title"},
    ).json()
    for publication in (detail, feed, mine, updated):
        assert publication["author_name"] == "Новое имя"
        assert set(publication) == expected_fields


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
