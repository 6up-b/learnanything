from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from learnloop import activation_journal
from learnloop.ai.routing import (
    is_embedding_profile, is_generation_profile, ready_client_for_task, route_names, runtime_for_provider,
)
from learnloop.attempts.stuck import stuck_prompt_active
from learnloop.clock import utc_now_iso
from learnloop.db.migrate import applied_versions, discover_migrations, schema_is_current
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
from learnloop.vault.loader import (
    CONTENT_FINGERPRINT_TTL_SECONDS,
    load_practice_item_file,
    load_vault,
    settled_load_vault,
    vault_content_fingerprint,
)
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.repository import open_vault_repository
from learnloop_sidecar.dto import to_camel, versioned
from learnloop_sidecar.background_jobs import BackgroundJobs
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.exam_grading import ExamGradingManager
from learnloop_sidecar.post_attempt_worker import PostAttemptWorker
from learnloop.content.pipeline.jobs import IngestJobManager

_LOGGER = logging.getLogger(__name__)


class LoadedVaultProvider:
    """A context's loaded vault (called) and its reload generation (AD1 fix round 5, V1)."""

    def __init__(self, context: "SidecarContext") -> None:
        self._context = context

    def __call__(self) -> LoadedVault | None:
        return self.snapshot()[0]

    def generation(self) -> int:
        return self.snapshot()[1]

    def snapshot(self) -> tuple[LoadedVault | None, int]:
        """``(vault, generation)``, read together under the publication lock (fix round 6, V1-a)."""

        with self._context._vault_lock:
            return self._context.vault, int(self._context.vault_generation)

    def admit(self, generation: Any) -> bool:
        """Whether the snapshot ``generation`` is still the published one.

        The comparison runs under the publication lock, so no reload is
        published between reading it and the admission it decides; the lock
        is held for this comparison only (fix round 6, V1-a)."""

        with self._context._vault_lock:
            return int(self._context.vault_generation) == generation


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
    # test-thread-leak review F1: the jobs a request starts on a thread of its
    # own (Reader cue discovery, library asks, reading-path judgments, intent
    # routings, hints, coverage). ``close`` cancels and joins them (bounded).
    background_jobs: BackgroundJobs = field(default_factory=BackgroundJobs, repr=False)
    # Adaptive difficulty AD1 (fix round 5, V1): bumped every time the loaded
    # vault object is replaced (a load, a reload, a re-read after recovery or
    # adoption). A background job's protection check reads it before and
    # after it builds the held-out predicate from the loaded vault, and its
    # request and record admissions compare it, so a reload in between is
    # never judged by the vault it replaced.
    vault_generation: int = field(default=0, repr=False)
    # Fix round 6 (V1-a): the vault and its generation are published together
    # under this lock, and read together (``loaded_vault.snapshot()``), so no
    # reader sees the new vault with the old generation. Held for those few
    # instructions only, never across loading, protection, a model call or
    # an SQLite commit.
    _vault_lock: Any = field(default_factory=threading.Lock, repr=False, compare=False)
    # Mobile PR-1 (spec_mobile_tailnet_v1 §3.1): True once the vault was
    # attached by :meth:`load_secondary`. Every later reload of this context
    # stays secondary; only an explicit :meth:`load` makes it primary.
    secondary: bool = field(default=False, repr=False)
    # The content fingerprint the secondary's last load was verified against
    # (the same before and after it), and when the vault was last known to
    # match it (``time.monotonic()``): the start of the G12 freshness window.
    # It advances only on a comparison that matched or a reload that
    # succeeded, so a failed refresh is retried by the next request.
    content_fingerprint: str | None = field(default=None, repr=False)
    _fingerprint_checked_at: float = field(default=float("-inf"), repr=False, compare=False)

    def __setattr__(self, name: str, value: Any) -> None:
        if name != "vault":
            object.__setattr__(self, name, value)
            return
        lock = self.__dict__.get("_vault_lock")
        if lock is None:  # the dataclass's own __init__, before the lock exists
            object.__setattr__(self, name, value)
            object.__setattr__(self, "vault_generation", self.__dict__.get("vault_generation", 0) + 1)
            return
        with lock:
            object.__setattr__(self, name, value)
            object.__setattr__(self, "vault_generation", self.__dict__.get("vault_generation", 0) + 1)

    def load(self, vault_path: str | Path, *, maintenance: bool = True) -> None:
        target = Path(vault_path).resolve()
        # An explicit load is the primary path, whatever this context was before.
        self.secondary = False
        self.content_fingerprint = None
        if self.vault_root is not None and target != self.vault_root:
            # A switch: the previous vault's map builds stop before anything of the new one opens.
            self.map_builds.close()
            # Plan-first transport T1 (review F4): "Use OpenRouter instead" was
            # the previous vault's; the new one is asked again.
            from learnloop.ai import plan_fallback

            plan_fallback.revoke_all()
        # Adaptive difficulty AD1 (Codex review F10): a reload of the same
        # vault compares its items with these, to prepare new revisions.
        previous = self.vault if self.vault_root is not None and target == self.vault_root else None
        vault = load_vault(target)
        # LP-min (a) (claim-fixes re-review F2): an upgrade that died after
        # publishing the successor's config and before its commit left a
        # journal; the opener completes that activation before anything
        # serves or re-projects the vault, or raises InterruptedActivation,
        # and then nothing of this vault is bound or served.
        repository = open_vault_repository(vault.root, VaultPaths(vault.root, vault.config).sqlite_path)
        self.vault_root = target
        self.vault = vault
        self.repository = repository
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
        self.prepare_new_revisions(previous)
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

    def load_secondary(self, vault_path: str | Path, *, bind_ingest: bool = False) -> None:
        """Attach to a vault another process is primary for, writing nothing while attaching.

        Mobile PR-1 (spec_mobile_tailnet_v1 §3.1, §3.3): the mobile host's
        workers, and with storage PR-8 the desktop while the hub service runs,
        attach this way. The vault's files are loaded for reading and the
        database is attached only if its schema is exactly this code's
        (``schema_mismatch`` otherwise: the primary migrates). None of
        :meth:`load`'s primary duties run (storage spec §6.2): no migration,
        facet-identity recovery, content sync, reference-question adoption,
        ingest binding or lease recovery, post-attempt worker, projection
        refresh, cold-probe scheduling, background preparation of new
        revisions, or startup maintenance and its recoveries. Queued work
        stays durable for the primary.

        It is not a read-only mode: handlers called on this context write as
        they do on a primary. Every :meth:`reload` of it (handlers reload
        after their writes) attaches the same way again.

        ``bind_ingest`` is the spec's seam for a restricted ingest binding
        (mobile M3's question-promotion runner, storage PR-8's submit-only
        mode). Neither exists yet, so True is refused rather than binding
        the full runner.
        """

        if bind_ingest:
            raise SidecarError(
                "secondary_ingest_unavailable",
                "A secondary attach cannot bind ingest yet (mobile M3 / storage PR-8).",
            )
        target = Path(vault_path).resolve()
        if self.vault_root is not None and not self.secondary:
            # A primary's ingest runner, worker and background builds are bound
            # to its vault; demoting one is the primary role's job (storage PR-8).
            raise SidecarError(
                "vault_loaded_as_primary",
                "This context holds its vault as the primary; it cannot attach as a secondary.",
            )
        # A settled snapshot only (review F1): the primary rewrites YAML in
        # place, and a source-sets file read mid-rewrite parses as no source
        # sets, so exam protection would vanish from the published vault.
        # ``load_vault`` is looked up at call time (tests patch this module's).
        loaded = settled_load_vault(target, load=lambda root: load_vault(root))
        if not loaded.settled:
            raise SidecarError(
                "vault_unsettled",
                "The vault's files were changing while they were read; try again in a moment.",
                details={"vault_root": str(target)},
            )
        vault = loaded.vault
        sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
        if not schema_is_current(sqlite_path):
            raise SidecarError(
                "schema_mismatch",
                "This vault's database is not at this code's migrations: open the desktop app, or run "
                f"`learnloop doctor --fix-state --vault {target}` once, to migrate it.",
                details={"vault_root": str(target)},
            )
        if self.vault_root is not None and target != self.vault_root:
            # A switch, as in load(): the previous vault's map builds stop and
            # its OpenRouter grants end before the new vault is published.
            self.map_builds.close()
            from learnloop.ai import plan_fallback

            plan_fallback.revoke_all()
        self.vault_root = target
        self.repository = Repository.attach(sqlite_path, read_only=False)
        self.vault = vault
        self.secondary = True
        self.content_fingerprint = loaded.fingerprint
        # The window starts when the snapshot was verified against the files,
        # after the load, never when it began (review F4).
        self._fingerprint_checked_at = loaded.verified_at
        # In-memory only: lets a serve's background builds run in this process.
        self.map_builds.bind(sqlite_path)

    def refresh_if_content_changed(self, *, now: float | None = None) -> bool:
        """Reload a secondary context when another process changed the vault's files.

        Run before each request (mobile spec §3.1, G12). The fingerprint is
        compared at most every ``CONTENT_FINGERPRINT_TTL_SECONDS`` after the
        vault was last known current, so a change is seen by the first request
        at most that long after it. A mismatch reloads with
        :meth:`load_secondary`. True when it reloaded.

        A reload that fails (an unparseable config, a schema this code would
        have to migrate, files still changing) raises, and the window does not
        advance (review F2): every later request compares and tries again, so
        none is served from the old vault while the change stands.
        """

        if not self.secondary or self.vault_root is None:
            raise SidecarError("vault_not_secondary", "Only a secondary attach compares content fingerprints.")
        moment = time.monotonic() if now is None else float(now)
        if moment - self._fingerprint_checked_at < CONTENT_FINGERPRINT_TTL_SECONDS:
            return False
        if vault_content_fingerprint(self.vault_root) == self.content_fingerprint:
            self._fingerprint_checked_at = moment
            return False
        self.load_secondary(self.vault_root)  # sets the window from its own verification
        return True

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

    def prepare_new_revisions(self, previous: LoadedVault | None, item_ids: list[str] | None = None) -> None:
        """Adaptive difficulty AD1 (spec §7.2, §8.2; Codex review F10): the
        feature audit and ``llm_v1:item`` of item revisions published,
        imported or edited since the last load (or the watcher's changed
        items), in the background on the vault's build registry. Never
        blocks or fails the reload."""

        if self.vault is None or self.repository is None:
            return
        try:
            from learnloop.adaptive_difficulty.background import schedule_new_revisions

            schedule_new_revisions(previous, self.vault, self.repository.sqlite_path, item_ids=item_ids,
                                   clients=getattr(self, "ad_clients", None), builds=self.map_builds,
                                   live_vault=self.loaded_vault)
        except Exception:  # noqa: BLE001 - never block a reload
            _LOGGER.warning("could not schedule AD preparation of new item revisions", exc_info=True)
        if previous is None and item_ids is None:
            return  # a first open schedules nothing (the owner's backfill comes first)
        try:
            # AD2+AD3 (spec §5.10): a subject whose content changed is re-proposed
            # (only after the owner's backfill adopted a coupling version for it).
            from learnloop.adaptive_difficulty.relatedness_jobs import schedule_reproposals

            clients = getattr(self, "ad_clients", None)
            schedule_reproposals(self.vault, self.repository.sqlite_path,
                                 client=getattr(clients, "llm", None) if clients is not None else None,
                                 builds=self.map_builds, live_vault=self.loaded_vault)
        except Exception:  # noqa: BLE001 - never block a reload
            _LOGGER.warning("could not schedule AD relatedness re-proposals", exc_info=True)

    @property
    def loaded_vault(self) -> "LoadedVaultProvider":
        """The provider of the vault loaded now (adaptive difficulty AD1, fix
        rounds 4 and 5, V1): a background job checks its requests against this
        vault's held-out predicate at each check, not the one it was started
        with, so a same-vault reload's source-set or exam-scope edit is seen;
        its ``generation()`` is :attr:`vault_generation`."""

        return LoadedVaultProvider(self)

    def close_background_builds(self) -> bool:
        """Drain the approach-map builds (shutdown and EOF; bounded, never hangs)."""

        return self.map_builds.close()

    def close(self) -> None:
        """Stop every background thread this context owns (the ``shutdown``
        RPC, EOF, and whoever else ends a context: a test's teardown, a host
        that drops it).

        The jobs requests started (:attr:`background_jobs`: Reader cue
        discovery, library asks, reading-path judgments, intent routings,
        hints, coverage) are cancelled first, before anything is joined: none
        sends another model request from then on (review F1). Then the ingest
        drain, its quick checks and the reading sweep, the exam graders, the
        post-attempt worker's three slots (a gap or diagnosis job in flight
        stops before its next paid request, review F2) and the approach-map
        builds are each told to stop and joined for a bounded time (never
        hangs), and last the cancelled jobs are joined, bounded too. A thread
        that outlived its context kept polling the vault it was started for:
        in one test process that was hundreds of threads (test-thread-leak).
        Idempotent; a later ``load``, request or submit starts work again, as
        after ``shutdown``."""

        self.background_jobs.cancel()
        self.exam_grading.shutdown()
        self.ingest_jobs.shutdown()
        self.post_attempt_worker.shutdown()
        self.close_background_builds()
        self.background_jobs.close()

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
        if self.secondary:
            # A secondary never takes on primary duties by reloading
            # (mobile PR-1; storage spec §6.2: first attach, reload and switch).
            self.load_secondary(self.vault_root)
            return
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
        from learnloop.substrate.state_sync import reconcile_practice_item_state

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
                    # Mobile PR-2: the same targeted write as a full sync, so an
                    # attempt committed by another process between this read
                    # and the write keeps its scheduling fields.
                    _outcome, active = reconcile_practice_item_state(
                        repository,
                        item.id,
                        item,
                        state=repository.practice_item_state(item.id),
                        review_parked=review_parked,
                        measurement_superseded=measurement_superseded,
                        content_hash=practice_item_hash(item),
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

        if changed:
            self.prepare_new_revisions(None, item_ids=changed)
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


def _complete_interrupted_activation(vault_root: Path) -> None:
    """Complete an activation a dead upgrade left journalled (LP-min (a) re-review F2; mvp-0.34 to mvp-0.38 too).

    Installed for the desktop sidecar (``learnloop.activation_journal``): the
    opener in :meth:`SidecarContext.load` completes it before anything serves
    or re-projects the vault, or raises and nothing of the vault is bound."""

    # The chain's latest upgrade completes its own journal and hands an
    # earlier link's to that link (rebuild equivalence's landing; Reader CA2's
    # mvp-0.35 at the batch landing; the kept replaced claims' mvp-0.36;
    # mobile PR-4's mvp-0.37; the cold-retry reschedule's mvp-0.38).
    from learnloop.cold_retry_reschedule_upgrade import complete_interrupted_activation

    complete_interrupted_activation(vault_root)


activation_journal.install_completer(_complete_interrupted_activation)


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


def _cold_help_converts(vault: LoadedVault) -> bool:
    from learnloop.serve_eligibility import help_converts_active

    return help_converts_active(vault)


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
            # UX Phase 2's kill switch (display only): the four-place shell,
            # or "classic" for the ten-tab shell as it was.
            "ui": {"practice_feedback": config.ui.practice_feedback, "shell": config.ui.shell},
            # Reader workbench RW2a's kill switch: present only while on, so
            # with it off the snapshot is exactly what it was before RW2a.
            # Reader workbench RW2b's kill switch rides inside it: "Check my
            # work" and the help ladder, ``help`` present only while
            # workbench.help_enabled is on (absent, RW2a's workbench renders
            # exactly as before); ``bridge``: "compare with the book". The
            # ladder's hints need the hint service (the ``hints`` key below).
            **({"workbench": {"enabled": True, "open_session_days": config.workbench.open_session_days,
                              **({"help": {"enabled": True, "bridge": bool(config.workbench.bridge_enabled),
                                           # RW2b fix round 13: the symbolic switch, so a
                                           # mounted workbench gates marks already shown.
                                           "symbolic": bool(config.workbench.symbolic_checks_enabled),
                                           # Reader RW2c's switches, each present only
                                           # while on (off: the snapshot is as before).
                                           **({"examples": True} if config.workbench.examples_enabled
                                              else {}),
                                           **({"compare_methods": True}
                                              if config.workbench.compare_methods_enabled else {}),
                                           **({"passage_draw": True} if config.workbench.passage_draw_enabled
                                              else {})}}
                                 if config.workbench.help_enabled else {})}}
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
            # Reader CA2 (ux_reader_compare_ask_v1 §7): the one Ask panel.
            # Present only while ask.panel_enabled is on, so with it off the
            # snapshot is exactly what it was and every host is the overlay's.
            # ``help_style`` is the stored preference Ask's mode follows;
            # ``cold_help_converts`` says the successor's one help rule is live
            # (the placeholder and labels on a check on your own say it).
            **({"ask": {"panel_enabled": True, "help_style": config.hints.help_style,
                        "cold_help_converts": _cold_help_converts(vault)}}
               if config.ask.panel_enabled else {}),
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
    """Selectable grading backends: configured AI providers, manual.

    Embedding-only and decision-model profiles have no completion transport
    and are never offered. A Codex (agent-harness) profile, and the legacy
    ``codex`` name, are offered only with ``ai.agent_harness_opt_in``
    (plan-first transport T1, review F9): without it they are always refused.
    """

    from learnloop.ai.agent_harness import is_agent_harness_profile
    from learnloop.config import CODEX_PROVIDER_NAMES

    config = vault.config
    opt_in = bool(config.ai.agent_harness_opt_in)
    providers = {
        name for name in config.ai.providers
        if is_generation_profile(config, name)
        and (opt_in or not (name in CODEX_PROVIDER_NAMES or is_agent_harness_profile(config.ai.providers[name])))
    }
    if opt_in:
        providers.add("codex")
    return sorted(providers) + ["manual"]


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
    from learnloop.ai.plan_fallback import quiet

    # A health line, not a feature the learner used: no OpenRouter offer.
    with quiet():
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
    from learnloop_sidecar.handlers.sessions import draft_first_hint_progress, draft_hint_seen, draft_page_seen

    marker = draft_first_hint_progress(
        focus.get("practice") if isinstance(focus, dict) else None, submission_id
    )
    hint_seen = draft_hint_seen(focus.get("practice") if isinstance(focus, dict) else None, submission_id)
    page_seen = draft_page_seen(focus.get("practice") if isinstance(focus, dict) else None, submission_id)
    from learnloop_sidecar.handlers.sessions import draft_earlier_opened

    current_item = row.get("current_practice_item_id")
    earlier_opened = bool(current_item) and draft_earlier_opened(row, practice_item_id=str(current_item))
    return to_camel(
        {
            # Reader CA2 (Codex review F1): *earlier on this question* was
            # opened on this draft (its one hint is the submit's, server-side).
            **({"earlier_opened": True} if earlier_opened else {}),
            # Adaptive difficulty AD1 (§11.2): the draft's first-hint progress
            # marker, present only when one was kept for this retry key.
            **({"first_hint_progress": marker} if marker is not None else {}),
            # AD1 fix round 5 (V4): a hint was seen on this draft; present
            # only when one was, for this retry key.
            **({"hint_seen": True} if hint_seen else {}),
            # Reader CA1: the original page was opened before Submit on this
            # draft (it counts as the book); present only when it was.
            **({"page_seen": True} if page_seen else {}),
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
