"""Reader workbench RW2a: the resumable scratchpad (spec_reader_workbench_v1
§5.1, §5.4, §5.7, §5.9; docs/reviews/reader-workbench-RW2a.md).

A problem worked in steps, saved as typed (append-only versions, tombstones,
idempotency keys), resumable after a restart, abandonable and reopened, opened
at once before the exercise import binds it (G58), and submitted through the
ordinary attempt path with the source-visible rule (G5's book rows, G10): a
visible book is one hint-equivalent, a hidden one is the learner's own
attempt, and the submit asks the one eligibility decision every submit asks.
The grader reads the composed answer only (G6). Switched off, every workbench
RPC refuses and nothing else changes (G11). Fakes only.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

from learnloop import serve_eligibility
from learnloop.attempts import salience_firewall as SF
from learnloop.clock import FrozenClock, utc_now_iso
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.table_roles import TableRole, tables_for_role
from learnloop.diagnosis.causal_activity_policy import resolve_attempt_activity_policy
from learnloop.reader import workbench as WB
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault
from learnloop_sidecar.errors import SidecarError

from tests.split_live_helpers import ReadyRuntime, append_config, split_vault
from tests.test_stuck_prompt import RefusingClient, StuckFake

ITEM = "pi_svd_compute_001"
OTHER_ITEM = "pi_transpose_001"
STEM = "Exercise 5.14: write the SVD of A."
EXTRACTION = "ext_wb"
WORKBENCH_TABLES = ("workbench_sessions", "workbench_steps")


# -- harness ------------------------------------------------------------------------------------


def _call(ctx, name: str, params: dict):
    import learnloop_sidecar.handlers  # noqa: F401 - register methods
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _context(root):
    from learnloop_sidecar.context import SidecarContext

    ctx = SidecarContext()
    ctx.load(root)
    return ctx


def _vault(tmp_path, *, config: str = ""):
    paths, _vault, repository = split_vault(tmp_path, version="mvp-0.27", config=config)
    return paths, repository


@pytest.fixture
def grader(monkeypatch):
    """A blind grader fake behind the sidecar's grading provider."""

    import learnloop_sidecar.handlers.practice as practice

    client = StuckFake()
    monkeypatch.setattr(
        practice, "ready_grading_provider", lambda vault, override=None: ("fake", ReadyRuntime(), client)
    )
    return client


def _open(ctx, **params):
    payload = {"origin": "reader", "entry": "work_through", "practiceItemId": ITEM, "stemMd": STEM,
               "extractionId": EXTRACTION, "spanIds": ["s5"], **params}
    return _call(ctx, "workbench.open", payload)["session"]


def _step(ctx, session_id: str, key: str, op: str = "add", **params):
    return _call(ctx, "workbench.save_step", {"sessionId": session_id, "clientIdempotencyKey": key, "op": op, **params})


def _submit(ctx, session_id: str, **params):
    return _call(ctx, "workbench.submit", {"sessionId": session_id, **params})


def _attempt(repository: Repository, attempt_id: str) -> dict:
    with connect(repository.sqlite_path, read_only=True) as connection:
        return dict(connection.execute("SELECT * FROM practice_attempts WHERE id = ?", (attempt_id,)).fetchone())


def _count(repository: Repository, table: str, where: str = "1 = 1", args: tuple = ()) -> int:
    with connect(repository.sqlite_path, read_only=True) as connection:
        return connection.execute(f'SELECT COUNT(*) FROM "{table}" WHERE {where}', args).fetchone()[0]


def _bodies(view: dict) -> list[str]:
    return [step["bodyMd"] for step in view["steps"]]


# -- migration 207 and table roles ---------------------------------------------------------------


def test_migration_207_creates_both_tables_with_every_check_value(tmp_path):
    _paths, repository = _vault(tmp_path)
    now = "2026-10-17T09:00:00Z"
    with connect(repository.sqlite_path) as connection:
        for index, (origin, entry, status, import_status, style) in enumerate(zip(
            ("reader", "practice", "plan", "reader", "reader", "reader", "reader", "reader"),
            WB.ENTRIES,
            ("open", "abandoned", "open", "open", "open", "open", "open", "open"),
            ("none", "pending", "failed", "none", "none", "none", "none", "none"),
            ("let_me_struggle", "balanced", "guide_me", None, None, None, None, None),
            strict=True,
        )):
            connection.execute(
                "INSERT INTO workbench_sessions(id, stem_md, import_status, origin, entry, status, help_style,"
                " created_at, updated_at) VALUES (?, 'stem', ?, ?, ?, ?, ?, ?, ?)",
                (f"wb{index}", import_status, origin, entry, status, style, now, now),
            )
        connection.execute(
            "INSERT INTO workbench_sessions(id, practice_item_id, stem_md, import_status, origin, entry, status,"
            " attempt_id, created_at, updated_at) VALUES ('wbs', 'pi', 'stem', 'bound', 'reader', 'resume',"
            " 'submitted', 'att', ?, ?)", (now, now),
        )
        for bad in ("origin", "entry", "status", "import_status", "help_style"):
            values = {"origin": "reader", "entry": "work_through", "status": "open", "import_status": "none",
                      "help_style": None, bad: "nonsense"}
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(
                    "INSERT INTO workbench_sessions(id, stem_md, import_status, origin, entry, status, help_style,"
                    " created_at, updated_at) VALUES ('bad', 'stem', :import_status, :origin, :entry, :status,"
                    " :help_style, 'x', 'x')", values,
                )
        with pytest.raises(sqlite3.IntegrityError):  # bound without an item
            connection.execute(
                "INSERT INTO workbench_sessions(id, stem_md, import_status, origin, entry, created_at, updated_at)"
                " VALUES ('bad2', 'stem', 'bound', 'reader', 'work_through', 'x', 'x')"
            )
        for kind in WB.STEP_KINDS:
            connection.execute(
                "INSERT INTO workbench_steps(id, session_id, ordinal, kind, body_md, client_idempotency_key,"
                " created_at) VALUES (?, 'wb0', 1.0, ?, 'x', ?, ?)", (f"st_{kind}", kind, f"k_{kind}", now),
            )
        connection.commit()
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            connection.execute("UPDATE workbench_steps SET body_md = 'changed'")
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            connection.execute("DELETE FROM workbench_steps")


def test_both_tables_are_classified_and_never_derived():
    assert "workbench_sessions" in tables_for_role(TableRole.WORKFLOW)
    assert "workbench_steps" in tables_for_role(TableRole.RAW_LEDGER)
    assert not set(WORKBENCH_TABLES) & set(tables_for_role(TableRole.DERIVED))


def test_the_kill_switch_and_open_session_days_default_on_and_30(tmp_path):
    paths, _repository = _vault(tmp_path)
    vault = load_vault(paths.root)
    assert WB.workbench_enabled(vault) is True
    assert WB.open_session_days(vault) == 30


# -- book visibility by entry (UX S7, D9) ----------------------------------------------------------


@pytest.mark.parametrize(("entry", "origin", "visible"), [
    ("work_through", "reader", True),
    ("resume", "reader", True),
    ("path_exercise", "reader", True),
    ("check_me", "reader", False),
    ("practice_this", "reader", False),
    ("discriminating_problem", "reader", False),
    ("plan", "plan", False),
    ("practice_screen", "practice", False),
    # Off the Reader there is no source pane: never visible, whatever the entry.
    ("work_through", "practice", False),
])
def test_the_default_book_visibility_follows_the_entry(entry, origin, visible):
    assert WB.default_book_visible(entry, origin) is visible


def test_an_opened_session_starts_with_its_entrys_book(tmp_path):
    paths, _repository = _vault(tmp_path)
    ctx = _context(paths.root)
    assert _open(ctx)["sourceVisible"] is True
    assert _open(ctx, entry="check_me", practiceItemId=OTHER_ITEM)["sourceVisible"] is False


# -- saving as typed (G32) -----------------------------------------------------------------------


def test_steps_save_as_typed_with_versions_tombstones_and_idempotency_keys(tmp_path):
    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    session = _open(ctx)
    first = _step(ctx, session["sessionId"], "k1", bodyMd="A = U Sigma V^T")["step"]
    second = _step(ctx, session["sessionId"], "k2", bodyMd="U holds the left singular vectors", afterStepId=first["stepId"])["step"]
    # An edit is a new version superseding the old one; the old text is kept.
    edited = _step(ctx, session["sessionId"], "k3", op="edit", stepId=first["stepId"], bodyMd="A = U \\Sigma V^T")["step"]
    assert edited["stepId"] != first["stepId"]
    # A retried write with the same key writes nothing and answers the same row.
    rows = _count(repository, "workbench_steps")
    again = _step(ctx, session["sessionId"], "k3", op="edit", stepId=first["stepId"], bodyMd="A = U \\Sigma V^T")["step"]
    assert again["stepId"] == edited["stepId"] and _count(repository, "workbench_steps") == rows
    view = _call(ctx, "workbench.get", {"sessionId": session["sessionId"]})["session"]
    assert _bodies(view) == ["A = U \\Sigma V^T", "U holds the left singular vectors"]
    assert [version["bodyMd"] for version in view["steps"][0]["versions"]] == ["A = U Sigma V^T"]
    # A delete is a tombstone: hidden from the work, its text kept; undo restores it.
    gone = _step(ctx, session["sessionId"], "k4", op="delete", stepId=second["stepId"])["step"]
    assert gone["deleted"] is True
    assert _bodies(_call(ctx, "workbench.get", {"sessionId": session["sessionId"]})["session"]) == ["A = U \\Sigma V^T"]
    _step(ctx, session["sessionId"], "k5", op="restore", stepId=gone["stepId"])
    view = _call(ctx, "workbench.get", {"sessionId": session["sessionId"]})["session"]
    assert _bodies(view) == ["A = U \\Sigma V^T", "U holds the left singular vectors"]
    assert view["lastEditedStepId"] == view["steps"][1]["stepId"]
    # Nothing was ever updated in place: five writes, five rows.
    assert _count(repository, "workbench_steps") == 5


