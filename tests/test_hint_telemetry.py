"""Adaptive hints H0: authored-hint reveal telemetry (spec_adaptive_hints_v1
§9 "H0's authored-reveal rows", §10 H0, G-H1's telemetry clause, G-H10).

``practice.record_hint_reveal`` writes one ``help_assists`` row per authored
hint the practice screen reveals (which hint, when, a hash and length of the
draft), under the screen's stable submission key; ``submit_attempt`` and
``submit_dont_know`` attach the rows recorded under their submission key to
the attempt (and only those: review F1), a retried submit or a recovery
repairs a failed attach, and the submit time is stamped before grading
(review F2). Telemetry only: the attempt's ``hints_used``,
``primed``, reveal events and every evidence table are byte-identical with
the telemetry on or off, and replay never reads the table. Fakes only: the
vault is the tests' basic vault, graded by self-grade (no provider at all).
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
from collections import Counter
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


def _reveal(
    ctx, session_id: str, index: int, *, answer: str = "", at: str | None = None, item: str = ITEM, key: str = "k1"
):
    params = {"sessionId": session_id, "practiceItemId": item, "submissionId": key, "authoredIndex": index,
              "answerMd": answer}
    if at is not None:
        params["revealedAt"] = at
    return _call(ctx, "practice.record_hint_reveal", params)


def _submit(
    ctx, session_id: str, *, hints: int, key: str, answer: str = "A = U Sigma V^T.", grade: dict | None = SELF_GRADE,
    latency: float | None = None,
):
    params = {
        "sessionId": session_id, "practiceItemId": ITEM, "answerMd": answer,
        "attemptType": "hinted_attempt" if hints else "independent_attempt", "hintsUsed": hints,
        "selfGrade": grade, "submissionId": key,
    }
    if latency is not None:
        params["latencySeconds"] = latency
    return _call(ctx, "submit_attempt", params)


def _report(paths, **options) -> dict:
    """The report as the CLI builds it: with the vault's item caps."""

    from learnloop.hints.report import build_hints_report, item_caps

    return build_hints_report(
        paths.sqlite_path, item_caps=item_caps(load_vault(paths.root).practice_items.values()), **options
    )


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
        "practice_item_id", "practice_session_id", "submission_id", "attempt_id", "body_md", "requested_at",
        "shown_at", "submitted_at",
    )} == {
        "surface": "practice", "assist_kind": "hint", "hint_kind": "authored", "level": 3, "chooser": "none",
        "counted_by": "client", "shown": 1, "authored_index": 0, "practice_item_id": ITEM,
        "practice_session_id": session_id, "submission_id": "k1", "attempt_id": None, "body_md": None,
        "requested_at": "2026-10-17T08:59:58.250Z", "shown_at": "2026-10-17T08:59:58.250Z", "submitted_at": None,
    }
    assert row["practice_item_hash"] == practice_item_hash(item)
    assert row["work_hash"] == hashlib.sha256(answer.encode()).hexdigest() and row["work_chars"] == len(answer)
    # The draft itself is never stored, and every later phase's column is empty.
    assert answer not in json.dumps(row)
    filled = {key for key, value in row.items() if value is not None}
    assert filled == {
        "id", "surface", "assist_kind", "practice_item_id", "practice_item_hash", "practice_session_id",
        "submission_id", "hint_kind", "level", "authored_index", "work_hash", "work_chars", "chooser", "shown",
        "counted_by", "requested_at", "shown_at",
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
    with pytest.raises(ValueError):
        _reveal(ctx, session_id, 0, key="")  # a reveal always names its submission
    assert _rows(paths.sqlite_path) == []


def test_an_older_client_without_a_submission_key_is_refused_and_nothing_else_changes(tmp_path):
    """Review round 2 (Codex job 20261018-000003-fesMOi): a reveal sent by a
    client from before F1 has no ``submissionId``. It is refused and no row
    is written (the screen's call is fire and forget, so its reveal is
    unchanged), and the submit still records the client's count."""

    paths = _vault(tmp_path)
    ctx, session_id = _sidecar(paths.root)
    with pytest.raises(ValueError, match="submissionId|submission_id"):
        _call(ctx, "practice.record_hint_reveal", {"sessionId": session_id, "practiceItemId": ITEM, "authoredIndex": 0})
    assert _rows(paths.sqlite_path) == []
    payload = _submit(ctx, session_id, hints=1, key="k1")
    attempt = Repository(paths.sqlite_path).fetch_practice_attempt(payload["attemptId"])
    assert (attempt["attempt_type"], attempt["hints_used"]) == ("hinted_attempt", 1)
    assert _rows(paths.sqlite_path) == []


# -- attempt_id at submit -------------------------------------------------------------


def test_submit_attaches_its_submissions_rows_and_keeps_the_clients_count(tmp_path):
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
    # The next attempt in the session gets only the rows revealed under its key.
    _reveal(ctx, session_id, 0, key="k2")
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
    _reveal(ctx, session_id, 0, key="dk-1")
    payload = _call(ctx, "submit_dont_know", {
        "sessionId": session_id, "practiceItemId": ITEM, "hintsUsed": 1, "submissionId": "dk-1"})
    attempt = Repository(paths.sqlite_path).fetch_practice_attempt(payload["attemptId"])
    assert attempt["attempt_type"] == "dont_know" and attempt["hints_used"] == 1
    assert [row["attempt_id"] for row in _rows(paths.sqlite_path)] == [payload["attemptId"]]


def test_an_empty_stuck_answer_attaches_the_rows_too(tmp_path):
    from tests.helpers import set_algorithm_version

    paths = _vault(tmp_path)
    set_algorithm_version(paths, "mvp-0.13")
    ctx, session_id = _sidecar(paths.root)
    _reveal(ctx, session_id, 0, key="stuck-1")
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
    monkeypatch.setattr(practice, "stamp_submission", forbidden)
    result = _reveal(ctx, session_id, 0)
    assert result == {"version": 1, "recorded": False, "reason": "telemetry_disabled", "assistId": None}
    # Off, the RPC answers before it looks at its input at all.
    assert _reveal(ctx, session_id, 7, item="pi_missing")["recorded"] is False
    _submit(ctx, session_id, hints=1, key="k1")
    _submit(ctx, session_id, hints=1, key="k1")  # a retry answered from its receipt
    _call(ctx, "recover_practice_submission", {"sessionId": session_id, "practiceItemId": ITEM, "submissionId": "k1"})
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
    monkeypatch.setattr(practice, "stamp_submission", broken)
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
    _reveal(ctx, session_id, 0, at="2026-10-17T08:59:30Z", key="k2")
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
    _reveal(ctx, session_id, 0, key="k2")  # an unattached row too
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
    _reveal(ctx, other, 0, key="k3")  # never submitted: unattached
    report = build_hints_report(paths.sqlite_path)
    assert report["report_version"] == "hints-report-v2"
    assert {key: value for key, value in report["totals"].items() if key != "per_attempt"} == {
        "shown": 3, "items": 1, "sessions": 2, "attempts": 1, "unattached": 1, "resolved_by_submission": 0,
    }
    assert {key: report["totals"]["per_attempt"][key] for key in ("n", "p50", "p95")} == {"n": 1, "p50": 2, "p95": 2}
    [row] = report["kinds"]
    assert (row["surface"], row["assist_kind"], row["hint_kind"], row["level"], row["baseline"]) == (
        "practice", "hint", "authored", 3, True)
    assert (row["shown"], row["items"], row["sessions"], row["attempts"], row["unattached"]) == (3, 1, 2, 1, 1)
    assert row["by_authored_index"] == {"0": 2, "1": 1}
    assert {k: row["work_empty_at_request"][k] for k in ("count", "of", "share")} == {"count": 2, "of": 3, "share": 0.6667}
    assert {k: row["more_help_in_attempt"][k] for k in ("count", "of", "share")} == {"count": 1, "of": 2, "share": 0.5}
    assert row["attempt_outcome"] == {"correct": 1, "partial": 0, "incorrect": 0, "ungraded": 0}
    assert row["attempt_types"] == {"hinted_attempt": 1}
    later = row["later_independent_success"]["item"]
    assert {key: later[key] for key in ("pass", "fail", "ungraded", "pending")} == {
        "pass": 1, "fail": 0, "ungraded": 0, "pending": 0}
    assert row["seconds_reveal_to_submit"]["n"] == 2 and row["timing_unknown"] == 0
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
    assert report["totals"]["shown"] == 1 and report["hints"] == {
        "telemetry_enabled": True, "price_per_million": None,
        "maps": {"enabled": True, "build_on_serve": True, "max_daily_cost_usd": 0.5},
        # Adaptive hints H2a's keys (the report shows the section as configured).
        "adaptive_enabled": True, "chooser_enabled": True, "choice_policy": "sample",
        "chooser_timeout_seconds": 3.0, "help_style": "balanced", "max_daily_cost_usd": 1.0,
        # Adaptive hints H2b's keys.
        "authored_offer_after_seconds": 4.0, "outcome_placement_enabled": True}
    # Adaptive hints H1's section, read from the same read-only connection's database.
    assert report["maps"]["versions_stored"] == 0 and report["maps"]["validation"]["failures_by_reason"] == {}
    assert hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest() == before
    bad = runner.invoke(app, ["hints", "report", "--vault", str(paths.root), "--surface", "reader"])
    assert bad.exit_code == 1 and json.loads(bad.output)["status"] == "invalid"


def test_work_digest_keeps_only_a_hash_and_a_length():
    assert telemetry.work_digest("abc") == (hashlib.sha256(b"abc").hexdigest(), 3)
    assert telemetry.work_digest("") == (hashlib.sha256(b"").hexdigest(), 0)


# -- review fixes (docs/reviews/hints-h0-codex-review.md) -----------------------------


def _broken(*args, **kwargs):
    raise sqlite3.OperationalError("disk I/O error")


def test_a_failed_attach_is_repaired_by_recovery_and_never_given_to_the_next_attempt(tmp_path, monkeypatch):
    """F1: attempt A commits but its attach fails (or the process stops before
    it); B, on the same item in the same session, must not take A's reveal,
    and recovering A (or retrying its submit) attaches it to A."""

    from learnloop.hints.report import build_hints_report

    paths = _vault(tmp_path, hints=["Name the three factors.", "U Sigma V^T."])
    ctx, session_id = _sidecar(paths.root)
    _reveal(ctx, session_id, 0, key="kA")
    with monkeypatch.context() as patch:
        patch.setattr(practice, "attach_reveals_to_attempt", _broken)
        first = _submit(ctx, session_id, hints=1, key="kA")
    assert [row["attempt_id"] for row in _rows(paths.sqlite_path)] == [None]
    # The report already gives the row to A, through the submission key.
    report = build_hints_report(paths.sqlite_path)
    assert (report["totals"]["unattached"], report["totals"]["resolved_by_submission"]) == (0, 1)
    # B: a later submission on the same item and session, with a reveal of its own.
    _reveal(ctx, session_id, 1, key="kB")
    second = _submit(ctx, session_id, hints=1, key="kB")
    assert first["attemptId"] != second["attemptId"]
    by_key = {row["submission_id"]: row["attempt_id"] for row in _rows(paths.sqlite_path)}
    assert by_key == {"kA": None, "kB": second["attemptId"]}
    # A's recovery answers from its receipt and repairs the attach.
    recovered = _call(ctx, "recover_practice_submission", {
        "sessionId": session_id, "practiceItemId": ITEM, "submissionId": "kA"})
    assert recovered["status"] == "recovered" and recovered["result"]["attemptId"] == first["attemptId"]
    by_key = {row["submission_id"]: row["attempt_id"] for row in _rows(paths.sqlite_path)}
    assert by_key == {"kA": first["attemptId"], "kB": second["attemptId"]}
    # Idempotent: recovering again, or retrying either submit, moves nothing.
    _call(ctx, "recover_practice_submission", {"sessionId": session_id, "practiceItemId": ITEM, "submissionId": "kA"})
    _submit(ctx, session_id, hints=1, key="kA")
    _submit(ctx, session_id, hints=1, key="kB")
    assert {row["submission_id"]: row["attempt_id"] for row in _rows(paths.sqlite_path)} == by_key
    report = build_hints_report(paths.sqlite_path)
    assert (report["totals"]["attempts"], report["totals"]["unattached"], report["totals"]["resolved_by_submission"]) == (
        2, 0, 0)


def test_a_retried_submit_repairs_a_failed_attach(tmp_path, monkeypatch):
    paths = _vault(tmp_path)
    ctx, session_id = _sidecar(paths.root)
    _reveal(ctx, session_id, 0, key="kA")
    with monkeypatch.context() as patch:
        patch.setattr(practice, "attach_reveals_to_attempt", _broken)
        first = _submit(ctx, session_id, hints=1, key="kA")
    assert [row["attempt_id"] for row in _rows(paths.sqlite_path)] == [None]
    assert _submit(ctx, session_id, hints=1, key="kA")["attemptId"] == first["attemptId"]
    assert [row["attempt_id"] for row in _rows(paths.sqlite_path)] == [first["attemptId"]]


def test_an_attempt_without_its_receipt_is_attached_when_its_completion_resumes(tmp_path, monkeypatch):
    """F1: the process stops after the attempt commits and before the receipt
    (and the attach): the resumed completion attaches the rows."""

    paths = _vault(tmp_path)
    ctx, session_id = _sidecar(paths.root)
    _reveal(ctx, session_id, 0, key="kA")

    def stop(*args, **kwargs):
        raise RuntimeError("process stopped before the receipt")

    with monkeypatch.context() as patch:
        patch.setattr(practice, "_store_submission_receipt", stop)
        with pytest.raises(RuntimeError):
            _submit(ctx, session_id, hints=1, key="kA")
    attempt = Repository(paths.sqlite_path).practice_attempt_by_submission_id("kA")
    assert attempt is not None and [row["attempt_id"] for row in _rows(paths.sqlite_path)] == [None]
    recovered = _call(ctx, "recover_practice_submission", {
        "sessionId": session_id, "practiceItemId": ITEM, "submissionId": "kA"})
    assert recovered["status"] == "recovered"
    assert [row["attempt_id"] for row in _rows(paths.sqlite_path)] == [attempt["id"]]


def _moving_clock(monkeypatch, start: datetime) -> dict:
    now = {"t": start}
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: now["t"])
    return now


