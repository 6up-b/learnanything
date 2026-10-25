"""Durable reference-only capture, with no ingestion or practice side effects."""

from __future__ import annotations

import base64
import hashlib
import io
import json
import re
import warnings
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image, ImageOps, UnidentifiedImageError

from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.ingest.originals import canonical_source_raw_path, store_original_bytes

from .devices import _now
from .errors import CaptureError

_ULID = re.compile(r"[0-7][0-9A-HJKMNP-TV-Z]{25}\Z")
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
PREVIEW_MAX_SIDE = 2048
_ARXIV = re.compile(r"(?:arXiv:)?(?:\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Z]{2})?/\d{7})(?:v[1-9]\d*)?\Z")
_SELECT = """SELECT i.*,r.state,r.route,r.routed_at,r.dismissed_at,r.result_refs_json,
                    r.media_delete_pending,r.media_retained_shared,
                    CASE WHEN r.intent_json IS NOT NULL THEN r.intent_route END AS pending_route
             FROM capture_inbox i JOIN capture_routes r ON r.capture_id=i.id"""


def validate_url(value: str) -> None:
    """Accept references, never local source paths; this function fetches nothing."""
    if _ARXIV.fullmatch(value):
        return
    try:
        parsed = urlsplit(value)
        valid = (
            parsed.scheme in ("http", "https") and bool(parsed.hostname)
            and parsed.username is None and parsed.password is None
            and not any(c.isspace() or ord(c) < 32 for c in value)
            and "\\" not in value
        )
        _ = parsed.port
    except ValueError:
        valid = False
    if not valid:
        raise CaptureError("validation_error", 422, "URL must be HTTP(S) or an arXiv identifier")


