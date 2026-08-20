---
title: "learnloop.config.schema"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/config/schema.py"
source_paths:
  - "src/learnloop/config/schema.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
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
| Source lines | 1396 |
| Owning package | [[Reference/Modules/learnloop/config/_package|learnloop.config]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

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
- `class AnimationConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 640) — AI-generated Manim explainer animations (spec_fork_features §2).
- `class AudioIngestConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 671) — Audio-source ingestion (.mp3/.wav/...): transcription settings.
- `class NativeIngestConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 694) — Native multimodal ingestion: media as chat content parts (§spec 1a).
- `class IngestBudgetsConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 711) — Per-stage token budgets for ingestion v2 (source-ingestion spec §3.1).
- `class IngestProviderLimits(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 733) — Per-provider context/output limits consulted by preflight (spec §3.1).
- `class IngestRunnerConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 742) — Durable-queue worker settings for ingestion v2 (source-ingestion §6.2).
- `class IngestConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 757)
- `class RungVariantsConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 776) — Learner-initiated re-runging (content/authoring/rung_variants).
- `class AIProviderConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 825) — Shared provider fields plus a direct-construction compatibility seam.
  - `_discard_auth_mode(cls, data: Any) -> Any` (line 845; internal)
  - `__getattr__(self, item: str) -> Any` (line 850; internal)
  - `__eq__(self, other: object) -> bool` (line 861; internal)
- `class CodexSDKProviderConfig(_CodexProviderConfig)` ([source](../../../../../../src/learnloop/config/schema.py), line 894)
- `class CodexHTTPProviderConfig(_CodexProviderConfig)` ([source](../../../../../../src/learnloop/config/schema.py), line 898)
- `class OpenAICompatibleProviderConfig(AIProviderConfig)` ([source](../../../../../../src/learnloop/config/schema.py), line 902)
- `class OpenRouterProviderConfig(OpenAICompatibleProviderConfig)` ([source](../../../../../../src/learnloop/config/schema.py), line 912)
- `class AIRoutingConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 927)
- `class AIConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 947)
  - `_normalize_provider_profiles(cls, data: Any) -> Any` (line 956; internal)
- `class ErrorImpact(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 982) — Error impact settings.
- `class FsrsFittingConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 995) — `learnloop fit fsrs` knobs (architecture_pivot.md Stage 1).
- `class FittingConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1006)
- `class LocksConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1010) — Curriculum identity-lock policy (knowledge-model §3.4/§12).
- `class EvidenceMassEntry(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1025) — Evidence carried by one attempt type (Fable's-take item 3).
- `default_attempt_type_evidence() -> dict[str, EvidenceMassEntry]` ([source](../../../../../../src/learnloop/config/schema.py), line 1040)
- `default_practice_mode_item_coverage() -> dict[str, float]` ([source](../../../../../../src/learnloop/config/schema.py), line 1062)
- `class EvidenceCorrelationConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1075) — Vault-wide surface-correlation discounting (knowledge-model spec §6).
- `class EvidenceCertificationConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1084) — Bounded certification credit (knowledge-model §5.4).
- `class EvidenceBlueprintsConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1112) — Blueprint recipe likelihood defaults (knowledge-model spec §9.2).
- `class EvidenceConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1123) — Single source of truth for per-attempt-type evidence carried.
  - `_merge_defaults(self) -> 'EvidenceConfig'` (line 1143; internal)
- `class CapabilitiesConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1153) — Capability damping/shrinkage + lazy residual activation (spec §4.2).
- `class TraceEvidenceConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1182) — A6 opportunistic trace evidence and its elicitation budget (Meas §3.A6).
- `class DiagnosticAugmentationConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1203) — Stage 7 live diagnosis rungs.
- `class LearnLoopConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1228)
  - `_normalize_legacy_input(cls, data: Any) -> Any` (line 1263; internal) — Keep direct model validation compatible; implementation lives in compat.
  - `_ensure_effective_defaults(self) -> 'LearnLoopConfig'` (line 1271; internal)
  - `codex(self) -> CodexConfig` (line 1328; public) — Non-serialized compatibility view of ``ai.providers.codex``.
- `default_codex_provider() -> CodexSDKProviderConfig` ([source](../../../../../../src/learnloop/config/schema.py), line 1336) — Return the modeled canonical Codex profile used when none is explicit.
- `deepseek_flash_provider() -> AIProviderConfig` ([source](../../../../../../src/learnloop/config/schema.py), line 1363)
- `deepseek_pro_provider() -> AIProviderConfig` ([source](../../../../../../src/learnloop/config/schema.py), line 1375)
- `openrouter_provider() -> AIProviderConfig` ([source](../../../../../../src/learnloop/config/schema.py), line 1388)

### Module constants

- `_COMPAT_OPTIONAL_PROVIDER_FIELDS` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 796)
- `DEFAULT_CODEX_MODEL` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 962)
- `DEFAULT_CODEX_REASONING_EFFORT` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 963)
- `LEGACY_CODEX_MODEL` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 964)
- `CODEX_LOW_PROVIDER` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 965)
- `CODEX_MEDIUM_PROVIDER` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 966)
- `CODEX_PROVIDER_NAMES` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 967)
- `OPENROUTER_TRANSCRIPTION_PROVIDER` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 968)
- `DEFAULT_CODEX_TASK_ROUTES` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 970)

## Internal implementation anchors

- `class _CodexProviderConfig(AIProviderConfig)` ([source](../../../../../../src/learnloop/config/schema.py), line 872)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `module`
- [[Reference/Modules/learnloop/config/compat|learnloop.config.compat]] — imports `AIProviderConfig`, `AudioIngestConfig`, `CodexHTTPProviderConfig`, `CodexSDKProviderConfig`, `DEFAULT_CODEX_MODEL`, `DEFAULT_CODEX_REASONING_EFFORT`, `DEFAULT_CODEX_TASK_ROUTES`, `LEGACY_CODEX_MODEL`, `LearnLoopConfig`, `OPENROUTER_TRANSCRIPTION_PROVIDER`, `openrouter_provider`; statically calls `AudioIngestConfig`, `openrouter_provider`
- [[Reference/Modules/learnloop/config/loader|learnloop.config.loader]] — imports `CODEX_LOW_PROVIDER`, `CODEX_MEDIUM_PROVIDER`, `CodexHTTPProviderConfig`, `CodexSDKProviderConfig`, `LearnLoopConfig`
- [[Reference/Modules/learnloop/config/template|learnloop.config.template]] — imports `LearnLoopConfig`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/compat|learnloop.config.compat]] — imports `CodexConfig`, `codex_config_view`, `discard_retired_provider_settings`, `normalize_ai_input`, `normalize_config_input`; calls `codex_config_view`, `discard_retired_provider_settings`, `normalize_ai_input`, `normalize_config_input`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/config/__init__|learnloop.config]], [[Reference/Modules/learnloop/config/compat|learnloop.config.compat]], [[Reference/Modules/learnloop/config/loader|learnloop.config.loader]], [[Reference/Modules/learnloop/config/template|learnloop.config.template]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_config_refactor.py](../../../../../../tests/test_config_refactor.py) — direct import
  - `test_config_responsibilities_have_canonical_module_owners`

## Modification guidance

- Change configuration behavior in the schema, loader, compatibility normalizer, or template owner that matches the concern; preserve one-way legacy normalization.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
