from __future__ import annotations

import shutil

import pytest

from learnloop.clock import FrozenClock
from learnloop.codex.schemas import GradingProposal, TeachBackQuestion
from learnloop.db.connection import connect
from learnloop.db.migrate import apply_migrations, discover_migrations
from learnloop.db.repositories import MasteryState, Repository
from learnloop.services.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.services.recall_coverage import derive_facet_outcomes
from learnloop.services.replay import rebuild_derived_state
from learnloop.services.scheduler import SchedulerSession, build_due_queue
from learnloop.services.teach_back import (
    TeachBackState,
    asked_criterion_ids,
    begin_teach_back,
    ensure_teach_back_item,
    finish_teach_back,
    next_question,
    plan_followups,
    record_answer,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.models import Rubric
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import ALGORITHM_VERSION, NOW, NOW_ISO, create_basic_vault, seed_due_item

LO_ID = "lo_svd_definition"
TEACH_ITEM_ID = "pi_svd_teach_001"


class FakeTeachBackClient:
    """AI double: canned naive-student questions + full-points grading.

    ``points_by_criterion`` overrides awarded points per criterion; anything
    not listed gets full points. The grader only sees (and only grades) the
    restricted rubric in the grading context, like the real provider.
    """

    provider_name = "fake_teach_back"
    provider_type = "fake"
    model = "fake-model"

    def __init__(self, points_by_criterion: dict[str, float] | None = None):
        self.points_by_criterion = points_by_criterion or {}
        self.question_contexts = []
        self.grading_contexts = []

    def run_teach_back_question(self, context) -> TeachBackQuestion:
        self.question_contexts.append(context)
        return TeachBackQuestion(
            question_md=f"Wait, I'm confused about {context.criterion_id} — can you explain?"
        )

    def run_grading_proposal(self, context) -> GradingProposal:
        self.grading_contexts.append(context)
        criteria = context.rubric["criteria"]
        evidence = []
        total = 0.0
        for criterion in criteria:
            awarded = self.points_by_criterion.get(criterion["id"], float(criterion["points"]))
            total += awarded
            evidence.append(
                {
                    "criterion_id": criterion["id"],
                    "points_awarded": awarded,
                    "evidence": f"Transcript covers {criterion['id']}.",
                }
            )
        rubric_score = max(0, min(4, int(round(total))))
        return GradingProposal.model_validate(
            {
                "attempt_id": context.attempt_id,
                "practice_item_id": context.practice_item_id,
                "rubric_score": rubric_score,
                "criterion_evidence": evidence,
                "fatal_errors": [],
                "error_attributions": [],
                "grader_confidence": 0.9,
            }
        )


def _teach_item_payload(item_id: str = TEACH_ITEM_ID) -> dict:
    return {
        "id": item_id,
        "learning_object_id": LO_ID,
        "subjects": None,
        "practice_mode": "teach_back",
        "attempt_types_allowed": ["teach_back"],
        "evidence_facets": ["definition", "geometry", "uniqueness"],
        "evidence_weights": {"definition": 1.0, "geometry": 1.0, "uniqueness": 1.0},
        "criterion_facet_weights": {
            "core_definition": {"definition": 1.0},
            "core_geometry": {"geometry": 1.0},
            "core_uniqueness": {"uniqueness": 1.0},
            "transfer_rank_deficient": {"definition": 1.0},
            "transfer_rotation": {"geometry": 1.0},
        },
        "prompt": "Teach the singular value decomposition to a curious student.",
        "expected_answer": "A full explanation of SVD: definition, geometry, uniqueness.",
        "grading_rubric": {
            "max_points": 4,
            "criteria": [
                {"id": "core_definition", "points": 1.0, "tier": "core", "description": "States what U, Sigma, V are."},
                {"id": "core_geometry", "points": 1.0, "tier": "core", "description": "Explains the rotate-scale-rotate geometry."},
                {"id": "core_uniqueness", "points": 1.0, "tier": "core", "description": "Explains what is and is not unique."},
                {"id": "transfer_rank_deficient", "points": 0.5, "tier": "transfer", "description": "What happens for a rank-deficient matrix?"},
                {"id": "transfer_rotation", "points": 0.5, "tier": "transfer", "description": "What does the SVD of a pure rotation look like?"},
            ],
            "fatal_errors": [],
        },
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }


def _setup(tmp_path, *, extra_items: list[dict] | None = None):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    clock = FrozenClock(NOW)
    upsert_practice_item(vault_root, _teach_item_payload(), clock=clock)
    for payload in extra_items or []:
        upsert_practice_item(vault_root, payload, clock=clock)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    return vault_root, vault, repository


def _helper_item_payload(item_id: str, facet: str) -> dict:
    return {
        "id": item_id,
        "learning_object_id": LO_ID,
        "subjects": None,
        "practice_mode": "short_answer",
        "attempt_types_allowed": ["independent_attempt"],
        "evidence_facets": [facet],
        "evidence_weights": {facet: 1.0},
        "prompt": f"Recall {facet}.",
        "expected_answer": f"About {facet}.",
        "grading_rubric": {
            "max_points": 4,
            "criteria": [{"id": "correct", "points": 4, "description": "Correct."}],
            "fatal_errors": [],
        },
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }


def _make_facet_solid(vault, repository, item_id: str) -> str:
    """Record one clean full-score attempt so the item's facet reads solid."""

    result = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id=item_id, learner_answer_md="a correct answer"),
        SelfGradeInput(criterion_points={"correct": 4}, confidence=5),
        clock=FrozenClock(NOW),
    )
    return result.attempt_id


