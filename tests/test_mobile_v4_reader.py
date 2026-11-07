"""Mobile v2 stage V4: the phone Reader (spec_mobile_frontend_v2 §3, §2.3, §5.1-§5.4, §8's V4 row).

Through the real host (TestClient, the fake identity header, a paired ``app`` token), on a synthetic vault
holding one small book: a real three-page PDF in the originals store and a reading of it in three sections,
the third held out for an exam. The desktop is a ``SidecarContext`` on the same database. No model and no
network: the Ask's provider is refused in the test, and the section generation is a recorder.

* ``reader.render_view``: today's reply byte for byte without a range; a section or span range in the same
  block shape;
* protection: the phone never gets a withheld passage's text, a page image showing one, or anything of a
  reading withheld whole; its library lists no such book; its Ask and Save refuse it;
* the page endpoint: ``Token(app)``, per vault, immutable, cached outside the vault, snapped widths;
* the asset endpoint: stored images only, never a PDF, protected as the pages are;
* progress, activity and dose events: the desktop's rows exactly, monotonic across devices, and an outbox
  replay (the same request id) recorded once;
* D6: a section finished on the phone builds its questions on the desktop, once.

The plan's reading blocks on the phone are in ``tests/test_mobile_v4_plan.py``.
"""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("starlette")
pdfium = pytest.importorskip("pypdfium2")
from starlette.testclient import TestClient

import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop_mobile.host import create_app
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import versioned
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.helpers import create_basic_vault
from tests.mobile_host_helpers import HOSTNAME, ITEM, Phone, bearer, config_for, identity, pair, rows
from tests.test_reread_safety import _clock, _made_on, _persist

#: The app this stage builds: it answers probes and it has the Reader.
READER_APP = ("phone_probes", "phone_reader")
EXTRACTION = "ext1"
HELD = ("b5", "b6")

_BLOCKS = {
    "b0": ("SectionHeader", 0, "1 Vectors"),
    "b1": ("Text", 0, "A vector space is a set with addition and scalar multiplication, $u + v = v + u$."),
    "b2": ("Text", 0, "Every vector space has a zero vector."),
    "b3": ("SectionHeader", 1, "2 Spans"),
    "b4": ("Text", 1, "The span of a list is the set of all linear combinations of it."),
    "b5": ("SectionHeader", 2, "3 Exam review"),
    "b6": ("Text", 2, "Exam problem: prove that the zero vector is unique."),
}
_UNITS = (("u1", "1 Vectors", ["b0", "b1", "b2"]), ("u2", "2 Spans", ["b3", "b4"]),
          ("u3", "3 Exam review", ["b5", "b6"]))


def pdf_bytes(pages: int = 3) -> bytes:
    document = pdfium.PdfDocument.new()
    try:
        for _ in range(pages):
            document.new_page(612, 792)
        buffer = io.BytesIO()
        document.save(buffer)
        return buffer.getvalue()
    finally:
        document.close()


def _ir() -> DocumentIR:
    blocks = [DocumentBlock.build(span_id=span, block_type=kind, text=text, ordinal=index, page=page,
                                  bbox=[40.0, 60.0 + 40 * index, 560.0, 90.0 + 40 * index],
                                  section_path=[next(label for _u, label, spans in _UNITS if span in spans)])
              for index, (span, (kind, page, text)) in enumerate(_BLOCKS.items())]
    units = [DocumentUnit(unit_id=unit, label=label, ordinal=index, semantic_hash=f"sha256:{unit}", page_start=0,
                          page_end=2, span_ids=spans) for index, (unit, label, spans) in enumerate(_UNITS)]
    return DocumentIR(extractor="marker", extractor_version="1", blocks=blocks, units=units, assets=[],
                      health=ExtractionHealth())


