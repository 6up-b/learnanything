---
title: "Desktop module · src/render/LiveMarkdownEditor.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.render.LiveMarkdownEditor"
language: "TypeScript"
area: "TypeScript/render"
source_path: "apps/learnloop-tauri/src/render/LiveMarkdownEditor.tsx"
source_paths:
  - "apps/learnloop-tauri/src/render/LiveMarkdownEditor.tsx"
source_commit: "4a28c9635f24945d78366fa26212db7488d82545"
source_commit_timestamp: "2026-05-28T11:36:12-04:00"
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

# `src/render/LiveMarkdownEditor.tsx`

Area: [[Reference/Desktop/TypeScript/render/_area|TypeScript/render]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Adapts `LiveMarkdownEditor` content editing or rendering into React presentation behavior.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/render/LiveMarkdownEditor.tsx](../../../../../../apps/learnloop-tauri/src/render/LiveMarkdownEditor.tsx) |
| Source lines | 218 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/render/_area|TypeScript/render]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `4a28c9635f24945d78366fa26212db7488d82545` |
| Commit timestamp | `2026-05-28T11:36:12-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/LibraryScreen|src/screens/LibraryScreen.tsx]] → [[Reference/Desktop/TypeScript/render/LiveMarkdownEditor|src/render/LiveMarkdownEditor.tsx]]

## Public API

- `export function LiveMarkdownEditor(` — function, line 78

## Internal implementation anchors

- `interface Block` — interface, line 15
- `function splitBlocks(value: string): Block[]` — function, line 25
- `const blocks: Block[] = []` — const, line 26
- `let scanFrom = 0` — let, line 27
- `const close = value.indexOf("\n---", 3)` — const, line 30
- `const afterClose = value.indexOf("\n", close + 1)` — const, line 32
- `const fmEnd = afterClose === -1 ? value.length : afterClose` — const, line 33
- `const lines = value.slice(scanFrom).split("\n")` — const, line 39
- `let cursor = scanFrom` — let, line 40
- `let blockStart = -1` — let, line 41
- `let blockEnd = -1` — let, line 42
- `let fence: "fence" | "math" | null = null` — let, line 43
- `const flush = ()` — const, line 45
- `const lineStart = cursor` — const, line 53
- `const lineEnd = cursor + line.length` — const, line 54
- `const trimmed = line.trim()` — const, line 55
- `const isFence = trimmed.startsWith("```") || trimmed.startsWith("~~~")` — const, line 56
- `const isMath = trimmed === "$$"` — const, line 57
- `const SCROLL_STYLE =` — const, line 76
- `const taRef = useRef<HTMLTextAreaElement | null>(null)` — const, line 89
- `const blocks = useMemo(()` — const, line 91
- `const aStart = editing ? editing.before.length : -1` — const, line 94
- `const aEnd = editing ? value.length - editing.after.length : -1` — const, line 95
- `const draft = editing ? value.slice(aStart, aEnd) : ""` — const, line 96
- `function startEdit(block: Block)` — function, line 98
- `function startEditEmpty()` — function, line 102
- `function onDraftChange(next: string)` — function, line 106
- `const node = taRef.current` — const, line 114
- `const end = node.value.length` — const, line 116
- `const node = taRef.current` — const, line 123
- `function renderBlock(block: Block)` — function, line 130
- `const textarea = ( <textarea ref=` — const, line 151
- `let body` — let, line 178
- `const beforeBlocks = blocks.filter((block)` — const, line 189
- `const afterBlocks = blocks.filter((block)` — const, line 190
- `const frontmatterStyle =` — const, line 207

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/LibraryScreen|src/screens/LibraryScreen.tsx]] — import-or-re-export: `LiveMarkdownEditor`; references `LiveMarkdownEditor`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- No repository test directly names this source path or a uniquely owned export. `npm run typecheck` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/render/LiveMarkdownEditor.tsx](../../../../../../apps/learnloop-tauri/src/render/LiveMarkdownEditor.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
