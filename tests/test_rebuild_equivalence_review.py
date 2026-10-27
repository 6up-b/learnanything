"""Codex review of the rebuild-equivalence fix (2026-10-25).

* **F1**: a direct per-LO replay (integration backfill, regrade's replay)
  publishes nothing until it has finished: no historical prefix of the
  vault-wide canonical cache, no reset LO, no reopened retired item is ever
  visible to another connection, and an interrupted replay leaves live state
  exactly as it was, so a retry starts from the right lifecycle.
* **F3**: a rebuild completes the recurrence reconciliation its own learner
  replay made necessary, so the rebuild right after it changes nothing.
* **F4**: the bounded replay is the successor ``REPLAY_LEDGER_ALGORITHM_VERSION``
  behind ``replay.ledger_bounded``; below it (or switched off) replay is
  the predecessor's, byte for byte.
* **F2** (rejected, out of scope): the same-second reverse-completion case is
  pinned as a strict xfail so its fix is noticed.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.clock import FrozenClock
from learnloop.content.authoring.item_authoring import retire_item
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.substrate import replay as replay_module
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.helpers import NOW, add_followup_item, create_placement_vault
from tests.test_rebuild_equivalence import _answer, _at

#: The vault-wide and per-LO state a direct replay rewrites.
DERIVED = (
    "learning_object_mastery", "facet_recall_state", "facet_capability_evidence",
    "practice_item_state", "practice_item_quality_state", "attempt_surprise",
    "unresolved_cause_factors",
)


def _read(paths) -> dict[str, list[tuple]]:
    """What another connection sees (a fresh read-only connection)."""

    with connect(paths.sqlite_path, read_only=True) as connection:
        return {
            table: sorted(tuple(row) for row in connection.execute(f'SELECT * FROM "{table}"'))
            for table in DERIVED
        }


def _declare_integration(paths) -> None:
    """Give lo_svd_definition a conjunctive recipe with an integration cell,
    so the integration backfill has a verdict to apply (and replays it)."""

    path = paths.learning_object_path("linear-algebra", "lo_svd_definition")
    payload = read_yaml(path)
    payload["blueprints"] = [{
        "id": "bp_svd", "weight": 1.0,
        "recipes": [{
            "id": "recipe_svd", "composition": "conjunctive",
            "all_of": [
                {"facet": "recall", "capability": "retrieval", "modality": "hard"},
                {"facet": "apply_it", "capability": "procedure_execution", "modality": "hard"},
            ],
            "integration": {"facet": "recall", "capability": "coordination", "modality": "hard"},
        }],
    }]
    write_yaml(path, payload)


def _history(tmp_path):
    """Interleaved attempts on two LOs, then a retirement and a primary load:
    a bounded fold through the first svd attempt would drop lo_diag's later
    evidence from the vault-wide cache, and the retired item is inactive."""

    paths = create_placement_vault(tmp_path / "vault", version=LATEST_ALGORITHM_VERSION)
    add_followup_item(paths.root)
    _declare_integration(paths)
    repository = Repository(paths.sqlite_path)
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=_at(0))
    _answer(vault, repository, "pi_svd_define_002", minutes=1, points=1.0)
    _answer(vault, repository, "pi_diag_easy", minutes=2, points=3.0)
    _answer(vault, repository, "pi_svd_define_001", minutes=3, points=2.0)
    _answer(vault, repository, "pi_diag_mid", minutes=4, points=0.0)
    retire_item(paths.root, repository, practice_item_id="pi_svd_define_002", reason="duplicate_surface",
                clock=_at(5))
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=_at(6))
    assert repository.practice_item_state("pi_svd_define_002").active is False
    return paths, vault, repository


def _inject(monkeypatch, paths, *, fail_on: int):
    """Wrap replay's per-attempt step: before attempt ``fail_on`` replays,
    read the database from another connection, then raise."""

    real = replay_module.replay_existing_attempt
    seen: list[dict[str, list[tuple]]] = []
    calls = {"n": 0}

    def step(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == fail_on:
            seen.append(_read(paths))
            raise RuntimeError("injected replay failure")
        return real(*args, **kwargs)

    monkeypatch.setattr(replay_module, "replay_existing_attempt", step)
    return seen


@pytest.mark.durability
def test_an_interrupted_integration_backfill_replay_publishes_nothing(tmp_path, monkeypatch):
    """F1 through a direct production caller: the backfill replays the LO
    outside any umbrella transaction."""

    from learnloop.curriculum.integration_backfill import (
        COORDINATION,
        apply_integration_backfill_and_recalibrate,
        plan_integration_backfill,
    )

    paths, vault, repository = _history(tmp_path)
    before = _read(paths)
    report = plan_integration_backfill(vault, capabilities=[COORDINATION])
    assert report.verdicts, "the fixture must give the backfill a verdict to apply"
    seen = _inject(monkeypatch, paths, fail_on=2)

    with pytest.raises(RuntimeError, match="injected"):
        apply_integration_backfill_and_recalibrate(
            vault, repository, report.verdicts, dry_run=False, clock=FrozenClock(NOW)
        )

    # Mid-replay, another connection read the state as it was: no reset LO,
    # no historical prefix of the canonical cache, no reopened retired item.
    assert seen == [before]
    # And the failure left it so.
    assert _read(paths) == before
    assert repository.practice_item_state("pi_svd_define_002").active is False


@pytest.mark.durability
def test_a_retry_after_an_interrupted_direct_replay_keeps_the_lifecycle(tmp_path, monkeypatch):
    """F1's second half: the inactive flags are read inside the replay's
    transaction, so an interruption cannot leave the retired item active
    for a retry to snapshot."""

    from learnloop.substrate.replay import replay_learning_object

    paths, vault, repository = _history(tmp_path)
    before = _read(paths)
    seen = _inject(monkeypatch, paths, fail_on=2)
    with pytest.raises(RuntimeError, match="injected"):
        replay_learning_object(vault, repository, "lo_svd_definition")
    assert seen == [before]
    assert _read(paths) == before
    monkeypatch.undo()

    replay_learning_object(vault, repository, "lo_svd_definition")
    assert repository.practice_item_state("pi_svd_define_002").active is False


def _answer_at(vault, repository, item_id, *, minutes, points, attempt_id):
    """A self-graded attempt with a chosen id (ids are allocated before
    grading, so the id order need not be the commit order)."""

    import learnloop.attempts.attempts as attempts_module

    real = attempts_module.new_ulid
    pending = [attempt_id]
    attempts_module.new_ulid = lambda: pending.pop() if pending else real()
    try:
        return _answer(vault, repository, item_id, minutes=minutes, points=points)
    finally:
        attempts_module.new_ulid = real


@pytest.mark.xfail(
    strict=True,
    reason=(
        "F2, rejected for this stage: two grades of one LO committed in the same second in reverse id "
        "order replay in (created_at, id) order, not commit order. Pre-existing (replay's fold order); "
        "the fix needs a persisted commit sequence (a migration) and a new ledger order everywhere."
    ),
)
def test_two_same_second_attempts_committed_in_reverse_id_order_rebuild_to_live(tmp_path):
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
    from tests.test_rebuild_equivalence import _mastery, _vault

    paths, vault, repository = _vault(tmp_path)
    # B (the later id) commits first; A (the earlier id) commits in the same second.
    _answer_at(vault, repository, "pi_svd_define_001", minutes=1, points=4.0,
               attempt_id="01ZZZZZZZZZZZZZZZZZZZZZZZB")
    _answer_at(vault, repository, "pi_svd_define_001", minutes=1, points=0.0,
               attempt_id="01ZZZZZZZZZZZZZZZZZZZZZZZA")
    live = _mastery(repository)

    rebuild_all_derived_state(vault, repository)

    assert _mastery(repository) == live


# ── F4: the successor and its kill switch ────────────────────────────────────

from learnloop.algorithm_versions import (  # noqa: E402
    CLAIM_FIXES_ALGORITHM_VERSION,
    REPLAY_LEDGER_ALGORITHM_VERSION,
    REPLAY_LEDGER_VERSIONS,
    SUCCESSOR_CHAIN,
)

TAG = REPLAY_LEDGER_ALGORITHM_VERSION
# The landing chained the tag after LP-min (a)'s claim fixes (mvp-0.33).
PREDECESSOR = CLAIM_FIXES_ALGORITHM_VERSION
SWITCH_OFF = "\n[replay]\nledger_bounded = false\n"


def _two_attempt_history(tmp_path, name, *, version, config=""):
    """The LP-min record's oracle case at ``version``: two attempts on one
    item with no claim, whose replay differed from live below the tag."""

    from tests.helpers import append_config_toml

    paths = create_placement_vault(tmp_path / name, version=version)
    add_followup_item(paths.root)
    if config:
        append_config_toml(paths.root, config)
    repository = Repository(paths.sqlite_path)
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=_at(0))
    _answer(vault, repository, "pi_svd_define_001", minutes=1, points=4.0)
    _answer(vault, repository, "pi_svd_define_001", minutes=61, points=2.0)
    return paths, vault, repository


def _rebuilt(vault, repository):
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
    from tests.test_rebuild_equivalence import _mastery

    rebuild_all_derived_state(vault, repository)
    return _mastery(repository)


def test_the_successor_is_one_constant_after_its_predecessor_with_its_defaults_snapshot():
    from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, defaults_fingerprint_for_version
    from learnloop.replay_ledger_upgrade import PREDECESSOR as UPGRADE_PREDECESSOR

    # Reader CA2's mvp-0.35 follows it, then the kept replaced claims' mvp-0.36 and mobile PR-4's mvp-0.37 as the latest (all keep it).
    assert TAG == "mvp-0.34" == SUCCESSOR_CHAIN[-4] and SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.37"
    assert UPGRADE_PREDECESSOR == PREDECESSOR == SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1]
    assert REPLAY_LEDGER_VERSIONS == frozenset({TAG, "mvp-0.35", "mvp-0.36", LATEST_ALGORITHM_VERSION})
    assert DEFAULTS_SNAPSHOT_BY_ALGORITHM[TAG] == defaults_fingerprint_for_version(TAG)
    assert DEFAULTS_SNAPSHOT_BY_ALGORITHM[PREDECESSOR] == defaults_fingerprint_for_version(PREDECESSOR)


def test_the_switch_is_on_by_default_and_classified():
    from learnloop.config.schema import ReplayConfig
    from learnloop.params import parameter_registry as registry

    assert ReplayConfig().ledger_bounded is True
    rule = registry.classify_config_path("replay.ledger_bounded")
    assert rule is not None


def test_a_live_write_is_the_same_below_and_at_the_tag(tmp_path):
    from tests.test_rebuild_equivalence import _mastery

    _paths, _vault, below = _two_attempt_history(tmp_path, "below", version=PREDECESSOR)
    _paths, _vault, at = _two_attempt_history(tmp_path, "at", version=TAG)
    assert _mastery(below) == _mastery(at)


def test_below_the_tag_replay_is_the_predecessors(tmp_path):
    """The same-version golden behaviour: a predecessor rebuild still reads the
    whole ledger (and so differs from live on this history), exactly as
    before the successor."""

    from tests.test_rebuild_equivalence import _mastery

    _paths, vault, repository = _two_attempt_history(tmp_path, "below", version=PREDECESSOR)
    live = _mastery(repository)
    assert _rebuilt(vault, repository) != live


def test_at_the_tag_replay_reproduces_live_and_the_switch_restores_the_predecessor(tmp_path):
    from tests.test_rebuild_equivalence import _mastery

    _paths, vault, repository = _two_attempt_history(tmp_path, "on", version=TAG)
    live = _mastery(repository)
    assert _rebuilt(vault, repository) == live

    _paths, below_vault, below = _two_attempt_history(tmp_path, "below", version=PREDECESSOR)
    predecessor = _rebuilt(below_vault, below)
    _paths, off_vault, off = _two_attempt_history(tmp_path, "off", version=TAG, config=SWITCH_OFF)
    assert off_vault.config.replay.ledger_bounded is False
    assert _mastery(off) == live
    assert _rebuilt(off_vault, off) == predecessor != live


def test_upgrade_from_the_predecessor_rebuilds_to_live_and_through_the_chain(tmp_path):
    from typer.testing import CliRunner

    from learnloop.cli.app import app
    from learnloop.replay_ledger_upgrade import upgrade_to_replay_ledger
    from tests.test_rebuild_equivalence import _mastery

    paths, vault, repository = _two_attempt_history(tmp_path, "direct", version=PREDECESSOR)
    live = _mastery(repository)
    old_replay = _rebuilt(vault, repository)
    assert old_replay != live  # the state a predecessor rebuild left
    result = upgrade_to_replay_ledger(paths.root)
    assert result.upgraded and (result.from_version, result.to_version) == (PREDECESSOR, TAG)
    assert load_vault(paths.root).config.algorithms.algorithm_version == TAG
    assert _mastery(repository) == live
    assert repository.latest_derived_state_rebuild()["algorithm_version"] == TAG
    again = upgrade_to_replay_ledger(paths.root)
    assert not again.upgraded and again.problems == [f"vault is already {TAG}"]

    chained = create_placement_vault(tmp_path / "chained", version="mvp-0.30")
    assert upgrade_to_replay_ledger(chained.root).upgraded
    assert load_vault(chained.root).config.algorithms.algorithm_version == TAG

    old = create_placement_vault(tmp_path / "old", version="mvp-0.8")
    refused = upgrade_to_replay_ledger(old.root)
    assert not refused.upgraded and load_vault(old.root).config.algorithms.algorithm_version == "mvp-0.8"

    cli = create_placement_vault(tmp_path / "cli", version=PREDECESSOR)
    # The bare upgrade targets the latest (mobile PR-4's mvp-0.37, after the kept replaced claims' mvp-0.36), through this tag.
    invoked = CliRunner().invoke(app, ["upgrade", "--vault", str(cli.root)])
    assert invoked.exit_code == 0, invoked.output
    assert f"{PREDECESSOR} -> {LATEST_ALGORITHM_VERSION}" in invoked.output


def test_a_failed_activation_leaves_the_predecessor_and_a_dead_one_resumes(tmp_path, monkeypatch):
    import learnloop.replay_ledger_upgrade as upgrade_module
    from tests.helpers import set_algorithm_version
    from tests.test_rebuild_equivalence import _mastery

    paths, vault, repository = _two_attempt_history(tmp_path, "vault", version=PREDECESSOR)
    live = _mastery(repository)
    old_replay = _rebuilt(vault, repository)
    before = _read(paths)

    def broken(*_args, **_kwargs):
        raise RuntimeError("injected publication failure")

    monkeypatch.setattr(upgrade_module, "_publish_algorithm_version", broken)
    with pytest.raises(RuntimeError, match="injected"):
        upgrade_module.upgrade_to_replay_ledger(paths.root)
    assert load_vault(paths.root).config.algorithms.algorithm_version == PREDECESSOR
    assert _read(paths) == before and _mastery(repository) == old_replay
    monkeypatch.undo()

    # A process that died after publishing the config and before the commit:
    # the tag over the predecessor's database. The upgrade completes it.
    set_algorithm_version(paths, TAG)
    resumed = upgrade_module.upgrade_to_replay_ledger(paths.root)
    assert resumed.upgraded and resumed.notes == [f"completed the activation of {TAG} (a whole-vault rebuild under it)"]
    assert _mastery(repository) == live


# ── Re-review F5: recovery reads the activation's own completion marker ──────

def _died_after_publication(tmp_path, name):
    """A vault whose predecessor rebuild left the predecessor's replay, then an
    activation that published the tag and died before its commit."""

    from tests.helpers import set_algorithm_version
    from tests.test_rebuild_equivalence import _mastery

    paths, vault, repository = _two_attempt_history(tmp_path, name, version=PREDECESSOR)
    live = _mastery(repository)
    assert _rebuilt(vault, repository) != live
    set_algorithm_version(paths, TAG)
    return paths, repository, live


def test_a_startup_receipt_after_a_died_activation_does_not_hide_it(tmp_path):
    """The desktop restarts before the retry: its canonical-projection startup
    refresh stamps a receipt under the tag without replaying mastery. The
    upgrade still completes the activation."""

    from learnloop.replay_ledger_upgrade import upgrade_to_replay_ledger
    from learnloop.substrate.canonical_projection_rollout import refresh_canonical_projection_on_startup
    from tests.test_rebuild_equivalence import _mastery

    paths, repository, live = _died_after_publication(tmp_path, "startup")
    assert refresh_canonical_projection_on_startup(load_vault(paths.root), repository) is not None
    assert repository.latest_derived_state_rebuild()["algorithm_version"] == TAG
    assert _mastery(repository) != live

    resumed = upgrade_to_replay_ledger(paths.root)
    assert resumed.upgraded and resumed.notes == [f"completed the activation of {TAG} (a whole-vault rebuild under it)"]
    assert _mastery(repository) == live
    again = upgrade_to_replay_ledger(paths.root)
    assert not again.upgraded and again.problems == [f"vault is already {TAG}"]


def test_a_died_activation_with_no_rebuild_receipt_is_completed(tmp_path):
    from learnloop.replay_ledger_upgrade import upgrade_to_replay_ledger
    from tests.test_rebuild_equivalence import _mastery

    paths, repository, live = _died_after_publication(tmp_path, "none")
    with repository.connection() as connection:
        connection.execute("DELETE FROM derived_state_rebuilds")
    assert repository.latest_derived_state_rebuild() is None

    resumed = upgrade_to_replay_ledger(paths.root)
    assert resumed.upgraded and _mastery(repository) == live


def test_a_partial_rebuild_under_the_tag_does_not_complete_the_activation(tmp_path):
    """Only a whole-vault rebuild under the tag is the activation's marker: a
    per-LO rebuild (an item edit's, a regrade's) replays only its own LOs."""

    from learnloop.replay_ledger_upgrade import upgrade_to_replay_ledger
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
    from tests.test_rebuild_equivalence import _mastery

    paths, repository, live = _died_after_publication(tmp_path, "partial")
    rebuild_all_derived_state(load_vault(paths.root), repository, learning_object_ids=["lo_diag"])
    assert repository.latest_derived_state_rebuild()["algorithm_version"] == TAG

    resumed = upgrade_to_replay_ledger(paths.root)
    assert resumed.upgraded and _mastery(repository) == live