def test_reveal_to_submit_ends_at_the_submit_not_at_the_graded_attempt(tmp_path, monkeypatch):
    """F2: opened 09:00:00, hint at 09:00:50, submit at 09:01:00, the grade
    applied at 09:01:30: 10 s from reveal to submit and 50 s into the attempt."""

    from learnloop.hints.report import build_hints_report

    now = _moving_clock(monkeypatch, FROZEN)
    paths = _vault(tmp_path)
    ctx, session_id = _sidecar(paths.root)
    _reveal(ctx, session_id, 0, at="2026-10-17T09:00:50Z")
    now["t"] = FROZEN + timedelta(seconds=60)
    original = practice.complete_attempt_with_ai_fallback

    def slow_grader(*args, **kwargs):
        now["t"] = FROZEN + timedelta(seconds=90)  # the grader takes 30 s
        return original(*args, **kwargs)

    monkeypatch.setattr(practice, "complete_attempt_with_ai_fallback", slow_grader)
    payload = _submit(ctx, session_id, hints=1, key="k1", latency=60)
    attempt = Repository(paths.sqlite_path).fetch_practice_attempt(payload["attemptId"])
    assert attempt["created_at"] == "2026-10-17T09:01:30Z"
    [row] = _rows(paths.sqlite_path)
    assert (row["attempt_id"], row["submitted_at"]) == (payload["attemptId"], "2026-10-17T09:01:00.000Z")
    [kind] = build_hints_report(paths.sqlite_path, now=FROZEN + timedelta(hours=1))["kinds"]
    assert (kind["seconds_reveal_to_submit"]["n"], kind["seconds_reveal_to_submit"]["p50"]) == (1, 10.0)
    assert (kind["seconds_into_attempt"]["n"], kind["seconds_into_attempt"]["p50"]) == (1, 50.0)
    assert kind["timing_unknown"] == 0


