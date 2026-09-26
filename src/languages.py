"""Perso target languages: the live list from the Language API, with a bundled snapshot as fallback."""
from typing import Optional

# Snapshot of GET /video-translator/api/v1/languages (2026-09-26), minus "auto". Used when the API
# can't be reached (demo mode, no key, tests). Rows are (code, languageTag, name).
_SNAPSHOT_ROWS = [
    ('en', 'default', 'English (US)'),
    ('pt', 'default', 'Portuguese (Brazil)'),
    ('es', 'default', 'Spanish (Mexico)'),
    ('hi', 'default', 'Hindi'),
    ('fr', 'default', 'French'),
    ('it', 'default', 'Italian'),
    ('es', 'es-ES', 'Spanish (Spain)'),
    ('th', 'default', 'Thai'),
    ('de', 'default', 'German'),
    ('ja', 'default', 'Japanese'),
    ('ru', 'default', 'Russian'),
    ('ar', 'default', 'Arabic'),
    ('hy', 'default', 'Armenian'),
    ('af', 'default', 'Afrikaans'),
    ('as', 'default', 'Assamese'),
    ('az', 'default', 'Azerbaijani'),
    ('be', 'default', 'Belarusian'),
    ('bn', 'default', 'Bengali'),
    ('bs', 'default', 'Bosnian'),
    ('bg', 'default', 'Bulgarian'),
    ('ca', 'default', 'Catalan'),
    ('ceb', 'default', 'Cebuano'),
    ('ny', 'default', 'Chichewa'),
    ('zh', 'default', 'Chinese'),
    ('hr', 'default', 'Croatian'),
    ('cs', 'default', 'Czech'),
    ('da', 'default', 'Danish'),
    ('nl', 'default', 'Dutch'),
    ('en', 'en-GB', 'English (UK)'),
    ('et', 'default', 'Estonian'),
    ('fil', 'default', 'Filipino'),
    ('fi', 'default', 'Finnish'),
    ('gl', 'default', 'Galician'),
    ('ka', 'default', 'Georgian'),
    ('el', 'default', 'Greek'),
    ('gu', 'default', 'Gujarati'),
    ('ha', 'default', 'Hausa'),
    ('he', 'default', 'Hebrew'),
    ('hu', 'default', 'Hungarian'),
    ('is', 'default', 'Icelandic'),
    ('id', 'default', 'Indonesian'),
    ('ga', 'default', 'Irish'),
    ('jv', 'default', 'Javanese'),
    ('kn', 'default', 'Kannada'),
    ('kk', 'default', 'Kazakh'),
    ('ko', 'default', 'Korean'),
    ('ky', 'default', 'Kyrgyz'),
    ('lv', 'default', 'Latvian'),
    ('ln', 'default', 'Lingala'),
    ('lt', 'default', 'Lithuanian'),
    ('lb', 'default', 'Luxembourgish'),
    ('mk', 'default', 'Macedonian'),
    ('ms', 'default', 'Malay'),
    ('ml', 'default', 'Malayalam'),
    ('mr', 'default', 'Marathi'),
    ('ne', 'default', 'Nepali'),
    ('no', 'default', 'Norwegian'),
    ('ps', 'default', 'Pashto'),
    ('fa', 'default', 'Persian'),
    ('pl', 'default', 'Polish'),
    ('pt', 'pt-PT', 'Portuguese (Portugal)'),
    ('pa', 'default', 'Punjabi'),
    ('ro', 'default', 'Romanian'),
    ('sr', 'default', 'Serbian'),
    ('sd', 'default', 'Sindhi'),
    ('sk', 'default', 'Slovak'),
    ('sl', 'default', 'Slovenian'),
    ('so', 'default', 'Somali'),
    ('sw', 'default', 'Swahili'),
    ('sv', 'default', 'Swedish'),
    ('ta', 'default', 'Tamil'),
    ('te', 'default', 'Telugu'),
    ('tr', 'default', 'Turkish'),
    ('uk', 'default', 'Ukrainian'),
    ('ur', 'default', 'Urdu'),
    ('vi', 'default', 'Vietnamese'),
    ('cy', 'default', 'Welsh'),
]


def _entry(code: str, tag: Optional[str], name: str, experimental: bool = False) -> dict:
    """One selectable language. `id` is the regional tag (en-GB) or, for a code's default row, the code."""
    tag = None if not tag or tag == "default" else tag
    return {"id": tag or code, "code": code, "tag": tag, "name": name, "experimental": experimental}


FALLBACK_LANGUAGES = [_entry(*row) for row in _SNAPSHOT_ROWS]


def parse_languages(rows: list[dict]) -> list[dict]:
    """Turns Language API rows into target entries; skips "auto" and rows that can't be dubbed into."""
    out = []
    for r in rows:
        if r.get("code") in (None, "", "auto") or not r.get("supportedTtsModels"):
            continue
        out.append(_entry(r["code"], r.get("languageTag"), r.get("name") or r["code"], bool(r.get("experiment"))))
    return out


def _key(lang: dict, key: str) -> str:
    """The value to match on; base_name is the name without its region ("English" for "English (US)")."""
    if key == "base_name":
        return lang["name"].split(" (")[0].lower()
    return (lang[key] or "").lower()


def resolve_language(value: str, languages: Optional[list[dict]] = None) -> dict:
    """Finds a language by id (ko, en-GB), code, or name (Korean). Raises ValueError if Perso doesn't offer it."""
    languages = languages or FALLBACK_LANGUAGES
    v = (value or "").strip().lower()
    for key in ("id", "name", "code", "base_name"):
        hit = next((l for l in languages if not (key in ("code", "base_name") and l["tag"])
                    and _key(l, key) == v), None)
        if hit:
            return hit
    raise ValueError(f"Unsupported target language {value!r}. Perso dubs into: "
                     + ", ".join(l["name"] for l in sorted(languages, key=lambda l: l["name"])) + ".")
