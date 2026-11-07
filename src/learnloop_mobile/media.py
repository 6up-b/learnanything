"""The host's read-only media lane (mobile v2 §5.1, stage V4): page images and stored images.

Two endpoints, both ``GET`` under ``Token(app)``, both content-addressed and immutable:

* ``/api/v1/reader/page/{ref}/{page}?w={px}`` (§3.3): one page of a book's original PDF as a PNG,
  rendered here with pypdfium2. ``ref`` is a reading (an extraction id, which names one revision and
  so one file) or the file itself (``sha256-<hex>``, the originals store's name, which an ``llpdf://``
  link names, §2.3). ``page`` is zero-based, as the reading's blocks carry it. ``w`` is snapped to
  :data:`PAGE_WIDTHS`.
* ``/api/v1/assets/{sha256-<hex>}`` (§2.3): a stored image (PNG, JPEG, GIF, WebP) as itself. Never a
  PDF: a PDF leaves the host only as page images.

What leaves here is decided by the same predicate as the phone's text and its eligibility
(``learnloop.reader.phone_media``; a page by either of its names is decided by every reading of its file):
nothing of a reading exam material covers whole, no page that holds a passage it covers, nothing of a book
opted out of the Reader, no page the reading does not cover, and nothing of another vault (the host is
pinned to one, and every id resolves only in its database). The predicate is read at every request, a
render cached or not, so a mark made on the desktop withholds the next request on.

The lane needs no ``SidecarContext``: it reads through the host's read-only attach, the vault's files
(a settled snapshot, as a secondary loads them, for the source sets protection reads) and the originals
store. It writes only its own cache, outside the vault (``MobileConfig.page_cache_root``), keyed by the
vault, the file's hash, the page and the width.
"""
from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
import re
import threading
from typing import Any
import uuid

LOG = logging.getLogger(__name__)

#: §3.3: the widths a page renders at, so the cache stays bounded. A ``keep`` bound (two sizes: a phone's
#: column at 2x and at 3x), not a decision parameter.
PAGE_WIDTHS = (720, 1080)
DEFAULT_PAGE_WIDTH = 1080
#: The rendered-page cache's size on disk. A ``keep`` bound: past it the oldest renders go, and a request for
#: one renders it again.
PAGE_CACHE_BYTES = 512 * 1024 * 1024
#: §5.1: requests in flight on the media lane; beyond it ``503 host_busy``. A ``keep`` bound.
MEDIA_LANE_LIMIT = 8
#: Threads that render (pdfium is serialized by its lock, so more would only queue). A ``keep`` bound.
MEDIA_WORKERS = 2
#: The largest page index the endpoint parses (a guard on the path, not a book's length).
MAX_PAGE = 99_999
#: The largest stored image served (the upload cap of a capture, mobile spec §4.4); one definition with the
#: phone's eligibility.
from learnloop.reader.phone_media import MAX_ASSET_BYTES  # noqa: E402
#: Responses here name their content, so they may be kept (§3.3, the stated exception to ``no-store``).
IMMUTABLE = "private, max-age=31536000, immutable"

_STORE_NAME = re.compile(r"sha256-([0-9a-f]{64})")
_EXTRACTION_ID = re.compile(r"[A-Za-z0-9_.:-]{1,128}")


class MediaRefused(Exception):
    """A media request the host refuses: its HTTP status and stable code."""

    def __init__(self, status: int, code: str, message: str = ""):
        super().__init__(message or code)
        self.status, self.code, self.message = status, code, message or code


def snap_width(requested: str | None) -> int:
    """The served width for ``?w=``: the smallest of :data:`PAGE_WIDTHS` at least as wide, else the largest."""

    if requested is None or requested == "":
        return DEFAULT_PAGE_WIDTH
    if not requested.isdecimal() or len(requested) > 5:
        raise MediaRefused(400, "invalid_request", "w must be a width in pixels")
    wanted = int(requested)
    return next((width for width in PAGE_WIDTHS if width >= wanted), PAGE_WIDTHS[-1])


