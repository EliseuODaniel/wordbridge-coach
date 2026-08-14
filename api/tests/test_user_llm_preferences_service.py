import uuid

from app.models.user_llm_preferences import UserLLMPreferences
from app.services.user_llm_preferences_service import get_user_llm_preferences


def test_get_user_llm_preferences_resets_stale_gemma_profile(db_session, test_user):
    preferences = UserLLMPreferences(
        user_id=test_user.id,
        chat_model_profile="gemma-4-e4b-it",
        teacher_model_profile="gemma-4-e4b-it",
    )
    db_session.add(preferences)
    db_session.commit()

    loaded = get_user_llm_preferences(db_session, test_user.id)

    assert loaded.chat_model_profile == "qwen2.5-7b-instruct"
    assert loaded.teacher_model_profile == "qwen2.5-7b-instruct"


def test_get_user_llm_preferences_creates_qwen_defaults(db_session, test_user):
    loaded = get_user_llm_preferences(db_session, test_user.id)

    assert loaded.chat_model_profile == "qwen2.5-7b-instruct"
    assert loaded.teacher_model_profile == "qwen2.5-7b-instruct"
