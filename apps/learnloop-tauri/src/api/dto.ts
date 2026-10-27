export type IsoTimestamp = string;
export type Ulid = string;

export type AttemptType =
  | "independent_attempt"
  | "hinted_attempt"
  | "dont_know"
  | "diagnostic_probe"
  | "guided_walkthrough"
  | "reconstruction_after_walkthrough"
  | "skip"
  | "self_report"
  | "open_text"
  | "teach_back";

export type FsrsRating = "again" | "hard" | "good" | "easy";
export type GradingSource = "codex" | "ai" | "self";

export interface RuntimeHealth {
  version: number;
  codex: {
    ready: boolean;
    status: string;
    model: string | null;
    actualRevision: string | null;
    baseUrl: string;
    checkedAt: IsoTimestamp;
  };
  ai: {
    ready: boolean;
    status: string;
    activeProvider: string;
    providerType: string | null;
    model: string | null;
    providerRevision: string | null;
    checkedAt: IsoTimestamp;
    manualGrading?: boolean;
    gradingProviderOverride?: string | null;
    availableGradingProviders?: string[];
    // True when every provider the app routes to is configured with no missing
    // fields (keys/checkout). Drives the settings chip color independent of
    // which provider is nominally active. Absent on older sidecars.
    settingsReady?: boolean;
  };
  database: { ok: boolean; migrationsApplied: number; latestMigration: number };
  vaultLoaded: boolean;
}

export interface GradingProviderResult {
  activeProvider: string;
  manualGrading: boolean;
  ready: boolean;
  availableProviders: string[];
}

export interface SettingsProviderDto {
  name: string;
  type: string;
  model: string | null;
  baseUrl: string | null;
  apiKeyEnv: string | null;
  // Media modalities the profile declares it accepts natively ([ai.providers.*]
  // input_modalities). Config-declared, never probed: this is what ingestion trusts.
  inputModalities: string[];
}

export interface SettingsAiDto {
  activeProvider: string;
  fallbackProvider: string | null;
  routing: Record<string, string | null>;
  useCases: string[];
  providers: SettingsProviderDto[];
  envProviderOverride: string | null;
}

export interface OpenrouterKeyStateDto {
  keyPresent: boolean;
  keyHint: string | null;
  settingsEnvPath: string;
}

export interface KeyStateDto {
  keyPresent: boolean;
  keyHint: string | null;
}

// The five `[ingest.budgets]` ceilings the build plan charts and the Settings
// modal edits. Keys match the sidecar's camelized config field names.
export interface IngestBudgetsDto {
  inventoryInputTokens: number;
  inventoryOutputTokens: number;
  synthesisShardInputTokens: number;
  synthesisShardOutputTokens: number;
  synthesisTotalInputCeiling: number;
}

export type IngestBudgetField = keyof IngestBudgetsDto;

// Accepted range per ceiling, served by the backend so the UI validates with the
// same numbers the handler enforces.
export type IngestBudgetBoundsDto = Record<IngestBudgetField, { min: number; max: number }>;

// `[ingest.providers.<routed>]`. Null limits mean the block is absent, which
// silently disables the build plan's context-overflow checks.
export interface IngestProviderLimitsDto {
  provider: string;
  contextTokens: number | null;
  maxOutputTokens: number | null;
}

export type AudioMode = "transcription" | "native";

// The sidecar's per-modality readiness judgement (learnloop.ai.native_media):
// the same function the import pipeline uses, so the UI never claims a route
// the import would reject.
export interface NativeModalityStateDto {
  modality: string;
  requested: boolean;
  task: string;
  providerName: string | null;
  providerType: string | null;
  model: string | null;
  declared: boolean;
  ready: boolean;
  reason: string | null;
  message: string;
  maxMb: number;
}

export interface CatalogStateDto {
  cached: boolean;
  fetchedAt: string | null;
  stale: boolean;
  path: string;
}

export interface SettingsNativeIngestDto {
  modalities: NativeModalityStateDto[];
  fallbackWhenUnavailable: boolean;
  maxPdfMb: number;
  maxAudioMb: number;
  knownModalities: string[];
  catalog: CatalogStateDto;
}

export interface SettingsIngestDto {
  pdfEngine: PdfEngine;
  audioMode: AudioMode;
  native: SettingsNativeIngestDto;
  transcriptionProvider: string;
  transcriptionModel: string;
  transcriptionBaseUrl: string;
  transcriptionKey: KeyStateDto;
  /** GLM-OCR text recognition: the z.ai key and the backend that would run now. */
  textRecognition: TextRecognitionStateDto;
  budgets: IngestBudgetsDto;
  budgetBounds: IngestBudgetBoundsDto;
  providerLimits: IngestProviderLimitsDto;
}

// One judgment route (router spec §6.2): who would receive learner text and
// when. Read-only; the sidecar computes readiness from key presence only.
export interface SettingsJudgeRouteDto {
  route: string;
  judge: "decider" | "llm";
  consumer: "llm_probability" | "router";
  provider: string | null;
  providerType: string | null;
  model: string | null;
  ready: boolean;
  disclosure: string;
}

// One chatgpt_plan profile in the open vault and the routes that name it.
export interface ChatGPTPlanProfileDto {
  name: string;
  model: string | null;
  enabled: boolean;
  responseFormat: string | null;
  reasoningEffort: string | null;
  usageLimitPauseMinutes: number;
  routes: string[];
  activeProvider: boolean;
  fallbackProvider: boolean;
  inUse: boolean;
}

export type ChatGPTPlanState =
  | "ready"
  | "signed_out"
  | "plan_usage_disabled"
  | "not_eligible"
  | "usage_exhausted"
  | "store_error";

// The desktop sign-in attempt (one at a time; the sidecar runs it in the background).
export interface ChatGPTPlanAttemptDto {
  id: string;
  status: "waiting" | "succeeded" | "failed" | "cancelled";
  result: { email: string | null; planUsageEnabled: boolean; welcomePending: boolean } | null;
  error: { code: string; message: string } | null;
  startedAt: number;
  finishedAt: number | null;
}

// "Continue with ChatGPT": this machine's sign-in (local files only, never a
// token) and the open vault's chatgpt_plan profiles.
export interface ChatGPTPlanDto {
  version?: number;
  signedIn: boolean;
  planUsageEnabled: boolean;
  email: string | null;
  clientId: string | null;
  secretStore: string | null;
  accessExpiresAt: string | null;
  pausedUntil: string | null;
  welcomePending: boolean;
  signedOutReason: string | null;
  state: ChatGPTPlanState;
  message: string;
  manageUsageUrl: string;
  attempt: ChatGPTPlanAttemptDto | null;
  profiles: ChatGPTPlanProfileDto[];
  usingPlan: boolean;
  /** Tasks the learner's "Use OpenRouter instead" covers on this vault this session (re-review F3). */
  openrouterGrantedTasks?: string[];
  openrouterGrantedActions?: string[];
  authorizeUrl?: string;
  cancelled?: boolean;
  signout?: { signedOut: boolean; revoked: boolean | null; message: string };
}

export interface SettingsDto {
  version: number;
  ai: SettingsAiDto;
  openrouter: OpenrouterKeyStateDto;
  chatgptPlan?: ChatGPTPlanDto;
  embedding: {
    enabled: boolean;
    backfillEnabled: boolean;
    model: string;
    dimensions: number;
    /** Knowledge-map neighbours from stored item-text vectors (display only). */
    mapNeighborsEnabled: boolean;
    privacyDisclosure: string;
  };
  judges?: SettingsJudgeRouteDto[];
  ingest: SettingsIngestDto;
  animation: SettingsAnimationDto;
  health?: RuntimeHealth;
}

// `[animation]` render settings. Bounds are served by the backend so the UI
// validates with the same numbers the handler enforces.
export type AnimationRenderer = "manim" | "video_model";

// Readiness of the video-model renderer: a routed OpenRouter video profile
// with a model slug and a key. Computed by the sidecar without network.
export interface SettingsVideoDto {
  ready: boolean;
  provider: string | null;
  model: string | null;
  reason: string | null;
  maxShots: number;
  timeoutSeconds: number;
  resolution: string;
}

export interface SettingsAnimationDto {
  enabled: boolean;
  renderer: AnimationRenderer;
  rendererOptions: string[];
  video: SettingsVideoDto;
  quality: string;
  qualityOptions: string[];
  minDurationSeconds: number;
  maxDurationSeconds: number;
  timeoutSeconds: number;
  durationBounds: { min: number; max: number };
  timeoutBounds: { min: number; max: number };
}

export interface UpdateAnimationSettingsInput {
  renderer?: AnimationRenderer;
  videoMaxShots?: number;
  quality?: string;
  maxDurationSeconds?: number;
  timeoutSeconds?: number;
}

export interface UpdateIngestSettingsInput {
  pdfEngine?: PdfEngine;
  audioMode?: AudioMode;
  nativeFallbackWhenUnavailable?: boolean;
  nativeMaxPdfMb?: number;
  nativeMaxAudioMb?: number;
  transcriptionProvider?: string;
  transcriptionModel?: string;
  transcriptionBaseUrl?: string;
  // Omitted ceilings are left untouched, so a row can be applied on its own.
  budgets?: Partial<IngestBudgetsDto>;
  providerContextTokens?: number;
  providerMaxOutputTokens?: number;
}

export interface DetectProviderCapabilitiesInput {
  provider: string;
  refresh?: boolean;
}

export interface ProviderCapabilitiesDto {
  version: number;
  provider: string;
  providerType: string;
  model: string | null;
  declared: string[];
  // null when the model is not in the catalog (or the catalog was unavailable).
  detected: string[] | null;
  modelKnown: boolean;
  source: "network" | "cache" | "unavailable";
  fetchedAt: string | null;
  stale: boolean;
  message: string;
}

export interface UpdateProviderModalitiesInput {
  provider: string;
  inputModalities: string[];
}

export interface TextRecognitionStateDto {
  keyPresent: boolean;
  keyHint: string | null;
  envName: string;
  backend: "auto" | "api" | "local";
  selectedBackend: "api" | "local" | null;
}

export interface TextRecognitionKeyResult extends TextRecognitionStateDto {
  settingsEnvPath: string;
}

export interface TranscriptionKeyResult {
  keyPresent: boolean;
  keyHint: string | null;
  envName: string;
  settingsEnvPath: string;
}

export interface AnimationRuntimeDto {
  enabled: boolean;
  renderer: AnimationRenderer;
  videoProvider: string | null;
  videoModel: string | null;
  videoReady: boolean;
  videoReason: string | null;
  videoMaxShots: number;
  // null when the probe was skipped (the video renderer never runs manim).
  manimAvailable: boolean | null;
  manimVersion: string | null;
  manimReason: string | null;
  provider: string;
  model: string | null;
  timeoutSeconds: number;
}

// One storyboard shot as authored (prompt, requested length, on-screen caption).
export interface StoryboardShotDto {
  prompt: string;
  durationSeconds: number | null;
  caption: string;
}

export interface StoryboardDto {
  promptVersion?: string;
  shots: StoryboardShotDto[];
  jobs?: Array<{ jobId: string; status: string; cost: number | null }>;
  totalCost?: number;
}

export interface ConceptAnimationDto {
  animationId: string;
  renderer: AnimationRenderer;
  storyboard: StoryboardDto | null;
  videoJobIds: string[];
  conceptId: string;
  learningObjectId: string | null;
  status: string;
  title: string | null;
  narrationMd: string | null;
  videoFileName: string | null;
  durationSeconds: number | null;
  provider: string | null;
  model: string | null;
  failureStage: string | null;
  failureReason: string | null;
  createdAt?: string;
  completedAt?: string | null;
  // Failure-only debug payload.
  sceneCode?: string | null;
  renderStderr?: string | null;
}

export interface RequestConceptAnimationResult {
  animationId: string;
  conceptId: string;
  status: string;
  batchId: string;
}

export interface UseCaseChoiceInput {
  provider: string;
  openrouterModel?: string | null;
}

export interface UpdateAiSettingsInput {
  activeProvider?: string | null;
  useCases?: Record<string, UseCaseChoiceInput>;
}

export interface OpenrouterKeyResult {
  keyPresent: boolean;
  keyHint: string | null;
  settingsEnvPath: string;
  ready: boolean;
  status: string;
}

export interface FacetMasteryLearningObject {
  id: string;
  title: string;
  state: string;
  facetMastery: number;
}

export interface FacetMasteryPracticeItem {
  id: string;
  title: string;
  learningObjectId: string;
  weight: number | null;
  difficulty: number | null;
  isProbe: boolean;
  queued: boolean;
}

export interface FacetMasteryFacet {
  facetId: string;
  mastery: number;
  /** Mean per-LO diagnostic posterior entropy (nats) — the radar's variance band radius. */
  uncertainty: number;
  stateCounts: { solid: number; uncertain: number; knownGap: number; unexamined: number };
  learningObjects: FacetMasteryLearningObject[];
  practiceItems: FacetMasteryPracticeItem[];
  /** Total tutor Q&A question events classified onto this facet. */
  questionCount: number;
}

export interface FacetMasterySnapshot {
  facets: FacetMasteryFacet[];
  counts: { facets: number; learningObjects: number; practiceItems: number };
  // KM3 §9.6 re-key: mvp-0.7 keys facets by canonical (post-alias) id so a
  // shared parent folds across every LO that touches it; mvp-0.6 keeps the
  // legacy raw key. The UI branches on these (optional for stale sidecars).
  modelVersion?: string;
  canonicalKeys?: boolean;
}

export interface KnowledgeMapPoint {
  id: string;
  title: string;
  learningObjectId: string;
  conceptId: string | null;
  x: number;
  y: number;
  mastery: number | null;
  variance: number | null;
  predictedCorrect: number | null;
  isProbe: boolean;
  queued: boolean;
  difficulty: number | null;
  facets: string[];
  /**
   * Top-4 nearest items (never the lossy 2D embedding). `distance` is always the
   * blended facet/concept-graph distance; `similarity` is present only when
   * `neighborBasis` is "item_text" (mean-centred cosine of stored item-stem vectors).
   */
  neighbors: Array<{ id: string; distance: number; similarity?: number }>;
  /** Which ranking chose `neighbors` (Slice 2 T7, display only). */
  neighborBasis: KnowledgeNeighborBasis;
  /** Learner field F2: the item's LO is assumed known (not tested). A label only. */
  assumed?: boolean;
}

export type KnowledgeNeighborBasis = "item_text" | "facet_graph";

/** Coverage of the item-text neighbour ranking: stored vectors only, no calls. */
export interface KnowledgeItemTextNeighbors {
  /** `embedding.map_neighbors_enabled`; false keeps every item on facet/graph neighbours. */
  enabled: boolean;
  /** The model whose stored vectors rank the spokes (`embedding.model` when none is stored). */
  modelId: string;
  /** Items with a current stem that could be embedded (retired items excluded). */
  stems: number;
  /** Items whose current stem has a stored vector for `modelId`. */
  embedded: number;
  /**
   * `embedding.model` while its re-embed has not caught up with `modelId`: the
   * spokes move to it once it covers every stem `modelId` covers (Slice 2 §4).
   */
  pendingModel: { modelId: string; embedded: number } | null;
}

/** Learner field F2 (mvp-0.11): LOs assumed known (not tested), each checked
 *  in its first review. Empty while placement is off. */
export interface KnowledgeMapPlacement {
  active: boolean;
  assumed: Array<{ learningObjectId: string; source: AssumptionSource; firstReviewDue: IsoTimestamp }>;
  /** Learner-text gaps: prerequisites created from the learner's own text
   *  whose one check is pending (listed apart: never assumed known). */
  addedFromQuestion?: Array<{ learningObjectId: string; firstReviewDue: IsoTimestamp }>;
}

export type AssumptionSource = "self_report" | "fast_track" | "predictor" | "quick_check" | "learner_text_gap";

export interface KnowledgeMapSnapshot {
  version: number;
  points: KnowledgeMapPoint[];
  counts: { items: number; learningObjects: number; concepts: number; facets: number };
  /** Kruskal stress-1 of the 2D embedding — how approximate the map is. */
  stress: number;
  /** Facet-native diagnostic field; item points above remain for strata/history. */
  facetField: KnowledgeFacetField;
  itemTextNeighbors: KnowledgeItemTextNeighbors;
  placement?: KnowledgeMapPlacement;
}

export type CapabilityArcStatus = "demonstrated" | "required" | "absent";

export type KnowledgeFacetPoint = KnowledgeFacetPointBase & (
  | { untested: true; ready?: never; readyGhost?: never; readyVariance?: never }
  | { untested?: false; ready: number; readyGhost: number; readyVariance: number }
);

interface KnowledgeFacetPointBase {
  id: string;
  title: string;
  x: number;
  y: number;
  evidenceMass: number;
  demonstratedMass: number;
  requiredCapabilities: string[];
  demonstratedCapabilities: string[];
  hasBlueprints: boolean;
  capabilityArcs: Array<{ capability: string; status: CapabilityArcStatus }>;
  learningObjectIds: string[];
  /**
   * A repair on this facet's material was done with assistance and the single
   * unassisted check it scheduled has not been answered yet. Strictly separate
   * from `demonstratedMass` — instructed work is never demonstrated evidence,
   * and must never be counted as such in a marker, a legend or a summary.
   */
  coldCheckPending?: boolean;
  ambiguityCandidates: string[];
  ambiguityAttemptId: string | null;
  correction: { at: string; delta: number; attemptId: string } | null;
  /**
   * Learner field F2: an LO on this facet is "assumed known (not tested)". A
   * separate label, never folded into well depth or the demonstrated beads.
   */
  assumed?: boolean;
  assumedLearningObjectIds?: string[];
}

export interface KnowledgeFieldEdge {
  source: string;
  target: string;
  weight: number;
}

export interface KnowledgeNextGap {
  kind: "bottleneck_component" | "integration_gap" | "retrievability" | "unresolved_diagnostic";
  facetId: string;
  goalId: string;
  targetType: "facet" | "learning_object" | "attempt" | "probe_episode";
  targetId: string;
  label: string;
  pathFacetIds: string[];
}

export interface KnowledgeFacetField {
  points: KnowledgeFacetPoint[];
  graphNodes: string[];
  edges: KnowledgeFieldEdge[];
  layoutVersion: string;
  stress: number;
  layoutValid: boolean;
  layoutWarning: string | null;
  nextGap: KnowledgeNextGap | null;
}

export interface KnowledgeHistoryAttempt {
  id: string;
  /** ISO timestamp of the attempt. */
  t: string;
  practiceItemId: string;
  learningObjectId: string;
  attemptType: string;
  correctness: number | null;
  rubricScore: number | null;
  hintsUsed: number;
}

export interface KnowledgeHistorySeriesPoint {
  /** ISO timestamp of the mastery update (the attempt that caused it). */
  t: string;
  /** Display-space mastery mean after the update. */
  mastery: number;
}

/** Attempt events + per-LO mastery step series for the chronicle view. */
export interface KnowledgeMapHistory {
  version: number;
  attempts: KnowledgeHistoryAttempt[];
  learningObjects: Array<{ id: string; series: KnowledgeHistorySeriesPoint[] }>;
  range: { start: string; end: string } | null;
}

export interface VaultSummary {
  version: number;
  root: string;
  schemaVersion: number;
  algorithmVersion: string;
  /** Subject ids, the ones the learner practises most first (usability round 1, U10). */
  subjects: string[];
  /** Each subject's title, in the same order. Absent from older sidecars. */
  subjectTitles?: Array<{ id: string; title: string }>;
  counts: {
    learningObjects: number;
    practiceItems: number;
    concepts: number;
    goals: number;
    errorTypes: number;
    notes: number;
  };
  issueCount: number;
}

export interface StreakSummary {
  /** Consecutive days (local time) ending today, or yesterday if today is not yet practiced. */
  current: number;
  /** Whether a session has already been started today. */
  activeToday: boolean;
  /** Longest day streak ever recorded. */
  longest: number;
}

export interface AppSnapshot {
  version: number;
  vault: VaultSummary | null;
  config: unknown | null;
  health: RuntimeHealth;
  activeSession: SessionSnapshot | null;
  streak: StreakSummary;
}

export interface SessionStartInput {
  /** Accepted for old clients; Start no longer asks for or sends it (daily-loop DL0). */
  energy?: "low" | "medium" | "high" | null;
  /** Accepted for old clients; Start no longer asks for or sends it (daily-loop DL0). */
  sleepQuality?: number | null;
  availableMinutes?: number | null;
  notesMdPath?: string | null;
}

/** What Start shows before a session begins (daily-loop DL0, spec §6.6 and §8). */
export interface StartSummaryDto {
  version: number;
  /** The last session's minutes, or 25 on a vault with none (decision D1). */
  rememberedMinutes: number;
  minutesSource: "last_session" | "first_run";
  /** The one-tap chips: 10, 15, 25, 40, 60. */
  minutesPresets: number[];
  /** The presets plus the remembered value when it isn't one, ascending. */
  minuteChoices: number[];
  /** Read fresh: days with a started session, the count the badge labels. */
  streak: StreakSummary;
}

export interface SessionSnapshot {
  version: number;
  sessionId: Ulid;
  startedAt: IsoTimestamp;
  endedAt: IsoTimestamp | null;
  energy: string | null;
  sleepQuality: number | null;
  availableMinutes: number | null;
  notesMdPath: string | null;
  checkpoint: SessionCheckpoint | null;
}

export interface SessionEndSummary {
  version: number;
  sessionId: Ulid;
  startedAt: IsoTimestamp;
  endedAt: IsoTimestamp;
  attemptsRecorded: number;
  itemsReviewed: number;
  followupsQueued: number | null;
  /** Unassisted repair checks this session spent, and how many passed. Counted
   *  separately on purpose: "answered" and "confirmed" are different facts. */
  coldChecksCompleted?: number;
  coldChecksPassed?: number;
  streak: StreakSummary;
  facetsDemonstrated: number;
  predictionsMoved: { up: number; down: number };
  corrections: number;
  misconceptionsTouched: { resolved: number; returned: number };
  /** UX Phase 4: the topics the session practised, in the well's words
   *  (● on your own, ◌ with help); a topic only tried, missed, skipped or
   *  held is not named. Absent from an older sidecar. */
  topics?: SessionTopicDto[];
}

export interface SessionTopicDto {
  learningObjectId: string;
  title: string;
  evidence: "on_your_own" | "with_help";
}

export interface SessionCheckpoint {
  currentPracticeItemId: string | null;
  currentAnswer: string | null;
  hintsUsed: number;
  /** Stable retry key for the in-progress attempt. Reused after app restart so
   *  an outcome-unknown submission cannot be graded twice. */
  submissionId: string | null;
  /** mvp-0.13: the draft was being written after "I'm stuck" (absent from an
   *  older sidecar, which never stored one). */
  declaredStuck?: boolean;
  /** Router R2a (review F5): the daily-plan presentation the draft answers
   *  (absent from an older sidecar). */
  planPresentationId?: string | null;
  /** UX Phase 4 (Codex review F1): the trace a plain self-grade froze before
   *  it showed a full answer; the draft reopens locked to it. */
  selfGradeDisclosure?: SelfGradeDisclosureDto | null;
  /** Adaptive difficulty AD1 (§11.2): the draft's first-hint progress marker,
   *  present only when one was kept under this retry key. */
  firstHintProgress?: FirstHintProgress | null;
  /** AD1 fix round 5 (V4): a hint of any kind was seen on this draft;
   *  present (true) only when one was, under this retry key. */
  hintSeen?: boolean;
  /** Reader CA1 (Q12): the original page was opened before Submit on this
   *  draft (it counts as the book); present only when it was. */
  pageSeen?: boolean;
  focusBlockState: Record<string, unknown> | null;
  pendingGradingProposal: unknown | null;
  readiness: Record<string, unknown> | null;
  updatedAt: IsoTimestamp;
  /** Mid-conversation teach-back state, when the checkpoint holds one. */
  teachBack?: TeachBackStateDto | null;
}

/** The whole trace a plain self-grade froze before showing a full answer. */
export interface SelfGradeDisclosureDto {
  submissionId: string;
  answerMd: string;
  explanationMd: string | null;
}

export interface QueueInput {
  sessionId?: string | null;
  availableMinutes?: number | null;
  energy?: string | null;
  limit?: number | null;
}

export interface SchedulerComponents {
  forgettingRisk: number;
  goalFrontier?: number;
  recentError: number;
  probeEig: number;
  /** Display-only: Fisher information of one ordinary attempt about the LO
   * mastery latent (a²·p·(1−p) × default evidence mass). Never a priority
   * input — practice selection optimizes learning, not measurement. */
  practiceInformation?: number;
  negativeSurpriseFollowup?: number;
  interventionFollowup?: number;
}

export interface ScheduledItemDto {
  schedulerSlateId?: string | null;
  schedulerCandidateId?: string | null;
  practiceItemId: string;
  learningObjectId: string;
  learningObjectTitle: string;
  subject: string | null;
  practiceMode: string;
  selectedMode: string;
  priority: number;
  components: SchedulerComponents;
  readinessFactor: number | null;
  plainEnglish: string[];
  dominantReason: string;
  mastery: number | null;
  masteryVariance: number | null;
  dueAt: IsoTimestamp | null;
  dueStatus: "due" | "later" | "probe" | "followup";
  isProbe: boolean;
  isFollowup: boolean;
  /** Which follow-up lane inserted this row. A `certification_cold_probe` is a
   *  held-out validity check on an already-certified skill, NOT a repair retry —
   *  narrating the two the same way misrepresents what the item is for.
   *  Null when `isFollowup` is false. */
  followupKind: FollowupKind | null;
}

export type FollowupKind =
  | "certification_cold_probe"
  | "cold_retry"
  | "intervention_followup"
  | "negative_surprise_followup";

export interface QueueSection {
  title: string;
  items: ScheduledItemDto[];
}

/** A cold check the scheduler is withholding because its answer was shown after
 *  it was scheduled. Not a queue item — it was removed before ranking — so it
 *  is reported as waiting, never offered. */
export interface DeferredColdCheckDto {
  followupTaskId: string;
  kind: FollowupKind;
  practiceItemId: string | null;
  learningObjectId: string | null;
  learningObjectTitle: string | null;
  /** When the check becomes available again (last reveal + the cold delay). */
  deferredTo: IsoTimestamp;
  lastRevealAt: IsoTimestamp;
}

export interface QueueSnapshot {
  version: number;
  generatedAt: IsoTimestamp;
  sessionId: string | null;
  sections: QueueSection[];
  totalItems: number;
  deferredColdChecks?: DeferredColdCheckDto[];
  /** Set while the welcome-back panel shows: the re-entry session is capped at
   *  this many items (owner decision P6). Null/absent: no re-entry cap. */
  reentryRefresherCap?: number | null;
}

/** Knowledge-model §5.1: what a rubric criterion actually observes. `role`
 *  compiles deterministically into certification credit (primary 1.0,
 *  supporting 0.3) — it is an allocation rule, not a claim of causal certainty. */
export interface CriterionTargetDto {
  facet: string;
  capability: string;
  role: "primary" | "supporting";
}

export interface RubricCriterionDto {
  id: string;
  points: number;
  description: string;
  tier?: "core" | "transfer";
  /** A1's authored observation contract. The backend has always serialized the
   *  whole criterion model; these were missing from the type, which made an
   *  item's authored measurement claims inspectable only by reading YAML. */
  targets?: CriterionTargetDto[];
  dependsOn?: string[];
  correlationGroup?: string | null;
  recipeIds?: string[];
  measurementStatus?:
    | "direct"
    | "supporting"
    | "composite"
    | "item_local"
    | "no_canonical_facet"
    | null;
}

export interface RubricFatalErrorDto {
  id: string;
  description: string;
  maxGrade: number;
}

export interface RubricDto {
  maxPoints: number;
  criteria: RubricCriterionDto[];
  fatalErrors: RubricFatalErrorDto[];
}

// Error taxonomy offered by the self-grade form when a criterion is below full
// credit. `relevant` flags types tied to the item's concept (sorted first).
export interface CandidateErrorTypeDto {
  id: string;
  title: string;
  isMisconception: boolean;
  severityDefault: number;
  relevant: boolean;
}

// Meas §3.A6 — whether this serve offers the optional one-line justification,
// and (when it does not) which of the four "we did not ask" arms applies. Null
// when the item was opened without a session: a read-only open is not a serve,
// so no decision was made rather than a negative one being fabricated.
export interface ElicitationDecisionDto {
  elicit: boolean;
  reason:
    | "answer_underdetermines_reasoning"
    | "self_documenting_trace"
    | "capability_shows_its_work"
    | "session_budget_exhausted"
    | "disabled";
  prompt: string | null;
}

// ── Meas §3.A2/§3.A3 item presentation ──────────────────────────────────────
// What the learner must SEE to answer an item, as one ordered structure shared
// by every serving surface. Before this, `prompt` was the only thing a surface
// carried, so an error hunt was served with no worked solution to repair and a
// laddered-stem part with no stimulus to climb — a silent failure, because the
// grader DID receive the material and marked every miss against the learner.
//
// Render `blocks` in order and in full. Do not switch on `kind` to decide
// whether to show a block: an unknown kind is a stimulus this build has not
// heard of, and dropping it reproduces exactly the defect this type exists to
// close. `kind` is for labelling and styling only.
export type PresentationBlockKind =
  | "prompt"
  // Method-explicit items: "Use {method} in your answer.", rendered from the
  // item's required method after the statement (never stored in it).
  | "required_method_instruction"
  | "error_hunt_worked_solution"
  | "laddered_stem_stimulus";

export interface PresentationBlockDto {
  kind: PresentationBlockKind | string;
  markdown: string;
  /** Caption above the block, or null for the prompt (which needs no chrome). */
  label: string | null;
  /** Present on `laddered_stem_stimulus`: the stem whose parts share this text. */
  stemId?: string;
}

export interface ItemPresentationDto {
  practiceItemId: string;
  blocks: PresentationBlockDto[];
}

export interface PracticeItemDetail {
  version: number;
  /** Learner field F2: "I know this" is offered only while placement is on. */
  placementActive?: boolean;
  id: string;
  learningObjectId: string;
  learningObjectTitle: string;
  subject: string | null;
  subjects: string[];
  practiceMode: string;
  attemptTypesAllowed: AttemptType[];
  teachBackSource: {
    sourcePracticeItemId: string;
    sourceUpdatedAt: string;
    compilerVersion: string;
    questId: string | null;
    questSentence: string | null;
    questBasis: "explicit_intent" | "exam_goal" | "practice_goal" | "legacy_title" | "provided" | null;
    questConnection: "connected" | "not_relevant" | "no_quest";
    authoringMode: "ai" | "deterministic_fallback";
  } | null;
  evidenceFacets: string[];
  evidenceWeights: Record<string, number>;
  /** The question text alone. Fine for previews and controls; anything asking
   *  the learner to ANSWER must render `presentation` instead. */
  prompt: string;
  presentation: ItemPresentationDto;
  expectedAnswer: string | Record<string, unknown>;
  difficulty: number | null;
  hints: string[];
  hintPolicy: {
    maxUsefulHints: number;
    fsrsRatingCapByHint: Record<string, string>;
    masteryAlphaDampeningByHint: Record<string, number>;
  };
  rubric: RubricDto | null;
  candidateErrorTypes: CandidateErrorTypeDto[];
  tags: string[];
  sourceRefs: SourceRefDto[];
  state: PracticeItemStateDto | null;
  mastery: MasteryDto | null;
  scheduler: SchedulerExplanationDto | null;
  attempts: AttemptHistoryRowDto[];
  assessmentContractVersionId: string | null;
  elicitation: ElicitationDecisionDto | null;
  /** The delayed follow-up lane this item is currently serving, if any
   *  ("cold_retry" | "certification_cold_probe" | ...). Cold lanes reject
   *  hinted/primed attempts, so the practice surface warns near the hint
   *  button. Optional: older sidecars omit it. */
  activeFollowupKind?: string | null;
  /** Canonical sources S1: a textbook exercise's provenance and its key's
   *  honest label (absent for every other item). */
  canonicalExercise?: CanonicalExerciseDto;
  /** Daily-loop DL2: present only when this session serve is a due "Check
   *  once" (a check on your own; Reader §9.3 item 10). */
  intentCheck?: IntentCheckDto;
}

// ── Daily-loop DL2: intent (spec_daily_loop_v1.md §5) ─────────────────────────

export type IntentScopeKind = "learning_object" | "practice_item" | "subject" | "source";
export type IntentChoice =
  | "master"
  | "learn"
  | "keep"
  | "light_touch"
  | "check_once"
  | "reference"
  | "pause"
  | "let_go";

/** One choice of the control, previewed by the resolution serving uses. */
export interface IntentChoicePreviewDto {
  choice: IntentChoice;
  label: string;
  /** What the choice does, in plain words. */
  does: string;
  /** "Pause 12 topics · replaces your earlier setting on 2 topics and 1 item". */
  consequence: string;
  replacedTopics: number;
  replacedItems: number;
  /** Projected review minutes a day (§6.4 estimates at §5.3 targets); null when unknown. */
  costMinutesPerDay: number | null;
  /** "about N min/day of reviews", "no reviews", "one check, about N min". */
  costLabel: string;
  servedCount: number;
  excludedCount: number;
}

export interface IntentCurrentDto {
  choice: IntentChoice | "uncommitted";
  label: string;
  /** Where the setting comes from ("this control", a broader setting, a request); null uncommitted. */
  source: string | null;
  deadline: { goalId: string; dueAt: string } | null;
  canAddDeadline: boolean;
}

export interface IntentViewDto {
  version?: number;
  enabled: boolean;
  available?: boolean;
  reason?: string;
  scope?: { kind: IntentScopeKind; id: string };
  title?: string;
  topics?: number;
  items?: number;
  current?: IntentCurrentDto;
  choices?: IntentChoicePreviewDto[];
  applied?: { choice: IntentChoice; commitmentId: string; created: boolean };
  deadlineSet?: { goalId: string; dueAt: string; created: boolean; commitmentId: string };
}

/** The way back after a check (Reader §9.3 item 9); only when the provenance carries it. */
export interface IntentRestorationDto {
  label: string;
  detail: string | null;
  inquiryRootEventIds: string[];
  anchorSpanIds: string[];
  extractionId: string | null;
  sourceId: string | null;
}

/** A served (or answered) "Check once". */
/** LP-min (a), LPQ9: "You marked this as known; this check: missed." */
export interface ClaimCheckDto {
  claim: "marked_known";
  check: "passed" | "missed";
  line: string;
}

export interface IntentCheckDto {
  kind: "check_once";
  commitmentId: string;
  dueSince?: string;
  /** "after_practice": dated again after an attempt that was not on your own. */
  dateSource?: "due_hint" | "test_me_later_days" | "after_practice";
  /**
   * Served cold now (the one eligibility decision). False: the item's answer
   * was seen, so this is practice, labelled so, and the check comes back later.
   */
  cold?: boolean;
  /** The cold banner, or the practice label when not cold. */
  banner?: string;
  /** The help ladder's header during a cold check (D42); absent when not cold. */
  helpHeader?: string;
  /** D46: nothing that locates the exercise is shown until feedback. */
  locatorsHidden?: boolean;
  /**
   * DL2 fix round 4 (F15): the item is also measured under a stricter duty
   * (a cold follow-up, an active diagnostic). The server then sends the
   * measured banner and no help header: the duty's own safeguards apply.
   */
  duty?: "cold_followup" | "diagnostic";
  restoration: IntentRestorationDto | null;
}

// ── Meas §3.A6 opportunistic trace evidence ─────────────────────────────────
// `reward` is the sentence the feedback surface says when a volunteered
// explanation demonstrated facets beyond the item's declared set — the visible
// half of "voluntary and visibly rewarded". Null, never zero, when it did not.
export interface TraceExercisedFacetDto {
  facetId: string;
  observationScope: "declared" | "opportunistic" | string;
  criterionId: string | null;
  evidence: string;
  source: string | null;
}

export interface AttemptTraceEvidenceDto {
  version: number;
  attemptId: string;
  observations: TraceExercisedFacetDto[];
  reward: string | null;
}

// ── Meas §3.A8 clarification channel ────────────────────────────────────────
// One question per attempt, asked only when the grade was hedged or abstained.
// While it is pending the attempt carries manual_review_reason
// `provisional_pending_clarification`: the grade is not final.
export interface GradingClarificationDto {
  id: string;
  attemptId: string;
  criterionId: string | null;
  reason:
    | "ambiguous_notation"
    | "skipped_step"
    | "correct_answer_possibly_invalid_reasoning"
    | "method_ambiguity"
    | "other";
  trigger: "hedged_criterion" | "abstained_attribution" | "low_grader_confidence";
  questionMd: string;
  expiresAt: IsoTimestamp;
  createdAt: IsoTimestamp;
  answerMd: string | null;
  answeredAt: IsoTimestamp | null;
  outcome: ClarificationOutcome | null;
  status: "pending" | "answered" | "timed_out";
}

export interface GradingClarificationResultDto {
  version: number;
  clarification: GradingClarificationDto | null;
}

/** `abstained` is first-class: the learner answered and the grader still could
 *  not name a cause. Null means the answer is recorded but no re-grade ran. */
export type ClarificationOutcome = "resolved" | "abstained" | "regrade_failed";

export interface AnswerGradingClarificationResultDto {
  version: number;
  clarificationId: string | null;
  outcome: ClarificationOutcome | null;
  regraded: boolean;
  /** Why the grade did not move, when it did not (provider outage, failed
   *  re-grade). The answer itself is persisted regardless. */
  error: string | null;
  feedback: FeedbackBundle;
}

export interface AttemptHistoryRowDto {
  id: string;
  createdAt: IsoTimestamp;
  attemptType: AttemptType | string;
  rubricScore: number | null;
  maxPoints: number;
  correctness: number | null;
  hintsUsed: number;
  errorType: string | null;
  surpriseDirection: string | null;
}

export interface SourceRefDto {
  refType: string;
  /** Human-facing ingest identity (original filename or captured video title). */
  displayName: string;
  refId: string;
  path: string | null;
  locator: string | null;
  quote: string | null;
}

export interface PracticeItemStateDto {
  difficulty: number | null;
  stability: number | null;
  retrievability: number | null;
  dueAt: IsoTimestamp | null;
  lastAttemptAt: IsoTimestamp | null;
  active: boolean;
}

export interface MasteryDto {
  mean: number;
  variance: number;
  plausibleLower?: number;
  plausibleUpper?: number;
  plausibleMass?: number;
  evidenceCount: number;
  lastEvidenceAt: IsoTimestamp | null;
}

/** One multiplicative term in the observation weight. */
export interface MasteryStepFactorDto {
  key: string;
  label: string;
  detail: string;
  multiplier: number;
}

