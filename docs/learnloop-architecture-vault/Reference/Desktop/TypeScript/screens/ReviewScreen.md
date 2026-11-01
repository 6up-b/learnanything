---
title: "Desktop module · src/screens/ReviewScreen.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.ReviewScreen"
language: "TypeScript"
area: "TypeScript/screens"
source_path: "apps/learnloop-tauri/src/screens/ReviewScreen.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/ReviewScreen.tsx"
source_commit: "c94882abe7a8f5a7cde491603d6abba8a4c0e2db"
source_commit_timestamp: "2026-10-22T16:58:30-04:00"
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

# `src/screens/ReviewScreen.tsx`

Area: [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `ReviewScreen` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/ReviewScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/ReviewScreen.tsx) |
| Source lines | 818 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `c94882abe7a8f5a7cde491603d6abba8a4c0e2db` |
| Commit timestamp | `2026-10-22T16:58:30-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReviewScreen|src/screens/ReviewScreen.tsx]]

## Public API

- `export function ReviewScreen(` — function, line 425

## Internal implementation anchors

- `const shortFacet = (facetId: string): string` — const, line 22
- `const ATTEMPT_OUTCOME_HUES_ENABLED = true` — const, line 25
- `const ATTEMPT_OUTCOME_HUE_MIX = 0.6` — const, line 26
- `function attemptOutcomeTone(attempt: KnowledgeHistoryAttempt): string` — function, line 30
- `const mix = (to: string)` — const, line 32
- `function fmtDate(iso: string | null): string` — function, line 47
- `const d = new Date(iso)` — const, line 49
- `function EventBadge(` — function, line 59
- `function FacetRef(` — function, line 68
- `function changelogFacetToneLabel(entry: ReviewChangelogEntryDto): string` — function, line 100
- `const WITHDRAWAL_REASON_LABEL: Record<BeliefWithdrawalReason, string> =` — const, line 111
- `function attemptsBySession( changelog: ReviewChangelogEntryDto[], attempts: KnowledgeHistoryAttempt[] ): Record<string, KnowledgeHistoryAttempt[]>` — function, line 118
- `const sessions = changelog .filter((entry)` — const, line 122
- `const orderedAttempts = attempts .slice() .sort((left, right)` — const, line 126
- `const grouped: Record<string, KnowledgeHistoryAttempt[]> =` — const, line 129
- `let previousEnd = Number.NEGATIVE_INFINITY` — let, line 130
- `const end = new Date(session.at).getTime()` — const, line 133
- `const candidates = orderedAttempts.filter((attempt)` — const, line 134
- `const at = new Date(attempt.t).getTime()` — const, line 135
- `function ChangelogEntry(` — function, line 146
- `const isRecalibration = entry.kind === "recalibration"` — const, line 157
- `const isRegrade = entry.kind === "regrade"` — const, line 158
- `const isWithdrawal = entry.kind === "belief_withdrawn"` — const, line 159
- `const moved = entry.predictionsMoved` — const, line 160
- `const touched = entry.misconceptionsTouched` — const, line 161
- `const badges: Array<` — const, line 162
- `const direction = entry.direction ?? "same"` — const, line 188
- `const markerColor = isRecalibration ? COLOR.textFaint : isRegrade ? COLOR.amber : isWithdrawal ? COLOR.red : COLOR.cyan` — const, line 199
- `const facetTone = COLOR.textDim` — const, line 206
- `function statementPairText(hypothesis: WorkingHypothesisDto): string` — function, line 331
- `const correction = hypothesis.correctionStatement.trim()` — const, line 332
- `function WorkingHypothesis(` — function, line 341
- `const claim: ClaimCandidateDto = useMemo(()` — const, line 354
- `const lastTransition = hypothesis.history[hypothesis.history.length - 1] ?? null` — const, line 365
- `const returned = hypothesis.history.some((item)` — const, line 366
- `function InlineStat(` — function, line 403
- `function SectionIntro(` — function, line 412
- `const visitId = useRef<string>(mintVisitId())` — const, line 443
- `let alive = true` — let, line 446
- `const message = error instanceof Error ? error.message : String(error)` — const, line 453
- `const onKeyDown = (event: KeyboardEvent)` — const, line 463
- `let alive = true` — let, line 482
- `const hypotheses = (log?.workingHypotheses ?? []).filter( (hypothesis)` — const, line 497
- `const changelog = log?.changelog ?? []` — const, line 500
- `const movementUp = changelog.reduce((sum, entry)` — const, line 501
- `const movementDown = changelog.reduce((sum, entry)` — const, line 502
- `const bodyStyle: CSSProperties =` — const, line 653
- `const heroStyle: CSSProperties =` — const, line 659
- `const summaryLineStyle: CSSProperties =` — const, line 665
- `const summaryContextStyle: CSSProperties =` — const, line 674
- `const summarySeparatorStyle: CSSProperties =` — const, line 681
- `const heroTitleStyle: CSSProperties =` — const, line 686
- `const heroCopyStyle: CSSProperties =` — const, line 695
- `const contentGridStyle: CSSProperties =` — const, line 703
- `const ledgerSectionStyle: CSSProperties =` — const, line 707
- `const eyebrowStyle: CSSProperties =` — const, line 712
- `const eyebrowInlineStyle: CSSProperties =` — const, line 719
- `const sectionTitleStyle: CSSProperties =` — const, line 726
- `const hypothesisStyle: CSSProperties =` — const, line 734
- `const repairButtonStyle: CSSProperties =` — const, line 742
- `const facetLinkStyle: CSSProperties =` — const, line 754
- `const attemptLinkStyle: CSSProperties =` — const, line 764
- `const timelineStyle: CSSProperties =` — const, line 774
- `const historyRevealStyle: CSSProperties =` — const, line 779
- `const timelineEntryStyle: CSSProperties =` — const, line 795
- `const timelineMarkerStyle: CSSProperties =` — const, line 800
- `const emptyStateStyle: CSSProperties =` — const, line 811

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `ReviewScreen`; references `ReviewScreen`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `BeliefWithdrawalReason`, `ClaimCandidateDto`, `KnowledgeHistoryAttempt`, `ReviewChangelogEntryDto`, `ReviewLogDto`, `WorkingHypothesisDto`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/ClaimSurface|src/components/ClaimSurface.tsx]] — import-or-re-export; imports `ClaimSurface`, `mintVisitId`
- [[Reference/Desktop/TypeScript/components/CommandOverlayFrame|src/components/CommandOverlayFrame.tsx]] — import-or-re-export; imports `CommandOverlayFrame`
- [[Reference/Desktop/TypeScript/components/KnowledgeModel|src/components/KnowledgeModel.tsx]] — import-or-re-export; imports `FacetEvidenceDrawer`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `Dim`, `FONT_MONO`, `Faint`, `Pill`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_review_log.py](../../../../../../tests/test_review_log.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_learner_review_system_entries.py](../../../../../../tests/test_learner_review_system_entries.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_forecast_ledger.py](../../../../../../tests/test_forecast_ledger.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/ReviewScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/ReviewScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
