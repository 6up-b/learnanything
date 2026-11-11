"""Reader RW6b part 1 landing onto main: its interactions with curriculum C0b,
the mvp-0.38 cold-retry reschedule and Reader CA5a's peek
(docs/reviews/reader-rw6b-p1-followups.md, "Landing onto main").

(i) C0b's *Check me later* and *Am I ready?* Check once commitments and RW6b's
    automatic follow-ups coexist in the maintain lane: DL2 serves both, and
    RW6b's serve-time gate touches only ``via: reader_followup`` commitments
    (a C0b check exposed since its creation is served exactly as with
    ``followups.enabled`` off).
(ii) The mvp-0.38 reschedule's fresh cold retry (help taken on a due repair
    cold retry withdraws it and schedules one fresh retry for the same repair)
    still owns the claim: no retention follow-up is planned for it, and an
    existing follow-up is held and retired as repair-owned.
(iii) Reader CA5a's peek records the blocks it shows as ``source_exposure``
    rows (``record_span_exposures``, context ``library``); a follow-up whose
    item's source span was shown that way since its valuation is held by the
    exposure gate.

(iv) (an interrupted mvp-0.38 activation then ``upgrade --to mvp-0.39``; the
denial-log archive once per upgrade command) is covered by
tests/test_reader_followups_successor.py and
tests/test_pr4_superseded_claims_landing.py, which pin the latest tag.

Every model is a fake; nothing leaves the machine.
"""
from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

from learnloop.curriculum import commitments as C
from learnloop.instructional import reader_followups as RF
from learnloop.source_retrieval import deliverable_path as DP
from learnloop.vault.loader import load_vault
from tests.recap_fixtures import at, iso
from tests.reader_followups_helpers import FakeSearch, NOW_MIN, _candidate, _now, _plan, _seeded
from tests.ux_phase1_support import set_config

ITEM = "pi_svd_define_002"


def _planned(tmp_path):
    vault, repo, session = _seeded(tmp_path)
    row = _plan(vault, repo, session, FakeSearch([_candidate(ITEM, 0.99, 0.01, 1.0)]))
    return vault, repo, session, row


def _noon(day: str) -> datetime:
    parsed = date.fromisoformat(day)
    return datetime(parsed.year, parsed.month, parsed.day, 12).astimezone().astimezone(UTC)


def _serving(root, repo, now):
    from learnloop.scheduling.intent.serving import intent_serving

    return intent_serving(load_vault(root), repo, now=now, force=True)


def _impression(repo, item_id, moment: datetime):
    from learnloop.db.stores.source_service import insert_impression

    with repo.connection() as connection:
        insert_impression(connection, id=f"imp_{item_id}_{moment.timestamp():.0f}",
                          created_at=moment.isoformat().replace("+00:00", "Z"), surface="reader",
                          caller_kind="reader", caller_ref="elsewhere", proposal_id="pp_elsewhere",
                          candidate_kind="item", practice_item_id=item_id, extraction_id=None, span_ids=[],
                          shown_fields={}, session_id=None)
        connection.commit()


def _state(check):
    return (check.due, check.answered_by, tuple(check.candidates), check.eligible, check.held, check.exposed,
            tuple(item for item, _ in check.refused), tuple(item for item, _ in check.gated))


# -- (i) C0b's Check once commitments beside RW6b's follow-ups -----------------------------------------------


def _c0b_check(vault, repo, item_id, *, via, key, clock):
    """A Check once commitment exactly as ``deliverable_path.create_check`` writes it, on a
    chosen item (``create_check`` picks the LO's first unattempted item itself)."""

    commitment = C.create_commitment(
        repo, action="test_me_later", intent_text="check on your own later: SVD",
        targets=[{"target_kind": "legacy_practice_item", "target_ref": item_id, "role": "required"}],
        depth_preset=DP.READY_DEPTH_PRESET, client_idempotency_key=key,
        due_hint=DP.check_due(vault, repo, "lo_svd_definition", due_at=None, clock=clock),
        reason="a cold check you asked for",
        provenance={"via": via, "goal_id": "goal_midterm", "learning_object_id": "lo_svd_definition"}, clock=clock)
    return commitment.id


