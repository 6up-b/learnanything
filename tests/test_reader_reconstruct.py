"""RW1b's "reconstruct this later" (spec_reader_workbench_v1 §4.2; gates G4, G51).

The reconstruct question is escalated through the quick check's own
escalation into exactly one ordinary practice item, and exactly one
``test_me_later`` commitment on that item is added (dated a few days ahead),
both undoable; repeating the act creates nothing more. Before escalation the
question is formative and writes no attempt (G4).
"""

from __future__ import annotations

import json

import pytest

from learnloop.clock import FrozenClock
from learnloop.curriculum import commitments as C
from learnloop.reader import active_reading as AR
from learnloop.reader import reader_quick_check as RQC
from learnloop.reader.ai_contracts import ReadingActiveCheck
from learnloop.vault.loader import load_vault
from tests.helpers import NOW
from tests.recap_fixtures import call, context, table_counts
from tests.test_reader_active_reading import ActiveClient
from tests.test_reader_guidance import _setup

CLOCK = FrozenClock(NOW)
LO = "lo_svd_definition"


def _reconstruct(repo):
    client = ActiveClient(ReadingActiveCheck(question_md="Derive the SVD's form without looking at the book.",
                                             span_ids=["s1"]))
    return RQC.author_selection_question(repo, client, extraction_id="ext1", anchor_span_ids=["s1", "s2"],
                                         style="reconstruct", clock=CLOCK, owner="job_r")


def _commitments(repo):
    with repo.connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT id, created_action, idempotency_key FROM commitments WHERE created_action = 'test_me_later'")]


def test_reconstruct_makes_one_item_and_one_test_me_later_commitment(tmp_path):
    vault, repo = _setup(tmp_path)
    row = _reconstruct(repo)
    before = table_counts(repo)
    first = AR.reconstruct_commit(vault.root, repo, question_id=row["id"], learning_object_id=LO, clock=CLOCK)
    again = AR.reconstruct_commit(vault.root, repo, question_id=row["id"], learning_object_id=LO, clock=CLOCK)
    assert (again["practice_item_id"], again["commitment_id"]) == (first["practice_item_id"], first["commitment_id"])
    loaded = load_vault(vault.root)
    item = loaded.practice_items[first["practice_item_id"]]
    assert item.prompt == row["question_md"] and item.expected_answer == row["expected_answer_md"]
    assert item.provenance.origin == "codex_proposal"
    (commitment,) = _commitments(repo)
    assert commitment["id"] == first["commitment_id"]
    head = C.resolve_head(repo, first["commitment_id"])
    with repo.connection() as connection:
        due_hint = connection.execute("SELECT due_hint FROM commitment_versions WHERE id = ?", (head.id,)).fetchone()[0]
    assert due_hint == first["due_hint"]
    assert [(t.target_kind, t.target_ref) for t in head.targets] == [("legacy_practice_item", first["practice_item_id"])]
    assert C.resolve_disposition(repo, first["commitment_id"]) == "one_check_pending"
    # Nothing was attempted: the item is new, with no attempt or evidence.
    after = table_counts(repo)
    for table in ("practice_attempts", "grading_evidence", "probe_observations"):
        assert after.get(table, 0) == before.get(table, 0)


def test_undo_retires_the_commitment_and_the_item(tmp_path):
    vault, repo = _setup(tmp_path)
    row = _reconstruct(repo)
    made = AR.reconstruct_commit(vault.root, repo, question_id=row["id"], learning_object_id=LO, clock=CLOCK)
    undone = AR.reconstruct_undo(vault.root, repo, question_id=row["id"], clock=CLOCK)
    assert undone["commitment_id"] == made["commitment_id"]
    assert C.resolve_disposition(repo, made["commitment_id"]) == "stopped"
    assert load_vault(vault.root).practice_items[made["practice_item_id"]].status == "retired"
    # Undo is idempotent.
    AR.reconstruct_undo(vault.root, repo, question_id=row["id"], clock=CLOCK)
    assert len(_commitments(repo)) == 1


def test_reconstruct_needs_a_reconstruct_question(tmp_path):
    vault, repo = _setup(tmp_path)
    next_step = RQC.author_selection_question(repo, ActiveClient(), extraction_id="ext1", anchor_span_ids=["s1"],
                                              style="next_step", clock=CLOCK, owner="job_n")
    with pytest.raises(AR.ActiveReadingError):
        AR.reconstruct_commit(vault.root, repo, question_id=next_step["id"], learning_object_id=LO, clock=CLOCK)


