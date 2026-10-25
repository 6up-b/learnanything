# Experiment E0 harness: contextual source embeddings (hosted, no GPU)

**Branch:** `experiments/e0-contextual-embeddings` (worktree `learnanything-e0`, base main `a76c8358a`, migration head 215). Owner-queued 2026-10-21 ("I definitely agree with queueing E0 now"). Spec: `docs/specs/spec_contextual_source_embeddings_experiments_v1.md` §4-§7, §11.

**This stage makes no paid, live or network model or embedding call.** It builds everything E0 needs, up to and including a dry run on fresh backup copies of the owner's vaults. The paid run is a separate, orchestrator-authorized step after review.

## Plan (written before the code)

1. **Package.** `src/learnloop/experiments/contextual_embeddings/` (research code) and `learnloop experiments e0 ...` (CLI). Production packages never import `learnloop.experiments` (an import-linter contract plus an AST test that also covers the namespace package `learnloop.content`). No config key, no migration, no production default changes; CLI flags only.
2. **Baseline handoff (§11 row 1).** A receipt with the delivery-fixes commit (`275fd5f7e`, merged; policy: complete blocks, nearest neighbours, references followed, one budget), the extraction engine/revision of every current extraction, a redacted effective-config allowlist (embedding switches, model/route/dims, rewrite, pool, policy, caps; never a raw dump), the extraction inventory and dense coverage (`source_vectors.source_coverage`). D0/D1 are rebuilt from `tutor.context_delivery`'s public primitives and checked for parity against `tutor_qa`'s own delivery (kill switch off = D0, defaults = D1).
3. **Corpus.** Copies via `learnloop.db.copies.copy_tree_with_databases` into gitignored `fixtures-local/contextual-embeddings/`; read-only attach (never migrated). Policy before encoding: `model_reader_withheld` (solution, assessment lane, held-out, exam) plus `exam_material` (D12), persisted as a policy fingerprint; every artifact carries its dependency keys and is invalidated on a new mark or a re-extraction. Candidate units: deterministic offset-preserving splits, bare equations attached, transcript captions merged toward 300-600 tokens, never across sources, sections, policy boundaries or numbered environments. Windows: 4,096 tokens with markers, section-first packing, no overlap, each unit exactly once, a whole-source window only when the permitted segment fits the provider limit. Dependency maps from numbered references. Families reserved before question generation.
4. **Question bank.** The 16-case smoke bank (built deterministically from the corpus, no model), the 60-80 development-question writer and two-pass label pipeline with a different adjudicator (exact model, transport and prompt hashes pinned), logged questions as a separate slice, evidence sets (AND/OR), Complete Evidence@10 and the other §5.2 metrics, Cohen's κ with the confusion table (S1 gate). Implemented and tested with fakes; costed in the dry run only.
5. **Arms.** D0-D3 delivery; R0-R5 retrieval with exact search (ordinary cosine, stable id tie-breaks) for the representation screen and named system arms. Hosted adapters for Perplexity (`pplx-embed-context-v1-4b` grouped and singleton, `pplx-embed-v1-4b` sibling) and Voyage (`voyage-context-4` grouped and singleton, `voyage-4-large`): grouped response ordering, query/document separation, wrong-method and mixed-space refusal, nonfinite/zero refusal, no silent truncation, contract and price pins (flagged unverified until the canary check), receipts, idempotent resume, canary drift.
6. **Budget.** One E0 spend ledger (file-locked, cross-thread and cross-process) capped at $25 across every paid call, admitted before every request with conservative reservations, unknown billing kept reserved; category sub-caps from §6; per-arm token/latency/bill ledgers; a clean incomplete report on refusal (never substitution).
7. **Stop rules S1-S4** computed from results into the report; adoption never automatic.
8. **Credentials.** Process environment only, configurable names; `--env-file` loads only named variables without printing, logging or persisting them; availability reported present/absent.
9. **Dry run.** `learnloop experiments e0 run --dry-run`: zero network (socket guard installed), nothing written to the copies (tree hash before/after), the frozen plan with arms, units, question counts, tokens per provider and route, $ per arm and total against the cap, keys present/absent. Aggregate committed here.
10. **Report template** (§11): paired delivery and retrieval results, blind answers for finalists, tokens/latency/bills, failure ledger with original denominators, S1-S4 decisions.

