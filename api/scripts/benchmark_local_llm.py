#!/usr/bin/env python3
"""Run a small, application-shaped latency and contract benchmark against llama.cpp."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from typing import Any

import httpx
from pydantic import BaseModel

from app.llm.pedagogical_tasks import (
    AutocompletePayload,
    DraftEvaluationPayload,
    TeacherAnalysisPayload,
    build_autocomplete_messages,
    build_llamacpp_response_format,
    build_micro_eval_messages,
    build_teacher_analysis_messages,
)
from app.services.chat_text_service import build_chat_generation_config, build_chat_system_prompt


PROFILE = {
    "target_language": "English",
    "feedback_language": "Portuguese",
    "cefr_level": "A2",
    "scaffolding_level": "guided_practice",
    "strengths": ["basic vocabulary"],
    "weaknesses": ["past tense"],
}
LESSON = {
    "topic": "weekend activities",
    "learning_goal": "describe past experiences",
    "cefr_target": "A2",
}
CONTEXT = "Tutor: What did you do last weekend?"
LEARNER_TEXT = "Yesterday I go in the museum with my sister."


@dataclass
class BenchmarkResult:
    case: str
    elapsed_seconds: float
    tokens_per_second: float
    contract_valid: bool
    quality_checks: dict[str, bool]
    output: Any
    error: str = ""


def _contains_portuguese(value: Any) -> bool:
    text = json.dumps(value, ensure_ascii=False).lower()
    markers = (
        " você",
        " verbo",
        " frase",
        " passado",
        " preposição",
        " correção",
        " tente",
        " precisa",
    )
    return any(marker in text for marker in markers)


def _post_case(
    client: httpx.Client,
    *,
    base_url: str,
    model: str,
    name: str,
    messages: list[dict[str, str]],
    config: dict[str, Any],
    response_model: type[BaseModel] | None = None,
) -> BenchmarkResult:
    payload: dict[str, Any] = {"model": model, "messages": messages, **config}
    if response_model is not None:
        payload["response_format"] = build_llamacpp_response_format(response_model)

    started = time.perf_counter()
    response = client.post(f"{base_url}/chat/completions", json=payload)
    elapsed = time.perf_counter() - started
    response.raise_for_status()
    response_data = response.json()
    raw_output = response_data["choices"][0]["message"]["content"]
    timings = response_data.get("timings", {})

    parsed: Any = raw_output
    contract_valid = True
    error = ""
    if response_model is not None:
        try:
            parsed = response_model.model_validate_json(raw_output).model_dump()
        except Exception as exc:  # benchmark must report malformed provider output
            contract_valid = False
            error = str(exc)

    checks: dict[str, bool] = {}
    if name == "chat":
        checks = {
            "asks_follow_up": "?" in str(parsed),
            "brief_reply": len(str(parsed).split()) <= 80,
            "no_meta_commentary": not any(
                marker in str(parsed).lower() for marker in ("analysis:", "system:", "teacher:")
            ),
        }
    elif name == "autocomplete" and contract_valid:
        suggestion = str(parsed["ghost_suggestion"])
        checks = {"one_to_six_words": 1 <= len(suggestion.split()) <= 6}
    elif name == "micro_eval" and contract_valid:
        issues = parsed["top_issues"]
        all_highlights_are_exact = all(
            not issue["highlight_text"] or issue["highlight_text"] in LEARNER_TEXT
            for issue in issues
        )
        feedback_fields = {
            "issues": [issue["explanation"] for issue in issues],
            "tip": parsed["micro_tip"],
            "self_check": parsed["self_check_prompt"],
        }
        output_text = json.dumps(parsed, ensure_ascii=False).lower()
        go_issue_text = json.dumps(
            [issue for issue in issues if issue["highlight_text"] == "go"],
            ensure_ascii=False,
        ).lower()
        checks = {
            "exact_highlights": all_highlights_are_exact,
            "feedback_in_portuguese": _contains_portuguese(feedback_fields),
            "detects_go": any(issue["highlight_text"] == "go" for issue in issues),
            "no_goed_advice": "goed" not in output_text,
            "no_regular_ed_rule_for_go": "-ed" not in go_issue_text and not (
                ("regular verb" in output_text or "verbos regulares" in output_text)
                and "-ed" in output_text
            ),
        }
    elif name == "teacher" and contract_valid:
        checks = {
            "feedback_in_portuguese": _contains_portuguese(
                {
                    "summary": parsed["teacher_summary"],
                    "why": [item["why"] for item in parsed["corrections"]],
                    "reflection": parsed["reflection_question"],
                }
            ),
            "bounded_feedback": all(
                len(parsed[field]) <= 3
                for field in ("corrections", "strengths", "focus_areas", "next_practice")
            ),
        }

    return BenchmarkResult(
        case=name,
        elapsed_seconds=round(elapsed, 3),
        tokens_per_second=round(float(timings.get("predicted_per_second") or 0), 2),
        contract_valid=contract_valid,
        quality_checks=checks,
        output=parsed,
        error=error,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8080/v1")
    parser.add_argument("--model", default="/models/model.gguf")
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args()

    cases = [
        {
            "name": "chat",
            "messages": [
                {"role": "system", "content": build_chat_system_prompt(LESSON, PROFILE)},
                {"role": "user", "content": LEARNER_TEXT},
            ],
            "config": {**build_chat_generation_config(), "stream": False},
        },
        {
            "name": "autocomplete",
            "messages": build_autocomplete_messages(
                context=CONTEXT,
                lesson_frame=LESSON,
                draft="Yesterday I went to",
                student_profile=PROFILE,
            ),
            "config": {"temperature": 0.1, "max_tokens": 120, "stream": False},
            "response_model": AutocompletePayload,
        },
        {
            "name": "micro_eval",
            "messages": build_micro_eval_messages(
                context=CONTEXT,
                lesson_frame=LESSON,
                draft=LEARNER_TEXT,
                student_profile=PROFILE,
            ),
            "config": {"temperature": 0.1, "max_tokens": 700, "stream": False},
            "response_model": DraftEvaluationPayload,
        },
        {
            "name": "teacher",
            "messages": build_teacher_analysis_messages(
                user_message=LEARNER_TEXT,
                context=CONTEXT,
                lesson_frame=LESSON,
                student_profile=PROFILE,
            ),
            "config": {"temperature": 0.2, "max_tokens": 900, "stream": False},
            "response_model": TeacherAnalysisPayload,
        },
    ]

    with httpx.Client(timeout=args.timeout) as client:
        results = [
            _post_case(
                client,
                base_url=args.base_url.rstrip("/"),
                model=args.model,
                **case,
            )
            for case in cases
        ]

    for result in results:
        summary = {
            "case": result.case,
            "elapsed_seconds": result.elapsed_seconds,
            "tokens_per_second": result.tokens_per_second,
            "contract_valid": result.contract_valid,
            "quality_checks": result.quality_checks,
        }
        print(json.dumps(summary if args.summary_only else asdict(result), ensure_ascii=False))

    return 0 if all(
        result.contract_valid and all(result.quality_checks.values()) for result in results
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
