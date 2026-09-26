"""Perso AI REST client, following https://developers.perso.ai/llms.txt.

Flow: SAS upload -> register media -> init queue -> translate -> poll progress
      -> (optional) lip-sync as a separate project -> poll -> download-info -> download.
"""
import os
import time
import logging
import threading
from dataclasses import dataclass
from typing import Callable, Optional
from urllib.parse import quote, urlsplit, urlunsplit

import requests

from src.languages import parse_languages

log = logging.getLogger(__name__)

API_BASE = os.getenv("PERSO_API_BASE", "https://api.perso.ai")
MEDIA_BASE = os.getenv("PERSO_MEDIA_BASE", "https://portal-media.perso.ai")
VT = "/video-translator/api/v1"
CREDENTIALS_FILE = os.path.join(os.path.expanduser("~"), ".perso", "credentials")

POLL_INTERVAL_SEC = 5            # the docs forbid polling faster than every 5 s
DEFAULT_TTS_MODEL = "AUDIO_ENGINE_V3"
SUPPORTED_UPLOAD_EXTENSIONS = (".mp4", ".webm", ".mov")

# User-facing names for Perso's progressReason values.
STAGE_LABELS = {
    "Enqueue Pending": "Waiting in the Perso queue",
    "Slow Mode Pending": "Waiting in the Perso queue (slow mode)",
    "Uploading": "Preparing media",
    "Transcribing": "Transcribing the original speech",
    "Translating": "Translating the script",
    "Generating Voice": "Generating the dubbed voice",
    "Analyzing Lip Sync": "Analyzing mouth movements",
    "Applying Lip Sync": "Re-rendering lips to match the new audio",
    "Completed": "Completed",
    "Failed": "Failed",
}

ERROR_HINTS = {
    "VT4021": "Not enough Perso credits for this video. Top up at https://perso.ai and try again.",
    "VT5034": "The Perso queue is full right now. Try again in a few minutes.",
    "VT4009": "This target language doesn't support the selected voice model.",
    "VT4044": "Perso doesn't offer this target language. Pick another one from the list.",
    "F4004": "The video file is too large for your Perso plan.",
    "F4007": "This file type isn't supported. Use .mp4, .mov or .webm.",
    "F4008": "The video is longer than your Perso plan allows.",
    "F4009": "The video is too short (minimum 1 second).",
    "F40010": "The video resolution is too high for Perso (max 7999 px).",
    "F40011": "The video resolution is too low for Perso (min 201 px).",
    "F4005": "Your Perso plan's usage limit has been reached.",
}


class PersoError(RuntimeError):
    """A Perso request failed; the message is safe to show to users."""

    def __init__(self, message: str, code: Optional[str] = None, status: Optional[int] = None):
        super().__init__(message)
        self.code = code
        self.status = status


class Cancelled(RuntimeError):
    """The user stopped waiting for a job."""


@dataclass
class ProjectStatus:
    """A snapshot of one Perso project's progress, as returned by the progress endpoint."""
    project_seq: int
    reason: str
    progress: float                 # 0..100
    eta_minutes: Optional[float]
    failed: bool
    failure_message: Optional[str]

    @property
    def label(self) -> str:
        """Plain-language name of the current Perso step, for the progress page."""
        return STAGE_LABELS.get(self.reason, self.reason or "Processing")

    @property
    def done(self) -> bool:
        """True once Perso reports the project as completed."""
        return self.reason == "Completed"


def resolve_api_key() -> Optional[str]:
    """PERSO_API_KEY / XP_API_KEY env, else the key registered by the Perso CLI (~/.perso/credentials)."""
    for var in ("PERSO_API_KEY", "XP_API_KEY"):
        if os.getenv(var, "").strip():
            return os.environ[var].strip()
    if os.name != "nt" and os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
            key = f.read().strip()
        return key or None
    return None


def media_url(path: str) -> str:
    """Resolves a relative /perso-storage/... path against the media host, URL-encoding the path."""
    url = path if path.startswith("http") else MEDIA_BASE.rstrip("/") + "/" + path.lstrip("/")
    parts = urlsplit(url)
    return urlunsplit(parts._replace(path=quote(parts.path, safe="/%")))