def add_book(root: Path, repository: Repository, *, source_id: str = "src1", revision_id: str = "rev1",
             extraction_id: str = EXTRACTION, held_out: bool = True, data: bytes | None = None) -> str:
    """One book: its original in the originals store, a completed reading of it, and (``held_out``) its third
    section held out for an exam, as the owner's exact mark records it."""

    from learnloop.ingest.originals import store_original_bytes

    data = data if data is not None else pdf_bytes()
    digest = "sha256:" + hashlib.sha256(data).hexdigest()
    store_original_bytes(root, digest, data)
    now = "2026-10-14T09:00:00+00:00"
    with repository.connection() as connection:
        connection.execute("INSERT INTO source_artifacts(id, acquisition_kind, canonical_uri, created_at, updated_at) "
                           "VALUES (?,?,?,?,?)", (source_id, "pdf", "file:///home/owner/books/book.pdf", now, now))
        connection.execute("INSERT INTO source_revisions(id, source_id, asset_hash, created_at) VALUES (?,?,?,?)",
                           (revision_id, source_id, digest, now))
        connection.commit()
    repository.set_source_current_revision(source_id, revision_id)
    _persist(repository, _ir(), revision_id=revision_id, extraction_id=extraction_id, clock=_clock())
    if held_out:
        repository.upsert_unit_selection(extraction_id=extraction_id, source_id=source_id, revision_id=revision_id,
                                         selected_unit_ids=["u1", "u2", "u3"],
                                         exam_use_modes={"u3": "held_out_evaluation"},
                                         exam_paper_metadata=_made_on(extraction_id, revision_id))
    return digest


def call(ctx: SidecarContext, name: str, params: dict) -> Any:
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def desktop(root: Path) -> SidecarContext:
    ctx = SidecarContext()
    ctx.load(root)
    return ctx


def host(root: Path, cache: Path, **changes: Any):
    config = config_for(root).model_copy(update={"page_cache_dir": cache, **changes})
    return create_app(config)


