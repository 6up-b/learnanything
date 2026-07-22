from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from learnloop.ai.runtime import check_ai_runtime
from learnloop.codex.runtime import check_codex_runtime
from learnloop.db.migrate import applied_versions, discover_migrations
from learnloop.db.repositories import Repository
from learnloop.services.canonical_projection import project_canonical_facet_state
from learnloop.services.facet_diagnostics import mastery_diagnostic_view
from learnloop.services.mastery import display_mastery
from learnloop.services.startup import run_startup_maintenance
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths
from learnloop_sidecar.dto import to_camel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.ingest_jobs import IngestJobManager


@dataclass
class SidecarContext:
    vault_root: Path | None = None
    vault: LoadedVault | None = None
    repository: Repository | None = None
    shutdown_requested: bool = False
    # Runtime-only grading backend override set via set_grading_provider: a
    # configured provider key, the literal "manual", or None (config routing).
    # Never persisted to learnloop.toml; survives vault reloads within this process.
    grading_provider_override: str | None = None
    ingest_jobs: IngestJobManager = field(default_factory=IngestJobManager, repr=False)

    def load(self, vault_path: str | Path, *, maintenance: bool = True) -> None:
        self.vault_root = Path(vault_path).resolve()
        self.vault = load_vault(self.vault_root)
        self.repository = Repository(VaultPaths(self.vault.root, self.vault.config).sqlite_path)
        runner_config = self.vault.config.ingest.runner
        self.ingest_jobs.bind(
            self.repository,
            self.vault_root,
            lease_ttl_seconds=runner_config.lease_ttl_seconds,
            heartbeat_interval_seconds=runner_config.heartbeat_interval_seconds,
            poll_interval_seconds=runner_config.poll_interval_seconds,
        )
        sync_vault_state(self.vault, self.repository)
        # Canonical facet state is a deterministic cache over the immutable
        # attempt ledger. Re-project on app load so vaults activated by the old
        # mvp-0.7 upgrader (which only flipped the config field) self-heal and
        # immediately show their historical attempts in the knowledge field.
        # This is a no-op for legacy vaults and idempotent for current ones.
        project_canonical_facet_state(self.vault, self.repository)
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
                "health": runtime_health(vault, repository, grading_override=self.grading_provider_override),
                "active_session": active_session,
                "streak": repository.session_day_streak(),
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
                "goal_frontier_weight": config.scheduler.goal_frontier_weight,
                "recent_error_weight": config.scheduler.recent_error_weight,
                "probe_eig_weight": config.scheduler.probe_eig_weight,
                "short_session_minutes": config.scheduler.short_session_minutes,
                "followup": {
                    "tau_followup_nats": config.scheduler.followup.tau_followup_nats,
                    "gate_mode": config.scheduler.followup.gate_mode,
                    "gate_score_threshold": config.scheduler.followup.gate_score_threshold,
                    "threshold_mode": config.scheduler.followup.threshold_mode,
                },
            },
            "mastery": {
                "base_observation_variance": config.mastery.base_observation_variance,
                "sigma2_drift": config.mastery.sigma2_drift,
                "p_max": config.mastery.p_max,
                "display_strong_threshold": config.mastery.display_strong_threshold,
                "display_developing_threshold": config.mastery.display_developing_threshold,
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
                # Per-task provider routes (the Settings tab edits these).
                "routing": {
                    task: getattr(config.ai.routing, task)
                    for task in (
                        "grading",
                        "canonical_ingest",
                        "canonical_ingest_retry",
                        "authoring",
                        "tutor_qa",
                        "teach_back",
                        "rung_variant",
                    )
                },
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


def available_grading_providers(vault: LoadedVault) -> list[str]:
    """Selectable grading backends: configured AI providers, legacy codex, manual."""

    providers = set(vault.config.ai.providers) | {"codex"}
    return sorted(providers) + ["manual"]


def runtime_health(
    vault: LoadedVault, repository: Repository, grading_override: str | None = None
) -> dict[str, Any]:
    report = check_codex_runtime(vault.root, vault.config.codex)
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
            "ai": _ai_health(vault, grading_override),
            "database": {
                "ok": latest in versions if latest else True,
                "migrations_applied": len(versions),
                "latest_migration": latest,
            },
            "vault_loaded": True,
        }
    )


