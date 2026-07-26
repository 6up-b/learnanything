"""The §3 B5 scoreboard (implementation_plan_v1.md items 4.1/4.3/4.4).

THE ONE RULE UNDER TEST. A metric with no data reports `unavailable`, never
`0.0`. `harmful_write_rate`'s target IS ~0, so a rate over an empty denominator
that rendered as zero would be indistinguishable from a solved problem — and the
same holds for `false_certification_rate` and for `probe_action_change_rate` on a
vault where no probe has been administered. `test_every_metric_is_unavailable_on_a_fresh_vault`
is the whole-board version of that assertion; the per-metric tests pin each arm.

SECOND RULE. The four adjudication-owned metrics and `measurement_rank` are
COMPOSED, not reimplemented. `test_adjudication_metrics_are_composed_not_recomputed`
and `test_measurement_rank_is_composed_from_identifiability` monkeypatch the
upstream producers and require the board to move with them — a silent
reimplementation passes neither.

Every attempt in here goes through the real `apply_attempt`; nothing fabricates a
receipt or a debug payload, per `tests/test_diagnosis_adjudication.py`'s note that
hand-built receipts are how dead code passes review in this area.
"""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    GradeAttribution,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.services.diagnosis_adjudication import append_diagnosis_adjudication
from learnloop.services.scoreboard import (
    AVAILABILITY,
    B5_ORDER,
    HARMFUL_WITHDRAWAL_REASONS,
    Metric,
    cells_cleared_per_question,
    cold_success_metrics,
    cold_success_trajectories,
    harmful_write_rate,
    measurement_rank_metric,
    planted_vs_adjudicated_agreement,
    probe_action_change_rate,
    scoreboard,
    tokens_per_resolved_diagnostic_episode,
)
from learnloop.services.surfaced_beliefs import (
    mark_belief_surfaced,
    record_belief_withdrawal,
)
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, NOW_ISO, create_basic_vault


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------


def _vault(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    return load_vault(paths.root), Repository(paths.sqlite_path), paths


def _belief(repository, belief_id: str, statement: str) -> str:
    """A real `misconceptions` row.

    `misconception_disposition_events` has an FK onto it, so a withdrawal cannot
    be recorded against an invented id — which is itself the scope guard working:
    the A6 lifecycle only applies to beliefs the system actually holds.
    """

    return repository.insert_misconception(
        id=belief_id,
        learning_object_id="lo_svd_definition",
        statement=statement,
        facet_ids=["recall"],
        clock=FrozenClock(NOW),
    )


def _surface_belief(repository, belief_id: str, statement: str, surface: str) -> None:
    """Create the belief and record that the learner was shown it."""

    _belief(repository, belief_id, statement)
    mark_belief_surfaced(
        repository,
        belief_id=belief_id,
        claim_text=statement,
        surface=surface,
        clock=FrozenClock(NOW),
    )


def _attempt(
    vault,
    repository,
    attempt_id: str,
    *,
    correctness_points: int = 0,
    attempt_type: str = "independent_attempt",
    hints_used: int = 0,
    latency_seconds: int | None = None,
    resolution_status: str = "unresolved",
    misconception_statement: str | None = None,
):
    """One real graded attempt through the live path.

    `correctness_points` drives the rubric score (max 4), which is what
    `practice_attempts.correctness` is derived from — so 4 is a full-credit
    attempt and 0 is a failure.
    """

    attribution = GradeAttribution(
        error_type="conceptual_slip",
        severity=0.7,
        evidence="The final factor is not transposed.",
        is_misconception=misconception_statement is not None,
        misconception_statement=misconception_statement,
        resolution_status=resolution_status,
        # A `resolved` attribution is one that NAMES a target — that is the
        # condition the live telemetry derives the status from
        # (`services/attempts.py`: resolved iff target families / criteria /
        # a non-`none` target_ref). Setting the string alone would leave the
        # persisted resolution_counts saying `unresolved`, and the metric reads
        # the persisted counts, not the caller's intent.
        target_evidence_families=["recall"] if resolution_status == "resolved" else [],
        target_criterion_ids=["correctness"] if resolution_status == "resolved" else [],
        abstention_reason=(
            "no facet in the vocabulary names branch retention"
            if resolution_status == "abstained"
            else None
        ),
        cause_scope="learner_state" if misconception_statement else "unknown",
        operation="transpose_confusion" if misconception_statement else None,
        first_divergence=(
            {"anchor_kind": "span", "criterion_id": "correctness", "quote": "Q"}
            if misconception_statement
            else None
        ),
        model_reported_causal_confidence=0.65,
        candidate_causes=(
            [
                {
                    "statement": misconception_statement,
                    "cause_scope": "learner_state",
                    "target_ref": {
                        "kind": "facet_capability",
                        "facet_id": "recall",
                        "capability": "retrieval",
                    },
                }
            ]
            if misconception_statement
            else []
        ),
        postdictive_claims=(
            [{"criterion_id": "correctness", "must": "not_full_credit"}]
            if misconception_statement
            else []
        ),
    )
    return apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id="pi_svd_define_001",
                learner_answer_md="U Sigma Q",
                attempt_type=attempt_type,
                hints_used=hints_used,
                latency_seconds=latency_seconds,
            ),
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=correctness_points,
                criterion_points={"correctness": correctness_points},
                evidence_rows=[
                    {
                        "id": f"ge_{attempt_id}",
                        "criterion_id": "correctness",
                        "points_awarded": float(correctness_points),
                        "evidence": "Transpose check.",
                        "notes": None,
                        "local_grader_id": "test",
                        "grader_tier": 1,
                        "created_at": NOW_ISO,
                    }
                ],
                error_attributions=[attribution],
                grader_confidence=0.9,
                confidence=4,
                manual_review_reason=None,
                feedback_md="Check the transpose on the final factor.",
                repair_suggestions=[],
            ),
        ),
        clock=FrozenClock(NOW),
    )