/**
 * Why the posterior moved as far as it did. The EKF step is governed by the
 * observation weight; `factors` are the terms that produced it, in application
 * order, and their product is `observationWeight`.
 */
export interface MasteryStepDto {
  observationWeight: number;
  factors: MasteryStepFactorDto[];
  expectedCorrectness: number | null;
  observedCorrectness: number | null;
  /** Factor that cost the most weight — emphasised in the strip. */
  dominantFactorKey: string | null;
  /** Weight is at the noise floor; shrinking it further stops shrinking the step. */
  atWeightFloor: boolean;
  /** False when the payload predates a scoring change — chain is partial. */
  productReconciles: boolean;
}

export interface SchedulerExplanationDto {
  version: number;
  practiceItemId: string;
  selectedMode: string;
  priority: number;
  components: SchedulerComponents;
  readinessFactor: number | null;
  expectedInformationGain: number;
  plainEnglish: string[];
}

// One learner-attributed error tied to a specific rubric criterion. Mirrors a
// Codex error_attribution once resolved server-side.
export interface SelfGradeErrorAttributionDto {
  errorType: string;
  criterionId?: string | null;
}

export interface SelfGradeInputDto {
  criterionPoints: Record<string, number>;
  confidence: number;
  fatalErrors?: string[] | null;
  errorType?: string | null;
  notes?: string | null;
  errorAttributions?: SelfGradeErrorAttributionDto[] | null;
}

export interface SubmitAttemptInput {
  sessionId: string;
  practiceItemId: string;
  /** The answer, and nothing but the answer. */
  answerMd: string;
  /** Meas §3.A6: the volunteered one-line justification, as its own field. The
   *  sidecar joins it to the answer into the single trace the grader reads —
   *  the client neither knows nor reproduces the heading that delimits it, so
   *  there is no constant to keep synchronized across the language boundary.
   *  Blank/omitted is submitted as nothing at all: not a decline, not a skip. */
  explanationMd?: string | null;
  attemptType: AttemptType;
  hintsUsed: number;
  /** RW2b fix round 5: the answer box's authored reveals alone (the server
   *  adds a counted book and the workbench's help itself, each once). */
  authoredHints?: number | null;
  /** RW2b fix round 12: the count holds a book the answer box carried (its own component). */
  bookCounted?: boolean | null;
  latencySeconds?: number | null;
  selfGrade?: SelfGradeInputDto | null;
  /** Retry launched from the feedback screen's source-review panel. */
  primed?: boolean;
  /** Probe redesign §5.1: the committed presentation this submission consumes. */
  probePresentationId?: string | null;
  /** Probe redesign §7.1: learner answer confidence (1–5), logged-only. */
  answerConfidence?: number | null;
  /** Immutable grading contract captured when this item was opened. */
  assessmentContractVersionId?: string | null;
  /** Stable identity reused when a network submission is retried. */
  submissionId?: string | null;
  schedulerCandidateId?: string | null;
  /** Router R2a: the daily-plan presentation this answer is to (the plan
   *  step's `presentationId`). A wrong or used one never fails the submit. */
  planPresentationId?: string | null;
  /** mvp-0.13: written after "I'm stuck" ("Write what you can, or what's
   *  confusing you"). May be empty. Still an ordinary attempt of
   *  `attemptType`: graded when it has text, scored 0 at once when empty. */
  declaredStuck?: boolean;
  /** Adaptive difficulty AD1 (§12): the optional "Felt" tap, sent only when
   *  tapped (logged only; stored with `adaptive_difficulty.rating_tap` on). */
  difficultyRating?: DifficultyRating | null;
  /** AD1 (§11.2): whether an answer had been started at the first hint. */
  firstHintProgress?: FirstHintProgress | null;
}

/** Adaptive difficulty AD1's optional rating tap (spec §12). */
export type DifficultyRating = "easy" | "about_right" | "hard";
/** AD1's first-hint progress marker (spec §5.3, §11.2): the tutor-question marker at the first hint. */
export type FirstHintProgress = "no_draft" | "draft_started";

/** §5.7 block-end hook payload: withheld feedback released at the boundary,
 *  the completion/open-set outcome, and where the learner routes next. */
export interface ProbeBlockEndDto {
  episodeId: string;
  status: string;
  releasedFeedback: {
    attemptId: string;
    practiceItemId: string | null;
    rubricScore: number | null;
    maxPoints: number;
    feedbackMd: string | null;
    fatalErrors: string[];
    /** Carries `commonRepair` exactly like the FeedbackScreen bundle (G3):
     *  the block-end hook resumes the deferred repair consultation and the
     *  released payload reads the recorded decision receipt. */
    causalFeedback?: CausalFeedbackDto | null;
    /** Server truth for "redo the part you missed" — same rule
     *  `start_guided_redo` enforces (the SELECTED repair preserves a prefix). */
    guidedRedoAvailable?: boolean;
    /** UX Phase 4: the grade is held for review (THE held predicate); its
     *  score is the grader's provisional one and is never shown. */
    heldForReview?: boolean;
  }[];
  normalizedMisconceptionIds: string[];
  openSet: Record<string, unknown> | null;
  completionReason: string | null;
  firstErrorStepOrClaim: string | null;
  route: "tutoring" | "next_block" | "ordinary_practice" | null;
  decision: Record<string, unknown> | null;
}

/** Probe measurement contract for an item under an active diagnostic episode (§12). */
export interface ProbeContractDto {
  version: number;
  active: boolean;
  reason?: string;
  presentationId?: string;
  episodeId?: string;
  observationNumber?: number;
  maximumObservations?: number;
  /** mvp-0.21: the check asks while the next question is worth its minutes, not up to a count. */
  valueStopping?: boolean;
  forcedAttemptType?: AttemptType;
  restrictions?: {
    hintsDisabled: boolean;
    askTutorDisabled: boolean;
    workedExampleDisabled: boolean;
    answerRevealDisabled: boolean;
    feedbackDeferred: boolean;
  };
  capabilitySummary?: string;
  feedbackNote?: string;
  actions?: { stopAndTeach: boolean; leaveAndResume: boolean };
  /** DL2 fix round 4 (F15): a due "Check once" served as this probe, in its measured view. */
  intentCheck?: IntentCheckDto;
}

export interface StopProbeResultDto {
  version: number;
  stopped: boolean;
  decision: Record<string, unknown> | null;
}

/** §5.7 block continuity: the item that would continue this LO's open episode,
 *  if any — a read-only peek, never commits a presentation. */
export interface GetNextProbeItemDto {
  version: number;
  active: boolean;
  practiceItemId?: string;
}

/** A source ref resolved to displayable content for the source-review panel. */
export interface ResolvedSourceRefDto {
  refType: string;
  /** canonical_source note kind (youtube_video | website_page | ...) or "note". */
  kind: string | null;
  /** Human-facing ingest identity (original filename or captured video title). */
  title: string;
  externalUrl: string | null;
  /** Vault path of the backing note, for the "View in Library" jump. */
  notePath: string | null;
  locator: string | null;
  locatorResolved: boolean;
  /** The source changed since this item was extracted (or the locator dangled). */
  sourceChanged: boolean;
  headingPath: string[] | null;
  /** Resolved section text (or transcript excerpt window; quote on fallback). */
  sectionMd: string | null;
  video: {
    videoId: string;
    startSeconds: number;
    endSeconds: number | null;
  } | null;
}

export interface AttemptResultDto {
  version: number;
  attemptId: string;
  practiceItemId: string;
  learningObjectId: string;
  rubricScore: number;
  correctness: number;
  graderConfidence: number;
  manualReviewReason: string | null;
  fsrsRating: FsrsRating;
  dueAt: IsoTimestamp;
  masteryMean: number;
  masteryVariance: number;
  surpriseDirection: string;
  predictiveSurprise: number;
  bayesianSurprise: number;
  errorEventIds: string[];
  gradingSource: GradingSource;
  fallbackReason: string | null;
  agentRunId: string | null;
  /** Present when the item's LO has an open diagnostic episode (§5.6):
   *  feedback stays deferred while the episode is still measuring. */
  probeEpisode?: { episodeId: string; status: string; feedbackDeferred: boolean } | null;
  /** Present when this submission closed a diagnostic block (§5.7). */
  probeBlockEnd?: ProbeBlockEndDto | null;
  /** Slice 1 §11: present when the attempt queued an asynchronous diagnosis
   *  (blind-graded vaults); poll `diagnosisStatus` while it is "pending". */
  diagnosisStatus?: DiagnosisStatusValue;
}

/** Slice 1 M2 (§11): where an attempt's asynchronous diagnosis stands. */
export type DiagnosisStatusValue = "pending" | "not_needed" | "done" | "failed";

/** The card's one optional tap (§12.2), in its fixed neutral order. */
export type DiagnosisCardResponse =
  | "believed_candidate"
  | "partly"
  | "slipped"
  | "diagnosis_wrong"
  | "unsure";

export interface DiagnosisCitationDto {
  attemptId: string;
  practiceItemId: string | null;
  date: IsoTimestamp | null;
  quote: string | null;
  rubricScore: number | null;
  correctness: number | null;
}

export interface DiagnosisPrerequisiteGapDto {
  prerequisiteRef: string;
  title: string;
  suggestedCheckMd: string | null;
  /** Always "possible cause - not yet checked". */
  label: string;
}

/** Slice 2 T1 §3.7: the escalated repair's one-tap usefulness rating. */
export type EscalationResponse = "escalation:helped" | "escalation:didnt_help" | "escalation:not_sure";

export interface EscalationAnswerDto {
  attemptId: string;
  practiceItemId: string | null;
  date: IsoTimestamp | null;
  rubricScore: number | null;
  correctness: number | null;
}

/** Shown when the diagnosis's cause has recurred K times (mvp-0.12): the
 *  repair with the earlier answers as its evidence. The headline claims a
 *  different approach only when the repair's operator really differs. */
export interface DiagnosisEscalationDto {
  escalationId: string;
  headline: string;
  recurrenceCount: number;
  differentApproach: boolean;
  /** Set when the repair is the same kind as before (honest label). */
  approachNote: string | null;
  repair: RepairSuggestionDto | null;
  earlierAnswers: EscalationAnswerDto[];
  responses: { response: EscalationResponse; label: string }[];
  recordedResponse: EscalationResponse | null;
}

/** `diagnosis_status`: the status, and the card's content once done. */
export interface DiagnosisCardDto {
  version: number;
  attemptId: string;
  status: DiagnosisStatusValue;
  cardEnabled: boolean;
  responses: { response: DiagnosisCardResponse; label: string }[];
  diagnosisId?: string | null;
  createdAt?: IsoTimestamp | null;
  historyMode?: string | null;
  summaryMd?: string;
  repairSuggestions?: RepairSuggestionDto[];
  /** Validated citations only (S4); empty when none validated. */
  madeBefore?: DiagnosisCitationDto[];
  prerequisiteGap?: DiagnosisPrerequisiteGapDto | null;
  /** Slice 2 T1: present only on an escalated recurrence. */
  escalation?: DiagnosisEscalationDto | null;
  recordedResponse?: DiagnosisCardResponse | null;
  notSameMistakeAttemptIds?: string[];
}

export interface DiagnosisFeedbackResultDto {
  version: number;
  feedbackId: string;
  forwardedFactorId: string | null;
  forwarding: string;
}

export interface PracticeSubmissionRecoveryDto {
  version: number;
  status: "pending" | "recovered";
  result: AttemptResultDto | null;
}

export interface PracticeSubmissionAcknowledgementDto {
  version: number;
  status: "cleared" | "already_absent" | "checkpoint_mismatch";
  acknowledged: boolean;
}

export interface FeedbackBundle {
  version: number;
  attemptId: string;
  /** Daily-loop DL2: present only when this attempt answered a "Check once". */
  intentCheck?: IntentCheckDto;
  /** LP-min (a), LPQ9: present only on the review that resolved a topic the
   *  learner marked as known. One quiet line; never a score or a label. */
  claimCheck?: ClaimCheckDto;
  /** Slice 1 §11: present when the attempt queued an asynchronous diagnosis. */
  diagnosisStatus?: DiagnosisStatusValue;
  practiceItemId: string;
  learningObjectId: string;
  learningObjectTitle: string;
  rubricScore: number;
  maxPoints: number;
  correctness: number;
  graderConfidence: number;
  gradingSource: GradingSource;
  fallbackReason: string | null;
  manualReviewReason: string | null;
  fsrsRating: FsrsRating;
  nextDueAt: IsoTimestamp;
  criterionEvidence: CriterionEvidenceRowDto[];
  fatalErrors: string[];
  errorAttributions: ErrorEventDto[];
  surprise: AttemptSurpriseDto;
  masteryBefore: MasteryDto | null;
  masteryAfter: MasteryDto | null;
  /** Observation-weight breakdown behind the posterior shift; null pre-trace. */
  masteryStep: MasteryStepDto | null;
  feedbackMd: string | null;
  repairSuggestions: RepairSuggestionDto[];
  /** Server truth for the "redo the part you missed" button: computed with the
   * same rule start_guided_redo enforces (the SELECTED repair preserves a
   * prefix), so a visible button cannot fail with guided_redo_unavailable. */
  guidedRedoAvailable: boolean;
  interventionNeed: InterventionNeedDto | null;
  /** This attempt was itself a primed retry. */
  primed: boolean;
  /** `primed` was FORCED by the reveal ledger rather than chosen: tutor answers
   *  or repair displays had already covered part of the solution before this
   *  attempt. `autoPrimedRevealTotal` is the summed reveal fraction behind it —
   *  absent, never zero, when the ledger did not force it. */
  autoPrimed?: boolean;
  autoPrimedRevealTotal?: number | null;
  /** Non-null only when this attempt CONSUMED a cold check — the single
   *  unassisted measurement an earlier assisted repair scheduled. Announced
   *  after the grade; nothing about it is shown before the attempt. */
  coldCheckResult?: ColdCheckResultDto | null;
  /** Canonical-source sections that spawned this item (source-review panel). */
  sourceRefs: ResolvedSourceRefDto[];
  followupQueued: boolean;
  // Non-null when this attempt is itself a follow-up (drives the rating strip).
  followupSource?: FollowupSourceDto | null;
  followupRating?: FollowupRatingDto | null;
  /** Tutor questions that counted as hints on this attempt. */
  questionHintEquivalents?: number;
  /** KM3 §9.6 unresolved-cause factors: ambiguous localized failures whose
   * candidate causes imply different repairs (drives the diagnostic card). */
  unresolvedCauses?: UnresolvedCauseDto[];
  matchedMisconception?: MatchedMisconceptionDto | null;
  /** P1 receipt-checked overlay. Every diagnostic statement is typed as
   * verified, uncertain, unverified, or a proposed action before display. */
  causalFeedback?: CausalFeedbackDto | null;
  /** Persisted §2.1 regrade ledger fact: present when this attempt's grading
   * history carries a regrade (a grading epoch after the original), so the
   * RegradeLedgerCard renders on a fresh load, not only after an in-screen
   * trigger_regrade. Null/absent when the attempt was never regraded. */
  regrade?: PersistedRegradeDto | null;
  /** UX Phase 4 (display only): the grade is held for review (THE held
   *  predicate, `learnloop.held_grades`): the surface says "held for review"
   *  and never shows its score. Absent from an older sidecar. */
  heldForReview?: boolean;
  /** The learner's own answer and volunteered line, apart (feedback shows
   *  "You wrote" beside a full answer). */
  learnerAnswerMd?: string;
  learnerExplanationMd?: string | null;
  /** The question as it was given when it differs from the item's own
   *  presentation (a method-explicit answer's frozen statement and rendered
   *  instruction, or the frozen statement of an item edited since); null
   *  otherwise. */
  answeredPresentation?: ItemPresentationDto | null;
  /** Codex review F5, re-review F9, round 3 F9: the answer key, criteria and
   *  maximum the grade stands on, sent directly. `answeredSource` says where
   *  they come from: the assessment contract its grading epoch cites (exact),
   *  "live" (only in the response of a regrade that has just run: what it
   *  read), or "unrecorded": nothing recorded says which version it read, so
   *  there is no key or criteria, and a maximum only when one was recorded
   *  with the grade. Absent from an older sidecar (feedback then reads the
   *  item, re-read after a regrade). The criteria are rows carrying their id
   *  (re-review F8: a map keyed by id had its keys camel-cased). */
  answeredSource?: "contract" | "live" | "unrecorded";
  answeredExpectedAnswer?: unknown;
  answeredCriteria?: { criterionId: string; description: string; pointsPossible: number }[] | null;
  answeredMaxPoints?: number | null;
  /** "I think I was right" (Codex review F3/F7): present on a contest's
   *  response. `recorded`: the learner's note is kept; `regraded`: the grader
   *  looked again; `reviewRequested`: the grade went to the owner's review. */
  contest?: { recorded: boolean; regraded: boolean; reviewRequested: boolean };
}

/** What the cold check this attempt spent turned out to say.
 *
 *  `passed` and `claim` are deliberately separate. `passed` is whether the
 *  unassisted answer was right; `claim` is what the system is licensed to
 *  conclude, which a downgraded receipt can withhold even from a correct
 *  answer. Rendering only one of them would let assistance buy a confirmation.
 */
export interface ColdCheckResultDto {
  passed: boolean;
  /** Recorded cold outcome (`cold_success`, `cold_failure`,
   *  `right_censored_expired`, `contaminated_or_assisted`, …). */
  outcome: string | null;
  claim: "repair_confirmed" | "escalated_unrepaired" | "downgraded" | "unmeasured";
  claimDowngradedReason: string | null;
  caseKind: string | null;
  caseRef: string | null;
  /** Human-readable name for what was under repair. */
  caseSummary: string;
  factorId: string | null;
  episodeId: string | null;
  /** The day the assisted repair happened, and the day this check answered. */
  instructedAt: IsoTimestamp | null;
  checkedAt: IsoTimestamp | null;
  revealSpend?: number | null;
  revealBudget?: number | null;
}

export interface CausalFeedbackDto {
  receiptId: string;
  verifiedCorrection: {
    label: string;
    rationale: string | null;
    verificationStatus: "verified";
    verificationScope: string;
  } | null;
  causalHypotheses: {
    hypothesisId: string;
    label: string;
    statement: string;
    causeScope: string;
    supportScore: number | null;
    supportAuthority?: string | null;
    traceConsistency?: CausalTraceConsistencyState;
  }[];
  unverified: {
    kind: string;
    hypothesisId?: string;
    /** Null when the receipt marks a claim unverified without supplying prose. */
    statement: string | null;
  }[];
  proposedNextAction: {
    label: string;
    operator: string | null;
    rationale: string | null;
    repairClassId: string | null;
  } | null;
  demonstratedCriteria: {
    criterionId: string;
    criterionLabel: string | null;
    pointsAwarded: number;
    pointsPossible: number;
  }[];
  firstDivergence: CausalDivergenceAnchorDto | null;
  protectedTargets: { target: string | null; reason: string }[];
  contestAction: {
    available: boolean;
    reasons: UnresolvedCauseSelfReportResponse[];
    factorId?: string | null;
  };
  repairedTrace: RepairedTraceDto | null;
  repairedTraceWithheldReason: string | null;
  permittedUses: string[];
  traceConsistency?: Record<string, CausalTraceConsistencyState>;
  probeNeed?: CausalProbeNeedDto | null;
  /** Journey B: the post-attempt orchestrator consultation found that every
   * plausible cause shares one repair (`skip_common_repair` /
   * `skip_action_equivalent`), read off the recorded decision receipt —
   * rendering this never re-decides. Absent for divergent or
   * incomplete-mapping factors, which keep the learner-initiated
   * `causal_repair_status` flow. */
  commonRepair?: {
    status: string;
    decision: string;
    reason: string;
    message: string;
    misconceptionId: string;
    factorId: string;
    decisionReceiptId: string;
  } | null;
  decisionPolicyVersion?: string | null;
}

export interface CausalTargetRefDto {
  kind: string;
  facetId?: string | null;
  capability?: string | null;
  criterionId?: string | null;
  recipeId?: string | null;
  checkpointId?: string | null;
  quote?: string | null;
  charStart?: number | null;
  charEnd?: number | null;
}

export interface CausalDivergenceAnchorDto {
  anchorKind?: string | null;
  criterionId?: string | null;
  checkpointId?: string | null;
  quote?: string | null;
  normalizedQuote?: string | null;
  charStart?: number | null;
  charEnd?: number | null;
  [key: string]: unknown;
}

export interface RepairedTraceDto {
  learnerWorkPrefix?: string | null;
  repairInsertionPoint?: CausalDivergenceAnchorDto | null;
  minimalEdit?: string | null;
  regeneratedWork?: string | null;
  repairedAnswerMd?: string | null;
  changedLatentClaims?: string[];
  changedCheckpointIds?: string[];
}

export interface CausalRepairClassDto {
  id: string;
  equivalenceScope?: string;
  episodeId?: string;
  repairPolicyVersion?: string;
  operator: string;
  targetRefs: CausalTargetRefDto[];
  preserveRefs: CausalTargetRefDto[];
  expectedMinutes: number | null;
  answerRevealBudget: number;
}

export interface CausalHypothesisDto {
  id: string;
  episodeKey: string;
  version: number;
  supersedesId: string | null;
  attemptId: string;
  errorEventId: string | null;
  learningObjectId: string;
  causeScope: string;
  statement: string;
  statementNormalized: string;
  mechanism: string | null;
  operation: string | null;
  targetRef: CausalTargetRefDto | null;
  applicability: Record<string, unknown> | null;
  postdictiveClaims: Record<string, unknown>[];
  evidence: Record<string, unknown> | null;
  repairClassId: string | null;
  status: string;
  generationAgentRunId: string | null;
  model: string | null;
  createdAt: IsoTimestamp;
}

export interface CausalMinimalityDto {
  preservedSpans: string[];
  preservedCriteria: string[];
  changedLatentClaims: string[];
  changedTraceSteps: string[];
  traceEditCost: number | null;
  latentChangeCost: number;
  checkpointChangeCost: number;
  backtrackingDepth?: number | null;
  estimatedMinutes: number | null;
  divergenceAnchors?: Record<string, CausalDivergenceAnchorDto | null>;
  textDiff?: { before: string; after: string } | null;
}

export interface DiagnosisReceiptDto {
  id: string;
  schemaVersion: number;
  attemptId: string;
  criterionOutcomes: {
    criterionId: string;
    pointsAwarded: number;
    pointsPossible: number;
    assessable: boolean;
    passed: boolean;
    fullCredit: boolean;
  }[];
  divergenceAnchors: {
    firstObservableDivergence: CausalDivergenceAnchorDto | null;
    earliestSupportedFaultyCommitment: CausalDivergenceAnchorDto | null;
    repairInsertionPoint: CausalDivergenceAnchorDto | null;
    observableDivergenceCandidates?: CausalDivergenceAnchorDto[];
    anchorDisagreement?: boolean;
  };
  attributionAxes: {
    hypothesisId: string;
    version: number;
    causeScope: string;
    resolutionStatus: string | null;
    targetRef: CausalTargetRefDto | null;
  }[];
  validTargets: CausalTargetRefDto[];
  hypotheses: {
    id: string;
    version: number;
    status: string;
    repairClassId: string | null;
  }[];
  supportScores: Record<string, number | null>;
  modelReportedSupportProposals?: Record<string, number | null>;
  supportAuthority?: string;
  plausibleSet: string[];
  ordinalRanking: string[];
  repairClasses: CausalRepairClassDto[];
  repairClassRanking: string[];
  repairSelection: {
    selected: {
      repairClass: CausalRepairClassDto;
      suggestion: RepairSuggestionDto;
      minimality: CausalMinimalityDto;
    } | null;
    rejected: { repairClassId: string; reasons: string[] }[];
    ranking: string[];
  };
  commonRepairCover: {
    coversPlausibleSet: boolean;
    repairClassId: string | null;
    matrix?: {
      hypothesisId: string;
      repairClassId: string | null;
      targetRef: CausalTargetRefDto | null;
      covered: boolean;
      basis: string;
    }[];
  };
  /** P2 §1.3: what a probe would have to resolve. The decision verbs moved to
   * the probe-coherence service; the receipt states a need, not a decision. */
  probeNeed?: CausalProbeNeedDto;
  /** @deprecated schema 2 alias of probeNeed; `decision` reads "see probe_need"
   * on schema 3 receipts. */
  probeDecision: { decision: string; reason: string };
  /** P2 §1.1: per-hypothesis trace-consistency state, keyed by hypothesis id.
   * Only "consistent_with_claims" is positive evidence. */
  traceConsistency?: Record<string, CausalTraceConsistencyState>;
  traceConsistencyDetail?: {
    policyVersion: string;
    rubricAvailable: boolean;
    unattributedPostdictiveClaims: {
      errorEventId: string;
      claim: Record<string, unknown>;
      reason: string;
    }[];
    byHypothesis: Record<
      string,
      {
        state: CausalTraceConsistencyState;
        reason: string;
        claimsAttributed: number;
        claimsChecked: number;
        claimsUnverifiable?: number;
        contradictedCriterionIds: string[];
      }
    >;
  };
  /** @deprecated receipt-level alias; cannot name the contradicted hypothesis. */
  traceConsistent?: boolean;
  decisionPolicyVersion?: string;
  unmappedHypothesisIds?: string[];
  permittedUses: string[];
  mechanismTaxonomyVersionId?: string | null;
  mechanismTaxonomyHash?: string | null;
  /** Legacy receipt field retained only so old vaults remain inspectable. */
  mechanismTaxonomy?: Record<string, unknown>;
  contaminationStatus?: string | null;
  createdAt: IsoTimestamp;
}

export type CausalTraceConsistencyState =
  | "contradicted"
  | "consistent_with_claims"
  | "no_deterministic_claims"
  | "unknown";

export interface CausalProbeNeedDto {
  divergent: boolean;
  repairClassIds: string[];
  commonRepairCover: boolean;
  incompleteRepairMapping: boolean;
  reason: string;
  /** Present when derived from a schema 2 receipt's decision verbs. */
  legacySchema?: boolean;
}

// ── P2 causal repair orchestration (spec_causal_attribution_v1 §6) ───────────
// The typed union `causal_orchestrator.causal_repair_status` returns. It
// replaces the old raw RemediationError path, whose only learner-visible form
// was an `invalid_request` toast reading "unrelated remediation is blocked …" —
// semantically wrong copy for a hold on the *branch-specific* repair inside one
// divergent causal factor.

export type CausalRepairStatusState =
  | "started"
  | "needs_disambiguation"
  | "deferred_machine_checks"
  | "safe_common_repair_available"
  | "blocked_pending_review";

/** Action ids the orchestrator offers. The backend is authoritative about
 *  *which* are offered: after "Not now" the state stays `needs_disambiguation`
 *  with `probeOffered: false` and only `teach_me_now` comes back. */
export type CausalRepairActionId = "take_quick_check" | "teach_me_now" | "not_now";

export interface CausalRepairActionDto {
  id: CausalRepairActionId;
  label: string;
}

export interface CausalRepairStatusDto {
  status: CausalRepairStatusState;
  /** Machine-readable hold reason (e.g. "divergent_repair_classes",
   *  "incomplete_repair_mapping", "unreviewed_probe_candidate"). */
  reason: string;
  /** Learner-facing copy authored in the orchestrator (§6). Render this. */
  message: string;
  misconceptionId: string;
  factorId: string | null;
  learningObjectId: string | null;
  attemptId: string | null;
  /** False once the learner has deferred: the causes still diverge, only the
   *  offer is withdrawn. Never re-offer the quick check on false. */
  probeOffered: boolean;
  probeDecision: string | null;
  probeDecisionReason: string | null;
  decisionReceiptId: string | null;
  candidateId: string | null;
  blindBundleIds: string[];
  hypothesisSetId: string | null;
  repairClassIds: string[];
  commonRepairClassId: string | null;
  pendingMachineCheckIds: string[];
  learnerPreference: string;
  actions: CausalRepairActionDto[];
  episode: RemediationEpisodeDto | null;
  /** Resolved fitted-parameter manifests (orchestrator + probe policy). */
  parameters: Record<string, unknown>;
  /** Standing constraint 4: per-EVSI-input provenance —
   *  "deterministic" | "model_reported" | "heuristic_default". */
  evsiProvenance: Record<string, string>;
  /** How much of the answer this repair episode has already handed over, on the
   *  reveal ledger's 0..1 fraction-of-answer scale, against the budget it is
   *  measured against. Null when the status carries no episode. Reported, never
   *  enforced: nothing is refused on budget. */
  revealSpend?: number | null;
  revealBudget?: number | null;
  decisionPolicyVersion?: string | null;
  formulaVersion?: string | null;
}

export interface CausalRepairStatusResultDto {
  version: number;
  repairStatus: CausalRepairStatusDto;
}

/** Result of "Take the quick check": a factor-aware probe episode with the
 *  candidate and its blind bundles pinned into the presentation. */
export interface CausalProbeOfferDto {
  accepted: boolean;
  reason: string;
  factorId: string;
  episodeId: string | null;
  presentationId: string | null;
  practiceItemId: string | null;
  candidateId: string | null;
  hypothesisSetId: string | null;
  blindBundleIds: string[];
}

export interface CausalProbeOfferResultDto {
  version: number;
  offer: CausalProbeOfferDto;
}

export interface CausalProbePreferenceDto {
  id: string;
  scope: string;
  scopeRef: string;
  sessionId: string | null;
  preference: string;
  source: string;
  expiresAt: IsoTimestamp | null;
  detail: Record<string, unknown> | null;
  createdAt: IsoTimestamp;
}

export interface CausalProbeDeferResultDto {
  version: number;
  preference: CausalProbePreferenceDto;
}

export interface CausalEpisodeDto {
  attemptId: string;
  receipt: DiagnosisReceiptDto | null;
  hypotheses: CausalHypothesisDto[];
  /** Normalized across receipt schema versions; legacy receipts read
   * "unknown" for every hypothesis rather than inheriting an unattributable
   * verdict. */
  traceConsistency?: Record<string, CausalTraceConsistencyState>;
  probeNeed?: CausalProbeNeedDto | null;
  decisionPolicyVersion?: string | null;
}

export interface PersistedRegradeDto {
  oldScore: number;
  newScore: number;
  maxPoints: number;
  regradedAt: IsoTimestamp;
  direction: "up" | "down" | "same";
  /** Codex review F6: the grade the regrade replaced was held for review (its
   *  score was provisional and is never shown). Absent from an older sidecar. */
  oldHeld?: boolean;
  /** UX Phase 4 (final verification F9, round 3): each side's own maximum,
   *  the one its grade stands on (its contract's, a live regrade's, or one
   *  recorded with the grade); null when none is known. `maxPoints` stays the
   *  item's (classic shows it). Absent from an older sidecar. */
  oldMaxPoints?: number | null;
  newMaxPoints?: number | null;
}

export interface MatchedMisconceptionDto {
  id: string;
  statement: string;
  correctionStatement: string;
  mechanism: string | null;
  targetFacet: string | null;
  confusedWithFacet: string | null;
  status: string;
}

export interface UnresolvedCauseDto {
  id: string;
  observationId: string | null;
  candidateCauses: {
    statement?: string | null;
    causeScope?: string | null;
    targetRef?: {
      kind: string;
      facetId?: string | null;
      capability?: string | null;
      criterionId?: string | null;
    } | null;
    facet?: string | null;
    capability?: string | null;
    hypothesisId?: string | null;
    openSet?: boolean;
  }[];
  selfReportQuestion?: {
    prompt: string;
    options: { id: UnresolvedCauseSelfReportResponse; label: string }[];
  } | null;
  selfReport?: {
    id: string;
    response: UnresolvedCauseSelfReportResponse;
    candidateIndex: number | null;
    createdAt: IsoTimestamp;
  } | null;
}

export type UnresolvedCauseSelfReportResponse =
  | "slipped"
  | "believed_candidate"
  | "item_unclear"
  | "notation_confused"
  | "other_valid_approach"
  | "diagnosis_wrong";

/**
 * Result of `submit_eliciting_response`: the learner's unaided answer to an
 * eliciting repair's question, recorded as a factor-response engagement signal.
 *
 * It is not a grade. `admissibleAsIndependent` is false when the item's answer
 * was revealed before the response was written — the response is still on the
 * record, it just cannot be read as independent evidence.
 */
export interface ElicitingResponseResultDto {
  reportId: string;
  factorId: string;
  attemptId: string;
  suggestionIndex: number;
  observationId: string;
  admissibleAsIndependent: boolean;
  inadmissibilityReason: string | null;
  feedback: FeedbackBundle;
}

export interface UnresolvedCauseSelfReportResultDto {
  factorId: string;
  response: UnresolvedCauseSelfReportResponse;
  resolved: boolean;
  provisionalBeliefId: string | null;
  observationId: string;
}

/** Result of start_primed_retry: a sibling item to retry with primed=true. */
export interface PrimedRetryResultDto {
  available: boolean;
  /** The item was generated on demand (LLM authoring) rather than pre-existing. */
  generated: boolean;
  reason?: string | null;
  practiceItem: PracticeItemDetail | null;
}

/** Result of start_guided_redo (Fix 3): redo ONLY the failed part of an
 *  attempt. `learnerWorkPrefix` is the server-recomposed preserved work,
 *  rendered read-only above the editor; the learner writes just the redo
 *  portion and the composed answer is submitted primed on the SAME item.
 *  Composition is always prefix + rewrite (end-append): the repaired-trace
 *  schema can only preserve a prefix, so there is never trailing learner text
 *  to splice the rewrite into. */
export interface GuidedRedoDto {
  version: number;
  attemptId: string;
  practiceItemId: string;
  prompt: string;
  learnerWorkPrefix: string;
  /** The repair op's rationale — what went wrong and what to fix. */
  redoInstruction: string | null;
  failedCheckpointIds: string[];
  repairClassId: string | null;
  /** The remediation episode this redo was bound to as the primed attempt —
   *  an already-open one for the diagnosed case, or one the server established
   *  through the repair entry. Null when the repair is held/blocked, in which
   *  case the redo is a plain primed attempt (no cold retry). */
  episodeId: string | null;
  coldItemId: string | null;
  /** Why no cold retry could be scheduled despite a bound episode:
   *  "no_independent_surface" | "case_unresolvable". */
  coldUnmeasurableReason: string | null;
  practiceItem: PracticeItemDetail;
}

// ── Tutor Q&A ("ask") ──────────────────────────────────────────────────────

export type TutorQuestionContext = "library" | "practice" | "feedback" | "reader";

/** Practice context: had the learner started an answer when they asked?
 *  Persisted as question_events.attempt_progress; "no_draft" is the explicit
 *  "help before any work" signal the learner field reads (spec §3.1). */
export type AttemptProgress = "no_draft" | "draft_started";

export interface AskTutorQuestionInput {
  captureId?: string;
  subjectId?: string;
  context: TutorQuestionContext;
  question: string;
  practiceItemId?: string;
  attemptId?: string;
  noteId?: string;
  sessionId?: string;
  secondsIntoAttempt?: number;
  attemptProgress?: AttemptProgress;
  /** Canonical sources S4, "Explain this with my work": passages the learner
   *  chose ("<extraction>:<span>") and their current draft. */
  pinnedSpanKeys?: string[];
  learnerDraftMd?: string;
  /** Reader CA2 (ask.panel_enabled, K5/K7): the attempt's key (the thread is
   *  the attempt's), the workbench session a Work-in-Steps question comes
   *  from (checked against the item on the server), the step it is about,
   *  and a one-question answer mode (absent: the help style's). */
  submissionId?: string;
  workbenchSessionId?: string;
  aboutStep?: number;
  answerMode?: AnswerMode;
}

/** Reader CA2 (§7.4): the help style is Ask's answer mode, one vocabulary. */
export type AnswerMode = "ask_me_first" | "help_me_reason" | "answer_directly";

/** ING M8 (§9.2): one source-span citation on a tutor answer; the chip opens
 *  the Open-in-source viewer (context "tutor_citation"). Validated server-side
 *  against provided spans — never model-invented. */
export interface TutorCitationDto {
  extractionId: string;
  spanId: string;
  label: string | null;
  /** RW1c: a retrieved passage's source, so the Reader can open it there. */
  sourceId?: string | null;
  /** Reader CA2 (K11, Codex review F9): the cited passage's own text, as the
   *  tutor was given it (practice and feedback, the Ask panel on). */
  excerpt?: string;
}

export interface TutorAnswerDto {
  noteId?: string | null;
  version: number;
  eventId: string;
  answerMd: string;
  questionType: string;
  facets: string[];
  hintEquivalent: boolean;
  leakSuspected: boolean;
  citations: TutorCitationDto[];
  /** Null: no request bound (a subscription route, Codex review F8). */
  remaining: number | null;
  /** Learner-text gaps: the question is read for a named gap off the request
   *  path ("queued"); the overlay polls getLearnerTextGap for the result. */
  learnerGap?: LearnerGapQueuedDto;
  /** Canonical sources S0: a deterministic "Practice this" request, run once
   *  the answer is on screen (null when the offer is off or the tutor wrote
   *  its own find_practice request). */
  practiceRequest?: PracticeRequestDto | null;
  /** Canonical sources S4: the tutor's typed tool requests, validated
   *  server-side (answer-leak checked, unknown ids dropped). */
  toolRequests?: SourceToolRequestDto[];
  /** Reader CA2 (§7.4): the mode the answer was written in; null when the
   *  panel is off (today's answer). */
  answerMode?: AnswerMode | null;
  /** Codex review F2 (K9): the answer was worked help, withheld; the ladder's
   *  take step (rungs 4 and 5) instead. */
  takeOffer?: { levels: number[]; reason: string } | null;
}

export interface LearnerGapQueuedDto {
  status: "queued" | "off" | "failed";
  kind?: string | null;
}

/** The learner's one-tap reversals of what a gap reading did. */
export type LearnerTextGapReversal = "undo_edge" | "undo_creation" | "not_this_belief";

/** What one learner text was read as, and what was done (honest labels only:
 *  `label` is null when nothing the learner should see happened). */
export interface LearnerTextGapViewDto {
  gapId: string;
  kind: string;
  action: string;
  named: { prerequisiteName?: string | null; prerequisiteLine?: string | null; beliefStatement?: string | null };
  target: { kind: string | null; id: string | null; title: string | null } | null;
  edgeId: string | null;
  seedPracticeItemId: string | null;
  seedStatus: string | null;
  label: string | null;
  reversals: string[];
  allowedReversals: LearnerTextGapReversal[];
  edge?: string | null;
}

