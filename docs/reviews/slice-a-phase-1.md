# Slice A Phase 1: implementation plan and checkpoint

## Scope and plan

Branch: `slice-a/phase-1`, created from `main` at `a3c8a867`.
Read: `CLAUDE.md`, the complete Slice A plan, Slice 1 §§9.1–9.2,
9.6 and embedding tests in §14, embedding consumers R1–R3 and §5.8,
the table-role registry, algorithm-change playbook and architecture Home.

1. Add the model-independent embedding contract and OpenRouter embedding
   transport under `src/learnloop/ai/`, including explicit routing, readiness,
   configuration/template defaults, privacy disclosure and call receipts.
2. Add migration `166_embedding_substrate_and_judgments.sql`: float16
   `embedding_vectors` (WORKFLOW) and append-only `judgment_ledger`
   (RAW_LEDGER), with store APIs and exact, model-isolated centered retrieval.
   Upgrade the migration-head fixture through a backup-API copy under
   `fixtures-local/`, retain rollback journal mode, update fixture references
   and regenerate/validate the database documentation.
3. Add reusable spend admission controls (candidate, pair, request/retry,
   token and estimated-cost caps), dry-run estimates and budget receipts.
   Unknown pricing fails closed unless explicitly bounded by the owner.
4. Add `learnloop embeddings backfill`, with a declarative recipe registry
   starting with canonical `facet/definition` and `item/stem`, batched calls,
   content-addressed resume, cancellation and aggregate-only reports.
5. Test clients with fake transports; stores, ledger immutability, spend
   admission, CLI dry-run, resume/idempotence and replay without provider calls.
   Run touched tests, durability tests, import lint and the full parallel suite.

## Invariants and boundaries

- No algorithm successor: scheduling, grading, persisted evidence semantics
  and served content remain unchanged.
- `embedding.enabled` and `embedding.backfill_enabled` default to false.
  PF generation and consumers belong to later phases.
- Rebuild consumes persisted inputs and never invokes embeddings or judges.
- Embeddings nominate/rank only; never decide identity, novelty or difficulty.
- No reads from the owner's settings or searches for their vault; no paid
  provider calls during implementation. Never modify tracked working vaults.
- Only the migration-head fixture is replaced under the documented procedure.
- No push, merge, or work on subsequent phases.

## Completion report

Implementation details, deviations, verification results, owner commands and
open questions will be recorded here before the checkpoint.