def _mark_facet_uncertain(
    repository, facet_id: str, *, opened_by_attempt_id: str, uncertainty: float = 0.9
) -> None:
    repository.upsert_facet_uncertainty_state(
        {
            "learning_object_id": LO_ID,
            "facet_id": facet_id,
            "hypothesis_marginal": {f"facet_solid:{facet_id}": 0.4, f"facet_absent:{facet_id}": 0.6},
            "uncertainty": uncertainty,
            "status": "open",
            "opened_by_attempt_id": opened_by_attempt_id,
            "opened_reason": "low_facet_outcome",
            "last_evidence_at": NOW_ISO,
            "algorithm_version": ALGORITHM_VERSION,
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        }
    )


def _run_conversation(vault, repository, item, client, *, answers, clock=None):
    state = begin_teach_back(
        vault,
        repository,
        item,
        opening_md="SVD factors any matrix into rotate, scale, rotate.",
        clock=clock,
    )
    for answer in answers:
        state, question = next_question(vault, state, client)
        assert question is not None
        record_answer(state, answer)
    return state


# ── follow-up planning ────────────────────────────────────────────────────────


def test_plan_orders_uncertain_core_first_then_escalates(tmp_path):
    _root, vault, repository = _setup(
        tmp_path, extra_items=[_helper_item_payload("pi_helper_def", "definition")]
    )
    clock = FrozenClock(NOW)
    attempt_id = _make_facet_solid(vault, repository, "pi_helper_def")  # definition -> solid
    _mark_facet_uncertain(repository, "geometry", opened_by_attempt_id=attempt_id)  # geometry -> uncertain
    # uniqueness stays unexamined.

    plan = plan_followups(vault, repository, vault.practice_items[TEACH_ITEM_ID], clock=clock)

    assert [entry["criterion_id"] for entry in plan] == [
        "core_geometry",  # uncertain facet first
        "core_uniqueness",  # unexamined next
        "transfer_rotation",  # solid 'definition' core skipped: escalate to transfer on the most uncertain facet
        "transfer_rank_deficient",
    ]
    assert [entry["tier"] for entry in plan] == ["core", "core", "transfer", "transfer"]
    assert plan[0]["facet_targets"] == ["geometry"]


def test_plan_escalates_to_transfer_when_everything_is_solid(tmp_path):
    _root, vault, repository = _setup(
        tmp_path,
        extra_items=[
            _helper_item_payload("pi_helper_def", "definition"),
            _helper_item_payload("pi_helper_geo", "geometry"),
            _helper_item_payload("pi_helper_uni", "uniqueness"),
        ],
    )
    clock = FrozenClock(NOW)
    for item_id in ("pi_helper_def", "pi_helper_geo", "pi_helper_uni"):
        _make_facet_solid(vault, repository, item_id)

    plan = plan_followups(vault, repository, vault.practice_items[TEACH_ITEM_ID], clock=clock)

    # Nothing uncertain remains: transfer-tier stress tests come first.
    assert [entry["tier"] for entry in plan][:2] == ["transfer", "transfer"]
    assert {entry["criterion_id"] for entry in plan[:2]} == {
        "transfer_rank_deficient",
        "transfer_rotation",
    }
    # Leftover slot falls back to a (solid) core criterion.
    assert plan[2]["tier"] == "core"
    assert len(plan) == vault.config.teach_back.max_followups


