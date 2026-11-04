---
title: "learnloop.config.schema"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/config/schema.py"
source_paths:
  - "src/learnloop/config/schema.py"
source_commit: "e444e25dd0f1c0a31ec57112a48aa81fe6cf5b12"
source_commit_timestamp: "2026-11-03T21:55:42-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
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

This module keeps schema behavior inside its owning package, [[Reference/Modules/learnloop/config/_package|learnloop.config]]. Its public surface centers on `StorageConfig`, `AlgorithmsConfig`, `SchedulerSurpriseConfig`, `SchedulerFollowupConfig`, `SchedulerConfig`, `GoalsConfig`, `HypothesisConfig`, `MasteryIRTConfig` and 137 more public symbols.

The authoritative system-level explanation remains in [[Configuration]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py) |
| Source lines | 4888 |
| Owning package | [[Reference/Modules/learnloop/config/_package|learnloop.config]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `e444e25dd0f1c0a31ec57112a48aa81fe6cf5b12` |
| Commit timestamp | `2026-11-03T21:55:42-05:00` |

## Public API

- `class StorageConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 9)
- `class AlgorithmsConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 13)
- `class SchedulerSurpriseConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 21)
- `class SchedulerFollowupConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 30)
- `class SchedulerConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 78)
- `class GoalsConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 106)
- `class HypothesisConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 125)
- `class MasteryIRTConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 141)
- `class ProbeIRTConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 173)
- `class ProbeSelfTagConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 183) — Learner self-attributed misconception probe coverage (spec_irt_difficulty.md §12).
- `class MasteryConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 192)
- `class ProbeEpisodeConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 219) — Diagnostic-episode policy (spec_probe_eig_redesign.md §5/§11).
- `class ProbeGenerationConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 283) — Parameterized instance generation from admitted family/card bindings (§10).
- `class ProbeDialogueConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 294) — Short adaptive dialogue microprobes (§8.1).
- `class ProbeCalibrationConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 300) — Learner-initiated calibration sessions (§5.9).
- `class ProbeHierarchyConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 311) — Hierarchical family → item shrinkage (§9.7, Checkpoint 4.2).
- `class ProbeLifecycleConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 324) — Metric gates for trusted/revise/retire transitions (§9.7, Checkpoint 4.7).
- `class ProbeShadowConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 343) — Shadow-mode alternative selection policies (§13.3, Checkpoint 5.1).
- `class ProbeBlockConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 355) — Precommitted diagnostic blocks (§5.6, Checkpoint 5.2/5.3).
- `class ProbeConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 376)
- `class PracticeGenerationConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 397) — Difficulty-calibration targets for authored Practice Items and probes.
- `class SeverityExampleConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 423)
- `default_severity_examples() -> dict[str, SeverityExampleConfig]` ([source](../../../../../../src/learnloop/config/schema.py), line 437)
- `class RecallCoverageConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 479)
- `class MisconceptionsConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 498) — Automatic misconception resolution ("close the loop").
- `class FacetDiagnosticConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 535)
- `class ExamSeedingConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 542) — Exam seeding: imported past-exam outcomes as backdated attempts.
- `class TutorQAConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 555) — Tutor Q&A ("ask") behavior.
- `class TutorPromotionConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 629) — Promoting Socratic tutor questions to practice items / learning objects (spec_tutor_promotion.md §5).
- `class TeachBackConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 656) — Teach-back conversation behavior.
- `class GlmOcrConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 681) — [ingest.pdf.glm_ocr]: GLM-OCR's complete layout + recognition pipeline (learnloop.ingest.extractors.glm_ocr).
- `class PdfIngestConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 706)
- `class AnimationConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 727) — AI-generated Manim explainer animations (spec_fork_features §2).
- `class AudioIngestConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 775) — Audio-source ingestion (.mp3/.wav/...): transcription settings.
- `class NativeIngestConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 804) — Shared limits for native media ingestion (media as chat content parts).
- `class IngestBudgetsConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 824) — Per-stage token budgets for ingestion v2 (source-ingestion spec §3.1).
- `class IngestProviderLimits(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 846) — Per-provider context/output limits consulted by preflight (spec §3.1).
- `class IngestRunnerConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 855) — Durable-queue worker settings for ingestion v2 (source-ingestion §6.2).
- `class IngestCostPauseConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 870) — When an automatic question build asks before spending (UX Phase 1, Q5), and its daily guard.
- `class IngestConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 897)
- `class RungVariantsConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 925) — Learner-initiated re-runging (content/authoring/rung_variants).
- `class AIProviderConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 981) — Shared provider fields plus a direct-construction compatibility seam.
  - `_discard_auth_mode(cls, data: Any) -> Any` (line 1001; internal)
  - `__getattr__(self, item: str) -> Any` (line 1006; internal)
  - `__eq__(self, other: object) -> bool` (line 1017; internal)
- `class CodexSDKProviderConfig(_CodexProviderConfig)` ([source](../../../../../../src/learnloop/config/schema.py), line 1050)
- `class CodexHTTPProviderConfig(_CodexProviderConfig)` ([source](../../../../../../src/learnloop/config/schema.py), line 1054)
- `class OpenAICompatibleProviderConfig(AIProviderConfig)` ([source](../../../../../../src/learnloop/config/schema.py), line 1058)
- `class OpenRouterProviderConfig(OpenAICompatibleProviderConfig)` ([source](../../../../../../src/learnloop/config/schema.py), line 1068)
- `class OpenAIEmbeddingProviderConfig(OpenAICompatibleProviderConfig)` ([source](../../../../../../src/learnloop/config/schema.py), line 1074)
- `class VoyageContextualEmbeddingProviderConfig(AIProviderConfig)` ([source](../../../../../../src/learnloop/config/schema.py), line 1091) — ``voyage-context-4`` through ``POST /v1/contextualizedembeddings``.
- `class DeciderProviderConfig(AIProviderConfig)` ([source](../../../../../../src/learnloop/config/schema.py), line 1117) — A decision model (router spec §6): typed questions in, probabilities out.
- `class ChatGPTPlanProviderConfig(AIProviderConfig)` ([source](../../../../../../src/learnloop/config/schema.py), line 1145) — OpenAI models billed to the owner's ChatGPT plan ("Continue with ChatGPT").
  - `_api_or_loopback(cls, value: str | None) -> str | None` (line 1184; internal)
- `class AIRoutingConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1238)
  - `_drop_retired_routes(cls, data: Any) -> Any` (line 1534; internal)
  - `_default_embedding_route(self) -> 'AIRoutingConfig'` (line 1541; internal)
