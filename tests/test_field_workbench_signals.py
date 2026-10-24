"""RW2d: workbench signals in the learner field (spec_reader_workbench_v1 §5.11, G41).

G41: RW2d is a proper successor. With ``workbench.field_signals_enabled =
false`` (or below the tag) the field derivation, Phase 6 serving and plan
builds are byte-identical to the predecessor on fixture copies; on, the
receipts record what the old derivation would have produced. A stuck step or
early help never lowers the record (F2).
"""

from __future__ import annotations

from contextlib import closing
from datetime import UTC, datetime
import json
from pathlib import Path
import re
import sqlite3

import pytest

from learnloop.algorithm_versions import (
    INTENT_ALGORITHM_VERSION,
    LATEST_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
    WORKBENCH_FIELD_SIGNALS_ALGORITHM_VERSION,
    WORKBENCH_FIELD_SIGNALS_VERSIONS,
)
from learnloop.db.connection import connect
from learnloop.field.signals import (
    STUCK_CONFUSION_SIGNAL,
    blocks_fast_track,
    enrich_attempts,
    load_interaction_signals,
)
from learnloop.field.types import SignalRow
from learnloop.placement.decisions import reconcile_fast_track
from learnloop.placement.signals import _attempt_rows, blocking_signals_by_lo
from learnloop.placement.state import load_answers
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, append_config_toml, create_placement_vault, set_algorithm_version
from tests.test_assumed_known import EVIDENCE_TABLES, LOW_Q, _answer, _at, _decisions, _queue, _snapshot
from tests.test_quick_check import _answer_target, _progress, _start

TAG = WORKBENCH_FIELD_SIGNALS_ALGORITHM_VERSION
#: The predecessor as the upgrade names it (one constant; the landing renumbers).
PREDECESSOR = SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1]
OFF = "[workbench]\nfield_signals_enabled = false\n"


def _iso(minutes: float) -> str:
    return _at(minutes).now().isoformat().replace("+00:00", "Z")


def _vault(tmp_path, name="vault", *, version=TAG, toml=LOW_Q):
    from learnloop.db.repositories import Repository
    from learnloop.clock import FrozenClock
    from learnloop.substrate.state_sync import sync_vault_state

    paths = create_placement_vault(tmp_path / name, version=version, placement_toml=toml)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return paths, vault, repository