def sanitize_image(raw: bytes) -> tuple[bytes, str]:
    """Decode before trusting MIME; orientation survives, ancillary data does not."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as image:
                if image.format not in ("JPEG", "PNG", "WEBP"):
                    raise CaptureError("unsupported_media", 415, "Use JPEG, PNG or WebP")
                if image.width * image.height > 40_000_000:
                    raise CaptureError("image_too_large", 413, "Decoded image exceeds 40 megapixels")
                image.load()
                ImageOps.exif_transpose(image, in_place=True)
                mode = "RGBA" if "A" in image.getbands() or "transparency" in image.info else "RGB"
                converted = image if image.mode == mode else image.convert(mode)
                # A fresh pixel-only image cannot inherit EXIF, XMP, ICC or comments.
                clean = Image.new(mode, converted.size)
                clean.paste(converted)
                output = io.BytesIO()
                clean.save(output, format="PNG")
                return output.getvalue(), "image/png"
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise CaptureError("image_too_large", 413, "Decoded image exceeds the safety limit") from exc
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        if isinstance(exc, CaptureError):
            raise
        raise CaptureError("unsupported_media", 415, "Invalid or unsupported image") from exc


def _json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _decode(row) -> dict:
    value = dict(row)
    value["capture_id"] = value["id"]
    value["status"] = "purged" if value["purged_at"] else value["state"]
    # An unfinished desktop save (route intent without a recorded route).
    if value["status"] != "new":
        value["pending_route"] = None
    value["media_delete_pending"] = bool(value["media_delete_pending"])
    value["media_retained_shared"] = bool(value["media_retained_shared"])
    value["result_refs"] = json.loads(value.pop("result_refs_json") or "{}")
    value["routed_to"] = (
        dict(route=value["route"], result_refs=value["result_refs"])
        if value["state"] == "routed" else None
    )
    return value


def create_capture(
    repo: Repository, *, client_capture_id: str, kind: str,
    text: str | None = None, url: str | None = None, note: str | None = None,
    source_app: str | None = None, captured_at: str | None = None,
    media: bytes | None = None, device_id: str | None = None,
    root: Path | None = None,
) -> dict:
    if not isinstance(client_capture_id, str) or not _ULID.fullmatch(client_capture_id):
        raise CaptureError("validation_error", 422, "client_capture_id must be a canonical ULID")
    if kind not in ("text", "url", "image"):
        raise CaptureError("validation_error", 422, "Unknown capture kind")
    fields = dict(kind=kind, text=text, url=url, note=note, source_app=source_app, captured_at=captured_at)
    for key, value in fields.items():
        if value is not None and not isinstance(value, str):
            raise CaptureError("validation_error", 422, f"{key} must be text")
    if sum(len((value or "").encode("utf-8")) for value in (text, note)) > 65536:
        raise CaptureError("body_too_large", 413, "Capture text exceeds 64 KiB")
    if (url and len(url.encode("utf-8")) > 8192) or (source_app and len(source_app) > 200):
        raise CaptureError("validation_error", 422, "Capture metadata is too long")
    if captured_at is not None:
        try:
            timestamp = datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                raise ValueError
        except ValueError as exc:
            raise CaptureError("validation_error", 422, "captured_at must include a timezone") from exc
    if kind == "text" and (not text or not text.strip()):
        raise CaptureError("validation_error", 422, "Text capture is empty")
    if kind == "url" and not url:
        raise CaptureError("validation_error", 422, "URL capture needs a URL")
    if url:
        validate_url(url)
    if kind == "image" and not media:
        raise CaptureError("validation_error", 422, "Image capture needs media")
    if kind != "image" and media is not None:
        raise CaptureError("validation_error", 422, "Only image captures accept media")
    if media is not None and not isinstance(media, bytes):
        raise CaptureError("validation_error", 422, "Media must be bytes")
    # A length-delimited canonical manifest plus RAW bytes binds metadata even
    # when re-encoding would discard it. Authentication is deliberately excluded:
    # an outbox retry after re-pairing is the same capture.
    manifest = _json(fields).encode("utf-8")
    fingerprint = hashlib.sha256(len(manifest).to_bytes(8, "big") + manifest + (media or b"")).hexdigest()
    root = Path(root) if root is not None else repo.sqlite_path.parent
    # Decode/re-encode before acquiring SQLite's writer reservation. At most one
    # host media task runs concurrently; desktop scheduling can still write here.
    with repo.connection() as conn:
        existing = conn.execute("SELECT id,request_sha256 FROM capture_inbox WHERE client_capture_id=?",
                                (client_capture_id,)).fetchone()
    if existing:
        if existing["request_sha256"] != fingerprint:
            raise CaptureError("capture_conflict", 409, "Capture id was already used for another request")
        return dict(capture_id=existing["id"], status="received", created=False)
    digest = mime = sanitized = None
    if media is not None:
        sanitized, mime = sanitize_image(media)
        digest = "sha256:" + hashlib.sha256(sanitized).hexdigest()
    with repo.atomic(), repo.connection() as conn:
        existing = conn.execute("SELECT id,request_sha256 FROM capture_inbox WHERE client_capture_id=?",
                                (client_capture_id,)).fetchone()
        if existing:
            if existing["request_sha256"] != fingerprint:
                raise CaptureError("capture_conflict", 409, "Capture id was already used for another request")
            # Retry must not recreate media or restore content after purge.
            return dict(capture_id=existing["id"], status="received", created=False)
        # File publication stays inside the short writer reservation so purge
        # cannot unlink bytes between storage and publishing their reference.
        # Canonical-source registration takes the same reservation.
        if sanitized is not None:
            store_original_bytes(root, digest, sanitized)
        capture_id = new_ulid()
        conn.execute(
            """INSERT INTO capture_inbox
               (id,client_capture_id,device_id,kind,text,url,note,media_sha256,media_mime,
                source_app,request_sha256,captured_at,received_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (capture_id, client_capture_id, device_id, kind, text, url, note, digest, mime,
             source_app, fingerprint, captured_at, _now().isoformat()),
        )
        conn.execute("INSERT INTO capture_routes(capture_id,state) VALUES (?,'new')", (capture_id,))
    return dict(capture_id=capture_id, status="received", created=True)


def get_capture(repo: Repository, capture_id: str) -> dict:
    with repo.connection() as conn:
        row = conn.execute(_SELECT + " WHERE i.id=?", (capture_id,)).fetchone()
    if row is None:
        raise CaptureError("not_found", 404, "Capture not found")
    return _decode(row)


def list_captures(
    repo: Repository, *, status: str | None = None, limit: int = 100, offset: int = 0,
) -> list[dict]:
    if status not in (None, "new", "routed", "dismissed", "processing", "failed", "purged",
                      "delete_pending"):
        raise CaptureError("validation_error", 422, "Unknown capture status")
    if not 1 <= limit <= 500 or offset < 0:
        raise CaptureError("validation_error", 422, "Invalid inbox page")
    where, args = "", []
    if status == "purged":
        where = " WHERE i.purged_at IS NOT NULL"
    elif status == "delete_pending":
        where = " WHERE r.media_delete_pending=1"
    elif status is not None:
        where, args = " WHERE r.state=? AND i.purged_at IS NULL", [status]
    with repo.connection() as conn:
        rows = conn.execute(_SELECT + where + " ORDER BY i.received_at DESC,i.id DESC LIMIT ? OFFSET ?",
                            (*args, limit, offset)).fetchall()
    return [_decode(row) for row in rows]


