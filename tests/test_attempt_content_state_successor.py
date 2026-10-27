"""Mobile PR-4's successor (mvp-0.37; mvp-0.36 on its branch, renumbered at landing after the kept
replaced claims' mvp-0.36): a live attempt writes only its scheduling columns.

Codex review F4 (``docs/reviews/mobile-pr3-pr4-codex-review.md``): the PR-4
race fix (``tests/test_attempt_content_state_race.py``) also changes serving
WITHOUT a concurrent writer. An item whose ``practice_item_state`` row is
closed while its YAML is active (review-parked, measurement-superseded, a
deactivation replay keeps) used to be reopened by an attempt on it, until the
next content sync re-decided the flag; with the fix it stays closed, so the
Today queue no longer serves it in that window. That is a change to which
items are served (the playbook's 2026-10-17 rule), so it is a successor with a
kill switch:

* at the tag with ``practice.attempt_keeps_content_state`` on, the attempt
  keeps the closed row closed and its content hash as content sync wrote it;
* off, or below the tag (an mvp-0.36 vault), the attempt writes the whole
  row exactly as the predecessor (the row reopens and the item is served);
* replay keeps its full upsert, so a same-version rebuild reproduces the live
  row at every setting (rebuild equivalence);
* the upgrade is the chain's next journalled link.

Fakes only: self-graded attempts, no model call.
"""

from __future__ import annotations

import json
from datetime import timedelta

import pytest
from typer.testing import CliRunner

from learnloop.algorithm_versions import (
    ATTEMPT_CONTENT_STATE_ALGORITHM_VERSION,
    ATTEMPT_CONTENT_STATE_VERSIONS,
    LATEST_ALGORITHM_VERSION,
    ONE_ASK_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
    SUPERSEDED_CLAIMS_ALGORITHM_VERSION,
)
from learnloop.attempts.attempts import (
    AttemptDraft,
    SelfGradeInput,
    attempt_keeps_content_state,
    complete_self_graded_attempt,
)
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ops.vault_upgrade import rewrite_algorithm_version
from learnloop.substrate.replay import rebuild_derived_state
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, append_config_toml, create_placement_vault

TAG = ATTEMPT_CONTENT_STATE_ALGORITHM_VERSION
PREDECESSOR = SUPERSEDED_CLAIMS_ALGORITHM_VERSION
ITEM = "pi_svd_define_001"
CLOCK = FrozenClock(NOW + timedelta(hours=1))


@pytest.fixture(autouse=True)
def _cli_process(monkeypatch):
    """This process as the CLI is: importing it installs the completion."""

    from learnloop import activation_journal
    from learnloop.cli.runtime import _complete_interrupted_activation

    monkeypatch.setattr(activation_journal, "_COMPLETER", _complete_interrupted_activation)


def _vault_at(tmp_path, name, version, *, switch: bool | None = None):
    paths = create_placement_vault(tmp_path / name, version=version)
    if switch is not None:
        append_config_toml(paths.root, f"\n[practice]\nattempt_keeps_content_state = {str(switch).lower()}\n")
    return paths


def _version(paths) -> str:
    return load_vault(paths.root).config.algorithms.algorithm_version


def _journal(paths):
    return paths.sqlite_path.with_name(paths.sqlite_path.name + ".claim-fixes-activation")


def _activated(paths, version=TAG) -> bool:
    import sqlite3
    from contextlib import closing

    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        return connection.execute(
            "SELECT 1 FROM derived_state_rebuilds WHERE scope = 'p0_projection_activation' AND algorithm_version = ?",
            (version,),
        ).fetchone() is not None


def _answer(vault, repository) -> None:
    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=ITEM,
            learner_answer_md="SVD factors a matrix into U, Sigma and V transpose.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=4),
        clock=CLOCK,
    )


def _served(vault, repository) -> bool:
    from learnloop.scheduling.serving_exclusions import routine_serving_exclusions, routine_withhold_reason

    state = repository.practice_item_states().get(ITEM)
    reason = routine_withhold_reason(
        vault, vault.practice_items[ITEM], state, routine_serving_exclusions(vault, repository)
    )
    return reason != "inactive_state"