# ---------------------------------------------------------------------------
# The board contract
# ---------------------------------------------------------------------------


def test_board_is_the_frozen_b5_list_in_b5_order(tmp_path):
    vault, repository, _paths = _vault(tmp_path)
    report = scoreboard(vault, repository)

    assert [metric["name"] for metric in report["metrics"]] == list(B5_ORDER)
    # B5's ordering argument: the two learner-denominated metrics lead, because a
    # system can raise anchor accuracy while becoming slower and more
    # interrogative and every other row would report success.
    assert B5_ORDER[0] == "problems_to_cold_success"
    assert B5_ORDER[2] == "harmful_write_rate"
    assert B5_ORDER.index("false_certification_rate") < B5_ORDER.index(
        "questions_to_certification"
    )
    # The minutes companion rides with the primary, not as a peer.
    minutes = next(
        metric
        for metric in report["metrics"]
        if metric["name"] == "learner_minutes_to_cold_success"
    )
    assert minutes["companion_of"] == "problems_to_cold_success"


#: The one B5 metric that is a property of the ITEM POOL rather than of learner
#: activity — §5.7: "independent dimensions the item pool can actually resolve,
#: vs facets declared". A vault with authored content but no attempts has a real
#: measurement rank, so it is legitimately available on a fresh vault. Every
#: other metric on the board is denominated in something the learner did.
_ACTIVITY_FREE_METRICS = frozenset({"measurement_rank"})


def test_every_metric_is_unavailable_on_a_fresh_vault(tmp_path):
    """The headline invariant, board-wide.

    An unused vault must produce an explicit refusal for every metric denominated
    in learner activity. If any came back as 0.0 the board would report a system
    with no harmful writes, no false certifications, and probes that never change
    an action.
    """

    vault, repository, _paths = _vault(tmp_path)
    report = scoreboard(vault, repository)

    for metric in report["metrics"]:
        assert metric["availability"] in AVAILABILITY, metric
        if metric["name"] in _ACTIVITY_FREE_METRICS:
            continue
        assert not metric["available"], f"{metric['name']} claims data it lacks"
        assert metric["value"] is None, f"{metric['name']} reported {metric['value']}"
        assert metric["note"], f"{metric['name']} refuses without saying why"
    assert report["available"] == len(_ACTIVITY_FREE_METRICS)
    assert len(report["unavailable"]) == len(B5_ORDER) - len(_ACTIVITY_FREE_METRICS)
    # Each refusal must name a remedy-bearing arm, not a generic falsy value.
    assert {entry["availability"] for entry in report["unavailable"]} <= set(AVAILABILITY)


def test_a_metric_may_not_carry_a_value_on_an_unavailable_arm():
    """The dataclass itself refuses the defect shape, not just its callers."""

    with pytest.raises(ValueError, match="no_data may not carry a value"):
        Metric(
            name="harmful_write_rate",
            availability="no_data",
            value=0.0,
            numerator=0,
            denominator=0,
            unit="rate",
            denominator_label="beliefs surfaced to the learner",
            note="",
        )
    with pytest.raises(ValueError, match="available metric carries no value"):
        Metric(
            name="harmful_write_rate",
            availability="available",
            value=None,
            numerator=0,
            denominator=1,
            unit="rate",
            denominator_label="beliefs surfaced to the learner",
            note="",
        )
    with pytest.raises(ValueError, match="unknown availability"):
        Metric(
            name="x",
            availability="probably_fine",
            value=None,
            numerator=None,
            denominator=None,
            unit="rate",
            denominator_label="",
            note="",
        )


# ---------------------------------------------------------------------------
# 4.1 — problems_to_cold_success + minutes companion
# ---------------------------------------------------------------------------


def test_problems_to_cold_success_counts_problems_until_the_first_cold_success(tmp_path):
    vault, repository, _paths = _vault(tmp_path)
    # Two failures, then a full-credit unassisted attempt: three problems served.
    _attempt(vault, repository, "att_1", correctness_points=0, latency_seconds=30)
    _attempt(vault, repository, "att_2", correctness_points=0, latency_seconds=60)
    _attempt(vault, repository, "att_3", correctness_points=4, latency_seconds=90)
    # A fourth attempt AFTER the cold success must not be counted.
    _attempt(vault, repository, "att_4", correctness_points=4, latency_seconds=120)

    problems, minutes = cold_success_metrics(repository)

    assert problems.availability == "available"
    assert problems.value == 3.0
    assert problems.denominator == 1
    assert problems.detail["censored_learning_objects"] == 0
    # 30 + 60 + 90 = 180s = 3 minutes; the post-success 120s is excluded.
    assert minutes.availability == "available"
    assert minutes.value == 3.0
    assert minutes.companion_of == "problems_to_cold_success"


def test_an_assisted_success_is_not_a_cold_success(tmp_path):
    """`attempt_counts_as_assisted` is the authority, and a hint disqualifies.

    Composition test as much as a semantics test: if this module grew its own
    assistance predicate it would drift from the projection that feeds
    certification.
    """

    vault, repository, _paths = _vault(tmp_path)
    _attempt(
        vault,
        repository,
        "att_hinted",
        correctness_points=4,
        attempt_type="hinted_attempt",
        hints_used=1,
        latency_seconds=45,
    )

    trajectories = cold_success_trajectories(repository)
    assert len(trajectories) == 1
    assert trajectories[0].reached is False

    problems, _minutes = cold_success_metrics(repository)
    assert problems.availability == "no_data"
    assert problems.value is None
    # Right-censoring must stay visible: the learner did answer a problem.
    assert problems.detail["censored_learning_objects"] == 1
    assert problems.detail["censored_problems_served"] == 1