def test_a_grading_fallback_keeps_the_first_submit_time(tmp_path, monkeypatch):
    """F2: the grader is unavailable at the first submit; the learner's
    self-grade a minute later commits the attempt. The submit time is the
    first submit's."""

    now = _moving_clock(monkeypatch, FROZEN)
    paths = _vault(tmp_path)
    ctx, session_id = _sidecar(paths.root)
    _reveal(ctx, session_id, 0, at="2026-10-17T08:59:40Z")
    with pytest.raises(SidecarError) as fallback:
        _submit(ctx, session_id, hints=1, key="k1", grade=None)
    assert fallback.value.code == "grading_fallback_required"
    [row] = _rows(paths.sqlite_path)
    assert (row["attempt_id"], row["submitted_at"]) == (None, "2026-10-17T09:00:00.000Z")
    now["t"] = FROZEN + timedelta(minutes=1)
    payload = _submit(ctx, session_id, hints=1, key="k1")
    [row] = _rows(paths.sqlite_path)
    assert (row["attempt_id"], row["submitted_at"]) == (payload["attemptId"], "2026-10-17T09:00:00.000Z")


def test_a_row_without_a_submit_time_is_timed_unknown_not_from_the_grade(tmp_path, monkeypatch):
    from learnloop.hints.report import build_hints_report

    paths = _vault(tmp_path)
    ctx, session_id = _sidecar(paths.root)
    _reveal(ctx, session_id, 0)
    monkeypatch.setattr(practice, "stamp_submission", _broken)
    _submit(ctx, session_id, hints=1, key="k1")
    [row] = _rows(paths.sqlite_path)
    assert row["attempt_id"] and row["submitted_at"] is None
    [kind] = build_hints_report(paths.sqlite_path)["kinds"]
    assert kind["seconds_reveal_to_submit"]["n"] == 0 and kind["timing_unknown"] == 1


def _set_correctness(database: Path, attempt_id: str, value) -> None:
    with closing(sqlite3.connect(database)) as connection:
        connection.execute("UPDATE practice_attempts SET correctness = ? WHERE id = ?", (value, attempt_id))
        connection.commit()


def test_an_ungraded_next_attempt_is_reported_ungraded_never_fail(tmp_path, monkeypatch):
    """F4: the next independent attempt has no grade. It stays that attempt's
    outcome (``ungraded``), neither imputed a failure nor skipped for a later
    attempt's pass."""

    from learnloop.hints.report import build_hints_report

    now = _moving_clock(monkeypatch, FROZEN)
    paths = _vault(tmp_path)
    ctx, session_id = _sidecar(paths.root)
    _reveal(ctx, session_id, 0)
    _submit(ctx, session_id, hints=1, key="k1")
    now["t"] = FROZEN + timedelta(minutes=1)
    ungraded = _submit(ctx, session_id, hints=0, key="k2")
    _set_correctness(paths.sqlite_path, ungraded["attemptId"], None)
    now["t"] = FROZEN + timedelta(minutes=2)
    _submit(ctx, session_id, hints=0, key="k3")  # a later pass is not the outcome
    [kind] = build_hints_report(paths.sqlite_path)["kinds"]
    for scope in ("item", "learning_object"):
        later = kind["later_independent_success"][scope]
        assert {key: later[key] for key in ("pass", "fail", "ungraded", "pending")} == {
            "pass": 0, "fail": 0, "ungraded": 1, "pending": 0}
        assert later["pass_rate"]["of"] == 0 and later["pass_rate"]["interval"] is None
    # Graded and not correct is a fail; no later attempt at all is pending.
    _set_correctness(paths.sqlite_path, ungraded["attemptId"], 0.0)
    [kind] = build_hints_report(paths.sqlite_path)["kinds"]
    assert kind["later_independent_success"]["item"]["fail"] == 1


def test_an_ungraded_hinted_attempt_and_no_later_attempt(tmp_path):
    from learnloop.hints.report import build_hints_report

    paths = _vault(tmp_path, hints=["Name the three factors.", "U Sigma V^T."])
    ctx, session_id = _sidecar(paths.root)
    _reveal(ctx, session_id, 0)
    payload = _submit(ctx, session_id, hints=1, key="k1")
    _set_correctness(paths.sqlite_path, payload["attemptId"], None)
    [kind] = _report(paths)["kinds"]
    assert kind["attempt_outcome"]["ungraded"] == 1
    assert kind["attempt_correct"]["of"] == 0 and kind["attempt_correct"]["share"] is None
    assert kind["later_independent_success"]["item"]["pending"] == 1
    assert kind["unaided_next_progress"]["unknown"]["ungraded"] == 1
    assert kind["unaided_next_progress"]["reached"]["count"] == 0