export interface LearnerTextGapStatusDto {
  version: number;
  status: "pending" | "done" | "off" | "none" | "skipped";
  gap: LearnerTextGapViewDto | null;
}

export interface LearnerTextGapReversalDto {
  version: number;
  status: string;
  gap: LearnerTextGapViewDto | null;
}

// ── Canonical sources (spec_source_practice_and_probes_v1) ─────────────────

export interface PracticeCallerDto {
  kind: string;
  ref?: string | null;
}

export interface PracticeRequestDto {
  request: {
    query: string;
    learningObjectIds: string[];
    facetIds: string[];
    excludeItemIds: string[];
    intent: string;
    kinds?: string;
  };
  caller: PracticeCallerDto;
  version: string;
}

export interface SourceToolRequestDto {
  toolCallId: string;
  tool: "find_practice" | "find_sources" | "compare_sources" | "find_facets" | "practice_availability";
  reason: string | null;
  /** "eager": run when the offer is shown; "lazy": run when tapped. */
  run: "eager" | "lazy";
  dropped: Array<Record<string, unknown>>;
  arguments: Record<string, unknown>;
}

export interface ProposedItemDto {
  rank: number;
  practiceItemId: string;
  learningObjectId: string;
  learningObjectTitle: string | null;
  practiceMode: string;
  prompt: string;
  facetIds: string[];
  rationale: string | null;
  unranked?: string;
}

export interface ProposedExerciseDto {
  kind: "source_exercise";
  key: string;
  extractionId: string;
  spanIds: string[];
  sourceId?: string | null;
  revisionId?: string | null;
  sourceTitle: string | null;
  label: string | null;
  page: number | null;
  statement: string;
  rationale: string | null;
  labelLine: string;
}

export interface FindPracticeResultDto {
  version: number;
  status: string;
  proposalId?: string;
  intent?: string;
  items: ProposedItemDto[];
  sourceExercises?: ProposedExerciseDto[];
  sourceExercisesStatus?: string;
  note?: string;
}

/** A model-reader view of a tool result (spec §5.3): no answers, rubrics or solutions. */
export interface SourcePassageDto {
  spanKey: string;
  sourceTitle: string | null;
  section: string | null;
  page: number | null;
  revisionId: string | null;
  text: string;
  label: string;
}

export interface ToolPracticeItemDto {
  practiceItemId: string;
  learningObjectId: string;
  facetIds: string[];
  practiceMode: string;
  prompt: string;
  difficulty: number | null;
  expectedMinutes: number | null;
  sourceLabel: string | null;
  rationale: string | null;
}

export interface ToolExerciseDto {
  key: string;
  spanKeys: string[];
  sourceLabel: string | null;
  page: number | null;
  statement: string;
  rationale: string | null;
}

export interface ComparisonSourceDto {
  ref: string;
  sourceId: string;
  sourceTitle: string | null;
  extractionId: string;
  spanId: string;
  page: number | null;
  passage: string;
  label: string;
  contributions?: Array<{ contribution: string; perspective: string | null; quote: string }>;
}

export interface SourceToolRunDto {
  version: number;
  tool: SourceToolRequestDto["tool"];
  policy: string;
  toolCallId: string;
  runId: string;
  result: {
    proposalId?: string;
    items?: ToolPracticeItemDto[];
    sourceExercises?: ToolExerciseDto[];
    passages?: SourcePassageDto[];
    comparisonId?: string | null;
    status?: string;
    sources?: ComparisonSourceDto[];
    relations?: Array<Record<string, unknown>>;
    missingPerspectives?: string[];
    unverifiedSources?: Array<Record<string, unknown>>;
    alsoDiscussedIn?: Array<Record<string, unknown>>;
    labels?: Record<string, string>;
    withheldAnswerOverlap?: number;
  };
}

export interface SourceExerciseImportDto {
  version: number;
  importId: string;
  status: string;
  practiceItemId?: string | null;
  keyStatus?: string | null;
  keyLabel?: string;
  reason?: string | null;
  /** The authored draft checked against what it was proposed for (§8.1). A
   *  learner's pick is imported anyway; `correction` corrects the claim. */
  validation?: { ok?: boolean; correction?: string | null; reason?: string | null } | null;
}

export interface CanonicalExerciseDto {
  sourceId: string;
  revisionId: string;
  extractionId: string;
  spanIds: string[];
  label: string;
  relation: "verbatim" | "variant_of";
  sourceTitle: string | null;
  keyStatus: string;
  keyLabel: string;
  authorship: string;
}

/** §12.1 proactive handoff: a tutor opening generated with no learner
 *  question yet, grounded in a just-closed diagnostic block's persisted
 *  decision. Ephemeral — never persisted as a question event. */
export interface TutorOpeningDto {
  version: number;
  openingMd: string | null;
}

export interface TutorQuestionEventDto {
  id: string;
  context: TutorQuestionContext;
  noteId: string | null;
  practiceItemId: string | null;
  attemptId: string | null;
  sessionId: string | null;
  questionMd: string;
  answerMd: string | null;
  questionType: string | null;
  facets: string[];
  hintEquivalent: boolean;
  leakSuspected: boolean;
  rating: number | null;
  secondsIntoAttempt: number | null;
  provider: string | null;
  createdAt: IsoTimestamp;
  /** Back-link to the note this turn was saved as (migration 027), null until saved. */
  savedNoteId: string | null;
  /** Persisted promotion ledger row for this turn (spec_tutor_promotion.md §5), null if unpromoted. */
  promotion: QuestionPromotionDto | null;
  /** Durable analysis/authoring request, including retryable failures. */
  promotionRequest: QuestionPromotionRequestDto | null;
  /** Reader CA2: the mode the answer was written in (Codex review F9). */
  answerMode?: string | null;
  /** The stored context: the attempt key and step (F5), the citations with
   *  their excerpts (F9), a withheld answer's take step (F2). */
  sourceContext?: Record<string, unknown> | null;
}

// ── Tutor question promotion (spec_tutor_promotion.md) ─────────────────────

export type PromotionIntent = "practice" | "gap";

export type PromotionRoute = "auto_apply" | "review_required" | "diagnostic_pending" | "existing_item";

export type QuestionNature = "core_recall" | "mechanism" | "transfer" | "edge_case" | "what_if";

export interface QuestionPromotionDto {
  questionEventId: string;
  intent: PromotionIntent;
  route: PromotionRoute;
  attributedFacets: string[];
  questionNature: QuestionNature | null;
  attemptedInThread: boolean | null;
  learnerClaimId: string | null;
  interventionNeedId: string | null;
  proposedPatchId: string | null;
  savedNoteId: string | null;
  existingPracticeItemId: string | null;
  createdPracticeItemId: string | null;
  createdLearningObjectId: string | null;
  createdAt: IsoTimestamp;
  updatedAt: IsoTimestamp;
}

export interface PromoteTutorQuestionInput {
  eventId: string;
  intent: PromotionIntent;
  subjectId?: string;
  learningObjectId?: string;
}

export interface QuestionPromotionRequestDto {
  questionEventId: string;
  intent: PromotionIntent;
  subjectId: string | null;
  learningObjectId: string | null;
  status: "queued" | "running" | "completed" | "failed";
  stage: "queued" | "analysis" | "authoring" | "diagnostic" | "review" | "ready" | "failed";
  batchId: string | null;
  promotionRoute: PromotionRoute | null;
  errorCode: string | null;
  errorMessage: string | null;
  retryable: boolean;
  createdAt: IsoTimestamp;
  updatedAt: IsoTimestamp;
}

export interface PromoteTutorQuestionResult {
  version: number;
  request: QuestionPromotionRequestDto;
  promotion: QuestionPromotionDto | null;
}

// ── Outstanding-question queue (migration 102) ─────────────────────────────
// answerStatus tracks whether the TUTOR answered; resolution tracks whether the
// LEARNER is done with the question. They are independent axes.

export type QuestionResolution = "open" | "resolved" | "dismissed";

export interface QuestionQueueRowDto {
  id: string;
  context: TutorQuestionContext;
  questionMd: string;
  answerMd: string | null;
  answerStatus: "pending" | "answered" | "failed";
  resolution: QuestionResolution;
  questionType: string | null;
  practiceItemId: string | null;
  attemptId: string | null;
  noteId: string | null;
  sessionId: string | null;
  savedNoteId: string | null;
  createdAt: IsoTimestamp;
  promotion: QuestionPromotionDto | null;
  promotionRequest: QuestionPromotionRequestDto | null;
  promotionTargetIds: string[];
  /** Exact canonical teaching span when one can be resolved honestly. */
  sourceCitation: TutorCitationDto | null;
}

export interface QuestionQueueSnapshot {
  version: number;
  questions: QuestionQueueRowDto[];
  openCount: number;
}

export interface ResolveQuestionEventResult {
  version: number;
  eventId: string;
  resolution: QuestionResolution;
  openCount: number;
}

export interface QueueRevisionDto {
  version: number;
  revision: number;
  updatedAt: IsoTimestamp | null;
}

// ── Learner item authoring (services.item_authoring) ───────────────────────
// The §3.7 typed retirement taxonomy — also the learner vocabulary from the
// Matuschak talk-aloud notes ("too easy", "knew the prompt, not the concept").

export const RETIREMENT_REASONS = [
  "too_easy",
  "ambiguous",
  "missing_context",
  "duplicate_surface",
  "wrong_granularity",
  "no_longer_relevant",
  "bad_underlying_explanation",
  "superseded_by_better_activity",
  "should_be_reference_not_memorized",
  "dont_care_enough_to_retain",
  "knew_prompt_not_concept"
] as const;

export type RetirementReason = (typeof RETIREMENT_REASONS)[number];

export interface TutorTranscriptInput {
  context: TutorQuestionContext;
  practiceItemId?: string;
  attemptId?: string;
  noteId?: string;
  sessionId?: string;
  /** Reader CA2 (K5): the attempt's key; its thread only. */
  submissionId?: string;
  /** Codex review F6: the unfinished workbench the thread is asked from. */
  workbenchSessionId?: string;
}

/** Reader CA2 (§7.5, K8; Codex review F7): the attempt's help record as
 *  Submit will fold it, in order, from stored state. */
export interface HelpRecordDto {
  items: Array<{
    kind: "question" | "hint" | "check" | "worked" | "earlier";
    at: string | null;
    counts: boolean;
    level?: number | null;
    thisAttempt?: boolean;
    eventId?: string;
    /** A hint's counter: the hint service ("server") or the screen ("client"). */
    countedBy?: "server" | "client" | null;
    /** A hint, check or worked help's ``help_assists`` row (re-review F14). */
    assistId?: string;
  }>;
  /** The hint-equivalents the submit's server side adds. */
  counted: number;
  earlierOpened: boolean;
}

/** Reader CA2 (§7.3, K6): one earlier attempt's help, read-only, never current. */
export interface EarlierThreadDto {
  attemptId: string;
  at: string;
  outcome: { label: string; assisted: boolean; rubricScore: number | null; maxPoints: number | null };
  exchanges: Array<{
    eventId: string;
    context: string;
    questionMd: string;
    answerMd: string | null;
    questionType: string | null;
    hintEquivalent: boolean;
    createdAt: string;
  }>;
  hints: Array<{ kind: string | null; level: number | null; bodyMd: string; at: string | null }>;
}

export interface TutorTranscriptSnapshot {
  version: number;
  events: TutorQuestionEventDto[];
  /** Null: no request bound (a subscription route, Codex review F8). */
  remaining: number | null;
  /** Codex review F7: practice, the panel on. */
  helpRecord?: HelpRecordDto;
  /** Reader CA2 (§7.3, K6, Q2), practice and feedback while the panel is on:
   *  earlier attempts' help (empty during a check on your own, ``cold``),
   *  whether opening one before Submit counts as a hint, and the stored help
   *  style. Absent with the panel off. */
  earlier?: EarlierThreadDto[];
  earlierCountsAsHint?: boolean;
  cold?: boolean;
  helpStyle?: HelpStyle;
}

export interface TutorSaveNoteResult {
  version: number;
  noteId: string | null;
  path: string;
}

// ── Teach-back conversation ────────────────────────────────────────────────

export type RubricTier = "core" | "transfer";

export interface TeachBackPlannedDto {
  criterionId: string;
  tier: RubricTier;
  facetTargets: string[];
}

export interface TeachBackTurnDto {
  role: "learner" | "ai";
  contentMd: string;
  criterionId: string | null;
}

/** Camelized core TeachBackState — persisted verbatim in the session checkpoint. */
export interface TeachBackStateDto {
  version: number;
  practiceItemId: string;
  planned: TeachBackPlannedDto[];
  turns: TeachBackTurnDto[];
  askedCount: number;
  /** The queue offer the conversation answers, linked to the graded attempt. */
  schedulerCandidateId?: string | null;
}

export interface StartTeachBackInput {
  sessionId: string;
  practiceItemId: string;
  /** The queue offer the item was opened from, as on submitAttempt. */
  schedulerCandidateId?: string | null;
}

export interface StartTeachBackResult {
  version: number;
  practiceItemId: string;
  /** Teaching brief: the item prompt. */
  prompt: string;
  learningObjectTitle: string;
  /** Planned number of follow-up questions (capped at config max). */
  budget: number;
  state: TeachBackStateDto;
}

export interface SubmitTeachBackTurnInput {
  sessionId: string;
  practiceItemId: string;
  schedulerCandidateId?: string | null;
  answerMd: string;
  /** Grade the transcript now instead of asking further questions. */
  finish?: boolean;
  latencySeconds?: number | null;
}

export interface TeachBackQuestionResult {
  version: number;
  done: false;
  questionMd: string;
  criterionId: string;
  tier: RubricTier;
  facetTargets: string[];
  questionNumber: number;
  remaining: number;
  asked: number;
  budget: number;
  state: TeachBackStateDto;
}

export type TeachBackFinishResult = AttemptResultDto & {
  done: true;
  transcriptMd: string;
  askedCriterionIds: string[];
  gradedCriterionIds: string[];
};

export type TeachBackTurnResult = TeachBackQuestionResult | TeachBackFinishResult;

export interface FollowupSourceDto {
  gateAttemptId: string;
}

export interface FollowupRatingDto {
  useful: boolean;
  ratedAt: IsoTimestamp;
}

export interface InterventionNeedDto {
  id: string;
  attemptId: string | null;
  learningObjectId: string;
  practiceItemId: string | null;
  desiredIntent: string;
  triggerReason: string;
  targetFacets: string[];
  errorTypes: string[];
  priority: number;
  status: "pending" | "fulfilled" | "dismissed" | "stale";
  blockedReason: string;
  candidateRequirements: Record<string, unknown>;
  createdAt: IsoTimestamp;
  updatedAt: IsoTimestamp;
}

export interface CriterionEvidenceRowDto {
  criterionId: string;
  criterionDescription: string;
  pointsAwarded: number;
  pointsPossible: number;
  evidence: string | null;
  notes: string | null;
  graderTier: number;
  /** Rubric tier ("core" | "transfer"); shown as a pill when a rubric mixes tiers. */
  tier?: RubricTier | null;
  /** PF-c: false when the learner's verified answer took a different route that
   *  never exercised this criterion. It is not assessed (no credit, no failure,
   *  out of the grade) and is shown with `notAssessedLabel`, never as points. */
  assessed?: boolean;
  notAssessedLabel?: string | null;
}

/** PF-c's manual-review reason: a non-blocking log, never a review to do. */
export const UNVERIFIED_ROUTE_REVIEW_REASON = "valid_alternative_unverified";
export const NOT_ASSESSED_LABEL = "not assessed (a different route)";

/** Whether a criterion row counts toward the grade (PF-c unassessed rows do not). */
export function criterionAssessed(row: Pick<CriterionEvidenceRowDto, "assessed">): boolean {
  return row.assessed !== false;
}

export interface ErrorEventDto {
  id: string;
  attemptId: string | null;
  learningObjectId: string;
  errorType: string;
  errorTitle: string | null;
  severity: number;
  isMisconception: boolean;
  repairPlan: Record<string, unknown> | null;
  status: "active" | "resolved";
  createdAt: IsoTimestamp;
}

export interface AttemptSurpriseDto {
  predictiveSurprise: number | null;
  bayesianSurprise: number | null;
  surpriseDirection: string | null;
  fsrsIntervalFactor: number | null;
  // Negative-surprise threshold inside the broader intervention gate.
  followupThresholdNats: number | null;
  triggeredActions: string[];
  suppressedActions: string[];
  // Per-attempt record of why the follow-up gate did (or did not) fire. Null on
  // legacy attempts recorded before the gate trace was persisted.
  gateDiagnostics: FollowupGateDiagnosticsDto | null;
}

// The single signal that decided a follow-up outcome (e.g. surprise vs τ, grader
// confidence vs γ_min). `value`/`threshold`/`comparator` render one line without
// re-deriving thresholds client-side; `satisfied` is whether the signal's own
// condition held.
export interface FollowupGateSignalDto {
  name: string | null;
  value: number | boolean | null;
  threshold: number | boolean | null;
  comparator: string | null;
  unit: string | null;
  satisfied: boolean;
  surpriseDirection?: string | null;
  // Quantile-threshold provenance (gate modernization); absent on legacy rows.
  thresholdSource?: "quantile" | "absolute_fallback" | "absolute" | null;
  thresholdQuantile?: number | null;
  thresholdSampleSize?: number | null;
}

export interface FollowupGateSubscoreDto {
  rawValue: number | null;
  subscore: number;
  weight: number;
  contribution: number;
  threshold?: number | null;
  thresholdSource?: string | null;
  thresholdQuantile?: number | null;
  thresholdSampleSize?: number | null;
}

export interface FollowupGateDiagnosticsDto {
  outcome: "queued" | "need_recorded" | "suppressed" | "not_triggered";
  decisiveReason: string;
  decisiveSignal: FollowupGateSignalDto | null;
  naturalTriggerReasons: string[];
  triggeredReasons: string[];
  wouldSuppress: string[];
  wouldAutoFire: boolean;
  manualOverride: boolean;
  bayesianSurprise: number | null;
  surpriseDirection: string | null;
  tauFollowupNats: number | null;
  graderConfidence: number | null;
  maxErrorSeverity: number | null;
  targetFacets: string[];
  // Gate modernization (all optional — legacy rows keep rendering).
  gateMode?: "cascade" | "score";
  gateScore?: number;
  gateScoreThreshold?: number;
  gateBias?: number;
  weightsProvenance?: string;
  hardGates?: string[];
  subscores?: Record<string, FollowupGateSubscoreDto>;
  thresholds?: Record<
    string,
    {
      value: number;
      source: string;
      quantile: number | null;
      sampleSize: number;
      absoluteFallback: number;
    }
  >;
}

export interface RepairSuggestionDto {
  /** e.g. `diagnosis:<id>:<n>`; `escalation:<diagnosis id>` for a repair
   *  written at a recurrence group's K-th answer (Slice 2 T1), which leads. */
  id?: string | null;
  practiceMode: string;
  learningObjectId: string | null;
  rationale: string;
  /** An escalated repair's representation (worked contrast, counterexample, ...). */
  representation?: string | null;
  /** True for the repair written at escalation time (not the diagnosis's own). */
  generated?: boolean;
  targetEvidenceFamilies?: string[];
  targetCriterionIds?: string[];
  operator?: string | null;
  targetRefs?: CausalTargetRefDto[];
  preserveRefs?: CausalTargetRefDto[];
  expectedMinutes?: number | null;
  answerRevealBudget?: number | null;
  /**
   * Eliciting repair. When present (the grader's default for misconception-class
   * mechanisms), the suggestion asks ONE question the learner answers unaided
   * instead of showing spliced corrected work — so the feedback screen must
   * render the question and a response box, NOT a solution. Submit the answer
   * with `submitElicitingResponse`.
   */
  elicitingQuestion?: string | null;
  /** What a correct unaided response to `elicitingQuestion` would demonstrate. */
  expectedResponseContract?: string | null;
  repairedTrace?: RepairedTraceDto | null;
  verificationRequest?: {
    kind: "symbolic_equality" | "exact_match";
    assumptions?: string[];
    requiredAssumptions?: string[];
  } | null;
  repairValidation?: {
    id: string;
    authority: "learnloop_validator";
    status: "valid" | "invalid" | "incomplete";
    reasons: string[];
    verification: {
      status: string;
      detail?: string | null;
    };
  };
}

// Detail payload for `inspect_entity` on a practice attempt (sidecar
// attempt_detail): the raw attempt row camelized, plus the full feedback bundle.
export interface AttemptInspectorDetail {
  version: number;
  id: string;
  practiceItemId: string;
  learningObjectId: string;
  subject: string | null;
  concept: string | null;
  practiceMode: string | null;
  attemptType: string | null;
  learnerAnswerMd: string | null;
  rubricScore: number | null;
  correctness: number | null;
  confidence: string | number | null;
  latencySeconds: number | null;
  hintsUsed: number | null;
  errorType: string | null;
  graderConfidence: number | null;
  manualReview: boolean | number | null;
  manualReviewReason: string | null;
  sessionId: string | null;
  schedulerSlateId?: string | null;
  schedulerCandidateId?: string | null;
  createdAt: IsoTimestamp;
  feedback: FeedbackBundle | null;
  /** Full P1 audit record. Unlike feedback.causalFeedback, this debug surface
   * includes evidence, alternatives, selector costs, and probe reasoning. */
  causalEpisode?: CausalEpisodeDto | null;
}

export interface NoteInspectorDetail {
  id: string;
  requestedId: string;
  title: string;
  subjects: string[];
  relatedLos: string[];
  relatedConcepts: string[];
  sourceType: string;
  path: string | null;
  locator: string | null;
  canonicalSource: Record<string, unknown> | null;
  createdAt: IsoTimestamp | null;
  updatedAt: IsoTimestamp | null;
  body: string;
}

export interface ProbeEpisodeInspectorDetail {
  id: string;
  learningObjectId: string;
  status: string;
  trigger: string;
  hypothesisSetId: string | null;
  targetDecision: Record<string, unknown> | null;
  requiredFacets: string[];
  minimumIndependentObservations: number;
  maximumObservations: number;
  enteredAt: IsoTimestamp | null;
  completedAt: IsoTimestamp | null;
  completionReason: string | null;
  createdAt: IsoTimestamp;
  observations: Array<{
    attemptId: string;
    practiceItemId: string;
    eligibleForCompletion: boolean;
    updatesBelief: boolean;
    entropyBefore: number;
    entropyAfter: number;
    realizedInformationGain: number;
    contamination: Record<string, unknown> | null;
    createdAt: IsoTimestamp;
  }>;
}

export type InspectorEntity =
  | { version: number; kind: "practice_item"; id: string; detail: PracticeItemDetail }
  | { version: number; kind: "learning_object"; id: string; detail: LearningObjectDetail }
  | { version: number; kind: "concept"; id: string; detail: ConceptInspectorDetail }
  | { version: number; kind: "attempt"; id: string; detail: AttemptInspectorDetail }
  | { version: number; kind: "error_event"; id: string; detail: ErrorEventDto }
  | { version: number; kind: "note"; id: string; detail: NoteInspectorDetail }
  | { version: number; kind: "probe_episode"; id: string; detail: ProbeEpisodeInspectorDetail }
  | { version: number; kind: "not_found"; id: string; suggestions: InspectorSearchResult[] };

export interface InspectorSearchResult {
  kind: "practice_item" | "learning_object" | "concept" | "attempt" | "error_event";
  id: string;
  title: string;
  subtitle: string | null;
  score: number;
}

export interface LearningObjectDetail {
  id: string;
  title: string;
  subjects: string[];
  concept: string;
  knowledgeType: string;
  status: string;
  summary: string;
  prerequisites: string[];
  confusables: string[];
  prerequisiteConcepts?: ConceptReferenceDto[];
  confusableConcepts?: ConceptReferenceDto[];
  difficultyPrior: number | null;
  tags: string[];
  mastery: MasteryDto | null;
  // Raw on-disk requirement recipes (§7.2) — the editable source of readiness,
  // distinct from the readiness *projection* in LoReadinessDto. Absent on legacy
  // LOs that predate blueprints. See LoBlueprintDto (graph-editor section).
  blueprints?: LoBlueprintDto[];
  /** Learner field F2: placement label and controls for this LO. */
  placement?: LearningObjectPlacementDto;
}

/** One LO's placement state (learner field §5.2). `assumed` is an open
 *  "assumed known (not tested)" decision; nothing here is evidence. */
export interface PlacementLearningObjectDto {
  learningObjectId: string;
  /** Current routing: assumed (check pending), maintenance (check passed:
   *  remaining learning items withheld) or learning; null when placement never
   *  acted on this LO. */
  intent: "assumed" | "maintenance" | "learning" | null;
  intentReason: "assumed" | "check_passed" | "check_missed" | "missed_in_maintenance" | "i_dont_know_this" | null;
  /** How the diagnosis decided the intent (owner decision 2026-10-12): a
   *  first review or a later review short of full marks keeps the topic in
   *  maintenance unless the diagnosis finds a knowledge gap. */
  outcomeReason?: PlacementOutcomeReason | null;
  /** A miss whose diagnosis has not landed yet: the decision waits on it. */
  awaitingDiagnosis?: boolean;
  assumed: boolean;
  /** Learner-text gaps: a prerequisite created from the learner's own text,
   *  its one delayed check pending (never "assumed known"). */
  addedFromQuestion?: boolean;
  /** mvp-0.16: the first review a learner-text gap brought forward, and the
   *  due date it replaced. */
  firstReviewBroughtForwardFrom?: IsoTimestamp | null;
  label: string | null;
  source: AssumptionSource | null;
  firstReviewDue: IsoTimestamp | null;
  firstReviewIsDue: boolean;
  lastOutcome: "passed" | "failed" | "returned" | null;
  returnedByLearner: boolean;
}

/** Kept in maintenance: clean (full marks), slip, item_contract (the question
 *  did not make clear what it expected), interaction_context (how it was
 *  presented, not knowledge) or unassessed (a route the grader could not
 *  check), each only when every part of the miss reads that way. Back to
 *  learning: knowledge_gap, no_gap_attributed (the diagnosis left part of the
 *  miss without a non-gap reading, so today's rule), learner_side (hints,
 *  priming, "don't know"), no_diagnosis (today's rule) or i_dont_know_this. */
export type PlacementOutcomeReason =
  | "clean"
  | "slip"
  | "item_contract"
  | "interaction_context"
  | "unassessed"
  | "no_gap_attributed"
  | "knowledge_gap"
  | "learner_side"
  | "no_diagnosis"
  | "i_dont_know_this";

export interface PlacementStateDto {
  version?: number;
  active: boolean;
  algorithmVersion: string;
  quickCheckK: number;
  quickCheckBudgetMinutes: number;
  learningObjects: PlacementLearningObjectDto[];
}

export type LearningObjectPlacementDto = Omit<PlacementStateDto, "learningObjects" | "version"> &
  Partial<PlacementLearningObjectDto>;

export type PlacementReport = "know_this" | "too_easy" | "dont_know_this";

export interface PlacementSelfReportInput {
  report: PlacementReport;
  learningObjectIds?: string[];
  practiceItemId?: string;
  /** With practiceItemId: the session whose draft for that card is cleared in
   *  the same transaction when the report succeeds. */
  sessionId?: string;
}

export interface PlacementSelfReportResult {
  version: number;
  report: PlacementReport;
  results: Array<{
    learningObjectId: string;
    status: string;
    assumptionId?: string | null;
    firstReviewDue?: IsoTimestamp;
  }>;
  /** Whether the reporting card's durable draft was cleared. */
  checkpointCleared: boolean;
  placement: PlacementStateDto;
}

export interface StartQuickCheckInput {
  sessionId: string;
  learningObjectIds: string[];
  /** Stable identity of this start: a retry returns the same check. */
  requestId?: string;
}

export interface ConceptReferenceDto {
  reference: string;
  conceptId: string | null;
  title: string;
  resolved: boolean;
  source?: "authored" | "learner_observed" | "authored_and_learner_observed";
  probability?: number;
  priorProbability?: number;
  evidenceCount?: number;
  lastObservedAt?: IsoTimestamp | null;
}

export interface ConceptInspectorDetail {
  id: string;
  title: string;
  type: "concept" | "procedure" | "skill" | "misconception";
  aliases: string[];
  description: string | null;
  tags: string[];
  relations: Array<{
    id: string;
    relationType: "prerequisite" | "confusable_with" | "part_of" | "related";
    direction: "incoming" | "outgoing";
    concept: ConceptReferenceDto;
    strength: number;
    rationale: string | null;
  }>;
  learningObjects: Array<{
    id: string;
    title: string;
    knowledgeType: string;
    status: string;
  }>;
}

/** Plan-first transport T1: the reply to ai_use_fallback ("Use OpenRouter instead"). */
export interface AiUseFallbackDto {
  version: number;
  provider: "openrouter";
  profile: string | null;
  grantedTasks: string[];
  /** The actions (RPC methods) said yes to on this vault (redesign D). */
  grantedActions?: string[];
  offerId?: string;
  action?: string;
  scope: "session";
}

export interface CommandError {
  code: string;
  message: string;
  retryable: boolean;
  details?: unknown;
}

export interface CliCommandResult {
  version: number;
  argv: string[];
  exitCode: number;
  stdout: string;
  stderr: string;
}

export interface RecentIngestEntry {
  noteId: string;
  path: string | null;
  subjectId: string | null;
  title: string;
  kind: string | null;
  canonicalUri: string | null;
  authors: string[];
  retrievedAt: string | null;
  createdAt: string | null;
  patchId: string | null;
  purpose: "canonical_ingest" | "exam_ingest";
}

export interface RecentIngestsSnapshot {
  version: number;
  ingests: RecentIngestEntry[];
}

export type IngestMode = "canonical" | "exam";
export type IngestJobStatus = "queued" | "running" | "completed" | "failed" | "cancelled";
export type IngestJobPhase =
  | "queued"
  | "preparing"
  | "fetching"
  | "extracting"
  | "staging"
  | "authoring"
  | "cancelling"
  | "completed"
  | "failed"
  | "cancelled";

export interface IngestSourceClassification {
  version: number;
  kind: "web" | "arxiv" | "pdf" | "youtube" | "textfile";
  normalizedSource: string;
}

export interface IngestJobResult {
  proposalId: string | null;
  agentRunId: string | null;
  sourceNoteId: string;
  sourceKind: string;
  subjectId: string;
  contentHash: string;
  reusedExisting: boolean;
  codexCalls: number;
  autoAppliedCount: number;
  reviewRequiredCount: number;
  invalidCount: number;
  sourceEventCount: number;
  goalId: string | null;
  goalCreated: boolean;
  goalUpdated: boolean;
}

export interface IngestJobError {
  code: string;
  message: string;
  details: { partial?: boolean; exitCode?: number; [key: string]: unknown };
}

export interface IngestJobDto {
  version?: number;
  id: string;
  source: string;
  subjectId: string;
  mode: IngestMode;
  status: IngestJobStatus;
  phase: IngestJobPhase;
  message: string;
  currentWindow: number | null;
  totalWindows: number | null;
  createdAt: string;
  updatedAt: string;
  startedAt: string | null;
  finishedAt: string | null;
  result: IngestJobResult | null;
  error: IngestJobError | null;
}

export interface IngestJobsSnapshot {
  version: number;
  jobs: IngestJobDto[];
}

export type PdfEngine = "auto" | "glm_ocr" | "marker" | "pypdf" | "native";

export interface StartIngestInput {
  source: string;
  subjectId: string;
  mode: IngestMode;
  /** PDF extraction engine; "auto" defers to the vault's [ingest.pdf] config. */
  pdfEngine?: PdfEngine;
}

// ── Durable ingest workflows (source-ingestion v2 §6.2) ──────────────────
export type DurableIngestStatus =
  | "queued"
  | "running"
  | "waiting_for_input"
  | "completed"
  | "failed"
  | "blocked"
  | "cancelled";

export interface IngestJobView {
  id: string;
  batchId: string;
  ordinal: number;
  jobType: string;
  status: DurableIngestStatus;
  phase: string | null;
  message: string | null;
  currentWindow: number | null;
  totalWindows: number | null;
  attemptCount: number;
  checkpointLadder: string[];
  usage: Record<string, number>;
  estimate: Record<string, number>;
  source: string | null;
  result: Record<string, unknown> | null;
  error: {
    code: string;
    message: string;
    details?: {
      diagnostics?: Array<{
        gate?: string;
        severity?: string;
        message?: string;
        entity_refs?: string[];
        suggested_action?: string;
      }>;
      stage?: string;
      completed_dependencies_preserved?: boolean;
      candidate_preserved?: boolean;
      synthesis_run_id?: string | null;
      [key: string]: unknown;
    };
    retryable?: boolean;
  } | null;
  waitingForInput: Record<string, unknown> | null;
  dependsOn: string[];
}

/** Facet identity (handoff §4): one merge or absorb a judge applied, with its undo state. */
export interface FacetIdentityFacetRef {
  id: string;
  claim: string;
}

/** A reword: an existing facet's meaning changed by an applied proposal. The
 *  facet keeps its id and evidence; the old wording is kept for the undo. */
export interface FacetRewordDto {
  from: string;
  to: string;
  fromVersion: number | null;
  toVersion: number | null;
  /** Which meaning fields changed: claim, kind, conditions, non-goals. */
  fields: string[];
}

/** A validated citation of a facet change, as the owner sees it beside the change.
 *  Exam material (assessmentOnly) never carries its text. */
export interface FacetChangeSourceDto {
  sourceId: string;
  revisionId: string;
  extractionId: string;
  unitId: string;
  spanId: string;
  /** The unit's effective role: primary_textbook, notes, problem_set, exam… */
  role: string;
  relation: string;
  locator: string;
  assessmentOnly: boolean;
  /** A short excerpt of the cited span (null for exam material). */
  excerpt: string | null;
}

/** One field a held reword changes, before and after. */
export interface FacetRewordChangeDto {
  field: string;
  before: unknown;
  after: unknown;
}

/** The span-support check that held a cited reword (Tier 1, owner 2026-10-13):
 *  the Decider's top option over the cited passages and the new wording.
 *  `verdict` is null when it gave no answer (`status` says why). */
export interface FacetSpanSupportDto {
  status: "ok" | "unavailable" | "refused" | "failed" | "disabled";
  verdict: "supports" | "partly supports" | "does not support" | "unrelated" | null;
  probabilities: Record<string, number>;
  judgmentId?: string | null;
}

/** A reword with no textbook, lecture, paper, reference or alternate-explanation
 *  source behind it, or one whose cited passages the span-support check did not
 *  find to support it, held for the owner's one-tap confirm (owner, 2026-10-13).
 *  `decideFacetReword(actionId, "confirm" | "keep")`. */
export interface FacetRewordConfirmDto {
  actionId: string;
  facetId: string;
  title: string;
  fields: string[];
  changes: FacetRewordChangeDto[];
  sources: FacetChangeSourceDto[];
  /** Citations that did not count (outside the selected units, wrong unit…), and why. */
  unresolved: string[];
  message: string;
  proposalId: string | null;
  proposalItemId: string | null;
  runId: string | null;
  createdAt: string;
  status: "pending" | "confirmed" | "kept" | "withdrawn";
  decidedAt: string | null;
  /** Why an earlier confirm did not land (it waits again). */
  interrupted: string | null;
  /** Set when the span-support check held it (empty otherwise). */
  spanSupport?: Partial<FacetSpanSupportDto>;
}

export interface FacetIdentityActionDto {
  id: string;
  /** proposal = a reword applied from a proposal; registry = the owner's own merge. */
  origin: "ingest" | "append" | "dedupe" | "proposal" | "registry";
  scope: "in_run" | "attach" | "vault";
  runId: string;
  proposalId: string | null;
  action: "merge" | "absorb" | "reword";
  absorbAs: "example" | "precondition" | null;
  survivor: FacetIdentityFacetRef;
  retired: FacetIdentityFacetRef[];
  rationale: string;
  /** Facets that carried graded evidence when the action applied (provenance:
   *  a merge re-keys it to the survivor and its undo moves it back). Facet
   *  identity locks were removed, so nothing is refused because of it. */
  evidencedFacets?: string[];
  /** Present on a reword. */
  reworded?: FacetRewordDto | null;
  /** The validated sources a reword cited (its history). */
  sources?: FacetChangeSourceDto[];
  /** A title or worked-example change: on the history, not a new version. */
  presentation?: boolean;
  /** A reword held for the owner's confirm, and what became of it. */
  confirm?: FacetRewordConfirmDto | null;
  /** Why an attach left a registered facet's contract as it was. */
  contractNote?: string | null;
  /** What an undo does not move back (rows graded while the merge stood). */
  undoLimits?: string | null;
  judge: string;
  judgeModel: string | null;
  /**
   * proposed = applies with its proposal (a reword: waits for the owner's
   * confirm); applied = undoable now; undone.
   * applying/undoing = interrupted mid-write (doctor --fix-state finishes it);
   * abandoned = withdrawn before it was written.
   */
  status: "proposed" | "applying" | "applied" | "undoing" | "undone" | "abandoned";
  undoable: boolean;
  /** Why this merge has no undo, when it has none by construction. */
  note?: string | null;
  createdAt: string;
  undoneAt: string | null;
}

/** The facet-identity block of a synthesis/append job result (absent when switched off). */
export interface FacetIdentitySummaryDto {
  status: string;
  /** The run whose actions the panel re-reads for their live undo state. */
  runId?: string | null;
  groups: number;
  groupsJudged: number;
  inRunRetired: number;
  attached: number;
  judge: string | null;
  notes: string[];
  actions: FacetIdentityActionDto[];
}

export interface IngestBatchDto {
  version?: number;
  id: string;
  workflowType: string;
  subjectId: string | null;
  sourceSetId: string | null;
  status: DurableIngestStatus;
  cancelRequested: boolean;
  createdAt: string | null;
  startedAt: string | null;
  finishedAt: string | null;
  jobs: IngestJobView[];
  // Present on build_study_map results: which routing was chosen for the
  // collection — "bootstrap" creates the map, "append" reconciles new material
  // into an existing one via the bounded neighborhood.
  mode?: "bootstrap" | "append";
}

export interface IngestBatchesSnapshot {
  version: number;
  batches: IngestBatchDto[];
}

export interface RetrySynthesisInput {
  batchId: string;
  /** Required for a model rerun; ignored when reuseCandidate is set. */
  synthesisTotalInputTokens?: number;
  synthesisShardOutputTokens?: number;
  synthesisOutputTokens?: number;
  /** Disable LearnLoop's synthesis total/output ceilings (provider limits still apply). */
  unlimitedTokenBudget?: boolean;
  /** Revalidate the preserved merged candidate with zero model calls. */
  reuseCandidate?: boolean;
  /** With reuseCandidate: auto-apply mechanically-safe repairs (e.g. drop
   * dangling criterion-id dependencies) before the gates rerun. */
  repairCandidate?: boolean;
}

