"""Mobile PR-2: content sync never restores stale scheduling state.

``sync_vault_state`` (and the desktop's incremental watcher refresh) reads the
item states, then writes back the items whose content hash or active flag
changed. Before PR-2 that write carried the snapshot's difficulty, stability,
retrievability, due date and last-attempt time, so an attempt committed by
another process (the phone host, the desktop sidecar, the TUI) between the read
and the write was erased. Each test here commits a real attempt inside that
window, through a second connection or a second process, and checks that the
attempt's scheduling fields survive while the content columns still reconcile.

The module runs in the durability lane: production pragmas and WAL on a freshly
initialized vault, the configuration two processes share in practice.
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from learnloop.attempts.attempts import (
    AttemptDraft,
    SelfGradeInput,
    complete_self_graded_attempt,
)
from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.db.repositories import PracticeItemState, Repository
from learnloop.substrate.state_sync import reconcile_practice_item_state, sync_vault_state
from learnloop.vault.hashes import practice_item_hash
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item
from learnloop_sidecar.context import SidecarContext

from tests.helpers import NOW, create_basic_vault

pytestmark = pytest.mark.durability

ITEM = "pi_svd_define_001"
SUBJECT = "linear-algebra"
SYNC_CLOCK = FrozenClock(NOW)
ATTEMPT_CLOCK = FrozenClock(NOW + timedelta(hours=1))
SCHEDULING_FIELDS = ("difficulty", "stability", "retrievability", "due_at", "last_attempt_at")


def _scheduling(state: PracticeItemState) -> dict[str, object]:
    return {field: getattr(state, field) for field in SCHEDULING_FIELDS}


def _commit_attempt(vault_root: Path, sqlite_path: Path) -> None:
    """Commit one self-graded attempt through its own Repository (own connection)."""

    other_process = Repository(sqlite_path)
    complete_self_graded_attempt(
        load_vault(vault_root),
        other_process,
        AttemptDraft(
            practice_item_id=ITEM,
            learner_answer_md="SVD factors a matrix into U, Sigma and V transpose.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=4),
        clock=ATTEMPT_CLOCK,
    )


def _edit_prompt(vault_root: Path, prompt: str) -> None:
    vault = load_vault(vault_root)
    payload = vault.practice_items[ITEM].model_dump(mode="json", exclude_none=False)
    payload["prompt"] = prompt
    upsert_practice_item(vault_root, payload, loaded_vault=vault, clock=SYNC_CLOCK)


def _attempt_after_snapshot(monkeypatch, repository: Repository, commit) -> dict:
    """Run ``commit`` right after the sync's snapshot read; record what it wrote."""

    original = Repository.practice_item_states
    seen: dict = {}

    def snapshot_then_commit(self):
        snapshot = original(self)
        if self is repository and "after_attempt" not in seen:
            commit()
            seen["after_attempt"] = Repository(repository.sqlite_path).practice_item_state(ITEM)
        return snapshot

    monkeypatch.setattr(Repository, "practice_item_states", snapshot_then_commit)
    return seen


def _fresh_vault(tmp_path: Path):
    paths = create_basic_vault(tmp_path / "vault", fresh=True)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(load_vault(paths.root), repository, clock=SYNC_CLOCK)
    return paths, repository


def test_content_change_sync_keeps_an_attempt_committed_after_its_snapshot(tmp_path, monkeypatch):
    paths, repository = _fresh_vault(tmp_path)
    before = repository.practice_item_state(ITEM)
    assert before.last_attempt_at is None

    _edit_prompt(paths.root, "Define the singular value decomposition of a real matrix.")
    edited = load_vault(paths.root)
    original_hash = before.content_hash

    def commit_with_old_hash():
        # The attempt lands with the pre-edit hash, as one graded on the phone
        # before the desktop's edit reached it would; the sync must still
        # write the edited hash, and only the hash and the flag.
        _commit_attempt(paths.root, paths.sqlite_path)
        with connect(paths.sqlite_path) as connection:
            connection.execute(
                "UPDATE practice_item_state SET content_hash = ? WHERE practice_item_id = ?",
                (original_hash, ITEM),
            )
            connection.commit()

    seen = _attempt_after_snapshot(monkeypatch, repository, commit_with_old_hash)

    result = sync_vault_state(edited, repository, clock=SYNC_CLOCK)

    after_attempt = seen["after_attempt"]
    assert after_attempt.last_attempt_at is not None
    assert after_attempt.stability is not None
    state = repository.practice_item_state(ITEM)
    assert _scheduling(state) == _scheduling(after_attempt)
    assert state.content_hash == practice_item_hash(edited.practice_items[ITEM])
    assert state.content_hash != original_hash
    assert state.active is True
    assert result.practice_item_states_updated == 1