@pytest.fixture
def world(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    digest = add_book(paths.root, repository)
    device = pair(repository)
    app = host(paths.root, tmp_path / "pages")
    with TestClient(app, base_url=f"https://{HOSTNAME}") as client:
        yield {"phone": Phone(client, device, capabilities=READER_APP), "root": paths.root, "repo": repository,
               "digest": digest, "cache": tmp_path / "pages", "host": app.state.host, "client": client,
               "device": device}


def job(phone: Phone, method: str, params: dict, key: str) -> Any:
    """A long method (an outbox intent, the Ask) to its end."""

    from tests.mobile_host_helpers import poll_job

    response = phone.post(method, params, request_id=key)
    if response.status_code == 202:
        body = poll_job(phone, response.json()["accepted"]["job_id"])
        assert body["state"] == "completed", body
        return body["result"]
    assert response.status_code == 200, response.text
    return response.json()["result"]


# -- reader.render_view's range (§3.2) -------------------------------------------------------


def test_render_view_without_a_range_is_todays_reply_byte_for_byte(world):
    """Absent, the reply is the pre-V4 handler's: rebuilt here from the same primitives in the same order,
    then compared as bytes. Explicit nulls are absence too."""

    from learnloop.content.sources.span_aliases import other_readings
    from learnloop.reader import reader_guidance as RG
    from learnloop.reader import source_render_views as RV

    ctx = desktop(world["root"])
    reply = call(ctx, "reader.render_view", {"extractionId": EXTRACTION})
    nulls = call(ctx, "reader.render_view", {"extractionId": EXTRACTION, "sectionId": None, "fromSpanId": None,
                                             "toSpanId": None})
    vault, repository = ctx.require_vault()
    view = RV.resolve_or_create_render_view(repository, extraction_id=EXTRACTION, revision_id=None)
    payload = RV.render_payload(repository, view["id"])
    payload["aliased_from"] = repository.span_reanchor_origins(EXTRACTION)
    payload["other_readings"] = other_readings(repository, EXTRACTION)
    payload["protection"] = RG.reading_protection(vault, repository, EXTRACTION,
                                                  [block.get("span_id") for block in payload["blocks"]])
    expected = json.dumps(versioned(payload))
    assert json.dumps(reply) == expected and json.dumps(nulls) == expected
    assert "range" not in reply
    # The desktop is sent the book's held-out text, as before (it withholds model actions on it).
    assert [b["markdown"] for b in reply["blocks"] if b["spanId"] in HELD][1].startswith("Exam problem")
    assert reply["protection"]["heldOutSpanIds"] == list(HELD)


def test_a_section_range_is_its_blocks_in_the_same_shape(world):
    ctx = desktop(world["root"])
    full = {block["spanId"]: block for block in call(ctx, "reader.render_view", {"extractionId": EXTRACTION})["blocks"]}
    part = call(ctx, "reader.render_view", {"extractionId": EXTRACTION, "sectionId": "u2"})
    assert [block["spanId"] for block in part["blocks"]] == ["b3", "b4"]
    assert all(block == full[block["spanId"]] for block in part["blocks"])
    assert part["range"] == {"sectionId": "u2", "fromSpanId": "b3", "toSpanId": "b4", "blockCount": 7}
    spans = call(ctx, "reader.render_view", {"extractionId": EXTRACTION, "fromSpanId": "b2", "toSpanId": "b3"})
    assert [block["spanId"] for block in spans["blocks"]] == ["b2", "b3"]
    open_end = call(ctx, "reader.render_view", {"extractionId": EXTRACTION, "fromSpanId": "b4"})
    assert [block["spanId"] for block in open_end["blocks"]] == ["b4", "b5", "b6"]
    from learnloop_sidecar.errors import SidecarError

    with pytest.raises(SidecarError) as unknown:
        call(ctx, "reader.render_view", {"extractionId": EXTRACTION, "sectionId": "nope"})
    assert unknown.value.code == "validation_error"
    with pytest.raises(Exception):
        call(ctx, "reader.render_view", {"extractionId": EXTRACTION, "sectionId": "u1", "fromSpanId": "b0"})
    # The phone loads by section through the host, in the same shape, each block naming its page (D4: the
    # phone's original page is the host's image of it).
    phone_part = world["phone"].rpc("reader.render_view", {"extractionId": EXTRACTION, "sectionId": "u2"})
    assert [block.pop("page") for block in phone_part["blocks"]] == [1, 1]
    assert phone_part["blocks"] == part["blocks"] and phone_part["range"] == part["range"]


# -- protection on text (§3; the stage's rule) ---------------------------------------------


def test_the_phone_is_never_sent_held_out_text(world):
    phone = world["phone"]
    whole = phone.rpc("reader.render_view", {"extractionId": EXTRACTION})
    held = [block for block in whole["blocks"] if block["spanId"] in HELD]
    assert [block["markdown"] for block in held] == ["", ""]
    assert all(block["withheld"] is True and block["assets"] == [] for block in held)
    assert "Exam problem" not in json.dumps(whole)
    assert whole["protection"]["heldOutSpanIds"] == list(HELD) and whole["protection"]["message"]
    # The rest is the desktop's text.
    ctx = desktop(world["root"])
    desktop_blocks = {b["spanId"]: b for b in call(ctx, "reader.render_view", {"extractionId": EXTRACTION})["blocks"]}
    assert all({key: value for key, value in block.items() if key != "page"} == desktop_blocks[block["spanId"]]
               for block in whole["blocks"] if block["spanId"] not in HELD)
    section = phone.rpc("reader.render_view", {"extractionId": EXTRACTION, "sectionId": "u3"})
    assert "Exam problem" not in json.dumps(section)
    plan = phone.rpc("reader.guide_plan", {"extractionId": EXTRACTION})
    assert [section["id"] for section in plan["sections"]] == ["u1", "u2", "u3"]
    assert "Exam problem" not in json.dumps(plan)


def test_a_reading_exam_material_covers_whole_reaches_the_phone_not_at_all(world):
    from learnloop.vault.writer import upsert_source_set

    add_book(world["root"], world["repo"], source_id="src_exam", revision_id="rev_exam", extraction_id="ext_exam",
             held_out=False, data=pdf_bytes(2))
    upsert_source_set(world["root"], {
        "id": "sset_la", "subject_id": "linear-algebra", "title": "Linear algebra sources",
        "members": [{"source_id": "src_exam", "revision_id": "rev_exam", "default_role": "exam"}],
    })
    phone = world["phone"]
    for method in ("reader.render_view", "reader.guide_plan"):
        status, error = phone.error(method, {"extractionId": "ext_exam"})
        assert (status, error["code"]) == (409, "held_out_material"), method
    response = phone.get("/api/v1/reader/page/ext_exam/0")
    assert response.status_code == 403 and response.json()["error"]["code"] == "held_out_material"
    books = phone.rpc("get_source_library")["sources"]
    assert [book["sourceId"] for book in books] == ["src1"]
    assert books[0]["extractionId"] == EXTRACTION and books[0]["canonicalUri"] is None
    # The desktop's library and Reader are as they were.
    ctx = desktop(world["root"])
    assert {card["sourceId"] for card in call(ctx, "get_source_library", {})["sources"]} >= {"src1", "src_exam"}
    assert call(ctx, "reader.render_view", {"extractionId": "ext_exam"})["blocks"]


def test_the_phones_ask_and_save_refuse_protected_passages_before_any_model(world, monkeypatch):
    import learnloop_sidecar.handlers.reader as reader_handlers

    asked: list[Any] = []

    def no_provider(vault):
        asked.append(vault)
        from learnloop_sidecar.errors import SidecarError

        raise SidecarError("provider_unavailable", "no provider in tests", retryable=True)

    monkeypatch.setattr(reader_handlers, "ready_tutor_qa_provider", no_provider)
    phone = world["phone"]
    refused = phone.post("reader.ask", {"extractionId": EXTRACTION, "spanId": "b6", "question": "why?"},
                         request_id="ask_held")
    assert refused.status_code == 409 and refused.json()["error"]["code"] == "held_out_material"
    selected = phone.post("reader.ask", {"extractionId": EXTRACTION, "spanId": "b4", "selectionSpanIds": ["b5"],
                                         "question": "why?"}, request_id="ask_selected")
    assert selected.status_code == 409 and selected.json()["error"]["code"] == "held_out_material"
    assert asked == []
    # A permitted passage reaches the desktop's Ask (here its provider is refused: no model in tests).
    allowed = phone.post("reader.ask", {"extractionId": EXTRACTION, "spanId": "b4", "question": "why?"},
                         request_id="ask_ok")
    assert allowed.status_code == 409 and allowed.json()["error"]["code"] == "provider_unavailable"
    assert len(asked) == 1
    save = {"sourceId": "src1", "revisionId": "rev1", "extractionId": EXTRACTION, "action": "highlight",
            "clientIdempotencyKey": "save_1",
            "rawSelection": {"nodes": [{"spanId": "b6", "quote": "Exam problem"}]}}
    status, error = phone.error("reader.capture", save)
    assert (status, error["code"]) == (409, "held_out_material")
    saved = phone.rpc("reader.capture", {**save, "clientIdempotencyKey": "save_2",
                                         "rawSelection": {"nodes": [{"spanId": "b4", "quote": "span of a list"}]}})
    assert saved["receipt"] == "acknowledged"


def test_the_phones_ask_is_refused_while_its_check_on_your_own_is_open(world, monkeypatch):
    """J8: the server knows a check is open (never the phone's word)."""

    import learnloop_sidecar.handlers.as_printed as as_printed
    import learnloop_sidecar.handlers.reader as reader_handlers

    monkeypatch.setattr(reader_handlers, "ready_tutor_qa_provider",
                        lambda vault: pytest.fail("no model while a check is open"))
    phone = world["phone"]
    session_id = phone.start()["sessionId"]
    phone.rpc("update_session_checkpoint", {"sessionId": session_id, "currentPracticeItemId": ITEM})
    monkeypatch.setattr(as_printed, "cold_now", lambda vault, repository, item_id: item_id == ITEM)
    refused = phone.post("reader.ask", {"extractionId": EXTRACTION, "spanId": "b4", "question": "why?"},
                         request_id="ask_cold")
    assert refused.status_code == 409 and refused.json()["error"]["code"] == "cold_check_open"


# -- the page endpoint (§3.3) --------------------------------------------------------------


def test_a_page_is_a_png_under_the_app_token_immutable_and_cached_outside_the_vault(world, monkeypatch):
    import learnloop_mobile.media as media

    renders: list[tuple[int, int]] = []
    real = media.render_page_png

    def counting(path, page, width):
        renders.append((page, width))
        return real(path, page, width)

    monkeypatch.setattr(media, "render_page_png", counting)
    phone, client = world["phone"], world["client"]
    response = phone.get("/api/v1/reader/page/ext1/1?w=700")
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "image/png" and response.content.startswith(b"\x89PNG")
    assert response.headers["cache-control"] == "private, max-age=31536000, immutable"
    assert response.headers["etag"]
    from PIL import Image

    assert Image.open(io.BytesIO(response.content)).size[0] == 720  # snapped to the 720 width
    again = phone.get("/api/v1/reader/page/ext1/1?w=720")
    assert again.content == response.content and renders == [(1, 720)]  # the second came from the cache
    cached = list(world["cache"].rglob("*.png"))
    assert len(cached) == 1 and not cached[0].resolve().is_relative_to(world["root"].resolve())
    assert world["digest"].split(":", 1)[1] in str(cached[0])
    # The file's own name (an llpdf:// link's) is the same page, from the same cache entry.
    by_file = phone.get(f"/api/v1/reader/page/sha256-{world['digest'].split(':', 1)[1]}/1?w=720")
    assert by_file.status_code == 200 and by_file.content == response.content and len(renders) == 1
    # No token, a capture token, a wrong identity: refused before anything is read.
    assert client.get("/api/v1/reader/page/ext1/1", headers=identity()).status_code == 401
    capture_device = pair(world["repo"], scope="capture", label="Shortcut")
    assert client.get("/api/v1/reader/page/ext1/1", headers=bearer(capture_device)).status_code == 403
    assert client.get("/api/v1/reader/page/ext1/1",
                      headers={**bearer(world["device"]), "Tailscale-User-Login": "other@example.com"}).status_code == 403
    # Only the width is a parameter, and nothing outside the reading's pages or the book is served.
    assert phone.get("/api/v1/reader/page/ext1/1?w=720&x=1").status_code == 400
    assert phone.get("/api/v1/reader/page/ext1/9").status_code == 404
    assert phone.get("/api/v1/reader/page/ext1/../1").status_code == 404
    assert phone.get("/api/v1/reader/page/not_a_reading/0").status_code == 404
    assert phone.get("/api/v1/reader/page/sha256-" + "0" * 64 + "/0").status_code == 404


def test_a_page_showing_a_held_out_passage_is_never_served(world):
    phone = world["phone"]
    response = phone.get("/api/v1/reader/page/ext1/2")
    assert response.status_code == 403 and response.json()["error"]["code"] == "held_out_material"
    by_file = phone.get(f"/api/v1/reader/page/sha256-{world['digest'].split(':', 1)[1]}/2")
    assert by_file.status_code == 403
    assert not list(world["cache"].rglob("2-*.png"))


def test_a_mark_made_after_a_page_was_cached_withholds_it_at_once(world):
    phone = world["phone"]
    assert phone.get("/api/v1/reader/page/ext1/1").status_code == 200
    world["repo"].upsert_unit_selection(extraction_id=EXTRACTION, source_id="src1", revision_id="rev1",
                                        selected_unit_ids=["u1", "u2", "u3"],
                                        exam_use_modes={"u2": "held_out_evaluation", "u3": "held_out_evaluation"},
                                        exam_paper_metadata=_made_on(EXTRACTION, "rev1"))
    assert phone.get("/api/v1/reader/page/ext1/1").status_code == 403
    section = phone.rpc("reader.render_view", {"extractionId": EXTRACTION, "sectionId": "u2"})
    assert all(block["markdown"] == "" for block in section["blocks"])


def test_the_page_endpoint_is_per_vault(tmp_path):
    """A token paired on one vault's host is no token on another's, an id of one vault's reading is not found
    on the other's, and the two caches never share an entry, even for the same file."""

    data = pdf_bytes()
    worlds = []
    for name in ("a", "b"):
        paths = create_basic_vault(tmp_path / name)
        repository = Repository(paths.sqlite_path)
        add_book(paths.root, repository, extraction_id=f"ext_{name}", data=data)
        worlds.append((paths, repository, pair(repository)))
    (paths_a, _repo_a, device_a), (paths_b, _repo_b, device_b) = worlds
    cache = tmp_path / "pages"
    with TestClient(host(paths_a.root, cache), base_url=f"https://{HOSTNAME}") as client_a, \
            TestClient(host(paths_b.root, cache), base_url=f"https://{HOSTNAME}") as client_b:
        phone_a, phone_b = Phone(client_a, device_a, READER_APP), Phone(client_b, device_b, READER_APP)
        assert phone_a.get("/api/v1/reader/page/ext_a/0").status_code == 200
        assert phone_a.get("/api/v1/reader/page/ext_b/0").status_code == 404
        assert client_b.get("/api/v1/reader/page/ext_b/0", headers=bearer(device_a)).status_code == 401
        assert phone_b.get("/api/v1/reader/page/ext_b/0").status_code == 200
    vaults = {path.relative_to(cache).parts[0] for path in cache.rglob("*.png")}
    assert len(vaults) == 2


def test_the_reader_switch_off_is_v3s_phone(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    add_book(paths.root, repository)
    device = pair(repository)
    with TestClient(host(paths.root, tmp_path / "pages", phone_reader=False), base_url=f"https://{HOSTNAME}") as client:
        phone = Phone(client, device, READER_APP)
        status, error = phone.error("reader.render_view", {"extractionId": EXTRACTION})
        assert (status, error["code"]) == (409, "phone_reader_off")
        assert phone.get("/api/v1/reader/page/ext1/0").status_code == 404
        assert phone.get("/api/v1/meta").json()["phone_reader"] is False


# -- the asset endpoint (§2.3) -------------------------------------------------------------


def _png() -> bytes:
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), (200, 10, 10)).save(buffer, format="PNG")
    return buffer.getvalue()