## What was built

Research code under `src/learnloop/experiments/contextual_embeddings/` and one CLI group, `learnloop experiments e0 {prepare,run,report}` (`src/learnloop/cli/experiments.py`, which imports the package only inside its commands). Production packages never import it: import-linter contract `experiments-stay-outside-production` (29 contracts now, 28 before) plus `tests/test_e0_isolation.py`, which also scans the namespace package `learnloop.content`, function-local imports and any package added later, and checks in a subprocess that importing `learnloop.cli` loads no experiment module. No migration, no config key, no default changed, no production module edited apart from registering the CLI group. The experiment package writes SQL in one place only (fix round 1, Codex review F1): the redaction of a SERVICE copy's protected block text, refused outside fixtures-local and registered in the architecture test's SQL owners; verdicts and receipts go to a per-copy experiment repository through the production stores (F4, F10).

| Module | What it does |
|---|---|
| `pins.py` | Every frozen constant: the delivery-fixes handoff (`275fd5f7e`, implementation `43060df29`/`0fa0ec1b4`, policy), the $25 cap and §6 allocation ($2 embeddings, $5 drafting/context, $10 labels/audits, $8 answers/verification), retries (2 transient, 0 auth/contract), timeouts, the request cap (6,000), seed 20261021, 10,000 bootstrap resamples, window 4,096 tokens with 8-token chunk markers, unit cap 1,024, caption target 300-600, D1 ceiling 8,192, top-10, pool depth 20, κ 0.60 and the S1-S4 thresholds; the embedding pins (Qwen, Perplexity contextual and independent, Voyage contextual and `voyage-4-large`) with endpoints, query methods, dimensions, output formats, decode transforms, limits, price upper bounds and `contract_verified`/`price_verified` flags; the LLM role pins (route, transport, model, effort, billing, category, output bound, price bound, prompt version); the arm definitions. `pins_fingerprint()` hashes all of it into the run id. The frozen token bound is UTF-8 bytes / 3 (conservative for every provider limit); delivery budgets keep production's chars/4. |
| `credentials.py` | Keys from the process environment only, configurable names; `load_env_file(path, names)` loads only the named variables, never overrides the shell, never prints, logs or persists a value; `availability()` reports `present`/`absent` only. |
| `budget.py` | `E0Ledger`: one file-backed ledger (fcntl lock plus a process lock; atomic replace with fsync) shared by every thread, process, copy and stage. `reserve` admits a request BEFORE it is sent only if reconciled charges plus every outstanding reservation plus this request fit the $25 cap and the request's category; unknown billing keeps the whole reservation; a failed request keeps it; subscription (Codex) requests are admitted at $0 but count against the request cap. `LedgerEnvelope` is a `learnloop.ai.spend.SpendEnvelope` over the ledger, so reused production paths (the source backfill on a service copy) reserve in the same envelope. Per-arm token/latency/bill report. |
| `corpus.py` | `prepare_copies` (backup API via `copy_tree_with_databases`, under `fixtures-local` only, never `arxiv_v2`, each copy then put in rollback-journal mode); `open_copy` (vault without settings or dotenv, database attached read-only and never migrated, a WAL copy refused); the extraction inventory (engine, version, request hash, source bytes hash, fingerprint); `PolicySnapshot` (exam and held-out material by `exam_material`, solutions and the assessment lane by `model_reader_withheld`; fails closed); `ArtifactDependency`, `stale_reasons` and `invalidate` (a new held-out mark or a re-extraction invalidates every dependent window, vector, header, label or packet); the common candidate units (deterministic offset-preserving splits, bare equations attached, captions merged, never across sources, sections, policy segments or numbered environments); section-first windows (each unit exactly once, `assert_partition`); whole-segment windows only when they fit; dependency maps from numbered references; families and their reservation (fixed before any question). |
| `adapters.py` | `encode_documents(list[Document]) -> list[list[Vector]]` and `encode_queries(list[PreparedQuery]) -> list[Vector]` for Perplexity contextual (grouped and singleton), Perplexity independent, Voyage contextual (grouped and singleton), `voyage-4-large`, and Qwen through the production OpenRouter client. Rows matched by `index` (never position), separate query and document methods, `WrongMethod`, `MixedSpace` (an index never mixes spaces; a query from another encoder is refused even at equal width), dimension/finite/nonzero/int8-range validation, int8 and base64-int8 decoding to an L2-normalized FP32 scoring copy, no silent truncation (over-limit inputs refused before sending; Voyage independent sent `truncation: false`), the spec's `document_space_id`/`query_encoder_id`, admission per attempt, two transient retries and none for auth/contract, receipts without headers, keys or bodies, the idempotent `VectorStore` keyed by `document_vector_key`, and canaries (first output cached, drift beyond cosine 0.995 opens a new epoch). |
| `retrieval.py` | Recipes (`production_recipe`, `plain`, R2's deterministic header, R3's generated context), `document_vector_key`/`query_vector_key`, exact cosine search with id tie-breaks, BM25 (contextual BM25 add-on), R3 context generation (one call per window, permitted text only, out-of-range contexts counted), production block hits mapped to units. |
| `delivery.py` | D0 (kill-switch window, 240/600 cuts, no references), D1 (complete blocks, nearest neighbours, references, 8,192 tokens), D2 (smallest outline unit holding the selection), D3 (whole permitted source), each filtered by the experiment's stricter policy with drops recorded; `does_not_fit` runs the named fallback (D2 -> D1, D3 -> D2); delivered coverage by canonical offsets. |
| `bank.py` | The deterministic 16-case smoke bank; development seeds per stratum from development families only (distant pairs by numbered reference, else shared rare terms); the writer prompt and pipeline; logged questions with their real selection only; two blinded, reordered label passes (ordinal relevance plus AND/OR sufficient sets); the audit plan (every disagreement, every accepted set, a seeded 20% of the rest); the adjudicator; evidence sets from labels. |
| `metrics.py`, `evaluate.py` | Complete Evidence@10, Support Recall@10 (first best set wins ties), Answer Recall@10, nDCG@10, MRR, unknown share, Cohen's κ (unweighted and linear) with the confusion table, the paired family-clustered bootstrap, latency p50/p95; per-question rows, arm summaries, completion shares, agreement. |
| `answers.py` | The same tutor route for every arm, two blinded judges in two orders, the adjudicator on disagreement; pass-all-criteria share and components; measured answer latency. |
| `stop_rules.py` | S1-S4 by code with their inputs; S1 blocks the rest; an unpinned Reader latency budget fails S2/S4 closed; `production_adoption` is always `not_authorized_by_e0`. |
| `plan.py`, `runner.py` | The frozen plan and estimate; the dry run (socket guard, tree digests before and after, read-only), the redacted config allowlist, dense coverage, the Markdown render, `freeze` (private manifests), the paid-run authorization check. |
| `callers.py`, `paid.py`, `system_arms.py`, `live.py`, `report.py` | The paid run's steps (never executed here): `E0RequestGate` installed with the existing `gate_model_requests`, so every physical LLM request (retries and JSON repairs included) is admitted by the ledger; checkpointed results for resume; the experiment's metered OpenRouter profile added to an in-memory config only; contracts first, then bank, contexts, every arm, system arms on separate service copies (R0 as configured; R1' with Qwen enabled and backfilled under the ledger), labels, finalists on development, answers, S1-S4; the report template (refuses private fields; renders incomplete runs with their denominators). |

## The dry run (this stage's deliverable)

Fresh copies made with `learnloop experiments e0 prepare` from the MAIN checkout's `fixtures/linear_algebra` and `fixtures/probability` (backup API; `arxiv_v2` never touched), into the worktree's `fixtures-local/contextual-embeddings/vaults/{linear_algebra,probability}-20261021`. The dry run ran under `env -i` with an empty HOME, CODEX_HOME and LEARNLOOP_CONFIG_DIR, no key variable and `OPENROUTER_BASE_URL=http://127.0.0.1:9`; no settings file was read. Committed aggregate: `docs/reviews/artifacts/experiments-e0/dry-run-plan.json` and `.md` (no text, titles, paths or private ids; sources, extractions and families aliased).

Checks: network calls 0 (the socket guard counted none); copy tree digests equal before and after (0 copies changed); database read-only; settings file not read. Keys: `PERPLEXITY_API_KEY`, `VOYAGE_API_KEY`, `OPENROUTER_API_KEY` all absent (as intended).

**Estimate: $8.71 expected against the $25 cap; every category within its allocation.** Worst case $26.13 assumes every request is retried twice; admission stops at the cap long before, so that case ends as an incomplete report, not an overspend. *(Fix round 1 refresh, `docs/reviews/experiments-e0-harness-codex-review.md`: $8.72 expected, $26.16 worst case, every category within its allocation; the online-latency queries and the joint sufficiency reviews are now in the estimate.)*

| Category | Expected $ | Worst case $ | Allocation $ |
|---|---|---|---|
| embeddings | 0.12 | 0.34 | 2.00 |
| drafting/context | 0.00 (Codex subscription) | 0.00 | 5.00 |
| labels/audits | 5.21 (Sonnet 5.5 adjudicator) | 15.63 | 10.00 |
| answers/verification | 3.39 (Sonnet 5.5 answer adjudicator) | 10.16 | 8.00 |

| Arm | Model | Documents / chunks | Requests | Tokens | Expected $ |
|---|---|---|---|---|---|
| R1 / R2 / R3 | qwen3-embedding-8b | 697 / 697 | 14 each | 87,812 / 131,349 / 209,748 | 0.003 / 0.004 / 0.006 |
| R4 grouped / singleton / independent | pplx-embed-context-v1-4b, pplx-embed-v1-4b | 37 windows or 697 / 697 | 4 / 5 / 5 | 66,438 each | 0.013 each |
| R5 grouped / singleton / independent | voyage-context-4, voyage-4-large | 37 windows or 697 / 697 | 4 each | 66,438 each | 0.020 each |
| R0 (both copies) | keyword-only (embeddings off); rewrite on the copy's Codex route | | 133 queries | | 0.00 |
| R1' service (both copies) | Qwen backfill 71,956 tokens plus queries | | | | 0.003 |

| LLM role | Route (billing) | Calls | Input / output tokens | Expected $ |
|---|---|---|---|---|
| writer | Codex `gpt-6-luna` (subscription) | 12 | 57,427 / 11,520 | 0 |
| R3 context | Codex `gpt-6-luna` (subscription) | 37 | 86,330 / 139,400 | 0 |
| label pass 1 / 2 | Codex `gpt-6-luna` / `gpt-5.6-sol` (subscription) | 404 each | 1,725,770 / 153,924 each | 0 |
| adjudicator | OpenRouter `anthropic/claude-sonnet-5.5` (metered) | 101 | 1,597,904 / 153,924 | 5.21 |
| tutor | Codex `gpt-5.6-sol` (subscription; the production tutor route) | 407 | 5,368,932 / 244,200 | 0 |
| judges 1 / 2 | Codex `gpt-6-luna` / `gpt-5.6-sol` (subscription) | 407 each | 3,496,732 / 122,100 each | 0 |
| answer adjudicator | OpenRouter Sonnet 5.5 (metered) | 144 | 1,323,590 / 43,200 | 3.39 |

Subscription tokens tallied `estimated_only`: 16.9 M. The plan's stated assumptions (pool overlap 0.5, every labelled question adjudicated, 35% judge disagreement, three retrieval finalists, header and query sizes) are in the JSON.

**Corpus (aggregates).** Both copies are at migration head 165 (the owner's vaults predate the current schema; the dry run reads them without migrating). Extraction engines: Marker 1.10.2 (`+map2`, `+map3`), the YouTube transcript extractor and the HTML extractor; **no GLM-OCR extraction exists on these copies**, so E0 pins the current Marker extractions as the provisional engine (spec §4.1). Linear algebra: 3 sources, 362 units (260 blocks, 76 with an attached equation, 26 merged caption groups), 10 windows, 23,241 unit tokens, 3 assessment-lane blocks withheld, 16 units with references (10 resolved, 6 unresolved; 6 of the resolved targets lie outside their unit's window). Probability: 4 sources, 335 units (6 splits of oversized blocks, 2 lone equations), 27 windows, 30,440 unit tokens, 65 assessment-lane and 61 solution blocks withheld (two small sources wholly withheld), 9 units with references (8 resolved, 3 outside the window). Every permitted source fits a whole-source window for both contextual families. Dense coverage: off on both (`embedding.enabled` false; 0 of 1,155 blocks embedded), so R0 is keyword-only today.

**Bank.** Smoke: 16 per copy (32), no shortfall. Development: 72 seeds (36 per copy; strata divided by permitted units), inside the 60-80 target, no shortfall. Logged: 29 eligible questions (21 linear algebra: 11 Reader, 8 practice, 2 feedback; 8 probability: 3 Reader, 3 practice, 2 feedback); 26 known-location questions in all.

## Deviations (and why)

1. **Copies in rollback-journal mode.** The owner's databases are WAL; even a read-only open of a WAL copy creates `-wal`/`-shm` files and rewrites the shared-memory index, which the first dry run's tree digest caught ("the dry run changed 2 copies"). `prepare` now converts each fresh copy to `journal_mode=DELETE` (content unchanged: a backup copy's WAL is empty) and `open_copy` refuses a WAL copy. Test: `test_wal_copies_are_converted_and_a_wal_copy_is_refused`.
2. **Label and judge routes.** The spec asks for two independent strong passes and a different strong adjudicator. To fit $25 and follow the owner's Codex rule, pass 1 is `gpt-6-luna`, pass 2 `gpt-5.6-sol` (both Codex), and the adjudicator is Claude Sonnet 5.5 on OpenRouter (a different family from the writer and both passes). The writer is GPT-6 Luna. All pinned in `pins.ROLE_PINS`; open question 2.
3. **Hosted contracts are unverified.** Endpoints, request/response shapes, query methods, dimensions (Perplexity 2,560 is a placeholder) and prices come from the spec's to-validate list. Prices are conservative upper bounds (Perplexity $0.20/M, Voyage $0.30/M, Qwen $0.03/M, Sonnet 5.5 list +10%) used for admission and reconciliation, so they can only stop work early. The paid run sends one public canary per hosted adapter first; a failed or different contract blocks that arm (no substitution).
4. **R1' and R1 (superseded in fix round 1, Codex review F12).** R0 and R1' now run the actual `find_sources` (policy `reading`, the question's intent, intent lists, mandatory verification of non-explain intents, `compare` delegation, two pages with duplicates counted); R1' keeps the first-page `dense_plus_bm25` variant; the production `pool_verify` control (`tutor_pool` + `verify_spans`) is the arm `R1_pool_verify`. A question whose required verification did not run, or whose Qwen search fell back from dense, has no ranking for that arm. Open question 3.
5. **Distant same-source seeds** use a numbered reference when one crosses windows, else the earlier unit sharing the most rare terms (the copies have few cross-window references); units at least 3 apart count as distant inside one window. Each seed records its link kind.
6. **Smoke questions are templated** (pipeline checks only; never used for verdicts).
7. **D0 budget** is the production default 24,000 tokens (the predecessor had none; nothing on these copies reaches it).
8. **Reader latency budget.** No pinned Reader latency budget exists in code; S2 and S4 fail closed unless `--reader-latency-budget-s` is given. Open question 4.
9. **Isolation slips (no effect).** Two `python3` invocations ran outside `env -i`: a one-line text edit of `bank.py` (no app import, no network, no credential) and an empty no-op heredoc. Every other Python or CLI run outside pytest used `env -i PATH HOME=<empty> CODEX_HOME=<empty> LEARNLOOP_CONFIG_DIR=<empty>`.

**Paid calls: none ($0.00).** No network, model or embedding call was made in this stage; every test uses fakes (`tests/e0_fakes.py`: hash-vector embedding transport with shuffled rows, a fake Qwen client, a prompt-reading role responder, a fake structured transport). No key or settings file was read.

## Tests

New files (92 tests): `tests/test_e0_adapters.py` 18 (grouped ordering by index, query/document separation, wrong methods refused before any request, mixed spaces and foreign encoders refused, NaN/inf/zero/wrong-width/out-of-range int8 refused, missing/duplicate indices, oversize refused never truncated, two transient retries each admitted and none for auth, a refused admission sends nothing, absent key fails before admission, idempotent resume by vector key, canary drift, receipts and ledger hold no key, Qwen prefixes and per-batch admission, exact-search ties), `tests/test_e0_budget.py` 9 (cap and allocations, outstanding and unknown-billing reservations, failed requests keep reservations, global cap across categories, subscription at $0 with the request cap, 16 threads and 4 spawned processes never overshoot, the ledger as a `SpendEnvelope`, the request gate), `tests/test_e0_corpus.py` 18 (exam and solution material never in a unit, withheld blocks as hard boundaries, deterministic units and offset maps, exact split coverage, equation attachment, caption merging, numbered environments, window partition and bound, whole-segment windows, reference dependencies, later held-out mark invalidation, re-extraction invalidation, policy failure fails closed, read-only never-migrated open, backup-API copies under fixtures-local only, families and reservation, aggregate inventory, WAL conversion), `tests/test_e0_delivery.py` 6 (D0 and D1 span-for-span equal to `tutor_qa`'s Reader delivery with the kill switch off and on, with and without a quote; canonical prefix coverage; D2/D3 complete and policy-filtered; `does_not_fit` fallbacks; retrieved D0/D1), `tests/test_e0_bank.py` 8, `tests/test_e0_metrics_stop_rules.py` 12, `tests/test_e0_credentials.py` 4 (named-only loading, shell precedence, never echoed to stdout, stderr or logs), `tests/test_e0_dry_run.py` 7 (socket guard, zero network and unchanged tree, plan contents, aggregate-only plan, the CLI with `--env-file` never prints the key, paid run refused without authorization, strata split), `tests/test_e0_isolation.py` 4, `tests/test_e0_paid_fakes.py` 6 (a full fake paid run with every arm and S1-S4, a budget stop reported incomplete with no substitution, resume re-sends no document, the live caller admits each physical request and resumes from checkpoints, R0 on a service copy leaves the frozen copy untouched, a pinned Reader budget checked against measured latency). Support: `tests/e0_fakes.py`.

Changed: `tests/cli_help_snapshot.json` (root help plus the five new `experiments` entries; nothing else changed).

## Gate (this step)

Recorded below, after the open questions.

## Commands for the paid run (orchestrator-authorized, after this review)

Run from the worktree (or the merged tree) with the app's normal environment: the paid run loads the owner's settings file itself (`open_copy(load_environment=True)`); `--env-file` is optional and loads only the named key variables, never printed. The cap is fixed at $25 with the §6 allocation; the request cap is 6,000; transient retries 2, auth/contract retries 0; the ledger lives at `fixtures-local/contextual-embeddings/runs/ledger/` and is shared by every later E0 run (one envelope across copies and stages).

```bash
# 1. Fresh backup-API copies (rollback journal; never arxiv_v2)
uv run learnloop experiments e0 prepare \
  --from /home/saturn/Documents/thinking/learnanything/fixtures/linear_algebra \
  --from /home/saturn/Documents/thinking/learnanything/fixtures/probability \
  --label <YYYYMMDD> --dest fixtures-local/contextual-embeddings/vaults

# 2. Dry run on those copies (must fit; writes nothing to them, no network)
uv run learnloop experiments e0 run --dry-run \
  --copy fixtures-local/contextual-embeddings/vaults/linear_algebra-<YYYYMMDD> \
  --copy fixtures-local/contextual-embeddings/vaults/probability-<YYYYMMDD> \
  --env-file <PATH/TO/KEYS.env> \
  --out fixtures-local/contextual-embeddings/runs/plan.json

# 3. The paid run (canaries first; every request admitted by the ledger)
uv run learnloop experiments e0 run \
  --copy fixtures-local/contextual-embeddings/vaults/linear_algebra-<YYYYMMDD> \
  --copy fixtures-local/contextual-embeddings/vaults/probability-<YYYYMMDD> \
  --env-file <PATH/TO/KEYS.env> \
  --reader-latency-budget-s <SECONDS> \
  --run-dir fixtures-local/contextual-embeddings/runs \
  --i-am-authorized-to-spend

# 4. Aggregate report per copy (refuses private fields) for docs/reviews
uv run learnloop experiments e0 report \
  --results fixtures-local/contextual-embeddings/runs/<run_id>/<copy>/results.json \
  --out docs/reviews/experiments-e0-report-<copy>.md
```

Optional `--perplexity-key-env`, `--voyage-key-env`, `--openrouter-key-env` rename the key variables (D13). A rerun of step 3 resumes: stored vectors, checkpointed LLM results and the ledger are keyed by complete input identity, so only missing work is paid for (canaries are re-sent each run by design).

## Open questions (with the defaults in force)

1. **Provisional extraction engine.** No GLM-OCR extraction exists on the copies. Default: pin the current Marker 1.10.2 extractions (recorded per source in the plan) and label every result "Marker, provisional"; re-extraction invalidates all artifacts.
2. **Label independence.** Default: passes `gpt-6-luna` and `gpt-5.6-sol` (Codex), adjudicator Claude Sonnet 5.5 (OpenRouter, metered). Alternative: a metered second pass (Sonnet 5.5) with Opus 5.5 adjudicating, which the dry-run arithmetic suggests would exceed the $10 labels allocation.
3. **R1' scope (updated in fix round 1).** Default: `find_sources` itself and the `pool_verify` control, verification on the service copy's own `source_rerank` route (Codex: $0 billed, more latency; a metered route needs `source_retrieval.llm_price_per_million` or is refused). Alternative: the retrieval core only (a named diagnostic, not R1').
4. **Reader latency budget for S2/S4.** Default: none pinned, so S2 cannot prefer direct reading and S4 cannot pass until the orchestrator passes `--reader-latency-budget-s` (suggested: the incumbent D1 p95 measured in the same run, or the Reader's 15 s retrieval time box plus the tutor's own budget).
5. **Hosted contract details.** Default: the canary validates shapes and dimensions before any paid call; a mismatch blocks the arm for contract review (the adapter's request builder and parser are the one place to adjust). The Perplexity contextual query method and int8 encoding name are the least certain pins.
6. **Independent families.** Seven sources become seven families (three linear algebra, four probability; two probability sources are wholly withheld). Default: `MIN_INDEPENDENT_FAMILIES = 5` decides "exploratory"; most questions come from two books, so treat every interval as exploratory regardless (S4 defers E1 when underpowered).
7. **Owner vault schema.** Both copies are at migration head 165. Default: read without migrating (the dry run proves the read paths work); the system-arm service copies are opened through the vault repository and may be migrated there (service copies only); if the migration coordinator refuses to upgrade a service copy, R0 and R1' are recorded as blocked and the report is incomplete.
8. **Latency regression tolerance (fix round 1, Codex review F9).** Default: `pins.LATENCY_REGRESSION_TOLERANCE = 0.10`: an arm's paired p50 and p95 may exceed the incumbent's (D1 for S2; the best one-model arm's online D1 path for S4) by at most 10%, and its p95 must meet the frozen `--reader-latency-budget-s` deadline. Alternative: a strict no-increase rule.

## Gate (this step, on `7fa5ee6ba`)

Owner rule 2026-10-17: no full suite, durability lane or vitest here; they run once in the landing gate. No migration, DB/connection code, frontend, `src-tauri` or schema change, so no durability, vitest, cargo or DB-reference step applies.

- `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2`.
- `uv run lint-imports --no-cache` (under `env -i`): **29 kept, 0 broken** (28 before plus `experiments-stay-outside-production`).
- `uv run pytest -n auto <files>` with `TMPDIR=fixtures-local/tmp`: **210 passed** across 21 files: the ten new `tests/test_e0_*.py` (92: adapters 18, bank 8, budget 9, corpus 18, credentials 4, delivery 6, dry_run 7, isolation 4, metrics_stop_rules 12, paid_fakes 6); the contracts `tests/test_architecture.py` (18), `tests/test_cli_help_snapshot.py` (1), `tests/test_sqlite_file_copies.py` (1), `tests/test_tracked_fixture_databases.py` (2); the modules whose helpers or contracts the new tests reuse or read, `tests/test_tutor_delivery_fixes.py` (56), `tests/test_source_inventory.py` (17), `tests/test_reader_observation_records.py` (6), `tests/test_approach_map_boundaries.py` (3), `tests/test_workbench_hint_service.py` (5); and the CLI tests `tests/test_cli_entrypoint.py` (2), `tests/test_cli_commands.py` (7).
- The main checkout's tracked fixtures are unchanged by this stage (`git status` there is as it was at the start; only backup-API reads touched them).
