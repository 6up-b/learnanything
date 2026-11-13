"""P1 step 9 (A1) -- the hot-path scheduling cutover is REAL, not dead code.

Before this fix ``attempts.apply_attempt`` called
``hot_path_applies_practice_review`` WITHOUT threading ``eligible`` (it defaulted
to ``True``), so on a live mvp-0.8 vault the §3.8 ineligible divergence was dead:
forcing the observation ineligible had zero effect on the scheduling write. These
tests thread REAL evidence eligibility through the seam and prove:

- an INELIGIBLE observation leaves card scheduling state EXACTLY as it was (the
  divergence exists, and the two latent else-branch bugs are fixed). The legacy
  vault's unconditional write went with the tag gate (refactor D5).
"""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.substrate import activities as ACT
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault, set_algorithm_version

ITEM = "pi_svd_define_001"
LO = "lo_svd_definition"


def _vault(tmp_path, *, version):
    vault_root = tmp_path / f"vault-{version}"
    paths = create_basic_vault(vault_root)
    set_algorithm_version(paths, version)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return vault, repository


def _attempt(vault, repository, *, answer="SVD is U Sigma V^T.", points=4, confidence=5, clock=None):
    return complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id=ITEM, learner_answer_md=answer, attempt_type="independent_attempt"),
        SelfGradeInput(criterion_points={"correctness": points}, confidence=confidence),
        clock=clock or FrozenClock(NOW),
    )


def test_ineligible_observation_leaves_mvp08_scheduling_untouched(tmp_path, monkeypatch):
    live_vault, live_repo = _vault(tmp_path, version="mvp-0.8")

    # Seed one eligible attempt so a prior memory exists on both vaults.
    clock1 = FrozenClock(NOW)
    _attempt(live_vault, live_repo, clock=clock1)
    live_before = live_repo.practice_item_state(ITEM)

    # Force the observation's evidence eligibility to INELIGIBLE (quarantined /
    # out-of-band). This is the REAL source the hot path now threads; before the fix
    # patching it had no effect (eligible defaulted True).
    monkeypatch.setattr(
        ACT, "evidence_eligibility_for", lambda *, purpose, feedback_condition: ("ineligible", "forced")
    )
    clock2 = FrozenClock(NOW.replace(day=NOW.day + 1))
    _attempt(live_vault, live_repo, clock=clock2)

    live_after = live_repo.practice_item_state(ITEM)

    # LIVE mvp-0.8: the ineligible second observation left scheduling EXACTLY as it was
    # (no memory rewrite, no due-date recompute) -- the §3.8 divergence.
    assert (live_after.difficulty, live_after.stability, live_after.retrievability, live_after.due_at) == (
        live_before.difficulty,
        live_before.stability,
        live_before.retrievability,
        live_before.due_at,
    )


def test_first_ever_ineligible_observation_creates_no_memory_state(tmp_path, monkeypatch):
    # else-branch bug 1: a first-ever ineligible observation must NOT synthesize memory
    # via apply_review(None, ...); it leaves scheduling null on a live vault.
    live_vault, live_repo = _vault(tmp_path, version="mvp-0.8")
    monkeypatch.setattr(
        ACT, "evidence_eligibility_for", lambda *, purpose, feedback_condition: ("ineligible", "forced")
    )
    _attempt(live_vault, live_repo)
    state = live_repo.practice_item_state(ITEM)
    assert state is not None
    assert state.stability is None and state.difficulty is None and state.due_at is None
