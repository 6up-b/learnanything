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
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
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
| Source lines | 2624 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]]

## Public API

- `export function FeedbackScreen(` — function, line 1372

## Internal implementation anchors

- `const C =` — const, line 45
- `const MONO = '"JetBrains Mono", "Fira Code", ui-monospace, SFMono-Regular, Menlo, monospace'` — const, line 62
- `function Faint(` — function, line 65
- `function Dim(` — function, line 68
- `function Meta(` — function, line 71
- `function FbHeader(` — function, line 76
- `function EvidenceHeader(` — function, line 95
- `function BlockBar(` — function, line 112
- `const filled = Math.max(0, Math.min(width, Math.round((value / max) * width)))` — const, line 115
- `function fmtDue(iso: string | null): string` — function, line 125
- `const d = new Date(iso)` — const, line 128
- `const now = new Date()` — const, line 129
- `const diffH = (d.getTime() - now.getTime()) / 3_600_000` — const, line 130
- `const tomorrow = new Date(now)` — const, line 131
- `function fmtDay(iso: string | null | undefined): string` — function, line 151
- `function ColdCheckBanner(` — function, line 164
- `const confirmed = result.claim === "repair_confirmed"` — const, line 165
- `const failed = result.claim === "escalated_unrepaired"` — const, line 166
- `const tone = confirmed ? C.green : failed ? C.amber : C.textDim` — const, line 167
- `const heading = confirmed ? "unassisted check · passed" : failed ? "unassisted check · did not hold" : result.claim === "downgraded" ? "unassisted check · recorded, not counted" : "unassisted check · no verdict"` — const, line 168
- `const when = fmtDay(result.instructedAt)` — const, line 175
- `const body = confirmed ? `This was the unassisted check for the repair you did on $` — const, line 176
- `function AutoPrimedNote(` — function, line 216
- `function ElicitingRepairCard(` — function, line 247
- `const anchor = suggestion.targetRefs?.[0] ?? null` — const, line 259
- `const answered = outcome != null` — const, line 260
- `function ratingPill(r: string): string` — function, line 350
- `function modePillTone(mode: string): string` — function, line 357
- `function ScoreBlock(` — function, line 362
- `const tone = score === max ? C.green : score >= max * 0.75 ? C.greenSoft : score >= max * 0.5 ? C.amber : C.red` — const, line 364
- `const label = score === max ? "perfect" : score >= max * 0.75 ? "good" : score >= max * 0.5 ? "partial credit" : "needs work"` — const, line 368
- `function CriterionRow(` — function, line 410
- `const ok = row.pointsAwarded === row.pointsPossible` — const, line 411
- `const partial = row.pointsAwarded > 0 && row.pointsAwarded < row.pointsPossible` — const, line 412
- `const mark = ok ? "✓" : partial ? "◐" : "✗"` — const, line 413
- `const tone = ok ? C.green : partial ? C.amber : C.red` — const, line 414
- `function ErrorAttribution(` — function, line 449
- `const plan = ea.repairPlan` — const, line 450
- `const resolutionStatus = typeof plan?.resolutionStatus === "string" ? plan.resolutionStatus : null` — const, line 451
- `const causeScope = typeof plan?.causeScope === "string" ? plan.causeScope : null` — const, line 453
- `const operation = typeof plan?.operation === "string" ? plan.operation : null` — const, line 454
- `const abstentionReason = typeof plan?.abstentionReason === "string" ? plan.abstentionReason : null` — const, line 455
- `const targetRef = plan?.targetRef && typeof plan.targetRef === "object" && !Array.isArray(plan.targetRef) ? plan.targetRef as Parameters<typeof formatCausalTarget>[0] : null` — const, line 457
- `const firstDivergence = plan?.firstDivergence && typeof plan.firstDivergence === "object" && !Array.isArray(plan.firstDivergence) ? plan.firstDivergence as Parameters<typeof formatDivergenceAnchor>[0] : null` — const, line 461
- `const SQRT_2PI = Math.sqrt(2 * Math.PI)` — const, line 527
- `const PROB_TICKS = [0.1, 0.25, 0.5, 0.75, 0.9]` — const, line 528
- `function logit(p: number): number` — function, line 530
- `const c = Math.min(1 - 1e-4, Math.max(1e-4, p))` — const, line 531
- `function toLogitSpace(mean: number, variance: number):` — function, line 537
- `const m = Math.min(1 - 1e-4, Math.max(1e-4, mean))` — const, line 538
- `const slope = m * (1 - m)` — const, line 539
- `const logitVar = Math.max(1e-4, variance / (slope * slope))` — const, line 540
- `function gaussianPdf(x: number, mu: number, sd: number): number` — function, line 544
- `const z = (x - mu) / sd` — const, line 545
- `function BeliefShiftChart(` — function, line 554
- `const prior = toLogitSpace(before.mean, before.variance)` — const, line 569
- `const post = toLogitSpace(after.mean, after.variance)` — const, line 570
- `const padL = 8` — const, line 572
- `const padR = 8` — const, line 573
- `const padT = 20` — const, line 574
- `const padB = 20` — const, line 575
- `const plotW = width - padL - padR` — const, line 576
- `const plotH = height - padT - padB` — const, line 577
- `const lo = Math.min(prior.mu - 3.4 * prior.sd, post.mu - 3.4 * post.sd, logit(0.15))` — const, line 581
- `const hi = Math.max(prior.mu + 3.4 * prior.sd, post.mu + 3.4 * post.sd, logit(0.85))` — const, line 582
- `const span = Math.max(1e-3, hi - lo)` — const, line 583
- `const xOf = (t: number)` — const, line 584
- `const peak = Math.max(gaussianPdf(prior.mu, prior.mu, prior.sd), gaussianPdf(post.mu, post.mu, post.sd))` — const, line 587
- `const yMax = peak * 1.12` — const, line 588
- `const baseY = padT + plotH` — const, line 589
- `const yOf = (d: number)` — const, line 590
- `const N = 72` — const, line 592
- `const curvePath = (mu: number, sd: number, close: boolean): string` — const, line 593
- `let d = ""` — let, line 594
- `const x = lo + (span * i) / N` — const, line 596
- `const y = gaussianPdf(x, mu, sd)` — const, line 597
- `const postColor = masteryTone(after.mean, C)` — const, line 604
- `const shift = post.mu - prior.mu` — const, line 605
- `const showArrow = bayesianSurprise > tau && Math.abs(shift) > 1e-3` — const, line 606
- `const arrowColor = shift >= 0 ? C.green : C.red` — const, line 607
- `const arrowY = 11` — const, line 608
- `const xPrior = xOf(prior.mu)` — const, line 609
- `const xPost = xOf(post.mu)` — const, line 610
- `const yPrior = yOf(gaussianPdf(prior.mu, prior.mu, prior.sd))` — const, line 611
- `const yPost = yOf(gaussianPdf(post.mu, post.mu, post.sd))` — const, line 612
- `const t = logit(p)` — const, line 618
- `const x = xOf(t)` — const, line 620
- `const mid = p === 0.5` — const, line 621
- `function MasteryStepBreakdown(` — function, line 676
- `const pct = (v: number)` — const, line 678
- `const dominant = factor.key === step.dominantFactorKey` — const, line 694
- `const removed = 1 - factor.multiplier` — const, line 697
- `const color = dominant ? C.amber : removed < 0 ? C.greenSoft : C.textDim` — const, line 698
- `function MasteryDelta(` — function, line 748
- `const tau = surprise.followupThresholdNats ?? algoConfig().tauFollowupNats` — const, line 754
- `const bayes = surprise.bayesianSurprise ?? 0` — const, line 755
- `const hasSurprise = bayes > tau` — const, line 756
- `const postColor = masteryTone(after.mean, C)` — const, line 757
- `const evidence = f.criterionEvidence ?? []` — const, line 758
- `const ok = row.pointsAwarded === row.pointsPossible` — const, line 806
- `const partial = row.pointsAwarded > 0 && row.pointsAwarded < row.pointsPossible` — const, line 807
- `const mark = ok ? "✓" : partial ? "◐" : "✗"` — const, line 808
- `const tone = ok ? C.green : partial ? C.amber : C.red` — const, line 809
- `function followupStatus(f: FeedbackBundle, tau: number): string` — function, line 834
- `const gate = f.surprise.gateDiagnostics` — const, line 838
- `const reasons = interventionReasons(f.surprise.triggeredActions ?? [])` — const, line 841
- `const suppressed = f.surprise.suppressedActions ?? []` — const, line 850
- `const GATE_SIGNAL_LABELS: Record<string, string> =` — const, line 859
- `const GATE_COMPARATORS: Record<string, string> =` — const, line 871
- `function gateNum(value: number | boolean | null): string | null` — function, line 875
- `function describeSignal(sig: FollowupGateSignalDto): string` — function, line 881
- `const name = sig.name ?? ""` — const, line 882
- `const label = GATE_SIGNAL_LABELS[name] ?? name.replace(/_/g, " ")` — const, line 888
- `const value = gateNum(sig.value)` — const, line 889
- `const cmp = sig.comparator ? GATE_COMPARATORS[sig.comparator] ?? sig.comparator : ""` — const, line 890
- `let threshold = gateNum(sig.threshold)` — let, line 891
- `const unit = sig.unit === "nats" ? " nats" : ""` — const, line 900
- `function describeGate(gate: FollowupGateDiagnosticsDto): string` — function, line 908
- `const sig = gate.decisiveSignal` — const, line 909
- `const signalText = sig ? describeSignal(sig) : gate.decisiveReason.replace(/_/g, " ")` — const, line 910
- `const scoreSuffix = typeof gate.gateScore === "number" && sig?.name !== "gate_score" ? ` · score $` — const, line 913
- `const base = (()` — const, line 918
- `const trigger = gate.triggeredReasons.find((r)` — const, line 928
- `const trigText = trigger ? trigger.replace(/_/g, " ") : "trigger"` — const, line 929
- `const v = gateNum(sig.value)` — const, line 939
- `function interventionReasons(actions: string[]): string[]` — function, line 948
- `const reasons = actions .map((action)` — const, line 949
- `function formatInterventionAction(action: string): string` — function, line 960
- `function fmtTimestamp(seconds: number): string` — function, line 972
- `const total = Math.max(0, Math.floor(seconds))` — const, line 973
- `const h = Math.floor(total / 3600)` — const, line 974
- `const m = Math.floor((total % 3600) / 60)` — const, line 975
- `const s = total % 60` — const, line 976
- `const mm = h > 0 ? String(m).padStart(2, "0") : String(m)` — const, line 977
- `function timeRangeLabel(video:` — function, line 981
- `function SourceRefCard(` — function, line 987
- `const video = sourceRef.video` — const, line 995
- `const openExternal = async (url: string)` — const, line 997
- `const externalVideoUrl = video ? `https://www.youtube.com/watch?v=$` — const, line 1006
- `const embedUrl = video ? `https://www.youtube-nocookie.com/embed/$` — const, line 1011
- `function SourceReviewPanel(` — function, line 1080
- `const refs = (f.sourceRefs ?? []).filter((ref)` — const, line 1088
- `const missed = f.rubricScore < f.maxPoints` — const, line 1091
- `function statementPairCopy(m: MatchedMisconceptionDto): string` — function, line 1150
- `const correction = m.correctionStatement.trim()` — const, line 1151
- `const x = m.targetFacet?.trim()` — const, line 1152
- `const y = m.confusedWithFacet?.trim()` — const, line 1153
- `const head = x && y ? `Your last answer was consistent with confusing $` — const, line 1154
- `function MisconceptionStatementCard(` — function, line 1161
- `const claim: ClaimCandidateDto = useMemo( ()` — const, line 1176
- `type RegradeReceipt =` — type, line 1217
- `function RegradeLedgerCard(` — function, line 1219
- `const claim: ClaimCandidateDto = useMemo( ()` — const, line 1233
- `const PROVISIONAL_PENDING_CLARIFICATION = "provisional_pending_clarification"` — const, line 1263
- `const CLARIFICATION_REASON_COPY: Record<string, string> =` — const, line 1267
- `function clarificationOutcomeCopy(result: AnswerGradingClarificationResultDto): string` — function, line 1275
- `function ClarificationCard(` — function, line 1287
- `const visitId = useRef(mintVisitId()).current` — const, line 1434
- `const errorInputRef = useRef<HTMLInputElement>(null)` — const, line 1446
- `const noteTitleRef = useRef<HTMLInputElement>(null)` — const, line 1454
- `const noteBodyRef = useRef<HTMLTextAreaElement>(null)` — const, line 1455
- `const suggestions = useMemo<CandidateErrorTypeDto[]>(()` — const, line 1457
- `const all = item?.candidateErrorTypes ?? []` — const, line 1458
- `const q = errorTypeInput.trim().toLowerCase()` — const, line 1459
- `const filtered = q ? all.filter((e)` — const, line 1460
- `let cancelled = false` — let, line 1467
- `let cancelled = false` — let, line 1503
- `const handleAnswerClarification = async ()` — const, line 1522
- `const answer = clarificationAnswer.trim()` — const, line 1523
- `const result = await api.answerGradingClarification(feedback.attemptId, answer)` — const, line 1527
- `const handleSkipClarification = ()` — const, line 1547
- `const applyRepairStatus = useCallback( (next: CausalRepairStatusDto)` — const, line 1559
- `const repairCaseId = useMemo(()` — const, line 1571
- `const causal = feedback?.causalFeedback` — const, line 1572
- `const need = causal?.probeNeed` — const, line 1573
- `let cancelled = false` — let, line 1590
- `const inspectIds = feedback ? uniqueIds([ feedback.attemptId, feedback.practiceItemId, feedback.learningObjectId, ...feedback.errorAttributions.map((event)` — const, line 1625
- `const practiceItemIds = feedback ? uniqueIds([feedback.practiceItemId]) : []` — const, line 1634
- `const handleRegrade = async ()` — const, line 1649
- `const before =` — const, line 1652
- `const updated = await api.triggerRegrade(feedback.attemptId)` — const, line 1654
- `const handleTriggerFollowup = async ()` — const, line 1669
- `const updated = await api.triggerFollowup(feedback.attemptId)` — const, line 1673
- `const handlePrimedRetry = async ()` — const, line 1686
- `const result = await api.startPrimedRetry(feedback.attemptId)` — const, line 1690
- `const handleGuidedRedo = async ()` — const, line 1708
- `const redo = await api.startGuidedRedo(feedback.attemptId)` — const, line 1712
- `const handleRateFollowup = async (useful: boolean)` — const, line 1724
- `const updated = await api.rateFollowup(feedback.attemptId, useful)` — const, line 1728
- `const handleElicitingResponse = async (suggestionIndex: number, responseMd: string)` — const, line 1743
- `const result = await api.submitElicitingResponse(` — const, line 1747
- `const doAddError = async (errorType: string, severity?: number)` — const, line 1764
- `const updated = await api.addErrorEvent(feedback.attemptId, errorType.trim(), severity)` — const, line 1772
- `const handleAddError = ()` — const, line 1783
- `const sel = selectedSuggestionIdx >= 0 ? suggestions[selectedSuggestionIdx] : null` — const, line 1784
- `const handleUnresolvedCauseReport = async ( factorId: string, response: UnresolvedCauseSelfReportResponse, candidateIndex?: number | null, )` — const, line 1788
- `const resetNote = ()` — const, line 1805
- `const openNoteCapture = ()` — const, line 1811
- `const doSaveNote = async ()` — const, line 1817
- `const title = noteTitle.trim()` — const, line 1819
- `const body = noteBody.trim()` — const, line 1820
- `const subjectId = item?.subject ?? item?.subjects?.[0] ?? null` — const, line 1825
- `const stamp = new Date().toISOString().replace(/[-:T.]/g, "").slice(0, 14)` — const, line 1830
- `const noteId = `$` — const, line 1831
- `const result = await api.addNote(` — const, line 1834
- `const onKey = (event: KeyboardEvent)` — const, line 1853
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 1854
- `const f = feedback` — const, line 1917
- `const subject = item?.subject ?? item?.subjects?.[0] ?? null` — const, line 1918
- `const tau = f.surprise.followupThresholdNats ?? algoConfig().tauFollowupNats` — const, line 1920
- `const interventionNeed = f.interventionNeed` — const, line 1921
- `const elicitingIndex = f.repairSuggestions.findIndex((s)` — const, line 1925
- `const elicitingSuggestion = elicitingIndex >= 0 ? f.repairSuggestions[elicitingIndex] : null` — const, line 1926
- `const matchedMisconception = f.matchedMisconception && f.matchedMisconception.correctionStatement?.trim() ? f.matchedMisconception : null` — const, line 1930
- `const receipt: RegradeReceipt | null = regradeReceipt ?? (f.regrade ?` — const, line 2253
- `const s = suggestions[selectedSuggestionIdx]` — const, line 2500
- `function uniqueIds(values: Array<string | null | undefined>): string[]` — function, line 2622

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `FeedbackScreen`; references `FeedbackScreen`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AnswerGradingClarificationResultDto`, `AttemptTraceDto`, `AttemptTraceEvidenceDto`, `CandidateErrorTypeDto`, `CausalRepairStatusDto`, `ClaimCandidateDto`, `ColdCheckResultDto`, `CriterionEvidenceRowDto`, `ElicitingResponseResultDto`, `ErrorEventDto`, `FeedbackBundle`, `FollowupGateDiagnosticsDto`, `FollowupGateSignalDto`, `GradingClarificationDto`, `GuidedRedoDto`, `MasteryDto`, `MasteryStepDto`, `MatchedMisconceptionDto`, `PracticeItemDetail`, `RepairSuggestionDto`, `ResolvedSourceRefDto`, `UnresolvedCauseSelfReportResponse`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `algoConfig`, `masteryTone`
- [[Reference/Desktop/TypeScript/components/CardControls|src/components/CardControls.tsx]] — import-or-re-export; imports `CardControls`, `ProbeRemintAction`
- [[Reference/Desktop/TypeScript/components/CausalAttribution|src/components/CausalAttribution.tsx]] — import-or-re-export; imports `CausalFeedbackPanel`, `formatCausalTarget`, `formatDivergenceAnchor`, `useCausalRepairActions`
- [[Reference/Desktop/TypeScript/components/ClaimSurface|src/components/ClaimSurface.tsx]] — import-or-re-export; imports `ClaimSurface`, `mintVisitId`
- [[Reference/Desktop/TypeScript/components/KnowledgeModel|src/components/KnowledgeModel.tsx]] — import-or-re-export; imports `AttemptTraceView`, `UnresolvedCauseCard`
- [[Reference/Desktop/TypeScript/components/RepairAffordances|src/components/RepairAffordances.tsx]] — import-or-re-export; imports `CommonRepairCard`, `GuidedRedoAffordance`
- [[Reference/Desktop/TypeScript/components/RepairTrace|src/components/RepairTrace.tsx]] — import-or-re-export; imports `RepairTraceBlocks`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `modePillColor`
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export; imports `EntityLink`, `KeyBar`, `Pill`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `@tauri-apps/plugin-opener`, `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_causal_repair_sidecar_rpcs.py](../../../../../../tests/test_causal_repair_sidecar_rpcs.py) — cross-boundary name contract: references uniquely owned exported name `FeedbackScreen`; it does **not** directly execute this source module.
- [tests/test_e2e_tui.py](../../../../../../tests/test_e2e_tui.py) — cross-boundary name contract: references uniquely owned exported name `FeedbackScreen`; it does **not** directly execute this source module.
- [tests/test_probe_block_end.py](../../../../../../tests/test_probe_block_end.py) — cross-boundary name contract: references uniquely owned exported name `FeedbackScreen`; it does **not** directly execute this source module.
- [tests/test_provider_resolution_parity.py](../../../../../../tests/test_provider_resolution_parity.py) — cross-boundary name contract: references uniquely owned exported name `FeedbackScreen`; it does **not** directly execute this source module.
- [tests/test_surfaced_belief_corrections.py](../../../../../../tests/test_surfaced_belief_corrections.py) — cross-boundary name contract: references uniquely owned exported name `FeedbackScreen`; it does **not** directly execute this source module.
- [tests/test_tui_feedback.py](../../../../../../tests/test_tui_feedback.py) — cross-boundary name contract: references uniquely owned exported name `FeedbackScreen`; it does **not** directly execute this source module.
- [tests/test_tui_practice.py](../../../../../../tests/test_tui_practice.py) — cross-boundary name contract: references uniquely owned exported name `FeedbackScreen`; it does **not** directly execute this source module.
- [tests/test_review_log.py](../../../../../../tests/test_review_log.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_learner_review_system_entries.py](../../../../../../tests/test_learner_review_system_entries.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_forecast_ledger.py](../../../../../../tests/test_forecast_ledger.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/FeedbackScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/FeedbackScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
