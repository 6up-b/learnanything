# Slice A Phase 5b: the practice index (facet dossiers and `find_practice`)

Branch `slice-a/phase-5b`, worktree `learnanything-phase-5b`, base `main` at
`16db5ac5` (Phase 1 merged, migration head 166, `fix/daily-loop-bugs` merged).

Read first: `CLAUDE.md`; `implementation_handoffs.md` §0 and the Phase 5b prompt;
`spec_slice_a_practice_and_field_v1.md` (whole, especially §3 row 5 and §5);
`spec_embedding_consumers_v1.md` §5.8, §5.9 (and R1–R4, §5.4, §12–§13);
the Phase 1 substrate (`ai/embedding.py`, `db/stores/embedding_vectors.py`,
`vault/embedding_recipes.py`, `ops/embedding_backfill.py`, `ai/spend.py`);
`db/table_roles.py`; `docs/algorithm-change-playbook.md`; the architecture Home.

## Plan (written before coding)

### Files

New:

- `migrations/167_practice_index.sql` (the next free number on `main`; expect a
  renumber at integration, since `integrate/slice-a-2-3` holds 167–168 and
  `mobile/m1` claims 167).
- `src/learnloop/db/stores/practice_index.py`: the only SQL writer for the new
  tables, plus read helpers (current dossier per facet, latest evaluation).
- `src/learnloop/scheduling/practice_admission.py`: the scheduler's ordinary
  eligibility rules as one reusable, read-only admission check.
- `src/learnloop/practice_index/` (new package):
  - `contracts.py`: strict wire models (dossier draft, rerank, query writer, relevance labels);
  - `text.py`: tokenizer, Okapi BM25, reciprocal-rank fusion;
  - `paid.py`: route resolution, billing mode (subscription vs metered), estimates, admission of every call under `SpendBudget`, receipts;
  - `dossiers.py`: grounding, `facet_dossiers` generation;
  - `retrieval.py`: the index snapshot, direct and two-level search, rerank, admission, `find_practice`;
  - `coverage.py`: the coverage report and 5a generation targets;
  - `usage.py`: usage signals (explicit learner taps and the attempt join);
  - `evaluation.py`: query set, pooling, two-pass labels, Recall@10/nDCG@10, the bar;
  - `tool.py`: the agent-tool declaration and dispatcher.
- `src/learnloop/cli/practice_index.py`: `learnloop practice-index
  {dossiers, find, coverage, usage, eval, status, tool-spec}`.
- `src/learnloop_sidecar/handlers/practice_index.py`: RPCs `find_practice`,
  `record_practice_usage`, `get_practice_coverage`.
- Tests: `tests/practice_index_fakes.py` and `tests/test_practice_index_*.py`.

Changed: `ai/routing.py` (four `AITask` routes and operations),
`config/schema.py` (routes + `[practice_index]`), `config/template.py` (template
switches + mvp-0.9 defaults fingerprint), `params/parameter_registry.py`
(classify new config leaves), `db/table_roles.py`, `vault/embedding_recipes.py`
(four dossier-field recipes + `facet_content_hash`), CLI and sidecar
registration, the migration-head fixture (166 → 167) and its five paths, the
DB reference docs, and test expectations that enumerate recipes, CLI help or
SQL owners.

### Migration 167 (four tables, no DERIVED table, so no replayer)

| Table | Role | Holds |
|---|---|---|
| `facet_dossiers` | WORKFLOW | Paid dossier outputs, unique on (facet, facet content hash, source hash, model, prompt version). Never regenerated on rebuild |
| `practice_index_proposals` | RECEIPT | What each `find_practice` call proposed (path, signals, picks, exclusions, manifest); the join key for usage signals |
| `practice_eval_queries` | WORKFLOW | The persisted held-out query set (LLM-written, plus logged real queries); paid output, never regenerated |
| `practice_index_evaluations` | RECEIPT | Each retrieval evaluation's aggregate result and the path it chose, with its manifest |

### Algorithm successors and kill switches

- **No algorithm successor.** `find_practice` proposes and never serves; it
  writes no evidence, scheduling or projection state. Admission reuses the
  scheduler's rules read-only. The mvp-0.9 effective-defaults fingerprint is
  updated for the additive `[practice_index]` config, as Phase 1 did.