def parse_page(value: str) -> int:
    if not value.isdecimal() or len(value) > 5 or int(value) > MAX_PAGE:
        raise MediaRefused(404, "not_found")
    return int(value)


class MediaLane:
    """The lane's state: the host's read-only repository, a protection snapshot of the vault, the cache."""

    def __init__(self, vault_root: Path, read_repo: Any, cache_root: Path):
        self.vault_root = Path(vault_root)
        self.repo = read_repo
        self.cache_root = Path(cache_root)
        #: The vault the cache's entries belong to (per vault, §3.3): two hosts on two vaults never share one.
        self.vault_key = hashlib.sha256(str(self.vault_root.resolve()).encode("utf-8")).hexdigest()[:16]
        self._snapshot: tuple[str, Any] | None = None
        self._snapshot_lock = threading.Lock()
        self._prune_lock = threading.Lock()

    # -- protection --------------------------------------------------------------------------

    def _vault(self) -> Any:
        """A settled snapshot of the vault's files (its config and source sets), reloaded when they change.
        One that can't settle (a writer mid-rewrite) refuses the request: protection is never read off a
        half-written source-sets file."""

        from learnloop.vault.loader import load_vault, settled_load_vault, vault_content_fingerprint

        fingerprint = vault_content_fingerprint(self.vault_root)
        with self._snapshot_lock:
            if self._snapshot is not None and self._snapshot[0] == fingerprint:
                return self._snapshot[1]
        loaded = settled_load_vault(self.vault_root, load=lambda root: load_vault(root, load_environment=False),
                                    fingerprint=fingerprint)
        if not loaded.settled:
            raise MediaRefused(503, "vault_unsettled", "The vault's files were changing; try again in a moment.")
        with self._snapshot_lock:
            self._snapshot = (str(loaded.fingerprint), loaded.vault)
        return loaded.vault

    @staticmethod
    def _refuse(refusal: Any) -> None:
        if refusal is not None:
            raise MediaRefused(refusal.status, refusal.code, refusal.message)

    # -- the page endpoint --------------------------------------------------------------------

    def page(self, ref: str, page: int, width: int) -> tuple[bytes, str, str]:
        """``(body, content type, etag)`` of one page, or :class:`MediaRefused`.

        Either name resolves to the file first, and then every reading of that file decides (Codex review of V4,
        F3): a page refused by its file's name is refused by any reading's id too. The predicate is
        ``learnloop.reader.phone_media.page_refusal``, which the phone's eligibility reads as well (F10)."""

        from learnloop.reader import phone_media as PM

        vault = self._vault()
        store = _STORE_NAME.fullmatch(ref)
        if store is not None:
            digest: str | None = f"sha256:{store.group(1)}"
        elif _EXTRACTION_ID.fullmatch(ref):
            digest = PM.digest_of_reading(self.repo, ref)
        else:
            digest = None
        if digest is None:
            raise MediaRefused(404, "not_found")
        self._refuse(PM.page_refusal(vault, self.repo, digest, page))
        from learnloop.ingest.originals import stored_original_path

        path = stored_original_path(self.vault_root, digest)
        if path is None:
            raise MediaRefused(404, "not_found", "The original isn't on this computer.")
        hexdigest = digest.split(":", 1)[1]
        body = self._cached_render(path, hexdigest, page, width)
        return body, "image/png", f'"{hexdigest[:20]}-{page}-{width}"'

    def _cache_path(self, hexdigest: str, page: int, width: int) -> Path:
        return self.cache_root / self.vault_key / hexdigest / f"{page}-{width}.png"

    def _cached_render(self, path: Path, hexdigest: str, page: int, width: int) -> bytes:
        cached = self._cache_path(hexdigest, page, width)
        try:
            return cached.read_bytes()
        except FileNotFoundError:
            pass
        except OSError:
            LOG.warning("page cache unreadable at %s", cached, exc_info=True)
        body = render_page_png(path, page, width)
        if body is None:
            raise MediaRefused(404, "not_found")
        self._store(cached, body)
        return body

    def _store(self, cached: Path, body: bytes) -> None:
        try:
            cached.parent.mkdir(parents=True, exist_ok=True)
            tmp = cached.with_name(f"{cached.name}.{uuid.uuid4().hex}.tmp")
            tmp.write_bytes(body)
            os.replace(tmp, cached)
        except OSError:
            LOG.warning("page not cached at %s", cached, exc_info=True)
            return
        self._prune()

    def _prune(self) -> None:
        """Keep the cache under :data:`PAGE_CACHE_BYTES`, oldest renders first."""

        if not self._prune_lock.acquire(blocking=False):
            return
        try:
            files = []
            total = 0
            for found in self.cache_root.rglob("*.png"):
                try:
                    stat = found.stat()
                except OSError:
                    continue
                files.append((stat.st_mtime, stat.st_size, found))
                total += stat.st_size
            if total <= PAGE_CACHE_BYTES:
                return
            for _mtime, size, found in sorted(files):
                if total <= PAGE_CACHE_BYTES:
                    break
                try:
                    found.unlink()
                    total -= size
                except OSError:
                    continue
        finally:
            self._prune_lock.release()

    # -- the asset endpoint ------------------------------------------------------------------

    def asset(self, name: str) -> tuple[bytes, str, str]:
        """``(body, content type, etag)`` of one stored image, or :class:`MediaRefused`."""

        from learnloop.ingest.originals import stored_original_path
        from learnloop.reader import phone_media as PM
        from learnloop.scheduling.device_eligibility import image_kind

        store = _STORE_NAME.fullmatch(name)
        if store is None:
            raise MediaRefused(404, "not_found")
        digest = f"sha256:{store.group(1)}"
        # The phone's eligibility reads the same predicate (F10).
        self._refuse(PM.asset_refusal(self._vault(), self.repo, digest))
        path = stored_original_path(self.vault_root, digest)
        try:
            with path.open("rb") as handle:  # type: ignore[union-attr]
                body = handle.read(MAX_ASSET_BYTES + 1)
        except (AttributeError, OSError):
            raise MediaRefused(404, "not_found") from None
        kind = image_kind(body[:12])
        if kind is None or len(body) > MAX_ASSET_BYTES:
            raise MediaRefused(404, "not_found")
        return body, kind, f'"{store.group(1)[:20]}"'