def test_creating_sync_keeps_a_row_an_attempt_inserted_after_its_snapshot(tmp_path, monkeypatch):
    paths, repository = _fresh_vault(tmp_path)
    with connect(paths.sqlite_path) as connection:
        connection.execute("DELETE FROM practice_item_state WHERE practice_item_id = ?", (ITEM,))
        connection.commit()
    assert repository.practice_item_state(ITEM) is None

    seen = _attempt_after_snapshot(
        monkeypatch, repository, lambda: _commit_attempt(paths.root, paths.sqlite_path)
    )
    vault = load_vault(paths.root)
    result = sync_vault_state(vault, repository, clock=SYNC_CLOCK)

    after_attempt = seen["after_attempt"]
    assert after_attempt.last_attempt_at is not None
    state = repository.practice_item_state(ITEM)
    assert _scheduling(state) == _scheduling(after_attempt)
    assert state.active is True
    assert state.content_hash == practice_item_hash(vault.practice_items[ITEM])
    # The snapshot had no row, but the attempt created one first: nothing was
    # inserted by the sync, and nothing needed updating.
    assert result.practice_item_states_created == 0
    assert result.practice_item_states_updated == 0


def test_deactivating_sync_keeps_an_attempt_committed_after_its_snapshot(tmp_path, monkeypatch):
    paths, repository = _fresh_vault(tmp_path)
    vault_with_item = load_vault(paths.root)
    item_path = paths.practice_item_path(SUBJECT, ITEM)
    item_yaml = item_path.read_bytes()
    item_path.unlink()
    vault_without_item = load_vault(paths.root)
    item_path.write_bytes(item_yaml)

    def commit_on_old_vault():
        complete_self_graded_attempt(
            vault_with_item,
            Repository(paths.sqlite_path),
            AttemptDraft(
                practice_item_id=ITEM,
                learner_answer_md="SVD factors a matrix into U, Sigma and V transpose.",
                attempt_type="independent_attempt",
            ),
            SelfGradeInput(criterion_points={"correctness": 4}, confidence=4),
            clock=ATTEMPT_CLOCK,
        )

    seen = _attempt_after_snapshot(monkeypatch, repository, commit_on_old_vault)
    result = sync_vault_state(vault_without_item, repository, clock=SYNC_CLOCK)

    after_attempt = seen["after_attempt"]
    assert after_attempt.last_attempt_at is not None
    state = repository.practice_item_state(ITEM)
    assert state.active is False
    assert _scheduling(state) == _scheduling(after_attempt)
    assert result.practice_item_states_deactivated == 1


def test_a_stale_snapshot_never_reactivates_a_probe_an_attempt_retired(tmp_path):
    """The active decision is taken again from the row the attempt left.

    A diagnostic probe is single-use: its attempt writes ``active = 0``. A sync
    that decided from a pre-attempt snapshot would reactivate it; the write
    decides again from the row under its write lock instead.
    """

    paths, repository = _fresh_vault(tmp_path)
    snapshot = repository.practice_item_state(ITEM)
    repository.upsert_practice_item_state(
        ITEM,
        difficulty=4.2,
        stability=3.1,
        retrievability=0.9,
        due_at="2026-05-22T12:00:00Z",
        active=False,
        content_hash=snapshot.content_hash,
        last_attempt_at="2026-05-19T13:00:00Z",
        clock=ATTEMPT_CLOCK,
    )
    retired = repository.practice_item_state(ITEM)
    probe = SimpleNamespace(status="active", practice_mode="diagnostic_probe")

    outcome, active = reconcile_practice_item_state(
        repository,
        ITEM,
        probe,
        state=snapshot,
        review_parked=set(),
        measurement_superseded=set(),
        content_hash="edited-hash",
        clock=SYNC_CLOCK,
    )

    state = repository.practice_item_state(ITEM)
    assert (outcome, active) == ("updated", False)
    assert state.active is False
    assert state.content_hash == "edited-hash"
    assert _scheduling(state) == _scheduling(retired)


