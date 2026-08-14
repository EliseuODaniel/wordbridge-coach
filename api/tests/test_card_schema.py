"""Boundary validation for card answer payloads."""

import pytest
from pydantic import ValidationError

from app.schemas.card import AnswerRequest


@pytest.mark.parametrize(
    "payload",
    [
        {"answer": "", "response_time_ms": 100},
        {"answer": "book", "response_time_ms": -1},
        {"answer": "book", "response_time_ms": 3_600_001},
        {"answer": "book", "response_time_ms": 100, "attempts": 0},
        {"answer": "book", "response_time_ms": 100, "hints_used": 21},
    ],
)
def test_answer_request_rejects_unbounded_or_impossible_values(payload):
    with pytest.raises(ValidationError):
        AnswerRequest(**payload)
