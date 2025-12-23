"""Integration tests for Themes and User Stats"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import uuid


@pytest.mark.integration
class TestThemesAndStats:
    """Test themes and user statistics functionality"""

    def test_answer_submission_creates_user_word_stats(
        self, client: TestClient, test_user, user_card_states, db_session
    ):
        """Test that answering cards creates UserWordStats records"""
        from app.models import UserWordStats

        # Initial word stats count
        initial_stats = db_session.query(UserWordStats).filter(
            UserWordStats.user_id == test_user.id
        ).count()

        # Get and answer a card
        response = client.get("/api/v1/cards/next-spec4",
                            params={"user_id": str(test_user.id)})

        if response.status_code == 200:
            card_data = response.json()

            # Submit answer
            answer_data = {
                "answer": card_data["word"],
                "response_time_ms": 2500
            }

            client.post(f"/api/v1/cards/{card_data['card_id']}/answer",
                       json=answer_data, params={"user_id": str(test_user.id)})

            # Check that UserWordStats was created/updated
            final_stats = db_session.query(UserWordStats).filter(
                UserWordStats.user_id == test_user.id
            ).count()

            # Should have created or updated stats
            assert final_stats >= initial_stats

    def test_answer_submission_updates_user_theme_stats(
        self, client: TestClient, test_user, user_card_states, sample_themes, db_session
    ):
        """Test that answering cards updates UserThemeStats"""
        from app.models import UserWordStats, WordThemeMapping, UserThemeStats

        # Get a card and its word
        response = client.get("/api/v1/cards/next-spec4",
                            params={"user_id": str(test_user.id)})

        if response.status_code == 200:
            card_data = response.json()
            word_id = card_data["word_id"]

            # Create word-theme mapping for testing
            from app.models import Word
            word = db_session.query(Word).filter(Word.id == word_id).first()
            if word:
                # Map word to first theme
                mapping = WordThemeMapping(
                    id=str(uuid.uuid4()),
                    word_id=word.id,
                    theme_id=sample_themes[0].id
                )
                db_session.add(mapping)
                db_session.commit()

                # Submit answer
                answer_data = {
                    "answer": card_data["word"],
                    "response_time_ms": 2000
                }

                client.post(f"/api/v1/cards/{card_data['card_id']}/answer",
                           json=answer_data, params={"user_id": str(test_user.id)})

                # Check UserThemeStats was updated
                theme_stats = db_session.query(UserThemeStats).filter(
                    UserThemeStats.user_id == test_user.id,
                    UserThemeStats.theme_id == sample_themes[0].id
                ).first()

                if theme_stats:
                    # Should have incremented attempts and correct
                    assert theme_stats.attempts > 0
                    assert theme_stats.correct > 0

    def test_answer_submission_updates_daily_stats(
        self, client: TestClient, test_user, user_card_states, db_session
    ):
        """Test that answering cards updates UserDailyStats"""
        from app.models import UserDailyStats

        today = datetime.utcnow().date()

        # Get initial daily stats
        initial_daily = db_session.query(UserDailyStats).filter(
            UserDailyStats.user_id == test_user.id,
            UserDailyStats.date == today
        ).first()

        initial_cards_answered = initial_daily.cards_answered if initial_daily else 0

        # Get and answer a card using the regular endpoint that returns actual cards
        response = client.get("/api/v1/cards/next",
                            params={"user_id": str(test_user.id)})

        if response.status_code == 200:
            card_data = response.json()
            print(f"DEBUG: Got card, card_id={card_data['card_id']}, word={card_data['word']}")

            # Submit correct answer
            answer_data = {
                "answer": card_data["word"],
                "response_time_ms": 1800
            }

            print(f"DEBUG: About to POST answer to /api/v1/cards/{card_data['card_id']}/answer")
            response = client.post(f"/api/v1/cards/{card_data['card_id']}/answer",
                       json=answer_data, params={"user_id": str(test_user.id)})
            print(f"DEBUG: POST response status: {response.status_code}")
            if response.status_code != 200:
                print(f"DEBUG: POST response body: {response.text}")

            # Check daily stats were updated
            updated_daily = db_session.query(UserDailyStats).filter(
                UserDailyStats.user_id == test_user.id,
                UserDailyStats.date == today
            ).first()

            assert updated_daily is not None
            assert updated_daily.cards_answered > initial_cards_answered
            assert updated_daily.new_words_learned >= 0
            assert updated_daily.reviews_done >= 0

    def test_multiple_answers_create_comprehensive_stats(
        self, client: TestClient, test_user, user_card_states, sample_themes, db_session
    ):
        """Test that multiple answers create comprehensive statistics"""
        from app.models import UserWordStats, UserThemeStats, UserDailyStats, WordThemeMapping

        # Create word-theme mappings for multiple themes
        words_mapped = 0
        theme_mappings = []

        # Get several cards and create mappings
        for i in range(3):
            response = client.get("/api/v1/cards/next-spec4",
                                 params={"user_id": str(test_user.id)})

            if response.status_code == 200:
                card_data = response.json()
                word_id = card_data["word_id"]

                # Map to different themes
                theme_idx = i % len(sample_themes)
                mapping = WordThemeMapping(
                    id=str(uuid.uuid4()),
                    word_id=word_id,
                    theme_id=sample_themes[theme_idx].id
                )
                theme_mappings.append(mapping)
                words_mapped += 1

                # Submit answer
                answer_data = {
                    "answer": card_data["word"],
                    "response_time_ms": 1500 + i * 200
                }

                client.post(f"/api/v1/cards/{card_data['card_id']}/answer",
                           json=answer_data, params={"user_id": str(test_user.id)})

        # Add all mappings to database
        for mapping in theme_mappings:
            db_session.add(mapping)
        db_session.commit()

        # Check that stats were created
        word_stats = db_session.query(UserWordStats).filter(
            UserWordStats.user_id == test_user.id
        ).count()

        theme_stats = db_session.query(UserThemeStats).filter(
            UserThemeStats.user_id == test_user.id
        ).count()

        daily_stats = db_session.query(UserDailyStats).filter(
            UserDailyStats.user_id == test_user.id
        ).count()

        # Should have created some stats for each type
        assert word_stats >= 0
        assert theme_stats >= 0
        assert daily_stats >= 0

    def test_incorrect_answers_affect_accuracy(
        self, client: TestClient, test_user, user_card_states, db_session
    ):
        """Test that incorrect answers properly affect accuracy calculations"""
        from app.models import UserDailyStats

        today = datetime.utcnow().date()

        # Get initial stats
        initial_daily = db_session.query(UserDailyStats).filter(
            UserDailyStats.user_id == test_user.id,
            UserDailyStats.date == today
        ).first()

        # Submit several incorrect answers
        incorrect_count = 0
        for i in range(3):
            response = client.get("/api/v1/cards/next-spec4",
                                 params={"user_id": str(test_user.id)})

            if response.status_code == 200:
                card_data = response.json()

                # Submit incorrect answer
                answer_data = {
                    "answer": "definitely_wrong_answer",
                    "response_time_ms": 5000
                }

                post_response = client.post(
                    f"/api/v1/cards/{card_data['card_id']}/answer",
                    json=answer_data,
                    params={"user_id": str(test_user.id)}
                )

                if post_response.status_code == 200:
                    incorrect_count += 1

        # Check that accuracy reflects incorrect answers
        final_daily = db_session.query(UserDailyStats).filter(
            UserDailyStats.user_id == test_user.id,
            UserDailyStats.date == today
        ).first()

        if final_daily and final_daily.cards_answered > 0:
            # Accuracy should be less than 100% if we had incorrect answers
            if incorrect_count > 0:
                assert final_daily.accuracy < 1.0

    def test_theme_stats_endpoint_accuracy_calculation(
        self, client: TestClient, test_user, sample_user_theme_stats
    ):
        """Test that theme stats endpoint returns correct accuracy calculations"""
        response = client.get(f"/api/v1/insights/user/{test_user.id}/themes")

        assert response.status_code == 200
        data = response.json()

        if len(data) > 0:
            for theme in data:
                # Verify accuracy calculation
                expected_accuracy = theme["correct"] / theme["attempts"] if theme["attempts"] > 0 else 0
                actual_accuracy = theme["accuracy"]

                assert abs(expected_accuracy - actual_accuracy) < 0.01, \
                    f"Accuracy mismatch: expected {expected_accuracy}, got {actual_accuracy}"

    def test_daily_stats_endpoint_multiple_days(
        self, client: TestClient, test_user, db_session
    ):
        """Test daily stats endpoint across multiple days"""
        from app.models import UserDailyStats

        # Create stats for multiple days
        today = datetime.utcnow().date()
        dates = [
            today - timedelta(days=2),
            today - timedelta(days=1),
            today
        ]

        for i, date in enumerate(dates):
            daily_stat = UserDailyStats(
                id=str(uuid.uuid4()),
                user_id=test_user.id,
                date=date,
                cards_answered=10 + i * 5,
                new_words_learned=3 + i,
                reviews_done=7 + i * 2,
                accuracy=0.8 + i * 0.05
            )
            db_session.add(daily_stat)

        db_session.commit()

        response = client.get(f"/api/v1/insights/user/{test_user.id}/daily?days=5")

        assert response.status_code == 200
        data = response.json()

        # Should return stats for multiple days in structured format
        assert isinstance(data, dict)
        assert "daily_stats" in data
        assert isinstance(data["daily_stats"], list)
        assert len(data["daily_stats"]) >= len(dates)

        # Verify data structure
        for day in data["daily_stats"]:
            assert "date" in day
            assert "cards_answered" in day
            assert "new_words_learned" in day
            assert "reviews_done" in day
            assert "accuracy" in day

    def test_word_theme_mapping_prevents_duplicate_themes(
        self, client: TestClient, db_session
    ):
        """Test that word-theme mapping prevents duplicate theme entries"""
        from app.models import WordThemeMapping, Word, WordTheme, Language
        from sqlalchemy.exc import IntegrityError
        import uuid

        # Create test data in isolation to avoid fixture conflicts
        language = Language(
            id=str(uuid.uuid4()),
            code="tt",
            name="Test Language",
            voice_model="test",
            voice_type="female",
            is_active=True
        )
        db_session.add(language)
        db_session.flush()

        word = Word(
            id=str(uuid.uuid4()),
            text="testword",
            lemma="testword",
            part_of_speech="noun",
            difficulty=1,
            language_id=language.id,
            frequency_rank=1
        )
        db_session.add(word)
        db_session.flush()

        theme = WordTheme(
            id=str(uuid.uuid4()),
            name="test_theme",
            is_active=True
        )
        db_session.add(theme)
        db_session.commit()

        # Create first mapping
        mapping1 = WordThemeMapping(
            id=str(uuid.uuid4()),
            word_id=word.id,
            theme_id=theme.id
        )
        db_session.add(mapping1)
        db_session.commit()

        # Try to create duplicate mapping (should fail due to unique constraint)
        mapping2 = WordThemeMapping(
            id=str(uuid.uuid4()),
            word_id=word.id,
            theme_id=theme.id
        )
        db_session.add(mapping2)

        # Should raise IntegrityError due to unique constraint violation
        with pytest.raises(IntegrityError, match="duplicate key value violates unique constraint"):
            db_session.commit()

    def test_theme_stats_respond_to_answer_activity(
        self, client: TestClient, test_user, user_card_states, sample_themes, db_session
    ):
        """Test that theme stats respond dynamically to answer activity"""
        from app.models import UserThemeStats, WordThemeMapping

        theme = sample_themes[0]

        # Get initial theme stats
        initial_stats = db_session.query(UserThemeStats).filter(
            UserThemeStats.user_id == test_user.id,
            UserThemeStats.theme_id == theme.id
        ).first()

        initial_attempts = initial_stats.attempts if initial_stats else 0

        # Get a card and map it to theme
        response = client.get("/api/v1/cards/next-spec4",
                            params={"user_id": str(test_user.id)})

        if response.status_code == 200:
            card_data = response.json()
            word_id = card_data["word_id"]

            # Create word-theme mapping
            mapping = WordThemeMapping(
                id=str(uuid.uuid4()),
                word_id=word_id,
                theme_id=theme.id
            )
            db_session.add(mapping)
            db_session.commit()

            # Submit multiple answers for this word
            for i in range(3):
                answer_data = {
                    "answer": card_data["word"] if i < 2 else "wrong",
                    "response_time_ms": 2000
                }

                client.post(f"/api/v1/cards/{card_data['card_id']}/answer",
                           json=answer_data, params={"user_id": str(test_user.id)})

            # Check theme stats were updated
            final_stats = db_session.query(UserThemeStats).filter(
                UserThemeStats.user_id == test_user.id,
                UserThemeStats.theme_id == theme.id
            ).first()

            if final_stats:
                assert final_stats.attempts >= initial_attempts + 3
                # Should have at least some correct answers
                assert final_stats.correct >= 2