"""The bounded ASGI host: capture (M1) and the phone's practice surface (M2a).

The event loop runs no handler code. Capture never loads a vault; the first RPC starts
the practice runtime's two secondary workers (:mod:`learnloop_mobile.runtime`).
"""
from __future__ import annotations

import asyncio
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from functools import partial
import json
import logging
from pathlib import Path
import re
import sqlite3
import time

from python_multipart.exceptions import MultipartParseError
from starlette.applications import Starlette
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException
from starlette.formparsers import MultiPartException
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response
from starlette.staticfiles import StaticFiles

from learnloop import activation_journal, capture
from learnloop.db.migrate import applied_versions, discover_migrations
from learnloop.db.repositories import Repository
from learnloop.db.stores.session_ownership import SessionOwnershipError
from learnloop_mobile.adapter import error_body, status_for, translate
from learnloop_mobile.allowlist import (
    ALLOWLIST, API_VERSION, PLAN_METHODS, PROBE_METHODS, ParamRejected, allowlist_digest, check_parameters,
    check_probe_parameters, validate_envelope,
)
from learnloop_mobile.config import APP_DIR, MobileConfig, sqlite_path
from learnloop_mobile.runtime import HostBusy, HostRuntime, JobView, ParamsInvalid, _status_body

#: What ``/api/v1/status`` and ``/api/v1/meta`` call this host.
HOST_VERSION = "0.1.0"
HEADER_LIMIT = 16 * 1024
JSON_LIMIT = 256 * 1024
BODY_DEADLINE = 60
PAIR_ATTEMPTS_PER_MINUTE = 30
#: §6.3: how long ``/rpc`` waits on a long job before it answers 202.
JOB_WAIT_SECONDS = 15
#: Requests in flight per lane. ``rpc`` holds the two queues of §4.6 plus what is
#: running on each worker and a request being read, so the queues are what answer
#: ``host_busy``. Status polls use ``short``, so waiting RPCs never starve them.
LANE_LIMITS = {"capture": 2, "short": 16, "rpc": 32}
_LOG = logging.getLogger(__name__)
ENDPOINT_SCOPES = {
    ("GET", "/api/v1/status"): "capture",
    ("POST", "/api/v1/capture"): "capture",
    ("GET", "/api/v1/capture/{capture_id}"): "capture",
    ("POST", "/rpc"): "app",
    ("GET", "/api/v1/queue-revision"): "app",
    ("GET", "/api/v1/meta"): "app",
    ("GET", "/api/v1/jobs/{job_id}"): "app",
    ("GET", "/api/v1/submissions/{submission_id}"): "app",
}
#: The pollable status reads with an id in their path: their route template, and how many
#: path separators a well-formed one has.
_ID_ROUTES = {
    "/api/v1/capture/": "/api/v1/capture/{capture_id}",
    "/api/v1/jobs/": "/api/v1/jobs/{job_id}",
    "/api/v1/submissions/": "/api/v1/submissions/{submission_id}",
}
#: The phone's measurement of its last ``/rpc`` round trip (mobile v2 §4.5), carried on its next
#: one: ``<method>;status=<code>;dur=<ms>[;host=<ms>]``, ``host`` being the ``Server-Timing``
#: total it read. One sample a request, so nothing here buffers or batches.
CLIENT_TIMING_HEADER = "learnloop-client-timing"
#: What the app says it can do, on every ``/rpc`` (mobile v2 V3; Codex review of V3, F3): a comma-separated list.
#: ``phone_probes``: it renders and answers a probe under its contract. A cached app from before V3 says nothing, so
#: the host's ``phone_probes`` never reaches it: its doors and its plan step are V2's (no burn it can't answer).
CLIENT_CAPABILITIES_HEADER = "learnloop-capabilities"
PHONE_PROBES_CAPABILITY = "phone_probes"
_CLIENT_TIMING = re.compile(r"([a-z_.]+);status=([1-5][0-9]{2});dur=([0-9]{1,9}(?:\.[0-9]{1,3})?)"
                            r"(?:;host=([0-9]{1,9}(?:\.[0-9]{1,3})?))?")
CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
       "img-src 'self' blob: data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