def _ai_health(vault: LoadedVault, grading_override: str | None) -> dict[str, Any]:
    """The health.ai dto, honoring the runtime grading override.

    - No override: unchanged behavior (config/env routed provider).
    - Override "manual": AI grading is intentionally off; reported as
      ready=True with status "manual" and manual_grading=True so the frontend
      shows the self-grade flow instead of an "AI unavailable" warning.
    - Override = provider key: health for that provider specifically.
    """

    base = {
        "manual_grading": False,
        "grading_provider_override": grading_override,
        "available_grading_providers": available_grading_providers(vault),
        "checked_at": _nowish(),
    }
    if grading_override == "manual":
        return {
            "ready": True,
            "status": "manual",
            "active_provider": "manual",
            "provider_type": None,
            "model": None,
            "provider_revision": None,
            **base,
            "manual_grading": True,
        }
    if grading_override == "codex" and "codex" not in vault.config.ai.providers:
        codex_report = check_codex_runtime(vault.root, vault.config.codex)
        return {
            "ready": codex_report.ready,
            "status": codex_report.status,
            "active_provider": "codex",
            "provider_type": "codex",
            "model": vault.config.codex.model,
            "provider_revision": codex_report.actual_revision,
            **base,
        }
    ai_report = check_ai_runtime(vault.root, vault.config, provider_name=grading_override)
    return {
        "ready": ai_report.ready,
        "status": ai_report.status,
        "active_provider": ai_report.active_provider,
        "provider_type": ai_report.provider_type,
        "model": ai_report.model,
        "provider_revision": ai_report.provider_revision,
        **base,
    }


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
    envelope = teach_back_envelope(row.get("current_answer"))
    return to_camel(
        {
            "current_practice_item_id": row.get("current_practice_item_id"),
            "current_answer": row.get("current_answer"),
            "hints_used": hints_used,
            "focus_block_state": focus,
            "pending_grading_proposal": row.get("pending_grading_proposal"),
            "readiness": row.get("readiness"),
            "updated_at": row.get("updated_at"),
            # Additive: a mid-conversation teach-back checkpoint, so the
            # frontend can rehydrate the transcript instead of starting fresh.
            "teach_back": envelope["state"] if envelope is not None else None,
        }
    )


def teach_back_envelope(current_answer: Any) -> dict[str, Any] | None:
    """Parse a teach-back conversation envelope from checkpoint current_answer.

    The teach-back handler persists ``{"mode": "teach_back", "state": <core
    TeachBackState dict>}`` as a JSON string in the checkpoint's
    ``current_answer`` slot. Anything else (a plain draft answer, empty, or
    malformed JSON) returns ``None``.
    """

    if not isinstance(current_answer, str) or not current_answer.strip():
        return None
    try:
        payload = json.loads(current_answer)
    except (json.JSONDecodeError, ValueError):
        return None
    if (
        isinstance(payload, dict)
        and payload.get("mode") == "teach_back"
        and isinstance(payload.get("state"), dict)
    ):
        return payload
    return None


def mastery_dto(repository: Repository, learning_object_id: str, vault: LoadedVault | None = None) -> dict[str, Any] | None:
    state = repository.mastery_state(learning_object_id)
    if state is None:
        return None
    display = display_mastery(state)
    payload: dict[str, Any] = {
        "mean": display.mastery_mean,
        "variance": display.mastery_variance,
        "plausible_lower": display.plausible_lower,
        "plausible_upper": display.plausible_upper,
        "plausible_mass": display.plausible_mass,
        "evidence_count": state.evidence_count,
        "last_evidence_at": state.last_evidence_at,
    }
    if vault is not None:
        diagnostic = mastery_diagnostic_view(vault, repository, learning_object_id)
        payload["required_facets"] = diagnostic["required_facets"]
        payload["facet_diagnostics"] = diagnostic["facets"]
    return to_camel(payload)


def _nowish() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
