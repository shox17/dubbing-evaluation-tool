"""Translation check: an LLM compares what the original says with what the dub says.

A share link carries no script, so this is the only measure of meaning. It works on Whisper transcripts of both
tracks, so a misheard word can look like a translation error; the report says so.

Provider: Gemini when GEMINI_API_KEY (or GOOGLE_API_KEY) is set, otherwise Claude when ANTHROPIC_API_KEY (or an
`ant auth login` profile) is available. Without either, or on any failure, it returns a not-measured result with
the reason instead of failing the run.
"""
import os
import json
import time
import logging
from pathlib import Path
from typing import Callable, Optional

import requests

log = logging.getLogger(__name__)

GEMINI_API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
# Tried in order: each one is retried on overload (503) or rate limits (429), then the next model is used. Google's
# "high demand" errors are usually per model, so a longer chain keeps the check working during demand spikes.
GEMINI_MODELS = [os.getenv("GEMINI_MODEL", "gemini-3.5-flash"), "gemini-flash-latest", "gemini-3.8-flash",
                 "gemini-3.1-flash-lite"]
GEMINI_THINKING = os.getenv("GEMINI_THINKING", "low")      # low ≈ 3 s per review, high ≈ 40 s
CLAUDE_MODEL = os.getenv("CLAUDE_JUDGE_MODEL", "claude-opus-5-5")
MAX_ISSUES = 12
RETRYABLE = (429, 500, 502, 503, 504)

SYSTEM_PROMPT = """You review AI-dubbed videos for a quality-assurance report.
You get two timestamped speech-recognition transcripts: the ORIGINAL video and its DUB in another language.
Judge whether the dub says what the original says: same meaning, nothing important missing, nothing invented,
names and numbers kept. Accept natural, idiomatic wording; a different but faithful phrasing is not an error.
Both transcripts come from automatic speech recognition, so small misspellings or misheard proper nouns may be
recognition errors rather than dubbing errors: mention them only when they change the meaning, and say when an
issue could be a recognition error. Quote the transcripts exactly (quotes stay in their own language).
Write the summary and every explanation for a non-expert reader, in plain language, one or two sentences each,
in four versions: English (en), Korean (ko), Brazilian Portuguese (pt) and Spanish (es)."""

LANGS = ("en", "ko", "pt", "es")
MULTILINGUAL = {"type": "object", "properties": {lang: {"type": "string"} for lang in LANGS},
                "required": list(LANGS), "additionalProperties": False}

RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "meaning_score": {"type": "integer", "enum": [1, 2, 3, 4, 5],
                          "description": "5 = same meaning throughout, 1 = mostly wrong or unrelated"},
        "summary": {**MULTILINGUAL, "description": "One or two plain sentences on the overall translation"},
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["missing", "added", "mistranslation", "name_or_number"]},
                    "severity": {"type": "string", "enum": ["minor", "major"]},
                    "start_sec": {"type": "number", "description": "Start time in the original, in seconds"},
                    "original": {"type": "string", "description": "Exact quote from the original, or empty"},
                    "dubbed": {"type": "string", "description": "Exact quote from the dub, or empty"},
                    "explanation": {**MULTILINGUAL, "description": "What is wrong and why it matters"},
                    "may_be_recognition_error": {"type": "boolean"},
                },
                "required": ["type", "severity", "start_sec", "original", "dubbed", "explanation",
                             "may_be_recognition_error"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["meaning_score", "summary", "issues"],
    "additionalProperties": False,
}