- `class AIConsentRecord(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1564) — One learner OK for one data flow to one AI provider (UX Phase 1, Q4).
- `class AIConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1577)
  - `_normalize_provider_profiles(cls, data: Any) -> Any` (line 1617; internal)
  - `_known_route_budgets(cls, value: dict[str, int]) -> dict[str, int]` (line 1624; internal)
  - `_merge_route_efforts(cls, value: Any) -> Any` (line 1633; internal)
  - `_known_route_efforts(cls, value: dict[str, str]) -> dict[str, str]` (line 1641; internal)
- `class ErrorImpact(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1752) — Error impact settings.
- `class FsrsFittingConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1765) — `learnloop fit fsrs` knobs (architecture_pivot.md Stage 1).
- `class FittingConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1776)
- `class LocksConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1780) — Retired: facet identity locks were removed (owner, 2026-10-12).
- `class EvidenceMassEntry(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1797) — Evidence carried by one attempt type (Fable's-take item 3).
- `default_attempt_type_evidence() -> dict[str, EvidenceMassEntry]` ([source](../../../../../../src/learnloop/config/schema.py), line 1812)
- `default_practice_mode_item_coverage() -> dict[str, float]` ([source](../../../../../../src/learnloop/config/schema.py), line 1834)
- `class EvidenceCorrelationConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1847) — Vault-wide surface-correlation discounting (knowledge-model spec §6).
- `class EvidenceCertificationConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1856) — Bounded certification credit (knowledge-model §5.4).
- `class EvidenceBlueprintsConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1884) — Blueprint recipe likelihood defaults (knowledge-model spec §9.2).
- `class EvidenceConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1895) — Single source of truth for per-attempt-type evidence carried.
  - `_merge_defaults(self) -> 'EvidenceConfig'` (line 1915; internal)
- `class CapabilitiesConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1925) — Capability damping/shrinkage + lazy residual activation (spec §4.2).
- `class TraceEvidenceConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1954) — A6 opportunistic trace evidence and its elicitation budget (Meas §3.A6).
- `class DiagnosticAugmentationConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1975) — Stage 7 live diagnosis rungs.
- `class DiagnosisConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2000) — Slice 1 M2: the live blind grader + asynchronous history-aware diagnoser.
- `class RecurrenceBlockingCutoff(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2090) — One benchmark-set blocking cutoff and the vectors it was measured on.
  - `_a_cosine(self) -> 'RecurrenceBlockingCutoff'` (line 2109; internal)
- `class RecurrenceConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2116) — Slice 2 T1 (M3): recurrence groups with authority (spec_embedding_consumers_v1 §3).
  - `_cutoffs_name_models(self) -> 'RecurrenceConfig'` (line 2163; internal)
- `class StuckPromptConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2170) — "Write what you can" replaces "I don't know" (``mvp-0.13``).
- `class HintsMapsConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2184) — Adaptive hints H1: approach maps (spec_adaptive_hints_v1 §4.3, §4.3.1, §9).
- `class HintsConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2216) — Adaptive hints (spec_adaptive_hints_v1 §9).
- `class ReaderInquiryConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2309) — Reader workbench RW1a: inquiry (spec_reader_workbench_v1 §4.1).
- `class CuesConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2337) — Reader workbench RW3a: margin cues from the Guide (spec_reader_workbench_v1 §6).
- `class WorkbenchConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2392) — Reader workbench RW2a: the resumable scratchpad (spec_reader_workbench_v1 §5.1, §5.9).
- `class RecapConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2461) — Reader workbench RW6a: "Last time here" and Wrap up (spec_reader_workbench_v1 §9.1, §9.6).
- `class FollowupsConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2482) — Reader workbench RW6b part 1: cold follow-ups, the owner's "short unfamiliar problem" (spec_reader_workbench_v1 §9.3-§9.6; UX §4.8-§4.9).
- `class DigestConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2524) — Reader workbench RW6b part 2: the session narrative and the router card's reader section (spec_reader_workbench_v1 §9.2, §9.6; UX §4.8).
- `class ReaderIntentConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2564) — Reader workbench RW1b: the intent box (spec_reader_workbench_v1 §4.2, §4.4).
- `class ReaderActiveReadingConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2597) — Reader workbench RW1b: active reading (spec_reader_workbench_v1 §4.2).
- `class ReaderFormativeConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2615) — Reader workbench RW1b: missed answers as learner text (spec_reader_workbench_v1 §4.2, W1).
- `class LibraryAskConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2630) — Reader workbench RW4a: ask your library (spec_reader_workbench_v1 §7.3, §7.7).
- `class ReaderTutorConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2662) — Reader workbench RW1c: a tutor that looks things up (spec_reader_workbench_v1 §4.6).
- `class LibraryExercisesConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2701) — Reader workbench RW4b: exercises from my sources (spec_reader_workbench_v1 §7.4, §7.7).
- `class FiguresPrefetchConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2726) — Reader RW5d P5 (spec_reader_show_me_figures_v1 §10b.4, §15): the guardrails of figures built ahead of need, each a ``keep`` cap, never a learned number.
- `class FiguresConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2739) — Reader workbench RW5a: explorable figures (spec_reader_workbench_v1 §8, §8.6).
- `class ReaderCompareConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2893) — Reader workbench RW4a: compare pinned passages (spec_reader_workbench_v1 §7.3).
- `class AsPrintedConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2947) — Reader CA1: the problem as printed (ux_reader_compare_ask_v1 §8, K15).
- `class PracticeConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2962) — The practice surfaces' own switches.
- `class RolesConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3008) — Reader workbench RW4e: instructional roles (spec_reader_workbench_v1 §7.9).
- `class ReadingPathsConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3040) — Reader workbench RW7a: reading paths in the Guide (spec_reader_workbench_v1 §10.1).
- `class CurriculumConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3079) — Deliverable curriculum C0a: section coverage and ``reader.correspondents`` (spec_deliverable_curriculum_v1 §6, §12; ux_reader_compare_ask_v1 §6).
- `class NotesConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3148) — Deliverable curriculum C2: notes in the learner's voice, linked (spec_deliverable_curriculum_v1 §10, §12 C2; C2b: the vault's own notes).
  - `_drop_legacy_tend(cls, data: Any) -> Any` (line 3193; internal)
- `class ReaderCorrespondenceConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3200) — Reader CA5a: *find this section in my other books* (ux_reader_compare_ask_v1 §6.2, §6.3; CA5's *also in your books* will share the switch).
- `class ReaderSideBySideConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3232) — Reader CA6: *side by side* (ux_reader_compare_ask_v1 §6.4, X9, K14, C5).
- `class ReaderConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3254) — The Reader's presentation switches (ux_reader_compare_ask_v1 §13).
- `class LearnerTextGapsConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3265) — Learner-text gaps (implementation_handoffs §4, owner-directed 2026-10-12).
- `class EvsiConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3327) — EVSI calibration (docs/reviews/evsi-calibration.md).
- `class ProofCheckConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3348) — The valid-alternative gate for proofs and explanations, in the grader.
- `class RequiredMethodConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3367) — Method-explicit items (owner rule 2026-10-13): the grading side.
- `class ProjectConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3387) — Project understanding M1 (spec_project_understanding_v1): delayed probes.
- `class FamiliesConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3427) — Offline family authoring only; live scheduling remains per card.
- `class PFScalingConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3434) — The scaling check's two configured tiers (Slice 2 §5.6), as route lists.
- `class PFConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3446) — PF-b: generate, verify, select and publish (Slice 2 §5.3-§5.4).
- `class LocalEmbeddingConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3472) — Local contextual retrieval P1a (spec_local_contextual_retrieval_v1 §4).
- `class FallbackEmbeddingConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3502) — Local contextual retrieval P1b (spec §8): the hosted Voyage fallback space.
- `class SourceSpaceConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3522) — The source-space resolver and its fusion (spec §5, §9.2).
- `class EmbeddingConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3540)
  - `privacy_disclosure(self) -> str` (line 3569; public)