def test_unaided_next_progress_is_settled_by_the_grade_where_it_can_be(tmp_path, monkeypatch):
    """F5 (§6.1): a fully correct submission with no further help after the
    hint reached the goal; every other case is unknown with its reason."""

    from learnloop.hints.report import build_hints_report

    now = _moving_clock(monkeypatch, FROZEN)
    paths = _vault(tmp_path, hints=["Name the three factors.", "U Sigma V^T."])
    ctx, session_id = _sidecar(paths.root)

    def attempt(key: str, reveals: int, *, hints: int | None = None, points: int = 4, primed: bool = False):
        now["t"] += timedelta(minutes=5)
        for index in range(reveals):
            _reveal(ctx, session_id, index, key=key, at=(now["t"] - timedelta(seconds=30 - index)).isoformat())
        params = {
            "sessionId": session_id, "practiceItemId": ITEM, "answerMd": "A = U Sigma V^T.",
            "attemptType": "hinted_attempt", "hintsUsed": reveals if hints is None else hints,
            "selfGrade": {"criterionPoints": {"correctness": points}, "confidence": 4}, "submissionId": key,
            "primed": primed,
        }
        return _call(ctx, "submit_attempt", params)

    attempt("reached", 1)                      # one hint, then a correct answer: reached
    attempt("two", 2)                          # the first is followed by more help; the second is at the cap
    attempt("wrong", 1, points=0)              # not correct: needs H2's outcome placement
    attempt("tutor", 1, hints=2)               # help the rows cannot order (say, a tutor question)
    attempt("primed", 1, primed=True)          # worked help or a disclosed answer
    [kind] = _report(paths)["kinds"]
    progress = kind["unaided_next_progress"]
    assert {key: progress["reached"][key] for key in ("count", "of")} == {"count": 1, "of": 6}
    assert progress["unknown"] == {
        "more_help_followed": 1, "primed": 1, "help_not_ordered": 1, "help_order_ambiguous": 0, "workbench_state_unknown": 0,
        "help_count_capped": 1,
        "help_cap_unknown": 0, "ungraded": 0, "not_fully_correct": 1,
    }
    assert progress["reached"]["interval"]["method"] == "wilson"
    assert "unaided_next_progress" not in build_hints_report(paths.sqlite_path)["not_yet_measured"]


def test_shares_and_summaries_carry_intervals_with_explicit_small_sample_behaviour():
    """F6 (§6: every number with its sample size and interval)."""

    from learnloop.hints.report import _percentiles, _share

    assert _share(0, 0) == {"count": 0, "of": 0, "share": None, "interval": None}
    one = _share(1, 1)
    assert one["share"] == 1.0
    assert one["interval"] == {"method": "wilson", "level": 0.95, "low": 0.2065, "high": 1.0}
    assert _share(0, 1)["interval"] == {"method": "wilson", "level": 0.95, "low": 0.0, "high": 0.7935}
    half = _share(5, 10)["interval"]
    assert (half["low"], half["high"]) == (0.2366, 0.7634)

    empty = _percentiles([])
    assert empty["n"] == 0 and empty["p50"] is None
    assert empty["p50_interval"]["reason"] == "empty" and empty["p50_interval"]["low"] is None
    # Five observations cannot bracket the median at 95% (coverage 1 - 2/32).
    five = _percentiles([1, 2, 3, 4, 5])
    assert five["p50"] == 3
    assert five["p50_interval"] == {
        "method": "order_statistic", "level": 0.95, "low": None, "high": None, "coverage": 0.9375,
        "reason": "too_few",
    }
    six = _percentiles([6, 1, 5, 2, 4, 3])
    assert six["p50_interval"] == {"method": "order_statistic", "level": 0.95, "low": 1, "high": 6, "coverage": 0.9688}
    assert six["p95_interval"]["reason"] == "too_few"
    large = _percentiles(range(1, 101))
    assert large["p50_interval"]["low"] < large["p50"] < large["p50_interval"]["high"]
    assert large["p50_interval"]["coverage"] >= 0.95
    assert large["p95_interval"]["low"] <= large["p95"] <= large["p95_interval"]["high"]
    assert large["p95_interval"]["coverage"] >= 0.95


# -- review round 2 (orchestrator, after Codex job 20261018-000003-fesMOi) -------------


def _exact_interval(ordered: list, q: float) -> dict:
    """The interval as b4d87cbed computed it (exact coefficients; it overflows
    from n = 1030): the reference the log-space terms must reproduce."""

    import math

    n = len(ordered)
    if n == 0:
        return {"method": "order_statistic", "level": 0.95, "low": None, "high": None, "coverage": None,
                "reason": "empty"}
    pmf = [math.comb(n, i) * q**i * (1.0 - q) ** (n - i) for i in range(n + 1)]
    rank = max(1, math.ceil(q * n))
    low, high, coverage = rank, rank, 0.0
    while coverage < 0.95:
        below = pmf[low - 1] if low > 1 else -1.0
        above = pmf[high] if high < n else -1.0
        if below < 0 and above < 0:
            return {"method": "order_statistic", "level": 0.95, "low": None, "high": None,
                    "coverage": round(coverage, 4), "reason": "too_few"}
        if above >= below:
            coverage += above
            high += 1
        else:
            coverage += below
            low -= 1
    return {"method": "order_statistic", "level": 0.95, "low": ordered[low - 1], "high": ordered[high - 1],
            "coverage": round(coverage, 4)}


def _check_summary(summary: dict, ordered: list) -> None:
    n = len(ordered)
    assert summary["n"] == n
    for q, key in ((0.50, "p50"), (0.95, "p95")):
        interval = summary[f"{key}_interval"]
        if n < 1030:
            assert interval == _exact_interval(ordered, q)
        else:
            # The reference overflows here; the interval brackets the estimate
            # at the level, as near the binomial's centre as it must be.
            assert interval["low"] <= summary[key] <= interval["high"]
            assert 0.95 <= interval["coverage"] < 0.96
            half_width = 2.6 * math.sqrt(n * q * (1 - q))
            assert ordered.index(interval["high"]) - ordered.index(interval["low"]) <= 2 * half_width


@pytest.mark.parametrize("n", [1, 2, 5, 1030, 20000])
def test_order_statistic_intervals_hold_at_any_sample_size(n):
    """V1: the binomial terms are computed stably (log space), equal to the
    exact ones wherever those can be computed, and never overflow."""

    from learnloop.hints.report import _percentiles

    values = [float(3 * index % 1009) for index in range(n)]  # not already sorted
    summary = _percentiles(values)
    _check_summary(summary, sorted(values))


