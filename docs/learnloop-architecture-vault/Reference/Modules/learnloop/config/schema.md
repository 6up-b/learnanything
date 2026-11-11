---
title: "learnloop.config.schema"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/config/schema.py"
source_paths:
  - "src/learnloop/config/schema.py"
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
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/config/_package|learnloop.config]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps schema behavior inside its owning package, [[Reference/Modules/learnloop/config/_package|learnloop.config]]. Its public surface centers on `StorageConfig`, `AlgorithmsConfig`, `SchedulerSurpriseConfig`, `SchedulerFollowupConfig`, `SchedulerConfig`, `GoalsConfig`, `HypothesisConfig`, `MasteryIRTConfig` and 138 more public symbols.

The authoritative system-level explanation remains in [[Configuration]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py) |
| Source lines | 5079 |
| Owning package | [[Reference/Modules/learnloop/config/_package|learnloop.config]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class StorageConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 11)
- `class AlgorithmsConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 15)
- `class SchedulerSurpriseConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 23)
- `class SchedulerFollowupConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 40)
- `class SchedulerConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 87)
- `class GoalsConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 115)
- `class HypothesisConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 132)
- `class MasteryIRTConfig(KeepsRetiredFields)` ([source](../../../../../../src/learnloop/config/schema.py), line 148)
- `class ProbeIRTConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 178)
- `class ProbeSelfTagConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 188) — Learner self-attributed misconception probe coverage.
- `class MasteryConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 197)
- `class ProbeEpisodeConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 223) — Diagnostic-episode policy.
- `class ProbeGenerationConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 287) — Parameterized instance generation from admitted family/card bindings.
- `class ProbeDialogueConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 298) — Short adaptive dialogue microprobes.
- `class ProbeCalibrationConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 304) — Learner-initiated calibration sessions.
- `class ProbeHierarchyConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 315) — Hierarchical family → item shrinkage.
- `class ProbeLifecycleConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 328) — Metric gates for trusted/revise/retire transitions.
- `class ProbeShadowConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 347) — Shadow-mode alternative selection policies.
- `class ProbeBlockConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 359) — Precommitted diagnostic blocks.
- `class ProbeConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 380)
- `class PracticeGenerationConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 400) — Difficulty-calibration targets for authored Practice Items and probes.
- `class SeverityExampleConfig(KeepsRetiredFields)` ([source](../../../../../../src/learnloop/config/schema.py), line 425)
- `default_severity_examples() -> dict[str, SeverityExampleConfig]` ([source](../../../../../../src/learnloop/config/schema.py), line 438)
- `class RecallCoverageConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 480)
- `class MisconceptionsConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 499) — Automatic misconception resolution ("close the loop").
- `class FacetDiagnosticConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 536)
- `class ExamSeedingConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 543) — Exam seeding: imported past-exam outcomes as backdated attempts.
- `class TutorQAConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 556) — Tutor Q&A ("ask") behavior.
- `class TutorPromotionConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 628) — Promoting Socratic tutor questions to practice items / learning objects.
- `class TeachBackConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 654) — Teach-back conversation behavior.
- `class GlmOcrConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 679) — [ingest.pdf.glm_ocr]: GLM-OCR's complete layout + recognition pipeline (learnloop.ingest.extractors.glm_ocr).
- `class PdfIngestConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 704)
- `class AnimationConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 725) — AI-generated Manim explainer animations.
- `class AudioIngestConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 773) — Audio-source ingestion (.mp3/.wav/...): transcription settings.
- `class NativeIngestConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 802) — Shared limits for native media ingestion (media as chat content parts).
- `class IngestBudgetsConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 822) — Per-stage token budgets for ingestion v2.
- `class IngestProviderLimits(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 844) — Per-provider context/output limits consulted by preflight.
- `class IngestRunnerConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 853) — Durable-queue worker settings for ingestion v2.
- `class IngestCostPauseConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 868) — When an automatic question build asks before spending, and its daily guard.
- `class IngestConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 894)
- `class RungVariantsConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 921) — Learner-initiated re-runging (content/authoring/rung_variants).
- `class AIProviderConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 977) — Shared provider fields plus a direct-construction compatibility seam.
  - `_discard_auth_mode(cls, data: Any) -> Any` (line 997; internal)
  - `__getattr__(self, item: str) -> Any` (line 1002; internal)
  - `__eq__(self, other: object) -> bool` (line 1013; internal)
