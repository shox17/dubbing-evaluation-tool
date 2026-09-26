"""Tests for interface translations: every text exists in all four languages with the same placeholders."""
import string

import pytest

from src.i18n import MESSAGES, TEXT, UI_LANGUAGES, pick_ui_language, t, translate_message
from src.jobs import STAGES
from src.perso_api import STAGE_LABELS


def placeholders(text: str) -> set:
    """The {names} a text expects from str.format."""
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


@pytest.mark.parametrize("key", sorted(TEXT))
def test_every_text_has_all_languages_and_matching_placeholders(key):
    entry = TEXT[key]
    assert set(entry) == set(UI_LANGUAGES), f"{key} is missing a language"
    assert all(entry[lang].strip() for lang in UI_LANGUAGES)
    assert {lang: placeholders(entry[lang]) for lang in UI_LANGUAGES} == \
        {lang: placeholders(entry["en"]) for lang in UI_LANGUAGES}, f"{key} placeholders differ"


def test_every_stage_and_perso_step_is_translated():
    assert all(f"stage.{key}" in TEXT for key, _ in STAGES)
    for label in STAGE_LABELS.values():
        assert set(MESSAGES[label]) == {"ko", "pt", "es"}


def test_lookup_fills_placeholders_and_passes_unknown_messages_through():
    assert t("cost.estimate", "ko", est="56", have="288") == "예상 비용: **56 크레딧** · 보유 288"
    assert translate_message("Generating the dubbed voice", "es") == "Generando la voz doblada"
    assert translate_message("Uploading 3.2 MB to Perso...", "pt") == "Uploading 3.2 MB to Perso..."
    assert translate_message("Completed", "en") == "Completed"


@pytest.mark.parametrize("locale, expected", [("ko-KR", "ko"), ("pt-BR", "pt"), ("es-MX", "es"), ("en-US", "en"),
                                              ("fr-FR", "en"), (None, "en")])
def test_browser_locale_picks_interface_language(locale, expected):
    assert pick_ui_language(locale) == expected