def _two_learning_object_vault(tmp_path):
    """The basic fixture plus a SECOND learning object with its own item.

    Needed because censoring is a per-learning-object fact and the basic fixture
    declares exactly one, so a censored trajectory cannot exist in it at all.
    """

    from learnloop.vault.yaml_io import write_yaml
    from tests.test_km2_write_path import _item, _lo, _rubric

    paths = create_basic_vault(tmp_path / "vault")
    write_yaml(
        paths.learning_object_path("linear-algebra", "lo_svd_apply"),
        _lo("lo_svd_apply", "Apply SVD", "Use the factorization."),
    )
    write_yaml(
        paths.practice_item_path("linear-algebra", "pi_svd_apply_001"),
        _item(
            "pi_svd_apply_001",
            "lo_svd_apply",
            evidence_facets=["recall"],
            rubric=_rubric("correctness", []),
        ),
    )
    return load_vault(paths.root), Repository(paths.sqlite_path), paths


def test_censored_learning_objects_are_reported_and_excluded_from_the_mean(tmp_path):
    """The "more accurate AND more annoying" guard.

    A learning object that never reaches a cold success is dropped from the mean
    — so the mean would IMPROVE as the system got worse unless the censored count
    rides alongside it. This is precisely what B5 means by
    `problems_to_cold_success` being "the only one that fails when the system gets
    more accurate *and* more annoying": without the censored count it would not
    fail either.
    """

    vault, repository, _paths = _two_learning_object_vault(tmp_path)
    # lo_svd_definition: cold success on the first problem.
    _attempt(vault, repository, "att_win", correctness_points=4, latency_seconds=10)
    # lo_svd_apply: four problems served, never a cold success.
    for index in range(4):
        apply_attempt(
            vault,
            repository,
            ApplyAttemptInput(
                draft=AttemptDraft(
                    practice_item_id="pi_svd_apply_001",
                    learner_answer_md="no idea",
                    latency_seconds=10,
                ),
                attempt_id=f"att_lose_{index}",
                grade=ResolvedGrade(
                    rubric_score=0,
                    criterion_points={"correctness": 0},
                    evidence_rows=[],
                    error_attributions=[],
                    grader_confidence=0.9,
                    confidence=1,
                    manual_review_reason=None,
                    feedback_md="Not yet.",
                    repair_suggestions=[],
                ),
            ),
            clock=FrozenClock(NOW),
        )

    problems, _minutes = cold_success_metrics(repository)

    # The mean is 1.0 — flattering — and would stay 1.0 no matter how many
    # problems the censored learning object burned.
    assert problems.value == 1.0
    assert problems.denominator == 1
    # ...which is only honest because the censoring is published next to it.
    assert problems.detail["censored_learning_objects"] == 1
    assert problems.detail["censored_problems_served"] == 4
    assert problems.detail["cold_success_share"] == 0.5
    assert "1 learning object(s) censored" in problems.note


def test_an_unrecorded_latency_never_counts_as_zero_minutes(tmp_path):
    """Standing constraint 6: a NULL latency is unmeasured, not instantaneous."""

    vault, repository, _paths = _vault(tmp_path)
    _attempt(vault, repository, "att_1", correctness_points=0, latency_seconds=None)
    _attempt(vault, repository, "att_2", correctness_points=4, latency_seconds=90)

    problems, minutes = cold_success_metrics(repository)

    assert problems.availability == "available"
    assert problems.value == 2.0
    # The trajectory is excluded outright rather than summed over its recorded
    # subset: 1.5 minutes would understate the learner's real time.
    assert minutes.availability == "unmeasured"
    assert minutes.value is None
    assert minutes.detail["trajectories_missing_latency"] == 1
    assert minutes.detail["trajectories_with_complete_latency"] == 0


def test_self_reports_are_not_problems_served(tmp_path):
    vault, repository, _paths = _vault(tmp_path)
    _attempt(
        vault,
        repository,
        "att_self",
        correctness_points=4,
        attempt_type="self_report",
        latency_seconds=5,
    )
    _attempt(vault, repository, "att_real", correctness_points=4, latency_seconds=15)

    problems, _minutes = cold_success_metrics(repository)
    # One problem, not two: a self-report is the learner telling us something,
    # not a problem the system made them solve.
    assert problems.value == 1.0


# ---------------------------------------------------------------------------
# 4.1 — harmful_write_rate
# ---------------------------------------------------------------------------


def test_harmful_write_rate_counts_a_surfaced_then_withdrawn_belief(tmp_path):
    """The definition this module chose: the harm is in the TELLING.

    B5: "Being told something false about your own mind, with confidence, is
    worse than silence." So the numerator is beliefs the learner SAW and that
    were later withdrawn as false.
    """

    _vault_obj, repository, _paths = _vault(tmp_path)

    _surface_belief(
        repository,
        "mc_transpose",
        "You treat Q and Q transpose as identical.",
        "feedback",
    )
    _surface_belief(
        repository, "mc_ordering", "You order the factors incorrectly.", "review"
    )

    before = harmful_write_rate(repository)
    assert before.availability == "available"
    # Two surfaced beliefs, none withdrawn: an honest 0.0 over a REAL denominator.
    # This is the case the availability arm exists to be distinguishable from.
    assert before.value == 0.0
    assert before.denominator == 2

    record_belief_withdrawal(
        repository,
        belief_id="mc_transpose",
        reason="retired_misdiagnosed",
        clock=FrozenClock(NOW),
    )

    after = harmful_write_rate(repository)
    assert after.availability == "available"
    assert after.numerator == 1
    assert after.denominator == 2
    assert after.value == 0.5
    assert after.detail["harmful_belief_ids"] == ["mc_transpose"]
    assert after.detail["withdrawals_by_reason"]["retired_misdiagnosed"] == 1


def test_zero_over_empty_and_zero_over_two_are_different_findings(tmp_path):
    """The exact confusion the availability arm exists to prevent."""

    _vault_obj, repository, _paths = _vault(tmp_path)

    empty = harmful_write_rate(repository)
    assert empty.availability == "no_data"
    assert empty.value is None
    assert empty.denominator == 0

    _surface_belief(
        repository,
        "mc_transpose",
        "You treat Q and Q transpose as identical.",
        "feedback",
    )
    clean = harmful_write_rate(repository)
    assert clean.availability == "available"
    assert clean.value == 0.0
    assert clean.denominator == 1