- `class CodexSDKProviderConfig(_CodexProviderConfig)` ([source](../../../../../../src/learnloop/config/schema.py), line 1046)
- `class CodexHTTPProviderConfig(_CodexProviderConfig)` ([source](../../../../../../src/learnloop/config/schema.py), line 1050)
- `class OpenAICompatibleProviderConfig(AIProviderConfig)` ([source](../../../../../../src/learnloop/config/schema.py), line 1054)
- `class OpenRouterProviderConfig(OpenAICompatibleProviderConfig)` ([source](../../../../../../src/learnloop/config/schema.py), line 1064)
- `class OpenAIEmbeddingProviderConfig(OpenAICompatibleProviderConfig)` ([source](../../../../../../src/learnloop/config/schema.py), line 1070)
- `class VoyageContextualEmbeddingProviderConfig(AIProviderConfig)` ([source](../../../../../../src/learnloop/config/schema.py), line 1086) — ``voyage-context-4`` through ``POST /v1/contextualizedembeddings``.
- `class DeciderProviderConfig(AIProviderConfig)` ([source](../../../../../../src/learnloop/config/schema.py), line 1112) — A decision model: typed questions in, probabilities out.
- `class ChatGPTPlanProviderConfig(AIProviderConfig)` ([source](../../../../../../src/learnloop/config/schema.py), line 1140) — OpenAI models billed to the owner's ChatGPT plan ("Continue with ChatGPT").
  - `_api_or_loopback(cls, value: str | None) -> str | None` (line 1179; internal)
- `class AIRoutingConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1229)
  - `_drop_retired_routes(cls, data: Any) -> Any` (line 1508; internal)
  - `_default_embedding_route(self) -> 'AIRoutingConfig'` (line 1515; internal)
- `class AIConsentRecord(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1538) — One learner OK for one data flow to one AI provider.
- `class AIConfig(KeepsRetiredFields)` ([source](../../../../../../src/learnloop/config/schema.py), line 1551)
  - `_normalize_provider_profiles(cls, data: Any) -> Any` (line 1587; internal)
  - `_known_route_budgets(cls, value: dict[str, int]) -> dict[str, int]` (line 1594; internal)
  - `_merge_route_efforts(cls, value: Any) -> Any` (line 1603; internal)
  - `_known_route_efforts(cls, value: dict[str, str]) -> dict[str, str]` (line 1611; internal)
- `class ErrorImpact(KeepsRetiredFields)` ([source](../../../../../../src/learnloop/config/schema.py), line 1718) — Error impact settings.
- `class FsrsFittingConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1729) — `learnloop fit fsrs` knobs.
- `class FittingConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1740)
- `class EvidenceMassEntry(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1744) — Evidence carried by one attempt type.
- `default_attempt_type_evidence() -> dict[str, EvidenceMassEntry]` ([source](../../../../../../src/learnloop/config/schema.py), line 1759)
- `default_practice_mode_item_coverage() -> dict[str, float]` ([source](../../../../../../src/learnloop/config/schema.py), line 1781)
- `class EvidenceCorrelationConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1794) — Vault-wide surface-correlation discounting (free-form overrides).
- `class EvidenceCertificationConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1800) — Bounded certification credit.
- `class EvidenceBlueprintsConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1827) — Blueprint recipe likelihood defaults.
- `class EvidenceConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1838) — Single source of truth for per-attempt-type evidence carried.
  - `_merge_defaults(self) -> 'EvidenceConfig'` (line 1857; internal)
- `class CapabilitiesConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1867) — Capability damping/shrinkage + lazy residual activation.
- `class TraceEvidenceConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1896) — Opportunistic trace evidence and its elicitation budget.
- `class DiagnosticAugmentationConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1917) — Live diagnosis rungs.
- `class DiagnosisConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 1941) — The live blind grader + asynchronous history-aware diagnoser.
- `class RecurrenceBlockingCutoff(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2021) — One benchmark-set blocking cutoff and the vectors it was measured on.
  - `_a_cosine(self) -> 'RecurrenceBlockingCutoff'` (line 2040; internal)