def test_plan_is_deterministic_and_capped(tmp_path):
    _root, vault, repository = _setup(tmp_path)
    clock = FrozenClock(NOW)
    item = vault.practice_items[TEACH_ITEM_ID]
    first = plan_followups(vault, repository, item, clock=clock)
    second = plan_followups(vault, repository, item, clock=clock)
    assert first == second
    assert len(first) == vault.config.teach_back.max_followups == 4


def test_plan_reserves_final_slot_for_transfer_when_core_would_crowd_it_out(tmp_path):
    _root, vault, repository = _setup(
        tmp_path, extra_items=[_helper_item_payload("pi_helper_def", "definition")]
    )
    clock = FrozenClock(NOW)
    attempt_id = _make_facet_solid(vault, repository, "pi_helper_def")  # definition -> solid
    _mark_facet_uncertain(repository, "geometry", opened_by_attempt_id=attempt_id)
    # Two slots, two uncertain-core criteria (geometry, uniqueness): without
    # the reserved slot the plan would be all core.
    config = vault.config.model_copy(deep=True)
    config.teach_back.max_followups = 2

    plan = plan_followups(
        vault, repository, vault.practice_items[TEACH_ITEM_ID], config=config, clock=clock
    )

    # The last slot went to the transfer criterion targeting the most SOLID
    # facet (definition) — clean attribution — not to core_uniqueness.
    assert [entry["criterion_id"] for entry in plan] == [
        "core_geometry",
        "transfer_rank_deficient",
    ]
    assert [entry["tier"] for entry in plan] == ["core", "transfer"]


def test_ensure_teach_back_item_mints_transfer_criterion(tmp_path):
    # Vault WITHOUT a teach_back card so the mint path runs.
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)

    item_id, created = ensure_teach_back_item(vault_root, vault, repository, LO_ID, clock=clock)
    assert created is True

    reloaded = load_vault(vault_root)
    minted = reloaded.practice_items[item_id]
    rubric = minted.grading_rubric
    tiers = [criterion.tier for criterion in rubric.criteria]
    assert tiers.count("transfer") == 1
    transfer = next(c for c in rubric.criteria if c.tier == "transfer")
    assert transfer.id == "criterion_teach_transfer"
    # Points stay within the rubric scale despite the extra criterion.
    assert sum(criterion.points for criterion in rubric.criteria) <= rubric.max_points
    # The transfer criterion is facet-mapped, so the guaranteed transfer slot
    # has real facet targets, and the plan always ends on it.
    assert minted.criterion_facet_weights["criterion_teach_transfer"]
    plan = plan_followups(reloaded, repository, minted, clock=clock)
    assert plan[-1]["criterion_id"] == "criterion_teach_transfer"
    assert plan[-1]["tier"] == "transfer"


# ── conversation state ────────────────────────────────────────────────────────


def test_state_json_round_trip(tmp_path):
    _root, vault, repository = _setup(tmp_path)
    clock = FrozenClock(NOW)
    client = FakeTeachBackClient()
    state = _run_conversation(
        vault, repository, vault.practice_items[TEACH_ITEM_ID], client, answers=["Because U is orthogonal."], clock=clock
    )

    restored = TeachBackState.from_json(state.to_json())

    assert restored.to_dict() == state.to_dict()
    assert restored.practice_item_id == TEACH_ITEM_ID
    assert restored.asked_count == 1
    assert [turn.role for turn in restored.turns] == ["learner", "ai", "learner"]
    assert restored.turns[1].criterion_id == state.planned[0]["criterion_id"]
    assert restored.planned == state.planned


