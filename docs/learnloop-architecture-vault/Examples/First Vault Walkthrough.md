---
title: First Vault Walkthrough
aliases:
  - New User Vault Example
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - README.md
  - research_on_learning.md
  - src/learnloop/bootstrap.py
  - src/learnloop/cli/app.py
  - tests/test_init.py
  - tests/test_cli_ingest.py
tags:
  - learnloop/example
  - learnloop/onboarding
  - learnloop/vault
---

# First Vault Walkthrough

This is the shortest auditable path from a checkout to a healthy vault with one extracted canonical source. For rationale and alternatives, open [[Initialize a Vault]] and [[Import Canonical Sources]].

## Prerequisites

- Python 3.12+
- `uv`
- this repository checkout, including `research_on_learning.md`
- an unused path; the example uses `$HOME/LearnLoop/learning-science-demo`

## 1. Install and expose the CLI

```bash
uv sync --extra dev
uv run learnloop --help
```

Observable: help exits successfully and lists `init`, `doctor`, and `import`.

## 2. Create the vault and first subject

```bash
VAULT="$HOME/LearnLoop/learning-science-demo"

uv run learnloop init "$VAULT" \
  --subject "Learning Science" \
  --starting-level new_to_this \
  --level-note "Starting from the repository's canonical reading."
```

Verified output shape:

```text
Initialized LearnLoop vault at /…/learning-science-demo
```

Check the key artifacts:

```bash
test -f "$VAULT/learnloop.toml"
test -f "$VAULT/state.sqlite"
test -f "$VAULT/profile/learner.yaml"
test -f "$VAULT/subjects/learning-science/subject.md"
find "$VAULT/subjects/learning-science" -maxdepth 1 -type d | sort
```

Expected subject directories include `learning-objects`, `notes`, and `practice-items` even though they are initially empty. The full creation contract is [[Initialize a Vault#Lifecycle effects]].

## 3. Verify before adding content

```bash
uv run learnloop config effective --only-overrides --json --vault "$VAULT"
uv run learnloop doctor --json --vault "$VAULT"
```

Expected structural result:

```json
{
  "clean": true,
  "errors": [],
  "warnings": []
}
```

The real response includes additional fields; assert the fields above rather than matching the entire object.

## 4. Check the AI operating mode

```bash
uv run learnloop doctor --ai --json --vault "$VAULT"
```

- `ai_runtime.ready: true` means model-backed inventory/synthesis can proceed.
- `provider_auth_required` means follow [[AI Provider Configuration Recipes#OpenAI-compatible profile]].
- to work without a model for ordinary practice, follow [[AI Provider Configuration Recipes#Manual mode]].

## 5. Import the repository sample

```bash
SOURCE="$(pwd)/research_on_learning.md"

uv run learnloop import "$SOURCE" \
  --subject learning-science \
  --json --vault "$VAULT"
```

Save `batch.id`, `jobs[0].result.source_id`, `revision_id`, and `extraction_id` from the response. Then:

```bash
uv run learnloop ingest-batches show <batch-id> --json --vault "$VAULT"
uv run learnloop source-outline <extraction-id> --json --vault "$VAULT"
```

Observable files and state:

- `canonical-sources/raw/sha256-…` exists;
- batch and import job are `completed`;
- the outline has ordered blocks and at least one source unit;
- `sources/source_sets.yaml` does **not** exist until the next deliberate pinning step.

## 6. Continue, without skipping review

Follow [[Deliberate Canonical Import Session#Pin the exact revision]] to create the source set, then [[Build a Study Map]]. Once the candidate is applied, use [[First Learning Session]].

> [!warning] Honest stopping point
> A successful extraction is not yet a study map and creates no mastery. Do not expect `review` to select the imported prose until synthesis has produced and applied practice items.

^first-vault-stopping-point

