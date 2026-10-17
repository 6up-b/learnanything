"""RW6a Codex review, round 2 (docs/reviews/reader-rw6a-codex-review.md).

* F1 (round 2) -- "as of the previous session's end" reads the grading state
  effective then: a regrade landing later no longer rewrites, through the
  novelty discount, the credit an earlier attempt banked before the cutoff.
* F3 (round 2) -- only credit that banks after the embedded-share cap answers
  a claim needing an independent check; uncapped embedded credit does not.

Everything runs through the production ledger writes, extraction, fold,
certification and recap; no timeline is mocked. Fakes only; no model call.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.attempts.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    ResolvedGrade,
    SelfGradeInput,
    apply_attempt,
    assessed_rubric_score,
    complete_self_graded_attempt,
)
from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.attempts.grading import resolved_rubric
from learnloop.attempts.grading_support import UNVERIFIED_REVIEW_REASON
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.goals.goal_certification import lo_certification
from learnloop.ids import new_ulid
from learnloop.learner.facet_evidence_timeline import facet_evidence_timelines
from learnloop.reader import reader_sessions as RS
from learnloop.reader import recap as RC
from learnloop.reader import workbench as WB
from learnloop.substrate.canonical_projection import project_canonical_facet_state, unassessed_evidence_row
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import write_yaml
from tests.helpers import NOW, NOW_ISO, set_algorithm_version
from tests.recap_fixtures import EXT, at, iso, problem, visit
from tests.test_goal_certification_any_of import COMP_A, LO_ID, _component, build_vault
from tests.test_reader_dialogue import _setup


def _stamp(minutes: float) -> str:
    return (NOW + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")


def _self_graded(vault, repository, item_id: str, minutes: float, criterion: str, points: float, *,
                 hints: int = 0) -> str:
    result = complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id=item_id, learner_answer_md="An answer.",
                     attempt_type="hinted_attempt" if hints else "independent_attempt", hints_used=hints),
        SelfGradeInput(criterion_points={criterion: points}, fatal_errors=[], confidence=4),
        clock=FrozenClock(NOW + timedelta(minutes=minutes)),
    )
    return str(result.attempt_id)


def _unassessed(vault, repository, item_id: str, minutes: float) -> str:
    """An attempt whose one criterion the grade left unassessed (PF-c), through
    the shared attempt step as the live door hands it."""

    clock = FrozenClock(NOW + timedelta(minutes=minutes))
    rubric = resolved_rubric(vault, vault.practice_items[item_id])
    attempt_id = new_ulid()
    apply_attempt(
        vault, repository,
        ApplyAttemptInput(
            draft=AttemptDraft(practice_item_id=item_id, learner_answer_md="Another route.",
                               attempt_type="independent_attempt"),
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=assessed_rubric_score(rubric, {"c1": 0.0}, [], unassessed_criterion_ids=("c1",)),
                criterion_points={"c1": 0.0},
                evidence_rows=[{
                    "id": new_ulid(), "criterion_id": "c1", "points_awarded": 0.0, "evidence": "unverified",
                    "notes": None, "local_grader_id": "test", "grader_tier": 1, "created_at": _stamp(minutes),
                }],
                error_attributions=[], grader_confidence=0.9, confidence=3,
                manual_review_reason=UNVERIFIED_REVIEW_REASON, feedback_md="", repair_suggestions=[],
            ),
            unverified_criterion_ids=("c1",),
        ),
        clock=clock,
    )
    return attempt_id


def _regrade(vault, repository, attempt_id: str, minutes: float, criterion: str, points: float) -> None:
    """A real retire-and-restate on the immutable ledger: the attempt's live
    rows are superseded and a later epoch restates the criterion, then the
    canonical projection is rebuilt from the ledger."""

    evidence_id = f"regrade_{attempt_id}_{int(minutes)}"
    repository.supersede_self_grade_rows(attempt_id, superseded_by_evidence_id=evidence_id,
                                         clock=FrozenClock(NOW + timedelta(minutes=minutes)))
    repository.insert_grading_evidence(attempt_id, [{
        "id": evidence_id, "criterion_id": criterion, "points_awarded": float(points), "evidence": None,
        "notes": "regrade", "grader_tier": 1, "created_at": _stamp(minutes),
    }])
    project_canonical_facet_state(vault, repository, clock=FrozenClock(NOW + timedelta(minutes=minutes)))


# -- F1 (round 2): the cutoff reads the grading state effective at the cutoff ----------------------


def test_f1_r2_a_later_regrade_does_not_rewrite_the_credit_banked_before_the_cutoff(tmp_path):
    """A is unassessed; B, on the same surface, certifies the LO before the
    previous session ends (minute 60); A is regraded at minute 120. At minute
    60 the LO was demonstrated, so A's regrade is not a gain since then."""

    paths = build_vault(tmp_path / "vault", {"id": "recipe_main", "composition": "conjunctive",
                                              "all_of": [_component(COMP_A)], "any_of": []})
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    lo = vault.learning_objects[LO_ID]

    attempt_a = _unassessed(vault, repository, "pi_comp_a", 5)
    assert all(unassessed_evidence_row(row.attribution_json) for row in repository.fetch_grading_evidence(attempt_a))
    attempt_b = _self_graded(vault, repository, "pi_comp_a", 10, "c1", 4)
    assert lo_certification(vault, repository, lo).demonstrated is True
    as_it_stood = facet_evidence_timelines(vault, repository, [COMP_A])[COMP_A]
    [b_then] = [point for point in as_it_stood if point.attempt_id == attempt_b]
    assert b_then.delta == pytest.approx(1.0)

    _regrade(vault, repository, attempt_a, 120, "c1", 4)
    assert lo_certification(vault, repository, lo).demonstrated is True
    # The current curve (default path, unchanged): A's latest grading now holds
    # the surface's novelty, so B's credit is the repeat-discounted share.
    now_curve = facet_evidence_timelines(vault, repository, [COMP_A])[COMP_A]
    [b_now] = [point for point in now_curve if point.attempt_id == attempt_b]
    assert b_now.delta < 1.0

    # As of the session's end the LO was already demonstrated: nothing new.
    assert RC.demonstrated_since(vault, repository, [LO_ID], after=_stamp(60)) == []
    # Before B it was not: B's certification is the gain, dated by B.
    gains = RC.demonstrated_since(vault, repository, [LO_ID], after=_stamp(7))
    assert [(row["learning_object_id"], row["demonstrated_on"], row["attempt_id"]) for row in gains] == [
        (LO_ID, _stamp(10), attempt_b),
    ]