def test_next_question_conditions_on_transcript_and_exhausts(tmp_path):
    _root, vault, repository = _setup(tmp_path)
    clock = FrozenClock(NOW)
    client = FakeTeachBackClient()
    item = vault.practice_items[TEACH_ITEM_ID]
    state = _run_conversation(
        vault,
        repository,
        item,
        client,
        answers=["answer one", "answer two", "answer three", "answer four"],
        clock=clock,
    )

    # All four planned questions were generated against the planned criteria.
    assert [context.criterion_id for context in client.question_contexts] == [
        entry["criterion_id"] for entry in state.planned
    ]
    # Each context carries the transcript so far (opening + prior turns).
    assert len(client.question_contexts[0].transcript) == 1
    assert len(client.question_contexts[3].transcript) == 7
    assert client.question_contexts[0].transcript[0]["role"] == "learner"
    # The plan is exhausted afterwards.
    state, question = next_question(vault, state, client)
    assert question is None
    assert state.asked_count == 4


# ── grading ───────────────────────────────────────────────────────────────────


def test_finish_partial_grading_only_asked_criteria_produce_evidence(tmp_path):
    _root, vault, repository = _setup(tmp_path)
    clock = FrozenClock(NOW)
    client = FakeTeachBackClient()
    item = vault.practice_items[TEACH_ITEM_ID]
    # Fresh vault: plan = core_definition, core_geometry, core_uniqueness,
    # transfer_rank_deficient. Ask and answer only the first two (provider
    # "fails" before question 3).
    state = _run_conversation(vault, repository, item, client, answers=["ans 1", "ans 2"], clock=clock)
    assert asked_criterion_ids(state) == ["core_definition", "core_geometry"]

    result = finish_teach_back(vault, repository, state, client, clock=clock)

    # The grader only saw the asked criteria.
    graded_rubric_ids = [c["id"] for c in client.grading_contexts[0].rubric["criteria"]]
    assert graded_rubric_ids == ["core_definition", "core_geometry"]
    # One attempt, teach_back type, no hints.
    attempts = repository.list_attempts_by_learning_object(LO_ID)
    assert len(attempts) == 1
    attempt = attempts[0]
    assert attempt["attempt_type"] == "teach_back"
    assert attempt["hints_used"] == 0
    assert attempt["id"] == result.attempt.attempt_id
    # Full marks on asked criteria: score normalized over asked points, not
    # penalized for the unasked criterion (2.0/2.0 asked -> 4/4, not 2/4).
    assert result.attempt.rubric_score == 4
    assert result.attempt.correctness == pytest.approx(1.0)
    # Transcript is the graded answer.
    assert "Opening explanation" in attempt["learner_answer_md"]
    assert "Follow-up 2" in attempt["learner_answer_md"]
    # Facet evidence exists only for asked facets; the unasked facet got none.
    states = {
        state.facet_id: state
        for state in repository.facet_recall_states(LO_ID)
        if state.practice_item_id is None
    }
    assert states["definition"].independent_evidence_mass > 0
    assert states["geometry"].independent_evidence_mass > 0
    assert "uniqueness" not in states
    # Evidence rows persist only asked criteria (replay input).
    evidence = repository.fetch_grading_evidence(result.attempt.attempt_id)
    assert sorted(row.criterion_id for row in evidence) == ["core_definition", "core_geometry"]


def test_finish_with_no_answered_followup_grades_opening_against_core(tmp_path):
    _root, vault, repository = _setup(tmp_path)
    clock = FrozenClock(NOW)
    client = FakeTeachBackClient()
    item = vault.practice_items[TEACH_ITEM_ID]
    state = begin_teach_back(vault, repository, item, opening_md="SVD is rotate-scale-rotate.", clock=clock)

    result = finish_teach_back(vault, repository, state, client, clock=clock)

    assert result.asked_criterion_ids == ["core_definition", "core_geometry", "core_uniqueness"]
    assert result.attempt.rubric_score == 4
    attempts = repository.list_attempts_by_learning_object(LO_ID)
    assert len(attempts) == 1
    assert attempts[0]["attempt_type"] == "teach_back"


