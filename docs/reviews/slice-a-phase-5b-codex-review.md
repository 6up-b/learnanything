# Slice A Phase 5b: Codex review fixes

Branch `slice-a/phase-5b`, worktree `learnanything-phase-5b`. Reviewed head:
`9ca5df87` (Codex job `~/.cache/codex-agent/jobs/20261012-012902-Z86gB4`).
Build record: `docs/reviews/slice-a-phase-5b.md`.

Owner decisions applied (2026-10-12): the specs' recommended defaults; Codex
on the ChatGPT subscription runs every paid LLM role with no physical-request
bound and an estimated-only cost (Slice A §5 rule 6); frictionless defaults
(honest labels, generous defaults, kill switches, no shadow stages).

Each finding was reproduced before it was fixed: by a failing test where the
behaviour is testable, and for F7 and F8 also against a scratch extraction of
`9ca5df87`. No live or paid AI call was made; every test uses fakes.

## Findings

| ID | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F1 | High | Metered calls bypass request and retry caps | fixed | `a34f292b` | `tests/test_practice_index_paid.py` (4 tests, real `OpenRouterProviderClient`); `tests/test_ai_single_request.py` (ported) |
| F2 | Medium | Batch dry runs apply migrations | fixed | `c63e1837`, `30780a3d` | `test_practice_index_adapters.py::test_batch_dry_runs_never_migrate_an_older_rollback_database` (durability) |
| F3 | Medium | Changed index content keeps an old evaluation approval | fixed | `d45141a5` | `test_practice_index_find.py::test_changed_index_content_voids_an_earlier_evaluation_approval` |
| F4 | Medium | Reverting sources leaves retrieval on the wrong dossier | fixed | `5cc17064` | `test_practice_index_dossiers.py::test_reverting_sources_selects_the_matching_earlier_dossier`, `::test_select_dossier_prefers_current_sources_then_the_intended_model` |
| F5 | Medium | Duplicate queries can manufacture a winning evaluation | fixed | `9717d0f1` | `test_practice_index_evaluation.py::test_duplicate_queries_cannot_manufacture_a_winning_evaluation` |
| F6 | Medium | Alternative embedding models have no usable price override | fixed | `d3e9f1da`, `b45465d1` | `test_practice_index_find.py::test_an_alternative_embedding_model_takes_an_explicit_price` |
| F7 | Medium | The paid `find` command has no dry run | fixed | `4289dd62` | `test_practice_index_find.py::test_find_dry_run_plans_embedding_and_rerank_without_clients_or_writes`, `::test_find_dry_run_names_metered_rerank_prices_and_caps` |
| F8 | Medium | A crash after a paid response pays again | fixed | `a34f292b` | `test_practice_index_dossiers.py::test_a_paid_answer_survives_a_failed_write_and_is_not_paid_again`; `test_practice_index_evaluation.py::test_paid_labels_and_queries_survive_a_failed_write` |

No finding was rejected.

## How each finding was reproduced and fixed

**F1 (High).** *Reproduced* through the real OpenRouter adapter (fake
`openai` module). Two timeouts and then an answer, with `max_calls=1` and
`max_retries=0`, sent **3** physical requests, while the budget recorded 1
call and 0 retries. An invalid first answer sent a hidden repair request (2
requests). *Fix:* Phase 3's `single_request()` transport bound is ported
verbatim: `ai/execution.py`, `ai/transport.py`
(`BOUNDED_STRUCTURED_COMPLETION`), `ai/providers/openai_chat.py`,
`ai/providers/codex.py` and `tests/test_ai_single_request.py`. The hunks
are identical to `slice-a/phase-3` and `integrate/slice-a-2-3`, so
integration merges cleanly.
- Every metered attempt runs under `single_request()` and reserves one
  request. A retry or repair is a new attempt, admitted and charged under the
  retry cap.
- A metered transport that cannot bound its requests is refused before any
  request (`status: unavailable`).
- A second physical request inside one admitted attempt is stopped before it
  is sent.
- Codex keeps the owner's subscription exception.

**F2.** *Reproduced* with a database built through migration 166 in
rollback-journal mode, run in the durability lane so the WAL switch is real.
After `dossiers --dry-run` the database was at **schema 167 and in WAL mode**,
with `facet_dossiers` present. *Fix:* both batch planners now plan through
`planning_repository()`, which attaches read-only without migrating; missing
tables read as empty. The test plans through both functions and the `dossiers`,
`eval` and `find` dry runs. It asserts the same version, journal mode and file
bytes before and after.

**F3.** *Reproduced:* approve dossiers on the current manifest, change an
item's text, regenerate the dossier it grounds, and backfill under the same
models and recipe versions. `auto` **kept the dossier path**. *Fix:* the index
manifest now includes content fingerprints (hashes only):
- the indexed item text;
- the item-to-facet mapping;
- the selected dossier revisions;
- the content hashes of the item and dossier vectors.

Any of these changing voids the approval, and `auto` uses direct search until
the evaluation is rerun. Reruns reuse persisted queries, labels and vectors.
The test also covers a mapping-only change.

**F4.** *Reproduced* with sources A → B (regenerated) → A. Generation
reported **0 pending**, because the A row exists, but status counted the facet
**stale** and selection took the newest row (B). *Fix:*
`practice_index.dossiers.select_dossier` picks, in order:
1. the revision written for the current sources and prompt version;
2. among those, the intended model (`ai.routing.practice_dossier`);
3. otherwise the newest revision, labelled stale.

Source hashes are computed only for facets with more than one revision (about
0.11 s for all 39 facets of the linear-algebra copy). The dossier embedding
recipes offer every revision of the facet's current content. Retrieval reads
the selected revision's vectors by content hash, so a backfill always makes
the serving revision searchable. Status uses the same selection.

