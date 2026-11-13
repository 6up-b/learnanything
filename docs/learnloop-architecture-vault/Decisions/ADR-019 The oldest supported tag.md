---
title: ADR-019 The oldest supported tag
aliases:
  - Oldest supported tag
  - The floor
  - OLDEST_SUPPORTED
status: active
doc_version: 1.1.0
implementation_version: mvp-0.58
decision_date: 2026-11-12
decision_status: accepted
amends: ADR-012 Freeze the compatibility substrate
last_reviewed: 2026-11-12
source_commit: 16a9e3fd48356ac09ef57d2a855e5c9ee01c128e
source_commit_timestamp: "2026-11-12T15:04:51-05:00"
source_paths:
  - src/learnloop/algorithm_versions.py
  - src/learnloop/version_floor.py
  - src/learnloop/vault/loader.py
  - src/learnloop/activation_journal.py
  - src/learnloop/ops/doctor.py
  - src/learnloop/remote/runtime.py
  - src/learnloop_mobile/host.py
  - src/learnloop_sidecar/handlers/app.py
  - src/learnloop/substrate/shadow_rebuild.py
  - src/learnloop/cli/app.py
  - src/learnloop/ops/upgrades.py
  - tests/test_version_floor.py
  - tests/test_upgrades.py
  - tests/helpers.py
  - docs/reviews/refactor-d1.md
  - docs/reviews/refactor-d3.md
tags:
  - learnloop/decision
  - learnloop/algorithm
  - learnloop/compatibility
---

# ADR-019 The oldest supported tag

## Context

Every algorithm successor since `mvp-0.9` kept its predecessor's code reachable: an upgrade module per link (`learnloop upgrade` walks the chain), a tag gate wherever behaviour changed, and a kill switch that serves the predecessor exactly. Any vault, at any tag, could be opened and served. The owner's vaults are all far past most of those tags (Nov 12: the live ones at `mvp-0.54` to `mvp-0.57`, the retired ones at `mvp-0.6` and `mvp-0.8`), so most of that code serves no vault, while the test suite mostly checks it (refactor strategy v3, finding 3).

## Decision

One constant, `algorithm_versions.OLDEST_SUPPORTED`, names the oldest tag a vault is opened at (the floor). It is `mvp-0.58`, the chain's head when it landed; the owner upgraded all three live vaults to it on 2026-11-12. Moving it is that one line.

- **A vault below the floor is refused at open** with `learnloop.version_floor.BelowOldestSupported`, which names the vault's tag, the floor and the commands that bring the vault there. Every door checks: `load_vault` (every CLI command, the desktop sidecar, the TUI, scripts, and the MCP server's and phone host's per-request loads), `learnloop doctor` before `--fix-state` writes anything, the MCP server's and phone host's attach (as their own `SchemaMismatch`, exit 78, so a supervisor does not restart them in a loop), and the desktop's `initialize` (error code `vault_below_oldest_supported`).
- **A vault whose `learnloop.toml` names no `algorithm_version` is refused the same way.** `learnloop init` always writes the key and the upgrade only rewrites it in place, so only a vault from before the key lacks it; the field's default exists for configs built in code and never stands for a vault's tag.
- **A journal of an unfinished upgrade from below the floor is refused the same way**: completing it runs that link's upgrade code, which is old-vault code.
- **A shadow rebuild cannot be forced below the floor** (`--set algorithms.algorithm_version=...` below it is refused).
- **Nothing on this code opens a vault below the floor, `learnloop upgrade` included** (amended by refactor D3: the upgrade chain has left the code). The refusal names the route through the code tagged `pre-floor` (below): `git worktree add ../learnloop-pre-floor pre-floor`, then `uv run --directory ../learnloop-pre-floor learnloop upgrade --vault <path>` (preceded by its `--to mvp-0.7`, `--to mvp-0.8` and `--to mvp-0.9` for a vault older than the chain), then open the vault here. `version_floor.upgrade_commands` is the one place that names the route.

## The upgrade table (refactor D3)

