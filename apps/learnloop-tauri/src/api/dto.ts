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

export interface SettingsDto {
  version: number;
  ai: SettingsAiDto;
  openrouter: OpenrouterKeyStateDto;
  health?: RuntimeHealth;
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
  /** Top-4 nearest items by the true blended distance (not the lossy 2D embedding). */
  neighbors: Array<{ id: string; distance: number }>;
}

export interface KnowledgeMapSnapshot {
  version: number;
  points: KnowledgeMapPoint[];
  counts: { items: number; learningObjects: number; concepts: number; facets: number };
  /** Kruskal stress-1 of the 2D embedding — how approximate the map is. */
  stress: number;
  /** Facet-native diagnostic field; item points above remain for strata/history. */
  facetField: KnowledgeFacetField;
}

export type CapabilityArcStatus = "demonstrated" | "required" | "absent";

export interface KnowledgeFacetPoint {
  id: string;
  title: string;
  x: number;
  y: number;
  ready: number;
  /** Undecayed prediction used as the retrievability well's ghost outline. */
  readyGhost: number;
  readyVariance: number;
  evidenceMass: number;
  demonstratedMass: number;
  requiredCapabilities: string[];
  demonstratedCapabilities: string[];
  hasBlueprints: boolean;
  capabilityArcs: Array<{ capability: string; status: CapabilityArcStatus }>;
  learningObjectIds: string[];
  ambiguityCandidates: string[];
  ambiguityAttemptId: string | null;
  correction: { at: string; delta: number; attemptId: string } | null;
  /** Padlock state (§3.4) for the knowledge field lock glyph. `lockSources` are
   *  the distinct `LockReason.source` values driving the lock. Legacy facets
   *  with no lock ledger are unlocked with an empty source list. */
  locked: boolean;
  lockSources: string[];
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
  subjects: string[];
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
  energy?: "low" | "medium" | "high" | null;
  sleepQuality?: number | null;
  availableMinutes?: number | null;
  notesMdPath?: string | null;
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
  streak: StreakSummary;
  facetsDemonstrated: number;
  predictionsMoved: { up: number; down: number };
  corrections: number;
  misconceptionsTouched: { resolved: number; returned: number };
}

export interface SessionCheckpoint {
  currentPracticeItemId: string | null;
  currentAnswer: string | null;
  hintsUsed: number;
  focusBlockState: Record<string, unknown> | null;
  pendingGradingProposal: unknown | null;
  readiness: Record<string, unknown> | null;
  updatedAt: IsoTimestamp;
  /** Mid-conversation teach-back state, when the checkpoint holds one. */
  teachBack?: TeachBackStateDto | null;
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
}

export interface QueueSection {
  title: string;
  items: ScheduledItemDto[];
}

export interface QueueSnapshot {
  version: number;
  generatedAt: IsoTimestamp;
  sessionId: string | null;
  sections: QueueSection[];
  totalItems: number;
}

