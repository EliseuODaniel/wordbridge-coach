"""Integration tests for stats/settings explicit user requirements."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_stats_basic_requires_user_id(client: TestClient):
    response = client.get('/api/v1/stats/basic')

    assert response.status_code == 400
    data = response.json()
    assert data['detail']['error'] == 'user_id is required'


@pytest.mark.integration
def test_settings_requires_user_id(client: TestClient):
    response = client.get('/api/v1/settings/')

    assert response.status_code == 400
    data = response.json()
    assert data['detail']['error'] == 'user_id is required'


@pytest.mark.integration
def test_settings_and_stats_work_for_explicit_user(client: TestClient, test_user):
    stats_response = client.get(f'/api/v1/stats/basic?user_id={test_user.id}')
    settings_response = client.get(f'/api/v1/settings/?user_id={test_user.id}')

    assert stats_response.status_code == 200
    assert settings_response.status_code == 200
    assert settings_response.json()['word_goal_rank'] == test_user.word_goal_rank
