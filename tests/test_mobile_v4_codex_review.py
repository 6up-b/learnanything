"""Mobile v2 stage V4, the Codex review's server-side findings (docs/reviews/phone-v4-codex-review.md), reproduced
first and pinned here: F3 (a page by a reading's id is decided by every reading of its file), F4 (Ask history
checks every selected span and citation), F5 (an outbox intent that committed before its job's end is not recorded
again after a restart), F9's server half (the phone answers a dose's extra question through the desktop's
question action), F10 (media eligibility is the page endpoint's own predicate) and F12 (the media lift admits no
new measurement on the phone).

Synthetic vaults only (``tests.test_mobile_v4_reader``'s book), the host in-process, no model and no network.
"""

from __future__ import annotations

import json
import sqlite3
from types import SimpleNamespace
from typing import Any

import pytest

pytest.importorskip("starlette")
pytest.importorskip("pypdfium2")
from starlette.testclient import TestClient

from learnloop.db.repositories import Repository
from learnloop.scheduling import device_eligibility as DE
from tests.helpers import create_basic_vault
from tests.mobile_host_helpers import HOSTNAME, Phone, pair, poll_job, rows
from tests.test_mobile_v4_reader import (  # noqa: F401 - the fixture
    EXTRACTION, READER_APP, add_book, call, desktop, host, job, world,
)


def _original(world) -> bytes:
    from learnloop.ingest.originals import stored_original_path

    return stored_original_path(world["root"], world["digest"]).read_bytes()


def _exam_role(root, source_id: str) -> None:
    from learnloop.vault.writer import upsert_source_set

    upsert_source_set(root, {
        "id": "sset_la", "subject_id": "linear-algebra", "title": "Linear algebra sources",
        "members": [{"source_id": source_id, "revision_id": f"rev_{source_id[4:]}", "default_role": "exam"}],
    })


# -- F3: either name of a page is decided by every reading of its file ------------------------------------------


def test_f3_a_page_named_by_an_ordinary_reading_is_withheld_when_another_reading_of_its_file_is_exam_material(world):
    phone = world["phone"]
    assert phone.get(f"/api/v1/reader/page/{EXTRACTION}/0").status_code == 200
    # The same bytes, registered again as an exam paper (another source, another reading).
    add_book(world["root"], world["repo"], source_id="src_exam", revision_id="rev_exam", extraction_id="ext_exam",
             held_out=False, data=_original(world))
    _exam_role(world["root"], "src_exam")
    by_file = phone.get(f"/api/v1/reader/page/sha256-{world['digest'].split(':', 1)[1]}/0")
    by_reading = phone.get(f"/api/v1/reader/page/{EXTRACTION}/0")
    assert by_file.status_code == 403 and by_file.json()["error"]["code"] == "held_out_material"
    assert by_reading.status_code == 403 and by_reading.json()["error"]["code"] == "held_out_material"
    # The desktop's own Reader still opens the ordinary reading.
    assert call(desktop(world["root"]), "reader.render_view", {"extractionId": EXTRACTION})["blocks"]


# -- F4: Ask history checks every selected span and every citation ----------------------------------------------


def _exchange(repository, *, span: str, selection: list[str], quote: str, citations: list[dict] | None = None,
              excerpt: dict | None = None) -> None:
    payload: dict[str, Any] = {
        "extraction_id": EXTRACTION, "span_id": span, "answer_md": f"An answer about {span}.",
        "citations": citations or [],
        "manifest": {"question_md": "why?", "selection": {"span_ids": selection, "quote_md": quote}},
    }
    if excerpt is not None:
        payload["tutor"] = {"excerpt": excerpt}
    repository.append_interaction_event(kind="reader_answer_submitted", origin="learner",
                                        subject_type="reader_span", subject_id=f"span:{EXTRACTION}/{span}",
                                        payload_json=json.dumps(payload))


