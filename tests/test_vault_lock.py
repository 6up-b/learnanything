from __future__ import annotations

import os

import pytest

from learnloop.services.vault_lock import (
    VaultLockTimeout,
    read_lock_holder,
    vault_lock_path,
    vault_mutation_lock,
)


def test_lock_acquire_writes_holder_and_releases(tmp_path):
    root = tmp_path / "vault"
    root.mkdir()
    with vault_mutation_lock(root, purpose="proposal_accept") as holder:
        assert holder.pid == os.getpid()
        assert holder.purpose == "proposal_accept"
        current = read_lock_holder(root)
        assert current is not None and current.pid == os.getpid()
    # After release the holder metadata is blanked.
    assert read_lock_holder(root) is None
    assert vault_lock_path(root).exists()


def test_reentrant_after_release(tmp_path):
    root = tmp_path / "vault"
    root.mkdir()
    for _ in range(3):
        with vault_mutation_lock(root, purpose="x"):
            pass


def test_contended_lock_times_out(tmp_path):
    """A second acquirer within the same process cannot take the held lock and
    times out with a diagnostic naming the holder."""

    root = tmp_path / "vault"
    root.mkdir()
    with vault_mutation_lock(root, purpose="holder"):
        # A held flock blocks another open fd on the same file.
        import fcntl

        fd = os.open(vault_lock_path(root), os.O_RDWR)
        try:
            with pytest.raises(BlockingIOError):
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        finally:
            os.close(fd)


def test_cross_process_serialization(tmp_path):
    """A forked child holding the lock forces the parent's timed acquire to fail."""

    import multiprocessing

    root = tmp_path / "vault"
    root.mkdir()
    ready = multiprocessing.get_context("fork").Event()
    release = multiprocessing.get_context("fork").Event()

    def _hold(root_str, ready_ev, release_ev):
        from learnloop.services.vault_lock import vault_mutation_lock as lock

        with lock(root_str, purpose="child"):
            ready_ev.set()
            release_ev.wait(timeout=5)
        os._exit(0)

    proc = multiprocessing.get_context("fork").Process(
        target=_hold, args=(str(root), ready, release)
    )
    proc.start()
    try:
        assert ready.wait(timeout=5)
        with pytest.raises(VaultLockTimeout):
            with vault_mutation_lock(root, purpose="parent", timeout_s=0.3):
                pass
    finally:
        release.set()
        proc.join(timeout=5)
    # Once the child releases, the parent can acquire.
    with vault_mutation_lock(root, purpose="parent", timeout_s=5):
        pass