def test_low_scoring_answers_are_just_low_scores(tmp_path):
    _root, vault, repository = _setup(tmp_path)
    clock = FrozenClock(NOW)
    # "I don't know" answers: the grader awards zero on those criteria; there
    # is no dont_know fork.
    client = FakeTeachBackClient(points_by_criterion={"core_definition": 0.0, "core_geometry": 0.0, "core_uniqueness": 0.0})
    item = vault.practice_items[TEACH_ITEM_ID]
    state = _run_conversation(
        vault, repository, item, client, answers=["I don't know", "no idea", "I don't know"], clock=clock
    )

    result = finish_teach_back(vault, repository, state, client, clock=clock)

    assert result.attempt.rubric_score == 0
    attempt = repository.list_attempts_by_learning_object(LO_ID)[0]
    assert attempt["attempt_type"] == "teach_back"
    assert attempt["correctness"] == pytest.approx(0.0)


def test_transfer_tier_evidence_mass_is_discounted_symmetrically(tmp_path):
    two_facet_item = {
        "id": "pi_svd_teach_002",
        "learning_object_id": LO_ID,
        "subjects": None,
        "practice_mode": "teach_back",
        "attempt_types_allowed": ["teach_back"],
        "evidence_facets": ["definition", "geometry"],
        "evidence_weights": {"definition": 1.0, "geometry": 1.0},
        "criterion_facet_weights": {
            "core_definition": {"definition": 1.0},
            "transfer_rotation": {"geometry": 1.0},
        },
        "prompt": "Teach SVD.",
        "expected_answer": "Explanation.",
        "grading_rubric": {
            "max_points": 4,
            "criteria": [
                {"id": "core_definition", "points": 2.0, "tier": "core", "description": "Defines the factorization."},
                {"id": "transfer_rotation", "points": 2.0, "tier": "transfer", "description": "SVD of a rotation."},
            ],
            "fatal_errors": [],
        },
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }
    for award_transfer in (2.0, 0.0):  # success and failure discounted equally
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory(dir=tmp_path) as scratch:
            _root, vault, repository = _setup(Path(scratch), extra_items=[two_facet_item])
            clock = FrozenClock(NOW)
            client = FakeTeachBackClient(points_by_criterion={"transfer_rotation": award_transfer})
            item = vault.practice_items["pi_svd_teach_002"]
            state = _run_conversation(vault, repository, item, client, answers=["a", "b"], clock=clock)
            finish_teach_back(vault, repository, state, client, clock=clock)

            states = {
                state.facet_id: state
                for state in repository.facet_recall_states(LO_ID)
                if state.practice_item_id is None
            }
            core_mass = states["definition"].independent_evidence_mass
            transfer_mass = states["geometry"].independent_evidence_mass
            multiplier = vault.config.teach_back.transfer_evidence_multiplier
            assert core_mass > 0
            # Same facet weight, same criterion points: only the tier differs.
            assert transfer_mass == pytest.approx(multiplier * core_mass)


def test_finish_and_rebuild_replay_reproduce_derived_state(tmp_path):
    _root, vault, repository = _setup(tmp_path)
    clock = FrozenClock(NOW)
    client = FakeTeachBackClient(points_by_criterion={"core_geometry": 0.25})
    item = vault.practice_items[TEACH_ITEM_ID]
    state = _run_conversation(vault, repository, item, client, answers=["ans 1", "ans 2"], clock=clock)
    finish_teach_back(vault, repository, state, client, clock=clock)

    def snapshot():
        mastery = repository.mastery_state(LO_ID)
        item_state = repository.practice_item_state(TEACH_ITEM_ID)
        facets = {
            (state.facet_id, state.practice_item_id): (
                state.recall_mean,
                state.recall_alpha,
                state.recall_beta,
                state.independent_evidence_mass,
            )
            for state in repository.facet_recall_states(LO_ID)
        }
        return mastery, item_state, facets

    before = snapshot()
    rebuild_derived_state(vault, repository, learning_object_ids=[LO_ID])
    after = snapshot()

    assert after[0].logit_mean == pytest.approx(before[0].logit_mean)
    assert after[0].logit_variance == pytest.approx(before[0].logit_variance)
    assert after[0].evidence_count == before[0].evidence_count
    assert after[1].due_at == before[1].due_at
    assert after[1].stability == pytest.approx(before[1].stability)
    assert set(after[2]) == set(before[2])
    for key, values in before[2].items():
        for observed, expected in zip(after[2][key], values, strict=True):
            assert observed == pytest.approx(expected)


