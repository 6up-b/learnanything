"""Reader workbench RW6b part 1: cold follow-ups (spec_reader_workbench_v1 §9.3-§9.6;
gates G26, G27, G35 and G49's follow-up parts; docs/reviews/reader-rw6b-p1-followups.md).

* The open questions come from RW6a's typed summary (claims needing an
  independent check; formative records only with their switch on); a claim
  whose repair cold retry is pending (mvp-0.38) gets no retention follow-up.
* ``find_practice`` is asked with the exact filters; the valuation is the
  sources spec's ``value_candidates`` (here a fake search composes the REAL
  one over synthetic pinned-channel tables): whatever clears the stop becomes
  a ``test_me_later`` commitment, with no count cap, a duplicate dropped by
  conditional valuation, ``item_point`` never dated, nothing when every LCB is
  below its minutes, ``no_item`` when nothing fits.
* Dating by purpose: discriminating for the next day's plan, retention at the
  practiced item's effective due or FSRS's first interval, never past
  ``followups.max_wait_days``; DL2 reads the ``due_hint``.
* Re-valuation retires an answered follow-up with its reason, once a day;
  undo (with a reason on a ``learner_card`` verdict), undo all and restore.
* Kill switch, spend cap, idempotency, provenance, the receipt.

Fakes only; no model call anywhere.
"""

from __future__ import annotations

import json
from datetime import timedelta
from types import SimpleNamespace

import pytest

from learnloop.ai.spend import SpendLimitExceeded
from learnloop.algorithm_versions import READER_FOLLOWUPS_ALGORITHM_VERSION
from learnloop.curriculum import commitments as C
from learnloop.db.repositories import PracticeItemState
from learnloop.db.stores import reader_digests as RDG
from learnloop.instructional import reader_followups as RF
from learnloop.instructional.valuation import CandidateInput, ValuationProblem, value_candidates
from learnloop.reader import reader_sessions as RS
from learnloop.scheduling import fsrs as F
from learnloop.vault.loader import load_vault
from tests.helpers import add_followup_item, append_config_toml
from tests.recap_fixtures import EXT, T0, at, call, context, iso, problem, visit
from tests.test_reader_dialogue import _setup
from tests.ux_phase1_support import set_config

ITEMS = ("pi_svd_define_002", "pi_svd_define_003", "pi_svd_define_004")
NOW_MIN = 300


def _now(minutes: float = NOW_MIN):
    return T0 + timedelta(minutes=minutes)


def _attempt(repo, attempt_id, *, minutes, hints, item="pi_svd_define_001", score=4, correctness=1.0):
    repo.insert_practice_attempt({
        "id": attempt_id, "practice_item_id": item, "learning_object_id": "lo_svd_definition",
        "subject": "linear-algebra", "concept": "singular_value_decomposition", "practice_mode": "short_answer",
        "attempt_type": "hinted_attempt" if hints else "independent_attempt",
        "learner_answer_md": "U Sigma V^T", "evidence_facets": ["recall"], "evidence_weights": {"recall": 1.0},
        "rubric_score": score, "correctness": correctness, "confidence": 3, "latency_seconds": 30,
        "hints_used": hints, "error_type": None, "grader_confidence": 1.0, "created_at": iso(minutes),
        "updated_at": iso(minutes), "entry_surface": "desktop_reader_workbench",
    })


def _seeded(tmp_path, *, config: str | None = None, version: str = READER_FOLLOWUPS_ALGORITHM_VERSION):
    """One ended session (0-40 min): a problem worked with the book and a hint,
    at the successor (mvp-0.39; Codex review F4) unless ``version`` says otherwise."""

    vault, repo = _setup(tmp_path)
    for item_id in ITEMS:
        add_followup_item(vault.root, item_id)
    set_config(vault.root, {("algorithms", "algorithm_version"): version})
    if config:
        append_config_toml(vault.root, config)
    vault = load_vault(vault.root)
    visit(repo, "v1", 0, 40)
    from learnloop.reader import workbench as WB

    row = problem(repo, 2, steps=1, book=True)
    _attempt(repo, "att_book", minutes=20, hints=1)
    WB.mark_submitted(repo, row["id"], attempt_id="att_book", practice_session_id="ps_1", clock=at(20))
    session = RS.sessions_for_source(repo, EXT)[0]
    return vault, repo, session


# -- a fake search over the REAL valuation ------------------------------------------------------


def _table(a, b):
    return {"holds_unaided": {"success": a, "failure": 1 - a}, "not_unaided": {"success": b, "failure": 1 - b}}


def _candidate(ref, a, b, minutes, regime="pinned_channel"):
    return CandidateInput(ref=ref, kind="item", members=(_table(a, b),), outcome_alphabet=("success", "failure"),
                          regime=regime, likelihood_basis="test", expected_minutes=minutes,
                          construction="pinned:test:retention")