def gemini_key() -> Optional[str]:
    """The Gemini API key from the environment, or None."""
    return (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip() or None


def claude_available() -> bool:
    """True when the anthropic package is installed and Claude credentials look configured."""
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    profile_dir = Path.home() / ".config" / "anthropic"
    return bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN") or profile_dir.is_dir())


def judge_provider() -> Optional[str]:
    """Which model provider the translation check will use: "gemini", "claude", or None."""
    return "gemini" if gemini_key() else "claude" if claude_available() else None


def judge_configured() -> bool:
    """True when some provider is configured, so the translation check will run."""
    return judge_provider() is not None


def judge_fingerprint() -> str:
    """What decides the judge's answer besides the transcripts: provider, models, thinking, prompt and schema.
    Changing any of them invalidates cached reviews."""
    return json.dumps([judge_provider(), GEMINI_MODELS, GEMINI_THINKING, CLAUDE_MODEL, SYSTEM_PROMPT, RESULT_SCHEMA],
                      sort_keys=True)


def not_measured(key: str, **params) -> dict:
    """The result when the translation couldn't be checked: a translatable reason key, plus the English text."""
    from src.i18n import t
    params = {k: str(v) for k, v in params.items()}
    return {"measured": False, "reason": t(key, "en", **params), "reason_key": key, "reason_params": params,
            "model": None, "meaning_score": None, "summary": None, "issues": []}


def _timestamped(segments: list[dict]) -> str:
    """Transcript lines like '[12.3-15.0] text' for the prompt."""
    return "\n".join(f"[{s['start']:.1f}-{s['end']:.1f}] {s['text']}" for s in segments if s.get("text")) or "(no speech)"


def build_prompt(original_segments: list[dict], dubbed_segments: list[dict], source_lang: str, target_lang: str) -> str:
    """The user message: both transcripts, labelled with their languages."""
    return (f"ORIGINAL (language: {source_lang}):\n{_timestamped(original_segments)}\n\n"
            f"DUB (language: {target_lang}):\n{_timestamped(dubbed_segments)}\n\n"
            "Rate how faithfully the dub carries the original's meaning and list every issue.")


def judge_translation(original_segments: list[dict], dubbed_segments: list[dict], source_lang: str,
                      target_lang: str, client=None, session=None,
                      sleep: Callable[[float], None] = time.sleep) -> dict:
    """Rates meaning (1-5) and lists missing, added, mistranslated and name/number issues, with Gemini or Claude.

    client: an Anthropic client (forces Claude); session: a requests-like session (forces Gemini). Both are for tests.
    """
    if not any(s.get("text") for s in original_segments) or not any(s.get("text") for s in dubbed_segments):
        return not_measured("r.judge.no_speech")
    prompt = build_prompt(original_segments, dubbed_segments, source_lang, target_lang)
    if client is not None:
        return _judge_claude(prompt, client)
    provider = "gemini" if session is not None else judge_provider()
    if provider == "gemini":
        return _judge_gemini(prompt, session or requests.Session(), sleep)
    if provider == "claude":
        return _judge_claude(prompt, None)
    return not_measured("r.judge.no_key")


def _result(data: dict, model: str, provider: str) -> dict:
    """A measured result from the model's JSON, or not measured if the JSON is incomplete."""
    try:
        issues = sorted(data.get("issues", []), key=lambda i: (i["severity"] != "major", i["start_sec"]))[:MAX_ISSUES]
        for i in issues:
            i["explanation"] = _as_langs(i["explanation"])
        return {"measured": True, "reason": "", "reason_key": None, "reason_params": {}, "model": model,
                "meaning_score": int(data["meaning_score"]), "summary": _as_langs(data["summary"]), "issues": issues}
    except (KeyError, TypeError, ValueError):
        return not_measured("r.judge.unreadable", model=provider)


def _as_langs(value) -> dict:
    """A {lang: text} dict from the model's multilingual field (or a plain string, used for every language)."""
    if isinstance(value, dict):
        return {lang: str(value.get(lang) or value.get("en") or "") for lang in LANGS}
    return {lang: str(value) for lang in LANGS}


def _judge_gemini(prompt: str, session, sleep: Callable[[float], None]) -> dict:
    """One Gemini review with structured JSON output; retries overload and rate limits, then tries fallbacks."""
    key = gemini_key() or ""
    body = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "responseJsonSchema": RESULT_SCHEMA,
                             "temperature": 0, "thinkingConfig": {"thinkingLevel": GEMINI_THINKING}},
    }
    busy = False
    for model in dict.fromkeys(GEMINI_MODELS):
        for attempt in range(2):
            try:
                resp = session.post(GEMINI_API.format(model=model), headers={"x-goog-api-key": key},
                                    json=body, timeout=120)
            except requests.RequestException as e:
                log.warning("Gemini request failed: %s", e.__class__.__name__)
                busy = True
                sleep(2 ** attempt)
                continue
            if resp.status_code in RETRYABLE:
                busy = True
                sleep(2 * (attempt + 1))
                continue
            if resp.status_code == 404:
                break                                        # model not available to this key: try the next one
            if resp.status_code in (400, 401, 403):
                try:
                    msg = resp.json().get("error", {}).get("message", "")
                except ValueError:
                    msg = ""
                if resp.status_code != 400 or "key" in msg.lower():
                    return not_measured("r.judge.bad_key", model="Gemini")
                log.warning("Gemini rejected the request: %s", msg[:200])
                return not_measured("r.judge.error", model="Gemini")
            if resp.status_code != 200:
                return not_measured("r.judge.error", model="Gemini")
            data = resp.json()
            candidate = (data.get("candidates") or [{}])[0]
            finish = candidate.get("finishReason")
            if finish in ("SAFETY", "PROHIBITED_CONTENT", "BLOCKLIST") or not candidate.get("content"):
                return not_measured("r.judge.declined", model="Gemini")
            if finish == "MAX_TOKENS":
                return not_measured("r.judge.cut_off", model="Gemini")
            text = "".join(p.get("text", "") for p in candidate["content"].get("parts", []) if not p.get("thought"))
            try:
                return _result(json.loads(text), data.get("modelVersion") or model, "Gemini")
            except json.JSONDecodeError:
                return not_measured("r.judge.unreadable", model="Gemini")
    if busy:
        return not_measured("r.judge.busy", model="Gemini")
    return not_measured("r.judge.error", model="Gemini")


