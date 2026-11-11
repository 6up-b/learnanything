---
title: "learnloop.diagnosis.offline_review.runner"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/offline_review/runner.py"
source_paths:
  - "src/learnloop/diagnosis/offline_review/runner.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.offline_review"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.offline_review.runner module"
  - "src/learnloop/diagnosis/offline_review/runner.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-offline-review"
---

# `learnloop.diagnosis.offline_review.runner`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/offline_review/_package|learnloop.diagnosis.offline_review]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.offline_review.runner` exists within [[Reference/Modules/learnloop/diagnosis/offline_review/_package|learnloop.diagnosis.offline_review]] to own the behavior summarized by its module contract: Plan, estimate and run the M1 offline review into a scratch copy (§12.1).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/offline_review/runner.py](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py) |
| Source lines | 1978 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/offline_review/_package|learnloop.diagnosis.offline_review]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ReviewOptions` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 130)
  - `__post_init__(self) -> None` (line 148; internal)
  - `as_dict(self) -> dict[str, Any]` (line 156; public)
  - `as_persisted(self) -> dict[str, Any]` (line 161; public) — Every field, the planted manifest included, for ``run.json``.
  - `from_persisted(cls, payload: Mapping[str, Any]) -> 'ReviewOptions'` (line 167; public)
  - `value_of(self, name: str) -> Any` (line 174; public) — A field, or ``settings.<field>``, by dotted name.
- `class ReviewClients` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 183)
- `route_profiles(vault: LoadedVault) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 202) — Each review route's configured provider, from config only (no client).
- `resolve_review_clients(vault: LoadedVault) -> ReviewClients` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 227) — Ready clients for every review route; a missing one is a note, not an error.
- `eligible_attempts(vault: LoadedVault, repository: Repository, *, since: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 245) — Model-graded practice attempts with an error, an answer and a known item.
- `data_check(vault: LoadedVault, repository: Repository) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 295)
- `select_sample(rows: Sequence[Mapping[str, Any]], size: int, seed: int) -> list[Mapping[str, Any]]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 309) — Stratified across LOs and time quartiles; deterministic for a seed.
- `unavailable_arms(*, embedding_ready: bool, workspace_ready: bool) -> dict[str, str]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 350) — Arms the routes cannot run, with the honest reason (§12.1).
- `plan_review(vault: LoadedVault, repository: Repository, options: ReviewOptions, *, clients: ReviewClients | None=None, skip_arms: Mapping[str, str] | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 361) — Targets and a per-route call/token estimate.
- `estimate_spend(plan: Mapping[str, Any], spend: ReviewSpend) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 495) — The plan's admission estimate per route; ``admissible`` false names why.
- `class IncompatibleResume(ValueError)` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 554) — A resume would mix configurations within one run.
  - `__init__(self, reasons: Sequence[str]) -> None` (line 557; internal)