class FakeSearch:
    """``find_practice``'s result shape, valued by the real ``value_candidates``."""

    def __init__(self, candidates=None, *, raise_first=None, empty=False):
        self.candidates = candidates if candidates is not None else []
        self.calls = []
        self.raise_first = raise_first
        self.empty = empty

    def __call__(self, query, constraints, *, caller, **kwargs):
        self.calls.append({"query": query, "constraints": constraints, "caller": caller, **kwargs})
        if self.raise_first is not None:
            exc, self.raise_first = self.raise_first, None
            raise exc
        problem = ValuationProblem(key=f"retention:{constraints['learning_object_ids'][0]}", space_kind="retention",
                                   slots=("holds_unaided", "not_unaided"),
                                   prior={"holds_unaided": 0.5, "not_unaided": 0.5},
                                   prior_basis="predictor:test", state_hash="h")
        inputs = [] if self.empty else list(self.candidates)
        receipt = value_candidates([problem], {problem.key: inputs}, caller_kind="reader", system_initiated=True)
        return {"status": "ok", "proposal_id": f"pp_fake_{len(self.calls)}", "valuation": receipt,
                "paging": {"outcome": "exhausted"}, "rerank_status": "reranked"}


def _plan(vault, repo, session, search, minutes=NOW_MIN):
    return RF.plan_session(vault, repo, extraction_id=EXT, session=session, search=search, now=_now(minutes),
                           clock=at(minutes))


def _pending(repo, row):
    return [cid for cid in row["followup_commitment_ids"] if C.resolve_disposition(repo, cid) == "one_check_pending"]


# -- the open questions --------------------------------------------------------------------------


def test_a_claim_needing_an_independent_check_is_a_retention_question(tmp_path):
    vault, repo, session = _seeded(tmp_path)
    from learnloop.reader import recap as RC

    summary = RC.session_summary(vault, repo, extraction_id=EXT, session=session, now=_now())
    questions, notes = RF.open_questions(vault, repo, summary, now=_now())
    [question] = questions
    assert question.purpose == RF.PURPOSE_RETENTION and question.intent == "retention"
    assert question.facet_ids == [vault.canonical_facet_id("recall")]
    assert question.learning_object_ids == ["lo_svd_definition"]
    assert question.attempt_ids == ["att_book"] and notes == []
    assert question.raised_by[0]["kind"] == "claim"


def test_a_pending_cold_retry_on_the_claim_takes_the_place_of_a_retention_follow_up(tmp_path):
    """mvp-0.38: a facet whose repair cold_retry is pending gets no retention
    follow-up for the same claim (its cold measurement answers it)."""

    vault, repo, session = _seeded(tmp_path)
    with repo.connection() as connection:
        connection.execute(
            "INSERT INTO followup_tasks (id, kind, case_kind, case_ref, source_attempt_id, not_before, expires_at, "
            "status, selected_item_id, created_at, updated_at) VALUES "
            "('ft_1', 'cold_retry', 'misconception', 'm1', 'att_book', ?, NULL, 'pending', 'pi_svd_define_002', ?, ?)",
            (iso(60), iso(60), iso(60)))
        connection.commit()
    search = FakeSearch([_candidate("pi_svd_define_002", 0.99, 0.01, 1.0)])
    row = _plan(vault, repo, session, search)
    assert search.calls == [] and row["followup_commitment_ids"] == []
    assert row["valuation"]["notes"] == [{"question": f"retention:{vault.canonical_facet_id('recall')}",
                                          "reason": "cold_retry_pending", "followup_task_id": "ft_1"}]


# -- candidates: the exact filters ---------------------------------------------------------------


def test_the_search_is_asked_with_the_exact_filters(tmp_path):
    vault, repo, session = _seeded(tmp_path)
    search = FakeSearch([])
    _plan(vault, repo, session, search)
    [call_] = search.calls
    constraints = call_["constraints"]
    assert constraints["intent"] == "retention"
    assert constraints["unattempted_only"] is True and constraints["exclude_revealed_families"] is True
    assert constraints["exclude_family_ids"] == []
    assert call_["caller"] == {"kind": RF.VIA, "ref": RF.digest_id_for(EXT, session.session_id)}


def test_the_exact_filters_reach_find_practice_admission(tmp_path):
    """The real ``find_practice`` keeps an attempted item out of the value
    search: the session's own item is never a candidate (G26)."""

    from learnloop.practice_index.retrieval import FilterContext, PracticeConstraints, filter_context

    vault, repo, _session = _seeded(tmp_path)
    question = RF.Question(key="retention:recall", purpose=RF.PURPOSE_RETENTION,
                           learning_object_ids=["lo_svd_definition"], facet_ids=["recall"])
    constraints = PracticeConstraints.from_mapping(RF.constraints_for(question, exclude_family_ids=["fam_x"]))
    context = filter_context(vault, repo, constraints)
    assert isinstance(context, FilterContext) and "pi_svd_define_001" in context.attempted
    assert constraints.exclude_family_ids == ("fam_x",) and constraints.unattempted_only


