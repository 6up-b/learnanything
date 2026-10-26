"""Rebuild equivalence (mvp-0.34) + mobile PR-2, landed together onto main.

The rebuild-equivalence stage built its successor on mvp-0.31; the landing
chained it after LP-min (a)'s claim fixes (mvp-0.33). The claim fixes journal
their activation across the config file and the database, and no entry point
serves a vault while that journal stands (``learnloop.activation_journal``).
mvp-0.34's activation is the same kind (one transaction, the config's
publication last), so it journals the same way at the same path: a death
between its publication and its commit is completed by the next guarded open
(every CLI command, the desktop start) or refused with the upgrade message
(a process that installed no completion, every read-only attach). One
completion serves the chain: a journal naming mvp-0.34 is completed by its
upgrade, any other is handed to the claim fixes'.
"""

from __future__ import annotations

import json
import multiprocessing
import os

import pytest

from learnloop.algorithm_versions import CLAIM_FIXES_ALGORITHM_VERSION, REPLAY_LEDGER_ALGORITHM_VERSION
from learnloop.db.repositories import Repository
from learnloop.ops.vault_upgrade import rewrite_algorithm_version
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

from tests.test_rebuild_equivalence import _mastery
from tests.test_rebuild_equivalence_review import _rebuilt, _two_attempt_history

TAG = REPLAY_LEDGER_ALGORITHM_VERSION
PREDECESSOR = CLAIM_FIXES_ALGORITHM_VERSION


@pytest.fixture(autouse=True)
def _cli_process(monkeypatch):
    """This process as the CLI is: importing it installs the completion."""

    from learnloop import activation_journal
    from learnloop.cli.runtime import _complete_interrupted_activation

    monkeypatch.setattr(activation_journal, "_COMPLETER", _complete_interrupted_activation)


def _journal(paths):
    return paths.sqlite_path.with_name(paths.sqlite_path.name + ".claim-fixes-activation")


def _predecessor_with_old_replay(tmp_path, name):
    """A predecessor vault whose last rebuild left the predecessor's replay
    (which differs from live on this history), and the live mastery."""

    paths, vault, repository = _two_attempt_history(tmp_path, name, version=PREDECESSOR)
    live = _mastery(repository)
    assert _rebuilt(vault, repository) != live
    return paths, live


def _interrupted(tmp_path, name):
    """The three facts a death between the publication and the commit leaves:
    the tag's label, the predecessor's database, and the journal naming both."""

    paths, live = _predecessor_with_old_replay(tmp_path, name)
    _journal(paths).write_text(json.dumps({"predecessor": PREDECESSOR, "target": TAG}), encoding="utf-8")
    rewrite_algorithm_version(paths.root / "learnloop.toml", PREDECESSOR, TAG, durable=True)
    return paths, live


def _die_after_publication(root):
    import learnloop.replay_ledger_upgrade as upgrade

    real = upgrade._publish_algorithm_version

    def publish_then_die(*args, **kwargs):
        real(*args, **kwargs)
        os._exit(17)  # no handler runs: the transaction never commits

    upgrade._publish_algorithm_version = publish_then_die
    upgrade.upgrade_to_replay_ledger(root)


def _crash_upgrade(paths):
    process = multiprocessing.get_context("fork").Process(target=_die_after_publication, args=(paths.root,))
    process.start()
    process.join(60)
    assert process.exitcode == 17


def _repository_mastery(paths):
    return _mastery(Repository(paths.sqlite_path))


def _open_vault_repository(paths):
    from learnloop.vault.repository import open_vault_repository

    open_vault_repository(paths.root, paths.sqlite_path)


def _vault_repository(paths):
    from learnloop.vault.repository import vault_repository

    vault_repository(VaultPaths(paths.root, load_vault(paths.root).config))


def _sidecar_start(paths):
    from learnloop_sidecar.context import SidecarContext

    SidecarContext().load(paths.root)