def render_page_png(path: Path, page: int, width: int) -> bytes | None:
    """One page of a PDF as a PNG ``width`` pixels wide, or None (no such page, or it can't be drawn). Under
    the Reader's pdfium lock (``span_view``), which every pdfium call in this process shares."""

    import io

    from learnloop.reader.span_view import _pdf_page

    try:
        import pypdfium2  # noqa: F401 - the renderer's own import, checked first so its absence is said plainly
    except ImportError:
        # The host's environment lacks the renderer (it comes with the pdf and glm-ocr extras): a typed refusal
        # the doctor and the phone can name, never a 404 that looks like a missing page.
        raise MediaRefused(503, "pages_unavailable", "Page images need pypdfium2 on the desktop.") from None
    try:
        with _pdf_page(path, int(page)) as pdf_page:
            if pdf_page is None:
                return None
            points = float(pdf_page.get_size()[0]) or 1.0
            bitmap = pdf_page.render(scale=max(width / points, 0.1))
            try:
                output = io.BytesIO()
                bitmap.to_pil().save(output, format="PNG", optimize=True)
            finally:
                bitmap.close()
        return output.getvalue()
    except Exception:  # noqa: BLE001 - a page that can't be drawn is not served, never a 500
        LOG.warning("page %s of %s not rendered", page, path, exc_info=True)
        return None