def test_f4_ask_history_withholds_an_exchange_whose_selection_or_citation_is_protected(world):
    repository = world["repo"]
    _exchange(repository, span="b4", selection=["b4"], quote="The span of a list")
    _exchange(repository, span="b4", selection=["b4", "b6"], quote="The span of a list. Exam problem: prove it.")
    _exchange(repository, span="b1", selection=["b1"], quote="A vector space",
              citations=[{"extraction_id": EXTRACTION, "span_id": "b6", "label": "x"}])
    _exchange(repository, span="b2", selection=["b2"], quote="Every vector space",
              excerpt={"extraction_id": EXTRACTION, "span_id": "b5", "text": "3 Exam review"})
    history = world["phone"].rpc("reader.ask_history", {"extractionId": EXTRACTION})["exchanges"]
    assert [exchange["spanId"] for exchange in history] == ["b4"]
    assert "Exam problem" not in json.dumps(history) and "Exam review" not in json.dumps(history)
    # The desktop's history is every exchange, as before.
    assert len(call(desktop(world["root"]), "reader.ask_history", {"extractionId": EXTRACTION})["exchanges"]) == 4


# -- F5: a committed intent is not recorded again after a restart -----------------------------------------------


def _crash_after_the_handler(monkeypatch, root, repository, cache, device, method: str, params: dict,
                             key: str) -> str:
    """Run one intent whose handler commits and whose job's end is never written (the host dies there), then
    start a new host on the vault, which re-runs what was left open. Returns the job's id."""

    import learnloop.capture as capture_module
    import learnloop_mobile.runtime as runtime_module

    real_finish = capture_module.finish_job

    def lost(*args, **kwargs):
        raise sqlite3.OperationalError("disk I/O error")

    monkeypatch.setattr(runtime_module, "_FINISH_RETRIES", 0)
    monkeypatch.setattr(runtime_module, "_FINISH_DEBT_RETRY_SECONDS", 3600.0)
    monkeypatch.setattr(capture_module, "finish_job", lost)
    with TestClient(host(root, cache), base_url=f"https://{HOSTNAME}") as client:
        response = Phone(client, device, READER_APP).post(method, params, request_id=key)
        assert response.status_code in (200, 202), response.text
        job_id = rows(repository, "SELECT id FROM mobile_jobs WHERE request_id = ?", key)[0]["id"]
    monkeypatch.setattr(capture_module, "finish_job", real_finish)
    left = rows(repository, "SELECT state FROM mobile_jobs WHERE id = ?", job_id)
    assert left[0]["state"] == "running"  # the crash window: domain rows committed, the job's end not
    with TestClient(host(root, cache), base_url=f"https://{HOSTNAME}") as client:
        body = poll_job(Phone(client, device, READER_APP), job_id)
        assert body["state"] == "completed", body
    return job_id


def test_f5_activity_committed_before_a_crash_is_recorded_once_after_the_restart(world, monkeypatch):
    events = {"events": [{"kind": "reader_view_opened", "occurredAt": "2026-10-14T08:00:00Z",
                          "payload": {"visitId": "v1", "extractionId": EXTRACTION, "surface": "text"}},
                         {"kind": "reader_view_closed", "occurredAt": "2026-10-14T08:05:00Z",
                          "payload": {"visitId": "v1", "extractionId": EXTRACTION, "activeSeconds": 240,
                                      "idleSeconds": 60}}]}
    _crash_after_the_handler(monkeypatch, world["root"], world["repo"], world["cache"], world["device"],
                             "reader.log_activity", events, "act_crash")
    found = rows(world["repo"], "SELECT kind FROM interaction_events WHERE kind IN "
                                "('reader_view_opened', 'reader_view_closed') ORDER BY rowid")
    assert [row["kind"] for row in found] == ["reader_view_opened", "reader_view_closed"]