def test_a_stored_image_is_served_by_its_content_address_and_never_a_pdf(world):
    from learnloop.ingest.originals import store_original_bytes

    image = _png()
    name = "sha256-" + hashlib.sha256(image).hexdigest()
    store_original_bytes(world["root"], "sha256:" + name[7:], image)
    phone = world["phone"]
    response = phone.get(f"/api/v1/assets/{name}")
    assert response.status_code == 200 and response.content == image
    assert response.headers["content-type"] == "image/png"
    assert response.headers["cache-control"] == "private, max-age=31536000, immutable"
    assert phone.get(f"/api/v1/assets/sha256-{world['digest'].split(':', 1)[1]}").status_code == 404  # a PDF
    assert phone.get("/api/v1/assets/../learnloop.toml").status_code == 404
    assert phone.get("/api/v1/assets/" + "a" * 64).status_code == 404
    assert world["client"].get(f"/api/v1/assets/{name}", headers=identity()).status_code == 401


def test_an_image_that_is_a_protected_books_original_is_withheld(world):
    from learnloop.vault.writer import upsert_source_set

    image = _png()
    add_book(world["root"], world["repo"], source_id="src_photo", revision_id="rev_photo",
             extraction_id="ext_photo", held_out=False, data=image)
    upsert_source_set(world["root"], {
        "id": "sset_la", "subject_id": "linear-algebra", "title": "Linear algebra sources",
        "members": [{"source_id": "src_photo", "revision_id": "rev_photo", "default_role": "exam"}],
    })
    name = "sha256-" + hashlib.sha256(image).hexdigest()
    response = world["phone"].get(f"/api/v1/assets/{name}")
    assert response.status_code == 403 and response.json()["error"]["code"] == "held_out_material"


