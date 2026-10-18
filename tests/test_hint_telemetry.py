"""Adaptive hints H0: authored-hint reveal telemetry (spec_adaptive_hints_v1
§9 "H0's authored-reveal rows", §10 H0, G-H1's telemetry clause, G-H10).

``practice.record_hint_reveal`` writes one ``help_assists`` row per authored
hint the practice screen reveals (which hint, when, a hash and length of the
draft); ``submit_attempt`` and ``submit_dont_know`` attach the session's rows
for the item to the attempt. Telemetry only: the attempt's ``hints_used``,
``primed``, reveal events and every evidence table are byte-identical with
the telemetry on or off, and replay never reads the table. Fakes only: the
vault is the tests' basic vault, graded by self-grade (no provider at all).
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

import learnloop.clock as clock_module
import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
import learnloop_sidecar.handlers.practice as practice
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import help_assists as store
from learnloop.hints import telemetry
from learnloop.vault.hashes import practice_item_hash
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.helpers import append_config_toml, create_basic_vault

ITEM = "pi_svd_define_001"
FROZEN = datetime(2026, 10, 17, 9, 0, tzinfo=UTC)
TELEMETRY_OFF = "[hints]\ntelemetry_enabled = false\n"
SELF_GRADE = {"criterionPoints": {"correctness": 4}, "confidence": 4}


def _call(ctx, name: str, params: dict):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _vault(tmp_path: Path, *, config: str = "", hints: list[str] | None = None, name: str = "vault"):
    paths = create_basic_vault(tmp_path / name)
    if hints is not None:
        item_path = paths.practice_item_path("linear-algebra", ITEM)
        data = read_yaml(item_path)
        data["hints"] = hints
        data["hint_policy"] = {**data["hint_policy"], "max_useful_hints": len(hints)}
        write_yaml(item_path, data)
    if config:
        append_config_toml(paths.root, config)
    return paths


def _sidecar(root: Path):
    ctx = SidecarContext()
    ctx.load(root)
    ctx.grading_provider_override = "manual"
    session = _call(ctx, "start_session", {"energy": "medium"})
    return ctx, session["sessionId"]


def _reveal(ctx, session_id: str, index: int, *, answer: str = "", at: str | None = None, item: str = ITEM):
    params = {"sessionId": session_id, "practiceItemId": item, "authoredIndex": index, "answerMd": answer}
    if at is not None:
        params["revealedAt"] = at
    return _call(ctx, "practice.record_hint_reveal", params)


def _submit(ctx, session_id: str, *, hints: int, key: str, answer: str = "A = U Sigma V^T."):
    return _call(ctx, "submit_attempt", {
        "sessionId": session_id, "practiceItemId": ITEM, "answerMd": answer,
        "attemptType": "hinted_attempt" if hints else "independent_attempt", "hintsUsed": hints,
        "selfGrade": SELF_GRADE, "submissionId": key,
    })


def _rows(database: Path) -> list[dict]:
    with closing(sqlite3.connect(database)) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute("SELECT * FROM help_assists ORDER BY requested_at, id")]


@pytest.fixture
def frozen(monkeypatch):
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: FROZEN)
    return FROZEN


# -- the row --------------------------------------------------------------------------


def test_a_reveal_writes_one_authored_hint_row(tmp_path, frozen):
    paths = _vault(tmp_path)
    ctx, session_id = _sidecar(paths.root)
    answer = "U and V are orthogonal"
    result = _reveal(ctx, session_id, 0, answer=answer, at="2026-10-17T08:59:58.250Z")
    assert result["recorded"] is True and result["reason"] is None and result["assistId"].startswith("ha_")
    [row] = _rows(paths.sqlite_path)
    item = load_vault(paths.root).practice_items[ITEM]
    assert row["id"] == result["assistId"]
    assert {key: row[key] for key in (
        "surface", "assist_kind", "hint_kind", "level", "chooser", "counted_by", "shown", "authored_index",
        "practice_item_id", "practice_session_id", "attempt_id", "body_md", "requested_at", "shown_at",
    )} == {
        "surface": "practice", "assist_kind": "hint", "hint_kind": "authored", "level": 3, "chooser": "none",
        "counted_by": "client", "shown": 1, "authored_index": 0, "practice_item_id": ITEM,
        "practice_session_id": session_id, "attempt_id": None, "body_md": None,
        "requested_at": "2026-10-17T08:59:58.250Z", "shown_at": "2026-10-17T08:59:58.250Z",
    }
    assert row["practice_item_hash"] == practice_item_hash(item)
    assert row["work_hash"] == hashlib.sha256(answer.encode()).hexdigest() and row["work_chars"] == len(answer)
    # The draft itself is never stored, and every later phase's column is empty.
    assert answer not in json.dumps(row)
    filled = {key for key, value in row.items() if value is not None}
    assert filled == {
        "id", "surface", "assist_kind", "practice_item_id", "practice_item_hash", "practice_session_id",
        "hint_kind", "level", "authored_index", "work_hash", "work_chars", "chooser", "shown", "counted_by",
        "requested_at", "shown_at",
    }


@pytest.mark.parametrize(("sent", "stored"), [
    ("2026-10-17T08:30:00Z", "2026-10-17T08:30:00.000Z"),       # the client's press time
    ("2026-10-17T09:30:00+01:00", "2026-10-17T08:30:00.000Z"),  # any offset, stored in UTC
    ("2026-10-17T09:00:50Z", "2026-10-17T09:00:50.000Z"),       # a little ahead: clock skew
    ("2026-10-17T09:05:00Z", "2026-10-17T09:00:00.000Z"),       # far ahead: the sidecar's time
    ("not a time", "2026-10-17T09:00:00.000Z"),
    (None, "2026-10-17T09:00:00.000Z"),
])
def test_timing_is_the_press_unless_it_cannot_be_believed(tmp_path, frozen, sent, stored):
    paths = _vault(tmp_path)
    ctx, session_id = _sidecar(paths.root)
    _reveal(ctx, session_id, 0, at=sent)
    [row] = _rows(paths.sqlite_path)
    assert row["requested_at"] == row["shown_at"] == stored


def test_the_rpc_validates_the_item_and_the_index(tmp_path):
    paths = _vault(tmp_path)
    ctx, session_id = _sidecar(paths.root)
    with pytest.raises(SidecarError) as unknown:
        _reveal(ctx, session_id, 0, item="pi_missing")
    assert unknown.value.code == "not_found"
    with pytest.raises(SidecarError) as past:
        _reveal(ctx, session_id, 1)  # the item has one authored hint
    assert past.value.code == "validation_error"
    with pytest.raises(ValueError):
        _reveal(ctx, session_id, -1)
    assert _rows(paths.sqlite_path) == []


# -- attempt_id at submit -------------------------------------------------------------


def test_submit_attaches_the_sessions_rows_for_the_item_and_keeps_the_clients_count(tmp_path):
    paths = _vault(tmp_path, hints=["Name the three factors.", "U Sigma V^T."])
    ctx, session_id = _sidecar(paths.root)
    _reveal(ctx, session_id, 0)
    _reveal(ctx, session_id, 1)
    # The client counts one (say, a restore lost a reveal): the attempt keeps
    # the client's count, never the rows' (telemetry only, §9).
    payload = _submit(ctx, session_id, hints=1, key="k1")
    attempt = Repository(paths.sqlite_path).fetch_practice_attempt(payload["attemptId"])
    assert attempt["hints_used"] == 1
    rows = _rows(paths.sqlite_path)
    assert [row["attempt_id"] for row in rows] == [payload["attemptId"]] * 2
    # A retried submit answers from its receipt and moves nothing.
    assert _submit(ctx, session_id, hints=1, key="k1")["attemptId"] == payload["attemptId"]
    # The next attempt in the session gets only the rows revealed since.
    _reveal(ctx, session_id, 0)
    second = _submit(ctx, session_id, hints=1, key="k2")
    assert [row["attempt_id"] for row in _rows(paths.sqlite_path)] == [payload["attemptId"]] * 2 + [second["attemptId"]]


def test_submit_never_attaches_another_sessions_or_items_rows(tmp_path):
    paths = _vault(tmp_path)
    ctx, session_id = _sidecar(paths.root)
    _reveal(ctx, session_id, 0)
    other_session = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    with connect(paths.sqlite_path) as connection:
        store.insert_assist(connection, {
            "id": "ha_other_item", "surface": "practice", "assist_kind": "hint", "practice_item_id": "pi_other",
            "practice_session_id": other_session, "chooser": "none", "shown": 1, "requested_at": "2026-10-17T09:00:00Z",
        })
    payload = _submit(ctx, other_session, hints=0, key="k-other")
    rows = {row["id"]: row["attempt_id"] for row in _rows(paths.sqlite_path)}
    assert rows["ha_other_item"] is None
    assert [attempt for row_id, attempt in rows.items() if row_id != "ha_other_item"] == [None]
    assert payload["attemptId"]


def test_dont_know_attaches_the_rows_too(tmp_path):
    paths = _vault(tmp_path)
    ctx, session_id = _sidecar(paths.root)
    _reveal(ctx, session_id, 0)
    payload = _call(ctx, "submit_dont_know", {"sessionId": session_id, "practiceItemId": ITEM, "hintsUsed": 1})
    attempt = Repository(paths.sqlite_path).fetch_practice_attempt(payload["attemptId"])
    assert attempt["attempt_type"] == "dont_know" and attempt["hints_used"] == 1
    assert [row["attempt_id"] for row in _rows(paths.sqlite_path)] == [payload["attemptId"]]


def test_an_empty_stuck_answer_attaches_the_rows_too(tmp_path):
    from tests.helpers import set_algorithm_version

    paths = _vault(tmp_path)
    set_algorithm_version(paths, "mvp-0.13")
    ctx, session_id = _sidecar(paths.root)
    _reveal(ctx, session_id, 0)
    payload = _call(ctx, "submit_attempt", {
        "sessionId": session_id, "practiceItemId": ITEM, "answerMd": "", "attemptType": "hinted_attempt",
        "hintsUsed": 1, "declaredStuck": True, "submissionId": "stuck-1",
    })
    assert [row["attempt_id"] for row in _rows(paths.sqlite_path)] == [payload["attemptId"]]


# -- refusals and the kill switch -----------------------------------------------------


def test_no_row_during_a_diagnostic_block(tmp_path, monkeypatch):
    paths = _vault(tmp_path)
    ctx, session_id = _sidecar(paths.root)
    monkeypatch.setattr(practice, "_in_diagnostic_block", lambda repository, item: True)
    result = _reveal(ctx, session_id, 0)
    assert (result["recorded"], result["reason"]) == (False, "diagnostic_block")
    assert _rows(paths.sqlite_path) == []


@pytest.mark.parametrize(("episode", "presentation", "blocked"), [
    (None, None, False),
    ("pending_items", "served", False),
    ("in_progress", None, False),
    ("in_progress", "selected", False),  # committed but not shown as a probe: an ordinary card
    ("in_progress", "served", True),
])
def test_the_diagnostic_block_is_a_served_probe_of_this_item(episode, presentation, blocked):
    asked: list[tuple] = []

    def active(episode_id, practice_item_id=None):
        asked.append((episode_id, practice_item_id))
        return None if presentation is None else SimpleNamespace(status=presentation)

    repository = SimpleNamespace(
        open_probe_episode=lambda lo: None if episode is None else SimpleNamespace(id="ep", status=episode),
        active_probe_presentation=active,
    )
    item = SimpleNamespace(id=ITEM, learning_object_id="lo_svd_definition")
    assert practice._in_diagnostic_block(repository, item) is blocked
    if episode == "in_progress":
        assert asked == [("ep", ITEM)]


def test_kill_switch_writes_nothing_and_the_rpc_is_a_no_op(tmp_path, monkeypatch):
    paths = _vault(tmp_path, config=TELEMETRY_OFF)
    ctx, session_id = _sidecar(paths.root)
    assert load_vault(paths.root).config.hints.telemetry_enabled is False

    def forbidden(*args, **kwargs):
        raise AssertionError("telemetry off: no help_assists access")

    monkeypatch.setattr(practice, "record_authored_reveal", forbidden)
    monkeypatch.setattr(practice, "attach_reveals_to_attempt", forbidden)
    result = _reveal(ctx, session_id, 0)
    assert result == {"version": 1, "recorded": False, "reason": "telemetry_disabled", "assistId": None}
    # Off, the RPC answers before it looks at its input at all.
    assert _reveal(ctx, session_id, 7, item="pi_missing")["recorded"] is False
    _submit(ctx, session_id, hints=1, key="k1")
    _call(ctx, "submit_dont_know", {"sessionId": session_id, "practiceItemId": ITEM, "hintsUsed": 1})
    assert _rows(paths.sqlite_path) == []


def test_a_failed_write_never_fails_the_reveal_or_the_submit(tmp_path, monkeypatch):
    paths = _vault(tmp_path)
    ctx, session_id = _sidecar(paths.root)

    def broken(*args, **kwargs):
        raise sqlite3.OperationalError("disk I/O error")

    monkeypatch.setattr(store, "insert_assist", broken)
    result = _reveal(ctx, session_id, 0)
    assert (result["recorded"], result["reason"]) == (False, "write_failed")
    monkeypatch.setattr(practice, "attach_reveals_to_attempt", broken)
    payload = _submit(ctx, session_id, hints=1, key="k1")
    assert Repository(paths.sqlite_path).fetch_practice_attempt(payload["attemptId"])["hints_used"] == 1


# -- no evidence change (G-H1's telemetry clause; §5, H1) ------------------------------

_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_ISO = re.compile(r"\d{4}-\d\d-\d\d[T ]\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)?")


def _scrub(value, root: Path | None = None) -> str:
    """Two runs' records as text, with only what differs between any two runs
    replaced: the vault's path and the wall clock some writers read directly
    (ids are made deterministic by ``_deterministic_ids``)."""

    text = json.dumps(value, sort_keys=True, default=str)
    if root is not None:
        text = text.replace(str(root.resolve()), "<root>").replace(str(root), "<root>")
    return _ISO.sub("<t>", _UUID.sub("<uuid>", text))


def _deterministic_ids(monkeypatch) -> None:
    """Every ULID from one counter, restarted per run, so both runs mint the
    same ids (receipt digests and id-seeded intervals follow them). The
    telemetry's own ids come from a counter of their own, so the rows it
    writes with the switch on never shift the ids anything else gets."""

    import learnloop.ids as ids

    counter = iter(range(1, 10**9))
    monkeypatch.setattr(ids, "_wall_clock_ms", lambda: 1_792_000_000_000)
    monkeypatch.setattr(ids, "secrets", SimpleNamespace(randbits=lambda bits: next(counter)))
    monkeypatch.setattr(ids, "_last_timestamp_ms", -1)
    monkeypatch.setattr(ids, "_last_randomness", 0)
    own = iter(range(1, 10**9))
    monkeypatch.setattr(telemetry, "new_ulid", lambda: f"TELEMETRY{next(own):017d}")


def _dump(database: Path) -> dict[str, list[str]]:
    with closing(sqlite3.connect(database)) as connection:
        tables = [name for (name,) in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        return {
            table: sorted(_scrub(list(row), database.parent) for row in connection.execute(f'SELECT * FROM "{table}"'))
            for table in tables if table != "help_assists"
        }


def _scenario(root: Path, monkeypatch) -> list[str]:
    """Reveal, draft, submit; reveal, don't know: the screen's calls, in order."""

    _deterministic_ids(monkeypatch)
    ctx = SidecarContext()
    ctx.load(root)
    ctx.grading_provider_override = "manual"
    session_id = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    responses = [_call(ctx, "get_practice_item", {"practiceItemId": ITEM, "sessionId": session_id})]
    _reveal(ctx, session_id, 0, answer="U, Sigma", at="2026-10-17T08:59:00Z")
    responses.append(_call(ctx, "save_practice_draft", {
        "sessionId": session_id, "practiceItemId": ITEM, "answerMd": "U, Sigma", "hintsUsed": 1,
        "submissionId": "k1"}))
    responses.append(_submit(ctx, session_id, hints=1, key="k1"))
    responses.append(_call(ctx, "acknowledge_practice_submission", {
        "sessionId": session_id, "practiceItemId": ITEM, "submissionId": "k1"}))
    _reveal(ctx, session_id, 0, at="2026-10-17T08:59:30Z")
    responses.append(_call(ctx, "submit_dont_know", {
        "sessionId": session_id, "practiceItemId": ITEM, "hintsUsed": 1, "submissionId": "k2"}))
    responses.append(_call(ctx, "get_session", {"sessionId": session_id}))
    return [_scrub(response, root) for response in responses]


def test_hints_used_primed_reveals_and_evidence_are_identical_with_telemetry_on_or_off(
    tmp_path, frozen, monkeypatch
):
    on = _vault(tmp_path, name="on")
    off = _vault(tmp_path, name="off", config=TELEMETRY_OFF)
    # A first run in a process does one-time work a later one does not (it
    # mints ids), so both compared runs follow a discarded one.
    _scenario(_vault(tmp_path, name="warm").root, monkeypatch)
    on_responses = _scenario(on.root, monkeypatch)
    off_responses = _scenario(off.root, monkeypatch)
    assert on_responses == off_responses
    assert len(_rows(on.sqlite_path)) == 2 and _rows(off.sqlite_path) == []
    on_dump, off_dump = _dump(on.sqlite_path), _dump(off.sqlite_path)
    assert set(on_dump) == set(off_dump)
    differing = sorted(table for table in on_dump if on_dump[table] != off_dump[table])
    assert differing == []
    with closing(sqlite3.connect(on.sqlite_path)) as connection:
        attempts = connection.execute(
            "SELECT attempt_type, hints_used, primed FROM practice_attempts ORDER BY created_at, id").fetchall()
        reveals = connection.execute("SELECT COUNT(*) FROM reveal_events").fetchone()[0]
    assert attempts == [("hinted_attempt", 1, 0), ("dont_know", 1, 0)]
    assert reveals == 0  # authored reveals still write no reveal row (§10.1 successor 3)


# -- G-H10: replay never reads it, and calls no model ---------------------------------


def test_rebuild_with_help_assists_populated_calls_no_model_and_never_reads_it(tmp_path, monkeypatch, frozen):
    from learnloop.ai import client
    from learnloop.ai.providers.openai_embedding import OpenAIEmbeddingProviderClient
    from learnloop.db.copies import copy_tree_with_databases
    from learnloop.db.table_roles import TableRole, tables_for_role
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
    from learnloop.substrate.shadow_rebuild import shadow_rebuild

    paths = _vault(tmp_path, hints=["Name the three factors.", "U Sigma V^T."])
    ctx, session_id = _sidecar(paths.root)
    for index in (0, 1):
        _reveal(ctx, session_id, index)
    _submit(ctx, session_id, hints=2, key="k1")
    _reveal(ctx, session_id, 0)  # an unattached row too
    assert len(_rows(paths.sqlite_path)) == 3

    def forbidden(*args, **kwargs):
        raise AssertionError("replay must not construct a model or embedding client")

    monkeypatch.setattr(client, "make_ai_provider_client", forbidden)
    monkeypatch.setattr(client, "make_ai_provider_client_from_profile", forbidden)
    monkeypatch.setattr("learnloop.ai.routing.ready_client_for_task", forbidden)
    monkeypatch.setattr("learnloop.diagnosis.split.jobs.default_embedding_client", forbidden)
    monkeypatch.setattr(OpenAIEmbeddingProviderClient, "__init__", forbidden)

    derived = sorted(tables_for_role(TableRole.DERIVED))

    def snapshot(database: Path):
        with closing(sqlite3.connect(database)) as connection:
            return {table: sorted(tuple(row) for row in connection.execute(f'SELECT * FROM "{table}"'))
                    for table in derived}

    # The same vault with the table gone: if rebuild read it, it would fail.
    gone = tmp_path / "gone"
    copy_tree_with_databases(paths.root, gone)
    with closing(sqlite3.connect(gone / "state.sqlite")) as connection:
        connection.execute("DROP TABLE help_assists")
        connection.commit()
    repository = Repository.attach(paths.sqlite_path)
    rebuild_all_derived_state(load_vault(paths.root), repository)
    rows_after = _rows(paths.sqlite_path)
    rebuild_all_derived_state(load_vault(gone), Repository.attach(gone / "state.sqlite"))
    assert snapshot(paths.sqlite_path) == snapshot(gone / "state.sqlite")
    assert rows_after == _rows(paths.sqlite_path) and len(rows_after) == 3
    # The isolated shadow replay too (no model call; it diffs nothing here).
    result = shadow_rebuild(load_vault(paths.root), assignments=())
    assert result is not None
    assert _rows(paths.sqlite_path) == rows_after


# -- the report (§6.3's descriptive rows, authored hints the baseline) ----------------


def test_the_report_describes_authored_reveals_and_what_followed(tmp_path):
    from learnloop.hints.report import build_hints_report

    paths = _vault(tmp_path, hints=["Name the three factors.", "U Sigma V^T."])
    ctx, session_id = _sidecar(paths.root)
    _reveal(ctx, session_id, 0, answer="")
    _reveal(ctx, session_id, 1, answer="U")
    _submit(ctx, session_id, hints=2, key="k1")
    # A later independent attempt on the item (no hint): the pending outcome resolves.
    _submit(ctx, session_id, hints=0, key="k2")
    other = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    _reveal(ctx, other, 0)  # never submitted: unattached
    report = build_hints_report(paths.sqlite_path)
    assert report["report_version"] == "hints-report-v1"
    assert report["totals"] == {
        "shown": 3, "items": 1, "sessions": 2, "attempts": 1, "unattached": 1,
        "per_attempt": {"n": 1, "p50": 2, "p95": 2},
    }
    [row] = report["kinds"]
    assert (row["surface"], row["assist_kind"], row["hint_kind"], row["level"], row["baseline"]) == (
        "practice", "hint", "authored", 3, True)
    assert (row["shown"], row["items"], row["sessions"], row["attempts"], row["unattached"]) == (3, 1, 2, 1, 1)
    assert row["by_authored_index"] == {"0": 2, "1": 1}
    assert row["work_empty_at_request"] == {"count": 2, "of": 3, "share": 0.6667}
    assert row["more_help_in_attempt"] == {"count": 1, "of": 2, "share": 0.5}
    assert row["attempt_outcome"] == {"correct": 1, "partial": 0, "incorrect": 0, "ungraded": 0}
    assert row["attempt_types"] == {"hinted_attempt": 1}
    assert row["later_independent_success"]["item"] == {"pass": 1, "fail": 0, "pending": 0}
    assert row["seconds_reveal_to_submit"]["n"] == 2
    assert report["top_items"] == [{"practice_item_id": ITEM, "shown": 3, "sessions": 2, "attempts": 1}]
    # No learner text reaches the report.
    assert "Name the three factors" not in json.dumps(report)
    # Filters.
    assert build_hints_report(paths.sqlite_path, surface="workbench")["totals"]["shown"] == 0
    future = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    assert build_hints_report(paths.sqlite_path, since=future)["totals"]["shown"] == 0


def test_the_report_cli_reads_the_vault_read_only(tmp_path):
    from learnloop.cli import app

    paths = _vault(tmp_path)
    ctx, session_id = _sidecar(paths.root)
    _reveal(ctx, session_id, 0)
    before = hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest()
    runner = CliRunner()
    result = runner.invoke(app, ["hints", "report", "--vault", str(paths.root), "--json", "--since", "7d"])
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["totals"]["shown"] == 1 and report["hints"] == {"telemetry_enabled": True}
    assert hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest() == before
    bad = runner.invoke(app, ["hints", "report", "--vault", str(paths.root), "--surface", "reader"])
    assert bad.exit_code == 1 and json.loads(bad.output)["status"] == "invalid"


def test_work_digest_keeps_only_a_hash_and_a_length():
    assert telemetry.work_digest("abc") == (hashlib.sha256(b"abc").hexdigest(), 3)
    assert telemetry.work_digest("") == (hashlib.sha256(b"").hexdigest(), 0)
