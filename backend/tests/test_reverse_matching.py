import pytest

from tests.test_publications import auth_headers, create_user_and_token
from tests.test_recommendations import publish


@pytest.fixture()
def people(client):
    owner = auth_headers(create_user_and_token(client, 'Owner', 'owner@example.com'))
    candidate = auth_headers(create_user_and_token(client, 'Алекс', 'alex@example.com'))
    outsider = auth_headers(create_user_and_token(client, 'Other', 'other@example.com'))
    return owner, candidate, outsider


def apply(client, candidate, publication_id, skills):
    assert client.patch('/users/me', headers=candidate, json={
        'skills': skills, 'bio': 'Private candidate biography',
    }).status_code == 200
    response = client.post(f'/publications/{publication_id}/applications',
                           headers=candidate, json={'message': 'Готов обсудить задачи проекта.'})
    assert response.status_code == 201
    return response.json()['id']


def received(client, owner):
    response = client.get('/applications/received', headers=owner)
    assert response.status_code == 200
    return response.json()


@pytest.mark.parametrize(('skills', 'requirements', 'expected'), [
    ('Python, Backend, FastAPI', 'Python Backend developer', ['Backend', 'Python']),
    ('БЭКЕНД; дизайн интерфейсов', 'backend; UX/UI', ['Backend', 'UX/UI']),
    ('BACK-END, UI/UX, PYTHON', 'бекенд, дизайнер интерфейсов, пайтон', ['Backend', 'Python', 'UX/UI']),
    ('Java; SQL', 'JavaScript; NoSQL', []),
    ('Photography', 'Python', []),
])
def test_candidate_matching(client, people, skills, requirements, expected):
    owner, candidate, _ = people
    pid = publish(client, owner, requirements)
    aid = apply(client, candidate, pid, skills)
    item = received(client, owner)[0]
    assert item['id'] == aid
    assert item['applicant_name'] == 'Алекс'
    assert item['matched_skills'] == expected
    assert item['status'] == 'pending'
    if expected:
        assert ', '.join(expected) in item['explanation']
    else:
        assert 'Это не означает, что кандидат не подходит' in item['explanation']


@pytest.mark.parametrize('skills', [None, '', ' \n '])
def test_empty_profile(client, people, skills):
    owner, candidate, _ = people
    apply(client, candidate, publish(client, owner, 'Python'), skills)
    item = received(client, owner)[0]
    assert item['matched_skills'] == []
    assert item['explanation'] == 'Кандидат пока не указал навыки'


def test_matches_per_publication_and_live_profile(client, people):
    owner, candidate, other = people
    first = publish(client, owner, 'Python')
    second = publish(client, owner, 'UX/UI')
    apply(client, candidate, first, 'Python; UX/UI')
    apply(client, candidate, second, 'Python; UX/UI')
    apply(client, other, first, 'Figma')
    items = received(client, owner)
    assert len(items) == 3
    assert [i['matched_skills'] for i in items if i['applicant_name'] == 'Other'] == [[]]
    assert {i['publication_id']: i['matched_skills'] for i in items
            if i['applicant_name'] == 'Алекс'} == {first: ['Python'], second: ['UX/UI']}
    assert client.patch('/users/me', headers=candidate, json={'skills': 'Figma'}).status_code == 200
    assert all(not i['matched_skills'] for i in received(client, owner))


def test_author_only_and_no_sensitive_fields(client, people):
    owner, candidate, outsider = people
    pid = publish(client, owner, 'Python')
    aid = apply(client, candidate, pid, 'Python, private-unmatched-skill')
    assert client.get('/applications/received').status_code == 401
    assert received(client, outsider) == []
    assert received(client, candidate) == []
    assert client.get('/applications/received?author_id=1', headers=outsider).json() == []
    for action in ('accept', 'reject'):
        assert client.patch(f'/applications/{aid}/{action}', headers=outsider).status_code == 403
    item = received(client, owner)[0]
    base_fields = {'id', 'publication_id', 'applicant_id', 'message', 'status', 'created_at', 'updated_at'}
    assert set(item) == base_fields | {'applicant_name', 'matched_skills', 'explanation'}
    for secret in ('alex@example.com', 'Private candidate biography', 'private-unmatched-skill',
                   'password123', 'password_hash', 'email'):
        assert secret not in str(item)
    assert set(client.get('/applications/sent', headers=candidate).json()[0]) == base_fields
    other_pid = publish(client, outsider, 'Python')
    other_aid = apply(client, candidate, other_pid, 'Python')
    assert [i['id'] for i in received(client, outsider)] == [other_aid]
    assert [i['id'] for i in received(client, owner)] == [aid]


@pytest.mark.parametrize(('action', 'status'), [('accept', 'accepted'), ('reject', 'rejected')])
def test_manual_status_changes_and_closed_publication(client, people, action, status):
    owner, candidate, _ = people
    pid = publish(client, owner, 'Python')
    aid = apply(client, candidate, pid, 'Python')
    before = received(client, owner)[0]
    assert before['status'] == 'pending'
    assert client.patch(f'/applications/{aid}/{action}', headers=owner).status_code == 200
    assert client.patch(f'/publications/{pid}', headers=owner, json={'status': 'closed'}).status_code == 200
    after = received(client, owner)[0]
    assert after['status'] == status
    assert after['matched_skills'] == before['matched_skills'] == ['Python']
    assert after['explanation'] == before['explanation']
    assert client.patch(f'/applications/{aid}/{action}', headers=owner).status_code == 409