def test_revealed_families_are_the_sessions_reveals_only():
    vault = SimpleNamespace(practice_items={"a": SimpleNamespace(family_id="fam_a"),
                                            "b": SimpleNamespace(family_id="fam_b"),
                                            "c": SimpleNamespace(family_id=None)})

    class Repo:
        sqlite_path = None

    session = RS.ReaderSession(EXT, ("v1",), iso(0), iso(40))
    import learnloop.instructional.reader_followups as module

    class Rows:
        def __init__(self, rows):
            self.rows = rows

        def execute(self, *_a):
            return SimpleNamespace(fetchall=lambda: self.rows)

        def close(self):
            pass

    rows = [{"practice_item_id": "a", "created_at": iso(10)}, {"practice_item_id": "b", "created_at": iso(90)},
            {"practice_item_id": "c", "created_at": iso(12)}]
    original = module.connect
    module.connect = lambda *_a, **_k: Rows(rows)
    try:
        assert RF.revealed_families(vault, Repo(), session) == ["fam_a"]
    finally:
        module.connect = original


# -- valuation: no count cap, the stop, conditional selection, licensing -----------------------


def test_several_checks_that_clear_the_stop_are_all_created_in_rank_order(tmp_path):
    vault, repo, session = _seeded(tmp_path)
    search = FakeSearch([_candidate("pi_svd_define_002", 0.8, 0.2, 0.2), _candidate("pi_svd_define_003", 0.75, 0.25, 0.3),
                         _candidate("pi_svd_define_004", 0.7, 0.3, 0.4)])
    row = _plan(vault, repo, session, search)
    chosen = row["valuation"]["chosen"]
    assert [entry["ref"] for entry in chosen] == ["pi_svd_define_002", "pi_svd_define_003", "pi_svd_define_004"]
    assert [entry["order"] for entry in chosen] == [1, 2, 3]
    assert len(row["followup_commitment_ids"]) == 3  # no count cap
    for entry in chosen:
        # Every created follow-up's receipt cleared the stop rule.
        assert entry["value_minutes_lcb"] > entry["expected_minutes"]
        assert entry["probe_eig"] is not None and entry["predicted_outcomes"]


def test_conditional_valuation_drops_a_second_check_that_duplicates_the_first(tmp_path):
    vault, repo, session = _seeded(tmp_path)
    search = FakeSearch([_candidate("pi_svd_define_002", 0.999, 0.001, 1.0),
                         _candidate("pi_svd_define_003", 0.99, 0.01, 2.0)])
    row = _plan(vault, repo, session, search)
    assert [entry["ref"] for entry in row["valuation"]["chosen"]] == ["pi_svd_define_002"]
    [question] = row["valuation"]["questions"]
    section = question["valuation"]["problems"][0]
    assert section["reason"] == "stopped_after_1" and section["stop_at"]["candidate"] == "pi_svd_define_003"


def test_nothing_is_created_when_every_lcb_is_below_its_minutes(tmp_path):
    vault, repo, session = _seeded(tmp_path)
    row = _plan(vault, repo, session, FakeSearch([_candidate("pi_svd_define_002", 0.55, 0.45, 30.0)]))
    assert row["followup_commitment_ids"] == [] and row["valuation"]["chosen"] == []
    [question] = row["valuation"]["questions"]
    assert question["outcome"] == "no_check" and question["verdicts"] == ["stop"]


def test_an_item_point_value_is_shown_never_dated(tmp_path):
    """A system-initiated check is created only from a licensing regime (sources §8.3.3, §20)."""

    vault, repo, session = _seeded(tmp_path)
    row = _plan(vault, repo, session, FakeSearch([_candidate("pi_svd_define_002", 0.99, 0.01, 1.0,
                                                             regime="item_point")]))
    assert row["followup_commitment_ids"] == []
    [question] = row["valuation"]["questions"]
    assert question["valuation"]["problems"][0]["verdict"] == "abstain"
    assert question["valuation"]["problems"][0]["reason"] == "regime_cannot_license"


def test_nothing_fits_records_no_item_and_generation_stays_off(tmp_path):
    vault, repo, session = _seeded(tmp_path)
    row = _plan(vault, repo, session, FakeSearch(empty=True))
    [question] = row["valuation"]["questions"]
    assert question["outcome"] == "no_item"
    assert question["generation"] == {"requested": False, "reason": "generate_when_nothing_fits is off"}
    assert row["followup_commitment_ids"] == []


def test_the_valuation_is_the_sources_specs_machinery(tmp_path, monkeypatch):
    """G35: RW6b defines no EIG, value or stop rule; the receipt's numbers are
    robust_composition's (spied here), and the constants are read from there."""

    from learnloop.diagnosis import robust_composition as RCmp

    calls = {"select": 0, "eig": 0}
    select, eig = RCmp.evaluate_selection, RCmp.expected_information_gain

    def spy_select(*args, **kwargs):
        calls["select"] += 1
        return select(*args, **kwargs)

    def spy_eig(*args, **kwargs):
        calls["eig"] += 1
        return eig(*args, **kwargs)

    monkeypatch.setattr(RCmp, "evaluate_selection", spy_select)
    monkeypatch.setattr(RCmp, "expected_information_gain", spy_eig)
    vault, repo, session = _seeded(tmp_path)
    row = _plan(vault, repo, session, FakeSearch([_candidate("pi_svd_define_002", 0.99, 0.01, 1.0)]))
    assert calls["select"] >= 1 and calls["eig"] >= 1 and len(row["followup_commitment_ids"]) == 1
    section = row["valuation"]["questions"][0]["valuation"]["problems"][0]
    assert section["constants"] == {"lambda_time": RCmp.LAMBDA_TIME, "burden_cost": RCmp.BURDEN_COST,
                                    "value_per_nat_minutes": RCmp.VALUE_PER_NAT_MINUTES,
                                    "quantile": RCmp.ROBUST_QUANTILE}
    import inspect

    source = inspect.getsource(RF)
    for forbidden in ("def expected_information_gain", "def robust_evsi", "def rank_feasible", "LAMBDA_TIME =",
                      "VALUE_PER_NAT_MINUTES ="):
        assert forbidden not in source


