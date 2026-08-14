from types import SimpleNamespace

from app.services.content_quality_service import validate_cloze_content


def test_validated_cloze_requires_one_gap_and_context():
    valid = validate_cloze_content(
        SimpleNamespace(text="I borrowed this ___ yesterday.", quality_status="approved"),
        SimpleNamespace(text="book"),
    )
    invalid = validate_cloze_content(
        SimpleNamespace(text="The book is here.", quality_status="unreviewed"),
        SimpleNamespace(text="book"),
    )
    assert valid.valid is True
    assert invalid.valid is False
    assert "cloze_must_have_exactly_one_gap" in invalid.issues


def test_unreviewed_content_and_stale_gap_offsets_are_not_deliverable():
    result = validate_cloze_content(
        SimpleNamespace(
            text="I borrowed this ___ yesterday.",
            quality_status="needs_review",
            gap_start=15,
            gap_end=22,
        ),
        SimpleNamespace(text="book"),
    )
    assert result.valid is False
    assert "content_not_reviewed" in result.issues
    assert "gap_offsets_mismatch" in result.issues