def test_the_stable_terms_reproduce_every_exact_interval_below_the_overflow():
    from learnloop.hints.report import _quantile_interval

    for n in range(0, 1030, 7):
        ordered = list(range(1, n + 1))
        for q in (0.50, 0.95):
            assert _quantile_interval(ordered, q) == _exact_interval(ordered, q), (n, q)


@pytest.mark.parametrize("n", [1, 2, 5, 1030, 20000])
def test_the_report_summarises_any_number_of_rows(tmp_path, n):
    """V1 through a full report: n rows, each its own item and session."""

    from learnloop.db.copies import backup_database
    from learnloop.hints.report import build_hints_report

    head = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_218" / "state.sqlite"
    database = tmp_path / "state.sqlite"
    backup_database(head, database)
    with closing(connect(database)) as connection:
        for index in range(n):
            store.insert_assist(connection, {
                "id": f"ha_{index:06d}", "surface": "practice", "assist_kind": "hint", "hint_kind": "authored",
                "level": 3, "practice_item_id": f"pi_{index % max(1, n // 2):06d}",
                "practice_session_id": f"s_{index:06d}", "submission_id": f"k_{index:06d}", "authored_index": 0,
                "chooser": "none", "shown": 1, "counted_by": "client",
                "requested_at": f"2026-10-17T09:{index // 6000 % 60:02d}:{index // 100 % 60:02d}.{index % 100:03d}Z",
            })
        connection.commit()
    report = build_hints_report(database, now=FROZEN + timedelta(days=1))
    [kind] = report["kinds"]
    assert kind["shown"] == report["totals"]["shown"] == n and kind["sessions"] == n
    _check_summary(kind["per_session"], [1] * n)
    per_item = sorted(Counter(f"pi_{index % max(1, n // 2):06d}" for index in range(n)).values())
    _check_summary(kind["per_item"], per_item)


def _question(
    paths, session_id: str, at: datetime, *, hint_equivalent: bool = True, attempt_id: str | None = None
) -> None:
    """A substantive tutor answer on the item, with no answer overlap (no
    reveal event): what the fold counts as a hint equivalent."""

    Repository(paths.sqlite_path).insert_question_event({
        "context": "practice", "practice_item_id": ITEM, "session_id": session_id,
        "question_md": "Why are the factors orthogonal?", "answer_md": "Think about the geometry.",
        "question_type": "mechanism", "facets": [], "hint_equivalent": hint_equivalent,
        "answer_status": "answered", "created_at": at.strftime("%Y-%m-%dT%H:%M:%SZ"), "attempt_id": attempt_id,
    })


def test_capped_tutor_help_never_reads_as_unaided_progress(tmp_path, monkeypatch):
    """V2, Codex's case: the item caps the combined count at 1; an authored
    hint, then a substantive tutor answer (no answer overlap), then a correct
    submit records hints_used == 1 == one recorded reveal. The tutor's help
    is recorded, uncapped, in question_events: unknown, never "reached". The
    attempt's count is the grading count, unchanged."""

    now = _moving_clock(monkeypatch, FROZEN)
    paths = _vault(tmp_path)  # one authored hint, max_useful_hints 1
    ctx, session_id = _sidecar(paths.root)
    _reveal(ctx, session_id, 0, key="k1", at="2026-10-17T09:00:10Z")
    _question(paths, session_id, FROZEN + timedelta(seconds=20))
    now["t"] = FROZEN + timedelta(seconds=30)
    payload = _submit(ctx, session_id, hints=1, key="k1")
    attempt = Repository(paths.sqlite_path).fetch_practice_attempt(payload["attemptId"])
    assert (attempt["hints_used"], attempt["correctness"]) == (1, 1.0)  # 1 + 1, capped at 1
    progress = _report(paths)["kinds"][0]["unaided_next_progress"]
    assert progress["reached"]["count"] == 0
    assert progress["unknown"]["help_not_ordered"] == 1