# -- scheduling as content: the commitment, its provenance, DL2's due_hint ---------------------


def test_each_follow_up_is_a_test_me_later_commitment_with_its_provenance(tmp_path):
    from learnloop.scheduling.intent.resolution import load_snapshots
    from learnloop.scheduling.intent.serving import DATE_FROM_DUE_HINT, check_date

    vault, repo, session = _seeded(tmp_path)
    row = _plan(vault, repo, session, FakeSearch([_candidate("pi_svd_define_002", 0.99, 0.01, 1.0)]))
    [commitment_id] = row["followup_commitment_ids"]
    commitment = C.load_commitment(repo, commitment_id)
    assert commitment.created_action == "test_me_later" and commitment.disposition == "one_check_pending"
    [target] = commitment.head.targets
    assert (target.target_kind, target.target_ref) == ("legacy_practice_item", "pi_svd_define_002")
    provenance = json.loads(repo.commitment_versions_for(commitment_id)[0]["provenance_json"])
    assert provenance["via"] == "reader_followup" and provenance["summary_id"] == row["id"]
    assert provenance["purpose"] == "retention" and provenance["novelty"] in RF.NOVELTY_LABELS
    assert provenance["valuation_ref"]["digest_id"] == row["id"]
    for key in ("inquiry_root_event_ids", "anchor_span_ids", "extraction_id", "source_id"):
        assert key in provenance
    # DL2's dated branch reads the due_hint.
    with repo.connection() as connection:
        [snapshot] = [s for s in load_snapshots(connection) if s.id == commitment_id]
    when, source = check_date(snapshot, default_days=7)
    assert source == DATE_FROM_DUE_HINT and when.astimezone().date().isoformat() == row["valuation"]["chosen"][0]["due_hint"]


def test_planning_is_idempotent_per_session(tmp_path):
    vault, repo, session = _seeded(tmp_path)
    search = FakeSearch([_candidate("pi_svd_define_002", 0.99, 0.01, 1.0)])
    first = _plan(vault, repo, session, search)
    second = _plan(vault, repo, session, search, minutes=NOW_MIN + 5)
    assert first["id"] == second["id"] and first["followup_commitment_ids"] == second["followup_commitment_ids"]
    assert len(search.calls) == 1


def test_a_budget_stop_leaves_the_digest_incomplete_and_the_next_plan_re_asks(tmp_path):
    vault, repo, session = _seeded(tmp_path)
    search = FakeSearch([_candidate("pi_svd_define_002", 0.99, 0.01, 1.0)],
                        raise_first=SpendLimitExceeded("followups.max_daily_cost_usd: over"))
    row = _plan(vault, repo, session, search)
    assert row["status"] == "incomplete" and row["followup_commitment_ids"] == []
    assert row["valuation"]["questions"][0]["reason"] == "budget"
    again = _plan(vault, repo, session, search, minutes=NOW_MIN + 60 * 24)
    assert again["status"] == "planned" and len(again["followup_commitment_ids"]) == 1


def test_the_spend_envelopes_are_the_followups_and_the_services(tmp_path):
    from learnloop.ai.spend import active_envelopes

    vault, repo, _session = _seeded(tmp_path)
    with RF.followup_spend(vault, repo):
        names = {envelope.name for envelope in active_envelopes()}
    assert RF.ENVELOPE in names and len(names) == 2


def test_the_kill_switch_creates_nothing_and_runs_no_revaluation(tmp_path):
    vault, repo, session = _seeded(tmp_path, config="[followups]\nenabled = false\n")
    search = FakeSearch([_candidate("pi_svd_define_002", 0.99, 0.01, 1.0)])
    assert _plan(vault, repo, session, search) is None and search.calls == []
    assert RF.sessions_to_plan(vault, repo, now=_now()) == []
    assert RF.revalue_pending(vault, repo, now=_now(), valuer=lambda *_a: {})["skipped"]
    with repo.connection() as connection:
        assert RDG.digests(connection) == []
        assert connection.execute("SELECT COUNT(*) FROM commitments").fetchone()[0] == 0


def test_only_ended_sessions_wait_for_planning(tmp_path):
    vault, repo, session = _seeded(tmp_path)
    assert RF.sessions_to_plan(vault, repo, now=_now(50)) == []  # within the 30-minute gap
    assert [s.session_id for s in RF.sessions_to_plan(vault, repo, now=_now())] == [session.session_id]
    _plan(vault, repo, session, FakeSearch([]))
    assert RF.sessions_to_plan(vault, repo, now=_now()) == []
    # Past the time cap a session is not planned retroactively.
    assert RF.sessions_to_plan(load_vault(vault.root), repo, now=_now(60 * 24 * 20)) == []


