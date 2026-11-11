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

from learnloop.scheduling import device_eligibility as DE
from tests.mobile_host_helpers import HOSTNAME, Phone, pair, poll_job, rows
from tests.reread_safety_helpers import _made_on
from tests.mobile_v4_reader_helpers import (  # noqa: F401 - the fixture
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


# -- F1's host half: a revalidation checks the token and the protection again ----------------------------------


def test_f1_a_revalidated_page_is_checked_again_and_a_match_is_a_bodiless_304(world):
    from tests.mobile_host_helpers import bearer, identity

    phone, client = world["phone"], world["client"]
    first = phone.get(f"/api/v1/reader/page/{EXTRACTION}/1")
    assert first.status_code == 200 and first.headers["vary"] == "Authorization"
    etag = first.headers["etag"]
    again = client.get(f"/api/v1/reader/page/{EXTRACTION}/1", headers={**phone.headers, "If-None-Match": etag})
    assert again.status_code == 304 and again.content == b"" and again.headers["etag"] == etag
    # The same validator from no token, or after a mark, is refused: a kept copy is never the host's yes.
    assert client.get(f"/api/v1/reader/page/{EXTRACTION}/1",
                      headers={**identity(), "If-None-Match": etag}).status_code == 401
    world["repo"].upsert_unit_selection(extraction_id=EXTRACTION, source_id="src1", revision_id="rev1",
                                        selected_unit_ids=["u1", "u2", "u3"],
                                        exam_use_modes={"u2": "held_out_evaluation", "u3": "held_out_evaluation"},
                                        exam_paper_metadata=_made_on(EXTRACTION, "rev1"))
    refused = client.get(f"/api/v1/reader/page/{EXTRACTION}/1", headers={**bearer(world["device"]),
                                                                          "If-None-Match": etag})
    assert refused.status_code == 403


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


def _phone_under(world, fragment: str) -> Phone:
    """The world's phone on a host started after ``fragment`` was added to the vault's configuration."""

    from tests.helpers import append_config_toml

    append_config_toml(world["root"], fragment)
    client = TestClient(host(world["root"], world["cache"]), base_url=f"https://{HOSTNAME}")
    client.__enter__()
    world.setdefault("_clients", []).append(client)
    return Phone(client, world["device"], capabilities=READER_APP)


def _close(world) -> None:
    for client in world.pop("_clients", []):
        client.__exit__(None, None, None)


def test_f4_reopened_a_protected_selection_is_withheld_with_reader_inquiry_off(world):
    """Landing ruling R1, Codex's first reproduction: anchored on the safe ``b4``, the selection names the held-out
    ``b6`` and the answer quotes it; the citations name only ``b4``. With ``reader_inquiry`` off the projection has no
    ``selection_span_ids``, and the filter must still see them (it reads the stored provenance, not the projection)."""

    repository = world["repo"]
    payload = {
        "extraction_id": EXTRACTION, "span_id": "b4", "answer_md": "As the exam problem says: prove it.",
        "citations": [{"extraction_id": EXTRACTION, "span_id": "b4", "label": "x"}],
        "manifest": {"question_md": "why?", "selection": {"span_ids": ["b4", "b6"],
                                                          "quote_md": "The span of a list. Exam problem: prove it."}},
    }
    repository.append_interaction_event(kind="reader_answer_submitted", origin="learner", subject_type="reader_span",
                                        subject_id=f"span:{EXTRACTION}/b4", payload_json=json.dumps(payload))
    _exchange(repository, span="b4", selection=["b4"], quote="The span of a list")
    try:
        phone = _phone_under(world, "[reader_inquiry]\nenabled = false\n")
        history = phone.rpc("reader.ask_history", {"extractionId": EXTRACTION})["exchanges"]
        assert [exchange["answerMd"] for exchange in history] == ["An answer about b4."]
        assert "selectionSpanIds" not in history[0]  # the projection is still the switch's
        assert "exam problem" not in json.dumps(history).lower()
    finally:
        _close(world)
    # The desktop's projection is unchanged: both exchanges, flat.
    flat = call(desktop(world["root"]), "reader.ask_history", {"extractionId": EXTRACTION})["exchanges"]
    assert len(flat) == 2 and all("selectionSpanIds" not in exchange for exchange in flat)


def test_f4_reopened_a_protected_excerpt_is_withheld_with_both_tutor_switches_off(world):
    """Landing ruling R1, Codex's second reproduction: the tutor's excerpt is the held-out ``b5`` (named by its
    locator); with both tutor presentation switches off the projection has no ``tutor``, and the filter must still
    see the excerpt."""

    repository = world["repo"]
    payload = {
        "extraction_id": EXTRACTION, "span_id": "b2", "answer_md": "From the review: 3 Exam review.",
        "citations": [],
        "manifest": {"question_md": "why?", "selection": {"span_ids": ["b2"], "quote_md": "Every vector space"}},
        "tutor": {"excerpt": {"locator": f"span:{EXTRACTION}/b5", "text": "3 Exam review"}},
    }
    repository.append_interaction_event(kind="reader_answer_submitted", origin="learner", subject_type="reader_span",
                                        subject_id=f"span:{EXTRACTION}/b2", payload_json=json.dumps(payload))
    _exchange(repository, span="b4", selection=["b4"], quote="The span of a list")
    try:
        phone = _phone_under(world, "[reader_tutor]\nretrieval_enabled = false\noffers_enabled = false\n")
        history = phone.rpc("reader.ask_history", {"extractionId": EXTRACTION})["exchanges"]
        assert [exchange["spanId"] for exchange in history] == ["b4"]
        assert "tutor" not in history[0]  # the projection is still the switches'
        assert "Exam review" not in json.dumps(history)
    finally:
        _close(world)
    assert len(call(desktop(world["root"]), "reader.ask_history", {"extractionId": EXTRACTION})["exchanges"]) == 2


def test_f4_reopened_a_fresh_answer_is_judged_on_what_it_stored_before_the_phone_is_sent_it(world, monkeypatch):
    """Landing ruling R1's sweep, the live Ask: the question is refused up front on its anchor and selection, but
    the answer's citations and excerpt come from the model. One that names a passage withheld from the phone (here
    the held-out ``b6``; on real data an exam unit next to the passage, which the desktop's tutor may read) is
    judged on the event the Ask stored, as its history judges it, and is not sent. The desktop is sent it."""

    import learnloop.reader.reader_dialogue as dialogue
    import learnloop_sidecar.handlers.reader as reader_handlers

    def fake_ask(vault, repository, client, **kwargs):
        payload = {"extraction_id": EXTRACTION, "span_id": kwargs["span_id"], "answer_md": "Exam problem: prove it.",
                   "citations": [{"extraction_id": EXTRACTION, "span_id": "b6", "label": "x"}],
                   "manifest": {"question_md": kwargs["question_md"], "selection": {"span_ids": [kwargs["span_id"]]}}}
        repository.append_interaction_event(kind="reader_answer_submitted", origin="learner",
                                            subject_type="reader_span",
                                            subject_id=f"span:{EXTRACTION}/{kwargs['span_id']}",
                                            payload_json=json.dumps(payload))
        event_id = [event["id"] for event in repository.reader_interaction_events(kind="reader_answer_submitted")][-1]
        return {"event_id": "qe_fake", "reader_answer_event_id": event_id, "answer_md": payload["answer_md"],
                "answer_mode": "explain", "citations": payload["citations"], "manifest": payload["manifest"],
                "warmed_surface_ids": [], "burned_surface_ids": [], "hint_equivalent": False, "remaining": 9}

    monkeypatch.setattr(reader_handlers, "ready_tutor_qa_provider",
                        lambda vault: ("fake", SimpleNamespace(ready=True), object()))
    monkeypatch.setattr(dialogue, "ask", fake_ask)
    response = world["phone"].post("reader.ask", {"extractionId": EXTRACTION, "spanId": "b4", "question": "why?"},
                                   request_id="ask_cites_held")
    body = response.json()
    if response.status_code == 202:
        body = poll_job(world["phone"], body["accepted"]["job_id"])
    assert "Exam problem" not in json.dumps(body)
    assert (body.get("error") or {}).get("code") == "held_out_material", body
    # The desktop (a None origin) is sent the answer, as before.
    answered = call(desktop(world["root"]), "reader.ask", {"extractionId": EXTRACTION, "spanId": "b4",
                                                           "question": "why?"})
    assert "Exam problem: prove it." in json.dumps(answered, default=str)


class _VaultWith:
    """The world's vault with other practice items (the rest is the real vault's)."""

    def __init__(self, real: Any, items: dict[str, Any]) -> None:
        self._real, self.practice_items = real, items

    def __getattr__(self, name: str) -> Any:
        return getattr(self._real, name)


def _placed(item_id: str, prompt: str) -> dict[str, Any]:
    return {"practice_item_id": item_id, "prompt": prompt, "placement": "owner_reviewed"}


def test_f4_reopened_the_guide_plans_placed_question_is_judged_by_its_items_stored_source(world):
    """Landing ruling R1's sweep of the other phone reads: a placed (owner-reviewed) guide question projects no
    span at all, so the phone judged it by its section only. Its item's own source (canonical exercise, source
    refs) is what it is stored with: a placement of an item cut from the held-out ``b6`` into the safe section
    ``u2`` is not sent; one cut from ``b1`` is; one whose item can't be read is not (fail closed)."""

    from learnloop.vault.loader import load_vault
    from learnloop_sidecar.handlers.reader import _phone_guide_plan

    def item(span: str) -> Any:
        ref = SimpleNamespace(extraction_id=EXTRACTION, span_ids=[span], locator=None)
        return SimpleNamespace(canonical_exercise=None, provenance=SimpleNamespace(source_refs=[ref]))

    vault = _VaultWith(load_vault(world["root"]), {"pi_exam": item("b6"), "pi_safe": item("b1")})
    plan = {"sections": [
        {"id": "u1", "span_ids": ["b0", "b1", "b2"], "question": _placed("pi_safe", "What is a vector space?"),
         "suggested_passages": []},
        {"id": "u2", "span_ids": ["b3", "b4"], "question": _placed("pi_exam", "Exam problem: prove it."),
         "suggested_passages": []},
        {"id": "u2b", "span_ids": ["b3"], "question": _placed("pi_gone", "Gone."), "suggested_passages": []},
    ]}
    phone = _phone_guide_plan(vault, world["repo"], EXTRACTION, plan)
    assert [section["question"] and section["question"]["practice_item_id"] for section in phone["sections"]] == [
        "pi_safe", None, None]
    assert "Exam problem" not in json.dumps(phone)


def test_landing_smoke_a_held_out_sections_heading_is_not_its_label_on_the_phone(world):
    """Found by the landing's smoke on the owner's arxiv_v2 copy: the guide plan sent a held-out section's heading
    (its first block, withheld in the text) as the section's label. The phone gets a plain label instead; the
    section, its id and its span ids stay, so the list, progress and place still line up. The desktop is unchanged."""

    plan = world["phone"].rpc("reader.guide_plan", {"extractionId": EXTRACTION})
    labels = {section["id"]: section["label"] for section in plan["sections"]}
    assert labels["u1"] == "1 Vectors" and labels["u2"] == "2 Spans"
    assert labels["u3"] != "3 Exam review" and "Exam review" not in json.dumps(plan)
    assert next(section for section in plan["sections"] if section["id"] == "u3")["spanIds"] == ["b5", "b6"]
    desk = call(desktop(world["root"]), "reader.guide_plan", {"extractionId": EXTRACTION})
    assert {section["id"]: section["label"] for section in desk["sections"]}["u3"] == "3 Exam review"


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
    from tests.ad1_reading_opportunities_helpers import FakeMap, _setup
    from tests.ad3_dose_arm_helpers import QUIET
    from tests.ad1_reading_opportunities_helpers import _question
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


# -- Codex re-review F13, F14: the question action is judged by its anchors and its source's Reader switch -------


def test_f13_a_question_anchored_on_a_protected_passage_is_refused_even_when_it_cites_a_safe_one(world):
    repository = world["repo"]
    # Anchored on b6 (the held-out section's problem, quoted in the prompt), citing b4 (safe) as its answer.
    question_id = repository.insert_reader_authored_question(fields={
        "extraction_id": EXTRACTION, "section_id": "u2", "source_id": "src1",
        "question_md": "Exam problem: prove that the zero vector is unique. What comes next?",
        "expected_answer_md": "The span of a list.", "span_ids": ["b4"], "prompt_version": "qc-v1",
        "scope_kind": "inquiry", "question_style": "next_step", "anchor_span_ids": ["b6"],
        "inquiry_root_event_id": "root-13",
    })
    status, error = world["phone"].error("reader.authored_question_action",
                                         {"questionId": question_id, "action": "answered", "response": "x"})
    assert (status, error["code"]) == (409, "held_out_material")
    assert "zero vector is unique" not in json.dumps(error)
    row = repository.get_reader_authored_question(question_id)
    assert row["status"] != "answered" and row.get("response_md") in (None, "")
    # The desktop (a None origin) is unchanged: its own card answers it as before.
    answered = call(desktop(world["root"]), "reader.authored_question_action",
                    {"question_id": question_id, "action": "answered", "response": "desktop words"})
    assert answered["question"]["status"] == "answered"


def test_f14_a_question_of_a_source_opted_out_of_the_reader_is_refused_on_the_phone(world):
    repository = world["repo"]
    question_id = repository.insert_reader_authored_question(fields={
        "extraction_id": EXTRACTION, "section_id": "u2", "source_id": "src1", "question_md": "What is a span?",
        "expected_answer_md": "All linear combinations.", "span_ids": ["b4"], "prompt_version": "qc-v1",
        "scope_kind": "inquiry", "question_style": "recall", "anchor_span_ids": ["b4"],
        "inquiry_root_event_id": "root-14",
    })
    with repository.connection() as connection:
        connection.execute("UPDATE source_artifacts SET reader_enabled = 0 WHERE id = 'src1'")
        connection.commit()
    status, error = world["phone"].error("reader.authored_question_action",
                                         {"questionId": question_id, "action": "answered", "response": "x"})
    assert error["code"] == "reader_disabled_for_source", (status, error)
    assert "All linear combinations" not in json.dumps(error)
    row = repository.get_reader_authored_question(question_id)
    assert row["status"] != "answered" and row.get("response_md") in (None, "")


# -- F10, F12: eligibility is the media endpoint's own predicate, and admits no new measurement -----------------


def _item(prompt: str, *, mode: str = "short_answer"):
    return SimpleNamespace(id="pi_x", practice_mode=mode, teach_back_source=None, error_hunt=None,
                           laddered_stem=None, prompt=prompt, provenance=None, lesson_id=None, lifecycle=None)


def _reason(vault, repository, prompt: str, *, mode: str = "short_answer", served: Any = "host") -> str | None:
    """The phone's reason, with the host's own predicate injected as the sidecar injects it."""

    from unittest import mock

    from learnloop.reader.phone_media import media_predicate

    predicate = media_predicate(vault, repository) if served == "host" else served
    with mock.patch.object(DE, "minted_for_lesson", lambda item: False):
        return DE.ineligibility_reason(vault, _item(prompt, mode=mode), DE.PHONE, media=True, served=predicate)


def test_f10_a_page_is_phone_eligible_exactly_when_the_page_endpoint_serves_it(world):
    vault, repository = desktop(world["root"]).require_vault()
    name = "sha256-" + world["digest"].split(":", 1)[1]
    phone = world["phone"]
    for page, served in ((0, True), (1, True), (2, False), (9, False)):
        prompt = f"Look at [the page](llpdf://localhost/{name}#page={page + 1})."
        status = phone.get(f"/api/v1/reader/page/{name}/{page}").status_code
        assert (status == 200) is served, (page, status)
        assert (_reason(vault, repository, prompt) is None) is served, page
    # Asked without a repository, the vault's database is read (the sidecar's by-id doors); not knowing it, or no
    # predicate at all, is never a lift (fail closed).
    link = f"[p](llpdf://localhost/{name}#page=1)"
    assert _reason(vault, None, link) is None
    assert _reason(SimpleNamespace(root=world["root"]), None, link) == DE.LINKS_LLPDF
    assert _reason(vault, repository, link, served=None) == DE.LINKS_LLPDF
    # The sidecar's by-id door injects the same predicate (an item a stale list names).
    from learnloop_sidecar.request_origin import RequestOrigin
    from learnloop_sidecar.serving import origin_ineligibility
    from unittest import mock

    origin = RequestOrigin(device_id="dev", phone_reader=True)
    with mock.patch.object(DE, "minted_for_lesson", lambda item: False):
        assert origin_ineligibility(origin, vault, _item(link)) is None
        assert origin_ineligibility(origin, vault, _item(f"[p](llpdf://localhost/{name}#page=3)")) == DE.LINKS_LLPDF


def test_f10_a_stored_image_of_an_exam_source_is_not_phone_eligible(world):
    import hashlib

    from tests.mobile_v4_reader_helpers import _png

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