export interface SynthesisCandidateSummary {
  version?: number;
  synthesisRunId: string;
  runStatus: string;
  createdAt: string | null;
  completedAt: string | null;
  summary: string;
  itemCounts: Record<string, number>;
  notes: string[];
}

export interface StartImportBatchInput {
  sources: string[];
  subjectId?: string | null;
  inventory?: boolean;
  /** Inclusive, 1-based PDF page range. Both values must be supplied together. */
  pageStart?: number | null;
  pageEnd?: number | null;
  /** Inclusive, 1-based page expression, e.g. "3-27, 29-33, 36". */
  pages?: string | null;
  /** Per-source page expressions for staged multi-source imports. */
  pageRanges?: Array<{ source: string; pages: string }>;
  /** Sources opted OUT of the reader loop at ingest setup (e.g. practice exams). */
  readerDisabledSources?: string[];
  /** PDF extraction engine; "auto" defers to the vault's [ingest.pdf] config. */
  pdfEngine?: PdfEngine;
  estimate?: Record<string, unknown> | null;
}

export type SourceReadiness = "ready" | "processing" | "needs_extraction";

export interface SourceLibraryCard {
  sourceId: string;
  title: string;
  acquisitionKind: string | null;
  canonicalUri: string | null;
  workId: string | null;
  currentRevisionId: string | null;
  revisionCount: number;
  readiness: SourceReadiness;
  unitCount: number;
  blockCount: number;
  extractionStatus: string | null;
  suggestedRole: string | null;
  /** Per-source ingest-time choice: false = opted out of the reader loop. */
  readerEnabled: boolean;
  updateAvailable: boolean;
  /** UX Phase 1: "book", "paper", "article", "video" or "recording". */
  kindNoun?: string;
  /** The subject the source is filed under (automatic for Add), if any. */
  subjectId?: string | null;
  /** That subject's title: what the learner reads (usability round 1). */
  subjectTitle?: string | null;
  /** The card's one learner-facing status line, or null when there is nothing to say. */
  statusLine?: SourceStatusLineDto | null;
  /** Whether text recognition can run for this book here: details offer
   *  "Read it again with text recognition" only then (usability round 2). */
  textRecognitionAvailable?: boolean;
}

// ── UX Phase 1: one Add, the book card's status line, connect AI once ──────
// docs/specs/ux_learnloop_v1.md §6, §7.2. Every string here is learner copy
// produced by the sidecar in plain words (glossary §9).

export type SourceActionKind =
  | "undo_questions"
  | "build_now"
  | "build_whole_book"
  | "retry"
  | "text_recognition"
  /** The separate OK for sending a whole file out (a recording, a whole PDF). */
  | "allow_upload"
  /** Re-read safety E1: make the reading the book had current again. */
  | "restore_reading"
  /** Protection redesign: the owner marks exam material on a reading held
   *  back because exam material is marked on another reading of the book. */
  | "mark_exam_material"
  | "connect_ai"
  | "open_changes"
  | "open_settings";

export interface SourceStatusLineDto {
  text: string;
  /** quiet: a fact; working: something is happening; problem: something stopped. */
  tone: "quiet" | "working" | "problem";
  action: { kind: SourceActionKind; label: string } | null;
  /** The raw message behind the line, for details ▸ only. */
  details: string | null;
  /** What the card says instead while no AI can write questions (usability
   *  round 2: "come up as you read" under "Connect an AI"). */
  withoutAi?: SourceStatusLineDto | null;
}

/** A link an Add is still fetching: it has no library card yet. */
export interface PendingAddDto {
  batchId: string;
  source: string;
  kind: string | null;
  kindNoun: string;
  title: string;
  statusLine: SourceStatusLineDto | null;
}

export type AddSourceStatus = "added" | "queued" | "existing" | "unsupported";

export interface AddSourceItemDto {
  source: string;
  /** The library's spelling of the source (a card's canonicalUri). */
  canonical?: string | null;
  kind: string | null;
  kindNoun: string | null;
  status: AddSourceStatus;
  sourceId: string | null;
  revisionId: string | null;
  title: string;
  batchId: string | null;
  /** True until the source's text is ready (the Reader shows the original meanwhile). */
  preparing: boolean;
  /** One plain line for "existing" and "unsupported". */
  message: string | null;
}

export interface AddSourceResultDto {
  version?: number;
  items: AddSourceItemDto[];
  /** The item the Reader opens: the first that could be added or found. */
  opened: AddSourceItemDto | null;
}

export interface AddSourceInput {
  sources: string[];
  pages?: string | null;
  problemSet?: boolean;
  textRecognition?: boolean;
}

export interface AiConnectionDto {
  version?: number;
  canAuthor: boolean;
  provider: string;
  providerLabel: string;
  consentKey: string;
  consented: boolean;
  consentedAt: string | null;
  /** connect: no AI can write questions; consent: one OK is missing; null: ready. */
  needs: "connect" | "consent" | null;
  message: string | null;
  whatLeaves: string;
  /** What the Decider's small judgments send to Perplexity (Tier 1), as
   *  Settings discloses it; null when none is on. Part of whatLeaves. */
  deciderNote?: string | null;
  chatgptSignedIn: boolean;
  openrouterKeyPresent: boolean;
  /** connect_ai only: books whose questions were waiting and now start. */
  released?: string[];
}

export interface SourceActionResultDto {
  version?: number;
  sourceId: string | null;
  action: SourceActionKind;
  batchId?: string;
  reverted?: number;
  /** text_recognition on a book with study state (or one z.ai would read at
   *  a cost no OK line shows), or mark_exam_material: nothing ran yet; ask,
   *  then call again with `confirmed` (re-read safety). */
  needsConfirmation?: boolean;
  confirmation?: SourceRereadConfirmationDto | SourceMarkConfirmationDto;
  /** restore_reading: the revision made current again, or null. */
  restoredRevisionId?: string | null;
  /** mark_exam_material, confirmed: the reading marked and the units held out on it. */
  marked?: { extractionId: string; heldOutUnitIds: string[]; fromExtractionIds: string[] } | null;
}

/** What a card's action asks before it runs, in plain words. */
export interface SourceActionConfirmationDto {
  sourceId: string;
  extractionId: string | null;
  needsConfirmation: boolean;
  title: string;
  lines: string[];
  confirmLabel: string;
  cancelLabel: string;
  /** The marking's confirmation only: the identity of the proposal shown,
   *  sent back with its extractionId when the owner confirms (exam
   *  protection by extraction identity, final verify F13). */
  proposalHash?: string | null;
}

/** Protection redesign: what marking exam material on a held-back reading
 *  will hold out (suggested from the reading marked before). Confirming sends
 *  back its extractionId and proposalHash; if either changed meanwhile the
 *  sidecar marks nothing and returns a fresh confirmation. */
export interface SourceMarkConfirmationDto extends SourceActionConfirmationDto {
  heldOutUnitIds: string[];
  revisionId: string | null;
  proposalHash: string;
}

/** What reading a book again reads, costs and carries, in plain words. */
export interface SourceRereadConfirmationDto extends SourceActionConfirmationDto {
  /** 0-based PDF pages of the reading it replaces; null: the whole file. */
  pageSelection: number[] | null;
  pages: number | null;
  estimatedUsd: number | null;
  /** glm_ocr: z.ai; glm_ocr_local: the owner's own GLM-OCR server; local: this computer. */
  engine: "glm_ocr" | "glm_ocr_local" | "local";
}

// ── Source deletion (§4.1) ───────────────────────────────────────────────
// The impact report shown before the confirmation. `blockers` non-empty means
// deletion is refused right now (a worker is still writing rows for it).
export interface SourceDeletionCollectionImpact {
  sourceSetId: string;
  title: string;
  subjectId: string;
  /** This source is the collection's only member, so it is left empty. */
  leavesEmpty: boolean;
}

export interface SourceDeletionPlanDto {
  sourceId: string;
  title: string;
  canonicalUri: string | null;
  revisionCount: number;
  extractionCount: number;
  unitCount: number;
  blockCount: number;
  /** Study-map entities citing this source; they survive, the citation does not. */
  citationCount: number;
  citedEntities: Array<{ entityType: string; entityId: string; relation: string }>;
  collections: SourceDeletionCollectionImpact[];
  annotationCount: number;
  blockers: string[];
  deletable: boolean;
  removesStoredOriginal: boolean;
}

export interface SourceDeletionResultDto {
  sourceId: string;
  title: string;
  deletedRows: Record<string, number>;
  collectionsUpdated: string[];
  removedOriginal: boolean;
}

export interface SourceLibrarySnapshot {
  version: number;
  sources: SourceLibraryCard[];
  /** UX Phase 1: links an Add is still fetching (no card yet). */
  pending?: PendingAddDto[];
}

// ── ING M3: outline, unit selection, budget planning, repair (§3/§5.3/§8.6) ──

export interface UnitInventoryMarker {
  inventoried: boolean;
  inventoryProfile: string | null;
  profiles?: string[];
}

export interface OutlineUnit {
  unitId: string;
  parentUnitId: string | null;
  label: string;
  ordinal: number;
  locator: Record<string, unknown>;
  semanticHash: string;
  pageStart: number | null;
  pageEnd: number | null;
  blockCount: number;
  blockCounts: Record<string, number>;
  structuralSignals: Record<string, number>;
  healthFlags: string[];
  approxTokens: number;
  inventory: UnitInventoryMarker;
}

// Byte-exact display markdown the authoring model receives for a selection.
export interface SelectionPreviewDto {
  version?: number;
  extractionId: string;
  selectedUnitIds: string[];
  markdown: string;
  approxTokens: number;
}

// ── ING: live effective-unit shape from boundary overrides (§5.3) ──────────
// Deterministic backend preview of how merge/split intents reshape the units;
// zero LLM. `kind` drives the row glyph, `splitNoop` flags a split with no
// level-2 headings to partition on.
export interface EffectiveUnitDto {
  effectiveId: string;
  label: string;
  sourceUnitIds: string[];
  blockCount: number;
  approxTokens: number;
  kind: "merged" | "split" | "unchanged";
  splitNoop?: boolean;
}

export interface EffectiveOutlineDto {
  version?: number;
  extractionId: string;
  units: EffectiveUnitDto[];
}

export interface UnitSelectionState {
  selectedUnitIds: string[];
  boundaryOverrides: Record<string, unknown>[];
  needsReview: string[];
  roleOverride: string | null;
}

export interface SourceOutline {
  version?: number;
  extractionId: string;
  revisionId: string | null;
  sourceId: string | null;
  title: string;
  authors: string[];
  extractor: string;
  extractorVersion: string;
  unitCount: number;
  blockCount: number;
  approxTokens: number;
  healthFlags: string[];
  difficultPageCount: number;
  units: OutlineUnit[];
  selection: UnitSelectionState;
}

export interface SaveUnitSelectionInput {
  extractionId: string;
  selectedUnitIds: string[];
  boundaryOverrides?: Record<string, unknown>[];
  roleOverride?: string | null;
}

// ── ING M4: source sets, role-aware inventories, coverage (§4.3/§7/§9.3) ──

export interface SourceSetScopeDto {
  unitId: string;
  roleOverride: string | null;
}

export interface SourceSetMemberDto {
  sourceId: string;
  revisionId: string;
  defaultRole: string;
  scope: SourceSetScopeDto[];
  priority: number;
  /** The reading (extraction) the scope's unit ids were chosen on, its
   *  revision, and the vault writer's seal binding them to the scope's
   *  entries (exam protection by extraction identity). Absent when not
   *  recorded; re-sent exactly as received. */
  scopeExtractionId?: string | null;
  scopeRevisionId?: string | null;
  scopeSeal?: string | null;
}

export interface SourceSetDto {
  id: string;
  subjectId: string;
  title: string;
  members: SourceSetMemberDto[];
  priority?: number;
}

export interface SourceSetSummaryDto {
  id: string;
  subjectId: string;
  title: string;
  memberCount: number;
}

export interface SourceSetsSnapshot {
  version?: number;
  sourceSets: SourceSetSummaryDto[];
}

export interface CoverageReadinessFlag {
  code: string;
  message: string;
}

export interface SourceCoverageDto {
  sourceSetId: string;
  subjectId: string;
  curriculumLinkageSeam: string;
  members: Record<string, unknown>[];
  conceptMatrix: Record<string, unknown>[];
  assessmentAlignment: Record<string, unknown> | null;
  readiness: { ready: boolean; flags: CoverageReadinessFlag[]; notInventoried: Record<string, string>[] };
  rollup?: CoverageRollupDto;
}

export interface CoverageRollupDto {
  total: number;
  buckets: {
    demonstrated: { count: number; facetIds: string[] };
    assessed: { count: number; facetIds: string[] };
    noPracticeSupply: { count: number; facetIds: string[] };
  };
}

export interface StartInventoryInput {
  extractionRef: string;
  units: { unitId: string; role: string; profile?: string }[];
  subjectId?: string | null;
  sourceSetId?: string | null;
  inventoryOutputTokens?: number;
  unlimitedTokenBudget?: boolean;
}

export interface CreateStudyMapInput {
  sourceSetId: string;
  mode?: "auto" | "bootstrap";
  brief?: Record<string, unknown>;
  apply?: boolean;
  createGoal?: boolean;
  unlimitedTokenBudget?: boolean;
}

export interface BuildStudyMapInput {
  sourceSetId: string;
  brief?: Record<string, unknown>;
  mode?: "auto" | "bootstrap";
  inventoryOutputTokens?: number;
  // Per-run ceilings for this build; omitted keys fall back to [ingest.budgets].
  budgetOverrides?: Partial<IngestBudgetsDto>;
  unlimitedTokenBudget?: boolean;
}

export interface StudyMapDto {
  sourceSetId: string;
  subjectId: string;
  mode: string;
  manifestHash: string;
  synthesisRunId: string | null;
  proposalId: string | null;
  reused: boolean;
  applied: boolean;
  goalId: string | null;
  itemCounts: Record<string, number>;
  gateDiagnostics: Record<string, unknown>[];
  generationNeeds: Record<string, unknown>[];
  spanRequestCount: number;
  resolvedSpanHashes: string[];
}

// --- Quick add (§1) ---------------------------------------------------------

export type StartingLevel = "new_to_this" | "some_exposure" | "comfortable" | "strong_background";
export type AuthoringPreset = "narrow_adjunct";

export interface StudyMapBriefDto {
  outcome?: "general_learning" | "reference_mastery" | "exam_prep" | string;
  authoringPreset?: AuthoringPreset;
  level?: string;
  // Machine-readable learner level: seeds the global learner claim / initial
  // mastery. Defaults from the vault's profile/learner.yaml when unset.
  startingLevel?: StartingLevel;
  depth?: string;
  scope?: string;
  subject?: string;
  includeTopics?: string[];
  excludeTopics?: string[];
  notation?: string;
  // Bootstrap item authoring: "as_you_read" authors NO practice items at
  // synthesis; items accrue progressively from reading. Backend default: upfront.
  practiceItems?: "upfront" | "as_you_read";
  // exam-prep goal fields (createGoal path)
  goalTitle?: string;
  intentSentence?: string;
  targetRecall?: number;
  dueAt?: string;
  examItemCount?: number;
  [key: string]: unknown;
}

// Learner-initiated re-runging (easier/harder sibling variants).
export interface RungVariantRequestDto {
  requestId: string;
  sourcePracticeItemId: string;
  learningObjectId: string;
  direction: "easier" | "harder";
  sourceWaypoint: string;
  targetWaypoint: string;
  status: "pending" | "generating" | "applied" | "review_required" | "failed";
  createdPracticeItemId: string | null;
  failureReason: string | null;
  batchId: string | null;
}

/** Result of keeping an administered diagnostic probe as an ordinary practice
 *  item (a new item; the probe stays retired with its history intact). */
export interface ProbeRemintResultDto {
  version?: number;
  practiceItemId: string;
  sourcePracticeItemId: string;
  attemptId: string;
  practiceMode: string;
  learningObjectId: string;
  created: boolean;
}

export interface RungVariantRequestResultDto {
  version?: number;
  requestId: string;
  direction: "easier" | "harder";
  sourceWaypoint: string;
  targetWaypoint: string;
  attemptId: string;
  learningObjectId: string;
  batchId: string;
}

export interface LearnerProfileDto {
  version: number;
  startingLevel: StartingLevel | null;
  levelNote: string | null;
  updatedAt: string | null;
}

export interface PlanQuickAddInput {
  source: string;
  subjectId?: string | null;
  brief?: StudyMapBriefDto;
}

export interface ConfirmQuickAddInput {
  captureId?: string;
  readerEnabled?: boolean | null;
  source: string;
  subjectId: string;
  brief?: StudyMapBriefDto;
  roleOverride?: string | null;
  inventoryOutputTokens?: number;
  unlimitedTokenBudget?: boolean;
}

export interface ProposeFacetMergeInput {
  subjectId: string;
  retiredFacetId: string;
  survivingFacetId: string;
  rationale?: string | null;
  needId?: string | null;
}

export interface QuickAddConsentDto {
  kind: string;
  stage: string;
  reason?: string;
  provider?: string;
  /** UX Phase 1: the learner already said OK to this provider once (with its date). */
  granted?: boolean;
  grantedAt?: string | null;
  [key: string]: unknown;
}

export interface QuickAddConfirmationDto {
  id: string;
  title: string;
  source: string;
  normalizedUri: string;
  suggestedRole: string;
  roleAmbiguous: boolean;
  selectedUnitIds: string[];
  selectedUnitLabels: string[];
  selectedUnitCount: number;
  selectedTokens: number;
  wholeSource: boolean;
  estimatedInputTokens: number;
  estimatedCalls: number | null;
  externalAiConsent: QuickAddConsentDto[];
  requiresExternalAi: boolean;
}

export interface QuickAddPlanDto {
  source: string;
  normalizedUri: string;
  category: string | null;
  subjectId: string | null;
  sourceId: string;
  revisionId: string;
  extractionId: string;
  sourceSetId: string;
  title: string;
  suggestedRole: string;
  roleAmbiguous: boolean;
  selectedUnitIds: string[];
  selectedUnitLabels: string[];
  selectedTokens: number;
  outlineTokens: number;
  wholeSource: boolean;
  brief: StudyMapBriefDto;
  tokenEstimate: BuildPlan;
  externalAiConsent: QuickAddConsentDto[];
  confirmation: QuickAddConfirmationDto;
}

export interface QuickAddResultDto {
  batchId: string;
  sourceSetId: string;
  subjectId: string;
  role: string;
  selectedUnitIds: string[];
}

// --- Open in source (§9.2) --------------------------------------------------

export interface SpanViewInput {
  extractionId: string;
  spanId: string;
  context?: string;
  entityType?: string | null;
  entityId?: string | null;
}

export interface SpanNeighborDto {
  spanId: string;
  blockType: string;
  page: number | null;
  ordinal: number;
  text: string;
  truncated: boolean;
}

export interface SpanViewDto {
  extractionId: string;
  spanId: string;
  sourceId: string | null;
  revisionId: string | null;
  originalUri: string | null;
  canonicalUri: string | null;
  acquisitionKind: string | null;
  viewerMode: "pdf_page" | "pdf_text" | "text_anchor";
  blockType: string;
  page: number | null;
  bbox: number[] | null;
  polygon: number[][] | null;
  sectionPath: string[];
  text: string;
  locator: string;
  locatorScheme: string;
  pageRender: string | null;
  pageRenderSize: number[] | null;
  pageSpans: { spanId: string; bbox: number[] | null; polygon: number[][] | null }[];
  previousSpans: SpanNeighborDto[];
  nextSpans: SpanNeighborDto[];
  entityType: string | null;
  entityId: string | null;
  exposureEventId: string | null;
}

// --- Registry review (§5.7) -------------------------------------------------

export interface FacetContractCardDto {
  facetId: string;
  title: string | null;
  conceptId: string | null;
  kind: string | null;
  claim: string | null;
  conditions: { preconditions: string[]; postconditions: string[]; applicability: string[] };
  examples: { positive: string[]; negative: string[] };
  nonGoals: string[];
  errorSignatures: string[];
  instructionalRepairs: string[];
  status: string;
  version: number;
}

export interface IdentifiabilityWarningDto {
  id: string | null;
  kind: string;
  targetKey: string;
  missingCapability: string;
  facetIds: string[];
  detail: string | null;
  status: string;
}

/** Meas §D1: independent measurement dimensions the pool can resolve, against
 *  facets declared. Two facets observed by exactly the same set of criteria and
 *  items are ONE dimension; a facet observed by nothing is none at all — hence
 *  the deficit split. Analysis only: publishing it merges nothing, the
 *  `collapsedGroups` are review candidates for `proposeFacetMerge`. */
export interface MeasurementRankDto {
  facetsDeclared: number;
  independentDimensions: number;
  measurementRank: number;
  rankRatio: number | null;
  deficit: number;
  deficitFromUnobserved: number;
  deficitFromCollapse: number;
  unobservedFacets: string[];
  collapsedGroups: string[][];
}

export interface SubjectRegistryDto {
  version?: number;
  subjectId: string;
  facets: FacetContractCardDto[];
  identifiabilityWarnings: IdentifiabilityWarningDto[];
  facetCount: number;
  measurementRank?: MeasurementRankDto;
  /** Rewords of this subject's facets waiting for the owner's one-tap confirm. */
  rewordConfirms?: FacetRewordConfirmDto[];
}

/** The result of `decideFacetReword`: applied (confirmed, with an undo) or kept. */
export interface FacetRewordDecisionDto {
  version: number;
  status: "applied" | "kept";
  actionId: string;
  facetId: string;
  ownerJudgmentId: string;
  action: FacetIdentityActionDto | null;
}

/** The owner's merge applies live (facet locks were removed); undo it with
 *  `undoFacetIdentityAction(actionId)`. */
export interface FacetMergeResultDto {
  status: "applied";
  actionId: string;
  /** The CLI form of the undo. */
  undo: string;
  action: FacetIdentityActionDto | null;
  retiredFacetId: string;
  survivingFacetId: string;
  needId: string | null;
  resolvedNeed: boolean;
}

export interface AcquisitionPreviewItem {
  input: string;
  recognized: boolean;
  category: string | null;
  normalizedUri: string | null;
  error: string | null;
  isLocal: boolean;
  fileSizeBytes: number | null;
  remoteMetadata: Record<string, unknown> | null;
  duplicateOfInput: string | null;
  existingSourceId: string | null;
  existingRevisionCount: number;
  configuredExtractor: string | null;
  potentialExternal: Record<string, unknown>[];
  /** GLM-OCR text recognition: pages x a per-page token estimate at the configured price. */
  extractionEstimate?: {
    pages: number | null;
    totalTokens: number | null;
    tokensPerPage: number;
    estimatedUsd: number | null;
    backend: "api" | "local";
    basis: string;
  } | null;
}

export interface AcquisitionPreview {
  version?: number;
  items: AcquisitionPreviewItem[];
  summary: {
    inputCount: number;
    recognizedCount: number;
    duplicateCount: number;
    existingCount: number;
    needsConsentCount: number;
  };
}

export interface BuildPlanStage {
  stage: string;
  calls: number;
  inputTokens: number;
  cachedTokens: number;
  maxOutputTokens: number;
  ceiling: number;
  exceedsCeiling: boolean;
}

export interface BuildPlanSource {
  extractionId: string;
  revisionId: string | null;
  sourceId: string | null;
  title: string;
  assetHash: string | null;
  extractionResultHash: string | null;
  selectedUnitIds: string[];
  selectedUnitCount: number;
  cachedInventoryCount: number;
  approxTokens: number;
  warnings: string[];
}

export interface BuildPlan {
  version?: number;
  routing: "create" | "update";
  subjectId: string | null;
  provider: string;
  providerContextTokens: number | null;
  providerMaxOutputTokens: number | null;
  sources: BuildPlanSource[];
  stages: BuildPlanStage[];
  warnings: string[];
  totals: {
    selectedUnitCount: number;
    inputTokens: number;
    maxOutputTokens: number;
    calls: number;
    cacheSavingsTokens: number;
  };
  whatWillBeCreated: {
    sources: number;
    selectedUnits: number;
    routing: string;
    subjectId: string | null;
  };
}

export interface BuildPlanSelectionInput {
  extractionId: string;
  selectedUnitIds?: string[];
}

export interface ExtractionRepairConsent {
  provider: string;
  purpose: string;
  pages?: unknown[];
  cached?: boolean;
  external?: boolean;
}

export interface StartExtractionRepairInput {
  revisionId: string;
  pages: unknown[];
  consent: ExtractionRepairConsent;
  repairOptions?: Record<string, unknown>;
  parentExtractionId?: string | null;
  subjectId?: string | null;
}

export interface ConceptGraphLearningObject {
  id: string;
  title: string;
  mastery: number | null;
}

export interface ConceptGraphNode {
  id: string;
  title: string;
  type: string;
  aliases: string[];
  description: string | null;
  learningObjects: ConceptGraphLearningObject[];
  practiceItemCount: number;
  openErrorEventCount: number;
}

export interface ConceptGraphEdge {
  id: string;
  source: string;
  target: string;
  relationType: string;
  strength: number;
}

export interface ConceptGraphSnapshot {
  version: number;
  subjects: string[];
  concepts: ConceptGraphNode[];
  edges: ConceptGraphEdge[];
  counts: { concepts: number; edges: number; misconceptions: number };
}

export interface VaultTreeNode {
  type: "dir" | "file";
  name: string;
  path: string;
  kind?: string;
  children?: VaultTreeNode[];
}

export interface VaultTreeSnapshot {
  version: number;
  root: string;
  tree: VaultTreeNode[];
}

export interface VaultFileContent {
  version: number;
  path: string;
  name: string;
  kind: string;
  size: number;
  editable: boolean;
  binary: boolean;
  truncated: boolean;
  // True for SQLite databases — the viewer routes these to the table browser /
  // SQL console instead of rendering a text body.
  database?: boolean;
  body: string | null;
}

// ── SQLite browser / console ──────────────────────────────────────────────
export interface SqliteTableInfo {
  name: string;
  rowCount: number;
}

export interface SqliteTablesSnapshot {
  version: number;
  path: string;
  tables: SqliteTableInfo[];
}

export interface SqliteColumn {
  name: string;
  type: string;
  pk: boolean;
  notnull: boolean;
}

// `cells` align by index to `columns`. `rowid` addresses the row for edits/deletes
// (null when the table is WITHOUT ROWID, in which case `editable` is false).
export interface SqliteRow {
  rowid: number | null;
  cells: Array<string | number | boolean | null>;
}

export interface SqliteTableSnapshot {
  version: number;
  path: string;
  table: string;
  columns: SqliteColumn[];
  primaryKey: string[];
  rowCount: number;
  editable: boolean;
  rows: SqliteRow[];
}

export type SqliteExecResult =
  | { version: number; kind: "rows"; columns: string[]; rows: Array<Array<string | number | boolean | null>>; truncated: boolean }
  | { version: number; kind: "write"; rowsAffected: number; lastInsertRowId: number | null };

export type ProposalDecision = "pending" | "accepted" | "rejected";
export type ProposalReviewRoute = "auto_apply" | "review_required" | "reject";

export interface ProposalSourceRefDto {
  label: string;
  kind: string;
  refId: string | null;
}

export interface ProposalItemDto {
  id: string;
  clientItemId: string | null;
  itemType: string;
  operation: string;
  decision: ProposalDecision;
  proposedEntityId: string;
  targetEntityType: string | null;
  targetEntityId: string | null;
  reviewRoute: ProposalReviewRoute;
  validationStatus: "valid" | "warning" | "invalid";
  validationErrors: string[];
  edited: boolean;
  applied: boolean;
  rationale: string;
  sourceRefs: ProposalSourceRefDto[];
  payloadLines: Array<[string, string]>;
  // Raw payload as a JSON string (snake_case field names preserved) — the source
  // the Library payload editor reads and writes back.
  payloadJson: string;
  /** A facet reword this accepted item holds for the owner's confirm, and its state. */
  rewordConfirm?: FacetRewordConfirmDto["status"] | null;
}

export interface ProposalAgentRunDto {
  id: string;
  model: string | null;
  provider: string | null;
  purpose: string | null;
  codexRevision: string | null;
  startedAt: IsoTimestamp | null;
  completedAt: IsoTimestamp | null;
  status: string | null;
  durationS: number | null;
}

export interface ProposalDecisionCounts {
  pending: number;
  accepted: number;
  rejected: number;
}

export interface ProposalBatchDto {
  id: string;
  summary: string | null;
  purpose: string | null;
  status: string;
  createdAt: IsoTimestamp | null;
  updatedAt: IsoTimestamp | null;
  agentRun: ProposalAgentRunDto;
  counts: ProposalDecisionCounts;
  items: ProposalItemDto[];
}

export interface ProposalsSnapshot {
  version: number;
  batches: ProposalBatchDto[];
  totals: ProposalDecisionCounts;
  batchCount: number;
  /** Rewords accepted proposals hold for the owner's one-tap confirm. */
  rewordConfirms?: FacetRewordConfirmDto[];
}

// ── entity provenance (source lineage read-only panel) ───────────────────────

/** One resolved source link for an entity: which source/revision, where in it
 *  (locator), the relation, and whether the link has gone stale. */
export interface EntitySourceLink {
  id: string;
  sourceId: string | null;
  revisionId: string | null;
  locator: string | null;
  locatorScheme: string | null;
  relation: string | null;
  extractionId: string | null;
  assetHash: string | null;
  spanHash: string | null;
  status: string | null;
  stale: boolean;
}

/** A recorded disagreement between two source spans about a statement. */
export interface SourceConflictRef {
  id: string;
  statement: string | null;
  status: string | null;
  leftSourceId: string | null;
  leftLocator: string | null;
  rightSourceId: string | null;
  rightLocator: string | null;
}

/** A canonical ↔ alternate notation mapping recorded for the entity. */
export interface NotationMappingRef {
  id: string;
  canonicalNotation: string | null;
  alternateNotation: string | null;
  context: string | null;
  status: string | null;
}

/** The synthesis run / proposal that introduced the entity. */
export interface IntroducedBy {
  synthesisRunId: string | null;
  mode: string | null;
  agentRunId: string | null;
  proposalId: string | null;
  manifestId: string | null;
  manifestHash: string | null;
}

export interface EntityProvenance {
  entityType: string;
  entityId: string;
  semanticSources: EntitySourceLink[];
  assessmentAlignmentSources: EntitySourceLink[];
  semanticAuthority: EntitySourceLink | null;
  staleLinks: EntitySourceLink[];
  conflicts: SourceConflictRef[];
  notationMappings: NotationMappingRef[];
  introducedBy: IntroducedBy | null;
  hasProvenance: boolean;
}

// ── goals + practice exams (goal redesign phases 3-4) ────────────────────────

export interface GoalPaceDto {
  attemptsPerDay: number;
  attemptsLast14d: number;
  daysLeft: number | null;
  attemptsRemaining: number | null;
  neededPerDay: number | null;
  onPace: boolean | null;
  attemptsLogged: number;
  paceKind: "activity" | "qualifying";
}

export interface GoalLatestExamDto {
  score: number | null;
  completedAt: string | null;
}

export interface GoalReportSummaryDto {
  onTrackCount: number;
  total: number;
  onTrackFraction: number | null;
  atRiskCount: number;
  horizon: string;
  dueAt: string | null;
  // Dual-axis fields (attainment vs certification); optional so a stale
  // sidecar degrades to the legacy on-track rendering.
  certifiedCount?: number;
  examinedCount?: number;
  attainmentFraction?: number | null;
  predictedRecallMean?: number | null;
  readyCurrentMean?: number | null;
  demonstratedCount?: number;
  modelCoverage?: { decayEstimated: number; heldFlat: number };
  attemptsRemaining?: number;
  attemptsRemainingIsPartial?: boolean;
  attemptsRemainingDetail?: {
    unreachable: number;
    noSupply: number;
    lowerBound: number;
  };
  pace?: GoalPaceDto | null;
  latestExam?: GoalLatestExamDto | null;
  // Spec §4.1/§6.3: ids of the current open issued forecast rows for this goal
  // (per kind). Renderer claims reference these; absent when no open row
  // exists. Read-only — rendering never issues a forecast.
  activeForecasts?: {
    decay?: { id: string; issuedAt: string };
    pace?: { id: string; issuedAt: string };
    plan?: { id: string; issuedAt: string };
  };
}

/** Meas §B2/§E2 provenance of a displayed facet number — how we came to believe
 *  it, orthogonal to the `unexamined | uncertain | known_gap | solid` bucket
 *  (which is *what* we believe, and the axis certification reads).
 *  `measured` = direct evidence over the mass gate; `inferred` = a pooled
 *  prediction with something real to pool from; `claimed` = learner-asserted and
 *  unverified; `unknown` = absence. Display only — never gate anything on it. */
export type MeasurementStateDto = "measured" | "inferred" | "claimed" | "unknown";

export interface GoalAtRiskFacetDto {
  learningObjectId: string;
  learningObjectTitle: string;
  facetId: string;
  label: "unexamined" | "uncertain" | "known_gap" | "solid";
  currentRecall: number | null;
  projectedRecall: number | null;
  predictedCurrent?: number;
  predictedAtHorizon?: number;
  /** Provenance of `predictedCurrent` / `predictedAtHorizon` / `ready`. */
  measurementState?: MeasurementStateDto;
  evidenceMass?: number;
  certified?: boolean;
  attemptsToCertify?: number | null;
  /** False means items may exist, but none observes the required capability. */
  certificationReachable?: boolean;
  /** The count is "at least this many", usually because retention is below target. */
  attemptsIsLowerBound?: boolean;
  // KM3 §9.5 dual-axis split. Ready = predicted ability (leads ambient
  // surfaces); Demonstrated = capability-matched direct evidence (leads goal /
  // certification surfaces). Never blended into one number.
  ready?: number;
  demonstrated?: boolean;
  requiredCapabilities?: string[];
  demonstratedCapabilities?: string[];
  demonstratedFromLegacyDefault?: boolean;
}

// -- KM3 §9.2 blueprint recipe projections (shared by the goal banner's
// "why not ready" and the LO-detail recipe tree / capability grid) ------------

export interface ComponentReadinessDto {
  facet: string;
  capability: string;
  modality: string;
  predictedRecall: number;
  gating: boolean;
}

export interface RecipeProjectionDto {
  recipeId: string;
  composition: string;
  successProbability: number;
  components: ComponentReadinessDto[];
  bottleneck: ComponentReadinessDto | null;
}

export interface BlueprintProjectionDto {
  blueprintId: string;
  weight: number;
  successProbability: number;
  bestRecipeId: string | null;
  recipes: RecipeProjectionDto[];
}

export interface LoReadinessDto {
  learningObjectId: string;
  hasBlueprints: boolean;
  readiness: number | null;
  blueprints: BlueprintProjectionDto[];
  bottleneck: ComponentReadinessDto | null;
}

export interface GoalDto {
  id: string;
  title: string;
  intentSentence: string | null;
  creationSource: "learner" | "source_ingestion" | "study_map" | "legacy";
  resolvedQuestSentence: string | null;
  questBasis: "explicit_intent" | "exam_goal" | "practice_goal" | "legacy_title" | null;
  status: "active" | "paused" | "completed" | "expired";
  priority: number;
  targetRecall: number;
  dueAt: string | null;
  facetScope: { concepts: string[]; facets: string[] };
  exam: { enabled: boolean; itemCount: number };
  /** Active, non-exam-reserved Practice Items in the goal's scope — the supply
   * the learner can actually practise. `null` when the sidecar could not
   * compute it; never read null as "no supply". */
  practicableItemCount: number | null;
  createdAt: string;
  updatedAt: string;
  report: GoalReportSummaryDto | null;
}

export interface GoalsListSnapshot {
  version: number;
  goals: GoalDto[];
}

export interface GoalReportSnapshot {
  version: number;
  goal: GoalDto;
  report: GoalReportSummaryDto & {
    atRisk: GoalAtRiskFacetDto[];
    // KM3 §9.2: per-LO blueprint readiness (keyed by LO id). Populated only for
    // blueprint-bearing LOs under mvp-0.7; the recipe tree / next-gap link here.
    blueprintReadiness?: Record<string, LoReadinessDto>;
  };
}

// -- KM3b §9.6 provenance UI DTOs ---------------------------------------------

export interface TraceTargetDto {
  facet: string;
  capability: string;
  role: string;
}

export interface TraceCriterionDto {
  criterionId: string;
  description: string;
  dependsOn: string[];
  pointsAwarded: number | null;
  pointsPossible: number;
  passed: boolean;
  assessable: boolean;
  firstError: boolean;
  // "demonstrated" = passed assessable branch; "first_error" = first localized
  // error; "not_judged" = unassessable descendant (never "wrong"); "partial".
  status: "demonstrated" | "first_error" | "not_judged" | "partial";
  targets: TraceTargetDto[];
}

export interface AttemptTraceDto {
  version: number;
  attemptId: string;
  practiceItemId: string;
  learningObjectId: string;
  hasDag: boolean;
  criteria: TraceCriterionDto[];
  demonstratedCount: number;
  firstErrorCount: number;
  notJudgedCount: number;
}

export interface CapabilityGridCellDto {
  facetId: string;
  capability: string;
  required: boolean;
  demonstrated: boolean;
  certificationCredit: number;
  directPositiveMass: number;
  directNegativeMass: number;
  ready: number;
  tested: boolean;
  /** Meas §B2 provenance of `ready` (facet-level, exactly as `ready` is). */
  measurementState?: MeasurementStateDto;
}

export interface CapabilityGridDto {
  learningObjectId: string;
  supported: boolean;
  facets: string[];
  capabilities: string[];
  cells: CapabilityGridCellDto[];
}

export interface CapabilityGridResult {
  version: number;
  grid: CapabilityGridDto;
  readiness: LoReadinessDto | null;
}

export interface DemonstratedTimelinePointDto {
  t: string;
  demonstrated: number;
  delta: number;
  kind: "observation" | "correction";
  isCorrection: boolean;
  attemptId: string;
  surfaceGroup: string;
  assisted: boolean;
  demonstratedCapabilities: string[];
  // B5 phase 2 (§5.1 per-observation receipt) — optional for older payloads.
  primed?: boolean;
  derivation?: ObservationDerivationDto[];
}

// B5 phase 2 (§5.1): one (facet, capability) cell's staged→banked receipt line.
export interface ObservationDerivationDto {
  capability: string;
  channel: "direct" | "embedded" | "assisted";
  rawCredit: number;
  cappedCredit: number;
  boundBy: string[];
}

