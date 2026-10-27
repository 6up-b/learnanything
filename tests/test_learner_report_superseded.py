"""Successor mvp-0.36: a replaced learner claim is kept, so replay applies it at its own time.

The Medium recorded at the rebuild-equivalence landing
(``docs/reviews/lp-learner-report-superseded.md``): a second learner report on
one LO (a too_easy/too_hard retirement or a rung-variant request) replaced the
LO's earlier claim of that source by DELETING it (the replace seam), though the
earlier claim's live re-anchor had already moved mastery. Replay cannot apply a
claim that is gone, so a rebuild disagreed with live (Δmean -0.269 on
``lo_diag`` with one attempt and two too_easy retirements). From the tag on the
seam keeps the replaced row, marked ``superseded_by``: every live reader reads
the claims in force, and replay applies each claim at its own point, reading a
replaced claim only until the claim that replaced it was made.

The predecessors' pin (strict xfail at mvp-0.33 to mvp-0.35) is in
``tests/test_rebuild_equivalence.py``; here: the seam, the readers, the
property test (random attempts and learner reports rebuild to live, 0/0/0) and
the chain with its journalled activation.
"""
from __future__ import annotations

import json
import multiprocessing
import os
import random
import sqlite3
from contextlib import closing

import pytest
from typer.testing import CliRunner

from learnloop.algorithm_versions import (
    LATEST_ALGORITHM_VERSION,
    ONE_ASK_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
    SUPERSEDED_CLAIMS_ALGORITHM_VERSION,
    SUPERSEDED_CLAIMS_VERSIONS,
)
from learnloop.content.authoring.item_authoring import retire_item
from learnloop.content.authoring.rung_variants import RungVariantError, request_rung_variant
from learnloop.db.repositories import Repository
from learnloop.learner.learner_profile import seed_global_learner_claim
from learnloop.learner.mastery import covering_learner_claim, replaced_claims_kept
from learnloop.ops.vault_upgrade import rewrite_algorithm_version
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

from tests.helpers import add_followup_item, create_placement_vault
from tests.test_rebuild_equivalence import (
    GAPS,
    ITEMS,
    KINDS,
    LOS,
    ZERO,
    _answer,
    _at,
    _live_reanchoring_claim,
    _mastery,
    _shadow_summary,
)

TAG = SUPERSEDED_CLAIMS_ALGORITHM_VERSION
PREDECESSOR = ONE_ASK_ALGORITHM_VERSION


def _vault(tmp_path, version=TAG, name="vault"):
    paths = create_placement_vault(tmp_path / name, version=version)
    add_followup_item(paths.root)
    repository = Repository(paths.sqlite_path)
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=_at(0))
    return paths, vault, repository