def test_supersession_is_not_harm_and_is_reported_separately(tmp_path):
    """A6 defines `superseded` as "a better-supported diagnosis replaced it".

    Counting refinement as harm would penalise exactly the behaviour A6 exists to
    encourage, so it is excluded from the numerator and published on its own.
    """

    _vault_obj, repository, _paths = _vault(tmp_path)
    _surface_belief(repository, "mc_old", "You confuse the factors.", "feedback")
    _belief(repository, "mc_new", "You confuse the factors only under transpose.")
    record_belief_withdrawal(
        repository,
        belief_id="mc_old",
        reason="superseded",
        replacement_belief_id="mc_new",
        clock=FrozenClock(NOW),
    )

    metric = harmful_write_rate(repository)
    assert "superseded" not in HARMFUL_WITHDRAWAL_REASONS
    assert metric.numerator == 0
    assert metric.detail["surfaced_then_superseded"] == 1
    assert metric.detail["withdrawals_by_reason"]["superseded"] == 1


def test_a_belief_never_surfaced_is_not_a_harmful_write(tmp_path):
    """Migration 132's scope guard, carried into the metric.

    Retiring an internal provisional hypothesis nobody saw is housekeeping. If it
    counted here, the metric would fire on the system tidying up after itself.
    """

    _vault_obj, repository, _paths = _vault(tmp_path)
    _surface_belief(
        repository,
        "mc_shown",
        "You treat Q and Q transpose as identical.",
        "feedback",
    )
    _belief(repository, "mc_never_shown", "An internal provisional hypothesis.")
    record_belief_withdrawal(
        repository,
        belief_id="mc_never_shown",
        reason="retired_misdiagnosed",
        clock=FrozenClock(NOW),
    )

    metric = harmful_write_rate(repository)
    assert metric.numerator == 0
    assert metric.denominator == 1
    assert metric.value == 0.0


def test_harmful_write_rate_reports_both_arms(tmp_path):
    """B5's wording picks the surfaced arm; the adjudicated arm still rides along.

    They answer different questions over different samples, and a single number
    would hide whichever was worse.
    """

    vault, repository, _paths = _vault(tmp_path)
    _attempt(
        vault,
        repository,
        "att_wrong",
        misconception_statement="The learner treats Q and Q transpose as identical.",
    )
    append_diagnosis_adjudication(
        repository,
        attempt_id="att_wrong",
        verdict="wrong_anchor",
        adjudicated_anchor={"anchor_kind": "whole_answer", "criterion_id": "correctness"},
        adjudicated_repair_md="Re-derive the factorization.",
    )
    _surface_belief(
        repository,
        "mc_transpose",
        "You treat Q and Q transpose as identical.",
        "feedback",
    )

    metric = harmful_write_rate(repository)
    arms = metric.detail["arms"]
    assert metric.detail["definition"] == "surfaced_withdrawn"
    # Headline == the surfaced arm.
    assert metric.value == arms["surfaced_withdrawn"]["value"] == 0.0
    # ...and they disagree, which is the case the two-arm report exists for.
    assert arms["adjudicated_verdicts"]["value"] == 1.0
    assert metric.detail["arms_agree"] is False


# ---------------------------------------------------------------------------
# 4.3 — cells_cleared_per_question
# ---------------------------------------------------------------------------


def test_cells_cleared_per_question_is_unavailable_before_any_question(tmp_path):
    vault, repository, _paths = _vault(tmp_path)
    metric = cells_cleared_per_question(vault, repository)
    assert metric.availability == "no_data"
    assert metric.value is None
    assert metric.detail["questions_served"] == 0


def test_cells_cleared_per_question_uses_the_contract_cell_vocabulary(tmp_path):
    """Composition test: the cell identity comes from `contract_reachability`.

    The basic fixture is the legacy (pre-blueprint) vault, so it declares no
    contract cell at all — and that is a DIFFERENT finding from "the instruments
    clear nothing", so it gets the `no_data` arm with a note that says which side
    is empty.
    """

    vault, repository, _paths = _vault(tmp_path)
    _attempt(vault, repository, "att_1", correctness_points=4)

    metric = cells_cleared_per_question(vault, repository)
    assert metric.detail["cell_vocabulary"] == "contract_reachability.contract_cells"
    assert metric.detail["contract_cells"] == 0
    assert metric.availability == "no_data"
    assert metric.value is None
    assert "no blueprint recipe declares a contract cell" in metric.note
    assert metric.detail["questions_served"] == 1


_CELL_FACET = "facet_svd_factorization"


def _canonical_vault(tmp_path):
    """An mvp-0.7 vault whose criterion NAMES a (facet, capability) target.

    `facet_capability_evidence` — the per-cell evidence
    `cells_cleared_per_question` reads — is only projected on a canonical-state
    vault with criterion targets. The legacy basic fixture writes no row at all,
    so a coverage test built on it would assert against a table that is empty for
    an unrelated reason.
    """

    from learnloop.services.state_sync import sync_vault_state
    from learnloop.vault.yaml_io import write_yaml

    from tests.helpers import set_algorithm_version, write_facets
    from tests.test_km2_write_path import _item, _rubric

    paths = create_basic_vault(tmp_path / "vault")
    write_yaml(paths.goals_path, {"schema_version": 2, "goals": []})
    write_facets(
        paths,
        [{"id": _CELL_FACET, "kind": "definition", "claim": "SVD factorization."}],
    )
    write_yaml(
        paths.practice_item_path("linear-algebra", "pi_svd_define_001"),
        _item(
            "pi_svd_define_001",
            "lo_svd_definition",
            evidence_facets=[_CELL_FACET],
            rubric=_rubric(
                "correctness",
                [{"facet": _CELL_FACET, "capability": "retrieval", "role": "primary"}],
                correlation_group="grp_a",
            ),
        ),
    )
    set_algorithm_version(paths, "mvp-0.7")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return vault, repository, paths