def _judge_claude(prompt: str, client) -> dict:
    """One Claude review with structured JSON output and server-side refusal fallback."""
    if client is None:
        try:
            import anthropic
        except ImportError:
            return not_measured("r.judge.no_key")
        client = anthropic.Anthropic()
    try:
        response = client.beta.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": "medium", "format": {"type": "json_schema", "schema": RESULT_SCHEMA}},
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as e:  # network, auth or API errors must not sink the whole evaluation
        name = e.__class__.__name__
        # No credentials at all is a TypeError from the SDK; a rejected key is a 401/403.
        if isinstance(e, TypeError) or getattr(e, "status_code", None) in (401, 403):
            log.info("Translation judge has no usable Claude credentials (%s)", name)
            return not_measured("r.judge.bad_key", model="Claude")
        log.warning("Translation judge failed: %s", name)
        return not_measured("r.judge.unreachable", model="Claude")

    if response.stop_reason == "refusal":
        return not_measured("r.judge.declined", model="Claude")
    if response.stop_reason == "max_tokens":
        return not_measured("r.judge.cut_off", model="Claude")
    text = next((b.text for b in response.content if b.type == "text"), "")
    try:
        return _result(json.loads(text), getattr(response, "model", CLAUDE_MODEL), "Claude")
    except json.JSONDecodeError:
        return not_measured("r.judge.unreadable", model="Claude")


def count_issues(result: dict, kinds: tuple[str, ...], severity: Optional[str] = None) -> Optional[int]:
    """How many issues of the given types (and severity) the judge found; None if it didn't run."""
    if not result.get("measured"):
        return None
    return sum(1 for i in result["issues"] if i["type"] in kinds and (severity is None or i["severity"] == severity))
