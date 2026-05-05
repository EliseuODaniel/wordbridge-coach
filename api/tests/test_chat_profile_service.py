from types import SimpleNamespace

from app.models import ChatConversation, User
from app.services import chat_profile_service

METRICS_FIXTURE = {
    "recent_accuracy": 0.72,
    "retention_score": 0.68,
    "retention_band": "building",
    "review_pressure": "medium",
    "due_review_count": 6,
    "relearn_queue_count": 1,
    "difficult_card_count": 2,
    "mature_ratio": 0.3,
    "recent_hint_ratio": 0.2,
    "average_attempts": 1.2,
    "cards_seen_today": 4,
    "session_new_ratio": 0.25,
    "recommended_pace": "balance",
    "recommended_mode": "spec4",
    "difficulty_signal": "on_target",
    "cefr_readiness": "operating_at_band",
}


class FakeQuery:
    def __init__(self, result=None):
        self.result = result

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return self.result


class FakeDb:
    def __init__(self, user, latest_conversation=None):
        self.user = user
        self.latest_conversation = latest_conversation
        self.added = []

    def add(self, obj):
        self.added.append(obj)

    def query(self, model):
        if model is User:
            return FakeQuery(self.user)
        if model is ChatConversation:
            return FakeQuery(self.latest_conversation)
        raise AssertionError(f"Unexpected model query: {model}")


def test_build_student_profile_combines_user_settings_and_recent_signals():
    user = SimpleNamespace(
        language_preference="pt",
        target_language_obj=SimpleNamespace(code="en"),
        word_goal_rank=1500,
        accuracy_last_20=0.72,
        mode="lingvist",
    )

    profile = chat_profile_service.build_student_profile(
        user,
        recent_signals={
            "strengths": ["Clear meaning"],
            "focus_areas": ["Use past simple"],
            "common_errors": ["go"],
            "topics": ["travel"],
        },
        pedagogical_metrics=METRICS_FIXTURE,
    )

    assert profile["feedback_language"] == "Portuguese"
    assert profile["target_language"] == "English"
    assert profile["scaffolding_level"] == "guided_practice"
    assert profile["coaching_focus"] == "frequency_progression_with_targeted_sentence_building"
    assert profile["strengths"] == ["Clear meaning"]
    assert profile["weaknesses"] == ["Use past simple"]
    assert profile["common_errors"][:2] == ["go", "Use past simple"]
    assert profile["pedagogical_metrics"]["retention_band"] == "building"


def test_build_seed_chat_state_uses_recent_history(monkeypatch):
    user = SimpleNamespace(
        id="user-1",
        language_preference="pt",
        target_language_obj=SimpleNamespace(code="en"),
        word_goal_rank=1000,
        accuracy_last_20=0.88,
        mode="spec4",
    )

    monkeypatch.setattr(
        chat_profile_service,
        "extract_recent_chat_signals",
        lambda db, user_id: {
            "strengths": ["Clear sentence openings"],
            "focus_areas": ["Past tense verbs"],
            "common_errors": ["go"],
            "topics": ["travel"],
        },
    )
    monkeypatch.setattr(
        chat_profile_service,
        "collect_pedagogical_metrics",
        lambda db, user_id, user=None: dict(METRICS_FIXTURE, recommended_mode="chat", recommended_pace="accelerate", difficulty_signal="ready_to_push"),
    )

    student_profile, lesson_frame, session_summary = chat_profile_service.build_seed_chat_state(
        db=object(),
        user=user,
        base_lesson_frame={"topic": "getting_started", "learning_goal": "conversation_start"},
    )

    assert student_profile["feedback_language"] == "Portuguese"
    assert lesson_frame["pedagogical_profile"]["feedback_language"] == "Portuguese"
    assert student_profile["pedagogical_state"]["primary_focus"] == "Past tense verbs"
    assert lesson_frame["primary_focus"] == "Past tense verbs"
    assert "Longitudinal learner profile" in session_summary
    assert "Past tense verbs" in session_summary
    assert lesson_frame["diagnostics"]["recommended_mode"] == "chat"
    assert lesson_frame["diagnostics"]["recommended_pace"] == "accelerate"


