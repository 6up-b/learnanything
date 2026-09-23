---
title: "learnloop.config.schema"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/config/schema.py"
source_paths:
  - "src/learnloop/config/schema.py"
source_commit: "2f1331ce04afea51266eaa93ae26b8c5ef72517a"
source_commit_timestamp: "2026-09-23T12:47:57-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-09-23"
package: "learnloop.config"
layer: "infrastructure"
concepts:
  - "Configuration"
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.config.schema module"
  - "src/learnloop/config/schema.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-config"
---

# `learnloop.config.schema`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/config/_package|learnloop.config]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps schema behavior inside its owning package, [[Reference/Modules/learnloop/config/_package|learnloop.config]]. Its public surface centers on `StorageConfig`, `AlgorithmsConfig`, `SchedulerSurpriseConfig`, `SchedulerFollowupConfig`, `SchedulerConfig`, `GoalsConfig`, `HypothesisConfig`, `MasteryIRTConfig` and 57 more public symbols.

The authoritative system-level explanation remains in [[Configuration]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py) |
| Source lines | 1433 |
| Owning package | [[Reference/Modules/learnloop/config/_package|learnloop.config]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `2f1331ce04afea51266eaa93ae26b8c5ef72517a` |
| Commit timestamp | `2026-09-23T12:47:57-04:00` |

## Public API

- `class StorageConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 9)
- `class AlgorithmsConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 13)
- `class SchedulerSurpriseConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 21)
- `class SchedulerFollowupConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 30)
- `class SchedulerConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 75)
- `class GoalsConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 103)
- `class HypothesisConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 109)
- `class MasteryIRTConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 125)
- `class ProbeIRTConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 157)
- `class ProbeSelfTagConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 167) — Learner self-attributed misconception probe coverage (spec_irt_difficulty.md §12).
- `class MasteryConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 176)
- `class ProbeEpisodeConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 196) — Diagnostic-episode policy (spec_probe_eig_redesign.md §5/§11).
- `class ProbeGenerationConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 257) — Parameterized instance generation from admitted family/card bindings (§10).
- `class ProbeDialogueConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 268) — Short adaptive dialogue microprobes (§8.1).
- `class ProbeCalibrationConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 274) — Learner-initiated calibration sessions (§5.9).
- `class ProbeHierarchyConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 285) — Hierarchical family → item shrinkage (§9.7, Checkpoint 4.2).
- `class ProbeLifecycleConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 298) — Metric gates for trusted/revise/retire transitions (§9.7, Checkpoint 4.7).
- `class ProbeShadowConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 317) — Shadow-mode alternative selection policies (§13.3, Checkpoint 5.1).
- `class ProbeBlockConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 329) — Precommitted diagnostic blocks (§5.6, Checkpoint 5.2/5.3).
- `class ProbeConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 350)
- `class PracticeGenerationConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 371) — Difficulty-calibration targets for authored Practice Items and probes.
- `class SeverityExampleConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 397)
- `default_severity_examples() -> dict[str, SeverityExampleConfig]` ([source](../../../../../../src/learnloop/config/schema.py), line 411)
- `class RecallCoverageConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 453)
- `class MisconceptionsConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 472) — Automatic misconception resolution ("close the loop").
- `class FacetDiagnosticConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 509)
- `class ExamSeedingConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 516) — Exam seeding: imported past-exam outcomes as backdated attempts.
- `class TutorQAConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 529) — Tutor Q&A ("ask") behavior.
- `class TutorPromotionConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 575) — Promoting Socratic tutor questions to practice items / learning objects (spec_tutor_promotion.md §5).
- `class TeachBackConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 602) — Teach-back conversation behavior.
- `class PdfIngestConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 622)
- `class AnimationConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 642) — AI-generated Manim explainer animations (spec_fork_features §2).
- `class AudioIngestConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 690) — Audio-source ingestion (.mp3/.wav/...): transcription settings.
- `class NativeIngestConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 719) — Shared limits for native media ingestion (media as chat content parts).
- `class IngestBudgetsConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 739) — Per-stage token budgets for ingestion v2 (source-ingestion spec §3.1).
- `class IngestProviderLimits(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 761) — Per-provider context/output limits consulted by preflight (spec §3.1).
- `class IngestRunnerConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 770) — Durable-queue worker settings for ingestion v2 (source-ingestion §6.2).
- `class IngestConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 785)
- `class RungVariantsConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 804) — Learner-initiated re-runging (content/authoring/rung_variants).
- `class AIProviderConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 860) — Shared provider fields plus a direct-construction compatibility seam.
  - `_discard_auth_mode(cls, data: Any) -> Any` (line 880; internal)
  - `__getattr__(self, item: str) -> Any` (line 885; internal)
  - `__eq__(self, other: object) -> bool` (line 896; internal)
- `class CodexSDKProviderConfig(_CodexProviderConfig)` ([source](../../../../../../src/learnloop/config/schema.py), line 929)
- `class CodexHTTPProviderConfig(_CodexProviderConfig)` ([source](../../../../../../src/learnloop/config/schema.py), line 933)
- `class OpenAICompatibleProviderConfig(AIProviderConfig)` ([source](../../../../../../src/learnloop/config/schema.py), line 937)
- `class OpenRouterProviderConfig(OpenAICompatibleProviderConfig)` ([source](../../../../../../src/learnloop/config/schema.py), line 947)
- `class AIRoutingConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 962)
- `class AIConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 986)
  - `_normalize_provider_profiles(cls, data: Any) -> Any` (line 995; internal)
- `class ErrorImpact(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1021) — Error impact settings.
- `class FsrsFittingConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1034) — `learnloop fit fsrs` knobs (architecture_pivot.md Stage 1).
- `class FittingConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1045)
- `class LocksConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1049) — Curriculum identity-lock policy (knowledge-model §3.4/§12).
- `class EvidenceMassEntry(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1064) — Evidence carried by one attempt type (Fable's-take item 3).
- `default_attempt_type_evidence() -> dict[str, EvidenceMassEntry]` ([source](../../../../../../src/learnloop/config/schema.py), line 1079)
- `default_practice_mode_item_coverage() -> dict[str, float]` ([source](../../../../../../src/learnloop/config/schema.py), line 1101)
- `class EvidenceCorrelationConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1114) — Vault-wide surface-correlation discounting (knowledge-model spec §6).
- `class EvidenceCertificationConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1123) — Bounded certification credit (knowledge-model §5.4).
- `class EvidenceBlueprintsConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1151) — Blueprint recipe likelihood defaults (knowledge-model spec §9.2).
- `class EvidenceConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1162) — Single source of truth for per-attempt-type evidence carried.
  - `_merge_defaults(self) -> 'EvidenceConfig'` (line 1182; internal)
