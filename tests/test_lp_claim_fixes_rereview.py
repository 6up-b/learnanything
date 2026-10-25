"""LP-min (a) Codex re-review (docs/reviews/lp-claim-fixes-codex-review.md, "Re-review").

F2 an interrupted activation is completed by every opener that may write the
vault, and every other attach refuses it, so nothing serves the successor's
label over the predecessor's state; F7 a claim keeps its place among the
attempts it was applied between, also when an attempt's id was reserved before
the claim and its grade committed after it; F8 a zero-evidence LO keeps the
variance its earlier claims left, in a rebuild as live; F9 the review a
diagnosis timeout resolves carries its claim line when reopened after the
deadline.
"""

from __future__ import annotations

from datetime import timedelta
import json

import pytest

from learnloop.algorithm_versions import CLAIM_FIXES_ALGORITHM_VERSION, SUCCESSOR_CHAIN
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.learner.mastery import reanchor_mastery_from_claim
from learnloop.ops.vault_upgrade import rewrite_algorithm_version
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

from tests.helpers import NOW
from tests.test_assumed_known import _answer
from tests.test_lp_claim_fixes_review import (
    ITEM,
    LO,
    _all_mastery,
    _crash_upgrade,
    _gap,
    _gap_claims,
    _iso,
    _journal,
    _mastery,
    _predecessor_vault_with_claims,
    _rebuild,
    _vault,
)

TAG = CLAIM_FIXES_ALGORITHM_VERSION
PREDECESSOR = SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1]


# ── F2: completed at every opener that may write; refused by every other ────


@pytest.fixture(autouse=True)
def _cli_process(monkeypatch):
    """This process as the CLI is: importing it installs the completion."""

    from learnloop import activation_journal
    from learnloop.cli.runtime import _complete_claim_fixes_activation

    monkeypatch.setattr(activation_journal, "_COMPLETER", _complete_claim_fixes_activation)


def _expected_after_activation(tmp_path):
    from learnloop.claim_fixes_upgrade import upgrade_to_claim_fixes

    clean = _predecessor_vault_with_claims(tmp_path, "clean")
    assert upgrade_to_claim_fixes(clean.root).upgraded
    return _all_mastery(clean.sqlite_path)


def _interrupted(tmp_path, name):
    """The state a death between the publication and the commit leaves.

    The successor's label over the predecessor's database, with the journal
    (``test_f2_a_death_between_publication_and_commit_is_completed_from_the_journal``
    produces it with a real death; this builds the same three facts directly)."""

    paths = _predecessor_vault_with_claims(tmp_path, name)
    _journal(paths).write_text(json.dumps({"predecessor": PREDECESSOR, "target": TAG}), encoding="utf-8")
    rewrite_algorithm_version(paths.root / "learnloop.toml", PREDECESSOR, TAG, durable=True)
    return paths


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
def test_f2_a_real_death_is_completed_by_the_next_cli_command(tmp_path):
    expected = _expected_after_activation(tmp_path)
    crashed = _predecessor_vault_with_claims(tmp_path, "crashed")
    _crash_upgrade(crashed)
    assert _journal(crashed).exists() and _all_mastery(crashed.sqlite_path) != expected

    _cli_command(crashed)

    assert _all_mastery(crashed.sqlite_path) == pytest.approx(expected)
    assert not _journal(crashed).exists()


@pytest.mark.parametrize("opener", sorted(OPENERS))
def test_f2_every_opener_that_may_write_completes_the_activation_first(tmp_path, opener):
    expected = _expected_after_activation(tmp_path)
    paths = _interrupted(tmp_path, "interrupted")
    assert _all_mastery(paths.sqlite_path) != expected

    OPENERS[opener](paths)

    assert _all_mastery(paths.sqlite_path) == pytest.approx(expected)
    assert not _journal(paths).exists()
    assert load_vault(paths.root).config.algorithms.algorithm_version == TAG


