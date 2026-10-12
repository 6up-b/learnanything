# Slice 2 T5: Codex review fixes

Branch `slice-2/t5`, worktree `learnanything-t5`. Review job
`codex-agent/jobs/20261012-123333-qg5MbT`, against the stage as gated at
`858645b9`. Each finding was reproduced first with a failing test (all six
failed on `858645b9`), then fixed, one commit per finding. Tests use fakes
only. No paid call was made: the one manual run (the new dry run on the
`fixtures-local/t5-linear_algebra` backup copy) constructs no client.

## Review

### Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Bootstrap cache bypasses the nomination kill switch | fixed | `5db6cb62` (+ `d1361ed2`) | `tests/test_graph_nomination_ingest.py`: `test_kill_switch_never_reuses_a_nominated_bootstrap`, `test_enabling_nominations_or_completing_the_index_is_a_new_bootstrap`, `test_registry_definition_change_is_a_new_bootstrap_and_repeats_reuse`; `test_kill_switch_restores_the_pre_t5_request` now pins the pre-T5 manifest scope |
| F2 | Medium | Embedding usage counters invalidate identical append runs | fixed | `34082789` | `test_identical_append_reuses_its_completed_run[True/False]` (append twice, `auto_apply=False`: reused, same proposal, zero model and embedding calls) |
| F3 | Medium | Registry merges proceed after their judgment transaction fails | fixed | `9d28c017` | `test_registry_merge_is_declined_when_its_verdict_cannot_be_ledgered[1/2]` (`OperationalError` on the first, and on the second, verdict write) |
| F4 | Medium | Append concept queries embed bare labels and discard their definitions | fixed | `15e09edf` | `tests/test_graph_nomination.py`: `test_concept_queries_carry_their_linked_definitions` ("ring" as algebra vs network topology); `test_inventory_queries_are_deterministic_and_deduplicated` updated |
| F5 | Medium | Backfill repays for vectors already purchased during ingest | fixed | `022a0a3a` | `test_backfill_reuses_a_vector_paid_at_ingest_under_another_id` (store level); `test_backfill_after_apply_reuses_the_vectors_paid_at_ingest` (synthesis with nominations, apply, backfill with zero calls) |
| F6 | Medium | New ingest embedding charges have no dry-run path | fixed | `57b0b27a` (+ `8fdb14d4`) | `test_bootstrap_dry_run_plans_ingest_embedding_without_a_client`, `test_append_dry_run_estimates_known_queries_without_a_client`, `test_synthesize_dry_run_cli_prints_the_plan_and_resolves_no_provider` |

No finding was rejected. The "claims that don't hold" in the review are the
same six defects; each now holds and is tested.

### What changed, by finding

- **F1 (bootstrap cache identity).**
  - **Order.** `_create_study_map` now builds the nominator before the
    manifest, so the completed-run cache lookup sees it.
  - **Identity.** With nominations on, the manifest scope becomes
    `{"brief_scope": <the brief's scope>, "graph_nomination": <identity>}`.
    `GraphNominator.identity()` holds the version, mode, status, embedding
    model, dimensions and route, the whole `[graph_nomination]` configuration,
    the registry prompt version, and for `facet/definition` and
    `concept/definition` the index status plus a digest of every current
    record's definition content hash. So the switch, a completed or broken
    index, and a changed registry definition each mint a new manifest.
  - **No usage in identity.** Usage counts, charges and notes are not
    identity.
  - **Kill switch.** With nominations off, the scope is the brief's, exactly
    as before T5, so existing manifest hashes do not move. There is no new
    manifest column and no migration.
  - **Shards.** Shard checkpoints are still reused across the switch.
    Nominations never reach a shard; only the structuring pass runs again.
- **F2 (append identity).**
  - **What is identity.** The neighbourhood's manifest record carries
    `identity()`, not `summary()`. Once queries have been compared, that
    includes a digest of `(recipe, query content hash, had a vector)`. A
    first run that paid for its vectors and a repeat that finds them stored
    compare the same thing.
  - **Where counts go.** Counts and charges stay in the run's
    `coverage_decisions.graph_nomination.summary`. The report reads them
    there.
  - **Result.** The identical append is reused, with the same proposal and
    no reconciliation or embedding call.
- **F3 (ledger durability).**
  - **Verdicts.** `_record_registry_merge_verdicts` writes every verdict in
    one transaction and returns `ledger_write_failed:<type>` on `sqlite3.Error`
    or `ValueError`.
  - **Declines.** On failure the caller declines every registry merge. The
    candidate stays its own concept, and the run's usage records
    `registry_merges_declined` and `registry_merge_decisions_unrecorded`
    (candidate, registry id, rationale, guard result) for the owner.
  - **Paid work.** The paid synthesis still completes. No unrecorded merge
    reaches a proposal.
  - **Retry.** Declining was chosen over retry: a retry key would need
    somewhere durable to wait, and the failure is the database itself.