- `class RecurrenceConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2047) — Recurrence groups with authority.
  - `_cutoffs_name_models(self) -> 'RecurrenceConfig'` (line 2094; internal)
- `class StuckPromptConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2101) — "Write what you can" replaces "I don't know".
- `class HintsMapsConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2115) — Adaptive hints: approach maps.
- `class HintsConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2147) — Adaptive hints.
- `class ReaderInquiryConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2239) — Reader workbench: inquiry.
- `class CuesConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2267) — Reader workbench: margin cues from the Guide.
- `class WorkbenchConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2322) — Reader workbench: the resumable scratchpad.
- `class RecapConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2387) — Reader workbench: "Last time here" and Wrap up.
- `class FollowupsConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2408) — Reader workbench: cold follow-ups, a "short unfamiliar problem" after reading.
- `class DigestConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2450) — Reader workbench: the session narrative and the router card's reader section.
- `class ReaderIntentConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2490) — Reader workbench: the intent box.
- `class ReaderActiveReadingConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2523) — Reader workbench: active reading.
- `class ReaderFormativeConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2541) — Reader workbench: missed answers as learner text.
- `class LibraryAskConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2556) — Reader workbench: ask your library.
- `class ReaderTutorConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2588) — Reader workbench: a tutor that looks things up.
- `class LibraryExercisesConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2626) — Reader workbench: exercises from my sources.
- `class FiguresPrefetchConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2651) — The guardrails of figures built ahead of need, each a fixed cap, never a learned number.
- `class FiguresConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2673) — Reader workbench: explorable figures.
- `class ReaderCompareConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2819) — Reader workbench: compare pinned passages.
- `class AsPrintedConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2872) — Reader: the problem as printed.
- `class PracticeConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2887) — The practice surfaces' own switches.
- `class RolesConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2930) — Reader workbench: instructional roles.
- `class ReadingPathsConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 2962) — Reader workbench: reading paths in the Guide.
- `class CurriculumConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3002) — Deliverable curriculum: section coverage and ``reader.correspondents``.
- `class NotesConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3070) — Deliverable curriculum: notes in the learner's voice, linked.
  - `_drop_legacy_tend(cls, data: Any) -> Any` (line 3114; internal)
- `class ReaderCorrespondenceConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3121) — Reader: *find this section in my other books* and *also in your books*.
- `class ReaderSideBySideConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3151) — Reader: *side by side*.
- `class ReaderConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3173) — The Reader's presentation switches.
- `class LearnerTextGapsConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3184) — Learner-text gaps.
- `class EvsiConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3246) — EVSI calibration.
- `class ProofCheckConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3267) — The valid-alternative gate for proofs and explanations, in the grader.
- `class RequiredMethodConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3285) — Method-explicit items: the grading side.
- `class ProjectConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3305) — Project understanding: delayed probes.
- `class FamiliesConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3346) — Offline family authoring only; live scheduling remains per card.
- `class PFScalingConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3353) — The scaling check's two configured tiers, as route lists.
- `class PFConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3365) — Practice families: generate, verify, select and publish.
- `class LocalEmbeddingConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3391) — Local contextual retrieval: the local pplx v2 9B document space.
- `class FallbackEmbeddingConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3419) — Local contextual retrieval: the hosted Voyage fallback space.
- `class SourceSpaceConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3439) — The source-space resolver and its fusion.
- `class EmbeddingConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3456)
  - `privacy_disclosure(self) -> str` (line 3484; public)
- `class GraphNominationConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3495) — Embedding nominations for ingest and graph review.
- `class FacetIdentityConfig(KeepsRetiredFields)` ([source](../../../../../../src/learnloop/config/schema.py), line 3518) — Facet identity at mint time, and the dedupe command.
- `class FieldConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3563) — Offline learner-field analysis only; activation requires a later algorithm successor.
- `class PracticeIndexConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3573) — The practice index: facet dossiers and ``find_practice``.
- `class SourceRetrievalConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3613) — Source retrieval.
- `class SourceServiceConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3690) — Canonical sources as a shared instructional service.
- `class PlacementConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3747) — Learner field: starting new material without ceremony.
- `class PlanConfig(KeepsRetiredFields)` ([source](../../../../../../src/learnloop/config/schema.py), line 3775) — Daily loop: the finite daily plan.
  - `_shares_leave_room(self) -> 'PlanConfig'` (line 3845; internal)
