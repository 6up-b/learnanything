from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from learnloop.ai.routing import (
    is_embedding_profile, is_generation_profile, ready_client_for_task, route_names, runtime_for_provider,
)
from learnloop.attempts.stuck import stuck_prompt_active
from learnloop.clock import utc_now_iso
from learnloop.db.migrate import applied_versions, discover_migrations
from learnloop.db.repositories import Repository
from learnloop.hints.map_builder import BackgroundBuilds
from learnloop.substrate.canonical_projection_rollout import (
    refresh_canonical_projection_on_startup,
)
from learnloop.learner.facet_diagnostics import mastery_diagnostic_view
from learnloop.learner.mastery import display_mastery
from learnloop.ops.startup import run_startup_maintenance
from learnloop.reader.reader_authoring import adopt_reference_questions
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.hashes import practice_item_hash
from learnloop.vault.loader import load_practice_item_file, load_vault
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.repository import open_vault_repository
from learnloop_sidecar.dto import to_camel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.exam_grading import ExamGradingManager
from learnloop_sidecar.post_attempt_worker import PostAttemptWorker
from learnloop.content.pipeline.jobs import IngestJobManager

_LOGGER = logging.getLogger(__name__)


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
    exam_grading: ExamGradingManager = field(
        default_factory=ExamGradingManager, repr=False
    )
    # Slice 1 M2 (§11): drains the durable diagnose/embed queue off the request
    # path. Starts lazily when a submit queues a job (joint vaults never start it).
    post_attempt_worker: PostAttemptWorker = field(
        default_factory=PostAttemptWorker, repr=False
    )
    # Adaptive hints H1 (fix round 2, M4): the approach-map builds a serve
    # starts belong to the loaded vault. Opening another vault, shutdown and
    # EOF drain them (bounded) and fence their late writes.
    map_builds: BackgroundBuilds = field(default_factory=BackgroundBuilds, repr=False)

    def load(self, vault_path: str | Path, *, maintenance: bool = True) -> None:
        target = Path(vault_path).resolve()
        if self.vault_root is not None and target != self.vault_root:
            # A switch: the previous vault's map builds stop before anything of the new one opens.
            self.map_builds.close()
        self.vault_root = target
        self.vault = load_vault(self.vault_root)
        self.repository = open_vault_repository(
            self.vault.root,
            VaultPaths(self.vault.root, self.vault.config).sqlite_path,
        )
        self.map_builds.bind(self.repository.sqlite_path)
        # Finish a facet merge or undo that a previous process left mid-flight
        # before anything reads or re-projects the vault (facet identity F12).
        if _recover_facet_identity_actions(self.vault_root, self.repository):
            self.vault = load_vault(self.vault_root)
        runner_config = self.vault.config.ingest.runner
        self.ingest_jobs.bind(
            self.repository,
            self.vault_root,
            lease_ttl_seconds=runner_config.lease_ttl_seconds,
            heartbeat_interval_seconds=runner_config.heartbeat_interval_seconds,
            poll_interval_seconds=runner_config.poll_interval_seconds,
        )
        sync_vault_state(self.vault, self.repository)
        # A reader question kept as a reference (no active LO cited its passage
        # when it was written) becomes practice once one does. Every study-map
        # apply ends in this (re)load, right after state sync, so this is where a
        # newly added or linked LO first becomes visible (daily-loop follow-up).
        # Kill switch: tutor_qa.adopt_reference_questions (checked by the sweep).
        if _adopt_reference_questions(self.vault, self.repository):
            self.vault = load_vault(self.vault_root)
            sync_vault_state(self.vault, self.repository)
            self.repository.bump_queue_revision()
        self.post_attempt_worker.bind(self._worker_target)
        # Canonical facet state is a deterministic cache over the immutable
        # attempt ledger. Re-project on app load so vaults activated by the old
        # mvp-0.7 upgrader (which only flipped the config field) self-heal and
        # immediately show their historical attempts in the knowledge field.
        # Projection semantics changes are also stamped here exactly once, so
        # the refresh cannot silently move learner-visible estimates.
        refresh_canonical_projection_on_startup(self.vault, self.repository)
        # Self-heal certificates earned before the live attempt hook existed.
        # The §5.7 scheduler is idempotent per content-addressed certificate and
        # reports unmeasurable certificates rather than inventing a probe.
        from learnloop.goals.certification_cold_probe import (
            schedule_certification_cold_probes,
        )

        schedule_certification_cold_probes(self.vault, self.repository)
        # Startup maintenance probes the Codex runtime, which (for the HTTP provider)
        # can launch the server and block up to startup_timeout_seconds. Skip it on
        # refreshes that only need fresh vault/DB state, not a runtime health pass.
        if maintenance:
            run_startup_maintenance(self.vault, self.repository)
            # Adaptive hints H2b (review F4, F5): work a previous process
            # committed the source of and never queued or finished.
            self.reconcile_hint_work()
            # A previous process may have left queued or leased jobs; resume.
            self.resume_post_attempt_jobs()
            # ... and imported exercises' key checks it never committed
            # (canonical sources, Codex review F5).
            self.recover_import_key_checks()
            # UX Phase 1 (review F7): reading progress that arrived while a
            # book's questions were being built, and the process ended first.
            try:
                from learnloop.content.pipeline.add_source import reconcile_reading_builds

                reconcile_reading_builds(self.ingest_jobs)
            except Exception:  # noqa: BLE001 - never block opening the library
                _LOGGER.warning("could not act on pending reading progress", exc_info=True)
            # A book's preparation the previous process queued and never ran:
            # a build it queued (settling the reading request it answered),
            # then ended before its worker started (reading-hardening Codex
            # review 2, F1). Independent of any reading request; the reading
            # sweep checks again on every pass.
            try:
                self.ingest_jobs.resume_book_preparation()
            except Exception:  # noqa: BLE001 - never block opening the library
                _LOGGER.warning("could not resume a book's queued preparation", exc_info=True)

    def reconcile_hint_work(self) -> None:
        """Adaptive hints H2b, at a vault's open (review F4, F5): queue the
        replies to hints and discriminating answers whose learner-text job
        never committed, and start, in the background, the outcome placements
        of hinted attempts that never got one (a process that ended before
        scheduling, or a placement a vault switch fenced). Both are
        idempotent and keep their own switches; neither blocks opening the
        vault, and neither reads learner text or calls a model here."""

        if self.vault is None or self.repository is None:
            return
        try:
            from learnloop.diagnosis.text_gaps.jobs import reconcile_hint_feedback

            reconcile_hint_feedback(self.vault, self.repository)
        except Exception:  # noqa: BLE001 - never block opening the vault
            _LOGGER.warning("could not queue unread replies to hints", exc_info=True)
        try:
            from learnloop.hints.outcome import reconcile_outcome_placements

            reconcile_outcome_placements(self.vault, self.repository.sqlite_path,
                                         client=getattr(self, "hint_outcome_client", None), builds=self.map_builds)
        except Exception:  # noqa: BLE001 - never block opening the vault
            _LOGGER.warning("could not resume outcome placements", exc_info=True)

    def close_background_builds(self) -> bool:
        """Drain the approach-map builds (shutdown and EOF; bounded, never hangs)."""

        return self.map_builds.close()

    def _worker_target(self) -> tuple[LoadedVault, Path] | None:
        if self.vault is None or self.repository is None:
            return None
        return self.vault, self.repository.sqlite_path

    def recover_import_key_checks(self) -> None:
        """Resume the key checks of imported exercises a dead process left
        incomplete. The durable state is the import row (its pending marker and
        content binding); the check runs off the request path and commits with
        the import's completion. Nothing runs when nothing is pending."""

        if self.vault is None or self.repository is None or self.vault_root is None:
            return
        service = self.vault.config.source_service
        if not (service.enabled and service.exercise_verification):
            return
        from learnloop.content.authoring.source_exercise_import import (
            CHECK_LEASE_SECONDS,
            pending_import_checks,
            recover_import_checks,
        )

        if not pending_import_checks(self.repository, include_held=True):
            return
        root, repository = self.vault_root, self.repository

        def run() -> None:
            import time

            try:
                # A check under a live lease is someone's running check; it is
                # retried only once its lease lapses (a dead process's lease
                # outlives it by at most CHECK_LEASE_SECONDS; Codex re-review F9).
                while True:
                    report = recover_import_checks(root, repository)
                    wait = report.get("retry_after_seconds")
                    if wait is None:
                        break
                    time.sleep(min(float(wait), float(CHECK_LEASE_SECONDS)) + 1.0)
            except Exception:  # noqa: BLE001 - the markers stay; the next start resumes them
                import logging

                logging.getLogger(__name__).warning("recovering imported exercises' key checks failed",
                                                    exc_info=True)

        import threading

        threading.Thread(target=run, name="import-key-check-recovery", daemon=True).start()

    def resume_post_attempt_jobs(self) -> None:
        """Wake the worker when the durable queue holds unfinished jobs."""

        if self.repository is None:
            return
        if self.repository.post_attempt_jobs(states=("queued", "leased")):
            self.post_attempt_worker.notify()
            return
        from learnloop.diagnosis.text_gaps.jobs import pending_jobs

        if pending_jobs(self.repository):
            # Learner-text gap readings left by a previous process.
            self.post_attempt_worker.notify()

    def reload(self, *, maintenance: bool = True) -> None:
        if self.vault_root is None:
            raise SidecarError("vault_not_loaded", "No vault has been initialized.")
        self.load(self.vault_root, maintenance=maintenance)

    def refresh_vault_files(
        self,
        relative_paths: list[str],
        *,
        expected_root: str | Path | None = None,
    ) -> dict[str, Any]:
        """Incrementally refresh watcher-reported Practice Item files.

        Other vault entities still take the conservative full-reload path. This
        narrow first seam is intentional: Practice Items are the high-frequency
        interactive files, and their scheduler-state impact already has one
        canonical activatability rule in ``state_sync``.
        """

        vault, repository = self.require_vault()
        root = vault.root.resolve()
        if expected_root is not None and Path(expected_root).resolve() != root:
            # A native event can already be queued when the learner switches
            # vaults. The originating root travels with the event so an old
            # relative path can never be applied to the newly selected vault.
            return {
                "mode": "stale",
                "changed_practice_item_ids": [],
                "practice_item_count": len(vault.practice_items),
            }
        resolved: list[tuple[Path, Path]] = []
        for raw in sorted(set(relative_paths)):
            candidate = (root / raw).resolve()
            try:
                relative = candidate.relative_to(root)
            except ValueError as exc:
                raise SidecarError(
                    "invalid_path", f"Watched path escapes the vault: {raw!r}."
                ) from exc
            resolved.append((candidate, relative))
        if not resolved:
            return {
                "mode": "noop",
                "changed_practice_item_ids": [],
                "practice_item_count": len(vault.practice_items),
            }

        practice_files = all(
            path.suffix.lower() == ".yaml"
            and len(relative.parts) == 4
            and relative.parts[0] == "subjects"
            and relative.parts[2] == "practice-items"
            for path, relative in resolved
        )
        if not practice_files:
            self.reload(maintenance=False)
            repository = self.require_vault()[1]
            revision = repository.bump_queue_revision()
            return {
                "mode": "full",
                "changed_practice_item_ids": [],
                "queue_revision": revision,
                "practice_item_count": len(self.require_vault()[0].practice_items),
                "snapshot": self.app_snapshot(),
            }

        from learnloop.diagnosis.probe_instance_generation import (
            pending_review_instance_ids,
        )
        from learnloop.substrate.state_sync import practice_item_activatable

        review_parked = pending_review_instance_ids(repository)
        measurement_superseded = repository.superseded_measurement_item_ids()
        changed: list[str] = []
        try:
            for path, relative in resolved:
                item_id = path.stem
                subjects_root = root / "subjects"
                matching_paths = [
                    subject_dir / "practice-items" / f"{item_id}.yaml"
                    for subject_dir in subjects_root.iterdir()
                    if subject_dir.is_dir()
                    and (
                        subject_dir / "practice-items" / f"{item_id}.yaml"
                    ).exists()
                ]
                if path.exists():
                    if len(matching_paths) != 1 or matching_paths[0].resolve() != path:
                        raise ValueError(
                            f"{relative} has a duplicate or non-canonical Practice Item path"
                        )
                    issues = []
                    item = load_practice_item_file(path, vault, issues=issues)
                    if item is None:
                        message = issues[0].message if issues else f"{relative} could not be loaded"
                        raise ValueError(message)
                    if item.id != item_id:
                        raise ValueError(
                            f"{relative} declares id {item.id!r}, expected {item_id!r}"
                        )
                    existing = vault.practice_items.get(item.id)
                    if existing is None:
                        # A new/recovered item can change duplicate-id and issue
                        # accounting; let the full loader own that transition.
                        raise ValueError(f"{relative} adds a new Practice Item")
                    if item.learning_object_id not in vault.learning_objects:
                        raise ValueError(
                            f"{relative} references missing Learning Object "
                            f"{item.learning_object_id!r}"
                        )
                    rubric = vault.rubric_for_item(item)
                    if rubric is not None and any(
                        fatal_error.id not in vault.error_types
                        for fatal_error in rubric.fatal_errors
                    ):
                        raise ValueError(f"{relative} has an unaligned fatal error")
                    if existing == item:
                        continue
                    vault.practice_items[item.id] = item
                    state = repository.practice_item_state(item.id)
                    active = practice_item_activatable(
                        item.id,
                        item,
                        review_parked=review_parked,
                        measurement_superseded=measurement_superseded,
                        state=state,
                    )
                    if state is None:
                        repository.upsert_practice_item_state(
                            item.id,
                            active=active,
                            content_hash=practice_item_hash(item),
                        )
                    else:
                        repository.upsert_practice_item_state(
                            item.id,
                            difficulty=state.difficulty,
                            stability=state.stability,
                            retrievability=state.retrievability,
                            due_at=state.due_at,
                            active=active,
                            content_hash=practice_item_hash(item),
                            last_attempt_at=state.last_attempt_at,
                        )
                    if not active:
                        repository.deactivate_practice_item_serving(item.id)
                    changed.append(item.id)
                    continue

                if matching_paths:
                    raise ValueError(
                        f"{relative} was removed but another file still declares {item_id!r}"
                    )
                removed = vault.practice_items.pop(item_id, None)
                if removed is not None:
                    repository.deactivate_practice_item_serving(item_id)
                    changed.append(item_id)
        except (OSError, ValueError):
            # Editors that rewrite in place can briefly expose an incomplete
            # document. The full loader owns issue reporting and conservative
            # recovery for malformed/cross-entity changes.
            self.reload(maintenance=False)
            repository = self.require_vault()[1]
            revision = repository.bump_queue_revision()
            return {
                "mode": "full",
                "changed_practice_item_ids": [],
                "queue_revision": revision,
                "practice_item_count": len(self.require_vault()[0].practice_items),
                "snapshot": self.app_snapshot(),
            }

        revision = (
            repository.bump_queue_revision()
            if changed
            else repository.queue_revision()["revision"]
        )
        return {
            "mode": "incremental",
            "changed_practice_item_ids": changed,
            "queue_revision": revision,
            "practice_item_count": len(vault.practice_items),
        }

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


