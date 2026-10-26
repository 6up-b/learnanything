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
    ADAPTIVE_DIFFICULTY_ALGORITHM_VERSION,
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

from tests.owner_vaults import owner_vault, working_vault_params
from tests.helpers import NOW, append_config_toml, create_placement_vault, set_algorithm_version
from tests.test_assumed_known import EVIDENCE_TABLES, LOW_Q, _answer, _at, _decisions, _queue, _snapshot
from tests.test_quick_check import _answer_target, _progress, _start
from tests.workbench_help_fakes import call, help_rows, run_job

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


#: The placement vault's items and their LOs (the contract a session freezes).
ITEM_LOS = {"pi_diag_easy": "lo_diag", "pi_diag_mid": "lo_diag", "pi_diag_hard": "lo_diag",
            "pi_eig_easy": "lo_eigen_basics"}


def _contract(path, item_id, lo, *, tag):
    """An assessment-contract snapshot for ``item_id`` naming ``lo`` (its id)."""

    version_id = f"acv_{tag}"
    with closing(_db(path)) as db, db:
        db.execute(
            "INSERT INTO assessment_contract_versions (id, practice_item_id, contract_hash, contract_json, "
            "schema_version, created_at) VALUES (?, ?, ?, ?, 1, ?)",
            (version_id, item_id, f"test:{tag}", json.dumps({"practice_item_id": item_id, "learning_object_id": lo}),
             _iso(0)),
        )
    return version_id


#: The placement vault's subject (its LOs' first; its items name none).
SUBJECT = "linear-algebra"