def test_f5_a_dose_event_committed_before_a_crash_is_recorded_once_after_the_restart(tmp_path, monkeypatch):
    from tests.ad_fakes import rows as ad_rows
    from tests.test_ad1_reading_opportunities import FakeMap, _setup
    from tests.test_ad3_dose_arm import QUIET, _question
    import learnloop.adaptive_difficulty.reading as reading

    mapping = FakeMap()
    mapping.examples["ext1"] = {"we1", "we2"}
    mapping.spans[("ext1", "we2")] = ["lo_svd_definition"]
    monkeypatch.setattr(reading, "VaultReadingMap", lambda *args, **kwargs: mapping)
    paths, _vault, repository = _setup(tmp_path / "dose", config=QUIET + "dose_floor = 0.3\n")
    _question(repository, "recall", 1, answer=False)
    device = pair(repository)
    cache = tmp_path / "pages"
    draw = None
    with TestClient(host(paths.root, cache), base_url=f"https://{HOSTNAME}") as client:
        phone = Phone(client, device, READER_APP)
        for visit in range(30):
            offer = phone.rpc("reader.dose_offer", {"extractionId": "ext1", "sectionId": "u1", "visitId": f"v{visit}"})
            if offer.get("offer"):
                draw = offer["drawId"]
                break
    assert draw is not None, "no extra offered"
    _crash_after_the_handler(monkeypatch, paths.root, repository, cache, device, "reader.dose_offer_event",
                             {"drawId": draw, "event": "delivered"}, "dose_crash")
    kinds = [row["row_kind"] for row in ad_rows(paths.sqlite_path, "SELECT * FROM ad_dose_offers")]
    assert kinds.count("delivered") == 1


def test_f5_the_desktop_writes_as_before(world):
    """The receipt is the phone's job's: a None origin has none, and its handler is the same call."""

    ctx = desktop(world["root"])
    event = {"kind": "reader_view_opened", "occurredAt": "2026-10-14T08:00:00Z",
             "payload": {"visitId": "v1", "extractionId": EXTRACTION, "surface": "text"}}
    assert call(ctx, "reader.log_activity", {"events": [event]}) == {"version": 1, "recorded": 1}
    assert call(ctx, "reader.log_activity", {"events": [event]}) == {"version": 1, "recorded": 1}
    assert len(rows(world["repo"], "SELECT id FROM interaction_events WHERE kind = 'reader_view_opened'")) == 2


# -- F8's server half: the phone's visit counts on the router's clock ------------------------------------------


def test_f8_a_phone_visits_active_time_reaches_the_routers_activity_readers(world):
    from learnloop.router_objective import price

    phone = world["phone"]
    events = [{"kind": "reader_view_opened", "occurredAt": "2026-10-14T08:00:00Z",
               "payload": {"visitId": "v_phone", "extractionId": EXTRACTION, "surface": "text", "sourceId": "src1",
                           "askAvailable": True, "initiator": "learner"}},
              {"kind": "reader_view_closed", "occurredAt": "2026-10-14T08:05:00Z",
               "payload": {"visitId": "v_phone", "extractionId": EXTRACTION, "activeSeconds": 240,
                           "idleSeconds": 60}}]
    job(phone, "reader.log_activity", {"events": events}, "act_visit")
    from learnloop.router_objective.decision_state import _reader_visits

    with world["repo"].connection() as connection:
        spans = price.activity_spans(connection, since="2000-01-01T00:00:00Z", until="2100-01-01T00:00:00Z")
        visits, unplaced = _reader_visits(connection, "2000-01-01T00:00:00Z")
    assert [span[2] for span in spans] == [240.0]
    assert [visit[2] for visit in visits] == [240.0] and unplaced == 0.0
    assert [(visit[1] - visit[0]).total_seconds() for visit in visits] == [300.0]


# -- F9's server half: the extra question is answered through the desktop's question action ---------------------


def test_f9_the_phone_answers_an_extra_question_through_the_desktops_question_action(world):
    from learnloop_mobile.allowlist import ALLOWLIST, check_parameters

    repository = world["repo"]
    question_id = repository.insert_reader_authored_question(fields={
        "extraction_id": EXTRACTION, "section_id": "u2", "source_id": "src1", "question_md": "What is a span?",
        "expected_answer_md": "All linear combinations.", "span_ids": ["b4"], "prompt_version": "qc-v1",
        "scope_kind": "inquiry", "question_style": "recall", "anchor_span_ids": ["b4"],
        "inquiry_root_event_id": "root-1",
    })
    method = ALLOWLIST["reader.authored_question_action"]
    from learnloop_mobile.allowlist import ParamRejected

    with pytest.raises(ParamRejected):
        check_parameters(method, {"questionId": question_id, "action": "dismissed"})
    answered = world["phone"].rpc("reader.authored_question_action",
                                  {"questionId": question_id, "action": "answered", "response": "my words"})
    assert answered["question"]["status"] == "answered"
    row = repository.get_reader_authored_question(question_id)
    assert row["status"] == "answered" and row["response_md"] == "my words"
    # A question on a passage now held out is refused on the phone.
    held = repository.insert_reader_authored_question(fields={
        "extraction_id": EXTRACTION, "section_id": "u3", "source_id": "src1", "question_md": "Prove it.",
        "expected_answer_md": "By uniqueness.", "span_ids": ["b6"], "prompt_version": "qc-v1",
        "scope_kind": "inquiry", "question_style": "recall", "anchor_span_ids": ["b6"],
        "inquiry_root_event_id": "root-2",
    })
    status, error = world["phone"].error("reader.authored_question_action",
                                         {"questionId": held, "action": "answered", "response": "x"})
    assert (status, error["code"]) == (409, "held_out_material")