def test_a_step_added_after_another_takes_its_place_and_a_stale_id_edits_the_newest_version(tmp_path):
    paths, _repository = _vault(tmp_path)
    ctx = _context(paths.root)
    session = _open(ctx)
    one = _step(ctx, session["sessionId"], "a", bodyMd="one")["step"]
    three = _step(ctx, session["sessionId"], "b", bodyMd="three")["step"]
    _step(ctx, session["sessionId"], "c", bodyMd="two", afterStepId=one["stepId"])
    newer = _step(ctx, session["sessionId"], "d", op="edit", stepId=three["stepId"], bodyMd="three!")["step"]
    # An edit sent with the older id lands on the newest version of the chain.
    _step(ctx, session["sessionId"], "e", op="edit", stepId=three["stepId"], bodyMd="three!!")
    view = _call(ctx, "workbench.get", {"sessionId": session["sessionId"]})["session"]
    assert _bodies(view) == ["one", "two", "three!!"]
    assert newer["stepId"] in [version["stepId"] for version in view["steps"][2]["versions"]]


def test_steps_and_the_book_survive_a_sidecar_restart(tmp_path):
    paths, _repository = _vault(tmp_path)
    ctx = _context(paths.root)
    session = _open(ctx, entry="check_me")
    _call(ctx, "workbench.set_book", {"sessionId": session["sessionId"], "visible": True})
    one = _step(ctx, session["sessionId"], "a", bodyMd="one")["step"]
    _step(ctx, session["sessionId"], "b", bodyMd="two")
    _step(ctx, session["sessionId"], "c", op="edit", stepId=one["stepId"], bodyMd="one, revised")
    _call(ctx, "workbench.leave", {"sessionId": session["sessionId"]})
    restarted = _context(paths.root)
    view = _call(restarted, "workbench.get", {"sessionId": session["sessionId"]})["session"]
    assert view["status"] == "open"
    assert _bodies(view) == ["one, revised", "two"]
    assert view["sourceVisible"] is True and view["record"]["bookCounted"] is True
    assert view["lastEditedStepId"] == view["steps"][0]["stepId"]
    assert view["spanIds"] == ["s5"] and view["extractionId"] == EXTRACTION
    # Opening the same item again resumes the open session instead of a new one.
    again = _call(restarted, "workbench.open", {"origin": "reader", "entry": "resume", "practiceItemId": ITEM,
                                                 "stemMd": STEM, "extractionId": EXTRACTION, "spanIds": ["s5"]})
    assert again["resumed"] is True and again["session"]["sessionId"] == session["sessionId"]


# -- leave, abandon, reopen (UX S13) -------------------------------------------------------------


def test_leave_keeps_it_open_abandon_closes_it_reopen_opens_it_and_none_writes_an_attempt(tmp_path):
    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    attempts = _count(repository, "practice_attempts")
    session = _open(ctx)
    _step(ctx, session["sessionId"], "a", bodyMd="one")
    assert _call(ctx, "workbench.leave", {"sessionId": session["sessionId"]})["session"]["status"] == "open"
    closed = _call(ctx, "workbench.abandon", {"sessionId": session["sessionId"]})["session"]
    assert closed["status"] == "abandoned" and closed["closedAt"] and _bodies(closed) == ["one"]
    with pytest.raises(SidecarError) as refused:
        _step(ctx, session["sessionId"], "b", bodyMd="two")
    assert refused.value.code == "not_open"
    with pytest.raises(SidecarError) as refused:
        _submit(ctx, session["sessionId"])
    assert refused.value.code == "not_open"
    reopened = _call(ctx, "workbench.reopen", {"sessionId": session["sessionId"]})["session"]
    assert reopened["status"] == "open" and reopened["closedAt"] is None and _bodies(reopened) == ["one"]
    assert _count(repository, "practice_attempts") == attempts
    events = [e["payload"]["event"] for e in repository.reader_interaction_events(kind="reader_action_invoked")
              if e["payload"].get("workbench_session_id") == session["sessionId"]]
    assert events == ["workbench_opened", "workbench_left", "workbench_closed", "workbench_reopened"]


def test_a_submitted_session_cannot_be_reopened_or_edited(tmp_path, grader):
    paths, _repository = _vault(tmp_path)
    ctx = _context(paths.root)
    session = _open(ctx)
    _step(ctx, session["sessionId"], "a", bodyMd="A = U Sigma V^T")
    _submit(ctx, session["sessionId"])
    for name, params in (("workbench.reopen", {}), ("workbench.abandon", {})):
        with pytest.raises(SidecarError) as refused:
            _call(ctx, name, {"sessionId": session["sessionId"], **params})
        assert refused.value.code in {"not_open", "already_submitted"}


# -- opening at once (G58, UX S2) ------------------------------------------------------------------


@pytest.fixture
def imports(monkeypatch):
    """The exercise import behind the workbench: enqueued and polled by fakes."""

    import learnloop_sidecar.handlers.workbench as handler

    state = {"enqueued": [], "jobs": {}}

    def enqueue(ctx, vault, repository, request):
        batch = f"batch_{len(state['enqueued']) + 1}"
        state["enqueued"].append(dict(request))
        state["jobs"][batch] = {"status": "running", "result": None, "error": None}
        return batch

    monkeypatch.setattr(handler, "_enqueue_import", enqueue)
    monkeypatch.setattr(handler, "_import_job", lambda ctx, repository, batch_id: state["jobs"].get(batch_id))
    return state


def _selection_open(ctx):
    return _call(ctx, "workbench.open", {
        "origin": "reader", "entry": "work_through", "stemMd": STEM, "extractionId": EXTRACTION,
        "spanIds": ["s5", "s6"],
        "importRequest": {"extractionId": EXTRACTION, "rawSelection": {"nodes": [{"spanId": "s5"}]}},
    })["session"]


def _imported(*item_ids: str) -> dict:
    return {"status": "completed", "error": None, "result": {
        "items": [{"practiceItemId": item_id, "title": f"part {index + 1}", "prompt": STEM}
                  for index, item_id in enumerate(item_ids)],
    }}


def test_a_selected_problem_opens_at_once_and_steps_save_before_the_import_binds(tmp_path, imports, grader):
    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    session = _selection_open(ctx)
    assert session["practiceItemId"] is None and session["importStatus"] == "pending"
    assert session["stemMd"] == STEM and len(imports["enqueued"]) == 1
    _step(ctx, session["sessionId"], "a", bodyMd="A = U Sigma V^T")
    # Submit waits for the bound item, and says so; nothing is written.
    attempts = _count(repository, "practice_attempts")
    with pytest.raises(SidecarError) as refused:
        _submit(ctx, session["sessionId"])
    assert refused.value.code == "not_bound" and "setup" in refused.value.message
    assert _count(repository, "practice_attempts") == attempts
    still = _call(ctx, "workbench.refresh_import", {"sessionId": session["sessionId"]})["session"]
    assert still["importStatus"] == "pending"
    imports["jobs"]["batch_1"] = _imported(ITEM)
    bound = _call(ctx, "workbench.refresh_import", {"sessionId": session["sessionId"]})["session"]
    assert bound["importStatus"] == "bound" and bound["practiceItemId"] == ITEM
    assert _bodies(bound) == ["A = U Sigma V^T"]
    payload = _submit(ctx, session["sessionId"])
    assert _attempt(repository, payload["attempt"]["attemptId"])["practice_item_id"] == ITEM


def test_a_multi_part_import_asks_which_part_and_binds_only_one_of_its_own(tmp_path, imports):
    paths, _repository = _vault(tmp_path)
    ctx = _context(paths.root)
    session = _selection_open(ctx)
    imports["jobs"]["batch_1"] = _imported(ITEM, "pi_svd_compute_002")
    asking = _call(ctx, "workbench.refresh_import", {"sessionId": session["sessionId"]})["session"]
    assert asking["importStatus"] == "pending"
    assert [part["practiceItemId"] for part in asking["parts"]] == [ITEM, "pi_svd_compute_002"]
    with pytest.raises(SidecarError):
        _call(ctx, "workbench.bind", {"sessionId": session["sessionId"], "practiceItemId": OTHER_ITEM})
    bound = _call(ctx, "workbench.bind", {"sessionId": session["sessionId"], "practiceItemId": "pi_svd_compute_002"})
    assert bound["session"]["practiceItemId"] == "pi_svd_compute_002" and bound["session"]["importStatus"] == "bound"


