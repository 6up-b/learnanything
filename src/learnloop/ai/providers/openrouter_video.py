"""OpenRouter text-to-video client (``POST /api/v1/videos``).

Video generation is an asynchronous job API, not a chat completion: submit a
prompt, poll the job until it is terminal, download the mp4. This client
keeps the protocol thin and injectable (``http`` seam, ``sleep``/``clock``
seams) so the storyboard service and its tests never touch the network.

Billing note: a job is charged when it is submitted, so ``submit`` is never
retried on a transport error — the caller decides whether to resubmit.
"""

from __future__ import annotations

import http.client
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from learnloop.ai.errors import AIProviderUnavailable, VideoGenerationFailed, VideoGenerationTimeout
from learnloop.ai.providers.openrouter import OPENROUTER_API_KEY_ENV, OPENROUTER_BASE_URL
from learnloop.ai.transport import VIDEO_GENERATION
from learnloop.config import AIProviderConfig

DEFAULT_POLL_INTERVAL_SECONDS = 30.0
FIRST_POLL_DELAY_SECONDS = 15.0
SUBMIT_TIMEOUT_SECONDS = 60.0
POLL_TIMEOUT_SECONDS = 30.0
DOWNLOAD_TIMEOUT_SECONDS = 300.0
# A status poll is idempotent, so a transport blip is retried a few times
# with a short pause before the whole storyboard is failed.
POLL_ATTEMPTS = 3
POLL_RETRY_DELAY_SECONDS = 2.0
TERMINAL_FAILURE_STATES = frozenset({"failed", "cancelled", "expired"})

#: (method, url, headers, body, timeout) -> (status, headers, body)
HttpTransport = Callable[[str, str, Mapping[str, str], bytes | None, float], tuple[int, Mapping[str, str], bytes]]


@dataclass(frozen=True)
class VideoGenerationRequest:
    prompt: str
    duration_seconds: int | None = None
    resolution: str | None = None
    aspect_ratio: str | None = None
    generate_audio: bool = False
    seed: int | None = None


@dataclass(frozen=True)
class VideoJob:
    id: str
    status: str
    polling_url: str | None


@dataclass(frozen=True)
class VideoJobStatus:
    id: str
    status: str
    error: str | None
    cost: float | None
    url_count: int


@dataclass(frozen=True)
class VideoModelConstraints:
    supported_durations: tuple[int, ...]
    supported_resolutions: tuple[str, ...]
    supported_aspect_ratios: tuple[str, ...]


