"""Scripted HTTP transport for OpenRouterVideoClient tests."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlparse


class FakeVideoHttp:
    """Answers the video API by (method, path); records every call.

    ``polls`` maps a job id to the sequence of statuses to return; the last
    entry repeats. ``contents`` maps a job id to the mp4 bytes to download.
    """

    def __init__(
        self,
        *,
        submit_status: int = 202,
        submit_error: dict[str, Any] | None = None,
        polls: dict[str, list[dict[str, Any]]] | None = None,
        contents: dict[str, bytes] | None = None,
        models: list[dict[str, Any]] | None = None,
        models_status: int = 200,
        poll_http_errors: dict[str, list[int]] | None = None,
    ) -> None:
        self.submit_status = submit_status
        self.submit_error = submit_error
        self.polls = {job: list(seq) for job, seq in (polls or {}).items()}
        self.contents = dict(contents or {})
        self.models = models if models is not None else [
            {
                "id": "google/veo-3.1",
                "supported_durations": [4, 6, 8],
                "supported_resolutions": ["720p", "1080p"],
                "supported_aspect_ratios": ["16:9"],
            }
        ]
        self.models_status = models_status
        self.poll_http_errors = {job: list(codes) for job, codes in (poll_http_errors or {}).items()}
        self.calls: list[tuple[str, str, dict[str, Any] | None]] = []
        self.submitted = 0

    def __call__(self, method: str, url: str, headers: Any, body: bytes | None, timeout: float):
        assert headers["Authorization"].startswith("Bearer "), "missing bearer token"
        path = urlparse(url).path
        query = urlparse(url).query
        payload = json.loads(body.decode("utf-8")) if body else None
        self.calls.append((method, path + (f"?{query}" if query else ""), payload))
        if method == "GET" and path.endswith("/videos/models"):
            return self.models_status, {}, json.dumps({"data": self.models}).encode("utf-8")
        if method == "POST" and path.endswith("/videos"):
            self.submitted += 1
            if self.submit_status not in (200, 202):
                return self.submit_status, {}, json.dumps({"error": self.submit_error or {"message": "rejected"}}).encode("utf-8")
            job_id = f"vid_{self.submitted}"
            self.polls.setdefault(job_id, [{"status": "completed"}])
            return 202, {}, json.dumps({"id": job_id, "status": "pending", "polling_url": f"/api/v1/videos/{job_id}"}).encode("utf-8")
        if method == "GET" and path.endswith("/content"):
            job_id = path.rsplit("/", 2)[-2]
            data = self.contents.get(job_id, b"mp4-" + job_id.encode())
            return 200, {}, data
        if method == "GET" and "/videos/" in path:
            job_id = path.rsplit("/", 1)[-1]
            codes = self.poll_http_errors.get(job_id)
            if codes:
                return codes.pop(0), {}, b'{"error": {"message": "flaky"}}'
            sequence = self.polls.get(job_id) or [{"status": "pending"}]
            entry = sequence.pop(0) if len(sequence) > 1 else sequence[0]
            body = {"id": job_id, **entry}
            if entry.get("status") == "completed":
                body.setdefault("unsigned_urls", [f"https://openrouter.ai/api/v1/videos/{job_id}/content?index=0"])
                body.setdefault("usage", {"cost": 0.25})
            return 200, {}, json.dumps(body).encode("utf-8")
        raise AssertionError(f"unexpected call {method} {path}")
