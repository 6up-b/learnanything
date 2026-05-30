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
  | "open_text";

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
  };
  database: { ok: boolean; migrationsApplied: number; latestMigration: number };
  vaultLoaded: boolean;
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
}

export interface QueueInput {
  sessionId?: string | null;
  availableMinutes?: number | null;
  energy?: string | null;
  limit?: number | null;
}

export interface SchedulerComponents {
  forgettingRisk: number;
  activeGoal: number;
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
  followupQueued: boolean;
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
}

export interface RepairSuggestionDto {
  practiceMode: string;
  learningObjectId: string | null;
  rationale: string;
}

export type InspectorEntity =
  | { version: number; kind: "practice_item"; id: string; detail: PracticeItemDetail }
  | { version: number; kind: "learning_object"; id: string; detail: LearningObjectDetail }
  | { version: number; kind: "attempt"; id: string; detail: unknown }
  | { version: number; kind: "error_event"; id: string; detail: ErrorEventDto }
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
