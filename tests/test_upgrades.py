"""The upgrade table (``learnloop.ops.upgrades``; ADR-019; playbook steps 3 and 8), every link on one small vault.

Each test runs once per row of ``UPGRADES``: a link activates from its predecessor in one transaction, writes its
journal before the config's publication and publishes last, recovers from a death at each point, refuses a jump,
re-runs idempotently, and leaves the predecessor's config readable when preparation fails. Every opener that may
write completes an interrupted activation; every other attach refuses it. The AD guard's denial mark is
``tests/test_ad_denial_log.py``'s, over the same rows. Fakes only; no model call.
"""

from __future__ import annotations

import json
import multiprocessing
import os
import re
import sqlite3
import subprocess
import sys
import tomllib
from contextlib import closing
from datetime import timedelta

import pytest
from typer.testing import CliRunner

from learnloop import activation_journal
from learnloop.activation_journal import InterruptedActivation, journal_path
from learnloop.algorithm_versions import (
    FACET_BELIEF_FIX_ALGORITHM_VERSION,
    LATEST_ALGORITHM_VERSION,
    OLDEST_SUPPORTED,
    SUCCESSOR_CHAIN,
)
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.cli import app
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ops import upgrades
from learnloop.ops.upgrades import (
    UPGRADES,
    Activation,
    Link,
    idempotent_projection,
    targets,
    upgrade,
    whole_vault_rebuild,
)
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.repository import open_vault_repository, vault_repository
from learnloop.version_floor import PRE_FLOOR_TAG

from tests.helpers import NOW, create_basic_vault, set_algorithm_version

#: One row per link: how it activates. A successor adds its row here and in ``UPGRADES``.
EXPECTED_ACTIVATIONS = {
    FACET_BELIEF_FIX_ALGORITHM_VERSION: whole_vault_rebuild,
}

LINKS = pytest.mark.parametrize("link", UPGRADES, ids=lambda link: link.tag)
ITEM_ID = "pi_svd_define_001"


@pytest.fixture(autouse=True)
def _cli_process(monkeypatch):
    """This process as the CLI is: the table's completion is installed."""

    monkeypatch.setattr(activation_journal, "_COMPLETER", upgrades.complete_interrupted_activation)


def _vault_at(tmp_path, tag, name="vault"):
    """The small vault at ``tag`` with a little history (two answers), so an activation has state to derive."""

    paths = create_basic_vault(tmp_path / name)
    set_algorithm_version(paths, tag)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    for offset, (answer, attempt_type) in enumerate(
        [("I do not know", "dont_know"), ("SVD factors a matrix as U Sigma V transpose.", "independent_attempt")]
    ):
        complete_self_graded_attempt(
            vault, repository, AttemptDraft(ITEM_ID, answer, attempt_type=attempt_type),
            SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
            clock=FrozenClock(NOW + timedelta(minutes=offset)),
        )
    return paths


def _tag(paths) -> str:
    return load_vault(paths.root).config.algorithms.algorithm_version


def _journal(paths):
    return journal_path(paths.sqlite_path)


def _committed(paths, link) -> bool:
    # Read as the activation's own writer does, so a standing journal does not refuse the read.
    with activation_journal.completing_activation():
        return link.activate.committed(Repository(paths.sqlite_path), link.tag)


def _receipts(paths, tag) -> int:
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM derived_state_rebuilds WHERE algorithm_version = ?", (tag,)
        ).fetchone()[0]


def _state(paths) -> dict:
    """What an activation derives, without its write times: mastery and the facet belief."""

    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        mastery = connection.execute(
            "SELECT learning_object_id, logit_mean, logit_variance, evidence_count FROM learning_object_mastery "
            "ORDER BY learning_object_id"
        ).fetchall()
        recall = connection.execute(
            "SELECT facet_id, capability_key, practice_item_id, recall_mean, recall_variance, consecutive_failures "
            "FROM facet_recall_state ORDER BY facet_id, capability_key, practice_item_id"
        ).fetchall()
    return {"mastery": mastery, "recall": recall}