@pytest.mark.parametrize("opener", sorted(OPENERS))
def test_f2_an_activation_that_cannot_complete_stops_the_opener(tmp_path, monkeypatch, opener):
    import learnloop.claim_fixes_upgrade as upgrade
    from learnloop.activation_journal import InterruptedActivation

    paths = _interrupted(tmp_path, "interrupted")
    before = _all_mastery(paths.sqlite_path)

    def fail(*_args, **_kwargs):
        raise OSError("disk")

    monkeypatch.setattr(upgrade, "rebuild_all_derived_state", fail)
    if opener == "cli_command":
        from typer.testing import CliRunner

        from learnloop.cli import app

        result = CliRunner().invoke(app, ["backfill-originals", "--vault", str(paths.root)])
        assert result.exit_code != 0
        assert isinstance(result.exception, InterruptedActivation)
    else:
        with pytest.raises(InterruptedActivation, match=f"learnloop upgrade --to {TAG}"):
            OPENERS[opener](paths)

    # Nothing served, nothing half-applied: the journal stays for the next try.
    assert _all_mastery(paths.sqlite_path) == before
    assert _journal(paths).exists()


@pytest.mark.parametrize("opener", ["open_vault_repository", "vault_repository"])
def test_f2_an_opener_in_a_process_that_cannot_complete_refuses(tmp_path, monkeypatch, opener):
    """A TUI or a script installs no completion: its opener serves nothing."""

    from learnloop import activation_journal

    paths = _interrupted(tmp_path, "interrupted")
    before = _all_mastery(paths.sqlite_path)
    monkeypatch.setattr(activation_journal, "_COMPLETER", None)

    with pytest.raises(activation_journal.InterruptedActivation, match=f"learnloop upgrade --to {TAG}"):
        OPENERS[opener](paths)
    assert _all_mastery(paths.sqlite_path) == before and _journal(paths).exists()


@pytest.mark.parametrize(
    ("module", "installed"),
    [("learnloop.cli", True), ("learnloop_sidecar.context", True), ("learnloop.vault.repository", False)],
)
def test_f2_the_cli_and_the_sidecar_install_the_completion(module, installed):
    import subprocess
    import sys

    code = f"import {module}; from learnloop import activation_journal as j; print(j._COMPLETER is not None)"
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True, timeout=120)
    assert result.stdout.strip() == str(installed)


def test_f2_attaches_that_never_write_refuse_while_the_journal_stands(tmp_path):
    from learnloop.activation_journal import InterruptedActivation
    from learnloop.remote.runtime import RemoteRuntime, SchemaMismatch

    paths = _interrupted(tmp_path, "interrupted")

    # The database layer itself: a read-only report, a secondary process.
    for attach in (lambda: Repository.attach(paths.sqlite_path, read_only=True), lambda: Repository(paths.sqlite_path)):
        with pytest.raises(InterruptedActivation, match=f"learnloop upgrade --to {TAG}"):
            attach()
    # A read-only CLI report.
    from typer.testing import CliRunner

    from learnloop.cli import app

    result = CliRunner().invoke(app, ["gaps", "list", "--vault", str(paths.root), "--json"])
    assert result.exit_code != 0 and isinstance(result.exception, InterruptedActivation)
    # The MCP server's attach (it never migrates or completes).
    with pytest.raises(SchemaMismatch, match=f"learnloop upgrade --to {TAG}"):
        RemoteRuntime.attach(paths.root, load_environment=False)


def test_f2_an_mcp_server_already_attached_stops_serving_when_a_journal_appears(tmp_path):
    from learnloop.claim_fixes_upgrade import upgrade_to_claim_fixes
    from learnloop.remote.runtime import RemoteRuntime, SchemaMismatch

    paths = _predecessor_vault_with_claims(tmp_path, "vault")
    assert upgrade_to_claim_fixes(paths.root).upgraded
    runtime = RemoteRuntime.attach(paths.root, load_environment=False)
    assert runtime.vault() is not None

    _journal(paths).write_text(json.dumps({"predecessor": PREDECESSOR, "target": TAG}), encoding="utf-8")

    with pytest.raises(SchemaMismatch, match=f"learnloop upgrade --to {TAG}"):
        runtime.vault()


def test_f2_the_phone_host_refuses_to_start_while_the_journal_stands(tmp_path):
    pytest.importorskip("starlette")
    from learnloop_mobile.config import MobileConfig
    from learnloop_mobile.host import SchemaMismatch, attach

    paths = _interrupted(tmp_path, "interrupted")
    config = MobileConfig(enabled=True, vault=paths.root, hostname="carson.example.ts.net", owner_login="owner")
    with pytest.raises(SchemaMismatch, match=f"learnloop upgrade --to {TAG}"):
        attach(config)


# ── F7: the claim's place is where it was applied, not its id ───────────────


