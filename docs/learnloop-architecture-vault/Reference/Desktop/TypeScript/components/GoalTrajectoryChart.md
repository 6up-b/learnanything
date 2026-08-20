---
title: "Desktop module · src/components/GoalTrajectoryChart.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.GoalTrajectoryChart"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/GoalTrajectoryChart.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/GoalTrajectoryChart.tsx"
source_commit: "a29853775f09f6b504620b1a8b6d5e890161f912"
source_commit_timestamp: "2026-07-14T17:11:30-04:00"
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

# `src/components/GoalTrajectoryChart.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `GoalTrajectoryChart` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/GoalTrajectoryChart.tsx](../../../../../../apps/learnloop-tauri/src/components/GoalTrajectoryChart.tsx) |
| Source lines | 250 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `a29853775f09f6b504620b1a8b6d5e890161f912` |
| Commit timestamp | `2026-07-14T17:11:30-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] → [[Reference/Desktop/TypeScript/components/GoalBanner|src/components/GoalBanner.tsx]] → [[Reference/Desktop/TypeScript/components/GoalTrajectoryChart|src/components/GoalTrajectoryChart.tsx]]

## Public API

- `export function trajectorySummary( series: GoalSeriesPointDto[], dueAt: string | null, targetRecall?: number ): string` — function, line 29
- `export function GoalTrajectoryChart(` — function, line 61

## Internal implementation anchors

- `const pctText = (v: number | null | undefined): string` — const, line 21
- `function daysBetween(fromMs: number, toMs: number): number` — function, line 24
- `const valid = series.filter((p)` — const, line 34
- `const hist = valid.filter((p)` — const, line 36
- `const last = hist[hist.length - 1] ?? valid[valid.length - 1]` — const, line 37
- `const parts: string[] = []` — const, line 38
- `let ready = `predicted recall now $` — let, line 43
- `const decayPts = valid.filter((p)` — const, line 47
- `const anyDecay = valid.some((p)` — const, line 48
- `const dueT = dueAt && !Number.isNaN(Date.parse(dueAt)) ? Date.parse(dueAt) : null` — const, line 49
- `const end = decayPts[decayPts.length - 1]` — const, line 51
- `let s = `if nothing is practiced, decay projects $` — let, line 52
- `const valid = series.filter((p)` — const, line 73
- `const hist = valid .filter((p)` — const, line 74
- `const decay = valid .filter((p)` — const, line 91
- `const lastValid = valid[valid.length - 1]` — const, line 97
- `const decayEstimated = lastValid?.decayEstimated ?? 0` — const, line 98
- `const heldFlat = lastValid?.heldFlat ?? 0` — const, line 99
- `const showProjection = decayEstimated > 0 && decay.length > 0` — const, line 100
- `const padL = 4` — const, line 103
- `const padR = 52` — const, line 104
- `const demoLaneH = 40` — const, line 105
- `const laneGap = 20` — const, line 106
- `const readyLaneH = 52` — const, line 107
- `const padT = 6` — const, line 108
- `const padB = 14` — const, line 109
- `const height = padT + demoLaneH + laneGap + readyLaneH + padB` — const, line 110
- `const plotW = width - padL - padR` — const, line 111
- `const firstT = hist[0].t` — const, line 114
- `const dueT = dueAt && !Number.isNaN(Date.parse(dueAt)) ? Date.parse(dueAt) : null` — const, line 115
- `const lastT = Math.max( hist[hist.length - 1].t, decay.length ? decay[decay.length - 1].t : 0, dueT ?? 0 )` — const, line 116
- `const spanT = Math.max(1, lastT - firstT)` — const, line 121
- `const xOf = (t: number)` — const, line 122
- `const demoTop = padT` — const, line 125
- `const demoBot = padT + demoLaneH` — const, line 126
- `const totalMax = Math.max(1, ...hist.map((p)` — const, line 127
- `const demoY = (count: number)` — const, line 128
- `const demoPath = hist .map((p, i)` — const, line 131
- `const x = xOf(p.t)` — const, line 133
- `const y = demoY(p.demonstrated)` — const, line 134
- `const prevY = demoY(hist[i - 1].demonstrated)` — const, line 136
- `const demoLast = hist[hist.length - 1]` — const, line 140
- `const readyTop = demoBot + laneGap` — const, line 143
- `const readyBot = readyTop + readyLaneH` — const, line 144
- `const readyY = (frac: number)` — const, line 145
- `const readyHist = hist.filter((p)` — const, line 147
- `const readyPath = readyHist .map((p, i)` — const, line 148
- `const decayAnchor = readyHist.length ? readyHist[readyHist.length - 1] : null` — const, line 153
- `const decaySeq = decayAnchor ? [decayAnchor, ...decay] : decay` — const, line 154
- `const decayPath = decaySeq .map((p, i)` — const, line 155
- `const decayEnd = decay.length ? decay[decay.length - 1] : null` — const, line 158
- `const summary = trajectorySummary(series, dueAt, targetRecall)` — const, line 160
- `const stepDown = i > 0 && p.demonstrated < hist[i - 1].demonstrated` — const, line 174
- `const x = xOf(p.t)` — const, line 175
- `const y = demoY(p.demonstrated)` — const, line 176

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/GoalBanner|src/components/GoalBanner.tsx]] — import-or-re-export: `GoalTrajectoryChart`; references `GoalTrajectoryChart`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `GoalSeriesPointDto`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Goals Exams and Certification Workflow|Goals, Exams, and Certification Workflow]] — owns the end-to-end goal path.
- [[Concepts/Goals and Certification|Goals and Certification]] — owns goal and certification semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_sidecar_goals.py](../../../../../../tests/test_sidecar_goals.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_exams.py](../../../../../../tests/test_sidecar_exams.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_goal_projection.py](../../../../../../tests/test_goal_projection.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_exam_session.py](../../../../../../tests/test_exam_session.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/GoalTrajectoryChart.tsx](../../../../../../apps/learnloop-tauri/src/components/GoalTrajectoryChart.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
