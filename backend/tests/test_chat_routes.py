import os
from unittest.mock import patch

import pytest

os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')
os.environ.setdefault('GROQ_API_KEY', 'test-groq-key')

from backend.app import create_app
from backend.auth.jwt_handler import create_access_token


@pytest.fixture
def app():
    application = create_app()
    application.config.update({
        'TESTING': True,
        'GROQ_API_KEY': 'test-groq-key',
    })
    return application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers(app):
    with app.app_context():
        token = create_access_token(subject=1, role='staff')
    return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}


def test_chat_history_empty(client, auth_headers):
    response = client.get('/api/chat/history?limit=30', headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json() == []


def test_chat_requires_message(client, auth_headers):
    response = client.post('/api/chat', headers=auth_headers, json={'message': '   '})
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] is True
    assert data['message'] == 'Message is required'


@patch('backend.services.chat_service.AIOrchestrator')
def test_chat_persists_and_returns_history(mock_orchestrator, client, auth_headers):
    mock_orchestrator.return_value.orchestrate.return_value = {
        'reply': 'Done.',
        'actions': [],
        'validation': [],
        'all_valid': True,
    }

    post_response = client.post(
        '/api/chat',
        headers=auth_headers,
        json={'message': 'Show inventory', 'session_id': 'test-session'},
    )
    assert post_response.status_code == 200
    post_data = post_response.get_json()
    assert post_data['reply'] == 'Done.'

    history_response = client.get(
        '/api/chat/history?limit=30&session_id=test-session',
        headers=auth_headers,
    )
    assert history_response.status_code == 200
    history = history_response.get_json()
    assert len(history) == 1
    assert history[0]['user_prompt'] == 'Show inventory'
    assert history[0]['ai_response'] == 'Done.'


def test_chat_history_requires_auth(client):
    response = client.get('/api/chat/history?limit=30')
    assert response.status_code == 401