- `prompt_versions() -> dict[str, str]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 562)
- `vault_content_hash(vault: LoadedVault) -> str` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 576) — What every grading and diagnosis context reads from the vault's files.
- `decider_route_profile(vault: LoadedVault) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 596) — The Decider's settings a run prices and binds, from config only; None when links stay with the LLM.
- `register_decider_route(spend: ReviewSpend, profile: Mapping[str, Any] | None) -> None` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 618) — Price the Decider's route at its listed input price (no output allowance), as each request is.
- `route_bindings(clients: ReviewClients, config: Any | None=None) -> dict[str, dict[str, Any] | None]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 632) — Per review route, the settings that change what its requests produce.
- `run_binding(vault: LoadedVault, clients: ReviewClients) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 660)
- `resume_options(persisted: Mapping[str, Any], options: ReviewOptions, explicit_options: Iterable[str] | None) -> ReviewOptions` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 669) — The run's persisted options; an explicit different value is refused.
- `binding_mismatches(persisted: Mapping[str, Any] | None, current: Mapping[str, Any]) -> list[str]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 705) — Why ``current`` would mix with the run's recorded binding (empty = none).
- `class ReviewRun` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 732) — One run directory: the scratch copy, its run row and the spend meter.
  - `__init__(self, vault: LoadedVault, run_dir: Path, options: ReviewOptions, clients: ReviewClients, spend: ReviewSpend, *, progress: Callable[[str], None] | None=None) -> None` (line 735; internal)
  - `plain_store(self) -> VaultHistoryStore` (line 757; public) — The scratch copy's history without blind overlays (loaded once).
  - `open(self, source_sqlite: Path, *, binding: Mapping[str, Any] | None=None) -> None` (line 766; public)
  - `_write(self) -> Iterator[sqlite3.Connection]` (line 834; internal)
  - `_rows(self, table: str, *, order_by: str='rowid', **where: Any) -> list[dict[str, Any]]` (line 838; internal)
  - `paid(self, route: str, purpose: str, *, stage: str, input_tokens: int, subject_id: str | None=None, arm: str | None=None) -> Iterator[None]` (line 846; public)
  - `guard_for(self, route: str, *, stage: str, subject_id: str | None, arm: str | None) -> Callable[[str, int], Any]` (line 884; public)
  - `stage_targets(self, plan: Mapping[str, Any]) -> None` (line 892; public)
  - `_stage_done(self, name: str) -> bool` (line 917; internal)
  - `_mark_stage(self, name: str) -> None` (line 921; internal)
  - `stage_planted(self) -> None` (line 927; public)
  - `_insert_case(self, case: PlantedCase) -> None` (line 935; internal) — Checkpoint one planted case (and its target) as soon as it exists.
  - `_stage_planted(self) -> None` (line 971; internal)
  - `planted_cases(self) -> dict[str, PlantedCase]` (line 1022; public)
  - `target_answer(self, target: Mapping[str, Any], planted: Mapping[str, PlantedCase]) -> str` (line 1028; public)
  - `blind_grade(self, *, attempt_id: str, item: PracticeItem, answer: str, purpose: str, stage: str) -> dict[str, Any] | None` (line 1035; public) — Blind-grade one answer once; returns the validated record or None.
  - `_joint_history(self, item: PracticeItem, prior: Sequence[HistoryAttempt]) -> list[dict[str, Any]]` (line 1083; internal) — Today's C4 filter (same facet AND same surface family), as of the attempt.
  - `joint_grade(self, *, attempt_id: str, item: PracticeItem, answer: str, prior: Sequence[HistoryAttempt], purpose: str, stage: str) -> tuple[GradingProposal | None, dict[str, Any] | None]` (line 1110; public) — Today's joint grader (C4 history, causal fields) on one answer.
  - `real_store(self) -> VaultHistoryStore` (line 1168; public)
  - `stage_grades(self) -> None` (line 1176; public)
  - `_insert_diagnosis(self, target_id: str, arm: str, mode: str, *, status: str, proposal: Mapping[str, Any] | None, provider: str | None=None, model: str | None=None, prompt_version: str | None=None, outcome: DiagnosisOutcome | None=None, error: str | None=None) -> str` (line 1202; internal)
  - `_retriever(self) -> EmbeddingHistoryRetriever | None` (line 1246; internal)
  - `_sweep_store(self, case: PlantedCase, base: StaticHistoryStore, budget: int, real: VaultHistoryStore) -> StaticHistoryStore` (line 1256; internal) — Planted needles interleaved among real distractors sized to ``budget``.
  - `stage_diagnoses(self) -> None` (line 1286; public)
  - `_ledger_has(self, task: str, left_kind: str, left_id: str, pass_index: int, revision: str) -> bool` (line 1386; internal) — Whether this judgment pass ran on exactly these inputs (``revision``).
  - `_judge_model(self) -> str` (line 1406; internal)
  - `_links_tier1(self) -> bool` (line 1409; internal) — mvp-0.22 (Tier 1): the Decider judges pattern links, the LLM its fallback.
  - `_append(self, connection: sqlite3.Connection, *, judge: str='llm', judge_model: str | None=None, **values: Any) -> None` (line 1414; internal)
  - `_item_view(self, item: PracticeItem) -> dict[str, Any]` (line 1418; internal)
  - `stage_judge(self) -> None` (line 1429; public)
  - `_judge_links(self, target, rows, answer, item, planted, index) -> None` (line 1507; internal)
  - `_judge_planted(self, target, rows, case: PlantedCase, item, answer, index) -> None` (line 1590; internal)
  - `stage_probes(self) -> None` (line 1635; public)
  - `_record_probe(self, probe: str, item: PracticeItem, *, status: str, known: float | None, maximum: float | None, blind_score: float | None, detail: Mapping[str, Any]) -> None` (line 1675; internal)
  - `_persisted_draft(previous: Mapping[str, Any] | None, model: type) -> tuple[Any | None, str | None]` (line 1695; internal) — The draft and probe id of a drafted or grading-failed probe, for grading.
  - `_generate(self, purpose: str, prompt: str, request: Callable[[Any, str], Any], subject: str) -> Any | None` (line 1705; internal)
  - `_draft(self, probe: str, item: PracticeItem, previous: Mapping[str, Any] | None, model: type, purpose: str, prompt: Callable[[], str], request: Callable[[Any, str], Any], maximum: float, extra: Mapping[str, Any] | None=None) -> tuple[Any, str] | None` (line 1714; internal) — The probe's draft: a persisted one, else a new one checkpointed AT ONCE.
  - `_probe_valid_alternative(self, item: PracticeItem, previous: Mapping[str, Any] | None=None) -> None` (line 1747; internal)
  - `_probe_synthetic(self, item: PracticeItem, previous: Mapping[str, Any] | None=None) -> None` (line 1770; internal)
  - `_probe_paraphrase(self, item: PracticeItem, target: Mapping[str, Any], original: Mapping[str, Any], previous: Mapping[str, Any] | None=None) -> None` (line 1796; internal)
  - `finish(self, status: str) -> dict[str, Any]` (line 1816; public)
- `run_review(vault: LoadedVault, *, source_sqlite: Path, run_dir: Path, options: ReviewOptions, clients: ReviewClients, caps: SpendCaps, price_per_million: float | None=None, cancelled: Callable[[], bool] | None=None, progress: Callable[[str], None] | None=None, explicit_options: Iterable[str] | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 1841) — Run (or resume) every stage; returns the manifest and stage status.