def test_cells_cleared_per_question_divides_by_questions_served(tmp_path, monkeypatch):
    """The rate itself, over REAL per-cell evidence.

    `contract_cells` is stubbed to a known two-cell contract (one measured, one
    never measured) because blueprint authoring is not what is under test — but
    the coverage side is the live `facet_capability_evidence` projection, so the
    numerator is a genuine uncovered->covered count.

    Stubbing the producer also proves the board reads it: a local
    reimplementation of the cell vocabulary would ignore the patch and see zero
    cells.
    """

    from learnloop.services import contract_reachability, scoreboard as board
    from tests.test_km2_write_path import _attempt as _km2_attempt

    vault, repository, _paths = _canonical_vault(tmp_path)
    _km2_attempt(vault, repository, "pi_svd_define_001", {"correctness": 4}, FrozenClock(NOW))
    _km2_attempt(vault, repository, "pi_svd_define_001", {"correctness": 4}, FrozenClock(NOW))

    # Sanity: the projection really did bank evidence in the measured cell.
    banked = {
        row.capability
        for row in repository.facet_capability_evidence_for_facet(_CELL_FACET)
    }
    assert "retrieval" in banked, banked

    cells = (
        contract_reachability.ContractCell(
            learning_object_id="lo_svd_definition",
            facet_id=_CELL_FACET,
            capability="retrieval",
            component_roles=("all_of",),
            modalities=("short_answer",),
            recipe_refs=("bp:r1",),
        ),
        contract_reachability.ContractCell(
            learning_object_id="lo_svd_definition",
            facet_id=_CELL_FACET,
            capability="coordination",
            component_roles=("integration",),
            modalities=("short_answer",),
            recipe_refs=("bp:r1",),
        ),
    )
    monkeypatch.setattr(
        contract_reachability, "contract_cells", lambda _vault: (cells, 0)
    )

    metric = board.cells_cleared_per_question(vault, repository)
    assert metric.availability == "available"
    assert metric.detail["contract_cells"] == 2
    # `retrieval` accrued mass from the two attempts; nothing observes the facet
    # at `coordination`, which is §5.8.2's unreachable-integration shape.
    assert metric.detail["cells_covered"] == 1
    assert metric.numerator == 1
    assert metric.denominator == 2
    assert metric.value == 0.5


# ---------------------------------------------------------------------------
# 4.3 — questions_to_certification / certification_regret
# ---------------------------------------------------------------------------


def test_certification_metrics_require_an_explicit_replay(tmp_path):
    """Opt-in, and unavailable rather than approximated when not opted into.

    §5.8.1: "Replaying a prefix of the attempts does not produce a prefix of the
    state." There is no cheap faithful answer, so the default arm says so instead
    of substituting something that is not regret.
    """

    vault, repository, _paths = _vault(tmp_path)
    _attempt(vault, repository, "att_1", correctness_points=4)

    report = scoreboard(vault, repository)
    by_name = {metric["name"]: metric for metric in report["metrics"]}
    for name in ("questions_to_certification", "certification_regret"):
        assert by_name[name]["availability"] == "requires_replay"
        assert by_name[name]["value"] is None
        assert "prefix replay" in by_name[name]["note"]
    # The free part is still reported: current certification status is a pure read.
    assert "certified_learning_objects_now" in by_name["certification_regret"]["detail"]


def test_certification_replay_reports_no_data_when_nothing_certifies(tmp_path):
    """The legacy fixture has no blueprint, so nothing can certify.

    The replay runs, finds no certifying prefix, and says `no_data` — not 0
    questions to certification, which would read as instant certification.
    """

    vault, repository, _paths = _vault(tmp_path)
    _attempt(vault, repository, "att_1", correctness_points=4)

    questions, regret = _certification(vault, repository)
    assert questions.availability == "no_data"
    assert questions.value is None
    assert regret.availability == "no_data"
    assert regret.value is None
    assert questions.detail["replay"]["evaluations"] >= 1
    assert questions.detail["replay"]["budget_exhausted"] is False


def test_certification_replay_budget_bounds_the_answer_and_says_so(tmp_path):
    vault, repository, _paths = _vault(tmp_path)
    _attempt(vault, repository, "att_1", correctness_points=4)

    from learnloop.services.scoreboard import certification_prefixes

    prefixes, trace = certification_prefixes(vault, repository, budget=0)
    assert prefixes == []
    assert trace["budget_exhausted"] is True
    assert trace["evaluations"] == 0


def _certification(vault, repository):
    from learnloop.services.scoreboard import certification_efficiency_metrics

    return certification_efficiency_metrics(vault, repository, replay=True)


# ---------------------------------------------------------------------------
# 4.4 — tokens_per_resolved_diagnostic_episode
# ---------------------------------------------------------------------------


def test_tokens_metric_is_unavailable_with_no_resolved_episode(tmp_path):
    vault, repository, _paths = _vault(tmp_path)
    metric = tokens_per_resolved_diagnostic_episode(repository)
    assert metric.availability == "no_data"
    assert metric.value is None


def test_tokens_metric_divides_by_resolved_episodes_only(tmp_path):
    """An abstained episode produced no diagnosis and is not in the denominator.

    Dividing by it would make abstention look cheap, which is the wrong incentive
    on the metric C1's revert criterion is stated in.
    """

    vault, repository, _paths = _vault(tmp_path)
    _attempt(
        vault,
        repository,
        "att_resolved",
        misconception_statement="The learner treats Q and Q transpose as identical.",
        resolution_status="resolved",
    )
    _attempt(vault, repository, "att_abstained", resolution_status="abstained")

    metric = tokens_per_resolved_diagnostic_episode(repository)
    assert metric.detail["diagnostic_episodes"] == 2
    assert metric.detail["resolved_episodes"] == 1
    assert metric.detail["abstained_episodes"] == 1