def test_refresh_conversation_learning_state_updates_profile_and_summary(monkeypatch):
    user = SimpleNamespace(
        id="user-1",
        language_preference="pt",
        target_language_obj=SimpleNamespace(code="en"),
        word_goal_rank=1000,
        accuracy_last_20=0.58,
        mode="spec4",
    )
    db = FakeDb(user)
    conversation = SimpleNamespace(
        id="conv-1",
        user_id="user-1",
        student_profile_json={
            "strengths": ["Clear meaning"],
            "weaknesses": ["Articles"],
            "common_errors": ["a/an"],
        },
        lesson_frame_json={"topic": "travel", "learning_goal": "past_simple"},
        session_summary="old summary",
    )

    monkeypatch.setattr(
        chat_profile_service,
        "extract_recent_chat_signals",
        lambda db, user_id: {
            "strengths": ["Clear meaning"],
            "focus_areas": ["Past tense verbs"],
            "common_errors": ["go"],
            "topics": ["travel"],
        },
    )
    monkeypatch.setattr(
        chat_profile_service,
        "collect_pedagogical_metrics",
        lambda db, user_id, user=None: dict(METRICS_FIXTURE, review_pressure="high", difficulty_signal="support_needed", recommended_pace="stabilize"),
    )

    student_profile, lesson_frame, session_summary = chat_profile_service.refresh_conversation_learning_state(
        db,
        conversation,
        {
            "strengths": ["Strong main idea"],
            "focus_areas": ["Use past simple after yesterday"],
            "corrections": [{"mistake": "go", "fix": "went"}],
            "reflection_question": "Which word shows the action happened in the past?",
        },
    )

    assert student_profile["scaffolding_level"] == "high_support"
    assert student_profile["strengths"][:2] == ["Strong main idea", "Clear meaning"]
    assert student_profile["weaknesses"][0] == "Use past simple after yesterday"
    assert student_profile["common_errors"][0] == "go"
    assert student_profile["recent_topics"][0] == "travel"
    assert student_profile["pedagogical_state"]["goal_key"] == "past_time_reference"
    assert lesson_frame["primary_focus"] == "Use past simple after yesterday"
    assert lesson_frame["expected_intent"] == "describe_one_past_event_clearly"
    assert "Use past simple after yesterday" in session_summary
    assert conversation.student_profile_json == student_profile
    assert conversation.lesson_frame_json == lesson_frame
    assert conversation.session_summary == session_summary
    assert db.added[0].lesson_frame_json["lesson_stage"] == "stabilize_foundations"
    assert lesson_frame["diagnostics"]["review_pressure"] == "high"
    assert student_profile["pedagogical_metrics"]["difficulty_signal"] == "support_needed"


def test_load_cross_mode_learning_context_prefers_latest_conversation(monkeypatch):
    latest_conversation = SimpleNamespace(
        student_profile_json={
            "cefr_level": "B1",
            "feedback_language": "Portuguese",
            "scaffolding_level": "guided_practice",
            "pedagogical_state": {
                "lesson_stage": "guided_expansion",
                "primary_focus": "Use past simple after yesterday",
                "session_goal": "stabilize past-time verbs in short personal sentences",
                "recommended_topic": "travel",
            },
        },
        lesson_frame_json={
            "learning_goal": "stabilize past-time verbs in short personal sentences",
            "topic": "travel",
        },
    )
    db = FakeDb(user=SimpleNamespace(id="user-1"), latest_conversation=latest_conversation)
    monkeypatch.setattr(
        chat_profile_service,
        "collect_pedagogical_metrics",
        lambda db, user_id, user=None: dict(METRICS_FIXTURE, recommended_mode="chat"),
    )

    context = chat_profile_service.load_cross_mode_learning_context(
        db,
        "user-1",
        mode="lingvist",
    )

    assert context["mode"] == "lingvist"
    assert context["current_focus"] == "Use past simple after yesterday"
    assert context["session_goal"] == "stabilize past-time verbs in short personal sentences"
    assert context["topic"] == "travel"
    assert context["next_mode_hint"] == "chat"
    assert context["retention_signal"] == "building"


