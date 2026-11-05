---
title: "learnloop_sidecar.context"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/context.py"
source_paths:
  - "src/learnloop_sidecar/context.py"
source_commit: "eff30f881a7d3ea5b06e0a10156b37049285cf52"
source_commit_timestamp: "2026-11-04T20:48:34-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop_sidecar.context module"
  - "src/learnloop_sidecar/context.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar"
---

# `learnloop_sidecar.context`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps context behavior inside its owning package, [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]]. Its public surface centers on `LoadedVaultProvider`, `SidecarContext`, `subjects_practised_first`, `vault_summary`, `config_dto`, `available_grading_providers`, `runtime_health`, `session_snapshot` and 3 more public symbols.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/context.py](../../../../../src/learnloop_sidecar/context.py) |
| Source lines | 1372 |
| Owning package | [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `eff30f881a7d3ea5b06e0a10156b37049285cf52` |
| Commit timestamp | `2026-11-04T20:48:34-05:00` |

## Public API

- `class LoadedVaultProvider` ([source](../../../../../src/learnloop_sidecar/context.py), line 54) — A context's loaded vault (called) and its reload generation (AD1 fix round 5, V1).
  - `__init__(self, context: 'SidecarContext') -> None` (line 57; internal)
  - `__call__(self) -> LoadedVault | None` (line 60; internal)
  - `generation(self) -> int` (line 63; public)
  - `snapshot(self) -> tuple[LoadedVault | None, int]` (line 66; public) — ``(vault, generation)``, read together under the publication lock (fix round 6, V1-a).
  - `admit(self, generation: Any) -> bool` (line 72; public) — Whether the snapshot ``generation`` is still the published one.
- `class SidecarContext` ([source](../../../../../src/learnloop_sidecar/context.py), line 84)
  - `origin_device_id(self) -> str | None` (line 146; public) — The device a session-scoped request comes from; None is the desktop.
  - `acting_as(self, origin: RequestOrigin | None) -> Iterator[None]` (line 152; public) — The one way a host sets the origin: around one call, restored after it.
  - `__setattr__(self, name: str, value: Any) -> None` (line 164; internal)
  - `load(self, vault_path: str | Path, *, maintenance: bool=True) -> None` (line 177; public)
  - `load_secondary(self, vault_path: str | Path, *, bind_ingest: bool=False) -> None` (line 287; public) — Attach to a vault another process is primary for, writing nothing while attaching.
  - `refresh_if_content_changed(self, *, now: float | None=None) -> bool` (line 364; public) — Reload a secondary context when another process changed the vault's files.
  - `reconcile_hint_work(self) -> None` (line 390; public) — Adaptive hints H2b, at a vault's open (review F4, F5): queue the replies to hints and discriminating answers whose learner-text job never committed, and start, in the background, the outcome placements of hinted attempts that never got one (a process that ended before scheduling…
  - `prepare_new_revisions(self, previous: LoadedVault | None, item_ids: list[str] | None=None) -> None` (line 423; public) — Adaptive difficulty AD1 (spec §7.2, §8.2; Codex review F10): the feature audit and ``llm_v1:item`` of item revisions published, imported or edited since the last load (or the watcher's changed items), in the background on the vault's build registry.
  - `loaded_vault(self) -> 'LoadedVaultProvider'` (line 455; public) — The provider of the vault loaded now (adaptive difficulty AD1, fix rounds 4 and 5, V1): a background job checks its requests against this vault's held-out predicate at each check, not the one it was started with, so a same-vault reload's source-set or exam-scope edit is seen; it…
  - `close_background_builds(self) -> bool` (line 464; public) — Drain the approach-map builds (shutdown and EOF; bounded, never hangs).
  - `close(self) -> None` (line 469; public) — Stop every background thread this context owns (the ``shutdown`` RPC, EOF, and whoever else ends a context: a test's teardown, a host that drops it).
  - `_prefetch_gaps(self) -> None` (line 498; internal)
  - `_worker_target(self) -> tuple[LoadedVault, Path] | None` (line 503; internal)
  - `recover_import_key_checks(self) -> None` (line 508; public) — Resume the key checks of imported exercises a dead process left incomplete.
  - `settle_followup_workflows_when_off(self) -> None` (line 552; public)
  - `resume_post_attempt_jobs(self) -> None` (line 564; public) — Wake the worker when the durable queue holds unfinished jobs.
  - `reload(self, *, maintenance: bool=True) -> None` (line 584; public)
  - `refresh_vault_files(self, relative_paths: list[str], *, expected_root: str | Path | None=None) -> dict[str, Any]` (line 594; public) — Incrementally refresh watcher-reported Practice Item files.
  - `require_vault(self) -> tuple[LoadedVault, Repository]` (line 762; public)
  - `app_snapshot(self) -> dict[str, Any]` (line 767; public)
- `subjects_practised_first(vault: LoadedVault) -> list[str]` ([source](../../../../../src/learnloop_sidecar/context.py), line 847) — Subject ids, the ones the learner practises most first, then by name.
- `vault_summary(vault: LoadedVault) -> dict[str, Any]` ([source](../../../../../src/learnloop_sidecar/context.py), line 870)
- `config_dto(vault: LoadedVault) -> dict[str, Any]` ([source](../../../../../src/learnloop_sidecar/context.py), line 933)
- `available_grading_providers(vault: LoadedVault) -> list[str]` ([source](../../../../../src/learnloop_sidecar/context.py), line 1067) — Selectable grading backends: configured AI providers, manual.
- `runtime_health(vault: LoadedVault, repository: Repository, grading_override: str | None=None) -> dict[str, Any]` ([source](../../../../../src/learnloop_sidecar/context.py), line 1091)
- `session_snapshot(repository: Repository, session_id: str) -> dict[str, Any] | None` ([source](../../../../../src/learnloop_sidecar/context.py), line 1222)
- `checkpoint_dto(row: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../src/learnloop_sidecar/context.py), line 1253)
- `teach_back_envelope(current_answer: Any) -> dict[str, Any] | None` ([source](../../../../../src/learnloop_sidecar/context.py), line 1330) — Parse a teach-back conversation envelope from checkpoint current_answer.
- `mastery_dto(repository: Repository, learning_object_id: str, vault: LoadedVault | None=None) -> dict[str, Any] | None` ([source](../../../../../src/learnloop_sidecar/context.py), line 1354)

### Module constants

- `_LOGGER` ([src/learnloop_sidecar/context.py](../../../../../src/learnloop_sidecar/context.py), line 51)

## Internal implementation anchors

- `_forget_reading_choice() -> None` ([source](../../../../../src/learnloop_sidecar/context.py), line 784) — Curriculum C1 (fix round 4): drop the plan's memoized reading choice and close its database watcher when a context loads, attaches, switches or closes, so a database restored at the same path is never watched through the old file.
- `_complete_interrupted_activation(vault_root: Path) -> None` ([source](../../../../../src/learnloop_sidecar/context.py), line 794) — Complete an activation a dead upgrade left journalled (LP-min (a) re-review F2; mvp-0.34 to mvp-0.42 too).
- `_recover_facet_identity_actions(vault_root: Path, repository: Repository) -> bool` ([source](../../../../../src/learnloop_sidecar/context.py), line 815) — Finish interrupted facet merges/undos; True when the vault files may have changed.
- `_adopt_reference_questions(vault: LoadedVault, repository: Repository) -> bool` ([source](../../../../../src/learnloop_sidecar/context.py), line 837) — Run the reader's reference-question adoption sweep; never block a load.
- `_adaptive_difficulty_dto(config: Any) -> dict[str, Any]` ([source](../../../../../src/learnloop_sidecar/context.py), line 896)
- `_figures_help(vault: LoadedVault) -> bool` ([source](../../../../../src/learnloop_sidecar/context.py), line 905)
- `_cold_help_converts(vault: LoadedVault) -> bool` ([source](../../../../../src/learnloop_sidecar/context.py), line 911)
- `_lessons_active(vault: LoadedVault) -> bool` ([source](../../../../../src/learnloop_sidecar/context.py), line 917)
- `_teacher_dto(vault: LoadedVault) -> dict[str, Any]` ([source](../../../../../src/learnloop_sidecar/context.py), line 923) — TE1's ``lessons`` while lessons may open; TE1b's ``suggestions`` while Today may suggest one.
- `_settings_ready(vault: LoadedVault) -> bool` ([source](../../../../../src/learnloop_sidecar/context.py), line 1122) — Whether every distinct provider the app routes to is configured/ready.
- `_ai_health(vault: LoadedVault, grading_override: str | None) -> dict[str, Any]` ([source](../../../../../src/learnloop_sidecar/context.py), line 1172) — The health.ai dto, honoring the runtime grading override.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/adaptive_difficulty|learnloop_sidecar.handlers.adaptive_difficulty]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/adjudication|learnloop_sidecar.handlers.adjudication]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]] — imports `SidecarContext`, `available_grading_providers`; statically calls `available_grading_providers`
- [[Reference/Modules/learnloop_sidecar/handlers/animation|learnloop_sidecar.handlers.animation]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/app|learnloop_sidecar.handlers.app]] — imports `SidecarContext`, `config_dto`, `runtime_health`, `vault_summary`; statically calls `config_dto`, `runtime_health`, `vault_summary`
- [[Reference/Modules/learnloop_sidecar/handlers/as_printed|learnloop_sidecar.handlers.as_printed]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/calibration|learnloop_sidecar.handlers.calibration]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/capture|learnloop_sidecar.handlers.capture]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/chatgpt_plan|learnloop_sidecar.handlers.chatgpt_plan]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/claims|learnloop_sidecar.handlers.claims]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/cli|learnloop_sidecar.handlers.cli]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/compare_scope|learnloop_sidecar.handlers.compare_scope]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/correspondents|learnloop_sidecar.handlers.correspondents]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/deliverables|learnloop_sidecar.handlers.deliverables]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/diagnosis_card|learnloop_sidecar.handlers.diagnosis_card]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/diagnostic|learnloop_sidecar.handlers.diagnostic]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/epigraphs|learnloop_sidecar.handlers.epigraphs]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/facet_detail|learnloop_sidecar.handlers.facet_detail]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/facet_identity|learnloop_sidecar.handlers.facet_identity]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/facets|learnloop_sidecar.handlers.facets]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/first_run|learnloop_sidecar.handlers.first_run]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/followup|learnloop_sidecar.handlers.followup]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/golden_path|learnloop_sidecar.handlers.golden_path]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/golden_path_assessment|learnloop_sidecar.handlers.golden_path_assessment]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/graph|learnloop_sidecar.handlers.graph]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/graph_edit|learnloop_sidecar.handlers.graph_edit]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/inspector|learnloop_sidecar.handlers.inspector]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/intent|learnloop_sidecar.handlers.intent]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/item_authoring|learnloop_sidecar.handlers.item_authoring]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/kept_comparisons|learnloop_sidecar.handlers.kept_comparisons]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_model|learnloop_sidecar.handlers.knowledge_model]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/ladder|learnloop_sidecar.handlers.ladder]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/learner_gaps|learnloop_sidecar.handlers.learner_gaps]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/lesson|learnloop_sidecar.handlers.lesson]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/library|learnloop_sidecar.handlers.library]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/library_exercises|learnloop_sidecar.handlers.library_exercises]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/notes|learnloop_sidecar.handlers.notes]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/placement|learnloop_sidecar.handlers.placement]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/practice_index|learnloop_sidecar.handlers.practice_index]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/proposals|learnloop_sidecar.handlers.proposals]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/provenance|learnloop_sidecar.handlers.provenance]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_cue_discovery|learnloop_sidecar.handlers.reader_cue_discovery]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_followups|learnloop_sidecar.handlers.reader_followups]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_intent|learnloop_sidecar.handlers.reader_intent]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/reading_paths|learnloop_sidecar.handlers.reading_paths]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/recap|learnloop_sidecar.handlers.recap]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/registry|learnloop_sidecar.handlers.registry]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/remediation|learnloop_sidecar.handlers.remediation]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/review|learnloop_sidecar.handlers.review]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `mastery_dto`; statically calls `mastery_dto`
- [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]] — imports `SidecarContext`, `session_snapshot`; statically calls `session_snapshot`
- [[Reference/Modules/learnloop_sidecar/handlers/settings|learnloop_sidecar.handlers.settings]] — imports `SidecarContext`, `runtime_health`; statically calls `runtime_health`
- [[Reference/Modules/learnloop_sidecar/handlers/side_by_side|learnloop_sidecar.handlers.side_by_side]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/source_service|learnloop_sidecar.handlers.source_service]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/sqlite_admin|learnloop_sidecar.handlers.sqlite_admin]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]] — imports `SidecarContext`, `teach_back_envelope`; statically calls `teach_back_envelope`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/vault|learnloop_sidecar.handlers.vault]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] — imports `SidecarContext`, `session_snapshot`; statically calls `session_snapshot`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_rw2c|learnloop_sidecar.handlers.workbench_rw2c]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/server|learnloop_sidecar.server]] — imports `SidecarContext`; statically calls `SidecarContext`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/activation_journal|learnloop.activation_journal]] — imports `module`; calls `install_completer`
- [[Reference/Modules/learnloop/adaptive_difficulty/background|learnloop.adaptive_difficulty.background]] — imports `schedule_new_revisions`; calls `schedule_new_revisions`
- [[Reference/Modules/learnloop/adaptive_difficulty/relatedness_jobs|learnloop.adaptive_difficulty.relatedness_jobs]] — imports `schedule_reproposals`; calls `schedule_reproposals`
- [[Reference/Modules/learnloop/adaptive_difficulty/switches|learnloop.adaptive_difficulty.switches]] — imports `rating_tap_enabled`, `receipts_enabled`; calls `rating_tap_enabled`, `receipts_enabled`
- [[Reference/Modules/learnloop/ai/agent_harness|learnloop.ai.agent_harness]] — imports `is_agent_harness_profile`; calls `is_agent_harness_profile`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`, `quiet`; calls `quiet`, `revoke_all`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `is_embedding_profile`, `is_generation_profile`, `provider_for_task`, `ready_client_for_task`, `route_names`, `runtime_for_provider`; calls `is_embedding_profile`, `is_generation_profile`, `provider_for_task`, `ready_client_for_task`, `route_names`, `runtime_for_provider`
- [[Reference/Modules/learnloop/attempts/stuck|learnloop.attempts.stuck]] — imports `stuck_prompt_active`; calls `stuck_prompt_active`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `CODEX_PROVIDER_NAMES`
- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `CHECK_LEASE_SECONDS`, `pending_import_checks`, `recover_import_checks`; calls `pending_import_checks`, `recover_import_checks`
- [[Reference/Modules/learnloop/content/facet_identity/actions|learnloop.content.facet_identity.actions]] — imports `recover_interrupted_actions`; calls `recover_interrupted_actions`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `reconcile_reading_builds`; calls `reconcile_reading_builds`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `IngestJobManager`
- [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]] — imports `suggestions_active`; calls `suggestions_active`
- [[Reference/Modules/learnloop/daily_plan/policy|learnloop.daily_plan.policy]] — imports `mixture_active`; calls `mixture_active`
- [[Reference/Modules/learnloop/daily_plan/reading_choice|learnloop.daily_plan.reading_choice]] — imports `module`; calls `forget`
- [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]] — imports `models_disabled`; calls `models_disabled`
- [[Reference/Modules/learnloop/db/migrate|learnloop.db.migrate]] — imports `applied_versions`, `discover_migrations`, `schema_is_current`; calls `applied_versions`, `discover_migrations`, `schema_is_current`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `pending_review_instance_ids`; calls `pending_review_instance_ids`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]] — imports `enqueue_learner_notes`, `pending_jobs`, `reconcile_hint_feedback`; calls `enqueue_learner_notes`, `pending_jobs`, `reconcile_hint_feedback`
- [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]] — imports `help_kind_enabled`; calls `help_kind_enabled`
- [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]] — imports `recover_pending_workflows`; calls `recover_pending_workflows`
- [[Reference/Modules/learnloop/followup_serve/queue|learnloop.followup_serve.queue]] — imports `pending_jobs`; calls `pending_jobs`
- [[Reference/Modules/learnloop/followup_serve/workflow|learnloop.followup_serve.workflow]] — imports `settle_open_when_off`; calls `settle_open_when_off`
- [[Reference/Modules/learnloop/goals/certification_cold_probe|learnloop.goals.certification_cold_probe]] — imports `schedule_certification_cold_probes`; calls `schedule_certification_cold_probes`
- [[Reference/Modules/learnloop/hints/map_builder|learnloop.hints.map_builder]] — imports `BackgroundBuilds`
- [[Reference/Modules/learnloop/hints/outcome|learnloop.hints.outcome]] — imports `reconcile_outcome_placements`; calls `reconcile_outcome_placements`
- [[Reference/Modules/learnloop/interval_factor_upgrade|learnloop.interval_factor_upgrade]] — imports `complete_interrupted_activation`; calls `complete_interrupted_activation`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `mastery_diagnostic_view`; calls `mastery_diagnostic_view`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `display_mastery`; calls `display_mastery`
- [[Reference/Modules/learnloop/ops/startup|learnloop.ops.startup]] — imports `run_startup_maintenance`; calls `run_startup_maintenance`
- [[Reference/Modules/learnloop/reader/reader_authoring|learnloop.reader.reader_authoring]] — imports `adopt_reference_questions`; calls `adopt_reference_questions`
- [[Reference/Modules/learnloop/router_objective/goal_lifecycle|learnloop.router_objective.goal_lifecycle]] — imports `module`; calls `sweep`
- [[Reference/Modules/learnloop/serve_eligibility|learnloop.serve_eligibility]] — imports `help_converts_active`; calls `help_converts_active`
- [[Reference/Modules/learnloop/substrate/canonical_projection_rollout|learnloop.substrate.canonical_projection_rollout]] — imports `forget_fold_memo`, `refresh_canonical_projection_on_startup`; calls `forget_fold_memo`, `refresh_canonical_projection_on_startup`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `reconcile_practice_item_state`, `sync_vault_state`; calls `reconcile_practice_item_state`, `sync_vault_state`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `lessons_active`; calls `lessons_active`
- [[Reference/Modules/learnloop/vault/hashes|learnloop.vault.hashes]] — imports `practice_item_hash`; calls `practice_item_hash`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `CONTENT_FINGERPRINT_TTL_SECONDS`, `load_practice_item_file`, `load_vault`, `settled_load_vault`, `vault_content_fingerprint`; calls `load_practice_item_file`, `load_vault`, `settled_load_vault`, `vault_content_fingerprint`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `open_vault_repository`; calls `open_vault_repository`
- [[Reference/Modules/learnloop_sidecar/background_jobs|learnloop_sidecar.background_jobs]] — imports `BackgroundJobs`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `to_camel`, `versioned`; calls `to_camel`, `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/exam_grading|learnloop_sidecar.exam_grading]] — imports `ExamGradingManager`
- [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]] — imports `draft_earlier_opened`, `draft_first_hint_progress`, `draft_hint_seen`, `draft_page_seen`, `draft_self_grade_disclosure`; calls `draft_earlier_opened`, `draft_first_hint_progress`, `draft_hint_seen`, `draft_page_seen`, `draft_self_grade_disclosure`
- [[Reference/Modules/learnloop_sidecar/post_attempt_worker|learnloop_sidecar.post_attempt_worker]] — imports `PostAttemptWorker`
- [[Reference/Modules/learnloop_sidecar/prefetch_runtime|learnloop_sidecar.prefetch_runtime]] — imports `notify`; calls `notify`
- [[Reference/Modules/learnloop_sidecar/request_origin|learnloop_sidecar.request_origin]] — imports `RequestOrigin`, `bump_for_host`; calls `bump_for_host`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `json`, `logging`, `pathlib`, `threading`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/adaptive_difficulty|learnloop_sidecar.handlers.adaptive_difficulty]], [[Reference/Modules/learnloop_sidecar/handlers/adjudication|learnloop_sidecar.handlers.adjudication]], [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]], [[Reference/Modules/learnloop_sidecar/handlers/animation|learnloop_sidecar.handlers.animation]], [[Reference/Modules/learnloop_sidecar/handlers/app|learnloop_sidecar.handlers.app]] and 70 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/reading_path_fixtures.py](../../../../../tests/reading_path_fixtures.py) — direct import
- [tests/recap_fixtures.py](../../../../../tests/recap_fixtures.py) — direct import
- [tests/rw2b_fix10_base_sequence.py](../../../../../tests/rw2b_fix10_base_sequence.py) — direct import
- [tests/rw2b_fix11_base_sequence.py](../../../../../tests/rw2b_fix11_base_sequence.py) — direct import
- [tests/rw2c_base_sequence.py](../../../../../tests/rw2c_base_sequence.py) — direct import
- [tests/rw2c_state_parity.py](../../../../../tests/rw2c_state_parity.py) — direct import
- [tests/test_ad1_attempt_columns.py](../../../../../tests/test_ad1_attempt_columns.py) — direct import
  - `test_the_app_snapshot_names_the_client_switches_only_while_on`
  - `test_the_rating_tap_switch_stores_nothing`
- [tests/test_ad1_codex_rereview_fixes.py](../../../../../tests/test_ad1_codex_rereview_fixes.py) — direct import
  - `test_an_edit_during_a_preparation_prepares_the_new_revision_too`
- [tests/test_ad1_codex_review_fixes.py](../../../../../tests/test_ad1_codex_review_fixes.py) — direct import
  - `test_a_reload_prepares_the_revisions_published_since_the_last_load`
- [tests/test_ad1_fix_round4.py](../../../../../tests/test_ad1_fix_round4.py) — direct import
  - `test_a_same_vault_reload_adding_an_exam_scope_refuses_the_next_request_and_the_record`
- [tests/test_ad1_fix_round5.py](../../../../../tests/test_ad1_fix_round5.py) — direct import
  - `test_a_reload_while_protection_is_built_is_never_judged_by_the_vault_it_replaced`
- [tests/test_ad1_fix_round6.py](../../../../../tests/test_ad1_fix_round6.py) — direct import
  - `test_a_publication_paused_between_assignment_and_bump_is_never_admitted`
- [tests/test_ad23_contract.py](../../../../../tests/test_ad23_contract.py) — direct import
  - `test_the_sidecar_uptake_callback_answers_a_no_op_with_ad_off`
- [tests/test_ad23_fix_review.py](../../../../../tests/test_ad23_fix_review.py) — direct import
  - `test_the_offer_names_the_sections_other_question_and_its_answer_is_the_extra`
  - `test_the_sidecar_queues_a_serve_commission_after_the_serve`
- [tests/test_ad23_intent_compose.py](../../../../../tests/test_ad23_intent_compose.py) — direct import
  - `test_the_real_scheduler_lane_with_commitments`
- [tests/test_ad23_successor.py](../../../../../tests/test_ad23_successor.py) — direct import
- [tests/test_ad2_serving.py](../../../../../tests/test_ad2_serving.py) — direct import
  - `test_why_this_item_names_the_draw_that_chose_it`
- [tests/test_ad3_dose_arm.py](../../../../../tests/test_ad3_dose_arm.py) — direct import
  - `test_switch_off_is_todays_reader_exactly`
- [tests/test_adaptive_difficulty_ad1.py](../../../../../tests/test_adaptive_difficulty_ad1.py) — direct import
  - `test_ad1_switches_restore_predecessor`
- [tests/test_approach_map_replay.py](../../../../../tests/test_approach_map_replay.py) — direct import
- [tests/test_approach_maps.py](../../../../../tests/test_approach_maps.py) — direct import
- [tests/test_batch3_landing.py](../../../../../tests/test_batch3_landing.py) — direct import
- [tests/test_canonical_projection_fold_skip.py](../../../../../tests/test_canonical_projection_fold_skip.py) — direct import
  - `test_a_sidecar_reload_after_nothing_happened_skips_the_fold`
- [tests/test_canonical_projection_rollout.py](../../../../../tests/test_canonical_projection_rollout.py) — direct import
  - `test_fresh_startup_stamps_a_silent_projection_baseline_once`
  - `test_projection_upgrade_stays_silent_while_vault_has_no_attempts`
  - `test_startup_records_one_recalibration_for_an_unstamped_practised_vault`
- [tests/test_capture_desktop.py](../../../../../tests/test_capture_desktop.py) — direct import
- [tests/test_chatgpt_plan_sidecar.py](../../../../../tests/test_chatgpt_plan_sidecar.py) — direct import
  - `test_cancel_and_failure_are_reported`
  - `test_resume_clears_a_pause`
  - `test_settings_payload_lists_plan_profiles_and_their_routes`
  - `test_sign_in_from_the_desktop_without_a_vault`
- [tests/test_config_refactor.py](../../../../../tests/test_config_refactor.py) — direct import
  - `test_legacy_codex_is_input_only_and_sidecar_does_not_reexport_it`
- [tests/test_curriculum_c1_landing.py](../../../../../tests/test_curriculum_c1_landing.py) — direct import
  - `test_ii_the_desktop_completion_is_c1s`
- [tests/test_daily_loop_lo_lifecycle_serving.py](../../../../../tests/test_daily_loop_lo_lifecycle_serving.py) — direct import
- [tests/test_daily_loop_reader_retire.py](../../../../../tests/test_daily_loop_reader_retire.py) — direct import
  - `test_sidecar_retire_takes_the_card_out_of_today`
- [tests/test_daily_loop_reentry_break.py](../../../../../tests/test_daily_loop_reentry_break.py) — direct import
- [tests/test_daily_loop_reentry_cap.py](../../../../../tests/test_daily_loop_reentry_cap.py) — direct import
- [tests/test_daily_loop_reference_adoption.py](../../../../../tests/test_daily_loop_reference_adoption.py) — direct import
  - `test_adoption_kill_switch_restores_baseline_and_keeps_adopted_cards`
  - `test_sidecar_reload_adopts_and_today_serves_it`
- [tests/test_daily_loop_start_minutes.py](../../../../../tests/test_daily_loop_start_minutes.py) — direct import
- [tests/test_daily_plan_composition.py](../../../../../tests/test_daily_plan_composition.py) — direct import
  - `test_an_empty_stuck_answer_on_a_plan_item_is_done_and_labelled_daily_plan`
- [tests/test_daily_plan_kill_switch.py](../../../../../tests/test_daily_plan_kill_switch.py) — direct import
  - `test_headline_switch_hides_only_the_headline`
  - `test_plan_off_rows_serve_the_open_queue_whatever_the_router`
  - `test_the_plan_needs_the_successor_version`
- [tests/test_daily_plan_reading.py](../../../../../tests/test_daily_plan_reading.py) — direct import
- [tests/test_daily_plan_reentry.py](../../../../../tests/test_daily_plan_reentry.py) — direct import
  - `test_the_reentry_panel_is_survival_first_with_no_overdue_count_or_streak`
  - `test_with_the_plan_off_the_dl0_queue_cap_still_applies_and_with_it_on_the_list_is_whole`
- [tests/test_daily_plan_review_regressions.py](../../../../../tests/test_daily_plan_review_regressions.py) — direct import
  - `test_f13_a_pick_ignores_a_used_or_unshown_offer`
  - `test_f5_plan_rpcs_finalize_no_offer_and_picks_keep_the_list_offer`
- [tests/test_daily_plan_rpc.py](../../../../../tests/test_daily_plan_rpc.py) — direct import
- [tests/test_data_capture_a1_prefilter.py](../../../../../tests/test_data_capture_a1_prefilter.py) — direct import
  - `test_todays_offer_links_its_builds_receipt_with_every_gate`
- [tests/test_data_capture_codex_review.py](../../../../../tests/test_data_capture_codex_review.py) — direct import
  - `test_f8_an_offers_receipt_commits_in_its_decisions_transaction`
- [tests/test_data_capture_successor.py](../../../../../tests/test_data_capture_successor.py) — direct import
  - `test_the_openers_install_this_links_completion`
- [tests/test_decider_landing.py](../../../../../tests/test_decider_landing.py) — direct import
- [tests/test_device_eligibility.py](../../../../../tests/test_device_eligibility.py) — direct import
  - `test_a_presentation_committed_on_the_phone_resumes_on_the_desktop`
  - `test_what_the_phone_left_for_the_desktop_is_held_back_from_its_next_build`
- [tests/test_diagnosis_async_router.py](../../../../../tests/test_diagnosis_async_router.py) — direct import
- [tests/test_diagnosis_card.py](../../../../../tests/test_diagnosis_card.py) — direct import
- [tests/test_dialogue_causal_join.py](../../../../../tests/test_dialogue_causal_join.py) — direct import
  - `test_submit_eliciting_response_sidecar_method`
- [tests/test_embedding_route_isolation.py](../../../../../tests/test_embedding_route_isolation.py) — direct import
  - `test_disabled_embedding_route_does_not_fail_settings_health`
  - `test_settings_health_checks_each_profile_of_a_pf_list_route`
  - `test_settings_health_checks_each_route_under_its_own_task`
  - `test_sidecar_never_offers_or_persists_an_embedding_profile_for_generation`
- [tests/test_evsi_router_composition.py](../../../../../tests/test_evsi_router_composition.py) — direct import
- [tests/test_exam_protection_identity.py](../../../../../tests/test_exam_protection_identity.py) — direct import
  - `test_f15_the_plans_reading_step_never_offers_held_out_material_in_either_order`
  - `test_identity_rereview_f3_the_running_app_records_hand_edited_exam_membership`
- [tests/test_exam_protection_review.py](../../../../../tests/test_exam_protection_review.py) — direct import
  - `test_the_exam_screen_stops_serving_an_item_exposed_mid_exam_and_refuses_its_answer`
- [tests/test_facet_identity_actions.py](../../../../../tests/test_facet_identity_actions.py) — direct import
  - `test_the_sidecar_finishes_an_interrupted_merge_when_it_opens_the_vault`
- [tests/test_facet_reword_paths.py](../../../../../tests/test_facet_reword_paths.py) — direct import
- [tests/test_facet_rewords.py](../../../../../tests/test_facet_rewords.py) — direct import
  - `test_the_facet_inspector_shows_the_version_history_and_undoes_a_reword`
- [tests/test_facet_state_write_on_change.py](../../../../../tests/test_facet_state_write_on_change.py) — direct import
  - `test_a_sidecar_reload_after_nothing_happened_writes_nothing_to_the_facet_tables`
- [tests/test_figures_help.py](../../../../../tests/test_figures_help.py) — direct import
- [tests/test_followup_codex_review.py](../../../../../tests/test_followup_codex_review.py) — direct import
  - `test_f7_next_through_the_sidecar_after_the_switch`
- [tests/test_followup_fg1c_r1_exposure_independence.py](../../../../../tests/test_followup_fg1c_r1_exposure_independence.py) — direct import
- [tests/test_followup_fg1d_probe_shadow.py](../../../../../tests/test_followup_fg1d_probe_shadow.py) — direct import
- [tests/test_followup_journey.py](../../../../../tests/test_followup_journey.py) — direct import
  - `test_with_no_plan_a_ready_probe_heads_todays_queue`
  - `test_with_the_switch_off_nothing_changes_in_the_feedback`
  - `test_with_the_switch_off_the_replies_match_the_predecessor`
- [tests/test_followup_next_matrix.py](../../../../../tests/test_followup_next_matrix.py) — direct import
- [tests/test_followup_rival_factor.py](../../../../../tests/test_followup_rival_factor.py) — direct import
  - `test_an_answered_probe_moves_the_same_measurement_with_or_without_a_mapped_repair`
- [tests/test_followup_successor.py](../../../../../tests/test_followup_successor.py) — direct import
  - `test_the_openers_install_this_links_completion`
- [tests/test_goal_scope_material.py](../../../../../tests/test_goal_scope_material.py) — direct import
- [tests/test_graph_editor_reads.py](../../../../../tests/test_graph_editor_reads.py) — direct import
- [tests/test_help_assist_work_md_migration.py](../../../../../tests/test_help_assist_work_md_migration.py) — direct import
- [tests/test_hint_authored_reveal_ruling.py](../../../../../tests/test_hint_authored_reveal_ruling.py) — direct import
- [tests/test_hint_blind.py](../../../../../tests/test_hint_blind.py) — direct import
  - `test_the_blind_prompt_of_a_hinted_attempt_carries_no_hint_map_placement_or_state`
- [tests/test_hint_discriminating.py](../../../../../tests/test_hint_discriminating.py) — direct import
  - `test_the_answer_is_an_assist_row_that_moves_nothing_and_never_reaches_the_grader`
- [tests/test_hint_evidence.py](../../../../../tests/test_hint_evidence.py) — direct import
- [tests/test_hint_feedback_texts.py](../../../../../tests/test_hint_feedback_texts.py) — direct import
- [tests/test_hint_h2a_review.py](../../../../../tests/test_hint_h2a_review.py) — direct import
- [tests/test_hint_h2a_review_round2.py](../../../../../tests/test_hint_h2a_review_round2.py) — direct import
- [tests/test_hint_h2b_review.py](../../../../../tests/test_hint_h2b_review.py) — direct import
  - `test_f4_a_reply_whose_job_never_committed_is_queued_by_the_sweep_and_at_open`
  - `test_f5_a_placement_never_scheduled_is_resumed_when_the_vault_opens`
- [tests/test_hint_kill_switch.py](../../../../../tests/test_hint_kill_switch.py) — direct import
  - `test_a_disabled_request_leaves_the_vault_exactly_as_if_never_made`
  - `test_adaptive_off_answers_disabled_writes_nothing_and_asks_nobody`
  - `test_h2b_outcome_placement_follows_the_adaptive_kill_switch`
  - `test_h2b_set_help_style_writes_the_one_stored_preference_and_reloads`
  - `test_h2b_the_app_snapshot_through_the_sidecar_carries_no_hints_key_when_off`
  - `test_no_hint_request_reaches_a_model_during_a_diagnostic_block`
  - `test_the_served_item_and_its_cold_check_fields_are_unchanged_by_the_switch`
- [tests/test_hint_outcome.py](../../../../../tests/test_hint_outcome.py) — direct import
- [tests/test_hint_report.py](../../../../../tests/test_hint_report.py) — direct import
- [tests/test_hint_service.py](../../../../../tests/test_hint_service.py) — direct import
  - `test_a_job_of_another_vault_is_never_delivered_after_a_switch`
  - `test_a_malformed_request_answers_its_job_with_a_validation_error`
  - `test_the_request_is_a_job_and_the_read_that_returns_it_shows_it`
  - `test_with_no_draft_in_the_request_the_session_checkpoints_draft_is_read`
- [tests/test_hint_telemetry.py](../../../../../tests/test_hint_telemetry.py) — direct import
- [tests/test_host_queue_revision.py](../../../../../tests/test_host_queue_revision.py) — direct import
  - `test_a_desktop_session_reply_is_unchanged_until_the_session_leaves_it`
- [tests/test_hypothesis_marks.py](../../../../../tests/test_hypothesis_marks.py) — direct import
  - `test_off_means_no_key_no_rows_and_the_same_replies`
  - `test_with_no_causes_on_the_attempt_the_bundle_has_no_key`
- [tests/test_ingest_jobs.py](../../../../../tests/test_ingest_jobs.py) — direct import
  - `test_batch_completion_triggers_one_vault_reload`
- [tests/test_ingest_latency_journey.py](../../../../../tests/test_ingest_latency_journey.py) — direct import
  - `test_synthetic_markdown_import_reaches_ready_library_and_outline`
- [tests/test_instrument_servability_journeys.py](../../../../../tests/test_instrument_servability_journeys.py) — direct import
- [tests/test_integration_daily_loop_field.py](../../../../../tests/test_integration_daily_loop_field.py) — direct import
  - `test_adopted_reader_card_is_untested_on_the_map_with_no_outcome_row`
- [tests/test_intent_fix_round4.py](../../../../../tests/test_intent_fix_round4.py) — direct import
  - `test_f15_the_probe_contract_carries_the_diagnostic_variant`
- [tests/test_intent_orchestrator_rulings.py](../../../../../tests/test_intent_orchestrator_rulings.py) — direct import
- [tests/test_intent_rpc.py](../../../../../tests/test_intent_rpc.py) — direct import
  - `test_with_intent_off_the_control_answers_off_and_refuses_writes`
- [tests/test_judge_routes.py](../../../../../tests/test_judge_routes.py) — direct import
  - `test_grading_providers_and_settings_health_ignore_judgment_routes`
- [tests/test_keep_local_retired.py](../../../../../tests/test_keep_local_retired.py) — direct import
- [tests/test_km2_activation.py](../../../../../tests/test_km2_activation.py) — direct import
  - `test_app_load_repairs_vault_activated_by_old_upgrade`
- [tests/test_knowledge_map_text_neighbors.py](../../../../../tests/test_knowledge_map_text_neighbors.py) — direct import
  - `test_render_never_calls_a_model_or_writes`
- [tests/test_learner_pick_proposal.py](../../../../../tests/test_learner_pick_proposal.py) — direct import
- [tests/test_learner_report_superseded.py](../../../../../tests/test_learner_report_superseded.py) — direct import
- [tests/test_learner_text_gaps_flow.py](../../../../../tests/test_learner_text_gaps_flow.py) — direct import
  - `test_the_sidecar_queues_the_reading_and_the_overlay_shows_it_with_undo`
- [tests/test_learner_text_gaps_review.py](../../../../../tests/test_learner_text_gaps_review.py) — direct import
  - `test_f16_a_removed_edge_reloads_once_and_bumps_nothing`
- [tests/test_lp_claim_fixes_rereview.py](../../../../../tests/test_lp_claim_fixes_rereview.py) — direct import
- [tests/test_lp_claim_fixes_review.py](../../../../../tests/test_lp_claim_fixes_review.py) — direct import
  - `test_f2_a_death_between_publication_and_commit_is_completed_from_the_journal`
  - `test_f6_get_feedback_attaches_the_line_to_the_resolving_review_only`
- [tests/test_mcp_runtime.py](../../../../../tests/test_mcp_runtime.py) — direct import
  - `test_a_second_process_serves_the_vault_beside_the_desktop_sidecar`
- [tests/test_mobile_handoff.py](../../../../../tests/test_mobile_handoff.py) — direct import
- [tests/test_mobile_jobs.py](../../../../../tests/test_mobile_jobs.py) — direct import
  - `test_the_submission_endpoint_covers_a_desktops_submissions`
- [tests/test_mobile_rpc.py](../../../../../tests/test_mobile_rpc.py) — direct import
  - `test_the_desktops_offer_under_a_plan_is_still_full_list`
- [tests/test_mobile_two_process.py](../../../../../tests/test_mobile_two_process.py) — direct import
  - `test_the_desktop_and_the_host_coexist_with_no_lost_writes`
- [tests/test_owner_capture_1025.py](../../../../../tests/test_owner_capture_1025.py) — direct import
- [tests/test_placement_opening_probes.py](../../../../../tests/test_placement_opening_probes.py) — direct import
  - `test_an_in_progress_opening_episode_serves_no_probe_and_is_not_parked`
- [tests/test_placement_sidecar.py](../../../../../tests/test_placement_sidecar.py) — direct import
- [tests/test_plan_determinism.py](../../../../../tests/test_plan_determinism.py) — direct import
- [tests/test_plan_first_transport.py](../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_a_background_jobs_offer_reaches_the_read_that_finds_it_done`
  - `test_f4_grants_are_per_vault_per_offer_and_the_env_grant_is_the_cli_commands_only`
  - `test_f8_an_error_that_is_not_a_sidecar_error_keeps_the_offer`
  - `test_f9_refused_codex_profiles_are_not_offered_as_grading_providers`
  - `test_rr_f1_the_connection_status_never_offers_and_shows_a_granted_build`
  - `test_rr_f3_the_plan_status_lists_the_sessions_grants_for_a_lasting_stop`
  - `test_the_sidecar_attaches_the_typed_hint_and_ai_use_fallback_records_the_choice`
