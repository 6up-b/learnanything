---
title: "Desktop module · src/screens/RepairScreen.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.RepairScreen"
language: "TypeScript"
area: "TypeScript/screens"
source_path: "apps/learnloop-tauri/src/screens/RepairScreen.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/RepairScreen.tsx"
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

# `src/screens/RepairScreen.tsx`

Area: [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `RepairScreen` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/RepairScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/RepairScreen.tsx) |
| Source lines | 676 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/RepairScreen|src/screens/RepairScreen.tsx]]

## Public API

- `export function RepairScreen(` — function, line 114

## Internal implementation anchors

- `const shortFacet = (facetId: string): string` — const, line 38
- `function fmtDate(iso: string | null): string` — function, line 40
- `const d = new Date(iso)` — const, line 42
- `const btn: CSSProperties =` — const, line 47
- `const btnDim: CSSProperties =` — const, line 58
- `const stageBox: CSSProperties =` — const, line 64
- `function PassageCard(` — function, line 72
- `const sv = passage.spanView` — const, line 79
- `const heading = sv.sectionPath.length > 0 ? sv.sectionPath.join(" › ") : sv.blockType` — const, line 80
- `const simple = simplePracticeFeedback()` — const, line 146
- `const report = useCallback( (e: unknown)` — const, line 150
- `const handler = (e: KeyboardEvent)` — const, line 158
- `let alive = true` — let, line 170
- `const episodeId = remediation?.episode?.id ?? null` — const, line 212
- `const prescribe = async ()` — const, line 214
- `const r = await api.prescribeRemediation(episodeId)` — const, line 218
- `const treat = async (): Promise<StartRemediationDto | null>` — const, line 228
- `const r = await api.startRemediationTreatment(episodeId)` — const, line 232
- `const tryOne = async ()` — const, line 246
- `const r = await treat()` — const, line 247
- `const itemId = r.primedItemId ?? r.episode?.primedItemId ?? null` — const, line 249
- `const kase = remediation?.case ?? null` — const, line 254
- `const passages = remediation?.episode?.passagesShown ?? []` — const, line 255
- `const primedItemId = remediation?.primedItemId ?? remediation?.episode?.primedItemId ?? null` — const, line 256
- `const coldItemId = remediation?.coldItemId ?? remediation?.episode?.coldItemId ?? null` — const, line 257
- `const coldUnmeasurableReason = remediation?.coldUnmeasurableReason ?? null` — const, line 258
- `const returned = kase?.history.some((h)` — const, line 259
- `const primary = !episodeId || nothingToTry ? null : !prescribed ?` — const, line 263
- `function plainSectionPath(sectionPath: string[]): string` — function, line 515
- `const titles = sectionPath.filter((part)` — const, line 516
- `function SimpleRepairStep(` — function, line 521
- `const handler = (event: KeyboardEvent)` — const, line 557
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 560
- `const backdrop: CSSProperties =` — const, line 645
- `const panel: CSSProperties =` — const, line 657
- `const header: CSSProperties =` — const, line 669

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `RepairScreen`; references `RepairScreen`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CausalRepairStatusDto`, `SpanViewDto`, `StartRemediationDto`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/app/practiceFeedback|src/app/practiceFeedback.ts]] — import-or-re-export; imports `FIX_MIX_UP_LABEL`, `simplePracticeFeedback`
- [[Reference/Desktop/TypeScript/components/CausalAttribution|src/components/CausalAttribution.tsx]] — import-or-re-export; imports `CausalRepairStatusPanel`, `useCausalRepairActions`
- [[Reference/Desktop/TypeScript/components/OpenInSource|src/components/OpenInSource.tsx]] — import-or-re-export; imports `OpenInSource`
- [[Reference/Desktop/TypeScript/components/PlainParts|src/components/PlainParts.tsx]] — import-or-re-export; imports `DetailsToggle`, `PrimaryAction`, `quietLine`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `Divider`, `FONT_MONO`, `Faint`, `Pill`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.
- [[Concepts/Diagnosis and Remediation#Episode lifecycle|diagnosis episode lifecycle]] — owns diagnostic and repair policy.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/RepairScreen.phase4.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/RepairScreen.phase4.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/RepairOverFeedback.phase4.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/RepairOverFeedback.phase4.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/copy/denyList.phase4.test.tsx](../../../../../../apps/learnloop-tauri/src/copy/denyList.phase4.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_causal_repair_sidecar_rpcs.py](../../../../../../tests/test_causal_repair_sidecar_rpcs.py) — cross-boundary name contract: references uniquely owned exported name `RepairScreen`; it does **not** directly execute this source module.
- [tests/test_causal_attribution_p0.py](../../../../../../tests/test_causal_attribution_p0.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_diagnosis_adjudication.py](../../../../../../tests/test_diagnosis_adjudication.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_diagnostic_review_policy.py](../../../../../../tests/test_diagnostic_review_policy.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/RepairScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/RepairScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
