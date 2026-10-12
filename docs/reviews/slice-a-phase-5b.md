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
