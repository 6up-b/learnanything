"""``learnloop upgrade --to mvp-0.26`` (regrade contracts): the upgrade path.

mvp-0.25 (or mvp-0.9 to mvp-0.24 through the chain) -> mvp-0.26. The upgrade
replays exactly the learning objects holding an attempt whose current grading
epoch it reinterprets (an epoch citing no contract, written before the tag,
that it now holds for review) and re-projects; every other attempt replays as
it did. Its notes name the attempts it holds. The upgrade shadow (a shadow
rebuild under ``algorithms.algorithm_version = mvp-0.26``) predicts exactly
what it changes. Playbook items 1, 3, 4, 7 and 8. Fakes only; no network.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from typer.testing import CliRunner

from learnloop.algorithm_versions import METHOD_EXPLICIT_ALGORITHM_VERSION, REGRADE_CONTRACT_ALGORITHM_VERSION
from learnloop.attempts.attempts import unrecorded_epoch_attempts
from learnloop.cli import app
from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop.db.table_roles import TableRole, tables_for_role
from learnloop.held_grades import attempt_grade_held
from learnloop.ops.doctor import run_doctor
from learnloop.outcome_contract import GRADE_CONTRACT_UNRECORDED
from learnloop.regrade_contract_upgrade import upgrade_to_mvp026
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.shadow_rebuild import _learner_state_snapshot, _semantic_diff, shadow_rebuild
from learnloop.vault.loader import load_vault

from tests.helpers import create_placement_vault, set_algorithm_version
from tests.test_held_grade_evidence import T, _graded_apply
from tests.test_regrade_contract_replay import ITEM, SIBLING_ITEM, _regrade, _self_graded_apply, _set_result_points
from tests.test_regrade_contract_successor import JOINT, _settle, _vault

TARGET = REGRADE_CONTRACT_ALGORITHM_VERSION
PREDECESSOR = METHOD_EXPLICIT_ALGORITHM_VERSION
CLOCK = FrozenClock(datetime(2026, 12, 1, 12, 0, tzinfo=UTC))
HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_221"


def _attempt_rows(repository):
    with repository.connection() as connection:
        return {
            row[0]: tuple(row[1:])
            for row in connection.execute(
                "SELECT id, rubric_score, correctness, manual_review, manual_review_reason FROM practice_attempts"
            )
        }


def _evidence(repository):
    with repository.connection() as connection:
        return sorted(tuple(row) for row in connection.execute("SELECT * FROM grading_evidence"))


def _legacy_vault(tmp_path, *, config=""):
    """An mvp-0.25 vault holding the three shapes the successor meets:
    ``att_keep`` graded and never regraded (cites its contract), ``att_blind``
    regraded within its original maximum by the blind grader (uncited; the
    blind record kept its maximum, 8) and ``att_self`` self-graded then
    regraded on a sibling item (uncited); rebuilt to the predecessor's fixed
    point."""

    paths, vault, repository = _vault(tmp_path, version=PREDECESSOR, config=config)
    _graded_apply(vault, repository, ITEM, {"setup": 2.0, "result": 2.0}, attempt_id="att_keep", when=T)
    _graded_apply(vault, repository, ITEM, {"setup": 1.0, "result": 1.0}, attempt_id="att_blind",
                  when=T + timedelta(hours=1))
    _self_graded_apply(vault, repository, SIBLING_ITEM, {"setup": 1.0, "result": 2.0}, attempt_id="att_self",
                       when=T + timedelta(hours=2))
    _set_result_points(paths, 6)
    vault = load_vault(paths.root)
    _regrade(vault, repository, "att_blind", {"setup": 1.0, "result": 2.0}, when=T + timedelta(days=1))
    _regrade(vault, repository, "att_self", {"setup": 2.0, "result": 2.0}, when=T + timedelta(days=1, hours=1))
    _settle(vault, repository)
    return paths, vault, repository


def test_upgrade_holds_exactly_the_unrecorded_epochs_and_rewrites_no_evidence(tmp_path):
    paths, vault, repository = _legacy_vault(tmp_path)
    attempts_before = _attempt_rows(repository)
    evidence_before = _evidence(repository)
    # What the successor will hold (the scan reads the ledger, whatever the label).
    assert sorted(row["attempt_id"] for row in unrecorded_epoch_attempts(vault, repository)) == ["att_blind", "att_self"]

    result = upgrade_to_mvp026(paths.root, clock=CLOCK)

    assert (result.upgraded, result.from_version, result.to_version) == (True, PREDECESSOR, TARGET), result.problems
    assert load_vault(paths.root).config.algorithms.algorithm_version == TARGET
    [note] = result.notes
    assert note.startswith("2 attempt(s)") and "att_blind, att_self" in note
    # Nothing is rewritten: the ledger keeps every row.
    assert _evidence(repository) == evidence_before
    after = _attempt_rows(repository)
    # att_blind: held, its correctness from the maximum its blind record kept (3/8).
    assert after["att_blind"] == (3, 0.375, 1, GRADE_CONTRACT_UNRECORDED)
    # att_self: held, from its regrade's blind record too (4 of 4, its item unchanged).
    assert after["att_self"] == (4, 1.0, 1, GRADE_CONTRACT_UNRECORDED)
    assert attempt_grade_held(repository, "att_blind") and attempt_grade_held(repository, "att_self")
    # Every other attempt reads as it did.
    for attempt_id, row in attempts_before.items():
        if attempt_id not in {"att_blind", "att_self"}:
            assert after[attempt_id] == row, attempt_id
    assert repository.latest_derived_state_rebuild()["algorithm_version"] == TARGET
    with sqlite3.connect(paths.sqlite_path) as connection:
        manifests = {row[0] for row in connection.execute("SELECT algorithm_version FROM parameter_registry_manifests")}
    assert PREDECESSOR in manifests


def test_the_upgrade_shadow_predicts_the_upgrade_exactly(tmp_path):
    """Playbook item 7: a shadow rebuild under the new label, on a scratch
    copy, shows the deltas the upgrade then applies (the live database is
    untouched); under the old label the shadow shows none. The deltas stay on
    the held attempts' items and learning object."""

    paths, vault, repository = _legacy_vault(tmp_path, config=JOINT)
    old = shadow_rebuild(load_vault(paths.root), assignments=[f"algorithms.algorithm_version={PREDECESSOR}"])
    assert old.live_database_unchanged
    assert old.learner_state_diff["summary"] == {"mastery": 0, "facet": 0, "schedule": 0}
    shadow = shadow_rebuild(load_vault(paths.root), assignments=[f"algorithms.algorithm_version={TARGET}"])
    assert shadow.live_database_unchanged
    before = _learner_state_snapshot(repository)

    upgrade_to_mvp026(paths.root, clock=CLOCK)

    applied = _semantic_diff(before, _learner_state_snapshot(repository))
    # The same changes, value for value. The shadow replays every learning
    # object, so its rows also carry the new version stamp where nothing else
    # moved; the upgrade replays only the held attempts' learning object (the
    # others take the stamp at their next rebuild, as at every successor).
    assert _changes(applied) == _changes(shadow.learner_state_diff)
    assert _changes(applied)  # the comparison is not vacuous
    vault = load_vault(paths.root)
    held_items = {ITEM, SIBLING_ITEM}
    learning_object = vault.practice_items[ITEM].learning_object_id
    for family in ("mastery", "facet", "schedule"):
        for change in applied[family]["changes"]:
            key = change["key"]
            if key.get("projection") == "practice_item_state":
                assert key["practice_item_id"] in held_items, change
            if "learning_object_id" in key and key["learning_object_id"] is not None:
                assert key["learning_object_id"] == learning_object, change