def _closed_then_answered(paths):
    """The non-concurrent case F4 names: the row is closed while the YAML is
    active (a deactivation the sync rule keeps), then an answer on the item is
    submitted with no other writer in between."""

    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    repository.set_practice_item_active(ITEM, active=False, clock=FrozenClock(NOW))
    before = repository.practice_item_state(ITEM)
    assert before.active is False and vault.practice_items[ITEM].status == "active"
    _answer(vault, repository)
    return vault, repository, before


# -- the chain -------------------------------------------------------------------------------------


def test_mvp037_is_one_constant_after_mvp036():
    from learnloop.attempt_content_state_upgrade import PREDECESSOR as UPGRADE_PREDECESSOR
    from learnloop.config.schema import PracticeConfig
    from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, defaults_fingerprint_for_version
    from learnloop.params.parameter_registry import classify_config_path

    # Built as mvp-0.36 after mvp-0.35; the kept replaced claims' mvp-0.36 landed first, so the landing renumbered it.
    # The cold-retry reschedule's mvp-0.38 follows it as the latest (and keeps it).
    assert SUCCESSOR_CHAIN[-4:-1] == (ONE_ASK_ALGORITHM_VERSION, PREDECESSOR, TAG) == ("mvp-0.35", "mvp-0.36", "mvp-0.37")
    assert SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.38" and UPGRADE_PREDECESSOR == PREDECESSOR
    assert ATTEMPT_CONTENT_STATE_VERSIONS == frozenset({TAG, "mvp-0.38"})
    assert PracticeConfig().attempt_keeps_content_state is True
    rule = classify_config_path("practice.attempt_keeps_content_state")
    assert rule is not None and rule.kind == "structural" and "kill switch" in rule.rationale
    for version in SUCCESSOR_CHAIN:
        assert DEFAULTS_SNAPSHOT_BY_ALGORITHM[version] == defaults_fingerprint_for_version(version), version


@pytest.mark.parametrize(("version", "switch", "keeps"), [
    (TAG, None, True), (TAG, False, False), (PREDECESSOR, None, False), (PREDECESSOR, True, False),
], ids=["tag", "tag-switch-off", "predecessor", "predecessor-switch-on"])
def test_the_gate_is_the_tag_and_its_switch(tmp_path, version, switch, keeps):
    paths = _vault_at(tmp_path, "v", version, switch=switch)
    assert attempt_keeps_content_state(load_vault(paths.root)) is keeps


# -- serving without a concurrent writer -------------------------------------------------------------


def test_at_the_tag_an_answer_keeps_a_closed_row_closed_and_out_of_serving(tmp_path):
    paths = _vault_at(tmp_path, "tag", TAG)
    vault, repository, before = _closed_then_answered(paths)

    state = repository.practice_item_state(ITEM)
    assert state.active is False
    assert state.content_hash == before.content_hash
    assert state.last_attempt_at is not None and state.stability is not None and state.due_at is not None
    assert not _served(vault, repository)


@pytest.mark.parametrize(("version", "switch"), [(TAG, False), (PREDECESSOR, None)],
                         ids=["tag-switch-off", "predecessor"])
def test_off_or_below_the_tag_the_answer_reopens_the_row_as_the_predecessor(tmp_path, version, switch):
    paths = _vault_at(tmp_path, "pred", version, switch=switch)
    vault, repository, _before = _closed_then_answered(paths)

    state = repository.practice_item_state(ITEM)
    assert state.active is True  # the predecessor's whole-row upsert
    assert state.last_attempt_at is not None and state.stability is not None
    assert _served(vault, repository)


@pytest.mark.parametrize(("version", "switch"), [(TAG, None), (TAG, False), (PREDECESSOR, None)],
                         ids=["tag", "tag-switch-off", "predecessor"])
