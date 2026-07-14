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
  | { version: number; kind: "attempt"; id: string; detail: AttemptInspectorDetail }
  | { version: number; kind: "error_event"; id: string; detail: ErrorEventDto }
  | { version: number; kind: "note"; id: string; detail: NoteInspectorDetail }
  | { version: number; kind: "probe_episode"; id: string; detail: ProbeEpisodeInspectorDetail }
  | { version: number; kind: "not_found"; id: string; suggestions: InspectorSearchResult[] };

export interface InspectorSearchResult {
  kind: "practice_item" | "learning_object" | "attempt" | "error_event";
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
  difficultyPrior: number | null;
  tags: string[];
  mastery: MasteryDto | null;
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

export interface StartIngestInput {
  source: string;
  subjectId: string;
  mode: IngestMode;
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
  error: { code: string; message: string } | null;
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

export interface StartImportBatchInput {
  sources: string[];
  subjectId?: string | null;
  inventory?: boolean;
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
}

export interface CreateStudyMapInput {
  sourceSetId: string;
  mode?: "auto" | "bootstrap";
  brief?: Record<string, unknown>;
  apply?: boolean;
  createGoal?: boolean;
}

export interface BuildStudyMapInput {
  sourceSetId: string;
  brief?: Record<string, unknown>;
  mode?: "auto" | "bootstrap";
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

export interface StudyMapBriefDto {
  outcome?: "general_learning" | "reference_mastery" | "exam_prep" | string;
  level?: string;
  depth?: string;
  scope?: string;
  subject?: string;
  includeTopics?: string[];
  excludeTopics?: string[];
  notation?: string;
  // exam-prep goal fields (createGoal path)
  goalTitle?: string;
  targetRecall?: number;
  dueAt?: string;
  examItemCount?: number;
  [key: string]: unknown;
}

export interface PlanQuickAddInput {
  source: string;
  subjectId?: string | null;
  brief?: StudyMapBriefDto;
}

export interface ConfirmQuickAddInput {
  source: string;
  subjectId: string;
  brief?: StudyMapBriefDto;
  roleOverride?: string | null;
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
}

export interface FacetEvidenceTimelineDto {
  version: number;
  facetId: string;
  modelVersion: string;
  supported: boolean;
  demonstrated: number;
  points: DemonstratedTimelinePointDto[];
  countedToward: { learningObjectId: string; learningObjectTitle: string }[];
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