def _changes(diff):
    """``{(family, key): after}`` of every change beyond the version stamp."""

    found = {}
    for family in ("mastery", "facet", "schedule"):
        for change in diff[family]["changes"]:
            before = {k: v for k, v in (change["before"] or {}).items() if k != "algorithm_version"}
            after = {k: v for k, v in (change["after"] or {}).items() if k != "algorithm_version"}
            if before != after:
                found[(family, tuple(sorted(change["key"].items())))] = after
    return found


def test_after_the_upgrade_a_rebuild_settles_and_stays(tmp_path):
    """Playbook item 8: FK check, doctor, and a settled rebuild that a
    further rebuild leaves byte-identical (derived tables)."""

    paths, vault, repository = _legacy_vault(tmp_path)
    upgrade_to_mvp026(paths.root, clock=CLOCK)
    vault = load_vault(paths.root)
    with sqlite3.connect(paths.sqlite_path) as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    derived = set(tables_for_role(TableRole.DERIVED))

    def snapshot():
        with connect(repository.sqlite_path, read_only=True) as connection:
            return {
                table: sorted(tuple(row) for row in connection.execute(f'SELECT * FROM "{table}"'))
                for table in sorted(derived)
            }

    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    second = snapshot()
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert snapshot() == second
    assert _attempt_rows(repository)["att_blind"] == (3, 0.375, 1, GRADE_CONTRACT_UNRECORDED)


