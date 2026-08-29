---
title: Initialize a Vault
aliases:
  - Install and Initialize LearnLoop
  - Vault Creation Workflow
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - README.md
  - pyproject.toml
  - src/learnloop/bootstrap.py
  - src/learnloop/vault/loader.py
  - src/learnloop/config/template.py
  - src/learnloop/migration_coordinator.py
  - src/learnloop/vault_lock.py
  - tests/test_init.py
  - tests/test_migrations.py
  - tests/test_migration_coordinator.py
tags:
  - learnloop/workflow
  - learnloop/onboarding
  - learnloop/vault
---

# Initialize a Vault

This workflow installs the development build, creates an mvp-0.9 vault, and verifies the result before any source or learner history is added. For what a vault owns over its lifetime, see [[Vault Lifecycle]]; for each configuration field, see [[Configuration]].

## Prerequisites

- Python 3.12 or newer
- [`uv`](https://docs.astral.sh/uv/) on `PATH`
- a local checkout of this repository
- a new or intentionally reusable directory for the vault

> [!info] Desktop option
> The desktop Start screen has a **New Vault** wizard and can create the first subject. The CLI below is the reproducible path and is easier to audit.

## 1. Install the development environment

From the repository root:

```bash
uv sync --extra dev
uv run learnloop --help
```

The second command should show `init`, `doctor`, `import`, `review`, `attempt`, and the other current command groups. No virtual-environment activation is required.

## 2. Choose the vault path and initialize

```bash
VAULT="$HOME/LearnLoop/linear-algebra"

uv run learnloop init "$VAULT" \
  --subject "Linear Algebra" \
  --starting-level some_exposure \
  --level-note "Completed an introductory course."
```

Allowed starting levels are `new_to_this`, `some_exposure`, `comfortable`, and `strong_background`. The subject name is normalized to the directory id `linear-algebra`.

> [!warning] Existing paths
> Initialization refuses a populated non-vault directory by default. `--force` permits adding the LearnLoop scaffold inside that directory, but it **never** permits replacing an existing file or overwriting guarded scaffold/configuration. Existing vaults are completed idempotently. Inspect the target first instead of adding `--force` reflexively.

## 3. Observe the filesystem contract

```bash
find "$VAULT" -maxdepth 3 -type f | sort
```

A fresh vault contains at least:

```text
.learnloop/vault.lock
AGENTS.md
concepts/concepts.yaml
concepts/relations.yaml
errors/error_types.yaml
facets.yaml
learnloop.toml
profile/goals.md
profile/goals.yaml
profile/learner.yaml
state.sqlite
subjects/linear-algebra/concept-graph.yaml
subjects/linear-algebra/subject.md
```

It also creates empty `rubrics/`, `subjects/linear-algebra/learning-objects/`, `notes/`, and `practice-items/` directories. The migration coordinator creates `.learnloop/vault.lock` as the advisory lock target and leaves it unlocked/empty after initialization. `profile/learner.yaml` records the starting-level claim; the same claim is inserted into the SQLite evidence ledger with a deliberately weak prior.

> [!important] Fresh-version invariant
> A new vault already has `algorithm_version = "mvp-0.9"`. Do not run `upgrade` as a routine initialization step. `upgrade` exists for older vaults and only accepts the immediate successor; see [[Doctor Migrations and Recovery#Algorithm upgrades are separate]].

## 4. Verify config and schema health

```bash
uv run learnloop config effective --only-overrides --json --vault "$VAULT"
uv run learnloop doctor --json --vault "$VAULT"
```

On a clean vault, `doctor` reports `clean: true`, no errors or warnings, and all current SQL migrations through migration head `156`. Migration numbers have intentional gaps, so a migration-row count is not expected to equal 156.

To inspect rather than mutate the database:

```bash
sqlite3 -readonly "$VAULT/state.sqlite" \
  'SELECT MAX(version) AS migration_head FROM schema_migrations;'
```

## 5. Decide the next branch

- Check or change the model route in [[Configure AI Providers]].
- Add authoritative material with [[Import Canonical Sources]].
- If this is a fixture or pre-populated vault, proceed to [[Start a Learning Cycle]].

## Lifecycle effects

| Area | Created or changed |
|---|---|
| configuration | `learnloop.toml` with schema v2 and mvp-0.9 defaults |
| identity/profile | learner claim plus optional first subject |
| durable state | `state.sqlite`, SQL migration receipts, initialization evidence |
| knowledge files | empty concept/facet/error/rubric and subject structures |
| locking | `.learnloop/vault.lock` used by later mutating operations |

^init-effects

> [!example] Fully worked run
> [[First Vault Walkthrough]] continues these commands through import, source pinning, and the first readiness check.

## Behavior-defining tests

- `tests/test_init.py` defines the generated layout and default-version behavior.
- `tests/test_migrations.py` defines the schema history applied to a fresh database.
- `tests/test_migration_coordinator.py` defines lock and crash-atomicity behavior.

## Related notes

- [[Configuration]]
- [[Vault Lifecycle]]
- [[State and Persistence]]
- [[Doctor Migrations and Recovery]]