def test_a_failed_import_keeps_the_steps_writes_no_attempt_and_tries_again(tmp_path, imports):
    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    attempts = _count(repository, "practice_attempts")
    session = _selection_open(ctx)
    _step(ctx, session["sessionId"], "a", bodyMd="my first move")
    imports["jobs"]["batch_1"] = {"status": "failed", "result": None, "error": {"message": "the model timed out"}}
    failed = _call(ctx, "workbench.refresh_import", {"sessionId": session["sessionId"]})["session"]
    assert failed["importStatus"] == "failed" and failed["importError"] == "the model timed out"
    assert _bodies(failed) == ["my first move"] and _count(repository, "practice_attempts") == attempts
    retried = _call(ctx, "workbench.retry_import", {"sessionId": session["sessionId"]})["session"]
    assert retried["importStatus"] == "pending" and len(imports["enqueued"]) == 2
    assert imports["enqueued"][1] == imports["enqueued"][0]
    # A restart before the import lands keeps waiting on the same batch.
    restarted = _context(paths.root)
    imports["jobs"]["batch_2"] = _imported(ITEM)
    assert _call(restarted, "workbench.refresh_import", {"sessionId": session["sessionId"]})["session"]["importStatus"] == "bound"


def test_an_import_that_cannot_start_opens_the_session_failed_with_the_steps_writable(tmp_path, monkeypatch):
    import learnloop_sidecar.handlers.workbench as handler

    def unavailable(ctx, vault, repository, request):
        raise SidecarError("provider_unavailable", "The AI provider is unavailable for exercise authoring.")

    monkeypatch.setattr(handler, "_enqueue_import", unavailable)
    paths, _repository = _vault(tmp_path)
    ctx = _context(paths.root)
    session = _selection_open(ctx)
    assert session["importStatus"] == "failed" and "unavailable" in session["importError"]
    assert _step(ctx, session["sessionId"], "a", bodyMd="still mine")["step"]["bodyMd"] == "still mine"


# -- what an attempt records (G5's book rows, G10, G62) ----------------------------------------------


def _policy(row: dict):
    return resolve_attempt_activity_policy(
        attempt_type=row["attempt_type"], primed=bool(row["primed"]), hints_used=int(row["hints_used"])
    )


def test_the_book_open_in_the_reader_is_one_hint_and_the_attempt_is_assisted(tmp_path, grader):
    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    session = _open(ctx)
    _step(ctx, session["sessionId"], "a", bodyMd="A = U Sigma V^T")
    view = _call(ctx, "workbench.get", {"sessionId": session["sessionId"]})["session"]
    assert view["record"] == {**view["record"], "bookCounted": True, "hints": 1, "ownAttempt": False}
    assert "book open" in view["record"]["line"] and "with help" in view["record"]["line"]
    payload = _submit(ctx, session["sessionId"])
    row = _attempt(repository, payload["attempt"]["attemptId"])
    assert row["hints_used"] == view["record"]["hints"] == 1
    assert row["entry_surface"] == "desktop_reader_workbench"
    assert row["attempt_type"] == "hinted_attempt" and not row["primed"] and not row["declared_stuck"]
    policy = _policy(row)
    assert policy.counts_as_assisted and policy.eligible_for_fsrs and not policy.eligible_for_certification
    done = payload["session"]
    assert done["status"] == "submitted" and done["attemptId"] == row["id"]
    assert done["practiceSessionId"] == row["session_id"]


def test_the_book_hidden_before_the_first_step_is_the_learners_own_attempt(tmp_path, grader):
    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    session = _open(ctx)
    _call(ctx, "workbench.set_book", {"sessionId": session["sessionId"], "visible": False})
    _step(ctx, session["sessionId"], "a", bodyMd="A = U Sigma V^T")
    view = _call(ctx, "workbench.get", {"sessionId": session["sessionId"]})["session"]
    assert view["record"]["ownAttempt"] is True and view["record"]["hints"] == 0
    assert view["record"]["line"] == "your own attempt"
    row = _attempt(repository, _submit(ctx, session["sessionId"])["attempt"]["attemptId"])
    assert row["hints_used"] == 0 and row["attempt_type"] == "independent_attempt"
    policy = _policy(row)
    assert not policy.counts_as_assisted and policy.eligible_for_certification


def test_flipping_the_book_before_the_first_step_is_free(tmp_path, grader):
    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    session = _open(ctx, entry="check_me")
    for visible in (True, False, True, False):
        _call(ctx, "workbench.set_book", {"sessionId": session["sessionId"], "visible": visible})
    _step(ctx, session["sessionId"], "a", bodyMd="A = U Sigma V^T")
    row = _attempt(repository, _submit(ctx, session["sessionId"])["attempt"]["attemptId"])
    assert row["hints_used"] == 0


def test_opening_the_book_after_a_step_counts_from_then_on_even_if_hidden_again(tmp_path, grader):
    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    session = _open(ctx, entry="check_me")
    _step(ctx, session["sessionId"], "a", bodyMd="A = U Sigma V^T")
    assert _call(ctx, "workbench.get", {"sessionId": session["sessionId"]})["session"]["record"]["hints"] == 0
    shown = _call(ctx, "workbench.set_book", {"sessionId": session["sessionId"], "visible": True})["session"]
    assert shown["record"]["bookCounted"] is True
    hidden = _call(ctx, "workbench.set_book", {"sessionId": session["sessionId"], "visible": False})["session"]
    assert hidden["sourceVisible"] is False and hidden["record"]["bookCounted"] is True
    assert hidden["sourceHiddenAt"]
    row = _attempt(repository, _submit(ctx, session["sessionId"])["attempt"]["attemptId"])
    assert row["hints_used"] == 1
    changes = [e["payload"] for e in repository.reader_interaction_events(kind="reader_action_invoked")
               if e["payload"].get("event") == "book_visibility_changed"]
    assert [change["visible"] for change in changes] == [True, False]
    assert [change["counts"] for change in changes] == [True, True]


def test_the_practice_screen_never_shows_the_book_and_records_its_own_surface(tmp_path, grader):
    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    practice_session = _call(ctx, "start_session", {})["sessionId"]
    session = _call(ctx, "workbench.open", {"origin": "practice", "entry": "practice_screen", "practiceItemId": ITEM,
                                            "stemMd": "Write the SVD of A."})["session"]
    assert session["sourceVisible"] is False
    with pytest.raises(SidecarError):
        _call(ctx, "workbench.set_book", {"sessionId": session["sessionId"], "visible": True})
    _step(ctx, session["sessionId"], "a", bodyMd="A = U Sigma V^T")
    payload = _submit(ctx, session["sessionId"], practiceSessionId=practice_session)
    row = _attempt(repository, payload["attempt"]["attemptId"])
    assert row["hints_used"] == 0 and row["entry_surface"] == "desktop_practice_workbench"
    assert row["session_id"] == practice_session


def test_submit_uses_the_open_practice_session_or_starts_one(tmp_path, grader):
    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    session = _open(ctx)
    _step(ctx, session["sessionId"], "a", bodyMd="A = U Sigma V^T")
    payload = _submit(ctx, session["sessionId"])
    started = payload["practiceSession"]["sessionId"]
    assert repository.fetch_session(started)["ended_at"] is None
    assert _attempt(repository, payload["attempt"]["attemptId"])["session_id"] == started
    other = _open(ctx, practiceItemId=OTHER_ITEM)
    _step(ctx, other["sessionId"], "a", bodyMd="M^T")
    assert _submit(ctx, other["sessionId"])["practiceSession"]["sessionId"] == started


def test_a_retried_submit_answers_the_same_attempt(tmp_path, grader):
    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    session = _open(ctx)
    _step(ctx, session["sessionId"], "a", bodyMd="A = U Sigma V^T")
    first = _submit(ctx, session["sessionId"])
    attempts = _count(repository, "practice_attempts")
    # The response was lost after the session was marked submitted: the
    # client resends, and the submission's receipt answers (review F10).
    again = _submit(ctx, session["sessionId"])
    assert again["attempt"]["attemptId"] == first["attempt"]["attemptId"]
    assert again["attempt"] == first["attempt"]
    assert again["session"]["status"] == "submitted"
    assert again["practiceSession"]["sessionId"] == first["practiceSession"]["sessionId"]
    assert _count(repository, "practice_attempts") == attempts
    # After a restart too.
    restarted = _context(paths.root)
    assert _submit(restarted, session["sessionId"])["attempt"]["attemptId"] == first["attempt"]["attemptId"]
    assert _count(repository, "practice_attempts") == attempts


def test_an_empty_submit_is_the_existing_empty_stuck_answer_with_no_model_call(tmp_path, monkeypatch):
    import learnloop_sidecar.handlers.practice as practice

    monkeypatch.setattr(
        practice, "ready_grading_provider", lambda vault, override=None: ("fake", ReadyRuntime(), RefusingClient())
    )
    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    session = _open(ctx, entry="check_me")
    _step(ctx, session["sessionId"], "a", kind="stuck", bodyMd="")
    view = _call(ctx, "workbench.get", {"sessionId": session["sessionId"]})["session"]
    assert view["record"]["stuckNote"] == "Submitting now records 'stuck' — that's fine"
    payload = _submit(ctx, session["sessionId"])
    row = _attempt(repository, payload["attempt"]["attemptId"])
    assert row["declared_stuck"] and row["learner_answer_md"] == "" and row["rubric_score"] == 0
    assert payload["attempt"]["gradingSource"] == "deterministic"