// B5 phase 2 (§5.1): one capability slice pooled into the facet's recall belief.
export interface ReadyCapabilitySliceDto {
  capability: string;
  recallAlpha: number;
  recallBeta: number;
  recallMean: number;
  independentEvidenceMass: number;
}

// B5 phase 2 (§5.1): the Ready-sentence ingredients, template-rendered from ledger.
export interface ReadyDerivationDto {
  supported: boolean;
  pooledRecallMean: number;
  recallAlpha: number;
  recallBeta: number;
  independentEvidenceMass: number;
  directObservationCount: number;
  unassistedObservationCount: number;
  pooledCapabilities: ReadyCapabilitySliceDto[];
  lastEvidenceAt: string | null;
  daysSinceLastEvidence: number | null;
  algorithmVersion: string;
  notes: string[];
}

export interface FacetEvidenceTimelineDto {
  version: number;
  facetId: string;
  modelVersion: string;
  supported: boolean;
  demonstrated: number;
  points: DemonstratedTimelinePointDto[];
  countedToward: { learningObjectId: string; learningObjectTitle: string }[];
  // B5 phase 2 (§5.1 Ready derivation) — null on legacy vaults / older payloads.
  ready?: ReadyDerivationDto | null;
}

export interface GoalSeriesPointDto {
  at: string;
  onTrackCount: number;
  total: number;
  onTrackFraction: number | null;
  certifiedCount?: number;
  examinedCount?: number;
  attainmentFraction?: number | null;
  predictedRecallMean?: number | null;
  demonstratedCount: number;
  readyMean: number | null;
  projectedReadyMean: number | null;
  projection: boolean;
  decayEstimated: number;
  heldFlat: number;
}

export interface GoalSeriesSnapshot {
  version: number;
  goalId: string;
  series: GoalSeriesPointDto[];
}

export interface GoalFeasibilityInput {
  title?: string;
  intentSentence?: string | null;
  examEnabled?: boolean;
  targetRecall: number;
  dueAt?: string | null;
  concepts: string[];
  facets: string[];
}

/** An in-scope learning object with nothing authored to practise on it yet.
 *  Distinct from an uncovered concept: this one is fillable, and
 *  `generateStarterPractice` is the action that fills it. */
export interface GoalMaterialGap {
  learningObjectId: string;
  title: string;
  conceptId: string;
  scopeFacetCount: number;
}

export interface GoalFeasibilityResult {
  version: number;
  scopeFacetCount: number;
  onTrackCount: number;
  projectedOnTrackFraction: number | null;
  uncoveredConcepts: string[];
  materialGaps: GoalMaterialGap[];
  resolvedQuestSentence: string | null;
  questBasis: GoalDto["questBasis"];
}

export interface GenerateStarterPracticeResult {
  version: number;
  batchId: string;
  batch: IngestBatchDto | null;
  learningObjectIds: string[];
}

/** Result of enqueueing authoring for the commissioning queue's gaps.
 *  `batchId` is null exactly when there was nothing to author — an empty
 *  commissioning queue is success, not failure, so it is not an error arm. */
export interface GenerateCommissioningPracticeResult {
  version: number;
  batchId: string | null;
  batch: IngestBatchDto | null;
  learningObjectIds: string[];
  /** Authorable contract cells covered by this run. */
  commissionableCellCount: number;
  /** Cells the queue holds but generation cannot close (coordination depth
   *  envelopes, downward dominance, blueprint repair). Reported so the button
   *  never implies it closed obligations it did not. */
  deferredCellCount: number;
}

/** Counts behind the nav-tab badges. Deliberately its own cheap call rather
 *  than a field on `AppSnapshot`: the file watcher re-embeds a whole snapshot on
 *  every vault change, and badge counts should not make unrelated edits pay. */
export interface ReviewCountsDto {
  version: number;
  pendingProposals: number;
  unreviewedProbeCandidates: number;
  openSourceConflicts: number;
  actionNeededNotices: number;
  pendingClarifications: number;
  /** Rollups the nav renders directly, computed sidecar-side so the two
   *  surfaces cannot drift on what a badge counts. */
  proposalsBadge: number;
  maintainBadge: number;
}

export interface CreateGoalInput {
  title: string;
  intentSentence?: string | null;
  targetRecall: number;
  dueAt?: string | null;
  concepts: string[];
  facets: string[];
  examEnabled: boolean;
  examItemCount?: number;
  populatePractice?: boolean;
  /** Opt out of the resolved-scope guard: create a goal that tracks nothing,
   *  as a stated intent rather than a silent default. */
  allowEmptyScope?: boolean;
}

export interface CreateGoalResult {
  version: number;
  goal: GoalDto;
  populationBatch?: IngestBatchDto | null;
}

// ── calibration sessions (probe redesign §5.9) ───────────────────────────────

export type CalibrationSessionStatus = "active" | "completed" | "stopped" | "expired";

export interface CalibrationEpisodeDto {
  episodeId: string;
  learningObjectId: string;
  /** Probe episode status: in_progress | complete | converted_to_tutoring | abandoned | … */
  status: string;
  qualifyingObservations: number;
  maximumObservations: number;
}

/** The adaptively-selected next block target (null once nothing is runnable). */
export interface CalibrationNextTargetDto {
  /** Null for a quick check, which serves ordinary items outside any episode. */
  episodeId: string | null;
  learningObjectId: string;
  practiceItemId: string;
  selectionObjective: string;
  /** Episode posterior entropy (nats), null before any posterior exists. */
  entropy: number | null;
}

export interface StartCalibrationSessionInput {
  sessionId: string;
  goalId?: string | null;
  learningObjectIds?: string[] | null;
  timeBudgetMinutes?: number | null;
}

export interface CalibrationSessionProgressDto {
  version: number;
  calibrationSessionId: string;
  sessionId: string;
  goalId: string | null;
  status: CalibrationSessionStatus;
  timeBudgetMinutes: number;
  elapsedMinutes: number;
  remainingMinutes: number;
  blocksCompleted: number;
  blocksPlanned: number;
  episodes: CalibrationEpisodeDto[];
  nextTarget: CalibrationNextTargetDto | null;
  /** Present only for "Check what I already know" (learner field F2). */
  quickCheck?: QuickCheckProgressDto;
}

/** The optional quick check: at most `k` answers; results are withheld (null)
 *  until it ends, then list each LO's verdict and the answers given. */
export interface QuickCheckProgressDto {
  learningObjectIds: string[];
  k: number;
  answered: number;
  remaining: number;
  finished: boolean;
  results: QuickCheckResultDto[] | null;
}

export interface QuickCheckResultDto {
  learningObjectId: string;
  learningObjectTitle: string;
  verdict: "assumed" | "learning" | "undecided" | "already_assumed";
  assumptionId: string | null;
  answers: Array<{
    attemptId: string;
    practiceItemId: string;
    learningObjectId: string;
    correctness: number | null;
    createdAt: IsoTimestamp;
  }>;
}

// ── dialogue microprobes (probe redesign §8.1) ───────────────────────────────

/** One committed dialogue turn: an ephemeral instance + served presentation.
 *  The learner's answer is submitted through the ordinary submit_attempt with
 *  attemptType "diagnostic_probe" and this presentationId. */
export interface DialogueTurnDto {
  /** commit | reason | counterfactual | counterexample */
  kind: string;
  practiceItemId: string;
  presentationId: string;
  promptMd: string;
  turnNumber: number;
  plannedTurns: number;
}

export interface BeginProbeDialogueResult {
  version: number;
  /** Opaque DialogueBlockState JSON — round-trip it through every call. */
  dialogueState: string;
  plannedTurns: number;
}

export interface NextProbeDialogueTurnResult {
  version: number;
  dialogueState: string;
  /** null once the block's planned turns are exhausted. */
  turn: DialogueTurnDto | null;
}

export interface RecordProbeDialogueTurnResult {
  version: number;
  dialogueState: string;
  blockComplete: boolean;
}

export interface EndProbeDialogueResult {
  version: number;
  ended: boolean;
  /** §5.7 block-end payload: released feedback, completion, and the route. */
  blockEnd: ProbeBlockEndDto | null;
}

export interface ExamStatusSnapshot {
  version: number;
  goalId: string;
  inWindow: boolean;
  daysUntilDue: number | null;
  pastDueGrace: boolean;
  existingSessionId: string | null;
  poolItemCount: number;
  uncoveredFacets: string[];
  /** The held-out pool could not be reserved yet — there is not enough material
   *  to hold one out of. The read self-heals: it retries the reservation. */
  reservationDeferred: boolean;
  /** How many items *could* be reserved once coverage exists. */
  reservableCandidateCount: number;
}

export interface ExamItemDto {
  practiceItemId: string;
  index: number;
  total: number;
  prompt: string;
  /** The SAME payload `PracticeItemDetail` carries, from the same serializer.
   *  Exams had their own prompt-only shape, which is why an error hunt served in
   *  exam mode would have stayed solution-less even after practice was fixed. */
  presentation: ItemPresentationDto;
  practiceMode: string;
}

export interface ExamSessionSnapshot {
  version: number;
  sessionId: string;
  goalId: string;
  status: "in_progress" | "completed" | "abandoned";
  items: ExamItemDto[];
  /** Submitted answers advance the cursor immediately, before grading finishes. */
  answeredItemIds: string[];
  gradedItemIds: string[];
  pendingItemIds: string[];
}

export interface ExamAnswerResult {
  version: number;
  sessionId: string;
  practiceItemId: string;
  accepted: boolean;
  gradingStatus: "pending" | "completed";
}

export interface ExamFacetOutcomeDto {
  facetId: string;
  learningObjectId: string;
  predictedRecall: number | null;
  observedCorrectness: number | null;
}

/** The learner-facing slice of a validated repair suggestion. Internal ids
 *  (validator id, checkpoint ids, structural refs) are deliberately absent —
 *  they are audit structure, not review material. */
export interface ExamItemRepairDto {
  rationale: string;
  practiceMode: string;
  learningObjectId: string | null;
  operator: string | null;
  expectedMinutes: number | null;
  repairedTrace: RepairedTraceDto | null;
}

/** Post-sitting only. `finish_exam` is the sole producer of this shape, so
 *  nothing here can reach a learner mid-exam. Derived from the durable
 *  `exam_answers` rows, which means sessions completed before these fields
 *  existed review just as well as fresh ones. */
export interface ExamItemOutcomeDto {
  practiceItemId: string;
  predictedCorrectness: number | null;
  observedCorrectness: number | null;
  /** The question as the learner was given it (the graded contract's
   *  statement and required-method instruction for a method item). */
  prompt: string | null;
  /** Method-explicit-3 review F3: the presentation of the question this
   *  answer was given, when it differs from the item's own (a required method
   *  set, renamed or cleared since); null when the item's presentation is it. */
  presentation?: ItemPresentationDto | null;
  answerMd: string | null;
  rubricScore: number | null;
  maxPoints: number | null;
  feedbackMd: string | null;
  repairSuggestions: ExamItemRepairDto[];
}

export interface ExamReportSnapshot {
  version: number;
  sessionId: string;
  goalId: string;
  scoreFraction: number | null;
  predictedScoreFraction: number | null;
  brier: number | null;
  perFacet: ExamFacetOutcomeDto[];
  itemOutcomes: ExamItemOutcomeDto[];
}

// --- ING M7: Update study map (append reconciliation, §10-§11, §15) ---------

export interface StudyMapDiffDto {
  newFacets: string[];
  removedFacets: string[];
  newLinks: number;
  newConflicts: number;
  newNotations: number;
  staleLinksRepaired: number;
  blueprintDistributionShift: Array<Record<string, unknown>>;
  hasChanges: boolean;
}

export interface MergeReviewProposalDto {
  leftFacetId: string;
  rightFacetId: string;
  similarity: number;
  reason: string;
  action: string;
}

export interface AppendResultDto {
  sourceSetId: string;
  subjectId: string;
  changeKind: string;
  manifestHash: string;
  synthesisRunId: string | null;
  proposalId: string | null;
  reused: boolean;
  autoAppliedItemIds: string[];
  reviewItemIds: string[];
  itemCounts: Record<string, number>;
  gateDiagnostics: Record<string, unknown>[];
  neighborhood: Record<string, unknown>;
  spanRequestCount: number;
  studyMapDiff: Partial<StudyMapDiffDto>;
  mergeReviewProposals: MergeReviewProposalDto[];
}

export interface AppendSourceInput {
  sourceSetId: string;
  newRevisionIds?: string[] | null;
  changeKind?: string;
  brief?: Record<string, unknown>;
  autoApply?: boolean;
  unlimitedTokenBudget?: boolean;
}

export interface RefreshResultDto {
  sourceId: string;
  oldRevisionId: string;
  newRevisionId: string;
  membershipAdvanced: boolean;
  unchangedLinks: string[];
  reanchoredLinks: string[];
  staleLinks: string[];
  needsReanchorLinks: string[];
  affectedEntities: Array<{ entityType: string; entityId: string }>;
  appendResult: AppendResultDto | null;
}

export interface RefreshRevisionInput {
  sourceSetId: string;
  sourceId: string;
  oldRevisionId: string;
  newRevisionId: string;
  newExtractionId?: string | null;
  confirm?: boolean;
}

export type MaintenanceSeverity = "info" | "warning" | "action_needed";

export interface MaintenanceNoticeDto {
  id: string;
  subjectId: string | null;
  noticeType: string;
  dedupKey: string;
  severity: MaintenanceSeverity;
  agingPolicy: "auto_resolution" | "auto_expiry" | "escalation";
  entityType: string | null;
  entityId: string | null;
  title: string;
  detail: Record<string, unknown> | null;
  action: { action?: string; label?: string } & Record<string, unknown>;
  status: string;
  snoozeCount: number;
  snoozedUntil: string | null;
  firstSeenAt: string;
  lastSeenAt: string;
}

export interface MaintenanceFeedSnapshot {
  version: number;
  notices: MaintenanceNoticeDto[];
}

// Stage 0–6 measurement / causal operational surface plus Stage 8.1's static
// inference precheck. Metric payloads keep
// availability explicit so the UI never renders "no data" as a zero.
export interface MeasurementMetricDto {
  name: string;
  availability: "available" | "no_data" | "no_producer" | "requires_replay" | "unmeasured";
  available: boolean;
  value: number | null;
  unit: string;
  numerator: number | null;
  denominator: number | null;
  denominatorLabel: string;
  note: string;
  detail: Record<string, unknown>;
}

export interface ReachabilityCellDto {
  learningObjectId: string;
  facetId: string;
  requiredCapability: string;
  verdict: string;
  remedy: string;
  integration: boolean;
}

export interface MeasurementHealthDto {
  version: number;
  scoreboard: {
    scoreboardVersion: string;
    metrics: MeasurementMetricDto[];
    available: number;
    availabilityCounts: Record<string, number>;
  };
  reachability: {
    version: number;
    summary: {
      cellCount: number;
      reachableCount: number;
      unreachableCount: number;
      reachableShare: number | null;
      counts: Record<string, number>;
      integrationCellCount: number;
      integrationReachableShare: number | null;
      facetsDeclared: number;
      facetsInstrumented: number;
    };
    cells: ReachabilityCellDto[];
  };
  /** Plan 8.1's read-only counterfactual. `cellsConverted` is the guaranteed
   *  static count; path-specific candidates stay separate until their path is
   *  actually exercised. */
  inferencePrecheck: {
    version: number;
    summary: {
      baseline: Record<string, unknown>;
      capabilityDominance: {
        cellsConverted: number;
        movesCount: boolean;
        shareOfUnreachable: number | null;
        shareOfAllCells: number | null;
        substitutableCells: number;
        integrationPredictionOnlyCells: number;
      };
      prerequisiteEntailment: {
        cellsConverted: number;
        movesCount: boolean;
        shareOfUnreachable: number | null;
        shareOfAllCells: number | null;
        substitutableCells: number;
        integrationPredictionOnlyCells: number;
        conditionalCells: number;
        maximumCellsConverted: number;
        maximumShareOfUnreachable: number | null;
        prerequisiteDeclarationCount: number;
        prerequisiteGraphEdgeCount: number;
        prerequisiteGraphEdgesUnreferenced: number;
        modalityCounts: Record<string, number>;
        dispositionCounts: Record<string, number>;
      };
      combined: {
        cellsConverted: number;
        maximumCellsConverted: number;
        movesCount: boolean;
        shareOfUnreachable: number | null;
        maximumShareOfUnreachable: number | null;
      };
    };
    dominanceCells: Array<Record<string, unknown>>;
    entailmentCells: Array<Record<string, unknown>>;
    prerequisiteAudit: Array<Record<string, unknown>>;
  };
  coldProbes: {
    coverage: {
      certificatesActive: number;
      certificatesUnmeasurable: number;
      certificatesUnscheduled: number;
    };
    falseCertificationRate: Record<string, unknown>;
    certificates: Array<{
      learningObjectId: string;
      probeStatus: string;
      unschedulableReason: string | null;
      verdict: string | null;
    }>;
  };
  missingVocabulary: {
    notes: number;
    attributions: number;
    abstentions: number;
    abstentionRate: number;
    uncapturedDiagnosticAbstentions: number;
    bySource: Record<string, number>;
  };
  causalHealth: {
    attempts: number;
    channels: Array<{
      channel: string;
      filled: number;
      missing: number;
      abstained: number;
      fillRate: number;
      tail: string;
    }>;
  };
  personaGate: MeasurementMetricDto;
  facetMintGate: {
    implementationStatus: "structural_proxy";
    originalSpecComplete: false;
    limitation: string;
    summary: {
      candidateCount: number;
      dispositions: Record<string, number>;
      reasons: Record<string, number>;
      aliases: Record<string, string[]>;
    };
    verdicts: Array<Record<string, unknown>>;
  };
  integrationBackfill: {
    summary: {
      integrationComponentCount: number;
      coordinationObserved: boolean;
      dispositions: Record<string, number>;
      learningObjects: number;
      owedCapstones: string[];
    };
    verdicts: Array<Record<string, unknown>>;
    previewEdits: Array<{
      learningObjectId: string;
      path: string;
      diff: string;
      applied: Array<Record<string, unknown>>;
    }>;
  };
  causalProbeReview: {
    openFactors: Array<{
      id: string;
      attemptId: string;
      candidateCauseCount: number;
      probeCandidateCount: number;
    }>;
    candidates: Array<{
      id: string;
      factorId: string;
      practiceItemId: string;
      status: string;
      blindInputContractValid: boolean;
      distinguishable: boolean;
      minimumMargin: number | null;
      reviewer: string | null;
      reviewReason: string | null;
    }>;
    pendingMachineChecks: Array<Record<string, unknown>>;
  };
  /** §3.A6 revert criterion: opportunistic credit concentrating on a handful of
   *  facets means the grader is pattern-matching the vocabulary rather than
   *  reading the work. `opportunisticConcentration` abstains (null) below a
   *  handful of observations rather than reporting 1.0 from a single row. */
  traceEvidence: {
    attemptsWithObservations: number;
    declaredObservations: number;
    opportunisticObservations: number;
    distinctOpportunisticFacets: number;
    opportunisticConcentration: number | null;
    topOpportunisticFacets: Array<{ facetId: string; count: number }>;
    unexercisedSupportingCells: Array<{
      facetId: string;
      capability: string;
      unexercisedSupportingMass: number;
      embeddedCertificationCredit: number;
      directCertificationCredit: number;
    }>;
    unexercisedSupportingCellCount: number;
  };
  /** §3.A8 revert criterion. `available: false` below the minimum denominator —
   *  a rate from a handful of attempts is noise, and must not render as 0%.
   *  `overThreshold` means machine-resident uncertainty is being misclassified
   *  as learner-resident and must be fixed machine-side. */
  clarificationRate: {
    available: boolean;
    unavailableReason?: string;
    rate?: number;
    gradeableAttempts: number;
    clarifications: number;
    answered?: number;
    threshold: number;
    overThreshold?: boolean;
  };
  instrumentAudit: InstrumentAuditDto;
}

/** Plan item 6.4: every Meas §3 instrument class's REVERT criterion, read by the
 *  same producers as `learnloop instrument-audit`. Each metric keeps its own
 *  availability arm — a rate over too little data is `no_data` with the counts
 *  visible, and must never render as 0. The companions travel alongside because
 *  a rejection rate of 0.4 over three profiled items says almost nothing, and a
 *  reader who cannot see the pool will read it as though it did. */
export interface InstrumentAuditDto {
  /** In fixed order: A2 laddered stems, A3 error hunts, A4 contrast pairs,
   *  A5 discrimination profiles. `detail.verdict` names the revert condition. */
  metrics: MeasurementMetricDto[];
  discriminationProfileCoverage: {
    practiceItems: number;
    itemsWithProfiles: number;
    profiles: number;
    profilesBySource: Record<string, number>;
    /** `authored` profiles are legitimate, but this is the arm A4 commissioning
     *  exists to replace: a registry-linked profile can be corroborated from
     *  evidence elsewhere in the vault, a freehand one cannot. */
    unlinkedAuthoredProfiles: number;
  };
  errorHuntOutcomes: {
    attempts: number;
    cleanSolutionAttempts: number;
    /** Null, not zero, with no attempts: §3.A3's "there is always an error"
     *  strategy returns the moment clean solutions stop being served, and a
     *  fabricated 0% would read as that failure rather than as no data. */
    cleanRotationShare: number | null;
    plantedTotal: number;
    plantedRepaired: number;
    plantedFoundNotRepaired: number;
    plantedMissed: number;
    falsePositiveReports: number;
    misconceptionCandidatesWritten: number;
    facetFailuresSuppressed: number;
  };
  /** A "stem" whose parts all sit at one capability is NOT a ladder — it is a
   *  set of near-clones on one stimulus, which is the instrument's failure mode
   *  and looks identical to success in an item count. Hence `isLadder`. */
  ladderedStems: Array<{
    stemId: string;
    partIds: string[];
    capabilities: string[];
    unplacedParts: string[];
    columnsFilled: number;
    isLadder: boolean;
  }>;
  /** A4 commissioning queue: identifiability findings turned into authoring
   *  requests. Deferred findings stay IN the queue with a typed reason. */
  contrastPairCommissioning: {
    version: number;
    summary: {
      queueLength: number;
      commissioned: number;
      deferred: number;
      dispositions: Record<string, number>;
    };
    requests: Array<{
      targetKey: string;
      check: string;
      detail: string;
      facetIds: string[];
      capability: string | null;
      disposition: string;
      queueRank: number;
      subjectId: string | null;
      why: string;
      reason?: string;
    }>;
  };
}

export type ConflictResolutionKind =
  | "prefer_for_context"
  | "keep_both_scoped"
  | "notation_mapping"
  | "dismiss";

export interface SourceConflictDto {
  id: string;
  subjectId: string | null;
  entityType: string;
  entityId: string;
  leftSourceId: string | null;
  leftRevisionId: string | null;
  leftLocator: string | null;
  leftExtractionId: string | null;
  /** The span to open on leftExtractionId (re-read safety: the reading the
   *  span was cited on, or its exact match on the current one); null when
   *  its reading is unknown. Absent from older sidecars. */
  leftSpanId?: string | null;
  rightSourceId: string | null;
  rightRevisionId: string | null;
  rightLocator: string | null;
  rightExtractionId: string | null;
  rightSpanId?: string | null;
  statement: string;
  status: string;
  resolution: Record<string, unknown> | null;
  resolutions?: Array<Record<string, unknown>>;
  createdAt: string;
  resolvedAt: string | null;
}

export interface ResolveConflictInput {
  conflictId: string;
  resolutionKind: ConflictResolutionKind;
  resolution?: Record<string, unknown>;
  rationale?: string | null;
}

export interface FacetCapabilityStateDto {
  facet: string;
  capability: string;
  demonstrated: boolean;
  certificationCredit: number;
  recallMean: number;
}

/** ING M8: analytic predicted score distribution for a task family. */
export interface PredictedScoreDto {
  mean: number;
  variance: number;
  std: number;
  nItems: number;
}

export interface TaskFamilyReadinessDto {
  taskFamily: string;
  weight: number;
  normalizedWeight: number;
  learningObjectIds: string[];
  ready: number | null;
  demonstratedFraction: number;
  facetCapabilities: FacetCapabilityStateDto[];
  calibration: { brier: number | null; sample: number } | null;
  predicted: PredictedScoreDto | null;
}

export interface ExamReadinessReportDto {
  subjectId: string | null;
  displayRule: "ready_vs_demonstrated";
  rows: TaskFamilyReadinessDto[];
  hasCalibration: boolean;
  /** ING M8: whole-exam predicted score distribution (mean/std) vs demonstrated
   *  fraction — reported side by side, never blended. */
  predictedScore: { mean: number; variance: number; std: number } | null;
  demonstratedScore: number | null;
}

// ── hypothesis surfaces / Review / remediation ─────────────────────────────

export type ClaimClass = "estimate" | "diagnosis" | "policy" | "ledger_fact";
export type ClaimTemperature = "hot" | "cold";

export interface ClaimCandidateDto {
  claimClass: ClaimClass;
  claimType: "ready_estimate" | "forecast" | "misconception" | "schedule_choice" | "regrade" | "session_delta" | string;
  claimRef: unknown;
  claimVersion: string;
  producerVersion: string;
  surface: string;
  temperature: ClaimTemperature;
  visibleAt?: string | null;
  coldReask?: boolean;
  claimText?: string | null;
  provenance?: string | null;
  receiptRef?: string | null;
}

export interface PresentedClaimDto extends ClaimCandidateDto {
  presentationId: string;
  affordancesEnabled: boolean;
  suppressionReason: string | null;
  debounced: boolean;
}

export interface HypothesisEventDto {
  id: string;
  createdAt: string;
  presentationId: string | null;
  eventType: "presented" | "responded" | "dismissed";
  claimClass: ClaimClass;
  claimType: string;
  claimRef: string;
  claimVersion: string;
  producerVersion: string;
  surface: string;
  temperature: ClaimTemperature;
  visibleAt: string | null;
  suppressionReason: string | null;
  responsePayload: Record<string, unknown> | null;
  sessionId: string | null;
  visitId: string | null;
}

export type BeliefWithdrawalReason =
  | "contradicted_by_trace"
  | "superseded"
  | "adjudicated"
  | "retired_misdiagnosed";

export interface ReviewChangelogEntryDto {
  id: string;
  kind: "session" | "recalibration" | "regrade" | "belief_withdrawn";
  at: string;
  attemptsRecorded: number;
  itemsReviewed: number;
  predictionsMoved: { up: number; down: number };
  facetIds: string[];
  corrections: number;
  facetsDemonstrated: number;
  misconceptionsTouched: { resolved: number; returned: number };
  // Present only on system-authored `regrade` entries (out-of-session
  // regrades): the persisted old→new rubric-point transition and its direction.
  direction?: "up" | "down" | "same";
  oldScore?: number;
  newScore?: number;
  // Present only on `recalibration` entries: the algorithm_version bump that
  // triggered the recompute (learner evidence unchanged).
  algorithmVersion?: string;
  previousAlgorithmVersion?: string;
  // Present only on `belief_withdrawn` entries (spec_diagnostic_augmentation_v1
  // §2 A6 — "the system must be able to say it was wrong"): a diagnosis the
  // learner was actually shown has been retired, and this names it in the words
  // they read. `claimTextSource` is an honesty marker: `as_shown` means the quote
  // came off the presentation record, `current_statement` means that record
  // predates capture and the live statement is standing in.
  beliefKind?: "misconception";
  beliefId?: string;
  learningObjectId?: string;
  withdrawnClaimText?: string;
  claimTextSource?: "as_shown" | "current_statement";
  withdrawalReason?: BeliefWithdrawalReason;
  statement?: string;
  disposition?: "demoted" | "superseded";
  surfacedAt?: string | null;
  surfacedOn?: string | null;
  // A successor belief is reported ALONGSIDE the withdrawal, never instead of it.
  replacementBeliefId?: string | null;
  replacementStatement?: string | null;
}

export interface WorkingHypothesisDto {
  id: string;
  learningObjectId: string;
  statement: string;
  correctionStatement: string;
  mechanism: string | null;
  targetFacet: string | null;
  confusedWithFacet: string | null;
  status: string;
  history: Array<{ id: string; at: string; fromStatus: string | null; toStatus: string; label: string }>;
  severity: number;
}

export interface ReviewLogDto {
  version: number;
  changelog: ReviewChangelogEntryDto[];
  workingHypotheses: WorkingHypothesisDto[];
}

export interface RemediationEpisodeDto {
  id: string;
  caseKind: "misconception" | "diagnosis";
  caseRef: string;
  state: string;
  passagesShown: Array<{ role: string; facetId: string; spanView: SpanViewDto }>;
  primedItemId: string | null;
  coldItemId: string | null;
  primedAttemptId: string | null;
  coldAttemptId: string | null;
  createdAt: string;
  updatedAt: string;
  completedAt: string | null;
}

export interface RemediationCaseDto {
  id: string;
  statement: string;
  correctionStatement: string | null;
  mechanism: string | null;
  targetFacet: string | null;
  confusedWithFacet: string | null;
  status: string;
  history: Array<{ id: string; at: string; label: string }>;
}

export interface RemediationDto {
  version: number;
  episode: RemediationEpisodeDto;
  case: RemediationCaseDto;
  primedItemId?: string;
  coldItemId?: string | null;
  /** Set (e.g. "no_independent_surface") when NO cold item could be paired:
   *  the repair cannot convert to Demonstrated credit and the UI must say so
   *  instead of promising a scheduled cold retry. */
  coldUnmeasurableReason?: string | null;
  practiceItem?: PracticeItemDetail;
}

/** `start_remediation` only. A causal hold is a *state*, not an error: the
 *  handler returns `episode: null` plus the typed §6 `repairStatus` so the
 *  learner sees the hold reason and its actions instead of an error toast. */
export interface StartRemediationDto {
  version: number;
  episode: RemediationEpisodeDto | null;
  case: RemediationCaseDto | null;
  repairStatus?: CausalRepairStatusDto | null;
  primedItemId?: string;
  coldItemId?: string | null;
  coldUnmeasurableReason?: string | null;
  practiceItem?: PracticeItemDetail;
}

export interface ForecastTrackRecordDto {
  version: number;
  trackRecord: {
    byKind: Record<string, { issued: number; resolved: number; censored: number; unobservable: number; meanAbsoluteError: number | null }>;
    forecasts: Array<Record<string, unknown>>;
  };
}

export interface CalibrationBinDto {
  lower: number;
  upper: number;
  count: number;
  meanPredicted: number | null;
  meanObserved: number | null;
}

export interface AnswerCalibrationReportDto {
  version: number;
  items: {
    n: number;
    brier: number | null;
    logLoss: number | null;
    bins: CalibrationBinDto[];
    minimumN: number;
    curveAvailable: boolean;
  };
  facets: {
    n: number;
    brier: number | null;
    logLoss: number | null;
    bins: CalibrationBinDto[];
    byFacet: Record<
      string,
      { n: number; meanProjected: number; meanObserved: number }
    >;
  };
  duel: {
    n: number;
    learnerBrier: number | null;
    modelBrier: number | null;
  };
}

// ── F5 overconfidence list (§4.3) ───────────────────────────────────────────

export interface OverconfidentFacetDto {
  learningObjectId: string;
  learningObjectTitle: string;
  facetId: string;
  ready: number;
  demonstrated: boolean;
  blueprintWeight: number;
  evidenceMass: number;
  score: number;
}

export interface OverconfidenceSnapshot {
  version: number;
  goalId: string;
  facets: OverconfidentFacetDto[];
}

export interface StartOverconfidenceProbeResult {
  version: number;
  episodeId: string;
  learningObjectId: string;
  status: string;
}

// ── F7 welcome-back diff (§4.4) ─────────────────────────────────────────────

export interface ReentrySlippedFacetDto {
  learningObjectId: string;
  learningObjectTitle: string;
  facetId: string;
  blueprintWeight: number;
}

export interface ReentrySummaryDto {
  show: boolean;
  gapDays: number;
  thresholdDays: number;
  lastEndedAt: string | null;
  solidCount: number;
  slippedCount: number;
  refresherCount: number;
  slippedTop: ReentrySlippedFacetDto[];
}

export interface ReentrySummarySnapshot {
  version: number;
  summary: ReentrySummaryDto;
}

// ── F7 no-goal decay pressure (§4.5) ────────────────────────────────────────

export interface DecayPressureFacetDto {
  learningObjectId: string;
  learningObjectTitle: string;
  facetId: string;
  readyNow: number;
  crossesInDays: number | null;
  hasHistory: boolean;
}

export interface DecayPressureDto {
  hasHistory: boolean;
  facets: DecayPressureFacetDto[];
  heldFlatCount: number;
}

export interface DecayPressureSnapshot {
  version: number;
  pressure: DecayPressureDto;
}

// ── Graph / knowledge-map editor (spec §8 three graphs, §12 mutation contract) ─
//
// One write path: every user edit compiles to items in the existing proposals
// machinery (provider "user", purpose "graph_editor"). Preview endpoints are
// pure reads. Method names: proposeGraphEdits, queueRestructureRequest,
// resolveEdgeDirection, getFacetDetail, listFacets, previewKnowledgeMap,
// previewBlueprintReadiness.

export type GraphEditItemType =
  | "concept_edge"
  | "learning_object"
  | "task_blueprint"
  | "concept";

export type GraphEditOperation = "create" | "update" | "delete";

/** One edit in a graph-editor batch. `payload` is the edited entity in its
 *  on-disk YAML shape; `targetEntityId` is required for update/delete. */
export interface GraphEditInput {
  itemType: GraphEditItemType;
  operation: GraphEditOperation;
  payload: Record<string, unknown>;
  targetEntityId: string | null;
}

export interface ProposeGraphEditsInput {
  rationale: string;
  edits: GraphEditInput[];
}

/** The compact per-item receipt returned alongside the refreshed inbox. Note
 *  `operation` is the proposal-vocabulary operation — the editor's "delete"
 *  compiles to "deactivate". */
export interface GraphEditItemDto {
  id: string;
  clientItemId: string | null;
  itemType: string;
  operation: string;
  decision: ProposalDecision;
  validationStatus: "valid" | "warning" | "invalid";
  validationErrors: string[];
  targetEntityId: string | null;
}

/** propose_graph_edits: the refreshed proposals inbox (one new pending batch)
 *  plus this batch's id and its item receipts. */
export interface ProposeGraphEditsResult extends ProposalsSnapshot {
  batchId: string;
  items: GraphEditItemDto[];
}

export interface QueueRestructureRequestInput {
  facetIds: string[];
  requestedOperation: "merge" | "split";
  rationale: string;
}

/** A durable restructure request (there is no split endpoint yet — this only
 *  queues the request, surfaced in the maintenance feed). */
export interface RestructureRequestDto {
  needId: string;
  subjectId: string;
  facetIds: string[];
  requestedOperation: "merge" | "split";
  rationale: string;
  status: string;
}

export interface QueueRestructureRequestResult {
  version: number;
  request: RestructureRequestDto;
}

export type EdgeDirectionResolution = "keep" | "flip" | "retype_related" | "retire";

export interface ResolveEdgeDirectionInput {
  edgeId: string;
  resolution: EdgeDirectionResolution;
  rationale: string;
}

/** The outcome of resolving an ambiguous-direction notice. `keep` files no edit
 *  (`batchId` null, `filedEdit` false); the others compile a concept_edge edit.
 *  `resolvedNoticeIds` are the maintenance notices marked resolved. */
export interface EdgeDirectionResolutionDto {
  edgeId: string;
  resolution: EdgeDirectionResolution;
  batchId: string | null;
  filedEdit: boolean;
  items: GraphEditItemDto[];
  resolvedNoticeIds: string[];
}

/** resolve_edge_direction: the refreshed proposals inbox plus the resolution. */
export interface ResolveEdgeDirectionResult extends ProposalsSnapshot {
  resolution: EdgeDirectionResolutionDto;
}

// -- get_facet_detail (FacetInspector panel, §9.6) ---------------------------

export interface FacetDetailContractDto {
  id: string;
  title: string;
  kind: string;
  claim: string | null;
  preconditions: string[];
  positiveExamples: string[];
  negativeExamples: string[];
  nonGoals: string[];
  errorSignatures: string[];
  aliases: string[];
  status: string;
  /** Goes up by one with each reword (an applied change of the facet's meaning). */
  version: number;
}

/** One blueprint-recipe component that references the facet, across every LO. */
export interface FacetMembershipRowDto {
  learningObjectId: string;
  loTitle: string;
  blueprintId: string;
  recipeId: string;
  capability: string;
  modality: string;
  role: "all_of" | "any_of" | "integration";
}

export interface FacetCapabilityLedgerRowDto {
  capability: string;
  directPositiveMass: number;
  directNegativeMass: number;
  certificationCredit: number;
  /** capability-matched certification credit > 0. */
  demonstrated: boolean;
}

/** `ready` blends LO mastery with accrued facet recall evidence; `readyGhost`
 *  is the mastery-only prior (evidence removed). Both null when no LO exercises
 *  the facet. */
export interface FacetEvidenceDto {
  ready: number | null;
  readyGhost: number | null;
  evidenceMass: number;
  capabilityLedger: FacetCapabilityLedgerRowDto[];
}

export interface FacetDetailDto {
  version: number;
  facet: FacetDetailContractDto;
  /** Rewords (with the wording each replaced) and merges into this facet,
   *  newest first, each with its undo state. */
  history: FacetIdentityActionDto[];
  membership: FacetMembershipRowDto[];
  evidence: FacetEvidenceDto;
  /** LOs beyond the first that touch this facet (cross-links). */
  sharedWith: string[];
}

// -- list_facets (autocomplete pickers) --------------------------------------

export interface FacetSummaryDto {
  id: string;
  title: string;
  kind: string;
  status: string;
}

export interface FacetListDto {
  version: number;
  facets: FacetSummaryDto[];
}

// -- preview_knowledge_map (geometry displacement, §8 layer honesty) ----------

export interface PreviewEdgeInput {
  source: string;
  target: string;
  relationType: string;
}

export interface PreviewKnowledgeMapInput {
  addedEdges: PreviewEdgeInput[];
  removedEdgeIds: string[];
}

export interface KnowledgeMapPreviewPoint {
  id: string;
  x: number;
  y: number;
}

/** Recomputed item-map MDS against a hypothetical edge set, plus the unchanged
 *  `baseline` so the UI can draw displacement without a second call. */
export interface KnowledgeMapPreviewDto {
  version: number;
  points: KnowledgeMapPreviewPoint[];
  stress: number;
  baseline: { points: KnowledgeMapPreviewPoint[]; stress: number };
}