def test_formative_records_add_questions_only_with_their_switch():
    vault = SimpleNamespace(
        canonical_facet_id=lambda f: f, evidence_facets={"f1": object()}, learning_objects={},
        practice_items={"pi": SimpleNamespace(learning_object_id="lo1", id="pi")},
        config=SimpleNamespace(followups=SimpleNamespace(formative_questions_enabled=True)))
    summary = {"observations": [{"kind": "still_unclear", "source_event_ids": ["e1"], "facet_candidates": ["f1"],
                                 "hypotheses": []}]}
    repo = SimpleNamespace(open_probe_episodes=lambda: {})
    import learnloop.instructional.reader_followups as module

    original_los, original_retry = module._facet_los, module.pending_cold_retry
    module._facet_los = lambda _v, _f: ["lo1"]
    module.pending_cold_retry = lambda *_a, **_k: None
    try:
        questions, _notes = RF.open_questions(vault, repo, summary, now=_now())
        assert [(q.key, q.raised_by[0]["kind"]) for q in questions] == [("retention:f1", "formative")]
        # A record changes which questions are asked, never a prior: no number rides on it.
        assert set(questions[0].as_dict()) == {"key", "purpose", "learning_object_ids", "facet_ids",
                                               "target_hypotheses", "raised_by", "attempt_ids", "intent",
                                               "pending_decision"}
        assert questions[0].pending_decision is None
        # A formative-only question names itself for the valuation (Codex review F9): a ref, not a number.
        assert questions[0].target_hypotheses == [{"kind": "retention", "id": "f1"}]
        vault.config.followups.formative_questions_enabled = False
        assert RF.open_questions(vault, repo, summary, now=_now())[0] == []
    finally:
        module._facet_los, module.pending_cold_retry = original_los, original_retry


# -- dating by purpose ----------------------------------------------------------------------------


def test_a_discriminating_check_is_dated_for_the_next_days_plan(tmp_path):
    vault, repo, _session = _seeded(tmp_path)
    dated = RF.date_for(vault, repo, purpose=RF.PURPOSE_DISCRIMINATING, practice_item_id=None, attempt=None,
                        now=_now())
    assert dated == {"due_hint": (_now().astimezone().date() + timedelta(days=1)).isoformat(),
                     "basis": "next_day_plan", "capped": False}


def _state(due_at):
    return PracticeItemState(practice_item_id="pi_svd_define_001", difficulty=5.0, stability=3.0, retrievability=0.9,
                             due_at=due_at, active=True, content_hash=None, last_attempt_at=iso(20),
                             updated_at=iso(20))


@pytest.mark.parametrize("days, expected_offset, capped", [(5, 5, False), (30, 14, True), (-3, 1, False)])
def test_a_retention_check_is_dated_at_the_effective_due_within_the_cap(tmp_path, monkeypatch, days,
                                                                         expected_offset, capped):
    vault, repo, _session = _seeded(tmp_path)
    due = (_now() + timedelta(days=days)).isoformat().replace("+00:00", "Z")
    monkeypatch.setattr(type(repo), "practice_item_state", lambda self, item_id: _state(due))
    dated = RF.date_for(vault, repo, purpose=RF.PURPOSE_RETENTION, practice_item_id="pi_svd_define_001",
                        attempt=None, now=_now())
    today = _now().astimezone().date()
    expected = max((_now() + timedelta(days=days)).astimezone().date(), today + timedelta(days=1))
    expected = min(expected, today + timedelta(days=14))
    assert dated["due_hint"] == expected.isoformat() and dated["capped"] is capped
    assert dated["basis"] in ("effective_due", "fsrs_due")


def test_without_fsrs_state_the_date_is_the_schedulers_first_interval(tmp_path, monkeypatch):
    """No bare fallback: FSRS's own first stability for that attempt's rating."""

    from learnloop.attempts.attempts import fsrs_rating_for_attempt
    from learnloop.params.fitted_params import resolve_fsrs_weights

    vault, repo, _session = _seeded(tmp_path)
    monkeypatch.setattr(type(repo), "practice_item_state", lambda self, item_id: None)
    attempt = {"rubric_score": 4, "hints_used": 1, "created_at": iso(20)}
    dated = RF.date_for(vault, repo, purpose=RF.PURPOSE_RETENTION, practice_item_id="pi_svd_define_001",
                        attempt=attempt, now=_now())
    item = vault.practice_items["pi_svd_define_001"]
    weights = tuple(resolve_fsrs_weights(repo))
    days = F.interval_for_retention(F.initial_stability(fsrs_rating_for_attempt(item, 4, 4, 1), weights), 0.90,
                                    weights)
    when = T0 + timedelta(minutes=20) + timedelta(days=days)
    expected = max(when.astimezone().date(), _now().astimezone().date() + timedelta(days=1))
    assert dated["basis"] == "fsrs_first_interval" and dated["due_hint"] == expected.isoformat()


