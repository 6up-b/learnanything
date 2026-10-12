# Slice 2 T5: ingest and graph nomination

Branch `slice-2/t5`, worktree `learnanything-t5`, base `974c5647` (main).
Spec: `spec_embedding_consumers_v1.md` §8 (T5), with §1 (R1–R6; R4 means
embeddings shortlist and judges decide, no calibrators), §4, §12, §13 (T5 row).
Prerequisite "previous track's report reviewed" waived (owner, 2026-10-12;
`implementation_goal.md` §1a: tracks are built in parallel, report gates are
post-hoc).

## 1. Plan (written before coding)

**What T5 changes.** Ingest and graph review gain embedding *nominations*.
Embeddings never decide identity (`spec_knowledge_model.md` §14: "no embeddings
for facet identity"): the append-reconciliation LLM, the graph-structuring LLM
or the owner decides. Doctor and review passes gain a cosine column next to
Jaccard. Registry vectors are the Phase 1 stored vectors; a missing or
incomplete index degrades to today's lexical behaviour, labelled as such.

**Files to add**
- `src/learnloop/content/synthesis/graph_nomination.py`: the nominator. Loads
  the stored registry index for one recipe (`facet/definition`,
  `concept/definition`) for the configured model, requires the complete current
  manifest, ranks by exact mean-centred cosine (the Phase 1 retrieval maths),
  embeds new LLM-written candidate text at ingest under spend caps (content
  addressed, so reruns and revalidation never repay), records receipts, and
  never raises into ingest: every failure degrades to lexical with a status.
- `src/learnloop/ops/graph_nomination_report.py` and
  `learnloop embeddings nomination-report` (the T5 report, §13: nomination recall
  on doctor-found duplicates), with `--dry-run`.
- Tests: `tests/test_graph_nomination.py`, `tests/test_graph_nomination_report.py`.

**Files to change**
- `vault/embedding_recipes.py`: `concept/definition` (LLM-written title,
  description, aliases) and `facet_repair/text` (one record per distinct
  instructional repair, for the repair shadow); recipe text functions accept
  payload dicts so ingest candidates hash exactly like registry records.
- `db/stores/embedding_vectors.py`: content-addressed read (same model, kind,
  field, prefix and content hash), so a candidate embedded at ingest is reused
  after apply and by revalidation.
- `ai/embedding.py`: the embedding price table moves here from
  `ops/embedding_backfill.py` (content may not import ops).
- `config/schema.py`, `config/template.py`: `[graph_nomination]` (kill switch,
  `top_k`, ingest query caps); fingerprint snapshot with a recorded decision.
- `append_neighborhood.py` / `source_append.py`: top-k registry facets and
  concepts nearest each new inventory claim / concept mention are unioned into
  the bounded neighbourhood as `embedding` match reasons, next to the lexical
  and provenance reasons. The lexical loose round is unchanged. The
  reconciliation LLM decides.
- `source_set_synthesis.py` / `ai_contracts.py`: the graph-structuring pass
  receives registry concept titles and definitions for the nominated
  candidates (not ids alone) and may decide `registry_merges` (candidate concept
  = existing registry concept), applied deterministically with guards (same
  type, nominated id, known candidate). Prompt, context and result model change
  only when nominations exist, so the kill switch restores today's request
  byte for byte.
- `facet_mint_gate` call site (`_normalize`): a repair-equivalence shadow for
  `distinct_repair` and the embedding top-k for each candidate are recorded
  beside the D2 verdicts (`coverage_decisions.graph_nomination`). They never
  change a disposition.
- `synthesis_gates.py`: the near-duplicate review diagnostic shows cosine
  beside Jaccard when vectors exist.
- `ops/doctor.py`, `facet_doctor.py`, `facet_candidates.py`, CLI
  `facet-mint-gate` / `facet-candidates`: cosine column next to Jaccard
  (stored vectors only; review passes never make paid calls).
- CLI help snapshot, config/DB references regenerated.

**Migrations.** None planned: vectors go to `embedding_vectors`, verdicts to
`judgment_ledger`, nomination records to existing manifest / synthesis-run JSON.

**Algorithm successor and kill switch.** No successor: nothing scored,
scheduled, projected or served changes meaning; T5 changes only what an
authoring LLM is shown and lets it decide one more kind of merge. Kill switch:
`graph_nomination.enabled = false` (or `embedding.enabled = false`, the
default) restores today's lexical-only behaviour exactly. Rebuild and replay
never construct a nominator (zero model or embedding calls).

**Spend caps and routes.** Ingest-time candidate embedding uses the existing
`ai.routing.embedding` route (never falls back), the Phase 1 `SpendBudget`
with `[graph_nomination]` caps (texts, calls, tokens, dollars; default $0.05
per ingest run), unknown price fails closed (degrade to lexical), receipts
under `owner_kind='graph_nomination'`. The report's paid step is the Phase 1
backfill of the three recipes it needs, with its caps and `--dry-run`. No new
LLM route: the deciders are the existing `canonical_ingest` (structuring) and
`append_reconciliation` routes.

**judgment_ledger writes.** Each `registry_merges` decision of the structuring
LLM appends a `same_concept` verdict (`judge='llm'`, model, prompt version,
input hash), including ones the deterministic guard refused (rationale records
`applied=false` and why). The report reads `same_concept` / `duplicate_facet`
`same` verdicts as additional confirmed pairs.

**Tests.** Recipes and content hashing; content-addressed lookup; nominator
degrade paths (kill switch, embedding off, incomplete index, unknown price,
provider failure, cap overflow) with zero calls where promised; append
neighbourhood union with lexical byte-identity when off; structuring
nominations, registry merges, guards and ledger rows; R1 test (embedding
nominations alone never merge, alias or change a D2 disposition); doctor /
review cosine columns; revalidation makes no embedding call; the report with a
fake client on a fixtures-local style copy, including `--dry-run` with zero
calls and no data changes.

## 2. What was built

**Substrate (additive).**
- Recipes `concept/definition` (title, type, synthesis-written description,
  aliases; no ids, tags or edges) and `facet_repair/text` (one record per
  distinct instructional repair of a non-retired facet, keyed by the text's
  digest). Recipe text functions now accept proposal payloads, so a candidate
  is hashed exactly as its later backfill would be. `facet/definition` and
  `item/stem` hashes are byte-identical to Phase 1 (checked against base).
- `get_vector_by_content` / `current_vectors` in the vector store: the same
  model, kind, field, prefix and content hash is the same input, so a vector
  paid for at ingest serves the applied record, a revalidation, or a rerun.
  `current_vectors` still refuses an incomplete manifest.
- `EMBEDDING_PRICES_PER_MILLION` moved to `ai/embedding.py` (the backfill keeps
  its `PRICES_PER_MILLION` name).

**`content/synthesis/graph_nomination.py`.** `GraphNominator`:
- `for_review` (stored vectors only; never constructs a client) and
  `for_ingest` (may embed new LLM-written text). Both return `None` unless
  `graph_nomination.enabled` and `embedding.enabled` are on.
- `RegistryIndex`: the complete current index of one recipe; exact
  mean-centred cosine, ties by id. A test pins its ranking and scores to the
  Phase 1 `retrieve()`.
- Ingest embedding: content-addressed reuse first, then batched calls on the
  `ai.routing.embedding` route under a per-run `SpendBudget`
  (`[graph_nomination] max_query_texts / calls / tokens / cost_usd`), receipts
  under `owner_kind='graph_nomination'`, vectors persisted. Unknown price,
  unavailable route, client model/width mismatch, exhausted cap and provider
  failure each degrade to lexical with a recorded note; nothing raises into
  ingest. Ingest pays only to compare against a complete, non-empty registry
  index.
- `summary()`: the honest label recorded wherever nominations are used
  (`active`, `lexical_only` with per-index status such as `index_incomplete`,
  `empty_registry`), plus counts, charges and notes.

**Consumers.**
1. *Append neighbourhood* (`append_neighborhood.py`, `source_append.py`): each
   new inventory claim (and procedure contract), composed in the
   `facet/definition` layout, nominates its top-k registry facets; each concept
   mention, in the `concept/definition` layout, its top-k registry concepts.
   They join as one `embedding` match reason per entity. Lexical and provenance
   matches keep today's order and come first, so under the token cap
   embeddings only add; the loose lexical round is unchanged. The manifest
   record carries `nomination` only when nominations are on. The
   reconciliation model decides reuse vs mint.
2. *Graph structuring* (`source_set_synthesis.py`, `ai_contracts.py`): each
   candidate concept nominates its top-k registry concepts; the pass receives
   `registry_concept_details` (id, title, type, aliases, definition) and
   `registry_nominations` (ids nearest first, no scores, so the model is not
   anchored on a number). A prompt addendum tells it nominations are not
   evidence and lets it decide `registry_merges`. Guards: surviving candidate,
   nominated registry id, same type, one decision per candidate. An applied
   merge drops the candidate and rewrites every reference
   (`concept_client_id` to `concept_id`, prerequisite/confusable client lists
   to canonical lists, dependencies, relations). Nominations also make the pass
   run when it otherwise would not (single shard with relations).
3. *D2 mint gate shadow* (`annotate_mint_report`, recorded in
   `coverage_decisions.graph_nomination`): per candidate, the top-k registered
   facets by definition embedding (marking which D2 also compared), the cosine
   of every D2 pair, and the **repair-equivalence shadow** for every D2 pair
   with repairs on both sides: the text `distinct_repair` verdict next to, for
   each repair the text test calls exclusive, the best raw cosine to any
   neighbour repair (`min_best_cosine` = the least-covered "distinct" repair).
   Dispositions never change (tested).
4. *Cosine column next to Jaccard*: doctor `concept:merge_candidate:*`,
   `evidence_facet:merge_candidate:*`, `evidence_facet:registry_near_duplicate`;
   `facet_doctor.near_duplicate_facet_review` (doctor and the post-append
   merge-review proposals); `facet-candidates` (registry pairs; other kinds say
   `no_stored_vector_for_candidate_kind`); `facet-mint-gate` (JSON gains
   `graph_nomination`, text shows the deciding pair's cosine); the synthesis
   near-duplicate gate message. A missing value says why
   (`cosine_status: index_incomplete` etc.). All stored-vector only.
5. *Ledger*: every `registry_merges` decision appends a `same_concept` verdict
   (`judge='llm'`, model, `mvp-0.7-concept-graph-structuring-1+t5-registry-nominations-1`,
   input hash of both definitions, `left_kind='concept_candidate'` keyed by the
   candidate definition's content hash), including refused ones
   (`applied=false`, `refused=<reason>`).

**The T5 report** (`ops/graph_nomination_report.py`,
`learnloop embeddings nomination-report`):
- ground truth without vectors: doctor registry near-duplicate facets, D2
  ALIAS verdicts from a registry re-run, doctor concept merge candidates
  (strong alias / similarity), and current-registry `same` verdicts in the
  ledger (`same_concept`, `duplicate_facet`; highest authority, supersession
  respected);
- paid step: the Phase 1 backfill of `facet/definition`, `concept/definition`
  and `facet_repair/text` (its caps, `--dry-run`, `--price-per-million`);
  `--stored-only` skips it;
- metrics: recall@{1,3,5,10,top_k} per source, cosine at 90/95/100% recall
  (candidate blocking cutoffs per R4, recorded and read by nothing), all-pairs
  noise floor, misses at top_k, embedding-only mutual nearest pairs (unjudged),
  the repair shadow over D2's registry pairs against a repair noise floor, the
  ingest records, and ledger counts.

## 3. Decisions and deviations

1. **No algorithm successor, no migration.** Nothing scored, scheduled,
   projected or served changes meaning. T5 changes what an authoring model is
   shown (and adds one decision it may make). Vectors, verdicts and records
   reuse `embedding_vectors`, `judgment_ledger` and existing JSON columns.
2. **Kill switch.** `graph_nomination.enabled = false` (or the default
   `embedding.enabled = false`) gives byte-identical pre-T5 behaviour: no
   nominator is built, no client constructed, prompts/contexts/result models
   and manifests are unchanged (tested: prompt equality, manifest record
   equality, absent keys). `embed_new_text = false` keeps nominations to stored
   vectors only.
3. **Mint gate: shadow, not nomination into D2.** Top-k always returns k
   neighbours (no cutoff exists yet, R4), so feeding embedding neighbours into
   D2 would put every candidate in front of the harness and turn
   payload-poor candidates into `proposed` (ABSTAIN) by embedding alone, a
   decision neither the structuring model nor the owner made. They are
   recorded beside the verdicts instead, and the report measures them. No new
   review diagnostics either: a `review` diagnostic downgrades the append
   auto-apply lane, which would add owner friction to protect the model.
4. **Structuring pass decides registry merges.** The spec gives the
   structuring model titles and definitions "for the nominated candidates";
   without an output it could only relate, never decide, so
   `registry_merges` was added (prompt/result model switch only when
   nominations exist). Guards are deterministic and never fire on a score.
5. **Ingest-time embedding has no `--dry-run`.** `learnloop synthesize` and
   the append path had none before T5. The new paid side effect (embedding a
   run's candidate text) is capped per run in config (default $0.05; at the
   spec's $0.01/M that is ~5M tokens), receipted, and off unless the owner has
   enabled embeddings and backfilled the registry. The report command, the
   stage's own paid command, has `--dry-run`.
6. **Bootstrap shards are unchanged.** Shards still receive `registry_index`
   ids; T5 nominates at the structuring pass (spec §8) and in append. Concept
   identity by slug (`_normalize`) stays an exact key.
7. **Cosine kinds.** Registry comparisons use the mean-centred cosine over the
   complete current index (Phase 1 maths). The repair shadow uses raw cosine
   (no registry centroid for individual repair texts), labelled `raw`, and the
   report compares it with a measured repair noise floor (R6), not a constant.
8. **Revalidation is stored-only.** It re-derives the shadow from
   content-addressed vectors and makes zero model or embedding calls (tested
   with the paid route patched to fail).

## 4. Manual runs (fixtures-local, backup-API copies)

Copies of the worktree's tracked `linear_algebra` and `probability` were made
with `copy_tree_with_databases` under `fixtures-local/` (`t5-linear_algebra`,
`t5-probability`, and `t5-linear_algebra-fake` for the fake run). Embeddings
were enabled on the copies as instructed (`routing.embedding =
"openrouter_embedding"`, the `openai_embedding` profile, `[embedding]` with both
switches on). Tracked fixtures are untouched.

- **Fakes** (`t5-linear_algebra-fake`, bag-of-words embedder, 256 dims, no
  network): dry-run planned 118 records / 4 calls; the report completed (4
  fake calls). 39 facets, 23 concepts, 56 distinct repairs.
- **Dry-run, real config** (`t5-linear_algebra`): 118 pending records, 4 calls,
  53,593 estimated tokens, $0.000536 estimated at the spec price; caps $0.25.
- **Real run** (`learnloop embeddings nomination-report --vault
  fixtures-local/t5-linear_algebra --json`, OpenRouter
  `qwen/qwen3-embedding-8b`, resolved `Qwen/Qwen3-Embedding-8B`): **4 calls,
  8,009 reported input tokens, provider-reported cost $0.000080** (budget
  charged its conservative estimate, $0.000536). Status `complete`. This is the
  only paid traffic of the stage.
  - Facets: no doctor-found duplicates in this vault (no Jaccard ≥ 0.85 pair,
    no D2 alias), so facet recall has n = 0. Noise floor of centred cosine over
    741 pairs: p50 −0.06, p95 0.35, p99 0.58, max 0.83. 13 embedding-only mutual
    nearest pairs, several plausibly duplicates the lexical passes miss (for
    example `facet_for_all_x_y_in_f_n_coordinatewise_addition_is_co` vs
    `facet_for_x_and_y_in_f_n_coordinatewise_addition_is_co`, cosine 0.82;
    the two "addition assigns an element…" facets, 0.73). Unjudged.
  - Concepts: 2 doctor similarity pairs; recall@1 0.0, recall@3/5/10 1.0;
    cosine keeping 100% of them 0.34 (noise p95 0.35). 6 embedding-only mutual
    nearest pairs (e.g. `concept_scalar_fields` vs `concept_scalars_over_r_or_c`).
  - Repair shadow: 1 D2 pair with repairs; text says distinct; its least-covered
    exclusive repair has raw cosine 0.54 to the neighbour's repairs, below the
    repair noise p95 (0.64), so no MINT-bias case here.
- `t5-probability` was not reported: its copy fails vault validation on a
  pre-existing malformed practice item
  (`subjects/counting/practice-items/pi_exercise_01kyn22qcffk7sae9ttxvz4j5n.yaml`,
  line 32). The report, like the backfill, refuses vaults with validation
  issues; the owner should run doctor on the live vault first.

## 5. Owner-run commands (live vaults stay the owner's)

Enable on the vault first (`learnloop.toml`): `[embedding] enabled = true`,
`backfill_enabled = true`, an `openrouter_embedding` profile and
`ai.routing.embedding = "openrouter_embedding"` (the owner's configs predate
Phase 1). `[graph_nomination]` needs nothing: its defaults are on and act only
with embeddings on.

```bash
# The T5 report: plan first, then the paid backfill + report (cents or less).
uv run learnloop embeddings nomination-report --vault <vault> --dry-run --json
uv run learnloop embeddings nomination-report --vault <vault> --json
# Re-read from stored vectors only (no calls), e.g. after an ingest:
uv run learnloop embeddings nomination-report --vault <vault> --stored-only --json
# Review passes with the cosine column (no calls):
uv run learnloop doctor --vault <vault> --json
uv run learnloop facet-mint-gate --vault <vault> --json
uv run learnloop facet-candidates --vault <vault>
# Kill switch, if needed: [graph_nomination] enabled = false
```

After the backfill, every synthesis and append run nominates live (capped per
run). The report's `ingest` block then counts those runs, and the ledger block
the structuring model's `same_concept` decisions.

## 6. Open questions

1. **Blocking cutoffs.** The report records cosine-at-recall per model and
   kind. Should a later change let review passes or the append neighbourhood
   drop nominations below such a cutoff (R4), or should T5 stay top-k only?
   Today nothing reads a cutoff.
2. **Facet nominations into D2.** Once a cutoff exists, should
   embedding-nominated pairs above it be put in front of the D2 harness (which
   then decides), or stay a shadow until an LLM judge (`duplicate_facet` task)
   decides them? The 13 embedding-only facet pairs on `linear_algebra` suggest
   a judge pass would find real duplicates.
3. **Owner merges in the ledger.** `learnloop merge-concepts` (owner identity
   decisions) does not append `same_concept` owner verdicts; adding it would
   give the report confirmed pairs, though merged-away records then have no
   current vector.
4. **Shard context.** Should bootstrap shards also receive nominated registry
   facet and concept definitions (not only the structuring pass)? Out of T5's
   spec text; it would change shard checkpoint keys.