def test_incremental_watch_refresh_keeps_an_attempt_committed_after_its_read(tmp_path, monkeypatch):
    paths = create_basic_vault(tmp_path / "vault", fresh=True)
    context = SidecarContext()
    context.load(paths.root, maintenance=False)
    vault, repository = context.require_vault()
    original_hash = repository.practice_item_state(ITEM).content_hash
    payload = vault.practice_items[ITEM].model_dump(mode="json", exclude_none=False)
    payload["prompt"] = "Define the singular value decomposition."
    upsert_practice_item(paths.root, payload, loaded_vault=vault)

    original = Repository.practice_item_state
    seen: dict = {}

    def read_then_commit(self, practice_item_id):
        state = original(self, practice_item_id)
        if self is repository and practice_item_id == ITEM and "after_attempt" not in seen:
            seen["after_attempt"] = None
            _commit_attempt(paths.root, paths.sqlite_path)
            with connect(paths.sqlite_path) as connection:
                connection.execute(
                    "UPDATE practice_item_state SET content_hash = ? WHERE practice_item_id = ?",
                    (original_hash, ITEM),
                )
                connection.commit()
            seen["after_attempt"] = original(Repository(paths.sqlite_path), ITEM)
        return state

    monkeypatch.setattr(Repository, "practice_item_state", read_then_commit)
    item_path = paths.practice_item_path(SUBJECT, ITEM)
    result = context.refresh_vault_files(
        [item_path.relative_to(paths.root).as_posix()], expected_root=paths.root
    )
    monkeypatch.undo()

    after_attempt = seen["after_attempt"]
    assert result["mode"] == "incremental"
    assert after_attempt.last_attempt_at is not None
    state = repository.practice_item_state(ITEM)
    assert _scheduling(state) == _scheduling(after_attempt)
    assert state.content_hash == practice_item_hash(context.require_vault()[0].practice_items[ITEM])
    assert state.content_hash != original_hash


_ATTEMPT_IN_ANOTHER_PROCESS = """
import sys
from datetime import datetime
from pathlib import Path
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

root, sqlite_path, item_id, when = sys.argv[1:5]
complete_self_graded_attempt(
    load_vault(Path(root)),
    Repository(Path(sqlite_path)),
    AttemptDraft(
        practice_item_id=item_id,
        learner_answer_md="SVD factors a matrix into U, Sigma and V transpose.",
        attempt_type="independent_attempt",
    ),
    SelfGradeInput(criterion_points={"correctness": 4}, confidence=4),
    clock=FrozenClock(datetime.fromisoformat(when)),
)
"""


def test_an_attempt_from_a_second_process_survives_a_concurrent_content_sync(tmp_path, monkeypatch):
    """G6b's PR-2 clause with a real second process on the WAL database."""

    paths, repository = _fresh_vault(tmp_path)
    original_hash = repository.practice_item_state(ITEM).content_hash
    _edit_prompt(paths.root, "Define the singular value decomposition of a real matrix.")
    edited = load_vault(paths.root)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": str(tmp_path / "home"),
        "LEARNLOOP_CONFIG_DIR": str(config_dir),
        "PYTHONPATH": os.pathsep.join(sys.path),
    }
    (tmp_path / "home").mkdir()

    def commit_in_another_process():
        subprocess.run(
            [
                sys.executable,
                "-c",
                _ATTEMPT_IN_ANOTHER_PROCESS,
                str(paths.root),
                str(paths.sqlite_path),
                ITEM,
                ATTEMPT_CLOCK.now().isoformat(),
            ],
            check=True,
            env=env,
            timeout=120,
        )

    seen = _attempt_after_snapshot(monkeypatch, repository, commit_in_another_process)
    sync_vault_state(edited, repository, clock=SYNC_CLOCK)

    after_attempt = seen["after_attempt"]
    assert after_attempt.last_attempt_at is not None
    assert after_attempt.stability is not None
    state = repository.practice_item_state(ITEM)
    assert _scheduling(state) == _scheduling(after_attempt)
    assert state.content_hash == practice_item_hash(edited.practice_items[ITEM])
    assert state.content_hash != original_hash
    assert state.active is True


# --- Codex review F1/F2: the active decision is taken under the write lock ----
#
# A sync that must write decides ``active`` from the row and the lifecycle
# tables (review parking, measurement corrections) as they stand inside the
# same ``BEGIN IMMEDIATE`` transaction as its write. Each test below commits a
# real lifecycle change right after one of the reads the decision depends on.
# Before the fix the change landed between that read and the write and the
# sync reactivated the item. With the fix, the read that feeds the decision is
# taken under the write lock, so the change cannot land there: the hook checks
# that the lock is held (a second connection's ``BEGIN IMMEDIATE`` is refused
# at once) and commits the change after the sync instead.