- [tests/test_plan_first_transport_grant_scope.py](../../../../../tests/test_plan_first_transport_grant_scope.py) — direct import
  - `test_a_hint_job_started_in_the_request_carries_its_grant_and_a_background_one_does_not`
  - `test_startup_recovery_of_import_key_checks_never_uses_the_grant`
  - `test_the_edit_recheck_never_uses_the_grant`
- [tests/test_plan_first_transport_offer_grants.py](../../../../../tests/test_plan_first_transport_offer_grants.py) — direct import
- [tests/test_plan_first_transport_offer_grants_r5.py](../../../../../tests/test_plan_first_transport_offer_grants_r5.py) — direct import
- [tests/test_plan_first_transport_today_quiet.py](../../../../../tests/test_plan_first_transport_today_quiet.py) — direct import
  - `test_opening_today_never_asks_and_using_teach_back_still_does`
- [tests/test_pr4_superseded_claims_landing.py](../../../../../tests/test_pr4_superseded_claims_landing.py) — direct import
  - `test_landing_i_a_too_easy_retirement_during_a_session`
  - `test_landing_i_control_below_the_tag_the_same_session_reopens_the_retired_row`
- [tests/test_practice_index_adapters.py](../../../../../tests/test_practice_index_adapters.py) — direct import
  - `test_sidecar_rpcs`