- `class GraphNominationConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3580) — Slice 2 T5: embedding nominations for ingest and graph review.
- `class FacetIdentityConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3603) — Facet identity at mint time, and the dedupe command (handoff §4).
- `class FieldConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3655) — Offline F1 analysis only; activation requires a later algorithm successor.
- `class PracticeIndexConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3665) — The practice index: facet dossiers and ``find_practice`` (Slice 2 §5.9).
- `class SourceRetrievalConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3705) — Slice 2 T6: source retrieval (spec_embedding_consumers_v1 §9).
- `class SourceServiceConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3785) — Canonical sources as a shared instructional service (``spec_source_practice_and_probes_v1.md`` §13).
- `class PlacementConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3843) — Learner field F2: starting new material without ceremony (spec §5.2).
- `class PlanConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3867) — Daily-loop DL1: the finite daily plan (``spec_daily_loop_v1.md`` §6, §10).
  - `_shares_leave_room(self) -> 'PlanConfig'` (line 3942; internal)
- `class IntentConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3963) — Daily-loop DL2: intent (``spec_daily_loop_v1.md`` §5, §11).
  - `_targets_are_probabilities(self) -> 'IntentConfig'` (line 3985; internal)
- `class CaptureConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3998) — Daily-loop capture settings (``spec_daily_loop_v1.md`` §10).
- `class RouterWeights(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4009) — The model mixture's component weights (D1: one third each).
  - `validate_total(self) -> 'RouterWeights'` (line 4021; public)
- `class RouterLessonSuggestionsConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4027) — Teacher TE1b: the router suggests a lesson, the learner opts in (spec_teacher_v1 §15.1, §18.4; ``learnloop.daily_plan.lesson_suggestion``).
- `class RouterConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4053) — Action router (spec_action_router_v1).
  - `validate_floor(self) -> 'RouterConfig'` (line 4127; public)
- `class DataCaptureConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4133) — What later offline evaluation needs, recorded now (owner, 2026-11-02; docs/reviews/data-capture-a1-a6.md).
- `class FollowupServeConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4151) — Follow-up generate and serve (FG1; ``docs/specs/spec_followup_generate_serve_v1.md``).
- `class VoiStoppingConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4164) — mvp-0.21 Part 1: four count caps lifted onto value of information.
- `class DeciderRoutesConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4220) — Tier 1 (owner decision 2026-10-13): small judgments the Decider decides, the LLM its fallback.
- `class UiConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4263) — How the desktop app presents learner surfaces (``docs/specs/ux_learnloop_v1.md`` §10).
- `class TeacherWeightConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4290) — The lesson-check weight's switches (spec_teacher_v1 §12.1, §12.2): operational only.
- `class TeacherBriefConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4297) — What the lesson brief holds (§8.1): the prerequisite depth (``keep``) and curriculum C4's switch.
- `class TeacherContextConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4304) — The teacher's context budget (§9.2): the goal's sections whole up to this many tokens (``keep``).
- `class TeacherDelayedConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4310) — Delayed retention and transfer checks (§13).
- `class TeacherConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4319) — Teacher (spec_teacher_v1).
- `class EligibilityConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4379) — One serve/administration eligibility decision (``mvp-0.27``; ``learnloop.serve_eligibility``, ``docs/reviews/serve-eligibility-decision.md``).
- `class ReplayConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4398) — How replay reads the attempt ledger (rebuild equivalence, ``mvp-0.34``; ``REPLAY_LEDGER_ALGORITHM_VERSION``, ``docs/reviews/rebuild-equivalence-fix.md``).
- `class AskConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4413) — One Ask (Reader CA2; ``docs/specs/ux_reader_compare_ask_v1.md`` §7, ``docs/reviews/reader-ca2-one-ask.md``).
- `class AdaptiveDifficultyConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4446) — Adaptive difficulty (``docs/specs/spec_adaptive_difficulty_v1.md`` §11.4).
  - `_ordered_band(cls, value: tuple[float, float]) -> tuple[float, float]` (line 4560; internal)
  - `_forecasters_switch(cls, value: Any) -> Any` (line 4568; internal)
  - `_canonical_forecasters(cls, value: list[str]) -> list[str]` (line 4578; internal)
- `class LearnLoopConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4583)
  - `_normalize_legacy_input(cls, data: Any) -> Any` (line 4671; internal) — Keep direct model validation compatible; implementation lives in compat.
  - `_ensure_effective_defaults(self) -> 'LearnLoopConfig'` (line 4679; internal)
  - `codex(self) -> CodexConfig` (line 4768; public) — Non-serialized compatibility view of ``ai.providers.codex``.
