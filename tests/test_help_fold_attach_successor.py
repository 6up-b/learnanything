"""Follow-ups Nov 2 (b) as the successor mvp-0.42 (Codex review F1; built as mvp-0.41 and renumbered
at its landing after teacher TE1's mvp-0.41, ruling R4;
docs/reviews/followups-nov2-codex-review.md; docs/algorithm-change-playbook.md,
the 2026-10-17 rule: a change to which new attempts are primed is a successor
with a kill switch even when replay is unchanged).

* the tag is ONE constant after mvp-0.41 and the latest; its defaults
  snapshot is recorded; ``hints.fold_follows_attach`` is its kill switch;
* below the tag, or switched off, a keyed submit folds exactly as the
  predecessor (the key's rows in the submit's own session only; no keyed
  attach in the attempt's transaction, H0's attach after the commit), so the
  session rollover case records ``hints_used`` 0 and ``primed`` 0 as before;
* replay re-applies the stored counts (a rebuild changes no attempt) and a
  shadow rebuild is 0/0/0 at the tag with the switch on and off;
* the upgrade is the chain's next journalled link (from its predecessor, or mvp-0.9
  onwards through the chain; from mvp-0.41 now), and the next command completes an interrupted
  activation.

Fakes only; no model call.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing

import pytest
from typer.testing import CliRunner

from learnloop.algorithm_versions import (
    HELP_FOLD_ATTACH_ALGORITHM_VERSION,
    HELP_FOLD_ATTACH_VERSIONS,
    LATEST_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
    TEACHER_ALGORITHM_VERSION,
)
from learnloop.ops.vault_upgrade import rewrite_algorithm_version
from learnloop.vault.loader import load_vault
from tests.helpers import create_placement_vault
from tests.hint_fakes import assists
from tests.test_followups_nov2_help_fold import _rollover, _submit
from tests.test_hint_h2a_review_round2 import ARGMAX, _attempt

TAG = HELP_FOLD_ATTACH_ALGORITHM_VERSION
PREDECESSOR = TEACHER_ALGORITHM_VERSION
OFF = ARGMAX + "fold_follows_attach = false\n"


def test_mvp042_is_one_constant_after_mvp041_and_the_latest():
    from learnloop.config.schema import HintsConfig
    from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, defaults_fingerprint_for_version
    from learnloop.help_fold_attach_upgrade import PREDECESSOR as UPGRADE_PREDECESSOR
    from learnloop.params.parameter_registry import classify_config_path

    # Teacher TE1b's mvp-0.43 follows it as the latest (and keeps it).
    assert SUCCESSOR_CHAIN[-8:-6] == (PREDECESSOR, TAG) == ("mvp-0.41", "mvp-0.42")
    assert LATEST_ALGORITHM_VERSION == SUCCESSOR_CHAIN[-1] == "mvp-0.48" and UPGRADE_PREDECESSOR == PREDECESSOR
    assert HELP_FOLD_ATTACH_VERSIONS == frozenset({TAG, "mvp-0.43", "mvp-0.44", "mvp-0.45", "mvp-0.46", "mvp-0.47", "mvp-0.48"})
    assert HintsConfig().fold_follows_attach is True
    rule = classify_config_path("hints.fold_follows_attach")
    assert rule is not None and rule.kind == "structural" and "mvp-0.42" in rule.rationale
    for version in SUCCESSOR_CHAIN:
        assert DEFAULTS_SNAPSHOT_BY_ALGORITHM[version] == defaults_fingerprint_for_version(version), version
    assert DEFAULTS_SNAPSHOT_BY_ALGORITHM[TAG] != DEFAULTS_SNAPSHOT_BY_ALGORITHM[PREDECESSOR]


def _rolled(tmp_path, *, version: str, config: str = ARGMAX, option: str = "next_step@L3"):
    """The session rollover case at ``version``: a hint shown under ``k1`` in
    an ended session, the same key submitted in a new one."""

    return _rollover(tmp_path, config=config, option=option, version=version)


@pytest.mark.parametrize(("version", "config", "live"), [
    (TAG, ARGMAX, True), (TAG, OFF, False), (PREDECESSOR, ARGMAX, False)], ids=["tag", "tag-off", "predecessor"])
def test_the_fold_is_gated_by_the_tag_and_the_switch(tmp_path, monkeypatch, version, config, live):
    """F1: below the tag or switched off, the predecessor's fold and attach
    exactly: the rollover hint is not counted, and nothing attaches in the
    attempt's own transaction (H0's attach, disabled here, would take it)."""

    from learnloop.attempts.hint_fold import fold_follows_attach
    from learnloop_sidecar.handlers import practice as practice_handlers

    paths, ctx, _first, second = _rolled(tmp_path, version=version, config=config)
    assert fold_follows_attach(load_vault(paths.root)) is live
    monkeypatch.setattr(practice_handlers, "_attach_hint_reveals", lambda *args, **kwargs: None)
    result = _submit(ctx, second)
    [row] = assists(paths.sqlite_path)
    assert _attempt(paths, result["attemptId"])["hints_used"] == (1 if live else 0)
    assert row["attempt_id"] == (result["attemptId"] if live else None)


@pytest.mark.parametrize(("version", "config", "live"), [
    (TAG, ARGMAX, True), (TAG, OFF, False), (PREDECESSOR, ARGMAX, False)], ids=["tag", "tag-off", "predecessor"])
def test_worked_help_primes_only_at_the_tag_with_the_switch_on(tmp_path, version, config, live):
    paths, ctx, _first, second = _rolled(tmp_path, version=version, config=config, option="worked_chunk@L4")
    result = _submit(ctx, second)
    attempt = _attempt(paths, result["attemptId"])
    [row] = assists(paths.sqlite_path)
    assert attempt["primed"] == (1 if live else 0) and attempt["hints_used"] == 0
    # H0's attach still binds the key's row after the commit, at every version.
    assert row["attempt_id"] == result["attemptId"]


def test_the_same_session_fold_is_the_same_below_and_at_the_tag(tmp_path):
    """Switched off, the predecessor's fold of a same-session keyed hint is unchanged."""

    from tests.hint_fakes import store_map
    from tests.test_followups_nov2_help_fold import _hinted_session, hint_vault
    from tests.test_hint_h2a_review_round2 import _context

    counts = []
    for name, config in (("on", ARGMAX), ("off", OFF)):
        paths = hint_vault(tmp_path / name, config=config)
        store_map(paths)
        ctx = _context(paths, inline=True)
        session = _hinted_session(paths, ctx)
        result = _submit(ctx, session)
        [row] = assists(paths.sqlite_path)
        counts.append((_attempt(paths, result["attemptId"])["hints_used"], row["attempt_id"] == result["attemptId"]))
    assert counts == [(1, True), (1, True)]