def test_stuck_text_stays_learner_work_and_the_steps_are_an_ordinary_answer(tmp_path, grader):
    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    session = _open(ctx, entry="check_me")
    _step(ctx, session["sessionId"], "a", kind="stuck", bodyMd="I can't see where Sigma comes from")
    _step(ctx, session["sessionId"], "b", bodyMd="A = U Sigma V^T")
    row = _attempt(repository, _submit(ctx, session["sessionId"])["attempt"]["attemptId"])
    assert row["learner_answer_md"] == "A = U Sigma V^T" and not row["declared_stuck"]


def test_only_stuck_text_is_submitted_as_the_existing_written_stuck_answer(tmp_path, grader):
    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    session = _open(ctx, entry="check_me")
    _step(ctx, session["sessionId"], "a", kind="stuck", bodyMd="I can't see where Sigma comes from")
    row = _attempt(repository, _submit(ctx, session["sessionId"])["attempt"]["attemptId"])
    assert row["declared_stuck"] and row["learner_answer_md"] == "I can't see where Sigma comes from"


def test_an_abandoned_session_writes_no_attempt_and_a_rebuild_leaves_the_workbench_alone(tmp_path, grader):
    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    kept = _open(ctx)
    _step(ctx, kept["sessionId"], "a", bodyMd="A = U Sigma V^T")
    _submit(ctx, kept["sessionId"])
    dropped = _open(ctx, practiceItemId=OTHER_ITEM)
    _step(ctx, dropped["sessionId"], "a", bodyMd="M^T")
    attempts = _count(repository, "practice_attempts")
    _call(ctx, "workbench.abandon", {"sessionId": dropped["sessionId"]})
    assert _count(repository, "practice_attempts") == attempts

    def snapshot(tables):
        with connect(repository.sqlite_path, read_only=True) as connection:
            return {table: sorted(json.dumps(dict(row), sort_keys=True, default=str)
                                  for row in connection.execute(f'SELECT * FROM "{table}"')) for table in tables}

    kept_attempt = _call(ctx, "workbench.get", {"sessionId": kept["sessionId"]})["session"]["attemptId"]
    evidence = ("practice_attempts", "grading_evidence")
    before = snapshot((*WORKBENCH_TABLES, *evidence))
    vault = load_vault(paths.root)
    clock = FrozenClock(datetime(2026, 10, 30, 12, 0, tzinfo=UTC))
    rebuild_all_derived_state(vault, repository, clock=clock)
    rebuild_all_derived_state(vault, repository, clock=clock)
    # A rebuild reads the attempt (its hints_used) and never the workbench.
    assert snapshot((*WORKBENCH_TABLES, *evidence)) == before
    assert _attempt(repository, kept_attempt)["hints_used"] == 1


# -- the grader stays blind (G6) ---------------------------------------------------------------------


def test_the_grader_reads_the_composed_answer_only(tmp_path, grader):
    paths, _repository = _vault(tmp_path)
    ctx = _context(paths.root)
    session = _open(ctx)
    first = _step(ctx, session["sessionId"], "a", bodyMd="DRAFT-ONE A = U V")["step"]
    _step(ctx, session["sessionId"], "b", op="edit", stepId=first["stepId"], bodyMd="A = U Sigma V^T")
    gone = _step(ctx, session["sessionId"], "c", bodyMd="DELETED-STEP nonsense")["step"]
    _step(ctx, session["sessionId"], "d", op="delete", stepId=gone["stepId"])
    _step(ctx, session["sessionId"], "e", kind="stuck", bodyMd="STUCK-TEXT where is Sigma from")
    _step(ctx, session["sessionId"], "f", bodyMd="Sigma holds the singular values")
    _submit(ctx, session["sessionId"])
    rendered = json.dumps(grader.contexts, default=str)
    assert "A = U Sigma V^T\\n\\nSigma holds the singular values" in rendered
    for leaked in ("DRAFT-ONE", "DELETED-STEP", "STUCK-TEXT", session["sessionId"], "workbench", "book open"):
        assert leaked not in rendered


# -- the one eligibility decision (mvp-0.27) ---------------------------------------------------------


def _due_cold_check(repository: Repository, item: str = ITEM):
    now = datetime.now(UTC)
    return repository.create_followup_task(
        kind="cold_retry", case_kind="misconception", case_ref="ep_wb",
        not_before=utc_now_iso(FrozenClock(now - timedelta(days=1))),
        expires_at=utc_now_iso(FrozenClock(now + timedelta(days=29))),
        selected_item_id=item, clock=FrozenClock(now - timedelta(days=2)),
    )


def test_a_workbench_submit_asks_the_same_eligibility_decision_as_every_submit(tmp_path, grader, monkeypatch):
    asked = []
    decide = serve_eligibility.decide

    def spy(inputs, request):
        asked.append((request, inputs))
        return decide(inputs, request)

    monkeypatch.setattr(serve_eligibility, "decide", spy)
    paths, _repository = _vault(tmp_path)
    ctx = _context(paths.root)
    practice_session = _call(ctx, "start_session", {})["sessionId"]
    # The practice screen's answer box with one hint: the reference.
    _call(ctx, "submit_attempt", {"sessionId": practice_session, "practiceItemId": OTHER_ITEM, "answerMd": "M^T",
                                  "attemptType": "hinted_attempt", "hintsUsed": 1})
    ordinary = [inputs for request, inputs in asked if request == serve_eligibility.SUBMIT]
    asked.clear()
    session = _open(ctx)
    _step(ctx, session["sessionId"], "a", bodyMd="A = U Sigma V^T")
    _submit(ctx, session["sessionId"], practiceSessionId=practice_session)
    workbench = [inputs for request, inputs in asked if request == serve_eligibility.SUBMIT]
    assert workbench and len(workbench) == len(ordinary)
    assert {(inputs.practice_item_id, inputs.hints_used, inputs.attempt_type) for inputs in workbench} == {
        (ITEM, 1, "hinted_attempt")
    }


def test_a_cold_check_with_the_book_open_is_refused_and_the_session_and_steps_stay(tmp_path, grader):
    paths, repository = _vault(tmp_path)
    _due_cold_check(repository)
    ctx = _context(paths.root)
    attempts = _count(repository, "practice_attempts")
    session = _open(ctx)
    _step(ctx, session["sessionId"], "a", bodyMd="A = U Sigma V^T")
    with pytest.raises(SidecarError) as refused:
        _submit(ctx, session["sessionId"])
    assert refused.value.code == "validation_error"
    assert _count(repository, "practice_attempts") == attempts
    view = _call(ctx, "workbench.get", {"sessionId": session["sessionId"]})["session"]
    assert view["status"] == "open" and _bodies(view) == ["A = U Sigma V^T"]
    # The same problem on your own (the book never counted) is admitted as the check.
    _call(ctx, "workbench.abandon", {"sessionId": session["sessionId"]})
    own = _open(ctx, entry="check_me")
    _step(ctx, own["sessionId"], "a", bodyMd="A = U Sigma V^T")
    row = _attempt(repository, _submit(ctx, own["sessionId"])["attempt"]["attemptId"])
    assert row["hints_used"] == 0


def test_with_the_eligibility_switch_off_the_old_cold_guard_still_refuses_the_book(tmp_path, grader):
    paths, repository = _vault(tmp_path, config="[eligibility]\nenabled = false")
    _due_cold_check(repository)
    ctx = _context(paths.root)
    session = _open(ctx)
    _step(ctx, session["sessionId"], "a", bodyMd="A = U Sigma V^T")
    with pytest.raises(SidecarError) as refused:
        _submit(ctx, session["sessionId"])
    assert "unassisted" in refused.value.message


# -- reads: for an attempt, an item, a source (RW6a's recap) -------------------------------------------


def test_the_session_for_an_attempt_is_found_for_a_workbench_attempt_and_nothing_else(tmp_path, grader):
    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    session = _open(ctx)
    _step(ctx, session["sessionId"], "a", bodyMd="A = U Sigma V^T")
    payload = _submit(ctx, session["sessionId"])
    found = _call(ctx, "workbench.session_for_attempt", {"attemptId": payload["attempt"]["attemptId"]})["session"]
    assert found["sessionId"] == session["sessionId"] and found["status"] == "submitted"
    assert found["origin"] == "reader" and found["spanIds"] == ["s5"] and _bodies(found) == ["A = U Sigma V^T"]
    practice_session = payload["practiceSession"]["sessionId"]
    plain = _call(ctx, "submit_attempt", {"sessionId": practice_session, "practiceItemId": OTHER_ITEM,
                                          "answerMd": "M^T", "attemptType": "independent_attempt"})
    assert _call(ctx, "workbench.session_for_attempt", {"attemptId": plain["attemptId"]})["session"] is None
    assert _attempt(repository, plain["attemptId"])["entry_surface"] == "desktop_practice"