- `default_codex_provider() -> CodexSDKProviderConfig` ([source](../../../../../../src/learnloop/config/schema.py), line 4776) — Return the modeled canonical Codex profile used when none is explicit.
- `default_chatgpt_plan_provider() -> ChatGPTPlanProviderConfig` ([source](../../../../../../src/learnloop/config/schema.py), line 4803) — The code-default ChatGPT-plan profile (plan-first transport T1).
- `deepseek_flash_provider() -> AIProviderConfig` ([source](../../../../../../src/learnloop/config/schema.py), line 4816)
- `deepseek_pro_provider() -> AIProviderConfig` ([source](../../../../../../src/learnloop/config/schema.py), line 4828)
- `openrouter_haiku_provider() -> AIProviderConfig` ([source](../../../../../../src/learnloop/config/schema.py), line 4841) — Claude Haiku through OpenRouter, for cheap metered judges.
- `openrouter_provider() -> AIProviderConfig` ([source](../../../../../../src/learnloop/config/schema.py), line 4852)
- `openrouter_embedding_provider() -> AIProviderConfig` ([source](../../../../../../src/learnloop/config/schema.py), line 4863) — The template's embedding profile, for vaults whose config predates it.
- `openrouter_decider_provider() -> AIProviderConfig` ([source](../../../../../../src/learnloop/config/schema.py), line 4879) — Perplexity Decider v1.1 through OpenRouter (router spec D4, owner).

### Module constants

- `_COMPAT_OPTIONAL_PROVIDER_FIELDS` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 945)
- `KNOWN_INPUT_MODALITIES` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 978)
- `VOYAGE_CONTEXTUAL_PROFILE_TYPE` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1088)
- `DECIDER_PROFILE_TYPE` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1108)
- `DEFAULT_DECIDER_PROVIDER` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1109)
- `DEFAULT_EMBEDDING_PROVIDER` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1110)
- `DEFAULT_DECIDER_MODEL` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1111)
- `DEFAULT_DECIDER_PRICE_PER_MILLION_INPUT` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1114)
- `CHATGPT_PLAN_PROFILE_TYPE` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1139)
- `CHATGPT_PLAN_API_BASE_URL` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1142)
- `RETIRED_ROUTES` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1218)
- `DEFAULT_OUTPUT_TOKENS` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1551)
- `REASONING_EFFORTS` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1553)
- `DEFAULT_ROUTE_REASONING_EFFORT` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1556)
- `DEFAULT_CODEX_MODEL` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1659)
- `DEFAULT_CODEX_REASONING_EFFORT` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1660)
- `LEGACY_CODEX_MODEL` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1661)
- `CODEX_LOW_PROVIDER` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1662)
- `CODEX_MEDIUM_PROVIDER` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1663)
- `CODEX_LUNA_PROVIDER` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1667)
- `CODEX_LUNA_MODEL` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1668)
- `CODEX_PROVIDER_NAMES` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1669)
- `OPENROUTER_HAIKU_PROVIDER` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1673)
- `OPENROUTER_HAIKU_MODEL` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1674)
- `OPENROUTER_TRANSCRIPTION_PROVIDER` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1675)
- `AGENT_HARNESS_PROFILE_TYPES` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1681)
- `CHATGPT_PLAN_PROVIDER` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1688)
- `CHATGPT_LOW_PROVIDER` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1689)
- `CHATGPT_MEDIUM_PROVIDER` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1690)
- `CHATGPT_LUNA_PROVIDER` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1691)
- `DEFAULT_CHATGPT_PLAN_MODEL` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1692)
- `CHATGPT_LUNA_MODEL` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1693)
- `CHATGPT_PLAN_PROVIDER_NAMES` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1694)
- `DEFAULT_SERVING_TASK_ROUTES` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1700)
- `LEGACY_CODEX_TASK_ROUTES` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1725)
- `CODEX_TO_PLAN_PROFILE` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1744)
- `DEFAULT_RECALL_TARGETS` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 3954)
- `AD_OUTSIDE_FORECASTERS` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 4443)

## Internal implementation anchors

