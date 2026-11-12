---
title: Testing and Invariants
aliases:
  - Verification Architecture
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-09-23
source_commit: 0622ea164f76ad7e1d62a00afda51473dbcd992e
source_commit_timestamp: "2026-09-23T13:06:55-04:00"
source_paths:
  - tests
  - pyproject.toml
  - tests/conftest.py
  - apps/learnloop-tauri/vitest.config.mjs
  - docs/specs/REFACTOR_PROPOSAL.md
tags:
  - learnloop/architecture
  - learnloop/testing
  - learnloop/invariants
---

# Testing and Invariants

Tests are part of the architecture. LearnLoop uses example tests for local rules, characterization tests for legacy behavior, and cross-cutting oracles for boundaries that ordinary unit tests cannot protect.

## Oracle families

| Oracle | Protects |
|---|---|
| import-linter contracts | layer direction, primitive purity, adapter independence, frozen cycles |
| AST architecture scans | private imports, function-local edges, SQL owners, dynamic references |
| provider matrix | identical selection/manual/fallback behavior through six production entry paths |
| structured transport parity | every feature operation works through SDK/chat; HTTP supports exact subset |
| attempt write-order instrumentation | receipt → grade → evidence → state → post-attempt sequence |
| table-role exactness | migration-head schema and registry match bidirectionally |
| rebuild golden | every derived column reproduces, stale rows clear, all attempts accounted, one receipt |
| shadow isolation | semantic diff on copy; live DB hash unchanged |
| CLI help snapshot | 171 root/group/command surfaces |
| sidecar JSON snapshot | protocol output for queue/practice/reader |
| migration process tests | two-process serialization, death rollback, FK restoration |
| attempt completion recovery | a committed grade keeps its provenance through recovery, and concurrent recoveries normalize an attempt once (`tests/test_attempt_completion.py`) |
| ingest ownership fence | a replaced attempt cannot finish or publish, and the heartbeat survives transient database errors (`tests/test_ingest_ownership.py`) |
| repository scopes | pinned/atomic transactions roll back on failure and publish nothing (`tests/test_repository_scopes.py`) |
| gate lanes | `arc_close` marks the pre-registered simulations and the journeys whose size is the point; every `arc_close` test is also `slow`; `scripts/check_gate_partition.py` checks the landing gate (`not arc_close`) and the arc-close gate together run every test once |
| durability lane | `@pytest.mark.durability` / `--durable-sqlite` run tests and fixtures of every scope with production SQLite pragmas and fresh vaults (`tests/test_sqlite_test_mode.py`) |
| vault template equivalence | the per-session basic-vault copy equals a fresh build (`tests/test_vault_template.py`) |
| desktop lifecycle tests | vitest + jsdom tests beside the React sources (`npm test`) |

## Verification commands

```bash
.venv/bin/pytest -q -n 8 --dist worksteal -m "not arc_close"   # the landing gate
.venv/bin/pytest -q -n 8 --dist worksteal -m arc_close         # at each arc's close: pre-registered sims, long journeys
.venv/bin/pytest -q -m durability
.venv/bin/lint-imports --no-cache
.venv/bin/ruff check
.venv/bin/python -m compileall -q src scripts tests
git diff --check
(cd apps/learnloop-tauri && npm test)
```

These commands define the current verification procedure. A dated CI/release artifact—not this conceptual note—must own any claim about a particular full-suite count; see [[Refactor Status#Verification]].

## Test placement guidance

- Put a behavior test near its domain's existing suite.
- Add a synthetic negative architecture test when adding a new detector; prove the detector fails on a fabricated violation.
- Prefer frozen clocks, stubbed runner services, and local provider fakes over sleeps/network.
- Use migration-head fixtures for schema policy and historical fixtures for compatibility/upgrades.
- The default test vault, `tests/helpers.py`'s `create_basic_vault` (and the per-session template copied from it), is at the head tag, the one `learnloop init` writes (`LATEST_ALGORITHM_VERSION`), with its item's `recall` facet registered in `facets.yaml`. `helpers.ALGORITHM_VERSION` is that tag, not `AlgorithmsConfig`'s field default, which is older than every real vault. A test of an older tag's path pins it explicitly: `set_algorithm_version(paths, tag)`, or `pin_old_basic_vault(paths)` for the pre-head basic vault (`mvp-0.6` with an empty facet registry, byte for byte). Refactor step D2a moved it; `docs/reviews/refactor-d2a.md` lists the pinned tests and `docs/reviews/refactor-d2b.md` what became of them.
- A test of a predecessor that a kill switch still serves runs on the head vault with that switch off (`helpers.set_config_switch(root, "table.key", False)`), not on an old tag, so it goes with the switch (D7) and never holds back the oldest supported tag. Only a behaviour gated by a tag alone (no switch) pins an old tag.
- On a head vault a reader of facet belief reads the canonical cache: seed it with `tests/canonical_facet_helpers.seed_canonical_facet_recall`, which writes through the projection's own writer (anything that re-projects, such as an attempt, rewrites it, so seed after). An end-to-end test whose model is the in-process HTTP server and grades on the head calls `tests.http_provider_double.serve_structured(monkeypatch)`, so the double can be the learner-blind grader.
- A refactor test should compare observable outcomes, not merely new import paths.

## When changing algorithms

Follow [[Algorithm Versions and Reproducibility#Change protocol]]. In particular, a same-version rebuild must reproduce the golden projection; a new version needs a predecessor-to-successor fixture, its line in the effective-defaults golden (`tests/goldens/effective_defaults.toml`), shadow diff, and simulation evidence.

> [!important] Green is necessary, not semantic approval
> Reproducibility tests prove that the code consistently implements a version. They do not prove a new policy helps learners. Use the simulation/evaluation library and owner-reviewed shadow diffs for that decision.

## Important anchors

- [[Developer Map]]
- [[Package Boundaries#Enforced dependency rules]]
- [[State and Persistence#Replay and rebuild]]
- [[AI Architecture#Output trust boundary]]
- [[ADR-009 Architecture rules are executable ratchets]]