- [tests/test_rbeq_pr2_landing.py](../../../../../tests/test_rbeq_pr2_landing.py) — direct import
- [tests/test_reader_ca1_as_printed.py](../../../../../tests/test_reader_ca1_as_printed.py) — direct import
  - `test_a_card_written_from_a_photo_shows_the_photo_outside_a_check`
  - `test_a_purged_photo_is_not_offered`
  - `test_an_item_with_no_page_and_no_photo_shows_nothing`
  - `test_the_draft_keeps_page_seen_under_its_retry_key`
  - `test_without_the_original_the_geometry_is_kept_and_nothing_is_drawn`
- [tests/test_reader_ca1_codex_review.py](../../../../../tests/test_reader_ca1_codex_review.py) — direct import
  - `test_a_page_known_without_a_box_offers_the_original_page_and_no_substitute_crop`
- [tests/test_reader_ca2_astra_handoff_recovery.py](../../../../../tests/test_reader_ca2_astra_handoff_recovery.py) — direct import
  - `test_after_a_restart_the_reader_still_reads_the_answer_box_s_questions`
- [tests/test_reader_ca2_codex_rereview.py](../../../../../tests/test_reader_ca2_codex_rereview.py) — direct import
- [tests/test_reader_ca2_codex_review.py](../../../../../tests/test_reader_ca2_codex_review.py) — direct import
  - `test_an_earlier_attempt_opened_before_submit_costs_one_hint_across_a_restart`
