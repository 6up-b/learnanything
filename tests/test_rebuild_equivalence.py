"""Rebuild equivalence: live state == a whole-vault rebuild of the same ledger.

Two pre-existing mismatches between live state and ``rebuild --shadow``
(fix stage 2026-10-25), both on the replay side:

1. **Mastery on multi-attempt histories.** Replay recomputes each attempt with
   the whole ledger already on disk, and read it unbounded: the recent-attempt
   windows (familiarity, error severity, item quality) counted the attempts
   recorded *after* the one being replayed, and the canonical facet cache it
   read was the whole-history fold. Replay now reads the ledger as the live
   write saw it: the windows are bounded to the attempts before the replayed
   one (``replay_ledger_position``), and the canonical cache is folded to the
   attempts before it (read) and through it (left), the whole-ledger
   projection closing the replay.
2. **``practice_item_state.active`` after a primary load.** State sync
   deactivates retired items; replay deleted the row and the attempt path
   rewrote it active. Replay now keeps a lifecycle deactivation.

The live path is unchanged (the bounds are set only on replay), so this is a
replay bug fix, not a successor.
"""

from __future__ import annotations

from datetime import timedelta
import random
import sqlite3

import pytest

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.content.authoring.item_authoring import retire_item
from learnloop.db.repositories import Repository
from learnloop.substrate.canonical_projection import project_canonical_facet_state
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
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


# ── the two reported mismatches ──────────────────────────────────────────────


@pytest.mark.parametrize(
    "items",
    [("pi_svd_define_001", "pi_svd_define_001"), ("pi_diag_easy", "pi_diag_mid")],
    ids=["same-item", "two-items"],
)
def test_a_two_attempt_history_without_claims_rebuilds_to_live_mastery(tmp_path, items):
    """The LP-min record's oracle case: live 0.687 vs rebuilt 0.560 before."""

    paths, vault, repository = _vault(tmp_path)
    _answer(vault, repository, items[0], minutes=1, points=4.0)
    _answer(vault, repository, items[1], minutes=61, points=2.0)
    live = _mastery(repository)

    rebuild_all_derived_state(vault, repository)

    assert _mastery(repository) == live


def test_replay_reads_no_attempt_recorded_after_the_one_it_recomputes(tmp_path):
    """Every replayed attempt's trace equals its live trace (familiarity,
    prediction, facet updates): nothing later in the ledger leaks in."""

    paths, vault, repository = _vault(tmp_path)
    ids = [
        _answer(vault, repository, "pi_svd_define_001", minutes=1, points=4.0).attempt_id,
        _answer(vault, repository, "pi_diag_easy", minutes=30, points=1.0).attempt_id,
        _answer(vault, repository, "pi_svd_define_001", minutes=61, points=2.0).attempt_id,
    ]
    live = {attempt_id: repository.attempt_debug_payload(attempt_id) for attempt_id in ids}

    rebuild_all_derived_state(vault, repository)

    for attempt_id in ids:
        replayed = repository.attempt_debug_payload(attempt_id)
        for key in ("familiarity_trace", "prediction_trace", "facet_recall_updates", "observation_weight",
                    "predicted_correctness", "mastery_trace"):
            assert replayed.get(key) == live[attempt_id].get(key), (attempt_id, key)