@pytest.mark.parametrize(("version", "config"), [(TAG, ARGMAX), (TAG, OFF), (PREDECESSOR, ARGMAX)],
                         ids=["on", "off", "predecessor"])
def test_a_rebuild_changes_no_attempt_and_a_shadow_rebuild_is_zero(tmp_path, version, config):
    """Replay re-applies the stored ``hints_used`` and ``primed`` (it never
    folds), so the successor's counts survive a rebuild and the shadow
    rebuild shows no mastery, facet or schedule delta."""

    from learnloop.db.repositories import Repository
    from learnloop.substrate.replay import rebuild_derived_state
    from learnloop.substrate.shadow_rebuild import shadow_rebuild

    paths, ctx, _first, second = _rolled(tmp_path, version=version, config=config, option="worked_chunk@L4")
    result = _submit(ctx, second)
    before = dict(_attempt(paths, result["attemptId"]))
    ctx.close()
    shadow = shadow_rebuild(load_vault(paths.root))
    assert shadow.live_database_unchanged
    summary = shadow.learner_state_diff["summary"]
    if version == TAG and config == ARGMAX:
        assert summary == {"mastery": 0, "facet": 0, "schedule": 0}
    else:
        # The predecessor's state (below the tag, or switched off): the
        # unprimed attempt's live due time and its replay differ by under a
        # second (the hint vault is a relabelled basic vault, not a
        # rebuild-equivalent one), identically at mvp-0.41 and at the tag
        # switched off; nothing else moves.
        assert summary["mastery"] == summary["facet"] == 0
        for change in shadow.learner_state_diff["schedule"]["changes"]:
            moved = {key for key in change["before"] if change["before"][key] != change["after"][key]}
            assert moved == {"due_at"}, change
            from datetime import datetime

            gap = abs(datetime.fromisoformat(change["before"]["due_at"].replace("Z", "+00:00"))
                      - datetime.fromisoformat(change["after"]["due_at"].replace("Z", "+00:00")))
            assert gap.total_seconds() <= 1, change
    rebuild_derived_state(load_vault(paths.root), Repository.attach(paths.sqlite_path))
    after = dict(_attempt(paths, result["attemptId"]))
    assert (after["hints_used"], after["primed"]) == (before["hints_used"], before["primed"])