def _session(path, session_id, item_id, *, minutes, attempt_id=None, status=None, lo=None, contract=True,
             subject=SUBJECT):
    """A workbench session; bound to ``item_id`` it froze its contract (the
    item's LO, or ``lo``) and the subject with it (``subject``; None: not on
    record) as the sidecar's open does, unless ``contract`` is false."""

    status = status or ("submitted" if attempt_id else "open")
    version_id = None
    if item_id and contract:
        version_id = _contract(path, item_id, lo or ITEM_LOS[item_id], tag=session_id)
    with closing(_db(path)) as db, db:
        db.execute(
            "INSERT INTO workbench_sessions (id, practice_item_id, stem_md, import_status, origin, entry, "
            "status, attempt_id, client_idempotency_key, created_at, updated_at, assessment_contract_version_id, "
            "contract_subject_id) "
            "VALUES (?, ?, 'A problem.', ?, 'reader', 'work_through', ?, ?, ?, ?, ?, ?, ?)",
            (session_id, item_id, "bound" if item_id else "pending", status, attempt_id,
             f"key-{session_id}", _iso(minutes), _iso(minutes), version_id, subject if version_id else None),
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

    # A session bound to pi_a froze contract cv_a (on lo_a) and its subject
    # unless it names its own.
    sessions = [{"assessment_contract_version_id": "cv_a" if s.get("practice_item_id") else None,
                 "contract_subject_id": "subj" if s.get("practice_item_id") else None, **s}
                for s in sessions]
    return derive_workbench_signals(
        sessions, steps, assists, attempts=attempts or {}, contract_targets={"cv_a": "lo_a"},
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


def test_no_row_for_an_empty_stuck_step_or_an_unbound_problem():
    sessions = [
        {"id": "s1", "practice_item_id": "pi_a", "attempt_id": None},
        {"id": "s3", "practice_item_id": None, "attempt_id": None},
        # Bound, but no contract on record (opened before contracts were frozen).
        {"id": "s4", "practice_item_id": "pi_a", "attempt_id": None, "assessment_contract_version_id": None},
    ]
    steps = [
        _row("a", "stuck", "", "2026-05-19T12:01:00Z", session="s1"),
        _row("c", "stuck", "Lost.", "2026-05-19T12:01:00Z", session="s3"),
        _row("d", "stuck", "Lost.", "2026-05-19T12:01:00Z", session="s4"),
    ]
    diagnostics: dict = {}
    assert _derive(sessions, steps, diagnostics=diagnostics) == ()
    assert diagnostics["workbench_unmapped_sessions"] == 2
    assert diagnostics["workbench_stuck_rows"] == 0


def test_review_f2_a_stuck_answer_keeps_the_step_time_row_through_delete_submit_and_grading():
    """Review F2: a stuck step with text, deleted, then the empty workbench
    submitted (``declared_stuck``) or graded later: the row the step made
    stays, from the step's own time, before and after the submit."""

    steps = [
        _row("b", "stuck", "No idea where to begin.", "2026-05-19T12:01:00Z", session="s2"),
        _row("b2", "stuck", "No idea where to begin.", "2026-05-19T12:02:00Z", session="s2", supersedes="b",
             deleted=1),
    ]
    open_session = [{"id": "s2", "practice_item_id": "pi_a", "attempt_id": None}]
    before = _derive(open_session, steps)
    submitted = [{"id": "s2", "practice_item_id": "pi_a", "attempt_id": "at_stuck"}]
    for attempt in ({"learning_object_id": "lo_a", "subject": "subj", "declared_stuck": True},
                    {"learning_object_id": "lo_a", "subject": "subj", "declared_stuck": True,
                     "graded_at": "2026-05-19T15:00:00Z"}):
        after = _derive(submitted, steps, attempts={"at_stuck": attempt})
        assert after == before == (SignalRow(
            signal_id="workbench_stuck:b", lo_id="lo_a", observed_at="2026-05-19T12:01:00Z",
            signal_type=STUCK_CONFUSION_SIGNAL, subject_id="subj",
        ),)


def test_review_f2_the_row_survives_the_submit_on_the_vault(tmp_path):
    """The same transition through the loader: the step-time row and its
    blocking are unchanged by submitting the (now empty) workbench."""

    paths, vault, repository = _vault(tmp_path)
    _session(paths.sqlite_path, "wb_s", "pi_diag_easy", minutes=1)
    _step(paths.sqlite_path, "wb_s", "st_s", "stuck", "I don't see why P is invertible.", minutes=2)
    _step(paths.sqlite_path, "wb_s", "st_s2", "stuck", "I don't see why P is invertible.", minutes=3,
          supersedes="st_s", deleted=1)

    def workbench_rows():
        return [(s.signal_id, s.lo_id, s.observed_at) for s in _signals(paths, vault) if s.signal_id.startswith("workbench_")]

    before = workbench_rows()
    assert before == [("workbench_stuck:st_s", "lo_diag", _iso(2))]
    from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt

    # The submit of the now-empty bench: the existing empty stuck answer.
    answered = complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id="pi_diag_easy", learner_answer_md="", attempt_type="independent_attempt",
                     declared_stuck=True),
        SelfGradeInput(criterion_points={"correctness": 0.0}, confidence=1), clock=_at(5),
    )
    with closing(_db(paths.sqlite_path)) as db:
        assert db.execute("SELECT declared_stuck FROM practice_attempts WHERE id = ?",
                          (answered.attempt_id,)).fetchone()[0] == 1
    with closing(_db(paths.sqlite_path)) as db, db:
        db.execute("UPDATE workbench_sessions SET status = 'submitted', attempt_id = ? WHERE id = 'wb_s'",
                   (answered.attempt_id,))
    assert workbench_rows() == before
    assert "workbench_stuck:st_s" in _blocking(paths, vault)["lo_diag"]


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


def test_review_f1_an_identity_only_snapshot_is_read_through_its_step_rows():
    """Review F1: the worked example logs each step's identity only (chain,
    step row id, number, hash). Its entries are read through the immutable
    step rows they name; an entry whose row is not found is unknown, never
    "no work"."""

    sessions = [{"id": f"s{n}", "practice_item_id": "pi_a", "attempt_id": None} for n in range(1, 5)]
    steps = [
        _row("w1", "step", "Let X be the CDF.", "2026-05-19T12:01:00Z", session="s1"),
        _row("k2", "stuck", "Lost", "2026-05-19T12:01:00Z", session="s2"),
        _row("w3", "step", "Let X be the CDF.", "2026-05-19T12:01:00Z", session="s3"),
    ]

    def example(aid, session, step_ids):
        snapshot = [{"chain_id": sid, "step_id": sid, "number": n, "hash": "h"} for n, sid in enumerate(step_ids, 1)]
        return {"id": aid, "workbench_session_id": session, "assist_kind": "example",
                "requested_at": "2026-05-19T12:05:00Z", "step_snapshot_json": json.dumps(snapshot)}

    signals = _derive(sessions, steps, assists=[
        example("e1", "s1", ["w1"]),             # ordinary work on record: not early
        example("e2", "s2", ["k2"]),             # only a stuck step: early
        example("e3", "s3", ["gone", "w3"]),     # work found beside an unknown entry: not early
        example("e4", "s4", ["gone"]),           # unknown entry, no work found: unknown, no row
    ])
    early = [s.signal_id for s in signals if s.signal_id.startswith("workbench_help:")]
    assert early == ["workbench_help:s2"]


