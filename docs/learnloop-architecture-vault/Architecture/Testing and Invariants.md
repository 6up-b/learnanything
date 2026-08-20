---
title: Testing and Invariants
aliases:
  - Verification Architecture
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-18
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - tests
  - pyproject.toml
  - REFACTOR_PROPOSAL.md
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
| CLI help snapshot | 168 root/group/command surfaces |
| sidecar JSON snapshot | protocol output for queue/practice/reader |
| migration process tests | two-process serialization, death rollback, FK restoration |

## Verification commands

```bash
.venv/bin/pytest -q
.venv/bin/lint-imports --no-cache
.venv/bin/python -m compileall -q src scripts tests
git diff --check
```

These commands define the current verification procedure. A dated CI/release artifact—not this conceptual note—must own any claim about a particular full-suite count; see [[Refactor Status#Verification]].

## Test placement guidance

- Put a behavior test near its domain's existing suite.
- Add a synthetic negative architecture test when adding a new detector; prove the detector fails on a fabricated violation.
- Prefer frozen clocks, stubbed runner services, and local provider fakes over sleeps/network.
- Use migration-head fixtures for schema policy and historical fixtures for compatibility/upgrades.
- A refactor test should compare observable outcomes, not merely new import paths.

## When changing algorithms

Follow [[Algorithm Versions and Reproducibility#Change protocol]]. In particular, a same-version rebuild must reproduce the golden projection; a new version needs a predecessor-to-successor fixture, defaults fingerprint, shadow diff, and simulation evidence.

> [!important] Green is necessary, not semantic approval
> Reproducibility tests prove that the code consistently implements a version. They do not prove a new policy helps learners. Use the simulation/evaluation library and owner-reviewed shadow diffs for that decision.

## Important anchors

- [[Developer Map]]
- [[Package Boundaries#Enforced dependency rules]]
- [[State and Persistence#Replay and rebuild]]
- [[AI Architecture#Output trust boundary]]
- [[ADR-009 Architecture rules are executable ratchets]]