# -- progress, activity, doses: the desktop's rows, once (§3.4, §5.4) ------------------------


def test_progress_is_monotonic_across_the_phone_and_the_desktop(world):
    phone = world["phone"]
    ctx = desktop(world["root"])
    job(phone, "reader.mark_section_progress",
        {"extractionId": EXTRACTION, "sectionId": "u1", "spansSeen": 3, "spanCount": 3}, "p1")
    call(ctx, "reader.mark_section_progress", {"extractionId": EXTRACTION, "sectionId": "u1", "spansSeen": 1,
                                               "spanCount": 3})
    job(phone, "reader.mark_section_progress",
        {"extractionId": EXTRACTION, "sectionId": "u1", "spansSeen": 0, "spanCount": 3}, "p2")
    row = world["repo"].reader_section_progress_row(EXTRACTION, "u1")
    assert row["spans_seen"] == 3 and row["span_count"] == 3
    both = [phone.rpc("reader.get_progress", {"extractionId": EXTRACTION})["sections"],
            call(ctx, "reader.get_progress", {"extractionId": EXTRACTION})["sections"]]
    assert both[0] == both[1] and both[0][0]["spansSeen"] == 3


def test_an_outbox_replay_is_recorded_once(world):
    phone = world["phone"]
    events = {"events": [{"kind": "reader_view_opened", "occurredAt": "2026-10-14T08:00:00Z",
                          "payload": {"visitId": "v1", "extractionId": EXTRACTION, "surface": "text"}}]}
    first = job(phone, "reader.log_activity", events, "act_1")
    second = job(phone, "reader.log_activity", events, "act_1")
    assert first == second == {"version": 1, "recorded": 1}
    assert len(rows(world["repo"], "SELECT id FROM interaction_events WHERE kind = 'reader_view_opened'")) == 1
    progress = {"extractionId": EXTRACTION, "sectionId": "u2", "spansSeen": 1, "spanCount": 2}
    job(phone, "reader.mark_section_progress", progress, "prog_1")
    job(phone, "reader.mark_section_progress", progress, "prog_1")
    # The same key with other params is a conflict, never a second write.
    conflict = phone.post("reader.log_activity", {"events": []}, request_id="act_1")
    assert conflict.status_code == 409 and conflict.json()["error"]["code"] == "submission_conflict"