def test_derive_pedagogical_metrics_marks_support_needed_when_reviews_pile_up():
    metrics = chat_profile_service.derive_pedagogical_metrics(
        daily_new_limit=10,
        accuracy_last_20=0.52,
        average_retention=0.49,
        due_review_count=24,
        relearn_queue_count=4,
        difficult_card_count=7,
        mature_ratio=0.1,
        hint_ratio=0.5,
        average_attempts=2.1,
        cards_seen_today=6,
        session_new_ratio=0.16,
        preferred_mode="spec4",
    )

    assert metrics["difficulty_signal"] == "support_needed"
    assert metrics["recommended_pace"] == "stabilize"
    assert metrics["recommended_mode"] == "lingvist"
    assert metrics["review_pressure"] == "high"


def test_build_learning_context_includes_adaptive_signals():
    profile = {
        "cefr_level": "A2",
        "scaffolding_level": "guided_practice",
        "feedback_language": "Portuguese",
        "pedagogical_metrics": dict(METRICS_FIXTURE, recommended_mode="lingvist"),
        "pedagogical_state": {
            "lesson_stage": "guided_expansion",
            "primary_focus": "Use past simple after yesterday",
            "session_goal": "stabilize past-time verbs in short personal sentences",
            "recommended_topic": "travel",
        },
    }
    lesson_frame = {
        "learning_goal": "stabilize past-time verbs in short personal sentences",
        "topic": "travel",
    }

    context = chat_profile_service.build_learning_context(profile, lesson_frame, mode="spec4")

    assert context["retention_signal"] == "building"
    assert context["review_pressure"] == "medium"
    assert context["recommended_pace"] == "balance"
    assert context["next_mode_hint"] == "lingvist"


def test_build_pedagogical_analytics_projection_uses_existing_json_state():
    profile = {
        "cefr_level": "A2",
        "scaffolding_level": "guided_practice",
        "feedback_language": "Portuguese",
        "pedagogical_metrics": dict(METRICS_FIXTURE, recommended_mode="lingvist"),
        "pedagogical_state": {
            "lesson_stage": "guided_expansion",
            "primary_focus": "Use past simple after yesterday",
            "session_goal": "stabilize past-time verbs in short personal sentences",
            "recommended_topic": "travel",
        },
    }
    lesson_frame = {
        "learning_goal": "stabilize past-time verbs in short personal sentences",
        "topic": "travel",
    }

    projection = chat_profile_service.build_pedagogical_analytics_projection(
        profile,
        lesson_frame,
        mode="lingvist",
        lesson_history=[
            {"lesson_stage": "stabilize_foundations", "primary_focus": "Article choice"},
            {"lesson_stage": "guided_expansion", "primary_focus": "Use past simple after yesterday"},
        ],
    )

    assert projection["storage_strategy"] == "project_from_conversation_json"
    assert projection["needs_dedicated_store"] is False
    assert projection["context"]["mode"] == "lingvist"
    assert projection["metrics"]["retention_band"] == "building"
    assert projection["metrics"]["recommended_mode"] == "lingvist"
    assert projection["history"]["snapshot_count"] == 2
    assert projection["history"]["recent_focus_areas"] == [
        "Article choice",
        "Use past simple after yesterday",
    ]
    assert projection["history"]["recent_lesson_stages"] == [
        "stabilize_foundations",
        "guided_expansion",
    ]