SECURITY_HEADERS = {
    "Cache-Control": "no-store", "Content-Security-Policy": CSP,
    "Referrer-Policy": "no-referrer", "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
}


def _is_app_path(path: str) -> bool:
    return path == "/app" or path.startswith("/app/")


def _route_of(method: str, path: str) -> tuple[str, str]:
    """The endpoint's template, for a GET with an id in its path."""

    if method == "GET":
        for prefix, template in _ID_ROUTES.items():
            if path.startswith(prefix) and path.count("/") == 4 and len(path) > len(prefix):
                return ("GET", template)
    return (method, path)


class HostError(Exception):
    def __init__(self, status: int, code: str, message: str = ""):
        self.status, self.code, self.message = status, code, message or code


class SchemaMismatch(RuntimeError):
    """Configuration error: supervisor must not restart (EX_CONFIG = 78)."""


def database_path(config: MobileConfig) -> Path:
    return sqlite_path(config)


def attach(config: MobileConfig, *, read_only: bool = False) -> Repository:
    path = database_path(config)
    expected = {migration.version for migration in discover_migrations()}
    try:
        valid = path.is_file() and bool(expected) and applied_versions(path) == expected
    except sqlite3.Error:
        valid = False
    if not valid:
        raise SchemaMismatch(
            "Schema mismatch: open the desktop app or run learnloop doctor --fix-state --vault "
            f"{config.vault} once to migrate"
        )
    if activation_journal.pending(path):
        # LP-min (a), re-review F2: an activation that did not commit; the
        # desktop or `learnloop upgrade` completes it, this host never does.
        raise SchemaMismatch(activation_journal.message(path))
    return Repository.attach(path, read_only=read_only)


def error_response(status: int, code: str, message: str = "") -> JSONResponse:
    return JSONResponse(
        {"ok": False, "error": {"code": code, "message": message or code,
                               "retryable": status in {429, 503}, "details": {}}},
        status_code=status,
        headers={"Retry-After": "60"} if status == 429 else None,
    )