- [tests/test_reader_ca2_one_ask.py](../../../../../tests/test_reader_ca2_one_ask.py) — direct import
  - `test_panel_off_the_sidecar_asks_as_before`
  - `test_the_snapshot_carries_the_panel_and_the_rule`
- [tests/test_reader_followups_successor.py](../../../../../tests/test_reader_followups_successor.py) — direct import
- [tests/test_reader_pdf_selection.py](../../../../../tests/test_reader_pdf_selection.py) — direct import
  - `test_a_reading_held_back_by_rule_4_is_withheld_whole`
  - `test_the_reader_is_told_which_passages_are_held_out`
- [tests/test_reader_recap.py](../../../../../tests/test_reader_recap.py) — direct import
  - `test_switched_off_opening_writes_nothing_and_the_recap_rpcs_refuse`
  - `test_the_kill_switches_default_on_and_the_config_dto_names_them`
- [tests/test_reader_recap_review.py](../../../../../tests/test_reader_recap_review.py) — direct import
  - `test_f10_inquiry_off_refuses_every_recap_rpc_and_names_no_switch`
- [tests/test_reader_rw3a_landing.py](../../../../../tests/test_reader_rw3a_landing.py) — direct import
- [tests/test_reader_rw4b_admission_idempotency.py](../../../../../tests/test_reader_rw4b_admission_idempotency.py) — direct import
- [tests/test_reader_rw4b_fix6.py](../../../../../tests/test_reader_rw4b_fix6.py) — direct import
- [tests/test_reader_workbench_rw2a.py](../../../../../tests/test_reader_workbench_rw2a.py) — direct import
- [tests/test_reader_wrap_up.py](../../../../../tests/test_reader_wrap_up.py) — direct import
  - `test_the_card_off_leaves_wrap_up_on_its_own_switch`
