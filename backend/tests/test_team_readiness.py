import pytest

from tests.test_publications import auth_headers, create_user_and_token
from tests.test_recommendations import publish


@pytest.fixture()
def team(client):
    owner = auth_headers(create_user_and_token(client, 'Owner', 'owner@example.com'))
    candidate = auth_headers(create_user_and_token(client, 'Candidate', 'candidate@example.com'))
    return owner, candidate


def join(client, owner, candidate, pid, skills, action=None):
    assert client.patch('/users/me', headers=candidate, json={'skills': skills}).status_code == 200
    response = client.post(f'/publications/{pid}/applications', headers=candidate,
                           json={'message': 'Ready to discuss the project'})
    assert response.status_code == 201
    if action:
        assert client.patch(f"/applications/{response.json()['id']}/{action}", headers=owner).status_code == 200


def readiness(client, owner, pid):
    response = client.get(f'/publications/{pid}/team-readiness', headers=owner)
    assert response.status_code == 200
    return response.json()


@pytest.mark.parametrize(('action', 'count', 'covered'), [
    (None, 0, []), ('reject', 0, []), ('accept', 1, ['Backend', 'Python']),
])
def test_only_accepted_and_synonyms(client, team, action, count, covered):
    owner, candidate = team
    pid = publish(client, owner, 'Python, BACK-END, дизайн интерфейсов')
    join(client, owner, candidate, pid, 'ПАЙТОН, бэкенд, FastAPI', action)
    result = readiness(client, owner, pid)
    assert result['accepted_count'] == count
    assert result['covered_skills'] == covered
    assert result['required_skills'] == ['Backend', 'Python', 'UX/UI']
    assert result['missing_skills'] == (['UX/UI'] if count else result['required_skills'])
    assert 'UX/UI' in result['recommendation']


def test_union_isolation_and_current_skills(client, team):
    owner, candidate = team
    other = auth_headers(create_user_and_token(client, 'Other', 'other@example.com'))
    pid = publish(client, owner, 'Python, UX/UI, SQL')
    unrelated = publish(client, owner, 'SQL')
    join(client, owner, candidate, pid, 'Python; UX/UI', 'accept')
    join(client, owner, other, pid, 'Python; NoSQL', 'accept')
    result = readiness(client, owner, pid)
    assert result['accepted_count'] == 2
    assert result['covered_skills'] == ['Python', 'UX/UI']
    assert result['missing_skills'] == ['SQL']
    assert readiness(client, owner, unrelated)['covered_skills'] == []
    assert client.patch('/users/me', headers=candidate, json={'skills': 'SQL'}).status_code == 200
    result = readiness(client, owner, pid)
    assert result['covered_skills'] == ['Python', 'SQL']
    assert result['missing_skills'] == ['UX/UI']


def test_no_applications_and_author_excluded(client, team):
    owner, _ = team
    assert client.patch('/users/me', headers=owner, json={'skills': 'Python'}).status_code == 200
    pid = publish(client, owner, 'Python')
    result = readiness(client, owner, pid)
    assert result['accepted_count'] == 0
    assert result['covered_skills'] == []
    assert result['missing_skills'] == ['Python']


@pytest.mark.parametrize('skills', [None, '', '  ', 'JavaScript'])
def test_empty_or_unmatched_profiles(client, team, skills):
    owner, candidate = team
    pid = publish(client, owner, 'Java')
    join(client, owner, candidate, pid, skills, 'accept')
    result = readiness(client, owner, pid)
    assert result['accepted_count'] == 1
    assert result['covered_skills'] == []
    assert result['missing_skills'] == ['Java']


def test_unknown_requirements_not_ready(client, team):
    owner, candidate = team
    pid = publish(client, owner, 'Космическая биология')
    join(client, owner, candidate, pid, 'Python', 'accept')
    result = readiness(client, owner, pid)
    assert result['required_skills'] == result['covered_skills'] == result['missing_skills'] == []
    assert 'Требования не распознаны' in result['recommendation']


def test_partial_recognition_and_closed_publication(client, team):
    owner, candidate = team
    pid = publish(client, owner, 'Python, космическая биология')
    join(client, owner, candidate, pid, 'Python', 'accept')
    assert client.patch(f'/publications/{pid}', headers=owner, json={'status': 'closed'}).status_code == 200
    result = readiness(client, owner, pid)
    assert result['covered_skills'] == ['Python']
    assert result['missing_skills'] == []
    assert 'распознанные' in result['recommendation']
    assert 'Нераспознанные требования' in result['limitation']
    assert 'не гарантия готовности' in result['limitation']
    assert client.patch(f'/publications/{pid}', headers=owner, json={'looking_for': 'SQL'}).status_code == 200
    assert readiness(client, owner, pid)['missing_skills'] == ['SQL']


def test_access_and_minimal_response(client, team):
    owner, candidate = team
    pid = publish(client, owner, 'Python')
    join(client, owner, candidate, pid, 'Python', 'accept')
    path = f'/publications/{pid}/team-readiness'
    assert client.get(path).status_code == 401
    assert client.get(path, headers=candidate).status_code == 403
    assert client.get('/publications/999999/team-readiness', headers=owner).status_code == 404
    result = readiness(client, owner, pid)
    assert set(result) == {'accepted_count', 'required_skills', 'covered_skills',
                           'missing_skills', 'recommendation', 'limitation'}
    assert 'candidate@example.com' not in str(result)
    assert 'Candidate' not in str(result)
    assert 'team_readiness' not in client.get(f'/publications/{pid}').json()