def _urllib_transport(
    method: str, url: str, headers: Mapping[str, str], body: bytes | None, timeout: float
) -> tuple[int, Mapping[str, str], bytes]:
    request = urllib.request.Request(url, data=body, headers=dict(headers), method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 — https API
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as exc:
        # Surface OpenRouter's error JSON to the caller instead of a bare code.
        return exc.code, dict(exc.headers or {}), exc.read()
    except (urllib.error.URLError, OSError, http.client.HTTPException) as exc:
        # URLError covers DNS/refused; a socket timeout, a reset mid-read or a
        # truncated response arrive as OSError / HTTPException and are just as
        # much "unreachable" from the caller's point of view.
        reason = getattr(exc, "reason", None) or exc
        raise AIProviderUnavailable(f"OpenRouter video API unreachable: {reason}") from exc


def _error_text(payload: Any) -> str:
    if isinstance(payload, Mapping):
        error = payload.get("error")
        if isinstance(error, Mapping):
            return str(error.get("message") or error)
        if error:
            return str(error)
        if "raw" in payload:
            return str(payload["raw"])
    return "no details"


def clamp_duration(
    requested: int | None, *, max_seconds: int, constraints: VideoModelConstraints | None
) -> int | None:
    """The shot length to ask for: the largest supported value under the caps."""

    wanted = requested if requested and requested > 0 else max_seconds
    wanted = min(wanted, max_seconds)
    supported = tuple(sorted(constraints.supported_durations)) if constraints else ()
    if not supported:
        return wanted if wanted > 0 else None
    under = [value for value in supported if value <= wanted]
    return under[-1] if under else supported[0]


def _clamp_choice(preferred: str | None, supported: Sequence[str]) -> str | None:
    if not preferred:
        return None
    if not supported or preferred in supported:
        return preferred
    return supported[0]


def clamp_resolution(preferred: str | None, constraints: VideoModelConstraints | None) -> str | None:
    """The preferred resolution when the model lists it (or lists nothing), else its first."""

    return _clamp_choice(preferred, constraints.supported_resolutions if constraints else ())


def clamp_aspect_ratio(preferred: str | None, constraints: VideoModelConstraints | None) -> str | None:
    """Same rule for aspect ratios: an off-list value is a 400 from OpenRouter."""

    return _clamp_choice(preferred, constraints.supported_aspect_ratios if constraints else ())


class OpenRouterVideoClient:
    provider_type = "openrouter_video"

    def __init__(
        self,
        provider_name: str,
        profile: AIProviderConfig,
        *,
        http: HttpTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.provider_name = provider_name
        self.profile = profile
        self.model = profile.model
        if not self.model:
            raise AIProviderUnavailable(f"video provider {provider_name!r} has no model slug")
        key_env = profile.api_key_env or OPENROUTER_API_KEY_ENV
        api_key = os.environ.get(key_env)
        if not api_key:
            raise AIProviderUnavailable(f"Environment variable {key_env} is required for video generation.")
        base_url = (profile.base_url or OPENROUTER_BASE_URL).rstrip("/")
        self._videos_url = f"{base_url}/videos"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Title": getattr(profile, "x_title", None) or "LearnLoop",
        }
        referer = getattr(profile, "http_referer", None)
        if referer:
            headers["HTTP-Referer"] = referer
        self._headers = headers
        self._http: HttpTransport = http or _urllib_transport
        self._sleep = sleep
        self._clock = clock
        self._constraints: VideoModelConstraints | None = None
        self._constraints_loaded = False

    def supports(self, capability: str) -> bool:
        return capability == VIDEO_GENERATION

    # -- protocol ---------------------------------------------------------------

    def _request(self, method: str, url: str, payload: Any = None, *, timeout: float) -> tuple[int, Any]:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        status, _headers, raw = self._http(method, url, self._headers, body, timeout)
        try:
            data = json.loads(raw.decode("utf-8")) if raw else {}
        except (UnicodeDecodeError, ValueError):
            data = {"raw": raw[:200].decode("utf-8", errors="replace")}
        return status, data

    def model_constraints(self) -> VideoModelConstraints | None:
        """Supported durations/resolutions for this model; None when unknown."""

        if self._constraints_loaded:
            return self._constraints
        self._constraints_loaded = True
        try:
            status, data = self._request("GET", f"{self._videos_url}/models", timeout=POLL_TIMEOUT_SECONDS)
        except AIProviderUnavailable:
            return None
        if status != 200 or not isinstance(data, Mapping):
            return None
        entries = data.get("data") if isinstance(data.get("data"), list) else data.get("models")
        for entry in entries or []:
            if isinstance(entry, Mapping) and entry.get("id") == self.model:
                self._constraints = VideoModelConstraints(
                    supported_durations=tuple(int(v) for v in entry.get("supported_durations") or []),
                    supported_resolutions=tuple(str(v) for v in entry.get("supported_resolutions") or []),
                    supported_aspect_ratios=tuple(str(v) for v in entry.get("supported_aspect_ratios") or []),
                )
                break
        return self._constraints

    def submit(self, request: VideoGenerationRequest) -> VideoJob:
        """Submit one generation job. Never retried: submission is billable."""

        payload: dict[str, Any] = {"model": self.model, "prompt": request.prompt}
        if request.duration_seconds:
            payload["duration"] = int(request.duration_seconds)
        if request.resolution:
            payload["resolution"] = request.resolution
        if request.aspect_ratio:
            payload["aspect_ratio"] = request.aspect_ratio
        payload["generate_audio"] = bool(request.generate_audio)
        if request.seed is not None:
            payload["seed"] = int(request.seed)
        status, data = self._request("POST", self._videos_url, payload, timeout=SUBMIT_TIMEOUT_SECONDS)
        # Documented as 202; any 2xx that names a job is a submitted (billed) job.
        if not 200 <= status < 300 or not isinstance(data, Mapping) or not data.get("id"):
            raise VideoGenerationFailed(
                f"OpenRouter video submit failed (HTTP {status}): {_error_text(data)}", status="rejected"
            )
        return VideoJob(id=str(data["id"]), status=str(data.get("status") or "pending"), polling_url=data.get("polling_url"))

    def poll(self, job_id: str) -> VideoJobStatus:
        last_error: Exception | None = None
        for attempt in range(POLL_ATTEMPTS):
            if attempt:
                self._sleep(POLL_RETRY_DELAY_SECONDS)
            try:
                status, data = self._request("GET", f"{self._videos_url}/{job_id}", timeout=POLL_TIMEOUT_SECONDS)
            except AIProviderUnavailable as exc:
                last_error = exc
                continue
            if status >= 500 and attempt < POLL_ATTEMPTS - 1:
                last_error = AIProviderUnavailable(f"OpenRouter video poll HTTP {status}")
                continue
            if status != 200 or not isinstance(data, Mapping):
                raise AIProviderUnavailable(f"OpenRouter video poll failed (HTTP {status}): {_error_text(data)}")
            usage = data.get("usage") if isinstance(data.get("usage"), Mapping) else {}
            cost = usage.get("cost") if isinstance(usage, Mapping) else None
            urls = data.get("unsigned_urls") if isinstance(data.get("unsigned_urls"), list) else []
            return VideoJobStatus(
                id=str(data.get("id") or job_id),
                status=str(data.get("status") or "pending"),
                error=_error_text(data) if data.get("error") else None,
                cost=float(cost) if isinstance(cost, (int, float)) else None,
                url_count=len(urls),
            )
        raise last_error or AIProviderUnavailable("OpenRouter video poll failed")

    def download(self, job_id: str, index: int = 0) -> bytes:
        url = f"{self._videos_url}/{job_id}/content?index={index}"
        headers = {**self._headers, "Accept": "*/*"}  # the body is an mp4, not JSON
        status, _headers, raw = self._http("GET", url, headers, None, DOWNLOAD_TIMEOUT_SECONDS)
        if status != 200 or not raw:
            raise VideoGenerationFailed(
                f"OpenRouter video download failed (HTTP {status})", status="download_failed", job_id=job_id
            )
        return raw

    def wait_all(
        self,
        job_ids: Sequence[str],
        *,
        max_wait_seconds: float,
        poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
        first_delay_seconds: float = FIRST_POLL_DELAY_SECONDS,
        checkpoint: Callable[[list[VideoJobStatus], float], None] | None = None,
    ) -> list[VideoJobStatus]:
        """Poll every job until all complete.

        ``checkpoint(statuses, elapsed)`` runs once per polling round so the
        caller can heartbeat a job lease and raise to cancel (OpenRouter has no
        cancel endpoint; abandoning the poll is the only way to stop waiting).
        A terminal failure on any shot raises with that shot's index."""

        started = self._clock()
        statuses: dict[str, VideoJobStatus] = {}
        pending = list(job_ids)
        delay = first_delay_seconds
        while pending:
            self._sleep(delay)
            delay = poll_interval_seconds
            for job_id in list(pending):
                current = self.poll(job_id)
                statuses[job_id] = current
                if current.status == "completed":
                    pending.remove(job_id)
                elif current.status in TERMINAL_FAILURE_STATES or current.error:
                    # An undocumented status that carries an error payload is
                    # not worth polling until the deadline.
                    index = list(job_ids).index(job_id)
                    raise VideoGenerationFailed(
                        f"shot {index + 1}/{len(job_ids)} {current.status}: {current.error or 'no details'}",
                        status=current.status,
                        job_id=job_id,
                        shot_index=index,
                    )
            elapsed = self._clock() - started
            if checkpoint is not None:
                checkpoint([statuses[job_id] for job_id in job_ids], elapsed)
            if pending and elapsed > max_wait_seconds:
                raise VideoGenerationTimeout(
                    f"video generation exceeded {max_wait_seconds:.0f}s with {len(pending)} shot(s) still pending"
                )
        return [statuses[job_id] for job_id in job_ids]


__all__ = [
    "DEFAULT_POLL_INTERVAL_SECONDS",
    "FIRST_POLL_DELAY_SECONDS",
    "HttpTransport",
    "OpenRouterVideoClient",
    "VideoGenerationRequest",
    "VideoJob",
    "VideoJobStatus",
    "VideoModelConstraints",
    "clamp_aspect_ratio",
    "clamp_duration",
    "clamp_resolution",
]
