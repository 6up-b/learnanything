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
source_commit: "52756865dbdcfd48e1fe2adbd6c7d87996a15d65"
source_commit_timestamp: "2026-11-04T09:17:25-05:00"
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
| Source lines | 3522 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `52756865dbdcfd48e1fe2adbd6c7d87996a15d65` |
| Commit timestamp | `2026-11-04T09:17:25-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]]

## Public API

- `export function FeedbackScreen(` — function, line 1460

## Internal implementation anchors

- `type FeedbackOrigin, simplePracticeFeedback, VERDICT_TEXT, verdictOf } from "../app/practiceFeedback"` — type, line 55
- `type FeedbackNextStep } from "./feedback/FeedbackSurface"` — type, line 66
- `const C =` — const, line 75
- `const MONO = '"JetBrains Mono", "Fira Code", ui-monospace, SFMono-Regular, Menlo, monospace'` — const, line 92
- `function Faint(` — function, line 95
- `function Dim(` — function, line 98
- `function Meta(` — function, line 101
- `function FbHeader(` — function, line 106
- `function EvidenceHeader(` — function, line 125
- `function BlockBar(` — function, line 142
- `const filled = Math.max(0, Math.min(width, Math.round((value / max) * width)))` — const, line 145
- `function fmtDue(iso: string | null): string` — function, line 155
- `const d = new Date(iso)` — const, line 158
- `const now = new Date()` — const, line 159
- `const diffH = (d.getTime() - now.getTime()) / 3_600_000` — const, line 160
- `const tomorrow = new Date(now)` — const, line 161
- `function fmtDay(iso: string | null | undefined): string` — function, line 181
- `function ColdCheckBanner(` — function, line 194
- `const confirmed = result.claim === "repair_confirmed"` — const, line 195
- `const failed = result.claim === "escalated_unrepaired"` — const, line 196
- `const tone = confirmed ? C.green : failed ? C.amber : C.textDim` — const, line 197
- `const heading = confirmed ? "unassisted check · passed" : failed ? "unassisted check · did not hold" : result.claim === "downgraded" ? "unassisted check · recorded, not counted" : "unassisted check · no verdict"` — const, line 198
- `const when = fmtDay(result.instructedAt)` — const, line 205
- `const body = confirmed ? `This was the unassisted check for the repair you did on $` — const, line 206
- `function AutoPrimedNote(` — function, line 246
- `function ElicitingRepairCard(` — function, line 277
- `const anchor = suggestion.targetRefs?.[0] ?? null` — const, line 289
- `const answered = outcome != null` — const, line 290
- `function ratingPill(r: string): string` — function, line 380
- `function modePillTone(mode: string): string` — function, line 387
- `function ScoreBlock(` — function, line 392
- `const tone = score === max ? C.green : score >= max * 0.75 ? C.greenSoft : score >= max * 0.5 ? C.amber : C.red` — const, line 394
- `const label = score === max ? "perfect" : score >= max * 0.75 ? "good" : score >= max * 0.5 ? "partial credit" : "needs work"` — const, line 398
- `function CriterionRow(` — function, line 440
- `const assessed = criterionAssessed(row)` — const, line 454
- `const ok = maxKnown && row.pointsAwarded === row.pointsPossible` — const, line 455
- `const partial = maxKnown && row.pointsAwarded > 0 && row.pointsAwarded < row.pointsPossible` — const, line 456
- `const mark = !assessed ? "–" : !maxKnown ? "·" : ok ? "✓" : partial ? "◐" : "✗"` — const, line 457
- `const tone = !assessed || !maxKnown ? C.textDim : ok ? C.green : partial ? C.amber : C.red` — const, line 458
- `function ErrorAttribution(` — function, line 496
- `const plan = ea.repairPlan` — const, line 497
- `const resolutionStatus = typeof plan?.resolutionStatus === "string" ? plan.resolutionStatus : null` — const, line 498
- `const causeScope = typeof plan?.causeScope === "string" ? plan.causeScope : null` — const, line 500
- `const operation = typeof plan?.operation === "string" ? plan.operation : null` — const, line 501
- `const abstentionReason = typeof plan?.abstentionReason === "string" ? plan.abstentionReason : null` — const, line 502
- `const targetRef = plan?.targetRef && typeof plan.targetRef === "object" && !Array.isArray(plan.targetRef) ? plan.targetRef as Parameters<typeof formatCausalTarget>[0] : null` — const, line 504
- `const firstDivergence = plan?.firstDivergence && typeof plan.firstDivergence === "object" && !Array.isArray(plan.firstDivergence) ? plan.firstDivergence as Parameters<typeof formatDivergenceAnchor>[0] : null` — const, line 508
- `const SQRT_2PI = Math.sqrt(2 * Math.PI)` — const, line 574
- `const PROB_TICKS = [0.1, 0.25, 0.5, 0.75, 0.9]` — const, line 575
- `function logit(p: number): number` — function, line 577
- `const c = Math.min(1 - 1e-4, Math.max(1e-4, p))` — const, line 578
- `function toLogitSpace(mean: number, variance: number):` — function, line 584
- `const m = Math.min(1 - 1e-4, Math.max(1e-4, mean))` — const, line 585
- `const slope = m * (1 - m)` — const, line 586
- `const logitVar = Math.max(1e-4, variance / (slope * slope))` — const, line 587
- `function gaussianPdf(x: number, mu: number, sd: number): number` — function, line 591
- `const z = (x - mu) / sd` — const, line 592
- `function BeliefShiftChart(` — function, line 601
- `const prior = toLogitSpace(before.mean, before.variance)` — const, line 616
- `const post = toLogitSpace(after.mean, after.variance)` — const, line 617
- `const padL = 8` — const, line 619
- `const padR = 8` — const, line 620
- `const padT = 20` — const, line 621
- `const padB = 20` — const, line 622
- `const plotW = width - padL - padR` — const, line 623
- `const plotH = height - padT - padB` — const, line 624
- `const lo = Math.min(prior.mu - 3.4 * prior.sd, post.mu - 3.4 * post.sd, logit(0.15))` — const, line 628
- `const hi = Math.max(prior.mu + 3.4 * prior.sd, post.mu + 3.4 * post.sd, logit(0.85))` — const, line 629
- `const span = Math.max(1e-3, hi - lo)` — const, line 630
- `const xOf = (t: number)` — const, line 631
- `const peak = Math.max(gaussianPdf(prior.mu, prior.mu, prior.sd), gaussianPdf(post.mu, post.mu, post.sd))` — const, line 634
- `const yMax = peak * 1.12` — const, line 635
- `const baseY = padT + plotH` — const, line 636
- `const yOf = (d: number)` — const, line 637
- `const N = 72` — const, line 639
- `const curvePath = (mu: number, sd: number, close: boolean): string` — const, line 640
- `let d = ""` — let, line 641
- `const x = lo + (span * i) / N` — const, line 643
- `const y = gaussianPdf(x, mu, sd)` — const, line 644
- `const postColor = masteryTone(after.mean, C)` — const, line 651
- `const shift = post.mu - prior.mu` — const, line 652
- `const showArrow = bayesianSurprise > tau && Math.abs(shift) > 1e-3` — const, line 653
- `const arrowColor = shift >= 0 ? C.green : C.red` — const, line 654
- `const arrowY = 11` — const, line 655
- `const xPrior = xOf(prior.mu)` — const, line 656
- `const xPost = xOf(post.mu)` — const, line 657
- `const yPrior = yOf(gaussianPdf(prior.mu, prior.mu, prior.sd))` — const, line 658
- `const yPost = yOf(gaussianPdf(post.mu, post.mu, post.sd))` — const, line 659
- `const t = logit(p)` — const, line 665
- `const x = xOf(t)` — const, line 667
- `const mid = p === 0.5` — const, line 668
- `function MasteryStepBreakdown(` — function, line 723
- `const pct = (v: number)` — const, line 725
- `const dominant = factor.key === step.dominantFactorKey` — const, line 741
- `const removed = 1 - factor.multiplier` — const, line 744
- `const color = dominant ? C.amber : removed < 0 ? C.greenSoft : C.textDim` — const, line 745
- `function MasteryDelta(` — function, line 795
- `const tau = surprise.followupThresholdNats ?? algoConfig().tauFollowupNats` — const, line 801
- `const bayes = surprise.bayesianSurprise ?? 0` — const, line 802
- `const hasSurprise = bayes > tau` — const, line 803
- `const postColor = masteryTone(after.mean, C)` — const, line 804
- `const evidence = f.criterionEvidence ?? []` — const, line 805
- `const assessed = criterionAssessed(row)` — const, line 853
- `const ok = row.pointsAwarded === row.pointsPossible` — const, line 854
- `const partial = row.pointsAwarded > 0 && row.pointsAwarded < row.pointsPossible` — const, line 855
- `const mark = !assessed ? "–" : ok ? "✓" : partial ? "◐" : "✗"` — const, line 856
- `const tone = !assessed ? C.textDim : ok ? C.green : partial ? C.amber : C.red` — const, line 857
- `function followupStatus(f: FeedbackBundle, tau: number): string` — function, line 886
- `const gate = f.surprise.gateDiagnostics` — const, line 890
- `const reasons = interventionReasons(f.surprise.triggeredActions ?? [])` — const, line 893
- `const suppressed = f.surprise.suppressedActions ?? []` — const, line 902
- `const GATE_SIGNAL_LABELS: Record<string, string> =` — const, line 911
- `const GATE_COMPARATORS: Record<string, string> =` — const, line 923
- `function gateNum(value: number | boolean | null): string | null` — function, line 927
- `function describeSignal(sig: FollowupGateSignalDto): string` — function, line 933
- `const name = sig.name ?? ""` — const, line 934
- `const label = GATE_SIGNAL_LABELS[name] ?? name.replace(/_/g, " ")` — const, line 940
- `const value = gateNum(sig.value)` — const, line 941
- `const cmp = sig.comparator ? GATE_COMPARATORS[sig.comparator] ?? sig.comparator : ""` — const, line 942
- `let threshold = gateNum(sig.threshold)` — let, line 943
- `const unit = sig.unit === "nats" ? " nats" : ""` — const, line 952
- `function describeGate(gate: FollowupGateDiagnosticsDto): string` — function, line 960
- `const sig = gate.decisiveSignal` — const, line 961
- `const signalText = sig ? describeSignal(sig) : gate.decisiveReason.replace(/_/g, " ")` — const, line 962
- `const scoreSuffix = typeof gate.gateScore === "number" && sig?.name !== "gate_score" ? ` · score $` — const, line 965
- `const base = (()` — const, line 970
- `const trigger = gate.triggeredReasons.find((r)` — const, line 980
- `const trigText = trigger ? trigger.replace(/_/g, " ") : "trigger"` — const, line 981
- `const v = gateNum(sig.value)` — const, line 991
- `function interventionReasons(actions: string[]): string[]` — function, line 1000
- `const reasons = actions .map((action)` — const, line 1001
- `function formatInterventionAction(action: string): string` — function, line 1012
- `function fmtTimestamp(seconds: number): string` — function, line 1024
- `const total = Math.max(0, Math.floor(seconds))` — const, line 1025
- `const h = Math.floor(total / 3600)` — const, line 1026
- `const m = Math.floor((total % 3600) / 60)` — const, line 1027
- `const s = total % 60` — const, line 1028
- `const mm = h > 0 ? String(m).padStart(2, "0") : String(m)` — const, line 1029
- `function timeRangeLabel(video:` — function, line 1033
- `function SourceRefCard(` — function, line 1039
- `const video = sourceRef.video` — const, line 1047
- `const openExternal = async (url: string)` — const, line 1049
- `const externalVideoUrl = video ? `https://www.youtube.com/watch?v=$` — const, line 1058
- `const embedUrl = video ? `https://www.youtube-nocookie.com/embed/$` — const, line 1063
- `function SourceReviewPanel(` — function, line 1132
- `const refs = (f.sourceRefs ?? []).filter((ref)` — const, line 1140
- `const missed = f.rubricScore < f.maxPoints` — const, line 1143
- `function statementPairCopy(m: MatchedMisconceptionDto): string` — function, line 1202
- `const correction = m.correctionStatement.trim()` — const, line 1203
- `const x = m.targetFacet?.trim()` — const, line 1204
- `const y = m.confusedWithFacet?.trim()` — const, line 1205
- `const head = x && y ? `Your last answer was consistent with confusing $` — const, line 1206
- `function MisconceptionStatementCard(` — function, line 1213
- `const claim: ClaimCandidateDto = useMemo( ()` — const, line 1228
- `type RegradeSide =` — type, line 1275
- `type RegradeReceipt =` — type, line 1276
- `function gradeSide(f: FeedbackBundle): RegradeSide` — function, line 1278
- `function newClientKey(prefix: "contest"): string` — function, line 1287
- `const random = globalThis.crypto?.randomUUID?.()` — const, line 1288
- `function regradeHistoryLine(` — function, line 1294
- `const words = (side: RegradeSide)` — const, line 1296
- `const side = (s: RegradeSide)` — const, line 1303
- `function RegradeLedgerCard(` — function, line 1307
- `const claim: ClaimCandidateDto = useMemo( ()` — const, line 1321
- `const PROVISIONAL_PENDING_CLARIFICATION = "provisional_pending_clarification"` — const, line 1351
- `const CLARIFICATION_REASON_COPY: Record<string, string> =` — const, line 1355
- `function clarificationOutcomeCopy(result: AnswerGradingClarificationResultDto): string` — function, line 1363
- `function ClarificationCard(` — function, line 1375
- `const simple = simplePracticeFeedback()` — const, line 1537
- `const visitId = useRef(mintVisitId()).current` — const, line 1560
- `const planMode = Boolean(nextPlan && onPlanStep)` — const, line 1565
- `const autoAdvance = Boolean(nextQueue && onOpenNext) && !planMode` — const, line 1566
- `const nextItem = useNextQueueItem(autoAdvance ? nextQueue : null, feedback !== null)` — const, line 1567
- `const nextPlanStep = useNextPlanStep(planMode && nextPlan ? nextPlan.sessionId : null, feedback !== null)` — const, line 1568
- `const advanceGeneration = useRef(0)` — const, line 1570
- `const advancingRef = useRef(false)` — const, line 1571
- `const pendingQueueWrites = useRef(new Set<Promise<void>>())` — const, line 1577
- `const trackQueueWrite = useCallback(<T,>(write: Promise<T>): Promise<T>` — const, line 1578
- `const settledWrite: Promise<void> = write.then(()` — const, line 1579
- `const resolveNext = nextItem.resolve` — const, line 1584
- `const resolvePlanStep = nextPlanStep.resolve` — const, line 1585
- `const followup = followupRead && followupRead.workflowId === feedback?.followup?.workflowId ? followupRead : feedback?.followup ?? null` — const, line 1595
- `const followupRef = useRef<FollowupDto | null>(null)` — const, line 1599
- `const followupHeldRef = useRef(false)` — const, line 1600
- `const goOn = useCallback(async ()` — const, line 1603
- `const generation = ++advanceGeneration.current` — const, line 1607
- `let step: PlanStepDto | null = null` — let, line 1609
- `const generation = ++advanceGeneration.current` — const, line 1629
- `let head: ScheduledItemDto | null = null` — let, line 1631
- `const actOnNext = useCallback((next: FollowupNextDto | null)` — const, line 1646
- `const actOnNextRef = useRef(actOnNext)` — const, line 1658
- `const advance = useCallback(async ()` — const, line 1660
- `const owner = followupRef.current` — const, line 1661
- `let next: FollowupNextDto | null = null` — let, line 1663
- `const followupOpen = followup !== null && (followup.state === "pending" || followup.held)` — const, line 1674
- `let stopped = false` — let, line 1677
- `const timer = window.setInterval(()` — const, line 1678
- `const asked = nextWaiting ? api.followupNext(attemptId).then((next)` — const, line 1681
- `const wasHeld = useRef(false)` — const, line 1701
- `const continueWithout = useCallback(async ()` — const, line 1709
- `const status = await api.followupStatus(attemptId).catch(()` — const, line 1712
- `const showAnyway = useCallback(async ()` — const, line 1719
- `const status = await api.followupStatus(attemptId).catch(()` — const, line 1721
- `const goBack = useCallback(()` — const, line 1727
- `const refreshAfterDiagnosis = useCallback(()` — const, line 1736
- `const diagnosis = useDiagnosisCard(attemptId, simple ? feedback?.diagnosisStatus : null, refreshAfterDiagnosis, onError)` — const, line 1745
- `const contestKey = useRef<` — const, line 1757
- `const errorInputRef = useRef<HTMLInputElement>(null)` — const, line 1779
- `const noteTitleRef = useRef<HTMLInputElement>(null)` — const, line 1787
- `const noteBodyRef = useRef<HTMLTextAreaElement>(null)` — const, line 1788
- `const suggestions = useMemo<CandidateErrorTypeDto[]>(()` — const, line 1790
- `const all = item?.candidateErrorTypes ?? []` — const, line 1791
- `const q = errorTypeInput.trim().toLowerCase()` — const, line 1792
- `const filtered = q ? all.filter((e)` — const, line 1793
- `let cancelled = false` — let, line 1800
- `let cancelled = false` — let, line 1836
- `const handleAnswerClarification = async ()` — const, line 1855
- `const answer = clarificationAnswer.trim()` — const, line 1856
- `const result = await trackQueueWrite(api.answerGradingClarification(feedback.attemptId, answer))` — const, line 1860
- `const handleSkipClarification = ()` — const, line 1880
- `const applyRepairStatus = useCallback( (next: CausalRepairStatusDto)` — const, line 1892
- `const repairCaseId = useMemo(()` — const, line 1904
- `const causal = feedback?.causalFeedback` — const, line 1905
- `const need = causal?.probeNeed` — const, line 1906
- `let cancelled = false` — let, line 1923
- `const inspectIds = feedback ? uniqueIds([ feedback.attemptId, feedback.practiceItemId, feedback.learningObjectId, ...feedback.errorAttributions.map((event)` — const, line 1958
- `const practiceItemIds = feedback ? uniqueIds([feedback.practiceItemId]) : []` — const, line 1967
- `const shownAttempt = useRef(attemptId)` — const, line 1987
- `const refreshItemAfterRegrade = useCallback((bundle: FeedbackBundle)` — const, line 1989
- `const handleRegrade = async ()` — const, line 1998
- `const before = gradeSide(feedback)` — const, line 2001
- `const updated = await trackQueueWrite(api.triggerRegrade(feedback.attemptId))` — const, line 2003
- `const handleContest = async ()` — const, line 2022
- `const before = verdictOf(` — const, line 2026
- `const prior = gradeSide(feedback)` — const, line 2029
- `const reason = contestReason.trim()` — const, line 2030
- `const bound = contestKey.current` — const, line 2031
- `const key = bound && bound.reason === reason ? bound.key : newClientKey("contest")` — const, line 2032
- `const updated = await trackQueueWrite(api.triggerRegrade(feedback.attemptId, reason, key))` — const, line 2035
- `const outcome = updated.contest` — const, line 2039
- `const reviewed = outcome?.reviewRequested ? " It's marked for review." : ""` — const, line 2040
- `const after = verdictOf(` — const, line 2045
- `const contestCausal = (reason: UnresolvedCauseSelfReportResponse, factorId: string | null | undefined)` — const, line 2066
- `const handleTriggerFollowup = async ()` — const, line 2089
- `const updated = await trackQueueWrite(api.triggerFollowup(feedback.attemptId))` — const, line 2093
- `const handlePrimedRetry = async ()` — const, line 2106
- `const result = await api.startPrimedRetry(feedback.attemptId)` — const, line 2110
- `const handleGuidedRedo = async ()` — const, line 2128
- `const redo = await api.startGuidedRedo(feedback.attemptId)` — const, line 2132
- `const handleRateFollowup = async (useful: boolean)` — const, line 2144
- `const updated = await api.rateFollowup(feedback.attemptId, useful)` — const, line 2148
- `const handleElicitingResponse = async (suggestionIndex: number, responseMd: string)` — const, line 2163
- `const result = await trackQueueWrite(api.submitElicitingResponse(` — const, line 2167
- `const doAddError = async (errorType: string, severity?: number)` — const, line 2184
- `const updated = await api.addErrorEvent(feedback.attemptId, errorType.trim(), severity)` — const, line 2192
- `const handleAddError = ()` — const, line 2203
- `const sel = selectedSuggestionIdx >= 0 ? suggestions[selectedSuggestionIdx] : null` — const, line 2204
- `const handleUnresolvedCauseReport = async ( factorId: string, response: UnresolvedCauseSelfReportResponse, candidateIndex?: number | null, )` — const, line 2208
- `const resetNote = ()` — const, line 2225
- `const openNoteCapture = ()` — const, line 2231
- `const doSaveNote = async ()` — const, line 2237
- `const title = noteTitle.trim()` — const, line 2239
- `const body = noteBody.trim()` — const, line 2240
- `const subjectId = item?.subject ?? item?.subjects?.[0] ?? null` — const, line 2245
- `const stamp = new Date().toISOString().replace(/[-:T.]/g, "").slice(0, 14)` — const, line 2250
- `const noteId = `$` — const, line 2251
- `const result = await api.addNote(` — const, line 2254
- `const onKey = (event: KeyboardEvent)` — const, line 2273
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 2277
- `const right = verdictOf(` — const, line 2293
- `function simpleScreen( f: FeedbackBundle, matchedMisconception: FeedbackBundle["matchedMisconception"] | null, elicitingIndex: number, elicitingSuggestion: FeedbackBundle["repairSuggestions"][number] | null, errorPanel: ReactNode, notePanel: ReactNode, )` — function, line 2318
- `const held = f.heldForReview === true` — const, line 2326
- `const verdict = verdictOf(` — const, line 2327
- `const contestAvailable = f.gradingSource !== "self" && verdict !== "right"` — const, line 2329
- `const fixId = matchedMisconception?.id ?? (!repairStatus ? f.causalFeedback?.commonRepair?.misconceptionId ?? null : null)` — const, line 2333
- `let step: FeedbackNextStep | null = null` — let, line 2336
- `let stepIsRetry = false` — let, line 2337
- `const probeIsNext = followup !== null && (followup.state === "pending" || followup.state === "ready")` — const, line 2339
- `const card = diagnosis.status === "done" ? diagnosis.card : null` — const, line 2353
- `const causal = f.causalFeedback ?? null` — const, line 2354
- `const canSayNotRight = Boolean(card?.diagnosisId && card.responses.some((option)` — const, line 2355
- `const causalNotRightOk = Boolean(causal?.contestAction?.available && causal.contestAction.reasons.includes("diagnosis_wrong"))` — const, line 2356
- `const why =` — const, line 2357
- `const nextLabel = nextWaiting ? "preparing a question…" : origin === "reader" ? "back to the book" : planMode ? nextPlanKeyLabel(advancing, nextPlanStep.step) : autoAdvance ? nextKeyLabel(autoAdvance, advancing, nextItem.head, nextItem.empty) : ""` — const, line 2383
- `const regradeHistory: RegradeReceipt | null = regradeReceipt ?? (f.regrade ?` — const, line 2393
- `const criteria = answeredCriterionRows(f)` — const, line 2405
- `const showTier = f.criterionEvidence.some((row)` — const, line 2406
- `const f = feedback` — const, line 2753
- `const subject = item?.subject ?? item?.subjects?.[0] ?? null` — const, line 2754
- `const tau = f.surprise.followupThresholdNats ?? algoConfig().tauFollowupNats` — const, line 2756
- `const interventionNeed = f.interventionNeed` — const, line 2757
- `const elicitingIndex = f.repairSuggestions.findIndex((s)` — const, line 2761
- `const elicitingSuggestion = elicitingIndex >= 0 ? f.repairSuggestions[elicitingIndex] : null` — const, line 2762
- `const matchedMisconception = f.matchedMisconception && f.matchedMisconception.correctionStatement?.trim() ? f.matchedMisconception : null` — const, line 2766
- `const errorPanel = addingError ? ( <div style=` — const, line 2773
- `const s = suggestions[selectedSuggestionIdx]` — const, line 2820
- `const notePanel = addingNote ? ( <div style=` — const, line 2848
- `const receipt: RegradeReceipt | null = regradeReceipt ?? (f.regrade ?` — const, line 3264
- `function nextKeyLabel( autoAdvance: boolean, advancing: boolean, head: ScheduledItemDto | null, empty: boolean ): string` — function, line 3504
- `const title = head.learningObjectTitle` — const, line 3513
- `function uniqueIds(values: Array<string | null | undefined>): string[]` — function, line 3520

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `FeedbackScreen`; references `FeedbackScreen`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AnswerGradingClarificationResultDto`, `AttemptTraceDto`, `AttemptTraceEvidenceDto`, `CandidateErrorTypeDto`, `CausalRepairStatusDto`, `ClaimCandidateDto`, `ColdCheckResultDto`, `CriterionEvidenceRowDto`, `ElicitingResponseResultDto`, `ErrorEventDto`, `FeedbackBundle`, `FollowupDto`, `FollowupGateDiagnosticsDto`, `FollowupGateSignalDto`, `FollowupNextDto`, `GradingClarificationDto`, `GuidedRedoDto`, `IntentRestorationDto`, `MasteryDto`, `MasteryStepDto`, `MatchedMisconceptionDto`, `NOT_ASSESSED_LABEL`, `PlanStepDto`, `PracticeItemDetail`, `QueueInput`, `RepairSuggestionDto`, `ResolvedSourceRefDto`, `ScheduledItemDto`, `UNVERIFIED_ROUTE_REVIEW_REASON`, `UnresolvedCauseSelfReportResponse`, `criterionAssessed`
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
- [[Reference/Desktop/TypeScript/screens/feedback/FollowupPanel|src/screens/feedback/FollowupPanel.tsx]] — import-or-re-export; imports `FollowupPanel`

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
- [apps/learnloop-tauri/src/screens/FeedbackScreen.followup.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/FeedbackScreen.followup.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/copy/denyList.phase4.test.tsx](../../../../../../apps/learnloop-tauri/src/copy/denyList.phase4.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_active_errors_overlay.py](../../../../../../tests/test_active_errors_overlay.py) — cross-boundary name contract: references uniquely owned exported name `FeedbackScreen`; it does **not** directly execute this source module.
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