def test_activity_is_the_desktops_row_with_the_phones_surface(world):
    phone = world["phone"]
    ctx = desktop(world["root"])
    event = {"kind": "reader_view_opened", "occurredAt": "2026-10-14T08:00:00Z",
             "payload": {"visitId": "v1", "extractionId": EXTRACTION, "surface": "text", "deviceSurface": "forged"}}
    call(ctx, "reader.log_activity", {"events": [event]})
    job(phone, "reader.log_activity", {"events": [event]}, "act_eq")
    found = rows(world["repo"], "SELECT kind, origin, subject_type, subject_id, payload_json, occurred_at "
                                "FROM interaction_events WHERE kind = 'reader_view_opened' ORDER BY rowid")
    assert len(found) == 2
    desk, mobile = (json.loads(row.pop("payload_json")) for row in found)
    assert found[0] == found[1]
    assert found[1]["occurred_at"] in (None, "2026-10-14T08:00:00Z")
    assert "device_surface" not in desk and mobile.pop("device_surface") == "phone_reader"
    assert desk == mobile and desk["surface"] == "text"


def test_a_section_finished_on_the_phone_builds_its_questions_on_the_desktop_once(world, monkeypatch):
    """D6: the host enqueues nothing; the desktop's Reader (or its start) builds them as its own completion
    would, once."""

    import learnloop.reader.reader_progression as progression
    from learnloop.content.pipeline.jobs import IngestJobManager

    enqueued: list[dict] = []
    monkeypatch.setattr(progression, "section_generation_candidates",
                        lambda vault, repository, *, extraction_id, section_id: ["lo_svd_definition"])
    monkeypatch.setattr(progression, "source_refs_for_section", lambda *args, **kwargs: [])
    monkeypatch.setattr(IngestJobManager, "enqueue_practice_expansion",
                        lambda self, **kwargs: enqueued.append(kwargs) or f"batch_{len(enqueued)}")
    phone = world["phone"]
    done = job(phone, "reader.mark_section_progress",
               {"extractionId": EXTRACTION, "sectionId": "u1", "spansSeen": 3, "spanCount": 3, "completed": True},
               "done_1")
    assert done["enqueuedGeneration"] is False and enqueued == []
    assert world["repo"].reader_section_progress_row(EXTRACTION, "u1")["generation_batch_id"] == "deferred_to_primary"
    ctx = desktop(world["root"])  # its start drains it
    assert len(enqueued) == 1 and enqueued[0]["reason"] == "reader_section_completed:u1"
    call(ctx, "reader.get_progress", {"extractionId": EXTRACTION})
    assert len(enqueued) == 1
    assert world["repo"].reader_section_progress_row(EXTRACTION, "u1")["generation_batch_id"] == "batch_1"
    # A completion on the desktop is as before.
    call(ctx, "reader.mark_section_progress", {"extractionId": EXTRACTION, "sectionId": "u2", "completed": True})
    assert len(enqueued) == 2