- `class _CodexProviderConfig(AIProviderConfig)` ([source](../../../../../../src/learnloop/config/schema.py), line 1028)
- `_require_known_routes(value: dict[str, Any], setting: str) -> None` ([source](../../../../../../src/learnloop/config/schema.py), line 1652)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/backfill|learnloop.adaptive_difficulty.backfill]] — imports `DEFAULT_DECIDER_PRICE_PER_MILLION_INPUT`
- [[Reference/Modules/learnloop/ai/agent_harness|learnloop.ai.agent_harness]] — imports `AGENT_HARNESS_PROFILE_TYPES`
- [[Reference/Modules/learnloop/ai/chatgpt_plan/routes|learnloop.ai.chatgpt_plan.routes]] — imports `CHATGPT_PLAN_PROFILE_TYPE`
- [[Reference/Modules/learnloop/ai/native_media|learnloop.ai.native_media]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/ai/output_budget|learnloop.ai.output_budget]] — imports `DEFAULT_OUTPUT_TOKENS`
- [[Reference/Modules/learnloop/ai/providers/chatgpt_plan|learnloop.ai.providers.chatgpt_plan]] — imports `CHATGPT_PLAN_API_BASE_URL`
- [[Reference/Modules/learnloop/ai/providers/decider|learnloop.ai.providers.decider]] — imports `DEFAULT_DECIDER_MODEL`, `DEFAULT_DECIDER_PRICE_PER_MILLION_INPUT`
- [[Reference/Modules/learnloop/ai/providers/openrouter_catalog|learnloop.ai.providers.openrouter_catalog]] — imports `KNOWN_INPUT_MODALITIES`
- [[Reference/Modules/learnloop/ai/review_spend|learnloop.ai.review_spend]] — imports `DEFAULT_OUTPUT_TOKENS`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `CHATGPT_PLAN_PROFILE_TYPE`, `DECIDER_PROFILE_TYPE`, `DEFAULT_DECIDER_PROVIDER`, `DEFAULT_EMBEDDING_PROVIDER`, `VOYAGE_CONTEXTUAL_PROFILE_TYPE`
- [[Reference/Modules/learnloop/cli/ai|learnloop.cli.ai]] — imports `CHATGPT_PLAN_API_BASE_URL`, `CHATGPT_PLAN_PROFILE_TYPE`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `module`
- [[Reference/Modules/learnloop/config/compat|learnloop.config.compat]] — imports `AIProviderConfig`, `AudioIngestConfig`, `CodexHTTPProviderConfig`, `CodexSDKProviderConfig`, `DEFAULT_CODEX_MODEL`, `DEFAULT_CODEX_REASONING_EFFORT`, `LEGACY_CODEX_MODEL`, `LEGACY_CODEX_TASK_ROUTES`, `LearnLoopConfig`, `OPENROUTER_TRANSCRIPTION_PROVIDER`, `openrouter_provider`; statically calls `AudioIngestConfig`, `openrouter_provider`
- [[Reference/Modules/learnloop/config/loader|learnloop.config.loader]] — imports `CODEX_LOW_PROVIDER`, `CODEX_LUNA_PROVIDER`, `CODEX_MEDIUM_PROVIDER`, `CodexHTTPProviderConfig`, `CodexSDKProviderConfig`, `LearnLoopConfig`
- [[Reference/Modules/learnloop/config/template|learnloop.config.template]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/content/facet_identity/authority|learnloop.content.facet_identity.authority]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/content/proposals/method_phrasing|learnloop.content.proposals.method_phrasing]] — imports `DECIDER_PROFILE_TYPE`, `DEFAULT_DECIDER_PROVIDER`
- [[Reference/Modules/learnloop/diagnosis/voi_stopping|learnloop.diagnosis.voi_stopping]] — imports `VoiStoppingConfig`; statically calls `VoiStoppingConfig`
- [[Reference/Modules/learnloop/evsi_calibration/experiments|learnloop.evsi_calibration.experiments]] — imports `ProbeConfig`; statically calls `ProbeConfig`
- [[Reference/Modules/learnloop/evsi_calibration/multifamily|learnloop.evsi_calibration.multifamily]] — imports `ProbeEpisodeConfig`; statically calls `ProbeEpisodeConfig`
- [[Reference/Modules/learnloop/evsi_calibration/policies|learnloop.evsi_calibration.policies]] — imports `ProbeEpisodeConfig`; statically calls `ProbeEpisodeConfig`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/replay|learnloop.experiments.contextual_embeddings.e1.replay]] — imports `DEFAULT_EMBEDDING_PROVIDER`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/live|learnloop.experiments.contextual_embeddings.live]] — imports `DEFAULT_EMBEDDING_PROVIDER`
- [[Reference/Modules/learnloop/ingest/extractors/glm_ocr|learnloop.ingest.extractors.glm_ocr]] — imports `GlmOcrConfig`; statically calls `GlmOcrConfig`
- [[Reference/Modules/learnloop/ops/contamination/judge|learnloop.ops.contamination.judge]] — imports `DEFAULT_DECIDER_PROVIDER`, `DEFAULT_OUTPUT_TOKENS`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `RETIRED_ROUTES`
- [[Reference/Modules/learnloop/ops/family_proposals|learnloop.ops.family_proposals]] — imports `DEFAULT_OUTPUT_TOKENS`
- [[Reference/Modules/learnloop/ops/plan_transport|learnloop.ops.plan_transport]] — imports `CHATGPT_LOW_PROVIDER`, `CHATGPT_MEDIUM_PROVIDER`, `CODEX_PROVIDER_NAMES`, `CODEX_TO_PLAN_PROFILE`, `LEGACY_CODEX_TASK_ROUTES`
- [[Reference/Modules/learnloop/reader/reader_quick_check|learnloop.reader.reader_quick_check]] — imports `DEFAULT_OUTPUT_TOKENS`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `StorageConfig`; statically calls `StorageConfig`
- [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]] — imports `DEFAULT_RECALL_TARGETS`
- [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]] — imports `CHATGPT_PLAN_PROFILE_TYPE`
- [[Reference/Modules/learnloop/source_retrieval/fallback_space|learnloop.source_retrieval.fallback_space]] — imports `LearnLoopConfig`, `VOYAGE_CONTEXTUAL_PROFILE_TYPE`
- [[Reference/Modules/learnloop/source_retrieval/source_vectors|learnloop.source_retrieval.source_vectors]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `TutorQAConfig`
- [[Reference/Modules/learnloop_sidecar/handlers/first_run|learnloop_sidecar.handlers.first_run]] — imports `DEFAULT_CHATGPT_PLAN_MODEL`, `DEFAULT_SERVING_TASK_ROUTES`
- [[Reference/Modules/learnloop_sidecar/handlers/settings|learnloop_sidecar.handlers.settings]] — imports `KNOWN_INPUT_MODALITIES`

### Repository tooling consumers

- [scripts/benchmark_chatgpt_plan_latency.py](../../../../../../scripts/benchmark_chatgpt_plan_latency.py); calls `ChatGPTPlanProviderConfig`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/compat|learnloop.config.compat]] — imports `CodexConfig`, `codex_config_view`, `discard_retired_provider_settings`, `normalize_ai_input`, `normalize_config_input`; calls `codex_config_view`, `discard_retired_provider_settings`, `normalize_ai_input`, `normalize_config_input`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`, `urllib`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/backfill|learnloop.adaptive_difficulty.backfill]], [[Reference/Modules/learnloop/ai/agent_harness|learnloop.ai.agent_harness]], [[Reference/Modules/learnloop/ai/chatgpt_plan/routes|learnloop.ai.chatgpt_plan.routes]], [[Reference/Modules/learnloop/ai/native_media|learnloop.ai.native_media]], [[Reference/Modules/learnloop/ai/output_budget|learnloop.ai.output_budget]] and 32 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/codex_cli_fakes.py](../../../../../../tests/codex_cli_fakes.py) — direct import
- [tests/rw2b_fix10_base_sequence.py](../../../../../../tests/rw2b_fix10_base_sequence.py) — direct import
- [tests/rw2b_fix11_base_sequence.py](../../../../../../tests/rw2b_fix11_base_sequence.py) — direct import
- [tests/rw2c_base_sequence.py](../../../../../../tests/rw2c_base_sequence.py) — direct import
- [tests/test_ad1_codex_review_fixes.py](../../../../../../tests/test_ad1_codex_review_fixes.py) — direct import
  - `test_a_configured_ad_price_is_a_classified_config_leaf`
- [tests/test_ad23_owner_decisions.py](../../../../../../tests/test_ad23_owner_decisions.py) — direct import
  - `test_the_owner_defaults_of_2026_10_19`
- [tests/test_ad23_t1_routes.py](../../../../../../tests/test_ad23_t1_routes.py) — direct import
  - `test_ads_routes_are_in_the_plan_first_table`
  - `test_inside_an_ad_operation_no_route_asks_and_no_grant_serves`
  - `test_under_code_defaults_each_ad_route_is_the_plan_and_codex_is_refused`
- [tests/test_attempt_content_state_successor.py](../../../../../../tests/test_attempt_content_state_successor.py) — direct import
  - `test_mvp037_is_one_constant_after_mvp036`
- [tests/test_chatgpt_plan_cli.py](../../../../../../tests/test_chatgpt_plan_cli.py) — direct import
  - `test_doctor_ignores_an_unrouted_plan_profile`
- [tests/test_chatgpt_plan_landing.py](../../../../../../tests/test_chatgpt_plan_landing.py) — direct import
  - `test_a_snapshot_diagnosis_on_the_plan_records_what_it_served_with_its_row_and_forecasts`
- [tests/test_chatgpt_plan_provider.py](../../../../../../tests/test_chatgpt_plan_provider.py) — direct import
  - `test_an_interrupt_during_the_token_refresh_keeps_the_new_tokens_and_sends_nothing`
  - `test_billing_class_is_subscription`
- [tests/test_chatgpt_plan_workspace.py](../../../../../../tests/test_chatgpt_plan_workspace.py) — direct import
  - `test_inline_mode_serves_a_workspace_over_its_budget_in_tools_mode`
  - `test_the_profile_default_is_inline`
  - `test_the_profile_validates_its_workspace_settings`
- [tests/test_codex_lockdown_round2.py](../../../../../../tests/test_codex_lockdown_round2.py) — direct import
- [tests/test_cold_retry_reschedule.py](../../../../../../tests/test_cold_retry_reschedule.py) — direct import
  - `test_mvp038_is_one_constant_after_mvp037`
- [tests/test_config_refactor.py](../../../../../../tests/test_config_refactor.py) — direct import
  - `test_config_responsibilities_have_canonical_module_owners`
  - `test_minimal_template_preserves_non_provider_effective_defaults`
- [tests/test_curriculum_c1_plan_follows_path.py](../../../../../../tests/test_curriculum_c1_plan_follows_path.py) — direct import
  - `test_the_switch_is_on_by_default_classified_and_needs_the_curriculum_and_rw7b`
- [tests/test_curriculum_c3_exam_scoping.py](../../../../../../tests/test_curriculum_c3_exam_scoping.py) — direct import
  - `test_the_config_default_is_on`
- [tests/test_data_capture_successor.py](../../../../../../tests/test_data_capture_successor.py) — direct import
  - `test_every_defaults_snapshot_is_recomputed_and_moves_only_by_the_new_keys`
  - `test_the_switches_are_on_by_default_and_the_gate_reads_the_tag`
- [tests/test_decider_client.py](../../../../../../tests/test_decider_client.py) — direct import
  - `test_error_statuses_surface_without_parsing`
  - `test_missing_key_and_oversized_state_refuse_before_any_request`
  - `test_probe_reads_the_free_listing_without_a_key`
  - `test_settings_resolve_from_the_dialect`
- [tests/test_decider_landing.py](../../../../../../tests/test_decider_landing.py) — direct import
  - `test_inside_an_automatic_builds_request_gate_the_span_check_is_admitted_and_settled`
  - `test_nothing_in_tier1_reads_the_deleted_route_check`
  - `test_the_decider_requests_no_output_budget_and_a_fallback_route_keeps_the_shared_policy`
  - `test_the_tier1_disclosure_and_the_one_ok_use_one_recipient_for_a_direct_perplexity_route`
  - `test_tier1_judgments_move_only_at_mvp022`
- [tests/test_diagnosis_input_provenance.py](../../../../../../tests/test_diagnosis_input_provenance.py) — direct import
  - `test_f5_every_defaults_snapshot_records_the_switch_off`
- [tests/test_diagnosis_input_provenance_landing.py](../../../../../../tests/test_diagnosis_input_provenance_landing.py) — direct import
  - `test_the_release_switch_defaults_off_and_the_default_source_is_the_narrow_rule`
- [tests/test_evsi_calibration_sim.py](../../../../../../tests/test_evsi_calibration_sim.py) — direct import
  - `test_simulation_runs_every_policy_on_common_random_numbers`
  - `test_the_incumbent_arm_includes_todays_robust_completion_gate`
- [tests/test_evsi_multisim.py](../../../../../../tests/test_evsi_multisim.py) — direct import
  - `test_each_ablation_puts_back_exactly_one_piece_of_the_successor`
  - `test_the_successor_arms_lift_the_episode_maximum_onto_value`
- [tests/test_facet_identity_composition.py](../../../../../../tests/test_facet_identity_composition.py) — direct import
  - `test_a_configured_decider_route_builds_the_decider_judge_without_a_call`
  - `test_a_decider_profile_may_serve_the_facet_identity_judge_route_only`
  - `test_facets_with_evidence_merge_whatever_the_retired_lock_key_says`
- [tests/test_facet_reword_confirm_review.py](../../../../../../tests/test_facet_reword_confirm_review.py) — direct import
  - `test_the_policy_follows_the_switch`
- [tests/test_family_proposals.py](../../../../../../tests/test_family_proposals.py) — direct import
  - `test_route_availability_never_changes_preview_model`
- [tests/test_field_config.py](../../../../../../tests/test_field_config.py) — direct import
  - `test_field_defaults_are_offline_and_incumbent_only`
  - `test_field_paid_routes_are_explicit_not_global`
  - `test_retired_numeric_probability_route_loads_with_a_deprecation_note`
- [tests/test_field_workbench_signals.py](../../../../../../tests/test_field_workbench_signals.py) — direct import
  - `test_the_switch_is_on_by_default_and_classified`
- [tests/test_figures_prefetch.py](../../../../../../tests/test_figures_prefetch.py) — direct import
  - `test_the_switch_defaults_on`
- [tests/test_figures_prefetch_review_fixes.py](../../../../../../tests/test_figures_prefetch_review_fixes.py) — direct import
  - `test_f15_figures_ahead_of_need_are_on_by_default_and_the_suite_keeps_hooks_inert`
- [tests/test_figures_scope_redesign.py](../../../../../../tests/test_figures_scope_redesign.py) — direct import
  - `test_no_code_path_can_store_or_render_verified_or_checked`
- [tests/test_figures_show_me.py](../../../../../../tests/test_figures_show_me.py) — direct import
  - `test_the_intent_boxs_figure_action_is_show_me_while_on`
- [tests/test_followup_successor.py](../../../../../../tests/test_followup_successor.py) — direct import
  - `test_new_vaults_get_true_effectively_and_older_templates_stay_as_they_were`
- [tests/test_glm_ocr.py](../../../../../../tests/test_glm_ocr.py) — direct import
  - `test_r2_f3_the_z_ai_ok_names_only_z_ai`
  - `test_the_legacy_path_uploads_only_with_the_ok_and_caches_by_backend`
- [tests/test_help_fold_attach_successor.py](../../../../../../tests/test_help_fold_attach_successor.py) — direct import
  - `test_mvp042_is_one_constant_after_mvp041_and_the_latest`
- [tests/test_ingest_runner.py](../../../../../../tests/test_ingest_runner.py) — direct import
  - `test_legacy_one_shot_pipeline_never_uses_the_native_engine`
- [tests/test_judge_routes.py](../../../../../../tests/test_judge_routes.py) — direct import
  - `test_decider_readiness_is_key_presence_without_network`
  - `test_the_llm_judge_runs_on_the_subscription_route_by_default`
- [tests/test_lp_claim_fixes.py](../../../../../../tests/test_lp_claim_fixes.py) — direct import
  - `test_one_switch_on_by_default_classified_and_gated_by_the_tag`
- [tests/test_method_explicit_landing.py](../../../../../../tests/test_method_explicit_landing.py) — direct import
  - `test_the_judges_decider_defaults_to_the_tier1_deciders_profile`
  - `test_the_statement_judgment_is_a_tier1_content_task_with_its_own_switch`
  - `test_the_tier1_disclosure_names_the_statement_judgment`
- [tests/test_method_explicit_upgrade.py](../../../../../../tests/test_method_explicit_upgrade.py) — direct import
  - `test_defaults_fingerprint_is_recorded_for_the_successor`
- [tests/test_mvp013_upgrade.py](../../../../../../tests/test_mvp013_upgrade.py) — direct import
  - `test_defaults_fingerprint_is_recorded_for_the_successor`
- [tests/test_mvp014_upgrade.py](../../../../../../tests/test_mvp014_upgrade.py) — direct import
  - `test_defaults_fingerprint_is_recorded_for_the_plan_successor`
- [tests/test_mvp015_upgrade.py](../../../../../../tests/test_mvp015_upgrade.py) — direct import
  - `test_defaults_fingerprint_is_recorded_for_the_probe_tie_successor`
- [tests/test_mvp016_upgrade.py](../../../../../../tests/test_mvp016_upgrade.py) — direct import
  - `test_defaults_fingerprint_is_recorded_for_the_learner_text_gap_successor`
- [tests/test_mvp017_upgrade.py](../../../../../../tests/test_mvp017_upgrade.py) — direct import
  - `test_defaults_fingerprint_is_recorded_for_the_route_check_successor`
- [tests/test_mvp020_upgrade.py](../../../../../../tests/test_mvp020_upgrade.py) — direct import
  - `test_defaults_fingerprint_is_recorded_for_the_route_rules_successor`
- [tests/test_mvp021_upgrade.py](../../../../../../tests/test_mvp021_upgrade.py) — direct import
  - `test_defaults_fingerprint_is_recorded_for_every_successor`
- [tests/test_mvp024_upgrade.py](../../../../../../tests/test_mvp024_upgrade.py) — direct import
  - `test_the_floor_must_leave_room_for_the_draw`
- [tests/test_native_media_readiness.py](../../../../../../tests/test_native_media_readiness.py) — direct import
- [tests/test_openai_embedding_client.py](../../../../../../tests/test_openai_embedding_client.py) — direct import
  - `test_embedding_route_defaults_but_a_vault_that_never_enables_embeddings_sends_nothing`
- [tests/test_openrouter_video_client.py](../../../../../../tests/test_openrouter_video_client.py) — direct import
- [tests/test_output_budget.py](../../../../../../tests/test_output_budget.py) — direct import
- [tests/test_pf_cli.py](../../../../../../tests/test_pf_cli.py) — direct import
  - `test_template_keeps_generation_off_and_caps_publication`
- [tests/test_plan_determinism.py](../../../../../../tests/test_plan_determinism.py) — direct import
  - `test_every_defaults_snapshot_records_the_switch_on`
- [tests/test_plan_first_transport.py](../../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_a_harness_profile_without_the_opt_in_raises_before_any_process`
  - `test_code_defaults_name_the_plan_tiers_with_the_codex_efforts_and_slugs`
  - `test_doctor_reports_each_pinned_codex_setting_and_fix_rewrites_it`
  - `test_every_task_under_code_defaults_resolves_tool_free_and_never_codex`
  - `test_f1_a_configured_metered_fallback_provider_is_never_used_silently_for_a_plan_route`
  - `test_f2_openrouter_is_offered_only_when_the_feature_could_use_it`
  - `test_f3_the_question_build_asks_and_a_grant_serves_it_priced_as_metered`
  - `test_f5_doctor_fix_keeps_the_tier_of_a_legacy_codex_route_value`
  - `test_the_plan_bearer_goes_only_to_openai_or_loopback`
