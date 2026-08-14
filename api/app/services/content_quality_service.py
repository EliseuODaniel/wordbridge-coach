"""Deterministic content-boundary validation for cloze items."""

from __future__ import annotations

from dataclasses import dataclass
import re


KNOWN_QUALITY_STATUSES = {"approved", "literary", "unreviewed", "needs_review", "rejected"}
DELIVERABLE_QUALITY_STATUSES = {"approved", "literary"}
_WORD_RE = re.compile(r"[A-Za-zÀ-ÿ']+")


@dataclass(frozen=True)
class ContentValidation:
    valid: bool
    issues: tuple[str, ...]
    quality_status: str


def validate_cloze_content(sentence, word) -> ContentValidation:
    text = str(getattr(sentence, "text", "") or "")
    target = str(getattr(word, "text", "") or "").strip()
    status = str(getattr(sentence, "quality_status", "unreviewed") or "unreviewed")
    issues = []
    if status not in KNOWN_QUALITY_STATUSES:
        issues.append("unknown_quality_status")
    elif status == "rejected":
        issues.append("content_rejected")
    elif status not in DELIVERABLE_QUALITY_STATUSES:
        issues.append("content_not_reviewed")
    if text.count("___") != 1:
        issues.append("cloze_must_have_exactly_one_gap")
    else:
        actual_start = text.index("___")
        stored_start = getattr(sentence, "gap_start", None)
        stored_end = getattr(sentence, "gap_end", None)
        if (
            (stored_start is not None and stored_start != actual_start)
            or (stored_end is not None and stored_end != actual_start + 3)
        ):
            issues.append("gap_offsets_mismatch")
    if not target:
        issues.append("missing_target_word")
    word_count = len(_WORD_RE.findall(text.replace("___", "")))
    if word_count < 3:
        issues.append("context_too_short")
    if word_count > 30:
        issues.append("context_too_long")
    return ContentValidation(not issues, tuple(issues), status)


def cloze_gap_bounds(sentence) -> tuple[int, int]:
    """Derive client-safe gap offsets from the canonical sentence text."""
    text = str(getattr(sentence, "text", "") or "")
    start = text.find("___")
    if start < 0:
        raise ValueError("Cloze sentence has no gap")
    return start, start + 3


def content_context(sentence) -> dict:
    return {
        "cefr_level": getattr(sentence, "cefr_level", None),
        "register": getattr(sentence, "register", "neutral"),
        "domain": getattr(sentence, "domain", None),
        "quality_status": getattr(sentence, "quality_status", "unreviewed"),
        "content_version": getattr(sentence, "content_version", "legacy-v1"),
        "is_contemporary": bool(getattr(sentence, "is_contemporary", False)),
        "license_name": getattr(sentence, "license_name", None),
    }
