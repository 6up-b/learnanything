"""RW1b's Codex review fixes (docs/reviews/reader-rw1b-codex-review.md).

Each test reproduces one finding on the stage tip before its fix:

* F1  a missed formative answer's gap is never a numeric serving signal (no
      weak prerequisite observation for placement, no sooner check);
* F2  the intent box's daily call allowance is reserved atomically, so two
      routings racing for the last call (or the last speculative one) admit one;
* F3  every routing is its own ledger question, so identical routings never
      record each other's fate or correction;
* F4  "change" reverts the capture the routed action made;
* F5  "reconstruct this later" is crash-idempotent: one item whatever write
      a retry follows;
* F6  a reconstruction undone stays undone (never a second success receipt);
* F7  a missed self-check and its learner-text job commit together, and the
      backlog sweep recovers a missed answer without a job;
* F12 the report's correction denominator is every used Decider routing
      (Enter-only included); a fate asked of a routing still in flight lands
      when it finishes;
* F13 answering writes no practice item; "add to practice" makes exactly one.

Every model is a fake.
"""

from __future__ import annotations

import dataclasses
import json
import threading
from contextlib import closing

import pytest

from learnloop.clock import FrozenClock
from learnloop.curriculum import commitments as C
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.reader import active_reading as AR
from learnloop.reader import reader_capture as RC
from learnloop.reader import reader_intent as RI
from learnloop.reader import reader_quick_check as RQC
from learnloop.vault.loader import load_vault
from tests.helpers import NOW, append_config_toml
from tests.recap_fixtures import call, context
from tests.test_reader_active_reading import ActiveClient
from tests.test_reader_guidance import _setup
from tests.test_reader_intent import ON, FakeDecider, _prefer
from tests.test_reader_reconstruct import LO, _reconstruct

CLOCK = FrozenClock(NOW)


def _ledger(repo):
    with repo.connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT * FROM judgment_ledger WHERE task = 'reader_intent' ORDER BY created_at, rowid")]


# -- F1: formative gaps are not serving signals ---------------------------------------------------


def test_f1_a_formative_gap_is_not_a_weak_prerequisite_signal(tmp_path):
    from learnloop.field.signals import learner_gap_targets
    from tests.test_learner_text_gaps_flow import _setup as gap_setup

    root, repository = gap_setup(tmp_path)
    from learnloop.db.stores import learner_gaps as store

    base = {"attempt_id": None, "practice_item_id": None, "anchor_learning_object_id": "lo_spectral",
            "subject_id": None, "learner_text": "x", "chooser": "context_model", "context_judge": "gap_reader",
            "context_kind": None, "decider_kind": None, "decider_json": {}, "kind": "prerequisite",
            "named_json": {}, "action": "matched_prerequisite", "target_kind": "learning_object",
            "target_id": "lo_eigen_basics", "target_subject_id": None, "match_basis": "decider", "edge_id": None,
            "created_concept_id": None, "created_learning_object_id": None, "seed_practice_item_id": None,
            "seed_status": None, "detail_json": {}, "algorithm_version": "mvp-0.16", "pipeline_version": "t",
            "created_at": NOW.isoformat()}
    with repository.atomic():
        store.insert_gap(repository.connection(), {**base, "source_kind": "tutor_question", "source_id": "qe_1"})
        store.insert_gap(repository.connection(), {**base, "source_kind": "reader_formative", "source_id": "raq_1"})
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        targets = learner_gap_targets(connection, load_vault(root))
    assert [t["source_kind"] for t in targets] == ["tutor_question"]


