# LearnLoop architecture

LearnLoop is organized around the boundaries that own behavior, not around a
generic service layer. Provider-neutral AI transport, routing, and shared wire
machinery live in `learnloop.ai`; each structured operation's context, prompt,
and result contract live with its owning domain. SQLite mechanics live in
`learnloop.db`, and learning behavior lives in the domain packages listed
below. The command-line, TUI, and sidecar layers are adapters over those public
APIs.

## Package map

```text
learnloop/
  ai/                    structured transport, routing, providers, usage
  config/                typed schema, compatibility normalization, template
  db/                    connections, migrations, table roles, stores
  ingest/                acquisition IR, locators, fetchers, extractors
  vault/                 filesystem layout and Markdown/YAML I/O

  attempts/              grading, evidence, and interaction acceptance
  learner/               mastery, recall, claims, and learner-state views
  scheduling/            selection, controller, progression, and review
  goals/                 forecasts, certification, and exams
  diagnosis/             probes, causal attribution, and remediation
  curriculum/            commitments, blueprints, depth, and golden paths
  substrate/             activity/card/surface identity and projections
    compat/              frozen old-vault compatibility machinery
  content/               source pipeline, synthesis, proposals, authoring
  reader/                reader workflows
  tutor/                 tutoring and teach-back workflows
  ops/                   vault diagnostics, locking, settings, and upgrades
  params/                parameter registry, fitted values, sensitivity

  cli/                    Typer entry point
  tui/                    Textual entry point
  sim/                    evaluation library
```

`learnloop.bootstrap` is the application-level vault creation coordinator.
`learnloop.algorithm_versions` and `learnloop.causal_activity_policy` are
dependency-neutral authorities shared by persistence and domains.

## Dependency rules

1. Primitives (`clock`, `ids`, `numeric`, `attempt_types`) import no LearnLoop
   internals.
2. Infrastructure (`config`, `vault`, `db`, `ingest`, `ai`) may depend on
   primitives and on lower infrastructure. `db` may decode `ingest` contracts,
   but `db` and `ai` never import domain packages.
3. Domains may import primitives, infrastructure, and public names from other
   domains. Cross-domain underscore-prefixed imports are forbidden.
4. Adapters (`cli`, `tui`, `learnloop_sidecar`) may import infrastructure and
   public domain APIs. They never import one another and never use private
   domain names.

The public `today` command delegates through the neutral
`learnloop.app_launch` coordinator. The CLI, TUI, and sidecar therefore have no
direct imports between adapters.

Function-local cross-domain imports are allowed only by the edge-level legacy
inventory in `tests/architecture_function_local_domain_imports.txt`; its
cycle-forming subset is also frozen by the import-linter contract. Both are
ratchets: entries may disappear, but new edges are not added. Adapter-local lazy
imports are outside that domain-cycle inventory. Runtime-constructed module
paths are executable architecture and are covered by resolution tests.

## Persistence and replay

Each table has a role in `learnloop.db.table_roles`:

- `RAW_LEDGER`: immutable input to replay.
- `DERIVED`: clearable and reproducible from ledgers.
- `RECEIPT`: append-only audit output, never rebuilt in place.
- `WORKFLOW`: queues, sessions, and leases preserved across rebuilds.
- `COMPAT`: frozen historical state.

Every writable table family has one owning store. Cross-family read models are
named explicitly. `Repository` remains a compatibility facade while stores are
extracted; new writes do not expand its monolithic remainder.

The rebuild registry assigns every derived family to exactly one replayer and
runs those replayers in dependency order. Existing automatic replay points are
preserved. Shadow rebuilds operate on a copied database and never mutate the
live vault.

## AI composition

All entry points resolve providers through
`learnloop.ai.routing.ready_client_for_task`. Resolution returns either a ready
client or a typed manual/unavailable outcome. Named profile identity is kept in
agent-run provenance. Provider transports implement the shared structured
completion contract; optional media, interruption, and retained legacy HTTP
operations are advertised explicitly with `supports()`.

AI is optional. Storage, scheduling, replay, and manual practice must remain
usable without a configured provider.

## Compatibility policy

The modules in [`src/learnloop/substrate/compat`](src/learnloop/substrate/compat/README.md)
are kept green for old vaults but are not extended. A behavior change there
requires an explicit compatibility decision and fixture-backed tests.

Legacy configuration is accepted as input and normalized into the current
model; new vaults only emit schema version 2. Migration and doctor inspection
use explicit open modes, and plain doctor is physically database-read-only.

The complete rationale and staged migration record live in
[`REFACTOR_PROPOSAL.md`](REFACTOR_PROPOSAL.md).
Changes to persisted algorithm semantics follow the
[`algorithm-change playbook`](docs/algorithm-change-playbook.md).
