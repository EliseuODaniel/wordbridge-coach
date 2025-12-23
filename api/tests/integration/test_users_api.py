"""Integration tests for Users API"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.mark.integration
class TestUsersAPI:
    """Test Users API endpoints"""

    def test_list_users_empty(self, client: TestClient):
        """Test listing users when database is empty"""
        response = client.get("/api/v1/users/")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_user_basic(self, client: TestClient, sample_languages):
        """Test creating a basic user"""
        user_data = {
            "username": "newuser",
            "language_preference": "pt",
            "target_language": "en",
            "word_goal_rank": 500
        }

        response = client.post("/api/v1/users/", json=user_data)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["language_preference"] == "pt"
        assert "id" in data
        assert "created_at" in data

    def test_create_user_with_goal_100(self, client: TestClient, sample_languages):
        """Test creating user with specific word goal rank"""
        user_data = {
            "username": "goal100user",
            "language_preference": "pt",
            "target_language": "en",
            "word_goal_rank": 100
        }

        response = client.post("/api/v1/users/", json=user_data)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "goal100user"

    def test_create_user_french_target(self, client: TestClient, sample_languages):
        """Test creating user with French as target language"""
        user_data = {
            "username": "frenchlearner",
            "language_preference": "pt",
            "target_language": "fr",
            "word_goal_rank": 150
        }

        response = client.post("/api/v1/users/", json=user_data)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "frenchlearner"

    def test_create_user_duplicate_username(self, client: TestClient, sample_languages):
        """Test creating user with duplicate username fails"""
        user_data = {
            "username": "duplicate",
            "language_preference": "pt",
            "target_language": "en",
            "word_goal_rank": 100
        }

        # Create first user
        response1 = client.post("/api/v1/users/", json=user_data)
        assert response1.status_code == 200

        # Try to create duplicate
        response2 = client.post("/api/v1/users/", json=user_data)
        assert response2.status_code == 409
        assert "already taken" in response2.json()["detail"]["message"]

    def test_get_user_by_id(self, client: TestClient, test_user):
        """Test getting user by ID"""
        response = client.get(f"/api/v1/users/{test_user.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["username"] == test_user.username

    def test_get_nonexistent_user(self, client: TestClient):
        """Test getting non-existent user returns 404"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/users/{fake_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]["message"]

    def test_update_user_username(self, client: TestClient, test_user):
        """Test updating user username"""
        update_data = {
            "username": "updatedusername"
        }

        response = client.patch(f"/api/v1/users/{test_user.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "updatedusername"

    def test_update_user_target_language_resets_progress(
        self, client: TestClient, test_user, user_card_states, db_session
    ):
        """Test that changing target language resets and reinitializes user progress"""
        from app.models import UserCardState, UserWordStats

        # Count initial states (from old language)
        initial_states = db_session.query(UserCardState).filter(
            UserCardState.user_id == test_user.id
        ).count()
        initial_word_stats = db_session.query(UserWordStats).filter(
            UserWordStats.user_id == test_user.id
        ).count()
        assert initial_states > 0

        # Change target language to French
        update_data = {"target_language": "fr"}
        response = client.patch(f"/api/v1/users/{test_user.id}", json=update_data)

        assert response.status_code == 200

        # Verify old progress was deleted (should be fewer or equal states)
        final_states = db_session.query(UserCardState).filter(
            UserCardState.user_id == test_user.id
        ).count()
        final_word_stats = db_session.query(UserWordStats).filter(
            UserWordStats.user_id == test_user.id
        ).count()

        # Old word stats should be deleted
        assert final_word_stats == 0

        # Card states should be reset (may have new cards for new language)
        # The important thing is that the old cards were removed
        # New cards should exist for the new language
        assert final_states > 0

    def test_update_user_native_language(self, client: TestClient, test_user):
        """Test updating user native language"""
        update_data = {
            "language_preference": "en"
        }

        response = client.patch(f"/api/v1/users/{test_user.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["language_preference"] == "en"

    def test_delete_user(self, client: TestClient, test_user, user_card_states, db_session):
        """Test deleting user and associated data"""
        from app.models import UserCardState, User

        # Store user ID before any session operations
        user_id = test_user.id

        # Verify user exists
        user = db_session.query(User).filter(User.id == user_id).first()
        assert user is not None

        # Delete user
        response = client.delete(f"/api/v1/users/{user_id}")

        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]

        # Verify user and associated data are deleted
        user = db_session.query(User).filter(User.id == user_id).first()
        assert user is None

        card_states = db_session.query(UserCardState).filter(
            UserCardState.user_id == user_id
        ).count()
        assert card_states == 0

    def test_list_users_multiple(self, client: TestClient, test_user, test_user_french):
        """Test listing multiple users"""
        response = client.get("/api/v1/users/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

        usernames = [user["username"] for user in data]
        assert test_user.username in usernames
        assert test_user_french.username in usernames

    def test_user_initialization_creates_card_states(
        self, client: TestClient, sample_languages, sample_cards, db_session
    ):
        """Test that new user gets initial card states created"""
        from app.models import UserCardState

        user_data = {
            "username": "init_test_user",
            "language_preference": "pt",
            "target_language": "en",
            "word_goal_rank": 100
        }

        response = client.post("/api/v1/users/", json=user_data)
        assert response.status_code == 200

        user_id = response.json()["id"]

        # Check that UserCardState records were created
        card_states = db_session.query(UserCardState).filter(
            UserCardState.user_id == user_id
        ).count()

        # Should have created some card states (not checking exact number as it depends on available cards)
        assert card_states > 0