def _interrupted(tmp_path, link, name="interrupted"):
    """The state a death between the publication and the commit leaves: the tag's label over the predecessor's
    database, with the journal (``test_a_real_death_*`` produces it with a real death)."""

    paths = _vault_at(tmp_path, link.predecessor, name)
    upgrades.write_activation_journal(_journal(paths), link.predecessor, link.tag)
    upgrades.rewrite_algorithm_version(paths.root / "learnloop.toml", link.predecessor, link.tag, durable=True)
    return paths


def _clean(tmp_path, link):
    paths = _vault_at(tmp_path, link.predecessor, "clean")
    assert upgrade(paths.root, to=link.tag).upgraded
    return paths


# -- the table -------------------------------------------------------------------------------------------------


def test_the_table_is_the_chain_from_the_floor_one_row_per_tag():
    chain = SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(OLDEST_SUPPORTED) + 1:]
    assert targets() == chain
    assert UPGRADES[0].predecessor == OLDEST_SUPPORTED
    assert all(earlier.tag == later.predecessor for earlier, later in zip(UPGRADES, UPGRADES[1:], strict=False))
    assert {link.tag: link.activate for link in UPGRADES} == EXPECTED_ACTIVATIONS


# -- activation, idempotence, jumps ----------------------------------------------------------------------------


@LINKS
def test_a_link_activates_from_its_predecessor_and_a_rerun_does_nothing(tmp_path, link):
    paths = _vault_at(tmp_path, link.predecessor)
    result = upgrade(paths.root, to=link.tag)
    assert result.upgraded and (result.from_version, result.to_version) == (link.predecessor, link.tag)
    assert _tag(paths) == link.tag and _committed(paths, link) and not _journal(paths).exists()
    receipts = _receipts(paths, link.tag)

    again = upgrade(paths.root, to=link.tag)
    assert not again.upgraded and again.problems == [f"vault is already {link.tag}"]
    assert _receipts(paths, link.tag) == receipts


@LINKS
def test_a_vault_born_at_the_tag_completes_its_activation_once(tmp_path, link):
    paths = _vault_at(tmp_path, link.tag)
    assert not _committed(paths, link)
    first = upgrade(paths.root, to=link.tag)
    assert first.upgraded and first.notes == [f"completed the activation of {link.tag} ({link.activate.description})"]
    assert _committed(paths, link)
    again = upgrade(paths.root, to=link.tag)
    assert not again.upgraded and again.problems == [f"vault is already {link.tag}"]


@LINKS
def test_the_floor_reaches_each_tag_through_the_table(tmp_path, link):
    paths = _vault_at(tmp_path, OLDEST_SUPPORTED)
    result = upgrade(paths.root, to=link.tag)
    assert result.upgraded and (result.from_version, result.to_version) == (OLDEST_SUPPORTED, link.tag)
    walked = UPGRADES[:UPGRADES.index(link) + 1]
    assert all(_committed(paths, step) for step in walked)


@LINKS
def test_a_jump_is_refused_and_nothing_changes(tmp_path, link):
    # A vault below the floor: refused with the route through pre-floor, at the table and at the command.
    below = SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(link.predecessor) - 1]
    paths = create_basic_vault(tmp_path / "below")
    re_tag = paths.root / "learnloop.toml"
    re_tag.write_text(re.sub(r'algorithm_version = "[^"]+"', f'algorithm_version = "{below}"',
                             re_tag.read_text("utf-8"), count=1), encoding="utf-8")
    refused = upgrade(paths.root, to=link.tag)
    assert not refused.upgraded and refused.from_version == below
    assert PRE_FLOOR_TAG in refused.problems[0] and f"learnloop upgrade --vault {paths.root.resolve()}" in (
        refused.problems[0])
    command = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root), "--to", link.tag])
    assert command.exit_code == 1 and PRE_FLOOR_TAG in command.output, command.output
    assert f'algorithm_version = "{below}"' in re_tag.read_text("utf-8")

    # A vault at a tag the table has no row from (a newer code's vault): refused, unchanged.
    newer = create_basic_vault(tmp_path / "newer")
    set_algorithm_version(newer, "mvp-0.9999")
    result = upgrade(newer.root, to=link.tag)
    assert not result.upgraded and result.problems == [
        f"cannot upgrade from 'mvp-0.9999' to {link.tag!r}: only {UPGRADES[0].predecessor!r} to "
        f"{link.predecessor!r} upgrade to it"
    ]
    assert _tag(newer) == "mvp-0.9999"


