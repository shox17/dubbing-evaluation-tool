"""In-memory stand-in for the Perso REST API (shapes from https://developers.perso.ai/llms.txt)."""
import json
import re
from typing import Optional

from src.perso_api import PersoClient


def _lang(code, name, tag="default", tts=("AUDIO_ENGINE_V3",)):
    """One row of the Language API response."""
    return {"code": code, "name": name, "languageTag": tag, "experiment": False, "supportedTtsModels": list(tts)}


# A slice of GET /languages, including a regional variant and a language Whisper doesn't know.
LANGUAGES = [_lang("auto", "Auto Detect", tts=()), _lang("en", "English (US)"), _lang("en", "English (UK)", "en-GB"),
             _lang("ko", "Korean"), _lang("ja", "Japanese"), _lang("fr", "French"), _lang("ceb", "Cebuano")]


class FakeResponse:
    """Minimal stand-in for requests.Response (status, JSON body, raw bytes)."""
    def __init__(self, status: int = 200, body=None, raw: Optional[bytes] = None):
        self.status_code = status
        self._body = body
        self.content = raw if raw is not None else (json.dumps(body).encode() if body is not None else b"")

    def json(self):
        return self._body if self._body is not None else json.loads(self.content)

    def iter_content(self, _size):
        yield self.content

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FakePerso:
    """Scriptable fake. Each project advances one progress step per poll."""

    def __init__(self, video_bytes: bytes = b"dubbed-video", plan_tier: str = "starter", credits: float = 300,
                 fail_translate: Optional[tuple] = None, fail_lipsync: bool = False, lipsync_available: bool = True):
        self.video_bytes = video_bytes
        self.plan_tier, self.credits = plan_tier, credits
        self.fail_translate, self.fail_lipsync, self.lipsync_available = fail_translate, fail_lipsync, lipsync_available
        self.calls: list[tuple[str, str, Optional[dict]]] = []
        self.projects: dict[int, list[dict]] = {}
        self.next_project = 100
        self.cancelled: list[int] = []

    def client(self) -> PersoClient:
        """A PersoClient wired to this fake, with no sleeping between polls."""
        return PersoClient(api_key="test-key", session=self, sleep=lambda s: None, poll_interval=0)

    def _project(self, steps: list[tuple[str, int]]) -> int:
        """Creates a fake project that walks through the given (progressReason, progress) steps."""
        seq = self.next_project
        self.next_project += 1
        self.projects[seq] = [{"progressReason": r, "progress": p, "hasFailed": r == "Failed",
                               "expectedRemainingTimeMinutes": 2 if r != "Completed" else -1,
                               **({"engineErrorMessage": {"errorMessage": {"en": "Face not found"}}} if r == "Failed" else {})}
                              for r, p in steps]
        return seq

    # requests.Session interface -------------------------------------------------
    def request(self, method, url, headers=None, json=None, params=None, timeout=None, **kw):
        """Answers an API call by path, the way the real Perso API would. Records every call."""
        path = url.split("perso.ai", 1)[1]
        self.calls.append((method, path, json or params))
        assert headers["XP-API-KEY"] == "test-key"
        if path == "/portal/api/v1/spaces":
            return FakeResponse(body={"result": [{"spaceSeq": 7, "spaceName": "QA", "planName": "Starter",
                                                  "serviceType": "video_translator", "isDefaultSpaceOwned": True}]})
        if path == "/video-translator/api/v1/languages":
            return FakeResponse(body={"languages": LANGUAGES})
        if path.endswith("/plan/status"):
            return FakeResponse(body={"result": {"planTier": self.plan_tier, "remainingQuota": {"remainingQuota": self.credits}}})
        if path.endswith("/media/quota"):
            d = int(params["durationMs"]) // 1000
            return FakeResponse(body={"result": {"expectedUsedQuota": d * (2 if params["lipSync"] == "true" else 1)}})
        if path == "/file/api/v1/media/validate":
            return FakeResponse(body={"status": True})
        if path.startswith("/file/api/upload/sas-token"):
            return FakeResponse(body={"blobSasUrl": "https://blob.perso.ai/perso-storage/u/in.mp4?sig=abc"})
        if path == "/file/api/upload/video":
            assert "?" not in json["fileUrl"]
            return FakeResponse(body={"seq": 555})
        if path.endswith("/queue"):
            return FakeResponse(body={"result": {"usedQueueCount": 0, "maxQueueCount": 3}})
        if path.endswith("/translate"):
            if self.fail_translate:
                status, code = self.fail_translate
                return FakeResponse(status, {"code": code, "message": "nope", "status": "ERR"})
            seq = self._project([("Enqueue Pending", 0), ("Transcribing", 30), ("Generating Voice", 70), ("Completed", 100)])
            return FakeResponse(body={"result": {"startGenerateProjectIdList": [seq]}})
        if path.endswith("/lip-sync"):
            steps = [("Analyzing Lip Sync", 20), ("Failed", 40)] if self.fail_lipsync else \
                [("Analyzing Lip Sync", 20), ("Applying Lip Sync", 60), ("Completed", 100)]
            return FakeResponse(body={"result": {"startGenerateProjectIdList": [self._project(steps)]}})
        m = re.search(r"/projects/(\d+)/space/\d+/progress", path)
        if m:
            steps = self.projects[int(m.group(1))]
            return FakeResponse(body={"result": steps.pop(0) if len(steps) > 1 else steps[0]})
        if path.endswith("/cancel"):
            self.cancelled.append(int(path.split("/projects/")[1].split("/")[0]))
            return FakeResponse(body={})
        if path.endswith("/download-info"):
            return FakeResponse(body={"hasTranslatedVideo": True, "hasLipSyncVideo": self.lipsync_available})
        if path.endswith("/download"):
            return FakeResponse(body={"result": {"videoFile": {"videoDownloadLink": f"/perso-storage/out/{params['target']} 비디오.mp4"}}})
        if path.endswith("/script"):
            return FakeResponse(body={"sentences": [{"translatedText": "안녕하세요."}, {"translatedText": "저는 존입니다."}]})
        return FakeResponse(404, {"code": "X404", "message": f"unknown {path}"})

    def put(self, url, data=None, headers=None, timeout=None):
        """Fake blob-storage upload (the PUT to the SAS URL)."""
        self.calls.append(("PUT-BLOB", url, None))
        assert headers["x-ms-blob-type"] == "BlockBlob"
        return FakeResponse(201)

    def get(self, url, stream=False, timeout=None):
        """Fake media download; checks the URL is on the media host and URL-encoded."""
        self.calls.append(("GET-MEDIA", url, None))
        assert url.startswith("https://portal-media.perso.ai/perso-storage/") and " " not in url
        return FakeResponse(200, raw=self.video_bytes)


class CopyingFakePerso(FakePerso):
    """Downloads return the bytes of a real video, so the evaluation can run on the 'dub'."""

    def __init__(self, source_video: str, **kw):
        with open(source_video, "rb") as f:
            super().__init__(video_bytes=f.read(), **kw)