// -- preview_blueprint_readiness (recipe-tree blast radius, §9.2) -------------

export interface PreviewBlueprintReadinessInput {
  learningObjectId: string;
  /** Edited blueprints in the LO YAML shape (list of blueprint dicts). */
  blueprints: Record<string, unknown>[];
}

/** `bottleneck` is the gating component of the best recipe (ComponentReadinessDto). */
export interface BlueprintReadinessSummaryDto {
  readiness: number | null;
  bottleneck: ComponentReadinessDto | null;
}

export interface BlueprintReadinessPreviewDto {
  version: number;
  current: BlueprintReadinessSummaryDto;
  proposed: BlueprintReadinessSummaryDto;
  identifiabilityWarnings: string[];
  affectedGoals: Array<{ goalId: string; title: string }>;
}

// -- Graph-editor maintenance notices ----------------------------------------
//
// MaintenanceNoticeDto.noticeType is an open string and `detail` is
// Record<string, unknown> | null, so these are not a closed union to extend.
// These interfaces type the `detail` payloads (produced by
// services/maintenance_feed.py) for the two graph-editor notice kinds; cast
// `notice.detail` to them when `noticeType` matches.

export type GraphEditorNoticeType = "ambiguous_edge_direction" | "restructure_request";

/** `detail` payload of an `ambiguous_edge_direction` notice. `evidence` is
 *  attempt-ordering stats on the target's items before vs after the first
 *  correct source attempt — null (omitted, never fabricated) on sparse data. */
export interface AmbiguousEdgeDirectionDetail {
  edgeId: string | null;
  reason: "bidirectional" | "cycle" | "proposed";
  relationType: string;
  sourceConcept: { id: string; title: string };
  targetConcept: { id: string; title: string };
  rationale: string | null;
  evidence: {
    firstCorrectSourceAt: string;
    targetSuccessBefore: number;
    targetSuccessAfter: number;
    targetAttemptsBefore: number;
    targetAttemptsAfter: number;
  } | null;
  resolutionOptions: EdgeDirectionResolution[];
  proposalItemId: string | null;
}

/** `detail` payload of a `restructure_request` notice (a queued split or merge request). */
export interface RestructureRequestDetail {
  facetIds: string[];
  operation: "merge" | "split";
  rationale: string | null;
}

// -- Raw on-disk blueprints (recipe-tree editor source shape) -----------------
//
// Exposed on LearningObjectDetail.blueprints so the recipe editor can seed and
// round-trip the EXACT on-disk recipe structure (all_of / any_of / integration
// / modality) — the readiness projection (LoReadinessDto) flattens these and
// drops the role distinction, so it cannot reconstruct the YAML shape. Keys are
// camelCased by the sidecar's to_camel; when filing edits back, the editor
// re-serializes to the snake_case YAML shape the write path expects.

/** Closed capability vocabulary (§7.2). */
export type RecipeCapability =
  | "retrieval"
  | "schema_interpretation"
  | "procedure_execution"
  | "method_selection"
  | "coordination";

/** Requirement modality (§8.2). */
export type RecipeModality =
  | "hard"
  | "path_specific"
  | "facilitating"
  | "instructional_order";

export interface RecipeComponentDto {
  facet: string;
  capability: string;
  modality: string;
}

export interface BlueprintRecipeDto {
  id: string;
  composition: string;
  allOf: RecipeComponentDto[];
  anyOf: RecipeComponentDto[];
  integration: RecipeComponentDto | null;
}

export interface LoBlueprintDto {
  id: string;
  weight: number;
  recipes: BlueprintRecipeDto[];
}

// ── NewVault wizard (create_vault) ───────────────────────────────────────────
// Backend RPC that scaffolds a fresh vault on disk (wraps init_vault) and, if a
// subject title is given, seeds a first subject. The frontend then re-selects
// and re-loads the vault so the whole app rebinds to it.
export interface CreateVaultInput {
  path: string;
  subject?: string | null;
  // Declared learner level: persists profile/learner.yaml and seeds the global
  // init-wizard learner claim at creation time.
  startingLevel?: StartingLevel | null;
  levelNote?: string | null;
}

export interface CreateVaultResult {
  version: number;
  vaultRoot: string;
  subjectId: string | null;
}

// ════════════════════════════════════════════════════════════════════════════
// P2 — narrow golden path (spec_p2_narrow_golden_path §9; spec_tauri_ui §3 rows)
//
// camelCase mirrors of the landed sidecar handler payloads (golden_path.* /
// blueprint.* / diagnostic.* / ladder.* / practice_pool.* / reader.*). Shapes
// captured verbatim from the real sidecar into src/fixtures/goldenpath/*.json.
// ════════════════════════════════════════════════════════════════════════════

/** Reliability-aware interval attached to every model-derived claim (§8.2). */
export interface GpInterval {
  point: number;
  low: number;
  high: number;
  width: number;
  leadingClass: string;
}

export type GpCalibrationStatus = "heuristic" | "simulation_validated" | "live_calibrated";
export type GpClaimLanguage = "provisional" | "calibrated" | "insufficient";

/** blueprint.get_version / register / review. */
export interface BlueprintExemplarDto {
  id: string;
  blueprintVersionId: string;
  exemplarRef: string;
  weight: number;
  heldOutWeight: number;
  exposureStatus: string;
  createdAt: string;
}
export interface BlueprintVersionDto {
  version: number;
  blueprintId: string;
  blueprintVersionId: string;
  status: string;
  contentHash: string;
  minted: boolean;
  exemplars: BlueprintExemplarDto[];
}

// ── Exemplar picker (blueprint.discover_candidates / compose_draft) ────────

export interface ExemplarPoolItemDto {
  practiceItemId: string;
  prompt: string;
  practiceMode: string;
  evidenceFacets: string[];
  attempted: boolean;
}

export interface ExemplarPoolEntryDto {
  learningObjectId: string;
  title: string;
  items: ExemplarPoolItemDto[];
}

export interface ExemplarPoolSnapshot {
  version: number;
  pool: ExemplarPoolEntryDto[];
}

export interface ComposeDraftResult {
  version: number;
  blueprint: BlueprintVersionDto;
  /** JSON string — parse and pass verbatim as goldenPathConfirm's contractBody. */
  contractBodyJson: string;
  sourceRev: string;
  unitId: string;
  heldOutItemId: string;
  warnings: string[];
}

/** golden_path.confirm receipt (atomic confirmation). */
export interface ConfirmReceiptDto {
  version: number;
  runId: string;
  goalId: string;
  mode: "certifying" | "practice_only";
  currentState: string;
  minted: boolean;
  blueprintVersionId: string;
  commitmentId: string;
  commitmentVersionId: string;
  goalContractVersionId: string;
  reservationId: string | null;
  reservedSurfaceId: string | null;
}

/** golden_path.run_status projection. */
export interface RunNextActionDto {
  toState: string | null;
  reason: string;
  terminal: boolean;
}
export interface RunHistoryEntryDto {
  seq: number;
  fromState: string;
  toState: string;
  reason: string;
  goalContractHeadVersionId: string | null;
}
export interface RunStateDto {
  version: number;
  runId: string;
  currentState: string;
  headEventId: string | null;
  headSeq: number;
  mode: string;
  milestone: string | null;
  goalContractHeadVersionId: string | null;
  eventCount: number;
  nextAction: RunNextActionDto;
  history: RunHistoryEntryDto[];
}
export interface RunAdvanceResultDto {
  version: number;
  /** Null when the staged rule deferred the step (router R2a, `bridge.deferred`). */
  result: { toState: string; [k: string]: unknown } | null;
  state: RunStateDto;
  /** Router R2a (D13): present when the step went through the staged bridge. */
  bridge?: {
    authority: string;
    toState: string | null;
    reason: string;
    vetoReason: string | null;
    deferred?: { vetoReason: string | null; message: string };
    [k: string]: unknown;
  };
}

/** capability × facet boundary cell (§5.3) — never blends two axes (§1). */
export type BoundaryCellState = "demonstrated" | "developing" | "untested" | "weak" | "contested";
export interface BoundaryCellDto {
  facet: string;
  capability: string;
  before: BoundaryCellState;
  after: BoundaryCellState;
  changed: boolean;
  calibrationStatus: GpCalibrationStatus;
  claimLanguage: GpClaimLanguage;
  interval: GpInterval;
}
export interface BoundaryDiffDto {
  version?: number;
  runId: string;
  passed: boolean;
  targetContractVersionId: string;
  schemaVersion: number;
  cells: BoundaryCellDto[];
}

/** golden_path.assess_open (cold assessment render / burn boundary). */
export interface AssessOpenDto {
  version: number;
  administrationId: string;
  surfaceId: string;
  cardVersionId: string;
  snapshotHash: string;
  purpose: string;
  consumesUnseen: boolean;
  alreadyOpen: boolean;
  /** The cold question to render (never the expected answer — that stays
   *  hidden until after submission). Absent when the surface has no legacy item. */
  practiceItemId?: string;
  prompt?: string;
  /** The full §3.A2/§3.A3 stimulus, from the same serializer practice and exams
   *  read. Absent when the surface has no legacy item. */
  presentation?: ItemPresentationDto;
  maxPoints?: number;
}

/** golden_path.assess_submit / assess_result (reliability-aware certification). */
export interface AssessReviewStateDto {
  quarantined: boolean;
  reviewFlag: boolean;
  influenceFlag: boolean;
  fallbackReason: string | null;
}
export interface AssessResultDto {
  version?: number;
  runId: string;
  administrationId: string;
  passed: boolean;
  observedClass: string;
  point: number;
  interval: GpInterval;
  coverage: Array<{ facet: string; capability: string }>;
  claimLanguage: GpClaimLanguage;
  calibrationStatus: GpCalibrationStatus;
  calibrationModelVersionId: string | null;
  citedVersion: number;
  targetContractVersionId: string;
  surfaceEligibility: string;
  eligibilityReason: string | null;
  burnReason: string;
  representative: boolean;
  terminal: boolean;
  reviewState: AssessReviewStateDto;
  practiceSuccessorEventId: string | null;
  projectionAlgorithmVersion: string;
  schemaVersion?: number;
}

/** A reviewed depth edge (§7.5) inside the envelope. */
export interface DepthEdgeDto {
  edgeId: string;
  reviewed: boolean;
  direction: string;
  milestoneSlug: string;
  taskFeatureDelta: Record<string, unknown>;
  capabilityDelta: unknown[];
  supportDelta: Record<string, unknown>;
  exitEvidence: Record<string, unknown>;
  successorActivityPath: Record<string, unknown>;
  freshProofRule: string;
  burden: { minutes?: number; [k: string]: unknown };
}
export interface DepthInvitationDto {
  activated: boolean;
  servedAs: string;
  milestoneSlug: string;
  edge: DepthEdgeDto;
  outcome: {
    kind: string;
    outcome: string;
    reason: string;
    selectedEdgeId: string | null;
    commitmentId: string;
    detail: Record<string, unknown>;
  };
}
export interface DepthInvitationResultDto {
  version?: number;
  invitation: DepthInvitationDto | null;
  milestone: { milestoneSlug: string; eventOnly: boolean } | null;
}
export interface AcceptEdgeResultDto {
  version?: number;
  activated: boolean;
  intentRecorded: boolean;
  [k: string]: unknown;
}

/** golden_path.restore (restoration + boundary diff + milestone + next edge). */
export interface RestoreDto {
  version?: number;
  runId: string;
  milestoneRecorded: boolean;
  achievedMilestone: string;
  activeEnvelopeVersionId: string;
  nextAction: string;
  nextReviewedEdge: DepthEdgeDto | null;
  boundaryDiff: BoundaryDiffDto;
  invitation: DepthInvitationDto | null;
  exemplarComparison: Array<{ exemplarRef: string; heldOut: boolean; weight: number }>;
  sourceNeighborhoods: Record<string, unknown>;
}

/** ladder.policy — the nine-stage pattern ladder (§7.1). */
export interface LadderStageDto {
  id: string;
  policyId: string;
  stageKey: string;
  ordinal: number;
  patternFamily: string;
  purpose: string;
  runState: string;
  entryCriteria: string;
  exitCriteria: string;
  mintsCertification: number;
  recordsScaffold: number;
  requiresCold: number;
  createdAt: string;
}
export interface LadderPolicyDto {
  version?: number;
  policy: {
    id: string;
    policySlug: string;
    policyVersion: number;
    schemaVersion: number;
    status: string;
    contentHash: string;
    createdAt: string;
  };
  stages: LadderStageDto[];
}
export interface LadderStatusDto {
  version?: number;
  runId: string;
  currentStage: string | null;
  [k: string]: unknown;
}
export interface LadderAdvanceResultDto {
  version?: number;
  toStage: string;
  [k: string]: unknown;
}

/** practice_pool.* — rotating practice surfaces (§7.3, U-028). */
export interface PoolSurfaceDto {
  surfaceSlug: string;
  surfaceId: string | null;
  angle: string;
  provenance: string;
  admissionStatus: "candidate" | "admitted" | "rejected";
}
export interface PoolDto {
  version?: number;
  poolId: string;
  poolSlug: string;
  blueprintVersionId: string;
  status: string;
  contentHash: string;
  minted: boolean;
  surfaces: PoolSurfaceDto[];
}
/** practice_pool.status — pool record + its admission/rotation ledger. */
export interface PoolStatusDto {
  version?: number;
  pool: PoolDto;
  events: Array<Record<string, unknown>>;
}
/** practice_pool.for_run / seed_for_run / admit_anchor — run-scoped pool view. */
export interface PoolAnchorCandidateDto {
  ref: string;
  inVault: boolean;
  angle: string;
}
export interface PoolForRunDto {
  version?: number;
  runId: string;
  blueprintVersionId: string;
  reservedSurfaceId: string | null;
  poolId: string | null;
  pool: PoolStatusDto | null;
  anchors: PoolAnchorCandidateDto[];
  heldOutRef: string | null;
}
/**
 * practice_pool.next_surface — one SERVED practice surface (§7.3). Distinct from
 * PoolSurfaceDto (a pool-admission row): this is the rotation-time projection
 * matching ServedSurface.as_dict(), carrying the P1 freshness/warmth flags the
 * practice view renders (fresh / reducedEvidence / exposureStatus / needsRotation).
 */
export interface ServedSurfaceDto {
  surfaceId: string;
  surfaceSlug: string;
  angle: string;
  fresh: boolean;
  reducedEvidence: boolean;
  warmth: number;
  exposureStatus: string;
  needsRotation: boolean;
}

export interface PoolNextSurfaceDto {
  version?: number;
  poolId: string;
  current: ServedSurfaceDto | null;
  spare: ServedSurfaceDto | null;
  fallback: boolean;
  rotated: boolean;
  reason: string;
}

/** diagnostic.triage — two-tier failure-reason triage decision aid (U-027). */
export interface TriageRouteDto {
  routeId: string;
  reason: string;
  ladderEntryStage: string;
  firstIntervention: string;
  coldFollowUp: string;
  reopensDiagnostic: boolean;
}
export interface TriageAlternativeDto {
  reason: string;
  weight: number;
  route: TriageRouteDto;
}
export interface TriageResultDto {
  version?: number;
  runId: string;
  eventId: string;
  kind: string;
  tier: "one" | "two";
  decisive: boolean;
  reason: string | null;
  route: TriageRouteDto | null;
  distribution: Record<string, number> | null;
  alternatives: TriageAlternativeDto[];
  routed: boolean;
  routedTo: string | null;
  autoCommitted: boolean;
  anchorSampleId: string | null;
  /**
   * Which arm of the P2 tier-one gate committed the route -- one of
   * "deterministic_trigger" | "legacy_dominance" | "causal_authority", or null for
   * tier two. Causal support may veto freely but promotes only under an approved
   * support authority (spec_causal_attribution_v1 §2).
   */
  tierOneBasis?: string | null;
}

/** golden_path.list_runs — every confirmed run, for re-entry after restart. */
export interface RunListEntryDto {
  runId: string;
  goalId: string;
  currentState: string;
  mode: string;
  milestone: string | null;
  blueprintVersionId: string;
  createdAt: string;
}
export interface RunListDto {
  version?: number;
  runs: RunListEntryDto[];
}

/** diagnostic.triage_status — the committed triage trace for a run. */
export interface TriageTraceEntryDto {
  eventId: string;
  seq: number;
  kind: string;
  tier: "one" | "two";
  decisive: boolean;
  routeId: string | null;
  selectedReason: string | null;
  distribution: Record<string, number> | null;
  overrideActor?: string | null;
  anchorSampleId?: string | null;
  goalContractHeadVersionId?: string | null;
}
export interface TriageStatusDto {
  version?: number;
  runId: string;
  latest: TriageTraceEntryDto | null;
  trace: TriageTraceEntryDto[];
}

/** reader.prompt_contract — the reviewed reader profile + gating flag (A.2). */
export interface ReaderPromptContractDto {
  version: string;
  context: string;
  readerEnabled: boolean;
  notSocraticByDefault: boolean;
  defaultAnswerMode: ReaderAnswerMode;
  answerModes: ReaderAnswerMode[];
  mayReveal: string[];
  manifestIncludes: string[];
  manifestNeverIncludes: string[];
  citations: string;
  exposureOnCommit: string;
  /** RW1a: reader_inquiry.enabled (present only when on; absent means off). */
  inquiryEnabled?: boolean;
  /** RW1b: the intent box (present only while reader_intent and reader_inquiry are on). */
  intent?: ReaderIntentContractDto;
  /** RW1b: active reading (present only while reader_active_reading and reader_inquiry are on). */
  activeReading?: { foldBlocks: number };
  /** RW4a: ask your library (present only while library_ask, the sources service and reader_inquiry are on). */
  libraryAsk?: { expandGraph: boolean; personalizedDefault: boolean; compare: boolean };
  /** RW4b: exercises from my sources (present only while library_exercises.enabled and the library answer are on). */
  libraryExercises?: { fallback: boolean };
  /** Reader workbench RW5a: explorable figures (absent while figures.enabled is off). */
  figures?: { predictions: boolean; region: boolean; revisions: boolean; offers?: boolean; /** RW5d P1: "show me" in the learner's words (figures.show_me_enabled). */ showMe?: boolean };
  /** RW1c: the tutor that looks things up (present only while reader_tutor.retrieval_enabled or offers_enabled is on). */
  readerTutor?: ReaderTutorContractDto;
  /** RW4d: keep a comparison (present only while reader_compare.keep_enabled and compare are on). */
  compareKeep?: CompareKeepContractDto;
  /** RW7a: reading paths in the Guide (present only while reading_paths.enabled is on). */
  readingPaths?: { enabled: boolean; depths: Array<{ id: ReadingPathDepth; label: string }> };
}
/** RW4d (spec §7.8): where a comparison can be kept, and the perspectives field. */
export interface CompareKeepContractDto {
  /** A library ask's comparison (the library answer is on). */
  library: boolean;
  /** The tutor's comparison (RW1c's "how do your books treat this?"). */
  tutor: boolean;
  perspectives: boolean;
  maxPerspectives: number;
}
/** RW1c (spec §4.6): which parts of the tutor that looks things up are on. */
export interface ReaderTutorContractDto {
  retrieval: boolean;
  offers: boolean;
  /** "another way" and "that didn't help": retrieval on and RW1a's branches on. */
  anotherWay: boolean;
  personalizedDefault: boolean;
  /** "Try the next step first": offers on and RW1b's active reading on. */
  tryNextStep: boolean;
  manifestIncludes: string[];
}
export type ReaderAnswerMode = "answer_directly" | "help_me_reason" | "ask_me_first";

// ── Reader workbench RW1b: the intent box and active reading ───────────────
// spec_reader_workbench_v1 §4.2; UX §4.1, §4.3, W2.

export type ReaderIntentEffect =
  | { kind: "ask"; answerMode: ReaderAnswerMode }
  | { kind: "preset"; preset: string }
  | { kind: "highlight"; note?: boolean }
  | { kind: "import_exercise" }
  | { kind: "work_through" }
  | { kind: "active_reading"; style: ReaderActiveStyle }
  | { kind: "another_way" }
  | { kind: "library_ask"; entry: LibraryAskEntry }
  | { kind: "reading_path" }
  | { kind: "figure" };
export type ReaderIntention = "orient" | "understand" | "apply" | "consolidate" | "transfer";
export interface ReaderIntentActionDto {
  id: string;
  group: ReaderIntention | "mark";
  intention: ReaderIntention | null;
  label: string;
  effect: ReaderIntentEffect;
  /** Whether the action shows the selection to a model (absent for held-out passages). */
  model: boolean;
}
export interface ReaderIntentGroupDto {
  group: ReaderIntention | "mark";
  label: string;
  intention: ReaderIntention | null;
  actions: ReaderIntentActionDto[];
}
export interface ReaderIntentContractDto {
  palette: ReaderIntentGroupDto[];
  /** The learner's own notes: only the actions that need no source anchor. */
  notesPalette: ReaderIntentGroupDto[];
  speculative: boolean;
  speculateAfterMs: number;
  timeoutSeconds: number;
}
/** reader.route_intent / reader.intent_routing: pending, or the action and why. */
export interface ReaderIntentRoutingDto {
  state: "pending" | "done";
  routingId: string;
  speculative: boolean;
  action?: string;
  /** routed (the Decider chose) · empty (an empty Enter) · fallback (Ask, see reason) · not_made (speculation). */
  status?: "routed" | "empty" | "fallback" | "not_made";
  reason?: string | null;
  intention?: ReaderIntention | null;
  group?: string | null;
  label?: string | null;
  effect?: ReaderIntentEffect | null;
  latencyMs?: number | null;
}
export type ReaderActiveStyle = "next_step" | "why_step" | "assumptions" | "reconstruct";
export interface ReaderActiveQuestionDto {
  id: string;
  extractionId: string;
  sectionId: string;
  status: "proposed" | "answered" | "dismissed" | "escalated";
  questionMd: string;
  expectedAnswerMd: string;
  spanIds: string[];
  practiceItemId: string | null;
  answeredAt: string | null;
  scopeKind: "selection";
  questionStyle: ReaderActiveStyle;
  anchorSpanIds: string[];
  responseMd: string | null;
  selfCheck: InquirySelfCheck | null;
  /** Whose words the expected answer is: the book's (quote-checked in code) or LearnLoop's model's. */
  answerBasis: "source" | "model" | null;
  escalationLearningObjectId: string | null;
  missed: boolean;
  reconstruct?: { commitmentId: string; practiceItemId: string | null; disposition: string } | null;
  model?: string | null;
  promptVersion?: string | null;
}
export interface ReaderActiveQuestionRequestDto {
  style: ReaderActiveStyle;
  anchorSpanIds: string[];
  /** The book's next blocks, folded at once while the learner tries the next step. */
  foldedSpanIds: string[];
  status: "queued" | "exists" | "provider_unavailable" | "no_next_step";
  batchId: string | null;
  message: string | null;
  question: ReaderActiveQuestionDto | null;
}
export interface ReaderActiveQuestionStatusDto {
  question: ReaderActiveQuestionDto | null;
  job: ReaderInquiryCheckJobDto | null;
}

/** reader.ask — a span-grounded exchange in the reader tutor context. */
export interface ReaderAskInput {
  extractionId: string;
  spanId: string;
  question: string;
  /** Completed reader-answer event ID; omitted/null starts a new root. */
  parentExchangeId?: string | null;
  answerMode?: ReaderAnswerMode;
  targetKey?: string | null;
  revealedSurfaceIds?: string[];
  /** Full capture selection: spanId stays the primary grounding block; these
   *  widen the tutor's citable context to every selected block + exact quote. */
  selectionSpanIds?: string[];
  selectionQuote?: string | null;
  /** RW1a (reader_inquiry on): the source's own wording when the learner
   *  edited the capture; selectionQuote is then the learner's wording. */
  selectionSourceQuote?: string | null;
  coldActive?: boolean;
  /** RW1c: "another way" (alternative) and "that didn't help" (remediate) name the answer they are under. */
  retrievalIntent?: ReaderRetrievalIntent;
  /** RW1c: the personalized toggle (omitted: the vault's default). */
  personalized?: boolean;
  /** RW1c: the bound workbench session the Ask comes from (its item's practice policy). */
  workbenchSessionId?: string | null;
}
export type ReaderRetrievalIntent = "explain" | "alternative" | "remediate";
/** RW1c's "From your books": a verbatim excerpt, quote-verified against its passage. */
export interface ReaderExcerptDto {
  extractionId: string;
  spanId: string;
  quote: string;
  label: string | null;
  relation: string | null;
  sourceId?: string | null;
}
/** RW1c: a Reader tutor answer's modes (absent while reader_tutor.retrieval_enabled is off). */
export interface ReaderTutorViewDto {
  modes: Array<"excerpt" | "grounded" | "bridge">;
  excerpt: ReaderExcerptDto | null;
  bridgeMd: string | null;
  abstained: boolean;
  abstentionLine: string | null;
  droppedExcerpt: string | null;
  droppedBridge: string | null;
  intent: ReaderRetrievalIntent;
  personalized: boolean;
  withheldCitations?: number;
  /** "Another way": citations of passages the inquiry already showed, not shown again. */
  repeatedCitations?: number;
  retrieval: {
    status?: string | null;
    policy?: string | null;
    intent?: string | null;
    /** How "another way"'s passages differ ("from a different book", "a worked example instead"). */
    label?: string | null;
    passages?: number | null;
    spanKeys?: string[] | null;
    booksCover?: boolean | null;
    reason?: string | null;
  };
}
/** RW1c: a button the Reader decides itself ("Try the next step first" on a cited derivation or worked example). */
export interface ReaderTutorButtonDto {
  /** RW5b adds "make_explorable" (a cited equation or figure the tutor judged explorable); RW5d P1
   *  adds "show_me" (the tutor's figure goal: `label` is the goal, AI-written; `spanId` is empty). */
  kind: "try_next_step" | "make_explorable" | "show_me";
  extractionId: string;
  spanId: string;
  label: string;
  role: string;
}
export interface ReaderAnswerDto {
  eventId: string;
  readerAnswerEventId: string;
  /** RW1a branches (absent while reader_inquiry is off). */
  parentExchangeId?: string | null;
  /** RW1a: the answering model, for the reader report's per-route funnel. */
  model?: string | null;
  answerMd: string;
  answerMode: ReaderAnswerMode;
  citations: TutorCitationDto[];
  manifest: Record<string, unknown>;
  warmedSurfaceIds: string[];
  burnedSurfaceIds: string[];
  hintEquivalent: boolean;
  remaining: number | null;
  /** Slice 2 T6: labelled nearest-LO suggestions when the span has no
   *  provenance-linked LO (absent otherwise). */
  suggestedLearningObjects?: SuggestedLearningObjectDto[];
  /** Learner-text gaps: the reading queued for this question (absent when
   *  nothing was queued). */
  learnerGap?: LearnerGapQueuedDto;
  /** Canonical sources S0: the deterministic "Practice this" request (absent when off). */
  practiceRequest?: PracticeRequestDto;
  /** Canonical sources S4: the tutor's own typed requests (absent when it wrote none). */
  toolRequests?: SourceToolRequestDto[];
  /** RW1c: the answer's modes (absent while reader_tutor.retrieval_enabled is off). */
  tutor?: ReaderTutorViewDto;
  /** RW1c: the Reader's own buttons (absent while reader_tutor.offers_enabled is off). */
  tutorOffers?: { buttons: ReaderTutorButtonDto[] };
}

/** A completed Reader Ask restored from the durable interaction-event log. */
export interface ReaderAskHistoryExchangeDto {
  eventId: string;
  /** Older saved exchanges have no parent and remain readable as roots. */
  parentExchangeId?: string | null;
  selectionSpanIds?: string[];
  selectionQuoteMd?: string | null;
  /** Non-null only when the learner edited the capture: then selectionQuoteMd
   *  is their wording and this is the source's own. */
  selectionSourceQuoteMd?: string | null;
  /** RW1a: the exchange's tutor question and its learner-owned resolution
   *  (a root's resolution is its inquiry's status). */
  questionEventId?: string | null;
  resolution?: InquiryResolution | null;
  extractionId: string;
  spanId: string;
  questionMd: string;
  answerMd: string;
  answerMode: ReaderAnswerMode;
  citations: TutorCitationDto[];
  createdAt: string | null;
  /** RW1c: the answer's modes (absent on exchanges before RW1c). */
  tutor?: ReaderTutorViewDto;
}
export type InquiryResolution = "open" | "resolved" | "dismissed";

/** reader.set_inquiry_status — any exchange names its inquiry; the status
 *  lands on the root question (RW1a). */
export interface ReaderSetInquiryStatusInput {
  extractionId: string;
  exchangeId: string;
  resolution: InquiryResolution;
  trigger?: "chip" | "reconnect" | "undo" | "key";
}
export interface ReaderInquiryStatusDto {
  rootExchangeId: string;
  questionEventId: string;
  resolution: InquiryResolution;
  previousResolution: InquiryResolution;
  openCount: number;
}

export type ReconnectAnswer = "yes" | "still_unclear" | "quick_check";
export interface ReaderReconnectAnswerInput {
  extractionId: string;
  exchangeId: string;
  answer: ReconnectAnswer;
  via: "inline" | "rail";
}
export interface ReaderReconnectAnswerDto {
  rootExchangeId: string;
  questionEventId: string;
  answer: ReconnectAnswer;
  resolution: InquiryResolution;
  /** quick_check only: exists | queued | provider_unavailable. */
  status: "exists" | "queued" | "provider_unavailable" | null;
  batchId: string | null;
  message: string | null;
  question: ReaderInquiryQuestionDto | null;
}

export type InquirySelfCheck = "matches" | "partly" | "no";
/** A passage-scoped quick check (reader_authored_questions, scope inquiry). */
export interface ReaderInquiryQuestionDto {
  id: string;
  extractionId: string;
  sectionId: string;
  status: "proposed" | "answered" | "dismissed" | "escalated";
  questionMd: string;
  expectedAnswerMd: string;
  spanIds: string[];
  practiceItemId: string | null;
  answeredAt: string | null;
  scopeKind: "inquiry";
  questionStyle: string;
  anchorSpanIds: string[];
  inquiryRootEventId: string | null;
  responseMd: string | null;
  selfCheck: InquirySelfCheck | null;
  escalationLearningObjectId: string | null;
  /** The route the check came from (the Reader's funnel). */
  model?: string | null;
  promptVersion?: string | null;
}
/** The durable job writing an inquiry's quick check (reader.inquiry_question
 *  with a batchId): its state, and why it failed. */
export interface ReaderInquiryCheckJobDto {
  status: "queued" | "running" | "waiting_for_input" | "blocked" | "completed" | "failed" | "cancelled" | string;
  /** capped · spend_refused · provider_unavailable · held · … (failed or cancelled only). */
  errorCode: string | null;
  message: string | null;
  /** spend_refused only: which limit stopped it (no_price · over_cap). */
  refusal?: "no_price" | "over_cap" | string | null;
}
export interface ReaderInquiryQuestionReadDto {
  question: ReaderInquiryQuestionDto | null;
  /** Present when the read named a batch; null when it is not this inquiry's. */
  job?: ReaderInquiryCheckJobDto | null;
}
export interface ReaderInquiryQuestionActionInput {
  questionId: string;
  action: "answered" | "self_checked" | "dismissed";
  response?: string | null;
  selfCheck?: InquirySelfCheck | null;
}

/** One funnel event for reader.log_activity (ids, kinds, counts and timings
 *  only; the sidecar drops anything else, learner text above all). */
export interface ReaderActivityEvent {
  kind:
    | "reader_view_opened"
    | "reader_view_closed"
    | "reader_selection"
    | "reader_job_queued"
    | "reader_job_completed"
    | "reader_action_invoked";
  event?:
    | "action_invoked"
    | "detour_opened"
    | "detour_returned"
    | "reconnect_shown"
    | "proactive_shown"
    | "back_to_reading"
    | "cue_shown"
    | "tutor_offer_shown"
    | "tutor_offer_pressed"
    | "figure_opened"
    | "figure_animated";
  payload: Record<string, string | number | boolean | null | Record<string, boolean>>;
}
export interface ReaderAskHistoryDto {
  version?: number;
  exchanges: ReaderAskHistoryExchangeDto[];
}

/** reader.choose_disposition — the four reading-question dispositions (U-033). */
export type ReaderDisposition =
  | "comprehension_only"
  | "check_once_later"
  | "keep_developing"
  | "reference_only";
export interface ReaderDispositionResultDto {
  version?: number;
  disposition: ReaderDisposition;
  [k: string]: unknown;
}

// --- P3 slice 1: render views, block health, annotations, capture/outbox ---

export type ReaderAnchorStatus =
  | "exact"
  | "reanchored"
  | "needs_reanchor"
  | "orphaned"
  | "manually_anchored";

export type ReaderBlockHealthStatus = "ok" | "suspect" | "failed" | "unknown";
export type ReaderRecommendedView = "derived" | "crop_adjacent" | "crop_default" | "warn_link";

/** One display node of a render view (spec §3.2). */

/** reader.watch_plan — YouTube watch mode: embed id + tutor pause points. */
export interface ReaderWatchPausePointDto {
  timeSeconds: number;
  segmentStartSeconds: number;
  practiceItemId: string;
  learningObjectId: string;
  promptPreview: string;
  goalId?: string | null;
  goalTitle?: string | null;
  goldenPathRunId?: string | null;
  targetContractVersionId?: string | null;
}
export interface ReaderWatchPlanDto {
  version?: number;
  sourceId: string;
  videoId: string;
  embedUrl: string;
  pausePoints: ReaderWatchPausePointDto[];
}

export interface ReaderRenderBlockDto {
  displayNodeId: string;
  spanId: string | null;
  blockType: string | null;
  /** Caption blocks carry their cue's "t=<start>-<end>" locator here (watch mode). */
  extractorBlockId?: string | null;
  markdown: string;
  sanitized: boolean;
  katexNodes: string[];
  assets: string[];
  health: {
    status: ReaderBlockHealthStatus;
    recommendedView: ReaderRecommendedView;
    reasonFlags: string[];
  };
}

/** reader.render_view — replaceable marker-markdown view over the extraction IR. */
export interface ReaderRenderViewDto {
  version?: number;
  renderViewId: string;
  extractionId: string;
  revisionId: string;
  sourceId: string;
  renderer: string;
  rendererVersion: string;
  contentHash: string;
  status: string;
  blocks: ReaderRenderBlockDto[];
  layers: Record<string, string>;
  /** Readings of this book whose spans have aliases into this one (it was
   *  read again): a place saved on one of them is translated first. */
  aliasedFrom?: string[];
  /** Every other reading of this book, whether or not aliases were recorded
   *  (re-read safety, Codex review F5): a bare saved span id is this
   *  reading's only when there are none. */
  otherReadings?: string[];
  /** What of this reading the model actions must not touch (exam_material
   *  decides; reader-pdf-selection). Absent from older sidecars. */
  protection?: ReaderProtectionDto | null;
}

/** The held-out partition on a reading, for its selection surfaces
 *  (reader-pdf-selection): the whole reading when it is held back until it is
 *  marked (rule 4) or held out whole, else its held-out passages. A selection
 *  touching any of it offers no model action; `message` is the refusal the
 *  sidecar would give. */
export interface ReaderProtectionDto {
  withheld: boolean;
  heldOutSpanIds: string[];
  message: string | null;
}

/** Where a saved annotation lands on the reading the Reader has open
 *  (reader.source_annotations with extractionId; span_aliases decides):
 *  `here` as made, `moved` carried over by a re-read (drawn on its words,
 *  labelled), `flagged` (its words changed: shown at the passage that took
 *  its place, never drawn as text) or `elsewhere` (rail only). Segment
 *  offsets are code points into that block's own text. */
export interface ReaderAnnotationPlacementDto {
  state: "here" | "moved" | "flagged" | "elsewhere";
  segments: Array<{ spanId: string; codepointStart: number; codepointEnd: number; exactQuote: string }>;
  flagSpanId: string | null;
}

/** Where a saved reading place lands on the book's current reading
 *  (reader.saved_place, re-read safety): the same text (`current`), the same
 *  place with changed text (`needs_reanchor`) or nowhere (`stale`). */
export interface ReaderSavedPlaceDto {
  version?: number;
  sourceId: string;
  /** null: a bare span id whose reading is unknown (then `stale`). */
  fromExtractionId: string | null;
  fromSpanId: string;
  /** The reading it landed on: the one asked for (toExtractionId), else the
   *  book's current reading. A Reader applies it only to that reading. */
  extractionId: string;
  spanId: string | null;
  status: "current" | "needs_reanchor" | "stale";
  matchKind: string | null;
  /** unknown_reading: a place saved before places recorded their reading, on
   *  a book read again since; the reading history decides instead. */
  reason?: "unknown_reading";
}

/** Local, source-grounded guidance for one reading section.  Learner-state
 * numbers stay server-side; the UI receives only a plain-language reason. */
export interface ReaderSuggestedPassageDto {
  spanId: string;
  quote: string;
  reason: string;
  learningObjectId: string;
  learningObjectTitle: string;
  learnerSignal: "recent_misunderstanding" | "uncertain" | "goal_frontier" | "new_material" | "source_relevance";
  /** needs_reanchor: cited on an earlier reading of the book and its words
   *  changed at this place when it was read again; `quote` is what was cited. */
  anchor?: "current" | "needs_reanchor";
}

export interface ReaderSectionQuestionDto {
  practiceItemId: string | null;
  learningObjectId: string | null;
  learningObjectTitle: string | null;
  prompt: string;
  reason: string;
  learnerSignal: ReaderSuggestedPassageDto["learnerSignal"] | "auto_authored";
  goalId: string | null;
  goalTitle: string | null;
  goldenPathRunId: string | null;
  targetContractVersionId: string | null;
  readingPhase: "before_section" | "during_section" | "after_section";
  pattern: string | null;
  placementEventId: string | null;
  blueprintVersionId: string | null;
  placement: "owner_reviewed" | "auto_authored";
  /** auto_authored only: the reader_authored_questions row id. */
  authoredQuestionId?: string;
  /** auto_authored only: the self-check anchor revealed after answering. */
  expectedAnswer?: string;
  /** auto_authored only: the section spans the question is grounded in. */
  spanIds?: string[];
  /** auto_authored only: default Learning Object for "add to practice". */
  escalationLearningObjectId?: string | null;
}

/** One AI-authored quick check row (reader quick-check producer). */
export interface ReaderAuthoredQuestionDto {
  id: string;
  extractionId: string;
  sectionId: string;
  status: "proposed" | "answered" | "dismissed" | "escalated";
  questionMd: string;
  expectedAnswerMd: string;
  spanIds: string[];
  practiceItemId: string | null;
  answeredAt: string | null;
}

