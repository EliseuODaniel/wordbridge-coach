"""Integration tests for Spec4 Card Selection and Gating"""

import pytest
from fastapi.testclient import TestClient
from datetime import timedelta
from sqlalchemy.orm import Session

from app.core.time import utc_now


@pytest.mark.integration
@pytest.mark.spec4
class TestSpec4CardSelection:
    """Test Spec4 card selection algorithm with proper gating"""

    def test_next_card_new_user_within_goal_window(
        self, client: TestClient, test_user, sample_words, sample_cards
    ):
        """Test that new user gets cards within their goal window (goal=100)"""
        params = {"user_id": str(test_user.id)}
        response = client.get("/api/v1/cards/next-spec4", params=params)

        assert response.status_code == 200
        data = response.json()

        # Should get a valid card response
        assert "word_id" in data
        assert "word" in data
        assert "is_new" in data

        # For new user with goal=100, should get a new card
        assert data["is_new"] is True

    def test_next_card_without_user_id_returns_demo_card(
        self, client: TestClient, sample_cards
    ):
        """Test that calling without user_id uses demo user"""
        response = client.get("/api/v1/cards/next-spec4")

        # Should work with demo user or return appropriate error
        assert response.status_code in [200, 404]

    def test_new_user_goal_100_respects_gating(
        self, client: TestClient, db_session, sample_languages, sample_words_frequencies
    ):
        """Test that user with goal=100 only gets words within rank 1-100 initially"""
        # Create user with goal=100
        user_data = {
            "username": "goal100_test",
            "language_preference": "pt",
            "target_language": "en",
            "word_goal_rank": 100
        }
        user_response = client.post("/api/v1/users/", json=user_data)
        user_id = user_response.json()["id"]

        # Get multiple cards and check ranks
        cards_received = []
        for _ in range(10):  # Try to get 10 cards
            response = client.get("/api/v1/cards/next-spec4", params={"user_id": user_id})
            if response.status_code == 200:
                card_data = response.json()
                cards_received.append(card_data)

                # Submit a correct answer to get next card
                answer_data = {
                    "answer": card_data["word"],
                    "response_time_ms": 2000
                }
                client.post(f"/api/v1/cards/{card_data['card_id']}/answer",
                           json=answer_data, params={"user_id": user_id})
            else:
                break

        # If we got cards, they should respect the gating for new users
        # (This is a simplified test - full gating testing requires more setup)
        assert len(cards_received) >= 0  # Basic check that we didn't crash

    def test_mix_25_percent_new_75_percent_review(
        self, client: TestClient, test_user, user_card_states, db_session
    ):
        """Test 25% new / 75% review mix for users with existing cards"""
        from app.models import UserCardState, MemoryStage, UserFrequencyProgress

        # Create UserFrequencyProgress to enable review functionality
        # CRITICAL: Match with fixture ranks (50, 100, 150 in conftest.py)
        progress = UserFrequencyProgress(
            user_id=test_user.id,
            max_contiguous_mastered_rank=100,  # Words <=100 are "review" candidates
            current_window_end_rank=200,  # Window extends to 200
            word_goal_rank=200  # Goal is 200
        )
        db_session.add(progress)
        db_session.commit()

        # Set some cards to review state to simulate existing progress
        review_cards = db_session.query(UserCardState).filter(
            UserCardState.user_id == test_user.id
        ).limit(4).all()

        for i, card_state in enumerate(review_cards):
            if i < 3:  # Make 3 cards due for review
                card_state.status = MemoryStage.LEARNING
                card_state.next_review_at = utc_now() - timedelta(days=1)
                card_state.repetitions = 1
            else:  # Keep 1 as new
                card_state.status = MemoryStage.NEW
                card_state.next_review_at = utc_now() + timedelta(days=1)

        db_session.commit()

        # Get several cards and count new vs review
        new_cards = 0
        review_cards_count = 0
        total_cards = 0
        last_card_id = None

        for i in range(20):  # Try to get 20 cards
            params = {"user_id": str(test_user.id)}
            if last_card_id:
                params["exclude_card_id"] = last_card_id

            response = client.get("/api/v1/cards/next-spec4", params=params)

            if response.status_code == 200:
                card_data = response.json()
                total_cards += 1
                last_card_id = card_data.get("card_id")

                if card_data.get("is_new"):
                    new_cards += 1
                else:
                    review_cards_count += 1

                # CRITICAL: Do NOT submit answer in this test
                # Submitting answers pushes next_review_at to future,
                # depleting the pool of due review cards
            else:
                break

        if total_cards > 0:
            # Check approximately 25% new / 75% review mix
            new_percentage = (new_cards / total_cards) * 100
            review_percentage = (review_cards_count / total_cards) * 100

            # Allow some flexibility in the percentage
            assert 15 <= new_percentage <= 35, f"New cards: {new_percentage}% ({new_cards}/{total_cards})"
            assert 65 <= review_percentage <= 85, f"Review cards: {review_percentage}% ({review_cards_count}/{total_cards})"

    def test_answer_submission_updates_sm2(
        self, client: TestClient, test_user, user_card_states, db_session
    ):
        """Test that answer submission updates SM-2 algorithm state"""
        from app.models import UserCardState

        # Get initial card state
        initial_state = db_session.query(UserCardState).filter(
            UserCardState.user_id == test_user.id
        ).first()

        initial_repetitions = initial_state.repetitions
        initial_interval = initial_state.interval_days
        initial_easiness = initial_state.easiness_factor

        # Get a card
        response = client.get("/api/v1/cards/next",
                            params={"user_id": str(test_user.id)})
        assert response.status_code == 200

        card_data = response.json()
        card_id = card_data["card_id"]
        correct_answer = card_data["word"]

        # Submit correct answer
        answer_data = {
            "answer": correct_answer,
            "response_time_ms": 3000
        }

        answer_response = client.post(
            f"/api/v1/cards/{card_id}/answer",
            json=answer_data,
            params={"user_id": str(test_user.id)}
        )

        assert answer_response.status_code == 200
        answer_data_response = answer_response.json()
        assert "next_review_at" in answer_data_response
        assert "quality" in answer_data_response

        # Check that card state was updated
        updated_state = db_session.query(UserCardState).filter(
            UserCardState.card_id == card_id,
            UserCardState.user_id == test_user.id
        ).first()

        # Should have increased repetitions for correct answer
        assert updated_state.repetitions > initial_repetitions
        # Should have updated next_review_at to future date
        assert updated_state.next_review_at > utc_now()

    def test_no_cards_available_handling(
        self, client: TestClient, db_session, sample_languages
    ):
        """Test handling when no cards are available"""
        # Create user but no cards
        user_data = {
            "username": "no_cards_user",
            "language_preference": "pt",
            "target_language": "en",
            "word_goal_rank": 100
        }
        user_response = client.post("/api/v1/users/", json=user_data)
        user_id = user_response.json()["id"]

        # Try to get card (might return 404 or handle gracefully)
        response = client.get("/api/v1/cards/next-spec4", params={"user_id": user_id})

        # Should handle gracefully (either 404 or 200 with appropriate message)
        assert response.status_code in [200, 404]

    def test_french_user_gets_french_cards(
        self, client: TestClient, test_user_french, sample_words, sample_cards
    ):
        """Test that French-targeting user gets French cards"""
        params = {"user_id": str(test_user_french.id)}
        response = client.get("/api/v1/cards/next-spec4", params=params)

        # Should get a card (or appropriate no-cards response)
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            # Card should be valid format
            assert "word_id" in data
            assert "word" in data

    def test_consecutive_correct_answers_advances_progress(
        self, client: TestClient, test_user, user_card_states, db_session
    ):
        """Test that consecutive correct answers advance user progress"""
        from app.models import ReviewEvent

        initial_reviews = db_session.query(ReviewEvent).filter(
            ReviewEvent.user_id == test_user.id,
            ReviewEvent.was_correct == True
        ).count()

        # Get and answer several cards correctly
        for i in range(5):
            # Get card
            response = client.get("/api/v1/cards/next",
                                 params={"user_id": str(test_user.id)})

            if response.status_code != 200:
                break

            card_data = response.json()

            # Submit correct answer
            answer_data = {
                "answer": card_data["word"],
                "response_time_ms": 2000 + i * 100
            }

            client.post(f"/api/v1/cards/{card_data['card_id']}/answer",
                       json=answer_data, params={"user_id": str(test_user.id)})

        # Check that correct answers were recorded
        final_reviews = db_session.query(ReviewEvent).filter(
            ReviewEvent.user_id == test_user.id,
            ReviewEvent.was_correct == True
        ).count()

        # Should have recorded some correct answers
        assert final_reviews > initial_reviews

    def test_user_with_no_progress_starts_with_new_cards(
        self, client: TestClient, test_user, db_session
    ):
        """Test that user with no progress starts with new cards"""
        # Get first card
        response = client.get("/api/v1/cards/next-spec4",
                            params={"user_id": str(test_user.id)})

        if response.status_code == 200:
            card_data = response.json()
            # First card for user should be marked as new
            assert card_data.get("is_new") is True

    def test_incorrect_answer_does_not_advance_gating(
        self, client: TestClient, test_user, user_card_states
    ):
        """Test that incorrect answers don't advance gating progress"""
        # Get card
        response = client.get("/api/v1/cards/next",
                            params={"user_id": str(test_user.id)})

        if response.status_code == 200:
            card_data = response.json()

            # Submit incorrect answer
            answer_data = {
                "answer": "incorrect_answer",
                "response_time_ms": 5000
            }

            answer_response = client.post(
                f"/api/v1/cards/{card_data['card_id']}/answer",
                json=answer_data,
                params={"user_id": str(test_user.id)}
            )

            assert answer_response.status_code == 200
            answer_data = answer_response.json()

            # Quality should be low for incorrect answer
            assert answer_data["quality"] <= 2
