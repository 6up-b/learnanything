---
title: "Desktop module · src/screens/workbench/helpModel.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.workbench.helpModel"
language: "TypeScript"
area: "TypeScript/screens/workbench"
source_path: "apps/learnloop-tauri/src/screens/workbench/helpModel.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/workbench/helpModel.ts"
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

# `src/screens/workbench/helpModel.ts`

Area: [[Reference/Desktop/TypeScript/screens/workbench/_area|TypeScript/screens/workbench]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `HELP_COPY`, `STYLE_OPTIONS`, `WORKBENCH_SHORTCUTS`, `WHERE_THIS_GOES` and related exports within the desktop's TypeScript/screens/workbench ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/workbench/helpModel.ts](../../../../../../../apps/learnloop-tauri/src/screens/workbench/helpModel.ts) |
| Source lines | 240 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/workbench/_area|TypeScript/screens/workbench]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/workbench/Workbench|src/screens/workbench/Workbench.tsx]] → [[Reference/Desktop/TypeScript/screens/workbench/helpModel|src/screens/workbench/helpModel.ts]]

## Public API

- `export const HELP_COPY =` — const, line 9
- `export const STYLE_OPTIONS = [` — const, line 50
- `export const WORKBENCH_SHORTCUTS = [` — const, line 57
- `export const WHERE_THIS_GOES =` — const, line 66
- `export type WhereThisGoesBox = keyof typeof WHERE_THIS_GOES` — type, line 80
- `export const DEFAULT_RUNGS: LadderRungDto[] = [` — const, line 83
- `export function suggestedLine(suggestion: HelpSuggestionDto | null): string | null` — function, line 93
- `export interface LadderChoice` — interface, line 101
- `export function chooseKey(state: LadderChoice, key: string): LadderChoice | "take" | "close" | null` — function, line 105
- `export function verdictFor(check: CheckViewDto | null, chainId: string)` — function, line 115
- `export const CHECKED_TEXT_CHARS = 2000` — const, line 120
- `export function textFingerprint(text: string): string` — function, line 130
- `export function withLocalEdits( check: CheckViewDto | null, steps: readonly` — function, line 156
- `export function verdictMark(verdict:` — function, line 185
- `export function claimLine(claim:` — function, line 200
- `export function staleLine(check: CheckViewDto | null): string | null` — function, line 210
- `export function hintLabel(hint: Pick<WorkbenchHintViewDto, "labels" | "level" | "stepLine" | "kind">): string` — function, line 226
- `export const FORBIDDEN_WORDING = ["you don't understand", "you struggle", "weak"] as const` — const, line 240

## Internal implementation anchors

