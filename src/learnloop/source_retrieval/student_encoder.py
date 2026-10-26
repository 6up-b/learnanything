"""The adopted query student behind the resolver's hook (spec_local_contextual_retrieval_v1 §5.1, §7.1 "Serving", §9.3; P2).

:func:`adopted_encoder` is ``spaces.LOCAL_QUERY_ENCODER``'s production value. It returns a
:class:`StudentEncoder` only when every switch allows it and a checkpoint was adopted by the
expected-utility rule of §9.3 (``query_student.evaluate``):

* ``embedding.local.enabled`` and ``embedding.local.student`` (the student's kill switch) on;
* the local space set up (``learnloop embeddings local setup``) and the student bases recorded;
* ``<data root>/students/<space id>/adoption.json`` naming a checkpoint present under the space.

Otherwise ``None``: the local space reports ``encoder_unavailable`` and the resolver serves
through the other spaces exactly as in P1.

**The query process** (``local_embeddings.student_server``) is started lazily on the first
local query, in its own ``systemd-run --user --scope -p MemoryMax=4G -p MemorySwapMax=0``, and
exits after ``embedding.local.student_idle_minutes`` idle. The app never imports torch: it talks
JSON over the process's Unix socket. Whether a query waits for a starting process is the rule of
§5.1 item 3 (``student_decision.should_wait``) on the MEASURED start times this module records.

**The nightly teacher replay (§9.3).** With ``embedding.local.teacher_replay`` on, every query
the student answers for a logged search (a receipt id) is queued in the vault's
``.learnloop/student-replay.sqlite`` (learner text stays local, outside ``state.sqlite``, like
the vector cache). The next index batch, which loads the 9B anyway, re-encodes a sample with the
teacher (``local_index``), so a ``local:teacher`` ranking exists for real traffic.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from contextlib import closing
from datetime import datetime, timedelta, timezone
import fcntl
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import threading
import time
from typing import Any
import uuid

import numpy as np

from learnloop.db.connection import connect
from learnloop.local_embeddings import pins
from learnloop.local_embeddings import student_decision as SD
from learnloop.local_embeddings import student_pins as SP
from learnloop.local_embeddings.identity import query_encoder_id
from learnloop.local_embeddings.launcher import gpu_lock_path, launch_environment
from learnloop.vault.models import LoadedVault

REPLAY_FILE = (".learnloop", "student-replay.sqlite")
_REPLAY_SCHEMA = (
    "CREATE TABLE IF NOT EXISTS replay_queries ("
    " receipt_id TEXT NOT NULL, text_key TEXT NOT NULL, text TEXT NOT NULL, encoder_id TEXT NOT NULL,"
    " checkpoint_sha256 TEXT NOT NULL, dims INTEGER NOT NULL, vector BLOB NOT NULL,"
    " created_at TEXT NOT NULL, replayed_at TEXT, teacher_top TEXT, student_top TEXT,"
    " PRIMARY KEY (receipt_id, text_key))",
    "CREATE INDEX IF NOT EXISTS replay_pending ON replay_queries(replayed_at, created_at)",
)
_ENCODERS: dict[tuple[str, str], "StudentEncoder"] = {}
_ENCODERS_LOCK = threading.Lock()


class StudentUnavailable(RuntimeError):
    """The query process could not answer (refused, failed its canary, or late)."""


# -- adoption ----------------------------------------------------------------------------------
def adoption_path(data_root: Path, space_id: str) -> Path:
    return SP.space_home(data_root, space_id) / "adoption.json"


def checkpoint_dir(data_root: Path, space_id: str, sha: str) -> Path:
    if not sha or "/" in sha or sha.startswith("."):
        raise ValueError("a checkpoint digest names one directory")
    return SP.space_home(data_root, space_id) / "checkpoints" / sha


def read_adoption(data_root: Path, space_id: str) -> dict[str, Any] | None:
    try:
        value = json.loads(adoption_path(data_root, space_id).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) and value.get("checkpoint_sha256") else None


def student_space(manifest: Mapping[str, Any]) -> str:
    """The space a student is trained for: the grouped local space of this epoch (its KD documents).

    The teacher's query vectors do not depend on the window variant, so the student serves both
    local lists; any change to the 9B's pins (revision, code, precision, epoch) is a new space and
    retires the student (spec §4.2)."""

    from learnloop.source_retrieval.local_index import local_spaces

    return local_spaces(manifest)["grouped"][0]


def bases_manifest(data_root: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(SP.bases_manifest_path(data_root).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def adopted_encoder(vault: LoadedVault, *, data_root: Path | None = None) -> "StudentEncoder | None":
    """``spaces.LOCAL_QUERY_ENCODER``: the adopted student, or None (never raises)."""

    try:
        settings = vault.config.embedding.local
        if not (settings.enabled and settings.student):
            return None
        from learnloop.source_retrieval.local_index import local_reason

        root = data_root or pins.data_root()
        manifest, _reason = local_reason(vault, root)
        if manifest is None:
            return None
        space = student_space(manifest)
        adoption = read_adoption(root, space)
        bases = bases_manifest(root)
        if adoption is None or bases is None:
            return None
        sha = str(adoption["checkpoint_sha256"])
        directory = checkpoint_dir(root, space, sha)
        base_name = str(adoption.get("base_name") or "")
        base_record = (bases.get("bases") or {}).get(base_name)
        if not (directory / "student.json").is_file() or base_record is None or base_name not in SP.STUDENT_BASES:
            return None
        key = (str(Path(vault.root).resolve()), sha)
        with _ENCODERS_LOCK:
            encoder = _ENCODERS.get(key)
            if encoder is None:
                encoder = StudentEncoder(vault, space_id=space, checkpoint_sha=sha, checkpoint=directory,
                                         base_name=base_name, base_dir=Path(base_record["dir"]),
                                         env_python=Path(manifest["env_python"]), data_root=root)
                _ENCODERS[key] = encoder
            encoder.vault = vault
        return encoder
    except Exception:  # noqa: BLE001 - a lookup never fails a search
        return None


# -- the client ----------------------------------------------------------------------------------
def runtime_dir(sha: str) -> Path:
    runtime = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
    return Path(runtime) / "learnloop-student" / sha[:16]


def server_command(env_python: Path, job: Path, *, unit: str) -> list[str]:
    """The query process inside its own transient scope with the 4G cap (keep)."""

    from learnloop.local_embeddings import student_server

    return ["systemd-run", "--user", "--scope", "--quiet", f"--unit={unit}",
            "-p", f"MemoryMax={SP.SERVE_SCOPE_MEMORY_MAX}", "-p", f"MemorySwapMax={SP.SERVE_SCOPE_SWAP_MAX}", "--",
            str(env_python), "-I", str(Path(student_server.__file__).resolve()), "--job", str(job)]


def _spawn(command: Sequence[str], *, env: Mapping[str, str], log: Path) -> Any:
    with open(log, "ab") as sink:
        return subprocess.Popen(list(command), env=dict(env), stdin=subprocess.DEVNULL, stdout=sink, stderr=sink,
                                start_new_session=True)


def request(socket_path: Path, payload: Mapping[str, Any], *, timeout_s: float) -> dict[str, Any]:
    """One JSON-line request over the query process's Unix socket."""

    with closing(socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)) as client:
        client.settimeout(max(timeout_s, 0.001))
        client.connect(str(socket_path))
        client.sendall((json.dumps(dict(payload)) + "\n").encode("utf-8"))
        chunks = []
        while True:
            chunk = client.recv(1 << 20)
            if not chunk:
                break
            chunks.append(chunk)
            if chunk.endswith(b"\n"):
                break
    return json.loads(b"".join(chunks).decode("utf-8") or "{}")