def test_f1_a_formative_gap_brings_no_check_forward(tmp_path):
    from learnloop.db.stores import learner_gaps as store
    from learnloop.diagnosis.text_gaps.pipeline import process_learner_text
    from learnloop.diagnosis.text_gaps.sources import tutor_question_text
    from learnloop.placement.decisions import record_self_report
    from learnloop.tutor.tutor_qa import ask_question
    from tests.test_learner_text_gaps_flow import EIGEN_GAP, _at, _clients
    from tests.test_learner_text_gaps_flow import _setup as gap_setup
    from tests.text_gap_fakes import GapLLMFake, GapTutor, word_match

    root, repository = gap_setup(tmp_path)
    record_self_report(load_vault(root), repository, learning_object_ids=["lo_eigen_basics"], report="know_this",
                       clock=_at(1))
    vault = load_vault(root)
    event_id = ask_question(vault, repository, GapTutor(EIGEN_GAP), context="practice",
                            question_md="What's an eigenvalue?", practice_item_id="pi_spec_easy",
                            session_id="sess_gap", clock=_at(5))["event_id"]
    asked = tutor_question_text(vault, repository, event_id)
    # The same words, as a missed active-reading answer (the kind RW1b adds).
    text = dataclasses.replace(asked, source_kind="reader_formative", source_id="raq_formative",
                               question_event_id=None)
    row = process_learner_text(root, repository, text,
                               clients=_clients(GapLLMFake(decide=word_match("eigenvalues"))), clock=_at(10))
    assert row["action"] == "matched_prerequisite" and row["target_id"] == "lo_eigen_basics"
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        assert store.check_advances(connection) == []


# -- F2: the allowance is reserved atomically ---------------------------------------------------