- `class CapabilitiesConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1192) — Capability damping/shrinkage + lazy residual activation (spec §4.2).
- `class TraceEvidenceConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1221) — A6 opportunistic trace evidence and its elicitation budget (Meas §3.A6).
- `class DiagnosticAugmentationConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1242) — Stage 7 live diagnosis rungs.
- `class LearnLoopConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1267)
  - `_normalize_legacy_input(cls, data: Any) -> Any` (line 1302; internal) — Keep direct model validation compatible; implementation lives in compat.
  - `_ensure_effective_defaults(self) -> 'LearnLoopConfig'` (line 1310; internal)
  - `codex(self) -> CodexConfig` (line 1365; public) — Non-serialized compatibility view of ``ai.providers.codex``.
- `default_codex_provider() -> CodexSDKProviderConfig` ([source](../../../../../../src/learnloop/config/schema.py), line 1373) — Return the modeled canonical Codex profile used when none is explicit.
- `deepseek_flash_provider() -> AIProviderConfig` ([source](../../../../../../src/learnloop/config/schema.py), line 1400)
- `deepseek_pro_provider() -> AIProviderConfig` ([source](../../../../../../src/learnloop/config/schema.py), line 1412)
- `openrouter_provider() -> AIProviderConfig` ([source](../../../../../../src/learnloop/config/schema.py), line 1425)

