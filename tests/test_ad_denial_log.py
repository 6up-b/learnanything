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
    first = D.archive_denial_log(sqlite_path, from_version="a", to_version="b", mark=D.cutover_mark(sqlite_path),
                                 now=now)
    log.write_text("second\n", encoding="utf-8")
    second = D.archive_denial_log(sqlite_path, from_version="a", to_version="b",
                                  mark=D.cutover_mark(sqlite_path), now=now)
    assert first.name == "ad_guard_denials.archived-a-to-b-20261027T120000Z.jsonl"
    assert second.name == "ad_guard_denials.archived-a-to-b-20261027T120000Z-2.jsonl"
    assert first.read_text(encoding="utf-8") == "first\n" and second.read_text(encoding="utf-8") == "second\n"
    assert D.archive_denial_log(sqlite_path, from_version="a", to_version="b", mark=D.cutover_mark(sqlite_path),
                                now=now) is None, "no log: no-op"


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


# -- 3. Codex review F1/F2 (2026-10-27): the cutover never hides a later denial ----------------------

NEW_LINE = {"reader": "learnloop.adaptive_difficulty.replay", "table": "practice_attempts", "verb": "read",
            "why": "derived"}
SIDECAR_ENTRY = "learnloop.adaptive_difficulty.replay.load_events"


def test_f1_a_denial_after_the_upgrade_returned_stays_live(tmp_path, monkeypatch):
    """F1: the upgrade commits and releases its lock; a sidecar operation, under the successor, logs a
    denial before the CLI archives. That denial is after the upgrade: it stays in the live count."""

    from learnloop import one_ask_upgrade

    paths = _vault_at(tmp_path, PREDECESSOR)
    log = _write_log(paths, [OLD_LINE, {**OLD_LINE, "table": "mastery_ekf"}])
    before = log.read_text(encoding="utf-8")
    real = one_ask_upgrade.upgrade_to_one_ask

    def then_a_sidecar_denial(*args, **kwargs):
        result = real(*args, **kwargs)
        D.append_denials(paths.sqlite_path, [NEW_LINE], epoch="e2", entry=SIDECAR_ENTRY)
        return result

    monkeypatch.setattr(one_ask_upgrade, "upgrade_to_one_ask", then_a_sidecar_denial)
    result = _upgrade(paths, TAG)
    assert result.exit_code == 0, result.output
    [archive] = _archives(paths)
    assert archive.read_text(encoding="utf-8") == before, "only the lines from before the upgrade are archived"
    assert O.denial_count(paths.sqlite_path) == 1, "the successor's denial stays counted"
    [line] = log.read_text(encoding="utf-8").splitlines()
    assert json.loads(line)["entry"] == SIDECAR_ENTRY
    block = D.summary(paths.sqlite_path)
    assert (block["denials"], block["archived_denials"]) == (1, 2)


def test_f1_an_append_in_flight_never_writes_into_the_archive(tmp_path):
    """F1, overlapping variant: an appender is between its two lines when the upgrade archives. Its
    lines land in the live log (not through a handle into the renamed archive)."""

    import threading

    paths = _vault_at(tmp_path, PREDECESSOR)
    log = _write_log(paths, [OLD_LINE])
    before = log.read_text(encoding="utf-8")
    started, go = threading.Event(), threading.Event()

    def denials():
        yield {**NEW_LINE, "table": "first"}
        started.set()
        go.wait(30)
        yield {**NEW_LINE, "table": "second"}

    appender = threading.Thread(target=D.append_denials, args=(paths.sqlite_path, denials()),
                                kwargs={"epoch": "e2", "entry": SIDECAR_ENTRY})
    appender.start()
    try:
        assert started.wait(30)
        result = _upgrade(paths, TAG)
    finally:
        go.set()
        appender.join(30)
    assert result.exit_code == 0, result.output
    [archive] = _archives(paths)
    assert archive.read_text(encoding="utf-8") == before
    assert [json.loads(line)["table"] for line in log.read_text(encoding="utf-8").splitlines()] == ["first", "second"]


