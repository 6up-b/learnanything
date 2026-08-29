---
title: Deliberate Canonical Import Session
aliases:
  - Canonical Markdown Import Example
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - research_on_learning.md
  - src/learnloop/content/pipeline/runner.py
  - src/learnloop/content/pipeline/source_ingestion.py
  - src/learnloop/cli/source_set.py
  - tests/test_ingest_runner.py
  - tests/test_source_sets.py
tags:
  - learnloop/example
  - learnloop/ingest
  - learnloop/content
---

# Deliberate Canonical Import Session

This run was checked against a disposable mvp-0.9 vault using the repository file `research_on_learning.md`. Returned ids below are representative receipts from that run; your ids will differ.

## Prerequisites

- `$VAULT` points to a healthy initialized vault
- subject id `linear-algebra` exists in that vault
- current directory is the repository root

## Import and capture receipts

```bash
SOURCE="$(pwd)/research_on_learning.md"

uv run learnloop import "$SOURCE" \
  --subject linear-algebra \
  --json --vault "$VAULT"
```

The verified run produced these identities:

```text
batch_id      batch_01M09EBB7Q7GT0PWNXAVYPQXPB
job_id        ijob_01M09EBB7ST7Y683B9AW0335KK
source_id     src_01M09EBB8QSNR0ZQ1CVQVQQK9C
revision_id   rev_01M09EBB8W62ARQZVKT953FRCR
extraction_id ext_01M09EBB9RWF0AS4ZE9KGN8ASN
```

Its completed result reported 65 blocks, one unit, and a SHA-256-addressed raw asset. Do not reuse these sample ids in commands; substitute your response values.

## Inspect batch and outline

```bash
BATCH=<batch-id>
EXTRACTION=<extraction-id>

uv run learnloop ingest-batches show "$BATCH" --json --vault "$VAULT"
uv run learnloop source-outline "$EXTRACTION" --json --vault "$VAULT"
```

The outline in the verified run reported extractor `text` version `2`, 65 blocks, no health flags, and unit `u1` labelled `Document`. This command is deterministic and performs no model call.

## Verify the canonical ledger read-only

```bash
sqlite3 -readonly "$VAULT/state.sqlite" <<'SQL'
.headers on
.mode box
SELECT id, workflow_type, status, subject_id
FROM ingest_batches ORDER BY created_at DESC LIMIT 1;
SELECT id, job_type, status, phase, attempt_count
FROM ingest_jobs ORDER BY created_at DESC LIMIT 1;
SELECT id, revision_id, extractor, extractor_version, status
FROM source_extraction_runs ORDER BY created_at DESC LIMIT 1;
SQL
```

Expected statuses are `completed`, and the job phase is `extracted`. See [[Import Canonical Sources#Inspect the batch and extraction]] for the filesystem observations.

## Pin the exact revision

```bash
SOURCE_ID=<source-id>
REVISION_ID=<revision-id>

uv run learnloop source-set create learning-science \
  --subject linear-algebra \
  --title "Learning Science" \
  --json --vault "$VAULT"

uv run learnloop source-set add learning-science \
  --source "$SOURCE_ID" \
  --revision "$REVISION_ID" \
  --role primary_textbook \
  --unit u1 \
  --json --vault "$VAULT"
```

Observable: `$VAULT/sources/source_sets.yaml` now contains set `learning-science`, the exact revision id, role, and unit scope.

## Preview the build before spending model calls

```bash
uv run learnloop build-plan "$EXTRACTION" \
  --subject linear-algebra --json --vault "$VAULT"

uv run learnloop source-coverage learning-science \
  --json --vault "$VAULT"
```

The build plan reports routing, selected units, inventory/synthesis stages, and estimated calls/tokens. It does not synthesize. If coverage is ready and the configured route passes [[Configure AI Providers]], continue with:

```bash
uv run learnloop synthesize learning-science \
  --mode auto --json --vault "$VAULT"
```

Review the staged candidate before adding `--apply`; follow [[Build a Study Map#Apply deliberately]].

## Idempotency check

Repeating the same import should return reuse flags and completed canonical identities rather than duplicate the revision/extraction. Confirm row counts before and after if testing this guarantee. Resume a failed original batch instead of manufacturing a new one; see [[Import Canonical Sources#Resume, cancel, and retry]].

^canonical-import-example