- `class IntentConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3865) — Daily loop: intent.
  - `_targets_are_probabilities(self) -> 'IntentConfig'` (line 3886; internal)
- `class CaptureConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3899) — Daily-loop capture settings.
- `class RouterWeights(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3909) — The model mixture's component weights (one third each).
  - `validate_total(self) -> 'RouterWeights'` (line 3921; public)
- `class RouterLessonSuggestionsConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3927) — Teacher: the router suggests a lesson, the learner opts in (``learnloop.daily_plan.lesson_suggestion``).
- `class RouterConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 3966) — Action router: decision logging, the staged frame and the model mixture.
  - `validate_floor(self) -> 'RouterConfig'` (line 4040; public)
- `class DataCaptureConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4046) — What later offline evaluation needs, recorded now.
- `class RouterObjectiveConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4064) — The router objective.
  - `_mins_leave_room(self) -> 'RouterObjectiveConfig'` (line 4294; internal)
- `class FollowupServeConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4307) — Follow-up generate and serve.
- `class VoiStoppingConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4326) — Four count caps lifted onto value of information.
- `class DeciderRoutesConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4381) — Tier 1: small judgments the Decider decides, the LLM its fallback.
- `class UiConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4424) — How the desktop app presents learner surfaces.
- `class TeacherWeightConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4449) — The lesson-check weight's switches: operational only.
- `class TeacherBriefConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4456) — What the lesson brief holds: the prerequisite depth (fixed) and the deliverable switch.
- `class TeacherContextConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4463) — The teacher's context budget: the goal's sections whole up to this many tokens (fixed).
- `class TeacherDelayedConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4469) — Delayed retention and transfer checks.
- `class TeacherPlacementConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4478) — ``max_probes`` (8, fixed): the generated probes one lesson may ask for: a burden guardrail; the teacher decides when to stop, this only bounds it.
- `class TeacherConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4485) — Teacher.
- `class EligibilityConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4565) — One serve/administration eligibility decision (``mvp-0.27``; ``learnloop.serve_eligibility``).
- `class ReplayConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4584) — How replay reads the attempt ledger (``mvp-0.34``, ``REPLAY_LEDGER_ALGORITHM_VERSION``).
- `class AskConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4599) — One Ask.
- `class AdaptiveDifficultyConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/schema.py), line 4631) — Adaptive difficulty.
  - `_ordered_band(cls, value: tuple[float, float]) -> tuple[float, float]` (line 4759; internal)
  - `_forecasters_switch(cls, value: Any) -> Any` (line 4767; internal)
  - `_canonical_forecasters(cls, value: list[str]) -> list[str]` (line 4777; internal)
- `class LearnLoopConfig(KeepsRetiredFields)` ([source](../../../../../../src/learnloop/config/schema.py), line 4782)
  - `_normalize_legacy_input(cls, data: Any) -> Any` (line 4870; internal) — Keep direct model validation compatible; implementation lives in compat.
  - `_ensure_effective_defaults(self) -> 'LearnLoopConfig'` (line 4878; internal)
- `default_codex_provider() -> CodexSDKProviderConfig` ([source](../../../../../../src/learnloop/config/schema.py), line 4967) — Return the modeled canonical Codex profile used when none is explicit.
- `default_chatgpt_plan_provider() -> ChatGPTPlanProviderConfig` ([source](../../../../../../src/learnloop/config/schema.py), line 4994) — The code-default ChatGPT-plan profile.
- `deepseek_flash_provider() -> AIProviderConfig` ([source](../../../../../../src/learnloop/config/schema.py), line 5007)
- `deepseek_pro_provider() -> AIProviderConfig` ([source](../../../../../../src/learnloop/config/schema.py), line 5019)
- `openrouter_haiku_provider() -> AIProviderConfig` ([source](../../../../../../src/learnloop/config/schema.py), line 5032) — Claude Haiku through OpenRouter, for cheap metered judges.
- `openrouter_provider() -> AIProviderConfig` ([source](../../../../../../src/learnloop/config/schema.py), line 5043)
- `openrouter_embedding_provider() -> AIProviderConfig` ([source](../../../../../../src/learnloop/config/schema.py), line 5054) — The template's embedding profile, for vaults whose config predates it.
- `openrouter_decider_provider() -> AIProviderConfig` ([source](../../../../../../src/learnloop/config/schema.py), line 5070) — The Perplexity Decider through OpenRouter.

### Module constants

- `_COMPAT_OPTIONAL_PROVIDER_FIELDS` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 941)
- `KNOWN_INPUT_MODALITIES` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 974)
- `VOYAGE_CONTEXTUAL_PROFILE_TYPE` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1083)
- `DECIDER_PROFILE_TYPE` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1103)
- `DEFAULT_DECIDER_PROVIDER` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1104)
- `DEFAULT_EMBEDDING_PROVIDER` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1105)
- `DEFAULT_DECIDER_MODEL` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1106)
- `DEFAULT_DECIDER_PRICE_PER_MILLION_INPUT` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1109)
- `CHATGPT_PLAN_PROFILE_TYPE` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1134)
- `CHATGPT_PLAN_API_BASE_URL` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1137)
- `RETIRED_ROUTES` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1213)
- `DEFAULT_OUTPUT_TOKENS` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1525)
- `REASONING_EFFORTS` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1527)
- `DEFAULT_ROUTE_REASONING_EFFORT` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1530)
- `DEFAULT_CODEX_MODEL` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1629)
- `DEFAULT_CODEX_REASONING_EFFORT` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1630)
- `LEGACY_CODEX_MODEL` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1631)
- `CODEX_LOW_PROVIDER` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1632)
- `CODEX_MEDIUM_PROVIDER` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1633)
- `CODEX_LUNA_PROVIDER` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1636)
- `CODEX_LUNA_MODEL` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1637)
- `CODEX_PROVIDER_NAMES` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1638)
- `OPENROUTER_HAIKU_PROVIDER` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1642)
- `OPENROUTER_HAIKU_MODEL` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1643)
- `OPENROUTER_TRANSCRIPTION_PROVIDER` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1644)
- `AGENT_HARNESS_PROFILE_TYPES` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1649)
- `CHATGPT_PLAN_PROVIDER` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1655)
- `CHATGPT_LOW_PROVIDER` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1656)
- `CHATGPT_MEDIUM_PROVIDER` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1657)
- `CHATGPT_LUNA_PROVIDER` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1658)
- `DEFAULT_CHATGPT_PLAN_MODEL` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1659)
- `CHATGPT_LUNA_MODEL` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1660)
- `CHATGPT_PLAN_PROVIDER_NAMES` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1661)
- `DEFAULT_SERVING_TASK_ROUTES` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1667)
- `LEGACY_CODEX_TASK_ROUTES` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1691)
- `CODEX_TO_PLAN_PROFILE` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 1710)
- `DEFAULT_RECALL_TARGETS` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 3856)
- `AD_OUTSIDE_FORECASTERS` ([src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py), line 4628)

## Internal implementation anchors

- `class _CodexProviderConfig(AIProviderConfig)` ([source](../../../../../../src/learnloop/config/schema.py), line 1024)
- `_require_known_routes(value: dict[str, Any], setting: str) -> None` ([source](../../../../../../src/learnloop/config/schema.py), line 1622)

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
- [[Reference/Modules/learnloop/config/compat|learnloop.config.compat]] — imports `AIProviderConfig`, `AudioIngestConfig`, `DEFAULT_CODEX_MODEL`, `DEFAULT_CODEX_REASONING_EFFORT`, `LEGACY_CODEX_MODEL`, `LEGACY_CODEX_TASK_ROUTES`, `OPENROUTER_TRANSCRIPTION_PROVIDER`, `openrouter_provider`; statically calls `AudioIngestConfig`, `openrouter_provider`
- [[Reference/Modules/learnloop/config/loader|learnloop.config.loader]] — imports `CODEX_LOW_PROVIDER`, `CODEX_LUNA_PROVIDER`, `CODEX_MEDIUM_PROVIDER`, `CodexHTTPProviderConfig`, `CodexSDKProviderConfig`, `LearnLoopConfig`
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
- [scripts/refactor_measures.py](../../../../../../scripts/refactor_measures.py)

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/compat|learnloop.config.compat]] — imports `discard_retired_provider_settings`, `normalize_ai_input`, `normalize_config_input`; calls `discard_retired_provider_settings`, `normalize_ai_input`, `normalize_config_input`
- [[Reference/Modules/learnloop/config/retired|learnloop.config.retired]] — imports `KeepsRetiredFields`, `remembering`; calls `remembering`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`, `urllib`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/backfill|learnloop.adaptive_difficulty.backfill]], [[Reference/Modules/learnloop/ai/agent_harness|learnloop.ai.agent_harness]], [[Reference/Modules/learnloop/ai/chatgpt_plan/routes|learnloop.ai.chatgpt_plan.routes]], [[Reference/Modules/learnloop/ai/native_media|learnloop.ai.native_media]], [[Reference/Modules/learnloop/ai/output_budget|learnloop.ai.output_budget]] and 31 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

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
- [tests/test_cold_retry_reschedule.py](../../../../../../tests/test_cold_retry_reschedule.py) — direct import
  - `test_mvp038_is_one_constant_after_mvp037`