def _answer_with_reserved_id(vault, repository, monkeypatch, reserved, points, *, minutes):
    """An attempt whose id was minted before grading (production reserves it
    before the model call) and whose grade commits at ``minutes``."""

    import learnloop.attempts.attempts as attempts

    real = attempts.new_ulid
    handed = {"done": False}

    def reserved_first():
        if not handed["done"]:
            handed["done"] = True
            return reserved
        return real()

    monkeypatch.setattr(attempts, "new_ulid", reserved_first)
    try:
        result = _answer(vault, repository, ITEM, points, minutes=minutes)
    finally:
        monkeypatch.setattr(attempts, "new_ulid", real)
    assert result.attempt_id == reserved
    return result


def test_f7_an_attempt_reserved_before_a_gap_and_graded_after_it_replays_after_it(tmp_path, monkeypatch):
    paths, vault, repository = _vault(tmp_path)
    reserved = new_ulid()  # the attempt's id, minted when grading started
    _gap(paths.root, repository, minutes=5)  # the gap commits while grading runs
    _answer_with_reserved_id(vault, repository, monkeypatch, reserved, 1.0, minutes=5)

    (claim,) = _gap_claims(repository)
    (attempt,) = repository.list_attempts_by_learning_object(LO)
    # The order the review describes: one stamp, the attempt's id first.
    assert claim["created_at"] == attempt["created_at"] and attempt["id"] < claim["id"]
    live = _mastery(repository)

    assert _mastery(_rebuild(paths)) == pytest.approx(live, rel=1e-12, abs=1e-12)


def test_f7_the_claim_records_how_many_of_its_los_attempts_it_was_applied_after(tmp_path, monkeypatch):
    """With an earlier attempt: the raced vault rebuilds as the unraced one does.

    (Two attempts on one LO do not rebuild to their live row in this harness
    whatever the claims, so the raced rebuild is compared with the rebuild of
    the same history whose second attempt's id was minted after the gap.)"""

    rebuilt = {}
    for race in (True, False):
        paths, vault, repository = _vault(tmp_path, f"race_{race}")
        _answer(vault, repository, ITEM, 4.0, minutes=1)
        reserved = new_ulid()
        _gap(paths.root, repository, minutes=5)
        if race:
            _answer_with_reserved_id(vault, repository, monkeypatch, reserved, 1.0, minutes=5)
        else:
            _answer(vault, repository, ITEM, 1.0, minutes=5)
        (claim,) = _gap_claims(repository)
        assert claim["applied_after_attempts"] == 1
        rebuilt[race] = _mastery(_rebuild(paths))

    assert rebuilt[True] == pytest.approx(rebuilt[False], rel=1e-12, abs=1e-12)


@pytest.mark.parametrize("writer", ["too_easy_report", "rung_variant_request"])
def test_f7_every_reanchoring_writer_records_its_point(tmp_path, writer):
    paths, vault, repository = _vault(tmp_path)
    _answer(vault, repository, ITEM, 4.0, minutes=1)
    item = vault.practice_items[ITEM]
    clock = FrozenClock(NOW + timedelta(minutes=2))
    if writer == "too_easy_report":
        from learnloop.content.authoring.item_authoring import _apply_difficulty_report as report

        report(vault, repository, item, reason="too_easy", clock=clock)
        source = "learner_report"
    else:
        from learnloop.content.authoring.rung_variants import CLAIM_SOURCE

        _request_rung_variant(paths, vault, repository, item, clock)
        source = CLAIM_SOURCE
    (claim,) = [row for row in repository.learner_claims() if row["source"] == source]
    assert claim["applied_after_attempts"] == 1


def _request_rung_variant(paths, vault, repository, item, clock):
    from learnloop.content.authoring.rung_variants import request_rung_variant

    request_rung_variant(vault, repository, practice_item_id=item.id, direction="harder", clock=clock)


def test_f7_off_the_claim_records_nothing(tmp_path):
    paths, _vault_, repository = _vault(tmp_path, toml="[mastery]\nclaim_fixes_enabled = false\n")
    _gap(paths.root, repository, minutes=5)
    (claim,) = _gap_claims(repository)
    assert claim["applied_after_attempts"] is None


# ── F8: a zero-evidence LO keeps the variance its earlier claims left ───────