def _race(vault, repo, *, speculative: bool, n: int = 2):
    barrier = threading.Barrier(n, timeout=10)
    decider = FakeDecider(choice=_prefer("test_me_later"))

    def factory():
        barrier.wait()
        return decider

    results: list = [None] * n

    def run(index: int) -> None:
        worker = Repository.attach(repo.sqlite_path)
        results[index] = RI.route(vault.root, vault.config, worker, text=f"quiz me {index}", quote="q",
                                  extraction_id="ext1", span_ids=["s1"], available=ON, speculative=speculative,
                                  client_factory=factory, clock=CLOCK)

    threads = [threading.Thread(target=run, args=(i,)) for i in range(n)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(30)
    return results, decider


def _vault_with(vault, toml):
    append_config_toml(vault.root, toml)
    return load_vault(vault.root)


def test_f2_two_routings_racing_for_the_last_call_admit_one(tmp_path):
    vault, repo = _setup(tmp_path)
    vault = _vault_with(vault, "\n[reader_intent]\nmax_calls_per_day = 1\n")
    results, decider = _race(vault, repo, speculative=False)
    assert len(decider.calls) == 1
    assert sorted((r.status, r.reason) for r in results) == [("fallback", "capped"), ("routed", None)]
    assert RI.calls_today(repo, clock=CLOCK) == 1


def test_f2_two_speculations_racing_for_the_last_speculative_call_admit_one(tmp_path):
    vault, repo = _setup(tmp_path)
    vault = _vault_with(vault, "\n[reader_intent]\nmax_calls_per_day = 5\n")
    for i in range(3):
        RI.route(vault.root, vault.config, repo, text=f"earlier {i}", quote="q", extraction_id="ext1",
                 span_ids=["s1"], available=ON, speculative=True,
                 client_factory=lambda: FakeDecider(choice=_prefer("test_me_later")), clock=CLOCK)
    results, decider = _race(vault, repo, speculative=True)
    assert len(decider.calls) == 1
    assert sorted(r.status for r in results) == ["not_made", "routed"]
    # Enter still routes until the cap.
    enter = RI.route(vault.root, vault.config, repo, text="now", quote="q", extraction_id="ext1", span_ids=["s1"],
                     available=ON, client_factory=lambda: FakeDecider(choice=_prefer("test_me_later")), clock=CLOCK)
    assert enter.status == "routed" and RI.calls_today(repo, clock=CLOCK) == 5


def test_f2_an_unavailable_decider_spends_no_allowance(tmp_path):
    from learnloop.ai.errors import AIProviderUnavailable

    vault, repo = _setup(tmp_path)

    def down():
        raise AIProviderUnavailable("Decider unavailable")

    routing = RI.route(vault.root, vault.config, repo, text="quiz me", quote="q", extraction_id="ext1",
                       span_ids=["s1"], available=ON, client_factory=down, clock=CLOCK)
    assert routing.reason == "unavailable" and RI.calls_today(repo, clock=CLOCK) == 0


# -- F3: each routing is its own ledger question --------------------------------------------------


def test_f3_identical_routings_keep_their_own_fates_and_corrections(tmp_path):
    vault, repo = _setup(tmp_path)

    def same():
        return RI.route(vault.root, vault.config, repo, text="quiz me later", quote="q", extraction_id="ext1",
                        span_ids=["s1"], available=ON, speculative=True,
                        client_factory=lambda: FakeDecider(choice=_prefer("test_me_later")), clock=CLOCK)

    a, b = same(), same()
    assert a.input_hash == b.input_hash
    fate_a = RI.record_fate(repo, a.judgment_id, "discarded")
    fate_b = RI.record_fate(repo, b.judgment_id, "used")
    assert fate_a is not None and fate_b is not None
    rows = {row["id"]: row for row in _ledger(repo)}
    assert rows[fate_a]["supersedes_id"] == a.judgment_id
    assert rows[fate_b]["supersedes_id"] == b.judgment_id
    assert json.loads(rows[fate_b]["rationale"])["fate"] == "used"
    correction = RI.record_correction(repo, b.judgment_id, "help_me_remember")
    assert _ledger(repo)[-1]["id"] == correction
    assert {row["id"]: row for row in _ledger(repo)}[correction]["supersedes_id"] == fate_b
    # The routing's ledger question is its own: the routing id, never the shared input.
    assert rows[a.judgment_id]["left_id"] != rows[b.judgment_id]["left_id"]
    assert rows[a.judgment_id]["input_hash"] == rows[b.judgment_id]["input_hash"]


# -- F4: "change" reverts the routed capture ------------------------------------------------------


def test_f4_change_reverts_the_routed_capture_its_commitment_and_its_request(tmp_path):
    vault, _repo = _setup(tmp_path)
    ctx = context(vault.root)
    ctx.reader_intent_inline = True
    ctx.reader_intent_client_factory = lambda: FakeDecider(choice=_prefer("help_me_remember"))
    _v, repo = ctx.require_vault()
    started = call(ctx, "reader.route_intent", {"extractionId": "ext1", "spanIds": ["s1"], "text": "remember this"})
    assert started["action"] == "help_me_remember"
    receipt = RC.invoke_preset(repo, preset="help_me_remember", source_id="src1", revision_id="rev1",
                               extraction_id="ext1", client_idempotency_key="intent-1",
                               raw_selection={"nodes": [{"span_id": "s1", "quote": "The singular"}]},
                               learner_text="remember this", subject_id="s1")
    RC.drain_outbox(repo)
    (request,) = repo.reader_requests_for_source("src1")
    reverted = call(ctx, "reader.intent_outcome", {"routingId": started["routingId"], "outcome": "reverted",
                                                   "annotationId": receipt["annotation_id"]})
    assert reverted["recorded"] is True
    assert reverted["reverted"] == {"annotationId": receipt["annotation_id"],
                                    "commitmentId": receipt["commitment_id"], "requestId": request["id"]}
    assert C.resolve_disposition(repo, receipt["commitment_id"]) == "stopped"
    assert repo.get_reader_request(request["id"])["status"] == "cancelled"
    listed = [a.get("annotation_id") for a in repo.source_annotations("src1")] \
        if hasattr(repo, "source_annotations") else None
    with repo.connection() as connection:
        events = [row[0] for row in connection.execute(
            "SELECT event_type FROM source_annotation_events WHERE annotation_id = ?", (receipt["annotation_id"],))]
    assert "delete_intent" in events
    assert listed is None or receipt["annotation_id"] not in listed
    # Reverting again changes nothing more.
    again = call(ctx, "reader.intent_outcome", {"routingId": started["routingId"], "outcome": "reverted",
                                                "annotationId": receipt["annotation_id"]})
    assert again["reverted"]["commitmentId"] == receipt["commitment_id"]
    with repo.connection() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM source_annotation_events WHERE annotation_id = ? AND event_type = 'delete_intent'",
            (receipt["annotation_id"],)).fetchone()[0] == 1