- [tests/test_config_refactor.py](../../../../../../tests/test_config_refactor.py) — direct import
  - `test_config_responsibilities_have_canonical_module_owners`
  - `test_each_plan_tier_runs_its_codex_tiers_model_and_effort`
- [tests/test_curriculum_c1_plan_follows_path.py](../../../../../../tests/test_curriculum_c1_plan_follows_path.py) — direct import
  - `test_the_switch_is_on_by_default_classified_and_needs_the_curriculum_and_rw7b`
- [tests/test_curriculum_c3_exam_scoping.py](../../../../../../tests/test_curriculum_c3_exam_scoping.py) — direct import
  - `test_the_config_default_is_on`
- [tests/test_data_capture_successor.py](../../../../../../tests/test_data_capture_successor.py) — direct import
  - `test_the_switches_are_on_by_default_and_the_gate_reads_the_tag`
- [tests/test_decider_client.py](../../../../../../tests/test_decider_client.py) — direct import
  - `test_a_transport_error_echoing_a_key_reaches_neither_receipt_nor_caller`
  - `test_an_unreachable_endpoint_is_recorded_as_network_without_a_status`
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
  - `test_f5_every_tag_defaults_the_switch_off`
- [tests/test_diagnosis_input_provenance_landing.py](../../../../../../tests/test_diagnosis_input_provenance_landing.py) — direct import
  - `test_the_release_switch_defaults_off_and_the_default_source_is_the_narrow_rule`