The upgrade from the floor up is one table, `learnloop.ops.upgrades.UPGRADES`: a row `Link(tag, activate)` per successor, its predecessor the tag before it in `SUCCESSOR_CHAIN` (the first row's is the floor), `activate` one of `idempotent_projection`, `whole_vault_rebuild` or an `Activation` of its own. Every row activates the same way: one transaction under the vault mutation lock, the journal written before the config's publication, the publication last, completion read from the activation's own receipt; the CLI and the desktop sidecar install the table's completion for an interrupted activation. `learnloop upgrade` walks the rows from the vault's tag. It replaced 47 upgrade modules (one per link from `mvp-0.7`, each a copy of the same journal, transaction and publication) and the CLI's 48-branch dispatch. A new tag is one constant, one row and one test row; `tests/test_upgrades.py` runs every kept property over every row on one small vault.

When the floor rises, the rows at or below it go with the gates and kill switches (the rule below), so the table always starts at the floor.

## Restoring a backup below the floor

A vault below the floor is upgraded by the code that still has every link: the annotated git tag `pre-floor`, the last commit before the chain left (the refactor's orchestrator creates it when D3 lands; no agent creates or pushes it).

1. Restore the backup to its own folder (never over a live vault).
2. Check out `pre-floor` in a separate worktree (`git worktree add ../learnloop-pre-floor pre-floor`), `uv sync` there, and run `uv run learnloop upgrade --vault <restored vault>` from it (with the `--to` steps the refusal names for a vault older than `mvp-0.9`).
3. Open the upgraded vault with the current code. It is at `pre-floor`'s latest tag, at or past the floor; `learnloop doctor` and `learnloop rebuild --shadow --json` check it, and `learnloop upgrade` takes it on from there if the current code has later rows.

The refusal at every door prints steps 2's commands for the vault's own path (`version_floor.upgrade_commands`).

**What `pre-floor` can and cannot do.** At that tag only `learnloop upgrade` opens a vault below the floor (its `version_floor.upgrading` allowance); every other command there refuses it, as here. So a link whose upgrade refuses until another command has run cannot be completed by running that command. Read from the tagged code, one link does that: `mvp-0.12`'s same-cause guard. With `recurrence.require_guard = true` and the guard not passed for the configured judge, that upgrade refuses and asks for `learnloop recurrence guard` (`--from-run` for the citation path), which is refused below the floor at `pre-floor` and on this code. The only route is the tag's documented switch: set `recurrence.require_guard = false` under `[recurrence]` (the default since 2026-10-12), and the upgrade reports the guard's status as notes and proceeds. A vault that must keep the guard required cannot be upgraded through `pre-floor`; the guard's verdicts can be recorded once it is at the floor. The refusal names this for a vault below `mvp-0.12` whose config requires the guard. No other link's refusal asks for a command: `mvp-0.7`'s readiness problems are vault files to edit (unregistered evidence facets, incomplete facet contracts), and the same-cause judge's model is a config setting (`ai.routing.same_cause_judge`), consulted only while the guard is required.

## The floor follows the vaults

A standing rule (owner-approved, refactor strategy v3 §2.18 L7): when the owner's `scripts/vault_report.py` shows every live vault at or past a tag, one chore step raises `OLDEST_SUPPORTED` to it and removes the gates and kill switches at or below it. The floor is not set once; each successor adds a gate and a switch, and this keeps the next floor move a single step.

## Consequences

- Code that serves only tags below the floor is unreachable for any opened vault, so the gates, kill switches and upgrade links below it can be removed (refactor D3 removed the links; D4 to D7 the gates and switches). Removing them changes nothing for a vault that opens.
- Tests that build a vault below the floor on purpose (upgrade and successor tests, the pinned old-path tests) register it through `tests/helpers.py`'s `allow_below_floor`, the suite's one allowance; `set_algorithm_version` and `pin_old_basic_vault` call it for an old tag. It keeps the root registered and, until that test ends (`tests/conftest.py` closes it), lets any vault open, since such tests also open copies of their vault. Production code never does (`tests/test_version_floor.py`). Retiring old code means emptying that allowance's callers; `docs/reviews/refactor-d1.md` counts them (5,421 test cases in 507 files when the floor landed).
- [[ADR-012 Freeze the compatibility substrate]] is amended: "old vaults stay green" now means vaults at or above the floor. Row readers that read old rows by shape stay (replay reads history written at any tag).

## Enforcement

`tests/test_version_floor.py`: each door, `learnloop upgrade` included, refuses a vault just below the floor with the three parts of the message and the `pre-floor` route; a vault at the floor and at the head opens; a keyless config is refused; a journal below the floor is refused, by the upgrade command too, and one from the floor is still completed; a forced shadow rebuild below the floor is refused; nothing in `src/` or `scripts/` calls the test allowance. `tests/test_upgrades.py`: every row of the upgrade table (jumps refused, journal before publication and publication last, recovery after a death at each point, an idempotent re-run, an old config readable when preparation fails, every opener completing or refusing). See [[Algorithm Versions and Reproducibility#The oldest supported tag]] and [[Algorithm Versions and Reproducibility#The upgrade table]].
