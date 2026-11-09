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
source_commit: "7772c7c7a641838f699c1d5cde165c17dcbde0e3"
source_commit_timestamp: "2026-11-09T00:34:52-05:00"
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
| Source lines | 3610 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `7772c7c7a641838f699c1d5cde165c17dcbde0e3` |
| Commit timestamp | `2026-11-09T00:34:52-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]]

## Public API

- `export function FeedbackScreen(` — function, line 1479

## Internal implementation anchors

- `type FeedbackOrigin, simplePracticeFeedback, VERDICT_TEXT, verdictOf } from "../app/practiceFeedback"` — type, line 56
- `type FeedbackNextStep } from "./feedback/FeedbackSurface"` — type, line 67
- `const C =` — const, line 78
- `const WHY_CAUSES_SHOWN = 3` — const, line 96
- `const MONO = '"JetBrains Mono", "Fira Code", ui-monospace, SFMono-Regular, Menlo, monospace'` — const, line 97
- `function Faint(` — function, line 100
- `function Dim(` — function, line 103
- `function Meta(` — function, line 106
- `function FbHeader(` — function, line 111
- `function EvidenceHeader(` — function, line 130
- `function BlockBar(` — function, line 147
- `const filled = Math.max(0, Math.min(width, Math.round((value / max) * width)))` — const, line 150
- `function fmtDue(iso: string | null): string` — function, line 160
- `const d = new Date(iso)` — const, line 163
- `const now = new Date()` — const, line 164
- `const diffH = (d.getTime() - now.getTime()) / 3_600_000` — const, line 165
- `const tomorrow = new Date(now)` — const, line 166
- `function fmtDay(iso: string | null | undefined): string` — function, line 186
- `function ColdCheckBanner(` — function, line 199
- `const confirmed = result.claim === "repair_confirmed"` — const, line 200
- `const failed = result.claim === "escalated_unrepaired"` — const, line 201
- `const tone = confirmed ? C.green : failed ? C.amber : C.textDim` — const, line 202
- `const heading = confirmed ? "unassisted check · passed" : failed ? "unassisted check · did not hold" : result.claim === "downgraded" ? "unassisted check · recorded, not counted" : "unassisted check · no verdict"` — const, line 203
- `const when = fmtDay(result.instructedAt)` — const, line 210
- `const body = confirmed ? `This was the unassisted check for the repair you did on $` — const, line 211
- `function AutoPrimedNote(` — function, line 251
- `function ElicitingRepairCard(` — function, line 282
- `const anchor = suggestion.targetRefs?.[0] ?? null` — const, line 294
- `const answered = outcome != null` — const, line 295
- `function ratingPill(r: string): string` — function, line 385
- `function modePillTone(mode: string): string` — function, line 392
- `function ScoreBlock(` — function, line 397
- `const tone = score === max ? C.green : score >= max * 0.75 ? C.greenSoft : score >= max * 0.5 ? C.amber : C.red` — const, line 399
- `const label = score === max ? "perfect" : score >= max * 0.75 ? "good" : score >= max * 0.5 ? "partial credit" : "needs work"` — const, line 403
- `function CriterionRow(` — function, line 445
- `const assessed = criterionAssessed(row)` — const, line 459
- `const ok = maxKnown && row.pointsAwarded === row.pointsPossible` — const, line 460
- `const partial = maxKnown && row.pointsAwarded > 0 && row.pointsAwarded < row.pointsPossible` — const, line 461
- `const mark = !assessed ? "–" : !maxKnown ? "·" : ok ? "✓" : partial ? "◐" : "✗"` — const, line 462
- `const tone = !assessed || !maxKnown ? C.textDim : ok ? C.green : partial ? C.amber : C.red` — const, line 463
- `function ErrorAttribution(` — function, line 501
- `const plan = ea.repairPlan` — const, line 502
- `const resolutionStatus = typeof plan?.resolutionStatus === "string" ? plan.resolutionStatus : null` — const, line 503
- `const causeScope = typeof plan?.causeScope === "string" ? plan.causeScope : null` — const, line 505
- `const operation = typeof plan?.operation === "string" ? plan.operation : null` — const, line 506
- `const abstentionReason = typeof plan?.abstentionReason === "string" ? plan.abstentionReason : null` — const, line 507
- `const targetRef = plan?.targetRef && typeof plan.targetRef === "object" && !Array.isArray(plan.targetRef) ? plan.targetRef as Parameters<typeof formatCausalTarget>[0] : null` — const, line 509
- `const firstDivergence = plan?.firstDivergence && typeof plan.firstDivergence === "object" && !Array.isArray(plan.firstDivergence) ? plan.firstDivergence as Parameters<typeof formatDivergenceAnchor>[0] : null` — const, line 513
- `const SQRT_2PI = Math.sqrt(2 * Math.PI)` — const, line 579
- `const PROB_TICKS = [0.1, 0.25, 0.5, 0.75, 0.9]` — const, line 580
- `function logit(p: number): number` — function, line 582
- `const c = Math.min(1 - 1e-4, Math.max(1e-4, p))` — const, line 583
- `function toLogitSpace(mean: number, variance: number):` — function, line 589
- `const m = Math.min(1 - 1e-4, Math.max(1e-4, mean))` — const, line 590
- `const slope = m * (1 - m)` — const, line 591
- `const logitVar = Math.max(1e-4, variance / (slope * slope))` — const, line 592
- `function gaussianPdf(x: number, mu: number, sd: number): number` — function, line 596
- `const z = (x - mu) / sd` — const, line 597
- `function BeliefShiftChart(` — function, line 606
- `const prior = toLogitSpace(before.mean, before.variance)` — const, line 621
- `const post = toLogitSpace(after.mean, after.variance)` — const, line 622
- `const padL = 8` — const, line 624
- `const padR = 8` — const, line 625
- `const padT = 20` — const, line 626
- `const padB = 20` — const, line 627
- `const plotW = width - padL - padR` — const, line 628
- `const plotH = height - padT - padB` — const, line 629
- `const lo = Math.min(prior.mu - 3.4 * prior.sd, post.mu - 3.4 * post.sd, logit(0.15))` — const, line 633
- `const hi = Math.max(prior.mu + 3.4 * prior.sd, post.mu + 3.4 * post.sd, logit(0.85))` — const, line 634
- `const span = Math.max(1e-3, hi - lo)` — const, line 635
- `const xOf = (t: number)` — const, line 636
- `const peak = Math.max(gaussianPdf(prior.mu, prior.mu, prior.sd), gaussianPdf(post.mu, post.mu, post.sd))` — const, line 639
- `const yMax = peak * 1.12` — const, line 640
- `const baseY = padT + plotH` — const, line 641
- `const yOf = (d: number)` — const, line 642
- `const N = 72` — const, line 644
- `const curvePath = (mu: number, sd: number, close: boolean): string` — const, line 645
- `let d = ""` — let, line 646
- `const x = lo + (span * i) / N` — const, line 648
- `const y = gaussianPdf(x, mu, sd)` — const, line 649
- `const postColor = masteryTone(after.mean, C)` — const, line 656
- `const shift = post.mu - prior.mu` — const, line 657
- `const showArrow = bayesianSurprise > tau && Math.abs(shift) > 1e-3` — const, line 658
- `const arrowColor = shift >= 0 ? C.green : C.red` — const, line 659
- `const arrowY = 11` — const, line 660
- `const xPrior = xOf(prior.mu)` — const, line 661
- `const xPost = xOf(post.mu)` — const, line 662
- `const yPrior = yOf(gaussianPdf(prior.mu, prior.mu, prior.sd))` — const, line 663
- `const yPost = yOf(gaussianPdf(post.mu, post.mu, post.sd))` — const, line 664
- `const t = logit(p)` — const, line 670
- `const x = xOf(t)` — const, line 672
- `const mid = p === 0.5` — const, line 673
- `function MasteryStepBreakdown(` — function, line 728
- `const pct = (v: number)` — const, line 730
- `const dominant = factor.key === step.dominantFactorKey` — const, line 746
- `const removed = 1 - factor.multiplier` — const, line 749
- `const color = dominant ? C.amber : removed < 0 ? C.greenSoft : C.textDim` — const, line 750
- `function MasteryDelta(` — function, line 800
- `const tau = surprise.followupThresholdNats ?? algoConfig().tauFollowupNats` — const, line 806
- `const bayes = surprise.bayesianSurprise ?? 0` — const, line 807
- `const hasSurprise = bayes > tau` — const, line 808
- `const postColor = masteryTone(after.mean, C)` — const, line 809
- `const evidence = f.criterionEvidence ?? []` — const, line 810
- `const assessed = criterionAssessed(row)` — const, line 858
- `const ok = row.pointsAwarded === row.pointsPossible` — const, line 859
- `const partial = row.pointsAwarded > 0 && row.pointsAwarded < row.pointsPossible` — const, line 860
- `const mark = !assessed ? "–" : ok ? "✓" : partial ? "◐" : "✗"` — const, line 861
- `const tone = !assessed ? C.textDim : ok ? C.green : partial ? C.amber : C.red` — const, line 862
- `function followupStatus(f: FeedbackBundle, tau: number): string` — function, line 891
- `const gate = f.surprise.gateDiagnostics` — const, line 895
- `const reasons = interventionReasons(f.surprise.triggeredActions ?? [])` — const, line 898
- `const suppressed = f.surprise.suppressedActions ?? []` — const, line 907
- `const GATE_SIGNAL_LABELS: Record<string, string> =` — const, line 916
- `const GATE_COMPARATORS: Record<string, string> =` — const, line 928
- `function gateNum(value: number | boolean | null): string | null` — function, line 932
- `function describeSignal(sig: FollowupGateSignalDto): string` — function, line 938
- `const name = sig.name ?? ""` — const, line 939
- `const label = GATE_SIGNAL_LABELS[name] ?? name.replace(/_/g, " ")` — const, line 945
- `const value = gateNum(sig.value)` — const, line 946
- `const cmp = sig.comparator ? GATE_COMPARATORS[sig.comparator] ?? sig.comparator : ""` — const, line 947
- `let threshold = gateNum(sig.threshold)` — let, line 948
- `const unit = sig.unit === "nats" ? " nats" : ""` — const, line 957
- `function describeGate(gate: FollowupGateDiagnosticsDto): string` — function, line 965
- `const sig = gate.decisiveSignal` — const, line 966
- `const signalText = sig ? describeSignal(sig) : gate.decisiveReason.replace(/_/g, " ")` — const, line 967
- `const scoreSuffix = typeof gate.gateScore === "number" && sig?.name !== "gate_score" ? ` · score $` — const, line 970
- `const base = (()` — const, line 975
- `const trigger = gate.triggeredReasons.find((r)` — const, line 985
- `const trigText = trigger ? trigger.replace(/_/g, " ") : "trigger"` — const, line 986
- `const v = gateNum(sig.value)` — const, line 996
- `function interventionReasons(actions: string[]): string[]` — function, line 1005
- `const reasons = actions .map((action)` — const, line 1006
- `function formatInterventionAction(action: string): string` — function, line 1017
- `function fmtTimestamp(seconds: number): string` — function, line 1029
- `const total = Math.max(0, Math.floor(seconds))` — const, line 1030
- `const h = Math.floor(total / 3600)` — const, line 1031
- `const m = Math.floor((total % 3600) / 60)` — const, line 1032
- `const s = total % 60` — const, line 1033
- `const mm = h > 0 ? String(m).padStart(2, "0") : String(m)` — const, line 1034
- `function timeRangeLabel(video:` — function, line 1038
- `function SourceRefCard(` — function, line 1044
- `const video = sourceRef.video` — const, line 1053
- `const openExternal = async (url: string)` — const, line 1055
- `const externalVideoUrl = video ? `https://www.youtube.com/watch?v=$` — const, line 1064
- `const openInReader = !externalVideoUrl && sourceId && onOpenPassage ? ()` — const, line 1069
- `const embedUrl = video ? `https://www.youtube-nocookie.com/embed/$` — const, line 1074
- `function SourceReviewPanel(` — function, line 1149
- `const refs = (f.sourceRefs ?? []).filter((ref)` — const, line 1158
- `const missed = f.rubricScore < f.maxPoints` — const, line 1161
- `function statementPairCopy(m: MatchedMisconceptionDto): string` — function, line 1221
- `const correction = m.correctionStatement.trim()` — const, line 1222
- `const x = m.targetFacet?.trim()` — const, line 1223
- `const y = m.confusedWithFacet?.trim()` — const, line 1224
- `const head = x && y ? `Your last answer was consistent with confusing $` — const, line 1225
- `function MisconceptionStatementCard(` — function, line 1232
- `const claim: ClaimCandidateDto = useMemo( ()` — const, line 1247
- `type RegradeSide =` — type, line 1294
- `type RegradeReceipt =` — type, line 1295
- `function gradeSide(f: FeedbackBundle): RegradeSide` — function, line 1297
- `function newClientKey(prefix: "contest"): string` — function, line 1306
- `const random = globalThis.crypto?.randomUUID?.()` — const, line 1307
- `function regradeHistoryLine(` — function, line 1313
- `const words = (side: RegradeSide)` — const, line 1315
- `const side = (s: RegradeSide)` — const, line 1322
- `function RegradeLedgerCard(` — function, line 1326
- `const claim: ClaimCandidateDto = useMemo( ()` — const, line 1340
- `const PROVISIONAL_PENDING_CLARIFICATION = "provisional_pending_clarification"` — const, line 1370
- `const CLARIFICATION_REASON_COPY: Record<string, string> =` — const, line 1374
- `function clarificationOutcomeCopy(result: AnswerGradingClarificationResultDto): string` — function, line 1382
- `function ClarificationCard(` — function, line 1394
- `const simple = simplePracticeFeedback()` — const, line 1562
- `const visitId = useRef(mintVisitId()).current` — const, line 1585
- `const planMode = Boolean(nextPlan && onPlanStep)` — const, line 1590
- `const autoAdvance = Boolean(nextQueue && onOpenNext) && !planMode` — const, line 1591
- `const nextItem = useNextQueueItem(autoAdvance ? nextQueue : null, feedback !== null)` — const, line 1592
- `const nextPlanStep = useNextPlanStep(planMode && nextPlan ? nextPlan.sessionId : null, feedback !== null)` — const, line 1593
- `const advanceGeneration = useRef(0)` — const, line 1595
- `const advancingRef = useRef(false)` — const, line 1596
- `const pendingQueueWrites = useRef(new Set<Promise<void>>())` — const, line 1602
- `const trackQueueWrite = useCallback(<T,>(write: Promise<T>): Promise<T>` — const, line 1603
- `const settledWrite: Promise<void> = write.then(()` — const, line 1604
- `const resolveNext = nextItem.resolve` — const, line 1609
- `const resolvePlanStep = nextPlanStep.resolve` — const, line 1610
- `const followup = followupRead && followupRead.workflowId === feedback?.followup?.workflowId ? followupRead : feedback?.followup ?? null` — const, line 1620
- `const followupRef = useRef<FollowupDto | null>(null)` — const, line 1624
- `const followupHeldRef = useRef(false)` — const, line 1625
- `const goOn = useCallback(async ()` — const, line 1628
- `const generation = ++advanceGeneration.current` — const, line 1632
- `let step: PlanStepDto | null = null` — let, line 1634
- `const generation = ++advanceGeneration.current` — const, line 1654
- `let head: ScheduledItemDto | null = null` — let, line 1656
- `const actOnNext = useCallback((next: FollowupNextDto | null)` — const, line 1671
- `const actOnNextRef = useRef(actOnNext)` — const, line 1683
- `const advance = useCallback(async ()` — const, line 1685
- `const owner = followupRef.current` — const, line 1686
- `let next: FollowupNextDto | null = null` — let, line 1688
- `const somethingElseChosen = useCallback((result: SomethingElseChosenDto)` — const, line 1701
- `const entry = lessonEntryFor(result)` — const, line 1702
- `const followupOpen = followup !== null && (followup.state === "pending" || followup.held)` — const, line 1713
- `let stopped = false` — let, line 1716
- `const timer = window.setInterval(()` — const, line 1717
- `const asked = nextWaiting ? api.followupNext(attemptId).then((next)` — const, line 1720
- `const wasHeld = useRef(false)` — const, line 1740
- `const continueWithout = useCallback(async ()` — const, line 1748
- `const status = await api.followupStatus(attemptId).catch(()` — const, line 1751
- `const showAnyway = useCallback(async ()` — const, line 1758
- `const status = await api.followupStatus(attemptId).catch(()` — const, line 1760
- `const goBack = useCallback(()` — const, line 1766
- `const refreshAfterDiagnosis = useCallback(()` — const, line 1775
- `const diagnosis = useDiagnosisCard(attemptId, simple ? feedback?.diagnosisStatus : null, refreshAfterDiagnosis, onError)` — const, line 1784
- `const contestKey = useRef<` — const, line 1796
- `const marksKept = useRef<` — const, line 1802
- `const marksRead = marksKept.current?.attemptId === attemptId ? marksKept.current.marks : null` — const, line 1804
- `const tapReplaced = marksRead !== null && marksRead.attemptId === feedback?.attemptId && marksRead.replacesCardTap` — const, line 1805
- `const listsOn = marksRead !== null && feedback?.attemptId === attemptId` — const, line 1806
- `const causalHypotheses = feedback?.causalFeedback?.causalHypotheses ?? []` — const, line 1807
- `const errorInputRef = useRef<HTMLInputElement>(null)` — const, line 1852
- `const noteTitleRef = useRef<HTMLInputElement>(null)` — const, line 1860
- `const noteBodyRef = useRef<HTMLTextAreaElement>(null)` — const, line 1861
- `const suggestions = useMemo<CandidateErrorTypeDto[]>(()` — const, line 1863
- `const all = item?.candidateErrorTypes ?? []` — const, line 1864
- `const q = errorTypeInput.trim().toLowerCase()` — const, line 1865
- `const filtered = q ? all.filter((e)` — const, line 1866
- `let cancelled = false` — let, line 1873
- `let cancelled = false` — let, line 1909
- `const handleAnswerClarification = async ()` — const, line 1928
- `const answer = clarificationAnswer.trim()` — const, line 1929
- `const result = await trackQueueWrite(api.answerGradingClarification(feedback.attemptId, answer))` — const, line 1933
- `const handleSkipClarification = ()` — const, line 1953
- `const applyRepairStatus = useCallback( (next: CausalRepairStatusDto)` — const, line 1965
- `const repairCaseId = useMemo(()` — const, line 1977
- `const causal = feedback?.causalFeedback` — const, line 1978
- `const need = causal?.probeNeed` — const, line 1979
- `let cancelled = false` — let, line 1996
- `const inspectIds = feedback ? uniqueIds([ feedback.attemptId, feedback.practiceItemId, feedback.learningObjectId, ...feedback.errorAttributions.map((event)` — const, line 2031
- `const practiceItemIds = feedback ? uniqueIds([feedback.practiceItemId]) : []` — const, line 2040
- `const shownAttempt = useRef(attemptId)` — const, line 2060
- `const refreshItemAfterRegrade = useCallback((bundle: FeedbackBundle)` — const, line 2062
- `const handleRegrade = async ()` — const, line 2071
- `const before = gradeSide(feedback)` — const, line 2074
- `const updated = await trackQueueWrite(api.triggerRegrade(feedback.attemptId))` — const, line 2076
- `const handleContest = async ()` — const, line 2095
- `const before = verdictOf(` — const, line 2099
- `const prior = gradeSide(feedback)` — const, line 2102
- `const reason = contestReason.trim()` — const, line 2103
- `const bound = contestKey.current` — const, line 2104
- `const key = bound && bound.reason === reason ? bound.key : newClientKey("contest")` — const, line 2105
- `const updated = await trackQueueWrite(api.triggerRegrade(feedback.attemptId, reason, key))` — const, line 2108
- `const outcome = updated.contest` — const, line 2112
- `const reviewed = outcome?.reviewRequested ? " It's marked for review." : ""` — const, line 2113
- `const after = verdictOf(` — const, line 2118
- `const contestCausal = (reason: UnresolvedCauseSelfReportResponse, factorId: string | null | undefined)` — const, line 2139
- `const handleTriggerFollowup = async ()` — const, line 2162
- `const updated = await trackQueueWrite(api.triggerFollowup(feedback.attemptId))` — const, line 2166
- `const handlePrimedRetry = async ()` — const, line 2179
- `const result = await api.startPrimedRetry(feedback.attemptId)` — const, line 2183
- `const handleGuidedRedo = async ()` — const, line 2201
- `const redo = await api.startGuidedRedo(feedback.attemptId)` — const, line 2205
- `const handleRateFollowup = async (useful: boolean)` — const, line 2217
- `const updated = await api.rateFollowup(feedback.attemptId, useful)` — const, line 2221
- `const handleElicitingResponse = async (suggestionIndex: number, responseMd: string)` — const, line 2236
- `const result = await trackQueueWrite(api.submitElicitingResponse(` — const, line 2240
- `const doAddError = async (errorType: string, severity?: number)` — const, line 2257
- `const updated = await api.addErrorEvent(feedback.attemptId, errorType.trim(), severity)` — const, line 2265
- `const handleAddError = ()` — const, line 2276
- `const sel = selectedSuggestionIdx >= 0 ? suggestions[selectedSuggestionIdx] : null` — const, line 2277
- `const handleUnresolvedCauseReport = async ( factorId: string, response: UnresolvedCauseSelfReportResponse, candidateIndex?: number | null, )` — const, line 2281
- `const resetNote = ()` — const, line 2298
- `const openNoteCapture = ()` — const, line 2304
- `const doSaveNote = async ()` — const, line 2310
- `const title = noteTitle.trim()` — const, line 2312
- `const body = noteBody.trim()` — const, line 2313
- `const subjectId = item?.subject ?? item?.subjects?.[0] ?? null` — const, line 2318
- `const stamp = new Date().toISOString().replace(/[-:T.]/g, "").slice(0, 14)` — const, line 2323
- `const noteId = `$` — const, line 2324
- `const result = await api.addNote(` — const, line 2327
- `const onKey = (event: KeyboardEvent)` — const, line 2346
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 2350
- `const right = verdictOf(` — const, line 2366
- `function simpleScreen( f: FeedbackBundle, matchedMisconception: FeedbackBundle["matchedMisconception"] | null, elicitingIndex: number, elicitingSuggestion: FeedbackBundle["repairSuggestions"][number] | null, errorPanel: ReactNode, notePanel: ReactNode, )` — function, line 2391
- `const held = f.heldForReview === true` — const, line 2399
- `const verdict = verdictOf(` — const, line 2400
- `const contestAvailable = f.gradingSource !== "self" && verdict !== "right"` — const, line 2402
- `const fixId = matchedMisconception?.id ?? (!repairStatus ? f.causalFeedback?.commonRepair?.misconceptionId ?? null : null)` — const, line 2406
- `let step: FeedbackNextStep | null = null` — let, line 2409
- `let stepIsRetry = false` — let, line 2410
- `const probeIsNext = followup !== null && (followup.state === "pending" || followup.state === "ready")` — const, line 2412
- `const card = diagnosis.status === "done" ? diagnosis.card : null` — const, line 2426
- `const causal = f.causalFeedback ?? null` — const, line 2427
- `const canSayNotRight = !tapReplaced && Boolean(card?.diagnosisId && card.responses.some((option)` — const, line 2429
- `const causalNotRightOk = Boolean(causal?.contestAction?.available && causal.contestAction.reasons.includes("diagnosis_wrong"))` — const, line 2430
- `const why =` — const, line 2431
- `const nextLabel = nextWaiting ? "preparing a question…" : origin === "reader" ? "back to the book" : planMode ? nextPlanKeyLabel(advancing, nextPlanStep.step) : autoAdvance ? nextKeyLabel(autoAdvance, advancing, nextItem.head, nextItem.empty) : ""` — const, line 2457
- `const regradeHistory: RegradeReceipt | null = regradeReceipt ?? (f.regrade ?` — const, line 2467
- `const criteria = answeredCriterionRows(f)` — const, line 2479
- `const showTier = f.criterionEvidence.some((row)` — const, line 2480
- `const f = feedback` — const, line 2838
- `const subject = item?.subject ?? item?.subjects?.[0] ?? null` — const, line 2839
- `const tau = f.surprise.followupThresholdNats ?? algoConfig().tauFollowupNats` — const, line 2841
- `const interventionNeed = f.interventionNeed` — const, line 2842
- `const elicitingIndex = f.repairSuggestions.findIndex((s)` — const, line 2846
- `const elicitingSuggestion = elicitingIndex >= 0 ? f.repairSuggestions[elicitingIndex] : null` — const, line 2847
- `const matchedMisconception = f.matchedMisconception && f.matchedMisconception.correctionStatement?.trim() ? f.matchedMisconception : null` — const, line 2851
- `const errorPanel = addingError ? ( <div style=` — const, line 2858
- `const s = suggestions[selectedSuggestionIdx]` — const, line 2905
- `const notePanel = addingNote ? ( <div style=` — const, line 2933
- `const receipt: RegradeReceipt | null = regradeReceipt ?? (f.regrade ?` — const, line 3349
- `function nextKeyLabel( autoAdvance: boolean, advancing: boolean, head: ScheduledItemDto | null, empty: boolean ): string` — function, line 3592
- `const title = head.learningObjectTitle` — const, line 3601
- `function uniqueIds(values: Array<string | null | undefined>): string[]` — function, line 3608

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `FeedbackScreen`; references `FeedbackScreen`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AnswerGradingClarificationResultDto`, `AttemptTraceDto`, `AttemptTraceEvidenceDto`, `CandidateErrorTypeDto`, `CausalRepairStatusDto`, `ClaimCandidateDto`, `ColdCheckResultDto`, `CriterionEvidenceRowDto`, `ElicitingResponseResultDto`, `ErrorEventDto`, `FeedbackBundle`, `FollowupDto`, `FollowupGateDiagnosticsDto`, `FollowupGateSignalDto`, `FollowupNextDto`, `GradingClarificationDto`, `GuidedRedoDto`, `HypothesisMarksDto`, `IntentRestorationDto`, `MasteryDto`, `MasteryStepDto`, `MatchedMisconceptionDto`, `NOT_ASSESSED_LABEL`, `PlanStepDto`, `PracticeItemDetail`, `QueueInput`, `RepairSuggestionDto`, `ResolvedSourceRefDto`, `ScheduledItemDto`, `SomethingElseChosenDto`, `UNVERIFIED_ROUTE_REVIEW_REASON`, `UnresolvedCauseSelfReportResponse`, `criterionAssessed`
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
- [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]] — import-or-re-export; imports `LessonEntry`
- [[Reference/Desktop/TypeScript/screens/feedback/CompareMethods|src/screens/feedback/CompareMethods.tsx]] — import-or-re-export; imports `CompareMethods`
- [[Reference/Desktop/TypeScript/screens/feedback/FeedbackSurface|src/screens/feedback/FeedbackSurface.tsx]] — import-or-re-export; imports `FeedbackNextStep`, `FeedbackSurface`, `answeredCriterionRows`, `answeredMaxPoints`, `gradedVersionUnrecorded`, `scoreOutOf`
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
- [apps/learnloop-tauri/src/screens/FeedbackScreen.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/FeedbackScreen.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/FeedbackScreen.somethingElse.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/FeedbackScreen.somethingElse.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/FeedbackScreen.plan.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/FeedbackScreen.plan.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/FeedbackScreen.phase4.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/FeedbackScreen.phase4.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/FeedbackScreen.liveQueue.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/FeedbackScreen.liveQueue.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/FeedbackScreen.followup.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/FeedbackScreen.followup.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/copy/denyList.phase4.test.tsx](../../../../../../apps/learnloop-tauri/src/copy/denyList.phase4.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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