# -- daily re-valuation ---------------------------------------------------------------------------


def _planned(tmp_path, **kwargs):
    vault, repo, session = _seeded(tmp_path, **kwargs)
    row = _plan(vault, repo, session, FakeSearch([_candidate("pi_svd_define_002", 0.99, 0.01, 1.0)]))
    return vault, repo, row


def test_revaluation_retires_a_follow_up_answered_since_with_its_reason(tmp_path):
    vault, repo, row = _planned(tmp_path)
    [commitment_id] = row["followup_commitment_ids"]
    valued = []
    still = lambda question, item_id: valued.append(item_id) or {  # noqa: E731
        "problems": [{"verdict": "act", "checks": [{"ref": item_id}], "reason": "positive_robust_net_value"}]}
    report = RF.revalue_pending(vault, repo, now=_now(400), valuer=still, clock=at(400))
    assert report["kept"][0]["kept_because"] == ["clears_the_stop"] and valued == ["pi_svd_define_002"]
    # An unaided success on the claim's facet since: the question is answered.
    _attempt(repo, "att_own", minutes=500, hints=0, item="pi_svd_define_003")
    report = RF.revalue_pending(vault, repo, now=_now(400), valuer=still, clock=at(600))
    assert report["retired"] == [] and valued == ["pi_svd_define_002"]  # once a local day
    report = RF.revalue_pending(vault, repo, now=_now(400 + 60 * 24), valuer=still, clock=at(600 + 60 * 24))
    [line] = report["retired"]
    assert line["reason"] == RF.RETIRE_ANSWERED and line["detail"]["solved_attempt_id"] == "att_own"
    assert C.resolve_disposition(repo, commitment_id) == "stopped"
    # RW6a's "Since last time" reads it as good news.
    from learnloop.reader import recap as RC

    [retired] = RC.retired_checks(repo, extraction_id=EXT, after=iso(40))
    assert retired["commitment_id"] == commitment_id and retired["solved_attempt_id"] == "att_own"
    timeline = RF.coming_up(vault, repo, extraction_id=EXT, now=_now(2000))
    assert timeline["next"] == [] and timeline["retired"][0]["text"].startswith("No longer needed: you solved")


def test_the_cards_good_news_names_how_the_question_was_answered_and_drops_a_restored_check(tmp_path):
    """"Since last time" says *how* the question was answered (a solve on its
    date, or the rival explanations settled) and stops listing a retirement
    the learner undid (restored), so a reload never offers undo twice."""

    from learnloop.reader import recap as RC

    vault, repo, row = _planned(tmp_path)
    [commitment_id] = row["followup_commitment_ids"]
    _attempt(repo, "att_own", minutes=500, hints=0, item="pi_svd_define_003")
    RF.revalue_pending(vault, repo, now=_now(400 + 60 * 24), valuer=lambda *_a: {"problems": []},
                       clock=at(600 + 60 * 24))
    [retired] = RC.retired_checks(repo, extraction_id=EXT, after=iso(40))
    assert retired["answered_by"] == RF.ANSWERED_SOLVED and retired["solved_at"] == iso(500)
    RF.restore_followup(repo, commitment_id=commitment_id, clock=at(700 + 60 * 24))
    assert RC.retired_checks(repo, extraction_id=EXT, after=iso(40)) == []
    # A rivals-resolved retirement carries its own reason (no solve date).
    C.retire(repo, commitment_id=commitment_id, clock=at(800 + 60 * 24), detail={
        "reason": RF.RETIRE_ANSWERED, "answered_by": RF.ANSWERED_RIVALS, "episode_ids": ["ep1"],
        "extraction_id": EXT})
    [retired] = RC.retired_checks(repo, extraction_id=EXT, after=iso(40))
    assert retired["answered_by"] == RF.ANSWERED_RIVALS and retired["solved_at"] is None


def test_revaluation_retires_a_check_that_no_longer_clears_the_stop(tmp_path):
    vault, repo, row = _planned(tmp_path)
    stop = lambda question, item_id: {"problems": [{"verdict": "stop", "checks": [],  # noqa: E731
                                                    "reason": "lcb_value_below_minutes_cost"}]}
    report = RF.revalue_pending(vault, repo, now=_now(400), valuer=stop, clock=at(400))
    assert report["retired"][0]["reason"] == RF.RETIRE_BELOW_STOP


@pytest.mark.parametrize("receipt", [
    {"problems": [{"verdict": "abstain", "checks": [], "reason": "couldnt_reliably_distinguish"}]},
    {"problems": [{"verdict": "act", "checks": []}], "excluded": {"pi_svd_define_002": ["exposed"]}},
    {"problems": [], "unavailable": [{"reason": "no_prior"}]},
])
def test_an_abstention_an_exclusion_or_an_unknown_keeps_the_check(tmp_path, receipt):
    vault, repo, row = _planned(tmp_path)
    report = RF.revalue_pending(vault, repo, now=_now(400), valuer=lambda *_a: receipt, clock=at(400))
    assert report["retired"] == [] and report["kept"]
    assert C.resolve_disposition(repo, row["followup_commitment_ids"][0]) == "one_check_pending"


