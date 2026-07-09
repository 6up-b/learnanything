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

export interface TutorAnswerDto {
  version: number;
  eventId: string;
  answerMd: string;
  questionType: string;
  facets: string[];
  hintEquivalent: boolean;
  leakSuspected: boolean;
  remaining: number;
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

export type InspectorEntity =
  | { version: number; kind: "practice_item"; id: string; detail: PracticeItemDetail }
  | { version: number; kind: "learning_object"; id: string; detail: LearningObjectDetail }
  | { version: number; kind: "attempt"; id: string; detail: AttemptInspectorDetail }
  | { version: number; kind: "error_event"; id: string; detail: ErrorEventDto }
  | { version: number; kind: "note"; id: string; detail: NoteInspectorDetail }
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

// ── goals + practice exams (goal redesign phases 3-4) ────────────────────────

export interface GoalReportSummaryDto {
  onTrackCount: number;
  total: number;
  onTrackFraction: number | null;
  atRiskCount: number;
  horizon: string;
  dueAt: string | null;
}

export interface GoalAtRiskFacetDto {
  learningObjectId: string;
  learningObjectTitle: string;
  facetId: string;
  label: "unexamined" | "uncertain" | "known_gap" | "solid";
  currentRecall: number | null;
  projectedRecall: number | null;
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
  report: GoalReportSummaryDto & { atRisk: GoalAtRiskFacetDto[] };
}

export interface GoalSeriesPointDto {
  at: string;
  onTrackCount: number;
  total: number;
  onTrackFraction: number | null;
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