# ── regrade restricted to the originally graded criteria ─────────────────────


def _regrade_runtime():
    from learnloop.codex.runtime import CodexRuntimeReport

    return CodexRuntimeReport(
        status="ready",
        checkout_path="codex",
        configured_revision="abc",
        actual_revision="abc",
    )


def test_regrade_teach_back_attempt_restricts_to_graded_criteria(tmp_path):
    from learnloop.services.regrade import _regrade_attempt

    _root, vault, repository = _setup(tmp_path)
    clock = FrozenClock(NOW)
    client = FakeTeachBackClient()
    item = vault.practice_items[TEACH_ITEM_ID]
    # Asked/answered 2 of the 5 rubric criteria.
    state = _run_conversation(vault, repository, item, client, answers=["ans 1", "ans 2"], clock=clock)
    result = finish_teach_back(vault, repository, state, client, clock=clock)
    attempt_id = result.attempt.attempt_id
    assert result.graded_criterion_ids == ["core_definition", "core_geometry"]

    regrade_client = FakeTeachBackClient(points_by_criterion={"core_geometry": 0.0})
    _regrade_attempt(
        vault,
        repository,
        repository.fetch_practice_attempt(attempt_id),
        runtime=_regrade_runtime(),
        client=regrade_client,
        grading_source="ai",
        clock=clock,
    )

    # The regrade grader only saw the originally graded criteria.
    regrade_rubric_ids = [c["id"] for c in regrade_client.grading_contexts[0].rubric["criteria"]]
    assert regrade_rubric_ids == ["core_definition", "core_geometry"]
    # Score normalization mirrors finish_teach_back: 1.0 of 2.0 asked points
    # projects to 2/4 — not 1/5-of-full-rubric, and unasked criteria are not
    # zero-score failures.
    regraded = repository.fetch_practice_attempt(attempt_id)
    assert regraded["rubric_score"] == 2
    assert regraded["correctness"] == pytest.approx(0.5)
    # Only the graded criteria carry live evidence; the previous teach-back
    # rows are superseded and NO row (live or superseded) exists for unasked
    # criteria.
    current = repository.fetch_grading_evidence(attempt_id)
    assert sorted(row.criterion_id for row in current) == ["core_definition", "core_geometry"]
    assert all(row.superseded_at is None for row in current)
    everything = repository.fetch_grading_evidence(attempt_id, include_superseded=True)
    assert {row.criterion_id for row in everything} == {"core_definition", "core_geometry"}
    assert len(everything) == 4  # 2 original (superseded) + 2 regrade rows

    # Replay after the regrade reproduces the regraded state (convergence).
    def snapshot():
        mastery = repository.mastery_state(LO_ID)
        facets = {
            (state.facet_id, state.practice_item_id): (
                state.recall_mean,
                state.independent_evidence_mass,
            )
            for state in repository.facet_recall_states(LO_ID)
        }
        return mastery.logit_mean, mastery.logit_variance, facets

    before = snapshot()
    rebuild_derived_state(vault, repository, learning_object_ids=[LO_ID])
    after = snapshot()
    assert after[0] == pytest.approx(before[0])
    assert after[1] == pytest.approx(before[1])
    assert set(after[2]) == set(before[2])
    for key, values in before[2].items():
        for observed, expected in zip(after[2][key], values, strict=True):
            assert observed == pytest.approx(expected)


def test_regrade_teach_back_attempt_without_evidence_falls_back_to_core(tmp_path):
    from learnloop.db.connection import connect
    from learnloop.services.regrade import _regrade_attempt

    _root, vault, repository = _setup(tmp_path)
    clock = FrozenClock(NOW)
    client = FakeTeachBackClient()
    item = vault.practice_items[TEACH_ITEM_ID]
    state = _run_conversation(vault, repository, item, client, answers=["ans 1"], clock=clock)
    result = finish_teach_back(vault, repository, state, client, clock=clock)
    attempt_id = result.attempt.attempt_id
    with connect(repository.sqlite_path) as connection:
        connection.execute("DELETE FROM grading_evidence WHERE attempt_id = ?", (attempt_id,))
        connection.commit()

    regrade_client = FakeTeachBackClient()
    _regrade_attempt(
        vault,
        repository,
        repository.fetch_practice_attempt(attempt_id),
        runtime=_regrade_runtime(),
        client=regrade_client,
        grading_source="ai",
        clock=clock,
    )

    regrade_rubric_ids = [c["id"] for c in regrade_client.grading_contexts[0].rubric["criteria"]]
    assert regrade_rubric_ids == ["core_definition", "core_geometry", "core_uniqueness"]


