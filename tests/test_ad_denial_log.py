"""The AD guard's denial log: cleared at upgrade, each line naming the refused operation.

Owner decision 2026-10-27 (``docs/reviews/ad-denial-log.md``):

* a successful ``learnloop upgrade --to <version>`` (chained steps included: once per command, after
  the final step) renames ``ad_guard_denials.jsonl`` to a dated archive beside it, so ``ad report``
  counts only the denials since the last upgrade; a failed or refused upgrade leaves the log in place;
  no log is a no-op; an archive is never overwritten;
* every new denial line records the refused operation's entry point (``entry``); lines written before
  it stay readable and are grouped as ``unrecorded``.

Fakes only: no network, no model call.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from learnloop.adaptive_difficulty import denial_log as D
from learnloop.adaptive_difficulty import operation as O
from learnloop.algorithm_versions import (
    CLAIM_FIXES_ALGORITHM_VERSION,
    ONE_ASK_ALGORITHM_VERSION,
    REPLAY_LEDGER_ALGORITHM_VERSION,
)
from learnloop.vault.loader import load_vault

TAG = ONE_ASK_ALGORITHM_VERSION
PREDECESSOR = REPLAY_LEDGER_ALGORITHM_VERSION
OLDER = CLAIM_FIXES_ALGORITHM_VERSION

OLD_LINE = {"epoch": "e1", "reader": "learnloop.adaptive_difficulty.replay", "table": "practice_attempts",
            "verb": "read", "why": "derived"}


@pytest.fixture(autouse=True)
def _cli_process(monkeypatch):
    """This process as the CLI is: importing it installs the journal completion."""

    from learnloop import activation_journal
    from learnloop.cli.runtime import _complete_interrupted_activation

    monkeypatch.setattr(activation_journal, "_COMPLETER", _complete_interrupted_activation)


def _vault_at(tmp_path, version):
    from tests.helpers import create_placement_vault

    return create_placement_vault(tmp_path / "v", version=version)


def _write_log(paths, lines) -> Path:
    log = D.denial_log_path(paths.sqlite_path)
    log.write_text("".join(json.dumps(line, sort_keys=True) + "\n" for line in lines), encoding="utf-8")
    return log


def _archives(paths) -> list[Path]:
    return D.archived_logs(paths.sqlite_path)


def _upgrade(paths, to):
    from learnloop.cli import app

    return CliRunner().invoke(app, ["upgrade", "--to", to, "--vault", str(paths.root)])


# -- 1. cleared at upgrade -------------------------------------------------------------------------


def test_a_successful_upgrade_archives_the_log_and_the_report_counts_from_zero(tmp_path):
    paths = _vault_at(tmp_path, PREDECESSOR)
    log = _write_log(paths, [OLD_LINE, {**OLD_LINE, "table": "mastery_ekf"}])
    before = log.read_text(encoding="utf-8")
    result = _upgrade(paths, TAG)
    assert result.exit_code == 0, result.output
    assert load_vault(paths.root).config.algorithms.algorithm_version == TAG
    assert not log.exists(), "the live log is moved aside"
    [archive] = _archives(paths)
    assert archive.parent == log.parent
    assert archive.name.startswith(f"ad_guard_denials.archived-{PREDECESSOR}-to-{TAG}-")
    assert archive.read_text(encoding="utf-8") == before, "archived, never rewritten or deleted"
    assert O.denial_count(paths.sqlite_path) == 0
    block = D.summary(paths.sqlite_path)
    assert block["denials"] == 0 and block["archived_denials"] == 2
    assert block["archived"] == [{"file": archive.name, "denials": 2}]


def test_a_chained_upgrade_archives_once_after_the_final_step(tmp_path):
    paths = _vault_at(tmp_path, OLDER)
    _write_log(paths, [OLD_LINE])
    result = _upgrade(paths, TAG)
    assert result.exit_code == 0, result.output
    [archive] = _archives(paths)
    assert archive.name.startswith(f"ad_guard_denials.archived-{OLDER}-to-{TAG}-")


def test_a_refused_upgrade_leaves_the_log_in_place(tmp_path):
    paths = _vault_at(tmp_path, PREDECESSOR)
    assert _upgrade(paths, TAG).exit_code == 0
    log = _write_log(paths, [OLD_LINE])
    result = _upgrade(paths, TAG)  # already at the tag: refused
    assert result.exit_code == 1 and f"vault is already {TAG}" in result.output, result.output
    unknown = _upgrade(paths, "mvp-0.99")  # an unknown target: refused before any step
    assert unknown.exit_code == 2, unknown.output
    assert log.exists() and _archives(paths) == []
    assert O.denial_count(paths.sqlite_path) == 1


def test_a_failed_upgrade_leaves_the_log_in_place(tmp_path, monkeypatch):
    from learnloop import one_ask_upgrade

    paths = _vault_at(tmp_path, PREDECESSOR)
    log = _write_log(paths, [OLD_LINE])

    def broken(*args, **kwargs):
        raise RuntimeError("activation failed")

    monkeypatch.setattr(one_ask_upgrade, "_activate", broken)
    result = _upgrade(paths, TAG)
    assert result.exit_code != 0
    assert log.exists() and _archives(paths) == []


def test_an_upgrade_without_a_log_archives_nothing(tmp_path):
    paths = _vault_at(tmp_path, PREDECESSOR)
    result = _upgrade(paths, TAG)
    assert result.exit_code == 0, result.output
    assert _archives(paths) == [] and not D.denial_log_path(paths.sqlite_path).exists()


def test_a_second_upgrade_never_overwrites_the_first_archive(tmp_path, monkeypatch):
    monkeypatch.setattr(D, "_stamp", lambda now: "20261027T000000Z")  # both upgrades in one second
    paths = _vault_at(tmp_path, OLDER)
    _write_log(paths, [OLD_LINE])
    assert _upgrade(paths, PREDECESSOR).exit_code == 0
    _write_log(paths, [{**OLD_LINE, "table": "second"}, {**OLD_LINE, "table": "third"}])
    assert _upgrade(paths, TAG).exit_code == 0
    first, second = _archives(paths)
    assert first.name == f"ad_guard_denials.archived-{OLDER}-to-{PREDECESSOR}-20261027T000000Z.jsonl"
    assert second.name == f"ad_guard_denials.archived-{PREDECESSOR}-to-{TAG}-20261027T000000Z.jsonl"
    assert len(first.read_text(encoding="utf-8").splitlines()) == 1


def test_an_archive_name_already_taken_gets_a_counter(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    now = datetime(2026, 10, 27, 12, 0, 0, tzinfo=UTC)
    log = D.denial_log_path(sqlite_path)
    log.write_text("first\n", encoding="utf-8")
    first = D.archive_denial_log(sqlite_path, from_version="a", to_version="b", now=now)
    log.write_text("second\n", encoding="utf-8")
    second = D.archive_denial_log(sqlite_path, from_version="a", to_version="b", now=now)
    assert first.name == "ad_guard_denials.archived-a-to-b-20261027T120000Z.jsonl"
    assert second.name == "ad_guard_denials.archived-a-to-b-20261027T120000Z-2.jsonl"
    assert first.read_text(encoding="utf-8") == "first\n" and second.read_text(encoding="utf-8") == "second\n"
    assert D.archive_denial_log(sqlite_path, from_version="a", to_version="b", now=now) is None, "no log: no-op"


# -- 2. each line names the refused operation -------------------------------------------------------


def test_a_new_denial_line_names_the_refused_operation(tmp_path, monkeypatch):
    from tests.test_ad_guard import _slot_serve

    seen: list[O.Operation] = []
    monkeypatch.setattr(O, "OBSERVERS", [seen.append])
    paths, _step, _rows = _slot_serve(tmp_path, monkeypatch, plant=True)
    refused = {op.guard.entry for op in seen if op.guard.denials and op.guard.mode != "observe"}
    lines = [json.loads(line) for line in D.denial_log_path(paths.sqlite_path).read_text(encoding="utf-8").splitlines()]
    assert lines, "the planted read is logged"
    for line in lines:
        assert isinstance(line.get("entry"), str) and line["entry"].startswith("learnloop."), line
        assert {"verb", "table", "why", "reader", "epoch"} <= set(line)
    assert {line["entry"] for line in lines} <= refused
    assert sum(D.summary(paths.sqlite_path)["by_entry"].values()) == len(lines)


def test_append_writes_the_entry_beside_the_refusal(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    entry = "learnloop.adaptive_difficulty.replay.load_events"
    D.append_denials(sqlite_path, [{"verb": "read", "table": "t", "why": "w", "reader": "r"}], epoch="e", entry=entry)
    [line] = D.denial_log_path(sqlite_path).read_text(encoding="utf-8").splitlines()
    assert json.loads(line) == {"verb": "read", "table": "t", "why": "w", "reader": "r", "epoch": "e", "entry": entry}


def test_old_format_lines_stay_readable_and_are_grouped_as_unrecorded(tmp_path):
    from learnloop.adaptive_difficulty.report import render_markdown

    sqlite_path = tmp_path / "state.sqlite"
    entry = "learnloop.adaptive_difficulty.replay.load_events"
    log = D.denial_log_path(sqlite_path)
    log.write_text(json.dumps(OLD_LINE) + "\n" + json.dumps({**OLD_LINE, "entry": entry}) + "\n"
                   + json.dumps({**OLD_LINE, "entry": entry, "table": "x"}) + "\n" + '{"verb": "re\n\n',
                   encoding="utf-8")
    assert O.denial_count(sqlite_path) == 4
    block = D.summary(sqlite_path)
    assert block["denials"] == 4
    assert block["by_entry"] == {entry: 2, D.UNRECORDED: 1, D.UNREADABLE: 1}
    report = {"generated_at": "now", "algorithm_version": TAG, "records": 0, "auto_flags": [], "honest_lines": [],
              "scores": {}, "dose_and_burden": {"lines": []}, "identifiability": {"statement": ""}, "guard": {**block, "archived": [{"file": "a.jsonl", "denials": 3}], "archived_denials": 3}}
    text = render_markdown(report)
    assert "refused 4 read(s) or write(s) since the last upgrade" in text
    assert f"{entry}: 2" in text and f"{D.UNRECORDED}: 1" in text
    assert "3 earlier denial(s) are archived (1 archive" in text


def test_the_report_renders_a_guard_block_without_entries(tmp_path):
    """A report built before the entry was recorded (``{"denials": n}`` only) still renders."""

    from learnloop.adaptive_difficulty.report import render_markdown

    report = {"generated_at": "now", "algorithm_version": TAG, "records": 0, "auto_flags": [], "honest_lines": [],
              "scores": {}, "dose_and_burden": {"lines": []}, "identifiability": {"statement": ""}, "guard": {"denials": 2}}
    assert "refused 2 read(s) or write(s) so far" in render_markdown(report)