export interface ReaderAuthorSectionQuestionDto {
  version?: number;
  status: "queued" | "exists";
  batchId?: string;
  question: ReaderAuthoredQuestionDto | null;
}

/** One across-source search hit ("where did I read that?"). */
export interface ReaderSourceSearchHitDto {
  sourceId: string;
  sourceTitle: string;
  extractionId: string;
  spanId: string;
  section: string | null;
  page: number | null;
  snippet: string;
}

export interface ReaderSourceSearchDto {
  version?: number;
  query: string;
  hits: ReaderSourceSearchHitDto[];
  searchedSources: number;
  /** Slice 2 T6: which evidence ranked the hits, e.g. "keyword",
   *  "keyword+meaning", "keyword+meaning+rewrite"; absent when retrieval is off
   *  (plain substring search). */
  basis?: string;
  deep?: boolean;
  /** Whether Enter would also search by meaning: "ready" or "partial" (some
   *  sources not embedded yet) when it would; absent when retrieval is off. */
  meaningSearch?: ReaderMeaningSearchDto;
  /** Local contextual retrieval P1: the search's feedback receipt, sent back
   *  when a hit is opened (absent unless a new embedding space is on). */
  retrievalReceiptId?: string | null;
}

export interface ReaderMeaningSearchDto {
  status: "ready" | "partial" | "incomplete" | "disabled" | "empty" | "unavailable" | string;
  reason?: string | null;
  sources: number;
  sourcesCovered: number;
  blocks: number;
  blocksCovered: number;
}

/** Slice 2 T6: a nearest learning object for a reader span without
 *  provenance. Always a labelled suggestion, never a filing or a target. */
export interface SuggestedLearningObjectDto {
  learningObjectId: string;
  title: string;
  label: "suggestion";
  basis: string[];
}

/** reader.span_learning_objects: provenance-linked LOs, else suggestions. */
export interface ReaderSpanLearningObjectsDto {
  version?: number;
  extractionId: string;
  spanId: string;
  status: string;
  provenance: string[];
  suggestions: SuggestedLearningObjectDto[];
  meaning?: string;
}

// Durable per-section reading progress (reader-first seeding).
export interface ReaderSectionProgressDto {
  extractionId: string;
  sectionId: string;
  spansSeen: number;
  spanCount: number;
  revealedAt: string | null;
  completedAt: string | null;
  generationBatchId: string | null;
}

export interface ReaderProgressListDto {
  version?: number;
  extractionId: string;
  sections: ReaderSectionProgressDto[];
}

export interface ReaderMarkProgressResultDto {
  version?: number;
  progress: ReaderSectionProgressDto;
  enqueuedGeneration: boolean;
  batchId: string | null;
}

export interface ReaderGuideSectionDto {
  id: string;
  label: string;
  startSpanId: string;
  endSpanId: string;
  spanIds: string[];
  question: ReaderSectionQuestionDto | null;
  suggestedPassages: ReaderSuggestedPassageDto[];
}

export interface ReaderGuidePlanDto {
  version?: number;
  sourceId: string;
  extractionId: string;
  personalized: boolean;
  selectionBasis: string;
  goalContext: {
    goalId: string;
    title: string;
    goldenPathRunId: string | null;
    targetContractVersionId: string | null;
  } | null;
  sections: ReaderGuideSectionDto[];
  /** Reader workbench RW3a: the plan's own misunderstanding passages as
   *  margin cues, within the learner's choices. Absent when cues are
   *  switched off (cues.enabled = false) or from an older sidecar. */
  cues?: ReaderCuesDto;
  /** Attempts whose live diagnosis is still pending behind a shown
   *  "Revisit this to resolve" reason: the reason names the error type until
   *  it lands. The Reader re-reads the plan while this is non-empty. Absent
   *  from a sidecar that predates it (nothing to wait on). */
  pendingDiagnosisAttemptIds?: string[];
}

/** The learner's margin-mark density: 0, 1, 2 or 4 marks per section (RW3a). */
export type CueDensity = "off" | "fewer" | "normal" | "more";

/** What "open" shows about a cue: the learner's earlier answer and LearnLoop's
 *  model's reading of it once it has one. */
export interface ReaderCueEarlierDto {
  attemptId: string | null;
  practiceItemId: string | null;
  /** The question answered, clipped. */
  prompt: string | null;
  /** The cited attempt's answer, in the learner's own words (clipped, line
   *  breaks kept); null when the error names no attempt or it has no text. */
  answer: string | null;
  answeredAt: string | null;
  /** "2 Oct". */
  answeredOn: string | null;
  /** The diagnoser's (or the joint grade's) statement; model text. */
  statement: string | null;
  /** The answer's diagnosis is still being written. */
  statementPending: boolean;
  /** RW3b, discovered cues: the learner's own words a named gap was read
   *  from (a question to the tutor, a workbench step), clipped; learner text. */
  learnerText?: string | null;
  /** Where those words were written (`tutor_question`, `workbench_text`, …). */
  learnerTextKind?: string | null;
}

/** A margin mark's kind: RW3a's Guide cue (`◌┆`), and RW3b's discovered
 *  kinds: a distinction (`◌┆`), a prerequisite (`◌┆`), a new application of
 *  something shown (`●┆`), try this step first (`▹┆`). */
export type ReaderCueKind = "revisit" | "distinction" | "prerequisite" | "application" | "try_first";

/** One margin cue (RW3a): one of the Guide's own passages, with fixed copy.
 *  RW3b adds discovered cues (`foundBy: "model"`) and, while discovery is on,
 *  the value each cue was ordered by. */
export interface ReaderCueDto {
  cueId: string;
  kind: ReaderCueKind;
  spanId: string;
  sectionId: string;
  learningObjectId: string;
  learningObjectTitle: string;
  /** The error event the cue is about (a new one is a new cue). */
  targetId: string;
  /** Global order for the one-mark-per-screenful rule (0 first). */
  rank: number;
  sectionRank: number;
  /** "Connects to something you worked on: …" (fixed template). */
  note: string;
  /** "Because: your answer on … · from the Guide's citations". */
  because: string;
  /** The screen reader's full sentence. */
  label: string;
  earlier: ReaderCueEarlierDto;
  /** RW3b (present while discovery is on): who found it ("guide": the
   *  Guide's citations; "model": LearnLoop's model, never a test). */
  foundBy?: "guide" | "model";
  /** RW3b, discovered cues: the link, the judge's relation and rank, the
   *  verified words of the passage it rests on, the target's kind. */
  linkId?: string | null;
  relation?: string;
  pickRank?: number;
  quote?: string;
  targetKind?: string;
  /** RW3b: the probability its target is still open (the order) and where it came from. */
  pOpen?: number | null;
  pOpenSource?: string;
  /** RW3b, discovered cues: the holdout's seed and the propensity of the arm drawn. */
  seed?: string;
  propensity?: number;
}

/** RW3b: the plan's discovery state (present while cues.discovery_enabled). */
export interface ReaderCueDiscoveryDto {
  version: string;
  /** This plan's id: impressions seen on it name it, and the sidecar records
   *  them against this plan as it was served (Codex verify F17). */
  planId: string;
  /** Changes when a target is new or resolved: the Reader asks for discovery again. */
  targetsKey: string;
  targets: number;
  holdoutRate: number;
  valueOrder: boolean;
  tryFirst: boolean;
  /** Background work (a learner-text gap being read) can still name a new
   *  target: the Reader re-reads the plan while it is true. */
  targetsPending?: boolean;
  /** Discovered cues withheld by the holdout (never drawn; their impression is logged in view). */
  heldOut: ReaderCueDto[];
  /** Cues cut by the density budget. */
  suppressed: Array<ReaderCueDto & { reason: "density" }>;
}

export interface ReaderCuesDto {
  version: string;
  density: CueDensity;
  budgetPerSection: number;
  onePerViewport: boolean;
  /** Cues are switched off for this book (marks is empty). */
  sourceOff: boolean;
  marks: ReaderCueDto[];
  withheld: Record<string, number>;
  /** RW3b: absent while discovery is off (the cues are RW3a's, byte for byte). */
  discovery?: ReaderCueDiscoveryDto;
}

export type ReaderCueAction = "opened" | "check_me" | "not_relevant" | "not_relevant_undone";

export interface ReaderCueCheckDto {
  status: "found" | "none" | "failed";
  practiceItemId?: string;
  learningObjectId?: string;
  prompt?: string;
  proposalId?: string | null;
  reason?: string;
}

export interface ReaderCueActionDto {
  cueId: string;
  action: ReaderCueAction;
  eventId: string;
  verdict: string | null;
  ledgerId: string | null;
  /** "Check me": one item proposed for an ordinary attempt on your own. */
  check: ReaderCueCheckDto | null;
}

/** RW3b: a tap on any cue while discovery is on (reader.cue_tap). */
export type ReaderCueTapAction = ReaderCueAction | "try_first";

export interface ReaderCueTapDto extends Omit<ReaderCueActionDto, "action"> {
  action: ReaderCueTapAction;
  /** "Try this step first": the line where RW1b's next-step question opens. */
  tryFirst: { spanId: string } | null;
  /** The visit's impression for the tap: recorded, not on the named plan, or
   *  refused for an unknown plan (the tap itself stands; F17, round 5). */
  impression?: string | null;
}

/** RW3b: the background discovery job (reader.cue_discovery / _job). */
export interface ReaderCueDiscoveryJobDto {
  jobId: string;
  extractionId: string;
  state: "pending" | "done";
  result: { status: string; targetsKey: string | null; calls: number; links: number } | null;
}

/** RW3b: one impression the Reader reports (reader.cue_impressions). */
export interface ReaderCueImpressionInput {
  cueId: string;
  shown?: boolean;
  reason?: "spacing" | "restored_line" | null;
  response?: "fewer" | null;
}

export interface ReaderCuePreferencesDto {
  enabled: boolean;
  density: CueDensity;
  budgetPerSection: number;
  onePerViewport: boolean;
  sourceOff: boolean;
  offSourceCount: number;
}

/** One block's geometry in the original PDF (points, origin top-left). */
export interface ReaderPdfBlockDto {
  spanId: string;
  page: number;
  bbox: number[];
  blockType: string | null;
  /** Extraction text for the block — the source-owned quote a block-snapped
   *  selection sends, so anchoring is exact by construction. */
  text?: string | null;
}

/** reader.pdf_view — Tier-2 embedded PDF manifest: originals-store file served
 *  by the llpdf:// protocol + per-block geometry for overlay/selection. */
export interface ReaderPdfViewDto {
  version?: number;
  available: boolean;
  /** UX Phase 1: the original is shown while the text is still being prepared (no blocks yet). */
  preparing?: boolean;
  fileName: string | null;
  extractionId: string;
  sourceId: string | null;
  revisionId: string | null;
  blocks: ReaderPdfBlockDto[];
  /** Every passage's page, geometry or not (usability round 1, U2): a
   *  text-only extraction has no boxes, but the Reader still jumps to,
   *  follows and resumes a page. Absent from older sidecars. */
  pageSpans?: Array<{ spanId: string; page: number }>;
  /** The held-out partition on this reading (reader-pdf-selection); null
   *  while the book is still being prepared, absent from older sidecars. */
  protection?: ReaderProtectionDto | null;
}

/** A raw display-coordinate selection captured by TS (design §A.2). */
export interface ReaderRawSelectionNode {
  spanId?: string;
  displayNodeId?: string;
  start?: number;
  end?: number;
  quote?: string;
  /** Rendered-surface text around the capture (atomic-unit ctrl+click sends
   *  it) — lets the backend disambiguate repeated quotes without guessing. */
  prefix?: string;
  suffix?: string;
  /** The learner edited this quote in the capture editor (OCR fix): the edited
   *  text overrides the extraction slice as the exercise surface. */
  edited?: boolean;
}
export interface ReaderRawSelection {
  nodes: ReaderRawSelectionNode[];
  /** Learner-edited combined passage (capture editor): overrides the whole
   *  exercise surface while `nodes` keep anchoring the original blocks. */
  editedText?: string;
  /** Reader CA1 (§12.4): a region selection's sub-box (one block), kept on
   *  the imported exercise as the crop shown for it. */
  region?: PrintRegionDto;
}

export interface ReaderTranslateSelectionInput {
  extractionId: string;
  rawSelection: ReaderRawSelection;
  renderViewId?: string | null;
}
export interface ReaderAnchorSegmentDto {
  spanId: string;
  blockContentHash: string;
  codepointStart: number;
  codepointEnd: number;
  exactQuote: string;
  prefix: string;
  suffix: string;
  selectionTextHash: string;
}
export interface ReaderTranslationDto {
  version?: number;
  status: ReaderAnchorStatus;
  segments: ReaderAnchorSegmentDto[];
  confidence: number;
}

/** reader.capture — the local-first capture receipt (spec §5.3). */
export interface ReaderCaptureInput {
  sourceId: string;
  revisionId: string;
  extractionId: string;
  action: string;
  clientIdempotencyKey: string;
  rawSelection?: ReaderRawSelection | null;
  renderViewId?: string | null;
  learnerText?: string;
  whatIThinkIsGoingOn?: string | null;
  sessionId?: string | null;
}
export interface ReaderCaptureReceiptDto {
  version?: number;
  annotationId: string | null;
  outboxId: string;
  interactionEventId: string;
  anchorStatus: ReaderAnchorStatus | null;
  captureKind: string;
  deduplicated: boolean;
  receipt: string;
  provisionalArc?: { stage: string; policy: string };
}

export interface ReaderCreateAnnotationInput {
  sourceId: string;
  revisionId: string;
  extractionId: string;
  annotationType: string;
  rawSelection: ReaderRawSelection;
  learnerText?: string;
  whatIThinkIsGoingOn?: string | null;
  renderViewId?: string | null;
  clientIdempotencyKey?: string | null;
}
export interface ReaderAnnotationResultDto {
  version?: number;
  annotationId: string;
  status: ReaderAnchorStatus;
  [k: string]: unknown;
}

export interface ReaderBlockRegionDto {
  version?: number;
  extractionId: string;
  spanId: string;
  page?: number | null;
  bbox?: number[] | null;
  regionRender: string | null;
  pageRenderSize?: number[] | null;
  reason: string;
}

// ── Reader CA1: the problem as printed (ux_reader_compare_ask_v1 §8) ─────────

/** One crop of a problem's own blocks on one page (never a neighbour, C10). */
export interface PrintedCropDto {
  page: number;
  /** The printed page label when the PDF has them, else the page's position. */
  pageLabel: string;
  bbox: number[];
  spanIds: string[];
  /** A PNG data URL; null when not rendered or not available. */
  image: string | null;
}

/** A learner-drawn sub-box of one block (ReaderSelection.region, §12.4). */
export interface PrintRegionDto {
  spanId: string;
  page: number;
  bbox: number[];
}

/** The multi-block form of reader.block_original_region. */
export interface PrintedCropsDto {
  version?: number;
  extractionId: string;
  spanIds: string[];
  /** ok · no_original (no readable page image) · no_geometry · not_found ·
   *  disabled (practice.as_printed.enabled off: nothing is cropped) */
  status: "ok" | "no_original" | "no_geometry" | "not_found" | "disabled";
  crops: PrintedCropDto[];
  skippedSpanIds: string[];
}

/** practice.as_printed: what an item may show of its print, decided on the server. */
export interface AsPrintedViewDto {
  version?: number;
  practiceItemId?: string;
  enabled: boolean;
  /** page: the crop and the original page · figure: a check on your own, the
   *  figure alone (Q10) · photo: the learner's photo · none */
  kind: "page" | "figure" | "photo" | "none";
  cold: boolean;
  reason?: string;
  label?: string;
  status?: "ok" | "no_original" | "no_geometry" | "not_found";
  /** kind page: PrintedCropDto; kind figure: only an index and the image. */
  crops?: Array<PrintedCropDto | { index: number; image: string | null }>;
  locator?: { sourceTitle: string | null; exerciseLabel: string | null; pageLabel: string };
  originalPage?: { extractionId: string; spanId: string; outlineSpanIds: string[]; sourceId?: string | null } | null;
  /** "the page image isn't available for this book · the transcription is above",
   *  or (a page known without a box) "the crop isn't available for this problem · the original page is" */
  notice?: string;
  transcriptionReport?: boolean;
  photo?: { captureId: string; capturedAt: string | null };
}

export interface TranscriptionReportDto {
  version?: number;
  noticeId: string | null;
  status: string | null;
  reports: number;
}

/** P3 slice 2: nine-preset palette, demand-paged synthesis, source objects (§5-§7). */
export interface ReaderInvokePresetInput {
  preset: string;
  sourceId: string;
  revisionId: string;
  extractionId: string;
  clientIdempotencyKey: string;
  rawSelection?: ReaderRawSelection | null;
  renderViewId?: string | null;
  learnerText?: string;
  whatIThinkIsGoingOn?: string | null;
  subjectId?: string | null;
  sessionId?: string | null;
}
export interface ReaderPresetReceiptDto extends ReaderCaptureReceiptDto {
  preset?: string;
  commitmentId?: string | null;
  suppressesProposals?: boolean;
  arcId?: string | null;
  arc?: ReaderArcDto | null;
}

// P3 slice 3: authoring + coach + maintenance, arcs + depth + primes, restoration.
export interface ReaderImportExerciseInput {
  extractionId: string;
  rawSelection: ReaderRawSelection;
  renderViewId?: string | null;
  sourceId?: string | null;
  revisionId?: string | null;
  learningObjectId?: string | null;
  clientIdempotencyKey?: string | null;
}
export interface ReaderExerciseImportReceiptDto {
  version?: number;
  status: string;
  batchId: string;
}
export interface ReaderExerciseImportedItem {
  practiceItemId: string;
  title: string;
  prompt: string;
  learningObjectId: string;
  learningObjectTitle: string;
  practiceMode: string;
  capability: string;
  taskFeatures: Record<string, unknown>;
  evidenceFacets: string[];
  difficulty: number | null;
  hintCount: number;
  classificationReason: string;
}
export interface ReaderExerciseImportSkip {
  title: string;
  reason: string;
  practiceItemId?: string;
  deduplicated?: boolean;
}
export interface ReaderExerciseImportResult {
  extractionId: string;
  items: ReaderExerciseImportedItem[];
  skipped: ReaderExerciseImportSkip[];
  warnings: string[];
  anchorStatus: string;
}
export interface ReaderExerciseImportStatusDto {
  version?: number;
  status: string;
  phase?: string | null;
  message?: string | null;
  result?: ReaderExerciseImportResult | null;
  error?: { code?: string; message?: string } | null;
}
export interface ReaderAuthorQAInput {
  question: string;
  answer: string;
  sourceId?: string | null;
  revisionId?: string | null;
  annotationId?: string | null;
  subjectId?: string | null;
  depthPreset?: string;
  clientIdempotencyKey?: string | null;
  /** File the card under this Learning Object instead of the passage's provenance. */
  learningObjectId?: string | null;
}
export interface ReaderAuthoredCardDto {
  version?: number;
  commitmentId: string;
  familyId: string;
  cardId: string;
  cardVersionId: string;
  lineageId: string;
  authorship: string;
  pinned: boolean;
  authoredBeforeAi: boolean;
  contract: Record<string, unknown>;
  /** `scheduled`: a Practice Item the scheduler serves; `reference_only`: no
   *  active Learning Object covers the passage, so it is kept as a reference. */
  practiceStatus: "scheduled" | "reference_only";
  practiceItemId: string | null;
  learningObjectId: string | null;
}
export interface ReaderCoachSuggestion {
  kind: string;
  prompt: string;
}
export interface ReaderCoachLintDto {
  version?: number;
  level: string;
  suggestions: ReaderCoachSuggestion[];
  blocking: boolean;
}
export interface ReaderMaintainInput {
  action: string;
  lineageId?: string | null;
  fromCardVersionId?: string | null;
  toCardVersionId?: string | null;
  prevContract?: Record<string, unknown> | null;
  newContract?: Record<string, unknown> | null;
  intoLineageId?: string | null;
  mergedCardVersionId?: string | null;
  splitCardVersionId?: string | null;
  forkedCardVersionId?: string | null;
  commitmentId?: string | null;
  policy?: string | null;
  bounds?: Record<string, unknown> | null;
}
export interface ReaderArcDto {
  version?: number;
  arcId: string;
  commitmentId: string;
  sourceId?: string | null;
  stages: string[];
  reachedStages?: string[];
  currentStage: string | null;
  policy: string | null;
  disposition?: string;
  paused?: boolean;
  nextReviewedEdge?: Record<string, unknown> | null;
  [k: string]: unknown;
}
export interface ReaderRestorationAnnotationDto {
  annotationId: string;
  anchorStatus: string | null;
  provenance: string;
  learnerText?: string | null;
  whatIThinkIsGoingOn?: string | null;
  quote?: string | null;
  spanId?: string | null;
  sourceText?: string | null;
  reason?: string;
}
export interface ReaderRestorationDto {
  version?: number;
  sourceId: string;
  runId?: string | null;
  achievedMilestone?: string | null;
  boundaryDiff?: Record<string, unknown> | null;
  sourceNeighborhoods?: Record<string, unknown> | null;
  annotations: ReaderRestorationAnnotationDto[];
  anchorNeedsReview: ReaderRestorationAnnotationDto[];
  observationMutated: boolean;
  allows: string[];
  eventId: string;
}
export interface ReaderSetModeResultDto {
  version?: number;
  eventId: string;
  mode: string;
  presentsOwnerQuestions: string;
}
export interface ReaderQuestionControlResultDto {
  version?: number;
  eventId: string;
  control: string;
  routesTo: string | null;
  signal: string;
}
export interface ReaderEnqueueRequestInput {
  sourceId: string;
  revisionId: string;
  extractionId: string;
  spanId: string;
  preset: string;
  provider?: string;
  model?: string;
  annotationId?: string | null;
  commitmentId?: string | null;
  clientIdempotencyKey?: string | null;
}
export interface ReaderRequestScopeDto {
  spanIds: string[];
  sectionPath: string[];
  assets: string[];
  adjacentBlocks: number;
}
export interface ReaderEnqueueRequestDto {
  version?: number;
  requestId: string;
  requestKey: string;
  deduplicated: boolean;
  cacheHit: boolean;
  status: string;
  scope: ReaderRequestScopeDto;
  estInputTokens: number;
  estOutputTokens: number;
  tokenCap: number;
  capRemaining: number;
  capped: boolean;
  provider: string;
  model: string;
}
export interface ReaderRequestRow {
  id: string;
  status: string;
  preset: string;
  resultJson?: string | null;
  errorJson?: string | null;
  cacheHit?: number;
  estInputTokens?: number;
  estOutputTokens?: number;
  tokenCap?: number;
  reason?: string | null;
  [k: string]: unknown;
}

/** Deterministic owner-review authoring stubs (§C). */
export interface StubDiagnosticPackDto {
  packSlug: string;
  cards: Array<{ cardSlug: string; coverage: string[] }>;
}
export interface StubPoolSurfacesDto {
  poolSlug: string;
  surfaces: Array<{ surfaceSlug: string; angle: string }>;
}

// ── Diagnosis adjudication (spec_diagnostic_augmentation_v1 §2 A4) ────────────
// `adjudication.queue | record | scoreboard`. The verdict vocabulary is
// partitioned: the four filled verdicts are recordable only against a diagnosis
// that named a cause, the two abstention verdicts only against an abstention.
// The overlay never derives that partition itself — every case carries the
// `allowedVerdicts` the store will accept for it.

export type AdjudicationVerdict =
  | "correct"
  | "wrong_anchor"
  | "wrong_repair"
  | "should_have_abstained"
  | "correctly_abstained"
  | "should_not_have_abstained";

/** learner_contest | system_abstention | anchor_disagreement | incomplete_repair_mapping | sampled | manual */
export type AdjudicationQueueReason = string;

export interface AdjudicationAnchorDto {
  anchorKind: string;
  criterionId?: string;
  quote?: string | null;
  normalizedQuote?: string | null;
  checkpointId?: string | null;
  charStart?: number | null;
  charEnd?: number | null;
  [k: string]: unknown;
}

export interface AdjudicationRepairClassOptionDto {
  id: string;
  operator?: string | null;
  expectedMinutes?: number | null;
  targetRefs?: unknown[];
}

export interface AdjudicationShownToLearnerDto {
  /** false when the receipt did not permit a learner-facing causal overlay. */
  rendered: boolean;
  feedbackMd: string | null;
  hypotheses: Array<{
    hypothesisId?: string | null;
    label?: string | null;
    statement?: string | null;
    traceConsistency?: string | null;
  }>;
  proposedNextAction: {
    label?: string;
    operator?: string | null;
    rationale?: string | null;
    repairClassId?: string | null;
  } | null;
  firstDivergence: AdjudicationAnchorDto | null;
  repairedTrace: Record<string, unknown> | null;
}

export interface AdjudicationCaseDto {
  attemptId: string;
  queueReason: AdjudicationQueueReason;
  priority: number;
  detail: string;
  createdAt: string;
  learningObjectId: string | null;
  learningObjectTitle: string | null;
  practiceItemId: string | null;
  prompt: string | null;
  learnerAnswerMd: string | null;
  rubricScore: number | null;
  correctness: number | null;
  systemAbstained: boolean;
  abstentionBasis: string;
  systemAnchor: AdjudicationAnchorDto | null;
  anchorDisagreement: boolean;
  systemRepairClassId: string | null;
  incompleteRepairMapping: boolean;
  repairClassOptions: AdjudicationRepairClassOptionDto[];
  shownToLearner: AdjudicationShownToLearnerDto;
  learnerReport: { id?: string; response?: string; createdAt?: string; [k: string]: unknown } | null;
  allowedVerdicts: AdjudicationVerdict[];
  /** The frozen system-side snapshot pinned with any verdict on this case. */
  system: Record<string, unknown>;
}

export interface AdjudicationQueueDto {
  version?: number;
  total: number;
  countsByReason: Array<{ reason: AdjudicationQueueReason; count: number }>;
  cases: AdjudicationCaseDto[];
}

export interface AdjudicationRecordInput {
  attemptId: string;
  verdict: AdjudicationVerdict;
  anchor?: {
    anchorKind: string;
    criterionId?: string;
    quote?: string | null;
    checkpointId?: string | null;
    charStart?: number | null;
    charEnd?: number | null;
  } | null;
  repairMd?: string | null;
  repairClassId?: string | null;
  queueReason?: AdjudicationQueueReason | null;
  adjudicatorSource?: "human_owner" | "independent_expert" | "deterministic_verifier";
  rationale?: string | null;
}

/** What §5.6 arm (d) actually did to belief state — never inferred from the verdict. */
export interface AdjudicationBeliefEffectDto {
  arm: string;
  attemptId: string;
  verdict: AdjudicationVerdict | null;
  promoted: string[];
  withdrawn: string[];
  declined: string[];
}

export interface AdjudicationOutcomeDto {
  status: "promoted" | "withdrawn" | "no_belief_change" | "effect_failed";
  message: string;
  beliefIds: string[];
  /** A withdrawal is narrated to the learner only if the belief was surfaced. */
  learnerCorrectionPending: boolean;
  declined: string[];
}

export interface AdjudicationRecordResultDto {
  version?: number;
  adjudication: {
    id: string;
    attemptId: string;
    verdict: AdjudicationVerdict;
    queueReason: AdjudicationQueueReason;
    supersedesId?: string | null;
    learnerReportId?: string | null;
    adjudicatedAnchor?: AdjudicationAnchorDto | null;
    adjudicatedRepairClassId?: string | null;
    [k: string]: unknown;
  };
  effect: AdjudicationBeliefEffectDto | null;
  outcome: AdjudicationOutcomeDto;
}

export interface AdjudicationScoreboardGroupDto {
  scope?: string;
  gradingPromptVersion?: string;
  graderModel?: string;
  queueReason?: AdjudicationQueueReason;
  records: number;
  byVerdict: Array<{ verdict: AdjudicationVerdict; count: number }>;
  byQueueReason: Array<{ reason: AdjudicationQueueReason; count: number }>;
  anchorScored: number;
  anchorCorrect: number;
  repairIdScored: number;
  repairIdMatch: number;
  abstentionConfusion: { tp: number; fp: number; fn: number; tn: number };
  // Every rate is null — never a flattering 1.0 — on an empty denominator.
  firstDivergenceAnchorAccuracy: number | null;
  repairClassMatchRate: number | null;
  repairClassIdMatchRate: number | null;
  abstentionPrecision: number | null;
  abstentionRecall: number | null;
  abstentionCasesPresent: boolean;
}

export interface AdjudicationScoreboardDto {
  version?: number;
  storeVersion: string;
  groupBy: string | null;
  overall: AdjudicationScoreboardGroupDto;
  groups: AdjudicationScoreboardGroupDto[];
}

// ── Daily-loop DL1: the finite daily plan (spec_daily_loop_v1.md §6, §7) ─────
// Every count and minute figure Start, Today, the done screen and the re-entry
// panel show is read from these DTOs (gate G3); the client computes none.

export type PlanLane = "repair" | "maintain" | "new" | "push";

export interface PlanSplitLaneDto {
  lane: PlanLane;
  minutes: number;
  /** Whole minutes for the split line; they add up to the rounded total. */
  displayMinutes: number;
  load: number | null;
  cap: number | null;
  /** One-line plain-language reason (the "why"). */
  reason: string | null;
}

export interface PlanReadingDto {
  sourceId: string | null;
  extractionId: string | null;
  sectionId: string | null;
  sectionTitle: string | null;
  wordsLeft: number | null;
  partial: boolean;
  startSpanId?: string | null;
  fullMinutes?: number | null;
  spansSeen?: number;
  spanCount?: number;
}

export interface PlanItemDto {
  practiceItemId: string;
  learningObjectId: string;
  learningObjectTitle: string;
  practiceMode: string | null;
  promptPreview: string;
  lane: PlanLane | null;
  estMinutes: number;
  state: "planned" | "served" | "done" | "skipped" | "displaced";
  origin: "chooser" | "requested" | "followup" | "learner_pick";
  servedAt: string | null;
  doneAt: string | null;
}

export interface PlanBlockDto {
  id: string;
  ordinal: number;
  lane: PlanLane | null;
  action: string;
  subtype: string | null;
  chosenBy: string;
  why: string;
  whyKind: string | null;
  /** Router R2a: the receipts behind the why ("details"), or null. */
  whyDetails?: string | null;
  fallback: boolean;
  estMinutes: number;
  status: "done" | "current" | "upcoming";
  startedAt: string | null;
  endedAt: string | null;
  outcome: string | null;
  reading: PlanReadingDto | null;
  learningObjectTitles: string[];
  items: PlanItemDto[];
  displacedCount: number;
}

export interface PlanProjectedBlockDto {
  ordinal: number;
  lane: PlanLane;
  estMinutes: number;
  itemCount: number;
  learningObjectTitles: string[];
  readingTitle: string | null;
  why: string;
}

export interface PlanItemStepDto {
  kind: "item";
  planId: string | null;
  blockId: string | null;
  blockOrdinal?: number;
  practiceItemId: string;
  learningObjectId: string;
  learningObjectTitle?: string;
  practiceMode?: string | null;
  estMinutes?: number;
  origin: string;
  schedulerCandidateId: string | null;
  /** Router R2a: the receipt an answer binds to; null until the item is served. */
  presentationId?: string | null;
  /** The first item of a block not started yet: show the block line first. */
  boundary: boolean;
}

export interface PlanReadingStepDto {
  kind: "reading";
  planId: string;
  blockId: string;
  blockOrdinal: number;
  reading: PlanReadingDto;
  estMinutes: number;
  boundary: boolean;
}

export interface PlanDoneStepDto {
  kind: "done";
  planId: string;
  status: string;
  stopReason: string | null;
}

/** UX Phase 4 round 7: nothing to do until a hold on the plan's last item
 *  (its answer was shown recently) lifts later today. The plan stays open. */
export interface PlanWaitingStepDto {
  kind: "waiting";
  planId: string;
  /** When the hold lifts (UTC). */
  until: string;
  minutes: number;
  practiceItemId: string;
  learningObjectId: string | null;
  learningObjectTitle: string | null;
}

/** The plan body's view of the waiting step. */
export interface PlanWaitingDto {
  until: string;
  minutes: number;
  practiceItemId: string;
  learningObjectTitle: string | null;
}

export type PlanStepDto = PlanItemStepDto | PlanReadingStepDto | PlanDoneStepDto | PlanWaitingStepDto;

export interface PlanTotalsDto {
  plannedMinutes: number;
  plannedItems: number;
  doneItems: number;
  skippedItems: number;
  displacedItems: number;
  readingBlocks: number;
  readingBlocksEnded: number;
  estMinutesDone: number;
  actualMinutes: number;
}

export interface PlanReentryDto {
  gapDays: number;
  solidCount: number;
  slippedCount: number;
  slippedNames: string[];
  namedBy: string;
  target: number;
  /** Today's re-entry: the chosen blocks plus the projected ones. */
  planMinutes: number;
  planItems: number;
}

export interface DailyPlanBodyDto {
  id: string;
  localDate: string;
  kind: "normal" | "reentry" | "keep_going";
  status: "open" | "complete" | "stopped" | "abandoned";
  stopReason: string | null;
  parentPlanId: string | null;
  minutesBudget: number;
  rememberedMinutes: number;
  minutesSource: "chip" | "carried" | "generated";
  minuteChoices: number[];
  minutesLeft: number;
  split: {
    rule: string | null;
    line: string;
    lanesAllowed: PlanLane[];
    requestedMinutes: number;
    lanes: PlanSplitLaneDto[];
  };
  admission: {
    admittedCount: number;
    exemptRequests: number;
    stoppedBy: string | null;
    floorApplied: boolean;
    reviewLoadPerDay: number | null;
    ceilingMinutes: number | null;
    override: string | null;
  };
  blocks: PlanBlockDto[];
  currentBlockId: string | null;
  /** Router R2b: the next block is still being chosen (its models are out); Begin decides it at once. */
  deciding?: boolean;
  /** UX Phase 4 round 7: nothing to do until a hold lifts later today (null otherwise). */
  waiting?: PlanWaitingDto | null;
  projected: PlanProjectedBlockDto[];
  /** "Block 2 of about N": chosen plus projected. */
  blockCountEstimate: number;
  firstBlock: { title: string | null; lane: PlanLane | null; itemCount: number; estMinutes: number; reading: boolean } | null;
  nextStep: PlanStepDto | null;
  totals: PlanTotalsDto;
  reentry: PlanReentryDto | null;
  source: string | null;
  chooser: string | null;
}

export interface DailyPlanDto {
  version: number;
  enabled: boolean;
  /** Present when the plan is off: "plan_disabled" or "algorithm_version". */
  reason?: string;
  headlineEnabled?: boolean;
  localDate?: string;
  plan: DailyPlanBodyDto | null;
  day?: PlanTotalsDto & { plans: number; kinds: string[]; complete: boolean };
  streak?: StreakSummary | null;
  /** next_plan_item / plan_learner_pick / plan_reading_ended: the typed step (null while the next block is being chosen). */
  step?: PlanStepDto | null;
  /** plan_more_new: the trade-off shown before anything is added. */
  preview?: {
    items: number;
    estMinutes: number;
    addsMinutesPerDay: number;
    horizonDays: number;
    available: boolean;
    practiceItemIds?: string[];
  };
}

export interface TodayHeadlineDto {
  version: number;
  enabled: boolean;
  counts?: { demonstrated: number; assumed?: number; learning: number; untested: number };
  showAssumed?: boolean;
  expectedRecall?: number | null;
  expectedRecallPercent?: number | null;
  expectedRecallItems?: number;
  expectedRecallTooltip?: string;
  line?: string;
}

// -- Reader workbench RW2a: the resumable scratchpad (spec_reader_workbench_v1 §5.1, §5.7) --

export type WorkbenchOrigin = "reader" | "practice" | "plan";
export type WorkbenchEntry =
  | "work_through"
  | "resume"
  | "check_me"
  | "practice_this"
  | "path_exercise"
  | "discriminating_problem"
  | "practice_screen"
  | "plan";
export type WorkbenchStatus = "open" | "submitted" | "abandoned";
export type WorkbenchImportStatus = "none" | "pending" | "bound" | "failed";
export type WorkbenchStepKind = "step" | "stuck";

export interface WorkbenchStepVersionDto {
  stepId: string;
  bodyMd: string;
  createdAt: string;
}

export interface WorkbenchStepDto {
  /** The newest version's row id (what an edit supersedes). */
  stepId: string;
  /** The step's first row: a stable key across its versions. */
  chainId: string;
  ordinal: number;
  kind: WorkbenchStepKind;
  bodyMd: string;
  deleted: boolean;
  createdAt: string;
  editedAt: string;
  /** Earlier texts, newest first (shown dimmed on request). */
  versions: WorkbenchStepVersionDto[];
}

/** What the attempt will record, stated before Submit (spec §5.1, G62). */
export interface WorkbenchRecordDto {
  bookCounted: boolean;
  bookVisible: boolean;
  hints: number;
  questionHints: number;
  /** The answer box's hints shown before working in steps (review F2). */
  carriedHints?: number;
  /** Reader CA2 fix F1/F15: an earlier attempt's help opened before Submit, its own component (0 or 1). */
  earlierHints?: number;
  ownAttempt: boolean;
  line: string;
  footer: string;
  stuckNote: string | null;
  /** RW2b: the problem's own shown checks and hints (only when it has any). */
  help?: { checks: number; byLevel: number[]; worked: number; primed: boolean };
}

export interface WorkbenchPartDto {
  practiceItemId: string;
  title: string;
  prompt: string;
}

