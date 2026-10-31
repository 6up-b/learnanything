"""Reader RW6b part 1: Codex re-review round 3 (F14 reopened, F15), each
reproduced first (docs/reviews/reader-rw6b-p1-followups-codex-review.md,
"Round 3").

Round 2 retired a live check when a resumed search no longer selected it.
That lost checks (F14: three budgeted searches end with nothing live) and
abandoned a question another check served (F15). Round 3 removes retirement
by reconciliation and applies the spec's own rule (§9.3 item 3: checks are
added greedily, each valued conditionally on those already chosen):

* the question's live checks seed the greedy conditional selection
  (``value_candidates(already_chosen=...)``; the default is byte-for-byte
  unchanged), so a resumed or re-asked search adds a check only if it still
  clears the stop given them, and never retires one;
* rescheduling reads the live checks, not every ref ever chosen: an item
  whose check was retired may be scheduled again as a fresh generation; one
  the learner undid stays out;
* a check several questions select is created once, records every licensing
  question, and re-valuation keeps it while any of them needs it.

Fakes only; no model call anywhere.
"""

from __future__ import annotations

import hashlib
import json

from learnloop.curriculum import commitments as C
from learnloop.db.stores import reader_digests as RDG
from learnloop.instructional import reader_followups as RF
from learnloop.instructional.valuation import (
    CandidateInput,
    PendingDecision,
    ValuationProblem,
    value_candidates,
    value_problem,
)
from learnloop.scheduling import action_loss as AL
from tests.recap_fixtures import EXT, at
from tests.test_reader_followups import FakeSearch, NOW_MIN, _candidate, _now, _plan, _seeded
from tests.test_reader_followups_rereview import _PerCall

A = "pi_svd_define_002"
B = "pi_svd_define_003"
D = "pi_svd_define_004"

SLOTS = ("mastered", "misconception:m1", "misconception:m2", "unfamiliar")


def _separates(winner, *, sharpness=0.98):
    return {slot: ({"hit": sharpness, "miss": 1 - sharpness} if slot == winner
                   else {"hit": 1 - sharpness, "miss": sharpness}) for slot in SLOTS}


def _input(ref, table, *, regime="pinned_channel", members=3, minutes=1.0):
    return CandidateInput(ref=ref, kind="item", members=tuple([table] * members), outcome_alphabet=("hit", "miss"),
                          regime=regime, likelihood_basis="estimated_row", expected_minutes=minutes,
                          construction=f"{regime}:{members}")


def _information_problem():
    return ValuationProblem(key="lo:x", space_kind="hypothesis_set", slots=SLOTS,
                            prior={slot: 0.25 for slot in SLOTS}, prior_basis="hypothesis_set", state_hash="h")


def _decision_problem():
    routes = [{"reason": "h1", "first_intervention": "repair_a"}, {"reason": "h2", "first_intervention": "repair_b"}]
    table = AL.build_loss_table(routes=routes, duration_overrides={"repair_a": 10.0, "repair_b": 10.0})
    return ValuationProblem(key="causal:f", space_kind="causal_factor", slots=("h1", "h2"),
                            prior={"h1": 0.5, "h2": 0.5}, prior_basis="support_weighted", state_hash="c",
                            decision=PendingDecision("repair_class", {"h1": "repair_a", "h2": "repair_b"}, table))


def _sharp(ref="sharp"):
    return CandidateInput(ref=ref, kind="item", members=({"h1": {"x": 1.0}, "h2": {"y": 1.0}},),
                          outcome_alphabet=("x", "y"), regime="pinned_channel", construction="p", expected_minutes=1.0)


def _golden_inputs():
    return {
        "lo:x": [_input("a", _separates("misconception:m1", sharpness=0.99)),
                 _input("b", _separates("misconception:m2", sharpness=0.93), minutes=1.5),
                 _input("a_copy", _separates("misconception:m1", sharpness=0.99), minutes=2.0),
                 _input("point", _separates("unfamiliar"), regime="item_point")],
        "causal:f": [_sharp()],
    }


def _golden_receipts(**kwargs):
    return [value_candidates([_information_problem(), _decision_problem()], _golden_inputs(), caller_kind=kind,
                             system_initiated=system, **kwargs)
            for kind, system in (("learner", False), ("reader_followup", True))]


#: sha256 of the canonical JSON of :func:`_golden_receipts`, computed from
#: the code before round 3 (50f502ac0).
GOLDEN_BEFORE_ROUND_3 = "a5ede5404c3aac095638cb5b85343942ef18baef5eb9f0bc3e89525d11a2a96d"