def test_f4_only_a_capture_routing_reverts(tmp_path):
    from learnloop_sidecar.errors import SidecarError

    vault, _repo = _setup(tmp_path)
    ctx = context(vault.root)
    ctx.reader_intent_inline = True
    ctx.reader_intent_client_factory = lambda: FakeDecider(choice=_prefer("ask_help_me_reason"))
    started = call(ctx, "reader.route_intent", {"extractionId": "ext1", "spanIds": ["s1"], "text": "why?"})
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.intent_outcome", {"routingId": started["routingId"], "outcome": "reverted",
                                            "annotationId": "ann_x"})
    assert caught.value.code == "validation_error"


# -- F5 / F6: reconstruct ---------------------------------------------------------------------------


def _reader_items(root):
    return sorted(item_id for item_id in load_vault(root).practice_items if item_id.startswith("pi_reader_"))


def test_f5_a_crash_after_the_item_is_written_leaves_one_item(tmp_path, monkeypatch):
    vault, repo = _setup(tmp_path)
    row = _reconstruct(repo)
    real = repo.transition_reader_authored_question
    crashed: list = []

    def crash_once(**kwargs):
        if not crashed:
            crashed.append(True)
            raise RuntimeError("crash between the item and its link")
        return real(**kwargs)

    monkeypatch.setattr(repo, "transition_reader_authored_question", crash_once)
    with pytest.raises(RuntimeError):
        AR.reconstruct_commit(vault.root, repo, question_id=row["id"], learning_object_id=LO, clock=CLOCK)
    made = AR.reconstruct_commit(vault.root, repo, question_id=row["id"], learning_object_id=LO, clock=CLOCK)
    assert _reader_items(vault.root) == [made["practice_item_id"]]
    assert repo.get_reader_authored_question(row["id"])["practice_item_id"] == made["practice_item_id"]


def test_f5_a_crash_before_the_commitment_leaves_one_item_and_one_commitment(tmp_path, monkeypatch):
    vault, repo = _setup(tmp_path)
    row = _reconstruct(repo)
    real = C.create_commitment
    crashed: list = []

    def crash_once(*args, **kwargs):
        if not crashed:
            crashed.append(True)
            raise RuntimeError("crash between the link and the commitment")
        return real(*args, **kwargs)

    monkeypatch.setattr(AR.C, "create_commitment", crash_once)
    with pytest.raises(RuntimeError):
        AR.reconstruct_commit(vault.root, repo, question_id=row["id"], learning_object_id=LO, clock=CLOCK)
    made = AR.reconstruct_commit(vault.root, repo, question_id=row["id"], learning_object_id=LO, clock=CLOCK)
    assert _reader_items(vault.root) == [made["practice_item_id"]]
    with repo.connection() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM commitments WHERE created_action = 'test_me_later'").fetchone()[0] == 1


def test_f6_an_undone_reconstruction_is_never_reported_as_scheduled_again(tmp_path):
    from learnloop_sidecar.errors import SidecarError

    vault, _repo = _setup(tmp_path)
    ctx = context(vault.root)
    _v, repo = ctx.require_vault()
    row = _reconstruct(repo)
    call(ctx, "reader.reconstruct", {"questionId": row["id"], "learningObjectId": LO})
    call(ctx, "reader.reconstruct_undo", {"questionId": row["id"]})
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.reconstruct", {"questionId": row["id"], "learningObjectId": LO})
    assert caught.value.code == "reconstruct_undone"
    _v, repo = ctx.require_vault()
    with pytest.raises(AR.ActiveReadingError):
        AR.reconstruct_commit(vault.root, repo, question_id=row["id"], learning_object_id=LO, clock=CLOCK)
    status = call(ctx, "reader.active_question_status", {"extractionId": "ext1", "anchorSpanIds": ["s1", "s2"],
                                                         "style": "reconstruct"})
    assert status["question"]["reconstruct"]["disposition"] == "stopped"