def test_for_item_and_for_source_list_open_and_abandoned_problems_never_submitted_ones(tmp_path, grader):
    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    open_one = _open(ctx)
    _step(ctx, open_one["sessionId"], "a", bodyMd="one")
    dropped = _open(ctx, practiceItemId=OTHER_ITEM)
    _call(ctx, "workbench.abandon", {"sessionId": dropped["sessionId"]})
    done = _open(ctx, practiceItemId="pi_eigen_001")
    _step(ctx, done["sessionId"], "a", bodyMd="P D P^{-1}")
    _submit(ctx, done["sessionId"])
    listed = _call(ctx, "workbench.for_source", {"extractionId": EXTRACTION})["sessions"]
    assert {(row["sessionId"], row["status"]) for row in listed} == {
        (open_one["sessionId"], "open"), (dropped["sessionId"], "abandoned"),
    }
    assert next(row for row in listed if row["sessionId"] == open_one["sessionId"])["stepCount"] == 1
    for_item = _call(ctx, "workbench.for_item", {"practiceItemId": ITEM})["sessions"]
    assert [row["sessionId"] for row in for_item] == [open_one["sessionId"]]
    assert _call(ctx, "workbench.for_item", {"practiceItemId": "pi_eigen_001"})["sessions"] == []


def test_an_open_session_past_open_session_days_is_unfinished_and_never_closed(tmp_path):
    _paths, repository = _vault(tmp_path)
    then = datetime(2026, 9, 1, 9, 0, tzinfo=UTC)
    row, _resumed = WB.open_session(repository, origin="reader", entry="work_through", stem_md=STEM,
                                    practice_item_id=ITEM, extraction_id=EXTRACTION, span_ids=["s5"],
                                    clock=FrozenClock(then))
    soon = WB.sessions_for_source(repository, EXTRACTION, now=then + timedelta(days=29), open_days=30)
    later = WB.sessions_for_source(repository, EXTRACTION, now=then + timedelta(days=31), open_days=30)
    assert [entry["unfinished"] for entry in soon] == [False]
    assert [entry["unfinished"] for entry in later] == [True]
    assert WB.session_row(repository, row["id"])["status"] == "open"


# -- nothing but the attempt is evidence (W1, G5) -------------------------------------------------------


def test_the_lifecycle_writes_only_workbench_rows_and_salience_only_events(tmp_path):
    from tests.test_reader_inquiry_status import table_counts

    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    before = table_counts(repository)
    session = _open(ctx)
    one = _step(ctx, session["sessionId"], "a", bodyMd="one")["step"]
    _step(ctx, session["sessionId"], "b", op="edit", stepId=one["stepId"], bodyMd="one!")
    _call(ctx, "workbench.set_book", {"sessionId": session["sessionId"], "visible": False})
    _call(ctx, "workbench.leave", {"sessionId": session["sessionId"]})
    _call(ctx, "workbench.abandon", {"sessionId": session["sessionId"]})
    _call(ctx, "workbench.reopen", {"sessionId": session["sessionId"]})
    after = table_counts(repository)
    changed = {name for name in after if after[name] != before.get(name)}
    # Besides its own rows and salience-only events, a session writes only
    # what a serve writes: the contract it shows (review F1) and the book's
    # exposure of its spans (review F11). Neither is evidence.
    assert changed <= set(WORKBENCH_TABLES) | {
        "interaction_events", "assessment_contract_versions", "source_exposure_events",
    }


@pytest.mark.parametrize("event", WB.SERVER_WORKBENCH_EVENTS)
def test_every_workbench_event_is_salience_only(tmp_path, imports, event):
    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    session = _selection_open(ctx)
    _call(ctx, "workbench.leave", {"sessionId": session["sessionId"]})
    _call(ctx, "workbench.abandon", {"sessionId": session["sessionId"]})
    _call(ctx, "workbench.reopen", {"sessionId": session["sessionId"]})
    _call(ctx, "workbench.set_book", {"sessionId": session["sessionId"], "visible": False})
    imports["jobs"]["batch_1"] = _imported(ITEM)
    _call(ctx, "workbench.refresh_import", {"sessionId": session["sessionId"]})
    _call(ctx, "workbench.open", {"origin": "reader", "entry": "resume", "practiceItemId": ITEM, "stemMd": STEM,
                                  "extractionId": EXTRACTION, "spanIds": ["s5", "s6"]})
    rows = [e for e in repository.reader_interaction_events(kind="reader_action_invoked")
            if e["payload"].get("event") == event]
    assert rows, event
    for row in rows:
        assert row["payload"]["authority_class"] == SF.SALIENCE_ONLY
        with pytest.raises(SF.SalienceEvidenceRejected):
            SF.reject_salience(row)


# -- the kill switch (G11) -------------------------------------------------------------------------------


WORKBENCH_RPCS = (
    ("workbench.open", {"origin": "reader", "entry": "work_through", "stemMd": STEM, "practiceItemId": ITEM}),
    ("workbench.get", {"sessionId": "wb"}),
    ("workbench.save_step", {"sessionId": "wb", "clientIdempotencyKey": "k", "op": "add", "bodyMd": "x"}),
    ("workbench.set_book", {"sessionId": "wb", "visible": True}),
    ("workbench.leave", {"sessionId": "wb"}),
    ("workbench.abandon", {"sessionId": "wb"}),
    ("workbench.reopen", {"sessionId": "wb"}),
    ("workbench.refresh_import", {"sessionId": "wb"}),
    ("workbench.bind", {"sessionId": "wb", "practiceItemId": ITEM}),
    ("workbench.retry_import", {"sessionId": "wb"}),
    ("workbench.submit", {"sessionId": "wb"}),
    ("workbench.session_for_attempt", {"attemptId": "att"}),
    ("workbench.for_item", {"practiceItemId": ITEM}),
    ("workbench.for_source", {"extractionId": EXTRACTION}),
)


def test_switched_off_every_workbench_rpc_refuses_and_writes_nothing(tmp_path):
    from tests.test_reader_inquiry_status import table_counts

    paths, repository = _vault(tmp_path, config="[workbench]\nenabled = false")
    ctx = _context(paths.root)
    before = table_counts(repository)
    events = _count(repository, "interaction_events")
    for name, params in WORKBENCH_RPCS:
        with pytest.raises(SidecarError) as refused:
            _call(ctx, name, params)
        assert refused.value.code == "workbench_disabled", name
    assert table_counts(repository) == before
    assert _count(repository, "interaction_events") == events


def test_switched_off_the_config_and_the_practice_rpcs_are_what_they_were(tmp_path, grader):
    """The config DTO carries the workbench only while it is on; the practice
    screen's own RPCs never read it: the same serve and the same submit write
    the same rows with it on or off."""

    shapes = {}
    for label, config in (("on", ""), ("off", "[workbench]\nenabled = false")):
        paths, repository = _vault(tmp_path / label, config=config)
        ctx = _context(paths.root)
        snapshot_config = ctx.app_snapshot()["config"]
        session_id = _call(ctx, "start_session", {})["sessionId"]
        served = _call(ctx, "get_practice_item", {"practiceItemId": ITEM, "sessionId": session_id})
        payload = _call(ctx, "submit_attempt", {"sessionId": session_id, "practiceItemId": ITEM,
                                                "answerMd": "A = U Sigma V^T", "attemptType": "independent_attempt"})
        row = _attempt(repository, payload["attemptId"])
        shapes[label] = {
            "config": {key: value for key, value in snapshot_config.items() if key != "workbench"},
            "workbench_key": "workbench" in snapshot_config,
            "served": {key: served[key] for key in sorted(served) if key in ("prompt", "practiceItemId", "hints", "attemptTypesAllowed")},
            "served_keys": sorted(served),
            "row": {key: row[key] for key in ("hints_used", "attempt_type", "entry_surface", "primed", "declared_stuck",
                                              "rubric_score", "learner_answer_md")},
        }
    assert shapes["on"]["workbench_key"] is True and shapes["off"]["workbench_key"] is False
    assert shapes["on"]["config"] == shapes["off"]["config"]
    assert shapes["on"]["served"] == shapes["off"]["served"]
    assert shapes["on"]["served_keys"] == shapes["off"]["served_keys"]
    assert shapes["on"]["row"] == shapes["off"]["row"]
    assert shapes["on"]["row"]["entry_surface"] == "desktop_practice"


# -- review fixes (docs/reviews/reader-rw2a-codex-review.md) ---------------------------------------------


def _with_method(ctx, item_id: str = ITEM, *, prompt: str | None = None, method: str = "the spectral theorem"):
    from learnloop.vault.models import RequiredMethod

    item = ctx.vault.practice_items[item_id]
    update = {"required_method": RequiredMethod(name=method, criterion_ids=["result"])}
    if prompt is not None:
        update["prompt"] = prompt
    ctx.vault.practice_items[item_id] = item.model_copy(update=update)


def _graded_contracts(repository: Repository, attempt_id: str) -> set[str]:
    with connect(repository.sqlite_path, read_only=True) as connection:
        rows = connection.execute(
            "SELECT DISTINCT assessment_contract_version_id FROM grading_evidence WHERE attempt_id = ?", (attempt_id,)
        ).fetchall()
    return {row[0] for row in rows}


