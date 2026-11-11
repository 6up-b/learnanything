"""What other test files use from ``tests/test_reader_followups.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import timedelta

from learnloop.algorithm_versions import READER_FOLLOWUPS_ALGORITHM_VERSION
from learnloop.instructional import reader_followups as RF
from learnloop.instructional.valuation import CandidateInput, ValuationProblem, value_candidates
from learnloop.reader import reader_sessions as RS
from learnloop.vault.loader import load_vault

from tests.helpers import add_followup_item, append_config_toml
from tests.recap_fixtures import EXT, T0, at, iso, problem, visit
from tests.reader_dialogue_helpers import _setup
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
        # The live checks seed the greedy selection as the real valuer does (round 3).
        receipt = value_candidates([problem], {problem.key: inputs}, caller_kind="reader", system_initiated=True,
                                   **({"already_chosen": kwargs["already_chosen"]}
                                      if kwargs.get("already_chosen") else {}))
        return {"status": "ok", "proposal_id": f"pp_fake_{len(self.calls)}", "valuation": receipt,
                "paging": {"outcome": "exhausted"}, "rerank_status": "reranked"}


def _plan(vault, repo, session, search, minutes=NOW_MIN):
    return RF.plan_session(vault, repo, extraction_id=EXT, session=session, search=search, now=_now(minutes),
                           clock=at(minutes))