def _recover_facet_identity_actions(vault_root: Path, repository: Repository) -> bool:
    """Finish interrupted facet merges/undos; True when the vault files may have changed.

    A failure never blocks opening the vault: the merge map leaves an
    unsettled action's rows out, and ``doctor`` reports the action.
    """

    from learnloop.content.facet_identity.actions import recover_interrupted_actions

    try:
        recovered = recover_interrupted_actions(vault_root, repository)
    except Exception:  # pragma: no cover - defensive: startup must not fail on recovery
        _LOGGER.warning("facet-identity recovery failed; run doctor --fix-state", exc_info=True)
        return False
    for row in recovered:
        if row.get("problem"):
            _LOGGER.warning("facet-identity recovery: %s", row["problem"])
        if row.get("refusal"):
            _LOGGER.warning("facet-identity recovery settled %s (%s): %s", row["id"], row["to"], row["refusal"])
    return bool(recovered)


def _adopt_reference_questions(vault: LoadedVault, repository: Repository) -> bool:
    """Run the reader's reference-question adoption sweep; never block a load."""

    try:
        return bool(adopt_reference_questions(vault, repository))
    except Exception:  # noqa: BLE001 - adoption is best-effort; the vault must load
        _LOGGER.warning("reader reference-question adoption failed", exc_info=True)
        return False