def test_f1_a_resumed_problem_is_graded_against_the_contract_it_showed(tmp_path, grader):
    from learnloop.learner.assessment_contracts import snapshot_for_presentation

    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    session = _open(ctx, entry="check_me")
    shown = session["assessmentContractVersionId"]
    assert shown
    _step(ctx, session["sessionId"], "a", bodyMd="A = U Sigma V^T")
    # The item gains a required method before the learner comes back.
    _with_method(ctx, prompt="Factor A.")
    current = snapshot_for_presentation(repository, ctx.vault, ctx.vault.practice_items[ITEM])
    assert current != shown
    resumed = _call(ctx, "workbench.open", {"origin": "reader", "entry": "resume", "sessionId": session["sessionId"]})
    assert resumed["session"]["assessmentContractVersionId"] == shown
    payload = _submit(ctx, session["sessionId"])
    assert _graded_contracts(repository, payload["attempt"]["attemptId"]) == {shown}


def test_f1_a_bound_import_snapshots_the_contract_of_the_item_it_bound(tmp_path, imports):
    from learnloop.learner.assessment_contracts import snapshot_for_presentation

    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    session = _selection_open(ctx)
    assert session["assessmentContractVersionId"] is None
    imports["jobs"]["batch_1"] = _imported(ITEM)
    bound = _call(ctx, "workbench.refresh_import", {"sessionId": session["sessionId"]})["session"]
    expected = snapshot_for_presentation(repository, ctx.vault, ctx.vault.practice_items[ITEM])
    assert bound["assessmentContractVersionId"] == expected


def test_f9_the_bound_problem_carries_the_items_whole_presentation(tmp_path, imports):
    paths, _repository = _vault(tmp_path)
    ctx = _context(paths.root)
    _with_method(ctx)
    session = _open(ctx)
    blocks = session["presentation"]["blocks"]
    assert [block["kind"] for block in blocks] == ["prompt", "required_method_instruction"]
    assert blocks[0]["markdown"] == "Write the SVD of A."
    assert "the spectral theorem" in blocks[1]["markdown"]
    # Resumed after the method is dropped, it still shows what it showed.
    ctx.vault.practice_items[ITEM] = ctx.vault.practice_items[ITEM].model_copy(update={"required_method": None})
    again = _call(ctx, "workbench.get", {"sessionId": session["sessionId"]})["session"]
    assert [block["kind"] for block in again["presentation"]["blocks"]] == ["prompt", "required_method_instruction"]
    # Before binding the verbatim selection is the display: no presentation yet.
    selected = _selection_open(ctx)
    assert selected["presentation"] is None and selected["stemMd"] == STEM


def test_f2_hints_shown_on_the_answer_box_are_carried_into_steps_and_counted(tmp_path, grader):
    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    practice_session = _call(ctx, "start_session", {})["sessionId"]
    opened = _call(ctx, "workbench.open", {"origin": "practice", "entry": "practice_screen", "practiceItemId": ITEM,
                                           "stemMd": "Write the SVD of A.", "carriedHints": 1})["session"]
    assert opened["carriedHints"] == 1
    record = opened["record"]
    assert record["hints"] == 1 and record["ownAttempt"] is False and record["bookCounted"] is False
    assert "1 shown on the answer box" in record["line"] and "help used: 1 hint" in record["footer"]
    _step(ctx, opened["sessionId"], "a", bodyMd="A = U Sigma V^T")
    # Back to the answer box and into steps again: the count is never taken back.
    again = _call(ctx, "workbench.open", {"origin": "practice", "entry": "practice_screen", "practiceItemId": ITEM,
                                          "stemMd": "Write the SVD of A.", "carriedHints": 0})
    assert again["resumed"] is True and again["session"]["carriedHints"] == 1
    more = _call(ctx, "workbench.open", {"origin": "practice", "entry": "practice_screen",
                                         "sessionId": opened["sessionId"], "carriedHints": 2})["session"]
    assert more["carriedHints"] == 2 and more["record"]["hints"] == 2
    payload = _submit(ctx, opened["sessionId"], practiceSessionId=practice_session)
    row = _attempt(repository, payload["attempt"]["attemptId"])
    assert row["hints_used"] == 2 and row["attempt_type"] == "hinted_attempt"
    policy = _policy(row)
    assert policy.counts_as_assisted and not policy.eligible_for_certification


def test_f4_a_practice_problem_resumed_in_the_reader_moves_there_book_hidden_and_counts_the_book_if_shown(
    tmp_path, grader
):
    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    practice = _call(ctx, "workbench.open", {"origin": "practice", "entry": "practice_screen", "practiceItemId": ITEM,
                                             "stemMd": "Write the SVD of A."})["session"]
    _step(ctx, practice["sessionId"], "a", bodyMd="A = U Sigma V^T")
    moved = _call(ctx, "workbench.open", {"origin": "reader", "entry": "work_through", "practiceItemId": ITEM,
                                          "stemMd": STEM, "extractionId": EXTRACTION, "spanIds": ["s5"]})
    session = moved["session"]
    assert moved["resumed"] is True and session["sessionId"] == practice["sessionId"]
    # In the Reader now, anchored to the passage, the book hidden: the step
    # was written without it, so it stays the learner's own until shown.
    assert session["origin"] == "reader" and session["extractionId"] == EXTRACTION and session["spanIds"] == ["s5"]
    assert session["sourceVisible"] is False and session["record"]["ownAttempt"] is True
    shown = _call(ctx, "workbench.set_book", {"sessionId": session["sessionId"], "visible": True})["session"]
    assert shown["record"]["bookCounted"] is True
    row = _attempt(repository, _submit(ctx, session["sessionId"])["attempt"]["attemptId"])
    assert row["entry_surface"] == "desktop_reader_workbench" and row["hints_used"] == 1
    events = [e["payload"] for e in repository.reader_interaction_events(kind="reader_action_invoked")
              if e["payload"].get("workbench_session_id") == session["sessionId"]
              and e["payload"].get("event") == "workbench_resumed"]
    assert events and events[0]["moved_from"] == "practice"


def test_f4_a_reader_problem_resumed_on_the_practice_screen_keeps_the_book_it_counted(tmp_path, grader):
    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    counted = _open(ctx)
    _step(ctx, counted["sessionId"], "a", bodyMd="A = U Sigma V^T")
    practice_session = _call(ctx, "start_session", {})["sessionId"]
    moved = _call(ctx, "workbench.open", {"origin": "practice", "entry": "practice_screen",
                                          "sessionId": counted["sessionId"]})["session"]
    assert moved["origin"] == "practice" and moved["sourceVisible"] is False
    assert moved["record"]["bookCounted"] is True and moved["record"]["hints"] == 1
    row = _attempt(repository, _submit(ctx, counted["sessionId"], practiceSessionId=practice_session)["attempt"]["attemptId"])
    assert row["entry_surface"] == "desktop_practice_workbench" and row["hints_used"] == 1
    # A Reader problem with the book open and no step yet: moving it is free.
    free = _open(ctx, practiceItemId=OTHER_ITEM)
    assert free["sourceVisible"] is True
    off = _call(ctx, "workbench.open", {"origin": "practice", "entry": "practice_screen", "practiceItemId": OTHER_ITEM,
                                        "stemMd": "Transpose the matrix M."})["session"]
    assert off["sessionId"] == free["sessionId"] and off["record"]["ownAttempt"] is True


def test_f4_resuming_an_abandoned_problem_by_its_id_reopens_it_on_the_asking_surface(tmp_path):
    paths, _repository = _vault(tmp_path)
    ctx = _context(paths.root)
    session = _open(ctx, entry="check_me")
    _step(ctx, session["sessionId"], "a", bodyMd="one")
    _call(ctx, "workbench.abandon", {"sessionId": session["sessionId"]})
    back = _call(ctx, "workbench.open", {"origin": "practice", "entry": "practice_screen",
                                         "sessionId": session["sessionId"]})
    assert back["resumed"] is True and back["session"]["status"] == "open"
    assert back["session"]["origin"] == "practice" and _bodies(back["session"]) == ["one"]


def _exposures(repository: Repository) -> list[dict]:
    with connect(repository.sqlite_path, read_only=True) as connection:
        rows = connection.execute("SELECT * FROM source_exposure_events ORDER BY created_at, id").fetchall()
    return [dict(row) for row in rows]


def test_f11_showing_the_book_records_an_exposure_of_the_anchored_spans(tmp_path):
    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    before = len(_exposures(repository))
    hidden = _open(ctx, entry="check_me", spanIds=["s5", "s6"])
    assert len(_exposures(repository)) == before
    _step(ctx, hidden["sessionId"], "a", bodyMd="A = U Sigma V^T")
    _call(ctx, "workbench.set_book", {"sessionId": hidden["sessionId"], "visible": True})
    rows = _exposures(repository)[before:]
    assert [(row["context"], row["extraction_id"], row["span_id"]) for row in rows] == [
        ("reader", EXTRACTION, "s5"), ("reader", EXTRACTION, "s6"),
    ]
    assert {(row["entity_type"], row["entity_id"]) for row in rows} == {("practice_item", ITEM)}
    # Opening with the book shown is a showing too.
    _open(ctx, practiceItemId=OTHER_ITEM, spanIds=["s9"])
    assert [row["span_id"] for row in _exposures(repository)[before + 2:]] == ["s9"]
    # Hiding records nothing; off the Reader there is no book to show.
    _call(ctx, "workbench.set_book", {"sessionId": hidden["sessionId"], "visible": False})
    assert len(_exposures(repository)) == before + 3


