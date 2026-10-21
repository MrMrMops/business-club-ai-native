import pytest

from app.services.matching import extract_skills
from tests.test_publications import create_user_and_token, auth_headers


@pytest.fixture()
def people(client):
    viewer = auth_headers(create_user_and_token(client, 'Viewer', 'viewer@example.com'))
    author = auth_headers(create_user_and_token(client, 'Author', 'author@example.com'))
    return viewer, author


def publish(client, headers, requirements, status='active', description=None):
    response = client.post('/publications', headers=headers, json={
        'type': 'startup', 'title': 'Matching project',
        'description': description or 'A meaningful project description.',
        'looking_for': requirements,
    })
    assert response.status_code == 201
    publication = response.json()
    if status == 'closed':
        assert client.patch(f"/publications/{publication['id']}", headers=headers,
                            json={'status': status}).status_code == 200
    return publication['id']


def recommend(client, viewer, skills):
    assert client.patch('/users/me', headers=viewer, json={'skills': skills}).status_code == 200
    response = client.get('/publications/recommended', headers=viewer)
    assert response.status_code == 200
    return response.json()


def test_matching_and_public_response(client, people):
    viewer, author = people
    assert client.patch('/users/me', headers=author, json={
        'bio': 'Private biography', 'skills': 'Private skills',
    }).status_code == 200
    pid = publish(client, author, 'Python, FastAPI, PostgreSQL')
    result = recommend(client, viewer, 'PYTHON, FastAPI')
    assert len(result) == 1
    item = result[0]
    assert item['id'] == pid
    assert item['matched_skills'] == ['FastAPI', 'Python']
    assert item['author_name'] == 'Author'
    assert 'FastAPI, Python' in item['explanation']
    assert set(item) == {
        'id', 'author_id', 'author_name', 'type', 'title', 'description',
        'looking_for', 'status', 'created_at', 'updated_at', 'matched_skills', 'explanation',
    }
    assert 'author@example.com' not in str(result)
    assert 'Private biography' not in str(result)
    assert 'Private skills' not in str(result)


@pytest.mark.parametrize('skills', [None, '', '  \n ', 'photography', 'Java'])
def test_empty_or_no_matching_skills(client, people, skills):
    viewer, author = people
    publish(client, author, 'Python, JavaScript')
    assert recommend(client, viewer, skills) == []


def test_own_and_closed_excluded(client, people):
    viewer, author = people
    publish(client, viewer, 'Python')
    publish(client, author, 'Python', status='closed')
    assert recommend(client, viewer, 'Python') == []


def test_requires_authentication_and_static_route(client):
    response = client.get('/publications/recommended')
    assert response.status_code == 401


@pytest.mark.parametrize(('skills', 'requirements', 'expected'), [
    ('бэкенд, дизайн интерфейсов', 'BACKEND; UX/UI', ['Backend', 'UX/UI']),
    ('BACK-END, UI/UX', 'бекенд, дизайнер интерфейсов', ['Backend', 'UX/UI']),
    ('Пайтон, Фигма', 'Python developer; FIGMA', ['Figma', 'Python']),
    ('product analytics', 'Ищем продуктового аналитика', ['Продуктовая аналитика']),
    ('react.js, fast-api', 'ReactJS, FAST API', ['FastAPI', 'React']),
])
def test_bilingual_synonyms(client, people, skills, requirements, expected):
    viewer, author = people
    publish(client, author, requirements)
    result = recommend(client, viewer, skills)
    assert result[0]['matched_skills'] == expected


@pytest.mark.parametrize(('text', 'excluded'), [
    ('NoSQL, MySQL, SQLAlchemy', 'SQL'),
    ('JavaScript', 'Java'),
    ('Reactivate reactions', 'React'),
    ('GitHub', 'Git'),
    ('build guide', 'UX/UI'),
    ('fast application', 'FastAPI'),
])
def test_no_substring_matches(text, excluded):
    assert excluded not in extract_skills(text)


def test_only_requirements_not_incidental_description(client, people):
    viewer, author = people
    publish(client, author, 'UX/UI designer', description='Our backend already uses Python.')
    assert recommend(client, viewer, 'Python') == []


def test_top_three_distinct_skills_and_deterministic_ties(client, people):
    viewer, author = people
    publish(client, author, 'Python Python PYTHON питон')
    second = publish(client, author, 'Python, SQL')
    third = publish(client, author, 'Python, SQL')
    first = publish(client, author, 'Python, SQL, FastAPI')
    result = recommend(client, viewer, 'Python, SQL, FastAPI')
    assert [p['id'] for p in result] == [first, third, second]
    assert client.get('/publications/recommended', headers=viewer).json() == result
    assert len(client.get('/publications').json()) == 4
    assert client.get(f'/publications/{first}').status_code == 200