- [tests/test_effective_defaults_golden.py](../../../../../../tests/test_effective_defaults_golden.py) — direct import
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
- [tests/test_figure_wait_successor.py](../../../../../../tests/test_figure_wait_successor.py) — direct import
  - `test_the_switch_defaults_on_and_is_classified`
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
- [tests/test_hypothesis_marks.py](../../../../../../tests/test_hypothesis_marks.py) — direct import
  - `test_the_switch_is_on_by_default_and_classified`
- [tests/test_ih2_lessons_compete.py](../../../../../../tests/test_ih2_lessons_compete.py) — direct import
  - `test_the_switch_defaults_on_is_classified_and_names_itself_in_the_prefetch_key`
- [tests/test_ih3_learner_preferences.py](../../../../../../tests/test_ih3_learner_preferences.py) — direct import
  - `test_the_switch_is_in_the_registry_and_the_default_is_on`
- [tests/test_ih4_preferences_inform_router.py](../../../../../../tests/test_ih4_preferences_inform_router.py) — direct import
  - `test_the_gate_reads_off_below_the_tag_switched_off_and_with_the_objective_off`
- [tests/test_ih5_successor.py](../../../../../../tests/test_ih5_successor.py) — direct import
  - `test_the_switch_defaults_on_and_is_classified`
