---
title: "Desktop module · src/screens/FeedbackScreen.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.FeedbackScreen"
language: "TypeScript"
area: "TypeScript/screens"
source_path: "apps/learnloop-tauri/src/screens/FeedbackScreen.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/FeedbackScreen.tsx"
source_commit: "c35ba8d9bd82db56a50cf2683c7d2733c277a683"
source_commit_timestamp: "2026-10-26T15:33:20-04:00"
source_worktree_state: "clean"
activation_kind: "entry-reachable build graph"
activation_evidence: "A static TypeScript import path reaches this file from the Vite entry src/main.tsx."
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/reference/module"
  - "learnloop/desktop"
  - "learnloop/desktop/typescript"
  - "refactor/active"
---

# `src/screens/FeedbackScreen.tsx`

Area: [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `FeedbackScreen` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/FeedbackScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/FeedbackScreen.tsx) |
| Source lines | 3400 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `c35ba8d9bd82db56a50cf2683c7d2733c277a683` |
| Commit timestamp | `2026-10-26T15:33:20-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]]

## Public API

- `export function FeedbackScreen(` — function, line 1459

## Internal implementation anchors

- `type FeedbackOrigin, simplePracticeFeedback, VERDICT_TEXT, verdictOf } from "../app/practiceFeedback"` — type, line 54
- `type FeedbackNextStep } from "./feedback/FeedbackSurface"` — type, line 65
- `const C =` — const, line 74
- `const MONO = '"JetBrains Mono", "Fira Code", ui-monospace, SFMono-Regular, Menlo, monospace'` — const, line 91
- `function Faint(` — function, line 94
- `function Dim(` — function, line 97
- `function Meta(` — function, line 100
- `function FbHeader(` — function, line 105
- `function EvidenceHeader(` — function, line 124
- `function BlockBar(` — function, line 141
- `const filled = Math.max(0, Math.min(width, Math.round((value / max) * width)))` — const, line 144
- `function fmtDue(iso: string | null): string` — function, line 154
- `const d = new Date(iso)` — const, line 157
- `const now = new Date()` — const, line 158
- `const diffH = (d.getTime() - now.getTime()) / 3_600_000` — const, line 159
- `const tomorrow = new Date(now)` — const, line 160
- `function fmtDay(iso: string | null | undefined): string` — function, line 180
- `function ColdCheckBanner(` — function, line 193
- `const confirmed = result.claim === "repair_confirmed"` — const, line 194
- `const failed = result.claim === "escalated_unrepaired"` — const, line 195
- `const tone = confirmed ? C.green : failed ? C.amber : C.textDim` — const, line 196
- `const heading = confirmed ? "unassisted check · passed" : failed ? "unassisted check · did not hold" : result.claim === "downgraded" ? "unassisted check · recorded, not counted" : "unassisted check · no verdict"` — const, line 197
- `const when = fmtDay(result.instructedAt)` — const, line 204
- `const body = confirmed ? `This was the unassisted check for the repair you did on $` — const, line 205
- `function AutoPrimedNote(` — function, line 245
- `function ElicitingRepairCard(` — function, line 276
- `const anchor = suggestion.targetRefs?.[0] ?? null` — const, line 288
- `const answered = outcome != null` — const, line 289
- `function ratingPill(r: string): string` — function, line 379
- `function modePillTone(mode: string): string` — function, line 386
- `function ScoreBlock(` — function, line 391
- `const tone = score === max ? C.green : score >= max * 0.75 ? C.greenSoft : score >= max * 0.5 ? C.amber : C.red` — const, line 393
- `const label = score === max ? "perfect" : score >= max * 0.75 ? "good" : score >= max * 0.5 ? "partial credit" : "needs work"` — const, line 397
- `function CriterionRow(` — function, line 439
- `const assessed = criterionAssessed(row)` — const, line 453
- `const ok = maxKnown && row.pointsAwarded === row.pointsPossible` — const, line 454
- `const partial = maxKnown && row.pointsAwarded > 0 && row.pointsAwarded < row.pointsPossible` — const, line 455
- `const mark = !assessed ? "–" : !maxKnown ? "·" : ok ? "✓" : partial ? "◐" : "✗"` — const, line 456
- `const tone = !assessed || !maxKnown ? C.textDim : ok ? C.green : partial ? C.amber : C.red` — const, line 457
- `function ErrorAttribution(` — function, line 495
- `const plan = ea.repairPlan` — const, line 496
- `const resolutionStatus = typeof plan?.resolutionStatus === "string" ? plan.resolutionStatus : null` — const, line 497
- `const causeScope = typeof plan?.causeScope === "string" ? plan.causeScope : null` — const, line 499
- `const operation = typeof plan?.operation === "string" ? plan.operation : null` — const, line 500
- `const abstentionReason = typeof plan?.abstentionReason === "string" ? plan.abstentionReason : null` — const, line 501
- `const targetRef = plan?.targetRef && typeof plan.targetRef === "object" && !Array.isArray(plan.targetRef) ? plan.targetRef as Parameters<typeof formatCausalTarget>[0] : null` — const, line 503
- `const firstDivergence = plan?.firstDivergence && typeof plan.firstDivergence === "object" && !Array.isArray(plan.firstDivergence) ? plan.firstDivergence as Parameters<typeof formatDivergenceAnchor>[0] : null` — const, line 507
- `const SQRT_2PI = Math.sqrt(2 * Math.PI)` — const, line 573
- `const PROB_TICKS = [0.1, 0.25, 0.5, 0.75, 0.9]` — const, line 574
- `function logit(p: number): number` — function, line 576
- `const c = Math.min(1 - 1e-4, Math.max(1e-4, p))` — const, line 577
- `function toLogitSpace(mean: number, variance: number):` — function, line 583
- `const m = Math.min(1 - 1e-4, Math.max(1e-4, mean))` — const, line 584
- `const slope = m * (1 - m)` — const, line 585
- `const logitVar = Math.max(1e-4, variance / (slope * slope))` — const, line 586
- `function gaussianPdf(x: number, mu: number, sd: number): number` — function, line 590
- `const z = (x - mu) / sd` — const, line 591
- `function BeliefShiftChart(` — function, line 600
- `const prior = toLogitSpace(before.mean, before.variance)` — const, line 615
- `const post = toLogitSpace(after.mean, after.variance)` — const, line 616
- `const padL = 8` — const, line 618
- `const padR = 8` — const, line 619
- `const padT = 20` — const, line 620
- `const padB = 20` — const, line 621
- `const plotW = width - padL - padR` — const, line 622
- `const plotH = height - padT - padB` — const, line 623
- `const lo = Math.min(prior.mu - 3.4 * prior.sd, post.mu - 3.4 * post.sd, logit(0.15))` — const, line 627
- `const hi = Math.max(prior.mu + 3.4 * prior.sd, post.mu + 3.4 * post.sd, logit(0.85))` — const, line 628
- `const span = Math.max(1e-3, hi - lo)` — const, line 629
- `const xOf = (t: number)` — const, line 630
- `const peak = Math.max(gaussianPdf(prior.mu, prior.mu, prior.sd), gaussianPdf(post.mu, post.mu, post.sd))` — const, line 633
- `const yMax = peak * 1.12` — const, line 634
- `const baseY = padT + plotH` — const, line 635
- `const yOf = (d: number)` — const, line 636
- `const N = 72` — const, line 638
- `const curvePath = (mu: number, sd: number, close: boolean): string` — const, line 639
- `let d = ""` — let, line 640
- `const x = lo + (span * i) / N` — const, line 642
- `const y = gaussianPdf(x, mu, sd)` — const, line 643
- `const postColor = masteryTone(after.mean, C)` — const, line 650
- `const shift = post.mu - prior.mu` — const, line 651
- `const showArrow = bayesianSurprise > tau && Math.abs(shift) > 1e-3` — const, line 652
- `const arrowColor = shift >= 0 ? C.green : C.red` — const, line 653
- `const arrowY = 11` — const, line 654
- `const xPrior = xOf(prior.mu)` — const, line 655
- `const xPost = xOf(post.mu)` — const, line 656
- `const yPrior = yOf(gaussianPdf(prior.mu, prior.mu, prior.sd))` — const, line 657
- `const yPost = yOf(gaussianPdf(post.mu, post.mu, post.sd))` — const, line 658
- `const t = logit(p)` — const, line 664
- `const x = xOf(t)` — const, line 666
- `const mid = p === 0.5` — const, line 667
- `function MasteryStepBreakdown(` — function, line 722
- `const pct = (v: number)` — const, line 724
- `const dominant = factor.key === step.dominantFactorKey` — const, line 740
- `const removed = 1 - factor.multiplier` — const, line 743
- `const color = dominant ? C.amber : removed < 0 ? C.greenSoft : C.textDim` — const, line 744
- `function MasteryDelta(` — function, line 794
- `const tau = surprise.followupThresholdNats ?? algoConfig().tauFollowupNats` — const, line 800
- `const bayes = surprise.bayesianSurprise ?? 0` — const, line 801
- `const hasSurprise = bayes > tau` — const, line 802
- `const postColor = masteryTone(after.mean, C)` — const, line 803
- `const evidence = f.criterionEvidence ?? []` — const, line 804
- `const assessed = criterionAssessed(row)` — const, line 852
- `const ok = row.pointsAwarded === row.pointsPossible` — const, line 853
- `const partial = row.pointsAwarded > 0 && row.pointsAwarded < row.pointsPossible` — const, line 854
- `const mark = !assessed ? "–" : ok ? "✓" : partial ? "◐" : "✗"` — const, line 855
- `const tone = !assessed ? C.textDim : ok ? C.green : partial ? C.amber : C.red` — const, line 856
- `function followupStatus(f: FeedbackBundle, tau: number): string` — function, line 885
- `const gate = f.surprise.gateDiagnostics` — const, line 889
- `const reasons = interventionReasons(f.surprise.triggeredActions ?? [])` — const, line 892
- `const suppressed = f.surprise.suppressedActions ?? []` — const, line 901
- `const GATE_SIGNAL_LABELS: Record<string, string> =` — const, line 910
- `const GATE_COMPARATORS: Record<string, string> =` — const, line 922
- `function gateNum(value: number | boolean | null): string | null` — function, line 926
- `function describeSignal(sig: FollowupGateSignalDto): string` — function, line 932
- `const name = sig.name ?? ""` — const, line 933
- `const label = GATE_SIGNAL_LABELS[name] ?? name.replace(/_/g, " ")` — const, line 939
- `const value = gateNum(sig.value)` — const, line 940
- `const cmp = sig.comparator ? GATE_COMPARATORS[sig.comparator] ?? sig.comparator : ""` — const, line 941
- `let threshold = gateNum(sig.threshold)` — let, line 942
- `const unit = sig.unit === "nats" ? " nats" : ""` — const, line 951
- `function describeGate(gate: FollowupGateDiagnosticsDto): string` — function, line 959
- `const sig = gate.decisiveSignal` — const, line 960
- `const signalText = sig ? describeSignal(sig) : gate.decisiveReason.replace(/_/g, " ")` — const, line 961
- `const scoreSuffix = typeof gate.gateScore === "number" && sig?.name !== "gate_score" ? ` · score $` — const, line 964
- `const base = (()` — const, line 969
- `const trigger = gate.triggeredReasons.find((r)` — const, line 979
- `const trigText = trigger ? trigger.replace(/_/g, " ") : "trigger"` — const, line 980
- `const v = gateNum(sig.value)` — const, line 990
- `function interventionReasons(actions: string[]): string[]` — function, line 999
- `const reasons = actions .map((action)` — const, line 1000
- `function formatInterventionAction(action: string): string` — function, line 1011
- `function fmtTimestamp(seconds: number): string` — function, line 1023
- `const total = Math.max(0, Math.floor(seconds))` — const, line 1024
- `const h = Math.floor(total / 3600)` — const, line 1025
- `const m = Math.floor((total % 3600) / 60)` — const, line 1026
- `const s = total % 60` — const, line 1027
- `const mm = h > 0 ? String(m).padStart(2, "0") : String(m)` — const, line 1028
- `function timeRangeLabel(video:` — function, line 1032
- `function SourceRefCard(` — function, line 1038
- `const video = sourceRef.video` — const, line 1046
- `const openExternal = async (url: string)` — const, line 1048
- `const externalVideoUrl = video ? `https://www.youtube.com/watch?v=$` — const, line 1057
- `const embedUrl = video ? `https://www.youtube-nocookie.com/embed/$` — const, line 1062
- `function SourceReviewPanel(` — function, line 1131
- `const refs = (f.sourceRefs ?? []).filter((ref)` — const, line 1139
- `const missed = f.rubricScore < f.maxPoints` — const, line 1142
- `function statementPairCopy(m: MatchedMisconceptionDto): string` — function, line 1201
- `const correction = m.correctionStatement.trim()` — const, line 1202
- `const x = m.targetFacet?.trim()` — const, line 1203
- `const y = m.confusedWithFacet?.trim()` — const, line 1204
- `const head = x && y ? `Your last answer was consistent with confusing $` — const, line 1205
- `function MisconceptionStatementCard(` — function, line 1212
- `const claim: ClaimCandidateDto = useMemo( ()` — const, line 1227
- `type RegradeSide =` — type, line 1274
- `type RegradeReceipt =` — type, line 1275
- `function gradeSide(f: FeedbackBundle): RegradeSide` — function, line 1277
- `function newClientKey(prefix: "contest"): string` — function, line 1286
- `const random = globalThis.crypto?.randomUUID?.()` — const, line 1287
- `function regradeHistoryLine(` — function, line 1293
- `const words = (side: RegradeSide)` — const, line 1295
- `const side = (s: RegradeSide)` — const, line 1302
- `function RegradeLedgerCard(` — function, line 1306
- `const claim: ClaimCandidateDto = useMemo( ()` — const, line 1320
- `const PROVISIONAL_PENDING_CLARIFICATION = "provisional_pending_clarification"` — const, line 1350
- `const CLARIFICATION_REASON_COPY: Record<string, string> =` — const, line 1354
- `function clarificationOutcomeCopy(result: AnswerGradingClarificationResultDto): string` — function, line 1362
- `function ClarificationCard(` — function, line 1374
- `const simple = simplePracticeFeedback()` — const, line 1536
- `const visitId = useRef(mintVisitId()).current` — const, line 1559
- `const planMode = Boolean(nextPlan && onPlanStep)` — const, line 1564
- `const autoAdvance = Boolean(nextQueue && onOpenNext) && !planMode` — const, line 1565
- `const nextItem = useNextQueueItem(autoAdvance ? nextQueue : null, feedback !== null)` — const, line 1566
- `const nextPlanStep = useNextPlanStep(planMode && nextPlan ? nextPlan.sessionId : null, feedback !== null)` — const, line 1567
- `const advanceGeneration = useRef(0)` — const, line 1569
- `const advancingRef = useRef(false)` — const, line 1570
- `const pendingQueueWrites = useRef(new Set<Promise<void>>())` — const, line 1576
- `const trackQueueWrite = useCallback(<T,>(write: Promise<T>): Promise<T>` — const, line 1577
- `const settledWrite: Promise<void> = write.then(()` — const, line 1578
- `const resolveNext = nextItem.resolve` — const, line 1583
- `const resolvePlanStep = nextPlanStep.resolve` — const, line 1584
- `const advance = useCallback(async ()` — const, line 1585
- `const generation = ++advanceGeneration.current` — const, line 1589
- `let step: PlanStepDto | null = null` — let, line 1591
- `const generation = ++advanceGeneration.current` — const, line 1611
- `let head: ScheduledItemDto | null = null` — let, line 1613
- `const goBack = useCallback(()` — const, line 1627
- `const refreshAfterDiagnosis = useCallback(()` — const, line 1636
- `const diagnosis = useDiagnosisCard(attemptId, simple ? feedback?.diagnosisStatus : null, refreshAfterDiagnosis, onError)` — const, line 1645
- `const contestKey = useRef<` — const, line 1657
- `const errorInputRef = useRef<HTMLInputElement>(null)` — const, line 1679
- `const noteTitleRef = useRef<HTMLInputElement>(null)` — const, line 1687
- `const noteBodyRef = useRef<HTMLTextAreaElement>(null)` — const, line 1688
- `const suggestions = useMemo<CandidateErrorTypeDto[]>(()` — const, line 1690
- `const all = item?.candidateErrorTypes ?? []` — const, line 1691
- `const q = errorTypeInput.trim().toLowerCase()` — const, line 1692
- `const filtered = q ? all.filter((e)` — const, line 1693
- `let cancelled = false` — let, line 1700
- `let cancelled = false` — let, line 1736
- `const handleAnswerClarification = async ()` — const, line 1755
- `const answer = clarificationAnswer.trim()` — const, line 1756
- `const result = await trackQueueWrite(api.answerGradingClarification(feedback.attemptId, answer))` — const, line 1760
- `const handleSkipClarification = ()` — const, line 1780
- `const applyRepairStatus = useCallback( (next: CausalRepairStatusDto)` — const, line 1792
- `const repairCaseId = useMemo(()` — const, line 1804
- `const causal = feedback?.causalFeedback` — const, line 1805
- `const need = causal?.probeNeed` — const, line 1806
- `let cancelled = false` — let, line 1823
- `const inspectIds = feedback ? uniqueIds([ feedback.attemptId, feedback.practiceItemId, feedback.learningObjectId, ...feedback.errorAttributions.map((event)` — const, line 1858
- `const practiceItemIds = feedback ? uniqueIds([feedback.practiceItemId]) : []` — const, line 1867
- `const shownAttempt = useRef(attemptId)` — const, line 1887
- `const refreshItemAfterRegrade = useCallback((bundle: FeedbackBundle)` — const, line 1889
- `const handleRegrade = async ()` — const, line 1898
- `const before = gradeSide(feedback)` — const, line 1901
- `const updated = await trackQueueWrite(api.triggerRegrade(feedback.attemptId))` — const, line 1903
- `const handleContest = async ()` — const, line 1922
- `const before = verdictOf(` — const, line 1926
- `const prior = gradeSide(feedback)` — const, line 1929
- `const reason = contestReason.trim()` — const, line 1930
- `const bound = contestKey.current` — const, line 1931
- `const key = bound && bound.reason === reason ? bound.key : newClientKey("contest")` — const, line 1932
- `const updated = await trackQueueWrite(api.triggerRegrade(feedback.attemptId, reason, key))` — const, line 1935
- `const outcome = updated.contest` — const, line 1939
- `const reviewed = outcome?.reviewRequested ? " It's marked for review." : ""` — const, line 1940
- `const after = verdictOf(` — const, line 1945
- `const contestCausal = (reason: UnresolvedCauseSelfReportResponse, factorId: string | null | undefined)` — const, line 1966
- `const handleTriggerFollowup = async ()` — const, line 1989
- `const updated = await trackQueueWrite(api.triggerFollowup(feedback.attemptId))` — const, line 1993
- `const handlePrimedRetry = async ()` — const, line 2006
- `const result = await api.startPrimedRetry(feedback.attemptId)` — const, line 2010
- `const handleGuidedRedo = async ()` — const, line 2028
- `const redo = await api.startGuidedRedo(feedback.attemptId)` — const, line 2032
- `const handleRateFollowup = async (useful: boolean)` — const, line 2044
- `const updated = await api.rateFollowup(feedback.attemptId, useful)` — const, line 2048
- `const handleElicitingResponse = async (suggestionIndex: number, responseMd: string)` — const, line 2063
- `const result = await trackQueueWrite(api.submitElicitingResponse(` — const, line 2067
- `const doAddError = async (errorType: string, severity?: number)` — const, line 2084
- `const updated = await api.addErrorEvent(feedback.attemptId, errorType.trim(), severity)` — const, line 2092
- `const handleAddError = ()` — const, line 2103
- `const sel = selectedSuggestionIdx >= 0 ? suggestions[selectedSuggestionIdx] : null` — const, line 2104
- `const handleUnresolvedCauseReport = async ( factorId: string, response: UnresolvedCauseSelfReportResponse, candidateIndex?: number | null, )` — const, line 2108
- `const resetNote = ()` — const, line 2125
- `const openNoteCapture = ()` — const, line 2131
- `const doSaveNote = async ()` — const, line 2137
- `const title = noteTitle.trim()` — const, line 2139
- `const body = noteBody.trim()` — const, line 2140
- `const subjectId = item?.subject ?? item?.subjects?.[0] ?? null` — const, line 2145
- `const stamp = new Date().toISOString().replace(/[-:T.]/g, "").slice(0, 14)` — const, line 2150
- `const noteId = `$` — const, line 2151
- `const result = await api.addNote(` — const, line 2154
- `const onKey = (event: KeyboardEvent)` — const, line 2173
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 2177
- `const right = verdictOf(` — const, line 2193
- `function simpleScreen( f: FeedbackBundle, matchedMisconception: FeedbackBundle["matchedMisconception"] | null, elicitingIndex: number, elicitingSuggestion: FeedbackBundle["repairSuggestions"][number] | null, errorPanel: ReactNode, notePanel: ReactNode, )` — function, line 2216
- `const held = f.heldForReview === true` — const, line 2224
- `const verdict = verdictOf(` — const, line 2225
- `const contestAvailable = f.gradingSource !== "self" && verdict !== "right"` — const, line 2227
- `const fixId = matchedMisconception?.id ?? (!repairStatus ? f.causalFeedback?.commonRepair?.misconceptionId ?? null : null)` — const, line 2231
- `let step: FeedbackNextStep | null = null` — let, line 2234
- `let stepIsRetry = false` — let, line 2235
- `const card = diagnosis.status === "done" ? diagnosis.card : null` — const, line 2249
- `const causal = f.causalFeedback ?? null` — const, line 2250
- `const canSayNotRight = Boolean(card?.diagnosisId && card.responses.some((option)` — const, line 2251
- `const causalNotRightOk = Boolean(causal?.contestAction?.available && causal.contestAction.reasons.includes("diagnosis_wrong"))` — const, line 2252
- `const why =` — const, line 2253
- `const nextLabel = origin === "reader" ? "back to the book" : planMode ? nextPlanKeyLabel(advancing, nextPlanStep.step) : autoAdvance ? nextKeyLabel(autoAdvance, advancing, nextItem.head, nextItem.empty) : ""` — const, line 2279
- `const regradeHistory: RegradeReceipt | null = regradeReceipt ?? (f.regrade ?` — const, line 2287
- `const criteria = answeredCriterionRows(f)` — const, line 2299
- `const showTier = f.criterionEvidence.some((row)` — const, line 2300
- `const f = feedback` — const, line 2635
- `const subject = item?.subject ?? item?.subjects?.[0] ?? null` — const, line 2636
- `const tau = f.surprise.followupThresholdNats ?? algoConfig().tauFollowupNats` — const, line 2638
- `const interventionNeed = f.interventionNeed` — const, line 2639
- `const elicitingIndex = f.repairSuggestions.findIndex((s)` — const, line 2643
- `const elicitingSuggestion = elicitingIndex >= 0 ? f.repairSuggestions[elicitingIndex] : null` — const, line 2644
- `const matchedMisconception = f.matchedMisconception && f.matchedMisconception.correctionStatement?.trim() ? f.matchedMisconception : null` — const, line 2648
- `const errorPanel = addingError ? ( <div style=` — const, line 2655
- `const s = suggestions[selectedSuggestionIdx]` — const, line 2702
- `const notePanel = addingNote ? ( <div style=` — const, line 2730
- `const receipt: RegradeReceipt | null = regradeReceipt ?? (f.regrade ?` — const, line 3142
- `function nextKeyLabel( autoAdvance: boolean, advancing: boolean, head: ScheduledItemDto | null, empty: boolean ): string` — function, line 3382
- `const title = head.learningObjectTitle` — const, line 3391
- `function uniqueIds(values: Array<string | null | undefined>): string[]` — function, line 3398

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `FeedbackScreen`; references `FeedbackScreen`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AnswerGradingClarificationResultDto`, `AttemptTraceDto`, `AttemptTraceEvidenceDto`, `CandidateErrorTypeDto`, `CausalRepairStatusDto`, `ClaimCandidateDto`, `ColdCheckResultDto`, `CriterionEvidenceRowDto`, `ElicitingResponseResultDto`, `ErrorEventDto`, `FeedbackBundle`, `FollowupGateDiagnosticsDto`, `FollowupGateSignalDto`, `GradingClarificationDto`, `GuidedRedoDto`, `IntentRestorationDto`, `MasteryDto`, `MasteryStepDto`, `MatchedMisconceptionDto`, `NOT_ASSESSED_LABEL`, `PlanStepDto`, `PracticeItemDetail`, `QueueInput`, `RepairSuggestionDto`, `ResolvedSourceRefDto`, `ScheduledItemDto`, `UNVERIFIED_ROUTE_REVIEW_REASON`, `UnresolvedCauseSelfReportResponse`, `criterionAssessed`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `algoConfig`, `masteryTone`
- [[Reference/Desktop/TypeScript/app/autoAdvance|src/app/autoAdvance.ts]] — import-or-re-export; imports `useNextQueueItem`
- [[Reference/Desktop/TypeScript/app/dailyPlan|src/app/dailyPlan.ts]] — import-or-re-export; imports `nextPlanKeyLabel`, `useNextPlanStep`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/app/practiceFeedback|src/app/practiceFeedback.ts]] — import-or-re-export; imports `FIX_MIX_UP_LABEL`, `FeedbackOrigin`, `VERDICT_TEXT`, `simplePracticeFeedback`, `verdictOf`
- [[Reference/Desktop/TypeScript/components/AsPrinted|src/components/AsPrinted.tsx]] — import-or-re-export; imports `PrintedAfterFeedback`, `printedPageInReader`
- [[Reference/Desktop/TypeScript/components/CardControls|src/components/CardControls.tsx]] — import-or-re-export; imports `CardControls`, `ProbeRemintAction`
- [[Reference/Desktop/TypeScript/components/CausalAttribution|src/components/CausalAttribution.tsx]] — import-or-re-export; imports `CausalFeedbackPanel`, `formatCausalTarget`, `formatDivergenceAnchor`, `useCausalRepairActions`
- [[Reference/Desktop/TypeScript/components/ClaimCheckFeedback|src/components/ClaimCheckFeedback.tsx]] — import-or-re-export; imports `ClaimCheckFeedback`
- [[Reference/Desktop/TypeScript/components/ClaimSurface|src/components/ClaimSurface.tsx]] — import-or-re-export; imports `ClaimSurface`, `mintVisitId`
- [[Reference/Desktop/TypeScript/components/DiagnosisCard|src/components/DiagnosisCard.tsx]] — import-or-re-export; imports `DiagnosisCard`, `useDiagnosisCard`
- [[Reference/Desktop/TypeScript/components/IntentCheckFeedback|src/components/IntentCheckFeedback.tsx]] — import-or-re-export; imports `IntentCheckFeedback`
- [[Reference/Desktop/TypeScript/components/KnowledgeModel|src/components/KnowledgeModel.tsx]] — import-or-re-export; imports `AttemptTraceView`, `UnresolvedCauseCard`
- [[Reference/Desktop/TypeScript/components/PlainParts|src/components/PlainParts.tsx]] — import-or-re-export; imports `PrimaryAction`, `QuietAction`
- [[Reference/Desktop/TypeScript/components/RepairAffordances|src/components/RepairAffordances.tsx]] — import-or-re-export; imports `CommonRepairCard`, `GuidedRedoAffordance`
- [[Reference/Desktop/TypeScript/components/RepairTrace|src/components/RepairTrace.tsx]] — import-or-re-export; imports `RepairTraceBlocks`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `modePillColor`
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export; imports `EntityLink`, `KeyBar`, `Pill`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
- [[Reference/Desktop/TypeScript/screens/feedback/CompareMethods|src/screens/feedback/CompareMethods.tsx]] — import-or-re-export; imports `CompareMethods`
- [[Reference/Desktop/TypeScript/screens/feedback/FeedbackSurface|src/screens/feedback/FeedbackSurface.tsx]] — import-or-re-export; imports `FeedbackNextStep`, `FeedbackSurface`, `answeredCriterionRows`, `answeredMaxPoints`, `gradedVersionUnrecorded`, `scoreOutOf`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `@tauri-apps/plugin-opener`, `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/RepairOverFeedback.phase4.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/RepairOverFeedback.phase4.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/FeedbackScreen.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/FeedbackScreen.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/FeedbackScreen.plan.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/FeedbackScreen.plan.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/FeedbackScreen.phase4.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/FeedbackScreen.phase4.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/FeedbackScreen.liveQueue.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/FeedbackScreen.liveQueue.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/copy/denyList.phase4.test.tsx](../../../../../../apps/learnloop-tauri/src/copy/denyList.phase4.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_active_errors_overlay.py](../../../../../../tests/test_active_errors_overlay.py) — cross-boundary name contract: references uniquely owned exported name `FeedbackScreen`; it does **not** directly execute this source module.
- [tests/test_causal_repair_sidecar_rpcs.py](../../../../../../tests/test_causal_repair_sidecar_rpcs.py) — cross-boundary name contract: references uniquely owned exported name `FeedbackScreen`; it does **not** directly execute this source module.
- [tests/test_review_log.py](../../../../../../tests/test_review_log.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_learner_review_system_entries.py](../../../../../../tests/test_learner_review_system_entries.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_forecast_ledger.py](../../../../../../tests/test_forecast_ledger.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/FeedbackScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/FeedbackScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
