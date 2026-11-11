"""What other test files use from ``tests/test_probe_robust_cutover.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.attempts.attempts import ApplyAttemptInput, AttemptDraft, ResolvedGrade, apply_attempt
from learnloop.diagnosis.probe_episodes import (
    commit_presentation,
    eligible_instruments,
    episode_hypothesis_set,
    serve_presentation,
)
from learnloop.diagnosis.probe_families import validate_and_compile_card
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, admit_probe_instrument_card, create_basic_vault, set_algorithm_version


LO_ID = "lo_svd_definition"
ITEM_ID = "pi_svd_define_001"
CLOCK = FrozenClock(NOW)


def _load(tmp_path, *, version: str = "mvp-0.8"):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    set_algorithm_version(paths, version)
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    admit_probe_instrument_card(repository, card_id="card_svd_contrast", items=(ITEM_ID,))
    return loaded, repository


def _record_full_score_probe(loaded, repository, episode, item_id=ITEM_ID):
    hypothesis_set = episode_hypothesis_set(repository, episode)
    eligible = next(
        entry
        for entry in eligible_instruments(loaded, repository, episode, hypothesis_set=hypothesis_set)
        if entry.item.id == item_id
    )
    presentation = commit_presentation(loaded, repository, episode, eligible, clock=CLOCK)
    serve_presentation(repository, presentation.id, clock=CLOCK)
    attempt_id = new_ulid()
    apply_attempt(
        loaded,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=item_id,
                learner_answer_md="answer",
                attempt_type="diagnostic_probe",
                probe_presentation_id=presentation.id,
            ),
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=4,
                criterion_points={"correctness": 4.0},
                evidence_rows=[],
                error_attributions=[],
                grader_confidence=1.0,
                confidence=4,
                manual_review_reason=None,
            ),
            grading_source="ai",
        ),
        clock=CLOCK,
    )
    return presentation, attempt_id


def _contrast_instrument():
    from learnloop.diagnosis.probe_families import (
        CONTRAST_CONFUSABLE_DEFAULT_ROWS,
        CONTRAST_CONFUSABLE_V1,
        InstrumentCard,
    )

    card = InstrumentCard(
        id="card_svd_contrast",
        version=1,
        family_template_id=CONTRAST_CONFUSABLE_V1.id,
        family_template_version=CONTRAST_CONFUSABLE_V1.version,
        learning_object_id=LO_ID,
        target_decision="choose_schema_vs_confusable_repair",
        bindings={"target_facet": "recall", "confusable_concept": "eigendecomposition"},
        hypotheses=CONTRAST_CONFUSABLE_V1.hypothesis_slots,
        conditional_observations=CONTRAST_CONFUSABLE_DEFAULT_ROWS,
        target_facets=("recall",),
        signature_error_types={"confusable_signature": ["conceptual_slip"]},
    )
    return validate_and_compile_card(card, CONTRAST_CONFUSABLE_V1)