@pytest.mark.parametrize("version", ["mvp-0.7", LATEST_ALGORITHM_VERSION])
def test_f1_r2_the_as_of_curve_ignores_gradings_recorded_after_the_cutoff(tmp_path, version):
    """The timeline read as of a moment: an epoch written later is absent and a
    row superseded later still stands, so the curve ends where it stood (at
    the latest tag too, where the current epoch is chosen among live rows)."""

    paths = build_vault(tmp_path / "vault", {"id": "recipe_main", "composition": "conjunctive",
                                              "all_of": [_component(COMP_A)], "any_of": []})
    set_algorithm_version(paths, version)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))

    attempt_a = _unassessed(vault, repository, "pi_comp_a", 5)
    attempt_b = _self_graded(vault, repository, "pi_comp_a", 10, "c1", 4)
    before = facet_evidence_timelines(vault, repository, [COMP_A])[COMP_A]
    _regrade(vault, repository, attempt_a, 120, "c1", 4)
    _regrade(vault, repository, attempt_b, 130, "c1", 0)

    as_of = facet_evidence_timelines(vault, repository, [COMP_A], as_of=_stamp(60))[COMP_A]
    assert [point.as_dict() for point in as_of] == [point.as_dict() for point in before]
    now = facet_evidence_timelines(vault, repository, [COMP_A])[COMP_A]
    assert [point.kind for point in now] == ["observation", "observation", "correction", "correction"]
    # Now B's credit is gone and A's regrade holds the surface: not the old curve.
    assert [point.as_dict() for point in now[:2]] != [point.as_dict() for point in before]


# -- F3 (round 2): uncredited embedded evidence answers no claim -----------------------------------

#: An item on ``compute`` whose one criterion also consumes ``recall`` (supporting).
EMBEDDED_ITEM = "pi_compute_with_recall"
#: An item whose one criterion targets ``recall`` directly (an authored target).
RECALL_ITEM = "pi_recall_targeted"


def _write_item(vault, item_id: str, targets: list[dict]) -> None:
    write_yaml(VaultPaths(vault.root, vault.config).practice_item_path("linear-algebra", item_id), {
        "schema_version": 1, "id": item_id, "learning_object_id": "lo_svd_definition", "subjects": None,
        "practice_mode": "constructed_response",
        "attempt_types_allowed": ["independent_attempt", "hinted_attempt", "dont_know"],
        "evidence_facets": ["recall"], "evidence_weights": {"recall": 1.0},
        "prompt": f"Prompt for {item_id}.", "expected_answer": "U Sigma V^T.", "difficulty": 0.5, "tags": [],
        "grading_rubric": {"max_points": 4, "fatal_errors": [], "criteria": [{
            "id": "c1", "points": 4, "description": "Answers it.", "targets": targets,
        }]},
        "provenance": {"origin": "human", "source_refs": []}, "created_at": NOW_ISO, "updated_at": NOW_ISO,
    })


def _embedded_world(tmp_path):
    vault, repo = _setup(tmp_path)
    _write_item(vault, EMBEDDED_ITEM, [{"facet": "compute", "capability": "procedure_execution", "role": "primary"},
                                       {"facet": "recall", "capability": "recall", "role": "supporting"}])
    _write_item(vault, RECALL_ITEM, [{"facet": "recall", "capability": "recall", "role": "primary"}])
    return load_vault(vault.root), repo