# -- Codex re-review (F2, F13, F14) --------------------------------------------------------------


def test_f2_a_book_counted_in_steps_goes_to_the_answer_box_and_back_into_steps_counted(tmp_path, grader):
    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    counted = _open(ctx)
    _step(ctx, counted["sessionId"], "a", bodyMd="A = U Sigma V^T")
    _call(ctx, "workbench.abandon", {"sessionId": counted["sessionId"]})
    # The item's card says the book counted, so the answer box counts it.
    [summary] = _call(ctx, "workbench.for_item", {"practiceItemId": ITEM})["sessions"]
    assert summary["bookCounted"] is True
    # Into steps again on the practice screen: a new problem, the book counted.
    practice_session = _call(ctx, "start_session", {})["sessionId"]
    fresh = _call(ctx, "workbench.open", {"origin": "practice", "entry": "practice_screen", "practiceItemId": ITEM,
                                          "stemMd": "Write the SVD of A.", "carriedBook": True})
    assert fresh["resumed"] is False and fresh["session"]["sessionId"] != counted["sessionId"]
    assert fresh["session"]["record"]["bookCounted"] is True and fresh["session"]["record"]["hints"] == 1
    # Carried into the session that counted it already, it is not counted twice.
    again = _call(ctx, "workbench.open", {"origin": "practice", "entry": "practice_screen",
                                          "sessionId": counted["sessionId"], "carriedBook": True})["session"]
    assert again["record"]["hints"] == 1
    _step(ctx, fresh["session"]["sessionId"], "a", bodyMd="A = U Sigma V^T")
    payload = _submit(ctx, fresh["session"]["sessionId"], practiceSessionId=practice_session)
    row = _attempt(repository, payload["attempt"]["attemptId"])
    assert row["hints_used"] == 1 and _policy(row).counts_as_assisted


def _offer(ctx, practice_session: str, item_id: str) -> str:
    queue = _call(ctx, "get_today_queue", {"sessionId": practice_session})
    return next(entry["schedulerCandidateId"] for section in queue["sections"] for entry in section["items"]
                if entry["practiceItemId"] == item_id)


def test_f13_a_resumed_check_still_submits_as_the_serve_it_was_opened_from(tmp_path, grader):
    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    practice_session = _call(ctx, "start_session", {})["sessionId"]
    candidate = _offer(ctx, practice_session, ITEM)
    check = _open(ctx, entry="check_me", schedulerCandidateId=candidate)
    _step(ctx, check["sessionId"], "a", bodyMd="A = U Sigma V^T")
    _call(ctx, "workbench.leave", {"sessionId": check["sessionId"]})
    # Resumed from the rail, which knows nothing of the serve.
    resumed = _call(ctx, "workbench.open", {"origin": "reader", "entry": "resume", "sessionId": check["sessionId"],
                                            "extractionId": EXTRACTION})["session"]
    assert resumed["schedulerCandidateId"] == candidate
    payload = _submit(ctx, check["sessionId"], practiceSessionId=practice_session)
    assert _attempt(repository, payload["attempt"]["attemptId"])["scheduler_candidate_id"] == candidate


def test_f13_a_kept_offer_that_went_stale_never_fails_the_submit(tmp_path, grader):
    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    first = _call(ctx, "start_session", {})["sessionId"]
    candidate = _offer(ctx, first, ITEM)
    check = _open(ctx, entry="check_me", schedulerCandidateId=candidate)
    _step(ctx, check["sessionId"], "a", bodyMd="A = U Sigma V^T")
    # Submitted in another practice session (after a restart, say): the
    # kept offer belongs to the first one, so it is dropped, not refused.
    _call(ctx, "end_session", {"sessionId": first})
    payload = _submit(ctx, check["sessionId"])
    assert payload["practiceSession"]["sessionId"] != first
    assert _attempt(repository, payload["attempt"]["attemptId"])["scheduler_candidate_id"] is None


def test_f14_check_me_on_a_problem_left_with_the_book_open_opens_it_hidden_keeping_what_it_counted(tmp_path):
    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    worked = _open(ctx)
    _step(ctx, worked["sessionId"], "a", bodyMd="A = U Sigma V^T")
    _call(ctx, "workbench.leave", {"sessionId": worked["sessionId"]})
    check = _call(ctx, "workbench.open", {"origin": "reader", "entry": "check_me", "practiceItemId": ITEM,
                                          "stemMd": STEM, "extractionId": EXTRACTION, "spanIds": ["s5"]})
    assert check["resumed"] is True and check["session"]["sessionId"] == worked["sessionId"]
    assert check["session"]["sourceVisible"] is False and check["session"]["sourceHiddenAt"]
    # The book already counted stays counted.
    assert check["session"]["record"]["bookCounted"] is True
    # A problem with the book open and no step yet: the check is the learner's own.
    untouched = _open(ctx, practiceItemId=OTHER_ITEM)
    assert untouched["sourceVisible"] is True
    exposures = _count(repository, "source_exposure_events")
    own = _call(ctx, "workbench.open", {"origin": "reader", "entry": "check_me", "practiceItemId": OTHER_ITEM,
                                        "stemMd": "Transpose the matrix M.", "extractionId": EXTRACTION,
                                        "spanIds": ["s5"]})["session"]
    assert own["sessionId"] == untouched["sessionId"] and own["sourceVisible"] is False
    assert own["record"]["ownAttempt"] is True
    assert _count(repository, "source_exposure_events") == exposures


# -- Codex final verification (F2, F15) ------------------------------------------------------------


def _answer_box(ctx, practice_session: str, **params):
    """The practice screen's own answer box: the ordinary ``submit_attempt``."""

    payload = {"sessionId": practice_session, "practiceItemId": ITEM, "answerMd": "A = U Sigma V^T",
               "attemptType": "independent_attempt", "hintsUsed": 0, **params}
    return _call(ctx, "submit_attempt", payload)


def test_final_f2_an_answer_box_submit_counts_the_book_its_open_problem_counted_whatever_the_client_sent(
    tmp_path, grader,
):
    # Reproduction 1: steps left in the Reader with the book counted; the
    # answer box submits before its lookup of the item's problems returns, so
    # the client sends no hint and an independent attempt.
    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    worked = _open(ctx)
    _step(ctx, worked["sessionId"], "a", bodyMd="A = U Sigma V^T")
    _call(ctx, "workbench.leave", {"sessionId": worked["sessionId"]})
    practice_session = _call(ctx, "start_session", {})["sessionId"]
    row = _attempt(repository, _answer_box(ctx, practice_session)["attemptId"])
    assert row["hints_used"] == 1 and row["attempt_type"] == "hinted_attempt"
    assert _policy(row).counts_as_assisted and not _policy(row).eligible_for_certification
    # A client that already counts the book sends it once: the larger of the
    # two, never their sum.
    row = _attempt(repository, _answer_box(ctx, practice_session, hintsUsed=1, attemptType="hinted_attempt")["attemptId"])
    assert row["hints_used"] == 1
    # An empty "I'm stuck" answer counts it too.
    row = _attempt(repository, _call(ctx, "submit_dont_know", {
        "sessionId": practice_session, "practiceItemId": ITEM, "hintsUsed": 0,
    })["attemptId"])
    assert row["hints_used"] == 1 and row["attempt_type"] == "hinted_attempt"


def test_final_f2_carried_hints_still_count_after_the_items_authored_hints_were_removed(tmp_path, grader):
    # Reproduction 2: a problem carrying two answer-box hints, resumed after
    # the item's authored hints were removed, then answered on the answer box.
    from learnloop.vault.yaml_io import read_yaml, write_yaml

    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    opened = _call(ctx, "workbench.open", {"origin": "practice", "entry": "practice_screen", "practiceItemId": ITEM,
                                           "stemMd": "Write the SVD of A.", "carriedHints": 2})["session"]
    assert opened["record"]["hints"] == 2
    item_path = paths.practice_item_path("linear-algebra", ITEM)
    item = read_yaml(item_path)
    item["hints"] = []
    write_yaml(item_path, item)
    ctx = _context(paths.root)
    assert ctx.require_vault()[0].practice_items[ITEM].hints == []
    practice_session = _call(ctx, "start_session", {})["sessionId"]
    row = _attempt(repository, _answer_box(ctx, practice_session)["attemptId"])
    assert row["hints_used"] == 2 and row["attempt_type"] == "hinted_attempt"


def _capture_submits(monkeypatch) -> list:
    import learnloop_sidecar.handlers.practice as practice

    seen: list = []
    original = practice.submit_attempt_on

    def spy(ctx, params, **kwargs):
        seen.append(params)
        return original(ctx, params, **kwargs)

    monkeypatch.setattr(practice, "submit_attempt_on", spy)
    return seen