def subjects_practised_first(vault: LoadedVault) -> list[str]:
    """Subject ids, the ones the learner practises most first, then by name.

    Screens that default to the first subject (Today's tutor subject,
    Maintain) keep the learner's own subject when Add files a new book under a
    new subject that happens to sort first (UX Phase 1 usability round 1, U10).
    """

    items: dict[str, int] = {}
    topics: dict[str, int] = {}
    for item in vault.practice_items.values():
        if getattr(item, "status", "active") != "active":
            continue
        for subject in vault.subjects_for_item(item):
            items[subject] = items.get(subject, 0) + 1
    for lo in vault.learning_objects.values():
        if lo.status != "active":
            continue
        for subject in lo.subjects:
            topics[subject] = topics.get(subject, 0) + 1
    return sorted(vault.subjects, key=lambda subject: (-items.get(subject, 0), -topics.get(subject, 0), subject))


def vault_summary(vault: LoadedVault) -> dict[str, Any]:
    return versioned(
        {
            "root": str(vault.root),
            "schema_version": vault.config.schema_version,
            "algorithm_version": vault.config.algorithms.algorithm_version,
            "subjects": subjects_practised_first(vault),
            # The learner reads titles, never ids (usability round 1, U10). A
            # list, not a map: ids are data and must not be camel-cased.
            "subject_titles": [
                {"id": subject_id, "title": vault.subjects[subject_id].metadata.title}
                for subject_id in subjects_practised_first(vault)
            ],
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


def _adaptive_difficulty_dto(config: Any) -> dict[str, Any]:
    from learnloop.adaptive_difficulty.switches import rating_tap_enabled, receipts_enabled

    rating, marker = rating_tap_enabled(config), receipts_enabled(config)
    if not (rating or marker):
        return {}
    return {"adaptive_difficulty": {"rating_tap": rating, "first_hint_progress": marker}}


def config_dto(vault: LoadedVault) -> dict[str, Any]:
    config = vault.config
    return versioned(
        {
            "schema_version": config.schema_version,
            "algorithm_version": config.algorithms.algorithm_version,
            "storage": {"sqlite_path": config.storage.sqlite_path},
            # mvp-0.13: the answer surfaces offer "I'm stuck" (write what you
            # can) instead of "I don't know" when this is true.
            "practice": {"stuck_prompt": stuck_prompt_active(vault)},
            # UX Phase 4's kill switch (display only): "simple" practice and
            # feedback surfaces, or "classic" for the screens as they were.
            "ui": {"practice_feedback": config.ui.practice_feedback},
            # Reader workbench RW2a's kill switch: present only while on, so
            # with it off the snapshot is exactly what it was before RW2a.
            **({"workbench": {"enabled": True, "open_session_days": config.workbench.open_session_days}}
               if config.workbench.enabled else {}),
            # Reader workbench RW6a's two kill switches: present only while one
            # of them is on, so with both off the snapshot is what it was. They
            # depend on RW1a's reader_inquiry.enabled (its sessions and chips):
            # with that off the key is absent too (review F10).
            **({"recap": {"enabled": config.recap.enabled, "wrap_up_enabled": config.recap.wrap_up_enabled}}
               if (config.recap.enabled or config.recap.wrap_up_enabled) and config.reader_inquiry.enabled
               else {}),
            # Adaptive hints H2b: the practice screen's hint panel. Present only
            # while adaptive hints are on (hints.adaptive_enabled, and the
            # telemetry their rows need), so with them off the snapshot is
            # exactly what it was and the screen is the base's (G-H1).
            **({"hints": {"adaptive_enabled": True,
                          "authored_offer_after_seconds": config.hints.authored_offer_after_seconds,
                          "help_style": config.hints.help_style}}
               if config.hints.adaptive_enabled and config.hints.telemetry_enabled else {}),
            # Adaptive difficulty AD1 (spec §12, §11.2): the practice screen's
            # rating tap and first-hint progress marker. Present only while
            # one of them is on, so with both off the snapshot is exactly
            # what it was before AD1 and the screen sends neither.
            **_adaptive_difficulty_dto(config),
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
                        "animation",
                        "video_generation",
                    )
                },
                "providers": {
                    name: {
                        "type": profile.type,
                        # embedding.model is authoritative for embedding profiles.
                        "model": config.embedding.model if is_embedding_profile(config, name) else profile.model,
                        "base_url": profile.base_url,
                        "api_key_env": profile.api_key_env,
                    }
                    for name, profile in sorted(config.ai.providers.items())
                },
            },
        }
    )