export interface WorkbenchSessionDto {
  version?: number;
  sessionId: string;
  practiceItemId: string | null;
  stemMd: string;
  importStatus: WorkbenchImportStatus;
  importError: string | null;
  origin: WorkbenchOrigin;
  entry: WorkbenchEntry;
  parentSessionId: string | null;
  extractionId: string | null;
  spanIds: string[];
  sourceVisible: boolean;
  sourceHiddenAt: string | null;
  sourceShownAt: string | null;
  practiceSessionId: string | null;
  /** The assessment contract the session shows (review F1). */
  assessmentContractVersionId?: string | null;
  /** The answer box's authored hints revealed before working in steps
   *  (review F2): the answer box's reveal index on the way back, nothing else. */
  carriedHints?: number;
  /** Reader CA2 fix F15: the answer box's draft opened an earlier attempt's
   *  help and the problem carries it as its own component (never an authored reveal). */
  earlierOpened?: boolean;
  /** The serve the problem answers, kept across a resume (review F13). */
  schedulerCandidateId?: string | null;
  planPresentationId?: string | null;
  helpStyle: string | null;
  status: WorkbenchStatus;
  attemptId: string | null;
  createdAt: string;
  updatedAt: string;
  closedAt: string | null;
  steps: WorkbenchStepDto[];
  lastEditedStepId: string | null;
  record: WorkbenchRecordDto;
  /** A multi-part import asks which part this problem is. */
  parts: WorkbenchPartDto[] | null;
  sourceId: string | null;
  /** Reader CA1 (§12.4): the learner-drawn sub-box a region selection was
   *  imported with (absent otherwise). */
  printRegion?: PrintRegionDto;
  /** Once bound: the item's whole frozen presentation (review F9). */
  presentation?: ItemPresentationDto | null;
  /** RW4b: a textbook exercise picked from a proposal ("use this one"): the
   *  sources service's import and the answer key's honest status. Absent on
   *  every other problem. */
  sourceExercise?: WorkbenchSourceExerciseDto;
  /** RW4b: present on a problem opened from a textbook exercise the learner
   *  picked in the Reader (either path). */
  exercisePick?: WorkbenchExercisePickDto;
}

export interface WorkbenchSourceExerciseDto {
  proposalId: string | null;
  importId: string | null;
  /** The import row's status: authoring, checking, written, rejected, failed. */
  importStatus: string | null;
  reason: string | null;
  /** book_solution, checked, panel_agrees, panel_agrees_unconfirmed, checking,
   *  model_answer, disputed, changed_since_check. */
  keyStatus: string | null;
  keyLabel: string;
}

/** One unfinished problem: the ✎ mark, the rail, the practice card, RW6a's recap. */
export interface WorkbenchSummaryDto {
  sessionId: string;
  status: WorkbenchStatus;
  practiceItemId: string | null;
  stemMd: string;
  origin: WorkbenchOrigin;
  entry: WorkbenchEntry;
  extractionId: string | null;
  spanIds: string[];
  importStatus: WorkbenchImportStatus;
  sourceVisible: boolean;
  /** The book counted on this problem: the answer box counts it too (review F2). */
  bookCounted?: boolean;
  stepCount: number;
  createdAt: string;
  updatedAt: string;
  /** Open and untouched for longer than workbench.open_session_days. */
  unfinished: boolean;
}

/** UX Phase 3: an open problem with the source it opens in (Today's threads). */
export interface WorkbenchOpenProblemDto extends WorkbenchSummaryDto {
  sourceId: string;
}

export interface WorkbenchOpenInput {
  origin: WorkbenchOrigin;
  entry: WorkbenchEntry;
  /** Resume this session on the asking surface (reopened when set aside,
   *  moved when it was worked on another surface; review F4). */
  sessionId?: string | null;
  /** The answer box's hints the learner saw before working in steps. */
  carriedHints?: number;
  /** The practice screen's open practice session, whose draft the steps
   *  take over (Reader CA2 re-review F1: the server carries an earlier
   *  attempt's help it opened onto the problem). */
  practiceSessionId?: string | null;
  /** A book a problem left for the answer box counted (review F2). */
  carriedBook?: boolean;
  /** The answer box's draft key handed to the steps (Astra batch review):
   *  the problem keeps the draft's Ask thread and budget in every host. */
  submissionId?: string | null;
  /** The serve the problem answers, kept on it for a resume (review F13).
   *  One pair (review F15): send both (a null included) to replace the pair
   *  the problem holds, or neither to keep it. */
  schedulerCandidateId?: string | null;
  planPresentationId?: string | null;
  stemMd?: string | null;
  practiceItemId?: string | null;
  extractionId?: string | null;
  spanIds?: string[];
  parentSessionId?: string | null;
  sourceVisible?: boolean | null;
  clientIdempotencyKey?: string | null;
  importRequest?: ReaderImportExerciseInput | null;
  /** RW4b: a textbook exercise picked from a find_practice proposal; the
   *  sources service's import runs while the problem is open. */
  sourceExercise?: { proposalId: string; extractionId: string; spanIds: string[] } | null;
  /** RW4b: a fallback exercise the learner picked: its listing's `pick`, sent
   *  back as it came (beside its importRequest). */
  exercisePick?: ExercisePickDto | null;
}

/** RW4b fix round 4 (R1): `workbench.admit`, the server's one admission of a
 *  picked exercise's owed learner pick, for the problem named by its id. */
export interface WorkbenchAdmitDto {
  version?: number;
  session: WorkbenchSessionDto;
  /** The practice session the pick was made in (started when none was open). */
  practiceSession: SessionSnapshot | null;
}

// -- Reader workbench RW4b: exercises from my sources (spec §7.4, UX §4.6) --

/** What a fallback candidate carries for "use this one" (its listing's own
 *  exposure rows never count against the pick; the server checks them). */
export interface ExercisePickDto {
  learningObjectIds: string[];
  shownEventIds: string[];
}

/** RW4b: a textbook exercise the learner picked, as the problem keeps it. */
export interface WorkbenchExercisePickDto {
  /** The proposal it came from; null for the fallback's. */
  proposalId: string | null;
  /** The exposure rule read on the server at the pick, then at admission. */
  exposure: ExerciseExposureDto | null;
  exposureChecked: "selection" | "admission" | null;
  /** The learner pick of the item its import wrote was delivered. */
  admitted: boolean;
  /** Bound and the pick still owed: the shell picks it, once (durable). */
  due: boolean;
}

/** The sources service's exposure rule, as the Reader shows it. */
export interface ExerciseExposureDto {
  exposed: boolean;
  reasons: string[];
  /** One honest line for the first reason, or null when unexposed. */
  label: string | null;
  /** "you read a worked example like this one": a note, not an exclusion. */
  note: string | null;
  /** How "use this one" offers it: an exposed exercise is practice beside the
   *  book, never a check on your own. */
  offeredAs: "practice" | "check_on_your_own";
  exposureRuleVersion: string;
}

export interface ExerciseCandidateViewDto {
  key: string;
  extractionId: string;
  spanIds: string[];
  sourceId: string | null;
  revisionId: string | null;
  exposure: ExerciseExposureDto;
}

export interface ExerciseCandidatesDto {
  version: number;
  proposalId: string;
  /** Only these may be shown: the others were exam or held-out material. */
  candidates: ExerciseCandidateViewDto[];
  withheld: number;
}

/** A fallback candidate ("find an exercise in my sources"). */
export interface FoundExerciseDto {
  key: string;
  extractionId: string;
  spanIds: string[];
  sourceId: string | null;
  revisionId: string | null;
  sourceTitle: string | null;
  page: number | null;
  label: string;
  statement: string;
  exposure: ExerciseExposureDto;
  /** What "use this one" sends to the Reader's own import (import_exercises). */
  importRequest: ReaderImportExerciseInput;
  /** What "use this one" sends back with it (workbench.open's exercisePick). */
  pick: ExercisePickDto;
}

export interface FindExercisesDto {
  version: number;
  status: "ok" | "none_found";
  policy: string;
  candidates: FoundExerciseDto[];
  dropped: Record<string, number>;
}

export interface WorkbenchSaveStepInput {
  sessionId: string;
  clientIdempotencyKey: string;
  op: "add" | "edit" | "delete" | "restore";
  stepId?: string | null;
  afterStepId?: string | null;
  kind?: WorkbenchStepKind;
  bodyMd?: string | null;
}

export interface WorkbenchSaveStepDto {
  version?: number;
  step: WorkbenchStepDto;
  savedAt: string;
  record: WorkbenchRecordDto;
}

export interface WorkbenchSubmitInput {
  sessionId: string;
  practiceSessionId?: string | null;
  answerConfidence?: number | null;
  latencySeconds?: number | null;
  /** The serve this submit answers, as one pair (review F15): both, or
   *  neither to answer the serve the problem kept. */
  schedulerCandidateId?: string | null;
  planPresentationId?: string | null;
}

export interface WorkbenchSubmitDto {
  version?: number;
  attempt: AttemptResultDto;
  session: WorkbenchSessionDto;
  practiceSession: SessionSnapshot | null;
}

// ── Reader workbench RW6a: "Last time here" and Wrap up (spec §9.1) ──────────

/** One reader session: a visit on a source, or visits less than 30 minutes apart. */
export interface ReaderRecapSessionDto {
  sessionId: string;
  extractionId: string;
  visitIds: string[];
  startedAt: string;
  endedAt: string;
  minutes: number;
}

/** Still open: an inquiry's root, in the learner's own words. */
export interface ReaderRecapOpenDto {
  rootExchangeId: string;
  questionEventId: string | null;
  questionMd: string;
  spanId: string;
  anchorSpanIds: string[];
  openedAt: string | null;
}

/** Unfinished: an open workbench problem on this source, or one set aside
 *  (abandoned: its steps kept, "Reopen this problem"; review F8). */
export interface ReaderRecapUnfinishedDto {
  sessionId: string;
  status?: "open" | "abandoned";
  title: string;
  stepCount: number;
  help: { bookCounted: boolean; hints: number };
  helpLine: string;
  unfinished: boolean;
  spanIds: string[];
  updatedAt: string;
}

/** The kinds of ReaderObservationV1 (spec §9.1). */
export type ReaderObservationKind =
  | "still_unclear" | "next_step_missed" | "why_step_missed" | "assumption_missed" | "prediction_missed"
  | "check_questionable" | "hint_taken" | "doesnt_connect" | "discriminate_answer";

/** Worth a second look: one formative record (routing only). */
export interface ReaderRecapSecondLookDto {
  kind: ReaderObservationKind;
  rootExchangeId: string | null;
  spanId: string | null;
  questionMd: string | null;
  observedAt: string;
  sourceEventIds: string[];
  observed?: Record<string, unknown>;
}

/** Since last time: an LO demonstrated on your own since the session ended. */
export interface ReaderRecapDemonstratedDto {
  learningObjectId: string;
  title: string;
  demonstratedOn: string;
  /** The certifying attempt (the point at which the LO's recipe was met). */
  attemptId: string | null;
}

export interface ReaderRecapCardDto {
  recapVersion: string;
  extractionId: string;
  session: ReaderRecapSessionDto;
  continueAt: { sectionId: string; label: string | null } | null;
  stillOpen: ReaderRecapOpenDto[];
  unfinished: ReaderRecapUnfinishedDto[];
  worthASecondLook: ReaderRecapSecondLookDto[];
  sinceLastTime: {
    demonstrated: ReaderRecapDemonstratedDto[];
    checksRetired: Array<{ commitmentId: string; retiredAt: string; solvedAttemptId?: string | null }>;
  };
}

export interface ReaderRecapDto {
  version: number;
  recap: ReaderRecapCardDto | null;
  dismissed: boolean;
}

export type ReaderRecapEvent = "recap_shown" | "recap_dismissed" | "wrap_up_opened";

/** One action on a Wrap up line: the RPC the same chip calls elsewhere (none for keep open). */
export interface ReaderWrapUpActionDto {
  action: "undo" | "resolve" | "revisit_once" | "keep_open";
  rpc?: string;
  params?: Record<string, unknown>;
  /** "reader": only where the open reading is (the preset needs it). */
  where?: string;
}

export interface ReaderWrapUpInquiryLineDto {
  rootExchangeId: string;
  questionMd: string;
  spanIds?: string[];
  actions: ReaderWrapUpActionDto[];
}

export interface ReaderWrapUpReinforceLineDto {
  kind: string;
  marker: string;
  sessionId?: string;
  title?: string;
  status?: string;
  helpLine?: string;
  facetId?: string;
  basis?: string;
  attemptIds?: string[];
  spanIds?: string[];
  observed?: Record<string, unknown>;
}

export interface ReaderWrapUpDto {
  version: number;
  wrapUpVersion: string;
  available: boolean;
  extractionId: string;
  session: ReaderRecapSessionDto | null;
  resolved: ReaderWrapUpInquiryLineDto[];
  stillOpen: ReaderWrapUpInquiryLineDto[];
  worthReinforcing: ReaderWrapUpReinforceLineDto[];
}

export interface ReaderWrapUpOfferDto {
  version: number;
  offer: { extractionId: string; sourceId: string | null; session: ReaderRecapSessionDto } | null;
}

// ── Reader workbench RW4a: ask your library, compare, the tutor ────────────
// spec_reader_workbench_v1 §7.3; UX §4.5, W9, W10.

export type LibraryAskEntry =
  | "library_search"
  | "reader"
  | "where_else_explained"
  | "where_is_this_used"
  | "what_do_i_need_first";
export type LibraryExpansion = "prerequisites" | "applications" | "confusables";

export interface LibraryHitDto {
  key: string;
  extractionId: string;
  spanId: string;
  sourceId: string | null;
  sourceTitle: string | null;
  section: string | null;
  page: number | null;
  text: string;
  role: string | null;
  group: string;
  expansion: LibraryExpansion | null;
  learningObjectIds: string[];
  authorship: "source";
  label: string;
  /** RW4e (roles.positive_filter_enabled): the passage's best instructional-role
   *  proposal when its ingest role is ordinary prose; absent otherwise. */
  proposedRole?: ProposedRoleDto | null;
}

/** RW4e: an instructional role LearnLoop's model proposed for a passage (a
 *  source-object proposal, labelled "model's label"; never an exclusion). */
export interface ProposedRoleDto {
  role: string;
  confidence: "high" | "medium" | "low" | null;
  judges: string[];
  label: string;
}

export interface LibraryExpansionDto {
  expansion: LibraryExpansion;
  label: string;
  learningObjects: Array<{ learningObjectId: string; title: string; demonstrated: boolean | null; keys: string[] }>;
}

export interface LibraryAskDto {
  version?: number;
  askId: string;
  query: string;
  entry: LibraryAskEntry;
  status: string;
  policy: string;
  personalized: boolean;
  basis: string;
  hits: LibraryHitDto[];
  learningObjectIds: string[];
  extractionId: string | null;
  anchorSpanIds: string[];
  groups: {
    sources: Array<{ sourceId: string | null; sourceTitle: string | null; groups: Array<{ group: string; keys: string[] }> }>;
    expansions: Array<{ expansion: LibraryExpansion; label: string; keys: string[] }>;
  };
  expansions: LibraryExpansionDto[];
  expandGraph: boolean;
  sourceCount: number;
  passageCount: number;
  /** RW4d: kept comparisons sharing these passages ("you compared these on 3 Oct"); absent while off. */
  comparedOn?: Array<{ askId: string; keptAt: string; keys: string[] }>;
}

export interface LibraryNoteDto {
  key: string;
  verdict: "contributes" | "related" | "unrelated" | null;
  ledgerId: string | null;
  line: string | null;
  roles: string[];
  speaksTo: { id: string; statement: string } | null;
  label: string;
  /** RW5b: the organizer judged this equation or figure block explorable (present only while figures.offers_enabled is on). */
  explorable?: boolean;
}

export interface LibraryNotesDto {
  version?: number;
  askId: string;
  status: string;
  reason?: string | null;
  notes: LibraryNoteDto[];
  order: string[];
  droppedLines?: Array<{ key: string; reason: string }>;
  personalized?: boolean;
  reused?: boolean;
}

export interface CompareCellDto {
  line: string | null;
  quote: string | null;
  perspective?: string | null;
  relation?: string | null;
  otherSourceTitle?: string | null;
  authorship: "ai";
}

export interface CompareTableDto {
  version?: number;
  askId: string;
  status: string;
  comparisonId: string | null;
  header: string;
  rows: Array<{
    sourceId: string | null;
    sourceTitle: string | null;
    key: string;
    page: number | null;
    isOpenSource: boolean;
    contributes: CompareCellDto[];
    assumes: CompareCellDto[];
    differs: CompareCellDto[];
  }>;
  alsoDiscussedIn: Array<Record<string, unknown>>;
  /** Sources whose passages could not be checked: possible matches, not compared. */
  unverifiedSources: Array<{ sourceId?: string | null; sourceTitle?: string | null; extractionId?: string; spanId?: string; label?: string }>;
  droppedPins: Array<Record<string, unknown>>;
  droppedLineCount: number;
  /** How the counterparts' verification went (capped, unreachable, timed out, …). */
  verification?: { status: string | null; stopped: string | null; verifiedSources?: number | null };
  exposureEventIds?: string[];
  /** RW4d: the perspectives asked for, and those no source covered (only when some were asked). */
  requestedPerspectives?: string[];
  missingPerspectives?: string[];
  /** RW4d: whether this comparison is kept (absent while reader_compare.keep_enabled is off). */
  kept?: KeptComparisonDto | null;
  /** RW4d (a reopened kept comparison): its kept relations with their fine labels. */
  keptRelations?: Array<{ fine: string; relationType: string; statement: string | null }>;
  query?: string | null;
}

/** RW4d (spec §7.8): a kept comparison, as proposals (ids, types, fine labels, the learner's takes). */
export interface KeptComparisonDto {
  askId: string;
  keptAt: string;
  objects: Array<{ id: string; key: string; objectType: "claim" | "definition"; sourceTitle: string | null }>;
  relations: Array<{ id: string; relationType: string; fine: string }>;
  takes: Array<{ id: string; keys: string[]; learnerText: string }>;
  notKept: number;
  status: "proposed";
  label: string;
}

export interface KeepComparisonResultDto {
  version?: number;
  askId: string;
  kept: KeptComparisonDto;
  addedTakes: number;
  alreadyKept: boolean;
  toolCallId?: string;
}

export interface KeptMarkDto {
  spanId: string;
  /** Every comparison kept on this passage, newest first. */
  askIds: string[];
  keptAt: string;
  otherSources: string[];
  /** Each kept comparison on this passage, told apart by its question and date (newest first). */
  comparisons?: Array<{ askId: string; keptAt: string; query: string | null; otherSources: string[] }>;
}

export interface KeptMarksDto {
  version?: number;
  extractionId: string;
  marks: KeptMarkDto[];
  label: string;
}

/** Reader workbench RW7a (spec §10.1; UX §4.11): the depth the path is for. */
export type ReadingPathDepth = "get_the_idea" | "learn_to_use_it" | "fluency";
/** A section's label; "already_shown" only when every LO it teaches is demonstrated (code's rule). */
export type ReadingPathLabel = "core" | "prerequisite" | "enrichment" | "already_shown" | "assumed";
/** "read it anyway" / "skip it"; "none" clears an earlier choice. */
export type ReadingPathChoice = "read_anyway" | "skip" | "none";

/** The exercise worth trying after a core section (an exercise block of it), re-read now. */
export interface ReadingPathExerciseDto {
  label: string;
  extractionId: string;
  spanIds: string[];
  page: number | null;
  /** The exercise's own words, verbatim and whole (the workbench's stem;
   *  Codex review F2: never clipped, a late condition is part of the problem). */
  statement: string;
  /** The statement clipped for a preview (600 characters at most); never the stem. */
  preview: string;
  /** "Try it": the Reader's own import of a selected problem. */
  importRequest: ReaderImportExerciseInput;
}

export interface ReadingPathSectionDto {
  sectionId: string;
  title: string;
  startSpanId: string;
  label: ReadingPathLabel;
  /** core · prerequisite · enrichment · already shown ● · assumed */
  chip: string;
  /** One line: why. */
  reason: string;
  /** Who wrote that line: "model" (shown as the model's reading) or "code"
   *  (the evidence lines, a changed label's line, and the neutral line that
   *  replaces a model reason whose judgment saw a section withheld since). */
  reasonBy: "model" | "code";
  override: "read_anyway" | "skip" | null;
  /** What the path treats it as: a "read it anyway" counts as core; a "skip it" is skipped. */
  effectiveLabel: ReadingPathLabel | "skipped";
  exercise: ReadingPathExerciseDto | null;
  words: number;
  learningObjectIds: string[];
}

export interface ReadingPathDto {
  version?: number;
  extractionId: string;
  sourceId?: string;
  /** ask_depth: the Guide asks "How deep do you want to go?" (no call yet);
   *  ready: the path for the current state; judging: being read (an older
   *  path, if any, is shown meanwhile); stale: an older path, not being
   *  read; pending: nothing yet; failed / withheld / no_sections. */
  status: "ask_depth" | "ready" | "judging" | "stale" | "pending" | "failed" | "withheld" | "no_sections";
  depth: ReadingPathDepth | null;
  depthLabel?: string | null;
  /** guide: the learner chose it here; intent: their Master/Learn/Keep/Light touch setting for this book. */
  depthOrigin?: "guide" | "intent" | null;
  intent?: { choice: string; label: string } | null;
  depths: Array<{ id: ReadingPathDepth; label: string; means: string }>;
  goal: { id: string; title: string } | null;
  goalLine?: string;
  sections: ReadingPathSectionDto[];
  next: { text: string; sectionId: string; spanId: string | null; exercise: ReadingPathExerciseDto | null; minutes: number } | null;
  stateKey?: string | null;
  stale?: boolean;
  /** The shown judgment was asked about a section withheld since, so none of
   *  its model reasons is shown (code's lines stand in while it is re-read). */
  reasonsHeldBack?: boolean;
  message?: string | null;
  reason?: string | null;
}

/** A take on a pair (two keys) or a claim (one key), as the table's rows name them. */
export interface KeepTakeDto {
  text: string;
  keys: string[];
}

// ---------------------------------------------------------------------------
// Reader workbench RW5a: explorable figures (spec §8; UX §4.7, W11)
// ---------------------------------------------------------------------------

export type FigureVerification = "verified" | "illustrative" | "failed" | "unsupported";

/** A prediction once answered: what the figure showed, decided by code. */
export interface FigurePredictionResultDto {
  version?: number;
  predictionId: string;
  figureId: string;
  extractionId: string;
  predictionIndex: number;
  learnerAnswer: string;
  matched: boolean;
  before: number | null;
  after: number | null;
  /** The right answer (sent only after the learner answered). */
  answer: string | null;
  explanationText: string | null;
}

export interface FigurePredictionDto {
  index: number;
  prompt: string;
  kind: "direction" | "area";
  choices: Array<{ value: string; label: string }>;
  answered: FigurePredictionResultDto | null;
}

export interface FigureViewDto {
  figureId: string;
  extractionId: string;
  spanIds: string[];
  anchorSpanId: string | null;
  region: { spanId: string; bbox: number[] } | null;
  /** RW5d P1 adds "show_me" (the intent box with words, or the Ask rail). */
  origin: "selection" | "library" | "tutor" | "show_me";
  verification: FigureVerification;
  kind: "reconstructed" | "illustrative" | null;
  /** The server's label (the Reader draws its own code-owned badge instead, FIGURE_FRAME). */
  label: string;
  reason: string | null;
  unsupportedKind: string | null;
  supersedesId: string | null;
  revisionNote: string | null;
  versions: number;
  createdAt: string;
  /** InteractiveFigureSpecV1 as JSON text (its keys are the spec's own); shown figures only. */
  specJson: string | null;
  demonstrates: string | null;
  assumptions: Array<{ text: string; spanId: string | null; quote: string | null }>;
  predictions: FigurePredictionDto[];
  /** The closed keys of the checks LearnLoop ran (§8.3 steps 1-2); the Reader names them in its own words. */
  propertyChecks?: string[];
  /** RW5d P1 (present only while figures.show_me_enabled is on): the goal in its author's voice. */
  goalText?: string | null;
  goalAuthor?: "learner" | "tutor" | null;
  /** Where its passages came from: the learner's selection, found in their books, or none ("not from your books"). */
  grounding?: FigureGrounding;
  /** The passages found in the learner's books it was built from (grounding "retrieved"). */
  passages?: FigurePassageDto[];
}

export type FigureGrounding = "anchor" | "retrieved" | "none";

export interface FigurePassageDto {
  extractionId: string;
  spanId: string;
  /** The passage's source (Codex review F8: its chip opens another book as a detour). */
  sourceId?: string | null;
  sourceTitle?: string | null;
  section?: string | null;
  page?: number | null;
}

/** RW5d P1: FigureRequestV1 (spec §7.1). goalAuthor, the policy and the tiers are the server's, never sent. */
export interface FigureRequestV1Input {
  goalText?: string | null;
  anchor?: { extractionId: string; spanIds: string[]; region?: { spanId: string; bbox: number[] } | null } | null;
  origin: "selection" | "library" | "tutor" | "show_me";
  hostRef?: { questionEventId?: string | null } | null;
  readingAt?: { extractionId: string; spanId: string } | null;
  offerRef?: string | null;
  coldActive?: boolean;
}

export interface FigureBuildResultDto {
  figure: FigureViewDto | null;
  reused: boolean;
  /** The passage became held out while it was being built: nothing is shown. */
  withheld?: boolean;
}

export interface FiguresDto {
  version?: number;
  extractionId: string;
  figures: FigureViewDto[];
}

/** A library request running off the request path (reader.library_job). */
export interface LibraryJobDto<T> {
  version?: number;
  jobId: string;
  /** RW4b adds "exercise_candidates" and "find_exercises" (the same runner). */
  kind: "ask" | "notes" | "compare" | "tutor" | "exercise_candidates" | "find_exercises" | "figure_build";
  askId: string | null;
  state: "pending" | "done" | "cancelled";
  result: T | null;
}

export interface LibraryTutorDto {
  version?: number;
  askId: string;
  eventId: string;
  answerMd: string | null;
  citations: Array<{ extractionId: string; spanId: string; label: string }>;
  groundedKeys: string[];
  /** Pinned passages the tutor's context budget trimmed (still given, in part). */
  trimmedKeys?: string[];
  droppedPins: Array<Record<string, unknown>>;
  label: string;
  remaining?: number | null;
  readerAnswerEventId?: string | null;
  burnedSurfaceIds?: string[];
  learnerGap?: { status: string; kind?: string | null } | null;
}

// ── Adaptive hints H2a/H2b: the practice screen's hint panel ────────────────
// (spec_adaptive_hints_v1 §4.1, §4.8; the sidecar's practice.request_hint,
// practice.hint_job, practice.cancel_hint, practice.answer_discriminating and
// practice.set_help_style). Keys arrive camel-cased; values do not.

export type HintStatus = "ready" | "withheld" | "unavailable" | "disabled" | "refused" | "cancelled";
export type HintRequestKind = "more" | "feedback" | "book_way" | "smaller_step";
export type HintShortcut = "not_where_stuck" | "too_big" | "learner_route" | "notation";
export type HelpStyle = "let_me_struggle" | "balanced" | "guide_me";

export interface HintLabelsDto {
  origin?: string | null;
  kind?: string | null;
  workedHelp?: string | null;
  horizon?: string | null;
}

export interface HintPickDto {
  level: number;
  label: string;
  workedHelp: string;
  consequence: string;
}

export interface HintDiscriminatingDto {
  rivals: Array<{ id: string; status: string }>;
  predictedAnswers: Array<{ rivalId: string; answer: string }>;
  eigNats: number | null;
  weightsBasis: string;
  answerBox: boolean;
}

export interface HintResultDto {
  version?: string;
  status: HintStatus;
  assistId?: string | null;
  hintMd?: string | null;
  kind?: string | null;
  level?: number | null;
  horizon?: number | null;
  horizonIndex?: number | null;
  labels?: HintLabelsDto;
  evidence?: { countsAsHint?: boolean; primed?: boolean; level?: number };
  discriminating?: HintDiscriminatingDto | null;
  authoredIndex?: number | null;
  chooser?: string | null;
  propensity?: number | null;
  reason?: string | null;
  message?: string | null;
  replies?: string[];
  picks?: HintPickDto[];
  /** Set by the job read: true only on the read that delivered (showed) it. */
  shown?: boolean;
}

export interface HintJobDto {
  version: number;
  jobId: string | null;
  state: "pending" | "done" | "cancelled";
  result: HintResultDto | null;
}

export interface HintCancelDto {
  version: number;
  jobId: string;
  state: string;
  cancelled: boolean;
  reason: string | null;
}

export interface HintDiscriminateAnswerDto {
  version: number;
  recorded: boolean;
  assistId: string | null;
  settled?: boolean;
  consistentRivals?: string[];
  message?: string;
  reason?: string | null;
}

export interface HintRequestInput {
  sessionId: string;
  practiceItemId: string;
  submissionId: string;
  answerMd?: string;
  request: HintRequestKind;
  answeredAssistId?: string;
  feedbackShortcut?: HintShortcut;
  feedbackText?: string;
  feedbackSelection?: string;
  takenLevel?: 4 | 5;
  secondsOnItem?: number;
}

// -- Adaptive difficulty AD2+AD3 (spec_adaptive_difficulty_v1 §5.12, §9.5, §12): desktop only --

/** The Reader's randomized dose offer at a section boundary (§5.12): null when nothing is offered. */
export interface ReaderDoseOfferDto {
  version: number;
  eligible: boolean;
  reason: string | null;
  drawId: string | null;
  offer: {
    drawId: string;
    variant: "extra_worked_example" | "extra_question";
    text: string;
    /** The glass box's line: "Offered at random, to learn how much of this helps you". */
    why: string;
    content: { extractionId?: string; spanId?: string; questionId?: string; style?: string };
    /** extra_question only: the exact question the draw chose (never the section's ordinary
     *  check), so the Reader shows that one. Absent from an older sidecar. */
    question?: {
      questionId: string;
      sectionId: string | null;
      prompt: string;
      expectedAnswer: string;
      spanIds: string[];
    } | null;
  } | null;
}

export type ReaderDoseOfferEvent = "delivered" | "not_delivered" | "taken" | "dismissed";

/** An LO's readiness lines from the subject view, labelled as predictions (§9.5). */
export interface AdaptiveReadinessDto {
  version: number;
  predicted: boolean;
  line: string;
  cells: Array<{
    facet: string;
    capability: string;
    untested: boolean;
    pBarAtTop: number | null;
    label: string;
    kind: "prediction";
  }>;
}

/** "Why this item" (§12): the one line of the draw that chose a served plan item, or null. */
export interface AdaptiveWhyItemDto {
  version: number;
  why: string | null;
  mode: "band" | "overlap" | "calibrate" | null;
}

// ── Reader workbench RW2b + adaptive hints H3: checks and the help ladder ──
// (spec_reader_workbench_v1 §5.2-5.6; the sidecar's workbench.check,
// workbench.suggest_help, workbench.request_help, workbench.help_job,
// workbench.cancel_help, workbench.answer_discriminating,
// workbench.set_help_style and workbench.help_state). Desktop only.

export type CheckVerdict = "valid" | "questionable" | "unchecked";
export type CheckMethod = "checked" | "checked_numerically" | "model";

export interface CheckStepVerdictDto {
  chainId: string;
  number: number | null;
  verdict: CheckVerdict;
  method: CheckMethod;
  /** ✓ ≠ ≈ ? · (UX §3.4): never a colour, never a score. */
  mark: string;
  /** "checked", "checked numerically" or "model's reading, not checked". */
  label: string;
  reason: string;
  dependsOn: string[];
  assumption: string;
  first: boolean;
  editedSinceCheck: boolean;
  deletedSinceCheck: boolean;
  /** The step's text the verdict was about (bounded at 2,000 characters): a
   *  local edit away from it dims the marker at once (review F6). */
  checkedText?: string;
  /** Fix round 5: a fingerprint of the FULL checked text (`fnv1a64:<hex>`,
   *  helpModel's textFingerprint); any edit to the text changes it. */
  checkedFingerprint?: string | null;
}

export interface CheckViewDto {
  assistId: string;
  checkedAt: string | null;
  verdicts: CheckStepVerdictDto[];
  firstQuestionableStepId: string | null;
  errorKind: { kind: string; label: string; reason: string } | null;
  assumptions: string[];
  /** Fix round 10: workbench.symbolic_checks_enabled now; off, nothing shows as checked. */
  symbolicEnabled?: boolean;
  symbolicAvailable: boolean;
  stale: boolean;
  changedSteps: number[];
}

export interface WorkbenchStepLabelsDto {
  aboutStepId: string | null;
  aboutStep: number | null;
  continueFromStepId: string | null;
  continueFromStep: number | null;
  firstQuestionableStep: number | null;
}

export interface LadderRungDto {
  level: 1 | 2 | 3 | 4 | 5;
  label: string;
  consequence: string;
  workedHelp: boolean;
  discriminating: boolean;
}

export interface HelpSuggestionDto {
  level: number;
  kind: string;
  chooser: "decider" | "fallback";
  horizonIndex: number | null;
  propensity: number | null;
  suggestionId: string | null;
  reason: string | null;
  why: string;
  split: string | null;
  rungs: LadderRungDto[];
  kindLabel: string | null;
  horizonLabel: string | null;
}

export interface WorkbenchHelpResultDto {
  status: string;
  assistId?: string | null;
  reason?: string | null;
  message?: string | null;
  shown?: boolean | null;
  /** A check's view, on the read that delivered it (or an unchanged re-check). */
  check?: CheckViewDto | null;
  /** The ladder's suggestion (suggest jobs). */
  suggestion?: HelpSuggestionDto;
  steps?: WorkbenchStepLabelsDto;
  /** A hint (hint jobs): the H2a result fields. */
  hintMd?: string | null;
  kind?: string | null;
  level?: number | null;
  labels?: HintLabelsDto;
  discriminating?: HintDiscriminatingDto | null;
  replies?: string[];
  stepLine?: string;
  claims?: HintClaimDto[];
  /** Fix round 11: workbench.symbolic_checks_enabled at read time. */
  symbolicEnabled?: boolean;
  bridgeJobId?: string | null;
  /** RW2c: the worked example looked for after a level-3+ hint (absent while
   *  workbench.examples_enabled is off; null when it does not apply). */
  exampleJobId?: string | null;
  /** A bridge (bridge jobs), or RW2c's worked example (example jobs). */
  line?: string;
  spanId?: string | null;
  extractionId?: string | null;
  /** RW2c review F1: the book the example is in (it may be another book). */
  sourceId?: string | null;
  label?: string | null;
  /** RW2c: the passages a logged draw kept one click away ("another passage"). */
  alternatives?: number;
  /** RW2c's example: follows_learner_route | worked_example. */
  verdict?: string | null;
  trigger?: string | null;
  aboutStepId?: string | null;
  /** The record line and footer after a delivered check or hint (G62). */
  record?: WorkbenchRecordDto;
}

export interface WorkbenchHelpJobDto {
  version: number;
  jobId: string | null;
  kind?: "check" | "suggest" | "hint" | "bridge" | "example" | "compare";
  state: "pending" | "done" | "cancelled";
  result: WorkbenchHelpResultDto | null;
}

export interface WorkbenchHintViewDto {
  assistId: string;
  kind: string;
  level: number;
  hintMd: string;
  labels: HintLabelsDto;
  aboutStepId: string | null;
  continueFromStepId: string | null;
  stepLine: string;
  replies: string[];
  discriminatingAnswer: { answerMd: string; message: string } | null;
  bridge: ({ assistId: string; line: string; spanId: string | null; extractionId: string | null; label: string | null;
    /** RW2c fix round 2 (7): the book a drawn or picked passage is in (only
     *  while workbench.passage_draw_enabled is on). */
    sourceId?: string | null } & WorkbenchPassageDrawDto) | null;
  /** RW2c: the worked example under this hint (key absent while
   *  workbench.examples_enabled is off). */
  example?: WorkbenchExampleViewDto | null;
  /** The hint's own checkable claims as verified (Reader §5.3, review F14). */
  claims?: HintClaimDto[];
  /** Fix round 10: workbench.symbolic_checks_enabled now; off, no claim shows ✓. */
  symbolicEnabled?: boolean;
}

export interface HintClaimDto {
  step: number;
  statement: string;
  /** checked | checked_numerically | model (failed claims are never shown). */
  status: string;
  label: string;
  kind: string;
  reason: string;
}

export interface WorkbenchHelpStateDto {
  version: number;
  check: CheckViewDto | null;
  hints: WorkbenchHintViewDto[];
  helpStyle: HelpStyle | null;
  storedHelpStyle: HelpStyle;
  hintsEnabled: boolean;
  /** RW2c: "Show me a similar example" can run here (both keys absent while
   *  workbench.examples_enabled is off). */
  examplesAvailable?: boolean;
  /** RW2c: the shown "Show me a similar example" results, not under a hint. */
  examples?: WorkbenchExampleViewDto[];
}

/** RW2c review F1: where a passage the workbench names is: its reading and
 *  book, so a passage in another book opens there, not in the book open now. */
export interface PassageTarget {
  extractionId?: string | null;
  sourceId?: string | null;
}

/** RW2c: a passage shown by a logged draw keeps the others one click away. */
export interface WorkbenchPassageDrawDto {
  alternatives?: number;
  optionId?: string;
  drawAssistId?: string;
}

/** RW2c: a worked example that takes the learner's route (no passage text:
 *  it opens in the book). */
export interface WorkbenchExampleViewDto extends WorkbenchPassageDrawDto {
  assistId: string;
  line: string;
  spanId: string | null;
  extractionId: string | null;
  /** RW2c review F1: the book the passage is in (the Reader opens it there
   *  when it is not the book open now). */
  sourceId?: string | null;
  label: string | null;
  verdict: string | null;
  trigger: string | null;
  aboutStepId: string | null;
  hintAssistId: string | null;
}

export interface WorkbenchAnotherPassageDto {
  version: number;
  kind: "bridge" | "example";
  passage: WorkbenchExampleViewDto;
}

export interface WorkbenchCompareOfferDto {
  version: number;
  available: boolean;
  reason: string | null;
  referenceKind?: "item_key" | "book_solution";
  label?: string;
}

export interface WorkbenchCompareLinesDto {
  differences: { kind: string; learnerStep: number | null; line: string }[];
  routeLine: string | null;
  sameMethod: boolean;
  learnerRouteValid: boolean;
  dropped: number;
  label: string;
}

export interface WorkbenchComparisonDto {
  assistId: string;
  revealId: string | null;
  learner: { label: string; steps: { number: number; kind: string; bodyMd: string }[] };
  reference: { kind: "item_key" | "book_solution"; label: string; text: string; extractionId?: string; spanIds?: string[]; page?: number | null };
  lines: WorkbenchCompareLinesDto | null;
}

export interface WorkbenchCompareMethodsDto {
  version: number;
  comparison: WorkbenchComparisonDto;
  linesJobId: string | null;
}

/** RW2c: the compare job's result (read with workbenchHelpJob). */
export interface WorkbenchCompareJobResultDto {
  status: string;
  assistId?: string;
  lines?: WorkbenchCompareLinesDto;
  reason?: string;
  message?: string;
}

export interface WorkbenchRequestHelpInput {
  sessionId: string;
  request?: HintRequestKind;
  takenLevel?: number;
  offeredLevel?: number | null;
  suggestionId?: string | null;
  focusedStepId?: string | null;
  answeredAssistId?: string;
  feedbackShortcut?: HintShortcut;
  feedbackText?: string;
  feedbackStepId?: string | null;
  secondsOnItem?: number;
}
