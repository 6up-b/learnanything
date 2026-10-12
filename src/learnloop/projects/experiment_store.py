"""``<vault>/projects/project_store.sqlite``: the standalone M1 store (spec §6.1).

M1 touches no ``state.sqlite`` table, algorithm version or rebuild path (gate
G6). This module owns the store's schema and every SQL write to it. The schema
is versioned with ``PRAGMA user_version``; M2's ``import-experiment`` reads it
into vault tables.

Two tables mirror vault contracts so M2 can import them unchanged:

- ``judgments`` has ``judgment_ledger``'s columns and append-only rules
  (migration 166); every LLM, verifier and owner verdict lands here.
- ``call_receipts`` has the vault receipt columns plus the §4 disclosure
  record (files sent, hunks, bytes, redactions, context scope) and the cost
  label (``estimated_only`` for subscription transports).
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path
from typing import Any, Iterator

import logging

from learnloop.db.connection import connect
from learnloop.db.migrate import JournalModeSwitchError, switch_to_wal
from learnloop.ids import new_ulid

_LOG = logging.getLogger(__name__)

# 1: the M1 tables. 2: ``pending_commits``, the durable queue of post-commit
# hook entries. Every statement in _SCHEMA is idempotent, so an older store is
# upgraded by running it again.
STORE_SCHEMA_VERSION = 2
STORE_RELATIVE_PATH = Path("projects") / "project_store.sqlite"
PENDING_RELATIVE_PATH = Path("projects") / "pending.jsonl"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS store_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS repos (
    id TEXT PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    remote_url TEXT,
    enrolled_at TEXT NOT NULL,
    capture_since TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0, 1)),
    gate_policy TEXT NOT NULL DEFAULT 'off'
        CHECK(gate_policy IN ('experiment', 'off', 'opt_in', 'default')),
    context_scope TEXT NOT NULL DEFAULT 'diff' CHECK(context_scope IN ('diff', 'repo')),
    secret_pattern_version TEXT NOT NULL,
    ignore_hash TEXT,
    hook_installed INTEGER NOT NULL DEFAULT 0 CHECK(hook_installed IN (0, 1)),
    last_swept_at TEXT,
    last_sweep_error TEXT
);

CREATE TABLE IF NOT EXISTS diffs (
    id TEXT PRIMARY KEY,
    repo_id TEXT NOT NULL REFERENCES repos(id),
    snapshot_kind TEXT NOT NULL CHECK(snapshot_kind IN ('commit', 'working_tree')),
    base_sha TEXT,
    head_sha TEXT,
    patch_id TEXT,
    bundle_hash TEXT NOT NULL,
    files_json TEXT NOT NULL,
    files_touched INTEGER NOT NULL,
    lines_added INTEGER NOT NULL,
    lines_removed INTEGER NOT NULL,
    skipped_files_json TEXT NOT NULL,
    agent TEXT NOT NULL CHECK(agent IN ('claude_code', 'codex', 'other', 'unknown')),
    agent_source TEXT NOT NULL CHECK(agent_source IN ('trailer', 'flag', 'self_report')),
    capture_timing TEXT NOT NULL CHECK(capture_timing IN ('pre_commit', 'post_commit')),
    capture_source TEXT NOT NULL CHECK(capture_source IN ('sweep', 'pending_list', 'accept')),
    capture_trigger TEXT NOT NULL,
    commit_message TEXT NOT NULL,
    committed_at TEXT,
    captured_at TEXT NOT NULL,
    redaction_count INTEGER NOT NULL,
    redactions_json TEXT NOT NULL,
    token_estimate INTEGER NOT NULL,
    truncated INTEGER NOT NULL CHECK(truncated IN (0, 1)),
    excluded_reason TEXT,
    selection_seed INTEGER NOT NULL,
    probe_status TEXT NOT NULL CHECK(probe_status IN (
        'excluded', 'pending', 'generated', 'under_probed', 'failed'
    )),
    generation_attempts INTEGER NOT NULL DEFAULT 0,
    generation_error TEXT,
    generated_at TEXT,
    secret_pattern_version TEXT NOT NULL,
    ignore_hash TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS diffs_commit_identity
    ON diffs(repo_id, head_sha) WHERE snapshot_kind = 'commit';
CREATE UNIQUE INDEX IF NOT EXISTS diffs_worktree_identity
    ON diffs(repo_id, bundle_hash) WHERE snapshot_kind = 'working_tree';
CREATE INDEX IF NOT EXISTS diffs_patch ON diffs(repo_id, patch_id);
CREATE INDEX IF NOT EXISTS diffs_status ON diffs(probe_status, captured_at);

CREATE TABLE IF NOT EXISTS provenance_reports (
    id TEXT PRIMARY KEY,
    diff_id TEXT NOT NULL REFERENCES diffs(id),
    accept_style TEXT CHECK(accept_style IN ('per_hunk', 'all_at_once', 'unknown')),
    usage_tap TEXT CHECK(usage_tap IN ('i_designed_it_typed', 'we_iterated', 'it_designed')),
    source TEXT NOT NULL CHECK(source IN ('self_report')),
    created_at TEXT NOT NULL,
    CHECK(accept_style IS NOT NULL OR usage_tap IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS probes (
    id TEXT PRIMARY KEY,
    diff_id TEXT NOT NULL REFERENCES diffs(id),
    candidate_index INTEGER NOT NULL,
    kind TEXT NOT NULL,
    question TEXT NOT NULL,
    reference_answer TEXT NOT NULL,
    citations_json TEXT NOT NULL,
    rationale_label TEXT CHECK(rationale_label IN ('cited', 'agent_stated')),
    validity TEXT NOT NULL CHECK(validity IN (
        'valid', 'invalid_kind', 'empty', 'no_citation', 'citation_unresolved',
        'quote_mismatch', 'why_uncited'
    )),
    validity_detail TEXT,
    status TEXT NOT NULL CHECK(status IN (
        'invalid', 'pending_closed_book', 'pending_closed_book_grade',
        'rejected_generic', 'survivor'
    )),
    closed_book_answer TEXT,
    closed_book_verdict TEXT,
    closed_book_score REAL,
    selected INTEGER NOT NULL DEFAULT 0 CHECK(selected IN (0, 1)),
    sealed_until TEXT NOT NULL,
    generator_provider TEXT NOT NULL,
    generator_model TEXT NOT NULL,
    generator_prompt_version TEXT NOT NULL,
    closed_book_model TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(diff_id, candidate_index)
);
CREATE INDEX IF NOT EXISTS probes_due ON probes(selected, sealed_until);

CREATE TABLE IF NOT EXISTS probe_responses (
    id TEXT PRIMARY KEY,
    probe_id TEXT NOT NULL UNIQUE REFERENCES probes(id),
    response_kind TEXT NOT NULL CHECK(response_kind IN ('answer', 'dont_know', 'unfair', 'skip')),
    answer TEXT,
    declaration TEXT NOT NULL CHECK(declaration IN ('unassisted', 'looked', 'used_ai')),
    served_at TEXT NOT NULL,
    answered_at TEXT NOT NULL,
    due_at TEXT NOT NULL,
    lateness_seconds INTEGER NOT NULL,
    grade_status TEXT NOT NULL CHECK(grade_status IN ('pending', 'graded', 'failed', 'not_applicable')),
    grade_attempts INTEGER NOT NULL DEFAULT 0,
    score REAL CHECK(score IS NULL OR (score >= 0 AND score <= 1)),
    verdict TEXT,
    feedback TEXT,
    grader_provider TEXT,
    grader_model TEXT,
    grader_prompt_version TEXT,
    graded_at TEXT,
    contested INTEGER NOT NULL DEFAULT 0 CHECK(contested IN (0, 1)),
    adjudicated_score REAL CHECK(adjudicated_score IS NULL OR (adjudicated_score >= 0 AND adjudicated_score <= 1)),
    adjudication_note TEXT,
    adjudicated_at TEXT,
    -- D6: practice evidence only; the repo working tree is an unobserved
    -- exposure channel, so isolation is unknown, never a silent pass.
    evidence_class TEXT NOT NULL DEFAULT 'practice' CHECK(evidence_class = 'practice'),
    exposure_isolation TEXT NOT NULL DEFAULT 'unknown' CHECK(exposure_isolation = 'unknown'),
    CHECK((response_kind = 'answer') = (answer IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS unattributed_commits (
    repo_id TEXT NOT NULL REFERENCES repos(id),
    sha TEXT NOT NULL,
    subject TEXT NOT NULL,
    committed_at TEXT,
    seen_at TEXT NOT NULL,
    resolved_diff_id TEXT REFERENCES diffs(id),
    PRIMARY KEY(repo_id, sha)
);

-- Post-commit hook entries, moved here from projects/pending.jsonl before the
-- file offset advances; each is removed only once its repo was swept, so a
-- repo that is unavailable for a while loses nothing.
CREATE TABLE IF NOT EXISTS pending_commits (
    repo_id TEXT NOT NULL REFERENCES repos(id),
    sha TEXT NOT NULL,
    logged_at TEXT,
    received_at TEXT NOT NULL,
    PRIMARY KEY(repo_id, sha)
);

CREATE TABLE IF NOT EXISTS judgments (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    supersedes_id TEXT REFERENCES judgments(id),
    task TEXT NOT NULL,
    left_kind TEXT NOT NULL,
    left_id TEXT NOT NULL,
    right_kind TEXT,
    right_id TEXT,
    judge TEXT NOT NULL CHECK(judge IN ('llm', 'verifier', 'owner', 'diagnoser', 'learner_card', 'exact_key')),
    judge_model TEXT,
    prompt_version TEXT,
    input_hash TEXT NOT NULL,
    verdict TEXT NOT NULL,
    score REAL,
    rationale TEXT NOT NULL,
    CHECK((right_kind IS NULL) = (right_id IS NULL)),
    CHECK(supersedes_id IS NULL OR supersedes_id != id)
);
CREATE INDEX IF NOT EXISTS judgments_question ON judgments(task, left_kind, left_id);
CREATE TRIGGER IF NOT EXISTS judgments_no_update BEFORE UPDATE ON judgments
BEGIN
    SELECT RAISE(ABORT, 'judgments are append-only');
END;
CREATE TRIGGER IF NOT EXISTS judgments_no_delete BEFORE DELETE ON judgments
BEGIN
    SELECT RAISE(ABORT, 'judgments are append-only');
END;
CREATE TRIGGER IF NOT EXISTS judgments_validate_insert BEFORE INSERT ON judgments
BEGIN
    SELECT RAISE(ABORT, 'judgments are append-only')
      WHERE EXISTS (SELECT 1 FROM judgments WHERE id = NEW.id);
    SELECT RAISE(ABORT, 'llm/diagnoser judgments require nonempty judge_model and prompt_version')
      WHERE NEW.judge IN ('llm', 'diagnoser')
        AND (COALESCE(NEW.judge_model, '') = '' OR COALESCE(NEW.prompt_version, '') = '');
    SELECT RAISE(ABORT, 'supersession must identify the same question')
      WHERE NEW.supersedes_id IS NOT NULL AND NOT EXISTS (
          SELECT 1 FROM judgments
          WHERE id = NEW.supersedes_id AND task = NEW.task
            AND left_kind = NEW.left_kind AND left_id = NEW.left_id
            AND right_kind IS NEW.right_kind AND right_id IS NEW.right_id
      );
END;

CREATE TABLE IF NOT EXISTS call_receipts (
    id TEXT PRIMARY KEY,
    parent_call_id TEXT REFERENCES call_receipts(id),
    owner_kind TEXT NOT NULL,
    owner_id TEXT NOT NULL,
    diff_id TEXT,
    purpose TEXT NOT NULL,
    provider TEXT,
    model TEXT,
    resolved_model TEXT,
    endpoint TEXT,
    prompt_hash TEXT,
    schema_hash TEXT,
    input_text TEXT,
    schema_json TEXT,
    output_text TEXT,
    status TEXT NOT NULL CHECK(status IN ('started', 'completed', 'failed', 'interrupted', 'truncated')),
    started_at TEXT NOT NULL,
    finished_at TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cached_input_tokens INTEGER,
    cache_write_tokens INTEGER,
    reasoning_tokens INTEGER,
    cost REAL,
    provider_response_id TEXT,
    finish_reason TEXT,
    error_type TEXT,
    usage_json TEXT,
    output_budget_tokens INTEGER,
    budget_json TEXT,
    disclosure_json TEXT,
    cost_label TEXT,
    estimated_usd REAL
);
CREATE INDEX IF NOT EXISTS receipts_owner ON call_receipts(owner_kind, owner_id, started_at);
CREATE INDEX IF NOT EXISTS receipts_diff ON call_receipts(diff_id);
"""

