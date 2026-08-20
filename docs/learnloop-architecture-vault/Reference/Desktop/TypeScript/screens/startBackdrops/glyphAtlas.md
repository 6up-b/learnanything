---
title: "Desktop module · src/screens/startBackdrops/glyphAtlas.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.startBackdrops.glyphAtlas"
language: "TypeScript"
area: "TypeScript/screens/startBackdrops"
source_path: "apps/learnloop-tauri/src/screens/startBackdrops/glyphAtlas.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/startBackdrops/glyphAtlas.ts"
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

# `src/screens/startBackdrops/glyphAtlas.ts`

Area: [[Reference/Desktop/TypeScript/screens/startBackdrops/_area|TypeScript/screens/startBackdrops]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `glyphAtlas` start-screen visualization or its rendering support.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/startBackdrops/glyphAtlas.ts](../../../../../../../apps/learnloop-tauri/src/screens/startBackdrops/glyphAtlas.ts) |
| Source lines | 178 |
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
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/startBackdrops/glyphAtlas|src/screens/startBackdrops/glyphAtlas.ts]]

## Public API

- `export const FULLSCREEN_CANVAS_STYLE =` — const, line 4
- `export function resolveCssColor(value: string, fallback: string): string` — function, line 25
- `export function readAmberAtlasPalette(glowStrength: number):` — function, line 38
- `export class MonospaceGlyphAtlas` — class, line 61

## Internal implementation anchors

- `type GlyphAtlasOptions =` — type, line 12
- `const probe = document.createElement("span")` — const, line 26
- `const resolved = getComputedStyle(probe).color || fallback` — const, line 33
- `const palette = readPaletteColors()` — const, line 39
- `const tileCount = this.glyphCount * this.colorCount` — const, line 95
- `const atlasCols = this.glyphCount` — const, line 96
- `const atlasRows = this.colorCount` — const, line 97
- `const ctx = this.atlas.getContext("2d")` — const, line 104
- `const metrics = ctx.measureText("Mg")` — const, line 111
- `const ascent = metrics.actualBoundingBoxAscent || 9 * dpr` — const, line 112
- `const descent = metrics.actualBoundingBoxDescent || 3 * dpr` — const, line 113
- `const baselineOffset = (this.cellHeight * dpr + ascent - descent) / 2` — const, line 114
- `const tileIndex = colorIndex * this.glyphCount + glyphIndex` — const, line 120
- `const code = tileIndex + 1` — const, line 121
- `const sx = glyphIndex * this.tilePixelWidth` — const, line 122
- `const sy = colorIndex * this.tilePixelHeight` — const, line 123
- `const index = this.glyphIndices.get(glyph)` — const, line 136
- `const sourceX = this.sourceX` — const, line 146
- `const sourceY = this.sourceY` — const, line 147
- `const sourceWidth = this.tilePixelWidth` — const, line 148
- `const sourceHeight = this.tilePixelHeight` — const, line 149
- `const destWidth = this.tileWidth` — const, line 150
- `const destHeight = this.tileHeight` — const, line 151
- `const pad = this.pad` — const, line 152
- `const cellWidth = this.cellWidth` — const, line 153
- `const cellHeight = this.cellHeight` — const, line 154
- `const atlas = this.atlas` — const, line 155
- `const rows = Math.ceil(cells.length / cols)` — const, line 157
- `let index = 0` — let, line 158
- `const y = row * cellHeight - pad` — const, line 160
- `const code = cells[index]` — const, line 162

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]] — import-or-re-export: `FULLSCREEN_CANVAS_STYLE`, `MonospaceGlyphAtlas`, `readAmberAtlasPalette`, `resolveCssColor`; references `FULLSCREEN_CANVAS_STYLE`, `MonospaceGlyphAtlas`, `readAmberAtlasPalette`, `resolveCssColor`
- [[Reference/Desktop/TypeScript/screens/startBackdrops/JuliaBackdrop|src/screens/startBackdrops/JuliaBackdrop.tsx]] — import-or-re-export: `FULLSCREEN_CANVAS_STYLE`, `MonospaceGlyphAtlas`, `readAmberAtlasPalette`; references `FULLSCREEN_CANVAS_STYLE`, `MonospaceGlyphAtlas`, `readAmberAtlasPalette`
- [[Reference/Desktop/TypeScript/screens/startBackdrops/LifeBackdrop|src/screens/startBackdrops/LifeBackdrop.tsx]] — import-or-re-export: `FULLSCREEN_CANVAS_STYLE`, `MonospaceGlyphAtlas`, `readAmberAtlasPalette`; references `FULLSCREEN_CANVAS_STYLE`, `MonospaceGlyphAtlas`, `readAmberAtlasPalette`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `FONT_MONO`
- [[Reference/Desktop/TypeScript/screens/startBackdrops/shared|src/screens/startBackdrops/shared.ts]] — import-or-re-export; imports `CHAR_H`, `CHAR_W`, `mixRgb`, `readPaletteColors`, `rgba`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

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

1. Modify [apps/learnloop-tauri/src/screens/startBackdrops/glyphAtlas.ts](../../../../../../../apps/learnloop-tauri/src/screens/startBackdrops/glyphAtlas.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