def test_unaided_progress_is_reached_only_when_the_uncapped_records_show_no_other_help(tmp_path, monkeypatch):
    """V2: "reached" needs the submission's rows to be all the help the
    attempt had, from records no cap applies to; each other case is unknown
    with its reason."""

    from learnloop.hints.report import build_hints_report

    now = _moving_clock(monkeypatch, FROZEN)
    paths = _vault(tmp_path, hints=["Name the three factors.", "U Sigma V^T."])  # max_useful_hints 2
    ctx, session_id = _sidecar(paths.root)

    def attempt(key: str, before_submit=None, *, reveals: int = 1) -> str:
        now["t"] += timedelta(minutes=5)
        for index in range(reveals):
            _reveal(ctx, session_id, index, key=key, at=(now["t"] - timedelta(seconds=30 - index)).isoformat())
        if before_submit is not None:
            before_submit(key)
        return _submit(ctx, session_id, hints=reveals, key=key)["attemptId"]

    attempt("clean")                                      # the reveal and nothing else: reached
    attempt("capped", reveals=2)                          # more help followed the first; the second is at the cap
    attempt("reveal", lambda key: Repository(paths.sqlite_path).insert_reveal_event({
        "practice_item_id": ITEM, "source_kind": "tutor_answer", "amount": 0.2,
        "created_at": (now["t"] - timedelta(seconds=10)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }))                                                   # a partial reveal (below auto-prime): other help
    attempt("own_disclosure", lambda key: _call(ctx, "record_self_grade_disclosure", {
        "sessionId": session_id, "practiceItemId": ITEM, "submissionId": key, "answerMd": "A = U Sigma V^T.",
    }))                                                   # the submission's own self-grade display: still reached
    progress = _report(paths)["kinds"][0]["unaided_next_progress"]
    assert {key: progress["reached"][key] for key in ("count", "of")} == {"count": 2, "of": 5}
    assert progress["unknown"] == {
        "more_help_followed": 1, "primed": 0, "help_not_ordered": 1, "help_order_ambiguous": 0, "workbench_state_unknown": 0,
        "help_count_capped": 1,
        "help_cap_unknown": 0, "ungraded": 0, "not_fully_correct": 0,
    }
    # Without the vault's caps (or for an item changed since the hint) no
    # count can be shown complete.
    unknown = build_hints_report(paths.sqlite_path)["kinds"][0]["unaided_next_progress"]
    assert unknown["reached"]["count"] == 0 and unknown["unknown"]["help_cap_unknown"] == 3
    item_path = paths.practice_item_path("linear-algebra", ITEM)
    data = read_yaml(item_path)
    data["hint_policy"] = {**data["hint_policy"], "max_useful_hints": 3}
    write_yaml(item_path, data)
    changed = _report(paths)["kinds"][0]["unaided_next_progress"]
    assert changed["reached"]["count"] == 0 and changed["unknown"]["help_cap_unknown"] == 3


def test_a_count_at_the_cap_with_nothing_else_recorded_is_still_unknown(tmp_path, monkeypatch):
    """V2: one reveal, one hint counted, the item's cap 1, no other record: the
    client's count may have been larger than the cap kept, so the rows cannot
    be shown to be all the help."""

    _moving_clock(monkeypatch, FROZEN)
    paths = _vault(tmp_path)  # one authored hint, max_useful_hints 1
    ctx, session_id = _sidecar(paths.root)
    _reveal(ctx, session_id, 0, key="k1")
    _submit(ctx, session_id, hints=1, key="k1")
    progress = _report(paths)["kinds"][0]["unaided_next_progress"]
    assert progress["reached"]["count"] == 0 and progress["unknown"]["help_count_capped"] == 1


def test_a_workbench_problem_holding_a_hint_is_workbench_state_unknown(tmp_path, monkeypatch):
    """V2, round 4: an open workbench problem on the item that carried a hint
    is folded into the count (the larger of it and the client's), so it can
    hide behind the one recorded reveal. Its help as of the attempt cannot be
    read from its current state, so the case is unknown."""

    now = _moving_clock(monkeypatch, FROZEN)
    paths = _vault(tmp_path, hints=["Name the three factors.", "U Sigma V^T."])
    ctx, session_id = _sidecar(paths.root)
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute(
            "INSERT INTO workbench_sessions (id, practice_item_id, stem_md, origin, entry, carried_hints, "
            "created_at, updated_at) VALUES ('wb_1', ?, 'Define the SVD.', 'practice', 'practice_screen', 1, ?, ?)",
            (ITEM, "2026-10-17T08:59:00Z", "2026-10-17T08:59:00Z"),
        )
        connection.commit()
    _reveal(ctx, session_id, 0, key="k1", at="2026-10-17T09:00:10Z")
    now["t"] = FROZEN + timedelta(seconds=30)
    payload = _submit(ctx, session_id, hints=1, key="k1")
    assert Repository(paths.sqlite_path).fetch_practice_attempt(payload["attemptId"])["hints_used"] == 1
    progress = _report(paths)["kinds"][0]["unaided_next_progress"]
    assert progress["reached"]["count"] == 0 and progress["unknown"]["workbench_state_unknown"] == 1


def test_seconds_into_the_attempt_after_a_grading_fallback_is_the_first_submits(tmp_path, monkeypatch):
    """V3, the exact scenario: opened 09:00:00, hint at 09:00:50, first submit
    at 09:01:00 (latency 60) answered by the self-grade fallback, the retry at
    09:02:00 sending latency 120. Reveal to submit is 10 s and the hint came
    50 s into the attempt (not 110): the first submit's time and latency,
    stamped together and kept."""

    now = _moving_clock(monkeypatch, FROZEN)
    paths = _vault(tmp_path)
    ctx, session_id = _sidecar(paths.root)
    _reveal(ctx, session_id, 0, at="2026-10-17T09:00:50Z")
    now["t"] = FROZEN + timedelta(seconds=60)
    with pytest.raises(SidecarError) as fallback:
        _submit(ctx, session_id, hints=1, key="k1", grade=None, latency=60)
    assert fallback.value.code == "grading_fallback_required"
    now["t"] = FROZEN + timedelta(seconds=120)
    payload = _submit(ctx, session_id, hints=1, key="k1", latency=120)
    attempt = Repository(paths.sqlite_path).fetch_practice_attempt(payload["attemptId"])
    assert attempt["latency_seconds"] == 120  # what submit stores is unchanged
    [kind] = _report(paths, now=FROZEN + timedelta(hours=1))["kinds"]
    assert (kind["seconds_reveal_to_submit"]["n"], kind["seconds_reveal_to_submit"]["p50"]) == (1, 10.0)
    assert (kind["seconds_into_attempt"]["n"], kind["seconds_into_attempt"]["p50"]) == (1, 50.0)
    assert kind["seconds_into_attempt_unknown"] == {"no_submit_time": 0, "no_submit_latency": 0}
    [row] = _rows(paths.sqlite_path)
    assert (row["attempt_id"], row["submitted_at"], row["submit_latency_seconds"]) == (
        payload["attemptId"], "2026-10-17T09:01:00.000Z", 60.0)


def test_seconds_into_the_attempt_is_unknown_without_the_submits_latency(tmp_path, monkeypatch):
    """V3: a submission that sent no latency (or a row whose submit time is
    unknown) is never timed from the attempt's own latency."""

    now = _moving_clock(monkeypatch, FROZEN)
    paths = _vault(tmp_path)
    ctx, session_id = _sidecar(paths.root)
    _reveal(ctx, session_id, 0, at="2026-10-17T09:00:50Z", key="k1")
    now["t"] = FROZEN + timedelta(seconds=60)
    with pytest.raises(SidecarError):
        _submit(ctx, session_id, hints=1, key="k1", grade=None)  # no latency sent
    now["t"] = FROZEN + timedelta(seconds=120)
    _submit(ctx, session_id, hints=1, key="k1", latency=120)
    _reveal(ctx, session_id, 0, at="2026-10-17T09:02:30Z", key="k2")
    with monkeypatch.context() as patch:
        patch.setattr(practice, "stamp_submission", _broken)
        patch.setattr(practice, "attach_reveals_to_attempt", _broken)
        now["t"] = FROZEN + timedelta(seconds=180)
        _submit(ctx, session_id, hints=1, key="k2", latency=30)
    _call(ctx, "recover_practice_submission", {"sessionId": session_id, "practiceItemId": ITEM, "submissionId": "k2"})
    [kind] = _report(paths, now=FROZEN + timedelta(hours=1))["kinds"]
    assert kind["seconds_into_attempt"]["n"] == 0
    assert kind["seconds_into_attempt_unknown"] == {"no_submit_time": 1, "no_submit_latency": 1}
    assert kind["seconds_reveal_to_submit"]["n"] == 1 and kind["timing_unknown"] == 1


# -- review round 3 (after Codex job 20261018-002703-ixJaw2) ----------------------------


def _stamp(at: datetime) -> str:
    return at.strftime("%Y-%m-%dT%H:%M:%SZ")


def _reveal_event(paths, at: datetime, *, attempt_id: str | None = None, amount: float = 1.0,
                  source_kind: str = "answer_display", basis: str | None = "feedback_full_answer:desktop:d") -> None:
    Repository(paths.sqlite_path).insert_reveal_event({
        "practice_item_id": ITEM, "source_kind": source_kind, "amount": amount, "basis": basis,
        "attempt_id": attempt_id, "created_at": _stamp(at),
    })


def _progress(paths) -> dict:
    progress = _report(paths)["kinds"][0]["unaided_next_progress"]
    return {"reached": progress["reached"]["count"], **{key: n for key, n in progress["unknown"].items() if n}}


def test_the_attempts_own_feedback_display_in_its_second_is_not_help_before_it(tmp_path, monkeypatch):
    """W1: the attempt's own post-attempt feedback display, stored in the same
    second as the attempt, is attributed to it: after the submit, not help."""

    now = _moving_clock(monkeypatch, FROZEN)
    paths = _vault(tmp_path, hints=["Name the three factors.", "U Sigma V^T."])
    ctx, session_id = _sidecar(paths.root)
    _reveal(ctx, session_id, 0, key="k1", at="2026-10-17T08:59:40Z")
    attempt_id = _submit(ctx, session_id, hints=1, key="k1")["attemptId"]
    assert Repository(paths.sqlite_path).fetch_practice_attempt(attempt_id)["created_at"] == _stamp(FROZEN)
    _reveal_event(paths, FROZEN, attempt_id=attempt_id)  # its feedback, the same second
    now["t"] = FROZEN + timedelta(minutes=1)
    _reveal_event(paths, now["t"], attempt_id=attempt_id)  # and a revisit later
    assert _progress(paths) == {"reached": 1}


def test_a_later_revisit_of_the_previous_attempts_feedback_is_not_help(tmp_path, monkeypatch):
    """W2: a display attributed to the previous attempt A counts for B only
    before B (attribution relaxes the lower bound, never the upper): A's
    feedback revisited after B leaves B reached; A's feedback before B does not."""

    now = _moving_clock(monkeypatch, FROZEN)
    paths = _vault(tmp_path, hints=["Name the three factors.", "U Sigma V^T."])
    ctx, session_id = _sidecar(paths.root)
    first = _submit(ctx, session_id, hints=0, key="kA")["attemptId"]
    now["t"] = FROZEN + timedelta(minutes=5)
    _reveal(ctx, session_id, 0, key="kB", at=(now["t"] - timedelta(seconds=20)).isoformat())
    _submit(ctx, session_id, hints=1, key="kB")
    _reveal_event(paths, FROZEN + timedelta(minutes=10), attempt_id=first)  # A revisited after B
    assert _progress(paths) == {"reached": 1}
    _reveal_event(paths, FROZEN, attempt_id=first)  # A's feedback in A's own second, before B
    assert _progress(paths) == {"reached": 0, "help_not_ordered": 1}


def test_help_in_a_boundarys_second_is_order_ambiguous_never_reached(tmp_path, monkeypatch):
    """W3: attempts and tutor events are stamped to the second. A tutor answer
    in the previous attempt's second, with no attribution, cannot be placed
    before or after it: unknown (help_order_ambiguous), never reached. The
    grading fold's count (``created_at > since``) is left as it is: it does
    not count that answer, the same boundary, pre-existing."""

    now = _moving_clock(monkeypatch, FROZEN)
    paths = _vault(tmp_path, hints=["Name the three factors.", "U Sigma V^T."])
    ctx, session_id = _sidecar(paths.root)
    first = _submit(ctx, session_id, hints=0, key="kA")["attemptId"]
    _question(paths, session_id, FROZEN)  # the same second as A
    now["t"] = FROZEN + timedelta(minutes=5)
    _reveal(ctx, session_id, 0, key="kB", at=(now["t"] - timedelta(seconds=20)).isoformat())
    second = _submit(ctx, session_id, hints=1, key="kB")["attemptId"]
    assert Repository(paths.sqlite_path).fetch_practice_attempt(second)["hints_used"] == 1  # grading unchanged
    assert _progress(paths) == {"reached": 0, "help_order_ambiguous": 1}
    # Attributed to A (a feedback question on A), the same second is after A: help.
    _question(paths, session_id, FROZEN, attempt_id=first)
    assert _progress(paths) == {"reached": 0, "help_not_ordered": 1}


def test_help_in_the_attempts_own_second_is_order_ambiguous(tmp_path, monkeypatch):
    """W3, the upper boundary: an unattributed reveal or tutor answer in the
    evaluated attempt's own second may have come before its submit or after."""

    now = _moving_clock(monkeypatch, FROZEN)
    for name, record in (
        ("reveal", lambda paths, session_id: _reveal_event(paths, FROZEN, amount=0.2, source_kind="tutor_answer",
                                                           basis=None)),
        ("question", lambda paths, session_id: _question(paths, session_id, FROZEN)),
    ):
        now["t"] = FROZEN
        paths = _vault(tmp_path, hints=["Name the three factors.", "U Sigma V^T."], name=name)
        ctx, session_id = _sidecar(paths.root)
        _reveal(ctx, session_id, 0, key="k1", at="2026-10-17T08:59:40Z")
        _submit(ctx, session_id, hints=1, key="k1")
        record(paths, session_id)
        assert _progress(paths) == {"reached": 0, "help_order_ambiguous": 1}, name


# -- review round 4 (after Codex job 20261018-003635-bF1uGX) ----------------------------


def _workbench(paths, problem_id: str, *, created_at: str, closed_at: str | None = None, origin: str = "reader",
               source_visible: int = 1) -> None:
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute(
            "INSERT INTO workbench_sessions (id, practice_item_id, stem_md, origin, entry, source_visible, status, "
            "created_at, updated_at, closed_at) VALUES (?, ?, 'Define the SVD.', ?, 'work_through', ?, ?, ?, ?, ?)",
            (problem_id, ITEM, origin, source_visible, "open" if closed_at is None else "abandoned", created_at,
             created_at, closed_at),
        )
        connection.commit()


def test_hiding_the_book_after_the_submit_never_flips_the_attempt(tmp_path, monkeypatch):
    """Round 4, Codex's scenario: a Reader problem on the item with the book
    shown and no steps (it counts one hint-equivalent at submit), a correct
    submit, then the book hidden. The report must not change with that later
    state: the workbench help as of the attempt is unknown, before and after."""

    now = _moving_clock(monkeypatch, FROZEN)
    paths = _vault(tmp_path, hints=["Name the three factors.", "U Sigma V^T."])
    ctx, session_id = _sidecar(paths.root)
    _workbench(paths, "wb_book", created_at="2026-10-17T08:59:00Z")
    _reveal(ctx, session_id, 0, key="k1", at="2026-10-17T09:00:10Z")
    now["t"] = FROZEN + timedelta(seconds=30)
    payload = _submit(ctx, session_id, hints=1, key="k1")
    attempt = Repository(paths.sqlite_path).fetch_practice_attempt(payload["attemptId"])
    assert (attempt["hints_used"], attempt["correctness"]) == (1, 1.0)  # max(1 client, 1 book), unchanged
    before = _progress(paths)
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute(
            "UPDATE workbench_sessions SET source_visible = 0, source_hidden_at = ? WHERE id = 'wb_book'",
            ("2026-10-17T09:05:00Z",),
        )
        connection.commit()
    assert before == _progress(paths) == {"reached": 0, "workbench_state_unknown": 1}


def test_a_workbench_problem_opened_only_after_the_submit_plays_no_part(tmp_path, monkeypatch):
    """Round 4: a problem opened after the attempt (and one closed before the
    window opened) could not have been open in it; the case is decided
    without it. A tie with a boundary, or an unreadable time, could have been."""

    now = _moving_clock(monkeypatch, FROZEN)
    paths = _vault(tmp_path, hints=["Name the three factors.", "U Sigma V^T."])
    ctx, session_id = _sidecar(paths.root)
    _workbench(paths, "wb_old", created_at="2026-10-17T08:00:00Z", closed_at="2026-10-17T08:30:00Z")
    _submit(ctx, session_id, hints=0, key="kA")  # the previous attempt, 09:00:00
    now["t"] = FROZEN + timedelta(minutes=5)
    _reveal(ctx, session_id, 0, key="kB", at=(now["t"] - timedelta(seconds=20)).isoformat())
    _submit(ctx, session_id, hints=1, key="kB")  # 09:05:00
    _workbench(paths, "wb_after", created_at="2026-10-17T09:05:01Z")
    assert _progress(paths) == {"reached": 1}
    _workbench(paths, "wb_tie", created_at="2026-10-17T08:50:00Z", closed_at="2026-10-17T09:00:00Z")
    assert _progress(paths) == {"reached": 0, "workbench_state_unknown": 1}


def test_a_workbench_problem_with_an_unreadable_time_could_have_been_open(tmp_path, monkeypatch):
    now = _moving_clock(monkeypatch, FROZEN)
    paths = _vault(tmp_path, hints=["Name the three factors.", "U Sigma V^T."])
    ctx, session_id = _sidecar(paths.root)
    _reveal(ctx, session_id, 0, key="k1", at="2026-10-17T08:59:40Z")
    _submit(ctx, session_id, hints=1, key="k1")
    _workbench(paths, "wb_unreadable", created_at="not a time", closed_at="2026-10-17T08:00:00Z")
    assert _progress(paths) == {"reached": 0, "workbench_state_unknown": 1}


# -- review round 5 (after Codex job 20261018-004402-IAnAPx) ----------------------------


def _open_import(paths, *, bind_to: str | None = None) -> str:
    """A Reader problem opened from a selection, as an import (no item yet),
    with the book hidden; bound through ``workbench.bind`` when asked."""

    from learnloop.reader import workbench as WB

    repository = Repository(paths.sqlite_path)
    row, _resumed = WB.open_session(
        repository, origin="reader", entry="work_through", stem_md="Define the SVD.",
        import_status="pending", source_visible=False,
    )
    if bind_to is not None:
        WB.bind(repository, row["id"], bind_to)
    return row["id"]


def _hinted_attempt(paths, monkeypatch) -> None:
    now = _moving_clock(monkeypatch, FROZEN)
    ctx, session_id = _sidecar(paths.root)
    _reveal(ctx, session_id, 0, key="k1", at="2026-10-17T09:00:10Z")
    now["t"] = FROZEN + timedelta(seconds=30)
    _submit(ctx, session_id, hints=1, key="k1")


def test_rebinding_an_imported_problem_to_another_item_never_flips_the_attempt(tmp_path, monkeypatch):
    """Round 5, Codex's scenario: an imported problem bound to the item is open
    during the attempt; ``workbench.bind`` later rebinds it to item B. Its
    current binding proves nothing about the window: unknown, before and after."""

    from learnloop.reader import workbench as WB

    paths = _vault(tmp_path, hints=["Name the three factors.", "U Sigma V^T."])
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: FROZEN - timedelta(minutes=5))
    problem = _open_import(paths, bind_to=ITEM)
    _hinted_attempt(paths, monkeypatch)
    before = _progress(paths)
    WB.bind(Repository(paths.sqlite_path), problem, "pi_other_item")
    assert before == _progress(paths) == {"reached": 0, "workbench_state_unknown": 1}


