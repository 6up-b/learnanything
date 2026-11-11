"""What other test files use from ``tests/test_p2_acceptance.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.diagnosis import diagnostic_pack as DP
from learnloop.attempts.attempts import ApplyAttemptInput, AttemptDraft, ResolvedGrade, apply_attempt
from learnloop.curriculum.golden_path_fixture import EXEMPLAR_A, EXEMPLAR_B, FIX_NOW, LO_ID
from learnloop.diagnosis.probe_episodes import (
    commit_presentation,
    eligible_instruments,
    episode_hypothesis_set,
    serve_presentation,
)
from learnloop.diagnosis.probe_families import (
    CONTRAST_CONFUSABLE_DEFAULT_ROWS,
    CONTRAST_CONFUSABLE_V1,
    InstrumentCard,
    ensure_builtin_families,
    validate_and_compile_card,
)


CLOCK = FrozenClock(FIX_NOW)


def _admit_probe_card(repo: Repository) -> None:
    """Admit ONE pre-authored contrast instrument card over the fixture LO's method-
    selection facet, linking the two familiar-anchor exemplars as probe candidates."""

    ensure_builtin_families(repo, clock=CLOCK)
    card = InstrumentCard(
        id="card_method_selection",
        version=1,
        family_template_id=CONTRAST_CONFUSABLE_V1.id,
        family_template_version=CONTRAST_CONFUSABLE_V1.version,
        learning_object_id=LO_ID,
        target_decision="choose_symmetric_decomposition",
        bindings={"target_facet": "method_selection", "confusable_concept": "non_symmetric"},
        hypotheses=CONTRAST_CONFUSABLE_V1.hypothesis_slots,
        conditional_observations=CONTRAST_CONFUSABLE_DEFAULT_ROWS,
        target_facets=("method_selection",),
        signature_error_types={"confusable_signature": ["wrong_method"]},
    )
    inst = validate_and_compile_card(card, CONTRAST_CONFUSABLE_V1)
    repo.insert_probe_instrument_card(
        card_id=card.id, version=1,
        probe_family_template_id=CONTRAST_CONFUSABLE_V1.id,
        probe_family_template_version=CONTRAST_CONFUSABLE_V1.version,
        learning_object_id=LO_ID, hypothesis_scope=list(card.hypotheses),
        card=card.as_dict(), compiled_likelihood_hash=inst.compiled_likelihood_hash(), clock=CLOCK,
    )
    for iid in (EXEMPLAR_A, EXEMPLAR_B):
        repo.link_probe_item_family(
            practice_item_id=iid, instrument_card_id=card.id, instrument_card_version=1, clock=CLOCK
        )


def _reviewed_pack(repo: Repository, blueprint_version_id: str):
    pack = DP.assemble_pack(
        repo, pack_slug="pack_acceptance", blueprint_version_id=blueprint_version_id,
        cards=[{"card_slug": "c1", "coverage": ["a"]}, {"card_slug": "c2", "coverage": ["b"]}],
    )
    for c in pack.cards:
        DP.admit_pack_card(repo, pack_id=pack.pack_id, card_slug=c.card_slug)
    DP.review_pack(repo, pack_id=pack.pack_id)
    return pack


def _drive_probe_item(vault, repo, episode_id: str, item_id: str, score: int) -> None:
    episode = repo.probe_episode(episode_id)
    hs = episode_hypothesis_set(repo, episode)
    eligible = next(
        e for e in eligible_instruments(vault, repo, episode, hypothesis_set=hs) if e.item.id == item_id
    )
    pres = commit_presentation(vault, repo, episode, eligible, clock=CLOCK)
    serve_presentation(repo, pres.id, clock=CLOCK)
    apply_attempt(
        vault, repo,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=item_id, learner_answer_md="answer",
                attempt_type="diagnostic_probe", hints_used=0, probe_presentation_id=pres.id,
            ),
            attempt_id=new_ulid(),
            grade=ResolvedGrade(
                rubric_score=score, criterion_points={"correctness": float(score)},
                evidence_rows=[], error_attributions=[], grader_confidence=1.0,
                confidence=4, manual_review_reason=None,
            ),
            grading_source="ai",
        ),
        clock=CLOCK,
    )
