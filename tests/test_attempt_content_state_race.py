"""Mobile PR-4: attempt recording never writes back the content columns it computed.

The reverse of PR-2's race (``docs/reviews/mobile-pr2-content-sync.md`` open
question 1; ``spec_mobile_tailnet_v1`` §9.3, G6b). An attempt graded from a
vault loaded before a content sync computed ``active`` and ``content_hash``
from that older vault. When the sync (another process: the desktop's watcher,
the phone host's reload, the TUI) commits while the answer is being graded,
the attempt's commit used to write both back: a retired item reopened, and an
edited item got its old hash again. Each test here commits the sync inside
that window, right before the attempt's transaction, and checks that the
attempt's scheduling fields land while the content columns stay the sync's.

Durability lane: production pragmas and WAL on fresh vaults.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import timedelta
from pathlib import Path

import pytest

import learnloop.attempts.attempts as attempts_module
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.hashes import practice_item_hash
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import NOW, create_basic_vault
from tests.test_state_sync_scheduling_race import (
    PROBE,
    _add_diagnostic_probe,
    _commit_probe_attempt,
)

pytestmark = pytest.mark.durability

ITEM = "pi_svd_define_001"
SYNC_CLOCK = FrozenClock(NOW)
ATTEMPT_CLOCK = FrozenClock(NOW + timedelta(hours=1))


def _fresh_vault(tmp_path: Path):
    paths = create_basic_vault(tmp_path / "vault", fresh=True)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(load_vault(paths.root), repository, clock=SYNC_CLOCK)
    return paths, repository


def _edit_item(vault_root: Path, **changes) -> None:
    vault = load_vault(vault_root)
    payload = vault.practice_items[ITEM].model_dump(mode="json", exclude_none=False)
    payload.update(changes)
    upsert_practice_item(vault_root, payload, loaded_vault=vault, clock=SYNC_CLOCK)


def _sync_before_the_attempt_commits(monkeypatch, sync) -> dict:
    """Run ``sync`` after the attempt was graded and before its transaction opens."""

    original = attempts_module.apply_attempt
    seen: dict = {}

    def sync_then_apply(vault, repository, attempt, *, clock=None):
        if "synced" not in seen and not attempt.replace_existing:
            sync()
            seen["synced"] = Repository.attach(repository.sqlite_path).practice_item_state(ITEM)
        return original(vault, repository, attempt, clock=clock)

    monkeypatch.setattr(attempts_module, "apply_attempt", sync_then_apply)
    return seen


def _attempt(vault, sqlite_path: Path) -> None:
    complete_self_graded_attempt(
        vault,
        Repository(sqlite_path),
        AttemptDraft(
            practice_item_id=ITEM,
            learner_answer_md="SVD factors a matrix into U, Sigma and V transpose.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=4),
        clock=ATTEMPT_CLOCK,
    )


def _sync_in_this_process(vault_root: Path, sqlite_path: Path):
    def sync():
        sync_vault_state(load_vault(vault_root), Repository(sqlite_path), clock=SYNC_CLOCK)

    return sync


def test_an_attempt_graded_before_a_retiring_sync_keeps_the_item_closed(tmp_path, monkeypatch):
    paths, repository = _fresh_vault(tmp_path)
    stale = load_vault(paths.root)  # the vault the answer is graded against
    before = repository.practice_item_state(ITEM)
    assert before.active is True and before.last_attempt_at is None
    _edit_item(paths.root, status="retired")
    seen = _sync_before_the_attempt_commits(monkeypatch, _sync_in_this_process(paths.root, paths.sqlite_path))

    _attempt(stale, paths.sqlite_path)

    assert seen["synced"].active is False
    state = repository.practice_item_state(ITEM)
    assert state.active is False
    assert state.content_hash == seen["synced"].content_hash
    # The attempt's own columns landed.
    assert state.last_attempt_at is not None and state.stability is not None and state.due_at is not None


def test_an_attempt_graded_before_an_editing_sync_keeps_the_edited_hash(tmp_path, monkeypatch):
    paths, repository = _fresh_vault(tmp_path)
    stale = load_vault(paths.root)
    old_hash = repository.practice_item_state(ITEM).content_hash
    _edit_item(paths.root, prompt="Define the singular value decomposition of a real matrix.")
    edited_hash = practice_item_hash(load_vault(paths.root).practice_items[ITEM])
    assert edited_hash != old_hash
    seen = _sync_before_the_attempt_commits(monkeypatch, _sync_in_this_process(paths.root, paths.sqlite_path))

    _attempt(stale, paths.sqlite_path)

    assert seen["synced"].content_hash == edited_hash
    state = repository.practice_item_state(ITEM)
    assert state.content_hash == edited_hash
    assert state.active is True
    assert state.last_attempt_at is not None and state.stability is not None


_SYNC_IN_ANOTHER_PROCESS = """
import sys
from datetime import datetime
from pathlib import Path
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

root, sqlite_path, when = sys.argv[1:4]
sync_vault_state(load_vault(Path(root)), Repository(Path(sqlite_path)), clock=FrozenClock(datetime.fromisoformat(when)))
"""


def test_a_retiring_sync_from_a_second_process_survives_an_attempt_graded_before_it(tmp_path, monkeypatch):
    """G6b's reverse clause with a real second process on the WAL database."""

    paths, repository = _fresh_vault(tmp_path)
    stale = load_vault(paths.root)
    _edit_item(paths.root, status="retired")
    (tmp_path / "home").mkdir()
    (tmp_path / "config").mkdir()
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": str(tmp_path / "home"),
        "LEARNLOOP_CONFIG_DIR": str(tmp_path / "config"),
        "PYTHONPATH": os.pathsep.join(sys.path),
    }

    def sync_in_another_process():
        subprocess.run(
            [sys.executable, "-c", _SYNC_IN_ANOTHER_PROCESS, str(paths.root), str(paths.sqlite_path),
             SYNC_CLOCK.now().isoformat()],
            check=True, env=env, timeout=120,
        )

    seen = _sync_before_the_attempt_commits(monkeypatch, sync_in_another_process)

    _attempt(stale, paths.sqlite_path)

    assert seen["synced"].active is False
    state = repository.practice_item_state(ITEM)
    assert state.active is False
    assert state.last_attempt_at is not None


def test_a_probe_attempt_still_closes_its_single_use_surface(tmp_path):
    paths = create_basic_vault(tmp_path / "vault", fresh=True)
    _add_diagnostic_probe(paths)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=SYNC_CLOCK)
    assert repository.practice_item_state(PROBE).active is True

    _commit_probe_attempt(vault, paths.sqlite_path)

    state = repository.practice_item_state(PROBE)
    assert state.active is False
    assert state.last_attempt_at is not None


def test_an_attempt_on_an_item_with_no_row_inserts_the_whole_row(tmp_path):
    paths = create_basic_vault(tmp_path / "vault", fresh=True)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    with connect(paths.sqlite_path) as connection:
        connection.execute("DELETE FROM practice_item_state WHERE practice_item_id = ?", (ITEM,))
        connection.commit()
    assert repository.practice_item_state(ITEM) is None

    _attempt(vault, paths.sqlite_path)

    state = repository.practice_item_state(ITEM)
    assert state.active is True
    assert state.content_hash == practice_item_hash(vault.practice_items[ITEM])
    assert state.last_attempt_at is not None and state.stability is not None
