---
title: "Desktop module · src/screens/startBackdrops/JuliaBackdrop.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.startBackdrops.JuliaBackdrop"
language: "TypeScript"
area: "TypeScript/screens/startBackdrops"
source_path: "apps/learnloop-tauri/src/screens/startBackdrops/JuliaBackdrop.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/startBackdrops/JuliaBackdrop.tsx"
source_commit: "971d7c274e09873d726d43578cd080e4d8865571"
source_commit_timestamp: "2026-07-27T06:01:19-04:00"
source_worktree_state: "clean"
activation_kind: "entry-reachable build graph"
activation_evidence: "Imported through StartScreen's supported optional backdrop paths reachable from src/main.tsx."
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/reference/module"
  - "learnloop/desktop"
  - "learnloop/desktop/typescript"
  - "refactor/active"
---

# `src/screens/startBackdrops/JuliaBackdrop.tsx`

Area: [[Reference/Desktop/TypeScript/screens/startBackdrops/_area|TypeScript/screens/startBackdrops]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `JuliaBackdrop` start-screen visualization or its rendering support.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/startBackdrops/JuliaBackdrop.tsx](../../../../../../../apps/learnloop-tauri/src/screens/startBackdrops/JuliaBackdrop.tsx) |
| Source lines | 163 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/startBackdrops/_area|TypeScript/screens/startBackdrops]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `971d7c274e09873d726d43578cd080e4d8865571` |
| Commit timestamp | `2026-07-27T06:01:19-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> Imported through StartScreen's supported optional backdrop paths reachable from src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/startBackdrops/JuliaBackdrop|src/screens/startBackdrops/JuliaBackdrop.tsx]]

## Public API

- `export function JuliaBackdrop(` — function, line 26

## Internal implementation anchors

- `const GLYPHS = ".:-=+*#%@"` — const, line 14
- `const MAX_IT = 28` — const, line 15
- `const FRAME_MS = 50` — const, line 16
- `const THETA_PER_MS = 0.004 / FRAME_MS` — const, line 17
- `type JuliaFrameResponse =` — type, line 19
- `const containerRef = useRef<HTMLDivElement>(null)` — const, line 27
- `const canvasRef = useRef<HTMLCanvasElement>(null)` — const, line 28
- `const container = containerRef.current` — const, line 31
- `const canvas = canvasRef.current` — const, line 32
- `const ctx = canvas.getContext("2d")` — const, line 34
- `const reduce = prefersReducedMotion()` — const, line 38
- `const worker = new JuliaWorker()` — const, line 39
- `let atlas: MonospaceGlyphAtlas | null = null` — let, line 41
- `let cols = 80` — let, line 42
- `let rows = 40` — let, line 43
- `let width = 0` — let, line 44
- `let height = 0` — let, line 45
- `let dpr = Math.min(window.devicePixelRatio || 1, 2)` — let, line 46
- `let raf = 0` — let, line 47
- `let resizeRaf = 0` — let, line 48
- `let requestId = 0` — let, line 49
- `let acceptedRequestId = 0` — let, line 50
- `let inFlight = false` — let, line 51
- `let lastRequestedAt = -Infinity` — let, line 52
- `const thetaOrigin = Math.random() * Math.PI * 2` — const, line 53
- `let cells = new Uint16Array(0)` — let, line 54
- `const codeByIteration = new Uint16Array(MAX_IT + 1)` — const, line 55
- `function rebuildAtlas()` — function, line 57
- `let colorIndex = Math.floor((it / MAX_IT) * colors.length)` — let, line 66
- `let glyphIndex = Math.floor((it / MAX_IT) * GLYPHS.length)` — let, line 68
- `function resize()` — function, line 75
- `const rect = container!.getBoundingClientRect()` — const, line 76
- `const nextDpr = Math.min(window.devicePixelRatio || 1, 2)` — const, line 79
- `const dprChanged = nextDpr !== dpr` — const, line 80
- `function requestFrame(ts: number)` — function, line 96
- `const id = ++requestId` — const, line 100
- `const theta = reduce ? 0 : thetaOrigin + ts * THETA_PER_MS` — const, line 102
- `const reSpan = 3.4` — const, line 103
- `const imSpan = (reSpan * (rows * CHAR_H)) / Math.max(1, cols * CHAR_W)` — const, line 104
- `function renderFrame(iterations: Uint8Array)` — function, line 116
- `const response = event.data` — const, line 123
- `function frame(ts: number)` — function, line 135
- `const ro = new ResizeObserver(()` — const, line 142

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]] — import-or-re-export: `JuliaBackdrop`; references `JuliaBackdrop`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/screens/startBackdrops/glyphAtlas|src/screens/startBackdrops/glyphAtlas.ts]] — import-or-re-export; imports `FULLSCREEN_CANVAS_STYLE`, `MonospaceGlyphAtlas`, `readAmberAtlasPalette`
- [[Reference/Desktop/TypeScript/screens/startBackdrops/julia.worker|src/screens/startBackdrops/julia.worker.ts]] — import-or-re-export; imports `JuliaWorker`
- [[Reference/Desktop/TypeScript/screens/startBackdrops/shared|src/screens/startBackdrops/shared.ts]] — import-or-re-export; imports `CHAR_H`, `CHAR_W`, `prefersReducedMotion`

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

1. Modify [apps/learnloop-tauri/src/screens/startBackdrops/JuliaBackdrop.tsx](../../../../../../../apps/learnloop-tauri/src/screens/startBackdrops/JuliaBackdrop.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