### Module constants

- `RUN_FILE` ([src/learnloop/diagnosis/offline_review/runner.py](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 110)
- `STAGES_FILE` ([src/learnloop/diagnosis/offline_review/runner.py](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 111)
- `SCRATCH_FILE` ([src/learnloop/diagnosis/offline_review/runner.py](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 112)
- `REVIEW_VERSION` ([src/learnloop/diagnosis/offline_review/runner.py](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 113)
- `MAIN_ARMS` ([src/learnloop/diagnosis/offline_review/runner.py](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 114)
- `ARM_MODES` ([src/learnloop/diagnosis/offline_review/runner.py](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 115)
- `DEFAULT_SWEEP_BUDGETS` ([src/learnloop/diagnosis/offline_review/runner.py](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 116)
- `MIN_SAMPLE` ([src/learnloop/diagnosis/offline_review/runner.py](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 117)
- `_GRADED_SOURCES` ([src/learnloop/diagnosis/offline_review/runner.py](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 118)
- `PROBE_SETTLED_STATUSES` ([src/learnloop/diagnosis/offline_review/runner.py](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 121)
- `PROBE_DRAFT_STATUSES` ([src/learnloop/diagnosis/offline_review/runner.py](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 125)
- `_JOINT_HISTORY_LIMIT` ([src/learnloop/diagnosis/offline_review/runner.py](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 126)
- `REVIEW_ROUTES` ([src/learnloop/diagnosis/offline_review/runner.py](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 192)
- `_SUBSCRIPTION_PROFILE_TYPES` ([src/learnloop/diagnosis/offline_review/runner.py](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 199)
- `DECIDER_ROUTE` ([src/learnloop/diagnosis/offline_review/runner.py](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 593)

### Explicit exports

`__all__` declares:

- `IncompatibleResume`
- `binding_mismatches`
- `prompt_versions`
- `resume_options`
- `run_binding`
- `vault_content_hash`
- `REVIEW_ROUTES`
- `resolve_review_clients`
- `route_profiles`
- `ARM_MODES`
- `DEFAULT_SWEEP_BUDGETS`
- `MAIN_ARMS`
- `MIN_SAMPLE`
- `REVIEW_VERSION`
- `RUN_FILE`
- `SCRATCH_FILE`
- `ReviewClients`
- `ReviewOptions`
- `ReviewRun`
- `data_check`
- `eligible_attempts`
- `unavailable_arms`
- `estimate_spend`
- `plan_review`
- `run_review`
- `select_sample`

## Internal implementation anchors

- `_placeholder_blind(item: PracticeItem, vault: LoadedVault) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 337)
- `_isolates(client: Any) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py), line 1836)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/diagnose|learnloop.cli.diagnose]] — imports `DECIDER_ROUTE`, `ReviewClients`, `ReviewOptions`, `data_check`, `decider_route_profile`, `estimate_spend`, `plan_review`, `register_decider_route`, `resolve_review_clients`, `route_profiles`, `run_review`, `unavailable_arms`; statically calls `ReviewOptions`, `data_check`, `decider_route_profile`, `estimate_spend`, `plan_review`, `register_decider_route`, `resolve_review_clients`, `route_profiles`, `run_review`, `unavailable_arms`
- [[Reference/Modules/learnloop/diagnosis/offline_review/links|learnloop.diagnosis.offline_review.links]] — imports `RUN_FILE`, `SCRATCH_FILE`
- [[Reference/Modules/learnloop/diagnosis/offline_review/report|learnloop.diagnosis.offline_review.report]] — imports `RUN_FILE`, `SCRATCH_FILE`
- [[Reference/Modules/learnloop/diagnosis/offline_review/spot_check|learnloop.diagnosis.offline_review.spot_check]] — imports `MAIN_ARMS`, `RUN_FILE`, `SCRATCH_FILE`
- [[Reference/Modules/learnloop/diagnosis/recurrence/guard|learnloop.diagnosis.recurrence.guard]] — imports `RUN_FILE`, `SCRATCH_FILE`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `route_profiles`; statically calls `route_profiles`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIProviderUnavailable`; calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `model_settings`; calls `model_settings`
- [[Reference/Modules/learnloop/ai/providers/decider|learnloop.ai.providers.decider]] — imports `resolved_decider_settings`; calls `resolved_decider_settings`
- [[Reference/Modules/learnloop/ai/review_spend|learnloop.ai.review_spend]] — imports `RouteInfo`; calls `RouteInfo`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `provider_for_task`, `ready_client_for_task`; calls `provider_for_task`, `ready_client_for_task`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`; calls `SpendEstimate`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `ISOLATED_TURN`, `READ_ONLY_WORKSPACE`
- [[Reference/Modules/learnloop/attempts/ai_contracts|learnloop.attempts.ai_contracts]] — imports `GRADING_PROMPT_VERSION`, `GradingProposal`, `grading_prompt`; calls `grading_prompt`
- [[Reference/Modules/learnloop/attempts/blind_grading|learnloop.attempts.blind_grading]] — imports `BLIND_GRADING_PROMPT_VERSION`, `blind_grading_context`, `blind_grading_context_hash`, `blind_grading_prompt`, `request_blind_grading_proposal`, `validate_blind_grading_proposal`; calls `blind_grading_context`, `blind_grading_context_hash`, `blind_grading_prompt`, `request_blind_grading_proposal`, `validate_blind_grading_proposal`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `GradingValidationError`, `build_grading_context`, `grading_context_hash`, `request_grading_proposal`, `resolved_rubric`, `validate_codex_grading_proposal`; calls `build_grading_context`, `grading_context_hash`, `request_grading_proposal`, `resolved_rubric`, `validate_codex_grading_proposal`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/copies|learnloop.db.copies]] — imports `backup_database`; calls `backup_database`
- [[Reference/Modules/learnloop/db/migrate|learnloop.db.migrate]] — imports `UPGRADE_SCRATCH_COPY`, `apply_migrations`, `upgrade_allowance`; calls `apply_migrations`, `upgrade_allowance`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/diagnosis_review|learnloop.db.stores.diagnosis_review]] — imports `ensure_review_schema`, `insert_review_row`, `review_rows`, `update_run`, `update_target_positions`; calls `ensure_review_schema`, `insert_review_row`, `review_rows`, `update_run`, `update_target_positions`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]] — imports `enabled`; calls `enabled`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_augmentation|learnloop.diagnosis.diagnostic_augmentation]] — imports `diagnostic_verifier_observations`; calls `diagnostic_verifier_observations`
- [[Reference/Modules/learnloop/diagnosis/offline_review/decider_links|learnloop.diagnosis.offline_review.decider_links]] — imports `module`; calls `judge_links`
- [[Reference/Modules/learnloop/diagnosis/offline_review/judge|learnloop.diagnosis.offline_review.judge]] — imports `module`; calls `assign_labels`, `canonical_pair`, `cited_links`, `diagnosis_judgment_prompt`, `diagnosis_judgment_revision`, `input_hash`, `judge_view`, `judged_arm_rows`, `link_judgment_prompt`, `link_judgment_revision`, `planted_cause_prompt`, `planted_judgment_revision`, `planted_statements`, `request_diagnosis_judgment`, `request_link_judgment`, `request_planted_cause_judgment`, `stable_json`
- [[Reference/Modules/learnloop/diagnosis/offline_review/planted|learnloop.diagnosis.offline_review.planted]] — imports `PLANTED_PROMPT_VERSION`, `PlantedCase`, `PlantedCaseInvalid`, `SHAPES`, `case_from_draft`, `cases_from_manifest`, `default_start`, `plantable_learning_objects`, `planted_history_store`, `request_planted_scenario`, `scenario_request`; calls `case_from_draft`, `cases_from_manifest`, `default_start`, `plantable_learning_objects`, `planted_history_store`, `request_planted_scenario`, `scenario_request`
- [[Reference/Modules/learnloop/diagnosis/offline_review/probes|learnloop.diagnosis.offline_review.probes]] — imports `module`; calls `is_reference_bearing`, `paraphrase_prompt`, `synthetic_error_prompt`, `valid_alternative_prompt`, `verify_alternative`, `verify_synthetic_error`
- [[Reference/Modules/learnloop/diagnosis/offline_review/spend|learnloop.diagnosis.offline_review.spend]] — imports `OUTPUT_ALLOWANCE`, `ReviewSpend`, `admitted_output_limit`, `is_subscription_client`; calls `ReviewSpend`, `admitted_output_limit`, `is_subscription_client`
- [[Reference/Modules/learnloop/diagnosis/split/context|learnloop.diagnosis.split.context]] — imports `assemble_diagnosis_context`, `current_attempt_from`, `estimate_tokens`, `history_attempt_tokens`; calls `assemble_diagnosis_context`, `current_attempt_from`, `estimate_tokens`, `history_attempt_tokens`
- [[Reference/Modules/learnloop/diagnosis/split/contract|learnloop.diagnosis.split.contract]] — imports `diagnosis_prompt`; calls `diagnosis_prompt`
- [[Reference/Modules/learnloop/diagnosis/split/diagnoser|learnloop.diagnosis.split.diagnoser]] — imports `DiagnosisOutcome`, `run_diagnosis`, `supports_snapshot`; calls `run_diagnosis`, `supports_snapshot`
- [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]] — imports `HistoryAttempt`, `StaticHistoryStore`, `VaultHistoryStore`, `learning_object_neighborhood`; calls `StaticHistoryStore`, `VaultHistoryStore`, `learning_object_neighborhood`
- [[Reference/Modules/learnloop/diagnosis/split/legacy_view|learnloop.diagnosis.split.legacy_view]] — imports `REVIEW_RECEIPT_OWNER_KIND`, `legacy_view_from_grading_proposal`, `stored_legacy_view`; calls `legacy_view_from_grading_proposal`, `stored_legacy_view`
- [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]] — imports `confidence_for_offline_target`; calls `confidence_for_offline_target`
- [[Reference/Modules/learnloop/diagnosis/split/retrieval|learnloop.diagnosis.split.retrieval]] — imports `EmbeddingHistoryRetriever`; calls `EmbeddingHistoryRetriever`
- [[Reference/Modules/learnloop/diagnosis/split/settings|learnloop.diagnosis.split.settings]] — imports `DIAGNOSIS_PROMPT_VERSION`, `DiagnosisSettings`; calls `DiagnosisSettings`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `held_for_review_attempts`; calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/vault/hashes|learnloop.vault.hashes]] — imports `content_hash`; calls `content_hash`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `presented_prompt`; calls `presented_prompt`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `dataclasses`, `datetime`, `json`, `math`, `pathlib`, `random`, `sqlite3`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/diagnose|learnloop.cli.diagnose]], [[Reference/Modules/learnloop/diagnosis/offline_review/links|learnloop.diagnosis.offline_review.links]], [[Reference/Modules/learnloop/diagnosis/offline_review/report|learnloop.diagnosis.offline_review.report]], [[Reference/Modules/learnloop/diagnosis/offline_review/spot_check|learnloop.diagnosis.offline_review.spot_check]], [[Reference/Modules/learnloop/diagnosis/recurrence/guard|learnloop.diagnosis.recurrence.guard]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/diagnose_review_helpers.py](../../../../../../../tests/diagnose_review_helpers.py) — direct import
- [tests/test_coordinated_migrations.py](../../../../../../../tests/test_coordinated_migrations.py) — direct import
  - `test_f8_the_offline_reviews_scratch_copy_is_upgraded_under_its_own_allowance`
