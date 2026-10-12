"""Shared setup for the Slice 1 M2 live-split tests.

A small graded multi-LO vault (``diagnosis_split_helpers``) switched to the
split successor, real ``complete_attempt_with_ai_required`` submissions with
the deterministic M1 fakes, and the job drain. No network, no paid call.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from learnloop.attempts.attempts import AttemptDraft, complete_attempt_with_ai_required
from learnloop.attempts.post_attempt import run_post_attempt_pipeline
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.diagnosis.split.jobs import drain
from learnloop.vault.loader import load_vault

from tests.diagnosis_fakes import ReviewFakeClient
from tests.diagnosis_split_helpers import at, build_diagnosis_vault, seed_history
from tests.helpers import set_algorithm_version


class ReadyRuntime:
    ready = True
    status = "ready"
    active_provider = "fake"
    provider_type = "codex_sdk"
    model = "fake-model"
    provider_revision = None


def append_config(root: Path, text: str) -> None:
    path = root / "learnloop.toml"
    path.write_text(path.read_text(encoding="utf-8") + "\n" + text.strip() + "\n", encoding="utf-8")


def enable_embeddings(root: Path) -> None:
    """Turn on the template's (off) embedding switches in place."""

    path = root / "learnloop.toml"
    text = path.read_text(encoding="utf-8")
    head, marker, tail = text.partition("[embedding]\n")
    assert marker, "the vault config has no [embedding] section"
    tail = tail.replace("enabled = false", "enabled = true", 1).replace(
        "backfill_enabled = false", "backfill_enabled = true", 1
    )
    path.write_text(head + marker + tail, encoding="utf-8")


def split_vault(tmp_path: Path, *, version: str = "mvp-0.10", config: str = "", seed: bool = True):
    """(paths, vault, repository) for a graded vault at ``version``."""

    paths = build_diagnosis_vault(tmp_path / "vault")
    if seed:
        seed_history(paths)
    set_algorithm_version(paths, version)
    if config:
        append_config(paths.root, config)
    return paths, load_vault(paths.root), Repository(paths.sqlite_path)


def submit(
    vault,
    repository: Repository,
    client: Any,
    *,
    item_id: str = "pi_svd_compute_001",
    answer: str = "A = U Sigma V wrong",
    when: datetime | None = None,
    session_id: str | None = None,
    pipeline: bool = True,
):
    """One graded practice attempt through the real door (+ the sync pipeline)."""

    clock = FrozenClock(when) if when is not None else None
    draft = AttemptDraft(
        practice_item_id=item_id,
        learner_answer_md=answer,
        attempt_type="independent_attempt",
        session_id=session_id,
    )
    result = complete_attempt_with_ai_required(
        vault, repository, draft, runtime=ReadyRuntime(), ai_client=client, clock=clock
    )
    if pipeline:
        run_post_attempt_pipeline(vault, repository, result=result, session_id=session_id, clock=clock)
    return result


def drain_jobs(vault, repository: Repository, client: Any, *, embedding: Any = None, clock=None, **kwargs):
    return drain(
        vault,
        repository,
        client_factory=lambda: client,
        embedding_factory=lambda: embedding,
        clock=clock,
        **kwargs,
    )


def fake_client(**kwargs) -> ReviewFakeClient:
    return ReviewFakeClient(**kwargs)


class CitingFake(ReviewFakeClient):
    """Cites every prior same-LO failure (S4-valid) and names a prerequisite gap."""

    def _diagnosis(self, request, context):
        from learnloop.diagnosis.split.contract import (
            Citation,
            PatternClaim,
            PrerequisiteGapHypothesis,
        )

        result = super()._diagnosis(request, context)
        current = context["current_attempt"]
        history = context.get("history") or context.get("failure_history") or []
        same_lo = [
            row
            for row in history
            if row.get("outcome") == "non_pass"
            and row.get("learning_object_id") == current["learning_object_id"]
            and row.get("first_divergence_quotes")
        ]
        claims = [
            PatternClaim(
                hypothesis_ref="cause:0:0",
                relation="same_mechanism",
                cited=[Citation(attempt_id=row["attempt_id"], quote=row["first_divergence_quotes"][0]) for row in same_lo],
            )
        ] if same_lo and result.event_diagnoses else []
        prerequisites = [
            row["learning_object_id"]
            for row in (context.get("neighborhood") or {}).get("learning_objects") or []
            if row.get("relation") == "prerequisite"
        ]
        gaps = [
            PrerequisiteGapHypothesis(
                prerequisite_ref=prerequisites[0],
                suggested_discriminator_md="Transpose a 2x2 matrix.",
            )
        ] if prerequisites else []
        return result.model_copy(
            update={
                "pattern_claims": claims,
                "prerequisite_gap_hypotheses": gaps,
                "evidence_attempt_ids": [row["attempt_id"] for row in same_lo],
            }
        )


__all__ = [
    "CitingFake",
    "ReadyRuntime",
    "append_config",
    "enable_embeddings",
    "at",
    "drain_jobs",
    "fake_client",
    "split_vault",
    "submit",
]
