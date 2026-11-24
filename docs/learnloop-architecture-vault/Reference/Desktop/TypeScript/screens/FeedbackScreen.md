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
| Source lines | 3665 |
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

- `export function FeedbackScreen(` — function, line 1486

## Internal implementation anchors

- `type FeedbackOrigin, simplePracticeFeedback, UNASSESSED_ROUTE_LINE, unestablishedRepairCopy, VERDICT_TEXT, verdictOf } from "../app/practiceFeedback"` — type, line 64
- `type FeedbackNextStep, type RedoContext } from "./feedback/FeedbackSurface"` — type, line 78
- `type RedoContext } from "./feedback/FeedbackSurface"` — type, line 79
- `const C =` — const, line 90
- `const WHY_CAUSES_SHOWN = 3` — const, line 108
- `const MONO = '"JetBrains Mono", "Fira Code", ui-monospace, SFMono-Regular, Menlo, monospace'` — const, line 109
- `function Faint(` — function, line 112
- `function Dim(` — function, line 115
- `function Meta(` — function, line 118
- `function FbHeader(` — function, line 123
- `function EvidenceHeader(` — function, line 142
- `function BlockBar(` — function, line 159
- `const filled = Math.max(0, Math.min(width, Math.round((value / max) * width)))` — const, line 162
- `function fmtDue(iso: string | null): string` — function, line 172
- `const d = new Date(iso)` — const, line 175
- `const now = new Date()` — const, line 176
- `const diffH = (d.getTime() - now.getTime()) / 3_600_000` — const, line 177
- `const tomorrow = new Date(now)` — const, line 178
- `function fmtDay(iso: string | null | undefined): string` — function, line 198
- `function ColdCheckBanner(` — function, line 211
- `const confirmed = result.claim === "repair_confirmed"` — const, line 212
- `const failed = result.claim === "escalated_unrepaired"` — const, line 213
- `const tone = confirmed ? C.green : failed ? C.amber : C.textDim` — const, line 214
- `const heading = confirmed ? "unassisted check · passed" : failed ? "unassisted check · did not hold" : result.claim === "repair_effect_unestablished" ? "unassisted check" : "unassisted check · no verdict"` — const, line 215
- `const when = fmtDay(result.instructedAt)` — const, line 222
- `const body = confirmed ? `This was the unassisted check for the repair you did on $` — const, line 223
- `function AutoPrimedNote(` — function, line 258
- `function ElicitingRepairCard(` — function, line 289
- `const anchor = suggestion.targetRefs?.[0] ?? null` — const, line 301
- `const answered = outcome != null` — const, line 302
- `function ratingPill(r: string): string` — function, line 392
- `function modePillTone(mode: string): string` — function, line 399
- `function ScoreBlock(` — function, line 404
- `const tone = score === max ? C.green : score >= max * 0.75 ? C.greenSoft : score >= max * 0.5 ? C.amber : C.red` — const, line 406
- `const label = score === max ? "perfect" : score >= max * 0.75 ? "good" : score >= max * 0.5 ? "partial credit" : "needs work"` — const, line 410
- `function CriterionRow(` — function, line 452
- `const assessed = criterionAssessed(row)` — const, line 466
- `const ok = maxKnown && row.pointsAwarded === row.pointsPossible` — const, line 467
- `const partial = maxKnown && row.pointsAwarded > 0 && row.pointsAwarded < row.pointsPossible` — const, line 468
- `const mark = !assessed ? "–" : !maxKnown ? "·" : ok ? "✓" : partial ? "◐" : "✗"` — const, line 469
- `const tone = !assessed || !maxKnown ? C.textDim : ok ? C.green : partial ? C.amber : C.red` — const, line 470
- `function ErrorAttribution(` — function, line 508
- `const plan = ea.repairPlan` — const, line 509
- `const resolutionStatus = typeof plan?.resolutionStatus === "string" ? plan.resolutionStatus : null` — const, line 510
- `const causeScope = typeof plan?.causeScope === "string" ? plan.causeScope : null` — const, line 512
- `const operation = typeof plan?.operation === "string" ? plan.operation : null` — const, line 513
- `const abstentionReason = typeof plan?.abstentionReason === "string" ? plan.abstentionReason : null` — const, line 514
- `const targetRef = plan?.targetRef && typeof plan.targetRef === "object" && !Array.isArray(plan.targetRef) ? plan.targetRef as Parameters<typeof formatCausalTarget>[0] : null` — const, line 516
- `const firstDivergence = plan?.firstDivergence && typeof plan.firstDivergence === "object" && !Array.isArray(plan.firstDivergence) ? plan.firstDivergence as Parameters<typeof formatDivergenceAnchor>[0] : null` — const, line 520
- `const SQRT_2PI = Math.sqrt(2 * Math.PI)` — const, line 586
- `const PROB_TICKS = [0.1, 0.25, 0.5, 0.75, 0.9]` — const, line 587
- `function logit(p: number): number` — function, line 589
- `const c = Math.min(1 - 1e-4, Math.max(1e-4, p))` — const, line 590
- `function toLogitSpace(mean: number, variance: number):` — function, line 596
- `const m = Math.min(1 - 1e-4, Math.max(1e-4, mean))` — const, line 597
- `const slope = m * (1 - m)` — const, line 598
- `const logitVar = Math.max(1e-4, variance / (slope * slope))` — const, line 599
- `function gaussianPdf(x: number, mu: number, sd: number): number` — function, line 603
- `const z = (x - mu) / sd` — const, line 604
- `function BeliefShiftChart(` — function, line 613
- `const prior = toLogitSpace(before.mean, before.variance)` — const, line 628
- `const post = toLogitSpace(after.mean, after.variance)` — const, line 629
- `const padL = 8` — const, line 631
- `const padR = 8` — const, line 632
- `const padT = 20` — const, line 633
- `const padB = 20` — const, line 634
- `const plotW = width - padL - padR` — const, line 635
- `const plotH = height - padT - padB` — const, line 636
- `const lo = Math.min(prior.mu - 3.4 * prior.sd, post.mu - 3.4 * post.sd, logit(0.15))` — const, line 640
- `const hi = Math.max(prior.mu + 3.4 * prior.sd, post.mu + 3.4 * post.sd, logit(0.85))` — const, line 641
- `const span = Math.max(1e-3, hi - lo)` — const, line 642
- `const xOf = (t: number)` — const, line 643
- `const peak = Math.max(gaussianPdf(prior.mu, prior.mu, prior.sd), gaussianPdf(post.mu, post.mu, post.sd))` — const, line 646
- `const yMax = peak * 1.12` — const, line 647
- `const baseY = padT + plotH` — const, line 648
- `const yOf = (d: number)` — const, line 649
- `const N = 72` — const, line 651
- `const curvePath = (mu: number, sd: number, close: boolean): string` — const, line 652
- `let d = ""` — let, line 653
- `const x = lo + (span * i) / N` — const, line 655
- `const y = gaussianPdf(x, mu, sd)` — const, line 656
- `const postColor = masteryTone(after.mean, C)` — const, line 663
- `const shift = post.mu - prior.mu` — const, line 664
- `const showArrow = bayesianSurprise > tau && Math.abs(shift) > 1e-3` — const, line 665
- `const arrowColor = shift >= 0 ? C.green : C.red` — const, line 666
- `const arrowY = 11` — const, line 667
- `const xPrior = xOf(prior.mu)` — const, line 668
- `const xPost = xOf(post.mu)` — const, line 669
- `const yPrior = yOf(gaussianPdf(prior.mu, prior.mu, prior.sd))` — const, line 670
- `const yPost = yOf(gaussianPdf(post.mu, post.mu, post.sd))` — const, line 671
- `const t = logit(p)` — const, line 677
- `const x = xOf(t)` — const, line 679
- `const mid = p === 0.5` — const, line 680
- `function MasteryStepBreakdown(` — function, line 735
- `const pct = (v: number)` — const, line 737
- `const dominant = factor.key === step.dominantFactorKey` — const, line 753
- `const removed = 1 - factor.multiplier` — const, line 756
- `const color = dominant ? C.amber : removed < 0 ? C.greenSoft : C.textDim` — const, line 757
- `function MasteryDelta(` — function, line 807
- `const tau = surprise.followupThresholdNats ?? algoConfig().tauFollowupNats` — const, line 813
- `const bayes = surprise.bayesianSurprise ?? 0` — const, line 814
- `const hasSurprise = bayes > tau` — const, line 815
- `const postColor = masteryTone(after.mean, C)` — const, line 816
- `const evidence = f.criterionEvidence ?? []` — const, line 817
- `const assessed = criterionAssessed(row)` — const, line 865
- `const ok = row.pointsAwarded === row.pointsPossible` — const, line 866
- `const partial = row.pointsAwarded > 0 && row.pointsAwarded < row.pointsPossible` — const, line 867
- `const mark = !assessed ? "–" : ok ? "✓" : partial ? "◐" : "✗"` — const, line 868
- `const tone = !assessed ? C.textDim : ok ? C.green : partial ? C.amber : C.red` — const, line 869
- `function followupStatus(f: FeedbackBundle, tau: number): string` — function, line 898
- `const gate = f.surprise.gateDiagnostics` — const, line 902
- `const reasons = interventionReasons(f.surprise.triggeredActions ?? [])` — const, line 905
- `const suppressed = f.surprise.suppressedActions ?? []` — const, line 914
- `const GATE_SIGNAL_LABELS: Record<string, string> =` — const, line 923
- `const GATE_COMPARATORS: Record<string, string> =` — const, line 935
- `function gateNum(value: number | boolean | null): string | null` — function, line 939
- `function describeSignal(sig: FollowupGateSignalDto): string` — function, line 945
- `const name = sig.name ?? ""` — const, line 946
- `const label = GATE_SIGNAL_LABELS[name] ?? name.replace(/_/g, " ")` — const, line 952
- `const value = gateNum(sig.value)` — const, line 953
- `const cmp = sig.comparator ? GATE_COMPARATORS[sig.comparator] ?? sig.comparator : ""` — const, line 954
- `let threshold = gateNum(sig.threshold)` — let, line 955
- `const unit = sig.unit === "nats" ? " nats" : ""` — const, line 964
- `function describeGate(gate: FollowupGateDiagnosticsDto): string` — function, line 972
- `const sig = gate.decisiveSignal` — const, line 973
- `const signalText = sig ? describeSignal(sig) : gate.decisiveReason.replace(/_/g, " ")` — const, line 974
- `const scoreSuffix = typeof gate.gateScore === "number" && sig?.name !== "gate_score" ? ` · score $` — const, line 977
- `const base = (()` — const, line 982
- `const trigger = gate.triggeredReasons.find((r)` — const, line 992
- `const trigText = trigger ? trigger.replace(/_/g, " ") : "trigger"` — const, line 993
- `const v = gateNum(sig.value)` — const, line 1003
- `function interventionReasons(actions: string[]): string[]` — function, line 1012
- `const reasons = actions .map((action)` — const, line 1013
- `function formatInterventionAction(action: string): string` — function, line 1024
- `function fmtTimestamp(seconds: number): string` — function, line 1036
- `const total = Math.max(0, Math.floor(seconds))` — const, line 1037
- `const h = Math.floor(total / 3600)` — const, line 1038
- `const m = Math.floor((total % 3600) / 60)` — const, line 1039
- `const s = total % 60` — const, line 1040
- `const mm = h > 0 ? String(m).padStart(2, "0") : String(m)` — const, line 1041
- `function timeRangeLabel(video:` — function, line 1045
- `function SourceRefCard(` — function, line 1051
- `const video = sourceRef.video` — const, line 1060
- `const openExternal = async (url: string)` — const, line 1062
- `const externalVideoUrl = video ? `https://www.youtube.com/watch?v=$` — const, line 1071
- `const openInReader = !externalVideoUrl && sourceId && onOpenPassage ? ()` — const, line 1076
- `const embedUrl = video ? `https://www.youtube-nocookie.com/embed/$` — const, line 1081
- `function SourceReviewPanel(` — function, line 1156
- `const refs = (f.sourceRefs ?? []).filter((ref)` — const, line 1165
- `const missed = f.rubricScore < f.maxPoints` — const, line 1168
- `function statementPairCopy(m: MatchedMisconceptionDto): string` — function, line 1228
- `const correction = m.correctionStatement.trim()` — const, line 1229
- `const x = m.targetFacet?.trim()` — const, line 1230
- `const y = m.confusedWithFacet?.trim()` — const, line 1231
- `const head = x && y ? `Your last answer was consistent with confusing $` — const, line 1232
- `function MisconceptionStatementCard(` — function, line 1239
- `const claim: ClaimCandidateDto = useMemo( ()` — const, line 1254
- `type RegradeSide =` — type, line 1301
- `type RegradeReceipt =` — type, line 1302
- `function gradeSide(f: FeedbackBundle): RegradeSide` — function, line 1304
- `function newClientKey(prefix: "contest"): string` — function, line 1313
- `const random = globalThis.crypto?.randomUUID?.()` — const, line 1314
- `function regradeHistoryLine(` — function, line 1320
- `const words = (side: RegradeSide)` — const, line 1322
- `const side = (s: RegradeSide)` — const, line 1329
- `function RegradeLedgerCard(` — function, line 1333
- `const claim: ClaimCandidateDto = useMemo( ()` — const, line 1347
- `const PROVISIONAL_PENDING_CLARIFICATION = "provisional_pending_clarification"` — const, line 1377
- `const CLARIFICATION_REASON_COPY: Record<string, string> =` — const, line 1381
- `function clarificationOutcomeCopy(result: AnswerGradingClarificationResultDto): string` — function, line 1389
- `function ClarificationCard(` — function, line 1401
- `const simple = simplePracticeFeedback()` — const, line 1570
- `const visitId = useRef(mintVisitId()).current` — const, line 1593
- `const planMode = Boolean(nextPlan && onPlanStep)` — const, line 1598
- `const autoAdvance = Boolean(nextQueue && onOpenNext) && !planMode` — const, line 1599
- `const nextItem = useNextQueueItem(autoAdvance ? nextQueue : null, feedback !== null)` — const, line 1600
- `const nextPlanStep = useNextPlanStep(planMode && nextPlan ? nextPlan.sessionId : null, feedback !== null)` — const, line 1601
- `const planDone = planMode && nextPlanStep.step?.kind === "done"` — const, line 1604
- `const nextReading = useNextReadingQuestion(planMode ? nextQueue : null, planDone, feedback?.practiceItemId ?? null)` — const, line 1605
- `const readingLabel = !planDone ? null : nextReading.known ? nextReading.item : "unknown"` — const, line 1606
- `const nothingNext = planDone && readingLabel === null` — const, line 1610
- `const planRead = useDailyPlan(nothingNext && nextPlan ? nextPlan.sessionId : null, nothingNext)` — const, line 1611
- `const books = useCachedQuery<SourceLibrarySnapshot>(nothingNext ? ["get_source_library"] : null, ()` — const, line 1612
- `const keptNote = nothingNext ? keptForCheckLine(planRead.data?.nextPractice, readingItemIds(books.data?.sources)) : null` — const, line 1613
- `const advanceGeneration = useRef(0)` — const, line 1615
- `const advancingRef = useRef(false)` — const, line 1616
- `const pendingQueueWrites = useRef(new Set<Promise<void>>())` — const, line 1622
- `const trackQueueWrite = useCallback(<T,>(write: Promise<T>): Promise<T>` — const, line 1623
- `const settledWrite: Promise<void> = write.then(()` — const, line 1624
- `const resolveNext = nextItem.resolve` — const, line 1629
- `const resolvePlanStep = nextPlanStep.resolve` — const, line 1630
- `const openNextReading = nextReading.open` — const, line 1631
- `const followup = followupRead && followupRead.workflowId === feedback?.followup?.workflowId ? followupRead : feedback?.followup ?? null` — const, line 1641
- `const followupRef = useRef<FollowupDto | null>(null)` — const, line 1645
- `const followupHeldRef = useRef(false)` — const, line 1646
- `const goOn = useCallback(async ()` — const, line 1649
- `const generation = ++advanceGeneration.current` — const, line 1653
- `let step: PlanStepDto | null = null` — let, line 1655
- `const picked = await openNextReading(nextPlan.sessionId).catch(()` — const, line 1662
- `const generation = ++advanceGeneration.current` — const, line 1680
- `let head: ScheduledItemDto | null = null` — let, line 1682
- `const actOnNext = useCallback((next: FollowupNextDto | null)` — const, line 1697
- `const actOnNextRef = useRef(actOnNext)` — const, line 1709
- `const advance = useCallback(async ()` — const, line 1711
- `const owner = followupRef.current` — const, line 1712
- `let next: FollowupNextDto | null = null` — let, line 1714
- `const somethingElseChosen = useCallback((result: SomethingElseChosenDto)` — const, line 1727
- `const entry = lessonEntryFor(result)` — const, line 1728
- `const followupOpen = followup !== null && (followup.state === "pending" || followup.held)` — const, line 1739
- `let stopped = false` — let, line 1742
- `const timer = window.setInterval(()` — const, line 1743
- `const asked = nextWaiting ? api.followupNext(attemptId).then((next)` — const, line 1746
- `const wasHeld = useRef(false)` — const, line 1766
- `const continueWithout = useCallback(async ()` — const, line 1774
- `const status = await api.followupStatus(attemptId).catch(()` — const, line 1777
- `const showAnyway = useCallback(async ()` — const, line 1784
- `const status = await api.followupStatus(attemptId).catch(()` — const, line 1786
- `const goBack = useCallback(()` — const, line 1792
- `const refreshAfterDiagnosis = useCallback(()` — const, line 1801
- `const diagnosis = useDiagnosisCard(attemptId, simple ? feedback?.diagnosisStatus : null, refreshAfterDiagnosis, onError)` — const, line 1810
- `const contestKey = useRef<` — const, line 1822
- `const marksKept = useRef<` — const, line 1828
- `const marksRead = marksKept.current?.attemptId === attemptId ? marksKept.current.marks : null` — const, line 1830
- `const tapReplaced = marksRead !== null && marksRead.attemptId === feedback?.attemptId && marksRead.replacesCardTap` — const, line 1831
- `const listsOn = marksRead !== null && feedback?.attemptId === attemptId` — const, line 1832
- `const causalHypotheses = feedback?.causalFeedback?.causalHypotheses ?? []` — const, line 1833
- `const errorInputRef = useRef<HTMLInputElement>(null)` — const, line 1878
- `const noteTitleRef = useRef<HTMLInputElement>(null)` — const, line 1887
- `const noteBodyRef = useRef<HTMLTextAreaElement>(null)` — const, line 1888
- `const suggestions = useMemo<CandidateErrorTypeDto[]>(()` — const, line 1890
- `const all = item?.candidateErrorTypes ?? []` — const, line 1891
- `const q = errorTypeInput.trim().toLowerCase()` — const, line 1892
- `const filtered = q ? all.filter((e)` — const, line 1893
- `let cancelled = false` — let, line 1900
- `let cancelled = false` — let, line 1936
- `const handleAnswerClarification = async ()` — const, line 1955
- `const answer = clarificationAnswer.trim()` — const, line 1956
- `const result = await trackQueueWrite(api.answerGradingClarification(feedback.attemptId, answer))` — const, line 1960
- `const handleSkipClarification = ()` — const, line 1980
- `const applyRepairStatus = useCallback( (next: CausalRepairStatusDto)` — const, line 1992
- `const repairCaseId = useMemo(()` — const, line 2004
- `const causal = feedback?.causalFeedback` — const, line 2005
- `const need = causal?.probeNeed` — const, line 2006
- `const repairAttemptId = feedback?.attemptId ?? null` — const, line 2022
- `let cancelled = false` — let, line 2027
- `const rereadRepairStatus = useCallback(()` — const, line 2047
- `const inspectIds = feedback ? uniqueIds([ feedback.attemptId, feedback.practiceItemId, feedback.learningObjectId, ...feedback.errorAttributions.map((event)` — const, line 2075
- `const practiceItemIds = feedback ? uniqueIds([feedback.practiceItemId]) : []` — const, line 2084
- `const shownAttempt = useRef(attemptId)` — const, line 2104
- `const refreshItemAfterRegrade = useCallback((bundle: FeedbackBundle)` — const, line 2106
- `const handleRegrade = async ()` — const, line 2115
- `const before = gradeSide(feedback)` — const, line 2118
- `const updated = await trackQueueWrite(api.triggerRegrade(feedback.attemptId))` — const, line 2120
- `const handleContest = async ()` — const, line 2139
- `const before = verdictOf(` — const, line 2143
- `const prior = gradeSide(feedback)` — const, line 2146
- `const reason = contestReason.trim()` — const, line 2147
- `const bound = contestKey.current` — const, line 2148
- `const key = bound && bound.reason === reason ? bound.key : newClientKey("contest")` — const, line 2149
- `const updated = await trackQueueWrite(api.triggerRegrade(feedback.attemptId, reason, key))` — const, line 2152
- `const outcome = updated.contest` — const, line 2156
- `const reviewed = outcome?.reviewRequested ? " It's marked for review." : ""` — const, line 2157
- `const after = verdictOf(` — const, line 2162
- `const contestCausal = (reason: UnresolvedCauseSelfReportResponse, factorId: string | null | undefined)` — const, line 2183
- `const handleTriggerFollowup = async ()` — const, line 2206
- `const updated = await trackQueueWrite(api.triggerFollowup(feedback.attemptId))` — const, line 2210
- `const handlePrimedRetry = async ()` — const, line 2223
- `const result = await api.startPrimedRetry(feedback.attemptId)` — const, line 2227
- `const handleGuidedRedo = async ()` — const, line 2245
- `const redo = await api.startGuidedRedo(feedback.attemptId)` — const, line 2249
- `const handleRateFollowup = async (useful: boolean)` — const, line 2261
- `const updated = await api.rateFollowup(feedback.attemptId, useful)` — const, line 2265
- `const handleElicitingResponse = async (suggestionIndex: number, responseMd: string)` — const, line 2280
- `const result = await trackQueueWrite(api.submitElicitingResponse(` — const, line 2284
- `const doAddError = async (errorType: string, severity?: number)` — const, line 2301
- `const updated = await api.addErrorEvent(feedback.attemptId, errorType.trim(), severity)` — const, line 2309
- `const handleAddError = ()` — const, line 2320
- `const sel = selectedSuggestionIdx >= 0 ? suggestions[selectedSuggestionIdx] : null` — const, line 2321
- `const handleUnresolvedCauseReport = async ( factorId: string, response: UnresolvedCauseSelfReportResponse, candidateIndex?: number | null, )` — const, line 2325
- `const resetNote = ()` — const, line 2342
- `const openNoteCapture = ()` — const, line 2349
- `const doSaveNote = async ()` — const, line 2355
- `const title = noteTitle.trim()` — const, line 2357
- `const body = noteBody.trim()` — const, line 2358
- `const subjectId = item?.subject ?? item?.subjects?.[0] ?? null` — const, line 2363
- `const stamp = new Date().toISOString().replace(/[-:T.]/g, "").slice(0, 14)` — const, line 2371
- `const noteId = `$` — const, line 2372
- `const result = await api.addNote(` — const, line 2375
- `const onKey = (event: KeyboardEvent)` — const, line 2394
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 2398
- `const right = verdictOf(` — const, line 2414
- `function simpleScreen( f: FeedbackBundle, matchedMisconception: FeedbackBundle["matchedMisconception"] | null, elicitingIndex: number, elicitingSuggestion: FeedbackBundle["repairSuggestions"][number] | null, errorPanel: ReactNode, notePanel: ReactNode, )` — function, line 2439
- `const held = f.heldForReview === true` — const, line 2447
- `const verdict = verdictOf(` — const, line 2448
- `const contestAvailable = f.gradingSource !== "self" && verdict !== "right"` — const, line 2450
- `const fixId = matchedMisconception?.id ?? (!repairStatus ? f.causalFeedback?.commonRepair?.misconceptionId ?? null : null)` — const, line 2454
- `let step: FeedbackNextStep | null = null` — let, line 2457
- `let stepIsRetry = false` — let, line 2458
- `const probeIsNext = followup !== null && (followup.state === "pending" || followup.state === "ready")` — const, line 2460
- `const card = diagnosis.status === "done" ? diagnosis.card : null` — const, line 2474
- `const causal = f.causalFeedback ?? null` — const, line 2475
- `const canSayNotRight = !tapReplaced && Boolean(card?.diagnosisId && card.responses.some((option)` — const, line 2477
- `const causalNotRightOk = Boolean(causal?.contestAction?.available && causal.contestAction.reasons.includes("diagnosis_wrong"))` — const, line 2478
- `const why =` — const, line 2479
- `const nextLabel = nextWaiting ? "preparing a question…" : origin === "reader" ? "back to the book" : planMode ? nextPlanKeyLabel(advancing, nextPlanStep.step, readingLabel) : autoAdvance ? nextKeyLabel(autoAdvance, advancing, nextItem.head, nextItem.empty) :…` — const, line 2505
- `const regradeHistory: RegradeReceipt | null = regradeReceipt ?? (f.regrade ?` — const, line 2515
- `const criteria = answeredCriterionRows(f)` — const, line 2527
- `const showTier = f.criterionEvidence.some((row)` — const, line 2528
- `const f = feedback` — const, line 2889
- `const subject = item?.subject ?? item?.subjects?.[0] ?? null` — const, line 2890
- `const tau = f.surprise.followupThresholdNats ?? algoConfig().tauFollowupNats` — const, line 2892
- `const interventionNeed = f.interventionNeed` — const, line 2893
- `const elicitingIndex = f.repairSuggestions.findIndex((s)` — const, line 2897
- `const elicitingSuggestion = elicitingIndex >= 0 ? f.repairSuggestions[elicitingIndex] : null` — const, line 2898
- `const matchedMisconception = f.matchedMisconception && f.matchedMisconception.correctionStatement?.trim() ? f.matchedMisconception : null` — const, line 2902
- `const errorPanel = addingError ? ( <div style=` — const, line 2909
- `const s = suggestions[selectedSuggestionIdx]` — const, line 2956
- `const notePanel = addingNote ? ( <div style=` — const, line 2984
- `const receipt: RegradeReceipt | null = regradeReceipt ?? (f.regrade ?` — const, line 3404
- `function nextKeyLabel( autoAdvance: boolean, advancing: boolean, head: ScheduledItemDto | null, empty: boolean ): string` — function, line 3647
- `const title = head.learningObjectTitle` — const, line 3656
- `function uniqueIds(values: Array<string | null | undefined>): string[]` — function, line 3663

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `FeedbackScreen`; references `FeedbackScreen`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AnswerGradingClarificationResultDto`, `AttemptTraceDto`, `AttemptTraceEvidenceDto`, `CandidateErrorTypeDto`, `CausalRepairStatusDto`, `ClaimCandidateDto`, `ColdCheckResultDto`, `CriterionEvidenceRowDto`, `ElicitingResponseResultDto`, `ErrorEventDto`, `FeedbackBundle`, `FollowupDto`, `FollowupGateDiagnosticsDto`, `FollowupGateSignalDto`, `FollowupNextDto`, `GradingClarificationDto`, `HypothesisMarksDto`, `IntentRestorationDto`, `MasteryDto`, `MasteryStepDto`, `MatchedMisconceptionDto`, `NOT_ASSESSED_LABEL`, `PlanStepDto`, `PracticeItemDetail`, `QueueInput`, `RepairSuggestionDto`, `ResolvedSourceRefDto`, `ScheduledItemDto`, `SomethingElseChosenDto`, `SourceLibrarySnapshot`, `UNVERIFIED_ROUTE_REVIEW_REASON`, `UnresolvedCauseSelfReportResponse`, `criterionAssessed`
- [[Reference/Desktop/TypeScript/api/queryTags|src/api/queryTags.ts]] — import-or-re-export; imports `TAG`
- [[Reference/Desktop/TypeScript/api/useCachedQuery|src/api/useCachedQuery.ts]] — import-or-re-export; imports `useCachedQuery`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `algoConfig`, `masteryTone`
- [[Reference/Desktop/TypeScript/app/autoAdvance|src/app/autoAdvance.ts]] — import-or-re-export; imports `useNextQueueItem`, `useNextReadingQuestion`
- [[Reference/Desktop/TypeScript/app/dailyPlan|src/app/dailyPlan.ts]] — import-or-re-export; imports `nextPlanKeyLabel`, `useDailyPlan`, `useNextPlanStep`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/app/nextPractice|src/app/nextPractice.ts]] — import-or-re-export; imports `keptForCheckLine`
- [[Reference/Desktop/TypeScript/app/practiceFeedback|src/app/practiceFeedback.ts]] — import-or-re-export; imports `FIX_MIX_UP_LABEL`, `FeedbackOrigin`, `UNASSESSED_ROUTE_LINE`, `VERDICT_TEXT`, `simplePracticeFeedback`, `unestablishedRepairCopy`, `verdictOf`
- [[Reference/Desktop/TypeScript/app/todayCause|src/app/todayCause.ts]] — import-or-re-export; imports `readingItemIds`
- [[Reference/Desktop/TypeScript/components/AsPrinted|src/components/AsPrinted.tsx]] — import-or-re-export; imports `PrintedAfterFeedback`, `printedPageInReader`
- [[Reference/Desktop/TypeScript/components/CardControls|src/components/CardControls.tsx]] — import-or-re-export; imports `CardControls`, `ProbeRemintAction`
- [[Reference/Desktop/TypeScript/components/CausalAttribution|src/components/CausalAttribution.tsx]] — import-or-re-export; imports `CausalFeedbackPanel`, `formatCausalTarget`, `formatDivergenceAnchor`, `useCausalRepairActions`, `useRouterDecisionPoll`
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
