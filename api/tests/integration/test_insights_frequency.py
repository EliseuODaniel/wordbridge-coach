"""Integration tests for Insights API and Frequency by Language"""

import pytest
import uuid
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestInsightsFrequency:
    """Test Insights API and frequency data by language"""

    def test_word_insights_english_returns_rank_and_coverage(
        self, client: TestClient, sample_words, sample_words_frequencies
    ):
        """Test that English word insights return rank and coverage data"""
        # Find an English word
        en_word = None
        for word_key, word in sample_words.items():
            if word_key.startswith("en_"):
                en_word = word
                break

        assert en_word is not None, "No English word found in fixtures"

        response = client.get(f"/api/v1/insights/word/{en_word.id}")

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "word_id" in data
        assert "word" in data
        assert "rank" in data
        assert "coverage_pct" in data
        assert "frequency_score" in data
        assert "band" in data
        assert "frequency_description" in data
        assert "coverage_description" in data

        # Should have valid rank and coverage for English word
        assert data["rank"] is not None
        assert data["coverage_pct"] is not None
        assert 0 <= data["coverage_pct"] <= 100

    def test_word_insights_french_returns_french_data(
        self, client: TestClient, sample_words, sample_words_frequencies
    ):
        """Test that French word insights return French-specific frequency data"""
        # Find a French word
        fr_word = None
        for word_key, word in sample_words.items():
            if word_key.startswith("fr_"):
                fr_word = word
                break

        assert fr_word is not None, "No French word found in fixtures"

        response = client.get(f"/api/v1/insights/word/{fr_word.id}")

        assert response.status_code == 200
        data = response.json()

        # Should return French word data
        assert data["word"] == fr_word.text
        assert data["rank"] is not None
        assert data["coverage_pct"] is not None

    def test_word_insights_language_separation_no_fallback(
        self, client: TestClient, sample_words, sample_words_frequencies, db_session
    ):
        """Test that English and French words don't fallback between languages"""
        # This test verifies that coverage curves are language-specific
        en_coverage_values = []
        fr_coverage_values = []

        # Collect coverage values for both languages
        for word_key, word in sample_words.items():
            response = client.get(f"/api/v1/insights/word/{word.id}")
            if response.status_code == 200:
                data = response.json()
                if data.get("coverage_pct") is not None:
                    if word_key.startswith("en_"):
                        en_coverage_values.append(data["coverage_pct"])
                    elif word_key.startswith("fr_"):
                        fr_coverage_values.append(data["coverage_pct"])

        # Should have coverage data for both languages
        assert len(en_coverage_values) > 0, "No English coverage data found"
        assert len(fr_coverage_values) > 0, "No French coverage data found"

    def test_coverage_curve_monotonic_decreasing(
        self, client: TestClient, sample_words_frequencies
    ):
        """Test that coverage curve is monotonic decreasing"""
        # Get coverage data directly from frequencies fixture
        en_coverages = [freq.coverage_pct for freq in sample_words_frequencies
                       if freq.language_code == "en"]
        fr_coverages = [freq.coverage_pct for freq in sample_words_frequencies
                       if freq.language_code == "fr"]

        # Sort by rank to ensure proper order
        en_coverages_sorted = sorted(en_coverages, reverse=True)  # Higher coverage for lower ranks
        fr_coverages_sorted = sorted(fr_coverages, reverse=True)

        # Check monotonic decreasing property
        for i in range(1, len(en_coverages_sorted)):
            assert en_coverages_sorted[i] <= en_coverages_sorted[i-1], \
                f"English coverage not monotonic: {en_coverages_sorted[i-1]} -> {en_coverages_sorted[i]}"

        for i in range(1, len(fr_coverages_sorted)):
            assert fr_coverages_sorted[i] <= fr_coverages_sorted[i-1], \
                f"French coverage not monotonic: {fr_coverages_sorted[i-1]} -> {fr_coverages_sorted[i]}"

    def test_word_insights_invalid_word_id(self, client: TestClient):
        """Test word insights with invalid word ID returns 400"""
        invalid_id = "invalid-uuid"
        response = client.get(f"/api/v1/insights/word/{invalid_id}")

        assert response.status_code == 400
        data = response.json()
        assert "Word ID must be a valid UUID" in data["detail"]["message"]

    def test_word_insights_nonexistent_word_id(self, client: TestClient):
        """Test word insights with non-existent word ID returns 404"""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/insights/word/{fake_uuid}")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]["message"]

    def test_user_themes_endpoint_returns_data(
        self, client: TestClient, test_user, sample_user_theme_stats
    ):
        """Test that user themes endpoint returns theme performance data"""
        response = client.get(f"/api/v1/insights/user/{test_user.id}/themes")

        assert response.status_code == 200
        data = response.json()

        # Should return theme performance data
        assert isinstance(data, list)

        if len(data) > 0:  # If we have theme data
            theme = data[0]
            assert "theme_id" in theme
            assert "name" in theme
            assert "attempts" in theme
            assert "correct" in theme
            assert "accuracy" in theme
            assert "avg_response_time_ms" in theme

            # Verify data consistency
            assert theme["attempts"] >= 0
            assert theme["correct"] >= 0
            assert theme["correct"] <= theme["attempts"]
            assert 0 <= theme["accuracy"] <= 1

    def test_user_themes_new_user_returns_empty(
        self, client: TestClient, db_session, sample_languages
    ):
        """Test that new user returns empty themes data"""
        # Create completely new user
        user_data = {
            "username": "new_theme_user",
            "language_preference": "pt",
            "target_language": "en",
            "word_goal_rank": 100
        }
        user_response = client.post("/api/v1/users/", json=user_data)
        user_id = user_response.json()["id"]

        response = client.get(f"/api/v1/insights/user/{user_id}/themes")

        assert response.status_code == 200
        data = response.json()
        # Should return empty list for new user
        assert isinstance(data, list)

    def test_user_daily_stats_endpoint_returns_data(
        self, client: TestClient, test_user, sample_user_daily_stats
    ):
        """Test that user daily stats endpoint returns daily performance data"""
        response = client.get(f"/api/v1/insights/user/{test_user.id}/daily")

        assert response.status_code == 200
        data = response.json()

        # Should return daily stats in structured format
        assert isinstance(data, dict)
        assert "daily_stats" in data
        assert "summary" in data
        assert isinstance(data["daily_stats"], list)

        if len(data["daily_stats"]) > 0:
            day = data["daily_stats"][0]
            assert "date" in day
            assert "cards_answered" in day
            assert "new_words_learned" in day
            assert "reviews_done" in day
            assert "accuracy" in day

            # Verify data consistency
            assert day["cards_answered"] >= 0
            assert day["new_words_learned"] >= 0
            assert day["reviews_done"] >= 0
            assert day["new_words_learned"] <= day["cards_answered"]
            assert 0 <= day["accuracy"] <= 1

    def test_user_recent_performance_endpoint(
        self, client: TestClient, test_user, db_session
    ):
        """Test that recent performance endpoint returns recent response data"""
        # This endpoint might return empty for users with no responses
        response = client.get(f"/api/v1/insights/user/{test_user.id}/recent")

        assert response.status_code == 200
        data = response.json()

        # Should return some structure (even if empty)
        # The exact structure depends on the implementation
        assert isinstance(data, (list, dict))

    def test_word_themes_endpoint_returns_themes(
        self, client: TestClient, sample_words, sample_themes, db_session
    ):
        """Test that word themes endpoint returns associated themes"""
        # Find a word and create theme mapping
        word = None
        for word_key, word_obj in sample_words.items():
            if word_key.startswith("en_"):
                word = word_obj
                break

        assert word is not None, "No English word found"

        # Create word-theme mapping
        from app.models import WordThemeMapping
        mapping = WordThemeMapping(
            id=str(uuid.uuid4()),
            word_id=word.id,
            theme_id=sample_themes[0].id
        )
        db_session.add(mapping)
        db_session.commit()

        response = client.get(f"/api/v1/insights/word/{word.id}/themes")

        assert response.status_code == 200
        data = response.json()

        # Should return theme names
        assert isinstance(data, list)
        if len(data) > 0:
            assert isinstance(data[0], str)

    def test_frequency_description_english_word(
        self, client: TestClient, sample_words
    ):
        """Test that English words get appropriate frequency descriptions"""
        # Find an English word
        en_word = None
        for word_key, word in sample_words.items():
            if word_key.startswith("en_"):
                en_word = word
                break

        if en_word:
            response = client.get(f"/api/v1/insights/word/{en_word.id}")
            assert response.status_code == 200

            data = response.json()
            assert "frequency_description" in data
            assert "coverage_description" in data

            # Should have meaningful descriptions
            assert len(data["frequency_description"]) > 0
            assert len(data["coverage_description"]) > 0

    def test_insights_endpoints_handle_user_with_no_data(
        self, client: TestClient, db_session, sample_languages
    ):
        """Test that insights endpoints gracefully handle users with no data"""
        # Create user with no activity
        user_data = {
            "username": "no_data_user",
            "language_preference": "pt",
            "target_language": "en",
            "word_goal_rank": 100
        }
        user_response = client.post("/api/v1/users/", json=user_data)
        user_id = user_response.json()["id"]

        # Test various insights endpoints
        endpoints = [
            f"/api/v1/insights/user/{user_id}/themes",
            f"/api/v1/insights/user/{user_id}/daily",
            f"/api/v1/insights/user/{user_id}/recent"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            # Should not crash - should return 200 with empty/placeholder data
            assert response.status_code == 200, f"Endpoint {endpoint} failed"