def test_a_closed_probe_episode_answers_a_discriminating_question():
    class Repo:
        @staticmethod
        def probe_episode(_id):
            return SimpleNamespace(status="completed")

    question = {"intent": "discriminate", "target_hypotheses": [{"kind": "episode_label", "id": "ep1"}]}
    assert RF.answered_since(None, Repo(), question, since=iso(0)) == {"answered_by": "rivals_resolved",
                                                                       "episode_ids": ["ep1"]}
    Repo.probe_episode = staticmethod(lambda _id: SimpleNamespace(status="in_progress"))
    assert RF.answered_since(None, Repo(), question, since=iso(0)) is None


# -- the timeline, undo, undo all, restore -------------------------------------------------------


def test_coming_up_is_a_dated_timeline_next_three_then_later(tmp_path):
    vault, repo, session = _seeded(tmp_path)
    _plan(vault, repo, session, FakeSearch([_candidate("pi_svd_define_002", 0.8, 0.2, 0.2),
                                            _candidate("pi_svd_define_003", 0.75, 0.25, 0.3),
                                            _candidate("pi_svd_define_004", 0.7, 0.3, 0.4)]))
    timeline = RF.coming_up(vault, repo, extraction_id=EXT, now=_now())
    assert len(timeline["next"]) == 3 and timeline["later"] == []
    line = timeline["next"][0]
    assert line["date"] and line["actions"] == ["why", "undo"]
    assert "LearnLoop's estimate" in line["why"] and "on your own" in line["purpose_text"]
    flat = json.dumps(timeline).lower()
    for word in ("error", "mistake", "wrong", "overdue", "weak"):
        assert word not in flat  # G16
    assert timeline["undo_all"] == [{"digest_id": RF.digest_id_for(EXT, session.session_id)}]


def test_undo_takes_an_optional_reason_on_a_learner_card_verdict(tmp_path):
    vault, repo, row = _planned(tmp_path)
    [commitment_id] = row["followup_commitment_ids"]
    result = RF.undo_followup(repo, commitment_id=commitment_id, reason="  I already know this one well  ",
                              clock=at(500))
    assert result["disposition"] == "stopped"
    with repo.connection() as connection:
        verdict = connection.execute("SELECT * FROM judgment_ledger WHERE task = ?", (RF.UNDO_TASK,)).fetchone()
        events = connection.execute("SELECT detail_json FROM commitment_events WHERE commitment_id = ? "
                                    "AND kind = 'retired'", (commitment_id,)).fetchall()
    assert verdict["judge"] == "learner_card" and verdict["left_id"] == commitment_id and verdict["verdict"] == "undone"
    assert json.loads(verdict["rationale"])["learner_reason"] == "I already know this one well"
    assert json.loads(events[0][0])["reason"] == RF.RETIRE_UNDONE
    # Idempotent.
    assert RF.undo_followup(repo, commitment_id=commitment_id)["judgment_id"] == result["judgment_id"]
    # Restore: pending again, and re-valuation leaves it to the learner.
    assert RF.restore_followup(repo, commitment_id=commitment_id)["disposition"] == "one_check_pending"
    stop = lambda *_a: {"problems": [{"verdict": "stop", "checks": []}]}  # noqa: E731
    assert RF.revalue_pending(vault, repo, now=_now(9000), valuer=stop)["retired"] == []


def test_undo_all_retires_every_pending_follow_up_from_the_session(tmp_path):
    vault, repo, session = _seeded(tmp_path)
    row = _plan(vault, repo, session, FakeSearch([_candidate("pi_svd_define_002", 0.8, 0.2, 0.2),
                                                  _candidate("pi_svd_define_003", 0.75, 0.25, 0.3)]))
    result = RF.undo_all(repo, digest_id=row["id"], reason=None)
    assert len(result["undone"]) == 2 and _pending(repo, row) == []
    with pytest.raises(RF.FollowupError):
        RF.undo_all(repo, digest_id="rsd_missing")


def test_only_reader_follow_ups_can_be_undone_here(tmp_path):
    vault, repo, _session = _seeded(tmp_path)
    other = C.create_commitment(repo, action="test_me_later", intent_text="mine",
                                targets=[{"target_kind": "legacy_practice_item", "target_ref": "pi_svd_define_002"}],
                                depth_preset="keep_in_touch", client_idempotency_key="k1")
    with pytest.raises(RF.FollowupError):
        RF.undo_followup(repo, commitment_id=other.id)


def test_undo_leaves_an_answered_check_answered(tmp_path):
    """An undo (or undo all) never retires a check its attempt already answered."""

    vault, repo, row = _planned(tmp_path)
    [commitment_id] = row["followup_commitment_ids"]
    C.satisfy_single_check(repo, commitment_id=commitment_id, clock=at(500))
    result = RF.undo_followup(repo, commitment_id=commitment_id, reason="late")
    assert result["disposition"] == "satisfied" and C.resolve_disposition(repo, commitment_id) == "satisfied"
    with repo.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM judgment_ledger WHERE task = ?",
                                  (RF.UNDO_TASK,)).fetchone()[0] == 0


