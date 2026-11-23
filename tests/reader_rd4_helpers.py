"""Builders shared by the Reader workbench v2 scratchpad tests (RD4: emission, submission, carried questions,
proposals): a basic vault, pad ops written the way the client writes them, and readers of what the gap pipeline
holds. Every model is a fake."""

from __future__ import annotations

from contextlib import closing
from typing import Any

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.diagnosis.text_gaps.pipeline import PipelineClients
from learnloop.pads import emission
from learnloop.tutor.ai_contracts import LearnerGap
from learnloop.vault.loader import load_vault
from tests.desk_helpers import Batches
from tests.helpers import append_config_toml, create_basic_vault
from tests.text_gap_fakes import GapLLMFake

PAD = "pad_1"


def pad_vault(tmp_path: Any, config: str = "") -> tuple[Any, Repository, Batches]:
    paths = create_basic_vault(tmp_path / "vault")
    if config:
        append_config_toml(paths.root, config)
    repository = Repository(paths.sqlite_path)
    return paths, repository, Batches(repository)


def vault(paths: Any) -> Any:
    return load_vault(paths.root)


def create_pad(batches: Batches, pad_id: str = PAD, kind: str = "running", **extra: Any) -> dict[str, Any]:
    return batches.pad(pad_id, {"op": "create_pad", "kind": kind, "title": "notes", **extra})


def insert(block_id: str, body: str, *, kind: str = "text", provenance: str = "learner", position: str = "a0",
           version_id: str | None = None, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    op: dict[str, Any] = {"op": "insert_block", "block_id": block_id, "kind": kind, "provenance": provenance,
                          "position_key": position, "body_md": body, "payload": payload or {}}
    if version_id is not None:
        op["version_id"] = version_id
    return op


def edit(block_id: str, head: str, body: str, version_id: str | None = None) -> dict[str, Any]:
    op = {"op": "edit_block", "block_id": block_id, "expected_head": head, "body_md": body}
    if version_id is not None:
        op["version_id"] = version_id
    return op


def head_of(reply: dict[str, Any], block_id: str) -> str:
    return next(head["head_version_id"] for head in reply["heads"] if head["block_id"] == block_id)


def settle(paths: Any, repository: Repository, reply: dict[str, Any]) -> emission.Settled:
    """What the sidecar's ``pad.apply`` does once the batch committed."""

    return emission.settle_blocks(vault(paths), repository, [head["block_id"] for head in reply["heads"]])


def apply_and_settle(paths: Any, repository: Repository, batches: Batches, pad_id: str,
                     *ops: dict[str, Any]) -> dict[str, Any]:
    reply = batches.pad(pad_id, *ops)
    settle(paths, repository, reply)
    return reply


def rows(repository: Repository, sql: str, params: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return [tuple(row) for row in connection.execute(sql, params)]


def pad_jobs(repository: Repository) -> dict[str, str]:
    """Each ``pad_text`` job's source (a block version) and state."""

    return dict(rows(repository, "SELECT source_id, state FROM learner_text_gap_jobs WHERE source_kind = 'pad_text'"))


def pad_gaps(repository: Repository) -> dict[str, tuple[str, str]]:
    """Each ``pad_text`` gap's source version, its kind and action."""

    return {row[0]: (row[1], row[2]) for row in rows(
        repository, "SELECT source_id, kind, action FROM learner_text_gaps WHERE source_kind = 'pad_text'")}


def pad_reversals(repository: Repository) -> dict[str, str]:
    """Each reversed ``pad_text`` gap's source version and its reversal."""

    return dict(rows(repository, "SELECT g.source_id, r.reversal FROM learner_text_gap_reversals AS r "
                                 "JOIN learner_text_gaps AS g ON g.id = r.gap_id WHERE g.source_kind = 'pad_text'"))


def gap_clients(reading: LearnerGap | None = None) -> tuple[PipelineClients, GapLLMFake]:
    llm = GapLLMFake(reading=reading or LearnerGap(kind="none", prerequisite_name=None, prerequisite_line=None,
                                                   belief_statement=None))
    return PipelineClients(judge=lambda: llm, reader=lambda: llm, decider=None, drafter=lambda: llm, tutor=None,
                           embedder=None), llm


def read_queued(paths: Any, repository: Repository, clients: PipelineClients) -> list[Any]:
    from learnloop.diagnosis.text_gaps.jobs import run_pending

    return run_pending(paths.root, repository, owner="test", clients=clients)