- [tests/test_reading_request_sweep.py](../../../../../tests/test_reading_request_sweep.py) — direct import
- [tests/test_regrade_contract_replay.py](../../../../../tests/test_regrade_contract_replay.py) — direct import
  - `test_case1_a_contest_of_a_model_grade_above_its_original_maximum_looks_again`
- [tests/test_regrade_contract_successor.py](../../../../../tests/test_regrade_contract_successor.py) — direct import
- [tests/test_request_origin.py](../../../../../tests/test_request_origin.py) — direct import
  - `test_acting_as_restores_the_origin_after_a_refused_call`
  - `test_each_context_keeps_its_own_origin`
- [tests/test_required_method_round3_review.py](../../../../../tests/test_required_method_round3_review.py) — direct import
- [tests/test_reread_safety.py](../../../../../tests/test_reread_safety.py) — direct import
  - `test_f5_a_legacy_saved_place_after_a_reread_with_no_alias_falls_back_to_the_history`
  - `test_f5_a_legacy_saved_place_on_a_book_read_once_is_on_its_reading`
  - `test_f5_a_legacy_saved_place_with_an_unknown_reading_falls_back_to_the_history`
  - `test_rereview_f10_a_place_is_translated_onto_the_reading_the_reader_has_open`
  - `test_source_conflicts_open_the_span_they_cite_never_another_block`
  - `test_the_saved_reading_place_translates_through_the_aliases`