def test_a_same_version_rebuild_reproduces_the_live_row(tmp_path, version, switch):
    paths = _vault_at(tmp_path, "rebuild", version, switch=switch)
    vault, repository, _before = _closed_then_answered(paths)
    live = repository.practice_item_state(ITEM)

    rebuild_derived_state(vault, repository, clock=CLOCK)

    rebuilt = repository.practice_item_state(ITEM)
    columns = ("active", "content_hash", "difficulty", "stability", "retrievability", "due_at", "last_attempt_at")
    assert {name: getattr(rebuilt, name) for name in columns} == {name: getattr(live, name) for name in columns}


# -- the upgrade -------------------------------------------------------------------------------------


@pytest.mark.parametrize("start", ["mvp-0.9", "mvp-0.30", "mvp-0.33", "mvp-0.34", "mvp-0.35", "mvp-0.36"])
def test_upgrade_to_mvp037_works_from_supported_versions(tmp_path, start):
    from learnloop.cli import app

    paths = _vault_at(tmp_path, "v", start)
    result = CliRunner().invoke(app, ["upgrade", "--to", TAG, "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert f"{start} -> {TAG}" in result.output
    assert _version(paths) == TAG and _activated(paths) and not _journal(paths).exists()


def test_a_bare_upgrade_targets_the_latest_through_mvp037(tmp_path):
    from learnloop.cli import app

    paths = _vault_at(tmp_path, "v", PREDECESSOR)
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    # The latest is the cold-retry reschedule's mvp-0.38, chained through this tag.
    assert f"{PREDECESSOR} -> {LATEST_ALGORITHM_VERSION}" in result.output
    assert _version(paths) == LATEST_ALGORITHM_VERSION and _activated(paths)


def test_the_upgrade_refuses_a_version_before_the_chain(tmp_path):
    from learnloop.attempt_content_state_upgrade import upgrade_to_attempt_content_state

    paths = _vault_at(tmp_path, "old", "mvp-0.9")
    rewrite_algorithm_version(paths.root / "learnloop.toml", "mvp-0.9", "mvp-0.8", durable=True)
    result = upgrade_to_attempt_content_state(paths.root)
    assert not result.upgraded and _version(paths) == "mvp-0.8"
    assert "cannot upgrade from 'mvp-0.8'" in result.problems[0]


def _interrupted(tmp_path, name):
    paths = _vault_at(tmp_path, name, PREDECESSOR)
    _journal(paths).write_text(json.dumps({"predecessor": PREDECESSOR, "target": TAG}), encoding="utf-8")
    rewrite_algorithm_version(paths.root / "learnloop.toml", PREDECESSOR, TAG, durable=True)
    assert not _activated(paths)
    return paths


def test_the_next_cli_command_completes_an_interrupted_mvp037_activation(tmp_path):
    from learnloop.attempt_content_state_upgrade import upgrade_to_attempt_content_state
    from learnloop.cli import app

    paths = _interrupted(tmp_path, "interrupted")
    result = CliRunner().invoke(app, ["backfill-originals", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert not _journal(paths).exists() and _activated(paths) and _version(paths) == TAG
    again = upgrade_to_attempt_content_state(paths.root)
    assert not again.upgraded and again.problems == [f"vault is already {TAG}"]


def test_the_upgrade_completes_its_own_journal(tmp_path):
    from learnloop.attempt_content_state_upgrade import upgrade_to_attempt_content_state

    paths = _interrupted(tmp_path, "interrupted")
    result = upgrade_to_attempt_content_state(paths.root)
    assert result.upgraded and result.notes == [f"completed the interrupted activation of {TAG}"]
    assert not _journal(paths).exists() and _activated(paths)


def test_a_failure_after_the_rename_leaves_the_predecessor_and_no_journal(tmp_path, monkeypatch):
    import learnloop.attempt_content_state_upgrade as upgrade

    paths = _vault_at(tmp_path, "failing", PREDECESSOR)
    real = upgrade._publish_algorithm_version

    def publish_then_fail(config_path, from_version, to_version, *, renamed=None):
        real(config_path, from_version, to_version, renamed=renamed)
        if to_version == TAG:
            raise OSError("the directory fsync failed")

    monkeypatch.setattr(upgrade, "_publish_algorithm_version", publish_then_fail)
    with pytest.raises(OSError):
        upgrade.upgrade_to_attempt_content_state(paths.root)
    assert _version(paths) == PREDECESSOR and not _journal(paths).exists() and not _activated(paths)


def test_an_mvp035_journal_is_handed_down_the_chain_then_the_tag_activates(tmp_path):
    """An interrupted Reader CA2 (mvp-0.35) activation: this link hands it to
    the kept replaced claims' completion, which hands it to CA2's own."""

    from learnloop.attempt_content_state_upgrade import complete_interrupted_activation, upgrade_to_attempt_content_state
    from tests.test_batch3_landing import _interrupted as ca2_interrupted

    paths = ca2_interrupted(tmp_path, "ca2")
    assert _version(paths) == ONE_ASK_ALGORITHM_VERSION and _journal(paths).exists()
    assert complete_interrupted_activation(paths.root) == ONE_ASK_ALGORITHM_VERSION
    assert not _journal(paths).exists() and complete_interrupted_activation(paths.root) is None
    result = upgrade_to_attempt_content_state(paths.root)
    assert result.upgraded and _version(paths) == TAG and not _journal(paths).exists()
    assert _activated(paths, PREDECESSOR) and _activated(paths)


def _interrupted_predecessor(tmp_path, name):
    """An mvp-0.36 activation (the kept replaced claims) that died after its
    publication and before its commit: the label names mvp-0.36 over an
    mvp-0.35 database, with that link's journal."""

    paths = _vault_at(tmp_path, name, ONE_ASK_ALGORITHM_VERSION)
    _journal(paths).write_text(
        json.dumps({"predecessor": ONE_ASK_ALGORITHM_VERSION, "target": PREDECESSOR}), encoding="utf-8")
    rewrite_algorithm_version(paths.root / "learnloop.toml", ONE_ASK_ALGORITHM_VERSION, PREDECESSOR, durable=True)
    assert not _activated(paths, PREDECESSOR)
    return paths


def test_landing_ii_an_interrupted_mvp036_activation_then_upgrade_to_mvp037_completes_it(tmp_path):
    """Landing interaction (ii): `learnloop upgrade --to mvp-0.37` over an
    interrupted mvp-0.36 activation. The CLI's opener (this link's completion,
    the chain's latest) hands the mvp-0.36 journal to its own link, which
    completes it; the upgrade then activates mvp-0.37 from mvp-0.36."""

    from learnloop.cli import app

    paths = _interrupted_predecessor(tmp_path, "interrupted036")
    result = CliRunner().invoke(app, ["upgrade", "--to", TAG, "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert f"{PREDECESSOR} -> {TAG}" in result.output
    assert _version(paths) == TAG and not _journal(paths).exists()
    assert _activated(paths, PREDECESSOR) and _activated(paths)


def test_landing_ii_without_a_completion_an_attach_refuses_and_the_upgrade_still_completes_it(tmp_path, monkeypatch):
    """Landing interaction (ii), without an installed completion: an attach
    refuses with mvp-0.36's upgrade message and changes nothing (the journal
    is never skipped), and the mvp-0.37 upgrade itself completes the mvp-0.36
    activation first (it reads every link's journal before the version), then
    activates mvp-0.37."""

    from learnloop import activation_journal
    from learnloop.attempt_content_state_upgrade import upgrade_to_attempt_content_state

    paths = _interrupted_predecessor(tmp_path, "refused036")
    monkeypatch.setattr(activation_journal, "_COMPLETER", None)
    with pytest.raises(activation_journal.InterruptedActivation, match=f"learnloop upgrade --to {PREDECESSOR}"):
        Repository(paths.sqlite_path)
    assert _version(paths) == PREDECESSOR and _journal(paths).exists()
    assert not _activated(paths, PREDECESSOR) and not _activated(paths)

    result = upgrade_to_attempt_content_state(paths.root)
    assert result.upgraded and result.from_version == PREDECESSOR and _version(paths) == TAG
    assert not _journal(paths).exists() and _activated(paths, PREDECESSOR) and _activated(paths)