def test_a_retired_item_stays_inactive_through_a_primary_load_and_a_rebuild(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    _answer(vault, repository, "pi_svd_define_002", minutes=1)
    _answer(vault, repository, "pi_svd_define_001", minutes=2)
    retire_item(paths.root, repository, practice_item_id="pi_svd_define_002", reason="duplicate_surface", clock=_at(3))
    vault = load_vault(paths.root)
    # A primary load runs state sync, which closes the retired item.
    sync_vault_state(vault, repository, clock=_at(4))
    assert repository.practice_item_state("pi_svd_define_002").active is False

    assert _shadow_summary(paths)["summary"] == ZERO

    rebuild_all_derived_state(vault, repository)
    assert repository.practice_item_state("pi_svd_define_002").active is False
    assert repository.practice_item_state("pi_svd_define_001").active is True


def test_replay_still_closes_an_administered_diagnostic_probe_left_active(tmp_path):
    """Keeping deactivations never reopens anything: the attempt path's own
    flip (a single-use probe) still applies to a row a pre-fix vault left
    active."""

    from tests.test_diagnostic_probe_single_use import DIAG_ITEM, LO_ID, _diagnostic_attempt
    from tests.test_diagnostic_probe_single_use import _vault as probe_vault
    from learnloop.substrate.replay import replay_learning_object

    vault, repository = probe_vault(tmp_path)
    _diagnostic_attempt(vault, repository)
    repository.set_practice_item_active(DIAG_ITEM, active=True)

    replay_learning_object(vault, repository, LO_ID)

    assert repository.practice_item_state(DIAG_ITEM).active is False


# ── the bounds themselves ────────────────────────────────────────────────────


def test_recent_attempt_windows_bound_by_ledger_position(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    first = _answer(vault, repository, "pi_svd_define_001", minutes=1).attempt_id
    second = _answer(vault, repository, "pi_svd_define_001", minutes=2).attempt_id
    third = _answer(vault, repository, "pi_svd_define_001", minutes=3).attempt_id
    rows = {row["id"]: row for row in repository.list_attempts_by_learning_object("lo_svd_definition")}
    position = (rows[second]["created_at"], second)

    by_lo = repository.list_recent_attempts_by_learning_object("lo_svd_definition", before=position)
    by_item = repository.list_recent_attempts_by_practice_item("pi_svd_define_001", before=position)

    assert [row["id"] for row in by_lo] == [first]
    assert [row["id"] for row in by_item] == [first]
    # Unbounded reads are unchanged.
    assert [row["id"] for row in repository.list_recent_attempts_by_learning_object("lo_svd_definition")] == [
        third, second, first,
    ]


def test_a_bounded_fold_equals_the_fold_live_left_and_reconciles_no_factor(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    first = _answer(vault, repository, "pi_svd_define_001", minutes=1, points=1.0).attempt_id

    def recall_rows():
        return sorted(
            (row.facet_id, row.capability_key, row.practice_item_id or "", row.recall_alpha, row.recall_beta)
            for row in repository.canonical_facet_recall_states()
        )

    after_first = recall_rows()
    _answer(vault, repository, "pi_svd_define_001", minutes=2, points=0.0)
    after_second = recall_rows()
    assert after_second != after_first
    created_at = next(
        row["created_at"] for row in repository.list_attempts_by_learning_object("lo_svd_definition")
        if row["id"] == first
    )
    with sqlite3.connect(paths.sqlite_path) as connection:
        factors_before = connection.execute("SELECT * FROM unresolved_cause_factors ORDER BY 1").fetchall()

    project_canonical_facet_state(vault, repository, through=(created_at, first))
    assert recall_rows() == after_first
    project_canonical_facet_state(vault, repository, before=(created_at, first))
    assert recall_rows() == []
    with sqlite3.connect(paths.sqlite_path) as connection:
        assert connection.execute("SELECT * FROM unresolved_cause_factors ORDER BY 1").fetchall() == factors_before

    project_canonical_facet_state(vault, repository)
    assert recall_rows() == after_second
    with pytest.raises(ValueError):
        project_canonical_facet_state(vault, repository, before=(created_at, first), through=(created_at, first))


# ── property: random histories ───────────────────────────────────────────────

ITEMS = (
    "pi_svd_define_001", "pi_svd_define_002",
    "pi_diag_easy", "pi_diag_mid", "pi_diag_hard",
    "pi_eig_easy", "pi_eig_mid", "pi_spec_easy",
)
KINDS = ("independent", "independent", "hinted", "primed", "dont_know")
GAPS = (1, 7, 45, 60 * 5, 60 * 24, 60 * 24 * 4)


@pytest.mark.parametrize("seed", range(16))
def test_random_attempt_histories_rebuild_to_live_state_exactly(tmp_path, seed):
    """Random multi-attempt histories over several LOs (interleaved, so the
    LO-by-LO replay order differs from the ledger's), with or without claims,
    with hints, primed retries and "I don't know"s, a retirement and a primary
    load: the shadow rebuild reports no difference in mastery, facet or
    schedule state, and an applied rebuild leaves mastery exactly as live."""

    rng = random.Random(seed)
    claims = ()
    if seed % 2:
        claims = tuple(
            (lo_id, round(rng.uniform(0.2, 0.9), 3))
            for lo_id in rng.sample(["lo_svd_definition", "lo_diag", "lo_eigen_basics"], k=rng.randint(1, 2))
        )
    paths, vault, repository = _vault(tmp_path, claims=claims)
    minutes = 0.0
    for _ in range(rng.randint(3, 12)):
        minutes += rng.choice(GAPS)
        _answer(
            vault,
            repository,
            rng.choice(ITEMS),
            minutes=minutes,
            points=float(rng.randint(0, 4)),
            kind=rng.choice(KINDS),
        )
    if rng.random() < 0.5:
        attempted = sorted({row["practice_item_id"] for row in repository.list_all_attempts()})
        minutes += 1
        retire_item(paths.root, repository, practice_item_id=rng.choice(attempted), reason="duplicate_surface",
                    clock=_at(minutes))
    # The primary load.
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=_at(minutes + 1))
    live = _mastery(repository)

    diff = _shadow_summary(paths)
    assert diff["summary"] == ZERO, {family: diff[family]["changes"][:3] for family in ZERO}

    rebuild_all_derived_state(vault, repository)
    assert _mastery(repository) == live