PROBE = "pi_diag_transposed_factor"
PROBE_LO = "lo_svd_definition"


def _write_lock_held(sqlite_path: Path) -> bool:
    with connect(sqlite_path) as probe:
        probe.execute("PRAGMA busy_timeout = 0")
        try:
            probe.execute("BEGIN IMMEDIATE")
        except sqlite3.OperationalError as error:
            if "locked" not in str(error) and "busy" not in str(error):
                raise
            return True
        probe.rollback()
    return False


def _add_diagnostic_probe(paths, prompt: str = "Which SVD factor is transposed in the product?") -> None:
    from learnloop.vault.yaml_io import write_yaml

    from tests.helpers import NOW_ISO

    write_yaml(
        paths.practice_item_path(SUBJECT, PROBE),
        {
            "schema_version": 1,
            "id": PROBE,
            "learning_object_id": PROBE_LO,
            "subjects": None,
            "practice_mode": "diagnostic_probe",
            "attempt_types_allowed": ["diagnostic_probe", "dont_know"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": prompt,
            "expected_answer": "V",
            "difficulty": 0.5,
            "tags": [],
            "hints": [],
            "hint_policy": {
                "max_useful_hints": 0,
                "fsrs_rating_cap_by_hint": {},
                "mastery_alpha_dampening_by_hint": {},
            },
            "grading_rubric": {
                "max_points": 4,
                "criteria": [
                    {"id": "correctness", "points": 4, "description": "Correct selection."}
                ],
                "fatal_errors": [],
            },
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )


def _commit_probe_attempt(vault, sqlite_path: Path) -> None:
    """A real diagnostic administration through its own Repository: it retires the probe."""

    from learnloop.attempts.attempts import ApplyAttemptInput, ResolvedGrade, apply_attempt

    from tests.helpers import NOW_ISO

    apply_attempt(
        vault,
        Repository(sqlite_path),
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=PROBE,
                learner_answer_md="U",
                attempt_type="diagnostic_probe",
            ),
            attempt_id="att_probe_after_decision_read",
            grade=ResolvedGrade(
                rubric_score=2,
                criterion_points={"correctness": 2},
                evidence_rows=[
                    {
                        "id": "ge_att_probe_after_decision_read",
                        "criterion_id": "correctness",
                        "points_awarded": 2.0,
                        "evidence": "Named a factor but not the transposed one.",
                        "notes": None,
                        "local_grader_id": "test",
                        "grader_tier": 1,
                        "created_at": NOW_ISO,
                    }
                ],
                error_attributions=[],
                grader_confidence=0.9,
                confidence=3,
                manual_review_reason=None,
            ),
        ),
        clock=ATTEMPT_CLOCK,
    )


def _change_after_read(monkeypatch, repository: Repository, method: str, change, *, when=None) -> dict:
    """After ``repository``'s first matching ``method`` call, commit ``change``.

    If this repository holds the write lock at that point, ``change`` cannot
    commit inside the window; it is queued in ``seen["deferred"]`` for the test
    to run after the sync, and ``seen["blocked"]`` records that the lock held.
    """

    original = getattr(Repository, method)
    seen: dict = {"deferred": []}

    def read_then_change(self, *args):
        result = original(self, *args)
        if self is repository and "fired" not in seen and (when is None or when(*args)):
            seen["fired"] = True
            if _write_lock_held(repository.sqlite_path):
                seen["blocked"] = True
                seen["deferred"].append(change)
            else:
                change()
        return result

    monkeypatch.setattr(Repository, method, read_then_change)
    return seen