def _db(path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def _session(path, session_id, item_id, *, minutes, attempt_id=None, status=None):
    status = status or ("submitted" if attempt_id else "open")
    with closing(_db(path)) as db, db:
        db.execute(
            "INSERT INTO workbench_sessions (id, practice_item_id, stem_md, import_status, origin, entry, "
            "status, attempt_id, client_idempotency_key, created_at, updated_at) "
            "VALUES (?, ?, 'A problem.', ?, 'reader', 'work_through', ?, ?, ?, ?, ?)",
            (session_id, item_id, "bound" if item_id else "pending", status, attempt_id,
             f"key-{session_id}", _iso(minutes), _iso(minutes)),
        )


def _step(path, session_id, step_id, kind, body, *, minutes, supersedes=None, deleted=0):
    with closing(_db(path)) as db, db:
        db.execute(
            "INSERT INTO workbench_steps (id, session_id, ordinal, kind, body_md, supersedes_id, deleted, "
            "client_idempotency_key, created_at) VALUES (?, ?, 1.0, ?, ?, ?, ?, ?, ?)",
            (step_id, session_id, kind, body, supersedes, deleted, f"key-{step_id}", _iso(minutes)),
        )


def _assist(path, assist_id, session_id, *, minutes, snapshot, kind="hint", item_id=None):
    with closing(_db(path)) as db, db:
        db.execute(
            "INSERT INTO help_assists (id, surface, assist_kind, practice_item_id, workbench_session_id, "
            "chooser, shown, step_snapshot_json, requested_at) VALUES (?, 'workbench', ?, ?, ?, 'none', 1, ?, ?)",
            (assist_id, kind, item_id, session_id, None if snapshot is None else json.dumps(snapshot),
             _iso(minutes)),
        )


def _receipts(paths) -> list[dict]:
    with closing(_db(paths.sqlite_path)) as db:
        if db.execute("SELECT 1 FROM sqlite_master WHERE name = 'field_signal_receipts'").fetchone() is None:
            return []
        return [dict(row) for row in db.execute("SELECT * FROM field_signal_receipts ORDER BY created_at, id")]


def _signals(paths, vault):
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        return load_interaction_signals(connection, vault, _attempt_rows(load_answers(connection)))


def _blocking(paths, vault):
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        return blocking_signals_by_lo(connection, vault, load_answers(connection))


def _two_clean_answers(vault, repository, *, start=10):
    _answer(vault, repository, "pi_diag_hard", minutes=start)
    _answer(vault, repository, "pi_diag_mid", minutes=start + 1)


def _stuck_on_diag(paths, *, minutes=1):
    """An abandoned problem on lo_diag with a stuck step that says where."""

    _session(paths.sqlite_path, "wb_stuck", "pi_diag_easy", minutes=minutes, status="abandoned")
    _step(paths.sqlite_path, "wb_stuck", "st_1", "step", "Write P D P^{-1}.", minutes=minutes)
    _step(paths.sqlite_path, "wb_stuck", "st_2", "stuck", "I don't see why P is invertible.", minutes=minutes + 1)


def _early_help_on_diag(paths, *, minutes=1):
    """A problem on lo_diag where Help came before any step."""

    _session(paths.sqlite_path, "wb_help", "pi_diag_easy", minutes=minutes)
    _assist(paths.sqlite_path, "ha_1", "wb_help", minutes=minutes + 1, snapshot=[], item_id="pi_diag_easy")


# ── the pure derivation ───────────────────────────────────────────────────────


def _derive(sessions, steps=(), assists=(), *, attempts=None, diagnostics=None):
    from learnloop.field.workbench_signals import derive_workbench_signals

    return derive_workbench_signals(
        sessions, steps, assists, attempts=attempts or {}, item_targets={"pi_a": ("lo_a", "subj")},
        diagnostics=diagnostics,
    )


def _row(step_id, kind, body, at, *, session="s1", supersedes=None, deleted=0):
    return {"id": step_id, "session_id": session, "kind": kind, "body_md": body, "supersedes_id": supersedes,
            "deleted": deleted, "created_at": at}


def test_a_stuck_step_with_text_is_one_zero_mass_confusion_row_per_chain():
    steps = [
        _row("a", "stuck", "  ", "2026-05-19T12:01:00Z"),
        _row("b", "stuck", "Why is P invertible?", "2026-05-19T12:02:00Z", supersedes="a"),
        _row("c", "stuck", "Why is P invertible?", "2026-05-19T12:03:00Z", supersedes="b", deleted=1),
        _row("d", "step", "P D P^-1", "2026-05-19T12:04:00Z"),
    ]
    (signal,) = _derive([{"id": "s1", "practice_item_id": "pi_a", "attempt_id": None}], steps)
    # Observed when the chain first held text; a later delete never takes it back.
    assert signal == SignalRow(
        signal_id="workbench_stuck:a", lo_id="lo_a", observed_at="2026-05-19T12:02:00Z",
        signal_type=STUCK_CONFUSION_SIGNAL, subject_id="subj",
    )
    assert signal.outcome is None and signal.effective_mass == 0.0 and signal.attempt_id is None
    assert blocks_fast_track(signal)


def test_no_row_for_an_empty_stuck_step_a_stuck_answer_or_an_unbound_problem():
    sessions = [
        {"id": "s1", "practice_item_id": "pi_a", "attempt_id": None},
        {"id": "s2", "practice_item_id": "pi_a", "attempt_id": "at_stuck"},
        {"id": "s3", "practice_item_id": None, "attempt_id": None},
    ]
    steps = [
        _row("a", "stuck", "", "2026-05-19T12:01:00Z", session="s1"),
        # s2 was submitted with no ordinary step: its stuck text IS the stuck
        # answer, which the derivation already reads through the grader.
        _row("b", "stuck", "No idea where to begin.", "2026-05-19T12:01:00Z", session="s2"),
        _row("c", "stuck", "Lost.", "2026-05-19T12:01:00Z", session="s3"),
    ]
    diagnostics: dict = {}
    attempts = {"at_stuck": {"learning_object_id": "lo_a", "subject": "subj", "declared_stuck": True}}
    assert _derive(sessions, steps, attempts=attempts, diagnostics=diagnostics) == ()
    assert diagnostics["workbench_unmapped_sessions"] == 1
    assert diagnostics["workbench_stuck_rows"] == 0


def test_help_before_the_first_step_comes_only_from_the_logged_snapshot():
    sessions = [{"id": f"s{n}", "practice_item_id": "pi_a", "attempt_id": None} for n in range(1, 6)]

    def assist(aid, session, snapshot, kind="hint", at="2026-05-19T12:05:00Z"):
        return {"id": aid, "workbench_session_id": session, "assist_kind": kind, "requested_at": at,
                "step_snapshot_json": None if snapshot is None else json.dumps(snapshot)}

    stuck_only = [{"chain_id": "x", "kind": "stuck", "body_md": "Lost"}]
    work = [{"chain_id": "y", "kind": "step", "body_md": "Let X be..."}]
    signals = _derive(sessions, assists=[
        assist("h1", "s1", []),
        assist("h1b", "s1", [], at="2026-05-19T12:06:00Z"),  # one row per session, at its first request
        assist("h2", "s2", stuck_only, kind="example"),       # a stuck step is not work
        assist("h3", "s3", work),                             # help after a step: not early
        assist("h4", "s4", None),                             # no snapshot logged: not evidence
        assist("h5", "s5", [], kind="check"),                 # checking work is not asking for help
    ])
    assert [(s.signal_id, s.observed_at, s.help_before_work) for s in signals] == [
        ("workbench_help:s1", "2026-05-19T12:05:00Z", True),
        ("workbench_help:s2", "2026-05-19T12:05:00Z", True),
    ]
    assert all(s.outcome is None and s.effective_mass == 0.0 and s.attempt_id is None for s in signals)
    assert all(blocks_fast_track(s) for s in signals)


def test_the_successor_vocabulary_is_one_constant_after_its_predecessor():
    from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, defaults_fingerprint_for_version
    from learnloop.workbench_field_signals_upgrade import PREDECESSOR as UPGRADE_PREDECESSOR

    assert LATEST_ALGORITHM_VERSION == TAG == SUCCESSOR_CHAIN[-1]
    assert UPGRADE_PREDECESSOR == PREDECESSOR == INTENT_ALGORITHM_VERSION
    assert WORKBENCH_FIELD_SIGNALS_VERSIONS == frozenset({TAG})
    assert DEFAULTS_SNAPSHOT_BY_ALGORITHM[TAG] == defaults_fingerprint_for_version(TAG)


# ── the kill switch: the predecessor exactly ─────────────────────────────────


def _seed_everything(paths):
    _stuck_on_diag(paths)
    _early_help_on_diag(paths, minutes=3)
    _session(paths.sqlite_path, "wb_eig", "pi_eig_easy", minutes=4, status="abandoned")
    _step(paths.sqlite_path, "wb_eig", "st_e", "stuck", "Is lambda allowed to be zero?", minutes=5)


@pytest.mark.parametrize("variant", ["switch_off", "below_tag"])
def test_off_the_derivation_and_blocking_are_the_predecessors(tmp_path, variant):
    base_paths, base_vault, _ = _vault(tmp_path, "base", version=PREDECESSOR)
    if variant == "switch_off":
        paths, vault, _ = _vault(tmp_path, "off", toml=LOW_Q + OFF)
    else:
        paths, vault, _ = _vault(tmp_path, "below", version=PREDECESSOR)
    for target in (base_paths, paths):
        _seed_everything(target)
    assert _signals(paths, vault) == _signals(base_paths, base_vault)
    assert _blocking(paths, vault) == _blocking(base_paths, base_vault) == {}


def test_on_the_derivation_is_the_predecessors_plus_the_workbench_rows(tmp_path):
    from learnloop.field.workbench_signals import is_workbench_signal

    base_paths, base_vault, _ = _vault(tmp_path, "base", version=PREDECESSOR)
    paths, vault, _ = _vault(tmp_path, "on")
    for target in (base_paths, paths):
        _seed_everything(target)
    on = _signals(paths, vault)
    assert tuple(s for s in on if not is_workbench_signal(s)) == _signals(base_paths, base_vault)
    assert sorted(s.signal_id for s in on if is_workbench_signal(s)) == [
        "workbench_help:wb_help", "workbench_stuck:st_2", "workbench_stuck:st_e",
    ]
    assert _blocking(paths, vault) == {
        "lo_diag": ("workbench_help:wb_help", "workbench_stuck:st_2"),
        "lo_eigen_basics": ("workbench_stuck:st_e",),
    }


# ── Phase 6 serving: fast-track, the quick check, new-material order ─────────


@pytest.mark.parametrize("seed", [_stuck_on_diag, _early_help_on_diag], ids=["stuck_step", "early_help"])
def test_a_workbench_signal_withholds_fast_track_and_the_receipt_says_the_old_rule_fired(tmp_path, seed):
    paths, vault, repository = _vault(tmp_path)
    seed(paths)
    _two_clean_answers(vault, repository)
    assert reconcile_fast_track(vault, repository, clock=_at(20)) == []
    assert _decisions(paths) == []
    (receipt,) = _receipts(paths)
    assert (receipt["decision_kind"], receipt["learning_object_id"], receipt["algorithm_version"]) == (
        "fast_track", "lo_diag", TAG,
    )
    predecessor, successor = json.loads(receipt["predecessor_json"]), json.loads(receipt["successor_json"])
    assert (predecessor["verdict"], predecessor["blocking_signal_ids"]) == ("fires", [])
    assert (successor["verdict"], successor["reason"]) == ("withheld", "blocked_by_signal")
    assert json.loads(receipt["signal_ids_json"]) == successor["blocking_signal_ids"]
    # The persisting build reconciles again: the same state writes no second receipt.
    assert reconcile_fast_track(vault, repository, clock=_at(21)) == []
    assert len(_receipts(paths)) == 1

    # Control: switched off, the old rule fires and no receipt is written.
    off_paths, off_vault, off_repository = _vault(tmp_path, "off", toml=LOW_Q + OFF)
    seed(off_paths)
    _two_clean_answers(off_vault, off_repository)
    assert [d["source"] for d in reconcile_fast_track(off_vault, off_repository, clock=_at(20))] == ["fast_track"]
    assert _receipts(off_paths) == []


def test_a_stuck_step_teaches_the_lo_first_and_the_candidate_records_the_old_value(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    _session(paths.sqlite_path, "wb_eig", "pi_eig_easy", minutes=1, status="abandoned")
    _step(paths.sqlite_path, "wb_eig", "st_e", "stuck", "Is lambda allowed to be zero?", minutes=2)
    queue = _queue(vault, repository, 3, persist=False)
    new = [s for s in queue if s.components.get("new_material")]
    eig = [s for s in new if s.learning_object_id == "lo_eigen_basics"]
    assert eig and all(s.components["taught_first"] == 1.0 for s in eig)
    assert all(s.components["taught_first_predecessor"] == 0.0 for s in eig)
    assert all("taught_first_predecessor" not in s.components for s in new if s.learning_object_id != "lo_eigen_basics")

    off_paths, off_vault, off_repository = _vault(tmp_path, "off", toml=LOW_Q + OFF)
    _session(off_paths.sqlite_path, "wb_eig", "pi_eig_easy", minutes=1, status="abandoned")
    _step(off_paths.sqlite_path, "wb_eig", "st_e", "stuck", "Is lambda allowed to be zero?", minutes=2)
    off = [s for s in _queue(off_vault, off_repository, 3, persist=False) if s.components.get("new_material")]
    assert not any(s.components["taught_first"] for s in off)
    assert not any("taught_first_predecessor" in s.components for s in off)


def test_a_quick_check_split_records_the_predecessors_verdict(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    _stuck_on_diag(paths)
    session_id, progress = _start(vault, repository, ["lo_diag"], minutes=3)
    _answer_target(vault, repository, session_id, progress, 4)
    middle = _progress(vault, repository, progress, 5)
    _answer_target(vault, repository, session_id, middle, 6)
    done = _progress(vault, repository, progress, 7)
    (result,) = done["quick_check"]["results"]
    assert result["verdict"] == "learning"
    assert _decisions(paths) == []
    (receipt,) = [r for r in _receipts(paths) if r["decision_kind"] == "quick_check"]
    assert receipt["decision_ref"] == progress["calibration_session_id"]
    assert json.loads(receipt["predecessor_json"])["verdict"] == "assumed"
    assert json.loads(receipt["successor_json"])["reason"] == "blocked_by_signal"


# ── F2: never the record ─────────────────────────────────────────────────────


def test_a_stuck_step_or_early_help_never_lowers_the_record(tmp_path):
    """G13 for RW2d: evidence, mastery, certification and FSRS state are
    byte-identical with and without the workbench rows; only routing differs."""

    paths, vault, repository = _vault(tmp_path)
    _two_clean_answers(vault, repository)
    before = _snapshot(paths)
    _stuck_on_diag(paths, minutes=12)
    _early_help_on_diag(paths, minutes=13)
    assert reconcile_fast_track(vault, repository, clock=_at(16)) == []
    _queue(vault, repository, 17)
    assert _snapshot(paths) == before
    assert _decisions(paths) == []


def test_an_attempts_rows_and_hint_outcome_are_unchanged_by_its_workbench_rows(tmp_path):
    """The rows the record and the predictors read: an attempt's outcome, mass,
    assistance, strata and coldness, and a hinted attempt's graded outcome (not
    capped as help before work: the workbench row is linked to no attempt)."""

    from learnloop.field.outcomes import load_effective_replay_rows

    def run(name, seeded):
        paths, vault, repository = _vault(tmp_path, name)
        session_id = repository.create_session(available_minutes=25, clock=_at(0))
        if seeded:
            _session(paths.sqlite_path, "wb_x", "pi_diag_easy", minutes=1)
            _assist(paths.sqlite_path, "ha_x", "wb_x", minutes=1.5, snapshot=[], item_id="pi_diag_easy")
            _step(paths.sqlite_path, "wb_x", "st_x", "stuck", "Which basis?", minutes=2)
        hinted = _answer(vault, repository, "pi_diag_easy", minutes=3, hints=1, session_id=session_id)
        if seeded:
            with closing(_db(paths.sqlite_path)) as db, db:
                db.execute("UPDATE workbench_sessions SET status = 'submitted', attempt_id = ? WHERE id = 'wb_x'",
                           (hinted.attempt_id,))
        _two_clean_answers(vault, repository)
        with closing(connect(paths.sqlite_path, read_only=True)) as connection:
            attempts, facets, signals = load_effective_replay_rows(connection, vault)
        hints = [(s.outcome, s.help_before_work) for s in signals if s.signal_id.startswith("hint:")]
        rows = [(a.features.item_id, a.outcome, a.effective_mass, a.help_before_work, a.preceded_by_question,
                 a.features.cold, a.retrieval_cold) for a in attempts]
        facet_rows = [(f.facet_id, f.outcome, f.effective_mass, f.help_before_work, f.features.cold) for f in facets]
        return hints, rows, facet_rows, signals

    plain = run("plain", False)
    seeded = run("seeded", True)
    assert any(s.signal_id.startswith("workbench_") for s in seeded[3])
    assert seeded[:3] == plain[:3] and plain[0]


def test_enrich_attempts_ignores_workbench_rows():
    from learnloop.field.types import AttemptRow, ItemFeatures

    attempt = AttemptRow(
        attempt_id="at", features=ItemFeatures(item_id="pi", lo_id="lo", observed_at="2026-05-19T13:00:00Z"),
        outcome=1.0, effective_mass=1.0,
    )
    rows = (
        SignalRow("workbench_stuck:x", "lo", "2026-05-19T12:00:00Z", STUCK_CONFUSION_SIGNAL),
        SignalRow("workbench_help:s", "lo", "2026-05-19T12:00:00Z", "workbench_help_before_work",
                  help_before_work=True),
    )
    assert enrich_attempts((attempt,), rows) == enrich_attempts((attempt,), ())


def test_the_rebuild_never_reads_the_workbench_tables(tmp_path):
    from learnloop.field.outcomes import load_effective_replay_rows

    paths, vault, _ = _vault(tmp_path)
    _seed_everything(paths)
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        statements: list[str] = []
        connection.set_trace_callback(statements.append)
        attempts, _facets, signals = load_effective_replay_rows(connection, vault, include_workbench=False)
        connection.set_trace_callback(None)
        with_workbench = load_effective_replay_rows(connection, vault)
    assert statements and not any(("FROM workbench_" in s or "FROM help_assists" in s) for s in statements)
    assert not any(s.signal_id.startswith("workbench_") for s in signals)
    assert attempts == with_workbench[0]
    assert any(s.signal_id.startswith("workbench_") for s in with_workbench[2])


# ── the upgrade ──────────────────────────────────────────────────────────────


def test_upgrade_from_the_predecessor_and_through_the_chain(tmp_path):
    from typer.testing import CliRunner

    from learnloop.cli.app import app
    from learnloop.workbench_field_signals_upgrade import upgrade_to_workbench_field_signals

    direct = create_placement_vault(tmp_path / "direct", version=PREDECESSOR)
    result = upgrade_to_workbench_field_signals(direct.root)
    assert result.upgraded and (result.from_version, result.to_version) == (PREDECESSOR, TAG)
    assert load_vault(direct.root).config.algorithms.algorithm_version == TAG
    again = upgrade_to_workbench_field_signals(direct.root)
    assert not again.upgraded and again.problems == [f"vault is already {TAG}"]

    chained = create_placement_vault(tmp_path / "chained", version="mvp-0.27")
    assert upgrade_to_workbench_field_signals(chained.root).upgraded
    assert load_vault(chained.root).config.algorithms.algorithm_version == TAG

    old = create_placement_vault(tmp_path / "old", version="mvp-0.8")
    refused = upgrade_to_workbench_field_signals(old.root)
    assert not refused.upgraded and load_vault(old.root).config.algorithms.algorithm_version == "mvp-0.8"

    cli = create_placement_vault(tmp_path / "cli", version=PREDECESSOR)
    invoked = CliRunner().invoke(app, ["upgrade", "--vault", str(cli.root)])
    assert invoked.exit_code == 0, invoked.output
    assert f"{PREDECESSOR} -> {TAG}" in invoked.output


# ── G41 on fixture copies ────────────────────────────────────────────────────

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
WORKING_FIXTURES = ("linear_algebra", "probability", "arxiv_v2")
FROZEN = datetime(2026, 10, 12, 9, 30, tzinfo=UTC)


def _fixture_copy(tmp_path, fixture, name, *, version, toml=None):
    from tests.test_daily_plan_kill_switch import _copy

    ctx, root = _copy(tmp_path, fixture, name, version=version, toml=toml)
    item = sorted(ctx.vault.practice_items)[0]
    path = root / "state.sqlite"
    # The same workbench history on every copy: a stuck step and early help.
    _session(path, "wb_g41", item, minutes=1, status="abandoned")
    _step(path, "wb_g41", "st_g41", "stuck", "I don't follow the second line.", minutes=2)
    _session(path, "wb_g41h", item, minutes=3)
    _assist(path, "ha_g41", "wb_g41h", minutes=4, snapshot=[], item_id=item)
    ctx.load(root)
    return ctx, root


def _reads(ctx):
    from tests.test_daily_plan_kill_switch import _call, _served, _today_reads

    reads = _today_reads(ctx)
    reads["plan"] = _served(_call(ctx, "get_daily_plan", {}))
    with closing(connect(ctx.repository.sqlite_path, read_only=True)) as connection:
        answers = load_answers(connection)
        reads["signals"] = load_interaction_signals(connection, ctx.vault, _attempt_rows(answers))
        reads["blocking"] = blocking_signals_by_lo(connection, ctx.vault, answers)
    return reads


_ULID = re.compile(r"\b[0-9A-HJKMNP-TV-Z]{26}\b")


def _strip_plan_ids(value):
    """A plan as served, without the ids its build mints or the version label."""

    if isinstance(value, dict):
        return {k: _strip_plan_ids(v) for k, v in value.items() if k != "algorithmVersion"}
    if isinstance(value, list):
        return [_strip_plan_ids(v) for v in value]
    return _ULID.sub("<id>", value) if isinstance(value, str) else value


@pytest.mark.parametrize("fixture", WORKING_FIXTURES)
def test_g41_off_is_the_predecessor_on_fixture_copies(tmp_path, monkeypatch, fixture):
    import learnloop.clock as clock_module

    if not (FIXTURES / fixture / "state.sqlite").exists():
        pytest.skip(f"{fixture} fixture absent")
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: FROZEN)
    base, _ = _fixture_copy(tmp_path, fixture, "base", version=PREDECESSOR)
    off, _ = _fixture_copy(tmp_path, fixture, "off", version=TAG, toml=OFF)
    baseline = _reads(base)
    assert baseline["queue"]["totalItems"] > 0
    got = _reads(off)
    # Today's queue and Start are equal as served; the plan up to the ids
    # its build mints and the version label it carries.
    assert {k: got[k] for k in ("queue", "queue_25", "start")} == {k: baseline[k] for k in ("queue", "queue_25", "start")}
    assert _strip_plan_ids(got["plan"]) == _strip_plan_ids(baseline["plan"])
    assert got["signals"] == baseline["signals"] and got["blocking"] == baseline["blocking"]

    # On: the same derivation plus exactly the workbench rows (the receipts'
    # "predecessor" is that derivation without them).
    from learnloop.field.workbench_signals import is_workbench_signal

    on, _ = _fixture_copy(tmp_path, fixture, "on", version=TAG)
    signals = _reads(on)["signals"]
    assert tuple(s for s in signals if not is_workbench_signal(s)) == baseline["signals"]
    assert {s.signal_id for s in signals if is_workbench_signal(s)} == {"workbench_stuck:st_g41", "workbench_help:wb_g41h"}
