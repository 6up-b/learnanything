"""Evaluate a whole-vault rebuild without writing to the live database.

The shadow run uses SQLite's backup API to make a consistent scratch database,
applies candidate in-memory config overrides, and invokes the ordinary derived
state rebuild umbrella against that copy.  The live database is attached
read-only and its SHA-256 is checked before and after the operation.  Vault
files and the live database are never migrated or synchronized here.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from contextlib import closing
from copy import deepcopy
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping, Sequence

from pydantic import ValidationError

from learnloop.config import LearnLoopConfig
from learnloop.db.repositories import Repository
from learnloop.substrate.rebuild_orchestrator import (
    OrchestratedRebuildResult,
    rebuild_all_derived_state,
)
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths


class ShadowRebuildError(RuntimeError):
    """Base error for a shadow rebuild that could not be evaluated safely."""


class ConfigOverrideError(ShadowRebuildError, ValueError):
    """A ``--set dotted.path=value`` assignment is malformed or invalid."""


class LiveDatabaseChangedError(ShadowRebuildError):
    """The live SQLite file changed while a shadow rebuild was running."""

    def __init__(self, before: str, after: str):
        self.before = before
        self.after = after
        super().__init__(
            "live database changed during shadow rebuild "
            f"(sha256 before={before}, after={after})"
        )


@dataclass(frozen=True, slots=True)
class ShadowRebuildResult:
    """Candidate replay result, semantic deltas, and live-isolation proof."""

    baseline_algorithm_version: str
    candidate_algorithm_version: str
    applied_overrides: Mapping[str, Any]
    learner_state_diff: Mapping[str, Any]
    rebuild: OrchestratedRebuildResult
    live_database_sha256_before: str
    live_database_sha256_after: str

    @property
    def live_database_unchanged(self) -> bool:
        return self.live_database_sha256_before == self.live_database_sha256_after

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode": "shadow",
            "baseline_algorithm_version": self.baseline_algorithm_version,
            "candidate_algorithm_version": self.candidate_algorithm_version,
            "applied_overrides": dict(sorted(self.applied_overrides.items())),
            "live_database": {
                "sha256_before": self.live_database_sha256_before,
                "sha256_after": self.live_database_sha256_after,
                "unchanged": self.live_database_unchanged,
            },
            "rebuild": self.rebuild.as_dict(),
            "learner_state_diff": dict(self.learner_state_diff),
        }


@dataclass(frozen=True, slots=True)
class _ProjectionSpec:
    family: str
    table: str
    key_columns: tuple[str, ...]
    value_columns: tuple[str, ...]


# Semantic learner-facing projections.  Surrogate ids plus created_at and
# updated_at are deliberately absent: a replay may remint them without changing
# what the learner knows or what the scheduler will do.
_PROJECTION_SPECS: tuple[_ProjectionSpec, ...] = (
    _ProjectionSpec(
        "mastery",
        "learning_object_mastery",
        ("learning_object_id",),
        (
            "logit_mean",
            "logit_variance",
            "evidence_count",
            "last_evidence_at",
            "algorithm_version",
        ),
    ),
    _ProjectionSpec(
        "facet",
        "evidence_facet_recall_state",
        ("learning_object_id", "facet_id", "practice_item_id"),
        (
            "recall_alpha",
            "recall_beta",
            "recall_mean",
            "recall_variance",
            "independent_evidence_mass",
            "raw_coverage_mass",
            "last_attempt_at",
            "last_error_at",
            "consecutive_failures",
            "algorithm_version",
        ),
    ),
    _ProjectionSpec(
        "facet",
        "facet_recall_state",
        ("facet_id", "capability_key", "practice_item_id"),
        (
            "recall_alpha",
            "recall_beta",
            "recall_mean",
            "recall_variance",
            "independent_evidence_mass",
            "raw_coverage_mass",
            "last_observed_at",
            "last_error_at",
            "consecutive_failures",
            "algorithm_version",
        ),
    ),
    _ProjectionSpec(
        "schedule",
        "practice_item_state",
        ("practice_item_id",),
        (
            "difficulty",
            "stability",
            "retrievability",
            "due_at",
            "active",
            "content_hash",
            "last_attempt_at",
        ),
    ),
    _ProjectionSpec(
        "schedule",
        "activity_card_state",
        ("learner_id", "card_lineage_id", "scheduler_algorithm_version"),
        (
            "model_label",
            "difficulty",
            "stability",
            "retrievability",
            "due_at",
            "last_eligible_review_at",
            "lapse_episode_id",
            "active",
        ),
    ),
)


def build_candidate_config(
    config: LearnLoopConfig,
    assignments: Sequence[str] = (),
) -> tuple[LearnLoopConfig, dict[str, Any]]:
    """Return a validated config with repeated dotted assignments applied.

    Values accept JSON scalars/containers; an unquoted value that is not valid
    JSON is treated as a string, which keeps common CLI input such as
    ``algorithms.algorithm_version=mvp-0.9`` ergonomic.  Unknown paths are
    rejected so a typo cannot silently turn a candidate experiment into the
    baseline configuration (``LearnLoopConfig`` intentionally allows legacy
    extra keys when loading vaults).
    """

    payload = deepcopy(config.model_dump(mode="python"))
    requested_paths: list[tuple[str, tuple[str, ...]]] = []
    for assignment in assignments:
        path, separator, raw_value = str(assignment).partition("=")
        path = path.strip()
        if not separator or not path or not raw_value.strip():
            raise ConfigOverrideError(
                f"invalid config override {assignment!r}; expected dotted.path=value"
            )
        parts = tuple(part.strip() for part in path.split("."))
        if any(not part for part in parts):
            raise ConfigOverrideError(
                f"invalid config override path {path!r}; path segments cannot be empty"
            )
        cursor: Any = payload
        for part in parts[:-1]:
            if not isinstance(cursor, dict) or part not in cursor:
                raise ConfigOverrideError(f"unknown config path: {path}")
            cursor = cursor[part]
        leaf = parts[-1]
        if not isinstance(cursor, dict) or leaf not in cursor:
            raise ConfigOverrideError(f"unknown config path: {path}")
        cursor[leaf] = _parse_override_value(raw_value.strip())
        requested_paths.append((path, parts))

    try:
        candidate = type(config).model_validate(payload)
    except ValidationError as exc:
        raise ConfigOverrideError(f"candidate config is invalid: {exc}") from exc

    normalized = candidate.model_dump(mode="json")
    applied: dict[str, Any] = {}
    for path, parts in requested_paths:
        cursor = normalized
        for part in parts:
            cursor = cursor[part]
        applied[path] = cursor
    return candidate, applied


def shadow_rebuild(
    vault: LoadedVault,
    *,
    assignments: Sequence[str] = (),
) -> ShadowRebuildResult:
    """Replay all history on a scratch DB and compare learner projections.

    This entry point deliberately accepts a loaded vault rather than a writable
    repository.  It derives the existing live path from the *baseline* config,
    attaches that database read-only, and never calls migrations or state sync.
    A candidate ``storage.sqlite_path`` override therefore cannot redirect or
    mutate the source database.
    """

    live_path = VaultPaths(vault.root, vault.config).sqlite_path.resolve()
    if not live_path.is_file():
        raise ShadowRebuildError(f"live database does not exist: {live_path}")
    before_hash = _sha256_file(live_path)
    candidate_config: LearnLoopConfig | None = None
    applied: dict[str, Any] = {}
    baseline_snapshot: dict[str, dict[tuple[Any, ...], dict[str, Any]]] | None = None
    rebuild_result: OrchestratedRebuildResult | None = None
    candidate_snapshot: dict[str, dict[tuple[Any, ...], dict[str, Any]]] | None = None
    after_hash = before_hash
    try:
        live_repository = Repository.attach(live_path, read_only=True)
        baseline_snapshot = _learner_state_snapshot(live_repository)
        candidate_config, applied = build_candidate_config(vault.config, assignments)
        candidate_vault = replace(vault, config=candidate_config)
        with tempfile.TemporaryDirectory(prefix="learnloop-shadow-rebuild-") as scratch:
            scratch_path = Path(scratch) / "state.sqlite"
            scratch_repository = Repository.attach(scratch_path, read_only=False)
            _backup_database(live_repository, scratch_repository)
            with scratch_repository.pinned():
                rebuild_result = rebuild_all_derived_state(
                    candidate_vault,
                    scratch_repository,
                )
                candidate_snapshot = _learner_state_snapshot(scratch_repository)
    finally:
        # This check runs even if candidate validation/replay fails.  A mismatch
        # is elevated over the candidate error because isolation is the stronger
        # safety invariant.
        after_hash = _sha256_file(live_path)
        if after_hash != before_hash:
            raise LiveDatabaseChangedError(before_hash, after_hash)

    if (
        baseline_snapshot is None
        or candidate_config is None
        or rebuild_result is None
        or candidate_snapshot is None
    ):  # pragma: no cover
        raise ShadowRebuildError("shadow rebuild did not produce a candidate result")
    return ShadowRebuildResult(
        baseline_algorithm_version=vault.config.algorithms.algorithm_version,
        candidate_algorithm_version=candidate_config.algorithms.algorithm_version,
        applied_overrides=applied,
        learner_state_diff=_semantic_diff(baseline_snapshot, candidate_snapshot),
        rebuild=rebuild_result,
        live_database_sha256_before=before_hash,
        live_database_sha256_after=after_hash,
    )


def _parse_override_value(raw_value: str) -> Any:
    try:
        return json.loads(raw_value)
    except json.JSONDecodeError:
        return raw_value


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _backup_database(source: Repository, destination: Repository) -> None:
    """Make a transactionally consistent copy using the requested attach APIs."""

    with closing(source.connection()) as source_connection, closing(
        destination.connection()
    ) as destination_connection:
        source_connection.backup(destination_connection)
        destination_connection.commit()


def _learner_state_snapshot(
    repository: Repository,
) -> dict[str, dict[tuple[Any, ...], dict[str, Any]]]:
    snapshot: dict[str, dict[tuple[Any, ...], dict[str, Any]]] = {
        "mastery": {},
        "facet": {},
        "schedule": {},
    }
    with closing(repository.connection()) as connection:
        for spec in _PROJECTION_SPECS:
            columns = spec.key_columns + spec.value_columns
            rows = connection.execute(
                f'SELECT {", ".join(columns)} FROM "{spec.table}"'
            ).fetchall()
            for row in rows:
                # Prefix with the projection table because legacy and canonical
                # facet/schedule rows intentionally coexist.
                storage_key = (spec.table, *(row[column] for column in spec.key_columns))
                snapshot[spec.family][storage_key] = {
                    "projection": spec.table,
                    **{column: row[column] for column in spec.key_columns},
                    **{column: row[column] for column in spec.value_columns},
                }
    return snapshot


def _semantic_diff(
    before: Mapping[str, Mapping[tuple[Any, ...], Mapping[str, Any]]],
    after: Mapping[str, Mapping[tuple[Any, ...], Mapping[str, Any]]],
) -> dict[str, Any]:
    report: dict[str, Any] = {}
    for family in ("mastery", "facet", "schedule"):
        old = before[family]
        new = after[family]
        keys = sorted(
            set(old) | set(new),
            key=lambda value: json.dumps(value, sort_keys=True, default=str),
        )
        changes: list[dict[str, Any]] = []
        counts = {"added": 0, "removed": 0, "changed": 0, "unchanged": 0}
        for key in keys:
            old_row = old.get(key)
            new_row = new.get(key)
            if old_row is None:
                change = "added"
            elif new_row is None:
                change = "removed"
            elif old_row != new_row:
                change = "changed"
            else:
                counts["unchanged"] += 1
                continue
            counts[change] += 1
            key_fields = {
                field: value
                for field, value in (new_row or old_row or {}).items()
                if field == "projection" or field in _key_fields_for_projection(key[0])
            }
            entry: dict[str, Any] = {
                "change": change,
                "key": key_fields,
                "before": dict(old_row) if old_row is not None else None,
                "after": dict(new_row) if new_row is not None else None,
            }
            delta = _numeric_delta(old_row, new_row)
            if delta:
                entry["delta"] = delta
            changes.append(entry)
        report[family] = {"summary": counts, "changes": changes}
    report["summary"] = {
        family: sum(
            int(report[family]["summary"][kind])
            for kind in ("added", "removed", "changed")
        )
        for family in ("mastery", "facet", "schedule")
    }
    return report


def _key_fields_for_projection(projection: str) -> frozenset[str]:
    for spec in _PROJECTION_SPECS:
        if spec.table == projection:
            return frozenset(spec.key_columns)
    return frozenset()  # pragma: no cover - snapshots only use declared specs


def _numeric_delta(
    before: Mapping[str, Any] | None,
    after: Mapping[str, Any] | None,
) -> dict[str, int | float]:
    if before is None or after is None:
        return {}
    delta: dict[str, int | float] = {}
    for field in sorted(set(before) & set(after)):
        old_value = before[field]
        new_value = after[field]
        if (
            isinstance(old_value, (int, float))
            and not isinstance(old_value, bool)
            and isinstance(new_value, (int, float))
            and not isinstance(new_value, bool)
            and old_value != new_value
        ):
            delta[field] = new_value - old_value
    return delta


__all__ = [
    "ConfigOverrideError",
    "LiveDatabaseChangedError",
    "ShadowRebuildError",
    "ShadowRebuildResult",
    "build_candidate_config",
    "shadow_rebuild",
]