def test_a_run_reporting_zero_tokens_is_unmetered_not_free(tmp_path):
    """Migration 131's 0 is "unreported or free" — and here it cannot be either.

    A resolved episode whose grading run reports 0/0 is indistinguishable from a
    pre-131 run. Counting it as 0 tokens would report a diagnostic loop that
    costs nothing.
    """

    vault, repository, _paths = _vault(tmp_path)
    result = _attempt(
        vault,
        repository,
        "att_resolved",
        misconception_statement="The learner treats Q and Q transpose as identical.",
        resolution_status="resolved",
    )
    _ = result
    run_id = repository.insert_agent_run(
        {"purpose": "grading", "provider": "codex", "started_at": NOW_ISO}
    )
    repository.complete_agent_run(run_id, status="completed")
    _link_grading_run(repository, "att_resolved", run_id)

    metric = tokens_per_resolved_diagnostic_episode(repository)
    assert metric.availability == "unmeasured"
    assert metric.value is None
    assert metric.detail["episodes_with_unmetered_run"] == 1
    assert metric.detail["episodes_with_metered_run"] == 0


def test_tokens_metric_reports_the_ratio_over_metered_episodes(tmp_path):
    vault, repository, _paths = _vault(tmp_path)
    _attempt(
        vault,
        repository,
        "att_resolved",
        misconception_statement="The learner treats Q and Q transpose as identical.",
        resolution_status="resolved",
    )
    from learnloop.token_usage import TokenUsage

    run_id = repository.insert_agent_run(
        {"purpose": "grading", "provider": "codex", "started_at": NOW_ISO}
    )
    repository.complete_agent_run(
        run_id, status="completed", usage=TokenUsage(input_tokens=900, output_tokens=100)
    )
    _link_grading_run(repository, "att_resolved", run_id)

    metric = tokens_per_resolved_diagnostic_episode(repository)
    assert metric.availability == "available"
    assert metric.numerator == 1000
    assert metric.denominator == 1
    assert metric.value == 1000.0
    assert metric.detail["input_tokens"] == 900
    assert metric.detail["output_tokens"] == 100


def _link_grading_run(repository: Repository, attempt_id: str, run_id: str) -> None:
    """Point the attempt's feedback metadata at a grading run.

    Through the real writer, not a raw UPDATE: `apply_attempt` does not always
    create the row (the fixture vault has one for half its attempts), so an
    UPDATE would silently affect zero rows and the test would pass against a
    metric that never saw a run.

    `diagnosis_snapshot` reads the grader identity through exactly this join, so
    the token metric uses it too rather than inventing a second one.
    """

    repository.upsert_attempt_feedback_metadata(
        attempt_id=attempt_id,
        grading_source="codex",
        agent_run_id=run_id,
        clock=FrozenClock(NOW),
    )
    assert (repository.fetch_attempt_feedback_metadata(attempt_id) or {}).get(
        "agent_run_id"
    ) == run_id


# ---------------------------------------------------------------------------
# 4.4 — probe_action_change_rate
# ---------------------------------------------------------------------------


def test_probe_action_change_rate_says_no_probes_administered(tmp_path):
    """Not "probes never change anything", which is what a 0.0 would assert.

    Migration 130's writer only became reachable when Stage 2.1 landed a
    probe-candidate producer, so current vaults have no rows at all.
    """

    _vault_obj, repository, _paths = _vault(tmp_path)
    metric = probe_action_change_rate(repository)

    assert metric.availability == "no_data"
    assert metric.value is None
    assert metric.detail["probes_administered"] == 0
    assert "no probe has been administered yet" in metric.note


def test_probe_action_change_rate_counts_resolving_observations(tmp_path, monkeypatch):
    """Numerator = admitted AND resolved_factor; denominator = administered.

    Migration 130's CHECK already forbids an unadmitted row resolving anything,
    so the two clauses are belt and braces — but a non-discriminating outcome
    (`matched_multiple`: "the instrument did not discriminate") must not count.
    """

    from learnloop.services import scoreboard as board

    _vault_obj, repository, _paths = _vault(tmp_path)
    observations = [
        {"outcome": "matched_single", "admitted": True, "resolved_factor": True},
        {"outcome": "matched_multiple", "admitted": True, "resolved_factor": False},
        {"outcome": "cohort_mismatch", "admitted": False, "resolved_factor": False},
    ]
    monkeypatch.setattr(
        repository, "causal_discriminating_observations", lambda **_: observations
    )
    monkeypatch.setattr(
        repository, "causal_probe_decision_receipts", lambda **_: []
    )

    metric = board.probe_action_change_rate(repository)
    assert metric.availability == "available"
    assert metric.numerator == 1
    assert metric.denominator == 3
    assert metric.value == pytest.approx(1 / 3)
    assert metric.detail["observations_by_outcome"]["matched_single"] == 1


# ---------------------------------------------------------------------------
# 4.4 — planted_vs_adjudicated_agreement (scaffold)
# ---------------------------------------------------------------------------


def test_planted_side_absent_reports_no_producer_not_zero_overlap(tmp_path):
    """A missing producer is a different fact from an empty producer.

    `planted_ground_truth` returns None rather than {} precisely so this arm is
    `no_producer` and not "0 agreements over 0 overlapping attempts".
    """

    vault, repository, _paths = _vault(tmp_path)
    _attempt(
        vault,
        repository,
        "att_1",
        misconception_statement="The learner treats Q and Q transpose as identical.",
    )
    append_diagnosis_adjudication(repository, attempt_id="att_1", verdict="correct")

    metric = planted_vs_adjudicated_agreement(repository)
    assert metric.availability == "no_producer"
    assert metric.value is None
    assert metric.detail["planted_labels"] is None
    # The adjudicated side is live and counted, so Stage 7 can see what it joins to.
    assert metric.detail["adjudicated_labels"] == 1


