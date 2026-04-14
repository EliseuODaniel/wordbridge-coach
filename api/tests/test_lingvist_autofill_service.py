"""Tests for on-demand Lingvist translation autofill helpers."""

from types import SimpleNamespace

from app.services import lingvist_autofill_service


class FakeDb:
    def __init__(self):
        self.flush_calls = 0

    def flush(self):
        self.flush_calls += 1


def test_load_tsv_translations_parses_and_caches_entries(tmp_path, monkeypatch):
    tsv_file = tmp_path / "translations.tsv"
    tsv_file.write_text(
        "# comment\nbook\tlivro\n\ninvalid-line\nhouse\tcasa\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(lingvist_autofill_service, "_tsv_translations_cache", None)

    loaded = lingvist_autofill_service.load_tsv_translations(str(tsv_file))
    cached = lingvist_autofill_service.load_tsv_translations(str(tsv_file))

    assert loaded == {"book": "livro", "house": "casa"}
    assert cached is loaded


def test_autofill_translations_prefers_tsv_for_word(monkeypatch):
    fake_db = FakeDb()
    word = SimpleNamespace(lemma="Book", text="book", features=None)
    sentence = SimpleNamespace(text="The ___ is here.", translation=None)
    card = SimpleNamespace()

    class FakeTranslationService:
        def is_enabled(self):
            return False

        def translate(self, text):
            raise AssertionError("MT should not be called when TSV has the word")

        def get_provider(self):
            return "fake"

    monkeypatch.setattr(
        lingvist_autofill_service,
        "load_tsv_translations",
        lambda tsv_path="/app/data/en_pt_word_translations_sample.tsv": {"book": "livro"},
    )
    monkeypatch.setattr(
        lingvist_autofill_service,
        "get_translation_service",
        lambda: FakeTranslationService(),
    )

    lingvist_autofill_service.autofill_translations(fake_db, word, sentence, card)

    assert word.features == {"pt_translation": "livro"}
    assert sentence.translation is None
    assert fake_db.flush_calls == 1


def test_autofill_translations_uses_mt_for_word_and_sentence_when_missing(monkeypatch):
    fake_db = FakeDb()
    word = SimpleNamespace(lemma="house", text="house", features={})
    sentence = SimpleNamespace(text="The ___ is blue.", translation="")
    card = SimpleNamespace()

    class FakeTranslationService:
        def is_enabled(self):
            return True

        def translate(self, text):
            return {
                "house": "casa",
                "The house is blue.": "A casa e azul.",
            }.get(text)

        def get_provider(self):
            return "fake"

    monkeypatch.setattr(
        lingvist_autofill_service,
        "load_tsv_translations",
        lambda tsv_path="/app/data/en_pt_word_translations_sample.tsv": {},
    )
    monkeypatch.setattr(
        lingvist_autofill_service,
        "get_translation_service",
        lambda: FakeTranslationService(),
    )

    lingvist_autofill_service.autofill_translations(fake_db, word, sentence, card)

    assert word.features["pt_translation"] == "casa"
    assert sentence.translation == "A casa e azul."
    assert fake_db.flush_calls == 2