def test_a_target_the_table_has_no_row_for_is_refused_before_any_step(tmp_path):
    paths = _vault_at(tmp_path, OLDEST_SUPPORTED)
    for target in (OLDEST_SUPPORTED, "mvp-0.9", "mvp-0.9999"):
        result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root), "--to", target])
        assert result.exit_code == 2, result.output
        assert f"Unknown target version {target!r}" in result.output and PRE_FLOOR_TAG in result.output
    assert _tag(paths) == OLDEST_SUPPORTED


@LINKS
def test_the_command_reaches_the_tag_by_name_and_the_latest_by_default(tmp_path, link):
    paths = _vault_at(tmp_path, link.predecessor)
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root), "--to", link.tag])
    assert result.exit_code == 0, result.output
    assert f"Upgraded vault: {link.predecessor} -> {link.tag}" in result.output
    floor = _vault_at(tmp_path, OLDEST_SUPPORTED, "default")
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(floor.root)])
    assert result.exit_code == 0, result.output
    assert _tag(floor) == LATEST_ALGORITHM_VERSION


# -- the journal before the publication, the publication last ----------------------------------------------------


@LINKS
def test_the_journal_is_written_before_the_publication_and_the_commit_follows_it(tmp_path, monkeypatch, link):
    paths = _vault_at(tmp_path, link.predecessor)
    real = upgrades.publish_algorithm_version
    seen: dict = {}

    def publish(config_path, from_version, to_version, **kwargs):
        seen["journal"] = json.loads(_journal(paths).read_text("utf-8"))
        seen["config before"] = _tag(paths)
        # Another connection does not see the activation yet: the commit follows the publication.
        seen["committed before"] = _committed(paths, link)
        real(config_path, from_version, to_version, **kwargs)

    monkeypatch.setattr(upgrades, "publish_algorithm_version", publish)
    assert upgrade(paths.root, to=link.tag).upgraded
    assert seen == {"journal": {"predecessor": link.predecessor, "target": link.tag},
                    "config before": link.predecessor, "committed before": False}
    assert _committed(paths, link) and not _journal(paths).exists()


# -- the publication sets the [algorithms] setting, and only it --------------------------------------------------


@LINKS
@pytest.mark.parametrize("decoy", ["comment", "another table"])
def test_the_publication_changes_the_setting_not_the_same_text_elsewhere(tmp_path, link, decoy):
    paths = _vault_at(tmp_path, link.predecessor)
    config = paths.root / "learnloop.toml"
    line = f'algorithm_version = "{link.predecessor}"'
    decoy_text = f"# {line}\n" if decoy == "comment" else f"[notes]\n{line}\n\n"
    text = config.read_text("utf-8")
    config.write_text(text.replace("[algorithms]\n", decoy_text + "[algorithms]\n", 1), encoding="utf-8")

    assert upgrade(paths.root, to=link.tag).upgraded

    assert _tag(paths) == link.tag and _committed(paths, link) and not _journal(paths).exists()
    published = config.read_text("utf-8")
    assert decoy_text + "[algorithms]\n" in published
    if decoy == "another table":
        assert tomllib.loads(published)["notes"] == {"algorithm_version": link.predecessor}
    # Nothing else in the file moved: the one setting's value is the only difference.
    assert published.replace(f'"{link.tag}"', f'"{link.predecessor}"') == text.replace(
        "[algorithms]\n", decoy_text + "[algorithms]\n", 1)


# -- an old config stays readable when preparation fails ---------------------------------------------------------


def _fail(*_args, **_kwargs):
    raise OSError("disk")