def test_i_check_once_commitments_and_follow_ups_coexist_and_the_gate_touches_only_follow_ups(tmp_path):
    from learnloop.scheduling.intent.followup_gate import followup_gate

    vault, repo, _session, row = _planned(tmp_path)
    [followup_id] = row["followup_commitment_ids"]
    clock = at(NOW_MIN + 10)
    check_ids = [_c0b_check(load_vault(vault.root), repo, "pi_svd_define_003", via=DP.PATH_VIA, key="landing:path",
                            clock=clock),
                 _c0b_check(load_vault(vault.root), repo, "pi_svd_define_004", via=DP.READY_VIA,
                            key="landing:ready", clock=clock)]
    for commitment_id in check_ids:
        assert C.resolve_disposition(repo, commitment_id) == "one_check_pending"
    dues = [row["valuation"]["chosen"][0]["due_hint"]]
    with repo.connection() as connection:
        dues += [str(r[0]) for r in connection.execute(
            "SELECT due_hint FROM commitment_versions WHERE commitment_id IN (?, ?)", check_ids)]
    moment = max(_noon(day) for day in dues)
    checks = _serving(vault.root, repo, moment).checks
    # DL2 serves both kinds: every commitment is a due check in the same view, each on its own item.
    assert {followup_id, *check_ids} <= set(checks)
    assert checks[followup_id].provenance.get("via") == RF.VIA
    assert {checks[cid].provenance.get("via") for cid in check_ids} == {DP.PATH_VIA, DP.READY_VIA}
    for cid in (followup_id, *check_ids):
        assert checks[cid].due and checks[cid].servable and not checks[cid].gated and not checks[cid].replaced, cid
    assert checks[followup_id].cold(ITEM)
    # RW6b's serve-time gate passes every non-follow-up commitment by construction.
    for cid in check_ids:
        check = checks[cid]
        assert followup_gate(load_vault(vault.root), repo, item_id=check.candidates[0], provenance=check.provenance,
                             valued_at=check.created_at, now=moment, commitment_id=cid) is None
    # An exposure since creation on every candidate (an impression in another proposal) holds the
    # follow-up, and leaves each Check once exactly as with RW6b switched off.
    for item_id in {*checks[followup_id].candidates, *(c for cid in check_ids for c in checks[cid].candidates)}:
        _impression(repo, item_id, moment - timedelta(hours=1))
    on = _serving(vault.root, repo, moment).checks
    assert ITEM in on[followup_id].held and "seen_in_proposal" in dict(on[followup_id].gated)[ITEM]["reasons"]
    set_config(vault.root, {("followups", "enabled"): False})
    off = _serving(vault.root, repo, moment).checks
    for cid in check_ids:
        assert not on[cid].gated
        assert _state(on[cid]) == _state(off[cid]), cid


def test_i_a_check_once_on_the_follow_ups_own_item_replaces_the_automatic_check(tmp_path):
    """C0b's ``create_check`` picks the LO's first unattempted item, which can be the item a
    follow-up already checks: DL2's own rule lets the learner's newer commitment decide it
    (the follow-up is ``replaced``), and the Check once is served."""

    vault, repo, _session, row = _planned(tmp_path)
    [followup_id] = row["followup_commitment_ids"]
    goal = SimpleNamespace(id="goal_midterm", due_at=None)
    later = DP.create_check(load_vault(vault.root), repo, goal, "lo_svd_definition", via=DP.PATH_VIA,
                            key="landing:path", clock=at(NOW_MIN + 10))
    assert later["item_id"] == ITEM
    moment = max(_noon(row["valuation"]["chosen"][0]["due_hint"]), _noon(later["due_hint"]))
    checks = _serving(vault.root, repo, moment).checks
    assert checks[followup_id].replaced and not checks[followup_id].servable
    assert checks[later["commitment_id"]].cold(ITEM) and not checks[later["commitment_id"]].gated


# -- (ii) the mvp-0.38 reschedule's fresh cold retry keeps repair ownership ----------------------------------


def _reschedule_shaped_retries(repo, *, source_attempt_id: str, withdrawn_item: str, fresh_item: str,
                               minutes: float) -> str:
    """The rows ``remediation.reschedule_assisted_cold_retry`` leaves (mvp-0.38): the
    assisted retry withdrawn (``expired``), one fresh ``cold_retry`` for the same repair
    on another surface, keeping the primed source attempt, its context marked."""

    import json

    from learnloop.diagnosis.remediation import ASSISTED_RESCHEDULE_CONTEXT_KEY

    stamp = iso(minutes)
    context = {ASSISTED_RESCHEDULE_CONTEXT_KEY: {"from_task_id": "ft_assisted", "assisted_attempt_id": "att_help",
                                                 "withdrawn_cold_item_id": withdrawn_item,
                                                 "reason": "cold_check_help_taken"}}
    with repo.connection() as connection:
        connection.execute(
            "INSERT INTO followup_tasks (id, kind, case_kind, case_ref, source_attempt_id, not_before, expires_at, "
            "status, selected_item_id, created_at, updated_at) VALUES ('ft_assisted', 'cold_retry', "
            "'misconception', 'm1', ?, ?, NULL, 'expired', ?, ?, ?)",
            (source_attempt_id, stamp, withdrawn_item, stamp, stamp))
        connection.execute(
            "INSERT INTO followup_tasks (id, kind, case_kind, case_ref, source_attempt_id, not_before, expires_at, "
            "status, selected_item_id, context_json, created_at, updated_at) VALUES ('ft_fresh', 'cold_retry', "
            "'misconception', 'm1', ?, ?, NULL, 'pending', ?, ?, ?, ?)",
            (source_attempt_id, stamp, fresh_item, json.dumps(context), stamp, stamp))
        connection.commit()
    return "ft_fresh"