# -- F10, F12: eligibility is the media endpoint's own predicate, and admits no new measurement -----------------


def _item(prompt: str, *, mode: str = "short_answer"):
    return SimpleNamespace(id="pi_x", practice_mode=mode, teach_back_source=None, error_hunt=None,
                           laddered_stem=None, prompt=prompt, provenance=None, lesson_id=None, lifecycle=None)


def _reason(vault, repository, prompt: str, *, mode: str = "short_answer") -> str | None:
    from unittest import mock

    with mock.patch.object(DE, "minted_for_lesson", lambda item: False):
        return DE.ineligibility_reason(vault, _item(prompt, mode=mode), DE.PHONE, media=True, repository=repository)


def test_f10_a_page_is_phone_eligible_exactly_when_the_page_endpoint_serves_it(world):
    vault, repository = desktop(world["root"]).require_vault()
    name = "sha256-" + world["digest"].split(":", 1)[1]
    phone = world["phone"]
    for page, served in ((0, True), (1, True), (2, False), (9, False)):
        prompt = f"Look at [the page](llpdf://localhost/{name}#page={page + 1})."
        status = phone.get(f"/api/v1/reader/page/{name}/{page}").status_code
        assert (status == 200) is served, (page, status)
        assert (_reason(vault, repository, prompt) is None) is served, page
    # Asked without a repository, the vault's database is read (the sidecar's by-id doors); not knowing it is
    # never a lift (fail closed).
    assert _reason(vault, None, f"[p](llpdf://localhost/{name}#page=1)") is None
    assert _reason(SimpleNamespace(root=world["root"]), None, f"[p](llpdf://localhost/{name}#page=1)") == DE.LINKS_LLPDF


def test_f10_a_stored_image_of_an_exam_source_is_not_phone_eligible(world):
    import hashlib

    from tests.test_mobile_v4_reader import _png

    image = _png()
    add_book(world["root"], world["repo"], source_id="src_photo", revision_id="rev_photo",
             extraction_id="ext_photo", held_out=False, data=image)
    vault, repository = desktop(world["root"]).require_vault()
    name = "sha256-" + hashlib.sha256(image).hexdigest()
    prompt = f"![graph](canonical-sources/raw/{name})"
    assert _reason(vault, repository, prompt) is None
    assert world["phone"].get(f"/api/v1/assets/{name}").status_code == 200
    _exam_role(world["root"], "src_photo")
    vault, repository = desktop(world["root"]).require_vault()
    assert _reason(vault, repository, prompt) == DE.EMBEDS_IMAGE
    assert world["phone"].get(f"/api/v1/assets/{name}").status_code == 403


def test_f12_the_media_lift_admits_no_new_measurement_on_the_phone(world):
    """A probe is a measurement (the playbook's 2026-10-17 rule): its media reason stays, so the phone's
    measurements are mvp-0.54's exactly; an ordinary item with the same served stimulus is lifted."""

    vault, repository = desktop(world["root"]).require_vault()
    name = "sha256-" + world["digest"].split(":", 1)[1]
    prompt = f"Look at [the page](llpdf://localhost/{name}#page=1)."
    assert _reason(vault, repository, prompt) is None
    for mode in sorted(DE.MEASUREMENT_MODES):
        assert _reason(vault, repository, prompt, mode=mode) is not None, mode
    from learnloop.scheduling.frame_constraints import FRESH_EVIDENCE_MODES

    assert DE.MEASUREMENT_MODES == FRESH_EVIDENCE_MODES