- [tests/test_ro0_codex_review.py](../../../../../tests/test_ro0_codex_review.py) — direct import
  - `test_f3_a_list_that_served_no_head_still_decides_nothing_and_reads_no_ad`
  - `test_f3_a_served_offer_keeps_its_candidates_ad_numbers`
  - `test_f3_the_staged_bridge_hands_its_decision_the_ad_reader`
- [tests/test_ro0_codex_verify.py](../../../../../tests/test_ro0_codex_verify.py) — direct import
  - `test_r1_a_source_opening_stands_whatever_its_initiators_receipt_meets`
- [tests/test_ro0_gate.py](../../../../../tests/test_ro0_gate.py) — direct import
- [tests/test_ro0_row11_goal_lifecycle.py](../../../../../tests/test_ro0_row11_goal_lifecycle.py) — direct import
  - `test_the_sidecar_sweeps_at_load`
- [tests/test_ro0_row4_exposure_initiator.py](../../../../../tests/test_ro0_row4_exposure_initiator.py) — direct import
  - `test_the_span_view_handler_records_the_mapped_initiator`
- [tests/test_ro0_rows7_8_sessions.py](../../../../../tests/test_ro0_rows7_8_sessions.py) — direct import
- [tests/test_ro1_successor.py](../../../../../tests/test_ro1_successor.py) — direct import
  - `test_the_openers_install_this_links_completion`
