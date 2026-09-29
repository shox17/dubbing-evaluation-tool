"""Tests for the translation check with Gemini and Claude, using fake sessions and clients (never the real APIs)."""
import json
from types import SimpleNamespace

import pytest

from src import translation_judge
from src.translation_judge import build_prompt, count_issues, judge_provider, judge_translation

ORIG = [{"start": 0.0, "end": 2.0, "text": "Hi, I'm John from Uzbekistan."}]
DUB = [{"start": 0.1, "end": 2.2, "text": "안녕하세요, 우즈베키스탄에서 온 존입니다."}]


class FakeClient:
    """Records the request and returns a canned response, like client.beta.messages.create would."""

    def __init__(self, payload=None, stop_reason="end_turn", error=None):
        self.payload, self.stop_reason, self.error, self.request = payload, stop_reason, error, None
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self.create))

    def create(self, **kw):
        self.request = kw
        if self.error:
            raise self.error
        text = self.payload if isinstance(self.payload, str) else json.dumps(self.payload)
        return SimpleNamespace(stop_reason=self.stop_reason, model="claude-opus-5-5",
                               content=[SimpleNamespace(type="text", text=text)])


GOOD = {"meaning_score": 5, "summary": "Faithful.", "issues": [
    {"type": "name_or_number", "severity": "minor", "start_sec": 1.0, "original": "Uzbekistan", "dubbed": "우즈베키스탄",
     "explanation": "Fine.", "may_be_recognition_error": False},
    {"type": "missing", "severity": "major", "start_sec": 0.5, "original": "Hi", "dubbed": "",
     "explanation": "Greeting dropped.", "may_be_recognition_error": False}]}


def test_judge_parses_structured_result_and_sorts_major_first():
    client = FakeClient(GOOD)
    r = judge_translation(ORIG, DUB, "en", "ko", client=client)
    assert r["measured"] and r["meaning_score"] == 5 and r["model"] == "claude-opus-5-5"
    assert r["issues"][0]["severity"] == "major"
    assert count_issues(r, ("missing", "added")) == 1 and count_issues(r, ("name_or_number",), "major") == 0
    req = client.request
    assert req["model"] == "claude-opus-5-5" and req["fallbacks"] == "default"
    assert req["output_config"]["format"]["type"] == "json_schema"
    assert "[0.0-2.0] Hi, I'm John" in req["messages"][0]["content"]


def test_prompt_labels_languages():
    p = build_prompt(ORIG, DUB, "en", "ko")
    assert "ORIGINAL (language: en)" in p and "DUB (language: ko)" in p


def test_missing_credentials_becomes_not_measured():
    r = judge_translation(ORIG, DUB, "en", "ko", client=FakeClient(error=TypeError("Could not resolve authentication method")))
    assert not r["measured"] and "rejected the API key" in r["reason"] and r["reason_key"] == "r.judge.bad_key"
    assert count_issues(r, ("missing",)) is None


def test_network_error_refusal_and_bad_json_never_raise():
    assert "couldn't be reached" in judge_translation(ORIG, DUB, "en", "ko", client=FakeClient(error=ConnectionError()))["reason"]
    assert "declined" in judge_translation(ORIG, DUB, "en", "ko", client=FakeClient(GOOD, stop_reason="refusal"))["reason"]
    assert "cut off" in judge_translation(ORIG, DUB, "en", "ko", client=FakeClient(GOOD, stop_reason="max_tokens"))["reason"]
    assert "couldn't be read" in judge_translation(ORIG, DUB, "en", "ko", client=FakeClient("not json"))["reason"]


def test_no_speech_skips_the_call():
    client = FakeClient(GOOD)
    r = judge_translation(ORIG, [], "en", "ko", client=client)
    assert not r["measured"] and client.request is None


# ---------------- Gemini ----------------
class FakeGemini:
    """A requests-like session answering generateContent with scripted (status, body) replies, in order."""

    def __init__(self, *replies):
        self.replies, self.calls = list(replies), []

    def post(self, url, headers=None, json=None, timeout=None):
        self.calls.append({"url": url, "headers": headers, "json": json})
        status, body = self.replies.pop(0) if self.replies else (503, {"error": {"message": "busy"}})
        return SimpleNamespace(status_code=status, json=lambda: body)


def gemini_ok(payload, model="gemini-3.5-flash"):
    """A successful generateContent response carrying payload as JSON text (with a thought part to skip)."""
    return 200, {"modelVersion": model, "candidates": [{"finishReason": "STOP", "content": {"parts": [
        {"text": "thinking...", "thought": True}, {"text": json.dumps(payload)}]}}]}


@pytest.fixture
def gemini_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")


def test_provider_prefers_gemini(monkeypatch):
    assert judge_provider() in (None, "claude")
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    assert judge_provider() == "gemini"


def test_gemini_structured_request_and_result(gemini_key):
    s = FakeGemini(gemini_ok(GOOD))
    r = judge_translation(ORIG, DUB, "en", "ko", session=s, sleep=lambda x: None)
    assert r["measured"] and r["meaning_score"] == 5 and r["model"] == "gemini-3.5-flash"
    call = s.calls[0]
    assert call["url"].endswith("/models/gemini-3.5-flash:generateContent")
    assert call["headers"] == {"x-goog-api-key": "test-key"}          # key in a header, never in the URL
    cfg = call["json"]["generationConfig"]
    assert cfg["responseMimeType"] == "application/json" and cfg["responseJsonSchema"]["required"]
    assert "[0.0-2.0] Hi, I'm John" in call["json"]["contents"][0]["parts"][0]["text"]


def test_gemini_retries_overload_then_falls_back_to_next_model(gemini_key):
    busy = (503, {"error": {"message": "high demand"}})
    s = FakeGemini(busy, busy, gemini_ok(GOOD, "gemini-flash-latest"))
    r = judge_translation(ORIG, DUB, "en", "ko", session=s, sleep=lambda x: None)
    assert r["measured"] and r["model"] == "gemini-flash-latest"
    assert [c["url"].split("/models/")[1].split(":")[0] for c in s.calls] == \
        ["gemini-3.5-flash"] * 2 + ["gemini-flash-latest"]


def test_gemini_overloaded_everywhere_is_not_measured(gemini_key):
    r = judge_translation(ORIG, DUB, "en", "ko", session=FakeGemini(), sleep=lambda x: None)
    assert not r["measured"] and "busy right now" in r["reason"]


@pytest.mark.parametrize("reply, reason", [
    ((400, {"error": {"message": "API key not valid. Please pass a valid API key."}}), "rejected the API key"),
    ((403, {"error": {"message": "Permission denied"}}), "rejected the API key"),
    ((200, {"candidates": [{"finishReason": "SAFETY"}]}), "declined"),
    ((200, {"candidates": [{"finishReason": "MAX_TOKENS", "content": {"parts": [{"text": "{"}]}}]}), "cut off"),
    ((200, {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": "not json"}]}}]}), "couldn't be read"),
    (gemini_ok({"summary": "no score"}), "Gemini's review couldn't be read"),
])
def test_gemini_failures_become_not_measured(gemini_key, reply, reason):
    r = judge_translation(ORIG, DUB, "en", "ko", session=FakeGemini(reply), sleep=lambda x: None)
    assert not r["measured"] and reason in r["reason"]


def test_no_key_at_all_is_not_measured(monkeypatch):
    monkeypatch.setattr(translation_judge, "claude_available", lambda: False)
    r = judge_translation(ORIG, DUB, "en", "ko")
    assert not r["measured"] and "GEMINI_API_KEY" in r["reason"]