- **F4 (definitions, not labels).**
  - **Query text.** A concept mention's query is its name, aliases and the
    statements of the claims that link to it through `concept_mention_ids`.
    Definition claims come first; other linked claims are used only when
    there is none. At most three statements are used, in the
    `concept/definition` layout, as query version 2.
  - **Same name, two meanings.** Each meaning is its own query.
  - **No definition.** A mention no claim defines gets no query and keeps
    today's lexical match. The nominator counts it as
    `concept_mentions_without_definition` and notes it.
  - **On the `linear_algebra` copy.** 41 inventories hold 451 mentions.
    185 have no defining claim and are now lexical-only. The rest give 235
    distinct concept queries. 219 of the 359 claims link a mention.
- **F5 (backfill reuse).**
  - **Planning.** `_pending` now splits records into pending and reusable. A
    record is reusable when a vector of the same kind, field, content hash,
    model and prefix is stored under another record id. A reusable record is
    reported as `reused_by_content`, counted as cached, and never estimated
    or sent.
  - **Real run.** The run writes the record's own identity row from the
    stored vector before embedding anything. Identity-keyed consumers such as
    `retrieve()` therefore find it.
  - **Dry run.** A dry run changes nothing.
  - **Changed text.** A record whose text changed at apply still pays. In
    the end-to-end test a structuring merge that adds an alias does exactly
    that, so that test keeps the candidates unmerged.
- **F6 (ingest dry run).**
  - **The planner.** `graph_nomination.plan_ingest_embedding` takes a
    stored-only nominator. It constructs no client, resolves no route and
    writes nothing.
  - **Known queries.** An append's new claim and defined concept queries are
    priced as `_embed` reserves them (UTF-8 bytes + 128 per text, the spec
    price), less those stored by content. `exceeds_caps` says when they pass
    a per-run cap.
  - **Generated text.** Text the run writes itself is bounded by what the
    per-run cap leaves: structuring candidates (bootstrap) and mint-shadow
    facets and repairs. That cap is
    `min(max_query_cost_usd, max_query_tokens × price)`, and the nominator's
    spend budget enforces it.
  - **Zero plans.** These cases plan zero and say why: the switch off,
    `embed_new_text = false`, an unknown price, an unset
    `ai.routing.embedding`, or no complete non-empty registry index.
  - **Entry points.** `plan_study_map_embedding` and `plan_append_embedding`
    wrap the planner; the append one reads inventories through a read-only
    attach. `learnloop synthesize <set> --dry-run [--mode] [--new-revision]
    [--json]` prints the plan before any provider is resolved.
  - **Scope.** The plan says it covers the embedding route only: the
    synthesis or reconciliation model is not priced here, as before T5.

Unchanged by the fixes: R1 (nominations never merge, alias or change a D2
disposition on their own), the review passes' stored-only cosine columns,
replay and rebuild (no nominator), and the schema (head 168, no migration).

## Manual run (fixtures-local, no paid call)

`learnloop synthesize sset_quickadd_src_01KY2YG27G1SDWA4FN939ZBB34 --dry-run
--vault fixtures-local/t5-linear_algebra` (embeddings enabled and the
registry backfilled by the stage's earlier real run):

- **append** (auto mode, the whole set): `may_embed`, both indexes
  `complete`. Known queries: 632 texts, 0 stored, about 285,787 tokens,
  $0.002858. `exceeds_caps` is true (256 texts and 200,000 tokens per run),
  so embedding stops at a cap and the rest stay lexical. The plan's maximum
  is $0.002000, the cap. 185 concept mentions are lexical-only.
- **bootstrap**: `may_embed`, no known queries. Structuring and the mint
  shadow are bounded by the cap: at most $0.002000.
- **No data change.** The copy's `state.sqlite` sha256 was identical before
  and after both runs. Paid calls: 0. Cost: $0.

Owner command, added to the stage's list: `uv run learnloop synthesize <set>
--dry-run --vault <vault>` before a synthesis or append on a vault with
embeddings on.

## Gate

Run on `622807db` (clean tree apart from these two review notes). The
commits after the six fixes are a test assertion (`d1361ed2`), the dry-run
cap flag (`8fdb14d4`), a docstring (`001f33e5`) and regenerated references
(`c100c6ae`, `3006fa62`, `622807db`); the suite ran on that source.

| Check | Result |
|---|---|
| `uv sync --extra dev` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **10 contracts kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **7,124 passed**, 14 existing warnings (fork DeprecationWarnings), 170 s |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **69 passed**, 7,055 deselected |
| T5 modules (`test_graph_nomination*.py`, 44 tests) with `--durable-sqlite` | 44 passed |
| DB/config reference generate + validate | no schema change (head 168, 266 table notes, 552 config leaves), zero errors; global docs-vault validator passed. Regenerated because line anchors into `graph_nomination.py` and `cli/app.py` moved |
| CLI help snapshot | regenerated (`synthesize` gained `--dry-run`) |
| Frontend | not touched (no `npm` run needed) |

New or changed tests: 13 new (7,111 at the stage gate, now 7,124), in
`tests/test_graph_nomination.py` (2 new, 1 updated for F4) and
`tests/test_graph_nomination_ingest.py` (11 new, 1 strengthened).
