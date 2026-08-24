
## Goal

Collect consenting users' cumulative `state.sqlite` databases with almost no
setup for the user, then collate them into research datasets that can inform
future LearnLoop scheduling, diagnosis, grading, and other learned algorithms.
This research transport is separate from GitHub and from any personal
laptop/desktop synchronization.

## Proposed flow

```text
LearnLoop vault
    -> consistent SQLite backup
    -> authenticated HTTPS upload
    -> Cloudflare Tunnel
    -> Raspberry Pi collector on the local network
    -> validated current database per user/vault
    -> learnloop-research collation
    -> DuckDB/Parquet research datasets
```

The Raspberry Pi runs a small upload service bound to localhost. A Cloudflare
Tunnel gives it a stable public HTTPS endpoint without opening inbound router
ports. The Pi can initially use its 64 GB SD card because it stores only
`state.sqlite`, manifests, and small logs rather than full vault source files.

## User onboarding

The collector generates a revocable invite code for each user. The code encodes
the collector endpoint and an authentication token tied to a contributor ID.
The user pastes the code into a LearnLoop **Research sharing** setting and
enables uploads; no Syncthing or server configuration is required on their
machine.

LearnLoop should show the connection state, last successful upload, and last
error. Uploads happen periodically when the database has changed, retry safely
after network failures, and use the database content hash as an idempotency key.

## Client upload

LearnLoop must not copy or upload a live database file directly. It should use
SQLite's backup API to create a consistent temporary `state.sqlite`, run
`PRAGMA quick_check`, calculate its SHA-256, and upload it with a small manifest:

- contributor and vault identifiers;
- capture time;
- database hash and size;
- LearnLoop application version;
- schema/migration head;
- algorithm version; and
- upload/export format version.

The temporary backup is removed after a successful upload. A retry of the same
hash is harmless.

## Collector behavior and logging

The Pi streams an upload to a temporary file, checks the token and declared
size/hash, validates that it is a healthy SQLite database, and atomically
publishes it only after validation. It keeps an upload catalog containing:

- contributor ID and vault ID;
- received time and originating capture time;
- database hash, byte size, and validation result;
- application, schema, and algorithm versions;
- whether the upload was new or a duplicate; and
- processing/collation status and error details.

The service should also keep bounded operational logs for authentication
failures, rejected uploads, request duration, bytes received, disk usage, and
collation failures. Tokens are stored hashed and can be revoked independently.

Suggested storage layout:

```text
/srv/learnloop-research/
├── current/<contributor>/<vault>/state.sqlite
├── boundaries/<algorithm-version>/<contributor>/<vault>/state.sqlite
├── manifests/
├── catalog.duckdb
├── incoming/
└── logs/
```

## Snapshot retention

The normal policy is **latest validated database per contributor/vault**, not a
daily archive. `state.sqlite` is cumulative and its authoritative learning
history is predominantly append-oriented, so the newest database already
contains the attempt, evidence, decision, and outcome history needed for normal
research collation.

Keep the immediately previous file only until the replacement passes validation
and backup. Preserve an explicit boundary snapshot when a major algorithm or
schema change could alter interpretation, backfill data, or change replay
semantics. Those boundary snapshots make before/after analysis and old-algorithm
reproduction possible without retaining every routine upload.

This assumption applies to durable history-bearing records; some workflow and
derived tables are mutable. If future research needs to study their transitions,
the collation step should extract those transitions before replacing the current
snapshot, or the retention policy should be expanded for those specific tables.

## `learnloop-research` collation

A separate `learnloop-research` tool reads only validated collector files. It
records the source hash, makes a disposable copy, migrates that copy to the
schema understood by the research checkout, and collates across users while
namespacing every local ID by contributor and vault.

Initial commands could be:

```bash
learnloop-research status
learnloop-research collate
learnloop-research build scheduler
learnloop-research build retention
learnloop-research build diagnosis
learnloop-research build grading
```

The durable outputs are normalized Parquet datasets plus a DuckDB catalog for
interactive analysis. Full raw SQLite remains available for inspection, while
model-specific datasets avoid duplicate rows caused by each database containing
the user's cumulative history.

## Initial implementation boundary

1. Pi upload API with token-based invites and Cloudflare Tunnel deployment.
2. LearnLoop invite-code UI and periodic SQLite-backup upload.
3. Latest-only validated storage with major algorithm/schema boundary snapshots.
4. Upload/catalog logging and disk-space safeguards.
5. `learnloop-research collate` producing normalized attempts, grading,
   scheduler/controller decisions, interventions, and outcomes.
6. Periodic copy of the Pi's current databases, boundary snapshots, and catalog
   to the desktop so the SD card is not the only copy.