def available_grading_providers(vault: LoadedVault) -> list[str]:
    """Selectable grading backends: configured AI providers, legacy codex, manual.

    Embedding-only and decision-model profiles have no completion transport
    and are never offered.
    """

    config = vault.config
    providers = {name for name in config.ai.providers if is_generation_profile(config, name)}
    return sorted(providers | {"codex"}) + ["manual"]


def runtime_health(
    vault: LoadedVault, repository: Repository, grading_override: str | None = None
) -> dict[str, Any]:
    report = runtime_for_provider(vault.root, vault.config, "codex")
    versions = applied_versions(repository.sqlite_path)
    latest = max((migration.version for migration in discover_migrations()), default=0)
    ai_block = _ai_health(vault, grading_override)
    # Overall settings validity ('no errors / missing fields'), used by the
    # settings chip color — broader than the active-provider readiness above.
    ai_block["settings_ready"] = _settings_ready(vault)
    return versioned(
        {
            "codex": {
                "ready": report.ready,
                "status": report.status,
                "model": vault.config.codex.model,
                "actual_revision": report.actual_revision,
                "base_url": vault.config.codex.base_url,
                "checked_at": utc_now_iso(),
            },
            "ai": ai_block,
            "database": {
                "ok": latest in versions if latest else True,
                "migrations_applied": len(versions),
                "latest_migration": latest,
            },
            "vault_loaded": True,
        }
    )