- [tests/test_plan_first_transport_grant_scope.py](../../../../../../tests/test_plan_first_transport_grant_scope.py) — direct import
  - `test_a_grant_counts_only_in_the_learners_request_or_a_job_carrying_it`
  - `test_a_hint_job_started_in_the_request_carries_its_grant_and_a_background_one_does_not`
  - `test_a_manual_fallback_is_never_replaced_by_a_grant`
  - `test_the_background_build_launcher_never_uses_the_grant`
  - `test_the_cli_commands_grant_is_its_own_threads_only`
  - `test_the_imports_time_boxed_key_check_carries_its_requests_grant`
- [tests/test_plan_first_transport_paid_roles.py](../../../../../../tests/test_plan_first_transport_paid_roles.py) — direct import
  - `test_a_grant_routes_a_paid_role_to_openrouter_priced_as_metered_and_a_ready_plan_comes_first`
  - `test_every_paid_role_resolves_to_the_plan_and_asks_before_openrouter`
- [tests/test_plan_follows_path.py](../../../../../../tests/test_plan_follows_path.py) — direct import
  - `test_the_switch_is_on_by_default_classified_and_acts_only_at_the_tag_with_the_guide_on`
- [tests/test_practice_index_find.py](../../../../../../tests/test_practice_index_find.py) — direct import
  - `test_find_dry_run_names_metered_rerank_prices_and_caps`
