"""Integration tests for word insights by card."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_word_insights_by_card_matches_word_endpoint(client: TestClient, sample_cards):
    card = next(iter(sample_cards.values()))
    assert card.sentence is not None
    assert card.sentence.word is not None

    by_word = client.get(f'/api/v1/insights/word/{card.sentence.word.id}')
    by_card = client.get(f'/api/v1/insights/word-by-card/{card.id}')

    assert by_word.status_code == 200
    assert by_card.status_code == 200
    assert by_card.json() == by_word.json()


@pytest.mark.integration
def test_word_insights_by_card_invalid_id_returns_400(client: TestClient):
    response = client.get('/api/v1/insights/word-by-card/invalid-uuid')

    assert response.status_code == 400
    data = response.json()
    assert 'Card ID must be a valid UUID' in data['detail']['message']
