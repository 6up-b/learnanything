"""Reader RW6b part 1: the Codex review's findings, each reproduced first
(docs/reviews/reader-rw6b-p1-followups-codex-review.md).

* F1/F11: a follow-up exposed since its valuation (or now owned by a repair
  cold retry) is never served cold: DL2's check gate holds it, and the next
  re-valuation retires it with ``exposed_since_valuation`` (or
  ``repair_retry_owns``) and re-asks the question.
* F2: an automatic follow-up never overrides the learner's explicit intent
  (Pause, Master, any commitment of their own on the item).
* F3: the commitments, the digest receipt and the queue revision are
  published in one transaction after the searches.
* F5: daily re-valuation makes no model call (the serve-time exposure rule,
  persisted judgments only) and honours the source switches.
* F6: a search stopped early stays incomplete with its continuation, even
  when it already chose a check.
* F7: an open causal factor with competing repairs becomes a decision
  question, its pending decision passed through to the valuation.
* F9: a formative-only question is posed with the active predictor on an
  item anchor (never a prior's numeric update).
* F10: the way back comes from the workbench session and the formative
  record when there was no inquiry.
* F12: the attempt-familiarity discount is composed into the valuation.

Fakes only; no model call anywhere.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta

import pytest

from learnloop.curriculum import commitments as C
from learnloop.db.stores import reader_digests as RDG
from learnloop.instructional import reader_followups as RF
from learnloop.reader import reader_sessions as RS
from learnloop.vault.loader import load_vault
from tests.recap_fixtures import EXT, at, iso
from tests.test_reader_followups import (
    FakeSearch,
    NOW_MIN,
    _attempt,
    _candidate,
    _now,
    _plan,
    _seeded,
)

ITEM = "pi_svd_define_002"


def _planned(tmp_path, **kwargs):
    vault, repo, session = _seeded(tmp_path, **kwargs)
    row = _plan(vault, repo, session, FakeSearch([_candidate(ITEM, 0.99, 0.01, 1.0)]))
    return vault, repo, session, row


def _due_moment(row) -> datetime:
    day = date.fromisoformat(row["valuation"]["chosen"][0]["due_hint"])
    return datetime(day.year, day.month, day.day, 12).astimezone().astimezone(UTC)


def _check(vault, repo, commitment_id, now):
    from learnloop.scheduling.intent.serving import intent_serving

    view = intent_serving(load_vault(vault.root), repo, now=now, force=True)
    return view.checks[commitment_id]


def _impression(repo, item_id, minutes, proposal_id="pp_elsewhere"):
    from learnloop.db.stores.source_service import insert_impression

    with repo.connection() as connection:
        insert_impression(connection, id=f"imp_{minutes}", created_at=iso(minutes), surface="reader",
                          caller_kind="reader", caller_ref="elsewhere", proposal_id=proposal_id,
                          candidate_kind="item", practice_item_id=item_id, extraction_id=None, span_ids=[],
                          shown_fields={}, session_id=None)
        connection.commit()


# -- F1: an exposure since valuation keeps the check from being served cold ---------------------------


def test_f1_an_impression_since_valuation_holds_the_check_and_revaluation_retires_and_re_asks(tmp_path):
    vault, repo, session, row = _planned(tmp_path)
    [commitment_id] = row["followup_commitment_ids"]
    due = _due_moment(row)
    assert ITEM in _check(vault, repo, commitment_id, due).eligible  # cold before any exposure
    # The learner sees the item's prompt in another proposal after the check was valued.
    minutes_due = (due - _now(0)).total_seconds() / 60.0
    _impression(repo, ITEM, minutes_due - 60)
    check = _check(vault, repo, commitment_id, due)
    assert ITEM not in check.eligible and not check.cold(ITEM)
    assert ITEM in check.held and dict(check.gated)[ITEM]["reasons"] == ["seen_in_proposal"]
    # The next re-valuation retires it (exposed since valuation) and re-asks.
    report = RF.revalue_pending(vault, repo, now=due, valuer=lambda *_a: {"problems": []},
                                clock=at(minutes_due))
    [line] = report["retired"]
    assert line["reason"] == RF.RETIRE_EXPOSED and line["detail"]["reasons"] == ["seen_in_proposal"]
    assert C.resolve_disposition(repo, commitment_id) == "stopped"
    with repo.connection() as connection:
        digest = RDG.digest(connection, row["id"])
    assert digest["status"] == "incomplete"
    [question] = digest["valuation"]["questions"]
    assert question["incomplete"] is True and question["reason"] == "exposed_since_valuation"
    assert [s.session_id for s in RF.sessions_to_plan(vault, repo, now=due)] == [session.session_id]
    # The retirement is not shown as good news.
    timeline = RF.coming_up(vault, repo, extraction_id=EXT, now=due)
    assert timeline["next"] == [] and timeline["retired"][0]["text"].startswith("No longer a check on your own")


def test_f1_a_related_worked_example_is_only_a_label_for_a_discriminating_check():
    from learnloop.scheduling.intent.followup_gate import independent_reasons

    assert independent_reasons(["related_worked_example"], intent="discriminate") == []
    assert independent_reasons(["related_worked_example"], intent="retention") == ["related_worked_example"]
    assert independent_reasons(["seen_in_proposal"], intent="discriminate") == ["seen_in_proposal"]


# -- F2: explicit learner intent is never overridden -------------------------------------------------


@pytest.mark.parametrize("choice", ["pause", "master"])
def test_f2_an_automatic_follow_up_never_lands_in_a_scope_the_learner_chose(tmp_path, choice):
    from learnloop.intent.control import Scope, apply_choice
    from learnloop.scheduling.intent.serving import intent_serving

    vault, repo, session = _seeded(tmp_path)
    apply_choice(vault, repo, Scope("learning_object", "lo_svd_definition"), choice, clock=at(250))
    search = FakeSearch([_candidate(ITEM, 0.99, 0.01, 1.0)])
    row = _plan(vault, repo, session, search)
    assert row["followup_commitment_ids"] == []
    [call] = search.calls
    assert ITEM in call["constraints"]["exclude_item_ids"]  # never valued at all
    assert row["valuation"]["learner_intent_item_ids"]
    intent = intent_serving(load_vault(vault.root), repo, now=_now(), force=True).intent(ITEM)
    assert intent.choice == choice or intent.disposition == ("paused" if choice == "pause" else "active")


def test_f2_creation_refuses_an_item_the_learner_committed_since_the_search(tmp_path):
    from learnloop.intent.control import Scope, apply_choice

    vault, repo, session = _seeded(tmp_path)

    class PauseDuringSearch(FakeSearch):
        def __call__(self, query, constraints, *, caller, **kwargs):
            apply_choice(vault, repo, Scope("practice_item", ITEM), "pause", clock=at(260))
            return super().__call__(query, constraints, caller=caller, **kwargs)

    row = _plan(vault, repo, session, PauseDuringSearch([_candidate(ITEM, 0.99, 0.01, 1.0)]))
    assert row["followup_commitment_ids"] == []
    [question] = row["valuation"]["questions"]
    assert question["skipped"] == [{"ref": ITEM, "reason": "learner_intent"}]


# -- F3: one publication after the searches ------------------------------------------------------------


def test_f3_a_failure_before_the_digest_is_written_leaves_no_orphan_commitment(tmp_path, monkeypatch):
    vault, repo, session = _seeded(tmp_path)

    def fail(*_a, **_k):
        raise RuntimeError("the process died before the digest")

    monkeypatch.setattr(RDG, "insert_digest", fail)
    with pytest.raises(RuntimeError):
        _plan(vault, repo, session, FakeSearch([_candidate(ITEM, 0.99, 0.01, 1.0)]))
    with repo.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM commitments").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM reader_session_digests").fetchone()[0] == 0


def test_f3_a_session_another_process_planned_meanwhile_is_not_published_twice(tmp_path):
    vault, repo, session = _seeded(tmp_path)

    class OtherProcessFirst(FakeSearch):
        def __call__(self, query, constraints, *, caller, **kwargs):
            result = super().__call__(query, constraints, caller=caller, **kwargs)
            if len(self.calls) == 1:
                # Another sidecar plans and publishes the same session meanwhile.
                RF.plan_session(vault, repo, extraction_id=EXT, session=session,
                                search=FakeSearch([_candidate("pi_svd_define_003", 0.99, 0.01, 1.0)]),
                                now=_now(), clock=at(NOW_MIN))
            return result

    row = _plan(vault, repo, session, OtherProcessFirst([_candidate(ITEM, 0.99, 0.01, 1.0)]))
    assert [entry["ref"] for entry in row["valuation"]["chosen"]] == ["pi_svd_define_003"]
    with repo.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM commitments").fetchone()[0] == 1


# -- F5: daily re-valuation makes no model call and honours the switches ------------------------------


def test_f5_revaluation_never_reaches_the_exposure_judge(tmp_path, monkeypatch):
    import learnloop.instructional.discriminating as D

    vault, repo, _session, row = _planned(tmp_path)
    called = []
    monkeypatch.setattr(D, "independent_check_eligibility",
                        lambda *a, **k: called.append(a) or {"eligible": True, "reasons": []})
    RF.revalue_pending(vault, repo, now=_now(400), valuer=RF.default_valuer(vault, repo), clock=at(400))
    assert called == []


def test_f5_with_the_source_switches_off_revaluation_values_nothing_and_keeps_the_check(tmp_path):
    vault, repo, _session, row = _planned(tmp_path)
    off = load_vault(vault.root)
    off.config.source_service.discriminating_search = False
    valued = []
    report = RF.revalue_pending(off, repo, now=_now(400), valuer=lambda *a: valued.append(a) or {},
                                clock=at(400))
    assert valued == [] and report["kept"][0]["kept_because"] == ["source_service.discriminating_search is false"]


def test_f5_an_unjudged_worked_example_is_refreshed_in_the_background_under_both_envelopes(tmp_path, monkeypatch):
    from learnloop.ai.spend import active_envelopes
    import learnloop.instructional.exposure as E

    vault, repo, _session, row = _planned(tmp_path)
    [commitment_id] = row["followup_commitment_ids"]
    seen = []

    def judged(*_a, **_k):
        seen.append({envelope.name for envelope in active_envelopes()})
        return {"eligible": True, "reasons": [], "worked_example": {"verdict": "unrelated"}}

    monkeypatch.setattr(E, "independent_check_eligibility", judged)
    monkeypatch.setattr(RF, "_gate_verdict", lambda *_a, **_k: {"reasons": ["worked_example_unjudged"]})
    report = RF.revalue_pending(vault, repo, now=_now(400), valuer=lambda *_a: {"problems": []}, clock=at(400))
    assert report["kept"][0]["kept_because"] == ["exposure_refresh_needed"] and seen == []
    refreshed = RF.refresh_exposure(vault, repo, now=_now(410), clock=at(410))
    assert refreshed == [{"commitment_id": commitment_id, "eligible": True, "reasons": []}]
    assert seen and RF.ENVELOPE in seen[0] and len(seen[0]) == 2


# -- F6: an early stop keeps its continuation ------------------------------------------------------------


class BudgetOnce(FakeSearch):
    """The first call stops on its budget after choosing a check; it leaves a cursor."""

    def __call__(self, query, constraints, *, caller, **kwargs):
        self.calls_kwargs = getattr(self, "calls_kwargs", []) + [kwargs]
        result = dict(super().__call__(query, constraints, caller=caller))
        if len(self.calls) == 1:
            result["paging"] = {"outcome": "budget", "cursor": {"judged_items": [ITEM]}}
        return result


def test_f6_a_budget_stop_after_a_pick_stays_incomplete_and_resumes_with_the_pick(tmp_path):
    vault, repo, session = _seeded(tmp_path)
    search = BudgetOnce([_candidate(ITEM, 0.8, 0.2, 0.2), _candidate("pi_svd_define_003", 0.75, 0.25, 0.3)])
    row = _plan(vault, repo, session, search)
    assert row["status"] == "incomplete"
    [question] = row["valuation"]["questions"]
    assert question["incomplete"] is True and question["continue_from"] == "pp_fake_1"
    assert len(row["followup_commitment_ids"]) == 2  # what was chosen is published
    again = _plan(vault, repo, session, search, minutes=NOW_MIN + 60)
    # Round 3: the resume also carries the question's live checks as already chosen.
    assert search.calls_kwargs[1] == {"continue_from": "pp_fake_1",
                                      "already_chosen": [ITEM, "pi_svd_define_003"]}
    assert again["status"] == "planned"
    refs = [entry["ref"] for entry in again["valuation"]["chosen"]]
    assert sorted(refs) == sorted(set(refs)) and len(again["followup_commitment_ids"]) == 2


# -- F7: a pending repair decision reaches the EVSI path --------------------------------------------------


def test_f7_an_open_causal_factor_with_competing_repairs_is_a_decision_question(tmp_path, monkeypatch):
    import learnloop.instructional.needs as N

    vault, repo, session = _seeded(tmp_path)
    decision = {"hypothesis_set_id": "hs_1", "action_by_slot": {"h_a": "rc_1", "h_b": "rc_2"},
                "live_repair_class": None}
    monkeypatch.setattr(N, "pending_causal_decision",
                        lambda _v, _r, need: decision if need.get("attempt_id") == "att_book" else None)
    from learnloop.reader import recap as RC

    summary = RC.session_summary(vault, repo, extraction_id=EXT, session=session, now=_now())
    questions, _notes = RF.open_questions(vault, repo, summary, now=_now())
    [decide] = [q for q in questions if q.key == "decide:hs_1"]
    assert decide.purpose == RF.PURPOSE_DISCRIMINATING
    assert decide.target_hypotheses == [{"kind": "causal_hypothesis", "id": "hs_1"}]
    assert decide.pending_decision == {"hypothesis_set_id": "hs_1", "action_by_slot": decision["action_by_slot"]}
    search = FakeSearch([])
    _plan(vault, repo, session, search)
    kwargs = [call for call in search.calls if call["constraints"]["target_hypotheses"]
              == [{"kind": "causal_hypothesis", "id": "hs_1"}]]
    assert kwargs and kwargs[0]["pending_decision"] == decide.pending_decision


def test_f7_revaluation_passes_the_stored_pending_decision(tmp_path, monkeypatch):
    import learnloop.instructional.discriminating as D

    vault, repo, _session = _seeded(tmp_path)
    seen = {}
    monkeypatch.setattr(D, "value_request", lambda *a, **k: seen.update(k) or {"problems": []})
    valuer = RF.default_valuer(vault, repo)
    valuer({"intent": "discriminate", "learning_object_ids": ["lo_svd_definition"],
            "target_hypotheses": [{"kind": "causal_hypothesis", "id": "hs_1"}],
            "pending_decision": {"hypothesis_set_id": "hs_1", "action_by_slot": {"h_a": "rc_1"}}}, ITEM)
    assert seen["pending_decision"] == {"hypothesis_set_id": "hs_1", "action_by_slot": {"h_a": "rc_1"}}


# -- F9: a formative-only question is valued ------------------------------------------------------------


class _Predictor:
    name = "fake_predictor"
    version_hash = "v1"

    def predict_item(self, item_id):
        from types import SimpleNamespace

        return SimpleNamespace(p_success=0.6)


def test_f9_a_formative_only_retention_question_reaches_a_valuation_problem(tmp_path, monkeypatch):
    import learnloop.placement.predictor as P
    from learnloop.instructional.discriminating import value_request
    from learnloop.practice_index.retrieval import PracticeConstraints

    vault, repo, _session = _seeded(tmp_path)
    # The facet's latest success is unaided: no claim needs an independent check.
    _attempt(repo, "att_own", minutes=30, hints=0, item="pi_svd_define_001")
    monkeypatch.setattr(P, "active_predictor", lambda *_a, **_k: _Predictor())
    vault.evidence_facets["recall"] = object()  # the record's facet is a registered facet
    summary = {"observations": [{"kind": "prediction_missed", "source_event_ids": ["e1"],
                                 "facet_candidates": ["recall"], "span_ids": ["s1"]}]}
    questions, _notes = RF.open_questions(vault, repo, summary, now=_now())
    [question] = questions
    assert question.purpose == RF.PURPOSE_RETENTION
    constraints = RF.constraints_for(question, exclude_family_ids=[])
    receipt = value_request(vault, repo, PracticeConstraints.from_mapping(constraints), items=[ITEM],
                            exercises=[], caller_kind=RF.VIA, system_initiated=True)
    [section] = receipt["problems"]
    problem = section["problem"]
    assert problem["prior"] == {"holds_unaided": 0.6, "not_unaided": 0.4}
    assert problem["prior_basis"] == "predictor:fake_predictor"


# -- F10: the way back without an inquiry ----------------------------------------------------------------


def test_f10_the_workbench_session_carries_the_way_back_without_an_inquiry(tmp_path):
    from learnloop.intent.checks import restoration_link

    vault, repo, _session, row = _planned(tmp_path)
    [commitment_id] = row["followup_commitment_ids"]
    provenance = json.loads(repo.commitment_versions_for(commitment_id)[0]["provenance_json"])
    assert provenance["inquiry_root_event_ids"] == [] and provenance["anchor_span_ids"] == ["s1"]
    assert restoration_link(provenance)["anchor_span_ids"] == ["s1"]


def test_f10_a_formative_record_and_the_studied_passage_are_the_fallbacks(tmp_path):
    vault, repo, _session = _seeded(tmp_path)
    summary = {"inquiries": {}, "workbench": [],
               "observations": [{"kind": "prediction_missed", "span_ids": ["s2"], "source_event_ids": ["e"]}]}
    roots, spans = RF._session_spans(vault, repo, summary, ["lo_svd_definition"], EXT)
    assert roots == [] and spans == ["s2"]


# -- F11: repair ownership by the assessed facets, at creation, re-valuation and serve -----------------


def _two_facet_item(vault):
    from learnloop.vault.writer import upsert_practice_item
    from learnloop.clock import FrozenClock
    from tests.helpers import NOW, NOW_ISO

    upsert_practice_item(vault.root, {
        "id": "pi_two", "learning_object_id": "lo_svd_definition", "subjects": None,
        "practice_mode": "short_answer", "attempt_types_allowed": ["independent_attempt"],
        "evidence_facets": ["recall", "interpretation"], "evidence_weights": {"recall": 0.5, "interpretation": 0.5},
        "prompt": "Define and interpret the SVD.", "expected_answer": "U Sigma V^T; rotations and a stretch.",
        "grading_rubric": {"max_points": 4, "criteria": [{"id": "c", "points": 4, "description": "ok"}],
                           "fatal_errors": []},
        "created_at": NOW_ISO, "updated_at": NOW_ISO}, clock=FrozenClock(NOW))
    return load_vault(vault.root)


def _cold_retry(repo, *, task_id="ft_1", source_attempt_id=None, item=ITEM, minutes=60):
    with repo.connection() as connection:
        connection.execute(
            "INSERT INTO followup_tasks (id, kind, case_kind, case_ref, source_attempt_id, not_before, expires_at, "
            "status, selected_item_id, created_at, updated_at) VALUES (?, 'cold_retry', 'misconception', 'm1', ?, "
            "?, NULL, 'pending', ?, ?, ?)", (task_id, source_attempt_id, iso(minutes), item, iso(minutes),
                                              iso(minutes)))
        connection.commit()


def test_f11_a_retry_owns_only_the_facets_its_item_assesses(tmp_path):
    vault, repo, _session = _seeded(tmp_path)
    vault = _two_facet_item(vault)
    _attempt(repo, "att_two", minutes=25, hints=1, item="pi_two")
    _cold_retry(repo, source_attempt_id="att_two", item=ITEM)  # ITEM assesses recall only
    summary = {"claims_needing_independent_check": [
        {"facet_id": "recall", "attempt_ids": ["att_two"]},
        {"facet_id": "interpretation", "attempt_ids": ["att_two"]}]}
    questions, notes = RF.open_questions(vault, repo, summary, now=_now())
    assert [q.key for q in questions] == ["retention:interpretation"]
    assert notes == [{"question": "retention:recall", "reason": "cold_retry_pending", "followup_task_id": "ft_1"}]


def test_f11_a_repair_retry_scheduled_after_the_follow_up_takes_its_place(tmp_path):
    vault, repo, _session, row = _planned(tmp_path)
    [commitment_id] = row["followup_commitment_ids"]
    due = _due_moment(row)
    _cold_retry(repo, source_attempt_id="att_book", item="pi_svd_define_003", minutes=360)
    check = _check(vault, repo, commitment_id, due)
    assert ITEM not in check.eligible and dict(check.gated)[ITEM]["reasons"] == ["repair_retry_owns"]
    report = RF.revalue_pending(vault, repo, now=_now(400), valuer=lambda *_a: {"problems": []}, clock=at(400))
    [line] = report["retired"]
    assert line["reason"] == RF.RETIRE_REPAIR_OWNS and line["detail"]["followup_task_id"] == "ft_1"


# -- F12: the familiarity discount reaches the valuation ---------------------------------------------------


def test_f12_a_familiar_sibling_counts_for_less_than_its_undiscounted_value():
    from learnloop.instructional.valuation import CandidateInput, ValuationProblem, discount_members, value_candidates

    problem = ValuationProblem(key="retention:lo", space_kind="retention", slots=("holds_unaided", "not_unaided"),
                               prior={"holds_unaided": 0.5, "not_unaided": 0.5}, prior_basis="predictor:test",
                               state_hash="h")
    table = {"holds_unaided": {"success": 0.9, "failure": 0.1}, "not_unaided": {"success": 0.2, "failure": 0.8}}

    def candidate(ref, discount):
        members = (table,) if discount == 1.0 else discount_members((table,), problem.prior, discount)
        made = CandidateInput(ref=ref, kind="item", members=members, outcome_alphabet=("success", "failure"),
                              regime="pinned_channel", likelihood_basis="test", expected_minutes=1.0,
                              construction="pinned:test:retention")
        made.familiarity = {"independent_evidence_discount": discount}
        return made

    receipt = value_candidates([problem], {problem.key: [candidate("fresh", 1.0), candidate("sibling", 0.5)]},
                               system_initiated=True)
    valued = {entry["ref"]: entry for entry in receipt["problems"][0]["groups"]["valued"]}
    assert valued["sibling"]["value_minutes_lcb"] < valued["fresh"]["value_minutes_lcb"]
    assert valued["sibling"]["familiarity"] == {"independent_evidence_discount": 0.5}


def test_f12_the_production_valuer_composes_the_attempt_familiarity_discount(tmp_path, monkeypatch):
    import learnloop.placement.predictor as P
    from learnloop.instructional.discriminating import value_request
    from learnloop.practice_index.retrieval import PracticeConstraints

    vault, repo, _session = _seeded(tmp_path)
    monkeypatch.setattr(P, "active_predictor", lambda *_a, **_k: _Predictor())
    question = RF.Question(key="retention:recall", purpose=RF.PURPOSE_RETENTION,
                           learning_object_ids=["lo_svd_definition"], facet_ids=["recall"])
    constraints = PracticeConstraints.from_mapping(RF.constraints_for(question, exclude_family_ids=[]))
    receipt = value_request(vault, repo, constraints, items=[ITEM], exercises=[], caller_kind=RF.VIA,
                            system_initiated=True, familiarity=True)
    entries = [entry for section in receipt["problems"] for group in section["groups"].values() for entry in group]
    assert entries and all(entry["familiarity"]["independent_evidence_discount"] < 1.0 for entry in entries)
