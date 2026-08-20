---
title: "Desktop module · src/render/MathLiveEditor.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.render.MathLiveEditor"
language: "TypeScript"
area: "TypeScript/render"
source_path: "apps/learnloop-tauri/src/render/MathLiveEditor.tsx"
source_paths:
  - "apps/learnloop-tauri/src/render/MathLiveEditor.tsx"
source_commit: "b0b0834ba8577623dad59e6a171029f6b7970b50"
source_commit_timestamp: "2026-07-06T20:57:41-04:00"
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

# `src/render/MathLiveEditor.tsx`

Area: [[Reference/Desktop/TypeScript/render/_area|TypeScript/render]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Adapts `MathLiveEditor` content editing or rendering into React presentation behavior.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/render/MathLiveEditor.tsx](../../../../../../apps/learnloop-tauri/src/render/MathLiveEditor.tsx) |
| Source lines | 426 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/render/_area|TypeScript/render]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `b0b0834ba8577623dad59e6a171029f6b7970b50` |
| Commit timestamp | `2026-07-06T20:57:41-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ExamScreen|src/screens/ExamScreen.tsx]] → [[Reference/Desktop/TypeScript/render/MathLiveEditor|src/render/MathLiveEditor.tsx]]

## Public API

- `export function MathLiveEditor(` — function, line 217

## Internal implementation anchors

- `interface Props` — interface, line 16
- `type Seg = |` — type, line 26
- `const ZWSP = new RegExp("\\u200B", "g")` — const, line 33
- `function tokenize(value: string): Seg[]` — function, line 38
- `const segs: Seg[] = []` — const, line 39
- `let i = 0` — let, line 40
- `let textStart = 0` — let, line 41
- `const pushText = (end: number)` — const, line 42
- `const ch = value[i]` — const, line 46
- `const display = value[i + 1] === "$"` — const, line 52
- `const delim = display ? 2 : 1` — const, line 53
- `const contentStart = i + delim` — const, line 54
- `let j = contentStart` — let, line 55
- `let close = -1` — let, line 56
- `const end = close + delim` — const, line 64
- `const isActiveMath = (seg: Seg, caret: number): boolean` — const, line 79
- `function escapeHtml(s: string): string` — function, line 82
- `function renderMath(tex: string, display: boolean): string` — function, line 86
- `function buildHtml(segs: Seg[], caret: number): string` — function, line 97
- `let html = ""` — let, line 98
- `const cls = seg.display ? "mle-math mle-display" : "mle-math"` — const, line 105
- `function widgetSig(segs: Seg[], caret: number): string` — function, line 115
- `function serialize(root: HTMLElement, anchorNode: Node | null, anchorOffset: number):` — function, line 124
- `let out = ""` — let, line 125
- `let caret = -1` — let, line 126
- `const visit = (node: Node, isBlock: boolean)` — const, line 127
- `const children = node.childNodes` — const, line 129
- `const child = children[idx]` — const, line 133
- `const raw = child.nodeValue ?? ""` — const, line 135
- `const el = child as HTMLElement` — const, line 139
- `function placeCaret(root: HTMLElement, offset: number): void` — function, line 160
- `let remaining = offset` — let, line 161
- `const range = document.createRange()` — const, line 162
- `let placed = false` — let, line 163
- `const visit = (node: Node)` — const, line 164
- `const child = node.childNodes[idx]` — const, line 166
- `const len = (child.nodeValue ?? "").length` — const, line 168
- `const el = child as HTMLElement` — const, line 172
- `const len = el.dataset.src.length` — const, line 174
- `const sel = window.getSelection()` — const, line 188
- `function offsetOfNode(root: HTMLElement, target: HTMLElement): number` — function, line 196
- `let out = 0` — let, line 197
- `let found = -1` — let, line 198
- `const visit = (node: Node)` — const, line 199
- `const child = node.childNodes[idx]` — const, line 201
- `const el = child as HTMLElement` — const, line 206
- `const editorRef = useRef<HTMLDivElement>(null)` — const, line 218
- `const lastModel = useRef<string | null>(null)` — const, line 219
- `const lastSig = useRef<string>("")` — const, line 220
- `const reconciling = useRef(false)` — const, line 221
- `const composing = useRef(false)` — const, line 222
- `const reconcile = useCallback((forceCaret?: number)` — const, line 227
- `const el = editorRef.current` — const, line 228
- `const sel = window.getSelection()` — const, line 230
- `const useForced = forceCaret != null` — const, line 231
- `const anchorNode = !useForced && sel && sel.rangeCount ? sel.anchorNode : null` — const, line 232
- `const anchorOffset = !useForced && sel && sel.rangeCount ? sel.anchorOffset : 0` — const, line 233
- `const read = serialize(el, anchorNode, anchorOffset)` — const, line 234
- `const model = read.text` — const, line 235
- `const caret = useForced ? Math.max(0, Math.min(forceCaret, model.length)) : read.caret` — const, line 236
- `const segs = tokenize(model)` — const, line 237
- `const sig = widgetSig(segs, caret)` — const, line 238
- `const renderAll = useCallback(()` — const, line 253
- `const el = editorRef.current` — const, line 254
- `const model = serialize(el, null, 0).text` — const, line 256
- `const segs = tokenize(model)` — const, line 257
- `const el = editorRef.current` — const, line 267
- `const focused = document.activeElement === el` — const, line 269
- `const segs = tokenize(value)` — const, line 270
- `const caret = focused ? value.length : -1` — const, line 271
- `const onSelectionChange = ()` — const, line 282
- `const el = editorRef.current` — const, line 284
- `const sel = window.getSelection()` — const, line 285
- `const onKeyDown = (event: React.KeyboardEvent<HTMLDivElement>)` — const, line 294
- `const el = editorRef.current` — const, line 299
- `const sel = window.getSelection()` — const, line 300
- `const range = document.createRange()` — const, line 303
- `const sel = window.getSelection()` — const, line 313
- `const range = sel.getRangeAt(0)` — const, line 315
- `const node = document.createTextNode("\n")` — const, line 317
- `const el = editorRef.current` — const, line 327
- `const sel = window.getSelection()` — const, line 328
- `const segs = tokenize(text)` — const, line 331
- `const seg = segs.find((s)` — const, line 335
- `const seg = segs.find((s)` — const, line 338
- `const onMouseDown = (event: React.MouseEvent<HTMLDivElement>)` — const, line 344
- `const widget = (event.target as HTMLElement).closest<HTMLElement>(".mle-math")` — const, line 345
- `const el = editorRef.current` — const, line 346
- `const start = offsetOfNode(el, widget)` — const, line 350
- `const onPaste = (event: React.ClipboardEvent<HTMLDivElement>)` — const, line 354
- `const textData = event.clipboardData.getData("text/plain")` — const, line 356
- `const sel = window.getSelection()` — const, line 357
- `const range = sel.getRangeAt(0)` — const, line 359
- `const node = document.createTextNode(textData)` — const, line 361
- `const selectionSource = (): string | null` — const, line 373
- `const el = editorRef.current` — const, line 374
- `const sel = window.getSelection()` — const, line 375
- `const range = sel.getRangeAt(0)` — const, line 377
- `const start = serialize(el, range.startContainer, range.startOffset).caret` — const, line 379
- `const end = serialize(el, range.endContainer, range.endOffset).caret` — const, line 380
- `const onCopy = (event: React.ClipboardEvent<HTMLDivElement>)` — const, line 385
- `const source = selectionSource()` — const, line 386
- `const onCut = (event: React.ClipboardEvent<HTMLDivElement>)` — const, line 392
- `const source = selectionSource()` — const, line 393
- `const sel = window.getSelection()` — const, line 397

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ExamScreen|src/screens/ExamScreen.tsx]] — import-or-re-export: `MathLiveEditor`; references `MathLiveEditor`
- [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] — import-or-re-export: `MathLiveEditor`; references `MathLiveEditor`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

- Imported packages/crates: `katex`, `katex/dist/katex.min.css`, `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- No repository test directly names this source path or a uniquely owned export. `npm run typecheck` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/render/MathLiveEditor.tsx](../../../../../../apps/learnloop-tauri/src/render/MathLiveEditor.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