# -- the sidecar RPCs -----------------------------------------------------------------------------


def test_the_rpcs_read_the_timeline_and_undo(tmp_path):
    vault, repo, row = _planned(tmp_path)
    ctx = context(vault.root)
    try:
        timeline = call(ctx, "reader.followups", {"extractionId": EXT})
        assert timeline["version"] == 1 and len(timeline["next"]) == 1
        [commitment_id] = row["followup_commitment_ids"]
        undone = call(ctx, "reader.followup_undo", {"commitmentId": commitment_id, "reason": "not now"})
        assert undone["disposition"] == "stopped"
        assert call(ctx, "reader.followups", {"extractionId": EXT})["next"] == []
        restored = call(ctx, "reader.followup_restore", {"commitmentId": commitment_id})
        assert restored["disposition"] == "one_check_pending"
    finally:
        ctx.close()


def test_the_plan_rpc_refuses_with_the_switch_off(tmp_path):
    from learnloop_sidecar.errors import SidecarError

    vault, _repo, _session = _seeded(tmp_path, config="[followups]\nenabled = false\n")
    ctx = context(vault.root)
    try:
        with pytest.raises(SidecarError) as refused:
            call(ctx, "reader.followups_plan", {})
        assert refused.value.code == "followups_disabled"
    finally:
        ctx.close()


# -- back to where you studied this (§9.3 item 9, G49) -------------------------------------------


def test_the_provenance_carries_the_way_back_and_dl2_renders_it(tmp_path, monkeypatch):
    from learnloop.intent.checks import restoration_link
    from tests.recap_fixtures import ask

    import learnloop.instructional.reader_followups as module

    vault, repo, session = _seeded(tmp_path)
    exchange = ask(vault, repo, "Why three factors?", 5)
    session = RS.sessions_for_source(repo, EXT)[0]
    monkeypatch.setattr(module, "learning_objects_for_span", lambda *_a, **_k: ["lo_svd_definition"])
    row = _plan(vault, repo, session, FakeSearch([_candidate("pi_svd_define_002", 0.99, 0.01, 1.0)]))
    [commitment_id] = row["followup_commitment_ids"]
    provenance = json.loads(repo.commitment_versions_for(commitment_id)[0]["provenance_json"])
    assert provenance["inquiry_root_event_ids"] == [exchange["reader_answer_event_id"]]
    assert provenance["anchor_span_ids"] == ["s1"]
    link = restoration_link(provenance)
    assert link["label"] == "Back to where you studied this" and link["source_id"] == "src1"
    assert link["detail"] == vault.learning_objects["lo_svd_definition"].title
    assert link["extraction_id"] == EXT


def test_the_recap_card_and_wrap_up_carry_coming_up(tmp_path):
    vault, repo, row = _planned(tmp_path)
    ctx = context(vault.root)
    try:
        card = call(ctx, "reader.recap", {"extractionId": EXT, "visitId": "v_now"})["recap"]
        assert len(card["comingUp"]["next"]) == 1 and card["comingUp"]["undoAll"] == [{"digestId": row["id"]}]
        wrap = call(ctx, "reader.wrap_up", {"extractionId": EXT})
        assert wrap["comingUp"]["next"][0]["commitmentId"] == row["followup_commitment_ids"][0]
    finally:
        ctx.close()


# -- replay: follow-ups are content, never re-valued, never evidence -----------------------------


def test_rebuild_shadow_is_zero_with_follow_ups_present(tmp_path):
    """``learnloop rebuild --shadow`` 0/0/0 with a digest, its commitments, a
    re-valuation retirement and an undo present: nothing replays or re-values them."""

    from learnloop.substrate.replay import rebuild_derived_state
    from learnloop.substrate.shadow_rebuild import shadow_rebuild

    vault, repo, session = _seeded(tmp_path)
    # The seeded attempt is a raw row: bring the projections in line first, so
    # the shadow diff measures only what the follow-ups would change.
    rebuild_derived_state(vault, repo, clock=at(250))
    assert shadow_rebuild(load_vault(vault.root)).learner_state_diff["summary"] == {
        "mastery": 0, "facet": 0, "schedule": 0}
    row = _plan(vault, repo, session, FakeSearch([_candidate("pi_svd_define_002", 0.8, 0.2, 0.2),
                                                  _candidate("pi_svd_define_003", 0.75, 0.25, 0.3)]))
    first, second = row["followup_commitment_ids"]
    RF.undo_followup(repo, commitment_id=first, reason="not now")
    with repo.connection() as connection:
        digests_before = connection.execute("SELECT * FROM reader_session_digests").fetchall()
    result = shadow_rebuild(load_vault(vault.root))
    assert result.learner_state_diff["summary"] == {"mastery": 0, "facet": 0, "schedule": 0}
    assert result.live_database_unchanged is True
    with repo.connection() as connection:
        assert connection.execute("SELECT * FROM reader_session_digests").fetchall() == digests_before
    assert C.resolve_disposition(repo, second) == "one_check_pending"