def _digest(receipts):
    return hashlib.sha256(json.dumps(receipts, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


# -- value_candidates: the optional seed, default unchanged -----------------------------------------


def test_value_candidates_without_already_chosen_is_byte_for_byte_the_previous_receipt():
    assert _digest(_golden_receipts()) == GOLDEN_BEFORE_ROUND_3
    assert _digest(_golden_receipts(already_chosen=())) == GOLDEN_BEFORE_ROUND_3
    assert "already_chosen" not in json.dumps(_golden_receipts())


def test_a_live_check_seeds_the_greedy_selection_and_is_never_a_new_check():
    redundant = [_input("a", _separates("misconception:m1", sharpness=1.0)),
                 _input("a_copy", _separates("misconception:m1", sharpness=1.0), minutes=0.5)]
    unseeded = value_problem(_information_problem(), redundant, system_initiated=True)
    assert [check["ref"] for check in unseeded["checks"]] == ["a_copy"]  # cheaper, same information
    seeded = value_problem(_information_problem(), redundant, system_initiated=True, already_chosen=["a"])
    assert (seeded["verdict"], seeded["reason"], seeded["checks"]) == ("stop", "already_chosen_suffice", [])
    assert seeded["already_chosen"] == {"conditioned_on": ["a"], "not_valued": []}
    # A check that still adds information given the live one is added, after it.
    distinct = [_input("a", _separates("misconception:m1", sharpness=0.99)),
                _input("b", _separates("misconception:m2", sharpness=0.99))]
    added = value_problem(_information_problem(), distinct, system_initiated=True, already_chosen=["a", "gone"])
    assert [check["ref"] for check in added["checks"]] == ["b"] and added["checks"][0]["order"] == 2
    assert added["already_chosen"] == {"conditioned_on": ["a"], "not_valued": ["gone"]}
    # A decision is settled by one measurement: a live one in the space is it.
    decided = value_problem(_decision_problem(), [_sharp(), _sharp("other")], system_initiated=True,
                            already_chosen=["sharp"])
    assert (decided["verdict"], decided["reason"], decided["checks"]) == ("stop", "already_chosen_suffice", [])


# -- F14 (reopened): three budgeted/resumed searches never lose the check ------------------------------


def _live(repo):
    with repo.connection() as connection:
        ids = [row[0] for row in connection.execute("SELECT id FROM commitments")]
    return {cid for cid in ids if C.resolve_disposition(repo, cid) == "one_check_pending"}


def _consistent(repo, row):
    """The digest holds every live check and names each chosen line's commitment."""

    chosen = row["valuation"]["chosen"]
    assert {line["commitment_id"] for line in chosen} <= set(row["followup_commitment_ids"])
    assert _live(repo) <= set(row["followup_commitment_ids"])
    assert len(row["followup_commitment_ids"]) == len(set(row["followup_commitment_ids"]))


def test_f14_the_exact_three_search_sequence_ends_with_exactly_one_live_check(tmp_path):
    vault, repo, session = _seeded(tmp_path)
    search = _PerCall([[_candidate(A, 1.0, 0.0, 3.0)],
                       [_candidate(A, 1.0, 0.0, 3.0), _candidate(B, 1.0, 0.0, 2.0)],
                       [_candidate(A, 1.0, 0.0, 1.0), _candidate(B, 1.0, 0.0, 2.0)]])
    first = _plan(vault, repo, session, search)
    assert first["status"] == "incomplete" and [line["ref"] for line in first["valuation"]["chosen"]] == [A]
    second = _plan(vault, repo, session, search, minutes=NOW_MIN + 60)
    assert second["status"] == "incomplete"
    third = _plan(vault, repo, session, search, minutes=NOW_MIN + 120)
    assert len(search.calls) == 3 and third["status"] == "planned"
    # Round 2 ended here with A and B both stopped, the digest planned and Coming up empty.
    [live] = _live(repo)
    _consistent(repo, third)
    refs = {line["commitment_id"]: line["ref"] for line in third["valuation"]["chosen"]}
    assert refs[live] == A
    assert [call.get("already_chosen") for call in search.calls] == [None, [A], [A]]
    [question] = third["valuation"]["questions"]
    assert question["outcome"] == "checks" and question["already_chosen"] == [A]
    timeline = RF.coming_up(vault, repo, extraction_id=EXT, now=_now(NOW_MIN + 120))
    assert [line["commitment_id"] for line in timeline["next"]] == [live] and timeline["retired"] == []


def test_a_re_ask_whose_live_check_already_suffices_adds_nothing(tmp_path):
    vault, repo, session = _seeded(tmp_path)

    class NoCursorBudget(FakeSearch):
        """The first search stops on its budget with nothing to resume: the next one is a fresh search."""

        def __call__(self, query, constraints, *, caller, **kwargs):
            result = dict(super().__call__(query, constraints, caller=caller, **kwargs))
            if len(self.calls) == 1:
                result["paging"] = {"outcome": "budget"}
            return result

    search = NoCursorBudget([_candidate(A, 1.0, 0.0, 3.0)])
    first = _plan(vault, repo, session, search)
    [earlier] = first["followup_commitment_ids"]
    search.candidates = [_candidate(A, 1.0, 0.0, 3.0), _candidate(D, 1.0, 0.0, 0.5)]
    again = _plan(vault, repo, session, search, minutes=NOW_MIN + 60)
    assert "continue_from" not in search.calls[1] and search.calls[1]["already_chosen"] == [A]
    assert again["status"] == "planned" and again["followup_commitment_ids"] == [earlier]
    assert _live(repo) == {earlier}
    [question] = again["valuation"]["questions"]
    assert question["outcome"] == "checks" and question["search_outcome"] == "no_check"
    section = question["valuation"]["problems"][0]
    assert section["reason"] == "already_chosen_suffice" and section["checks"] == []


# -- rescheduling reads the live checks: a fresh generation, never a retired check -------------------


def _stop_valuer(*_a):
    return {"problems": [{"verdict": "stop", "reason": "lcb_value_below_minutes_cost", "checks": []}]}


def test_an_item_whose_check_was_retired_is_scheduled_again_as_a_fresh_generation(tmp_path):
    vault, repo, session = _seeded(tmp_path)
    search = _PerCall([[_candidate(A, 1.0, 0.0, 3.0)], [_candidate(A, 1.0, 0.0, 3.0)]])
    first = _plan(vault, repo, session, search)
    [earlier] = first["followup_commitment_ids"]
    report = RF.revalue_pending(vault, repo, now=_now(NOW_MIN + 30), valuer=_stop_valuer, clock=at(NOW_MIN + 30))
    assert [line["reason"] for line in report["retired"]] == [RF.RETIRE_BELOW_STOP]
    again = _plan(vault, repo, session, search, minutes=NOW_MIN + 60)
    assert search.calls[1].get("already_chosen") is None  # nothing live to condition on
    assert again["status"] == "planned"
    _consistent(repo, again)
    [fresh] = _live(repo)
    assert fresh != earlier and C.resolve_disposition(repo, earlier) == "stopped"
    lines = {line["commitment_id"]: line for line in again["valuation"]["chosen"]}
    assert (lines[earlier]["generation"], lines[fresh]["generation"]) == (0, 1)
    assert lines[fresh]["ref"] == A
    timeline = RF.coming_up(vault, repo, extraction_id=EXT, now=_now(NOW_MIN + 60))
    assert [line["commitment_id"] for line in timeline["next"]] == [fresh]


def test_an_item_the_learner_undid_is_never_scheduled_again_by_the_same_session(tmp_path):
    vault, repo, session = _seeded(tmp_path)
    search = _PerCall([[_candidate(A, 1.0, 0.0, 3.0)], [_candidate(A, 1.0, 0.0, 3.0)]])
    first = _plan(vault, repo, session, search)
    [earlier] = first["followup_commitment_ids"]
    RF.undo_followup(repo, commitment_id=earlier, reason="not now", clock=at(NOW_MIN + 30))
    again = _plan(vault, repo, session, search, minutes=NOW_MIN + 60)
    assert A in search.calls[1]["constraints"]["exclude_item_ids"]
    assert again["followup_commitment_ids"] == [earlier] and _live(repo) == set()


# -- F15: a shared check stays live while any licensing question needs it ----------------------------


Q1 = "retention:recall"
Q2 = "retention:procedure"


def _two_questions(monkeypatch):
    def questions(*_a, **_k):
        return ([RF.Question(key=Q1, purpose=RF.PURPOSE_RETENTION, learning_object_ids=["lo_svd_definition"],
                             facet_ids=["recall"], attempt_ids=["att_book"]),
                 RF.Question(key=Q2, purpose=RF.PURPOSE_RETENTION, learning_object_ids=["lo_svd_definition"],
                             facet_ids=["procedure"], attempt_ids=["att_book"])], [])

    monkeypatch.setattr(RF, "open_questions", questions)


class _ByQuestion(FakeSearch):
    """Per question (its facet), call ``n`` values ``rounds[facet][n]``;
    every call but the question's last stops on its budget with a cursor."""

    def __init__(self, rounds):
        super().__init__([])
        self.rounds = rounds
        self.seen: dict[str, int] = {}

    def __call__(self, query, constraints, *, caller, **kwargs):
        facet = constraints["facet_ids"][0]
        n = self.seen.get(facet, 0)
        self.seen[facet] = n + 1
        rounds = self.rounds[facet]
        self.candidates = rounds[min(n, len(rounds) - 1)]
        result = dict(super().__call__(query, constraints, caller=caller, **kwargs))
        if n + 1 < len(rounds):
            result["paging"] = {"outcome": "budget", "cursor": {"judged_items": []}}
        return result


def test_f15_resuming_one_question_never_abandons_the_check_another_question_shares(tmp_path, monkeypatch):
    vault, repo, session = _seeded(tmp_path)
    _two_questions(monkeypatch)
    # Q1 (recall) chooses A and stops on its budget; Q2 (procedure) chooses A and finishes.
    # Resumed, Q1 finds B, cheaper and with the same information on recall only.
    search = _ByQuestion({"recall": [[_candidate(A, 1.0, 0.0, 3.0)],
                                     [_candidate(A, 1.0, 0.0, 3.0), _candidate(B, 1.0, 0.0, 1.0)]],
                          "procedure": [[_candidate(A, 1.0, 0.0, 3.0)]]})
    first = _plan(vault, repo, session, search)
    assert first["status"] == "incomplete"
    [shared] = first["followup_commitment_ids"]
    again = _plan(vault, repo, session, search, minutes=NOW_MIN + 60)
    assert again["status"] == "planned"
    # Round 2 retired A here (Q2 left with no check) and scheduled B for Q1.
    assert _live(repo) == {shared} and again["followup_commitment_ids"] == [shared]
    _consistent(repo, again)
    [line] = again["valuation"]["chosen"]
    assert line["ref"] == A and line["questions"] == [Q1, Q2]
    entries = {entry["key"]: entry for entry in first["valuation"]["questions"]}
    assert entries[Q2]["shared"] == [{"ref": A, "commitment_id": None, "first_licensed_by": Q1}]
    resumed = [call for call in search.calls if call["constraints"]["facet_ids"] == ["recall"]][-1]
    assert resumed["already_chosen"] == [A] and resumed["continue_from"]
    # Shown once on Coming up.
    timeline = RF.coming_up(vault, repo, extraction_id=EXT, now=_now(NOW_MIN + 60))
    assert [line["commitment_id"] for line in timeline["next"]] == [shared]


def test_f15_revaluation_keeps_a_shared_check_while_any_licensing_question_needs_it(tmp_path, monkeypatch):
    vault, repo, session = _seeded(tmp_path)
    _two_questions(monkeypatch)
    search = _ByQuestion({"recall": [[_candidate(A, 1.0, 0.0, 3.0)]], "procedure": [[_candidate(A, 1.0, 0.0, 3.0)]]})
    row = _plan(vault, repo, session, search)
    [shared] = row["followup_commitment_ids"]
    asked = []

    def recall_answered_procedure_open(question, item_id):
        asked.append(tuple(question["facet_ids"]))
        if question["facet_ids"] == ["recall"]:
            return _stop_valuer()
        return {"problems": [{"verdict": "act", "reason": "positive_robust_net_value", "checks": [{"ref": item_id}]}]}

    report = RF.revalue_pending(vault, repo, now=_now(NOW_MIN + 30), valuer=recall_answered_procedure_open,
                                clock=at(NOW_MIN + 30))
    [kept] = report["kept"]
    assert kept["kept_because"] == ["clears_the_stop"] and kept["questions"] == [Q1, Q2]
    assert asked == [("recall",), ("procedure",)]
    assert C.resolve_disposition(repo, shared) == "one_check_pending"
    # Below the stop for every licensing question: retired.
    report = RF.revalue_pending(vault, repo, now=_now(NOW_MIN + 60), valuer=_stop_valuer, clock=at(NOW_MIN + 60),
                                force=True)
    [retired] = report["retired"]
    assert retired["reason"] == RF.RETIRE_BELOW_STOP and C.resolve_disposition(repo, shared) == "stopped"


def test_round_2s_reconciliation_reason_is_gone():
    import inspect

    assert not hasattr(RF, "RETIRE_SUPERSEDED")
    assert "superseded_by_resumed_search" not in inspect.getsource(RF)
    with_digest = RDG  # the digest store is unchanged: no reconciliation column or reason
    assert "superseded_by_resumed_search" not in inspect.getsource(with_digest)
