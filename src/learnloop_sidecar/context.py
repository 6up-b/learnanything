from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from learnloop.ai.runtime import check_ai_runtime
from learnloop.codex.runtime import check_codex_runtime
from learnloop.db.migrate import applied_versions, discover_migrations
from learnloop.db.repositories import Repository
from learnloop.services.mastery import display_mastery
from learnloop.services.startup import run_startup_maintenance
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths
from learnloop_sidecar.dto import to_camel, versioned
from learnloop_sidecar.errors import SidecarError


@dataclass
class SidecarContext:
    vault_root: Path | None = None
    vault: LoadedVault | None = None
    repository: Repository | None = None
    shutdown_requested: bool = False

    def load(self, vault_path: str | Path, *, maintenance: bool = True) -> None:
        self.vault_root = Path(vault_path).resolve()
        self.vault = load_vault(self.vault_root)
        self.repository = Repository(VaultPaths(self.vault.root, self.vault.config).sqlite_path)
        sync_vault_state(self.vault, self.repository)
        # Startup maintenance probes the Codex runtime, which (for the HTTP provider)
        # can launch the server and block up to startup_timeout_seconds. Skip it on
        # refreshes that only need fresh vault/DB state, not a runtime health pass.
        if maintenance:
            run_startup_maintenance(self.vault, self.repository)

    def reload(self, *, maintenance: bool = True) -> None:
        if self.vault_root is None:
            raise SidecarError("vault_not_loaded", "No vault has been initialized.")
        self.load(self.vault_root, maintenance=maintenance)

    def require_vault(self) -> tuple[LoadedVault, Repository]:
        if self.vault is None or self.repository is None:
            raise SidecarError("vault_not_loaded", "No vault has been initialized.")
        return self.vault, self.repository

    def app_snapshot(self) -> dict[str, Any]:
        vault, repository = self.require_vault()
        active = repository.most_recent_open_session()
        active_session = None
        if active is not None and repository.fetch_session_checkpoint(active["id"]) is not None:
            active_session = session_snapshot(repository, active["id"])
        return versioned(
            {
                "vault": vault_summary(vault),
                "config": config_dto(vault),
                "health": runtime_health(vault, repository),
                "active_session": active_session,
            }
        )


def vault_summary(vault: LoadedVault) -> dict[str, Any]:
    return versioned(
        {
            "root": str(vault.root),
            "schema_version": vault.config.schema_version,
            "algorithm_version": vault.config.algorithms.algorithm_version,
            "subjects": sorted(vault.subjects),
            "counts": {
                "learning_objects": len(vault.learning_objects),
                "practice_items": len(vault.practice_items),
                "concepts": len(vault.concepts),
                "goals": len(vault.goals),
                "error_types": len(vault.error_types),
                "notes": len(vault.notes),
            },
            "issue_count": len(vault.issues),
        }
    )


def config_dto(vault: LoadedVault) -> dict[str, Any]:
    config = vault.config
    return versioned(
        {
            "schema_version": config.schema_version,
            "algorithm_version": config.algorithms.algorithm_version,
            "storage": {"sqlite_path": config.storage.sqlite_path},
            "scheduler": {
                "forgetting_risk_weight": config.scheduler.forgetting_risk_weight,
                "active_goal_weight": config.scheduler.active_goal_weight,
                "recent_error_weight": config.scheduler.recent_error_weight,
                "probe_eig_weight": config.scheduler.probe_eig_weight,
                "short_session_minutes": config.scheduler.short_session_minutes,
            },
            "mastery": {
                "base_observation_variance": config.mastery.base_observation_variance,
                "sigma2_drift": config.mastery.sigma2_drift,
                "p_max": config.mastery.p_max,
            },
            "probe": {
                "attempts_target_default": config.probe.attempts_target_default,
                "attempts_target_with_strong_claim": config.probe.attempts_target_with_strong_claim,
                "claim_skip_threshold": config.probe.claim_skip_threshold,
                "variance_convergence_threshold": config.probe.variance_convergence_threshold,
                "hypothesis_set_max_size": config.probe.hypothesis_set_max_size,
            },
            "codex": {
                "provider": config.codex.provider,
                "model": config.codex.model,
                "base_url": config.codex.base_url,
                "auth_mode": config.codex.auth_mode,
            },
            "ai": {
                "active_provider": config.ai.active_provider,
                "fallback_provider": config.ai.fallback_provider,
                "providers": {
                    name: {
                        "type": profile.type,
                        "model": profile.model,
                        "base_url": profile.base_url,
                        "api_key_env": profile.api_key_env,
                    }
                    for name, profile in sorted(config.ai.providers.items())
                },
            },
        }
    )


def runtime_health(vault: LoadedVault, repository: Repository) -> dict[str, Any]:
    report = check_codex_runtime(vault.root, vault.config.codex)
    ai_report = check_ai_runtime(vault.root, vault.config)
    versions = applied_versions(repository.sqlite_path)
    latest = max((migration.version for migration in discover_migrations()), default=0)
    return versioned(
        {
            "codex": {
                "ready": report.ready,
                "status": report.status,
                "model": vault.config.codex.model,
                "actual_revision": report.actual_revision,
                "base_url": vault.config.codex.base_url,
                "checked_at": _nowish(),
            },
            "ai": {
                "ready": ai_report.ready,
                "status": ai_report.status,
                "active_provider": ai_report.active_provider,
                "provider_type": ai_report.provider_type,
                "model": ai_report.model,
                "provider_revision": ai_report.provider_revision,
                "checked_at": _nowish(),
            },
            "database": {
                "ok": latest in versions if latest else True,
                "migrations_applied": len(versions),
                "latest_migration": latest,
            },
            "vault_loaded": True,
        }
    )


def session_snapshot(repository: Repository, session_id: str) -> dict[str, Any] | None:
    row = repository.fetch_session(session_id)
    if row is None:
        return None
    checkpoint = repository.fetch_session_checkpoint(session_id)
    return versioned(
        {
            "session_id": row["id"],
            "started_at": row["started_at"],
            "ended_at": row["ended_at"],
            "energy": row["energy"],
            "sleep_quality": row["sleep_quality"],
            "available_minutes": row["available_minutes"],
            "notes_md_path": row["notes_md_path"],
            "checkpoint": checkpoint_dto(checkpoint) if checkpoint is not None else None,
        }
    )


def checkpoint_dto(row: dict[str, Any]) -> dict[str, Any]:
    focus = row.get("focus_block_state")
    hints_used = 0
    if isinstance(focus, dict):
        practice = focus.get("practice")
        if isinstance(practice, dict):
            hints_used = int(practice.get("hintsUsed") or practice.get("hints_used") or 0)
    return to_camel(
        {
            "current_practice_item_id": row.get("current_practice_item_id"),
            "current_answer": row.get("current_answer"),
            "hints_used": hints_used,
            "focus_block_state": focus,
            "pending_grading_proposal": row.get("pending_grading_proposal"),
            "readiness": row.get("readiness"),
            "updated_at": row.get("updated_at"),
        }
    )


def mastery_dto(repository: Repository, learning_object_id: str) -> dict[str, Any] | None:
    state = repository.mastery_state(learning_object_id)
    if state is None:
        return None
    display = display_mastery(state)
    return to_camel(
        {
            "mean": display.mastery_mean,
            "variance": display.mastery_variance,
            "evidence_count": state.evidence_count,
            "last_evidence_at": state.last_evidence_at,
        }
    )


def _nowish() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