- [tests/test_probability_prep.py](../../../../../../tests/test_probability_prep.py) — direct import
  - `test_decider_end_to_end_through_the_fake_endpoint`
  - `test_llm_judge_metered_route_is_isolated_bounded_and_ledgered`
  - `test_rate_limits_retry_within_caps_and_malformed_answers_fail_closed`
- [tests/test_reader_ca2_one_ask.py](../../../../../../tests/test_reader_ca2_one_ask.py) — direct import
  - `test_the_successor_is_one_constant_after_rebuild_equivalence`
- [tests/test_reader_ca5_also_in_books.py](../../../../../../tests/test_reader_ca5_also_in_books.py) — direct import
  - `test_the_hide_preferences_default_to_shown`
- [tests/test_reader_ca5a_find_section.py](../../../../../../tests/test_reader_ca5a_find_section.py) — direct import
  - `test_the_switch_is_on_by_default`
- [tests/test_reader_ca6_side_by_side.py](../../../../../../tests/test_reader_ca6_side_by_side.py) — direct import
  - `test_the_switch_is_on_by_default`
- [tests/test_reader_followups_successor.py](../../../../../../tests/test_reader_followups_successor.py) — direct import
  - `test_mvp039_is_one_constant_after_mvp038_and_the_latest`
- [tests/test_reader_intentions.py](../../../../../../tests/test_reader_intentions.py) — direct import
  - `test_the_readers_test_fixture_is_the_sidecars_palette`
