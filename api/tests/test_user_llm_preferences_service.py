import uuid

from app.models.user_llm_preferences import UserLLMPreferences
from app.services.user_llm_preferences_service import get_user_llm_preferences


def test_get_user_llm_preferences_resets_stale_profiles(db_session, test_user):
    preferences = UserLLMPreferences(
        user_id=test_user.id,
        chat_model_profile="qwen2.5-7b-instruct",
        teacher_model_profile="qwen2.5-7b-instruct",
    )
    db_session.add(preferences)
    db_session.commit()

    loaded = get_user_llm_preferences(db_session, test_user.id)

    assert loaded.chat_model_profile == "gemma-4-e4b-it"
    assert loaded.teacher_model_profile == "gemma-4-e4b-it"


def test_get_user_llm_preferences_creates_gemma_defaults(db_session, test_user):
    loaded = get_user_llm_preferences(db_session, test_user.id)

    assert loaded.chat_model_profile == "gemma-4-e4b-it"
    assert loaded.teacher_model_profile == "gemma-4-e4b-it"