def _json(body: bytes | bytearray) -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result
    try:
        value = json.loads(body, object_pairs_hook=unique,
                           parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        if not isinstance(value, dict):
            raise ValueError()
        return value
    except (ValueError, UnicodeError, RecursionError):
        raise HostError(400, "invalid_request") from None


def _multipart(scope, body: bytes | bytearray, max_media: int) -> tuple[dict, bytes]:
    """Parse on the admitted worker, including multipart spool-file I/O."""
    async def parse():
        async def replay():
            return {"type": "http.request", "body": body, "more_body": False}
        request = Request(scope, replay)
        async with request.form(max_files=1, max_fields=10, max_part_size=64 * 1024) as form:
            pairs = list(form.multi_items())
            if len({key for key, _ in pairs}) != len(pairs):
                raise HostError(400, "invalid_request")
            files = [(key, value) for key, value in pairs if isinstance(value, UploadFile)]
            if len(files) != 1 or files[0][0] != "file":
                raise HostError(422, "validation_error")
            media = await files[0][1].read(max_media + 1)
            if len(media) > max_media:
                raise HostError(413, "body_too_large")
            data = {key: value for key, value in pairs if not isinstance(value, UploadFile)}
            return data, media
    try:
        return asyncio.run(parse())
    except (MultipartParseError, MultiPartException, ValueError):
        raise HostError(400, "invalid_request") from None


def _ms(seconds: float) -> str:
    return f"{max(seconds, 0.0) * 1000:.1f}"


def server_timing(timing: dict[str, float] | None, total_seconds: float) -> str:
    """Mobile v2 §4.5's ``Server-Timing``: the whole request on the host, and where it went.

    ``queue`` is the wait for the RPC worker and ``handler`` the sidecar handler on it (a short
    method); ``job`` is the time ``/rpc`` held a long method (its 15 s wait, or less). A request
    refused before a worker saw it carries ``total`` alone.
    """

    parts = []
    timing = timing or {}
    if "submitted" in timing and "started" in timing:
        parts.append(f"queue;dur={_ms(timing['started'] - timing['submitted'])}")
        if "finished" in timing:
            parts.append(f"handler;dur={_ms(timing['finished'] - timing['started'])}")
    if "job_from" in timing and "job_to" in timing:
        parts.append(f"job;dur={_ms(timing['job_to'] - timing['job_from'])}")
    parts.append(f"total;dur={_ms(total_seconds)}")
    return ", ".join(parts)


def client_timing(value: str | None) -> tuple[str, int, float, float | None] | None:
    """The phone's last round trip, as ``(method, status, ms, host ms)``, or None.

    Only an allowlisted method's name is ever logged (the request log's rule), and a header that
    does not parse is ignored, never refused: it is a measurement, not a request.
    """

    match = _CLIENT_TIMING.fullmatch(value or "")
    if match is None or match.group(1) not in ALLOWLIST:
        return None
    duration = float(match.group(3))
    host = float(match.group(4)) if match.group(4) is not None else None
    if host is not None and host > duration:
        host = None  # Two clocks that disagree say nothing about the network.
    return match.group(1), int(match.group(2)), duration, host


def _log_client_timing(repo: Repository, sample: tuple[str, int, float, float | None], device_id: str) -> None:
    """``client:<method>``: the round trip the phone saw; ``network:<method>``: that less the host's
    own ``Server-Timing`` total. Both in the request log's existing ``duration_ms`` (§4.5)."""

    method, status, duration, host = sample
    capture.log_request(repo, endpoint=f"client:{method}", status=status, duration_ms=duration, device_id=device_id)
    if host is not None:
        capture.log_request(repo, endpoint=f"network:{method}", status=status, duration_ms=duration - host,
                            device_id=device_id)


class MobileHost:
    def __init__(self, config: MobileConfig):
        if not config.enabled:
            raise SchemaMismatch("Mobile host is disabled; set enabled = true in mobile.toml")
        self.config = config
        self.repo = attach(config)
        self.read_repo = Repository.attach(self.repo.sqlite_path, read_only=True)
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="mobile-auth")
        self.capture_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="mobile-capture")
        self.active = {"short": 0, "capture": 0, "media": 0, "rpc": 0}
        self.runtime = HostRuntime(config.vault, self.repo, self.read_repo, phone_probes=config.phone_probes)
        self.app_dir = APP_DIR
        # attach() checked the applied migrations are exactly the discovered ones, so the
        # head is the vault's schema (mobile v2 §5.2's meta).
        self.schema_version = max(migration.version for migration in discover_migrations())
        # Spec §4.6: no per-device/token rate limits (bounded admission covers
        # work). Only pairing attempts share an in-memory budget, on top of the
        # durable per-record and global exchange locks.
        self.pair_attempts: deque[float] = deque()
        self.last_prune = float("-inf")
        self.assets = {}
        for name in ("pair.html", "pair.js"):
            path = Path(__file__).with_name("static") / name
            if path.is_symlink() or not path.resolve().is_relative_to(Path(__file__).parent.resolve()):
                raise SchemaMismatch("Packaged assets must not be symlinks")
            self.assets[name] = path.read_bytes()

    def on_start(self) -> None:
        """What a starting host owes the desktop and the phone (§3.3, §6.3).

        One bump, unconditionally: a bump that failed in a host that then died is lost with
        that process, and this moves the token anyway. A desktop's poll spends one refetch
        per host start. Then the jobs another run left open.
        """

        try:
            self.repo.bump_queue_revision()
        except sqlite3.Error:
            _LOG.warning("queue revision not bumped at start", exc_info=True)
        self.runtime.recover()

    async def work(self, function, *args, **kwargs):
        return await self._work(self.executor, function, *args, **kwargs)

    async def capture_work(self, function, *args, **kwargs):
        return await self._work(self.capture_executor, function, *args, **kwargs)

    async def _work(self, executor, function, *args, **kwargs):
        future = asyncio.get_running_loop().run_in_executor(
            executor, partial(function, *args, **kwargs)
        )
        # A disconnected caller cannot release admission while its write continues.
        try:
            return await asyncio.shield(future)
        except asyncio.CancelledError:
            await asyncio.shield(future)
            raise

    def pair_rate_limit(self):
        now = time.monotonic()
        while self.pair_attempts and self.pair_attempts[0] <= now - 60:
            self.pair_attempts.popleft()
        if len(self.pair_attempts) >= PAIR_ATTEMPTS_PER_MINUTE:
            raise HostError(429, "rate_limited")
        self.pair_attempts.append(now)

    async def body(self, scope, receive, headers, *, multipart: bool) -> bytearray:
        limit = self.config.max_upload_mb * 1024 * 1024 + JSON_LIMIT if multipart else JSON_LIMIT
        length = headers.get("content-length")
        if length is not None:
            if not length.isdecimal():
                raise HostError(400, "invalid_request")
            if len(length) > 10 or int(length) > limit:
                raise HostError(413, "body_too_large")
        buffer, size = bytearray(), 0
        try:
            async with asyncio.timeout(BODY_DEADLINE):
                while True:
                    message = await receive()
                    if message["type"] == "http.disconnect":
                        raise HostError(400, "client_disconnected")
                    chunk = message.get("body", b"")
                    size += len(chunk)
                    if size > limit:
                        raise HostError(413, "body_too_large")
                    buffer.extend(chunk)
                    if not message.get("more_body", False):
                        break
        except TimeoutError:
            raise HostError(408, "body_timeout") from None
        if length is not None and size != int(length):
            raise HostError(400, "invalid_request")
        return buffer

    async def dispatch(self, scope, receive, headers, device):
        path, method = scope["path"], scope["method"]
        if (method, path) == ("GET", "/healthz"):
            return JSONResponse({"ok": True})
        if (method, path) == ("GET", "/pair"):
            return Response(self.assets["pair.html"], media_type="text/html")
        if (method, path) == ("GET", "/pair.js"):
            return Response(self.assets["pair.js"], media_type="text/javascript")
        if (method, path) == ("GET", "/api/v1/status"):
            return JSONResponse({"vault_loaded": True, "schema_ok": True,
                                 "grading_ready": self.runtime.grading_ready(), "host_version": HOST_VERSION})
        if (method, path) == ("GET", "/api/v1/meta"):
            # Mobile v2 §5.2: a cached app built against another allowlist offers a reload.
            # Mobile v2 §2.2: ``phone_plan`` says whether Today is the shared plan or M2a's queue.
            # Mobile v2 V3: ``phone_probes`` says whether the phone answers probes (the host's switch; the vault's
            # tag decides too, and a phone below it is told so by the replies themselves).
            return JSONResponse({"host_version": HOST_VERSION, "api_version": API_VERSION,
                                 "allowlist_digest": allowlist_digest(), "schema_version": self.schema_version,
                                 "phone_plan": self.config.phone_plan, "phone_probes": self.config.phone_probes})
        if (method, path) == ("GET", "/api/v1/queue-revision"):
            # Read-only, never the sidecar's get_queue_revision, which can reload (§3.1).
            value = await self.work(self.read_repo.queue_revision)
            return JSONResponse({"revision": value["revision"]})
        route = _route_of(method, path)[1]
        if route == "/api/v1/capture/{capture_id}":
            value = await self.work(capture.get_capture, self.read_repo, path.rsplit("/", 1)[1])
            # Status-only API, not a payload or media export.
            return JSONResponse({key: value[key] for key in ("capture_id", "status", "routed_to")
                                 if key in value})
        if route == "/api/v1/jobs/{job_id}":
            job = await self.work(self.runtime.job_status, path.rsplit("/", 1)[1])
            if job is None:
                raise HostError(404, "not_found")
            return JSONResponse(_status_body(job))
        if route == "/api/v1/submissions/{submission_id}":
            return JSONResponse(await self.work(self.runtime.submission_status, path.rsplit("/", 1)[1], device["device_id"]))
        if method in {"GET", "HEAD"} and _is_app_path(path):
            return await self.static_app(scope, path)
        if method != "POST" or path not in {"/pair", "/rpc", "/api/v1/capture"}:
            raise HostError(404, "not_found")
        content_type = headers.get("content-type", "").split(";", 1)[0].strip().lower()
        multipart = path == "/api/v1/capture" and content_type == "multipart/form-data"
        if content_type != "application/json" and not multipart:
            raise HostError(415, "unsupported_media_type")
        body = await self.body(scope, receive, headers, multipart=multipart)
        media = None
        if multipart:
            data, media = await self.capture_work(
                _multipart, scope, body, self.config.max_upload_mb * 1024 * 1024)
        else:
            data = await self.work(_json, body)
        del body  # Do not retain the multipart envelope during image decoding.
        if path == "/rpc":
            try:
                envelope = validate_envelope(data)
            except ValueError:
                raise HostError(400, "invalid_request") from None
            return await self.rpc(scope, envelope, device, probes=self._client_probes(headers))
        if path == "/pair":
            if set(data) - {"secret", "code", "device_label"}:
                raise HostError(400, "invalid_request")
            if sum(key in data for key in ("secret", "code")) != 1:
                raise HostError(400, "invalid_request")
            if any(not isinstance(value, str) or len(value) > 256 for value in data.values()):
                raise HostError(400, "invalid_request")
            return JSONResponse(await self.work(
                capture.exchange_pairing, self.repo, **data,
                tailscale_login=self.config.owner_login))
        allowed = {"client_capture_id", "kind", "text", "url", "note", "source_app", "captured_at"}
        if set(data) - allowed or not {"client_capture_id", "kind"} <= set(data):
            raise HostError(422, "validation_error")
        if any(not isinstance(value, str) for value in data.values()):
            raise HostError(422, "validation_error")
        if any(len(data.get(key, "").encode("utf-8")) > 64 * 1024 for key in ("text", "note")):
            raise HostError(413, "text_too_large")
        if multipart and data["kind"] != "image":
            raise HostError(422, "validation_error")
        result = await self.capture_work(capture.create_capture, self.repo, **data,
                                         media=media, device_id=device["device_id"], root=self.config.vault)
        created = result.pop("created")
        return JSONResponse(result, status_code=201 if created else 200)

    async def static_app(self, scope, path: str) -> Response:
        """The PWA's shell: identity-gated, no bearer, no vault data (§6.1). Never a fallback
        to anything outside the packaged directory (§4.6)."""

        if path == "/app":
            return RedirectResponse("/app/", status_code=307)
        files = StaticFiles(directory=self.app_dir, html=True, check_dir=False, follow_symlink=False)
        try:
            response = await files.get_response(path[len("/app/"):] or ".", scope)
        except (HTTPException, RuntimeError):
            raise HostError(404, "not_found") from None
        scope["learnloop.static"] = True
        return response

    def _client_probes(self, headers: dict[str, str]) -> bool:
        """The host's ``phone_probes`` for this request: the switch on AND the app saying it answers probes."""

        said = {part.strip() for part in headers.get(CLIENT_CAPABILITIES_HEADER, "").split(",")}
        return self.config.phone_probes and PHONE_PROBES_CAPABILITY in said

    async def rpc(self, scope, envelope: dict, device: dict, *, probes: bool = False) -> JSONResponse:
        """§6.2: allowlist, constraints, then a worker; the body the desktop client normalizes.

        ``probes``: the host's ``phone_probes`` for this request (:meth:`_client_probes`)."""

        name, params = envelope["method"], envelope.get("params", {})
        method = ALLOWLIST.get(name)
        if method is None:
            raise HostError(403, "method_not_allowed")
        scope["learnloop.log_endpoint"] = f"rpc:{name}"
        if name in PLAN_METHODS and not self.config.phone_plan:
            # Mobile v2 §2.2's kill switch: Today is M2a's queue, and the plan is the desktop's.
            return self._rpc_error("phone_plan_off", "Today's plan is on the desktop; the phone shows today's list.")
        if name in PROBE_METHODS and not probes:
            # Mobile v2 V3's kill switch, or an app that doesn't answer probes: the phone leaves every probe for the
            # desktop, as V2's did.
            return self._rpc_error("phone_probes_off", "This question is waiting for the desktop.")
        try:
            check_parameters(method, params)
            check_probe_parameters(name, params, phone_probes=probes)
        except ParamRejected as rejected:
            return self._rpc_error("validation_error", rejected.message, details={"field": rejected.field})
        timing: dict[str, float] = {}
        scope["learnloop.timing"] = timing
        try:
            validated = await self.work(self.runtime.validate, method, params)
            if method.kind == "long":
                timing["job_from"] = time.monotonic()
                try:
                    return await self._rpc_long(method, params, validated, envelope, device, probes=probes)
                finally:
                    timing["job_to"] = time.monotonic()
            timing["submitted"] = time.monotonic()
            future = self.runtime.call_short(method, params, device["device_id"], timing=timing, probes=probes)
            status, body = translate(await asyncio.wrap_future(future))
            return JSONResponse(body, status_code=status)
        except ParamsInvalid as invalid:
            return self._rpc_error("validation_error", "Invalid params.", details=invalid.details)
        except HostBusy:
            return self._rpc_error("host_busy", "The desktop is busy; try again in a moment.")
        except SessionOwnershipError as refused:
            return self._rpc_error(refused.code, refused.message, details=refused.details)

    async def _rpc_long(self, method, params, validated, envelope, device, *, probes: bool = False) -> JSONResponse:
        """§6.3: commit the job, wait up to 15 s, then the final answer or 202."""

        request_id = envelope.get("request_id")
        if not request_id:
            return self._rpc_error("validation_error", "A long request needs a request_id.")
        if method.name in {"submit_attempt", "submit_dont_know"} and request_id != str(validated["submission_id"]).strip():
            return self._rpc_error("validation_error", "A submit's request_id is its submission id.")
        if method.name == "trigger_regrade" and request_id != str(validated["contest_id"]).strip():
            # Mobile v2 V2: one contest, one job: a retry under its key records and queues it once.
            return self._rpc_error("validation_error", "A contest's request_id is its contest id.")
        try:
            job = await self.work(
                self.runtime.accept, method, params, validated, request_id=request_id, device_id=device["device_id"],
                probes=probes,
            )
        except capture.CaptureError as refused:
            return self._rpc_error(refused.code, refused.message)
        if not job.terminal:
            waiter = self.runtime.waiter(job.id)
            if waiter is not None:
                try:
                    job = await asyncio.wait_for(asyncio.shield(asyncio.wrap_future(waiter)), JOB_WAIT_SECONDS)
                except (TimeoutError, asyncio.TimeoutError):
                    pass  # A disconnect or a slow grade: the job runs on either way.
            else:
                # Finished between the acceptance and this line, or a stopping host's: the row knows.
                job = await self.work(self.runtime.job_status, job.id) or job
        return self._job_response(job)

    @staticmethod
    def _job_response(job: JobView) -> JSONResponse:
        if job.state == capture.COMPLETED:
            return JSONResponse({"ok": True, "result": job.result})
        if job.state in (capture.FAILED, capture.RECORDED):
            error = job.error or {}
            return JSONResponse({"ok": False, "error": error}, status_code=status_for(str(error.get("code"))))
        return JSONResponse(
            {"ok": True, "accepted": {"job_id": job.id, "request_id": job.request_id, "state": job.state}},
            status_code=202,
        )

    @staticmethod
    def _rpc_error(code: str, message: str, *, details: dict | None = None) -> JSONResponse:
        return JSONResponse(error_body(code, message, details=details), status_code=status_for(code))

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return
        started = time.monotonic()
        path = scope["path"]
        endpoint = (scope["method"], path)
        lane = "capture" if endpoint == ("POST", "/api/v1/capture") else "rpc" if endpoint == ("POST", "/rpc") else "short"
        admitted, log_admitted, media_admitted, device = False, False, False, None
        try:
            raw = scope.get("headers", [])
            if sum(len(k) + len(v) + 4 for k, v in raw) > HEADER_LIMIT:
                raise HostError(431, "headers_too_large")
            headers = {}
            for key, value in raw:
                name = key.decode("latin1").lower()
                if name in headers:
                    raise HostError(400, "duplicate_header")
                headers[name] = value.decode("latin1")
            if headers.get("host") != self.config.https_authority:
                raise HostError(403, "invalid_host")
            if "origin" in headers and headers["origin"] != self.config.base_url:
                raise HostError(403, "invalid_origin")
            health = (scope["method"], path) == ("GET", "/healthz")
            if not health and headers.get("tailscale-user-login") != self.config.owner_login:
                raise HostError(403, "invalid_identity")
            if self.active[lane] >= LANE_LIMITS[lane]:
                raise HostError(503, "host_busy")
            is_media = lane == "capture" and headers.get(
                "content-type", "").split(";", 1)[0].strip().lower() == "multipart/form-data"
            if is_media and self.active["media"] >= 1:
                raise HostError(503, "host_busy")
            self.active[lane] += 1
            admitted = True
            if is_media:
                self.active["media"] += 1
                media_admitted = True
            public = health or (path == "/pair" and scope["method"] in {"GET", "POST"}) or (
                path == "/pair.js" and scope["method"] == "GET") or (
                _is_app_path(path) and scope["method"] in {"GET", "HEAD"})
            if not public:
                auth = headers.get("authorization", "")
                if not auth.startswith("Bearer ") or not auth[7:] or " " in auth[7:]:
                    raise HostError(401, "unauthorized")
                required = ENDPOINT_SCOPES.get(_route_of(scope["method"], path))
                if required is None:
                    raise HostError(404, "not_found")
                device = await self.work(capture.authenticate_device, self.read_repo, auth[7:], scope=required)
            if endpoint == ("POST", "/pair"):
                # All pairing attempts share one bounded budget, including malformed bodies.
                self.pair_rate_limit()
            log_admitted = scope["method"] == "POST" and path in {"/pair", "/rpc", "/api/v1/capture"}
            if log_admitted and device:
                await self.work(capture.touch_device, self.repo, device["device_id"])
            response = await self.dispatch(scope, receive, headers, device)
        except HostError as exc:
            response = error_response(exc.status, exc.code, exc.message)
        except capture.CaptureError as exc:
            response = error_response(exc.status, exc.code, exc.message)
        except sqlite3.OperationalError:
            response = error_response(503, "database_busy")
        except HTTPException:
            response = error_response(400, "invalid_request")
        except Exception:
            # No exception text: parser/SQLite messages may contain submitted text.
            response = error_response(500, "internal")
        except BaseException:
            if admitted:
                self.active[lane] -= 1
            if media_admitted:
                self.active["media"] -= 1
            raise
        # Log only known mutations, with constant endpoint labels. Never query strings,
        # arbitrary RPC method names, unknown paths, or polling reads.
        try:
            if log_admitted:
                try:
                    if time.monotonic() - self.last_prune >= 86400:
                        await self.work(capture.prune_request_log, self.repo)
                        self.last_prune = time.monotonic()
                    await self.work(capture.log_request, self.repo, endpoint=scope.get("learnloop.log_endpoint", path),
                                    status=response.status_code, duration_ms=int((time.monotonic()-started)*1000),
                                    device_id=device["device_id"] if device else None)
                except Exception:
                    pass  # A log failure must not invalidate a committed receipt.
                if device is not None and endpoint == ("POST", "/rpc"):
                    sample = client_timing(headers.get(CLIENT_TIMING_HEADER))
                    if sample is not None:
                        try:
                            await self.work(_log_client_timing, self.repo, sample, device["device_id"])
                        except Exception:
                            pass  # A measurement never costs the request its answer.
            response.headers.update(SECURITY_HEADERS)
            if path == "/rpc":
                response.headers["Server-Timing"] = server_timing(scope.get("learnloop.timing"), time.monotonic() - started)
            if scope.get("learnloop.static"):
                # The shell revalidates by its ETag; the service worker caches it (§4.6).
                response.headers["Cache-Control"] = "no-cache"
            await response(scope, receive, send)
        finally:
            if admitted:
                self.active[lane] -= 1
            if media_admitted:
                self.active["media"] -= 1


def create_app(config: MobileConfig):
    host = MobileHost(config)

    @asynccontextmanager
    async def lifespan(app):
        await asyncio.to_thread(host.on_start)
        try:
            yield
        finally:
            await asyncio.to_thread(host.runtime.stop)
            host.executor.shutdown(wait=True)
            host.capture_executor.shutdown(wait=True)

    app = Starlette(lifespan=lifespan)
    app.state.host = host
    # Mounting at root passes exact paths through without redirect/fallback.
    app.mount("/", host)
    return app