def _error_from_response(resp: requests.Response) -> PersoError:
    """Turns a failed HTTP response into a PersoError with a plain-language message."""
    try:
        body = resp.json()
    except ValueError:
        body = {}
    code = body.get("code") if isinstance(body, dict) else None
    detail = (body.get("message") or body.get("detail") or body.get("error")) if isinstance(body, dict) else None
    if code in ERROR_HINTS:
        msg = ERROR_HINTS[code]
    elif resp.status_code == 401:
        msg = "The Perso API key is missing, invalid or expired. Check PERSO_API_KEY."
    elif resp.status_code == 403:
        msg = "Your Perso API key has no permission for this workspace."
    elif resp.status_code == 429:
        msg = "Perso is rate-limiting requests. Wait a minute and try again."
    else:
        msg = f"Perso API error {resp.status_code}" + (f": {detail}" if detail else "")
    return PersoError(msg, code=code, status=resp.status_code)


class PersoClient:
    """Client for the Perso REST API. Needs an API key; see resolve_api_key."""
    def __init__(self, api_key: Optional[str] = None, session: Optional[requests.Session] = None,
                 sleep: Callable[[float], None] = time.sleep, poll_interval: float = POLL_INTERVAL_SEC):
        """Raises PersoError if no API key is found. session/sleep/poll_interval are overridable for tests."""
        self.api_key = api_key or resolve_api_key()
        if not self.api_key:
            raise PersoError("No Perso API key found. Add PERSO_API_KEY to the .env file "
                             "(get a key at https://developers.perso.ai/api-keys).")
        self.http = session or requests.Session()
        self.sleep = sleep
        self.poll_interval = poll_interval
        self._queue_ready: set[int] = set()

    # ---------------- low level ----------------
    def _request(self, method: str, path: str, retries: int = 3, **kwargs) -> dict:
        """Calls the API and returns its JSON; retries rate limits and server errors with backoff."""
        url = API_BASE + path
        headers = {"XP-API-KEY": self.api_key, **kwargs.pop("headers", {})}
        timeout = kwargs.pop("timeout", 60)
        for attempt in range(retries + 1):
            try:
                resp = self.http.request(method, url, headers=headers, timeout=timeout, **kwargs)
            except requests.RequestException as e:
                if attempt == retries:
                    raise PersoError(f"Could not reach Perso ({e.__class__.__name__}). Check your internet connection.")
                self.sleep(2 ** attempt)
                continue
            if resp.status_code == 429 or resp.status_code >= 500:
                if attempt < retries:
                    self.sleep(2 ** (attempt + 1))
                    continue
            if resp.status_code >= 400:
                raise _error_from_response(resp)
            if not resp.content:
                return {}
            return resp.json()
        raise PersoError("Perso request failed after retries.")

    # ---------------- account ----------------
    def list_spaces(self) -> list[dict]:
        """Workspaces usable for dubbing (serviceType video_translator), falling back to all."""
        spaces = self._request("GET", "/portal/api/v1/spaces").get("result") or []
        vt = [s for s in spaces if s.get("serviceType") == "video_translator" or s.get("useVideoTranslatorEdit")]
        return vt or spaces

    def default_space(self) -> dict:
        """The workspace to dub in: PERSO_SPACE_SEQ if set, else the owned default, else the first."""
        spaces = self.list_spaces()
        if not spaces:
            raise PersoError("This Perso account has no workspace. Create one at https://perso.ai.")
        pinned = os.getenv("PERSO_SPACE_SEQ")
        if pinned:
            for s in spaces:
                if str(s.get("spaceSeq")) == pinned.strip():
                    return s
        return next((s for s in spaces if s.get("isDefaultSpaceOwned")), spaces[0])

    def list_languages(self) -> list[dict]:
        """Target languages Perso can dub into (GET /languages), as entries from src.languages."""
        rows = self._request("GET", f"{VT}/languages").get("languages") or []
        return parse_languages(rows)

    def plan_status(self, space_seq: int) -> dict:
        """Plan tier, remaining quota and reset date for a workspace."""
        return self._request("GET", f"{VT}/projects/spaces/{space_seq}/plan/status").get("result") or {}

    def remaining_credits(self, space_seq: int) -> Optional[float]:
        """Credits (seconds of video) left in a workspace, or None if Perso doesn't say."""
        quota = (self.plan_status(space_seq).get("remainingQuota") or {}).get("remainingQuota")
        return float(quota) if quota is not None else None

    def estimate_credits(self, space_seq: int, duration_ms: int, width: int, height: int, lip_sync: bool) -> Optional[float]:
        """Credits Perso expects a video of this size and length to cost, with or without lip-sync."""
        r = self._request("GET", f"{VT}/projects/spaces/{space_seq}/media/quota", params={
            "mediaType": "video", "lipSync": str(lip_sync).lower(), "durationMs": int(duration_ms),
            "width": int(width), "height": int(height), "targetLanguageSize": 1,
        }).get("result") or {}
        value = r.get("expectedUsedQuota")
        return float(value) if value is not None else None

    # ---------------- media ----------------
    def validate_media(self, space_seq: int, file_name: str, size: int, duration_ms: int, width: int, height: int) -> None:
        """Asks Perso whether the video fits the plan's limits before uploading; raises PersoError if not."""
        ext = os.path.splitext(file_name)[1].lower()
        self._request("POST", "/file/api/v1/media/validate", json={
            "spaceSeq": space_seq, "durationMs": int(duration_ms), "originalName": file_name, "mediaType": "video",
            "extension": ext, "size": int(size), "width": int(width), "height": int(height),
        })

    def upload_video(self, space_seq: int, path: str) -> int:
        """SAS token -> PUT to blob storage -> register. Returns mediaSeq."""
        file_name = os.path.basename(path)
        sas = self._request("GET", "/file/api/upload/sas-token", params={"fileName": file_name})
        blob_url = sas.get("blobSasUrl")
        if not blob_url:
            raise PersoError("Perso did not return an upload URL.")
        with open(path, "rb") as f:
            resp = self.http.put(blob_url, data=f, timeout=600, headers={
                "x-ms-blob-type": "BlockBlob", "Content-Type": "application/octet-stream"})
        if resp.status_code not in (200, 201):
            raise PersoError(f"Uploading the video to Perso storage failed (HTTP {resp.status_code}).")
        registered = self._request("PUT", "/file/api/upload/video", timeout=300, json={
            "spaceSeq": space_seq, "fileUrl": blob_url.split("?", 1)[0], "fileName": file_name})
        media_seq = registered.get("seq")
        if media_seq is None:
            raise PersoError("Perso did not register the uploaded video.")
        return int(media_seq)

    # ---------------- projects ----------------
    def _ensure_queue(self, space_seq: int) -> None:
        """Creates the workspace's dubbing queue once; Perso rejects dubbing requests without it."""
        if space_seq not in self._queue_ready:
            self._request("PUT", f"{VT}/projects/spaces/{space_seq}/queue")
            self._queue_ready.add(space_seq)

    def request_dubbing(self, space_seq: int, media_seq: int, target_lang: str, source_lang: str = "auto",
                        title: Optional[str] = None, tts_model: str = DEFAULT_TTS_MODEL,
                        language_tag: Optional[str] = None) -> int:
        """Starts a dub. language_tag picks a regional variant of target_lang (en-GB, pt-PT, es-ES)."""
        target = {"languageCode": target_lang, **({"languageTag": language_tag} if language_tag else {}),
                  "ttsModel": tts_model}
        self._ensure_queue(space_seq)
        body = {
            "mediaSeq": media_seq,
            "isVideoProject": True,
            "sourceLanguageCode": source_lang or "auto",
            "targetLanguages": [target],
            "numberOfSpeakers": 1,
            "withLipSync": False,        # lip-sync runs as its own project afterwards
            "preferredSpeedType": "GREEN",
            **({"title": title} if title else {}),
        }
        ids = (self._request("POST", f"{VT}/projects/spaces/{space_seq}/translate", json=body).get("result") or {}) \
            .get("startGenerateProjectIdList") or []
        if not ids:
            raise PersoError("Perso accepted the request but returned no project.")
        return int(ids[0])

    def request_lipsync(self, project_seq: int, space_seq: int) -> int:
        """Starts lip-sync on a finished dub. Returns the new lip-sync project's id."""
        ids = (self._request("POST", f"{VT}/projects/{project_seq}/spaces/{space_seq}/lip-sync",
                             json={"preferredSpeedType": "GREEN"}).get("result") or {}).get("startGenerateProjectIdList") or []
        if not ids:
            raise PersoError("Perso returned no lip-sync project.")
        return int(ids[0])

    def get_status(self, project_seq: int, space_seq: int) -> ProjectStatus:
        """Current progress of a project, including Perso's failure message if it failed."""
        r = self._request("GET", f"{VT}/projects/{project_seq}/space/{space_seq}/progress")
        r = r.get("result", r)
        reason = r.get("progressReason") or "Processing"
        failed = bool(r.get("hasFailed")) or reason == "Failed"
        message = None
        if failed:
            em = r.get("engineErrorMessage")
            if isinstance(em, dict):
                em = em.get("errorMessage", em)
                message = em.get("en") or em.get("ko") if isinstance(em, dict) else str(em)
            message = message or r.get("failureReason") or "Perso reported a failure."
        eta = r.get("expectedRemainingTimeMinutes")
        return ProjectStatus(
            project_seq=project_seq, reason=reason, progress=float(r.get("progress") or 0),
            eta_minutes=float(eta) if isinstance(eta, (int, float)) and eta >= 0 else None,
            failed=failed, failure_message=message)

    def wait_for(self, project_seq: int, space_seq: int, on_update: Callable[[ProjectStatus], None],
                 cancel_event: Optional[threading.Event] = None, timeout_sec: float = 6 * 3600) -> ProjectStatus:
        """Polls until the project completes. Raises PersoError on failure, Cancelled if cancel_event is set."""
        deadline = time.monotonic() + timeout_sec
        while True:
            if cancel_event is not None and cancel_event.is_set():
                self.cancel(project_seq, space_seq)
                raise Cancelled("Stopped by user.")
            status = self.get_status(project_seq, space_seq)
            on_update(status)
            if status.failed:
                raise PersoError(f"Perso could not finish this video: {status.failure_message}")
            if status.done:
                return status
            if time.monotonic() > deadline:
                raise PersoError(f"Perso did not finish within {timeout_sec / 3600:.0f} hours.")
            self.sleep(self.poll_interval)

    def cancel(self, project_seq: int, space_seq: int) -> bool:
        """Best effort: Perso only cancels projects that are still queued."""
        try:
            self._request("POST", f"{VT}/projects/{project_seq}/spaces/{space_seq}/cancel", json={}, retries=0)
            return True
        except PersoError:
            return False

    def get_script(self, project_seq: int, space_seq: int) -> list[dict]:
        """The sentences Perso transcribed and translated for a project."""
        r = self._request("GET", f"{VT}/projects/{project_seq}/spaces/{space_seq}/script")
        return r.get("sentences") or (r.get("result") or {}).get("sentences") or []

    def download_video(self, project_seq: int, space_seq: int, out_path: str, lipsync: bool = False) -> str:
        """Downloads the dubbed (or lip-synced) video to out_path, retrying on network errors."""
        info = self._request("GET", f"{VT}/projects/{project_seq}/spaces/{space_seq}/download-info")
        info = info.get("result", info)
        flag, target = ("hasLipSyncVideo", "lipSyncVideo") if lipsync else ("hasTranslatedVideo", "dubbingVideo")
        if info.get(flag) is False:
            raise PersoError("The finished video is not available for download. "
                             "Free Perso plans cannot download results — a paid plan is required.")
        r = self._request("GET", f"{VT}/projects/{project_seq}/spaces/{space_seq}/download", params={"target": target})
        r = r.get("result", r)
        link = (r.get("videoFile") or {}).get("videoDownloadLink") or _find_download_link(r)
        if not link:
            raise PersoError("Perso returned no download link for the video.")
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        for attempt in range(3):
            try:
                with self.http.get(media_url(link), stream=True, timeout=600) as resp:
                    if resp.status_code != 200:
                        raise PersoError(f"Downloading the dubbed video failed (HTTP {resp.status_code}).")
                    with open(out_path, "wb") as f:
                        for chunk in resp.iter_content(1 << 20):
                            f.write(chunk)
                return out_path
            except (requests.RequestException, PersoError):
                if attempt == 2:
                    raise
                self.sleep(2 * (attempt + 1))
        return out_path


def _find_download_link(obj) -> Optional[str]:
    """Searches a response for any *DownloadLink value, in case Perso moves the field."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and k.endswith("DownloadLink") and v:
                return v
            found = _find_download_link(v)
            if found:
                return found
    return None