def test_agreement_is_computed_once_a_planted_side_exists(tmp_path, monkeypatch):
    """The scaffold is a real producer, not a stub that raises.

    Stage 7 only has to fill `planted_ground_truth`; the comparison already works.
    """

    from learnloop.services import scoreboard as board
    from learnloop.services.diagnosis_adjudication import (
        adjudicated_ground_truth,
        anchor_key,
    )

    vault, repository, _paths = _vault(tmp_path)
    _attempt(
        vault,
        repository,
        "att_agree",
        misconception_statement="The learner treats Q and Q transpose as identical.",
    )
    append_diagnosis_adjudication(repository, attempt_id="att_agree", verdict="correct")
    truth = adjudicated_ground_truth(repository)["att_agree"]

    monkeypatch.setattr(
        board,
        "planted_ground_truth",
        lambda _repository, **_kw: {
            "att_agree": {
                "should_abstain": truth["should_abstain"],
                "anchor_key": truth["anchor_key"],
            },
            "att_disagree": {
                "should_abstain": True,
                "anchor_key": anchor_key(None),
            },
        },
    )

    metric = board.planted_vs_adjudicated_agreement(repository)
    assert metric.availability == "available"
    # Only `att_agree` is in the overlap; `att_disagree` has no adjudication.
    assert metric.denominator == 1
    assert metric.numerator == 1
    assert metric.value == 1.0
    assert metric.detail["planted_labels"] == 2


# ---------------------------------------------------------------------------
# false_certification_rate seam
# ---------------------------------------------------------------------------


def test_false_certification_rate_is_composed_from_item_4_2(tmp_path):
    """Composed from `certification_cold_probe`, and never 0.0 over zero probes.

    Meas §5.7 calls this "the only number that licenses any speed claim", so the
    board must not grow a second definition of it — and on an unprobed vault it
    must refuse rather than reporting the strongest possible claim by accident.
    """

    from learnloop.services.certification_cold_probe import false_certification_rate
    from learnloop.services.scoreboard import (
        false_certification_rate as composed,
    )

    vault, repository, _paths = _vault(tmp_path)

    upstream = false_certification_rate(repository)
    metric = composed(vault, repository)

    assert metric.detail["composed_from"] == (
        "learnloop.services.certification_cold_probe.false_certification_rate"
    )
    assert metric.numerator == upstream.numerator
    assert metric.denominator == upstream.denominator
    # Nothing certified, nothing probed: unavailable, with the producer's own
    # reason carried through rather than paraphrased.
    assert metric.availability == "no_data"
    assert metric.value is None
    assert upstream.rate is None


def test_false_certification_seam_composes_a_producer_when_present(tmp_path, monkeypatch):
    """The seam is wiring, not a permanent refusal."""

    from learnloop.services import scoreboard as board

    vault, repository, _paths = _vault(tmp_path)
    monkeypatch.setattr(
        board,
        "_resolve_false_certification_producer",
        lambda: (
            lambda _repository, **_kw: {
                "numerator": 1,
                "denominator": 4,
                "denominator_definition": "certificates with a scored delayed cold probe",
                "note": "one certificate failed its delayed cold probe",
            }
        ),
    )
    metric = board.false_certification_rate(vault, repository)
    assert metric.name == "false_certification_rate"
    assert metric.availability == "available"
    assert metric.value == 0.25
    assert metric.denominator_label == (
        "certificates with a scored delayed cold probe"
    )


# ---------------------------------------------------------------------------
# Composition, proved by moving the upstream producer
# ---------------------------------------------------------------------------


def test_adjudication_metrics_are_composed_not_recomputed(tmp_path, monkeypatch):
    """The four A4-owned metrics must come from the A4 store's own scoreboard.

    Monkeypatching `diagnosis_adjudication_scoreboard` moves the board. A silent
    reimplementation would keep reporting the real verdicts and fail here — which
    is the only way to test "did not reimplement".
    """

    from learnloop.services import diagnosis_adjudication, scoreboard as board

    vault, repository, _paths = _vault(tmp_path)
    calls: list[dict] = []

    def fake(repo, *, group_by="version", attempt_ids=None):
        calls.append({"group_by": group_by})
        return {
            "store_version": "diagnosis_adjudication_v1",
            "group_by": group_by,
            "overall": {
                "records": 10,
                "by_verdict": {
                    "correct": 3,
                    "wrong_anchor": 2,
                    "wrong_repair": 1,
                    "should_have_abstained": 1,
                    "correctly_abstained": 2,
                    "should_not_have_abstained": 1,
                },
                "by_queue_reason": {},
                "anchor_scored": 6,
                "anchor_correct": 4,
                "repair_id_scored": 0,
                "repair_id_match": 0,
                "abstention_confusion": {"tp": 2, "fp": 1, "fn": 1, "tn": 6},
                "first_divergence_anchor_accuracy": 4 / 6,
                "repair_class_match_rate": 3 / 6,
                "repair_class_id_match_rate": None,
                "abstention_precision": 2 / 3,
                "abstention_recall": 2 / 3,
                "abstention_cases_present": True,
            },
            "groups": [{"grading_prompt_version": "v9", "grader_model": "m"}],
        }

    monkeypatch.setattr(
        diagnosis_adjudication, "diagnosis_adjudication_scoreboard", fake
    )
    report = board.scoreboard(vault, repository)
    by_name = {metric["name"]: metric for metric in report["metrics"]}

    assert by_name["first_divergence_anchor_accuracy"]["value"] == round(4 / 6, 6)
    assert by_name["repair_class_match_rate"]["value"] == round(3 / 6, 6)
    assert by_name["abstention_precision"]["value"] == round(2 / 3, 6)
    assert by_name["abstention_recall"]["value"] == round(2 / 3, 6)
    # B5 requires the grading-prompt-version x grader-model slice, so the board
    # must ask for it rather than pooling.
    assert {"group_by": "version"} in calls
    assert by_name["first_divergence_anchor_accuracy"]["detail"]["groups"] == [
        {"grading_prompt_version": "v9", "grader_model": "m"}
    ]
    assert (
        by_name["abstention_recall"]["detail"]["composed_from"]
        == "diagnosis_adjudication.diagnosis_adjudication_scoreboard"
    )


