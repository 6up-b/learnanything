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
| Source lines | 3646 |
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

- `export function FeedbackScreen(` — function, line 1485

## Internal implementation anchors

- `type FeedbackOrigin, simplePracticeFeedback, UNASSESSED_ROUTE_LINE, unestablishedRepairCopy, VERDICT_TEXT, verdictOf } from "../app/practiceFeedback"` — type, line 63
- `type FeedbackNextStep, type RedoContext } from "./feedback/FeedbackSurface"` — type, line 77
- `type RedoContext } from "./feedback/FeedbackSurface"` — type, line 78
- `const C =` — const, line 89
- `const WHY_CAUSES_SHOWN = 3` — const, line 107
- `const MONO = '"JetBrains Mono", "Fira Code", ui-monospace, SFMono-Regular, Menlo, monospace'` — const, line 108
- `function Faint(` — function, line 111
- `function Dim(` — function, line 114
- `function Meta(` — function, line 117
- `function FbHeader(` — function, line 122
- `function EvidenceHeader(` — function, line 141
- `function BlockBar(` — function, line 158
- `const filled = Math.max(0, Math.min(width, Math.round((value / max) * width)))` — const, line 161
- `function fmtDue(iso: string | null): string` — function, line 171
- `const d = new Date(iso)` — const, line 174
- `const now = new Date()` — const, line 175
- `const diffH = (d.getTime() - now.getTime()) / 3_600_000` — const, line 176
- `const tomorrow = new Date(now)` — const, line 177
- `function fmtDay(iso: string | null | undefined): string` — function, line 197
- `function ColdCheckBanner(` — function, line 210
- `const confirmed = result.claim === "repair_confirmed"` — const, line 211
- `const failed = result.claim === "escalated_unrepaired"` — const, line 212
- `const tone = confirmed ? C.green : failed ? C.amber : C.textDim` — const, line 213
- `const heading = confirmed ? "unassisted check · passed" : failed ? "unassisted check · did not hold" : result.claim === "repair_effect_unestablished" ? "unassisted check" : "unassisted check · no verdict"` — const, line 214
- `const when = fmtDay(result.instructedAt)` — const, line 221
- `const body = confirmed ? `This was the unassisted check for the repair you did on $` — const, line 222
- `function AutoPrimedNote(` — function, line 257
- `function ElicitingRepairCard(` — function, line 288
- `const anchor = suggestion.targetRefs?.[0] ?? null` — const, line 300
- `const answered = outcome != null` — const, line 301
- `function ratingPill(r: string): string` — function, line 391
- `function modePillTone(mode: string): string` — function, line 398
- `function ScoreBlock(` — function, line 403
- `const tone = score === max ? C.green : score >= max * 0.75 ? C.greenSoft : score >= max * 0.5 ? C.amber : C.red` — const, line 405
- `const label = score === max ? "perfect" : score >= max * 0.75 ? "good" : score >= max * 0.5 ? "partial credit" : "needs work"` — const, line 409
- `function CriterionRow(` — function, line 451
- `const assessed = criterionAssessed(row)` — const, line 465
- `const ok = maxKnown && row.pointsAwarded === row.pointsPossible` — const, line 466
- `const partial = maxKnown && row.pointsAwarded > 0 && row.pointsAwarded < row.pointsPossible` — const, line 467
- `const mark = !assessed ? "–" : !maxKnown ? "·" : ok ? "✓" : partial ? "◐" : "✗"` — const, line 468
- `const tone = !assessed || !maxKnown ? C.textDim : ok ? C.green : partial ? C.amber : C.red` — const, line 469
- `function ErrorAttribution(` — function, line 507
- `const plan = ea.repairPlan` — const, line 508
- `const resolutionStatus = typeof plan?.resolutionStatus === "string" ? plan.resolutionStatus : null` — const, line 509
- `const causeScope = typeof plan?.causeScope === "string" ? plan.causeScope : null` — const, line 511
- `const operation = typeof plan?.operation === "string" ? plan.operation : null` — const, line 512
- `const abstentionReason = typeof plan?.abstentionReason === "string" ? plan.abstentionReason : null` — const, line 513
- `const targetRef = plan?.targetRef && typeof plan.targetRef === "object" && !Array.isArray(plan.targetRef) ? plan.targetRef as Parameters<typeof formatCausalTarget>[0] : null` — const, line 515
- `const firstDivergence = plan?.firstDivergence && typeof plan.firstDivergence === "object" && !Array.isArray(plan.firstDivergence) ? plan.firstDivergence as Parameters<typeof formatDivergenceAnchor>[0] : null` — const, line 519
- `const SQRT_2PI = Math.sqrt(2 * Math.PI)` — const, line 585
- `const PROB_TICKS = [0.1, 0.25, 0.5, 0.75, 0.9]` — const, line 586
- `function logit(p: number): number` — function, line 588
- `const c = Math.min(1 - 1e-4, Math.max(1e-4, p))` — const, line 589
- `function toLogitSpace(mean: number, variance: number):` — function, line 595
- `const m = Math.min(1 - 1e-4, Math.max(1e-4, mean))` — const, line 596
- `const slope = m * (1 - m)` — const, line 597
- `const logitVar = Math.max(1e-4, variance / (slope * slope))` — const, line 598
- `function gaussianPdf(x: number, mu: number, sd: number): number` — function, line 602
- `const z = (x - mu) / sd` — const, line 603
- `function BeliefShiftChart(` — function, line 612
- `const prior = toLogitSpace(before.mean, before.variance)` — const, line 627
- `const post = toLogitSpace(after.mean, after.variance)` — const, line 628
- `const padL = 8` — const, line 630
- `const padR = 8` — const, line 631
- `const padT = 20` — const, line 632
- `const padB = 20` — const, line 633
- `const plotW = width - padL - padR` — const, line 634
- `const plotH = height - padT - padB` — const, line 635
- `const lo = Math.min(prior.mu - 3.4 * prior.sd, post.mu - 3.4 * post.sd, logit(0.15))` — const, line 639
- `const hi = Math.max(prior.mu + 3.4 * prior.sd, post.mu + 3.4 * post.sd, logit(0.85))` — const, line 640
- `const span = Math.max(1e-3, hi - lo)` — const, line 641
- `const xOf = (t: number)` — const, line 642
- `const peak = Math.max(gaussianPdf(prior.mu, prior.mu, prior.sd), gaussianPdf(post.mu, post.mu, post.sd))` — const, line 645
- `const yMax = peak * 1.12` — const, line 646
- `const baseY = padT + plotH` — const, line 647
- `const yOf = (d: number)` — const, line 648
- `const N = 72` — const, line 650
- `const curvePath = (mu: number, sd: number, close: boolean): string` — const, line 651
- `let d = ""` — let, line 652
- `const x = lo + (span * i) / N` — const, line 654
- `const y = gaussianPdf(x, mu, sd)` — const, line 655
- `const postColor = masteryTone(after.mean, C)` — const, line 662
- `const shift = post.mu - prior.mu` — const, line 663
- `const showArrow = bayesianSurprise > tau && Math.abs(shift) > 1e-3` — const, line 664
- `const arrowColor = shift >= 0 ? C.green : C.red` — const, line 665
- `const arrowY = 11` — const, line 666
- `const xPrior = xOf(prior.mu)` — const, line 667
- `const xPost = xOf(post.mu)` — const, line 668
- `const yPrior = yOf(gaussianPdf(prior.mu, prior.mu, prior.sd))` — const, line 669
- `const yPost = yOf(gaussianPdf(post.mu, post.mu, post.sd))` — const, line 670
- `const t = logit(p)` — const, line 676
- `const x = xOf(t)` — const, line 678
- `const mid = p === 0.5` — const, line 679
- `function MasteryStepBreakdown(` — function, line 734
- `const pct = (v: number)` — const, line 736
- `const dominant = factor.key === step.dominantFactorKey` — const, line 752
- `const removed = 1 - factor.multiplier` — const, line 755
- `const color = dominant ? C.amber : removed < 0 ? C.greenSoft : C.textDim` — const, line 756
- `function MasteryDelta(` — function, line 806
- `const tau = surprise.followupThresholdNats ?? algoConfig().tauFollowupNats` — const, line 812
- `const bayes = surprise.bayesianSurprise ?? 0` — const, line 813
- `const hasSurprise = bayes > tau` — const, line 814
- `const postColor = masteryTone(after.mean, C)` — const, line 815
- `const evidence = f.criterionEvidence ?? []` — const, line 816
- `const assessed = criterionAssessed(row)` — const, line 864
- `const ok = row.pointsAwarded === row.pointsPossible` — const, line 865
- `const partial = row.pointsAwarded > 0 && row.pointsAwarded < row.pointsPossible` — const, line 866
- `const mark = !assessed ? "–" : ok ? "✓" : partial ? "◐" : "✗"` — const, line 867
- `const tone = !assessed ? C.textDim : ok ? C.green : partial ? C.amber : C.red` — const, line 868
- `function followupStatus(f: FeedbackBundle, tau: number): string` — function, line 897
- `const gate = f.surprise.gateDiagnostics` — const, line 901
- `const reasons = interventionReasons(f.surprise.triggeredActions ?? [])` — const, line 904
- `const suppressed = f.surprise.suppressedActions ?? []` — const, line 913
- `const GATE_SIGNAL_LABELS: Record<string, string> =` — const, line 922
- `const GATE_COMPARATORS: Record<string, string> =` — const, line 934
- `function gateNum(value: number | boolean | null): string | null` — function, line 938
- `function describeSignal(sig: FollowupGateSignalDto): string` — function, line 944
- `const name = sig.name ?? ""` — const, line 945
- `const label = GATE_SIGNAL_LABELS[name] ?? name.replace(/_/g, " ")` — const, line 951
- `const value = gateNum(sig.value)` — const, line 952
- `const cmp = sig.comparator ? GATE_COMPARATORS[sig.comparator] ?? sig.comparator : ""` — const, line 953
- `let threshold = gateNum(sig.threshold)` — let, line 954
- `const unit = sig.unit === "nats" ? " nats" : ""` — const, line 963
- `function describeGate(gate: FollowupGateDiagnosticsDto): string` — function, line 971
- `const sig = gate.decisiveSignal` — const, line 972
- `const signalText = sig ? describeSignal(sig) : gate.decisiveReason.replace(/_/g, " ")` — const, line 973
- `const scoreSuffix = typeof gate.gateScore === "number" && sig?.name !== "gate_score" ? ` · score $` — const, line 976
- `const base = (()` — const, line 981
- `const trigger = gate.triggeredReasons.find((r)` — const, line 991
- `const trigText = trigger ? trigger.replace(/_/g, " ") : "trigger"` — const, line 992
- `const v = gateNum(sig.value)` — const, line 1002
- `function interventionReasons(actions: string[]): string[]` — function, line 1011
- `const reasons = actions .map((action)` — const, line 1012
- `function formatInterventionAction(action: string): string` — function, line 1023
- `function fmtTimestamp(seconds: number): string` — function, line 1035
- `const total = Math.max(0, Math.floor(seconds))` — const, line 1036
- `const h = Math.floor(total / 3600)` — const, line 1037
- `const m = Math.floor((total % 3600) / 60)` — const, line 1038
- `const s = total % 60` — const, line 1039
- `const mm = h > 0 ? String(m).padStart(2, "0") : String(m)` — const, line 1040
- `function timeRangeLabel(video:` — function, line 1044
- `function SourceRefCard(` — function, line 1050
- `const video = sourceRef.video` — const, line 1059
- `const openExternal = async (url: string)` — const, line 1061
- `const externalVideoUrl = video ? `https://www.youtube.com/watch?v=$` — const, line 1070
- `const openInReader = !externalVideoUrl && sourceId && onOpenPassage ? ()` — const, line 1075
- `const embedUrl = video ? `https://www.youtube-nocookie.com/embed/$` — const, line 1080
- `function SourceReviewPanel(` — function, line 1155
- `const refs = (f.sourceRefs ?? []).filter((ref)` — const, line 1164
- `const missed = f.rubricScore < f.maxPoints` — const, line 1167
- `function statementPairCopy(m: MatchedMisconceptionDto): string` — function, line 1227
- `const correction = m.correctionStatement.trim()` — const, line 1228
- `const x = m.targetFacet?.trim()` — const, line 1229
- `const y = m.confusedWithFacet?.trim()` — const, line 1230
- `const head = x && y ? `Your last answer was consistent with confusing $` — const, line 1231
- `function MisconceptionStatementCard(` — function, line 1238
- `const claim: ClaimCandidateDto = useMemo( ()` — const, line 1253
- `type RegradeSide =` — type, line 1300
- `type RegradeReceipt =` — type, line 1301
- `function gradeSide(f: FeedbackBundle): RegradeSide` — function, line 1303
- `function newClientKey(prefix: "contest"): string` — function, line 1312
- `const random = globalThis.crypto?.randomUUID?.()` — const, line 1313
- `function regradeHistoryLine(` — function, line 1319
- `const words = (side: RegradeSide)` — const, line 1321
- `const side = (s: RegradeSide)` — const, line 1328
- `function RegradeLedgerCard(` — function, line 1332
- `const claim: ClaimCandidateDto = useMemo( ()` — const, line 1346
- `const PROVISIONAL_PENDING_CLARIFICATION = "provisional_pending_clarification"` — const, line 1376
- `const CLARIFICATION_REASON_COPY: Record<string, string> =` — const, line 1380
- `function clarificationOutcomeCopy(result: AnswerGradingClarificationResultDto): string` — function, line 1388
- `function ClarificationCard(` — function, line 1400
- `const simple = simplePracticeFeedback()` — const, line 1568
- `const visitId = useRef(mintVisitId()).current` — const, line 1591
- `const planMode = Boolean(nextPlan && onPlanStep)` — const, line 1596
- `const autoAdvance = Boolean(nextQueue && onOpenNext) && !planMode` — const, line 1597
- `const nextItem = useNextQueueItem(autoAdvance ? nextQueue : null, feedback !== null)` — const, line 1598
- `const nextPlanStep = useNextPlanStep(planMode && nextPlan ? nextPlan.sessionId : null, feedback !== null)` — const, line 1599
- `const planDone = planMode && nextPlanStep.step?.kind === "done"` — const, line 1602
- `const nextReading = useNextReadingQuestion(planMode ? nextQueue : null, planDone, feedback?.practiceItemId ?? null)` — const, line 1603
- `const readingLabel = !planDone ? null : nextReading.known ? nextReading.item : "unknown"` — const, line 1604
- `const nothingNext = planDone && readingLabel === null` — const, line 1608
- `const planRead = useDailyPlan(nothingNext && nextPlan ? nextPlan.sessionId : null, nothingNext)` — const, line 1609
- `const books = useCachedQuery<SourceLibrarySnapshot>(nothingNext ? ["get_source_library"] : null, ()` — const, line 1610
- `const keptNote = nothingNext ? keptForCheckLine(planRead.data?.nextPractice, readingItemIds(books.data?.sources)) : null` — const, line 1611
- `const advanceGeneration = useRef(0)` — const, line 1613
- `const advancingRef = useRef(false)` — const, line 1614
- `const pendingQueueWrites = useRef(new Set<Promise<void>>())` — const, line 1620
- `const trackQueueWrite = useCallback(<T,>(write: Promise<T>): Promise<T>` — const, line 1621
- `const settledWrite: Promise<void> = write.then(()` — const, line 1622
- `const resolveNext = nextItem.resolve` — const, line 1627
- `const resolvePlanStep = nextPlanStep.resolve` — const, line 1628
- `const openNextReading = nextReading.open` — const, line 1629
- `const followup = followupRead && followupRead.workflowId === feedback?.followup?.workflowId ? followupRead : feedback?.followup ?? null` — const, line 1639
- `const followupRef = useRef<FollowupDto | null>(null)` — const, line 1643
- `const followupHeldRef = useRef(false)` — const, line 1644
- `const goOn = useCallback(async ()` — const, line 1647
- `const generation = ++advanceGeneration.current` — const, line 1651
- `let step: PlanStepDto | null = null` — let, line 1653
- `const picked = await openNextReading(nextPlan.sessionId).catch(()` — const, line 1660
- `const generation = ++advanceGeneration.current` — const, line 1678
- `let head: ScheduledItemDto | null = null` — let, line 1680
- `const actOnNext = useCallback((next: FollowupNextDto | null)` — const, line 1695
- `const actOnNextRef = useRef(actOnNext)` — const, line 1707
- `const advance = useCallback(async ()` — const, line 1709
- `const owner = followupRef.current` — const, line 1710
- `let next: FollowupNextDto | null = null` — let, line 1712
- `const somethingElseChosen = useCallback((result: SomethingElseChosenDto)` — const, line 1725
- `const entry = lessonEntryFor(result)` — const, line 1726
- `const followupOpen = followup !== null && (followup.state === "pending" || followup.held)` — const, line 1737
- `let stopped = false` — let, line 1740
- `const timer = window.setInterval(()` — const, line 1741
- `const asked = nextWaiting ? api.followupNext(attemptId).then((next)` — const, line 1744
- `const wasHeld = useRef(false)` — const, line 1764
- `const continueWithout = useCallback(async ()` — const, line 1772
- `const status = await api.followupStatus(attemptId).catch(()` — const, line 1775
- `const showAnyway = useCallback(async ()` — const, line 1782
- `const status = await api.followupStatus(attemptId).catch(()` — const, line 1784
- `const goBack = useCallback(()` — const, line 1790
- `const refreshAfterDiagnosis = useCallback(()` — const, line 1799
- `const diagnosis = useDiagnosisCard(attemptId, simple ? feedback?.diagnosisStatus : null, refreshAfterDiagnosis, onError)` — const, line 1808
- `const contestKey = useRef<` — const, line 1820
- `const marksKept = useRef<` — const, line 1826
- `const marksRead = marksKept.current?.attemptId === attemptId ? marksKept.current.marks : null` — const, line 1828
- `const tapReplaced = marksRead !== null && marksRead.attemptId === feedback?.attemptId && marksRead.replacesCardTap` — const, line 1829
- `const listsOn = marksRead !== null && feedback?.attemptId === attemptId` — const, line 1830
- `const causalHypotheses = feedback?.causalFeedback?.causalHypotheses ?? []` — const, line 1831
- `const errorInputRef = useRef<HTMLInputElement>(null)` — const, line 1876
- `const noteTitleRef = useRef<HTMLInputElement>(null)` — const, line 1885
- `const noteBodyRef = useRef<HTMLTextAreaElement>(null)` — const, line 1886
- `const suggestions = useMemo<CandidateErrorTypeDto[]>(()` — const, line 1888
- `const all = item?.candidateErrorTypes ?? []` — const, line 1889
- `const q = errorTypeInput.trim().toLowerCase()` — const, line 1890
- `const filtered = q ? all.filter((e)` — const, line 1891
- `let cancelled = false` — let, line 1898
- `let cancelled = false` — let, line 1934
- `const handleAnswerClarification = async ()` — const, line 1953
- `const answer = clarificationAnswer.trim()` — const, line 1954
- `const result = await trackQueueWrite(api.answerGradingClarification(feedback.attemptId, answer))` — const, line 1958
- `const handleSkipClarification = ()` — const, line 1978
- `const applyRepairStatus = useCallback( (next: CausalRepairStatusDto)` — const, line 1990
- `const repairCaseId = useMemo(()` — const, line 2002
- `const causal = feedback?.causalFeedback` — const, line 2003
- `const need = causal?.probeNeed` — const, line 2004
- `let cancelled = false` — let, line 2021
- `const inspectIds = feedback ? uniqueIds([ feedback.attemptId, feedback.practiceItemId, feedback.learningObjectId, ...feedback.errorAttributions.map((event)` — const, line 2056
- `const practiceItemIds = feedback ? uniqueIds([feedback.practiceItemId]) : []` — const, line 2065
- `const shownAttempt = useRef(attemptId)` — const, line 2085
- `const refreshItemAfterRegrade = useCallback((bundle: FeedbackBundle)` — const, line 2087
- `const handleRegrade = async ()` — const, line 2096
- `const before = gradeSide(feedback)` — const, line 2099
- `const updated = await trackQueueWrite(api.triggerRegrade(feedback.attemptId))` — const, line 2101
- `const handleContest = async ()` — const, line 2120
- `const before = verdictOf(` — const, line 2124
- `const prior = gradeSide(feedback)` — const, line 2127
- `const reason = contestReason.trim()` — const, line 2128
- `const bound = contestKey.current` — const, line 2129
- `const key = bound && bound.reason === reason ? bound.key : newClientKey("contest")` — const, line 2130
- `const updated = await trackQueueWrite(api.triggerRegrade(feedback.attemptId, reason, key))` — const, line 2133
- `const outcome = updated.contest` — const, line 2137
- `const reviewed = outcome?.reviewRequested ? " It's marked for review." : ""` — const, line 2138
- `const after = verdictOf(` — const, line 2143
- `const contestCausal = (reason: UnresolvedCauseSelfReportResponse, factorId: string | null | undefined)` — const, line 2164
- `const handleTriggerFollowup = async ()` — const, line 2187
- `const updated = await trackQueueWrite(api.triggerFollowup(feedback.attemptId))` — const, line 2191
- `const handlePrimedRetry = async ()` — const, line 2204
- `const result = await api.startPrimedRetry(feedback.attemptId)` — const, line 2208
- `const handleGuidedRedo = async ()` — const, line 2226
- `const redo = await api.startGuidedRedo(feedback.attemptId)` — const, line 2230
- `const handleRateFollowup = async (useful: boolean)` — const, line 2242
- `const updated = await api.rateFollowup(feedback.attemptId, useful)` — const, line 2246
- `const handleElicitingResponse = async (suggestionIndex: number, responseMd: string)` — const, line 2261
- `const result = await trackQueueWrite(api.submitElicitingResponse(` — const, line 2265
- `const doAddError = async (errorType: string, severity?: number)` — const, line 2282
- `const updated = await api.addErrorEvent(feedback.attemptId, errorType.trim(), severity)` — const, line 2290
- `const handleAddError = ()` — const, line 2301
- `const sel = selectedSuggestionIdx >= 0 ? suggestions[selectedSuggestionIdx] : null` — const, line 2302
- `const handleUnresolvedCauseReport = async ( factorId: string, response: UnresolvedCauseSelfReportResponse, candidateIndex?: number | null, )` — const, line 2306
- `const resetNote = ()` — const, line 2323
- `const openNoteCapture = ()` — const, line 2330
- `const doSaveNote = async ()` — const, line 2336
- `const title = noteTitle.trim()` — const, line 2338
- `const body = noteBody.trim()` — const, line 2339
- `const subjectId = item?.subject ?? item?.subjects?.[0] ?? null` — const, line 2344
- `const stamp = new Date().toISOString().replace(/[-:T.]/g, "").slice(0, 14)` — const, line 2352
- `const noteId = `$` — const, line 2353
- `const result = await api.addNote(` — const, line 2356
- `const onKey = (event: KeyboardEvent)` — const, line 2375
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 2379
- `const right = verdictOf(` — const, line 2395
- `function simpleScreen( f: FeedbackBundle, matchedMisconception: FeedbackBundle["matchedMisconception"] | null, elicitingIndex: number, elicitingSuggestion: FeedbackBundle["repairSuggestions"][number] | null, errorPanel: ReactNode, notePanel: ReactNode, )` — function, line 2420
- `const held = f.heldForReview === true` — const, line 2428
- `const verdict = verdictOf(` — const, line 2429
- `const contestAvailable = f.gradingSource !== "self" && verdict !== "right"` — const, line 2431
- `const fixId = matchedMisconception?.id ?? (!repairStatus ? f.causalFeedback?.commonRepair?.misconceptionId ?? null : null)` — const, line 2435
- `let step: FeedbackNextStep | null = null` — let, line 2438
- `let stepIsRetry = false` — let, line 2439
- `const probeIsNext = followup !== null && (followup.state === "pending" || followup.state === "ready")` — const, line 2441
- `const card = diagnosis.status === "done" ? diagnosis.card : null` — const, line 2455
- `const causal = f.causalFeedback ?? null` — const, line 2456
- `const canSayNotRight = !tapReplaced && Boolean(card?.diagnosisId && card.responses.some((option)` — const, line 2458
- `const causalNotRightOk = Boolean(causal?.contestAction?.available && causal.contestAction.reasons.includes("diagnosis_wrong"))` — const, line 2459
- `const why =` — const, line 2460
- `const nextLabel = nextWaiting ? "preparing a question…" : origin === "reader" ? "back to the book" : planMode ? nextPlanKeyLabel(advancing, nextPlanStep.step, readingLabel) : autoAdvance ? nextKeyLabel(autoAdvance, advancing, nextItem.head, nextItem.empty) :…` — const, line 2486
- `const regradeHistory: RegradeReceipt | null = regradeReceipt ?? (f.regrade ?` — const, line 2496
- `const criteria = answeredCriterionRows(f)` — const, line 2508
- `const showTier = f.criterionEvidence.some((row)` — const, line 2509
- `const f = feedback` — const, line 2870
- `const subject = item?.subject ?? item?.subjects?.[0] ?? null` — const, line 2871
- `const tau = f.surprise.followupThresholdNats ?? algoConfig().tauFollowupNats` — const, line 2873
- `const interventionNeed = f.interventionNeed` — const, line 2874
- `const elicitingIndex = f.repairSuggestions.findIndex((s)` — const, line 2878
- `const elicitingSuggestion = elicitingIndex >= 0 ? f.repairSuggestions[elicitingIndex] : null` — const, line 2879
- `const matchedMisconception = f.matchedMisconception && f.matchedMisconception.correctionStatement?.trim() ? f.matchedMisconception : null` — const, line 2883
- `const errorPanel = addingError ? ( <div style=` — const, line 2890
- `const s = suggestions[selectedSuggestionIdx]` — const, line 2937
- `const notePanel = addingNote ? ( <div style=` — const, line 2965
- `const receipt: RegradeReceipt | null = regradeReceipt ?? (f.regrade ?` — const, line 3385
- `function nextKeyLabel( autoAdvance: boolean, advancing: boolean, head: ScheduledItemDto | null, empty: boolean ): string` — function, line 3628
- `const title = head.learningObjectTitle` — const, line 3637
- `function uniqueIds(values: Array<string | null | undefined>): string[]` — function, line 3644

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