def test_ii_a_rescheduled_fresh_cold_retry_owns_the_claim_at_planning(tmp_path):
    vault, repo, _session = _seeded(tmp_path)
    fresh = _reschedule_shaped_retries(repo, source_attempt_id="att_book", withdrawn_item="pi_svd_define_004",
                                       fresh_item="pi_svd_define_003", minutes=60)
    summary = {"claims_needing_independent_check": [{"facet_id": "recall", "attempt_ids": ["att_book"]}]}
    questions, notes = RF.open_questions(vault, repo, summary, now=_now())
    assert [q.key for q in questions] == []
    assert notes == [{"question": "retention:recall", "reason": "cold_retry_pending", "followup_task_id": fresh}]


def test_ii_a_rescheduled_fresh_cold_retry_holds_and_retires_an_existing_follow_up(tmp_path):
    vault, repo, _session, row = _planned(tmp_path)
    [commitment_id] = row["followup_commitment_ids"]
    due = _noon(row["valuation"]["chosen"][0]["due_hint"])
    fresh = _reschedule_shaped_retries(repo, source_attempt_id="att_book", withdrawn_item="pi_svd_define_004",
                                       fresh_item="pi_svd_define_003", minutes=360)
    check = _serving(vault.root, repo, due).checks[commitment_id]
    assert ITEM not in check.eligible and dict(check.gated)[ITEM]["reasons"] == ["repair_retry_owns"]
    assert dict(check.gated)[ITEM]["followup_task_id"] == fresh
    report = RF.revalue_pending(vault, repo, now=_now(400), valuer=lambda *_a: {"problems": []}, clock=at(400))
    [line] = report["retired"]
    assert line["reason"] == RF.RETIRE_REPAIR_OWNS and line["detail"]["followup_task_id"] == fresh


# -- (iii) CA5a's peek writes source exposure the gate reads -----------------------------------------------


def test_iii_a_ca5a_peek_of_the_items_source_span_holds_the_follow_up(tmp_path):
    from learnloop.reader.span_view import record_span_exposures
    from learnloop.scheduling.intent.followup_gate import followup_gate
    from tests.source_service_fakes import seed_textbook

    _vault, repo, _session = _seeded(tmp_path)
    units = {"exercises": ("Exercises", [("Exercise 2.4 Define the singular values of a matrix A.", 4)])}
    span = seed_textbook(repo, source_id="src_peek", revision_id="rev_peek", extraction_id="ext_peek",
                         units=units)["exercises"][0]
    item = SimpleNamespace(id=ITEM, family_id=None, learning_object_id="lo_svd_definition", evidence_facets=(),
                           canonical_exercise=SimpleNamespace(extraction_id="ext_peek", span_ids=(span,)))
    vault = SimpleNamespace(practice_items={ITEM: item}, canonical_facet_id=lambda facet: facet)
    provenance = {"via": RF.VIA, "purpose": "discriminating",
                  "question": {"intent": "discriminate", "facet_ids": [], "learning_object_ids": ["lo_svd_definition"]},
                  "attempt_ids": []}
    valued_at, now = iso(NOW_MIN), _now(NOW_MIN + 600)
    assert followup_gate(vault, repo, item_id=ITEM, provenance=provenance, valued_at=valued_at, now=now) is None
    # The Guide's peek at that section in another book shows the exercise's block (CA5a, Codex review F2).
    ids = record_span_exposures(repo, "ext_peek", [span], context="library", clock=at(NOW_MIN + 500))
    assert ids
    verdict = followup_gate(vault, repo, item_id=ITEM, provenance=provenance, valued_at=valued_at, now=now)
    assert verdict is not None and verdict["reasons"] == ["source_exposed"]
    assert verdict["exposure"]["inputs"]["exposure_event_ids"] == ids