@LINKS
@pytest.mark.parametrize("stage", ["activation", "before the rename", "after the rename", "renamed without the tag"])
def test_a_failure_before_the_commit_leaves_the_predecessor_readable_and_no_journal(tmp_path, monkeypatch, link,
                                                                                   stage):
    paths = _vault_at(tmp_path, link.predecessor)
    before = _state(paths)
    links = None
    if stage == "activation":
        links = [Link(link.tag, Activation(link.activate.description, _fail, link.activate.committed))]
    else:
        real = upgrades.publish_algorithm_version

        def publish(config_path, from_version, to_version, *, renamed=None):
            if to_version != link.tag:  # the failure's own restoration of the predecessor's label
                return real(config_path, from_version, to_version, renamed=renamed)
            if stage == "before the rename":
                raise OSError("disk")
            if stage == "renamed without the tag":
                # A rename that landed a file still naming the predecessor: only reading it back can tell.
                if renamed is not None:
                    renamed()
                return None
            real(config_path, from_version, to_version, renamed=renamed)
            raise OSError("directory fsync")

        monkeypatch.setattr(upgrades, "publish_algorithm_version", publish)
    with pytest.raises(upgrades.UnpublishedTag if stage == "renamed without the tag" else OSError):
        upgrade(paths.root, to=link.tag, links=links)
    monkeypatch.undo()
    monkeypatch.setattr(activation_journal, "_COMPLETER", upgrades.complete_interrupted_activation)

    assert _tag(paths) == link.predecessor and not _journal(paths).exists()
    assert not _committed(paths, link) and _state(paths) == before
    # The predecessor's config serves, and the upgrade runs again.
    open_vault_repository(paths.root, paths.sqlite_path)
    assert upgrade(paths.root, to=link.tag).upgraded


# -- recovery after death at each point --------------------------------------------------------------------------


def _die(root, tag, before_publication):
    real = upgrades.publish_algorithm_version

    def publish_then_die(*args, **kwargs):
        if not before_publication:
            real(*args, **kwargs)
        os._exit(17)  # no handler runs: the transaction never commits

    upgrades.publish_algorithm_version = publish_then_die
    upgrade(root, to=tag)


def _crash(paths, link, *, before_publication):
    process = multiprocessing.get_context("fork").Process(
        target=_die, args=(paths.root, link.tag, before_publication)
    )
    process.start()
    process.join(120)
    assert process.exitcode == 17