- Switches: `practice_index.enabled` (find_practice on; kill switch),
  `practice_index.retrieval_path = "auto" | "direct" | "dossier"` (auto uses
  the dossier path only when the latest evaluation on the current manifest says
  dossiers beat direct search), `practice_index.rerank_enabled`, and two paid
  batch switches off in the template: `practice_index.dossiers_enabled`,
  `practice_index.evaluation_enabled`.

### Spend caps and model routes

- Routes (each falls back to the active provider when unset):
  `ai.routing.practice_dossier`, `practice_rerank`, `practice_query_writer`,
  `practice_relevance_judge`. Embeddings use the Phase 1 `embedding` route,
  which never falls back.
- Every paid command takes caps and `--dry-run`; every call is admitted by
  `SpendBudget.request` before it is sent. Codex (`codex_sdk`, the HTTP
  adapter) is a subscription transport: no physical-request bound, tokens and
  cost estimated from reported usage (falling back to input + output
  estimates) and labelled `estimated_only`; call, candidate and pair caps still
  apply. Metered routes keep every cap; unknown prices fail closed unless the
  owner supplies `--price-per-million`. Receipts carry the caps plus a
  `practice_index` block (task, billing, cost basis, prompt version, input hash).
- Live calls inside `find_practice` (one query embedding, one rerank) run under
  small per-call caps from config.

### `judgment_ledger` writes

- `practice_relevance` (judge `llm`): the live rerank (prompt `practice_rerank.v1`)
  and the evaluation's two label passes (`practice_relevance_label.v1.pass1/.pass2`),
  one row per (query, item). Deterministic ids make reruns free.
- `practice_usage`: explicit learner taps (judge `learner_card`: practised,
  skipped, too_easy, not_what_i_asked) and the attempt join (judge `exact_key`:
  practised).

### Tests

Admission parity with `build_due_queue` and each exclusion rule; BM25/RRF;
dossier grounding, planning, idempotent generation, regeneration only on a
facet or source change, and no regeneration on rebuild; recipes and backfill
over dossier fields; both retrieval paths, path choice and fallbacks; rerank
ledger rows and caching; never-serves (no attempts, slates or follow-up
changes); coverage targets; usage signals; the evaluation end to end with fakes
(metrics, agreement, bar, persisted decision); spend caps (subscription vs
metered, unknown price, dry-run makes no calls); strict wire schemas; CLI,
sidecar and tool; table roles and the migration head.

## Built

**Facet dossiers** (`practice_index/dossiers.py`, `learnloop practice-index dossiers`).
- One dossier per registered, non-retired facet with four fields: **scope**
  (covers / excludes), **moves**, **errors**, **contrast** (one line per
  structural neighbour). The writer returns a strict structured draft; the
  rendered text of each field is what is embedded and keyword-indexed.
- Grounding: the facet's structured fields; up to six current source spans
  (`entity_source_links` primary → support → alternate, then the facet's
  provenance refs, resolved through the extraction IR); up to eight of the
  items that test it (oldest first, so newly published items rarely move the
  sample) with their rubric criteria; up to four neighbours (shared learning
  objects, then shared concept). **Never sent:** expected answers, learner
  data, `diagnostic_probe`/`diagnostic_microprobe` surfaces, exam-reserved
  items.