- [tests/test_ih6_workbench_open_item.py](../../../../../../tests/test_ih6_workbench_open_item.py) — direct import
  - `test_the_switch_defaults_on_and_is_classified`
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
  - `test_the_successors_kill_switch_defaults_on_and_its_judge_route_is_unset`
- [tests/test_mvp013_upgrade.py](../../../../../../tests/test_mvp013_upgrade.py) — direct import
  - `test_the_successors_kill_switch_defaults_on`
- [tests/test_mvp014_upgrade.py](../../../../../../tests/test_mvp014_upgrade.py) — direct import
  - `test_the_plan_successors_defaults`
- [tests/test_mvp015_upgrade.py](../../../../../../tests/test_mvp015_upgrade.py) — direct import
  - `test_the_probe_tie_successors_switches_default_on`
- [tests/test_mvp016_upgrade.py](../../../../../../tests/test_mvp016_upgrade.py) — direct import
  - `test_the_learner_text_gap_successors_defaults`
- [tests/test_mvp017_upgrade.py](../../../../../../tests/test_mvp017_upgrade.py) — direct import
  - `test_the_route_check_successors_kill_switch_defaults_on`
- [tests/test_mvp020_upgrade.py](../../../../../../tests/test_mvp020_upgrade.py) — direct import
  - `test_the_route_rules_successors_kill_switch_stays_and_its_route_is_retired`
- [tests/test_mvp021_upgrade.py](../../../../../../tests/test_mvp021_upgrade.py) — direct import
  - `test_the_voi_stopping_successors_defaults`
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
  - `test_every_tag_defaults_the_switch_on`
