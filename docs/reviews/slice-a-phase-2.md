# Slice A Phase 2 — learner field F1

## Plan

Base: primary checkout `main` at `1a0f7a0`, including merged Phase 1.
Branch: `slice-a/phase-2`. Owner accepted field D1, D2, D3, D8, D9,
D10 and D12 defaults.

- Add `src/learnloop/field/` for authoritative outcome projection, immutable
  replay rows, interaction signals, predictor interfaces and pure predictors.
  Reuse grading epochs, item snapshots, effective observations, facet outcome
  arithmetic, canonical facet resolution and serving receipts.
- Add the shared evaluation harness and CLI commands `learnloop field data-check`
  and `learnloop eval`. Generate aggregate-only JSON and Markdown reports 1–2
  with exclusions, uncertainty, prequential ordering and version manifests.
- Harness arms: `base_rate_lo`, `facet_beta`, incumbent `mastery_ekf`,
  `lo_general`, practice/capability/transfer/retrievability/hints/tutor-signal
  extensions and composite; retrievability and signal-constant sweeps.
  Provide a registration seam for Phase 3's family arms. Optional offline LLM
  predictions remain off by default and cannot be active.
- Add field config and import contracts. Only the incumbent may serve in F1;
  no algorithm successor, placement changes, graph coupling or evidence writes.
- Add a migration for DERIVED `facet_outcome_observations` and WORKFLOW
  `question_classifications`, register the outcome rebuild owner, then take the
  next free number at completion and regenerate the migration-head fixture and
  database references. No active challenger snapshot is needed in F1.
- Reuse Phase 1 spend caps, dry-run, checkpoints and per-component routes for
  optional question classification and offline LLM prediction. Each model
  verdict appends to `judgment_ledger`; replay consumes cached outputs only.
- Change the map RPC/types/rendering so no-evidence points omit `ready` and
  explicitly display an outlined, flat `untested` state. Preserve demonstrated
  geometry, beads, ghost rings and decay markers.
- Add the F1 tests named in field §9 and gate tests G1–G6/G10–G13; run focused
  tests, import lint, full parallel pytest, durability, frontend typecheck,
  vitest and build. Exercise both CLI commands and reports on backup-API copies
  under `fixtures-local/`, never on working vaults.

## Scope boundaries and decisions

- F2 assumed-known and quick-check tests/behaviour, activation successors and
  kill switches belong to later phases. Phase 3 owns family-specific arms.
- No live API calls in tests. Never read `.env` files or
  `~/.config/learnloop`. Validation commands use isolated configuration.
- D12 specifies a cap but not its numeric value, and “before any work” lacks
  a defined timestamp cutoff. Any conservative interpretation will be
  explicitly documented and versioned, not fitted to owner history.

## Built / deviations / validation / owner commands

Implementation and validation pending. This document will record actual
results, exact owner commands for reports 1–2, and remaining questions before
the checkpoint. No merge or push is authorized.