**F5.** *Reproduced:* ten seeds wrote one normalized request whose rankings
favour dossiers. The pre-fix run persisted **winner = dossier, ΔnDCG@10 =
1.000 [1.000, 1.000], n = 10**. *Fix:*
- Requests are grouped by normalized text (whitespace and case) before
  ranking, labelling and scoring. The ten-query minimum and the bootstrap
  count distinct requests.
- Seed provenance is kept: the seed-kind and writer-model splits count a
  request under each seed that wrote it.
- The report adds `distinct_queries`, `duplicate_query_rows` and
  `query_provenance`.
- The fixed run gives n = 1 and "insufficient evidence", so direct search
  stays.

**F6.** *Reproduced* with `openai/text-embedding-3-small`, backfilled with
`--price-per-million`. The evaluation refused the unknown price and its reason
named the LLM flag. Live `find_practice` skipped the query embedding. *Fix:*
- `eval --embedding-price-per-million` feeds both the evaluation's plan and
  its run.
- The new `practice_index.query_embedding_price_per_million` feeds live
  retrieval.
- The price source is reported. Unknown prices still fail closed, and the
  refusal names the right flag.
- Planning no longer refuses an unknown price when every query vector is
  cached, which matches execution.
- The mvp-0.9 defaults fingerprint, the CLI help snapshot and the reference
  (537 leaves) are updated.

**F7.** *Reproduced* at `9ca5df87`: `practice-index find … --dry-run` fails
with **"No such option: --dry-run"** (exit 2). *Fix:* `plan_find_practice`
and `find --dry-run` run admission, the snapshot, path choice and ranking
read-only. For the query embedding and the rerank, the plan reports:
- cache hits (vector cache, rerank ledger, recoverable checkpoint);
- calls, estimated tokens and cost, and billing;
- the effective caps, and whether they admit the call.

The dry run constructs no client, sends nothing, writes no receipt and does
not migrate. When the query vector is not cached, the rerank pool is not
known, so its cost is an upper bound (`pool_exact: false`).

**F8.** *Reproduced* at `9ca5df87` (scratch extraction, fake LLM). The first
write of the `facet_span` dossier failed after its answer was paid, and the
rerun **paid for it again (2 answers)**; with the fix it pays once. *Fix:*
- Every validated paid answer is checkpointed in `model_work_checkpoints`
  under its request identity before its row is written. The identity is the
  purpose, prompt, schema, output budget, provider and model.
- A rerun recovers the answer without a request and writes it idempotently.
  This covers dossiers, label passes and the rerank.
- A rerun batches the remaining seeds differently, so interrupted
  query-writer batches are written first, from their checkpoints.
- Dry runs report the recoverable work and leave it out of the paid estimate.

## Claims that did not hold

| Claim | Now |
|---|---|
| "Dry runs make no migration or data change" | Holds: read-only attach, tested on a schema-166 rollback database (F2) |
| "Metered routes keep every cap" | Holds: one admitted physical request per attempt, no hidden retry or repair (F1) |
| "Current index" evaluation approval | Holds: content fingerprints in the manifest (F3) |
| Current dossier selection | Holds: generation, status, recipes and retrieval agree after a revert (F4) |
| "At least ten scored queries" | Holds: ten **distinct** requests (F5) |

The build record (`slice-a-phase-5b.md`) was corrected where these fixes
changed it, and it links here.

## Not changed

- **Duplicated admission logic** (spec-conformance note, not a finding). It is
  unchanged and pinned by the parity test with `build_due_queue`. Phase 5b
  does not own `build_due_queue`.
- **Migration 167** is unchanged (no schema change), and so is
  `fixtures/migration_head_167`, verified by checksum. It still needs a
  renumber at integration. No tracked vault fixture changed.
- **RPC and agent-tool dry run.** `find_practice`'s sidecar RPC and agent tool
  have no dry-run flag. Planning is available through the CLI and
  `plan_find_practice`, which matches the finding's scope (the CLI command).

## Gate (final, on `30780a3d` plus this document)

| Command / check | Result |
|---|---|
| `uv sync --extra dev`; `uv pip install pypdfium2` | OK (no `learnloop_mobile` change, so no `--extra mobile`) |
| `uv run lint-imports --no-cache` | **6 contracts kept, 0 broken** |
| `uv run pytest -n auto` | **6,221 passed**, 14 existing warnings, 173.9 s |
| `uv run pytest -m durability` | **64 passed**, 6,157 deselected, 28.0 s |
| Practice-index and single-request modules | **69 passed** |
| `db_generate_reference.py` / `db_validate_reference.py` | schema **167**, **265** table notes, **537** config leaves in 29 sections, **0 errors** |
| Frontend (`npm`) | not applicable: no frontend change |

The first full run had one failure,
`test_sqlite_file_copies.py::test_every_file_copy_site_is_an_audited_sqlite_copier`.
The new F2 test copied migration SQL with `shutil.copy2`. It now copies the
bytes directly (`30780a3d`), and the rerun above is clean.

## Open questions for the owner

1. **F3 strictness.** Any change to item text, a facet mapping, a dossier
   revision or vector content now voids the dossier path's approval. `auto`
   then uses direct search until `practice-index eval` is rerun. Reruns are
   cheap: persisted labels, and no marginal cost on Codex. Keep this strict
   rule, or allow small content drift?
2. **F4 stale fallback.** When no revision matches a facet's current sources,
   the newest revision still serves and status labels it stale, as before.
   Strict matching would send the whole dossier path to direct search after
   any source edit until regeneration.