def test_the_rpcs_commit_and_undo_and_say_when_no_objective_is_linked(tmp_path):
    from learnloop_sidecar.errors import SidecarError

    vault, _repo = _setup(tmp_path)
    ctx = context(vault.root)
    _v, repo = ctx.require_vault()
    row = _reconstruct(repo)
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.reconstruct", {"questionId": row["id"]})
    assert caught.value.code == "no_learning_object"
    made = call(ctx, "reader.reconstruct", {"questionId": row["id"], "learningObjectId": LO})
    assert made["question"]["status"] == "escalated"
    assert made["question"]["reconstruct"]["disposition"] == "one_check_pending"
    _v, repo = ctx.require_vault()
    with repo.connection() as connection:
        events = [json.loads(p[0]).get("event") for p in connection.execute(
            "SELECT payload_json FROM interaction_events WHERE kind = 'reader_action_invoked'")]
    assert "reconstruct_committed" in events
    undone = call(ctx, "reader.reconstruct_undo", {"questionId": row["id"]})
    assert undone["question"]["reconstruct"]["disposition"] == "stopped"
    _vault, _repo2 = ctx.require_vault()
    assert _vault.practice_items[made["practiceItemId"]].status == "retired"


def test_every_rw1b_event_is_salience_only_refused_as_evidence_and_never_client_recorded(tmp_path):
    """The salience firewall covers each new payload ``event`` (spec W1)."""

    from learnloop.attempts import salience_firewall as SF
    from learnloop.reader import reader_inquiry as RI
    from tests.test_reader_intent import FakeDecider, _prefer

    vault, _repo = _setup(tmp_path)
    ctx = context(vault.root)
    ctx.reader_intent_inline = True
    ctx.reader_intent_client_factory = lambda: FakeDecider(choice=_prefer("test_me_later"))
    _v, repo = ctx.require_vault()
    started = call(ctx, "reader.route_intent", {"extractionId": "ext1", "spanIds": ["s1"], "text": "quiz me"})
    call(ctx, "reader.intent_outcome", {"routingId": started["routingId"], "outcome": "used"})
    call(ctx, "reader.intent_outcome", {"routingId": started["routingId"], "outcome": "corrected",
                                        "action": "help_me_remember"})
    ctx.ingest_jobs.enqueue_reader_selection_check = lambda **kwargs: "batch_x"  # type: ignore[method-assign]
    import learnloop_sidecar.handlers.ai_providers as providers

    real = providers.ready_canonical_ingest_provider
    providers.ready_canonical_ingest_provider = lambda vault: ("fake", None, object())
    try:
        call(ctx, "reader.active_question", {"extractionId": "ext1", "spanIds": ["s1", "s2"], "style": "reconstruct"})
    finally:
        providers.ready_canonical_ingest_provider = real
    row = _reconstruct(repo)
    call(ctx, "reader.reconstruct", {"questionId": row["id"], "learningObjectId": LO})
    call(ctx, "reader.reconstruct_undo", {"questionId": row["id"]})
    nxt = RQC.author_selection_question(repo, ActiveClient(), extraction_id="ext1", anchor_span_ids=["s1"],
                                        style="next_step", clock=CLOCK, owner="job_e")
    call(ctx, "reader.active_question_action", {"questionId": nxt["id"], "action": "answered", "response": "x"})
    call(ctx, "reader.active_question_action", {"questionId": nxt["id"], "action": "self_checked",
                                                "selfCheck": "no"})
    _v, repo = ctx.require_vault()
    seen: set[str] = set()
    for event in repo.reader_interaction_events(kind="reader_action_invoked"):
        name = event["payload"].get("event")
        if name not in RI.RW1B_SERVER_EVENTS:
            continue
        seen.add(name)
        assert event["payload"]["authority_class"] == SF.SALIENCE_ONLY
        with pytest.raises(SF.SalienceEvidenceRejected):
            SF.reject_salience(event)
    assert seen == set(RI.RW1B_SERVER_EVENTS)
    for name in RI.RW1B_SERVER_EVENTS:
        with pytest.raises(RI.InquiryError):
            RI.record_activity(repo, [{"kind": "reader_action_invoked", "event": name, "payload": {}}])