- [tests/test_plan_first_transport.py](../../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_a_harness_profile_raises_before_any_process`
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
  - `test_every_tag_defaults_the_switch_on`
- [tests/test_rebuild_equivalence_review.py](../../../../../../tests/test_rebuild_equivalence_review.py) — direct import
  - `test_the_switch_is_on_by_default_and_classified`
- [tests/test_recurrence_benchmarks.py](../../../../../../tests/test_recurrence_benchmarks.py) — direct import
  - `test_b3_recommends_only_at_the_serving_width_with_its_provenance`
- [tests/test_recurrence_commands.py](../../../../../../tests/test_recurrence_commands.py) — direct import
  - `test_a_blocking_cutoff_must_be_a_cosine_and_name_what_it_was_measured_on`
  - `test_the_successor_sets_no_cosine_cutoff_by_default`
- [tests/test_retired_config_identities.py](../../../../../../tests/test_retired_config_identities.py) — direct import
  - `test_retired_fields_stay_off_the_models_and_out_of_every_other_dump`
  - `test_the_pre_arc_c_shape_reproduces_the_recorded_default_digest`
- [tests/test_ro0_row4_exposure_initiator.py](../../../../../../tests/test_ro0_row4_exposure_initiator.py) — direct import
- [tests/test_ro1_successor.py](../../../../../../tests/test_ro1_successor.py) — direct import
  - `test_the_factors_constants_stay_in_config`
- [tests/test_ro1_upgrade_report.py](../../../../../../tests/test_ro1_upgrade_report.py) — direct import
  - `test_the_shadow_rebuild_reports_the_upgrades_schedule_effects`
- [tests/test_ro4_goals.py](../../../../../../tests/test_ro4_goals.py) — direct import
  - `test_a_copy_made_at_creation_is_read_and_a_config_change_does_not_move_it`
  - `test_the_stated_default_for_a_goal_with_no_contract_and_no_copy`
- [tests/test_ro4_price.py](../../../../../../tests/test_ro4_price.py) — direct import
  - `test_the_runaway_guard_is_three_remembered_minutes_unless_set`
- [tests/test_ro4_successor.py](../../../../../../tests/test_ro4_successor.py) — direct import
  - `test_the_seeds_are_the_specs_and_validated`
- [tests/test_ro5_successor.py](../../../../../../tests/test_ro5_successor.py) — direct import
  - `test_the_seeds_are_the_specs_and_validated`
- [tests/test_ro6_successor.py](../../../../../../tests/test_ro6_successor.py) — direct import
  - `test_the_seeds_are_labelled_and_validated`
- [tests/test_rofu_successor.py](../../../../../../tests/test_rofu_successor.py) — direct import
  - `test_the_switches_default_on`
- [tests/test_rofu_switch_key.py](../../../../../../tests/test_rofu_switch_key.py) — direct import
  - `test_below_the_tag_the_key_names_no_switch`
- [tests/test_router_objective_migration.py](../../../../../../tests/test_router_objective_migration.py) — direct import
  - `test_the_switch_is_on_by_default_and_classified`
- [tests/test_router_offer_log.py](../../../../../../tests/test_router_offer_log.py) — direct import
- [tests/test_router_probe_ties.py](../../../../../../tests/test_router_probe_ties.py) — direct import
- [tests/test_sg_successor.py](../../../../../../tests/test_sg_successor.py) — direct import
  - `test_the_switches_default_on_and_are_classified`
- [tests/test_sidecar_contract.py](../../../../../../tests/test_sidecar_contract.py) — direct import
  - `test_sidecar_submit_attempt_never_falls_back_to_codex_when_routed_ai_unavailable`
- [tests/test_sketch_service.py](../../../../../../tests/test_sketch_service.py) — direct import
  - `test_the_shipped_default_is_on`
- [tests/test_source_retrieval_guards.py](../../../../../../tests/test_source_retrieval_guards.py) — direct import
  - `test_at_most_four_spans_reach_the_tutor`
- [tests/test_source_roles.py](../../../../../../tests/test_source_roles.py) — direct import
  - `test_every_roles_key_and_the_route_are_classified_as_operational_switches_and_bounds`
- [tests/test_t6_followup_review.py](../../../../../../tests/test_t6_followup_review.py) — direct import
  - `test_a_route_override_cannot_exceed_the_profile_maximum`
- [tests/test_te3a_successor.py](../../../../../../tests/test_te3a_successor.py) — direct import
  - `test_the_switch_defaults_on_and_is_classified`
- [tests/test_te3b_successor.py](../../../../../../tests/test_te3b_successor.py) — direct import
  - `test_the_switch_defaults_on_and_is_classified`
- [tests/test_teacher_te0_review_fixes.py](../../../../../../tests/test_teacher_te0_review_fixes.py) — direct import
  - `test_the_switch_is_on_by_default_and_registered`
- [tests/test_teacher_te1_review_fixes.py](../../../../../../tests/test_teacher_te1_review_fixes.py) — direct import
  - `test_f5_a_forecast_agreeing_with_the_cold_prediction_leaves_the_mass_near_the_learned_one`
- [tests/test_teacher_te1_successor.py](../../../../../../tests/test_teacher_te1_successor.py) — direct import
  - `test_no_openrouter_offer_for_a_lesson_until_its_price_is_set`
- [tests/test_teacher_te1_weight.py](../../../../../../tests/test_teacher_te1_weight.py) — direct import
  - `test_planted_recovery_a_check_whose_cold_outcomes_agree_raises_the_mass`
  - `test_the_pool_implied_mass_is_the_parametric_mass_at_lambda_zero`
- [tests/test_teacher_te2_successor.py](../../../../../../tests/test_teacher_te2_successor.py) — direct import
  - `test_the_switch_and_the_keep_bound_and_their_validation`
- [tests/test_teacher_te2log_episodes.py](../../../../../../tests/test_teacher_te2log_episodes.py) — direct import
  - `test_teacher_episode_log_is_classified_and_on_by_default`
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
- [tests/test_voi_v2.py](../../../../../../tests/test_voi_v2.py) — direct import
  - `test_the_study_switches_default_to_the_recommendation`
- [tests/test_voyage_fallback.py](../../../../../../tests/test_voyage_fallback.py) — direct import
  - `test_errors_never_carry_the_key_or_the_body`
- [tests/voi_restore_scenarios.py](../../../../../../tests/voi_restore_scenarios.py) — direct import
- [tests/voi_stopping_helpers.py](../../../../../../tests/voi_stopping_helpers.py) — direct import

## Modification guidance

- Change configuration behavior in the schema, loader, compatibility normalizer, or template owner that matches the concern; preserve one-way legacy normalization.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/config/schema.py](../../../../../../src/learnloop/config/schema.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
