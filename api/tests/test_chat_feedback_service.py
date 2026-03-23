import asyncio
from types import SimpleNamespace

from app.services import chat_feedback_service
from app.services.chat_feedback_service import (
    build_draft_feedback,
    evaluate_draft_feedback,
    freeze_user_message_feedback,
    merge_issues,
)


def test_merge_issues_deduplicates_overlapping_heuristic_items():
    lt_issues = [
        {
            "category": "grammar",
            "title": "Verb tense",
            "highlight_spans": [{"start": 2, "end": 6}],
            "suggestions": ["went"],
        }
    ]
    heuristic_issues = [
        {
            "category": "grammar",
            "title": "Verb tense",
            "highlight_spans": [{"start": 2, "end": 6}],
            "suggestions": ["gone"],
        },
        {
            "category": "style",
            "title": "Word choice",
            "highlight_spans": [{"start": 10, "end": 14}],
            "suggestions": ["nice"],
        },
    ]

    merged = merge_issues(lt_issues, heuristic_issues)

    assert len(merged) == 2
    assert merged[0]["suggestions"] == ["went"]
    assert merged[1]["category"] == "style"


def test_build_draft_feedback_generates_micro_tip_when_no_issues():
    payload = build_draft_feedback(
        conversation_id="conv-1",
        eval_result={
            "spelling_score": 95,
            "grammar_score": 90,
            "lesson_alignment_score": 88,
            "naturalness_score": 84,
            "top_issues": [],
            "suggested_next_words": [],
            "topic": "travel",
            "intent": "future_plan",
        },
        now_ms=100,
        draft="I travel tomorrow",
        lesson_frame={"topic": "travel"},
    )

    assert payload["type"] == "draft_feedback"
    assert payload["micro_tip"] is not None
    assert payload["topic"] == "travel"


def test_evaluate_draft_feedback_merges_language_tool_issues(monkeypatch):
    conversation = SimpleNamespace(
        id="conv-1",
        session_summary="summary",
        lesson_frame_json={"topic": "travel"},
        student_profile_json={"cefr_level": "A2"},
    )

    class FakeProvider:
        async def micro_eval(self, context, lesson_frame, draft, student_profile):
            assert draft == "I go yesterday"
            return {
                "spelling_score": 95,
                "grammar_score": 70,
                "lesson_alignment_score": 80,
                "naturalness_score": 75,
                "top_issues": [
                    {
                        "category": "grammar",
                        "title": "Verb tense",
                        "explanation": "Use past simple.",
                        "highlight_spans": [{"start": 2, "end": 4}],
                        "suggestions": ["went"],
                    }
                ],
                "suggested_next_words": [],
                "topic": "travel",
                "intent": "past_experience",
            }

    async def fake_get_grammar_issues(draft_text, grammar_provider, grammar_url):
        assert grammar_provider == "languagetool"
        assert grammar_url == "http://lt"
        return [
            {
                "category": "grammar",
                "title": "Verb tense",
                "explanation": "Use past simple.",
                "highlight_spans": [{"start": 2, "end": 4}],
                "suggestions": ["went"],
            },
            {
                "category": "style",
                "title": "Word choice",
                "explanation": "Try a more specific word.",
                "highlight_spans": [{"start": 5, "end": 14}],
                "suggestions": ["to school"],
            },
        ]

    monkeypatch.setattr(chat_feedback_service, "get_grammar_issues", fake_get_grammar_issues)

    payload = asyncio.run(
        evaluate_draft_feedback(
            conversation=conversation,
            draft_text="I go yesterday",
            now_ms=123,
            llm_provider=FakeProvider(),
            grammar_provider="languagetool",
            grammar_url="http://lt",
            include_grammar_check=True,
        )
    )

    assert payload["type"] == "draft_feedback"
    assert len(payload["issues"]) == 2
    assert payload["issues"][0]["suggestions"] == ["went"]
    assert payload["issues"][1]["category"] == "style"


def test_freeze_user_message_feedback_sends_snapshot_payload():
    class FakeChatProvider:
        async def micro_eval(self, context, lesson_frame, draft, student_profile):
            return {
                "spelling_score": 95,
                "grammar_score": 90,
                "lesson_alignment_score": 88,
                "naturalness_score": 85,
                "top_issues": [],
                "suggested_next_words": ["to"],
                "topic": "travel",
                "intent": "future_plan",
            }

    class FakeWebSocket:
        def __init__(self):
            self.payloads = []

        async def send_json(self, payload):
            self.payloads.append(payload)

    conversation = SimpleNamespace(
        id="conv-1",
        session_summary="session-summary",
        lesson_frame_json={"topic": "travel"},
        student_profile_json={"cefr_level": "A2"},
    )
    websocket = FakeWebSocket()

    payload = asyncio.run(
        freeze_user_message_feedback(
            websocket=websocket,
            conversation=conversation,
            content="I travel tomorrow",
            chat_provider=FakeChatProvider(),
        )
    )

    assert payload["type"] == "draft_feedback"
    assert payload["draft"] == "I travel tomorrow"
    assert websocket.payloads == [payload]