# ── replay survives item edits away from teach_back mode ─────────────────────


def test_replay_teach_back_attempt_survives_practice_mode_change(tmp_path):
    _root, vault, repository = _setup(tmp_path)
    clock = FrozenClock(NOW)
    client = FakeTeachBackClient()
    item = vault.practice_items[TEACH_ITEM_ID]
    state = _run_conversation(vault, repository, item, client, answers=["ans 1", "ans 2"], clock=clock)
    finish_teach_back(vault, repository, state, client, clock=clock)

    # The item is later edited to another practice mode: the persisted
    # teach_back attempt was valid when recorded, so replay must still apply it.
    vault.practice_items[TEACH_ITEM_ID] = item.model_copy(
        update={"practice_mode": "short_answer", "attempt_types_allowed": ["independent_attempt"]}
    )

    result = rebuild_derived_state(vault, repository, learning_object_ids=[LO_ID])

    assert LO_ID in result.learning_object_ids
    assert result.replayed_attempts >= 1
    assert repository.mastery_state(LO_ID) is not None


# ── unasked criteria are never zero-score failures ────────────────────────────


def test_derive_facet_outcomes_skips_ungraded_criteria(tmp_path):
    _root, vault, _repository = _setup(tmp_path)
    item = vault.practice_items[TEACH_ITEM_ID]
    rubric = item.grading_rubric
    covered = {"definition": 0.33, "geometry": 0.33, "uniqueness": 0.33}

    partial = derive_facet_outcomes(
        item,
        rubric,
        criterion_points={"core_definition": 1.0},  # only one criterion graded
        covered_facets=covered,
        correctness=0.6,
        attempt_type="teach_back",
    )
    # Graded criterion drives its facet; ungraded criteria contribute nothing,
    # so their facets fall back to whole-attempt correctness — never 0.0.
    assert partial["definition"] == pytest.approx(1.0)
    assert partial["geometry"] == pytest.approx(0.6)
    assert partial["uniqueness"] == pytest.approx(0.6)

    # Full criterion_points reproduce the existing behavior bit-for-bit.
    full_points = {
        "core_definition": 1.0,
        "core_geometry": 0.0,
        "core_uniqueness": 1.0,
        "transfer_rank_deficient": 0.5,
        "transfer_rotation": 0.0,
    }
    full = derive_facet_outcomes(
        item,
        rubric,
        criterion_points=full_points,
        covered_facets=covered,
        correctness=0.6,
        attempt_type="independent_attempt",
    )
    assert full["geometry"] == pytest.approx(0.0)
    assert full["uniqueness"] == pytest.approx(1.0)


def test_rubric_tier_defaults_to_core_for_existing_items(tmp_path):
    _root, vault, _repository = _setup(tmp_path)
    legacy = vault.practice_items["pi_svd_define_001"].grading_rubric
    assert all(criterion.tier == "core" for criterion in legacy.criteria)
    parsed = Rubric.model_validate(
        {"max_points": 4, "criteria": [{"id": "c", "points": 4, "description": "d"}], "fatal_errors": []}
    )
    assert parsed.criteria[0].tier == "core"


# ── scheduler ─────────────────────────────────────────────────────────────────


def _seed_lo_evidence(repository):
    repository.upsert_mastery_state(
        MasteryState(
            learning_object_id=LO_ID,
            logit_mean=0.0,
            logit_variance=1.0,
            evidence_count=1,
            last_evidence_at="2026-05-18T12:00:00Z",
            algorithm_version=ALGORITHM_VERSION,
            updated_at=NOW_ISO,
        )
    )


