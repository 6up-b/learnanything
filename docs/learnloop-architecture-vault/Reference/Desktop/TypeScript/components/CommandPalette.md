---
title: "Desktop module · src/components/CommandPalette.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.CommandPalette"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/CommandPalette.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/CommandPalette.tsx"
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

# `src/components/CommandPalette.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `CommandPalette` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/CommandPalette.tsx](../../../../../../apps/learnloop-tauri/src/components/CommandPalette.tsx) |
| Source lines | 945 |
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
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/CommandPalette|src/components/CommandPalette.tsx]]

## Public API

- `export function CommandPalette(` — function, line 668

## Internal implementation anchors

- `const HISTORY_KEY = "learnloop.commandHistory"` — const, line 22
- `type OutputRow = |` — type, line 25
- `type ArgKind = "practice_item" | "concept" | "goal" | "any" | "subject" | "tab" | "url" | "path"` — type, line 43
- `interface ArgSpec` — interface, line 44
- `interface GrammarSpec` — interface, line 48
- `const GRAMMAR: Record<string, GrammarSpec> =` — const, line 54
- `const CLI_DELEGATED_COMMANDS = new Set([ "propose", "proposals", "accept", "reject", "edit-proposal-item", "ingest", "add-subject", "add-note", "generate-practice", "kill-codex", "populate-goal", "generate-diagnostics", "observation-templates", "register-obse…` — const, line 92
- `interface CmdCtx` — interface, line 114
- `type Flags = Record<string, string | true>` — type, line 126
- `async function runCommand(name: string, args: string[], flags: Flags, ctx: CmdCtx, argv: string[]): Promise<OutputRow[]>` — function, line 128
- `const tab = findTab(args[0])` — const, line 146
- `async function runCli(argv: string[]): Promise<OutputRow[]>` — function, line 211
- `const result = await api.runCliCommand(argv)` — const, line 212
- `function cliResultRows(result: CliCommandResult): OutputRow[]` — function, line 216
- `const rows: OutputRow[] = []` — const, line 217
- `function splitOutput(value: string): string[]` — function, line 233
- `async function runReview(_args: string[], flags: Flags, ctx: CmdCtx): Promise<OutputRow[]>` — function, line 237
- `const energy = typeof flags["--energy"] === "string" ? (flags["--energy"] as string) : null` — const, line 238
- `let minutes: number | null = null` — let, line 242
- `const parsed = Number(flags["--minutes"])` — const, line 244
- `const queue = await api.getTodayQueue(` — const, line 248
- `const rows: OutputRow[] = [` — const, line 256
- `async function runCalibrate(args: string[], flags: Flags, ctx: CmdCtx): Promise<OutputRow[]>` — function, line 277
- `let minutes: number | null = null` — let, line 281
- `const parsed = Number(flags["--minutes"])` — const, line 283
- `const progress = await api.startCalibrationSession(` — const, line 287
- `async function runWhy(args: string[]): Promise<OutputRow[]>` — function, line 302
- `const explanation = await api.explainPracticeItem(args[0])` — const, line 304
- `const c = explanation.components` — const, line 305
- `const rows: OutputRow[] = [` — const, line 306
- `const followupContribution = (c.interventionFollowup ?? 0) + (c.negativeSurpriseFollowup ?? 0)` — const, line 314
- `async function runShow(args: string[], ctx: CmdCtx, argv: string[]): Promise<OutputRow[]>` — function, line 329
- `const entity = await api.inspectEntity(args[0])` — const, line 331
- `async function runDoctor(): Promise<OutputRow[]>` — function, line 340
- `const health = await api.getRuntimeHealth()` — const, line 341
- `const checks: Array<` — const, line 342
- `const rows: OutputRow[] = [` — const, line 355
- `interface Completion` — interface, line 367
- `function tokenize(line: string, cursor: number)` — function, line 374
- `const left = line.slice(0, cursor)` — const, line 375
- `const leftTokens = left.split(/\s+/)` — const, line 376
- `const all = line.trim() === "" ? [] : line.trim().split(/\s+/)` — const, line 377
- `interface Candidates` — interface, line 386
- `function candidatesFor(kind: ArgKind | undefined, c: Candidates): string[]` — function, line 394
- `function computeCompletions(line: string, cursor: number, cands: Candidates): Completion[]` — function, line 413
- `const tok = tokenize(line, cursor)` — const, line 414
- `const prefix = tok.endsWithSpace ? "" : tok.activePrefix` — const, line 415
- `const spec = GRAMMAR[tok.all[0]]` — const, line 424
- `const positional: string[] = []` — const, line 435
- `let pendingFlag: string | null = null` — let, line 436
- `const token = tok.all[i]` — const, line 438
- `const before = tok.all.slice(0, tok.activeIndex)` — const, line 451
- `const lastBefore = before[before.length - 1]` — const, line 452
- `const posIndex = tok.endsWithSpace ? positional.length : positional.length - 1` — const, line 460
- `const argSpec = spec.args[posIndex] ?? spec.args[spec.args.length - 1]` — const, line 461
- `const pool = candidatesFor(argSpec.kind, cands)` — const, line 464
- `const exact = pool.filter((id)` — const, line 465
- `const sub = pool.filter((id)` — const, line 466
- `function parse(line: string):` — function, line 475
- `const tokenized = shellTokenize(line)` — const, line 476
- `let tokens = tokenized.tokens` — let, line 478
- `const name = tokens[0].startsWith("-") ? "__cli__" : tokens[0]` — const, line 484
- `const positional: string[] = []` — const, line 485
- `const flags: Flags =` — const, line 486
- `const token = tokens[i]` — const, line 488
- `const next = tokens[i + 1]` — const, line 490
- `function shellTokenize(line: string):` — function, line 504
- `const tokens: string[] = []` — const, line 505
- `let current = ""` — let, line 506
- `let quote: "'" | '"' | null = null` — let, line 507
- `let escaping = false` — let, line 508
- `let tokenStarted = false` — let, line 509
- `function findTab(value: string | undefined): TopTab | null` — function, line 555
- `const lowered = value.toLowerCase()` — const, line 557
- `function KindBadge(` — function, line 562
- `const map: Record<string,` — const, line 563
- `const m = map[kind] ??` — const, line 573
- `function modeTone(mode: string): string` — function, line 578
- `function OutputRowView(` — function, line 585
- `const mark = row.status === "ok" ? "✓" : row.status === "warn" ? "⚠" : "✗"` — const, line 636
- `const inputRef = useRef<HTMLInputElement>(null)` — const, line 706
- `const scrollRef = useRef<HTMLDivElement>(null)` — const, line 707
- `const subjectsKey = useMemo(()` — const, line 709
- `const cands = useMemo<Candidates>( ()` — const, line 710
- `const completions = useMemo(()` — const, line 714
- `const helpCommands = useMemo(()` — const, line 716
- `let cancelled = false` — let, line 728
- `function applyCompletion(index: number)` — function, line 757
- `const sel = completions[index]` — const, line 758
- `const tok = tokenize(line, cursor)` — const, line 760
- `const tokStart = cursor - tok.activePrefix.length` — const, line 761
- `const before = line.slice(0, tokStart)` — const, line 762
- `const after = line.slice(cursor)` — const, line 763
- `const trail = after.startsWith(" ") ? "" : " "` — const, line 764
- `const newLine = `$` — const, line 765
- `const newCursor = (before + sel.completion + trail).length` — const, line 766
- `async function execute()` — function, line 775
- `const raw = line.trim()` — const, line 776
- `const parsed = parse(raw)` — const, line 778
- `const nextHistory = [raw, ...history.filter((entry)` — const, line 779
- `const ctx: CmdCtx =` — const, line 797
- `const out = await runCommand(parsed.name as string, parsed.positional, parsed.flags, ctx, parsed.argv)` — const, line 808
- `const message = (error as Error).message ?? String(error)` — const, line 811
- `function onInputKey(event: React.KeyboardEvent<HTMLInputElement>)` — function, line 819
- `const next = Math.max(-1, histIdx - 1)` — const, line 838
- `const value = next === -1 ? "" : history[next] ?? ""` — const, line 840
- `const next = Math.min(history.length - 1, histIdx + 1)` — const, line 849
- `const value = history[next] ?? ""` — const, line 851
- `function readHistory(): string[]` — function, line 938
- `const parsed = JSON.parse(localStorage.getItem(HISTORY_KEY) ?? "[]")` — const, line 940

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `CommandPalette`; references `CommandPalette`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CliCommandResult`, `SessionSnapshot`
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export; imports `Pill`, `TopTab`, `navTabs`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- No repository test directly names this source path or a uniquely owned export. `npm run typecheck` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/CommandPalette.tsx](../../../../../../apps/learnloop-tauri/src/components/CommandPalette.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