def test_upgrade_with_nothing_to_reinterpret_replays_nothing(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version=PREDECESSOR)
    repository = Repository(paths.sqlite_path)
    with sqlite3.connect(paths.sqlite_path) as connection:
        attempts_before = connection.execute("SELECT * FROM practice_attempts ORDER BY id").fetchall()
        states_before = connection.execute("SELECT * FROM practice_item_state ORDER BY practice_item_id").fetchall()

    result = upgrade_to_mvp026(paths.root, clock=CLOCK)

    assert (result.upgraded, result.notes) == (True, [])
    with sqlite3.connect(paths.sqlite_path) as connection:
        assert connection.execute("SELECT * FROM practice_attempts ORDER BY id").fetchall() == attempts_before
        assert connection.execute("SELECT * FROM practice_item_state ORDER BY practice_item_id").fetchall() == states_before
    assert repository.latest_derived_state_rebuild()["algorithm_version"] == TARGET


def test_upgrade_through_the_chain_from_earlier_successors(tmp_path):
    for version in ("mvp-0.16", "mvp-0.23", "mvp-0.24"):
        paths = create_placement_vault(tmp_path / version, version=version)
        result = upgrade_to_mvp026(paths.root, clock=CLOCK)
        assert (result.upgraded, result.from_version, result.to_version) == (True, version, TARGET), result.problems
        assert load_vault(paths.root).config.algorithms.algorithm_version == TARGET


def test_upgrade_refuses_older_versions_and_is_idempotent(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version="mvp-0.8")
    refused = upgrade_to_mvp026(paths.root, clock=CLOCK)
    assert refused.upgraded is False and "only 'mvp-0.25'" in refused.problems[0]
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.8"
    set_algorithm_version(paths, TARGET)
    already = upgrade_to_mvp026(paths.root, clock=CLOCK)
    assert already.upgraded is False and already.problems == [f"vault is already {TARGET}"]


def test_upgrade_command_reaches_the_successor(tmp_path):
    paths = create_placement_vault(tmp_path / "vault", version=PREDECESSOR)
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root), "--to", TARGET])
    assert result.exit_code == 0, result.output
    assert f"{PREDECESSOR} -> {TARGET}" in result.output
    # The default target is the latest successor (adaptive difficulty
    # AD2+AD3, mvp-0.30), through this step.
    default = create_placement_vault(tmp_path / "default", version=PREDECESSOR)
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(default.root)])
    assert result.exit_code == 0, result.output
    assert f"{PREDECESSOR} -> mvp-0.33" in result.output
    explicit = create_placement_vault(tmp_path / "explicit", version="mvp-0.24")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(explicit.root), "--to", TARGET])
    assert result.exit_code == 0, result.output
    assert load_vault(explicit.root).config.algorithms.algorithm_version == TARGET


# -- a failed, interrupted or contended activation (review F1) ------------------------------------


