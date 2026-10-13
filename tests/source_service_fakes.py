"""Fakes and builders for the canonical-sources service tests (no network).

``build_service_vault`` is T6's retrieval vault (three LOs, six facets, a
textbook and an exam in one source set) with the practice index on. Every
paid role is answered by a deterministic fake from the prompt's own JSON:
results are plumbing checks, never evidence about quality.
"""
from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from tests.source_retrieval_fakes import build_retrieval_vault


def build_service_vault(root: Path, *, embeddings: bool = False) -> tuple[VaultPaths, Repository]:
    return build_retrieval_vault(root, embeddings=embeddings)


def set_config(paths: VaultPaths, section: str, **values: Any) -> None:
    """Append (or extend) a TOML section in the vault's learnloop.toml."""

    config = paths.root / "learnloop.toml"
    text = config.read_text(encoding="utf-8")
    lines = []
    for key, value in values.items():
        if isinstance(value, bool):
            rendered = "true" if value else "false"
        elif isinstance(value, str):
            rendered = json.dumps(value)
        else:
            rendered = repr(value)
        lines.append(f"{key} = {rendered}")
    header = f"[{section}]"
    if f"\n{header}\n" in text:
        text = text.replace(f"\n{header}\n", f"\n{header}\n" + "\n".join(lines) + "\n", 1)
    else:
        text = text.rstrip("\n") + f"\n\n{header}\n" + "\n".join(lines) + "\n"
    config.write_text(text, encoding="utf-8")


def insert_question(repository: Repository, *, context: str, question: str,
                    practice_item_id: str | None = None, attempt_id: str | None = None,
                    note_id: str | None = None, facets: list[str] | None = None,
                    source_context: dict[str, Any] | None = None,
                    answered: bool = True, event_id: str | None = None) -> str:
    return repository.insert_question_event({
        "id": event_id, "context": context, "question_md": question,
        "practice_item_id": practice_item_id, "attempt_id": attempt_id, "note_id": note_id,
        "answer_md": "an answer" if answered else None, "facets": facets or [],
        "answer_status": "answered" if answered else "pending",
        "source_context": source_context,
    })


def rpc(messages: list[dict]) -> list[dict]:
    from learnloop_sidecar.server import serve

    stdin = io.StringIO("".join(json.dumps(message) + "\n" for message in messages))
    stdout = io.StringIO()
    serve(stdin, stdout)
    return [json.loads(line) for line in stdout.getvalue().splitlines()]


def init_message(root: Path) -> dict:
    return {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(root)}}


def call(root: Path, method: str, params: dict[str, Any]) -> dict:
    responses = rpc([init_message(root), {"jsonrpc": "2.0", "id": 2, "method": method, "params": params}])
    return responses[1]


def loaded(paths: VaultPaths):
    return load_vault(paths.root)


def table_counts(repository: Repository, tables: list[str]) -> dict[str, int]:
    with repository.connection() as connection:
        return {table: connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                for table in tables}


#: The learning-state tables G1 says a tool never writes.
LEARNING_STATE_TABLES = [
    "practice_attempts", "grading_evidence", "error_events", "facet_mastery_state",
    "fsrs_state", "scheduler_candidate_log", "attention_blocks", "daily_plans",
]


def learning_state_tables(repository: Repository) -> list[str]:
    with repository.connection() as connection:
        names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    return [table for table in LEARNING_STATE_TABLES if table in names]