- `const form = [suggestion.kindLabel, suggestion.horizonLabel].filter(Boolean).join(", ")` — const, line 95
- `const FNV_OFFSET = 0xcbf29ce484222325n` — const, line 122
- `const FNV_PRIME = 0x100000001b3n` — const, line 123
- `const MASK_64 = 0xffffffffffffffffn` — const, line 124
- `const fingerprints = new Map<string, string>()` — const, line 125
- `const known = fingerprints.get(text)` — const, line 131
- `let value = FNV_OFFSET` — let, line 133
- `const out = `fnv1a64:$` — const, line 138
- `function sameAsChecked(body: string, verdict:` — function, line 148
- `const bodies = new Map<string, string>()` — const, line 161
- `let moved = false` — let, line 163
- `const changed = new Set(check.changedSteps)` — const, line 164
- `const verdicts = check.verdicts.map((verdict)` — const, line 165
- `const body = bodies.get(verdict.chainId)` — const, line 167
- `const edited = body === undefined || !sameAsChecked(body, verdict)` — const, line 168
- `const CHECKED_METHODS = new Set(["checked", "checked_numerically"])` — const, line 178
- `const MODEL_LABEL = "model's reading, not checked"` — const, line 179
- `const mark = verdict.verdict === "valid" ? "≈" : verdict.verdict === "questionable" ? "?" : "·"` — const, line 194
- `const checked = symbolicEnabled === true && CHECKED_METHODS.has(claim.status)` — const, line 202
- `const mark = checked ? "✓" : "≈"` — const, line 203
- `const label = checked ? claim.label : claim.status === "model" || CHECKED_METHODS.has(claim.status) ? MODEL_LABEL : claim.label` — const, line 204
- `const at = check.checkedAt ? new Date(check.checkedAt) : null` — const, line 212
- `const time = at && !Number.isNaN(at.getTime()) ? `$` — const, line 213
- `const changed = check.changedSteps.length ? check.changedSteps.length === 1 ? `step $` — const, line 216
- `const parts: string[] = []` — const, line 227
- `const labels = hint.labels ??` — const, line 228

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/workbench/BookPassage|src/screens/workbench/BookPassage.tsx]] — import-or-re-export: `HELP_COPY`; references `HELP_COPY`
- [[Reference/Desktop/TypeScript/screens/workbench/CheckColumn|src/screens/workbench/CheckColumn.tsx]] — import-or-re-export: `HELP_COPY`, `staleLine`, `verdictMark`; references `HELP_COPY`, `staleLine`, `verdictMark`
- [[Reference/Desktop/TypeScript/screens/workbench/HelpLadder|src/screens/workbench/HelpLadder.tsx]] — import-or-re-export: `HELP_COPY`, `chooseKey`, `suggestedLine`; references `HELP_COPY`, `chooseKey`, `suggestedLine`
- [[Reference/Desktop/TypeScript/screens/workbench/HelpStyleControl|src/screens/workbench/HelpStyleControl.tsx]] — import-or-re-export: `HELP_COPY`, `STYLE_OPTIONS`; references `HELP_COPY`, `STYLE_OPTIONS`
- [[Reference/Desktop/TypeScript/screens/workbench/StepHints|src/screens/workbench/StepHints.tsx]] — import-or-re-export: `HELP_COPY`, `WORKBENCH_SHORTCUTS`, `claimLine`, `hintLabel`; references `HELP_COPY`, `WORKBENCH_SHORTCUTS`, `claimLine`, `hintLabel`
- [[Reference/Desktop/TypeScript/screens/workbench/WhereThisGoes|src/screens/workbench/WhereThisGoes.tsx]] — import-or-re-export: `HELP_COPY`, `WHERE_THIS_GOES`, `WhereThisGoesBox`; references `HELP_COPY`, `WHERE_THIS_GOES`, `WhereThisGoesBox`
- [[Reference/Desktop/TypeScript/screens/workbench/Workbench|src/screens/workbench/Workbench.tsx]] — import-or-re-export: `HELP_COPY`, `verdictFor`, `withLocalEdits`; references `HELP_COPY`, `verdictFor`, `withLocalEdits`
- [[Reference/Desktop/TypeScript/screens/workbench/useWorkbenchHelp|src/screens/workbench/useWorkbenchHelp.ts]] — import-or-re-export: `DEFAULT_RUNGS`; references `DEFAULT_RUNGS`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CheckViewDto`, `HelpSuggestionDto`, `LadderRungDto`, `WorkbenchHintViewDto`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/workbench/symbolicOff.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/workbench/symbolicOff.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/workbench/rw2cFixRound2.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/workbench/rw2cFixRound2.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/workbench/reviewFixes.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/workbench/reviewFixes.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/workbench/ownerCapture1025.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/workbench/ownerCapture1025.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/workbench/fingerprint.test.ts](../../../../../../../apps/learnloop-tauri/src/screens/workbench/fingerprint.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/workbench/HelpLadder.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/workbench/HelpLadder.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/workbench/BookPassage.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/workbench/BookPassage.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_workbench_text_gaps.py](../../../../../../../tests/test_workbench_text_gaps.py) — direct source contract: references the exact source path.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/workbench/helpModel.ts](../../../../../../../apps/learnloop-tauri/src/screens/workbench/helpModel.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
