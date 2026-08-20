---
title: "Desktop module · src/components/AdjudicationOverlay.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.AdjudicationOverlay"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/AdjudicationOverlay.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/AdjudicationOverlay.tsx"
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

# `src/components/AdjudicationOverlay.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `AdjudicationOverlay` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/AdjudicationOverlay.tsx](../../../../../../apps/learnloop-tauri/src/components/AdjudicationOverlay.tsx) |
| Source lines | 632 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/AdjudicationOverlay|src/components/AdjudicationOverlay.tsx]]

## Public API

- `export function AdjudicationOverlay(` — function, line 106

## Internal implementation anchors

- `const STRATUM_LABEL: Record<string, string> =` — const, line 33
- `const VERDICT_KEY: Record<AdjudicationVerdict, string> =` — const, line 42
- `const VERDICT_LABEL: Record<AdjudicationVerdict, string> =` — const, line 51
- `const VERDICT_GLOSS: Record<AdjudicationVerdict, string> =` — const, line 60
- `const ANCHOR_FORM_VERDICTS: AdjudicationVerdict[] = ["wrong_anchor", "should_not_have_abstained"]` — const, line 73
- `const REPAIR_FORM_VERDICTS: AdjudicationVerdict[] = ["wrong_anchor", "wrong_repair"]` — const, line 74
- `const ANCHOR_KINDS = ["span", "between_spans", "missing_required_step", "whole_answer", "none"] as const` — const, line 76
- `type Draft =` — type, line 78
- `function newDraft(verdict: AdjudicationVerdict, kase: AdjudicationCaseDto): Draft` — function, line 89
- `function rate(value: number | null | undefined): string` — function, line 102
- `const refreshBoard = useCallback(()` — const, line 124
- `let alive = true` — let, line 132
- `const message = errorMessage(error, "Could not load the adjudication queue.")` — const, line 140
- `const cases = queue?.cases ?? []` — const, line 150
- `const kase: AdjudicationCaseDto | null = cases[index] ?? null` — const, line 151
- `const strata = useMemo( ()` — const, line 153
- `const advance = useCallback( (drop: boolean)` — const, line 158
- `const submit = useCallback( (input: AdjudicationRecordInput)` — const, line 180
- `const message = errorMessage(error, "Could not record this adjudication.")` — const, line 196
- `const chooseVerdict = useCallback( (verdict: AdjudicationVerdict)` — const, line 205
- `function submitDraft()` — function, line 221
- `const anchorRequired = ANCHOR_FORM_VERDICTS.includes(draft.verdict)` — const, line 223
- `function onKeyDown(event: React.KeyboardEvent<HTMLElement>)` — function, line 249
- `const key = event.key.toLowerCase()` — const, line 263
- `const match = kase.allowedVerdicts.find((verdict)` — const, line 268
- `const overall = board?.overall` — const, line 275
- `const badge = overall ? ( <Pill color=` — const, line 276
- `const verdictButtonStyle: React.CSSProperties =` — const, line 612
- `const inputStyle: React.CSSProperties =` — const, line 623

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `AdjudicationOverlay`; references `AdjudicationOverlay`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AdjudicationCaseDto`, `AdjudicationOutcomeDto`, `AdjudicationQueueDto`, `AdjudicationRecordInput`, `AdjudicationScoreboardDto`, `AdjudicationVerdict`
- [[Reference/Desktop/TypeScript/app/keyboard|src/app/keyboard.ts]] — import-or-re-export; imports `isTypingTarget`
- [[Reference/Desktop/TypeScript/components/CommandOverlayFrame|src/components/CommandOverlayFrame.tsx]] — import-or-re-export; imports `CommandOverlayFrame`, `commandOverlayActionStyle`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `Card`, `Dim`, `Divider`, `FONT_MONO`, `Faint`, `Pill`, `SectionHeader`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
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

1. Modify [apps/learnloop-tauri/src/components/AdjudicationOverlay.tsx](../../../../../../apps/learnloop-tauri/src/components/AdjudicationOverlay.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