def _assisted_session(vault, repo):
    """A session whose book-visible, hinted problem on ``recall`` leaves a claim."""

    visit(repo, "v1", 0, 40)
    row = problem(repo, 2, steps=1, book=True)
    attempt = _self_graded(vault, repo, "pi_svd_define_001", 20, "correctness", 4, hints=1)
    WB.mark_submitted(repo, row["id"], attempt_id=attempt, practice_session_id="ps_1", clock=at(20))
    return RS.sessions_for_source(repo, EXT)[0]


def _claimed(vault, repo, session) -> list[str]:
    summary = RC.session_summary(vault, repo, extraction_id=EXT, session=session, now=NOW + timedelta(minutes=300))
    return [claim["facet_id"] for claim in summary["claims_needing_independent_check"]]


def test_f3_r2_embedded_only_credit_under_the_default_cap_leaves_the_claim_open(tmp_path):
    vault, repo = _embedded_world(tmp_path)
    share = vault.config.evidence.certification.max_embedded_credit_share
    assert share == 0.5  # the production default, read from the vault's own config
    session = _assisted_session(vault, repo)
    facet = vault.canonical_facet_id("recall")
    assert _claimed(vault, repo, session) == [facet]

    # Unassisted, full marks, and the trace shows recall exercised: recall gets
    # embedded credit only, which the default cap banks as nothing.
    own = _self_graded(vault, repo, EMBEDDED_ITEM, 200, "c1", 4)
    repo.insert_trace_exercised_facets(own, [{"facet_id": "recall", "observation_scope": "opportunistic",
                                              "evidence": "the trace shows it"}], clock=at(200))
    [point] = [p for p in facet_evidence_timelines(vault, repo, [facet])[facet] if p.attempt_id == own]
    assert point.attempt_credit > 0.0          # the uncapped contribution
    assert dict(point.capability_credit).get("recall", 0.0) == 0.0 and point.delta == 0.0
    assert _claimed(vault, repo, session) == [facet]


def test_f3_r2_embedded_credit_that_banks_answers_the_claim(tmp_path):
    """Control: with the cap off (share 1.0) the same embedded credit banks,
    so it is an unassisted success on the facet."""

    from tests.helpers import append_config_toml

    vault, repo = _embedded_world(tmp_path)
    append_config_toml(vault.root, """
    [evidence.certification]
    max_embedded_credit_share = 1.0
    """)
    vault = load_vault(vault.root)
    session = _assisted_session(vault, repo)
    facet = vault.canonical_facet_id("recall")
    own = _self_graded(vault, repo, EMBEDDED_ITEM, 200, "c1", 4)
    repo.insert_trace_exercised_facets(own, [{"facet_id": "recall", "observation_scope": "opportunistic",
                                              "evidence": "the trace shows it"}], clock=at(200))
    assert _claimed(vault, repo, session) == []


@pytest.mark.parametrize("history, answered", [
    ("revoked", False),        # a success regraded to nothing
    ("standing", True),        # a success that stands
    ("regraded_up", True),     # a failure regraded to a success
    ("before_session", False), # a success made before the session, regraded after it
])
def test_f3_a_success_regraded_to_nothing_leaves_the_claim_open(tmp_path, history, answered):
    """Round 1's F3 regression, now through the real ledger (it used to mock
    the timeline with synthetic events): assisted work, then an unassisted
    attempt on the facet whose effective (latest) grading decides whether it
    answers the claim."""

    vault, repo = _embedded_world(tmp_path)
    if history == "before_session":
        old = _self_graded(vault, repo, RECALL_ITEM, -10, "c1", 4)
    session = _assisted_session(vault, repo)
    facet = vault.canonical_facet_id("recall")
    if history == "revoked":
        own = _self_graded(vault, repo, RECALL_ITEM, 200, "c1", 4)
        _regrade_rows(repo, own, 260, "c1", 0)
    elif history == "standing":
        _self_graded(vault, repo, RECALL_ITEM, 200, "c1", 4)
    elif history == "regraded_up":
        own = _self_graded(vault, repo, RECALL_ITEM, 200, "c1", 0)
        _regrade_rows(repo, own, 260, "c1", 4)
    else:
        _regrade_rows(repo, old, 250, "c1", 4)
    assert _claimed(vault, repo, session) == ([] if answered else [facet]), history


def _regrade_rows(repo, attempt_id: str, minutes: float, criterion: str, points: float) -> None:
    evidence_id = f"regrade_{attempt_id}_{int(minutes)}"
    repo.supersede_self_grade_rows(attempt_id, superseded_by_evidence_id=evidence_id, clock=at(minutes))
    repo.insert_grading_evidence(attempt_id, [{
        "id": evidence_id, "criterion_id": criterion, "points_awarded": float(points), "evidence": None,
        "notes": "regrade", "grader_tier": 1, "created_at": iso(minutes),
    }])
