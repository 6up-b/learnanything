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
    that decided from a pre-attempt snapshot would reactivate it; the guarded
    update sees the row moved and decides from the fresh row instead.
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