def test_adjudication_metrics_track_the_real_store(tmp_path):
    """...and with nothing patched, they equal what the real store reports."""

    from learnloop.services.diagnosis_adjudication import (
        diagnosis_adjudication_scoreboard,
    )

    vault, repository, _paths = _vault(tmp_path)
    for index in range(2):
        _attempt(
            vault,
            repository,
            f"att_{index}",
            misconception_statement="The learner treats Q and Q transpose as identical.",
        )
    append_diagnosis_adjudication(repository, attempt_id="att_0", verdict="correct")
    append_diagnosis_adjudication(
        repository,
        attempt_id="att_1",
        verdict="wrong_anchor",
        adjudicated_anchor={"anchor_kind": "whole_answer", "criterion_id": "correctness"},
        adjudicated_repair_md="Re-derive.",
    )

    truth = diagnosis_adjudication_scoreboard(repository, group_by="version")["overall"]
    by_name = {
        metric["name"]: metric
        for metric in scoreboard(vault, repository)["metrics"]
    }
    assert by_name["first_divergence_anchor_accuracy"]["value"] == round(
        truth["first_divergence_anchor_accuracy"], 6
    )
    assert by_name["repair_class_match_rate"]["value"] == round(
        truth["repair_class_match_rate"], 6
    )


def test_measurement_rank_is_composed_from_identifiability(tmp_path, monkeypatch):
    from learnloop.services import identifiability, scoreboard as board

    vault, repository, _paths = _vault(tmp_path)
    _ = repository
    real = identifiability.measurement_rank
    seen: list[object] = []

    def fake(view):
        seen.append(view)
        return identifiability.MeasurementRank(
            facets_declared=39,
            independent_dimensions=14,
            deficit=25,
            deficit_from_unobserved=20,
            deficit_from_collapse=5,
        )

    monkeypatch.setattr(identifiability, "measurement_rank", fake)
    metric = board.measurement_rank_metric(vault)
    assert seen, "the board did not call identifiability.measurement_rank"
    # §5.8.2's published figure: 14 of 39 = 0.36.
    assert metric.numerator == 14
    assert metric.denominator == 39
    assert metric.value == round(14 / 39, 6)
    assert metric.detail["composed_from"] == "identifiability.measurement_rank"
    monkeypatch.setattr(identifiability, "measurement_rank", real)


def test_measurement_rank_is_unavailable_with_no_declared_facet(tmp_path, monkeypatch):
    from learnloop.services import identifiability, scoreboard as board

    vault, _repository, _paths = _vault(tmp_path)
    monkeypatch.setattr(
        identifiability,
        "measurement_rank",
        lambda _view: identifiability.MeasurementRank(
            facets_declared=0,
            independent_dimensions=0,
            deficit=0,
            deficit_from_unobserved=0,
            deficit_from_collapse=0,
        ),
    )
    metric = board.measurement_rank_metric(vault)
    assert metric.availability == "no_data"
    assert metric.value is None


def test_the_board_composes_rather_than_declaring_its_own_producers(tmp_path):
    """Guard on the composition list itself.

    The four A4 metrics and `measurement_rank` must NOT have a local producer
    function on this module — if one appeared, the composition would be dead code
    and the board would drift from the store.
    """

    from learnloop.services import scoreboard as board

    for name in (
        "first_divergence_anchor_accuracy",
        "repair_class_match_rate",
        "abstention_precision",
        "abstention_recall",
    ):
        assert not hasattr(board, name), (
            f"{name} has a local producer; it must be composed from "
            "diagnosis_adjudication"
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_cli_prints_the_board_in_b5_order_with_unavailable_arms_visible(tmp_path):
    _vault_obj, _repository, paths = _vault(tmp_path)
    result = CliRunner().invoke(app, ["scoreboard", "--vault", str(paths.root)])

    assert result.exit_code == 0, result.output
    lines = [line for line in result.output.splitlines() if line.strip()]
    positions = [
        index
        for index, line in enumerate(lines)
        for name in [line.strip().split(":")[0]]
        if name in B5_ORDER
    ]
    printed = [lines[index].strip().split(":")[0] for index in positions]
    assert printed == list(B5_ORDER)
    # Every arm on an empty vault is unavailable and says so in words.
    assert result.output.count("unavailable") == len(B5_ORDER) - len(
        _ACTIVITY_FREE_METRICS
    )
    # The load-bearing rendering check: no metric's VALUE field may read as a
    # number when the metric has no data. Checked positionally rather than by
    # substring, because a numerator of 0 legitimately appears in the bracket
    # that names the empty denominator.
    for index in positions:
        name, _, rest = lines[index].strip().partition(": ")
        if name in _ACTIVITY_FREE_METRICS:
            continue
        value_field = rest.split(" [")[0]
        assert value_field.startswith("unavailable ("), (
            f"{name} rendered its value as {value_field!r}; an unproduced metric "
            "must never read as a number"
        )
    assert f"{len(_ACTIVITY_FREE_METRICS)}/{len(B5_ORDER)} metrics available" in result.output


def test_cli_json_carries_denominators_and_the_ordering_rationale(tmp_path):
    _vault_obj, _repository, paths = _vault(tmp_path)
    result = CliRunner().invoke(
        app, ["scoreboard", "--vault", str(paths.root), "--json"]
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["order"] == list(B5_ORDER)
    assert "problems_to_cold_success" in payload["order_rationale"]
    for metric in payload["metrics"]:
        assert "denominator" in metric
        assert "denominator_label" in metric
        assert metric["availability"] in AVAILABILITY