_RECEIPT_START_FIELDS = (
    "id", "parent_call_id", "purpose", "provider", "model", "endpoint", "prompt_hash",
    "schema_hash", "input_text", "schema_json", "budget_json", "output_budget_tokens", "started_at",
)
_RECEIPT_FINISH_FIELDS = (
    "status", "finished_at", "input_tokens", "output_tokens", "cached_input_tokens",
    "cache_write_tokens", "reasoning_tokens", "cost", "provider_response_id", "resolved_model",
    "usage_json", "finish_reason", "error_type", "output_text",
)


def store_path(vault_root: Path) -> Path:
    return Path(vault_root) / STORE_RELATIVE_PATH


def pending_path(vault_root: Path) -> Path:
    return Path(vault_root) / PENDING_RELATIVE_PATH


class StoreSchemaError(RuntimeError):
    """The store was written by a newer LearnLoop."""


_JUDGMENT_COLUMNS = (
    "id", "created_at", "supersedes_id", "task", "left_kind", "left_id", "judge",
    "judge_model", "prompt_version", "input_hash", "verdict", "score", "rationale",
)


def _insert_judgment(connection: sqlite3.Connection, judgment: dict[str, Any]) -> str:
    """Insert one ``judgments`` row on ``connection`` (inside its transaction)."""

    row = {**judgment, "id": judgment.get("id") or new_ulid()}
    connection.execute(
        f"INSERT INTO judgments ({', '.join(_JUDGMENT_COLUMNS)}) "
        f"VALUES ({', '.join('?' for _ in _JUDGMENT_COLUMNS)})",
        tuple(row.get(column) for column in _JUDGMENT_COLUMNS),
    )
    return str(row["id"])


