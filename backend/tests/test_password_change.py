import pytest
from sqlalchemy import select

from app.core.security import verify_password
from app.models.user import User
from tests.conftest import TestingSessionLocal
from tests.test_publications import create_user_and_token, auth_headers


@pytest.fixture()
def account(client):
    return auth_headers(create_user_and_token(client, 'Demo', 'demo@example.com'))


def login(client, password, email='demo@example.com'):
    return client.post('/auth/login', json={'email': email, 'password': password})


def test_change_password_success(client, account):
    response = client.post('/auth/change-password', headers=account, json={
        'old_password': 'password123', 'new_password': 'new-test-password',
    })
    assert response.status_code == 204
    assert response.content == b''
    assert login(client, 'password123').status_code == 401
    assert login(client, 'new-test-password').status_code == 200
    with TestingSessionLocal() as db:
        user = db.scalar(select(User).where(User.email == 'demo@example.com'))
        assert user.password_hash != 'new-test-password'
        assert verify_password('new-test-password', user.password_hash)


def test_wrong_old_password(client, account):
    response = client.post('/auth/change-password', headers=account, json={
        'old_password': 'wrong-test-password', 'new_password': 'new-test-password',
    })
    assert response.status_code == 400
    assert 'wrong-test-password' not in response.text
    assert 'new-test-password' not in response.text
    assert login(client, 'password123').status_code == 200


@pytest.mark.parametrize('payload', [
    {'old_password': 'password123', 'new_password': 'short'},
    {'old_password': 'password123', 'new_password': 'x' * 129},
    {'old_password': 'password123'},
    {'old_password': 'password123', 'new_password': None},
    {'old_password': 'password123', 'new_password': 'new-test-password', 'user_id': 999},
    {'old_password': 'password123', 'new_password': 'new-test-password', 'email': 'other@example.com'},
])
def test_invalid_input_is_redacted_and_does_not_change_password(client, account, payload):
    response = client.post('/auth/change-password', headers=account, json=payload)
    assert response.status_code == 422
    assert 'input' not in response.json()
    for value in payload.values():
        if isinstance(value, str):
            assert value not in response.text
    assert login(client, 'password123').status_code == 200


@pytest.mark.parametrize('headers', [{}, {'Authorization': 'Bearer invalid-token'}])
def test_change_password_requires_valid_token(client, account, headers):
    response = client.post('/auth/change-password', headers=headers, json={
        'old_password': 'password123', 'new_password': 'new-test-password',
    })
    assert response.status_code == 401
    assert login(client, 'password123').status_code == 200


def test_only_authenticated_user_changes_even_with_shared_old_password(client, account):
    create_user_and_token(client, 'Other', 'other@example.com')
    response = client.post('/auth/change-password', headers=account, json={
        'old_password': 'password123', 'new_password': 'new-test-password',
    })
    assert response.status_code == 204
    assert login(client, 'password123', 'other@example.com').status_code == 200
    assert login(client, 'new-test-password', 'other@example.com').status_code == 401


def test_malformed_json_does_not_echo_password(client, account):
    response = client.post('/auth/change-password', headers={**account, 'Content-Type': 'application/json'},
                           content='{"old_password":"never-echo-this",')
    assert response.status_code == 422
    assert 'never-echo-this' not in response.text