def get_inbox_summary(repo: Repository) -> dict:
    """New captures plus every capture whose media deletion is still pending.

    Deletion-pending captures are surfaced here, not only in the paged handled
    listing, so a failed unlink is never buried behind newer captures.
    """
    with repo.connection() as conn:
        count = conn.execute(
            """SELECT count(*) FROM capture_inbox i JOIN capture_routes r ON i.id=r.capture_id
               WHERE r.state='new' AND i.purged_at IS NULL"""
        ).fetchone()[0]
        pending = conn.execute(
            "SELECT count(*) FROM capture_routes WHERE media_delete_pending=1"
        ).fetchone()[0]
    return dict(count=count, new_count=count, captures=list_captures(repo, status="new", limit=20),
                delete_pending=list_captures(repo, status="delete_pending", limit=100),
                delete_pending_count=pending)


def route_capture(repo: Repository, capture_id: str, *, route: str, result_refs) -> dict:
    if route not in ("make_card", "quick_add", "ask_tutor", "photo_to_item"):
        raise CaptureError("validation_error", 422, "Unknown capture route")
    if not isinstance(result_refs, (dict, list)) or not result_refs:
        raise CaptureError("validation_error", 422, "A successful route must name its result")
    refs = _json(result_refs)
    with repo.atomic(), repo.connection() as conn:
        capture = get_capture(repo, capture_id)
        if capture["purged_at"]:
            raise CaptureError("capture_conflict", 409, "Capture was purged")
        if capture["state"] == "routed":
            if capture["route"] != route or _json(capture["result_refs"]) != refs:
                raise CaptureError("capture_conflict", 409, "Capture already has a different route")
        else:
            conn.execute(
                "UPDATE capture_routes SET state='routed',route=?,result_refs_json=?,routed_at=? WHERE capture_id=?",
                (route, refs, _now().isoformat(), capture_id),
            )
        return get_capture(repo, capture_id)


def photo_for_practice_item(repo: Repository, practice_item_id: str) -> dict | None:
    """The phone photo a card was written from (Reader CA1, *your photo*): the
    reverse of a routed capture's link, read from its ``result_refs_json``.

    Only a photo capture routed to this item whose media is still held (not
    purged, no deletion pending); the latest when several were. A read: the
    photo itself is served by :func:`capture_media_preview`, from its hash."""

    with repo.connection() as conn:
        row = conn.execute(
            """SELECT i.id, i.captured_at, i.received_at FROM capture_inbox i
                 JOIN capture_routes r ON r.capture_id = i.id
                WHERE r.state = 'routed' AND r.route IN ('make_card', 'photo_to_item')
                  AND i.kind = 'image' AND i.media_sha256 IS NOT NULL AND i.purged_at IS NULL
                  AND r.media_delete_pending = 0
                  AND json_type(r.result_refs_json) = 'object'
                  AND json_extract(r.result_refs_json, '$.practice_item_id') = ?
                ORDER BY r.routed_at DESC, i.id DESC LIMIT 1""",
            (practice_item_id,),
        ).fetchone()
    if row is None:
        return None
    return dict(capture_id=row["id"], captured_at=row["captured_at"] or row["received_at"])


def dismiss_capture(repo: Repository, capture_id: str) -> dict:
    with repo.atomic(), repo.connection() as conn:
        capture = get_capture(repo, capture_id)
        if capture["state"] == "routed" or capture["purged_at"]:
            raise CaptureError("capture_conflict", 409, "A routed or purged capture cannot be dismissed")
        conn.execute("UPDATE capture_routes SET state='dismissed',dismissed_at=? WHERE capture_id=?",
                     (_now().isoformat(), capture_id))
        return get_capture(repo, capture_id)


def _referenced(conn, digest: str) -> bool:
    return bool(
        conn.execute("SELECT 1 FROM capture_inbox WHERE media_sha256=? AND purged_at IS NULL LIMIT 1",
                     (digest,)).fetchone()
        or conn.execute("SELECT 1 FROM source_revisions WHERE asset_hash=? LIMIT 1", (digest,)).fetchone()
    )