def test_f1_lines_appended_after_the_mark_stay_live_and_the_marked_ones_are_archived(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    log = D.denial_log_path(sqlite_path)
    log.write_text(json.dumps(OLD_LINE) + "\n" + '{"verb": "re', encoding="utf-8")  # a torn tail at the mark
    mark = D.cutover_mark(sqlite_path)
    D.append_denials(sqlite_path, [NEW_LINE], epoch="e2", entry=SIDECAR_ENTRY)
    archive = D.archive_denial_log(sqlite_path, from_version="a", to_version="b", mark=mark)
    assert archive.read_text(encoding="utf-8") == json.dumps(OLD_LINE) + "\n" + '{"verb": "re'
    [line] = D._lines(log)
    assert json.loads(line)["entry"] == SIDECAR_ENTRY, "the torn tail was ended: the new line stands alone"
    assert not log.with_name(D.LOG_NAME + ".tmp").exists()
    # A later log (another archival moved the marked lines) and no log at the mark: nothing archived.
    assert D.archive_denial_log(sqlite_path, from_version="a", to_version="b", mark=mark) is None
    fresh = tmp_path / "fresh" / "state.sqlite"
    fresh.parent.mkdir()
    empty = D.cutover_mark(fresh)
    D.append_denials(fresh, [NEW_LINE], epoch="e2", entry=SIDECAR_ENTRY)
    assert D.archive_denial_log(fresh, from_version="a", to_version="b", mark=empty) is None
    assert D.denial_count(fresh) == 1


def test_f1_the_archival_waits_for_an_append_holding_the_log_lock(tmp_path):
    """Appends and the archival share the log's leaf lock (a second open file description, as another
    process's): the archival does not run while an append holds it."""

    import threading

    sqlite_path = tmp_path / "state.sqlite"
    D.denial_log_path(sqlite_path).write_text(json.dumps(OLD_LINE) + "\n", encoding="utf-8")
    mark = D.cutover_mark(sqlite_path)
    done = threading.Event()
    out: list = []

    def archive():
        out.append(D.archive_denial_log(sqlite_path, from_version="a", to_version="b", mark=mark))
        done.set()

    worker = threading.Thread(target=archive)
    with D._log_lock(sqlite_path):
        worker.start()
        assert not done.wait(0.3), "the archival ran while the log lock was held"
    worker.join(30)
    assert done.is_set() and out[0] is not None and D.denial_count(sqlite_path) == 0


def test_f2_a_report_never_counts_a_line_live_and_archived(tmp_path, monkeypatch):
    """F2: an upgrade archiving between the live read and the archive listing. The report is read
    under the log lock, so the archival waits and the snapshot counts each line once."""

    import threading

    sqlite_path = tmp_path / "state.sqlite"
    D.denial_log_path(sqlite_path).write_text(json.dumps(OLD_LINE) + "\n" + json.dumps(OLD_LINE) + "\n",
                                              encoding="utf-8")
    mark = D.cutover_mark(sqlite_path)
    real_lines = D._lines
    workers: list[threading.Thread] = []

    def lines_then_an_upgrade(path):
        out = real_lines(path)
        if path.name == D.LOG_NAME and not workers:
            worker = threading.Thread(target=D.archive_denial_log, args=(sqlite_path,),
                                      kwargs={"from_version": "a", "to_version": "b", "mark": mark})
            workers.append(worker)
            worker.start()
            worker.join(0.5)  # an unlocked report lets the archival finish here
        return out

    monkeypatch.setattr(D, "_lines", lines_then_an_upgrade)
    block = D.summary(sqlite_path)
    for worker in workers:
        worker.join(30)
    assert block["denials"] + block["archived_denials"] == 2, block
    monkeypatch.setattr(D, "_lines", real_lines)
    after = D.summary(sqlite_path)
    assert (after["denials"], after["archived_denials"]) == (0, 2)


# -- 4. Codex verify 2 (2026-10-27): a degraded path never hides a line ------------------------------


def test_v2_f1_an_unmarked_upgrade_leaves_the_log_live(tmp_path, monkeypatch):
    """Verify 2 F1: the mark fails at the command's start. Without a mark the archival cannot tell the
    lines from before the upgrade from a successor's, so it archives nothing and says so on stderr."""

    from learnloop import one_ask_upgrade

    paths = _vault_at(tmp_path, PREDECESSOR)
    log = _write_log(paths, [OLD_LINE, {**OLD_LINE, "table": "mastery_ekf"}])

    def unmarkable(sqlite_path):
        raise OSError("lock directory unavailable")

    real = one_ask_upgrade.upgrade_to_one_ask

    def then_a_sidecar_denial(*args, **kwargs):
        result = real(*args, **kwargs)
        D.append_denials(paths.sqlite_path, [NEW_LINE], epoch="e2", entry=SIDECAR_ENTRY)
        return result

    monkeypatch.setattr(D, "cutover_mark", unmarkable)
    monkeypatch.setattr(one_ask_upgrade, "upgrade_to_one_ask", then_a_sidecar_denial)
    result = _upgrade(paths, TAG)
    assert result.exit_code == 0, result.output
    assert load_vault(paths.root).config.algorithms.algorithm_version == TAG
    assert _archives(paths) == [], "no mark: nothing archived"
    assert O.denial_count(paths.sqlite_path) == 3, "the successor's denial (and the earlier ones) stay live"
    assert json.loads(D._lines(log)[-1])["entry"] == SIDECAR_ENTRY
    assert "AD guard denial log not archived" in result.output
    # The module agrees: no mark, no archive.
    assert D.archive_denial_log(paths.sqlite_path, from_version="a", to_version="b", mark=None) is None
    assert O.denial_count(paths.sqlite_path) == 3 and _archives(paths) == []


def _split_log(sqlite_path) -> tuple[D.Cutover, bytes]:
    """A live log with two marked lines and one appended after the mark (so the archival splits)."""

    log = D.denial_log_path(sqlite_path)
    log.write_text(json.dumps(OLD_LINE) + "\n" + json.dumps({**OLD_LINE, "table": "mastery_ekf"}) + "\n",
                   encoding="utf-8")
    mark = D.cutover_mark(sqlite_path)
    D.append_denials(sqlite_path, [NEW_LINE], epoch="e2", entry=SIDECAR_ENTRY)
    return mark, log.read_bytes()


def _short_writes(monkeypatch, *, at: int, then: str) -> list[int]:
    """os.write as under RLIMIT_FSIZE or a full disk: call number ``at`` writes a 64-byte prefix and
    returns its length; later calls write normally (``then="resume"``) or raise EFBIG (``"fail"``)."""

    import errno
    import os

    real = os.write
    calls: list[int] = []

    def write(fd, data):
        calls.append(len(data))
        n = len(calls) - 1
        if n < at or (n > at and then == "resume"):
            return real(fd, data)
        if n == at:
            return real(fd, bytes(data[:64]))
        raise OSError(errno.EFBIG, "File too large")

    monkeypatch.setattr(D.os, "write", write)
    return calls


@pytest.mark.parametrize("at", [0, 1], ids=["archive", "staging"])
def test_v2_a_short_write_that_resumes_completes_every_byte(tmp_path, monkeypatch, at):
    """Verify 2 (new Medium): os.write may write fewer bytes than asked. Each write is looped until
    every byte is down: the archive holds every marked line and the live log every later one."""

    sqlite_path = tmp_path / "state.sqlite"
    mark, before = _split_log(sqlite_path)
    cut = mark.length
    _short_writes(monkeypatch, at=at, then="resume")
    archive = D.archive_denial_log(sqlite_path, from_version="a", to_version="b", mark=mark)
    monkeypatch.undo()
    assert archive.read_bytes() == before[:cut]
    assert D.denial_log_path(sqlite_path).read_bytes() == before[cut:]
    assert not D.denial_log_path(sqlite_path).with_name(D.LOG_NAME + ".tmp").exists()


@pytest.mark.parametrize("at", [0, 1], ids=["archive", "staging"])
def test_v2_a_failed_write_keeps_the_live_log_and_removes_what_it_created(tmp_path, monkeypatch, at):
    """Verify 2 (new Medium): a write that cannot finish (EFBIG after a short write) fails the
    archival. The live log is untouched, and the partial archive and staging file are removed."""

    sqlite_path = tmp_path / "state.sqlite"
    log = D.denial_log_path(sqlite_path)
    mark, before = _split_log(sqlite_path)
    _short_writes(monkeypatch, at=at, then="fail")
    with pytest.raises(OSError):
        D.archive_denial_log(sqlite_path, from_version="a", to_version="b", mark=mark)
    monkeypatch.undo()
    assert log.read_bytes() == before, "the live log is untouched"
    assert D.archived_logs(sqlite_path) == [], "no partial archive"
    assert not log.with_name(D.LOG_NAME + ".tmp").exists(), "no staging file"
    assert D.denial_count(sqlite_path) == 3


def test_v2_a_failed_archival_never_touches_an_existing_archive(tmp_path, monkeypatch):
    sqlite_path = tmp_path / "state.sqlite"
    now = datetime(2026, 10, 27, 12, 0, 0, tzinfo=UTC)
    D.denial_log_path(sqlite_path).write_text("first\n", encoding="utf-8")
    first = D.archive_denial_log(sqlite_path, from_version="a", to_version="b", mark=D.cutover_mark(sqlite_path),
                                 now=now)
    mark, before = _split_log(sqlite_path)
    _short_writes(monkeypatch, at=1, then="fail")
    with pytest.raises(OSError):
        D.archive_denial_log(sqlite_path, from_version="a", to_version="b", mark=mark, now=now)
    monkeypatch.undo()
    assert D.archived_logs(sqlite_path) == [first] and first.read_text(encoding="utf-8") == "first\n"
    assert D.denial_log_path(sqlite_path).read_bytes() == before


def test_v2_f2_a_report_without_the_lock_does_not_count_archives(tmp_path, monkeypatch):
    """Verify 2 F2: the lock cannot be taken. The report gives the live count and marks the archive
    count unavailable, so a line moved by an archival between the two reads is never counted twice."""

    import os
    from contextlib import contextmanager

    from learnloop.adaptive_difficulty.report import render_markdown

    sqlite_path = tmp_path / "state.sqlite"
    log = D.denial_log_path(sqlite_path)
    log.write_text(json.dumps(OLD_LINE) + "\n" + json.dumps(OLD_LINE) + "\n", encoding="utf-8")

    @contextmanager
    def no_lock(path):
        raise PermissionError("lock not writable")
        yield  # pragma: no cover

    real_lines = D._lines

    def lines_then_an_archival(path):
        out = real_lines(path)
        if path == log:  # another process archives between the live read and the archive listing
            os.rename(log, log.with_name("ad_guard_denials.archived-a-to-b-20261027T120000Z.jsonl"))
        return out

    monkeypatch.setattr(D, "_log_lock", no_lock)
    monkeypatch.setattr(D, "_lines", lines_then_an_archival)
    block = D.summary(sqlite_path)
    monkeypatch.undo()
    assert block["denials"] == 2
    assert block["archived"] is None and block["archived_denials"] is None, block
    assert block["archived_unavailable"]
    report = {"generated_at": "now", "algorithm_version": TAG, "records": 0, "auto_flags": [], "honest_lines": [],
              "scores": {}, "dose_and_burden": {"lines": []}, "identifiability": {"statement": ""}, "guard": block}
    text = render_markdown(report)
    assert "refused 2 read(s) or write(s)" in text and "archive counts unavailable" in text
    assert "are archived" not in text