def _whole_database(sqlite_path):
    """Every row of every table: the predecessor's whole state. A writable
    connection opens first, so a hot journal a crash left is rolled back."""

    Repository(sqlite_path).fetch_practice_attempt("none")
    with connect(sqlite_path, read_only=True) as connection:
        tables = [
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        return {
            table: sorted((tuple(row) for row in connection.execute(f'SELECT * FROM "{table}"')), key=repr)
            for table in tables
        }


def _fail_after(real, failure):
    def wrapper(*args, **kwargs):
        real(*args, **kwargs)
        raise failure

    return wrapper


@pytest.mark.parametrize("stage", ["after_rebuild", "during_activation", "after_activation", "at_publication"])
def test_a_failed_activation_leaves_the_predecessor_exactly_as_it_was(tmp_path, monkeypatch, stage):
    """Review F1: a failure at any point before the config names mvp-0.26
    leaves the predecessor's whole database as it was (no hold recorded, no
    learner state replayed, no receipt) and the label at mvp-0.25; the
    upgrade, run again, then succeeds."""

    import learnloop.params.parameter_registry as registry
    import learnloop.regrade_contract_upgrade as upgrade

    paths, vault, repository = _legacy_vault(tmp_path)
    before = _whole_database(paths.sqlite_path)
    failure = OSError(f"injected: {stage}")
    if stage == "after_rebuild":
        monkeypatch.setattr(upgrade, "rebuild_all_derived_state", _fail_after(upgrade.rebuild_all_derived_state, failure))
    elif stage == "during_activation":
        monkeypatch.setattr(upgrade, "activate_p0_projection", _fail_after(upgrade.activate_p0_projection, failure))
    elif stage == "after_activation":
        monkeypatch.setattr(registry, "refresh", _fail_after(registry.refresh, failure))
    else:

        def rename_fails(*_args, **_kwargs):
            raise failure

        monkeypatch.setattr(upgrade, "rewrite_algorithm_version", rename_fails)

    with pytest.raises(OSError, match="injected"):
        upgrade_to_mvp026(paths.root, clock=CLOCK)

    assert load_vault(paths.root).config.algorithms.algorithm_version == PREDECESSOR
    assert _whole_database(paths.sqlite_path) == before
    assert not attempt_grade_held(repository, "att_blind") and not attempt_grade_held(repository, "att_self")
    monkeypatch.undo()
    result = upgrade_to_mvp026(paths.root, clock=CLOCK)
    assert result.upgraded, result.problems
    assert attempt_grade_held(repository, "att_blind") and attempt_grade_held(repository, "att_self")


def test_a_failed_commit_after_publication_restores_the_predecessors_label(tmp_path, monkeypatch):
    """Review F1: the config is published inside the activation's transaction;
    when that transaction then fails to commit (here a deferred foreign key
    the commit checks), the database rolls back and the config is restored to
    mvp-0.25, so the label and the state still agree."""

    import learnloop.params.parameter_registry as registry
    import learnloop.regrade_contract_upgrade as upgrade

    paths, vault, repository = _legacy_vault(tmp_path)
    before = _whole_database(paths.sqlite_path)
    real_refresh = registry.refresh
    real_publish = upgrade.rewrite_algorithm_version
    published: list[str] = []

    def refresh_then_defer_a_broken_key(vault, repository, **kwargs):
        written = real_refresh(vault, repository, **kwargs)
        if published or vault.config.algorithms.algorithm_version != TARGET:
            return written  # the manifest freeze refreshes the predecessor's registry first
        # On the activation's own transaction: checked only at its commit.
        with repository.connection() as connection:
            connection.execute("PRAGMA defer_foreign_keys = ON")
            connection.execute(
                "INSERT INTO grading_evidence (id, attempt_id, criterion_id, points_awarded, grader_tier, created_at) "
                "VALUES ('ge_orphan', 'no_such_attempt', 'setup', 0, 1, '2026-12-01T12:00:00Z')"
            )
        return written

    def publish(*args, **kwargs):
        real_publish(*args, **kwargs)
        published.append(load_vault(paths.root).config.algorithms.algorithm_version)

    monkeypatch.setattr(registry, "refresh", refresh_then_defer_a_broken_key)
    monkeypatch.setattr(upgrade, "rewrite_algorithm_version", publish)
    with pytest.raises(sqlite3.IntegrityError):
        upgrade_to_mvp026(paths.root, clock=CLOCK)

    # The config named the successor, the commit failed, the label was restored.
    assert published == [TARGET, PREDECESSOR]
    assert load_vault(paths.root).config.algorithms.algorithm_version == PREDECESSOR
    assert _whole_database(paths.sqlite_path) == before


@pytest.mark.parametrize("target", ["file", "directory"])
def test_a_failed_publication_fsync_leaves_the_predecessors_label(tmp_path, monkeypatch, target):
    """Re-review F4: the publication's durability steps fail like any other
    step. The config file is fsynced (as the temporary file, before the
    rename) and then its directory (after the rename); whichever fsync
    raises, the transaction rolls back and the config names mvp-0.25 again,
    with no temporary file left beside it; the upgrade, run again, then
    succeeds."""

    import learnloop.regrade_contract_upgrade as upgrade

    paths, vault, repository = _legacy_vault(tmp_path)
    before = _whole_database(paths.sqlite_path)
    real_fsync = os.fsync
    real_publish = upgrade.rewrite_algorithm_version
    published: list[str] = []
    failed: list[int] = []

    def publication_files():
        # The config (or its temporary file) for a file fsync, the vault's
        # directory for a directory fsync; the vault lock's fsync passes.
        if target == "directory":
            return [paths.root]
        return [path for path in (paths.root / "learnloop.toml", paths.root / "learnloop.toml.tmp") if path.exists()]

    def fsync_fails_once(fd):
        status = os.fstat(fd)
        if not failed and any(os.path.samestat(status, path.stat()) for path in publication_files()):
            failed.append(fd)
            raise OSError(f"injected: {target} fsync")
        return real_fsync(fd)

    def publish(*args, **kwargs):
        try:
            real_publish(*args, **kwargs)
        finally:
            published.append(load_vault(paths.root).config.algorithms.algorithm_version)

    monkeypatch.setattr(os, "fsync", fsync_fails_once)
    monkeypatch.setattr(upgrade, "rewrite_algorithm_version", publish)
    with pytest.raises(OSError, match=f"injected: {target} fsync"):
        upgrade_to_mvp026(paths.root, clock=CLOCK)

    assert failed
    assert load_vault(paths.root).config.algorithms.algorithm_version == PREDECESSOR
    assert _whole_database(paths.sqlite_path) == before
    assert not (paths.root / "learnloop.toml.tmp").exists()
    # The file's fsync precedes the rename (nothing to restore); the
    # directory's follows it (the config is restored).
    assert published == ([PREDECESSOR] if target == "file" else [TARGET, PREDECESSOR])
    monkeypatch.undo()
    result = upgrade_to_mvp026(paths.root, clock=CLOCK)
    assert result.upgraded, result.problems
    assert load_vault(paths.root).config.algorithms.algorithm_version == TARGET


_CRASH_AFTER_PUBLICATION = """
import os, sys
from pathlib import Path
import learnloop.regrade_contract_upgrade as upgrade

real = upgrade.rewrite_algorithm_version

def publish_then_die(*args, **kwargs):
    real(*args, **kwargs)
    os._exit(17)  # the process dies: nothing after the rename runs, nothing commits

upgrade.rewrite_algorithm_version = publish_then_die
upgrade.upgrade_to_mvp026(Path(sys.argv[1]))
"""


def test_an_upgrade_interrupted_after_publication_is_resumed(tmp_path):
    """Review F1: a process that dies after the config names mvp-0.26 but
    before the activation commits leaves the successor's label over the
    predecessor's untouched database (the transient state every successor
    leaves until a rebuild, never the reverse). Doctor reports the stale
    derived state, and running the upgrade again completes the activation:
    the state equals an upgrade that was never interrupted."""

    import subprocess
    import sys

    paths, vault, repository = _legacy_vault(tmp_path / "interrupted")
    before = _whole_database(paths.sqlite_path)
    crashed = subprocess.run(
        [sys.executable, "-c", _CRASH_AFTER_PUBLICATION, str(paths.root)],
        capture_output=True, text=True, timeout=600,
    )
    assert crashed.returncode == 17, crashed.stderr

    assert load_vault(paths.root).config.algorithms.algorithm_version == TARGET
    assert _whole_database(paths.sqlite_path) == before
    assert "sql:derived_state_rebuild_stale" in {issue.code for issue in run_doctor(paths.root).issues}

    resumed = upgrade_to_mvp026(paths.root, clock=CLOCK)

    assert (resumed.upgraded, resumed.from_version, resumed.to_version) == (True, TARGET, TARGET), resumed.problems
    [note] = resumed.notes
    assert "completed" in note and "att_blind, att_self" in note
    clean_paths, _vault_, clean = _legacy_vault(tmp_path / "clean")
    upgrade_to_mvp026(clean_paths.root, clock=CLOCK)
    assert _attempt_rows(repository) == _attempt_rows(clean)
    assert _learner_state_snapshot(repository) == _learner_state_snapshot(clean)
    assert repository.latest_derived_state_rebuild()["algorithm_version"] == TARGET
    again = upgrade_to_mvp026(paths.root, clock=CLOCK)
    assert again.upgraded is False and again.problems == [f"vault is already {TARGET}"]


def test_no_writer_interleaves_between_the_scan_and_the_publication(tmp_path, monkeypatch):
    """Review F1, concurrent writers: from the scan of the attempts it holds
    to the config's publication, the activation holds the database's write
    lock (one ``BEGIN IMMEDIATE``) and the vault mutation lock, so no regrade,
    adjudication or item edit lands between what it read and what it
    publishes."""

    import threading

    import learnloop.regrade_contract_upgrade as upgrade
    from learnloop.vault_lock import VaultLockTimeout, vault_mutation_lock

    paths, vault, repository = _legacy_vault(tmp_path)
    observed: dict[str, tuple[bool, bool]] = {}

    def contended():
        other = sqlite3.connect(paths.sqlite_path, timeout=0)
        try:
            other.execute("BEGIN IMMEDIATE")
            other.rollback()
            database_locked = False
        except sqlite3.OperationalError as error:
            database_locked = "locked" in str(error)
        finally:
            other.close()
        vault_locked: list[bool] = []

        def try_vault_lock():
            try:
                with vault_mutation_lock(paths.root, purpose="contender", timeout_s=0):
                    vault_locked.append(False)
            except VaultLockTimeout:
                vault_locked.append(True)

        thread = threading.Thread(target=try_vault_lock)
        thread.start()
        thread.join()
        return database_locked, vault_locked[0]

    real_scan = upgrade.unrecorded_epoch_attempts
    real_publish = upgrade.rewrite_algorithm_version

    def scan(*args, **kwargs):
        observed["scan"] = contended()
        return real_scan(*args, **kwargs)

    def publish(*args, **kwargs):
        observed["publication"] = contended()
        return real_publish(*args, **kwargs)

    monkeypatch.setattr(upgrade, "unrecorded_epoch_attempts", scan)
    monkeypatch.setattr(upgrade, "rewrite_algorithm_version", publish)
    result = upgrade_to_mvp026(paths.root, clock=CLOCK)

    assert result.upgraded, result.problems
    assert observed == {"scan": (True, True), "publication": (True, True)}
    # Released once the activation committed.
    assert contended() == (False, False)


def test_head_fixture_predecessor_to_successor_path(tmp_path):
    """Playbook item 8 on the migration-head fixture (no migration here:
    the successor changes no schema)."""

    root = tmp_path / "head"
    copy_tree_with_databases(HEAD, root)
    from tests.helpers import _set_algorithm_version_at

    _set_algorithm_version_at(root, PREDECESSOR)
    result = upgrade_to_mvp026(root, clock=CLOCK)
    assert result.upgraded, result.problems
    vault = load_vault(root)
    repository = Repository(root / "state.sqlite")
    with sqlite3.connect(root / "state.sqlite") as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    errors = [
        issue for issue in run_doctor(root).issues
        if issue.severity == "error"
        and issue.code.startswith(("sqlite", "diagnosis", "state", "placement", "plan", "router", "learner",
                                   "required_method"))
    ]
    assert errors == []
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    with connect(repository.sqlite_path, read_only=True) as connection:
        second = sorted(tuple(row) for row in connection.execute("SELECT * FROM practice_attempts"))
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    with connect(repository.sqlite_path, read_only=True) as connection:
        assert sorted(tuple(row) for row in connection.execute("SELECT * FROM practice_attempts")) == second