# -- F7: the self-check and its job are one transaction -------------------------------------------


def _answered_next_step(repo, owner="job_f7", spans=("s1",)):
    row = RQC.author_selection_question(repo, ActiveClient(), extraction_id="ext1", anchor_span_ids=list(spans),
                                        style="next_step", clock=CLOCK, owner=owner)
    RQC.record_selection_action(repo, question_id=row["id"], action="answered", response_md="U is diagonal",
                                clock=CLOCK)
    return row


def _gap_jobs(repo):
    with repo.connection() as connection:
        return [tuple(r) for r in connection.execute("SELECT source_kind, source_id FROM learner_text_gap_jobs")]


def test_f7_a_failed_enqueue_leaves_the_self_check_unrecorded(tmp_path, monkeypatch):
    from learnloop.db.stores import learner_gaps as store

    vault, _repo = _setup(tmp_path)
    ctx = context(vault.root)
    monkeypatch.setattr(ctx.post_attempt_worker, "notify", lambda: None)
    _v, repo = ctx.require_vault()
    row = _answered_next_step(repo)
    real = store.enqueue_job

    def crash(*args, **kwargs):
        raise RuntimeError("stopped before the job")

    monkeypatch.setattr(store, "enqueue_job", crash)
    with pytest.raises(RuntimeError):
        call(ctx, "reader.active_question_action", {"questionId": row["id"], "action": "self_checked",
                                                    "selfCheck": "no"})
    after = repo.get_reader_authored_question(row["id"])
    assert after["self_check"] is None and _gap_jobs(repo) == []
    with repo.connection() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM judgment_ledger WHERE judge = 'learner_card' AND right_id = ?",
            (row["id"],)).fetchone()[0] == 0
    # The learner can still self-check, and this time the job is queued.
    monkeypatch.setattr(store, "enqueue_job", real)
    done = call(ctx, "reader.active_question_action", {"questionId": row["id"], "action": "self_checked",
                                                       "selfCheck": "no"})
    assert done["formativeJobId"] and _gap_jobs(repo) == [("reader_formative", row["id"])]


def test_f7_the_backlog_sweep_recovers_a_missed_answer_without_a_job(tmp_path):
    from learnloop.diagnosis.text_gaps.jobs import sweep_backlog

    vault, repo = _setup(tmp_path)
    row = _answered_next_step(repo)
    RQC.record_selection_action(repo, question_id=row["id"], action="self_checked", self_check="partly",
                                clock=CLOCK)
    assert _gap_jobs(repo) == []
    assert sweep_backlog(vault, repo, dry_run=True)["reader_formative"] == 1
    assert sweep_backlog(vault, repo)["reader_formative"] == 1
    assert _gap_jobs(repo) == [("reader_formative", row["id"])]
    assert sweep_backlog(vault, repo)["reader_formative"] == 0
    off = _vault_with(vault, "\n[reader_formative]\nenabled = false\n")
    other = _answered_next_step(repo, owner="job_f7b", spans=("s0", "s1"))
    RQC.record_selection_action(repo, question_id=other["id"], action="self_checked", self_check="no", clock=CLOCK)
    assert sweep_backlog(off, repo)["reader_formative"] == 0


# -- F12: the report and late fates ---------------------------------------------------------------


