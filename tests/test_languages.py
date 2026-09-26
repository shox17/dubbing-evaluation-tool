"""Tests for Perso target languages: the bundled snapshot, lookup by id/name/code, and Whisper codes."""
import pytest

from src.evaluate import whisper_language
from src.languages import FALLBACK_LANGUAGES, parse_languages, resolve_language


def test_snapshot_covers_every_perso_target():
    ids = [l["id"] for l in FALLBACK_LANGUAGES]
    assert len(ids) == 77 and len(set(ids)) == 77
    assert {"ko", "en", "en-GB", "pt-PT", "es-ES", "fil", "cy"} <= set(ids)


@pytest.mark.parametrize("value, expected", [
    ("ko", "ko"), ("Korean", "ko"), ("en", "en"), ("English", "en"), ("English (UK)", "en-GB"),
    ("en-gb", "en-GB"), ("pt", "pt"), ("PT-PT", "pt-PT"), ("Spanish (Spain)", "es-ES"),
])
def test_resolve_by_id_name_or_code(value, expected):
    assert resolve_language(value)["id"] == expected


def test_unknown_language_lists_what_perso_offers():
    with pytest.raises(ValueError, match="Unsupported target language 'Klingon'.*Korean"):
        resolve_language("Klingon")


def test_parse_skips_auto_and_untargetable_rows():
    rows = [{"code": "auto", "name": "Auto Detect", "languageTag": "default", "supportedTtsModels": []},
            {"code": "xx", "name": "Beta", "languageTag": "default", "experiment": True,
             "supportedTtsModels": ["AUDIO_ENGINE_V3"]}]
    assert parse_languages(rows) == [{"id": "xx", "code": "xx", "tag": None, "name": "Beta", "experimental": True}]


@pytest.mark.parametrize("code, expected", [("ko", "ko"), ("fil", "tl"), ("jv", "jw"), ("ceb", None), ("ga", None)])
def test_whisper_language_mapping(code, expected):
    assert whisper_language(code) == expected