def purge_capture(repo: Repository, capture_id: str, *, root: Path | None = None) -> dict:
    """Erase capture payload but preserve its fingerprint tombstone and provenance.

    The digest remains on the tombstone so a failed unlink can be retried. Shared
    originals are retained, explicitly reported, never removed out from under
    another capture or canonical source.
    """
    root = Path(root) if root is not None else repo.sqlite_path.parent
    with repo.atomic(), repo.connection() as conn:
        capture = get_capture(repo, capture_id)
        conn.execute(
            """UPDATE capture_inbox SET text=NULL,url=NULL,note=NULL,source_app=NULL,
               purged_at=COALESCE(purged_at,?) WHERE id=?""",
            (_now().isoformat(), capture_id),
        )
        conn.execute(
            """UPDATE capture_routes SET media_delete_pending=?,media_retained_shared=0,
               intent_json=NULL WHERE capture_id=?""",
            (int(bool(capture["media_sha256"])), capture_id),
        )
    # Payload erasure must commit even if the filesystem refuses deletion.
    # Serialize the reference check and unlink against new capture publication.
    retained = False
    deletion_error = False
    with repo.atomic(), repo.connection() as conn:
        digest = capture["media_sha256"]
        if digest:
            retained = _referenced(conn, digest)
            if not retained:
                try:
                    canonical_source_raw_path(root, digest).unlink(missing_ok=True)
                except OSError:
                    deletion_error = True
        conn.execute(
            "UPDATE capture_routes SET media_delete_pending=?,media_retained_shared=? WHERE capture_id=?",
            (int(deletion_error), int(retained), capture_id),
        )
        result = get_capture(repo, capture_id)
    result.update(media_retained_shared=retained, media_delete_pending=deletion_error)
    return result


def capture_media_preview(
    repo: Repository, capture_id: str, *, root: Path | None = None,
    max_side: int = PREVIEW_MAX_SIDE,
) -> dict:
    """Desktop-only, read-only bounded preview of a photo capture.

    The file is resolved from the capture's stored content hash alone, never a
    caller-supplied path, and its bytes must still hash to that value.
    """
    root = Path(root) if root is not None else repo.sqlite_path.parent
    capture = get_capture(repo, capture_id)
    if capture["kind"] != "image":
        raise CaptureError("validation_error", 422, "Only photo captures have an image")
    if capture["purged_at"]:
        raise CaptureError("capture_conflict", 409, "Capture was purged")
    digest = capture["media_sha256"] or ""
    if not _DIGEST.fullmatch(digest):
        raise CaptureError("not_found", 404, "The captured photo is unavailable")
    try:
        raw = canonical_source_raw_path(root, digest).read_bytes()
    except OSError:
        raise CaptureError("not_found", 404, "The captured photo is missing from the originals store") from None
    if "sha256:" + hashlib.sha256(raw).hexdigest() != digest:
        raise CaptureError("not_found", 404, "The captured photo no longer matches its stored hash")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as image:
                original = image.size
                image.thumbnail((max_side, max_side))
                alpha = "A" in image.getbands()
                output = io.BytesIO()
                if alpha:
                    image.save(output, format="PNG")
                else:
                    image.convert("RGB").save(output, format="JPEG", quality=85)
                size = image.size
    except (Image.DecompressionBombError, Image.DecompressionBombWarning, UnidentifiedImageError,
            OSError, ValueError):
        raise CaptureError("not_found", 404, "The captured photo cannot be decoded") from None
    mime = "image/png" if alpha else "image/jpeg"
    return dict(
        capture_id=capture_id, mime=mime, width=size[0], height=size[1],
        original_width=original[0], original_height=original[1],
        data_url=f"data:{mime};base64," + base64.b64encode(output.getvalue()).decode("ascii"),
    )


def report_orphan_originals(repo: Repository, *, root: Path | None = None) -> list[str]:
    """Read-only reporting: never remove unknown files from the shared store."""
    root = Path(root) if root is not None else repo.sqlite_path.parent
    with repo.connection() as conn:
        return sorted(
            str(path.relative_to(root))
            for path in (root / "canonical-sources" / "raw").glob("sha256-*")
            if path.is_file() and re.fullmatch(r"sha256-[a-f0-9]{64}", path.name)
            and not _referenced(conn, path.name.replace("sha256-", "sha256:", 1))
        )