def test_an_unbound_problem_open_in_the_window_is_workbench_state_unknown(tmp_path, monkeypatch):
    """Round 5: an import that has not bound yet may later bind to this item
    (or may have been this item's problem, rebound): unknown."""

    paths = _vault(tmp_path, hints=["Name the three factors.", "U Sigma V^T."])
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: FROZEN - timedelta(minutes=5))
    _open_import(paths)
    _hinted_attempt(paths, monkeypatch)
    assert _progress(paths) == {"reached": 0, "workbench_state_unknown": 1}


def test_a_problem_opened_on_another_item_leaves_the_attempt_reached(tmp_path, monkeypatch):
    """Round 5, the control: a problem opened on another item
    (``import_status = 'none'``) can never be bound to this one, so even open
    across the window it plays no part. Its binding is fixed: ``bind`` refuses
    it and ``mark_import`` leaves it unchanged."""

    from learnloop.reader import workbench as WB

    paths = _vault(tmp_path, hints=["Name the three factors.", "U Sigma V^T."])
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute(
            "INSERT INTO workbench_sessions (id, practice_item_id, stem_md, origin, entry, created_at, updated_at) "
            "VALUES ('wb_other', 'pi_other_item', 'Another problem.', 'practice', 'practice_screen', ?, ?)",
            ("2026-10-17T08:59:00Z", "2026-10-17T08:59:00Z"),
        )
        connection.commit()
    _hinted_attempt(paths, monkeypatch)
    assert _progress(paths) == {"reached": 1}
    repository = Repository(paths.sqlite_path)
    with pytest.raises(WB.WorkbenchError):
        WB.bind(repository, "wb_other", ITEM)
    for status in ("pending", "failed"):
        assert WB.mark_import(repository, "wb_other", status=status)["import_status"] == "none"
    assert _progress(paths) == {"reached": 1}


def test_a_pending_or_failed_tutor_question_counts_as_help(tmp_path, monkeypatch):
    """Round 5 audit: a question's status and hint flag are rewritten by its
    completion (``Repository.update_question_event_answer``, no status guard), so a pending
    or failed turn in the window may yet be, or have been, answered: help."""

    for status in ("pending", "failed"):
        now = _moving_clock(monkeypatch, FROZEN)
        paths = _vault(tmp_path, hints=["Name the three factors.", "U Sigma V^T."], name=status)
        ctx, session_id = _sidecar(paths.root)
        _reveal(ctx, session_id, 0, key="k1", at="2026-10-17T09:00:10Z")
        Repository(paths.sqlite_path).insert_question_event({
            "context": "practice", "practice_item_id": ITEM, "session_id": session_id,
            "question_md": "Why are the factors orthogonal?", "answer_md": None, "question_type": None,
            "facets": [], "hint_equivalent": False, "answer_status": status, "created_at": _stamp(FROZEN + timedelta(seconds=20)),
        })
        now["t"] = FROZEN + timedelta(seconds=30)
        _submit(ctx, session_id, hints=1, key="k1")
        assert _progress(paths) == {"reached": 0, "help_not_ordered": 1}, status