def test_doses_from_the_phone_are_the_desktops_draw_and_rows(tmp_path, monkeypatch):
    """The same boundary on two identical vaults, one through the desktop's handler and one through the phone:
    the draw (its seed is the visit and section) and every uptake row are equal; an uptake replayed from the
    outbox is one row."""

    from tests.ad_fakes import rows as ad_rows
    from tests.test_ad1_reading_opportunities import FakeMap, _setup
    from tests.test_ad3_dose_arm import QUIET, _question
    import learnloop.adaptive_difficulty.reading as reading

    mapping = FakeMap()
    mapping.examples["ext1"] = {"we1", "we2"}
    mapping.spans[("ext1", "we2")] = ["lo_svd_definition"]
    monkeypatch.setattr(reading, "VaultReadingMap", lambda *args, **kwargs: mapping)
    def visits(offer_at, uptake):
        """The same boundaries in the same order until one offers an extra; its uptake, as each device sends it."""

        offers = []
        for visit in range(30):
            offer = offer_at({"extractionId": "ext1", "sectionId": "u1", "visitId": f"visit{visit}"})
            shown = {key: value for key, value in offer.items() if key != "drawId"}
            if isinstance(shown.get("offer"), dict):
                shown["offer"] = {key: value for key, value in shown["offer"].items() if key != "drawId"}
            offers.append(shown)
            if offer.get("offer"):
                uptake(offer["drawId"])
                return offers
        pytest.fail("no extra offered")

    outcomes = []
    for name in ("desktop", "phone"):
        paths, _vault, repository = _setup(tmp_path / name, config=QUIET + "dose_floor = 0.3\n")
        _question(repository, "recall", 1, answer=False)
        if name == "desktop":
            ctx = desktop(paths.root)

            def uptake(draw_id, ctx=ctx):
                for event in ("delivered", "taken"):
                    call(ctx, "reader.dose_offer_event", {"drawId": draw_id, "event": event})

            offers = visits(lambda boundary, ctx=ctx: call(ctx, "reader.dose_offer", boundary), uptake)
        else:
            device = pair(repository)
            with TestClient(host(paths.root, tmp_path / "pages"), base_url=f"https://{HOSTNAME}") as client:
                phone = Phone(client, device, READER_APP)

                def uptake(draw_id, phone=phone):
                    for event in ("delivered", "taken"):
                        job(phone, "reader.dose_offer_event", {"drawId": draw_id, "event": event}, f"u_{event}")
                    # The outbox sends "taken" again after a lost reply: the same key, one row.
                    job(phone, "reader.dose_offer_event", {"drawId": draw_id, "event": "taken"}, "u_taken")

                offers = visits(lambda boundary, phone=phone: phone.rpc("reader.dose_offer", boundary), uptake)
        found = ad_rows(paths.sqlite_path, "SELECT * FROM ad_dose_offers ORDER BY created_at, rowid")
        outcomes.append(([{key: value for key, value in row.items() if key not in ("id", "draw_id", "created_at")}
                          for row in found], offers))
    assert outcomes[0] == outcomes[1]
    kinds = [row["row_kind"] for row in outcomes[1][0]]
    assert kinds.count("delivered") == 1 and kinds.count("taken") == 1
