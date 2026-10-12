"""Bounded M1 ASGI capture host; never constructs a desktop runtime."""
from __future__ import annotations

import asyncio
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from functools import partial
import json
from pathlib import Path
import sqlite3
import time

from python_multipart.exceptions import MultipartParseError
from starlette.applications import Starlette
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException
from starlette.formparsers import MultiPartException
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from learnloop import capture
from learnloop.db.migrate import applied_versions, discover_migrations
from learnloop.db.repositories import Repository
from learnloop_mobile.allowlist import ALLOWLIST, validate_envelope
from learnloop_mobile.config import MobileConfig, sqlite_path

HEADER_LIMIT = 16 * 1024
JSON_LIMIT = 256 * 1024
BODY_DEADLINE = 60
ENDPOINT_SCOPES = {
    ("GET", "/api/v1/status"): "capture",
    ("POST", "/api/v1/capture"): "capture",
    ("GET", "/api/v1/capture/{capture_id}"): "capture",
    ("POST", "/rpc"): "app",
}
CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
       "img-src 'self' blob: data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
SECURITY_HEADERS = {
    "Cache-Control": "no-store", "Content-Security-Policy": CSP,
    "Referrer-Policy": "no-referrer", "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
}


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
            "Schema mismatch: open the desktop app or run learnloop doctor --vault "
            f"{config.vault} once to migrate"
        )
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


class MobileHost:
    def __init__(self, config: MobileConfig):
        if not config.enabled:
            raise SchemaMismatch("Mobile host is disabled; set enabled = true in mobile.toml")
        self.config = config
        self.repo = attach(config)
        self.read_repo = Repository.attach(self.repo.sqlite_path, read_only=True)
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="mobile-auth")
        self.capture_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="mobile-capture")
        self.active = {"short": 0, "capture": 0, "media": 0}
        self.rates: dict[str, tuple[deque, deque]] = {}
        self.last_prune = float("-inf")
        self.assets = {}
        for name in ("pair.html", "pair.js"):
            path = Path(__file__).with_name("static") / name
            if path.is_symlink() or not path.resolve().is_relative_to(Path(__file__).parent.resolve()):
                raise SchemaMismatch("Packaged assets must not be symlinks")
            self.assets[name] = path.read_bytes()

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

    def rate_limit(self, device: str, is_capture: bool):
        now = time.monotonic()
        # Bounded lifetime, keyed by durable device ids, never raw tokens.
        for key, (overall, captures) in list(self.rates.items()):
            for queue in (overall, captures):
                while queue and queue[0] <= now - 60:
                    queue.popleft()
            if not overall:
                del self.rates[key]
        overall, captures = self.rates.setdefault(device, (deque(), deque()))
        if len(overall) >= 120 or (is_capture and len(captures) >= 30):
            raise HostError(429, "rate_limited")
        overall.append(now)
        if is_capture:
            captures.append(now)

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
                                 "grading_ready": False, "host_version": "0.1.0"})
        if method == "GET" and path.startswith("/api/v1/capture/") and path.count("/") == 4:
            value = await self.work(capture.get_capture, self.read_repo, path.rsplit("/", 1)[1])
            # Status-only API, not a payload or media export.
            return JSONResponse({key: value[key] for key in ("capture_id", "status", "routed_to")
                                 if key in value})
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
            if envelope["method"] not in ALLOWLIST:
                raise HostError(403, "method_not_allowed")
            raise HostError(403, "method_not_allowed")  # No dispatch exists in M1.
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

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return
        started = time.monotonic()
        path = scope["path"]
        endpoint = (scope["method"], path)
        lane = "capture" if endpoint == ("POST", "/api/v1/capture") else "short"
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
            if headers.get("host") != self.config.hostname:
                raise HostError(403, "invalid_host")
            if "origin" in headers and headers["origin"] != f"https://{self.config.hostname}":
                raise HostError(403, "invalid_origin")
            health = (scope["method"], path) == ("GET", "/healthz")
            if not health and headers.get("tailscale-user-login") != self.config.owner_login:
                raise HostError(403, "invalid_identity")
            if self.active[lane] >= (2 if lane == "capture" else 16):
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
                path == "/pair.js" and scope["method"] == "GET")
            if not public:
                auth = headers.get("authorization", "")
                if not auth.startswith("Bearer ") or not auth[7:] or " " in auth[7:]:
                    raise HostError(401, "unauthorized")
                route = endpoint
                if scope["method"] == "GET" and path.startswith("/api/v1/capture/") and path.count("/") == 4:
                    route = ("GET", "/api/v1/capture/{capture_id}")
                required = ENDPOINT_SCOPES.get(route)
                if required is None:
                    raise HostError(404, "not_found")
                device = await self.work(capture.authenticate_device, self.read_repo, auth[7:], scope=required)
                self.rate_limit(device["device_id"], lane == "capture")
            if endpoint == ("POST", "/pair"):
                # All pairing attempts share one bounded budget, including malformed bodies.
                self.rate_limit("pair", True)
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
                    await self.work(capture.log_request, self.repo, endpoint=path,
                                    status=response.status_code, duration_ms=int((time.monotonic()-started)*1000),
                                    device_id=device["device_id"] if device else None)
                except Exception:
                    pass  # A log failure must not invalidate a committed receipt.
            response.headers.update(SECURITY_HEADERS)
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
        try:
            yield
        finally:
            host.executor.shutdown(wait=True)
            host.capture_executor.shutdown(wait=True)

    app = Starlette(lifespan=lifespan)
    app.state.host = host
    # Mounting at root passes exact paths through without redirect/fallback.
    app.mount("/", host)
    return app
