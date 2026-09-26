"""Tests for the Perso REST client against the in-memory fake API (tests/fake_perso.py)."""
import threading

import pytest

from src import perso_api
from src.perso_api import PersoError, Cancelled, media_url, resolve_api_key
from fake_perso import FakePerso


def test_media_url_resolves_and_encodes():
    assert media_url("/perso-storage/a b/비디오.mp4") == \
        "https://portal-media.perso.ai/perso-storage/a%20b/%EB%B9%84%EB%94%94%EC%98%A4.mp4"


def test_api_key_from_env_wins(monkeypatch):
    monkeypatch.setenv("PERSO_API_KEY", " env-key ")
    assert resolve_api_key() == "env-key"


def test_missing_key_has_clear_message(monkeypatch, tmp_path):
    monkeypatch.delenv("PERSO_API_KEY", raising=False)
    monkeypatch.delenv("XP_API_KEY", raising=False)
    monkeypatch.setattr(perso_api, "CREDENTIALS_FILE", str(tmp_path / "none"))
    with pytest.raises(PersoError, match="No Perso API key"):
        perso_api.PersoClient()


def test_upload_flow_strips_sas_query_and_returns_media_seq(tmp_path):
    fake = FakePerso()
    video = tmp_path / "in.mp4"
    video.write_bytes(b"x")
    assert fake.client().upload_video(7, str(video)) == 555
    kinds = [c[0] + " " + c[1].split("?")[0] for c in fake.calls]
    assert kinds == ["GET /file/api/upload/sas-token", "PUT-BLOB https://blob.perso.ai/perso-storage/u/in.mp4",
                     "PUT /file/api/upload/video"]


def test_dubbing_request_initialises_queue_and_uses_target_languages():
    fake = FakePerso()
    seq = fake.client().request_dubbing(7, 555, "ko")
    assert seq == 100
    methods = [(m, p) for m, p, _ in fake.calls]
    assert methods[0] == ("PUT", "/video-translator/api/v1/projects/spaces/7/queue")
    body = fake.calls[1][2]
    assert body["targetLanguages"] == [{"languageCode": "ko", "ttsModel": "AUDIO_ENGINE_V3"}]
    assert body["sourceLanguageCode"] == "auto" and body["withLipSync"] is False


def test_regional_variant_is_sent_as_language_tag():
    fake = FakePerso()
    fake.client().request_dubbing(7, 555, "en", language_tag="en-GB")
    assert fake.calls[1][2]["targetLanguages"] == [{"languageCode": "en", "languageTag": "en-GB",
                                                    "ttsModel": "AUDIO_ENGINE_V3"}]


def test_list_languages_skips_auto_and_keeps_regional_variants():
    langs = FakePerso().client().list_languages()
    assert [l["id"] for l in langs] == ["en", "en-GB", "ko", "ja", "fr", "ceb"]
    uk = langs[1]
    assert uk == {"id": "en-GB", "code": "en", "tag": "en-GB", "name": "English (UK)", "experimental": False}


def test_wait_for_reports_each_stage_until_completed():
    fake = FakePerso()
    c = fake.client()
    seq = c.request_dubbing(7, 555, "ko")
    seen = []
    final = c.wait_for(seq, 7, on_update=seen.append)
    assert [s.reason for s in seen] == ["Enqueue Pending", "Transcribing", "Generating Voice", "Completed"]
    assert seen[1].label == "Transcribing the original speech" and seen[1].eta_minutes == 2
    assert final.done and final.eta_minutes is None      # negative ETA after completion is dropped


def test_failed_project_raises_with_engine_message():
    fake = FakePerso(fail_lipsync=True)
    c = fake.client()
    ls = c.request_lipsync(100, 7)
    with pytest.raises(PersoError, match="Face not found"):
        c.wait_for(ls, 7, on_update=lambda s: None)


def test_cancel_stops_polling_and_asks_perso_to_cancel():
    fake = FakePerso()
    c = fake.client()
    seq = c.request_dubbing(7, 555, "ko")
    ev = threading.Event()
    ev.set()
    with pytest.raises(Cancelled):
        c.wait_for(seq, 7, on_update=lambda s: None, cancel_event=ev)
    assert fake.cancelled == [seq]


@pytest.mark.parametrize("status, code, message", [
    (402, "VT4021", "Not enough Perso credits"),
    (503, "VT5034", "queue is full"),
    (401, "A0010", "API key is missing, invalid or expired"),
])
def test_api_errors_become_friendly_messages(status, code, message):
    fake = FakePerso(fail_translate=(status, code))
    with pytest.raises(PersoError, match=message):
        fake.client().request_dubbing(7, 555, "ko")


def test_download_refuses_when_video_unavailable(tmp_path):
    fake = FakePerso(lipsync_available=False)
    with pytest.raises(PersoError, match="not available for download"):
        fake.client().download_video(101, 7, str(tmp_path / "o.mp4"), lipsync=True)


def test_download_writes_file(tmp_path):
    fake = FakePerso(video_bytes=b"VIDEO")
    out = fake.client().download_video(101, 7, str(tmp_path / "o.mp4"))
    assert open(out, "rb").read() == b"VIDEO"


def test_estimate_and_credits():
    c = FakePerso(credits=42).client()
    assert c.remaining_credits(7) == 42
    assert c.estimate_credits(7, 28_700, 1920, 1080, lip_sync=True) == 56