class StudentEncoder:
    """``LocalQueryEncoder`` for the adopted checkpoint (lazy start, idle exit, measured starts)."""

    accepts_receipt = True

    def __init__(self, vault: LoadedVault, *, space_id: str, checkpoint_sha: str, checkpoint: Path, base_name: str,
                 base_dir: Path, env_python: Path, data_root: Path,
                 spawn: Callable[..., Any] = _spawn, clock: Callable[[], float] = time.time,
                 sleep: Callable[[float], None] = time.sleep) -> None:
        self.vault = vault
        self.space_id = space_id
        self.sha = checkpoint_sha
        self.checkpoint = Path(checkpoint)
        self.base_name = base_name
        self.base = SP.STUDENT_BASES[base_name]
        self.base_dir = Path(base_dir)
        self.env_python = Path(env_python)
        self.data_root = Path(data_root)
        self.spawn = spawn
        self.clock = clock
        self.sleep = sleep
        self.home = runtime_dir(checkpoint_sha)
        self.socket_path = self.home / "student.sock"
        self.status_path = self.home / "status.json"
        self._requested_at: float | None = None

    # identity
    def device_class(self) -> str:
        status = self.status()
        if status.get("status") == "ready":
            return str(status.get("device") or "gpu")
        return "gpu"

    @property
    def encoder_id(self) -> str:
        return query_encoder_id(self.space_id, encoder=f"student:{self.sha}", precision=SP.STUDENT_PRECISION,
                                device_class=self.device_class(), method=SP.STUDENT_QUERY_METHOD)

    # process state
    def status(self) -> dict[str, Any]:
        try:
            value = json.loads(self.status_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        if value.get("checkpoint_sha256") != self.sha:
            return {}
        return value

    def _alive(self, status: Mapping[str, Any]) -> bool:
        pid = status.get("pid")
        if not isinstance(pid, int):
            return False
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True

    def ready(self) -> bool:
        status = self.status()
        return status.get("status") == "ready" and self.socket_path.exists() and self._alive(status)

    def start_times(self) -> list[float]:
        try:
            return [float(value) for value in json.loads((self.checkpoint / "start_times.json").read_text(
                encoding="utf-8"))]
        except (OSError, ValueError, TypeError):
            return []

    def _record_start(self, seconds: float) -> None:
        values = (self.start_times() + [round(float(seconds), 3)])[-SP.START_TIMES_KEPT:]
        path = self.checkpoint / "start_times.json"
        temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        temporary.write_text(json.dumps(values), encoding="utf-8")
        os.replace(temporary, path)

    def job(self) -> dict[str, Any]:
        idle = float(self.vault.config.embedding.local.student_idle_minutes)
        return {"version": SP.SERVER_VERSION, "checkpoint_dir": str(self.checkpoint), "checkpoint_sha256": self.sha,
                "base_dir": str(self.base_dir), "base": {key: self.base[key] for key in (
                    "repo", "revision", "pooling", "query_prefix", "hidden_size", "trust_remote_code", "files",
                    "remote_code", "inert_python")},
                "socket_path": str(self.socket_path), "status_path": str(self.status_path),
                "gpu_lock": str(gpu_lock_path()), "idle_minutes": idle, "socket_timeout_s": SP.SOCKET_TIMEOUT_S,
                "canary_queries": list(SP.STUDENT_CANARY_QUERIES), "canary_min_cos": SP.STUDENT_CANARY_MIN_COS,
                "limits": {"memory_max_bytes": SP.SERVE_SCOPE_MEMORY_MAX_BYTES, "swap_max_bytes": 0,
                           "min_host_available_gib": SP.SERVE_MIN_HOST_AVAILABLE_GIB,
                           "min_free_vram_gib": SP.SERVE_MIN_FREE_VRAM_GIB, "host_floor_gib": pins.HOST_FLOOR_GIB}}

    def start(self) -> bool:
        """Start the query process unless one is up or starting (one starter at a time, by a lock)."""

        if self.ready():
            return False
        from learnloop.source_retrieval.student_data import models_off

        if models_off():
            return False
        self.home.mkdir(parents=True, exist_ok=True)
        os.chmod(self.home, 0o700)
        status = self.status()
        if status.get("status") == "starting" and self._alive(status):
            return False
        with open(self.home / "start.lock", "a+") as handle:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return False
            try:
                job_path = self.home / "job.json"
                job_path.write_text(json.dumps(self.job()), encoding="utf-8")
                os.chmod(job_path, 0o600)
                self._requested_at = self.clock()
                unit = f"learnloop-student-{self.sha[:12]}-{uuid.uuid4().hex[:8]}"
                process = self.spawn(server_command(self.env_python, job_path, unit=unit),
                                     env=launch_environment(self.home / "home"), log=self.home / "server.log")
                pid = getattr(process, "pid", None)
                temporary = self.status_path.with_name(".status.json.tmp")
                temporary.write_text(json.dumps({"status": "starting", "pid": pid, "checkpoint_sha256": self.sha,
                                                 "requested_unix": self._requested_at}), encoding="utf-8")
                os.replace(temporary, self.status_path)
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        return True

    def wait_decision(self, remaining_s: float, weight_share: float) -> tuple[bool, float]:
        return SD.should_wait(self.start_times(), remaining_s, weight_share)

    def _await_ready(self, deadline: float | None) -> None:
        while not self.ready():
            status = self.status()
            if status.get("status") in ("refused", "failed", "canary_failed", "exited"):
                raise StudentUnavailable(f"the query student {status.get('status')}: {status.get('reason') or ''}"[:300])
            if deadline is not None and time.monotonic() >= deadline:
                raise TimeoutError("the query student did not start within the time box")
            self.sleep(0.05)
        status = self.status()
        if self._requested_at is not None:
            ready_at = float(status.get("started_unix") or self._requested_at) + float(status.get("start_s") or 0.0)
            self._record_start(max(0.0, ready_at - self._requested_at))
            self._requested_at = None

    def encode(self, texts: Sequence[str], *, deadline: float | None = None,
               receipt_id: str | None = None) -> list[list[float]]:
        if not self.ready():
            self.start()
            self._await_ready(deadline)
        remaining = SP.SOCKET_TIMEOUT_S if deadline is None else deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("the retrieval time box ran out before the student query")
        reply = request(self.socket_path, {"op": "encode", "texts": list(texts)}, timeout_s=remaining)
        if not reply.get("ok"):
            raise StudentUnavailable(f"the query student refused the request ({reply.get('error')})")
        vectors = [list(map(float, row)) for row in reply["vectors"]]
        if len(vectors) != len(texts):
            raise StudentUnavailable("the query student returned the wrong number of vectors")
        if receipt_id and self.vault.config.embedding.local.teacher_replay:
            queue_replay(self.vault, receipt_id=receipt_id, texts=texts, vectors=vectors,
                         encoder_id=self.encoder_id, checkpoint_sha=self.sha)
        return vectors


# -- the replay queue (learner text, local) -----------------------------------------------------------
def replay_path(vault_root: Path) -> Path:
    return Path(vault_root).joinpath(*REPLAY_FILE)


def _replay(vault_root: Path) -> sqlite3.Connection:
    path = replay_path(vault_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = connect(path)
    for statement in _REPLAY_SCHEMA:
        connection.execute(statement)
    return connection


def _text_key(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]


def queue_replay(vault: LoadedVault, *, receipt_id: str, texts: Sequence[str], vectors: Sequence[Sequence[float]],
                 encoder_id: str, checkpoint_sha: str) -> int:
    """Queue a served query for the next teacher replay (never fails the search)."""

    try:
        now = datetime.now(timezone.utc).isoformat()
        with closing(_replay(vault.root)) as connection, connection:
            written = 0
            for text, vector in zip(texts, vectors, strict=True):
                array = np.asarray(vector, dtype=np.float64)
                cursor = connection.execute(
                    "INSERT OR IGNORE INTO replay_queries (receipt_id, text_key, text, encoder_id, checkpoint_sha256,"
                    " dims, vector, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (receipt_id, _text_key(text), str(text), encoder_id, checkpoint_sha, int(array.size),
                     array.astype("<f2").tobytes(), now))
                written += cursor.rowcount
        return written
    except Exception:  # noqa: BLE001 - the queue never fails a search
        return 0


def pending_replay(vault_root: Path, *, limit: int = SP.REPLAY_MAX_QUERIES) -> list[dict[str, Any]]:
    """Unreplayed queries, newest first, at most ``limit`` (the GPU budget, keep)."""

    if not replay_path(vault_root).is_file():
        return []
    with closing(connect(replay_path(vault_root), read_only=True)) as connection:
        rows = connection.execute(
            "SELECT receipt_id, text_key, text, encoder_id, checkpoint_sha256, vector, created_at FROM replay_queries"
            " WHERE replayed_at IS NULL ORDER BY created_at DESC LIMIT ?", (int(limit),)).fetchall()
    return [{"receipt_id": row[0], "text_key": row[1], "text": row[2], "encoder_id": row[3], "checkpoint": row[4],
             "vector": np.frombuffer(row[5], dtype="<f2").astype(np.float64), "created_at": row[6]} for row in rows]


def replay_due(vault_root: Path, *, now: datetime | None = None) -> bool:
    """A replay-only batch is due when queries wait and the last replay is older than REPLAY_EVERY_HOURS."""

    if not replay_path(vault_root).is_file():
        return False
    with closing(connect(replay_path(vault_root), read_only=True)) as connection:
        waiting = connection.execute("SELECT COUNT(*) FROM replay_queries WHERE replayed_at IS NULL").fetchone()[0]
        last = connection.execute("SELECT MAX(replayed_at) FROM replay_queries").fetchone()[0]
    if not waiting:
        return False
    if last is None:
        return True
    moment = now or datetime.now(timezone.utc)
    return moment - datetime.fromisoformat(str(last)) >= timedelta(hours=SP.REPLAY_EVERY_HOURS)


def record_replay(vault_root: Path, results: Sequence[Mapping[str, Any]]) -> int:
    now = datetime.now(timezone.utc).isoformat()
    with closing(_replay(vault_root)) as connection, connection:
        for row in results:
            connection.execute("UPDATE replay_queries SET replayed_at = ?, teacher_top = ?, student_top = ? "
                               "WHERE receipt_id = ? AND text_key = ?",
                               (now, json.dumps(list(row["teacher_top"])), json.dumps(list(row["student_top"])),
                                row["receipt_id"], row["text_key"]))
    return len(results)


def replay_report(vault: LoadedVault, repository: Any) -> dict[str, Any]:
    """§9.3 on real traffic: the student's teacher top-10 agreement, and the signalled spans each
    list held in its top 10 (biased toward the delivered student list: a lower bound on the
    teacher's advantage)."""

    from learnloop.db.stores.retrieval_spaces import feedback_rows

    if not replay_path(vault.root).is_file():
        return {"replayed": 0, "pending": 0}
    with closing(connect(replay_path(vault.root), read_only=True)) as connection:
        rows = connection.execute("SELECT receipt_id, teacher_top, student_top FROM replay_queries "
                                  "WHERE replayed_at IS NOT NULL").fetchall()
        pending = connection.execute("SELECT COUNT(*) FROM replay_queries WHERE replayed_at IS NULL").fetchone()[0]
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        try:
            signals = feedback_rows(connection)
        except sqlite3.DatabaseError:
            signals = []
    signalled: dict[str, set[str]] = {}
    for row in signals:
        if row.get("event") in ("cited", "opened", "anchored") and row.get("span_id"):
            from learnloop.source_retrieval.recipes import block_record_id

            signalled.setdefault(str(row["receipt_id"]), set()).add(
                block_record_id(str(row["extraction_id"]), str(row["span_id"])))
    agreements, teacher_hits, student_hits, signal_total = [], 0, 0, 0
    for receipt, teacher_top, student_top in rows:
        teacher, student = json.loads(teacher_top or "[]")[:SP.AGREEMENT_K], json.loads(student_top or "[]")[:SP.AGREEMENT_K]
        if teacher:
            agreements.append(len(set(teacher) & set(student)) / len(teacher))
        for span in signalled.get(str(receipt), ()):
            signal_total += 1
            teacher_hits += span in teacher
            student_hits += span in student
    return {"replayed": len(rows), "pending": int(pending),
            "agreement_mean": round(float(np.mean(agreements)), 4) if agreements else None,
            "signalled_spans": signal_total, "teacher_top10_signal_hits": teacher_hits,
            "student_top10_signal_hits": student_hits,
            "teacher_advantage_lower_bound": (round((teacher_hits - student_hits) / signal_total, 4)
                                              if signal_total else None)}


__all__ = ["REPLAY_FILE", "StudentEncoder", "StudentUnavailable", "adopted_encoder", "adoption_path",
           "bases_manifest", "checkpoint_dir", "pending_replay", "queue_replay", "read_adoption", "record_replay",
           "replay_due", "replay_path", "replay_report", "request", "runtime_dir", "server_command", "student_space"]