### Module constants

- `_COMPAT_OPTIONAL_PROVIDER_FIELDS` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 824)
- `KNOWN_INPUT_MODALITIES` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 857)
- `DEFAULT_CODEX_MODEL` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1001)
- `DEFAULT_CODEX_REASONING_EFFORT` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1002)
- `LEGACY_CODEX_MODEL` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1003)
- `CODEX_LOW_PROVIDER` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1004)
- `CODEX_MEDIUM_PROVIDER` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1005)
- `CODEX_PROVIDER_NAMES` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1006)
- `OPENROUTER_TRANSCRIPTION_PROVIDER` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1007)
- `DEFAULT_CODEX_TASK_ROUTES` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1009)

## Internal implementation anchors

- `class _CodexProviderConfig(AIProviderConfig)` ([source](../../../../../../src/learnloop/config/schema.py), line 907)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/native_media|learnloop.ai.native_media]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/ai/providers/openrouter_catalog|learnloop.ai.providers.openrouter_catalog]] — imports `KNOWN_INPUT_MODALITIES`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `module`
- [[Reference/Modules/learnloop/config/compat|learnloop.config.compat]] — imports `AIProviderConfig`, `AudioIngestConfig`, `CodexHTTPProviderConfig`, `CodexSDKProviderConfig`, `DEFAULT_CODEX_MODEL`, `DEFAULT_CODEX_REASONING_EFFORT`, `DEFAULT_CODEX_TASK_ROUTES`, `LEGACY_CODEX_MODEL`, `LearnLoopConfig`, `OPENROUTER_TRANSCRIPTION_PROVIDER`, `openrouter_provider`; statically calls `AudioIngestConfig`, `openrouter_provider`
- [[Reference/Modules/learnloop/config/loader|learnloop.config.loader]] — imports `CODEX_LOW_PROVIDER`, `CODEX_MEDIUM_PROVIDER`, `CodexHTTPProviderConfig`, `CodexSDKProviderConfig`, `LearnLoopConfig`
- [[Reference/Modules/learnloop/config/template|learnloop.config.template]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop_sidecar/handlers/settings|learnloop_sidecar.handlers.settings]] — imports `KNOWN_INPUT_MODALITIES`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/compat|learnloop.config.compat]] — imports `CodexConfig`, `codex_config_view`, `discard_retired_provider_settings`, `normalize_ai_input`, `normalize_config_input`; calls `codex_config_view`, `discard_retired_provider_settings`, `normalize_ai_input`, `normalize_config_input`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/native_media|learnloop.ai.native_media]], [[Reference/Modules/learnloop/ai/providers/openrouter_catalog|learnloop.ai.providers.openrouter_catalog]], [[Reference/Modules/learnloop/config/__init__|learnloop.config]], [[Reference/Modules/learnloop/config/compat|learnloop.config.compat]], [[Reference/Modules/learnloop/config/loader|learnloop.config.loader]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_config_refactor.py](../../../../../../tests/test_config_refactor.py) — direct import
  - `test_config_responsibilities_have_canonical_module_owners`
- [tests/test_ingest_runner.py](../../../../../../tests/test_ingest_runner.py) — direct import
  - `test_legacy_one_shot_pipeline_never_uses_the_native_engine`
- [tests/test_native_media_readiness.py](../../../../../../tests/test_native_media_readiness.py) — direct import
- [tests/test_openrouter_video_client.py](../../../../../../tests/test_openrouter_video_client.py) — direct import

## Modification guidance

- Change configuration behavior in the schema, loader, compatibility normalizer, or template owner that matches the concern; preserve one-way legacy normalization.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