def test_final_f15_a_replacement_serve_replaces_both_identifiers_and_a_resume_naming_none_keeps_both(
    tmp_path, grader, monkeypatch,
):
    seen = _capture_submits(monkeypatch)
    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    practice_session = _call(ctx, "start_session", {})["sessionId"]
    candidate_b = _offer(ctx, practice_session, ITEM)
    check = _open(ctx, entry="check_me", schedulerCandidateId="cand_A", planPresentationId="pres_P")
    assert (check["schedulerCandidateId"], check["planPresentationId"]) == ("cand_A", "pres_P")
    _step(ctx, check["sessionId"], "a", bodyMd="A = U Sigma V^T")
    # An ordinary serve of the item names candidate B and no plan presentation:
    # both identifiers are replaced, the explicit null included.
    replaced = _call(ctx, "workbench.open", {"origin": "practice", "entry": "practice_screen",
                                             "sessionId": check["sessionId"], "schedulerCandidateId": candidate_b,
                                             "planPresentationId": None})["session"]
    assert (replaced["schedulerCandidateId"], replaced["planPresentationId"]) == (candidate_b, None)
    # A resume that names no serve (the rail, the ✎ mark) keeps both.
    kept = _call(ctx, "workbench.open", {"origin": "reader", "entry": "resume", "sessionId": check["sessionId"],
                                         "extractionId": EXTRACTION})["session"]
    assert (kept["schedulerCandidateId"], kept["planPresentationId"]) == (candidate_b, None)
    payload = _submit(ctx, check["sessionId"], practiceSessionId=practice_session)
    [sent] = seen
    assert (sent.scheduler_candidate_id, sent.plan_presentation_id) == (candidate_b, None)
    assert _attempt(repository, payload["attempt"]["attemptId"])["scheduler_candidate_id"] == candidate_b


def test_final_f15_a_submit_naming_a_serve_never_mixes_it_with_the_kept_one(tmp_path, grader, monkeypatch):
    seen = _capture_submits(monkeypatch)
    paths, _repository = _vault(tmp_path)
    ctx = _context(paths.root)
    practice_session = _call(ctx, "start_session", {})["sessionId"]
    candidate_b = _offer(ctx, practice_session, ITEM)
    check = _open(ctx, entry="check_me", schedulerCandidateId="cand_A", planPresentationId="pres_P")
    _step(ctx, check["sessionId"], "a", bodyMd="A = U Sigma V^T")
    _submit(ctx, check["sessionId"], practiceSessionId=practice_session, schedulerCandidateId=candidate_b,
            planPresentationId=None)
    [sent] = seen
    assert (sent.scheduler_candidate_id, sent.plan_presentation_id) == (candidate_b, None)


# -- Codex round 4 (F2): an independent-only item ---------------------------------------------------
#
# Binding ruling: assisted work is never credited as unassisted evidence or
# certification. Main's answer box, on an item whose only allowed type is
# ``independent_attempt``, records a revealed authored hint as that type with
# ``hints_used`` > 0 (``chooseAttemptType`` falls back to the item's default
# type; ``stuck_attempt_type`` does the same for "I'm stuck"). The one activity
# policy reads ``hints_used`` > 0 as assisted and never certifying, whatever
# the type, so held workbench assistance is recorded exactly that way.


def _independent_only(paths) -> None:
    from learnloop.vault.yaml_io import read_yaml, write_yaml

    item_path = paths.practice_item_path("linear-algebra", ITEM)
    item = read_yaml(item_path)
    item["attempt_types_allowed"] = ["independent_attempt"]
    assert item.get("hints"), "the item needs an authored hint to reveal"
    write_yaml(item_path, item)


def _recorded_policy(repository: Repository, row: dict):
    return resolve_attempt_activity_policy(
        attempt_type=row["attempt_type"], primed=bool(row["primed"]), hints_used=int(row["hints_used"]),
        recorded=repository.all_causal_activity_classifications().get(str(row["id"])),
        reference_status=row.get("reference_status"),
    )


def _timeline_points(paths, repository: Repository, attempt_ids: set[str]) -> list:
    from learnloop.learner.facet_evidence_timeline import facet_evidence_timelines

    from learnloop.attempts.grading import resolved_rubric

    vault = load_vault(paths.root)
    rubric = resolved_rubric(vault, vault.practice_items[ITEM])
    facets = sorted({target.facet for criterion in rubric.criteria for target in criterion.targets})
    timelines = facet_evidence_timelines(vault, repository, facets)
    return [point for points in timelines.values() for point in points if point.attempt_id in attempt_ids]


def _assert_assisted_and_never_certifying(paths, repository: Repository, attempt_ids: list[str], hints: int) -> None:
    for attempt_id in attempt_ids:
        row = _attempt(repository, attempt_id)
        # Recorded exactly as main records an authored hint on this item.
        assert (row["attempt_type"], row["hints_used"]) == ("independent_attempt", hints), attempt_id
        policy = _recorded_policy(repository, row)
        assert policy.counts_as_assisted and not policy.eligible_for_certification, attempt_id
    # The certification ledger (the Demonstrated fold the canonical projection
    # shares) reads every point of these attempts as assisted, banking nothing.
    points = _timeline_points(paths, repository, set(attempt_ids))
    assert points, "the attempts are graded evidence on some facet"
    assert all(point.assisted for point in points)
    assert all(point.delta == 0.0 for point in points)


def test_round4_f2_main_records_an_authored_hint_on_an_independent_only_item_as_assisted_and_never_certifying(
    tmp_path, grader,
):
    # What main does, with no workbench involved: the answer box, after
    # revealing one authored hint, sends the item's only type with the hint
    # counted; so does "I'm stuck" (empty) and a "don't know" client.
    paths, repository = _vault(tmp_path)
    _independent_only(paths)
    ctx = _context(paths.root)
    practice_session = _call(ctx, "start_session", {})["sessionId"]
    answered = _answer_box(ctx, practice_session, hintsUsed=1)["attemptId"]
    stuck = _answer_box(ctx, practice_session, answerMd="", declaredStuck=True, hintsUsed=1)["attemptId"]
    dont_know = _call(ctx, "submit_dont_know", {"sessionId": practice_session, "practiceItemId": ITEM,
                                                "hintsUsed": 1})["attemptId"]
    _assert_assisted_and_never_certifying(paths, repository, [answered, stuck, dont_know], hints=1)
    # Control: the same answer with no hint is unassisted and certifies.
    own = _attempt(repository, _answer_box(ctx, practice_session)["attemptId"])
    assert own["hints_used"] == 0 and own["attempt_type"] == "independent_attempt"
    assert _recorded_policy(repository, own).eligible_for_certification
    banked = _timeline_points(paths, repository, {own["id"]})
    assert banked and not any(point.assisted for point in banked) and any(point.delta > 0 for point in banked)


def test_round4_f2_held_assistance_on_an_independent_only_item_is_assisted_on_every_submit_path_and_after_replay(
    tmp_path, grader, monkeypatch,
):
    # Codex's reproduction: the book counted in a Reader workbench, left, then
    # every submit path on an independent-only item, the client sending no hint.
    import learnloop_sidecar.handlers.ai_providers as ai_providers

    monkeypatch.setattr(
        ai_providers, "ready_grading_provider", lambda vault, override=None: ("fake", ReadyRuntime(), grader)
    )
    paths, repository = _vault(tmp_path)
    _independent_only(paths)
    ctx = _context(paths.root)
    worked = _open(ctx)
    _step(ctx, worked["sessionId"], "a", bodyMd="A = U Sigma V^T")
    _call(ctx, "workbench.leave", {"sessionId": worked["sessionId"]})
    practice_session = _call(ctx, "start_session", {})["sessionId"]
    answered = _answer_box(ctx, practice_session)["attemptId"]
    stuck = _answer_box(ctx, practice_session, answerMd="", declaredStuck=True)["attemptId"]
    dont_know = _call(ctx, "submit_dont_know", {"sessionId": practice_session, "practiceItemId": ITEM,
                                                "hintsUsed": 0})["attemptId"]
    _call(ctx, "workbench.open", {"origin": "reader", "entry": "resume", "sessionId": worked["sessionId"],
                                  "extractionId": EXTRACTION})
    workbench = _submit(ctx, worked["sessionId"], practiceSessionId=practice_session)["attempt"]["attemptId"]
    attempt_ids = [answered, stuck, dont_know, workbench]
    _assert_assisted_and_never_certifying(paths, repository, attempt_ids, hints=1)
    # A regrade supersedes the grade and replays, never the assistance.
    graded = {attempt_id: _count(repository, "grading_evidence", "attempt_id = ?", (attempt_id,))
              for attempt_id in (answered, workbench)}
    _call(ctx, "trigger_regrade", {"attemptId": answered})
    _call(ctx, "trigger_regrade", {"attemptId": workbench})
    assert all(_count(repository, "grading_evidence", "attempt_id = ?", (attempt_id,)) > count
               for attempt_id, count in graded.items())
    _assert_assisted_and_never_certifying(paths, repository, attempt_ids, hints=1)
    # A full replay reads the attempt rows, so the classification is the same.
    rebuild_all_derived_state(load_vault(paths.root), repository,
                              clock=FrozenClock(datetime(2026, 10, 30, 12, 0, tzinfo=UTC)))
    _assert_assisted_and_never_certifying(paths, repository, attempt_ids, hints=1)