def test_review_f1_a_worked_example_after_real_work_is_not_early_help(tmp_path):
    """Review F1 through the real producer: the learner writes ordinary steps,
    then asks for a similar worked example; its logged snapshot (identity only)
    holds work, so no help-before-work row is derived, and the session's
    frozen contract gives the target."""

    from learnloop.field.workbench_signals import load_workbench_signals
    from tests.test_workbench_route_example import OTHER, ROUTE, FindFake
    from tests.workbench_help_fakes import open_problem, sidecar

    paths, ctx, _practice = sidecar(tmp_path)
    set_algorithm_version(paths, TAG)  # the hint vault is pinned below the successor
    ctx.load(paths.root)
    ctx.workbench_example_find = FindFake([OTHER, ROUTE])
    ctx.passage_draw_seed = "seed-ex"
    wb, _chains = open_problem(ctx, origin="reader", entry="work_through")
    vault, _repository = ctx.require_vault()
    assert vault.config.algorithms.algorithm_version == TAG
    shown = run_job(ctx, call(ctx, "workbench.show_example", {"sessionId": wb}))
    assert shown["status"] == "ready"
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "example"]
    entries = json.loads(row["step_snapshot_json"])
    assert entries and all("kind" not in e and "body_md" not in e for e in entries)  # the production format
    diagnostics: dict = {}
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        signals = load_workbench_signals(connection, vault, diagnostics=diagnostics)
    assert not [s for s in signals if s.help_before_work]
    assert diagnostics["workbench_unmapped_sessions"] == 0

    # Control: the same request with no work on the bench is early help.
    with closing(_db(paths.sqlite_path)) as db, db:
        db.execute("UPDATE help_assists SET step_snapshot_json = '[]' WHERE id = ?", (row["id"],))
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        signals = load_workbench_signals(connection, vault)
    assert [s.signal_id for s in signals if s.help_before_work] == [f"workbench_help:{wb}"]


def test_review_f3_an_edited_or_removed_item_keeps_the_signal_on_the_frozen_lo(tmp_path):
    """Review F3: an abandoned session's signal stays on the LO of the contract
    it froze; moving the item to another LO, or removing it, changes nothing."""

    from learnloop.learner.assessment_contracts import snapshot_for_presentation

    paths, vault, repository = _vault(tmp_path)
    version_id = snapshot_for_presentation(repository, vault, vault.practice_items["pi_diag_easy"])
    _session(paths.sqlite_path, "wb_f3", "pi_diag_easy", minutes=1, status="abandoned", contract=False)
    with closing(_db(paths.sqlite_path)) as db, db:
        db.execute("UPDATE workbench_sessions SET assessment_contract_version_id = ? WHERE id = 'wb_f3'",
                   (version_id,))
    _step(paths.sqlite_path, "wb_f3", "st_f3", "stuck", "Why is P invertible?", minutes=2)

    def rows():
        return [(s.signal_id, s.lo_id) for s in _signals(paths, vault) if s.signal_id.startswith("workbench_")]

    assert rows() == [("workbench_stuck:st_f3", "lo_diag")]
    original = vault.practice_items["pi_diag_easy"]
    vault.practice_items["pi_diag_easy"] = original.model_copy(update={"learning_object_id": "lo_eigen_basics"})
    assert rows() == [("workbench_stuck:st_f3", "lo_diag")]
    assert "lo_eigen_basics" not in _blocking(paths, vault)
    del vault.practice_items["pi_diag_easy"]
    assert rows() == [("workbench_stuck:st_f3", "lo_diag")]


