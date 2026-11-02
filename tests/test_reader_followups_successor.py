"""Reader RW6b part 1 as the successor mvp-0.39 (Codex review F4;
spec_reader_workbench_v1 §9.3 "Why no successor", whose fallback applies;
docs/reviews/reader-rw6b-p1-followups-codex-review.md).

* the tag is ONE constant after mvp-0.38 and the latest; its defaults
  snapshot is recorded; ``followups.enabled`` is its kill switch;
* below the tag, or switched off, nothing is planned or re-valued: the Today
  queue is the predecessor's (plan parity), and no digest or commitment is
  written;
* the upgrade is the chain's next journalled link (from mvp-0.38, or mvp-0.9
  onwards through the chain), and the next command completes an
  interrupted activation.

Fakes only; no model call.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing

import pytest
from typer.testing import CliRunner

from learnloop.algorithm_versions import (
    COLD_RETRY_RESCHEDULE_ALGORITHM_VERSION,
    LATEST_ALGORITHM_VERSION,
    READER_FOLLOWUPS_ALGORITHM_VERSION,
    READER_FOLLOWUPS_VERSIONS,
    SUCCESSOR_CHAIN,
)
from learnloop.db.repositories import Repository
from learnloop.instructional import reader_followups as RF
from learnloop.ops.vault_upgrade import rewrite_algorithm_version
from learnloop.vault.loader import load_vault
from tests.helpers import create_placement_vault
from tests.recap_fixtures import EXT, at
from tests.test_reader_followups import FakeSearch, _candidate, _now, _plan, _seeded

TAG = READER_FOLLOWUPS_ALGORITHM_VERSION
PREDECESSOR = COLD_RETRY_RESCHEDULE_ALGORITHM_VERSION


def test_mvp039_is_one_constant_after_mvp038_and_the_latest():
    from learnloop.config.schema import FollowupsConfig
    from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, defaults_fingerprint_for_version
    from learnloop.params.parameter_registry import classify_config_path
    from learnloop.reader_followups_upgrade import PREDECESSOR as UPGRADE_PREDECESSOR

    # Curriculum C1's mvp-0.40 follows it as the latest (and keeps it).
    assert SUCCESSOR_CHAIN[-6:-4] == (PREDECESSOR, TAG) == ("mvp-0.38", "mvp-0.39")
    assert SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.43" and UPGRADE_PREDECESSOR == PREDECESSOR
    assert READER_FOLLOWUPS_VERSIONS == frozenset({TAG, "mvp-0.40", "mvp-0.41", "mvp-0.42", "mvp-0.43"})
    assert FollowupsConfig().enabled is True
    rule = classify_config_path("followups.enabled")
    assert rule is not None and rule.kind == "structural" and "mvp-0.39" in rule.rationale
    for version in SUCCESSOR_CHAIN:
        assert DEFAULTS_SNAPSHOT_BY_ALGORITHM[version] == defaults_fingerprint_for_version(version), version
    assert DEFAULTS_SNAPSHOT_BY_ALGORITHM[TAG] != DEFAULTS_SNAPSHOT_BY_ALGORITHM[PREDECESSOR]


@pytest.mark.parametrize(("version", "switch", "live"), [
    (TAG, None, True), (TAG, False, False), (PREDECESSOR, None, False), (PREDECESSOR, True, False)])
def test_planning_and_revaluation_are_gated_by_the_tag_and_the_switch(tmp_path, version, switch, live):
    config = None if switch is None else f"[followups]\nenabled = {'true' if switch else 'false'}\n"
    vault, repo, session = _seeded(tmp_path, config=config, version=version)
    assert RF.followups_enabled(vault) is live
    search = FakeSearch([_candidate("pi_svd_define_002", 0.99, 0.01, 1.0)])
    planned = RF.plan_ended_sessions(vault, repo, search=search, now=_now(), clock=at(300))
    revalued = RF.revalue_pending(vault, repo, now=_now(400), valuer=lambda *_a: {"problems": []}, clock=at(400))
    with repo.connection() as connection:
        commitments = connection.execute("SELECT COUNT(*) FROM commitments").fetchone()[0]
        digests = connection.execute("SELECT COUNT(*) FROM reader_session_digests").fetchone()[0]
    if live:
        assert len(planned) == 1 and commitments == 1 and digests == 1 and revalued["skipped"] is None
    else:
        assert planned == [] and search.calls == [] and commitments == 0 and digests == 0
        assert revalued["skipped"] == "followups.enabled is false"


def _served(tmp_path, name, *, version, config=None):
    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.registry import METHOD_REGISTRY

    vault, repo, _session = _seeded(tmp_path / name, config=config, version=version)
    ctx = SidecarContext()
    ctx.load(vault.root)
    try:
        spec = METHOD_REGISTRY["get_today_queue"]
        queue = spec.handler(ctx, spec.params_model.model_validate({}))
    finally:
        ctx.close()
    with repo.connection() as connection:
        written = (connection.execute("SELECT COUNT(*) FROM commitments").fetchone()[0],
                   connection.execute("SELECT COUNT(*) FROM reader_session_digests").fetchone()[0])
    return [item["practiceItemId"] for section in queue["sections"] for item in section["items"]], written


def test_switched_off_the_today_queue_is_the_predecessors(tmp_path):
    """Plan parity: an ended reader session waits at both versions; mvp-0.39
    with ``followups.enabled = false`` serves exactly what mvp-0.38 serves and
    writes no digest or commitment."""

    before, written_before = _served(tmp_path, "pred", version=PREDECESSOR)
    after, written_after = _served(tmp_path, "off", version=TAG, config="[followups]\nenabled = false\n")
    assert after == before and written_before == written_after == (0, 0)


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


@pytest.mark.parametrize("start", ["mvp-0.9", "mvp-0.30", "mvp-0.37", "mvp-0.38"])
def test_upgrade_to_mvp039_works_from_supported_versions(tmp_path, _cli_process, start):
    from learnloop.cli import app

    paths = _vault_at(tmp_path, "v", start)
    result = CliRunner().invoke(app, ["upgrade", "--to", TAG, "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert f"{start} -> {TAG}" in result.output
    assert _version(paths) == TAG and _activated(paths) and not _journal(paths).exists()
    if start != PREDECESSOR:
        assert _activated(paths, PREDECESSOR)


def test_a_bare_upgrade_targets_the_latest_through_mvp039_and_mvp039_refuses_twice(tmp_path, _cli_process):
    from learnloop.cli import app
    from learnloop.reader_followups_upgrade import upgrade_to_reader_followups

    paths = _vault_at(tmp_path, "v", PREDECESSOR)
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    # The latest is curriculum C1's mvp-0.40, chained through this tag.
    assert f"{PREDECESSOR} -> {LATEST_ALGORITHM_VERSION}" in result.output
    assert _version(paths) == LATEST_ALGORITHM_VERSION and _activated(paths)
    other = _vault_at(tmp_path, "w", PREDECESSOR)
    assert upgrade_to_reader_followups(other.root).upgraded and _version(other) == TAG
    again = upgrade_to_reader_followups(other.root)
    assert not again.upgraded and again.problems == [f"vault is already {TAG}"]


def test_the_upgrade_refuses_a_version_before_the_chain(tmp_path):
    from learnloop.reader_followups_upgrade import upgrade_to_reader_followups

    paths = _vault_at(tmp_path, "old", "mvp-0.9")
    rewrite_algorithm_version(paths.root / "learnloop.toml", "mvp-0.9", "mvp-0.8", durable=True)
    result = upgrade_to_reader_followups(paths.root)
    assert not result.upgraded and _version(paths) == "mvp-0.8"
    assert "cannot upgrade from 'mvp-0.8'" in result.problems[0]


def _interrupted(tmp_path, name, predecessor=PREDECESSOR, target=TAG):
    paths = _vault_at(tmp_path, name, predecessor)
    _journal(paths).write_text(json.dumps({"predecessor": predecessor, "target": target}), encoding="utf-8")
    rewrite_algorithm_version(paths.root / "learnloop.toml", predecessor, target, durable=True)
    assert not _activated(paths, target)
    return paths


def test_the_next_cli_command_completes_an_interrupted_mvp039_activation(tmp_path, _cli_process):
    from learnloop.cli import app
    from learnloop.reader_followups_upgrade import upgrade_to_reader_followups

    paths = _interrupted(tmp_path, "interrupted")
    result = CliRunner().invoke(app, ["backfill-originals", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert not _journal(paths).exists() and _activated(paths) and _version(paths) == TAG
    again = upgrade_to_reader_followups(paths.root)
    assert not again.upgraded and again.problems == [f"vault is already {TAG}"]


def test_a_failure_after_the_rename_leaves_the_predecessor_and_no_journal(tmp_path, monkeypatch):
    import learnloop.reader_followups_upgrade as upgrade

    paths = _vault_at(tmp_path, "failing", PREDECESSOR)
    real = upgrade._publish_algorithm_version

    def publish_then_fail(config_path, from_version, to_version, *, renamed=None):
        real(config_path, from_version, to_version, renamed=renamed)
        if to_version == TAG:
            raise OSError("the directory fsync failed")

    monkeypatch.setattr(upgrade, "_publish_algorithm_version", publish_then_fail)
    with pytest.raises(OSError):
        upgrade.upgrade_to_reader_followups(paths.root)
    assert _version(paths) == PREDECESSOR and not _journal(paths).exists() and not _activated(paths)


def test_an_interrupted_mvp038_activation_then_upgrade_to_mvp039_completes_it(tmp_path, _cli_process):
    from learnloop.cli import app

    paths = _interrupted(tmp_path, "interrupted038", "mvp-0.37", PREDECESSOR)
    result = CliRunner().invoke(app, ["upgrade", "--to", TAG, "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert f"{PREDECESSOR} -> {TAG}" in result.output
    assert _version(paths) == TAG and not _journal(paths).exists()
    assert _activated(paths, PREDECESSOR) and _activated(paths)


def test_without_a_completion_an_attach_refuses_and_the_upgrade_still_completes_the_mvp038_journal(
        tmp_path, monkeypatch):
    from learnloop import activation_journal
    from learnloop.reader_followups_upgrade import complete_interrupted_activation, upgrade_to_reader_followups

    paths = _interrupted(tmp_path, "refused038", "mvp-0.37", PREDECESSOR)
    monkeypatch.setattr(activation_journal, "_COMPLETER", None)
    with pytest.raises(activation_journal.InterruptedActivation, match=f"learnloop upgrade --to {PREDECESSOR}"):
        Repository(paths.sqlite_path)
    assert complete_interrupted_activation(paths.root) == PREDECESSOR
    assert not _journal(paths).exists() and complete_interrupted_activation(paths.root) is None
    result = upgrade_to_reader_followups(paths.root)
    assert result.upgraded and result.from_version == PREDECESSOR and _version(paths) == TAG
    assert not _journal(paths).exists() and _activated(paths, PREDECESSOR) and _activated(paths)


def test_replay_plans_nothing_and_a_shadow_rebuild_is_zero(tmp_path):
    """The successor's state is workflow state (digests, commitments): a
    rebuild neither replays nor re-values it (the stage's 0/0/0, at the tag)."""

    from learnloop.substrate.replay import rebuild_derived_state
    from learnloop.substrate.shadow_rebuild import shadow_rebuild

    vault, repo, session = _seeded(tmp_path)
    rebuild_derived_state(vault, repo, clock=at(250))
    row = _plan(vault, repo, session, FakeSearch([_candidate("pi_svd_define_002", 0.99, 0.01, 1.0)]))
    assert row["followup_commitment_ids"]
    result = shadow_rebuild(load_vault(vault.root))
    assert result.learner_state_diff["summary"] == {"mastery": 0, "facet": 0, "schedule": 0}
    assert result.live_database_unchanged is True
    with repo.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM reader_session_digests WHERE extraction_id = ?",
                                  (EXT,)).fetchone()[0] == 1