def test_a_probe_attempt_after_the_fallback_read_stays_retired(tmp_path, monkeypatch):
    """F1: another sync moves the row, then a real probe attempt lands right
    after the read the activation decision uses; the probe must stay retired."""

    paths = create_basic_vault(tmp_path / "vault", fresh=True)
    _add_diagnostic_probe(paths)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(load_vault(paths.root), repository, clock=SYNC_CLOCK)
    before = repository.practice_item_state(PROBE)
    assert before.active is True and before.last_attempt_at is None
    pre_edit_vault = load_vault(paths.root)
    _add_diagnostic_probe(paths, prompt="Which SVD factor appears transposed in A = U Sigma V^T?")
    edited = load_vault(paths.root)

    # Another content sync writes its hash between this sync's snapshot and its
    # write, so a snapshot-guarded update would miss and fall back to a re-read.
    original_states = Repository.practice_item_states
    other_sync: dict = {}

    def snapshot_then_other_sync(self):
        snapshot = original_states(self)
        if self is repository and "done" not in other_sync:
            other_sync["done"] = True
            with connect(paths.sqlite_path) as connection:
                connection.execute(
                    "UPDATE practice_item_state SET content_hash = ? WHERE practice_item_id = ?",
                    ("hash-from-another-sync", PROBE),
                )
                connection.commit()
        return snapshot

    monkeypatch.setattr(Repository, "practice_item_states", snapshot_then_other_sync)
    seen = _change_after_read(
        monkeypatch,
        repository,
        "practice_item_state",
        lambda: _commit_probe_attempt(pre_edit_vault, paths.sqlite_path),
        when=lambda item_id: item_id == PROBE,
    )

    sync_vault_state(edited, repository, clock=SYNC_CLOCK)
    monkeypatch.undo()
    for change in seen["deferred"]:
        change()

    assert seen.get("fired") is True
    state = repository.practice_item_state(PROBE)
    assert state.last_attempt_at is not None
    assert state.active is False
    # The decision read was taken under the sync's write lock.
    assert seen.get("blocked") is True
    # A later sync leaves the administered probe retired too.
    sync_vault_state(edited, repository, clock=SYNC_CLOCK)
    assert repository.practice_item_state(PROBE).active is False


def test_a_measurement_correction_after_the_lifecycle_reads_keeps_the_original_retired(
    tmp_path, monkeypatch
):
    """F2: a real correction (with its own sync) commits after this sync read
    ``measurement_superseded``; the superseded original must stay inactive."""

    from learnloop.attempts.measurement_corrections import create_measurement_correction

    paths, repository = _fresh_vault(tmp_path)
    _commit_attempt(paths.root, paths.sqlite_path)
    attempted = repository.practice_item_state(ITEM)
    assert attempted.active is True and attempted.last_attempt_at is not None
    _edit_prompt(paths.root, "Define the singular value decomposition of a real matrix.")
    edited = load_vault(paths.root)
    corrected_id = "pi_svd_define_001_measurement_v2"

    def correct():
        create_measurement_correction(
            paths.root,
            Repository(paths.sqlite_path),
            source_practice_item_id=ITEM,
            corrected_practice_item_id=corrected_id,
            corrected_fields={"expected_answer": "A = U Sigma V^T with orthogonal U, V."},
            reason="The expected answer omitted the orthogonality of the factors.",
            consuming_projection_version="mvp-0.7",
            clock=ATTEMPT_CLOCK,
        )

    seen = _change_after_read(monkeypatch, repository, "superseded_measurement_item_ids", correct)
    sync_vault_state(edited, repository, clock=SYNC_CLOCK)
    monkeypatch.undo()
    for change in seen["deferred"]:
        change()

    assert seen.get("fired") is True
    assert ITEM in repository.superseded_measurement_item_ids()
    state = repository.practice_item_state(ITEM)
    assert state.active is False
    assert _scheduling(state) == _scheduling(attempted)
    assert repository.practice_item_state(corrected_id).active is True


def test_review_parking_after_the_lifecycle_reads_keeps_the_item_inactive(tmp_path, monkeypatch):
    """F2's ``review_parked`` twin: an item parked behind instance review after
    this sync read the parked set must not be reactivated by it."""

    paths, repository = _fresh_vault(tmp_path)
    _edit_prompt(paths.root, "Define the singular value decomposition of a real matrix.")
    edited = load_vault(paths.root)

    def park():
        with connect(paths.sqlite_path) as connection:
            connection.execute(
                """
                INSERT INTO probe_item_family_links (
                  practice_item_id, instrument_card_id, instrument_card_version,
                  instance_metadata_json, created_at
                ) VALUES (?, 'card_parking_race', 1, '{"review_status": "pending_review"}', ?)
                """,
                (ITEM, ATTEMPT_CLOCK.now().isoformat()),
            )
            connection.execute(
                "UPDATE practice_item_state SET active = 0 WHERE practice_item_id = ?", (ITEM,)
            )
            connection.commit()

    seen = _change_after_read(
        monkeypatch,
        repository,
        "probe_instance_ids_with_review_status",
        park,
        when=lambda status: status == "pending_review",
    )
    sync_vault_state(edited, repository, clock=SYNC_CLOCK)
    monkeypatch.undo()
    for change in seen["deferred"]:
        change()

    assert seen.get("fired") is True
    state = repository.practice_item_state(ITEM)
    assert state.active is False