def test_rereview_f3_the_subject_is_the_one_frozen_with_the_contract(tmp_path):
    """Re-review F3: an unsubmitted session's subject is the one recorded when
    it froze its contract, so editing the item's (or its LO's) subject changes
    no historical row, and the subject-aware check keeps its verdict. A session
    whose subject was never recorded says so (``SUBJECT_UNRECORDED``), never
    today's label; per-LO routing still blocks it."""

    from learnloop.field.signals import confusion_blocks_fast_track
    from learnloop.field.workbench_signals import SUBJECT_UNRECORDED

    paths, vault, repository = _vault(tmp_path)
    _session(paths.sqlite_path, "wb_s", "pi_diag_easy", minutes=1, status="abandoned")
    _step(paths.sqlite_path, "wb_s", "st_s", "stuck", "Why is P invertible?", minutes=2)
    _session(paths.sqlite_path, "wb_u", "pi_eig_easy", minutes=1, status="abandoned", subject=None)
    _step(paths.sqlite_path, "wb_u", "st_u", "stuck", "Lost at the eigenvectors.", minutes=2)
    as_of = _iso(10)
    expected = [("workbench_stuck:st_s", "lo_diag", SUBJECT),
                ("workbench_stuck:st_u", "lo_eigen_basics", SUBJECT_UNRECORDED)]

    def rows(diagnostics=None):
        with closing(connect(paths.sqlite_path, read_only=True)) as connection:
            signals = load_interaction_signals(connection, vault, _attempt_rows(load_answers(connection)),
                                               diagnostics=diagnostics)
        return signals, sorted((s.signal_id, s.lo_id, s.subject_id) for s in signals
                               if s.signal_id.startswith("workbench_"))

    diagnostics: dict = {}
    signals, before = rows(diagnostics)
    assert before == expected
    assert diagnostics["workbench_subject_unrecorded_sessions"] == 1
    assert confusion_blocks_fast_track(signals, lo_id="lo_diag", as_of=as_of, subject_id=SUBJECT)
    for item_id in ("pi_diag_easy", "pi_eig_easy"):
        vault.practice_items[item_id] = vault.practice_items[item_id].model_copy(update={"subjects": ["physics"]})
    for lo_id in ("lo_diag", "lo_eigen_basics"):
        vault.learning_objects[lo_id] = vault.learning_objects[lo_id].model_copy(update={"subjects": ["physics"]})
    signals, after = rows()
    assert after == expected
    assert confusion_blocks_fast_track(signals, lo_id="lo_diag", as_of=as_of, subject_id=SUBJECT)
    assert not confusion_blocks_fast_track(signals, lo_id="lo_diag", as_of=as_of, subject_id="physics")
    assert not confusion_blocks_fast_track(signals, lo_id="lo_eigen_basics", as_of=as_of, subject_id="physics")
    blocking = _blocking(paths, vault)
    assert "workbench_stuck:st_s" in blocking["lo_diag"]
    assert "workbench_stuck:st_u" in blocking["lo_eigen_basics"]


def test_rereview_f3_the_sidecar_records_the_subject_with_the_contract(tmp_path):
    """Re-review F3: the open that freezes a session's contract records the
    subject a submit would then have recorded; a resume after the item's
    subject changed keeps it, and a bind to another item clears both."""

    from learnloop.reader import workbench as WB
    from tests.test_reader_workbench_rw2a import ITEM, _context, _open, _vault as _rw2a_vault

    paths, repository = _rw2a_vault(tmp_path)
    ctx = _context(paths.root)
    item = ctx.vault.practice_items[ITEM]
    (frozen, *_) = ctx.vault.subjects_for_item(item)
    session = _open(ctx)
    assert session["assessmentContractVersionId"]

    def recorded(session_id):
        return WB.session_row(repository, session_id)["contract_subject_id"]

    assert recorded(session["sessionId"]) == frozen
    ctx.vault.practice_items[ITEM] = item.model_copy(update={"subjects": ["physics"]})
    again = _open(ctx)
    assert again["sessionId"] == session["sessionId"]
    assert recorded(session["sessionId"]) == frozen
    with closing(_db(repository.sqlite_path)) as db, db:
        db.execute("UPDATE workbench_sessions SET import_status = 'pending' WHERE id = ?", (session["sessionId"],))
    WB.bind(repository, session["sessionId"], "pi_transpose_001")
    row = WB.session_row(repository, session["sessionId"])
    assert row["assessment_contract_version_id"] is None and row["contract_subject_id"] is None


def test_review_f4_a_long_autosaved_history_resolves_in_linear_time():
    """Review F4: thousands of autosaved versions of ordinary and stuck steps
    resolve once each (memoized roots); the old walk was cubic."""

    import time

    steps = [_row("o0", "step", "x = 0", "2026-05-19T12:00:00Z")]
    for n in range(1, 4000):
        steps.append(_row(f"o{n}", "step", f"x = {n}", "2026-05-19T12:00:00Z", supersedes=f"o{n - 1}"))
    steps.append(_row("k0", "stuck", "", "2026-05-19T12:00:01Z"))
    for n in range(1, 3000):
        steps.append(_row(f"k{n}", "stuck", f"why {n}", "2026-05-19T12:00:01Z", supersedes=f"k{n - 1}"))
    started = time.perf_counter()
    (signal,) = _derive([{"id": "s1", "practice_item_id": "pi_a", "attempt_id": None}], steps)
    assert time.perf_counter() - started < 2.0
    assert signal.signal_id == "workbench_stuck:k0"


