"""P2 LEAKAGE SUITE -- the consolidated §12.4 / §12.3.2 leakage acceptance contract.

Every leakage guard the golden path relies on, gathered into ONE named suite so the
launch-defaults review (§13) has a single place to read them. The canonical cases are
REUSED from their track modules (imported under private aliases so pytest collects them
only here); the diagnostic-exposure-consumption case (§5.2 -- rendered diagnostic
surfaces burn their held-out eligibility) is added because no track module owned it.

Cases:
  1. practice -> assessment fingerprint blocking (same surface_hash exposure invalidates
     the reserve before render);
  2. an assessment-reserved surface is refused at pool admission (hard-group collision);
  3. reader-answer exposure -> reserve invalidation (a revealed reserved surface burns);
  4. diagnostic exposure consumption (a rendered diagnostic surface loses cold
     eligibility exactly like any other exposure).
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services import diagnostic_pack as DP
from learnloop.services import golden_path_run as GPR
from learnloop.services.activities import (
    evaluate_held_out_eligibility,
    reserve_surface,
    resolve_legacy_item,
)
from learnloop.services.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.services.golden_path_fixture import (
    EXEMPLAR_A,
    FIX_NOW,
    LO_ID,
    build_golden_path_fixture,
)
from learnloop.services.probe_episodes import (
    commit_presentation,
    eligible_instruments,
    episode_hypothesis_set,
    serve_presentation,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

# Reused track-test cases (aliased so pytest does not collect them twice).
from tests.test_reader_dialogue import (
    test_ask_warms_and_invalidates_a_revealed_reserve as _reader_reveal_burns_reserve,
)
from tests.test_surface_pool import (
    test_assessment_reserved_surface_is_refused_at_admission as _assessment_reserved_refused,
)
from tests.test_surface_pool import (
    test_practice_exposure_invalidates_same_fingerprint_assessment_reserve as _practice_invalidates_reserve,
)

CLOCK = FrozenClock(FIX_NOW)


def _fixture(tmp_path):
    """The (vault, repo, fx) triple the surface-pool track cases expect as ``fixture``."""

    root = tmp_path / "vault"
    fx = build_golden_path_fixture(root)
    vault = load_vault(root)
    repo = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    return vault, repo, fx


class TestP2LeakageSuite:
    """The named consolidation point for every P2 leakage guard (§12.4 / §12.3.2)."""

    def test_practice_to_assessment_fingerprint_blocking(self, tmp_path):
        # Reused from the PRACTICE track: a practice render on the same fingerprint
        # invalidates the assessment reserve before render (§12.4).
        _practice_invalidates_reserve(_fixture(tmp_path))

    def test_assessment_reserved_surface_refused_at_admission(self, tmp_path):
        # Reused from the PRACTICE track: an assessment-reserved surface (hard-group
        # collision) is refused at pool admission (§7.3 / §12.4).
        _assessment_reserved_refused(_fixture(tmp_path))

    def test_reader_answer_exposure_invalidates_reserve(self, tmp_path):
        # Reused from the READER track: an AI answer revealing a reserved surface's cues
        # burns it exactly as any other exposure (§12.3.2 hard-group collision).
        _reader_reveal_burns_reserve(tmp_path)

    def test_diagnostic_exposure_consumes_cold_eligibility(self, tmp_path):
        # NEW case: a rendered diagnostic surface consumes its held-out eligibility via
        # the same shared exposure ledger (§5.2 "burns every rendered diagnostic
        # surface via the existing exposure path"). No manufactured freshness.
        vault, repo, fx = _fixture(tmp_path)
        rid = fx.receipt.run_id

        # Reserve the anchor exemplar under the assessment purpose -> initially unseen.
        reserved = resolve_legacy_item(vault, repo, vault.practice_items[EXEMPLAR_A],
                                       purpose="assessment", clock=CLOCK)
        reserve_surface(repo, surface_id=reserved.surface_id, purpose="assessment", clock=CLOCK)
        assert evaluate_held_out_eligibility(
            repo, surface=repo.fetch_surface(reserved.surface_id), purpose="assessment"
        ).is_unseen is True

        # Admit a probe card, enter the baseline, and render ONE diagnostic surface on
        # the same item through the live probe machinery.
        _admit_probe_card(repo)
        pack = _reviewed_pack(repo, fx.blueprint_version_id)
        GPR.advance(repo, rid, to_state="measuring", reason="b", idempotency_key="m", clock=CLOCK)
        baseline = DP.enter_baseline(vault, repo, run_id=rid, learning_object_id=LO_ID,
                                     pack_id=pack.pack_id, clock=CLOCK)
        _drive_probe_item(vault, repo, baseline["episode_id"], EXEMPLAR_A, score=4)

        # The diagnostic render landed a rendered exposure in the ONE ledger, so the
        # same-fingerprint reserve is no longer unseen.
        assert evaluate_held_out_eligibility(
            repo, surface=repo.fetch_surface(reserved.surface_id), purpose="assessment"
        ).is_unseen is False


# ---------------------------------------------------------------------------
# Local helpers for the new diagnostic-exposure case (kept identical in shape to
# the acceptance-suite drivers).
# ---------------------------------------------------------------------------

def _admit_probe_card(repo: Repository) -> None:
    from learnloop.services.probe_families import (
        CONTRAST_CONFUSABLE_DEFAULT_ROWS,
        CONTRAST_CONFUSABLE_V1,
        InstrumentCard,
        ensure_builtin_families,
        validate_and_compile_card,
    )

    ensure_builtin_families(repo, clock=CLOCK)
    card = InstrumentCard(
        id="card_leak_diag", version=1,
        family_template_id=CONTRAST_CONFUSABLE_V1.id,
        family_template_version=CONTRAST_CONFUSABLE_V1.version,
        learning_object_id=LO_ID, target_decision="choose_symmetric_decomposition",
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
    repo.link_probe_item_family(
        practice_item_id=EXEMPLAR_A, instrument_card_id=card.id, instrument_card_version=1, clock=CLOCK
    )


def _reviewed_pack(repo: Repository, blueprint_version_id: str):
    pack = DP.assemble_pack(
        repo, pack_slug="pack_leak", blueprint_version_id=blueprint_version_id,
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