class ProjectStore:
    """Short transactions over the standalone store; owns every SQL write."""

    def __init__(self, path: Path, *, busy_timeout_ms: int | None = None) -> None:
        self.path = Path(path)
        self._busy_timeout_ms = busy_timeout_ms
        self._ensure_schema()

    @classmethod
    def for_vault(cls, vault_root: Path, *, busy_timeout_ms: int | None = None) -> "ProjectStore":
        return cls(store_path(vault_root), busy_timeout_ms=busy_timeout_ms)

    @classmethod
    def existing(cls, vault_root: Path, *, busy_timeout_ms: int | None = None) -> "ProjectStore | None":
        """Open the store only if it exists; never create it."""

        path = store_path(vault_root)
        return cls(path, busy_timeout_ms=busy_timeout_ms) if path.is_file() else None

    def _connect(self) -> sqlite3.Connection:
        connection = connect(self.path)
        if self._busy_timeout_ms is not None:
            connection.execute(f"PRAGMA busy_timeout = {int(self._busy_timeout_ms)}")
        return connection

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        with closing(self._connect()) as connection:
            try:
                yield connection
                connection.commit()
            except BaseException:
                connection.rollback()
                raise

    def _ensure_schema(self) -> None:
        with closing(self._connect()) as connection:
            version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            if version > STORE_SCHEMA_VERSION:
                raise StoreSchemaError(
                    f"{self.path} has store schema {version}; this LearnLoop knows {STORE_SCHEMA_VERSION}"
                )
            if version < STORE_SCHEMA_VERSION:
                connection.executescript(_SCHEMA)
                connection.execute(f"PRAGMA user_version = {STORE_SCHEMA_VERSION}")
                connection.commit()
            # ADR-015: WAL + synchronous=FULL, as for the vault database. The
            # switch is idempotent and a no-op where the linked SQLite forbids it;
            # a busy store keeps its mode and is switched on a later open.
            try:
                switch_to_wal(connection, self.path)
            except JournalModeSwitchError as exc:
                _LOG.warning("Project store stays in rollback mode for now: %s", exc)

    # --- meta -----------------------------------------------------------------

    def meta(self, key: str) -> str | None:
        with self.connection() as connection:
            row = connection.execute("SELECT value FROM store_meta WHERE key = ?", (key,)).fetchone()
        return None if row is None else str(row["value"])

    def set_meta(self, key: str, value: str) -> None:
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO store_meta(key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )

    # --- repos ----------------------------------------------------------------

    def repos(self, *, enabled_only: bool = False) -> list[dict[str, Any]]:
        query = "SELECT * FROM repos" + (" WHERE enabled = 1" if enabled_only else "") + " ORDER BY enrolled_at, id"
        with self.connection() as connection:
            return [dict(row) for row in connection.execute(query)]

    def repo(self, repo_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM repos WHERE id = ?", (repo_id,)).fetchone()
        return None if row is None else dict(row)

    def repo_by_path(self, path: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM repos WHERE path = ?", (path,)).fetchone()
        return None if row is None else dict(row)

    def enroll_repo(self, row: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        """Insert a repo, or re-enable the existing one. Returns (row, created)."""

        with self.connection() as connection:
            existing = connection.execute("SELECT * FROM repos WHERE path = ?", (row["path"],)).fetchone()
            if existing is not None:
                connection.execute(
                    "UPDATE repos SET enabled = 1, remote_url = ?, context_scope = ? WHERE id = ?",
                    (row.get("remote_url"), row["context_scope"], existing["id"]),
                )
                updated = connection.execute("SELECT * FROM repos WHERE id = ?", (existing["id"],)).fetchone()
                return dict(updated), False
            columns = (
                "id", "path", "name", "remote_url", "enrolled_at", "capture_since",
                "context_scope", "secret_pattern_version", "ignore_hash",
            )
            connection.execute(
                f"INSERT INTO repos ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})",
                tuple(row.get(column) for column in columns),
            )
            created = connection.execute("SELECT * FROM repos WHERE id = ?", (row["id"],)).fetchone()
            return dict(created), True

    def set_repo_enabled(self, repo_id: str, enabled: bool) -> None:
        with self.connection() as connection:
            connection.execute("UPDATE repos SET enabled = ? WHERE id = ?", (int(enabled), repo_id))

    def set_hook_installed(self, repo_id: str, installed: bool) -> None:
        with self.connection() as connection:
            connection.execute("UPDATE repos SET hook_installed = ? WHERE id = ?", (int(installed), repo_id))

    def record_repo_sweep(self, repo_id: str, *, swept_at: str, error: str | None) -> None:
        with self.connection() as connection:
            connection.execute(
                "UPDATE repos SET last_swept_at = ?, last_sweep_error = ? WHERE id = ?",
                (swept_at, error, repo_id),
            )

    # --- diffs ----------------------------------------------------------------

    def known_commit_shas(self, repo_id: str) -> set[str]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT head_sha FROM diffs WHERE repo_id = ? AND snapshot_kind = 'commit'",
                (repo_id,),
            )
            return {str(row["head_sha"]) for row in rows}

    def diff_with_patch_id(self, repo_id: str, patch: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM diffs WHERE repo_id = ? AND patch_id = ? ORDER BY captured_at LIMIT 1",
                (repo_id, patch),
            ).fetchone()
        return None if row is None else dict(row)

    def diff_for_commit(self, repo_id: str, sha: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM diffs WHERE repo_id = ? AND snapshot_kind = 'commit' AND head_sha = ?",
                (repo_id, sha),
            ).fetchone()
        return None if row is None else dict(row)

    def diff_for_worktree_bundle(self, repo_id: str, bundle_hash: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM diffs WHERE repo_id = ? AND snapshot_kind = 'working_tree' AND bundle_hash = ?",
                (repo_id, bundle_hash),
            ).fetchone()
        return None if row is None else dict(row)

    def insert_diff(self, row: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        """Insert a capture; a concurrent duplicate returns the stored row."""

        columns = (
            "id", "repo_id", "snapshot_kind", "base_sha", "head_sha", "patch_id", "bundle_hash",
            "files_json", "files_touched", "lines_added", "lines_removed", "skipped_files_json",
            "agent", "agent_source", "capture_timing", "capture_source", "capture_trigger",
            "commit_message", "committed_at", "captured_at", "redaction_count", "redactions_json",
            "token_estimate", "truncated", "excluded_reason", "selection_seed", "probe_status",
            "secret_pattern_version", "ignore_hash",
        )
        with self.connection() as connection:
            cursor = connection.execute(
                f"INSERT OR IGNORE INTO diffs ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})",
                tuple(row.get(column) for column in columns),
            )
            created = cursor.rowcount == 1
            if created:
                stored = connection.execute("SELECT * FROM diffs WHERE id = ?", (row["id"],)).fetchone()
            elif row["snapshot_kind"] == "commit":
                stored = connection.execute(
                    "SELECT * FROM diffs WHERE repo_id = ? AND snapshot_kind = 'commit' AND head_sha = ?",
                    (row["repo_id"], row["head_sha"]),
                ).fetchone()
            else:
                stored = connection.execute(
                    "SELECT * FROM diffs WHERE repo_id = ? AND snapshot_kind = 'working_tree' AND bundle_hash = ?",
                    (row["repo_id"], row["bundle_hash"]),
                ).fetchone()
            return dict(stored), created

    def diff(self, diff_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM diffs WHERE id = ?", (diff_id,)).fetchone()
        return None if row is None else dict(row)

    def diffs(self, *, repo_id: str | None = None, probe_status: str | None = None) -> list[dict[str, Any]]:
        clauses, params = [], []
        if repo_id is not None:
            clauses.append("repo_id = ?")
            params.append(repo_id)
        if probe_status is not None:
            clauses.append("probe_status = ?")
            params.append(probe_status)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        with self.connection() as connection:
            return [
                dict(row)
                for row in connection.execute(f"SELECT * FROM diffs{where} ORDER BY captured_at, id", params)
            ]

    def record_generation_failure(self, diff_id: str, *, error: str, max_attempts: int) -> None:
        with self.connection() as connection:
            connection.execute(
                "UPDATE diffs SET generation_attempts = generation_attempts + 1, generation_error = ?, "
                "probe_status = CASE WHEN generation_attempts + 1 >= ? THEN 'failed' ELSE probe_status END "
                "WHERE id = ? AND probe_status = 'pending'",
                (error[:500], max_attempts, diff_id),
            )

    def finish_generation(self, diff_id: str, *, status: str, generated_at: str) -> None:
        with self.connection() as connection:
            connection.execute(
                "UPDATE diffs SET probe_status = ?, generated_at = ?, generation_error = NULL WHERE id = ?",
                (status, generated_at, diff_id),
            )

    def retry_failed_generation(self, diff_id: str) -> bool:
        """Back to ``pending`` with fresh attempts; probes from finished stages are kept."""

        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE diffs SET probe_status = 'pending', generation_attempts = 0 "
                "WHERE id = ? AND probe_status = 'failed'",
                (diff_id,),
            )
            return cursor.rowcount == 1

    # --- provenance -------------------------------------------------------------

    def add_provenance(self, row: dict[str, Any]) -> None:
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO provenance_reports (id, diff_id, accept_style, usage_tap, source, created_at) "
                "VALUES (?, ?, ?, ?, 'self_report', ?)",
                (row["id"], row["diff_id"], row.get("accept_style"), row.get("usage_tap"), row["created_at"]),
            )

    def latest_provenance(self) -> dict[str, dict[str, Any]]:
        """Per diff, the newest self-reported accept style and usage tap."""

        latest: dict[str, dict[str, Any]] = {}
        with self.connection() as connection:
            for row in connection.execute("SELECT * FROM provenance_reports ORDER BY created_at, id"):
                entry = latest.setdefault(str(row["diff_id"]), {})
                if row["accept_style"] is not None:
                    entry["accept_style"] = row["accept_style"]
                if row["usage_tap"] is not None:
                    entry["usage_tap"] = row["usage_tap"]
        return latest

    # --- probes ---------------------------------------------------------------

    def probes_for_diff(self, diff_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            return [
                dict(row)
                for row in connection.execute(
                    "SELECT * FROM probes WHERE diff_id = ? ORDER BY candidate_index", (diff_id,)
                )
            ]

    def insert_probe_candidates(self, rows: list[dict[str, Any]], judgments: list[dict[str, Any]] = ()) -> None:
        """Insert a diff's candidates and their validity verdicts in one transaction."""

        columns = (
            "id", "diff_id", "candidate_index", "kind", "question", "reference_answer",
            "citations_json", "rationale_label", "validity", "validity_detail", "status",
            "sealed_until", "generator_provider", "generator_model", "generator_prompt_version",
            "created_at",
        )
        with self.connection() as connection:
            connection.executemany(
                f"INSERT INTO probes ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})",
                [tuple(row.get(column) for column in columns) for row in rows],
            )
            for judgment in judgments:
                _insert_judgment(connection, judgment)

    def record_closed_book_answers(self, answers: dict[str, str], *, model: str) -> None:
        with self.connection() as connection:
            connection.executemany(
                "UPDATE probes SET closed_book_answer = ?, closed_book_model = ?, "
                "status = 'pending_closed_book_grade' WHERE id = ? AND status = 'pending_closed_book'",
                [(answer, model, probe_id) for probe_id, answer in answers.items()],
            )

    def record_closed_book_grades(self, grades: list[dict[str, Any]]) -> int:
        """Each ``{probe_id, verdict, score, generic, judgment}`` with its judgment, atomically.

        A probe no longer awaiting its closed-book grade (another run got
        there first) gets neither the verdict nor a second judgment.
        Returns how many verdicts were recorded.
        """

        recorded = 0
        with self.connection() as connection:
            for grade in grades:
                cursor = connection.execute(
                    "UPDATE probes SET closed_book_verdict = ?, closed_book_score = ?, status = ? "
                    "WHERE id = ? AND status = 'pending_closed_book_grade'",
                    (grade["verdict"], grade["score"], "rejected_generic" if grade["generic"] else "survivor",
                     grade["probe_id"]),
                )
                if cursor.rowcount == 1:
                    _insert_judgment(connection, grade["judgment"])
                    recorded += 1
        return recorded

    def select_probes(self, probe_ids: list[str]) -> None:
        with self.connection() as connection:
            connection.executemany(
                "UPDATE probes SET selected = 1 WHERE id = ? AND status = 'survivor'",
                [(probe_id,) for probe_id in probe_ids],
            )

    def probe(self, probe_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM probes WHERE id = ?", (probe_id,)).fetchone()
        return None if row is None else dict(row)

    def all_probes(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            return [dict(row) for row in connection.execute("SELECT * FROM probes ORDER BY created_at, id")]

    def due_probes(self, now_iso: str, *, repo_id: str | None = None) -> list[dict[str, Any]]:
        """Selected probes past their seal with no response, oldest first."""

        query = (
            "SELECT probes.*, diffs.repo_id AS repo_id FROM probes "
            "JOIN diffs ON diffs.id = probes.diff_id "
            "LEFT JOIN probe_responses ON probe_responses.probe_id = probes.id "
            "WHERE probes.selected = 1 AND probes.sealed_until <= ? AND probe_responses.id IS NULL"
        )
        params: list[Any] = [now_iso]
        if repo_id is not None:
            query += " AND diffs.repo_id = ?"
            params.append(repo_id)
        query += " ORDER BY probes.sealed_until, diffs.captured_at, probes.candidate_index"
        with self.connection() as connection:
            return [dict(row) for row in connection.execute(query, params)]

    # --- responses --------------------------------------------------------------

    def insert_response(self, row: dict[str, Any], judgment: dict[str, Any] | None = None) -> bool:
        """Insert a response (and the owner verdict it carries) in one transaction."""

        columns = (
            "id", "probe_id", "response_kind", "answer", "declaration", "served_at", "answered_at",
            "due_at", "lateness_seconds", "grade_status",
        )
        with self.connection() as connection:
            cursor = connection.execute(
                f"INSERT OR IGNORE INTO probe_responses ({', '.join(columns)}) "
                f"VALUES ({', '.join('?' for _ in columns)})",
                tuple(row.get(column) for column in columns),
            )
            inserted = cursor.rowcount == 1
            if inserted and judgment is not None:
                _insert_judgment(connection, judgment)
            return inserted

    def response(self, response_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM probe_responses WHERE id = ?", (response_id,)).fetchone()
        return None if row is None else dict(row)

    def response_for_probe(self, probe_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM probe_responses WHERE probe_id = ?", (probe_id,)
            ).fetchone()
        return None if row is None else dict(row)

    def responses(self, *, grade_status: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM probe_responses"
        params: tuple[Any, ...] = ()
        if grade_status is not None:
            query += " WHERE grade_status = ?"
            params = (grade_status,)
        with self.connection() as connection:
            return [dict(row) for row in connection.execute(query + " ORDER BY answered_at, id", params)]

    def record_grade(self, response_id: str, *, score: float, verdict: str, feedback: str,
                     provider: str, model: str, prompt_version: str, graded_at: str,
                     judgment: dict[str, Any]) -> bool:
        """The grade and its judgment, atomically; ``False`` if the answer was no longer pending.

        Only a pending answer takes a grade, so two graders racing on one
        answer can never leave two outcomes or two unsuperseded judgments:
        the loser writes nothing and reads back the stored grade.
        """

        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE probe_responses SET grade_status = 'graded', score = ?, verdict = ?, feedback = ?, "
                "grader_provider = ?, grader_model = ?, grader_prompt_version = ?, graded_at = ?, "
                "grade_attempts = grade_attempts + 1 WHERE id = ? AND grade_status = 'pending'",
                (score, verdict, feedback, provider, model, prompt_version, graded_at, response_id),
            )
            if cursor.rowcount != 1:
                return False
            _insert_judgment(connection, judgment)
            return True

    def retry_failed_grade(self, response_id: str) -> bool:
        """Back to ``pending`` with fresh attempts; the answer and receipts are kept."""

        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE probe_responses SET grade_status = 'pending', grade_attempts = 0 "
                "WHERE id = ? AND grade_status = 'failed'",
                (response_id,),
            )
            return cursor.rowcount == 1

    def record_grade_failure(self, response_id: str, *, max_attempts: int) -> None:
        with self.connection() as connection:
            connection.execute(
                "UPDATE probe_responses SET grade_attempts = grade_attempts + 1, "
                "grade_status = CASE WHEN grade_attempts + 1 >= ? THEN 'failed' ELSE 'pending' END "
                "WHERE id = ? AND grade_status = 'pending'",
                (max_attempts, response_id),
            )

    def record_adjudication(
        self, response_id: str, *, score: float, note: str, adjudicated_at: str, judgment: dict[str, Any],
    ) -> bool:
        """The owner's adjudication and its judgment, atomically.

        The judgment supersedes the response's latest grade judgment, read in
        the same transaction. ``False`` when the response is not graded.
        """

        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE probe_responses SET contested = 1, adjudicated_score = ?, adjudication_note = ?, "
                "adjudicated_at = ? WHERE id = ? AND grade_status = 'graded'",
                (score, note, adjudicated_at, response_id),
            )
            if cursor.rowcount != 1:
                return False
            prior = connection.execute(
                "SELECT id FROM judgments WHERE task = ? AND left_kind = ? AND left_id = ? "
                "ORDER BY created_at DESC, id DESC LIMIT 1",
                (judgment["task"], judgment["left_kind"], response_id),
            ).fetchone()
            _insert_judgment(connection, {**judgment, "supersedes_id": None if prior is None else prior["id"]})
            return True

    # --- the post-commit pending queue -----------------------------------------

    def enqueue_pending(self, entries: list[dict[str, Any]], *, offset: int, received_at: str) -> int:
        """Queue hook entries and advance the pending-file offset in one transaction."""

        with self.connection() as connection:
            added = 0
            for entry in entries:
                cursor = connection.execute(
                    "INSERT OR IGNORE INTO pending_commits (repo_id, sha, logged_at, received_at) VALUES (?, ?, ?, ?)",
                    (entry["repo_id"], entry["sha"], entry.get("at"), received_at),
                )
                added += cursor.rowcount
            connection.execute(
                "INSERT INTO store_meta(key, value) VALUES ('pending_offset', ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (str(offset),),
            )
        return added

    def pending_commits(self, repo_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM pending_commits"
        params: tuple[Any, ...] = ()
        if repo_id is not None:
            query += " WHERE repo_id = ?"
            params = (repo_id,)
        with self.connection() as connection:
            return [dict(row) for row in connection.execute(query + " ORDER BY received_at, rowid", params)]

    def dequeue_pending(self, repo_id: str, sha: str) -> None:
        with self.connection() as connection:
            connection.execute("DELETE FROM pending_commits WHERE repo_id = ? AND sha = ?", (repo_id, sha))

    # --- unattributed commits ---------------------------------------------------

    def note_unattributed(self, row: dict[str, Any]) -> bool:
        with self.connection() as connection:
            cursor = connection.execute(
                "INSERT OR IGNORE INTO unattributed_commits (repo_id, sha, subject, committed_at, seen_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (row["repo_id"], row["sha"], row["subject"], row.get("committed_at"), row["seen_at"]),
            )
            return cursor.rowcount == 1

    def resolve_unattributed(self, repo_id: str, sha: str, diff_id: str) -> None:
        with self.connection() as connection:
            connection.execute(
                "UPDATE unattributed_commits SET resolved_diff_id = ? WHERE repo_id = ? AND sha = ?",
                (diff_id, repo_id, sha),
            )

    def unattributed(self, *, unresolved_only: bool = True) -> list[dict[str, Any]]:
        query = "SELECT * FROM unattributed_commits"
        if unresolved_only:
            query += " WHERE resolved_diff_id IS NULL"
        with self.connection() as connection:
            return [dict(row) for row in connection.execute(query + " ORDER BY seen_at DESC, sha")]

    # --- judgments (judgment_ledger mirror) -------------------------------------

    def append_judgment(
        self,
        *,
        task: str,
        left_kind: str,
        left_id: str,
        judge: str,
        input_hash: str,
        verdict: str,
        rationale: str,
        created_at: str,
        score: float | None = None,
        judge_model: str | None = None,
        prompt_version: str | None = None,
        supersedes_id: str | None = None,
    ) -> str:
        with self.connection() as connection:
            return _insert_judgment(
                connection,
                {
                    "created_at": created_at, "supersedes_id": supersedes_id, "task": task,
                    "left_kind": left_kind, "left_id": left_id, "judge": judge, "judge_model": judge_model,
                    "prompt_version": prompt_version, "input_hash": input_hash, "verdict": verdict,
                    "score": score, "rationale": rationale,
                },
            )

    def judgments(self, *, task: str | None = None, left_id: str | None = None) -> list[dict[str, Any]]:
        clauses, params = [], []
        if task is not None:
            clauses.append("task = ?")
            params.append(task)
        if left_id is not None:
            clauses.append("left_id = ?")
            params.append(left_id)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        with self.connection() as connection:
            return [
                dict(row)
                for row in connection.execute(f"SELECT * FROM judgments{where} ORDER BY created_at, id", params)
            ]

    # --- model call receipts ----------------------------------------------------

    def record_model_event(
        self,
        action: str,
        event: dict[str, Any],
        *,
        owner_kind: str,
        owner_id: str,
        diff_id: str | None = None,
        disclosure: dict[str, Any] | None = None,
        cost_label: str | None = None,
    ) -> None:
        """The ``observe_model_calls`` sink: a durable start, then a finish."""

        with self.connection() as connection:
            if action == "start":
                is_root = event.get("parent_call_id") is None
                connection.execute(
                    f"INSERT INTO call_receipts ({', '.join(_RECEIPT_START_FIELDS)}, owner_kind, owner_id, "
                    "diff_id, disclosure_json, cost_label, status) "
                    f"VALUES ({', '.join('?' for _ in _RECEIPT_START_FIELDS)}, ?, ?, ?, ?, ?, 'started')",
                    (
                        *(event.get(field) for field in _RECEIPT_START_FIELDS),
                        owner_kind,
                        owner_id,
                        diff_id,
                        json.dumps(disclosure, sort_keys=True) if (disclosure is not None and is_root) else None,
                        cost_label,
                    ),
                )
            elif action == "finish":
                connection.execute(
                    f"UPDATE call_receipts SET {', '.join(f'{field} = ?' for field in _RECEIPT_FINISH_FIELDS)} "
                    "WHERE id = ? AND status = 'started'",
                    (*(event.get(field) for field in _RECEIPT_FINISH_FIELDS), event["id"]),
                )
            else:
                raise ValueError(f"Unknown model receipt action: {action}")

    def set_receipt_estimate(self, call_id: str, estimated_usd: float | None) -> None:
        with self.connection() as connection:
            connection.execute(
                "UPDATE call_receipts SET estimated_usd = ? WHERE id = ?", (estimated_usd, call_id)
            )

    def receipts(self, *, diff_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM call_receipts"
        params: tuple[Any, ...] = ()
        if diff_id is not None:
            query += " WHERE diff_id = ?"
            params = (diff_id,)
        with self.connection() as connection:
            return [dict(row) for row in connection.execute(query + " ORDER BY started_at, id", params)]


__all__ = [
    "PENDING_RELATIVE_PATH",
    "ProjectStore",
    "STORE_RELATIVE_PATH",
    "STORE_SCHEMA_VERSION",
    "StoreSchemaError",
    "pending_path",
    "store_path",
]