- [tests/test_router_offer_log.py](../../../../../tests/test_router_offer_log.py) — direct import
- [tests/test_router_outcomes.py](../../../../../tests/test_router_outcomes.py) — direct import
  - `test_the_replayer_rebuilds_router_outcomes_deterministically_with_no_model_call`
- [tests/test_router_p2_bridge.py](../../../../../tests/test_router_p2_bridge.py) — direct import
- [tests/test_router_probe_ties.py](../../../../../tests/test_router_probe_ties.py) — direct import
- [tests/test_router_r1_composition.py](../../../../../tests/test_router_r1_composition.py) — direct import
- [tests/test_router_r2a_serving.py](../../../../../tests/test_router_r2a_serving.py) — direct import
  - `test_a_saved_drafts_presentation_survives_a_restart_and_binds_at_submit`
- [tests/test_router_r2b_serving.py](../../../../../tests/test_router_r2b_serving.py) — direct import
  - `test_a_read_leaves_the_decision_open_and_a_serve_decides_it`
- [tests/test_rw2c_switch_off.py](../../../../../tests/test_rw2c_switch_off.py) — direct import
  - `test_each_switch_off_drops_only_its_own_part`
  - `test_switched_on_the_same_sequence_carries_rw2c`
- [tests/test_secondary_attach.py](../../../../../tests/test_secondary_attach.py) — direct import
  - `test_a_change_during_a_slow_load_is_in_the_snapshot_and_the_window_starts_after_it`
  - `test_a_directory_alias_does_not_hide_a_truncated_source_sets_file_from_the_sidecar`
  - `test_a_failed_refresh_is_retried_by_every_later_request`
  - `test_a_source_sets_file_that_stays_truncated_is_refused_not_published`
  - `test_a_source_sets_rewrite_during_the_load_never_publishes_empty_protection`
  - `test_content_fingerprint_reload_within_the_freshness_bound`
  - `test_load_secondary_writes_nothing_where_load_writes`
  - `test_reload_and_switch_of_a_secondary_stay_secondary`
  - `test_retargeting_a_directory_link_between_two_fingerprinted_directories_reloads`
  - `test_secondary_handlers_still_write`
  - `test_secondary_never_creates_a_missing_database`
  - `test_secondary_refusals_for_unbuilt_modes`
  - `test_secondary_refuses_a_schema_it_would_have_to_migrate`