def _cli_command(paths):
    from typer.testing import CliRunner

    from learnloop.cli import app

    result = CliRunner().invoke(app, ["backfill-originals", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output


OPENERS = {
    "open_vault_repository": _open_vault_repository,
    "vault_repository": _vault_repository,
    "sidecar_start": _sidecar_start,
    "cli_command": _cli_command,
}


@pytest.mark.filterwarnings("ignore:This process .* is multi-threaded:DeprecationWarning")
def test_a_real_death_after_the_publication_is_journalled_and_the_next_cli_command_completes_it(tmp_path):
    from learnloop.replay_ledger_upgrade import upgrade_to_replay_ledger

    paths, live = _predecessor_with_old_replay(tmp_path, "crashed")
    before = _repository_mastery(paths)
    _crash_upgrade(paths)
    assert load_vault(paths.root).config.algorithms.algorithm_version == TAG
    assert _journal(paths).exists()
    with sqlite3_connection(paths) as connection:  # the predecessor's database, untouched
        assert _rows(connection) == before

    _cli_command(paths)

    assert not _journal(paths).exists()
    assert _repository_mastery(paths) == live
    again = upgrade_to_replay_ledger(paths.root)
    assert not again.upgraded and again.problems == [f"vault is already {TAG}"]


@pytest.mark.parametrize("opener", sorted(OPENERS))
def test_every_opener_that_may_write_completes_an_interrupted_mvp034_activation_first(tmp_path, opener):
    paths, live = _interrupted(tmp_path, "interrupted")
    with sqlite3_connection(paths) as connection:
        assert _rows(connection) != live

    OPENERS[opener](paths)

    assert not _journal(paths).exists()
    assert _repository_mastery(paths) == live
    assert Repository(paths.sqlite_path).has_whole_vault_rebuild(algorithm_version=TAG)


def test_without_a_completion_the_opener_and_every_attach_refuse_with_the_upgrade_message(tmp_path, monkeypatch):
    from learnloop import activation_journal

    paths, live = _interrupted(tmp_path, "interrupted")
    monkeypatch.setattr(activation_journal, "_COMPLETER", None)
    with sqlite3_connection(paths) as connection:
        before = _rows(connection)

    with pytest.raises(activation_journal.InterruptedActivation, match=f"learnloop upgrade --to {TAG}"):
        _open_vault_repository(paths)
    for attach in (lambda: Repository.attach(paths.sqlite_path, read_only=True), lambda: Repository(paths.sqlite_path)):
        with pytest.raises(activation_journal.InterruptedActivation, match=f"learnloop upgrade --to {TAG}"):
            attach()
    with sqlite3_connection(paths) as connection:
        assert _rows(connection) == before
    assert _journal(paths).exists()


def test_the_upgrade_completes_its_own_journal(tmp_path):
    from learnloop.replay_ledger_upgrade import upgrade_to_replay_ledger

    paths, live = _interrupted(tmp_path, "interrupted")
    result = upgrade_to_replay_ledger(paths.root)
    assert result.upgraded and result.notes == [f"completed the interrupted activation of {TAG}"]
    assert not _journal(paths).exists() and _repository_mastery(paths) == live


def test_a_failure_after_the_rename_leaves_the_predecessor_and_no_journal(tmp_path, monkeypatch):
    import learnloop.replay_ledger_upgrade as upgrade

    paths, live = _predecessor_with_old_replay(tmp_path, "vault")
    before = _repository_mastery(paths)
    real = upgrade._publish_algorithm_version
    calls = []

    def publish_then_fail(config_path, from_version, to_version, **kwargs):
        calls.append((from_version, to_version))
        real(config_path, from_version, to_version, **kwargs)
        if len(calls) == 1:
            raise OSError("injected failure after the rename")

    monkeypatch.setattr(upgrade, "_publish_algorithm_version", publish_then_fail)
    with pytest.raises(OSError, match="injected"):
        upgrade.upgrade_to_replay_ledger(paths.root)
    assert calls == [(PREDECESSOR, TAG), (TAG, PREDECESSOR)]
    assert load_vault(paths.root).config.algorithms.algorithm_version == PREDECESSOR
    assert not _journal(paths).exists()
    assert _repository_mastery(paths) == before != live


def test_a_claim_fixes_journal_is_handed_to_its_own_upgrade_then_the_tag_activates(tmp_path):
    """A death in the chain's mvp-0.33 step: the dispatcher hands that journal
    to the claim fixes' completion, and the upgrade then activates mvp-0.34."""

    from learnloop.replay_ledger_upgrade import complete_interrupted_activation, upgrade_to_replay_ledger
    from tests.test_lp_claim_fixes_rereview import _interrupted as claim_fixes_interrupted

    paths = claim_fixes_interrupted(tmp_path, "lp")
    assert load_vault(paths.root).config.algorithms.algorithm_version == PREDECESSOR
    assert _journal(paths).exists()

    assert complete_interrupted_activation(paths.root) == PREDECESSOR
    assert not _journal(paths).exists()
    assert complete_interrupted_activation(paths.root) is None

    result = upgrade_to_replay_ledger(paths.root)
    assert result.upgraded and (result.from_version, result.to_version) == (PREDECESSOR, TAG)
    assert not _journal(paths).exists()


def test_a_torn_journal_at_the_predecessor_is_removed_and_nothing_replays(tmp_path):
    from learnloop.replay_ledger_upgrade import complete_interrupted_activation

    paths, _live = _predecessor_with_old_replay(tmp_path, "torn")
    before = _repository_mastery(paths)
    _journal(paths).write_text('{"predecessor": "mvp-0.3', encoding="utf-8")
    assert complete_interrupted_activation(paths.root) is None
    assert not _journal(paths).exists()
    assert load_vault(paths.root).config.algorithms.algorithm_version == PREDECESSOR
    assert _repository_mastery(paths) == before


# ── helpers reading the database without any LearnLoop opener ───────────────

def sqlite3_connection(paths):
    import contextlib
    import sqlite3

    return contextlib.closing(sqlite3.connect(paths.sqlite_path))


def _rows(connection):
    return {
        row[0]: (row[1], row[2], row[3], row[4])
        for row in connection.execute(
            "SELECT learning_object_id, logit_mean, logit_variance, evidence_count, last_evidence_at "
            "FROM learning_object_mastery"
        )
    }