# -- the chain and the upgrade -------------------------------------------------------------------------


@pytest.fixture
def _cli_process(monkeypatch):
    """This process as the CLI is: importing it installs the completion."""

    from learnloop import activation_journal
    from learnloop.cli.runtime import _complete_interrupted_activation

    monkeypatch.setattr(activation_journal, "_COMPLETER", _complete_interrupted_activation)


def _vault_at(tmp_path, name, version):
    return create_placement_vault(tmp_path / name, version=version)


def _version(paths) -> str:
    return load_vault(paths.root).config.algorithms.algorithm_version


def _journal(paths):
    return paths.sqlite_path.with_name(paths.sqlite_path.name + ".claim-fixes-activation")


def _activated(paths, version=TAG) -> bool:
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        return connection.execute(
            "SELECT 1 FROM derived_state_rebuilds WHERE scope = 'p0_projection_activation' AND algorithm_version = ?",
            (version,),
        ).fetchone() is not None


@pytest.mark.parametrize("start", ["mvp-0.9", "mvp-0.30", "mvp-0.39", "mvp-0.40", "mvp-0.41"])
def test_upgrade_to_mvp042_works_from_supported_versions(tmp_path, _cli_process, start):
    from learnloop.cli import app

    paths = _vault_at(tmp_path, "v", start)
    result = CliRunner().invoke(app, ["upgrade", "--to", TAG, "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert f"{start} -> {TAG}" in result.output
    assert _version(paths) == TAG and _activated(paths) and not _journal(paths).exists()
    if start != PREDECESSOR:
        assert _activated(paths, PREDECESSOR)


def test_a_bare_upgrade_targets_mvp042_and_it_refuses_twice(tmp_path, _cli_process):
    from learnloop.cli import app
    from learnloop.help_fold_attach_upgrade import upgrade_to_help_fold_attach

    paths = _vault_at(tmp_path, "v", PREDECESSOR)
    # Teacher TE1b's mvp-0.43 is the bare upgrade's target since its landing: this link is reached by --to.
    result = CliRunner().invoke(app, ["upgrade", "--to", TAG, "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert f"{PREDECESSOR} -> {TAG}" in result.output
    assert _version(paths) == TAG and _activated(paths)
    again = upgrade_to_help_fold_attach(paths.root)
    assert not again.upgraded and again.problems == [f"vault is already {TAG}"]


def test_the_upgrade_refuses_a_version_before_the_chain(tmp_path):
    from learnloop.help_fold_attach_upgrade import upgrade_to_help_fold_attach

    paths = _vault_at(tmp_path, "old", "mvp-0.9")
    rewrite_algorithm_version(paths.root / "learnloop.toml", "mvp-0.9", "mvp-0.8", durable=True)
    result = upgrade_to_help_fold_attach(paths.root)
    assert not result.upgraded and _version(paths) == "mvp-0.8"
    assert "cannot upgrade from 'mvp-0.8'" in result.problems[0]


def _interrupted(tmp_path, name, predecessor=PREDECESSOR, target=TAG):
    paths = _vault_at(tmp_path, name, predecessor)
    _journal(paths).write_text(json.dumps({"predecessor": predecessor, "target": target}), encoding="utf-8")
    rewrite_algorithm_version(paths.root / "learnloop.toml", predecessor, target, durable=True)
    assert not _activated(paths, target)
    return paths


def test_the_next_cli_command_completes_an_interrupted_mvp042_activation(tmp_path, _cli_process):
    from learnloop.cli import app
    from learnloop.help_fold_attach_upgrade import upgrade_to_help_fold_attach

    paths = _interrupted(tmp_path, "interrupted")
    result = CliRunner().invoke(app, ["backfill-originals", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert not _journal(paths).exists() and _activated(paths) and _version(paths) == TAG
    again = upgrade_to_help_fold_attach(paths.root)
    assert not again.upgraded and again.problems == [f"vault is already {TAG}"]


def test_an_earlier_links_interrupted_activation_is_handed_down_the_chain(tmp_path, _cli_process):
    from learnloop.cli import app

    paths = _interrupted(tmp_path, "earlier", predecessor="mvp-0.40", target=PREDECESSOR)
    result = CliRunner().invoke(app, ["backfill-originals", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert not _journal(paths).exists() and _activated(paths, PREDECESSOR) and _version(paths) == PREDECESSOR