def test_scheduler_caps_teach_back_items_per_queue(tmp_path):
    second_item = _teach_item_payload("pi_svd_teach_002")
    _root, vault, repository = _setup(tmp_path, extra_items=[second_item])
    _seed_lo_evidence(repository)

    queue = build_due_queue(
        vault,
        repository,
        clock=FrozenClock(NOW),
        session=SchedulerSession(session_id="sess_1"),
        persist_explanations=False,
    )

    teach_back_items = [entry for entry in queue if entry.selected_mode == "teach_back"]
    assert vault.config.teach_back.session_cap == 1
    assert len(teach_back_items) == 1
    # PROBE-like semantics: rides the probe intent with an EIG-driven reward.
    assert teach_back_items[0].reward_debug["intent"] == "probe"
    assert teach_back_items[0].components.get("selection_reward", 0.0) > 0

    # Raising the cap admits both teach_back items.
    vault.config.teach_back.session_cap = 2
    queue = build_due_queue(
        vault,
        repository,
        clock=FrozenClock(NOW),
        session=SchedulerSession(session_id="sess_1"),
        persist_explanations=False,
    )
    assert len([entry for entry in queue if entry.selected_mode == "teach_back"]) == 2


def test_teach_back_stays_weakly_schedulable_on_solid_knowledge(tmp_path):
    _root, vault, repository = _setup(
        tmp_path,
        extra_items=[
            _helper_item_payload("pi_helper_def", "definition"),
            _helper_item_payload("pi_helper_geo", "geometry"),
            _helper_item_payload("pi_helper_uni", "uniqueness"),
        ],
    )
    for item_id in ("pi_helper_def", "pi_helper_geo", "pi_helper_uni"):
        _make_facet_solid(vault, repository, item_id)

    queue = build_due_queue(
        vault,
        repository,
        clock=FrozenClock(NOW),
        session=SchedulerSession(session_id="sess_1"),
        persist_explanations=False,
    )

    teach_back_items = [entry for entry in queue if entry.selected_mode == "teach_back"]
    assert len(teach_back_items) == 1
    # The floor keeps it in the queue, at low (floored) priority.
    assert teach_back_items[0].priority > 0


# ── migration ─────────────────────────────────────────────────────────────────


def test_migration_020_allows_teach_back_on_existing_db(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    old_migrations = tmp_path / "old_migrations"
    old_migrations.mkdir()
    for migration in discover_migrations():
        if migration.version <= 19:
            shutil.copy2(migration.path, old_migrations / migration.path.name)
    apply_migrations(sqlite_path, migrations_dir=old_migrations)
    with connect(sqlite_path) as connection:
        _insert_attempt(connection, attempt_id="attempt_live", attempt_type="independent_attempt", session_id="sess1")
        connection.commit()

    apply_migrations(sqlite_path)

    with connect(sqlite_path) as connection:
        _insert_attempt(connection, attempt_id="attempt_teach", attempt_type="teach_back")
        connection.commit()
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        existing = connection.execute(
            "SELECT attempt_type, session_id FROM practice_attempts WHERE id = ?",
            ("attempt_live",),
        ).fetchone()
        indexes = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index' AND tbl_name = 'practice_attempts'"
            )
        }
    assert existing["attempt_type"] == "independent_attempt"
    assert existing["session_id"] == "sess1"
    assert {"idx_attempts_lo_time", "idx_attempts_item_time"} <= indexes


def _insert_attempt(connection, *, attempt_id: str, attempt_type: str, session_id: str | None = None) -> None:
    connection.execute(
        """
        INSERT INTO practice_attempts(
          id, practice_item_id, learning_object_id, subject, concept, practice_mode,
          attempt_type, learner_answer_md, evidence_facets_json, evidence_weights_json,
          rubric_score, correctness, confidence, latency_seconds, hints_used,
          error_type, grader_confidence, manual_review, manual_review_reason,
          created_at, updated_at, session_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            attempt_id,
            "pi_svd",
            "lo_svd",
            "linear-algebra",
            "singular_value_decomposition",
            "teach_back",
            attempt_type,
            "transcript",
            "[]",
            "{}",
            4,
            1.0,
            5,
            10,
            0,
            None,
            0.9,
            0,
            None,
            "2026-05-19T12:00:00Z",
            "2026-05-19T12:00:00Z",
            session_id,
        ),
    )