def _cli_command(paths):
    result = CliRunner().invoke(app, ["backfill-originals", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output


@pytest.mark.filterwarnings("ignore:This process .* is multi-threaded:DeprecationWarning")
@LINKS
def test_a_real_death_after_the_publication_is_completed_by_the_next_command(tmp_path, link):
    clean = _state(_clean(tmp_path, link))
    paths = _vault_at(tmp_path, link.predecessor, "crashed")
    before = _state(paths)
    _crash(paths, link, before_publication=False)
    assert _tag(paths) == link.tag and _journal(paths).exists()
    assert _state(paths) == before and not _committed(paths, link)  # the predecessor's database, untouched

    _cli_command(paths)

    assert not _journal(paths).exists() and _committed(paths, link)
    assert _state(paths) == clean
    again = upgrade(paths.root, to=link.tag)
    assert not again.upgraded and again.problems == [f"vault is already {link.tag}"]


@pytest.mark.filterwarnings("ignore:This process .* is multi-threaded:DeprecationWarning")
@LINKS
def test_a_real_death_after_the_journal_before_the_publication_leaves_the_predecessor(tmp_path, link):
    paths = _vault_at(tmp_path, link.predecessor, "crashed")
    before = _state(paths)
    _crash(paths, link, before_publication=True)
    assert _tag(paths) == link.predecessor and _journal(paths).exists()

    _cli_command(paths)

    # The config never named the tag: nothing of the activation is in force, and the journal goes.
    assert not _journal(paths).exists() and not _committed(paths, link)
    assert _tag(paths) == link.predecessor and _state(paths) == before
    assert upgrade(paths.root, to=link.tag).upgraded


@LINKS
def test_a_journal_left_after_the_commit_is_just_removed(tmp_path, link):
    paths = _clean(tmp_path, link)
    receipts = _receipts(paths, link.tag)
    upgrades.write_activation_journal(_journal(paths), link.predecessor, link.tag)

    open_vault_repository(paths.root, paths.sqlite_path)

    assert not _journal(paths).exists() and _receipts(paths, link.tag) == receipts


@LINKS
def test_a_torn_journal_is_removed_and_nothing_activates(tmp_path, link):
    paths = _vault_at(tmp_path, link.predecessor)
    before = _state(paths)
    _journal(paths).write_text('{"predecessor": "mvp-0.', encoding="utf-8")

    open_vault_repository(paths.root, paths.sqlite_path)

    assert not _journal(paths).exists() and _tag(paths) == link.predecessor
    assert not _committed(paths, link) and _state(paths) == before


@LINKS
def test_the_upgrade_command_completes_its_own_interrupted_activation(tmp_path, link):
    clean = _state(_clean(tmp_path, link))
    paths = _interrupted(tmp_path, link)
    result = upgrade(paths.root, to=link.tag)
    assert result.upgraded and result.notes == [f"completed the interrupted activation of {link.tag}"]
    assert not _journal(paths).exists() and _state(paths) == clean


# -- the openers -------------------------------------------------------------------------------------------------


def _open_vault_repository(paths):
    open_vault_repository(paths.root, paths.sqlite_path)


def _vault_repository(paths):
    vault_repository(VaultPaths(paths.root, load_vault(paths.root).config))


def _sidecar_start(paths):
    from learnloop_sidecar.context import SidecarContext

    SidecarContext().load(paths.root)


OPENERS = {
    "open_vault_repository": _open_vault_repository,
    "vault_repository": _vault_repository,
    "sidecar_start": _sidecar_start,
    "cli_command": _cli_command,
}


@LINKS
@pytest.mark.parametrize("opener", sorted(OPENERS))
def test_every_opener_that_may_write_completes_an_interrupted_activation_first(tmp_path, link, opener):
    clean = _state(_clean(tmp_path, link))
    paths = _interrupted(tmp_path, link)

    OPENERS[opener](paths)

    assert not _journal(paths).exists() and _committed(paths, link)
    assert _state(paths) == clean and _tag(paths) == link.tag


@LINKS
@pytest.mark.parametrize("opener", sorted(OPENERS))
def test_an_activation_that_cannot_complete_stops_the_opener(tmp_path, monkeypatch, link, opener):
    paths = _interrupted(tmp_path, link)
    before = _state(paths)
    failing = Link(link.tag, Activation(link.activate.description, _fail, link.activate.committed))
    monkeypatch.setattr(upgrades, "UPGRADES", (failing,))

    if opener == "cli_command":
        result = CliRunner().invoke(app, ["backfill-originals", "--vault", str(paths.root)])
        assert result.exit_code != 0 and isinstance(result.exception, InterruptedActivation)
    else:
        with pytest.raises(InterruptedActivation, match=f"learnloop upgrade --to {link.tag}"):
            OPENERS[opener](paths)
    # Nothing served, nothing half-applied: the journal stays for the next try.
    assert _state(paths) == before and _journal(paths).exists()


@LINKS
@pytest.mark.parametrize("opener", ["open_vault_repository", "vault_repository"])
def test_an_opener_in_a_process_that_cannot_complete_refuses(tmp_path, monkeypatch, link, opener):
    """A TUI or a script installs no completion: its opener serves nothing."""

    paths = _interrupted(tmp_path, link)
    before = _state(paths)
    monkeypatch.setattr(activation_journal, "_COMPLETER", None)
    with pytest.raises(InterruptedActivation, match=f"learnloop upgrade --to {link.tag}"):
        OPENERS[opener](paths)
    assert _state(paths) == before and _journal(paths).exists()


_COMPLETE_IN_A_FRESH_PROCESS = """
import sys
from pathlib import Path
import {module}
from learnloop import activation_journal
try:
    activation_journal.complete(Path(sys.argv[1]), Path(sys.argv[2]))
except activation_journal.InterruptedActivation:
    print("refused")
else:
    print("completed")
"""


@LINKS
@pytest.mark.parametrize(
    ("module", "completes"),
    [("learnloop.cli", True), ("learnloop_sidecar.context", True), ("learnloop.vault.repository", False)],
)
def test_the_cli_and_the_sidecar_install_the_tables_completion(tmp_path, link, module, completes):
    """Importing the CLI or the sidecar installs a completion that finishes the table's journal; the vault layer
    alone installs none."""

    paths = _interrupted(tmp_path, link)
    result = subprocess.run(
        [sys.executable, "-c", _COMPLETE_IN_A_FRESH_PROCESS.format(module=module), str(paths.root),
         str(paths.sqlite_path)],
        capture_output=True, text=True, check=True, timeout=300,
    )
    assert result.stdout.strip().splitlines()[-1] == ("completed" if completes else "refused"), result.stderr
    assert _journal(paths).exists() is not completes
    assert _committed(paths, link) is completes


@LINKS
def test_attaches_that_never_write_refuse_while_the_journal_stands(tmp_path, link):
    from learnloop.remote.runtime import RemoteRuntime, SchemaMismatch

    paths = _interrupted(tmp_path, link)
    for attach in (lambda: Repository.attach(paths.sqlite_path, read_only=True), lambda: Repository(paths.sqlite_path)):
        with pytest.raises(InterruptedActivation, match=f"learnloop upgrade --to {link.tag}"):
            attach()
    result = CliRunner().invoke(app, ["gaps", "list", "--vault", str(paths.root), "--json"])
    assert result.exit_code != 0 and isinstance(result.exception, InterruptedActivation)
    with pytest.raises(SchemaMismatch, match=f"learnloop upgrade --to {link.tag}"):
        RemoteRuntime.attach(paths.root, load_environment=False)


@LINKS
def test_an_mcp_server_already_attached_stops_serving_when_a_journal_appears(tmp_path, link):
    from learnloop.remote.runtime import RemoteRuntime, SchemaMismatch

    paths = _clean(tmp_path, link)
    runtime = RemoteRuntime.attach(paths.root, load_environment=False)
    assert runtime.vault() is not None
    upgrades.write_activation_journal(_journal(paths), link.predecessor, link.tag)
    with pytest.raises(SchemaMismatch, match=f"learnloop upgrade --to {link.tag}"):
        runtime.vault()


@LINKS
def test_the_phone_host_refuses_to_start_while_the_journal_stands(tmp_path, link):
    pytest.importorskip("starlette")
    from learnloop_mobile.config import MobileConfig
    from learnloop_mobile.host import SchemaMismatch, attach

    paths = _interrupted(tmp_path, link)
    config = MobileConfig(enabled=True, vault=paths.root, hostname="carson.example.ts.net", owner_login="owner")
    with pytest.raises(SchemaMismatch, match=f"learnloop upgrade --to {link.tag}"):
        attach(config)


# -- the two activations ------------------------------------------------------------------------------------------


@pytest.mark.parametrize("activation", [idempotent_projection, whole_vault_rebuild], ids=["projection", "rebuild"])
def test_each_activation_kind_commits_its_own_receipt_once(tmp_path, activation):
    """Each kind a row may name, on the head's link: its receipt marks exactly a committed activation."""

    link = Link(LATEST_ALGORITHM_VERSION, activation)
    paths = _vault_at(tmp_path, link.predecessor)
    assert not activation.committed(Repository(paths.sqlite_path), link.tag)
    assert upgrade(paths.root, to=link.tag, links=[link]).upgraded
    assert activation.committed(Repository(paths.sqlite_path), link.tag)
    receipts = _receipts(paths, link.tag)
    again = upgrade(paths.root, to=link.tag, links=[link])
    assert again.problems == [f"vault is already {link.tag}"] and _receipts(paths, link.tag) == receipts