export interface RubricCriterionDto {
  id: string;
  points: number;
  description: string;
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

export interface PracticeItemDetail {
  version: number;
  id: string;
  learningObjectId: string;
  learningObjectTitle: string;
  subject: string | null;
  subjects: string[];
  practiceMode: string;
  attemptTypesAllowed: AttemptType[];
  evidenceFacets: string[];
  evidenceWeights: Record<string, number>;
  prompt: string;
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
  answerMd: string;
  attemptType: AttemptType;
  hintsUsed: number;
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
}

/** §5.7 block-end hook payload: withheld feedback released at the boundary,
 *  the completion/open-set outcome, and where the learner routes next. */
export interface ProbeBlockEndDto {
  episodeId: string;
  status: string;
  releasedFeedback: {
    attemptId: string;
    practiceItemId: string | null;
    rubricScore: number | null;
    feedbackMd: string | null;
    fatalErrors: string[];
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
}

export interface FeedbackBundle {
  version: number;
  attemptId: string;
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
  feedbackMd: string | null;
  repairSuggestions: RepairSuggestionDto[];
  interventionNeed: InterventionNeedDto | null;
  /** This attempt was itself a primed retry. */
  primed: boolean;
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
  /** Persisted §2.1 regrade ledger fact: present when this attempt's grading
   * history carries a regrade (a grading epoch after the original), so the
   * RegradeLedgerCard renders on a fresh load, not only after an in-screen
   * trigger_regrade. Null/absent when the attempt was never regraded. */
  regrade?: PersistedRegradeDto | null;
}

export interface PersistedRegradeDto {
  oldScore: number;
  newScore: number;
  maxPoints: number;
  regradedAt: IsoTimestamp;
  direction: "up" | "down" | "same";
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
  candidateCauses: { facet: string; capability: string }[];
}

/** Result of start_primed_retry: a sibling item to retry with primed=true. */
export interface PrimedRetryResultDto {
  available: boolean;
  /** The item was generated on demand (LLM authoring) rather than pre-existing. */
  generated: boolean;
  reason?: string | null;
  practiceItem: PracticeItemDetail | null;
}

// ── Tutor Q&A ("ask") ──────────────────────────────────────────────────────

export type TutorQuestionContext = "library" | "practice" | "feedback";

export interface AskTutorQuestionInput {
  context: TutorQuestionContext;
  question: string;
  practiceItemId?: string;
  attemptId?: string;
  noteId?: string;
  sessionId?: string;
  secondsIntoAttempt?: number;
}

/** ING M8 (§9.2): one source-span citation on a tutor answer; the chip opens
 *  the Open-in-source viewer (context "tutor_citation"). Validated server-side
 *  against provided spans — never model-invented. */
export interface TutorCitationDto {
  extractionId: string;
  spanId: string;
  label: string | null;
}

export interface TutorAnswerDto {
  version: number;
  eventId: string;
  answerMd: string;
  questionType: string;
  facets: string[];
  hintEquivalent: boolean;
  leakSuspected: boolean;
  citations: TutorCitationDto[];
  remaining: number;
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
}

export interface PromoteTutorQuestionResult extends QuestionPromotionDto {
  version: number;
}

// ── Outstanding-question queue (migration 102) ─────────────────────────────
// answerStatus tracks whether the TUTOR answered; resolution tracks whether the
// LEARNER is done with the question. They are independent axes.

export type QuestionResolution = "open" | "resolved" | "dismissed";

export interface QuestionQueueRowDto {
  id: string;
  context: TutorQuestionContext | "reader";
  questionMd: string;
  answerMd: string | null;
  answerStatus: "pending" | "answered" | "failed";
  resolution: QuestionResolution;
  questionType: string | null;
  practiceItemId: string | null;
  noteId: string | null;
  savedNoteId: string | null;
  createdAt: IsoTimestamp;
  promotion: QuestionPromotionDto | null;
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
}

export interface TutorTranscriptSnapshot {
  version: number;
  events: TutorQuestionEventDto[];
  remaining: number;
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
}

export interface StartTeachBackInput {
  sessionId: string;
  practiceItemId: string;
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
  practiceMode: string;
  learningObjectId: string | null;
  rationale: string;
  targetEvidenceFamilies?: string[];
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

export type PdfEngine = "auto" | "marker" | "pypdf";

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
}

export interface SourceLibrarySnapshot {
  version: number;
  sources: SourceLibraryCard[];
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

export interface StudyMapBriefDto {
  outcome?: "general_learning" | "reference_mastery" | "exam_prep" | string;
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
  locked: boolean;
  lockReasons: { source: string; entityType: string; entityId: string; detail: string }[];
  canMerge: boolean;
  requiresReview: boolean;
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

export interface SubjectRegistryDto {
  version?: number;
  subjectId: string;
  facets: FacetContractCardDto[];
  identifiabilityWarnings: IdentifiabilityWarningDto[];
  facetCount: number;
  lockedCount: number;
}

export interface FacetMergeResultDto {
  proposalId: string;
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

export interface GoalAtRiskFacetDto {
  learningObjectId: string;
  learningObjectTitle: string;
  facetId: string;
  label: "unexamined" | "uncertain" | "known_gap" | "solid";
  currentRecall: number | null;
  projectedRecall: number | null;
  predictedCurrent?: number;
  predictedAtHorizon?: number;
  evidenceMass?: number;
  certified?: boolean;
  attemptsToCertify?: number | null;
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
  status: "active" | "paused" | "completed" | "expired";
  priority: number;
  targetRecall: number;
  dueAt: string | null;
  facetScope: { concepts: string[]; facets: string[] };
  exam: { enabled: boolean; itemCount: number };
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
  targetRecall: number;
  dueAt?: string | null;
  concepts: string[];
  facets: string[];
}

export interface GoalFeasibilityResult {
  version: number;
  scopeFacetCount: number;
  onTrackCount: number;
  projectedOnTrackFraction: number | null;
  uncoveredConcepts: string[];
}

export interface CreateGoalInput {
  title: string;
  targetRecall: number;
  dueAt?: string | null;
  concepts: string[];
  facets: string[];
  examEnabled: boolean;
  examItemCount?: number;
}

export interface CreateGoalResult {
  version: number;
  goal: GoalDto;
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
  episodeId: string;
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
}

export interface ExamItemDto {
  practiceItemId: string;
  index: number;
  total: number;
  prompt: string;
  practiceMode: string;
}

export interface ExamSessionSnapshot {
  version: number;
  sessionId: string;
  goalId: string;
  status: "in_progress" | "completed" | "abandoned";
  items: ExamItemDto[];
  answeredItemIds: string[];
}

export interface ExamAnswerResult {
  version: number;
  sessionId: string;
  practiceItemId: string;
  correctness: number;
  score: number;
  maxPoints: number;
}

export interface ExamFacetOutcomeDto {
  facetId: string;
  learningObjectId: string;
  predictedRecall: number | null;
  observedCorrectness: number | null;
}

export interface ExamReportSnapshot {
  version: number;
  sessionId: string;
  goalId: string;
  scoreFraction: number | null;
  predictedScoreFraction: number | null;
  brier: number | null;
  perFacet: ExamFacetOutcomeDto[];
  itemOutcomes: Array<{
    practiceItemId: string;
    predictedCorrectness: number | null;
    observedCorrectness: number | null;
  }>;
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
  rightSourceId: string | null;
  rightRevisionId: string | null;
  rightLocator: string | null;
  rightExtractionId: string | null;
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

export interface ReviewChangelogEntryDto {
  id: string;
  kind: "session" | "recalibration" | "regrade";
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
  coldItemId?: string;
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

/** A durable restructure-intent record for locked facets (spec §17 machinery
 *  does not exist yet — this only queues intent, surfaced in the maintenance
 *  feed). `lockedFacetIds` is the subset of `facetIds` actually locked. */
export interface RestructureRequestDto {
  needId: string;
  subjectId: string;
  facetIds: string[];
  lockedFacetIds: string[];
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
}

export interface FacetLockReasonDto {
  source: string;
  detail: string;
}

export interface FacetLockDto {
  locked: boolean;
  reasons: FacetLockReasonDto[];
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
  lock: FacetLockDto;
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
  locked: boolean;
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

/** `detail` payload of a `restructure_request` notice (queued locked-facet intent). */
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
  result: { toState: string; [k: string]: unknown };
  state: RunStateDto;
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
}
export type ReaderAnswerMode = "answer_directly" | "help_me_reason" | "ask_me_first";

/** reader.ask — a span-grounded exchange in the reader tutor context. */
export interface ReaderAskInput {
  extractionId: string;
  spanId: string;
  question: string;
  answerMode?: ReaderAnswerMode;
  targetKey?: string | null;
  revealedSurfaceIds?: string[];
  coldActive?: boolean;
}
export interface ReaderAnswerDto {
  eventId: string;
  readerAnswerEventId: string;
  answerMd: string;
  answerMode: ReaderAnswerMode;
  citations: unknown[];
  manifest: Record<string, unknown>;
  warmedSurfaceIds: string[];
  burnedSurfaceIds: string[];
  hintEquivalent: boolean;
  remaining: number | null;
}

/** A completed Reader Ask restored from the durable interaction-event log. */
export interface ReaderAskHistoryExchangeDto {
  eventId: string;
  extractionId: string;
  spanId: string;
  questionMd: string;
  answerMd: string;
  answerMode: ReaderAnswerMode;
  citations: unknown[];
  createdAt: string | null;
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
  fileName: string | null;
  extractionId: string;
  sourceId: string | null;
  revisionId: string | null;
  blocks: ReaderPdfBlockDto[];
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