def _settings_ready(vault: LoadedVault) -> bool:
    """Whether every distinct provider the app routes to is configured/ready.

    Drives the settings chip color ('no errors / missing fields'): the app runs
    work through the per-task routing providers, so a vault that routes to a
    configured OpenRouter backend reads as healthy even when active_provider
    still names an unconfigured codex. Checks are cheap (config/key presence, no
    network) and independent of the grading override. The embedding route counts
    only once embeddings are enabled: a disabled opt-in feature is not a missing
    setting. Each route is checked under its own task, so an embedding profile on
    a generation route (or the reverse) reads as not ready. A list route (PF-b's
    ``pf_proposers`` and ``pf_solver_panel``) is checked profile by profile.
    The same holds for the judgment routes: the router routes count once the
    router has a consumer (R2), the llm_probability routes once the offline
    harness is on."""

    config = vault.config
    routing = config.ai.routing
    probability_on = bool(config.field.enabled and config.field.llm_probability_enabled)
    # Router R2b: the router's routes count once the model mixture serves
    # Today (mvp-0.24, router.mode = "mixture"); before, they have no consumer.
    from learnloop.daily_plan.policy import mixture_active
    from learnloop.daily_plan.router_runtime import models_disabled

    router_on = mixture_active(vault) and not models_disabled()
    routes = {
        (task, name)
        for task in type(routing).model_fields
        if (task != "embedding" or config.embedding.enabled)
        # The llm_probability routes serve only the opt-in offline harness.
        and (task not in {"router_decider", "router_llm"} or router_on)
        and (task not in {"llm_probability_decider", "llm_probability_llm"} or probability_on)
        for name in route_names(getattr(routing, task))
    }
    if router_on:
        # An unset router route resolves (the Decider to its code-default
        # profile, the LLM to the active provider); check what it resolves to.
        from learnloop.ai.routing import provider_for_task

        for task in ("router_decider", "router_llm"):
            name = provider_for_task(config, task).provider_name  # type: ignore[arg-type]
            if name:
                routes.add((task, name))
    if not any(task != "embedding" for task, _name in routes):
        routes.add(("grading", config.ai.active_provider))
    return all(
        runtime_for_provider(vault.root, config, name, task=task).ready for task, name in routes
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
        "checked_at": utc_now_iso(),
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
    resolved = ready_client_for_task(
        vault.root,
        vault.config,
        "grading",
        explicit=grading_override,
    )
    ai_report = resolved.runtime
    return {
        "ready": True if resolved.manual else ai_report.ready,
        "status": "manual" if resolved.manual else ai_report.status,
        "active_provider": "manual" if resolved.manual else ai_report.active_provider,
        "provider_type": ai_report.provider_type,
        "model": ai_report.model,
        "provider_revision": ai_report.provider_revision,
        **base,
        "manual_grading": resolved.manual,
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
    submission_id = None
    declared_stuck = False
    plan_presentation_id = None
    if isinstance(focus, dict):
        practice = focus.get("practice")
        if isinstance(practice, dict):
            hints_used = int(practice.get("hintsUsed") or practice.get("hints_used") or 0)
            declared_stuck = practice.get("declaredStuck") is True
            stored = practice.get("planPresentationId")
            if isinstance(stored, str) and stored.strip():
                plan_presentation_id = stored.strip()
            candidate_submission_id = practice.get("submissionId") or practice.get("submission_id")
            if isinstance(candidate_submission_id, str) and candidate_submission_id.strip():
                submission_id = candidate_submission_id.strip()
    envelope = teach_back_envelope(row.get("current_answer"))
    # UX Phase 4 (Codex review F1): the trace a plain self-grade froze before
    # it showed a full answer, so a resumed draft reopens locked to it.
    from learnloop_sidecar.handlers.sessions import draft_self_grade_disclosure

    disclosure = draft_self_grade_disclosure(row)
    from learnloop_sidecar.handlers.sessions import draft_first_hint_progress

    marker = draft_first_hint_progress(
        focus.get("practice") if isinstance(focus, dict) else None, submission_id
    )
    return to_camel(
        {
            # Adaptive difficulty AD1 (§11.2): the draft's first-hint progress
            # marker, present only when one was kept for this retry key.
            **({"first_hint_progress": marker} if marker is not None else {}),
            "current_practice_item_id": row.get("current_practice_item_id"),
            "current_answer": row.get("current_answer"),
            "hints_used": hints_used,
            "submission_id": submission_id,
            # mvp-0.13: the draft was being written after "I'm stuck".
            "declared_stuck": declared_stuck,
            # Router R2a (review F5): the daily-plan presentation the draft
            # answers, restored with it after a restart.
            "plan_presentation_id": plan_presentation_id,
            "self_grade_disclosure": (
                {
                    "submission_id": disclosure["submission_id"],
                    "answer_md": disclosure["answer_md"],
                    "explanation_md": disclosure["explanation_md"],
                }
                if disclosure is not None
                else None
            ),
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
