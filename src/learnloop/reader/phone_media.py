"""Mobile v2 stage V4: what of a reading, a page or a stored image the phone may be sent (spec §2.3, §3.3).

One predicate for every phone path, so they can't disagree (Codex review of V4, F3 and F10):

* :func:`phone_withheld`: what exam material covers of one reading (the phone's text, its guide, its Ask
  history, and the pages below);
* :func:`page_refusal`: whether the host's page endpoint serves one page of a stored PDF, which every
  reading of that file decides together, whichever name the request used (a reading's id or the file's);
* :func:`asset_refusal`: the same for a stored image.

The host's media lane (``learnloop_mobile.media``) answers with these refusals, and the phone's eligibility
(``scheduling.device_eligibility.media_served``) lifts a prompt's image, page or asset reason only when every
target is served by them, so an item is never admitted on the phone with a stimulus the host then refuses.

Nothing here writes, and the desktop (a None origin) never asks.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Iterable

# Module level, so the reader's cross-domain edges stay the architecture's frozen inventory: exam material decides
# protection, and the eligibility's sniff decides what is an image.
from learnloop.content.sources.exam_material import HELD_OUT_REFUSAL, exam_material, held_out_refusal
from learnloop.scheduling.device_eligibility import image_kind

LOG = logging.getLogger(__name__)

#: The largest stored image served (the upload cap of a capture, mobile spec §4.4). A ``keep`` bound.
MAX_ASSET_BYTES = 20 * 1024 * 1024


@dataclass(frozen=True)
class PhoneWithheld:
    """What of one reading the phone may not be sent."""

    #: The whole reading: nothing of it reaches the phone.
    whole: bool
    #: The passages, when the reading is not withheld whole.
    spans: frozenset[str]
    #: The plain refusal the desktop's model paths give, or None.
    message: str | None

    def covers(self, span_id: str | None) -> bool:
        return self.whole or (span_id is not None and str(span_id) in self.spans)

    def any(self, span_ids: Iterable[str | None]) -> bool:
        return self.whole or any(self.covers(span) for span in span_ids)

    def as_protection(self, desktop: dict[str, Any] | None) -> dict[str, Any]:
        """The ``protection`` key a phone reads: the desktop's held-out partition widened to
        every passage withheld here, so a selection on any of them offers no model action."""

        held = list((desktop or {}).get("held_out_span_ids") or [])
        merged = list(dict.fromkeys([*held, *sorted(self.spans)]))
        whole = self.whole or bool((desktop or {}).get("withheld"))
        message = self.message or (desktop or {}).get("message")
        return {"withheld": whole, "held_out_span_ids": [] if whole else merged,
                "message": message if (whole or merged) else None}


def phone_withheld(vault_or_sets: Any, repository: Any, extraction_id: str,
                   span_ids: Iterable[str | None] = ()) -> PhoneWithheld:
    """What exam material (rules 1-4, the held-out partition included) covers of
    ``extraction_id``, among ``span_ids``. A predicate that can't be read withholds the whole
    reading (fail closed)."""

    extraction = str(extraction_id)
    try:
        material = exam_material(vault_or_sets, repository)
    except Exception:  # noqa: BLE001 - fail closed: an unreadable predicate sends nothing
        LOG.exception("exam material unreadable for %s", extraction)
        return PhoneWithheld(whole=True, spans=frozenset(), message=HELD_OUT_REFUSAL)
    if material.covers(extraction):
        return PhoneWithheld(whole=True, spans=frozenset(), message=held_out_refusal(material.material, extraction))
    spans = frozenset(str(span) for span in span_ids if span and material.covers(extraction, str(span)))
    message = held_out_refusal(material.material, extraction) if spans else None
    return PhoneWithheld(whole=False, spans=spans, message=message)


@dataclass(frozen=True)
class MediaRefusal:
    """Why the host does not serve a page or an image: its HTTP status, stable code and plain line."""

    status: int
    code: str
    message: str


NOT_FOUND = MediaRefusal(404, "not_found", "not_found")


def _held_out(withheld: PhoneWithheld) -> MediaRefusal:
    return MediaRefusal(403, "held_out_material", withheld.message or "This page is held out.")


def readings_of_file(repository: Any, digest: str) -> list[str]:
    """Every completed reading of the stored file ``digest`` (``sha256:<hex>``), whatever source it belongs to."""

    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT r.id FROM source_extraction_runs r JOIN source_revisions v ON v.id = r.revision_id "
            "WHERE v.asset_hash = ? AND r.status = 'completed' ORDER BY r.id", (digest,),
        ).fetchall()
    return [str(row[0]) for row in rows]


def digest_of_reading(repository: Any, extraction_id: str) -> str | None:
    """The stored file a completed reading was made from (``sha256:<hex>``), or None."""

    run = repository.get_extraction_run(extraction_id)
    if run is None or run.get("status") != "completed" or not run.get("revision_id"):
        return None
    revision = repository.get_source_revision(str(run["revision_id"]))
    digest = str((revision or {}).get("asset_hash") or "")
    return digest if digest.startswith("sha256:") else None


def _reader_source_ok(repository: Any, source_id: Any) -> bool:
    artifact = repository.get_source_artifact(str(source_id)) if source_id else None
    return artifact is not None and bool(artifact.get("reader_enabled", 1))


def page_refusal(vault: Any, repository: Any, digest: str, page: int) -> MediaRefusal | None:
    """Why page ``page`` (zero-based) of the stored PDF ``digest`` is not served to the phone, or None.

    Every reading of the file decides (F3): one held out whole, or holding a passage on that page, withholds the
    page whichever URL named it; a book opted out of the Reader serves nothing; and only a page some reading
    covers is served (an answer key at the back of a book read only in part is not known to be safe). The file
    must be on this computer and the renderer installed."""

    from learnloop.reader import reader_dialogue as RD

    if not RD.reader_enabled(vault) or not str(digest).startswith("sha256:"):
        return NOT_FOUND
    readings = readings_of_file(repository, digest)
    if not readings:
        return NOT_FOUND
    covered = False
    for reading in readings:
        run = repository.get_extraction_run(reading)
        revision = repository.get_source_revision(str(run["revision_id"])) if run and run.get("revision_id") else None
        if revision is None or not _reader_source_ok(repository, revision.get("source_id")):
            return NOT_FOUND
        blocks = repository.document_blocks_on_pages(reading, [int(page)])
        withheld = phone_withheld(vault, repository, reading, [block.span_id for block in blocks])
        if withheld.whole or withheld.spans:
            return _held_out(withheld)
        covered = covered or bool(blocks)
    if not covered:
        return NOT_FOUND
    from learnloop.ingest.originals import is_pdf_file, stored_original_path

    path = stored_original_path(vault.root, digest)
    if path is None or not is_pdf_file(path):
        return MediaRefusal(404, "not_found", "The original isn't on this computer.")
    try:
        import pypdfium2  # noqa: F401 - the renderer the page endpoint draws with
    except ImportError:
        return MediaRefusal(503, "pages_unavailable", "Page images need pypdfium2 on the desktop.")
    return None


def asset_refusal(vault: Any, repository: Any, digest: str) -> MediaRefusal | None:
    """Why the stored image ``digest`` is not served to the phone, or None. Never a PDF (one leaves the host only as
    pages); an image that is a book's own original is withheld as that book's readings are."""

    from learnloop.ingest.originals import stored_original_path

    if not str(digest).startswith("sha256:"):
        return NOT_FOUND
    path = stored_original_path(vault.root, digest)
    if path is None:
        return NOT_FOUND
    try:
        size = path.stat().st_size
        with path.open("rb") as handle:
            head = handle.read(12)
    except OSError:
        return NOT_FOUND
    if image_kind(head) is None or size > MAX_ASSET_BYTES:
        return NOT_FOUND
    with repository.connection() as connection:
        revisions = connection.execute("SELECT id, source_id FROM source_revisions WHERE asset_hash = ?",
                                       (digest,)).fetchall()
    for revision_id, source_id in revisions:
        if not _reader_source_ok(repository, source_id):
            return NOT_FOUND
        with repository.connection() as connection:
            readings = [str(row[0]) for row in connection.execute(
                "SELECT id FROM source_extraction_runs WHERE revision_id = ? AND status = 'completed'",
                (revision_id,)).fetchall()]
        for reading in readings:
            withheld = phone_withheld(vault, repository, reading, list(repository.block_content_hashes(reading)))
            if withheld.whole or withheld.spans:
                return _held_out(withheld)
    return None


def _repository_for(vault: Any) -> Any:
    """The vault's database, read only, for a check asked without one; None when it can't be named."""

    config = getattr(vault, "config", None)
    root = getattr(vault, "root", None)
    if config is None or root is None:
        return None
    try:
        from learnloop.db.repositories import Repository
        from learnloop.vault.paths import VaultPaths

        path = VaultPaths(root, config).sqlite_path
        return Repository.attach(path, read_only=True) if path.exists() else None
    except Exception:  # noqa: BLE001 - an unreadable database serves nothing
        return None


def media_predicate(vault: Any, repository: Any = None) -> Any:
    """The phone eligibility's "does the host serve this target" (``scheduling.device_eligibility.MediaPredicate``):
    exactly the page and asset endpoints' refusals, over ``repository`` (or the vault's database, opened read only
    at the first question). Without a database nothing is served (fail closed)."""

    held: dict[str, Any] = {"repository": repository}

    def served(kind: str, digest: str, page: int | None) -> bool:
        if held["repository"] is None:
            held["repository"] = _repository_for(vault)
            if held["repository"] is None:
                return False
        if kind == "page":
            return page is not None and page_refusal(vault, held["repository"], digest, int(page)) is None
        if kind == "asset":
            return asset_refusal(vault, held["repository"], digest) is None
        return False

    return served


__all__ = [
    "MAX_ASSET_BYTES",
    "media_predicate",
    "MediaRefusal",
    "PhoneWithheld",
    "asset_refusal",
    "digest_of_reading",
    "page_refusal",
    "phone_withheld",
    "readings_of_file",
]