def _rows(repository):
    with closing(sqlite3.connect(repository.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(
            "SELECT id, source, scope_type, scope_id, claimed_level, superseded_by FROM learner_claims "
            "ORDER BY created_at, id")]


# -- the seam ---------------------------------------------------------------------------------------


def test_the_tag_is_one_constant_after_mvp035_and_the_latest():
    from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, defaults_fingerprint_for_version
    from learnloop.superseded_claims_upgrade import PREDECESSOR as UPGRADE_PREDECESSOR

    assert SUCCESSOR_CHAIN[-2:] == ("mvp-0.35", "mvp-0.36")
    assert TAG == "mvp-0.36" == LATEST_ALGORITHM_VERSION and UPGRADE_PREDECESSOR == PREDECESSOR == "mvp-0.35"
    assert SUPERSEDED_CLAIMS_VERSIONS == frozenset({TAG})
    assert DEFAULTS_SNAPSHOT_BY_ALGORITHM[TAG] == defaults_fingerprint_for_version(TAG)
    # No new default and no kill switch: only the version string moves the fingerprint.
    assert DEFAULTS_SNAPSHOT_BY_ALGORITHM[TAG] != DEFAULTS_SNAPSHOT_BY_ALGORITHM[PREDECESSOR]


def test_a_second_too_easy_report_keeps_the_first_as_a_replaced_row_that_no_live_reader_reads(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    _answer(vault, repository, "pi_diag_easy", minutes=1, points=1.0)
    retire_item(paths.root, repository, practice_item_id="pi_diag_easy", reason="too_easy", clock=_at(2))
    retire_item(paths.root, repository, practice_item_id="pi_diag_mid", reason="too_easy", clock=_at(4))

    reports = [row for row in _rows(repository) if row["source"] == "learner_report"]
    assert [row["scope_id"] for row in reports] == ["lo_diag", "lo_diag"]
    first, second = reports
    assert first["superseded_by"] == second["id"] and second["superseded_by"] is None
    # The live readers: the claims in force, exactly what the predecessor's delete left.
    in_force = [claim["id"] for claim in repository.learner_claims() if claim["source"] == "learner_report"]
    assert in_force == [second["id"]]
    assert covering_learner_claim(load_vault(paths.root), repository, "lo_diag")["id"] == second["id"]
    assert {claim["id"] for claim in repository.learner_claims(include_superseded=True)} >= {first["id"], second["id"]}


@pytest.mark.parametrize("version", ["mvp-0.33", "mvp-0.35"])
def test_below_the_tag_the_seam_still_deletes_the_replaced_claim(tmp_path, version):
    paths, vault, repository = _vault(tmp_path, version=version)
    assert not replaced_claims_kept(vault)
    _answer(vault, repository, "pi_diag_easy", minutes=1, points=1.0)
    retire_item(paths.root, repository, practice_item_id="pi_diag_easy", reason="too_easy", clock=_at(2))
    retire_item(paths.root, repository, practice_item_id="pi_diag_mid", reason="too_easy", clock=_at(4))
    reports = [row for row in _rows(repository) if row["source"] == "learner_report"]
    assert len(reports) == 1 and reports[0]["superseded_by"] is None


def test_a_rung_variant_request_replaces_only_its_own_source_on_its_own_lo(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    _answer(vault, repository, "pi_diag_easy", minutes=1, points=4.0)
    retire_item(paths.root, repository, practice_item_id="pi_eig_easy", reason="too_easy", clock=_at(2))
    vault = load_vault(paths.root)
    request_rung_variant(vault, repository, practice_item_id="pi_diag_easy", direction="harder", clock=_at(3))
    request_rung_variant(vault, repository, practice_item_id="pi_diag_mid", direction="easier", clock=_at(5))

    rows = _rows(repository)
    rung = [row for row in rows if row["source"] == "rung_variant_request"]
    assert [row["superseded_by"] for row in rung] == [rung[1]["id"], None]
    # The other LO's learner report is untouched.
    assert [row["superseded_by"] for row in rows if row["source"] == "learner_report"] == [None]
    assert _shadow_summary(paths)["summary"] == ZERO


def test_a_new_starting_level_keeps_the_old_one_for_an_lo_first_practised_under_it(tmp_path):
    """The init-wizard seam (global). The starting level set when the vault was
    made seeded every LO at its first sync; a later change replaces it. An LO
    first practised before the change rebuilds to live: replay seeds it from the
    claim in force at its first attempt, the replaced one (below the tag that
    claim was deleted and the LO rebuilt from the cold start)."""

    paths = create_placement_vault(tmp_path / "vault", version=TAG)
    add_followup_item(paths.root)
    repository = Repository(paths.sqlite_path)
    seed_global_learner_claim(repository, "comfortable", keep_replaced=True, clock=_at(-10))
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=_at(0))
    _answer(vault, repository, "pi_svd_define_001", minutes=2, points=2.0)
    seed_global_learner_claim(repository, "new_to_this", keep_replaced=replaced_claims_kept(vault), clock=_at(3))
    wizard = [row for row in _rows(repository) if row["source"] == "init_wizard"]
    assert len(wizard) == 2 and wizard[0]["superseded_by"] == wizard[1]["id"]
    live = _mastery(repository)

    changed = {change["key"].get("learning_object_id") for change in _shadow_summary(paths)["mastery"]["changes"]}
    assert "lo_svd_definition" not in changed
    rebuild_all_derived_state(load_vault(paths.root), repository)
    assert _mastery(repository)["lo_svd_definition"] == live["lo_svd_definition"]


@pytest.mark.parametrize("version", [PREDECESSOR, TAG])
@pytest.mark.xfail(strict=True, reason=(
    "pre-existing, a separate class (found by this stage, not its subject): a claim that never re-anchors "
    "(an init-wizard starting level, a manual claim) made after an LO's row was materialized (every LO is at "
    "the vault's first sync) leaves the live row as it was, while replay seeds the LO from the claims in force "
    "at its first attempt, and an attempt-free LO from the claims in force at rebuild time"
))
def test_a_global_claim_made_after_materialization_rebuilds_to_live(tmp_path, version):
    paths, vault, repository = _vault(tmp_path, version=version)
    seed_global_learner_claim(repository, "some_exposure", clock=_at(1))
    _answer(vault, repository, "pi_svd_define_001", minutes=2, points=2.0)
    assert _shadow_summary(paths)["summary"] == ZERO


def test_two_reports_before_any_attempt_seed_from_the_latest_with_the_variance_each_left(tmp_path):
    """Zero-evidence re-anchors: the replaced report re-seeded the row, then the
    replacing one; replay's seed before the first attempt is the replacing
    claim's mean with the larger variance either left (re-review F8, with the
    replaced anchor read at its own point)."""

    paths, vault, repository = _vault(tmp_path)
    request_rung_variant(vault, repository, practice_item_id="pi_diag_hard", direction="easier", clock=_at(1))
    request_rung_variant(vault, repository, practice_item_id="pi_diag_mid", direction="harder", clock=_at(2))
    rung = [row for row in _rows(repository) if row["source"] == "rung_variant_request"]
    assert rung[0]["superseded_by"] == rung[1]["id"] and rung[0]["claimed_level"] != rung[1]["claimed_level"]
    _answer(vault, repository, "pi_diag_easy", minutes=3, points=3.0)
    live = _mastery(repository)

    assert _shadow_summary(paths)["summary"] == ZERO
    rebuild_all_derived_state(vault, repository)
    assert _mastery(repository) == live


def test_the_field_priors_read_only_the_claims_in_force(tmp_path):
    """``field.priors`` reads the table raw: a replaced row changes nothing it
    derives (the same result as with the row deleted, as the predecessor did)."""

    from types import SimpleNamespace

    from learnloop.field.priors import load_frozen_priors

    paths, vault, repository = _vault(tmp_path)
    retire_item(paths.root, repository, practice_item_id="pi_diag_easy", reason="too_easy", clock=_at(1))
    retire_item(paths.root, repository, practice_item_id="pi_diag_mid", reason="too_easy", clock=_at(2))
    attempts = [SimpleNamespace(observed_at="2030-01-01T00:00:00Z", lo_id="lo_diag",
                                features=SimpleNamespace(subject_id="linear-algebra"))]

    def priors():
        with closing(sqlite3.connect(repository.sqlite_path)) as connection:
            connection.row_factory = sqlite3.Row
            return load_frozen_priors(connection, attempts, vault.config)

    kept = priors()
    with closing(sqlite3.connect(repository.sqlite_path)) as connection:
        assert connection.execute("DELETE FROM learner_claims WHERE superseded_by IS NOT NULL").rowcount == 1
        connection.commit()
    assert kept == priors()


# -- the predecessors' xfail, now passing; the property ---------------------------------------------


def _report(paths, repository, rng, minutes, active, focus):
    """One learner report on an active item: a too_easy retirement or a rung-variant request (easier or harder).

    Mostly on an item of the history's ``focus`` LO, so a report replaces an earlier one of its source."""

    focused = sorted(item for item in active if item.startswith(focus))
    item_id = rng.choice(focused if focused and rng.random() < 0.7 else sorted(active))
    if rng.random() < 0.5 and len(active) > 3:
        retire_item(paths.root, repository, practice_item_id=item_id, reason="too_easy", clock=_at(minutes))
        active.discard(item_id)
        return
    try:
        request_rung_variant(load_vault(paths.root), repository, practice_item_id=item_id,
                             direction=rng.choice(("easier", "harder")), clock=_at(minutes))
    except RungVariantError:
        pass  # one pending variant per item: the request is refused, nothing written


def _replaced(repository) -> bool:
    return any(row["superseded_by"] for row in _rows(repository)
               if row["source"] in ("learner_report", "rung_variant_request"))


@pytest.mark.parametrize("seed", range(24))
def test_random_attempts_and_learner_reports_rebuild_to_live(tmp_path, seed):
    """Random interleavings of attempts, too_easy retirements,
    rung-variant requests in either direction (each a learner report that replaces the LO's earlier
    one of its source) and tutor gap declarations, then a primary load: the shadow rebuild reports 0/0/0 and an applied rebuild
    (twice) leaves mastery exactly as live."""

    rng = random.Random(7000 + seed)
    paths, vault, repository = _vault(tmp_path)
    active = set(ITEMS)
    minutes = 0.0
    focus = rng.choice(("pi_diag_", "pi_eig_", "pi_svd_"))
    for _ in range(rng.randint(8, 18)):
        minutes += rng.choice(GAPS)
        roll = rng.random()
        if roll < 0.45:
            _answer(load_vault(paths.root), repository, rng.choice(sorted(active)), minutes=minutes,
                    points=float(rng.randint(0, 4)), kind=rng.choice(KINDS))
        elif roll < 0.85:
            _report(paths, repository, rng, minutes, active, focus)
        else:
            _live_reanchoring_claim(load_vault(paths.root), repository, rng.choice(LOS), minutes=minutes,
                                    level=round(rng.uniform(0.1, 0.95), 3))
    if not _replaced(repository):
        # Close with a replacement, so no seed is vacuous: a too_easy report on
        # an LO that has one already (or two on one LO), each after an attempt.
        reported = {row["scope_id"] for row in _rows(repository) if row["source"] == "learner_report"}
        by_lo: dict[str, list[str]] = {}
        for item_id in sorted(active):
            by_lo.setdefault(load_vault(paths.root).practice_items[item_id].learning_object_id, []).append(item_id)
        lo_id = next((lo for lo in sorted(by_lo) if lo in reported),
                     next(lo for lo in sorted(by_lo) if len(by_lo[lo]) >= 2))
        for item_id in by_lo[lo_id][: 1 if lo_id in reported else 2]:
            minutes += rng.choice(GAPS)
            _answer(load_vault(paths.root), repository, item_id, minutes=minutes, points=float(rng.randint(0, 4)))
            minutes += 1
            retire_item(paths.root, repository, practice_item_id=item_id, reason="too_easy", clock=_at(minutes))
    # Not vacuous: every seed replaces at least one learner report or rung-variant claim.
    assert any(row["superseded_by"] for row in _rows(repository)
               if row["source"] in ("learner_report", "rung_variant_request"))
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=_at(minutes + 1))
    live = _mastery(repository)

    diff = _shadow_summary(paths)
    assert diff["summary"] == ZERO, {family: diff[family]["changes"][:3] for family in ZERO}
    rebuild_all_derived_state(vault, repository)
    assert _mastery(repository) == live
    rebuild_all_derived_state(vault, repository)
    assert _mastery(repository) == live


# -- the chain and its journalled activation ----------------------------------------------------------


@pytest.fixture
def _cli_process(monkeypatch):
    from learnloop import activation_journal
    from learnloop.cli.runtime import _complete_interrupted_activation

    monkeypatch.setattr(activation_journal, "_COMPLETER", _complete_interrupted_activation)


def _journal(paths):
    return paths.sqlite_path.with_name(paths.sqlite_path.name + ".claim-fixes-activation")


def _version(paths) -> str:
    return load_vault(paths.root).config.algorithms.algorithm_version


def _activated(paths, version=TAG) -> bool:
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        return connection.execute(
            "SELECT 1 FROM derived_state_rebuilds WHERE scope = 'p0_projection_activation' AND algorithm_version = ?",
            (version,),
        ).fetchone() is not None


@pytest.mark.parametrize("start", ["mvp-0.9", "mvp-0.30", "mvp-0.33", "mvp-0.34", "mvp-0.35"])
def test_upgrade_to_mvp036_works_from_every_supported_version(tmp_path, start, _cli_process):
    from learnloop.cli import app

    paths = create_placement_vault(tmp_path / "v", version=start)
    result = CliRunner().invoke(app, ["upgrade", "--to", TAG, "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert f"{start} -> {TAG}" in result.output
    assert _version(paths) == TAG and _activated(paths) and not _journal(paths).exists()


def test_a_bare_upgrade_targets_mvp036(tmp_path, _cli_process):
    from learnloop.cli import app

    paths = create_placement_vault(tmp_path / "v", version=PREDECESSOR)
    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    assert f"{PREDECESSOR} -> {TAG}" in result.output and _version(paths) == TAG


def test_the_upgrade_refuses_an_older_vault_and_one_already_at_the_tag(tmp_path):
    from learnloop.superseded_claims_upgrade import upgrade_to_superseded_claims

    old = create_placement_vault(tmp_path / "old", version="mvp-0.8")
    refused = upgrade_to_superseded_claims(old.root)
    assert not refused.upgraded and _version(old) == "mvp-0.8"
    current = create_placement_vault(tmp_path / "current", version=TAG)
    upgrade_to_superseded_claims(current.root)  # a vault created at the tag: completes its projection activation
    again = upgrade_to_superseded_claims(current.root)
    assert not again.upgraded and again.problems == [f"vault is already {TAG}"]


def test_the_activation_derives_what_the_predecessor_derived(tmp_path):
    """No row is superseded at activation (the predecessor deleted replaced
    claims), so the activation's rebuild moves nothing: 0/0/0 and live mastery
    unchanged on a predecessor history with two reports on one LO."""

    from learnloop.superseded_claims_upgrade import upgrade_to_superseded_claims

    paths, vault, repository = _vault(tmp_path, version=PREDECESSOR)
    _answer(vault, repository, "pi_diag_easy", minutes=1, points=1.0)
    retire_item(paths.root, repository, practice_item_id="pi_diag_easy", reason="too_easy", clock=_at(2))
    rebuild_all_derived_state(load_vault(paths.root), repository)
    before = _mastery(repository)
    assert upgrade_to_superseded_claims(paths.root).upgraded
    assert _mastery(Repository(paths.sqlite_path)) == before
    # The rows keep the label they were written with; a shadow rebuild re-derives
    # them under the tag, and the label is all that differs.
    for change in _shadow_summary(paths)["mastery"]["changes"]:
        assert change["change"] == "changed"
        assert {key for key in change["before"] if change["before"][key] != change["after"][key]} == {
            "algorithm_version"
        }, change


def _interrupted(tmp_path, name):
    paths = create_placement_vault(tmp_path / name, version=PREDECESSOR)
    _journal(paths).write_text(json.dumps({"predecessor": PREDECESSOR, "target": TAG}), encoding="utf-8")
    rewrite_algorithm_version(paths.root / "learnloop.toml", PREDECESSOR, TAG, durable=True)
    assert not _activated(paths)
    return paths


def _die_after_publication(root):
    import learnloop.superseded_claims_upgrade as upgrade

    real = upgrade._publish_algorithm_version

    def publish_then_die(*args, **kwargs):
        real(*args, **kwargs)
        os._exit(17)  # no handler runs: the transaction never commits

    upgrade._publish_algorithm_version = publish_then_die
    upgrade.upgrade_to_superseded_claims(root)


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
def test_a_real_death_after_the_publication_is_journalled_and_the_next_cli_command_completes_it(
    tmp_path, _cli_process,
):
    from learnloop.superseded_claims_upgrade import upgrade_to_superseded_claims

    paths = create_placement_vault(tmp_path / "crashed", version=PREDECESSOR)
    process = multiprocessing.get_context("fork").Process(target=_die_after_publication, args=(paths.root,))
    process.start()
    process.join(60)
    assert process.exitcode == 17
    assert _version(paths) == TAG and _journal(paths).exists() and not _activated(paths)

    _cli_command(paths)

    assert not _journal(paths).exists() and _activated(paths)
    again = upgrade_to_superseded_claims(paths.root)
    assert not again.upgraded and again.problems == [f"vault is already {TAG}"]


@pytest.mark.parametrize("opener", sorted(OPENERS))
def test_every_opener_that_may_write_completes_an_interrupted_mvp036_activation_first(tmp_path, opener, _cli_process):
    paths = _interrupted(tmp_path, "interrupted")
    OPENERS[opener](paths)
    assert not _journal(paths).exists() and _activated(paths) and _version(paths) == TAG


def test_without_a_completion_every_attach_refuses_with_the_mvp036_upgrade_message(tmp_path, monkeypatch):
    from learnloop import activation_journal

    paths = _interrupted(tmp_path, "interrupted")
    monkeypatch.setattr(activation_journal, "_COMPLETER", None)
    with pytest.raises(activation_journal.InterruptedActivation, match=f"learnloop upgrade --to {TAG}"):
        _open_vault_repository(paths)
    for attach in (lambda: Repository.attach(paths.sqlite_path, read_only=True), lambda: Repository(paths.sqlite_path)):
        with pytest.raises(activation_journal.InterruptedActivation, match=f"learnloop upgrade --to {TAG}"):
            attach()
    assert _journal(paths).exists() and not _activated(paths)


def test_the_upgrade_completes_its_own_journal(tmp_path, _cli_process):
    from learnloop.superseded_claims_upgrade import upgrade_to_superseded_claims

    paths = _interrupted(tmp_path, "interrupted")
    result = upgrade_to_superseded_claims(paths.root)
    assert result.upgraded and result.notes == [f"completed the interrupted activation of {TAG}"]
    assert not _journal(paths).exists() and _activated(paths)


def test_a_failure_after_the_rename_leaves_the_predecessor_and_no_journal(tmp_path, monkeypatch, _cli_process):
    import learnloop.superseded_claims_upgrade as upgrade

    paths = create_placement_vault(tmp_path / "failing", version=PREDECESSOR)
    real = upgrade._publish_algorithm_version

    def publish_then_fail(config_path, from_version, to_version, *, renamed=None):
        real(config_path, from_version, to_version, renamed=renamed)
        if to_version == TAG:
            raise OSError("the directory fsync failed")

    monkeypatch.setattr(upgrade, "_publish_algorithm_version", publish_then_fail)
    with pytest.raises(OSError):
        upgrade.upgrade_to_superseded_claims(paths.root)
    assert _version(paths) == PREDECESSOR and not _journal(paths).exists() and not _activated(paths)


def test_an_mvp035_journal_is_handed_to_its_own_upgrade_then_the_tag_activates(tmp_path, _cli_process):
    from learnloop.superseded_claims_upgrade import complete_interrupted_activation, upgrade_to_superseded_claims

    paths = create_placement_vault(tmp_path / "ca2", version="mvp-0.34")
    _journal(paths).write_text(json.dumps({"predecessor": "mvp-0.34", "target": PREDECESSOR}), encoding="utf-8")
    rewrite_algorithm_version(paths.root / "learnloop.toml", "mvp-0.34", PREDECESSOR, durable=True)
    assert complete_interrupted_activation(paths.root) == PREDECESSOR
    assert not _journal(paths).exists() and _activated(paths, PREDECESSOR)
    assert complete_interrupted_activation(paths.root) is None
    result = upgrade_to_superseded_claims(paths.root)
    assert result.upgraded and _version(paths) == TAG and not _journal(paths).exists()


def test_a_torn_journal_at_the_predecessor_is_removed_and_nothing_activates(tmp_path):
    from learnloop.superseded_claims_upgrade import complete_interrupted_activation

    paths = create_placement_vault(tmp_path / "torn", version=PREDECESSOR)
    _journal(paths).write_text('{"predecessor": "mvp-0.3', encoding="utf-8")
    assert complete_interrupted_activation(paths.root) is None
    assert not _journal(paths).exists() and _version(paths) == PREDECESSOR and not _activated(paths)


# -- Codex review (2026-10-27): one transaction per report, supersession order, attempt-free history --


def _attempt_count(repository) -> int:
    with closing(sqlite3.connect(repository.sqlite_path)) as connection:
        return int(connection.execute("SELECT COUNT(*) FROM practice_attempts").fetchone()[0])


def _rebuilds_to_live(paths, repository):
    live = _mastery(repository)
    diff = _shadow_summary(paths)
    assert diff["summary"] == ZERO, {family: diff[family]["changes"][:3] for family in ZERO}
    for _ in range(2):
        rebuild_all_derived_state(load_vault(paths.root), repository)
        assert _mastery(repository) == live
    return live


def test_two_writers_on_one_warm_lo_apply_their_reports_in_the_order_replay_reads(tmp_path, monkeypatch):
    """Review F1. Writer A commits its replacement claim and pauses before its
    re-anchor; writer B reports on the same LO meanwhile. The replacement, its
    application position and its re-anchor are one transaction, so B waits for
    A's whole report: live applies A then B, as replay does (before the fix B's
    claim and re-anchor landed between A's, and the precision-weighted merges
    ran in an order replay cannot see)."""

    import threading

    from learnloop.learner import mastery

    paths, vault, repository = _vault(tmp_path)
    _answer(vault, repository, "pi_diag_easy", minutes=1, points=1.0)
    paused, release = threading.Event(), threading.Event()
    original = mastery.reanchor_mastery_from_claim

    def pausing(*args, **kwargs):
        if threading.current_thread().name == "writer-a":
            paused.set()
            assert release.wait(10)
        return original(*args, **kwargs)

    monkeypatch.setattr(mastery, "reanchor_mastery_from_claim", pausing)
    failures: list[BaseException] = []
    _set_report_config(paths, 0.25)  # A's report and B's differ, so the order of their merges shows

    def writer(item_id, reason, minutes):
        try:
            retire_item(paths.root, Repository(paths.sqlite_path), practice_item_id=item_id, reason=reason,
                        clock=_at(minutes))
        except BaseException as failure:  # pragma: no cover - surfaced below
            failures.append(failure)

    a = threading.Thread(target=writer, args=("pi_diag_mid", "too_easy", 2), name="writer-a")
    b = threading.Thread(target=writer, args=("pi_diag_hard", "too_easy", 3), name="writer-b")
    a.start()
    assert paused.wait(10)
    _set_report_config(paths, 2.0, level=0.9)
    b.start()
    b.join(2)  # well inside the 5 s busy timeout: B is held at its transaction while A is open
    held = b.is_alive()
    release.set()
    a.join(10)
    b.join(10)
    assert not failures and not a.is_alive() and not b.is_alive()
    assert held, "writer B's report landed between writer A's replacement and its re-anchor"
    reports = [row for row in _rows(repository) if row["source"] == "learner_report"]
    assert len(reports) == 2 and reports[0]["superseded_by"] == reports[1]["id"]
    _rebuilds_to_live(paths, repository)


def test_a_failure_between_the_replacement_and_its_re_anchor_leaves_the_earlier_report_in_force(
    tmp_path, monkeypatch
):
    """Review F1, fault injection: the re-anchor fails after the replacement was
    written. Nothing of the report commits: the earlier report is still the one
    in force (no ``superseded_by``), no new claim is on record, and the vault
    still rebuilds to live."""

    from learnloop.learner import mastery

    paths, vault, repository = _vault(tmp_path)
    _answer(vault, repository, "pi_diag_easy", minutes=1, points=1.0)
    retire_item(paths.root, repository, practice_item_id="pi_diag_mid", reason="too_easy", clock=_at(2))
    before = _rows(repository)

    def failing(*args, **kwargs):
        raise RuntimeError("injected: the re-anchor fails")

    monkeypatch.setattr(mastery, "reanchor_mastery_from_claim", failing)
    with pytest.raises(RuntimeError, match="injected"):
        retire_item(paths.root, repository, practice_item_id="pi_diag_hard", reason="too_easy", clock=_at(3))
    monkeypatch.undo()
    assert _rows(repository) == before
    _rebuilds_to_live(paths, repository)


def _report_in_child(root, sqlite_path, item_id, reason, minutes, claim_id, conn):
    """A second process's report whose claim id sorts BEFORE the first process's (review F2):
    ULIDs are monotonic only within one process."""

    try:
        insert = Repository.insert_learner_claim

        def with_this_process_id(self, claim, **kwargs):
            return insert(self, {**claim, "id": claim_id}, **kwargs)

        Repository.insert_learner_claim = with_this_process_id  # the forked child only
        retire_item(root, Repository(sqlite_path), practice_item_id=item_id, reason=reason,
                    clock=_at(minutes))
        conn.send(None)
    except BaseException as failure:  # pragma: no cover - surfaced in the parent
        conn.send(repr(failure))
    finally:
        conn.close()


def test_a_replacement_from_another_process_whose_id_sorts_first_replays_after_the_claim_it_replaced(tmp_path):
    """Review F2. Two reports on one warm LO in the same second at the same
    attempt count, the second written by another process whose claim id sorts
    before the first's. Replay places the replacing claim after the claim it
    replaced (the supersession edge), whatever the ids say, so the two
    precision-weighted merges run in live's order."""

    paths, vault, repository = _vault(tmp_path)
    _answer(vault, repository, "pi_diag_easy", minutes=1, points=1.0)
    _set_report_config(paths, 0.25)
    retire_item(paths.root, repository, practice_item_id="pi_diag_mid", reason="too_easy", clock=_at(2))
    _set_report_config(paths, 2.0, level=0.9)
    (first,) = [row for row in _rows(repository) if row["source"] == "learner_report"]
    inverted = "0" * 26  # a valid id that sorts before every ULID
    assert inverted < first["id"]
    context = multiprocessing.get_context("fork")
    parent, child = context.Pipe(duplex=False)
    process = context.Process(target=_report_in_child,
                              args=(paths.root, paths.sqlite_path, "pi_diag_hard", "too_easy", 2, inverted, child))
    process.start()
    child.close()
    outcome = parent.recv()
    process.join(30)
    assert outcome is None, outcome
    reports = [row for row in _rows(repository) if row["source"] == "learner_report"]
    by_id = {row["id"]: row for row in reports}
    assert set(by_id) == {first["id"], inverted} and by_id[first["id"]]["superseded_by"] == inverted
    with closing(sqlite3.connect(repository.sqlite_path)) as connection:
        stamps = dict(connection.execute(
            "SELECT id, created_at || '/' || applied_after_attempts FROM learner_claims WHERE source = 'learner_report'"))
    assert stamps[first["id"]] == stamps[inverted]  # the tie only the edge can break
    _rebuilds_to_live(paths, repository)


def _set_report_config(paths, pseudo_count, level=0.70):
    """The vault's ``[rung_variants]`` report settings (a too_easy report claims ``harder_claim_level``)."""

    path = paths.root / "learnloop.toml"
    marker = "\n[rung_variants]\n"
    head = path.read_text().split(marker)[0]
    path.write_text(f"{head}{marker}claim_pseudo_count = {pseudo_count}\nharder_claim_level = {level}\n")


def test_two_retirements_on_an_lo_without_attempts_rebuild_to_the_variance_the_replaced_one_left(tmp_path):
    """Review F3. No attempt at all on the LO (retirements write none; rung
    requests would). The first retirement report at pseudo-count 0.25 seeds the
    row at variance 4; the second, after the setting moves to 2, replaces it.
    Live keeps 4 (a re-anchor never lowers a zero-evidence row's variance); the
    attempt-free rebuild reads the replaced claim's seed too, so it keeps 4 and
    does not manufacture certainty from no evidence."""

    paths, vault, repository = _vault(tmp_path)
    _set_report_config(paths, 0.25)
    retire_item(paths.root, repository, practice_item_id="pi_diag_mid", reason="too_easy", clock=_at(1))
    _set_report_config(paths, 2.0)
    retire_item(paths.root, repository, practice_item_id="pi_diag_hard", reason="too_easy", clock=_at(2))
    assert _attempt_count(repository) == 0
    reports = [row for row in _rows(repository) if row["source"] == "learner_report"]
    assert len(reports) == 2 and reports[0]["superseded_by"] == reports[1]["id"]
    live = _rebuilds_to_live(paths, repository)
    assert live["lo_diag"][1] == pytest.approx(4.0) and live["lo_diag"][2] == 0
