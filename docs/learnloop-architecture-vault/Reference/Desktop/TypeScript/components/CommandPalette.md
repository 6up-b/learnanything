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
| Source lines | 1408 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `c94882abe7a8f5a7cde491603d6abba8a4c0e2db` |
| Commit timestamp | `2026-10-22T16:58:30-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/CommandPalette|src/components/CommandPalette.tsx]]

## Public API

- `export interface PaletteCommand` — interface, line 31
- `export function matchPlainCommands(commands: PaletteCommand[], query: string): PaletteCommand[]` — function, line 44
- `export function CommandPalette(props: Parameters<typeof SimpleCommandPalette>[0])` — function, line 1124

## Internal implementation anchors

- `const words = query.toLowerCase().split(/\s+/).filter(Boolean)` — const, line 45
- `const haystack = [command.label, command.hint ?? "", ...(command.keywords ?? [])].join(" ").toLowerCase()` — const, line 48
- `const SHELL_PREFIX = /^\s*>\s*/` — const, line 55
- `const HISTORY_KEY = "learnloop.commandHistory"` — const, line 57
- `type OutputRow = |` — type, line 60
- `type ArgKind = "practice_item" | "concept" | "goal" | "any" | "subject" | "tab" | "url" | "path"` — type, line 78
- `interface ArgSpec` — interface, line 79
- `interface GrammarSpec` — interface, line 83
- `const GRAMMAR: Record<string, GrammarSpec> =` — const, line 89
- `const CLI_DELEGATED_COMMANDS = new Set([ "propose", "proposals", "accept", "reject", "edit-proposal-item", "ingest", "add-subject", "add-note", "generate-practice", "kill-codex", "populate-goal", "generate-diagnostics", "observation-templates", "register-obse…` — const, line 127
- `interface CmdCtx` — interface, line 149
- `type Flags = Record<string, string | true>` — type, line 161
- `async function runCommand(name: string, args: string[], flags: Flags, ctx: CmdCtx, argv: string[]): Promise<OutputRow[]>` — function, line 163
- `const tab = findTab(args[0])` — const, line 181
- `async function runCli(argv: string[]): Promise<OutputRow[]>` — function, line 246
- `const result = await api.runCliCommand(argv)` — const, line 247
- `function cliResultRows(result: CliCommandResult): OutputRow[]` — function, line 251
- `const rows: OutputRow[] = []` — const, line 252
- `function splitOutput(value: string): string[]` — function, line 268
- `async function runReview(_args: string[], flags: Flags, ctx: CmdCtx): Promise<OutputRow[]>` — function, line 272
- `const energy = typeof flags["--energy"] === "string" ? (flags["--energy"] as string) : null` — const, line 273
- `let minutes: number | null = null` — let, line 277
- `const parsed = Number(flags["--minutes"])` — const, line 279
- `const queue = await api.getTodayQueue(` — const, line 283
- `const rows: OutputRow[] = [` — const, line 291
- `async function runCalibrate(args: string[], flags: Flags, ctx: CmdCtx): Promise<OutputRow[]>` — function, line 312
- `let minutes: number | null = null` — let, line 316
- `const parsed = Number(flags["--minutes"])` — const, line 318
- `const progress = await api.startCalibrationSession(` — const, line 322
- `async function runWhy(args: string[]): Promise<OutputRow[]>` — function, line 337
- `const explanation = await api.explainPracticeItem(args[0])` — const, line 339
- `const c = explanation.components` — const, line 340
- `const rows: OutputRow[] = [` — const, line 341
- `const followupContribution = (c.interventionFollowup ?? 0) + (c.negativeSurpriseFollowup ?? 0)` — const, line 349
- `async function runShow(args: string[], ctx: CmdCtx, argv: string[]): Promise<OutputRow[]>` — function, line 364
- `const entity = await api.inspectEntity(args[0])` — const, line 366
- `async function runDoctor(): Promise<OutputRow[]>` — function, line 375
- `const health = await api.getRuntimeHealth()` — const, line 376
- `const checks: Array<` — const, line 377
- `const rows: OutputRow[] = [` — const, line 390
- `interface Completion` — interface, line 402
- `function tokenize(line: string, cursor: number)` — function, line 409
- `const left = line.slice(0, cursor)` — const, line 410
- `const leftTokens = left.split(/\s+/)` — const, line 411
- `const all = line.trim() === "" ? [] : line.trim().split(/\s+/)` — const, line 412
- `interface Candidates` — interface, line 421
- `function candidatesFor(kind: ArgKind | undefined, c: Candidates): string[]` — function, line 429
- `function computeCompletions(line: string, cursor: number, cands: Candidates): Completion[]` — function, line 448
- `const tok = tokenize(line, cursor)` — const, line 449
- `const prefix = tok.endsWithSpace ? "" : tok.activePrefix` — const, line 450
- `const spec = GRAMMAR[tok.all[0]]` — const, line 459
- `const positional: string[] = []` — const, line 470
- `let pendingFlag: string | null = null` — let, line 471
- `const token = tok.all[i]` — const, line 473
- `const before = tok.all.slice(0, tok.activeIndex)` — const, line 486
- `const lastBefore = before[before.length - 1]` — const, line 487
- `const posIndex = tok.endsWithSpace ? positional.length : positional.length - 1` — const, line 495
- `const argSpec = spec.args[posIndex] ?? spec.args[spec.args.length - 1]` — const, line 496
- `const pool = candidatesFor(argSpec.kind, cands)` — const, line 499
- `const exact = pool.filter((id)` — const, line 500
- `const sub = pool.filter((id)` — const, line 501
- `function parse(line: string):` — function, line 510
- `const tokenized = shellTokenize(line)` — const, line 511
- `let tokens = tokenized.tokens` — let, line 513
- `const name = tokens[0].startsWith("-") ? "__cli__" : tokens[0]` — const, line 519
- `const positional: string[] = []` — const, line 520
- `const flags: Flags =` — const, line 521
- `const token = tokens[i]` — const, line 523
- `const next = tokens[i + 1]` — const, line 525
- `function shellTokenize(line: string):` — function, line 539
- `const tokens: string[] = []` — const, line 540
- `let current = ""` — let, line 541
- `let quote: "'" | '"' | null = null` — let, line 542
- `let escaping = false` — let, line 543
- `let tokenStarted = false` — let, line 544
- `function findTab(value: string | undefined): TopTab | null` — function, line 590
- `const lowered = value.toLowerCase()` — const, line 592
- `function KindBadge(` — function, line 597
- `const map: Record<string,` — const, line 598
- `const m = map[kind] ??` — const, line 608
- `function modeTone(mode: string): string` — function, line 613
- `function OutputRowView(` — function, line 620
- `const mark = row.status === "ok" ? "✓" : row.status === "warn" ? "⚠" : "✗"` — const, line 671
- `function SimpleCommandPalette(` — function, line 703
- `const inputRef = useRef<HTMLInputElement>(null)` — const, line 747
- `const scrollRef = useRef<HTMLDivElement>(null)` — const, line 748
- `const subjectsKey = useMemo(()` — const, line 750
- `const cands = useMemo<Candidates>( ()` — const, line 751
- `const simple = shell === "simple"` — const, line 755
- `const shellMatch = simple ? SHELL_PREFIX.exec(line) : null` — const, line 758
- `const cliMode = !simple || shellMatch !== null` — const, line 759
- `const offset = shellMatch ? shellMatch[0].length : 0` — const, line 760
- `const cliLine = offset ? line.slice(offset) : line` — const, line 761
- `const cliCursor = Math.max(0, cursor - offset)` — const, line 762
- `const completions = useMemo( ()` — const, line 763
- `const plainMatches = useMemo( ()` — const, line 767
- `const helpCommands = useMemo(()` — const, line 772
- `let cancelled = false` — let, line 797
- `function applyCompletion(index: number)` — function, line 826
- `const sel = completions[index]` — const, line 827
- `const tok = tokenize(cliLine, cliCursor)` — const, line 829
- `const tokStart = cliCursor - tok.activePrefix.length` — const, line 830
- `const prefix = line.slice(0, offset)` — const, line 831
- `const before = cliLine.slice(0, tokStart)` — const, line 832
- `const after = cliLine.slice(cliCursor)` — const, line 833
- `const trail = after.startsWith(" ") ? "" : " "` — const, line 834
- `const newLine = `$` — const, line 835
- `const newCursor = (prefix + before + sel.completion + trail).length` — const, line 836
- `function runPlain(index: number)` — function, line 845
- `const command = plainMatches[index]` — const, line 846
- `async function execute()` — function, line 855
- `const raw = cliLine.trim()` — const, line 860
- `const parsed = parse(raw)` — const, line 862
- `const nextHistory = [raw, ...history.filter((entry)` — const, line 863
- `const ctx: CmdCtx =` — const, line 883
- `const out = await runCommand(parsed.name as string, parsed.positional, parsed.flags, ctx, parsed.argv)` — const, line 894
- `const message = (error as Error).message ?? String(error)` — const, line 897
- `function onInputKey(event: React.KeyboardEvent<HTMLInputElement>)` — function, line 905
- `const next = Math.max(-1, histIdx - 1)` — const, line 946
- `const value = next === -1 ? (simple ? "> " : "") : `$` — const, line 948
- `const next = Math.min(history.length - 1, histIdx + 1)` — const, line 957
- `const value = `$` — const, line 959
- `const scrollback = ( <div className="cli-scrollback" ref=` — const, line 974
- `const completionList = completions.length > 0 ? ( <div className="cli-completions">` — const, line 988
- `const input = ( <input ref=` — const, line 1009
- `const matchCount = completions.length > 0 ? ( <span className="cli-faint cli-match-count">` — const, line 1026
- `const query = line.trim()` — const, line 1035
- `function ClassicCommandPalette(` — function, line 1131
- `const inputRef = useRef<HTMLInputElement>(null)` — const, line 1169
- `const scrollRef = useRef<HTMLDivElement>(null)` — const, line 1170
- `const subjectsKey = useMemo(()` — const, line 1172
- `const cands = useMemo<Candidates>( ()` — const, line 1173
- `const completions = useMemo(()` — const, line 1177
- `const helpCommands = useMemo(()` — const, line 1179
- `let cancelled = false` — let, line 1191
- `function applyCompletion(index: number)` — function, line 1220
- `const sel = completions[index]` — const, line 1221
- `const tok = tokenize(line, cursor)` — const, line 1223
- `const tokStart = cursor - tok.activePrefix.length` — const, line 1224
- `const before = line.slice(0, tokStart)` — const, line 1225
- `const after = line.slice(cursor)` — const, line 1226
- `const trail = after.startsWith(" ") ? "" : " "` — const, line 1227
- `const newLine = `$` — const, line 1228
- `const newCursor = (before + sel.completion + trail).length` — const, line 1229
- `async function execute()` — function, line 1238
- `const raw = line.trim()` — const, line 1239
- `const parsed = parse(raw)` — const, line 1241
- `const nextHistory = [raw, ...history.filter((entry)` — const, line 1242
- `const ctx: CmdCtx =` — const, line 1260
- `const out = await runCommand(parsed.name as string, parsed.positional, parsed.flags, ctx, parsed.argv)` — const, line 1271
- `const message = (error as Error).message ?? String(error)` — const, line 1274
- `function onInputKey(event: React.KeyboardEvent<HTMLInputElement>)` — function, line 1282
- `const next = Math.max(-1, histIdx - 1)` — const, line 1301
- `const value = next === -1 ? "" : history[next] ?? ""` — const, line 1303
- `const next = Math.min(history.length - 1, histIdx + 1)` — const, line 1312
- `const value = history[next] ?? ""` — const, line 1314
- `function readHistory(): string[]` — function, line 1401
- `const parsed = JSON.parse(localStorage.getItem(HISTORY_KEY) ?? "[]")` — const, line 1403

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `CommandPalette`, `PaletteCommand`; references `CommandPalette`, `PaletteCommand`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CliCommandResult`, `SessionSnapshot`
- [[Reference/Desktop/TypeScript/app/shell|src/app/shell.ts]] — import-or-re-export; imports `ShellMode`
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export; imports `Pill`, `TopTab`, `navTabs`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/components/CommandPalette.shell.test.tsx](../../../../../../apps/learnloop-tauri/src/components/CommandPalette.shell.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/CommandPalette.tsx](../../../../../../apps/learnloop-tauri/src/components/CommandPalette.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
