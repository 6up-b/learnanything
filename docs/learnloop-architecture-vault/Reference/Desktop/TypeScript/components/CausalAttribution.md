---
title: "Desktop module · src/components/CausalAttribution.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.CausalAttribution"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/CausalAttribution.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/CausalAttribution.tsx"
source_commit: "d0f25b2598a77dcc5236118dad9e1af2422d8682"
source_commit_timestamp: "2026-08-16T20:45:34-04:00"
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

# `src/components/CausalAttribution.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `CausalAttribution` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/CausalAttribution.tsx](../../../../../../apps/learnloop-tauri/src/components/CausalAttribution.tsx) |
| Source lines | 1286 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `d0f25b2598a77dcc5236118dad9e1af2422d8682` |
| Commit timestamp | `2026-08-16T20:45:34-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/InspectorOverlay|src/components/InspectorOverlay.tsx]] → [[Reference/Desktop/TypeScript/components/CausalAttribution|src/components/CausalAttribution.tsx]]

## Public API

- `export function formatCausalTarget(ref: CausalTargetRefDto | null | undefined): string` — function, line 38
- `export function formatDivergenceAnchor( anchor: CausalDivergenceAnchorDto | null | undefined, ): string` — function, line 53
- `export function CausalRepairStatusPanel(` — function, line 374
- `export function useCausalRepairActions(` — function, line 490
- `export function CausalFeedbackPanel(` — function, line 569
- `export function CausalEpisodeInspector(` — function, line 910

## Internal implementation anchors

- `const CONTEST_LABELS: Partial<Record<UnresolvedCauseSelfReportResponse, string>> =` — const, line 20
- `const ANCHOR_LABELS: Record<string, string> =` — const, line 28
- `function humanize(value: string | null | undefined): string` — function, line 34
- `const kind = humanize(typeof anchor.anchorKind === "string" ? anchor.anchorKind : null)` — const, line 57
- `const quote = typeof anchor.quote === "string" && anchor.quote.trim() ? `“$` — const, line 58
- `const checkpoint = typeof anchor.checkpointId === "string" && anchor.checkpointId ? `checkpoint $` — const, line 59
- `const criterion = typeof anchor.criterionId === "string" && anchor.criterionId ? `criterion $` — const, line 63
- `function Panel(` — function, line 70
- `const border =` — const, line 79
- `function SmallLabel(` — function, line 105
- `function GroupHeader(` — function, line 128
- `function AuditGroup(` — function, line 148
- `function TraceView(` — function, line 157
- `function splitDivergence( before: string, after: string, ):` — function, line 178
- `const limit = Math.min(before.length, after.length)` — const, line 182
- `let common = 0` — let, line 183
- `const newline = after.lastIndexOf("\n", common)` — const, line 188
- `const space = after.lastIndexOf(" ", common)` — const, line 189
- `const cut = Math.min(newline >= 0 ? newline + 1 : space > 0 ? space + 1 : 0, common)` — const, line 193
- `function PanelRow(` — function, line 201
- `function PanelFooter(` — function, line 222
- `function DiffBlock(` — function, line 245
- `function MinimalRepairDiff(` — function, line 270
- `const REPAIR_STATUS_TONE: Record< CausalRepairStatusState, "cyan" | "green" | "amber" | "red" | "slate" > =` — const, line 332
- `const REPAIR_STATUS_PILL: Record<CausalRepairStatusState, string> =` — const, line 343
- `const REPAIR_STATUS_HEADING: Record<CausalRepairStatusState, string> =` — const, line 351
- `const PROBE_OFFER_COPY: Record<string, string> =` — const, line 361
- `function probeOfferCopy(reason: string): string` — function, line 370
- `const tone = REPAIR_STATUS_TONE[status.status] ?? "slate"` — const, line 388
- `const busy = pendingActionId != null` — const, line 389
- `const pendingChecks = status.pendingMachineCheckIds.length` — const, line 390
- `const primary = action.id === "take_quick_check"` — const, line 450
- `const color = primary ? COLOR.cyan : COLOR.amber` — const, line 451
- `const runAction = useCallback( (actionId: CausalRepairActionId, status: CausalRepairStatusDto)` — const, line 505
- `const factorId = status.factorId` — const, line 507
- `const refresh = ()` — const, line 511
- `const done = ()` — const, line 515
- `const fail = (error: unknown)` — const, line 516
- `const offer = result.offer` — const, line 529
- `const graderFeedback = feedback.unverified.filter( (claim)` — const, line 597
- `const nonHypothesisUnverified = feedback.unverified.filter( (claim)` — const, line 600
- `const correctionRemainsUnverified = graderFeedback.length > 0 && feedback.verifiedCorrection === null` — const, line 603
- `const hasUnverifiedClaims = nonHypothesisUnverified.length > 0 || feedback.causalHypotheses.length > 0 || correctionRemainsUnverified` — const, line 605
- `const canContest = Boolean(feedback.contestAction.available && onContest)` — const, line 609
- `const statement = claim.statement?.trim()` — const, line 628
- `const statement = claim.statement?.trim()` — const, line 733
- `function AuditRow(` — function, line 877
- `function observedEvidence(hypothesis: CausalHypothesisDto): string | null` — function, line 895
- `const value = hypothesis.evidence?.observedEvidence` — const, line 896
- `function recordString(record: Record<string, unknown> | null, key: string): string | null` — function, line 900
- `const value = record?.[key]` — const, line 901
- `function recordNumber(record: Record<string, unknown> | null, key: string): number | null` — function, line 905
- `const value = record?.[key]` — const, line 906
- `const receipt = episode?.receipt` — const, line 911
- `const hypothesisById = new Map( (episode?.hypotheses ?? []).map((hypothesis)` — const, line 920
- `const axesById = new Map(receipt.attributionAxes.map((axis)` — const, line 923
- `const orderedRefs = [...receipt.hypotheses].sort((left, right)` — const, line 924
- `const leftRank = receipt.ordinalRanking.indexOf(left.id)` — const, line 925
- `const rightRank = receipt.ordinalRanking.indexOf(right.id)` — const, line 926
- `const selected = receipt.repairSelection.selected` — const, line 930
- `const legacyTaxonomy = receipt.mechanismTaxonomy ??` — const, line 931
- `const taxonomyClusters = Array.isArray(legacyTaxonomy.clusters) ? legacyTaxonomy.clusters : []` — const, line 932
- `const taxonomyAbstained = Array.isArray(legacyTaxonomy.abstained) ? legacyTaxonomy.abstained : []` — const, line 935
- `const tone = criterion.fullCredit ? COLOR.green : criterion.assessable ? COLOR.red : COLOR.textFaint` — const, line 960
- `const mark = criterion.fullCredit ? "✓" : criterion.assessable ? "✗" : "·"` — const, line 961
- `const hypothesis = hypothesisById.get(ref.id)` — const, line 1000
- `const axis = axesById.get(ref.id)` — const, line 1002
- `const support = receipt.supportScores[ref.id]` — const, line 1003
- `const evidence = observedEvidence(hypothesis)` — const, line 1004
- `const errorType = recordString(hypothesis.evidence, "errorType")` — const, line 1005
- `const severity = recordNumber(hypothesis.evidence, "severity")` — const, line 1006
- `const observedSignature = recordString(hypothesis.evidence, "observedSignature")` — const, line 1007
- `const preregisteredSignature = recordString( hypothesis.evidence, "preregisteredSignature", )` — const, line 1008
- `const applicabilitySurface = recordString(hypothesis.applicability, "surfaceFamily")` — const, line 1012
- `const criterion = typeof claim.criterionId === "string" ? claim.criterionId : null` — const, line 1063
- `const must = typeof claim.must === "string" ? humanize(claim.must) : null` — const, line 1065
- `const cluster = raw && typeof raw === "object" && !Array.isArray(raw) ? raw as Record<string, unknown> :` — const, line 1233
- `const group = raw && typeof raw === "object" && !Array.isArray(raw) ? raw as Record<string, unknown> :` — const, line 1252
- `function AuditMetric(` — function, line 1279

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/InspectorOverlay|src/components/InspectorOverlay.tsx]] — import-or-re-export: `CausalEpisodeInspector`, `formatCausalTarget`, `formatDivergenceAnchor`; references `CausalEpisodeInspector`, `formatCausalTarget`, `formatDivergenceAnchor`
- [[Reference/Desktop/TypeScript/components/ProbeBlockResult|src/components/ProbeBlockResult.tsx]] — import-or-re-export: `CausalFeedbackPanel`; references `CausalFeedbackPanel`
- [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] — import-or-re-export: `CausalFeedbackPanel`, `formatCausalTarget`, `formatDivergenceAnchor`, `useCausalRepairActions`; references `CausalFeedbackPanel`, `formatCausalTarget`, `formatDivergenceAnchor`, `useCausalRepairActions`
- [[Reference/Desktop/TypeScript/screens/RepairScreen|src/screens/RepairScreen.tsx]] — import-or-re-export: `CausalRepairStatusPanel`, `useCausalRepairActions`; references `CausalRepairStatusPanel`, `useCausalRepairActions`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CausalDivergenceAnchorDto`, `CausalEpisodeDto`, `CausalFeedbackDto`, `CausalHypothesisDto`, `CausalProbeOfferDto`, `CausalRepairActionId`, `CausalRepairStatusDto`, `CausalRepairStatusState`, `CausalTargetRefDto`, `RepairedTraceDto`, `UnresolvedCauseSelfReportResponse`
- [[Reference/Desktop/TypeScript/components/RepairTrace|src/components/RepairTrace.tsx]] — import-or-re-export; imports `RepairTraceBlocks`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `BlockBar`, `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `Pill`, `PlainEnglishPanel`, `SectionHeader`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.
- [[Concepts/Diagnosis and Remediation#Episode lifecycle|diagnosis episode lifecycle]] — owns diagnostic and repair policy.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_causal_repair_sidecar_rpcs.py](../../../../../../tests/test_causal_repair_sidecar_rpcs.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_causal_attribution_p0.py](../../../../../../tests/test_causal_attribution_p0.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_diagnosis_adjudication.py](../../../../../../tests/test_diagnosis_adjudication.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_diagnostic_review_policy.py](../../../../../../tests/test_diagnostic_review_policy.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/CausalAttribution.tsx](../../../../../../apps/learnloop-tauri/src/components/CausalAttribution.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