def test_f12_an_enter_only_use_and_its_correction_are_counted(tmp_path):
    from learnloop.reader.reader_report import build_reader_report

    vault, _repo = _setup(tmp_path)
    append_config_toml(vault.root, "\n[reader_intent]\nspeculative_enabled = false\n")
    ctx = context(vault.root)
    ctx.reader_intent_inline = True
    ctx.reader_intent_client_factory = lambda: FakeDecider(choice=_prefer("test_me_later"))
    enter = call(ctx, "reader.route_intent", {"extractionId": "ext1", "spanIds": ["s1"], "text": "quiz me"})
    call(ctx, "reader.intent_outcome", {"routingId": enter["routingId"], "outcome": "used"})
    call(ctx, "reader.intent_outcome", {"routingId": enter["routingId"], "outcome": "corrected",
                                        "action": "help_me_remember"})
    # A fallback that ran Ask is used too, but it is no Decider routing to correct.
    ctx.reader_intent_client_factory = lambda: FakeDecider()  # a tie: Ask
    tied = call(ctx, "reader.route_intent", {"extractionId": "ext1", "spanIds": ["s1"], "text": "hmm"})
    assert tied["status"] == "fallback"
    call(ctx, "reader.intent_outcome", {"routingId": tied["routingId"], "outcome": "used"})
    _v, repo = ctx.require_vault()
    report = build_reader_report(repo.sqlite_path)["intent"]
    assert report["used"] == 2 and report["used_speculative"] == 0
    assert report["corrected"] == {"count": 1, "of": 1, "share": 1.0}


def test_f12_a_fate_asked_while_the_routing_runs_lands_when_it_finishes(tmp_path):
    vault, _repo = _setup(tmp_path)
    ctx = context(vault.root)
    gate = threading.Event()
    ctx.reader_intent_client_factory = lambda: FakeDecider(choice=_prefer("test_me_later"), gate=gate)
    started = call(ctx, "reader.route_intent", {"extractionId": "ext1", "spanIds": ["s1"], "text": "quiz me",
                                                "speculative": True})
    assert started["state"] == "pending"
    deferred = call(ctx, "reader.intent_outcome", {"routingId": started["routingId"], "outcome": "discarded"})
    assert deferred == {"routingId": started["routingId"], "recorded": False, "deferred": True,
                        **({"version": deferred["version"]} if "version" in deferred else {})}
    gate.set()
    done = call(ctx, "reader.intent_routing", {"routingId": started["routingId"], "waitMs": 1000})
    for _ in range(20):
        if done["state"] == "done":
            break
        done = call(ctx, "reader.intent_routing", {"routingId": started["routingId"], "waitMs": 1000})
    assert done["state"] == "done"
    running = ctx.reader_intent_routings.get(started["routingId"])
    assert running.fate_done.wait(5)
    _v, repo = ctx.require_vault()
    fates = [json.loads(row["rationale"]).get("fate") for row in _ledger(repo)]
    assert fates == ["pending", "discarded"]


# -- F13: add to practice ---------------------------------------------------------------------------


def test_f13_answering_makes_no_item_and_add_to_practice_makes_exactly_one(tmp_path):
    vault, _repo = _setup(tmp_path)
    ctx = context(vault.root)
    _v, repo = ctx.require_vault()
    row = RQC.author_selection_question(repo, ActiveClient(), extraction_id="ext1", anchor_span_ids=["s1"],
                                        style="next_step", clock=CLOCK, owner="job_13")
    before = _reader_items(vault.root)
    call(ctx, "reader.active_question_action", {"questionId": row["id"], "action": "answered", "response": "x"})
    assert _reader_items(vault.root) == before
    first = call(ctx, "reader.escalate_authored_question", {"questionId": row["id"], "learningObjectId": LO})
    again = call(ctx, "reader.escalate_authored_question", {"questionId": row["id"], "learningObjectId": LO})
    assert first["practiceItemId"] == again["practiceItemId"]
    assert _reader_items(vault.root) == [*before, first["practiceItemId"]]
    status = call(ctx, "reader.active_question_status", {"extractionId": "ext1", "anchorSpanIds": ["s1"],
                                                         "style": "next_step"})
    assert status["question"]["status"] == "escalated"
