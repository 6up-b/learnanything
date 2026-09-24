"""Compare disposable DELETE/WAL databases using FULL durability.

Run with `uv run python scripts/benchmark_sqlite_concurrency.py --iterations 200`.
`--fixture fixtures/linear_algebra` additionally measures, on disposable copies
of that vault, the longest reader blackout during live rebuilds in each mode
and the WAL size across repeated queue builds. The fixture itself is only read:
it is copied with the SQLite backup API. This never imports the test
connection patch.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import platform
import sqlite3
from tempfile import TemporaryDirectory
import threading
import time

# A busy failure is an operation that waited this long for the lock and then
# gave up, so every counted failure is a stall of the full timeout.
BUSY_TIMEOUT_SECONDS = 5


def _percentiles(elapsed: list[float]) -> dict:
    ordered = sorted(elapsed)
    return {
        "p50_ms": ordered[len(ordered) // 2],
        "p95_ms": ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))],
        "max_ms": ordered[-1],
    }


def benchmark(directory: Path, mode: str, iterations: int) -> dict:
    path = directory / f"{mode}.sqlite"
    def connect():
        connection = sqlite3.connect(path, timeout=BUSY_TIMEOUT_SECONDS)
        connection.execute("PRAGMA synchronous=FULL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection
    connection = connect()
    connection.execute(f"PRAGMA journal_mode={mode}")
    connection.execute("CREATE TABLE events(id INTEGER PRIMARY KEY, payload TEXT NOT NULL)")
    connection.commit()
    connection.close()
    barrier = threading.Barrier(3)
    def worker(writer):
        connection = connect()
        elapsed = []
        locked = 0
        barrier.wait()
        try:
            for ordinal in range(iterations):
                started = time.perf_counter()
                try:
                    if writer:
                        connection.execute("INSERT INTO events(payload) VALUES (?)", ("evidence:" + "x" * 2048,))
                        connection.commit()
                    else:
                        # Hold a short read snapshot as the UI serializes it.
                        connection.execute("BEGIN")
                        connection.execute("SELECT id,length(payload) FROM events ORDER BY id DESC LIMIT 30").fetchall()
                        time.sleep(0.002)
                        connection.commit()
                except sqlite3.OperationalError as exc:
                    connection.rollback()
                    if "locked" not in str(exc).lower():
                        raise
                    locked += 1
                elapsed.append((time.perf_counter() - started) * 1000)
        finally:
            connection.close()
        return {"role": "writer" if writer else "reader", "operations": iterations, "busy_failures": locked, **_percentiles(elapsed)}
    # Closing the last connection checkpoints and removes the WAL, so a
    # connection held open across the run keeps the WAL for the checkpoint
    # below to measure. It must read once to attach to the WAL index.
    keeper = connect()
    try:
        keeper.execute("SELECT count(*) FROM events").fetchone()
        started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(worker, writer) for writer in (True, False, False)]
            results = [future.result() for future in futures]
        seconds = time.perf_counter() - started
        count = keeper.execute("SELECT count(*) FROM events").fetchone()[0]
        integrity = keeper.execute("PRAGMA integrity_check").fetchone()[0]
        checkpoint = None
        if mode == "WAL":
            # TRUNCATE reports zero frames once it has emptied the log, so a
            # PASSIVE pass measures the frames and TRUNCATE confirms the reset.
            busy, log_frames, checkpointed_frames = keeper.execute("PRAGMA wal_checkpoint(PASSIVE)").fetchone()
            truncate_busy = keeper.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()[0]
            checkpoint = {"busy": busy, "log_frames": log_frames, "checkpointed_frames": checkpointed_frames, "truncate_busy": truncate_busy}
    finally:
        keeper.close()
    return {
        "journal_mode": mode,
        "synchronous": "FULL",
        "busy_timeout_seconds": BUSY_TIMEOUT_SECONDS,
        "seconds": seconds,
        "workers": results,
        "acknowledged_rows": count,
        "integrity": integrity,
        "checkpoint": checkpoint,
    }


# The reader polls this often and every rebuild is repeated this many times,
# matching the earlier rollback-journal measurement recorded in ADR-014.
READER_POLL_SECONDS = 0.001
REBUILDS_PER_MODE = 3
QUEUE_BUILDS = 20


def _fixture_copy(fixture: Path, destination: Path):
    """A migrated copy of ``fixture``: (vault, sqlite_path)."""

    from learnloop.db.copies import copy_tree_with_databases
    from learnloop.migration_coordinator import migrate_vault
    from learnloop.vault.loader import load_vault
    from learnloop.vault.paths import VaultPaths

    copy_tree_with_databases(fixture, destination)
    vault = load_vault(destination)
    sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
    migrate_vault(vault.root, sqlite_path)
    return vault, sqlite_path


def _poll_reads(sqlite_path: Path, stop: threading.Event, successes: list[float], failures: list[str]) -> None:
    from learnloop.db.connection import connect

    connection = connect(sqlite_path, read_only=True)
    try:
        while not stop.is_set():
            try:
                connection.execute("BEGIN")
                connection.execute("SELECT COUNT(*) FROM learning_object_mastery").fetchone()
                connection.commit()
                successes.append(time.perf_counter())
            except sqlite3.OperationalError as exc:
                connection.rollback()
                failures.append(str(exc))
            time.sleep(READER_POLL_SECONDS)
    finally:
        connection.close()


def rebuild_blackout(fixture: Path, directory: Path, mode: str) -> dict:
    """Longest gap between successful reads while live rebuilds run."""

    from learnloop.db.checkpoint import checkpoint_wal
    from learnloop.db.repositories import Repository
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
    from learnloop.substrate.state_sync import sync_vault_state

    vault, sqlite_path = _fixture_copy(fixture, directory / f"rebuild-{mode.lower()}")
    if mode == "DELETE":
        with closing(sqlite3.connect(sqlite_path)) as connection:
            connection.execute("PRAGMA journal_mode=DELETE")
    repository = Repository.attach(sqlite_path, read_only=False)
    sync_vault_state(vault, repository)
    rebuilds = []
    for _ in range(REBUILDS_PER_MODE):
        stop = threading.Event()
        successes: list[float] = []
        failures: list[str] = []
        reader = threading.Thread(target=_poll_reads, args=(sqlite_path, stop, successes, failures))
        reader.start()
        time.sleep(0.05)
        started = time.perf_counter()
        rebuild_all_derived_state(vault, repository)
        finished = time.perf_counter()
        time.sleep(0.05)
        stop.set()
        reader.join()
        window = [started] + [moment for moment in successes if started <= moment <= finished] + [finished]
        longest_gap = max(later - earlier for earlier, later in zip(window, window[1:]))
        rebuilds.append({
            "rebuild_seconds": round(finished - started, 3),
            "longest_reader_blackout_seconds": round(longest_gap, 3),
            "reads_during_rebuild": len(window) - 2,
            "reader_busy_failures": len(failures),
        })
    checkpoint = None
    if mode == "WAL":
        wal_before = _wal_bytes(sqlite_path)
        started = time.perf_counter()
        result = checkpoint_wal(sqlite_path, reason="benchmark")
        checkpoint = {
            "wal_bytes_before": wal_before,
            "wal_bytes_after": _wal_bytes(sqlite_path),
            "seconds": round(time.perf_counter() - started, 3),
            "busy": result.busy if result else None,
        }
    return {"journal_mode": mode, "database_bytes": sqlite_path.stat().st_size, "rebuilds": rebuilds, "truncate_checkpoint": checkpoint}


def _wal_bytes(sqlite_path: Path) -> int:
    wal_path = sqlite_path.with_name(sqlite_path.name + "-wal")
    return wal_path.stat().st_size if wal_path.exists() else 0


def queue_build_wal_growth(fixture: Path, directory: Path) -> dict:
    """WAL size after each of QUEUE_BUILDS persisted queue builds, with a reader open."""

    from learnloop.db.checkpoint import checkpoint_wal
    from learnloop.db.connection import connect
    from learnloop.scheduling.scheduler import build_due_queue
    from learnloop.substrate.state_sync import sync_vault_state
    from learnloop.vault.repository import open_vault_repository

    vault, sqlite_path = _fixture_copy(fixture, directory / "queue-builds")
    repository = open_vault_repository(vault.root, sqlite_path)
    sync_vault_state(vault, repository)
    # The desktop keeps connections open, so the WAL is never removed on close.
    idle_reader = connect(sqlite_path, read_only=True)
    try:
        idle_reader.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()
        sizes = []
        seconds = []
        for _ in range(QUEUE_BUILDS):
            started = time.perf_counter()
            build_due_queue(vault, repository, persist_explanations=True)
            seconds.append(round(time.perf_counter() - started, 3))
            sizes.append(_wal_bytes(sqlite_path))
        result = checkpoint_wal(sqlite_path, reason="benchmark")
        after = _wal_bytes(sqlite_path)
    finally:
        idle_reader.close()
    return {
        "queue_builds": QUEUE_BUILDS,
        "wal_bytes_after_each_build": sizes,
        "max_wal_bytes": max(sizes),
        "build_seconds_p50": sorted(seconds)[len(seconds) // 2],
        "truncate_checkpoint_busy": result.busy if result else None,
        "wal_bytes_after_truncate": after,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=200)
    parser.add_argument("--directory", type=Path, help="Parent filesystem to measure; default system temporary directory.")
    parser.add_argument("--fixture", type=Path, help="Vault to copy for the live-rebuild and queue-build measurements.")
    args = parser.parse_args()
    if args.iterations < 1:
        parser.error("iterations must be positive")
    with TemporaryDirectory(prefix="learnloop-sqlite-benchmark-", dir=args.directory) as directory:
        results = [benchmark(Path(directory), mode, args.iterations) for mode in ("DELETE", "WAL")]
        report = {"sqlite_version": sqlite3.sqlite_version, "platform": platform.platform(), "filesystem_path": str(Path(directory).parent), "results": results}
        if args.fixture is not None:
            fixture = args.fixture.resolve()
            report["fixture"] = str(fixture)
            report["live_rebuild"] = [rebuild_blackout(fixture, Path(directory), mode) for mode in ("DELETE", "WAL")]
            report["queue_build_wal_growth"] = queue_build_wal_growth(fixture, Path(directory))
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