def test_the_successor_vocabulary_is_one_constant_after_its_predecessor():
    from learnloop.config.template import DEFAULTS_SNAPSHOT_BY_ALGORITHM, defaults_fingerprint_for_version
    from learnloop.workbench_field_signals_upgrade import PREDECESSOR as UPGRADE_PREDECESSOR

    # Reader workbench RW7b's mvp-0.32, LP-min (a)'s mvp-0.33, rebuild equivalence's mvp-0.34 and Reader
    # CA2's mvp-0.35 (the latest) follow it and keep it.
    assert TAG == SUCCESSOR_CHAIN[21] and LATEST_ALGORITHM_VERSION == SUCCESSOR_CHAIN[-1] == "mvp-0.35"
    # Landed after adaptive difficulty AD2+AD3: its mvp-0.30 is the predecessor (the landing renumber).
    assert UPGRADE_PREDECESSOR == PREDECESSOR == ADAPTIVE_DIFFICULTY_ALGORITHM_VERSION == "mvp-0.30"
    assert TAG == "mvp-0.31"
    assert WORKBENCH_FIELD_SIGNALS_VERSIONS == frozenset({TAG, "mvp-0.32", "mvp-0.33", "mvp-0.34", "mvp-0.35"})
    assert DEFAULTS_SNAPSHOT_BY_ALGORITHM[TAG] == defaults_fingerprint_for_version(TAG)


def test_the_switch_is_on_by_default_and_classified():
    from learnloop.config.schema import WorkbenchConfig
    from learnloop.field.workbench_signals import workbench_field_signals_live
    from learnloop.params import parameter_registry as registry

    assert WorkbenchConfig().field_signals_enabled is True
    assert registry.classify_config_path("workbench.field_signals_enabled") is not None
    config = type("C", (), {"algorithms": type("A", (), {"algorithm_version": TAG})(),
                            "workbench": WorkbenchConfig()})()
    assert workbench_field_signals_live(type("V", (), {"config": config})())
    config.algorithms.algorithm_version = PREDECESSOR
    assert not workbench_field_signals_live(type("V", (), {"config": config})())


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

    for start in ("mvp-0.27", "mvp-0.29"):  # through AD2+AD3's step (and DL2's, from mvp-0.27)
        chained = create_placement_vault(tmp_path / f"chained-{start}", version=start)
        assert upgrade_to_workbench_field_signals(chained.root).upgraded, start
        assert load_vault(chained.root).config.algorithms.algorithm_version == TAG

    old = create_placement_vault(tmp_path / "old", version="mvp-0.8")
    refused = upgrade_to_workbench_field_signals(old.root)
    assert not refused.upgraded and load_vault(old.root).config.algorithms.algorithm_version == "mvp-0.8"

    cli = create_placement_vault(tmp_path / "cli", version=PREDECESSOR)
    # RW2d's own step (the default target is the latest's, rebuild equivalence's, since its landing).
    invoked = CliRunner().invoke(app, ["upgrade", "--vault", str(cli.root), "--to", TAG])
    assert invoked.exit_code == 0, invoked.output
    assert f"{PREDECESSOR} -> {TAG}" in invoked.output


# ── G41 on fixture copies ────────────────────────────────────────────────────

# The owner's working vaults: backup-API copies in the owner_vaults lane (S0).
WORKING_FIXTURES = working_vault_params()
FROZEN = datetime(2026, 10, 12, 9, 30, tzinfo=UTC)


def _fixture_copy(tmp_path, fixture, name, *, version, toml=None):
    from tests.test_daily_plan_kill_switch import _copy

    ctx, root = _copy(tmp_path, fixture, name, version=version, toml=toml)
    item = sorted(ctx.vault.practice_items)[0]
    path = root / "state.sqlite"
    # The same workbench history on every copy: a stuck step and early help.
    lo = ctx.vault.practice_items[item].learning_object_id
    _session(path, "wb_g41", item, minutes=1, status="abandoned", lo=lo)
    _step(path, "wb_g41", "st_g41", "stuck", "I don't follow the second line.", minutes=2)
    _session(path, "wb_g41h", item, minutes=3, lo=lo)
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

    if not (owner_vault(fixture) / "state.sqlite").exists():
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
