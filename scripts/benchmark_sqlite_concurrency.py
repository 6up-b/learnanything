"""Compare disposable DELETE/WAL databases using FULL durability.

Run with `uv run python scripts/benchmark_sqlite_concurrency.py --iterations 200`.
This never changes a vault's journal mode or imports the test connection patch.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import platform
import sqlite3
from tempfile import TemporaryDirectory
import threading
import time


def benchmark(directory: Path, mode: str, iterations: int) -> dict:
    path = directory / f"{mode}.sqlite"
    def connect():
        connection = sqlite3.connect(path, timeout=5)
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
        elapsed.sort()
        return {"role": "writer" if writer else "reader", "operations": iterations, "busy_failures": locked, "p50_ms": elapsed[len(elapsed) // 2], "p95_ms": elapsed[min(len(elapsed) - 1, int(len(elapsed) * 0.95))], "max_ms": elapsed[-1]}
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(worker, writer) for writer in (True, False, False)]
        results = [future.result() for future in futures]
    connection = connect()
    try:
        count = connection.execute("SELECT count(*) FROM events").fetchone()[0]
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        checkpoint = list(connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()) if mode == "WAL" else None
    finally:
        connection.close()
    return {"journal_mode": mode, "synchronous": "FULL", "seconds": time.perf_counter() - started, "workers": results, "acknowledged_rows": count, "integrity": integrity, "checkpoint": checkpoint}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=200)
    parser.add_argument("--directory", type=Path, help="Parent filesystem to measure; default system temporary directory.")
    args = parser.parse_args()
    if args.iterations < 1:
        parser.error("iterations must be positive")
    with TemporaryDirectory(prefix="learnloop-sqlite-benchmark-", dir=args.directory) as directory:
        print(json.dumps({"sqlite_version": sqlite3.sqlite_version, "platform": platform.platform(), "filesystem_path": str(Path(directory).parent), "results": [benchmark(Path(directory), mode, args.iterations) for mode in ("DELETE", "WAL")]}, indent=2))


if __name__ == "__main__":
    main()