- Keyed by facet content hash (authored meaning, provenance excluded), source
  hash (the grounding sources, including neighbours' content hashes), model and
  prompt version. A rerun pays only for new keys, so a dossier is regenerated
  only when its facet or its sources change (or the owner changes the model or
  prompt version). `learnloop practice-index status` reports current / stale /
  missing per facet. Rebuild never touches them (tested under the durability
  lane with model construction forbidden).

**Dossier embeddings.** Four recipes in `vault/embedding_recipes.py`:
`facet/dossier_scope`, `facet/dossier_moves`, `facet/dossier_errors`,
`facet/dossier_contrast`. Each reads the newest persisted dossier for the
facet's current content; the existing `learnloop embeddings backfill` embeds
them (`--record-kind facet` now selects all five facet recipes).

**`find_practice(query, constraints)`** (`practice_index/retrieval.py`): a
sidecar RPC (`find_practice`), a CLI command (`learnloop practice-index find`,
`--json` for shell agents) and an agent-tool declaration
(`practice_index/tool.py`, printed by `learnloop practice-index tool-spec`).
1. **Admission first** (`practice_index/admission.py`): the scheduler's
   ordinary eligibility rules, built from the same predicates and reads as
   `build_due_queue` (item status and scheduler state, exam reserves, the
   rung-variant hold, staged-controller ownership, the diagnostic freshness
   reserve, servability, and `fix/daily-loop-bugs`' LO lifecycle), plus two
   proposal rules: **reserved cold checks** (the selected item of an open
   cold follow-up task) and **the reveal ledger** (an answer revealed within
   the 1-day cold retrieval delay). A parity test pins that, for the shared
   rules, the admitted set equals what `build_due_queue` keeps, item for item.
   Then the constraints (learning objects, subjects, facets, modes, excluded
   ids, difficulty range, limit).
2. **Direct path** (default): items ranked by BM25 over item text and by
   item-outline vectors (`item/skeleton` once Phase 5a's index is complete,
   otherwise `item/stem`), fused by reciprocal rank (k = 60; ranks only, no
   hand-set cosine or score threshold).
3. **Two-level path**: facets ranked by BM25 over dossier text plus each
   dossier field's vectors (RRF); at least `facet_top_k` facets, then more in
   rank order until their admissible items fill the candidate pool; items of
   those facets ranked by the same item lists plus the facet rank.
4. **Path choice** (`practice_index.retrieval_path = "auto"`): the two-level
   path only when the latest retrieval evaluation on the **current index
   manifest** (embedding model, item recipe, dossier models and prompt
   versions, recipe versions, fusion and pool settings) chose dossiers.
   Otherwise direct, with the reason returned and receipted. `direct` and
   `dossier` force a path; a forced dossier path falls back to direct while
   dossiers or their vectors are incomplete.
5. **LLM rerank** (`ai.routing.practice_rerank`): judges every candidate in the
   pool (20) and picks the best few with a one-line rationale. Every verdict
   goes to `judgment_ledger` (task `practice_relevance`, judge `llm`, prompt
   `practice_rerank.v1`); an identical request reuses the ledger rows instead
   of paying again. A partial answer is retried once, then reported
   unreranked. A metered rerank route without
   `practice_index.rerank_price_per_million` is skipped and labelled.
6. **Receipt**: every call writes `practice_index_proposals` (path and reason,
   signals, rerank status and model, picks, exclusion counts, manifest). The
   result says `serves: false`; a test asserts that proposing writes no row to
   any table other than the index's own receipts, ledger, vectors and model
   receipts.
- The query is embedded once (`retrieval-query` prefix, Phase 1 route, capped,
  cached under record kind `practice_query`) only when the embedding index the
  chosen path uses is complete; with embeddings off, keyword search only, and
  the response says so.

**Coverage** (`practice_index/coverage.py`, `learnloop practice-index coverage`,
RPC `get_practice_coverage`): per registered facet, tagged vs admissible
items; facets below `practice_index.coverage_min_eligible` (3) are targets,
fewest first. `coverage_targets()` is the API for Phase 5a.

**Usage signals** (`practice_index/usage.py`): learner taps via RPC
`record_practice_usage` or `learnloop practice-index usage` (judge
`learner_card`: practised, skipped, too_easy, not_what_i_asked), and an
idempotent sweep that joins proposals to attempts within 72 h (judge
`exact_key`: practised). Both append to `judgment_ledger` (task
`practice_usage`); the evaluation report summarizes them by path.

**Retrieval evaluation** (`practice_index/evaluation.py`,
`learnloop practice-index eval`):
- A persisted held-out query set (`practice_eval_queries`): LLM-written
  requests seeded half from facets (label, claim, learning objects; never
  dossier text) and half from items (the writer must not copy the question),
  plus up to 20 real logged `find_practice` requests. Nothing is fitted on the
  queries, so all are held out; the set only grows, so reruns stay comparable.
- Pooling: each path's top 10 over the currently admissible items.
- Labels: an LLM judge (`ai.routing.practice_relevance_judge`) grades every
  pooled item in two passes with different framings and opposite orders;
  both go to `judgment_ledger` (`practice_relevance_label.v1.pass1/.pass2`),
  keyed per (query, item, item text, pass, judge model), so reruns label only
  new pairs. Agreement: exact and Cohen's kappa, three-class and binary.
- Metrics: Recall@10 and nDCG@10 (gain = mean grade; relevant = both passes
  at least partial), paired differences with seeded percentile-bootstrap 95%
  intervals, split by seed kind and query-writer model; label models counted.
- **The bar**: dossiers win only if the nDCG@10 difference's interval is above
  0, the mean Recall@10 difference is not negative, and at least 10 queries are
  scored. Anything else keeps direct. Complete runs persist the decision in
  `practice_index_evaluations`, which `auto` reads.
- The report (`fixtures-local/reports/practice-index-eval-<run>.json`) is
  aggregate only: counts, metrics, intervals, agreement, spend, usage and a
  version manifest; no query, item or answer text (tested).

**Spend and routes.**
- Four routes, each falling back to the active provider when unset:
  `practice_dossier`, `practice_rerank`, `practice_query_writer`,
  `practice_relevance_judge`. The embedding route is Phase 1's and never falls
  back.
- `practice_index/paid.py` admits every call with `SpendBudget.request`
  before it is sent. **Codex** (`codex_sdk`, the Codex HTTP adapter) is billed
  as a subscription: no physical-request bound and no token or dollar cap;
  tokens are taken from reported usage, else the input + output estimate, and
  reported as `estimated_only` (a dollar equivalent appears when the owner
  passes `--price-per-million`). Call, candidate, pair and retry caps still
  apply. **Metered** routes keep every cap, fail closed on an unknown price,
  and reserve twice each call's estimate (one possible JSON-repair request);
  reported usage reconciles upward. Root receipts carry the caps plus a
  `practice_index` block (task, billing, cost basis, prompt version, input
  hash).
- Paid batch work has its own switches, off in the template:
  `practice_index.dossiers_enabled`, `practice_index.evaluation_enabled`.
  Dry runs need neither and make no client, migration or data change. The
  evaluation checks its whole plan (query writing, labels, query embeddings)
  against the caps before the first request; its dry run counts exact pending
  label work for queries it can rank now, and a full-pool upper bound only for
  queries not yet written or embedded. Dossier generation and the evaluation
  each hold a per-vault lock.

**Kill switches and config** (`[practice_index]`): `enabled` (find_practice),
`retrieval_path`, `rerank_enabled`, `rerank_price_per_million`,
`rerank_max_cost_usd`, `facet_top_k`, `candidate_pool`, `proposals`, `rrf_k`,
`coverage_min_eligible`, `usage_window_hours`, `dossiers_enabled`,
`evaluation_enabled`. All classified `structural/operational` in the parameter
registry: the index proposes and never serves.

## Decisions and deviations

1. **No algorithm successor.** `find_practice` proposes; it writes no evidence,
   scheduling, projection or certification state, and admission is a pure
   read. The mvp-0.9 effective-defaults fingerprint is updated for the
   additive config, as Phase 1 did.
2. **Admission runs before ranking, not after the rerank** (the spec lists it
   as step 4). The rules are the same; running them first stops the rerank
   from spending a slot on an item that can never be served.
3. **Admission lives in `practice_index/admission.py`, not in `scheduling/`**
   (the plan said `scheduling/practice_admission.py`). From `scheduling`, the
   import of `diagnosis.remediation.COLD_RETRIEVAL_DELAY` made a new
   `scheduling → diagnosis` cycle, which the frozen-cycles contract rejects.
   `build_due_queue` is untouched (it is Phase 6's and R1's file), so the rules
   are shared by reusing the same predicates, and the parity test pins them.
   A new scheduler rule must be added there too; the module docstring says so.
4. **The routine cold-start gate does not apply** to a proposal: an explicit
   request for practice adopts the material, as with requested cards. Two
   proposal-only rules are added (reserved cold checks, recent reveals); the
   scheduler would serve those items, a proposal must not burn them.
5. **Adaptive facet count.** The spec's two-level path keeps "the top facets".
   Facets here are often finer than a learning object (the linear-algebra
   fixture has 39 facets over 42 admissible items), so a fixed five left the
   item stage too few questions and handicapped Recall@10 structurally (ΔRecall
   −0.48 on the fixture before the change, −0.02 after). The path now keeps at
   least `facet_top_k` facets and adds more until the candidate pool is full.
6. **Dossier recipes read SQLite from `vault/`.** Dossiers are persisted paid
   outputs, not vault YAML, so their recipes open the vault's database read-only
   (`vault → db` is an existing edge). Phase 5a's `item/skeleton` recipe faces
   the same question; expect a small merge in that file.
7. **Embedding geometry.** Retrieval reuses Phase 1's mean-centred cosine
   (centroid of the current field's vectors), Qwen's query-only instruction and
   no whitening. Projecting out only the mean direction (2511.11041) is not a
   separate code path.
8. **"Active facet"** = registered, canonical, non-retired (`proposed` facets
   included).
9. **Evaluation command.** It is `learnloop practice-index eval`, not a
   subcommand of `learnloop eval`: on `main`, `eval` is still a single command,
   and the unified group exists only on `integrate/slice-a-2-3`. The command
   function is standalone, so integration mounts it with one line:
   `eval_app.command("practice-index")(practice_index_eval)`.
10. **Metered routes and hidden retries.** Phase 3's `single_request` bound is
    not on `main`, so a metered `openai_chat`/`openrouter` call may still make
    transport retries after a failed request (at most three HTTP attempts) in
    addition to one JSON repair. Each call reserves twice its estimate, and
    every physical attempt's reported usage reconciles the charge upward, so
    overspend is bounded and recorded rather than prevented. At integration,
    wrap metered calls in `single_request()`.
11. **Coverage counts the scheduler's admission**, so exam-reserved and
    parked items do not count as coverage.
12. **No frontend.** The RPCs exist for the tutor, the daily loop's "practice
    this" box and Slice 1's repair targeting; no screen calls them yet, so
    `npm` gates did not apply.

## Verification

Run in this worktree with `uv sync --extra dev` and `uv pip install pypdfium2`.
`LEARNLOOP_CONFIG_DIR` was isolated under `fixtures-local/` for manual runs.

GATE_RESULTS_PLACEHOLDER

## Manual run on a fixtures-local copy (fakes only)

A backup-API copy of the tracked `fixtures/linear_algebra`
(`fixtures-local/p5b-la-final`, migrated 155 → 167 on the copy) ran the whole
pipeline with fakes injected into the same entry points the CLI calls
(`FakePracticeLLM` for all four LLM roles, a 64-dimension hashing embedder
for the embedding route). No provider was constructed.

| Step | Result |
|---|---|
| CLI dossier dry run (un-migrated copy) | 39 facets, 39 calls, ~294k tokens, subscription / `estimated_only`, $0 marginal; no data change |
| Dossiers | 39 written, 0 failed; rerun 0 calls |
| Embedding backfill | 247 vectors (definition, 4 dossier fields, item stems); rerun 0 |
| Coverage | 42 admissible items (15 exam-reserved, 1 cold-check-reserved, 1 inactive excluded); 30 of 39 facets below 3 admissible items |
| `find_practice` | direct path ("no retrieval evaluation yet"), reranked; repeat calls served from the ledger |
| Evaluation | 43 queries (40 written + 3 logged), all scored, 86 label calls, 589 pooled pairs; rerun 0 calls |
| Label agreement | exact 1.0, kappa 1.0 (both fake passes are the same lexical rule) |
| nDCG@10 | direct 0.957, dossier 0.944; Δ −0.013 [−0.028, 0.000] |
| Recall@10 | direct 0.755, dossier 0.734; Δ −0.021 [−0.047, −0.002] |
| **Path that won** | **direct**: "dossiers did not beat direct item search"; `find_practice` (auto) then stays direct |

These numbers test plumbing only. The fake judge grades by keyword overlap with
the item text, which structurally favours direct item search, and it marks
almost every pooled item at least partial (13.0 of 13.7 per query). The real
verdict needs the owner's run with real models.

## Owner-run commands

No paid call was made during implementation. First make a backup-API copy of
a vault **you choose** (the destination must be new), as in Phase 1:

```bash
export LEARNLOOP_CONFIG_DIR="$PWD/fixtures-local/phase5b-owner-config"
SOURCE=/absolute/path/you/choose
COPY="$PWD/fixtures-local/phase5b-owner-copy"
uv run python - "$SOURCE" "$COPY" <<'PY'
from pathlib import Path
import sys
from learnloop.db.copies import copy_tree_with_databases
copy_tree_with_databases(Path(sys.argv[1]), Path(sys.argv[2]))
PY
```

Merge into the copy's `learnloop.toml` (into existing sections; don't create
duplicate tables). Supply `OPENROUTER_API_KEY` through your shell or the
copy's `.env`.

```toml
[embedding]
enabled = true
backfill_enabled = true
model = "qwen/qwen3-embedding-8b"
dimensions = 4096

[ai.routing]
embedding = "openrouter_embedding"
# Optional; empty = the active provider (Codex by default, on your subscription).
# practice_dossier = "codex_medium"
# practice_rerank = "codex_low"
# practice_query_writer = "codex_low"
# practice_relevance_judge = "codex_medium"

[practice_index]
dossiers_enabled = true
evaluation_enabled = true
```

Then, dry run first at each step:

```bash
# 1. Facet dossiers (Codex: estimated_only tokens, no marginal cost).
uv run learnloop practice-index dossiers --vault "$COPY" --dry-run --json
uv run learnloop practice-index dossiers --vault "$COPY" --json
# 2. Embed dossier fields, facet definitions and item stems (metered OpenRouter).
uv run learnloop embeddings backfill --vault "$COPY" --dry-run --json \
  --max-candidates 10000 --max-calls 400 --max-retries 2 --max-tokens 10000000 --max-cost-usd 1
uv run learnloop embeddings backfill --vault "$COPY" --json \
  --max-candidates 10000 --max-calls 400 --max-retries 2 --max-tokens 10000000 --max-cost-usd 1
# 3. The retrieval evaluation (writes fixtures-local/reports/practice-index-eval-<run>.json).
uv run learnloop practice-index eval --vault "$COPY" --dry-run --json
uv run learnloop practice-index eval --vault "$COPY" --json
# 4. Inspect: which path find_practice now uses, and try it.
uv run learnloop practice-index status --vault "$COPY" --json
uv run learnloop practice-index find "give me practice on <a topic>" --vault "$COPY"
uv run learnloop practice-index coverage --vault "$COPY" --json
```

If you route a paid role to a metered model instead of Codex, add
`--price-per-million <USD per million tokens>` to `dossiers` and `eval` (and
set `practice_index.rerank_price_per_million` for the live rerank); unknown
prices fail closed. Raise `--queries` (default 40) for a tighter interval; the
whole plan is checked against the caps before the first request.

## Open questions

1. **The real verdict.** Only the owner's run decides whether dossiers stay in
   `find_practice`'s path; on fixtures with fakes, direct won.
2. **Live rerank latency.** The default rerank runs a Codex turn per request
   (no marginal cost, but seconds). Keep it on by default, or have the daily
   loop's box call with `rerank: false` and rerank lazily?
3. **Empty picks.** When the rerank judges nothing relevant, `find_practice`
   returns no items (an honest "nothing fits"). Should consumers then show the
   unreranked top items, labelled as such?
4. **Dossier churn.** Neighbour content is part of a dossier's sources, so
   editing one facet also regenerates the dossiers that contrast with it.
   Acceptable at 30–60 facets on Codex; say if you would rather pin contrast
   to neighbour ids only.
5. **Integration.** Renumber migration 167 when `integrate/slice-a-2-3`
   (167–168) and `mobile/m1` (167) land; mount the eval command under the
   unified `learnloop eval`; adopt `single_request()` for metered calls;
   merge Phase 5a's `item/skeleton` recipe (find_practice picks it up
   automatically once its index is complete).

## Files touched

- Migration: `migrations/167_practice_index.sql`.
- New: `src/learnloop/practice_index/` (`admission`, `catalog`, `contracts`,
  `coverage`, `dossiers`, `evaluation`, `paid`, `query_vectors`, `retrieval`,
  `text`, `tool`, `usage`), `src/learnloop/db/stores/practice_index.py`,
  `src/learnloop/cli/practice_index.py`,
  `src/learnloop_sidecar/handlers/practice_index.py`,
  `tests/practice_index_fakes.py`, `tests/test_practice_index_{admission,adapters,dossiers,evaluation,find,text}.py`.
- Changed: `ai/routing.py`, `config/schema.py`, `config/template.py`,
  `params/parameter_registry.py`, `db/table_roles.py`,
  `vault/embedding_recipes.py`, `cli/__init__.py`, `cli/embeddings.py` (help
  text), `learnloop_sidecar/handlers/__init__.py`; tests `test_architecture`,
  `test_embedding_backfill`, `test_migrations`, `test_rebuild_orchestrator`,
  `test_shadow_rebuild`, `cli_help_snapshot.json`.
- Fixture: `fixtures/migration_head_166/` → `fixtures/migration_head_167/`
  (backup-API upgrade, `journal_mode=DELETE`, integrity and foreign-key checks
  clean). No change to `fixtures/linear_algebra`, `probability` or `arxiv_v2`.
- Docs: `db_generate_reference.py` / `db_validate_reference.py` (head 167, the
  `practice_index` section and field descriptions), the regenerated database
  and configuration reference, and the two prose counts it validates.