- [tests/test_serve_eligibility_review.py](../../../../../tests/test_serve_eligibility_review.py) — direct import
- [tests/test_session_ownership.py](../../../../../tests/test_session_ownership.py) — direct import
- [tests/test_sidecar_adjudication.py](../../../../../tests/test_sidecar_adjudication.py) — direct import
- [tests/test_sidecar_contract.py](../../../../../tests/test_sidecar_contract.py) — direct import
  - `test_configured_manual_grading_is_ready`
- [tests/test_sidecar_exams.py](../../../../../tests/test_sidecar_exams.py) — direct import
  - `test_exam_submit_advances_before_background_grade_finishes`
  - `test_finished_report_carries_per_item_feedback_and_repairs`
- [tests/test_sidecar_goals.py](../../../../../tests/test_sidecar_goals.py) — direct import
- [tests/test_sidecar_item_authoring.py](../../../../../tests/test_sidecar_item_authoring.py) — direct import
  - `test_retire_rpc_updates_cached_vault_without_global_reload`
- [tests/test_sidecar_item_presentation.py](../../../../../tests/test_sidecar_item_presentation.py) — direct import
- [tests/test_sidecar_measurement.py](../../../../../tests/test_sidecar_measurement.py) — direct import
  - `test_generate_commissioning_practice_treats_an_empty_queue_as_success`
- [tests/test_sidecar_trace_and_clarification.py](../../../../../tests/test_sidecar_trace_and_clarification.py) — direct import
- [tests/test_sidecar_transport.py](../../../../../tests/test_sidecar_transport.py) — direct import
  - `test_duplicate_method_registration_fails_loudly`
  - `test_unexpected_handler_failure_marks_the_commit_outcome_unknown`
- [tests/test_source_exercise_import.py](../../../../../tests/test_source_exercise_import.py) — direct import
  - `test_the_sidecar_resumes_pending_checks_at_startup`
- [tests/test_sqlite_wal.py](../../../../../tests/test_sqlite_wal.py) — direct import
  - `test_sidecar_needs_a_writable_vault_and_says_so`
- [tests/test_state_sync_scheduling_race.py](../../../../../tests/test_state_sync_scheduling_race.py) — direct import
  - `test_incremental_watch_refresh_keeps_an_attempt_committed_after_its_read`
- [tests/test_stuck_prompt.py](../../../../../tests/test_stuck_prompt.py) — direct import
  - `test_the_draft_checkpoint_keeps_the_stuck_marker_across_a_restart`
- [tests/test_teacher_te1b_suggestions.py](../../../../../tests/test_teacher_te1b_suggestions.py) — direct import
  - `test_re_acceptance_after_a_decline_teaches_the_recovery_rate`
  - `test_the_openers_install_this_links_completion`
  - `test_the_seeded_priors_reproduce_one_a_day_and_a_week_long_mute`
  - `test_with_the_switch_off_the_desktop_config_is_byte_identical`
- [tests/test_ux_phase1_add_source.py](../../../../../tests/test_ux_phase1_add_source.py) — direct import
- [tests/test_ux_phase1_connect_ai.py](../../../../../tests/test_ux_phase1_connect_ai.py) — direct import
- [tests/test_ux_phase1_finish.py](../../../../../tests/test_ux_phase1_finish.py) — direct import
- [tests/test_ux_phase1_landing.py](../../../../../tests/test_ux_phase1_landing.py) — direct import
  - `test_todays_plan_reads_mains_exam_predicate_for_the_reading_step`
- [tests/test_ux_phase1_review_fixes.py](../../../../../tests/test_ux_phase1_review_fixes.py) — direct import
  - `test_f11_retry_tries_the_zero_model_repair_first_then_a_fresh_run`
  - `test_f1_sending_a_whole_recording_out_waits_for_its_own_ok`
  - `test_f9_text_recognition_names_an_extractor_that_recognises_text`
  - `test_f9_text_recognition_without_an_extractor_that_can_do_it_says_so`
- [tests/test_ux_phase1_round2_rereview.py](../../../../../tests/test_ux_phase1_round2_rereview.py) — direct import
- [tests/test_ux_phase1_round2_review.py](../../../../../tests/test_ux_phase1_round2_review.py) — direct import
  - `test_f2_todays_plan_follows_the_switch`
- [tests/test_ux_phase1_usability_round1.py](../../../../../tests/test_ux_phase1_usability_round1.py) — direct import
  - `test_u10_the_practised_subject_comes_before_a_new_books_subject`
- [tests/test_ux_phase1_usability_round2.py](../../../../../tests/test_ux_phase1_usability_round2.py) — direct import
  - `test_r4_asking_for_text_recognition_that_is_not_installed_says_how_to_get_it`
- [tests/test_ux_phase2_shell.py](../../../../../tests/test_ux_phase2_shell.py) — direct import
  - `test_classic_keeps_the_old_shell_and_leaves_phase_4_alone`
  - `test_the_shell_switch_defaults_to_simple_and_reaches_the_app`
- [tests/test_ux_phase4_feedback.py](../../../../../tests/test_ux_phase4_feedback.py) — direct import
  - `test_f1l_the_scheduler_never_commits_or_serves_a_covered_probe`
  - `test_the_practice_feedback_switch_defaults_to_simple_and_reaches_the_app`
- [tests/test_ux_phase4_landing.py](../../../../../tests/test_ux_phase4_landing.py) — direct import
- [tests/test_vault_watcher_refresh.py](../../../../../tests/test_vault_watcher_refresh.py) — direct import
  - `test_non_item_watch_refresh_returns_the_updated_application_snapshot`
  - `test_practice_item_deletion_deactivates_cached_serving_state`
  - `test_practice_item_watch_refresh_is_incremental`
  - `test_watch_refresh_rejects_an_event_from_the_previously_selected_vault`
- [tests/test_voi_merge_composition.py](../../../../../tests/test_voi_merge_composition.py) — direct import
- [tests/test_voi_stopping.py](../../../../../tests/test_voi_stopping.py) — direct import
  - `test_below_the_successor_the_offer_logs_no_value_decisions`
  - `test_the_continue_decision_rides_on_the_committed_presentation_and_the_offer`
- [tests/workbench_help_fakes.py](../../../../../tests/workbench_help_fakes.py) — direct import

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/context.py](../../../../../src/learnloop_sidecar/context.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