def _claim(vault, repository, *, source, pseudo_count, minutes, level=0.3):
    claim_id = repository.insert_learner_claim({
        "claim_type": "self_rating", "scope_type": "learning_object", "scope_id": LO, "evidence_family": "recall",
        "claimed_level": level, "prior_pseudo_count": pseudo_count, "source": source, "created_at": _iso(minutes),
    })
    return reanchor_mastery_from_claim(
        vault, repository, LO, claimed_level=level, prior_pseudo_count=pseudo_count, now_iso=_iso(minutes),
        claim_id=claim_id,
    )


def test_f8_two_claims_with_differing_pseudo_counts_keep_the_weak_claims_variance_in_a_rebuild(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    weak = _claim(vault, repository, source="learner_report", pseudo_count=0.25, minutes=1)
    assert weak.logit_variance == pytest.approx(4.0)
    later = _claim(vault, repository, source="rung_variant_request", pseudo_count=2.0, minutes=2, level=0.7)
    assert later.logit_variance == pytest.approx(4.0)  # live keeps the retained uncertainty
    live = _mastery(repository)

    assert _mastery(_rebuild(paths)) == pytest.approx(live, rel=1e-12, abs=1e-12)


def test_f8_the_first_replayed_attempt_starts_from_the_retained_variance(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    _claim(vault, repository, source="learner_report", pseudo_count=0.25, minutes=1)
    _claim(vault, repository, source="rung_variant_request", pseudo_count=2.0, minutes=2, level=0.7)
    _answer(vault, repository, ITEM, 4.0, minutes=5)
    live = _mastery(repository)

    assert _mastery(_rebuild(paths)) == pytest.approx(live, rel=1e-12, abs=1e-12)


def test_f8_activation_reseeds_with_the_retained_variance_as_a_rebuild_does(tmp_path):
    from learnloop.claim_fixes_upgrade import upgrade_to_claim_fixes

    paths, vault, repository = _vault(tmp_path, version=PREDECESSOR)
    for minutes, source, pseudo_count in ((1, "learner_report", 0.25), (2, "rung_variant_request", 2.0)):
        repository.insert_learner_claim({
            "claim_type": "self_rating", "scope_type": "learning_object", "scope_id": LO,
            "evidence_family": "recall", "claimed_level": 0.3, "prior_pseudo_count": pseudo_count,
            "source": source, "created_at": _iso(minutes),
        })
    assert upgrade_to_claim_fixes(paths.root).upgraded
    upgraded = _all_mastery(paths.sqlite_path)
    assert upgraded[LO][1] == pytest.approx(4.0)
    assert _all_mastery(_rebuild(paths).sqlite_path) == pytest.approx(upgraded)


# ── F9: a timeout-resolved review carries its line when reopened ────────────


def test_f9_a_miss_the_diagnosis_timeout_decides_carries_its_line_reopened_after_the_deadline(tmp_path, monkeypatch):
    import learnloop.clock as clock_module
    from learnloop.placement.claim_check import claim_check
    from learnloop.placement.decisions import record_self_report
    from learnloop.placement.rules import DIAGNOSIS_WAIT_DAYS
    from learnloop.placement.state import load_placement_state

    from tests.diagnosis_split_helpers import at
    from tests.split_live_helpers import drain_jobs, split_vault
    from tests.test_placement_diagnosis_decides import DUE_HOURS, LO as SPLIT_LO, _Diagnosed, _miss

    _paths, vault, repository = split_vault(tmp_path, version=TAG, seed=False)
    record_self_report(vault, repository, learning_object_ids=[SPLIT_LO], report="know_this", clock=FrozenClock(at(0)))
    miss = _miss(vault, repository, _Diagnosed(), drain=False)
    # The provider never comes: the diagnose job stays queued.
    drain_jobs(vault, repository, None, clock=FrozenClock(at(DUE_HOURS + 2)))
    deadline_hours = DUE_HOURS + 1 + 24 * DIAGNOSIS_WAIT_DAYS

    def now(hours):
        monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: at(hours))

    now(deadline_hours - 1)
    assert claim_check(vault, repository, miss.attempt_id) is None  # still waiting on the diagnosis

    now(deadline_hours + 1)
    (assumption,) = load_placement_state(vault, repository).assumptions
    assert (assumption.status, assumption.resolving_attempt_id) == ("failed", miss.attempt_id)
    assert claim_check(vault, repository, miss.attempt_id) == {
        "claim": "marked_known", "check": "missed", "line": "You marked this as known; this check: missed.",
    }
