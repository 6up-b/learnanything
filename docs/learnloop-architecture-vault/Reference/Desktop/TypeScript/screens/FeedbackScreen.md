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
| Source lines | 3633 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]]

## Public API

- `export function FeedbackScreen(` — function, line 1480

## Internal implementation anchors

- `type FeedbackOrigin, simplePracticeFeedback, UNASSESSED_ROUTE_LINE, unestablishedRepairCopy, VERDICT_TEXT, verdictOf } from "../app/practiceFeedback"` — type, line 58
- `type FeedbackNextStep, type RedoContext } from "./feedback/FeedbackSurface"` — type, line 72
- `type RedoContext } from "./feedback/FeedbackSurface"` — type, line 73
- `const C =` — const, line 84
- `const WHY_CAUSES_SHOWN = 3` — const, line 102
- `const MONO = '"JetBrains Mono", "Fira Code", ui-monospace, SFMono-Regular, Menlo, monospace'` — const, line 103
- `function Faint(` — function, line 106
- `function Dim(` — function, line 109
- `function Meta(` — function, line 112
- `function FbHeader(` — function, line 117
- `function EvidenceHeader(` — function, line 136
- `function BlockBar(` — function, line 153
- `const filled = Math.max(0, Math.min(width, Math.round((value / max) * width)))` — const, line 156
- `function fmtDue(iso: string | null): string` — function, line 166
- `const d = new Date(iso)` — const, line 169
- `const now = new Date()` — const, line 170
- `const diffH = (d.getTime() - now.getTime()) / 3_600_000` — const, line 171
- `const tomorrow = new Date(now)` — const, line 172
- `function fmtDay(iso: string | null | undefined): string` — function, line 192
- `function ColdCheckBanner(` — function, line 205
- `const confirmed = result.claim === "repair_confirmed"` — const, line 206
- `const failed = result.claim === "escalated_unrepaired"` — const, line 207
- `const tone = confirmed ? C.green : failed ? C.amber : C.textDim` — const, line 208
- `const heading = confirmed ? "unassisted check · passed" : failed ? "unassisted check · did not hold" : result.claim === "repair_effect_unestablished" ? "unassisted check" : "unassisted check · no verdict"` — const, line 209
- `const when = fmtDay(result.instructedAt)` — const, line 216
- `const body = confirmed ? `This was the unassisted check for the repair you did on $` — const, line 217
- `function AutoPrimedNote(` — function, line 252
- `function ElicitingRepairCard(` — function, line 283
- `const anchor = suggestion.targetRefs?.[0] ?? null` — const, line 295
- `const answered = outcome != null` — const, line 296
- `function ratingPill(r: string): string` — function, line 386
- `function modePillTone(mode: string): string` — function, line 393
- `function ScoreBlock(` — function, line 398
- `const tone = score === max ? C.green : score >= max * 0.75 ? C.greenSoft : score >= max * 0.5 ? C.amber : C.red` — const, line 400
- `const label = score === max ? "perfect" : score >= max * 0.75 ? "good" : score >= max * 0.5 ? "partial credit" : "needs work"` — const, line 404
- `function CriterionRow(` — function, line 446
- `const assessed = criterionAssessed(row)` — const, line 460
- `const ok = maxKnown && row.pointsAwarded === row.pointsPossible` — const, line 461
- `const partial = maxKnown && row.pointsAwarded > 0 && row.pointsAwarded < row.pointsPossible` — const, line 462
- `const mark = !assessed ? "–" : !maxKnown ? "·" : ok ? "✓" : partial ? "◐" : "✗"` — const, line 463
- `const tone = !assessed || !maxKnown ? C.textDim : ok ? C.green : partial ? C.amber : C.red` — const, line 464
- `function ErrorAttribution(` — function, line 502
- `const plan = ea.repairPlan` — const, line 503
- `const resolutionStatus = typeof plan?.resolutionStatus === "string" ? plan.resolutionStatus : null` — const, line 504
- `const causeScope = typeof plan?.causeScope === "string" ? plan.causeScope : null` — const, line 506
- `const operation = typeof plan?.operation === "string" ? plan.operation : null` — const, line 507
- `const abstentionReason = typeof plan?.abstentionReason === "string" ? plan.abstentionReason : null` — const, line 508
- `const targetRef = plan?.targetRef && typeof plan.targetRef === "object" && !Array.isArray(plan.targetRef) ? plan.targetRef as Parameters<typeof formatCausalTarget>[0] : null` — const, line 510
- `const firstDivergence = plan?.firstDivergence && typeof plan.firstDivergence === "object" && !Array.isArray(plan.firstDivergence) ? plan.firstDivergence as Parameters<typeof formatDivergenceAnchor>[0] : null` — const, line 514
- `const SQRT_2PI = Math.sqrt(2 * Math.PI)` — const, line 580
- `const PROB_TICKS = [0.1, 0.25, 0.5, 0.75, 0.9]` — const, line 581
- `function logit(p: number): number` — function, line 583
- `const c = Math.min(1 - 1e-4, Math.max(1e-4, p))` — const, line 584
- `function toLogitSpace(mean: number, variance: number):` — function, line 590
- `const m = Math.min(1 - 1e-4, Math.max(1e-4, mean))` — const, line 591
- `const slope = m * (1 - m)` — const, line 592
- `const logitVar = Math.max(1e-4, variance / (slope * slope))` — const, line 593
- `function gaussianPdf(x: number, mu: number, sd: number): number` — function, line 597
- `const z = (x - mu) / sd` — const, line 598
- `function BeliefShiftChart(` — function, line 607
- `const prior = toLogitSpace(before.mean, before.variance)` — const, line 622
- `const post = toLogitSpace(after.mean, after.variance)` — const, line 623
- `const padL = 8` — const, line 625
- `const padR = 8` — const, line 626
- `const padT = 20` — const, line 627
- `const padB = 20` — const, line 628
- `const plotW = width - padL - padR` — const, line 629
- `const plotH = height - padT - padB` — const, line 630
- `const lo = Math.min(prior.mu - 3.4 * prior.sd, post.mu - 3.4 * post.sd, logit(0.15))` — const, line 634
- `const hi = Math.max(prior.mu + 3.4 * prior.sd, post.mu + 3.4 * post.sd, logit(0.85))` — const, line 635
- `const span = Math.max(1e-3, hi - lo)` — const, line 636
- `const xOf = (t: number)` — const, line 637
- `const peak = Math.max(gaussianPdf(prior.mu, prior.mu, prior.sd), gaussianPdf(post.mu, post.mu, post.sd))` — const, line 640
- `const yMax = peak * 1.12` — const, line 641
- `const baseY = padT + plotH` — const, line 642
- `const yOf = (d: number)` — const, line 643
- `const N = 72` — const, line 645
- `const curvePath = (mu: number, sd: number, close: boolean): string` — const, line 646
- `let d = ""` — let, line 647
- `const x = lo + (span * i) / N` — const, line 649
- `const y = gaussianPdf(x, mu, sd)` — const, line 650
- `const postColor = masteryTone(after.mean, C)` — const, line 657
- `const shift = post.mu - prior.mu` — const, line 658
- `const showArrow = bayesianSurprise > tau && Math.abs(shift) > 1e-3` — const, line 659
- `const arrowColor = shift >= 0 ? C.green : C.red` — const, line 660
- `const arrowY = 11` — const, line 661
- `const xPrior = xOf(prior.mu)` — const, line 662
- `const xPost = xOf(post.mu)` — const, line 663
- `const yPrior = yOf(gaussianPdf(prior.mu, prior.mu, prior.sd))` — const, line 664
- `const yPost = yOf(gaussianPdf(post.mu, post.mu, post.sd))` — const, line 665
- `const t = logit(p)` — const, line 671
- `const x = xOf(t)` — const, line 673
- `const mid = p === 0.5` — const, line 674
- `function MasteryStepBreakdown(` — function, line 729
- `const pct = (v: number)` — const, line 731
- `const dominant = factor.key === step.dominantFactorKey` — const, line 747
- `const removed = 1 - factor.multiplier` — const, line 750
- `const color = dominant ? C.amber : removed < 0 ? C.greenSoft : C.textDim` — const, line 751
- `function MasteryDelta(` — function, line 801
- `const tau = surprise.followupThresholdNats ?? algoConfig().tauFollowupNats` — const, line 807
- `const bayes = surprise.bayesianSurprise ?? 0` — const, line 808
- `const hasSurprise = bayes > tau` — const, line 809
- `const postColor = masteryTone(after.mean, C)` — const, line 810
- `const evidence = f.criterionEvidence ?? []` — const, line 811
- `const assessed = criterionAssessed(row)` — const, line 859
- `const ok = row.pointsAwarded === row.pointsPossible` — const, line 860
- `const partial = row.pointsAwarded > 0 && row.pointsAwarded < row.pointsPossible` — const, line 861
- `const mark = !assessed ? "–" : ok ? "✓" : partial ? "◐" : "✗"` — const, line 862
- `const tone = !assessed ? C.textDim : ok ? C.green : partial ? C.amber : C.red` — const, line 863
- `function followupStatus(f: FeedbackBundle, tau: number): string` — function, line 892
- `const gate = f.surprise.gateDiagnostics` — const, line 896
- `const reasons = interventionReasons(f.surprise.triggeredActions ?? [])` — const, line 899
- `const suppressed = f.surprise.suppressedActions ?? []` — const, line 908
- `const GATE_SIGNAL_LABELS: Record<string, string> =` — const, line 917
- `const GATE_COMPARATORS: Record<string, string> =` — const, line 929
- `function gateNum(value: number | boolean | null): string | null` — function, line 933
- `function describeSignal(sig: FollowupGateSignalDto): string` — function, line 939
- `const name = sig.name ?? ""` — const, line 940
- `const label = GATE_SIGNAL_LABELS[name] ?? name.replace(/_/g, " ")` — const, line 946
- `const value = gateNum(sig.value)` — const, line 947
- `const cmp = sig.comparator ? GATE_COMPARATORS[sig.comparator] ?? sig.comparator : ""` — const, line 948
- `let threshold = gateNum(sig.threshold)` — let, line 949
- `const unit = sig.unit === "nats" ? " nats" : ""` — const, line 958
- `function describeGate(gate: FollowupGateDiagnosticsDto): string` — function, line 966
- `const sig = gate.decisiveSignal` — const, line 967
- `const signalText = sig ? describeSignal(sig) : gate.decisiveReason.replace(/_/g, " ")` — const, line 968
- `const scoreSuffix = typeof gate.gateScore === "number" && sig?.name !== "gate_score" ? ` · score $` — const, line 971
- `const base = (()` — const, line 976
- `const trigger = gate.triggeredReasons.find((r)` — const, line 986
- `const trigText = trigger ? trigger.replace(/_/g, " ") : "trigger"` — const, line 987
- `const v = gateNum(sig.value)` — const, line 997
- `function interventionReasons(actions: string[]): string[]` — function, line 1006
- `const reasons = actions .map((action)` — const, line 1007
- `function formatInterventionAction(action: string): string` — function, line 1018
- `function fmtTimestamp(seconds: number): string` — function, line 1030
- `const total = Math.max(0, Math.floor(seconds))` — const, line 1031
- `const h = Math.floor(total / 3600)` — const, line 1032
- `const m = Math.floor((total % 3600) / 60)` — const, line 1033
- `const s = total % 60` — const, line 1034
- `const mm = h > 0 ? String(m).padStart(2, "0") : String(m)` — const, line 1035
- `function timeRangeLabel(video:` — function, line 1039
- `function SourceRefCard(` — function, line 1045
- `const video = sourceRef.video` — const, line 1054
- `const openExternal = async (url: string)` — const, line 1056
- `const externalVideoUrl = video ? `https://www.youtube.com/watch?v=$` — const, line 1065
- `const openInReader = !externalVideoUrl && sourceId && onOpenPassage ? ()` — const, line 1070
- `const embedUrl = video ? `https://www.youtube-nocookie.com/embed/$` — const, line 1075
- `function SourceReviewPanel(` — function, line 1150
- `const refs = (f.sourceRefs ?? []).filter((ref)` — const, line 1159
- `const missed = f.rubricScore < f.maxPoints` — const, line 1162
- `function statementPairCopy(m: MatchedMisconceptionDto): string` — function, line 1222
- `const correction = m.correctionStatement.trim()` — const, line 1223
- `const x = m.targetFacet?.trim()` — const, line 1224
- `const y = m.confusedWithFacet?.trim()` — const, line 1225
- `const head = x && y ? `Your last answer was consistent with confusing $` — const, line 1226
- `function MisconceptionStatementCard(` — function, line 1233
- `const claim: ClaimCandidateDto = useMemo( ()` — const, line 1248
- `type RegradeSide =` — type, line 1295
- `type RegradeReceipt =` — type, line 1296
- `function gradeSide(f: FeedbackBundle): RegradeSide` — function, line 1298
- `function newClientKey(prefix: "contest"): string` — function, line 1307
- `const random = globalThis.crypto?.randomUUID?.()` — const, line 1308
- `function regradeHistoryLine(` — function, line 1314
- `const words = (side: RegradeSide)` — const, line 1316
- `const side = (s: RegradeSide)` — const, line 1323
- `function RegradeLedgerCard(` — function, line 1327
- `const claim: ClaimCandidateDto = useMemo( ()` — const, line 1341
- `const PROVISIONAL_PENDING_CLARIFICATION = "provisional_pending_clarification"` — const, line 1371
- `const CLARIFICATION_REASON_COPY: Record<string, string> =` — const, line 1375
- `function clarificationOutcomeCopy(result: AnswerGradingClarificationResultDto): string` — function, line 1383
- `function ClarificationCard(` — function, line 1395
- `const simple = simplePracticeFeedback()` — const, line 1563
- `const visitId = useRef(mintVisitId()).current` — const, line 1586
- `const planMode = Boolean(nextPlan && onPlanStep)` — const, line 1591
- `const autoAdvance = Boolean(nextQueue && onOpenNext) && !planMode` — const, line 1592
- `const nextItem = useNextQueueItem(autoAdvance ? nextQueue : null, feedback !== null)` — const, line 1593
- `const nextPlanStep = useNextPlanStep(planMode && nextPlan ? nextPlan.sessionId : null, feedback !== null)` — const, line 1594
- `const planDone = planMode && nextPlanStep.step?.kind === "done"` — const, line 1597
- `const nextReading = useNextReadingQuestion(planMode ? nextQueue : null, planDone, feedback?.practiceItemId ?? null)` — const, line 1598
- `const readingLabel = !planDone ? null : nextReading.known ? nextReading.item : "unknown"` — const, line 1599
- `const advanceGeneration = useRef(0)` — const, line 1601
- `const advancingRef = useRef(false)` — const, line 1602
- `const pendingQueueWrites = useRef(new Set<Promise<void>>())` — const, line 1608
- `const trackQueueWrite = useCallback(<T,>(write: Promise<T>): Promise<T>` — const, line 1609
- `const settledWrite: Promise<void> = write.then(()` — const, line 1610
- `const resolveNext = nextItem.resolve` — const, line 1615
- `const resolvePlanStep = nextPlanStep.resolve` — const, line 1616
- `const openNextReading = nextReading.open` — const, line 1617
- `const followup = followupRead && followupRead.workflowId === feedback?.followup?.workflowId ? followupRead : feedback?.followup ?? null` — const, line 1627
- `const followupRef = useRef<FollowupDto | null>(null)` — const, line 1631
- `const followupHeldRef = useRef(false)` — const, line 1632
- `const goOn = useCallback(async ()` — const, line 1635
- `const generation = ++advanceGeneration.current` — const, line 1639
- `let step: PlanStepDto | null = null` — let, line 1641
- `const picked = await openNextReading(nextPlan.sessionId).catch(()` — const, line 1648
- `const generation = ++advanceGeneration.current` — const, line 1666
- `let head: ScheduledItemDto | null = null` — let, line 1668
- `const actOnNext = useCallback((next: FollowupNextDto | null)` — const, line 1683
- `const actOnNextRef = useRef(actOnNext)` — const, line 1695
- `const advance = useCallback(async ()` — const, line 1697
- `const owner = followupRef.current` — const, line 1698
- `let next: FollowupNextDto | null = null` — let, line 1700
- `const somethingElseChosen = useCallback((result: SomethingElseChosenDto)` — const, line 1713
- `const entry = lessonEntryFor(result)` — const, line 1714
- `const followupOpen = followup !== null && (followup.state === "pending" || followup.held)` — const, line 1725
- `let stopped = false` — let, line 1728
- `const timer = window.setInterval(()` — const, line 1729
- `const asked = nextWaiting ? api.followupNext(attemptId).then((next)` — const, line 1732
- `const wasHeld = useRef(false)` — const, line 1752
- `const continueWithout = useCallback(async ()` — const, line 1760
- `const status = await api.followupStatus(attemptId).catch(()` — const, line 1763
- `const showAnyway = useCallback(async ()` — const, line 1770
- `const status = await api.followupStatus(attemptId).catch(()` — const, line 1772
- `const goBack = useCallback(()` — const, line 1778
- `const refreshAfterDiagnosis = useCallback(()` — const, line 1787
- `const diagnosis = useDiagnosisCard(attemptId, simple ? feedback?.diagnosisStatus : null, refreshAfterDiagnosis, onError)` — const, line 1796
- `const contestKey = useRef<` — const, line 1808
- `const marksKept = useRef<` — const, line 1814
- `const marksRead = marksKept.current?.attemptId === attemptId ? marksKept.current.marks : null` — const, line 1816
- `const tapReplaced = marksRead !== null && marksRead.attemptId === feedback?.attemptId && marksRead.replacesCardTap` — const, line 1817
- `const listsOn = marksRead !== null && feedback?.attemptId === attemptId` — const, line 1818
- `const causalHypotheses = feedback?.causalFeedback?.causalHypotheses ?? []` — const, line 1819
- `const errorInputRef = useRef<HTMLInputElement>(null)` — const, line 1864
- `const noteTitleRef = useRef<HTMLInputElement>(null)` — const, line 1873
- `const noteBodyRef = useRef<HTMLTextAreaElement>(null)` — const, line 1874
- `const suggestions = useMemo<CandidateErrorTypeDto[]>(()` — const, line 1876
- `const all = item?.candidateErrorTypes ?? []` — const, line 1877
- `const q = errorTypeInput.trim().toLowerCase()` — const, line 1878
- `const filtered = q ? all.filter((e)` — const, line 1879
- `let cancelled = false` — let, line 1886
- `let cancelled = false` — let, line 1922
- `const handleAnswerClarification = async ()` — const, line 1941
- `const answer = clarificationAnswer.trim()` — const, line 1942
- `const result = await trackQueueWrite(api.answerGradingClarification(feedback.attemptId, answer))` — const, line 1946
- `const handleSkipClarification = ()` — const, line 1966
- `const applyRepairStatus = useCallback( (next: CausalRepairStatusDto)` — const, line 1978
- `const repairCaseId = useMemo(()` — const, line 1990
- `const causal = feedback?.causalFeedback` — const, line 1991
- `const need = causal?.probeNeed` — const, line 1992
- `let cancelled = false` — let, line 2009
- `const inspectIds = feedback ? uniqueIds([ feedback.attemptId, feedback.practiceItemId, feedback.learningObjectId, ...feedback.errorAttributions.map((event)` — const, line 2044
- `const practiceItemIds = feedback ? uniqueIds([feedback.practiceItemId]) : []` — const, line 2053
- `const shownAttempt = useRef(attemptId)` — const, line 2073
- `const refreshItemAfterRegrade = useCallback((bundle: FeedbackBundle)` — const, line 2075
- `const handleRegrade = async ()` — const, line 2084
- `const before = gradeSide(feedback)` — const, line 2087
- `const updated = await trackQueueWrite(api.triggerRegrade(feedback.attemptId))` — const, line 2089
- `const handleContest = async ()` — const, line 2108
- `const before = verdictOf(` — const, line 2112
- `const prior = gradeSide(feedback)` — const, line 2115
- `const reason = contestReason.trim()` — const, line 2116
- `const bound = contestKey.current` — const, line 2117
- `const key = bound && bound.reason === reason ? bound.key : newClientKey("contest")` — const, line 2118
- `const updated = await trackQueueWrite(api.triggerRegrade(feedback.attemptId, reason, key))` — const, line 2121
- `const outcome = updated.contest` — const, line 2125
- `const reviewed = outcome?.reviewRequested ? " It's marked for review." : ""` — const, line 2126
- `const after = verdictOf(` — const, line 2131
- `const contestCausal = (reason: UnresolvedCauseSelfReportResponse, factorId: string | null | undefined)` — const, line 2152
- `const handleTriggerFollowup = async ()` — const, line 2175
- `const updated = await trackQueueWrite(api.triggerFollowup(feedback.attemptId))` — const, line 2179
- `const handlePrimedRetry = async ()` — const, line 2192
- `const result = await api.startPrimedRetry(feedback.attemptId)` — const, line 2196
- `const handleGuidedRedo = async ()` — const, line 2214
- `const redo = await api.startGuidedRedo(feedback.attemptId)` — const, line 2218
- `const handleRateFollowup = async (useful: boolean)` — const, line 2230
- `const updated = await api.rateFollowup(feedback.attemptId, useful)` — const, line 2234
- `const handleElicitingResponse = async (suggestionIndex: number, responseMd: string)` — const, line 2249
- `const result = await trackQueueWrite(api.submitElicitingResponse(` — const, line 2253
- `const doAddError = async (errorType: string, severity?: number)` — const, line 2270
- `const updated = await api.addErrorEvent(feedback.attemptId, errorType.trim(), severity)` — const, line 2278
- `const handleAddError = ()` — const, line 2289
- `const sel = selectedSuggestionIdx >= 0 ? suggestions[selectedSuggestionIdx] : null` — const, line 2290
- `const handleUnresolvedCauseReport = async ( factorId: string, response: UnresolvedCauseSelfReportResponse, candidateIndex?: number | null, )` — const, line 2294
- `const resetNote = ()` — const, line 2311
- `const openNoteCapture = ()` — const, line 2318
- `const doSaveNote = async ()` — const, line 2324
- `const title = noteTitle.trim()` — const, line 2326
- `const body = noteBody.trim()` — const, line 2327
- `const subjectId = item?.subject ?? item?.subjects?.[0] ?? null` — const, line 2332
- `const stamp = new Date().toISOString().replace(/[-:T.]/g, "").slice(0, 14)` — const, line 2340
- `const noteId = `$` — const, line 2341
- `const result = await api.addNote(` — const, line 2344
- `const onKey = (event: KeyboardEvent)` — const, line 2363
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 2367
- `const right = verdictOf(` — const, line 2383
- `function simpleScreen( f: FeedbackBundle, matchedMisconception: FeedbackBundle["matchedMisconception"] | null, elicitingIndex: number, elicitingSuggestion: FeedbackBundle["repairSuggestions"][number] | null, errorPanel: ReactNode, notePanel: ReactNode, )` — function, line 2408
- `const held = f.heldForReview === true` — const, line 2416
- `const verdict = verdictOf(` — const, line 2417
- `const contestAvailable = f.gradingSource !== "self" && verdict !== "right"` — const, line 2419
- `const fixId = matchedMisconception?.id ?? (!repairStatus ? f.causalFeedback?.commonRepair?.misconceptionId ?? null : null)` — const, line 2423
- `let step: FeedbackNextStep | null = null` — let, line 2426
- `let stepIsRetry = false` — let, line 2427
- `const probeIsNext = followup !== null && (followup.state === "pending" || followup.state === "ready")` — const, line 2429
- `const card = diagnosis.status === "done" ? diagnosis.card : null` — const, line 2443
- `const causal = f.causalFeedback ?? null` — const, line 2444
- `const canSayNotRight = !tapReplaced && Boolean(card?.diagnosisId && card.responses.some((option)` — const, line 2446
- `const causalNotRightOk = Boolean(causal?.contestAction?.available && causal.contestAction.reasons.includes("diagnosis_wrong"))` — const, line 2447
- `const why =` — const, line 2448
- `const nextLabel = nextWaiting ? "preparing a question…" : origin === "reader" ? "back to the book" : planMode ? nextPlanKeyLabel(advancing, nextPlanStep.step, readingLabel) : autoAdvance ? nextKeyLabel(autoAdvance, advancing, nextItem.head, nextItem.empty) :…` — const, line 2474
- `const regradeHistory: RegradeReceipt | null = regradeReceipt ?? (f.regrade ?` — const, line 2484
- `const criteria = answeredCriterionRows(f)` — const, line 2496
- `const showTier = f.criterionEvidence.some((row)` — const, line 2497
- `const f = feedback` — const, line 2857
- `const subject = item?.subject ?? item?.subjects?.[0] ?? null` — const, line 2858
- `const tau = f.surprise.followupThresholdNats ?? algoConfig().tauFollowupNats` — const, line 2860
- `const interventionNeed = f.interventionNeed` — const, line 2861
- `const elicitingIndex = f.repairSuggestions.findIndex((s)` — const, line 2865
- `const elicitingSuggestion = elicitingIndex >= 0 ? f.repairSuggestions[elicitingIndex] : null` — const, line 2866
- `const matchedMisconception = f.matchedMisconception && f.matchedMisconception.correctionStatement?.trim() ? f.matchedMisconception : null` — const, line 2870
- `const errorPanel = addingError ? ( <div style=` — const, line 2877
- `const s = suggestions[selectedSuggestionIdx]` — const, line 2924
- `const notePanel = addingNote ? ( <div style=` — const, line 2952
- `const receipt: RegradeReceipt | null = regradeReceipt ?? (f.regrade ?` — const, line 3372
- `function nextKeyLabel( autoAdvance: boolean, advancing: boolean, head: ScheduledItemDto | null, empty: boolean ): string` — function, line 3615
- `const title = head.learningObjectTitle` — const, line 3624
- `function uniqueIds(values: Array<string | null | undefined>): string[]` — function, line 3631

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `FeedbackScreen`; references `FeedbackScreen`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AnswerGradingClarificationResultDto`, `AttemptTraceDto`, `AttemptTraceEvidenceDto`, `CandidateErrorTypeDto`, `CausalRepairStatusDto`, `ClaimCandidateDto`, `ColdCheckResultDto`, `CriterionEvidenceRowDto`, `ElicitingResponseResultDto`, `ErrorEventDto`, `FeedbackBundle`, `FollowupDto`, `FollowupGateDiagnosticsDto`, `FollowupGateSignalDto`, `FollowupNextDto`, `GradingClarificationDto`, `HypothesisMarksDto`, `IntentRestorationDto`, `MasteryDto`, `MasteryStepDto`, `MatchedMisconceptionDto`, `NOT_ASSESSED_LABEL`, `PlanStepDto`, `PracticeItemDetail`, `QueueInput`, `RepairSuggestionDto`, `ResolvedSourceRefDto`, `ScheduledItemDto`, `SomethingElseChosenDto`, `UNVERIFIED_ROUTE_REVIEW_REASON`, `UnresolvedCauseSelfReportResponse`, `criterionAssessed`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `algoConfig`, `masteryTone`
- [[Reference/Desktop/TypeScript/app/autoAdvance|src/app/autoAdvance.ts]] — import-or-re-export; imports `useNextQueueItem`, `useNextReadingQuestion`
- [[Reference/Desktop/TypeScript/app/dailyPlan|src/app/dailyPlan.ts]] — import-or-re-export; imports `nextPlanKeyLabel`, `useNextPlanStep`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/app/practiceFeedback|src/app/practiceFeedback.ts]] — import-or-re-export; imports `FIX_MIX_UP_LABEL`, `FeedbackOrigin`, `UNASSESSED_ROUTE_LINE`, `VERDICT_TEXT`, `simplePracticeFeedback`, `unestablishedRepairCopy`, `verdictOf`
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
- [[Reference/Desktop/TypeScript/components/Waiting|src/components/Waiting.tsx]] — import-or-re-export; imports `Waiting`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `modePillColor`
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export; imports `EntityLink`, `KeyBar`, `Pill`
- [[Reference/Desktop/TypeScript/copy/refusals|src/copy/refusals.ts]] — import-or-re-export; imports `NOTE_NO_SUBJECT`
- [[Reference/Desktop/TypeScript/copy/waiting|src/copy/waiting.ts]] — import-or-re-export; imports `WAITING_COPY`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
- [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]] — import-or-re-export; imports `LessonEntry`
- [[Reference/Desktop/TypeScript/screens/feedback/CompareMethods|src/screens/feedback/CompareMethods.tsx]] — import-or-re-export; imports `CompareMethods`
- [[Reference/Desktop/TypeScript/screens/feedback/FeedbackSurface|src/screens/feedback/FeedbackSurface.tsx]] — import-or-re-export; imports `FeedbackNextStep`, `FeedbackSurface`, `RedoContext`, `answeredCriterionRows`, `answeredMaxPoints`, `gradedVersionUnrecorded`, `missedRubricLines`, `scoreOutOf`
- [[Reference/Desktop/TypeScript/screens/feedback/FollowupPanel|src/screens/feedback/FollowupPanel.tsx]] — import-or-re-export; imports `FollowupPanel`
- [[Reference/Desktop/TypeScript/screens/feedback/HypothesisMarks|src/screens/feedback/HypothesisMarks.tsx]] — import-or-re-export; imports `HypothesisMarksPanel`, `useHypothesisListExposure`
- [[Reference/Desktop/TypeScript/screens/today/SomethingElse|src/screens/today/SomethingElse.tsx]] — import-or-re-export; imports `SomethingElse`, `lessonEntryFor`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `@tauri-apps/plugin-opener`, `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/RepairOverFeedback.phase4.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/RepairOverFeedback.phase4.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/FeedbackScreen.waiting.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/FeedbackScreen.waiting.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/FeedbackScreen.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/FeedbackScreen.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/FeedbackScreen.somethingElse.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/FeedbackScreen.somethingElse.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/FeedbackScreen.refusals.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/FeedbackScreen.refusals.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/FeedbackScreen.plan.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/FeedbackScreen.plan.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/FeedbackScreen.phase4.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/FeedbackScreen.phase4.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/FeedbackScreen.liveQueue.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/FeedbackScreen.liveQueue.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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