- [tests/test_diagnose_review.py](../../../../../../../tests/test_diagnose_review.py) — direct import
  - `test_a_diagnosis_repaired_on_resume_is_judged_and_only_the_current_revision_counts`
  - `test_a_resume_refuses_a_changed_output_limit`
  - `test_a_resume_restores_the_persisted_experiment_and_refuses_changes`
  - `test_a_run_without_grader_or_diagnoser_refuses_before_copying`
  - `test_an_owner_verdict_never_lands_on_a_receipt_the_owner_did_not_see`
  - `test_cli_resume_with_only_the_run_dir_keeps_the_original_settings`
  - `test_rejected_planted_drafts_are_recorded_and_never_redrafted`
  - `test_review_round_trip_under_production_durability`
  - `test_sampling_is_seeded_and_stratified`
  - `test_snapshot_arm_is_skipped_with_a_note_without_the_capability`
- [tests/test_diagnosis_isolation.py](../../../../../../../tests/test_diagnosis_isolation.py) — direct import
  - `test_a_review_refuses_a_grader_or_diagnoser_that_cannot_isolate`
- [tests/test_teacher_te0_fix_round2.py](../../../../../../../tests/test_teacher_te0_fix_round2.py) — direct import
  - `test_a_held_review_grade_reads_held_for_review_in_a_later_targets_history`
- [tests/test_teacher_te0_review_fixes.py](../../../../../../../tests/test_teacher_te0_review_fixes.py) — direct import
  - `test_the_offline_runner_renders_the_confidence_block_into_each_arms_prompt`
- [tests/test_tier1_decider.py](../../../../../../../tests/test_tier1_decider.py) — direct import
  - `test_a_review_resume_refuses_a_changed_decider_profile`

## Modification guidance

- Change runner policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/offline_review/runner.py](../../../../../../../src/learnloop/diagnosis/offline_review/runner.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
