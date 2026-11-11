"""What other test files use from ``tests/test_rebuild_equivalence.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import timedelta

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.substrate.shadow_rebuild import shadow_rebuild
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, add_followup_item, create_placement_vault


ZERO = {"mastery": 0, "facet": 0, "schedule": 0}


def _at(minutes: float) -> FrozenClock:
    return FrozenClock(NOW + timedelta(minutes=minutes))


def _vault(tmp_path, *, claims=()):
    paths = create_placement_vault(tmp_path / "vault", version=LATEST_ALGORITHM_VERSION)
    add_followup_item(paths.root)
    repository = Repository(paths.sqlite_path)
    # A claim made before the vault's first sync is in force at the LO's
    # first materialization live and at its first attempt in replay alike.
    # (Claims made later are the LP claim-fix successor's subject.)
    for lo_id, level in claims:
        repository.insert_learner_claim(
            {
                "claim_type": "self_rating", "scope_type": "learning_object", "scope_id": lo_id,
                "evidence_family": "recall", "claimed_level": level, "prior_pseudo_count": 2.0,
                "source": "manual_cli",
            },
            clock=_at(-10),
        )
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=_at(0))
    return paths, vault, repository


def _answer(vault, repository, item_id, *, minutes, points=4.0, kind="independent"):
    if kind == "hinted" and "hinted_attempt" not in vault.practice_items[item_id].attempt_types_allowed:
        kind = "independent"
    if kind == "dont_know":
        draft = AttemptDraft(practice_item_id=item_id, learner_answer_md="", attempt_type="dont_know")
        grade = SelfGradeInput(criterion_points={}, confidence=3)
    else:
        draft = AttemptDraft(
            practice_item_id=item_id,
            learner_answer_md="An answer.",
            attempt_type="hinted_attempt" if kind == "hinted" else "independent_attempt",
            hints_used=1 if kind == "hinted" else 0,
            primed=kind == "primed",
        )
        grade = SelfGradeInput(criterion_points={"correctness": points}, confidence=4)
    return complete_self_graded_attempt(vault, repository, draft, grade, clock=_at(minutes))


def _mastery(repository):
    return {
        lo_id: (state.logit_mean, state.logit_variance, state.evidence_count, state.last_evidence_at)
        for lo_id, state in repository.mastery_states().items()
    }


def _shadow_summary(paths):
    result = shadow_rebuild(load_vault(paths.root))
    assert result.live_database_unchanged
    return result.learner_state_diff


ITEMS = (
    "pi_svd_define_001", "pi_svd_define_002",
    "pi_diag_easy", "pi_diag_mid", "pi_diag_hard",
    "pi_eig_easy", "pi_eig_mid", "pi_spec_easy",
)
KINDS = ("independent", "independent", "hinted", "primed", "dont_know")
GAPS = (1, 7, 45, 60 * 5, 60 * 24, 60 * 24 * 4)


def _iso(minutes: float) -> str:
    return (NOW + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")


def _live_reanchoring_claim(vault, repository, lo_id, *, minutes, level, pseudo_count=2.0,
                            source="tutor_gap_declaration"):
    """A claim written and re-anchored live at its own time, as a tutor gap
    declaration does (LP-min (a), defect 1; an appended claim, never replaced)."""

    from learnloop.learner.mastery import reanchor_mastery_from_claim

    claim_id = repository.insert_learner_claim(
        {
            "claim_type": "self_rating", "scope_type": "learning_object", "scope_id": lo_id,
            "evidence_family": "recall", "claimed_level": level, "prior_pseudo_count": pseudo_count,
            "source": source, "created_at": _iso(minutes),
        }
    )
    reanchor_mastery_from_claim(
        vault, repository, lo_id, claimed_level=level, prior_pseudo_count=pseudo_count, now_iso=_iso(minutes),
        claim_id=claim_id,
    )


LOS = ("lo_svd_definition", "lo_diag", "lo_eigen_basics")