- [tests/test_reader_rw2b_fix9.py](../../../../../../tests/test_reader_rw2b_fix9.py) — direct import
  - `test_the_default_is_off`
- [tests/test_reader_rw2b_review.py](../../../../../../tests/test_reader_rw2b_review.py) — direct import
  - `test_f11_every_key_rw2b_added_is_classified`
- [tests/test_reading_paths.py](../../../../../../tests/test_reading_paths.py) — direct import
  - `test_on_by_default_classified_and_the_contract_and_palette_gain_only_rw7a_keys`
- [tests/test_reading_step_switch.py](../../../../../../tests/test_reading_step_switch.py) — direct import
  - `test_every_defaults_snapshot_records_the_switch_on`
- [tests/test_rebuild_equivalence_review.py](../../../../../../tests/test_rebuild_equivalence_review.py) — direct import
  - `test_the_switch_is_on_by_default_and_classified`
- [tests/test_recurrence_benchmarks.py](../../../../../../tests/test_recurrence_benchmarks.py) — direct import
  - `test_b3_recommends_only_at_the_serving_width_with_its_provenance`
- [tests/test_recurrence_commands.py](../../../../../../tests/test_recurrence_commands.py) — direct import
  - `test_a_blocking_cutoff_must_be_a_cosine_and_name_what_it_was_measured_on`
  - `test_defaults_fingerprint_is_recorded_for_the_successor`
- [tests/test_router_offer_log.py](../../../../../../tests/test_router_offer_log.py) — direct import
- [tests/test_router_probe_ties.py](../../../../../../tests/test_router_probe_ties.py) — direct import
- [tests/test_sketch_service.py](../../../../../../tests/test_sketch_service.py) — direct import
  - `test_the_shipped_default_is_on`
- [tests/test_source_retrieval_guards.py](../../../../../../tests/test_source_retrieval_guards.py) — direct import
  - `test_at_most_four_spans_reach_the_tutor`
- [tests/test_source_roles.py](../../../../../../tests/test_source_roles.py) — direct import
  - `test_every_roles_key_and_the_route_are_classified_as_operational_switches_and_bounds`
- [tests/test_t6_followup_review.py](../../../../../../tests/test_t6_followup_review.py) — direct import
  - `test_a_route_override_cannot_exceed_the_profile_maximum`
- [tests/test_teacher_te0_review_fixes.py](../../../../../../tests/test_teacher_te0_review_fixes.py) — direct import
  - `test_the_switch_is_on_by_default_and_registered`
- [tests/test_teacher_te1_review_fixes.py](../../../../../../tests/test_teacher_te1_review_fixes.py) — direct import
  - `test_f5_a_forecast_agreeing_with_the_cold_prediction_leaves_the_mass_near_the_learned_one`
- [tests/test_teacher_te1_successor.py](../../../../../../tests/test_teacher_te1_successor.py) — direct import
  - `test_every_defaults_snapshot_drops_to_mains_value_without_the_teacher_keys`
  - `test_no_openrouter_offer_for_a_lesson_until_its_price_is_set`
- [tests/test_teacher_te1_weight.py](../../../../../../tests/test_teacher_te1_weight.py) — direct import
  - `test_planted_recovery_a_check_whose_cold_outcomes_agree_raises_the_mass`
  - `test_the_pool_implied_mass_is_the_parametric_mass_at_lambda_zero`
- [tests/test_teacher_te1b_suggestions.py](../../../../../../tests/test_teacher_te1b_suggestions.py) — direct import
  - `test_every_defaults_snapshot_drops_to_te1s_value_without_the_suggestion_keys`
- [tests/test_tier1_decider.py](../../../../../../tests/test_tier1_decider.py) — direct import
  - `test_serving_judgments_wait_for_the_successor_and_the_router_is_never_tier1`
- [tests/test_ux_phase1_connect_ai.py](../../../../../../tests/test_ux_phase1_connect_ai.py) — direct import
  - `test_continue_with_chatgpt_routes_every_use_case_to_the_plan`
- [tests/test_ux_phase1_round2_review.py](../../../../../../tests/test_ux_phase1_round2_review.py) — direct import
  - `test_f2_the_switch_is_on_by_default_and_documented`
- [tests/test_ux_phase2_shell.py](../../../../../../tests/test_ux_phase2_shell.py) — direct import
  - `test_the_shell_switch_accepts_only_its_two_shells`
- [tests/test_ux_phase4_feedback.py](../../../../../../tests/test_ux_phase4_feedback.py) — direct import
  - `test_the_switch_accepts_only_its_two_presentations`
- [tests/test_voi_merge_composition.py](../../../../../../tests/test_voi_merge_composition.py) — direct import
  - `test_misconception_labels_are_charged_the_learners_recurrence_measured_cost`
  - `test_rank_four_is_off_by_default`
  - `test_rank_four_on_charges_only_misconceptions_confusions_and_unknown_causes`
- [tests/test_voi_stopping.py](../../../../../../tests/test_voi_stopping.py) — direct import
- [tests/test_voi_v2.py](../../../../../../tests/test_voi_v2.py) — direct import
  - `test_the_study_switches_default_to_the_recommendation`
- [tests/test_voyage_fallback.py](../../../../../../tests/test_voyage_fallback.py) — direct import
  - `test_errors_never_carry_the_key_or_the_body`
- [tests/voi_restore_scenarios.py](../../../../../../tests/voi_restore_scenarios.py) — direct import

## Modification guidance

- Change configuration behavior in the schema, loader, compatibility normalizer, or template owner that matches the concern; preserve one-way legacy normalization.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
