# Slice A Phase 5a: PF-b generation, verification, selection, publishing

**Branch:** `slice-a/phase-5a`, created from `main` at `974c5647` (Phase 1, the
Phase 2/3 integration and its Codex re-review). The handoff's branch instruction is
overridden: the worktree and branch already existed.

## Plan (written before coding)

Specs read: `CLAUDE.md`; `docs/learnloop-architecture-vault/Home.md`;
`docs/algorithm-change-playbook.md`; `spec_slice_a_practice_and_field_v1.md` in full;
`spec_embedding_consumers_v1.md` §§5.1, 5.3, 5.4, 5.6, 5.7, 5.8 and §13; the Phase 1,
Phase 3 and integration reviews; `db/table_roles.py`.

### Files to add

| File | Role |
|---|---|
| `migrations/169_pf_generation.sql` | `pf_candidates` (WORKFLOW), `item_skeletons` (WORKFLOW), `item_fingerprints` (DERIVED) |
| `db/stores/pf.py` | The only SQL writer for the three tables |
| `content/authoring/pf_sandbox.py` | Bubblewrap sandbox runner built on `concept_animation._sandboxed_command`: fails closed without `bwrap` on every platform; CPU, memory, file-size and wall-clock limits; no vault paths or keys in the environment; generator-program and sympy-equivalence harnesses |
| `content/authoring/pf_contracts.py` | Wire models and versioned prompts for every PF role |
| `substrate/item_fingerprints.py` | Pure symbolic fingerprints in the 077 namespaces, plus the one DERIVED replayer |
| `ops/pf_calls.py` | Role-routed caller: spend admission, per-call checkpoint (`model_work_checkpoints`), receipts, `estimated_only` for Codex |
| `ops/pf_generation.py` | Plan, dry run and run: generator programs, the ensemble path, the single-shot pilot arm; verification, filters, solver panel, structure check, freshness gate |
| `ops/pf_selection.py` | Lexical diversity kernel, MMR and Vendi scores (pure) |
| `ops/pf_publish.py` | Publication into the family as ordinary items, capped per UTC day |
| `ops/embedding_compare.py` | The shared `learnloop embeddings compare` harness with two suites: `b2` and `valid_alternative` |
| `ops/pf_reports.py` | Pilot and scaling-check reports (generation-path comparison, blind pairwise LLM judge, usage signals) |
| `cli/pf.py` | `learnloop pf generate / publish / status` |

### Files to change

`config/schema.py` (`[pf]` section; `pf_proposers`, `pf_selection_judge` routes; list
routes), `config/template.py` (`[pf] generation_enabled = false`, defaults fingerprint),
`params/parameter_registry.py` (`pf.*` operational), `ai/routing.py` (two tasks, list
resolution), `vault/models.py` (`difficulty_source = "solver_panel"`),
`vault/embedding_recipes.py` (`item/skeleton`), `db/table_roles.py`,
`substrate/rebuild_orchestrator.py` (one replayer), `db/repositories.py` (claim one mint
request by id; the generic rotation claim skips `pf_*` jobs), `cli/embeddings.py`
(`compare`), `cli/evaluation.py` (`eval pf-pilot`, `eval pf-scaling`), the sidecar
settings display of list routes, the head fixture and generated references.

### Migrations

One migration, `169_pf_generation.sql` (next free at branch time; Phase 5b is being
renumbered to 169 separately, so expect a renumber at merge). Head fixture
`migration_head_168` → `migration_head_169` by the `CLAUDE.md` procedure.

### Algorithm successors and kill switches

No algorithm successor: publishing verified items is a content change (Slice A §0.3).
Kill switch `pf.generation_enabled`, off in the template; it gates every paid PF command
and publication. `pf.max_published_per_day` (default 10) caps publication per UTC day.
`item_fingerprints` holds rows only for family members, so vaults without families
rebuild unchanged.

### Spend caps and routes

Every paid command uses the Phase 1 framework: `--dry-run` first; candidate, pair, call,
retry, token and dollar caps before each request; unknown metered prices fail closed;
Codex routes run on the subscription (no physical-request bound; token and dollar caps
recorded but not enforced; `estimated_only` on receipts; call and candidate caps still
apply). Routes: `pf_generator`, `pf_proposers` (list; at least two distinct model slugs,
else refused), `pf_solver_panel` (one profile or a list; P10 default three solves per
model), `pf_reference_verifier` (agreement plus the LLM-written sympy check),
`pf_isomorph_judge` (structure check and freshness), `pf_selection_judge`. The scaling
check's tiers are configured route lists `[pf.scaling] cheap` / `frontier`.

### `judgment_ledger` writes

`answer_equivalence` (per panel solve: LLM agreement, then the sandboxed sympy check as
`verifier`), `reference_verified` (per candidate), `isomorph` (structure check against
the parent; freshness against same-LO items), `selection` (ensemble judge),
`pf_publish` (publication decision), `pilot_rating` (blind pairwise judge). Workflow
tables hold pipeline state only; every report reads verdicts from the ledger.

### Tests

Sandbox (network, vault reads and writes outside scratch denied; fails closed without
bubblewrap; limits), generator programs (invariance, CAS), ensemble (two distinct
proposers, panel disagreement never published, structure check, the selection judge
never offered unverified candidates), freshness and fingerprints, solver-panel
difficulty, publication cap and card/membership, replay never executes a generator,
no-family rebuild unchanged, dry-run makes no calls, resume never repays, Codex
`estimated_only`, the compare harness suites, the pilot/scaling reports, CLI help, a
fake-model end-to-end run of both paths on a `fixtures-local/` copy.

The plan above was carried out, plus the source-anchored path (§5.3) and its
closed-book, figure-only and provenance filters (§5.4), which the spec list for this
phase includes; see "Deviations".

---

## What was built

### Two generation paths, a source-anchored path and the pilot baseline

`learnloop pf generate` runs one durable job per (family, path, relation, round, tier).
Paths (`--path`, or `auto`: the family's `source_kind`, else `pf.default_path`):

- **`generator`** (procedural drill). The LLM (`pf_generator`) writes one program per
  family (protocol `pf-generator-v1`: `generate(seed)` and `check(draw, answer)`). It
  runs only in the bubblewrap sandbox, where unit tests assert, over
  `pf.generator_test_draws` seeds, that every draw self-verifies by its own sympy/exact
  `check`, that `check` rejects negative controls (catches an always-true check), that
  the checkpoint list is identical for every draw and equals the declared one, and that
  the surface varies. A failing program is retried with the failure text (bounded by
  `--max-retries`); a passing one is stored as the family's authored `generator`
  content (`source_kind = "generator"`, reference `verified` by `generator_cas_unit_tests`).
  Draws are CAS-verified isomorphs; the solver panel then sets difficulty and rejects
  outliers (no panel solve reaches the CAS answer). One structure check per program
  confirms structure and rubric applicability.
- **`ensemble`**. At least two **distinct model slugs** propose (`pf_proposers`); fewer
  is refused before any call, at plan time and again on the resolved clients. The solver
  panel (`pf_solver_panel`, P10 default: every listed model, three solves each) solves
  each stem without the proposer's answer. The reference is `verified` only when at least
  `pf.min_agreeing_solves` (≥ 2) panel solves agree: the verifier (`pf_reference_verifier`)
  judges agreement and, for numeric/symbolic answers, writes a sympy check that must also
  confirm it inside the sandbox. A declared isomorph must pass the structure check
  (`pf_isomorph_judge`): otherwise it is relabelled `near`/`far` or rejected, and the
  parent's rubric must apply verbatim. The selection judge (`pf_selection_judge`) ranks
  the verified survivors as a whole with MMR and Vendi scores as input; the code asserts
  that nothing unverified is offered and ignores refs it did not offer.
- **`source_anchored`**. Answer first from a cited span of the LO's teaching sources
  (`practice_leakage.build_cross_source_spans`, assessment-adjacent sources excluded) or
  quotes on the parent. The reference is verified only when the quoted span (≥ 4 words)
  appears verbatim in that passage, and a "method does not apply" item carries its
  counterexample. Why-items without a verified span are relabelled `inferred` and never
  published (provenance filter). Source-specific items a closed-book model
  (`pf_closed_book`) answers correctly are rejected (closed-book filter).
- **`single_shot`**: the pilot's baseline arm. One `pf_generator` call, measured through
  the same verification and filters, status `baseline`, never published.

### Filters, freshness, difficulty, selection

Order, cheapest first: the shared **authoring instrument chain**
(`authoring_gates.build_instrument_gates`: selected-response ban, persona and
contrast-pair gates), the **held-out exam leakage** screen (`practice_leakage`),
**exact-key duplicates**, verification, **solver-panel outliers**, the **structure
check**, the **freshness judge**. Closed-book, figure-only and provenance are recorded
`not_applicable` on paths they don't apply to; no figure items exist yet.

- **Fingerprints** (`substrate/item_fingerprints.py`) use the 077 namespaces:
  `surface_hash/stem` and `parameter_template/parameters` are exact keys that decide a
  duplicate; `verbatim_target` (answer, answer + key quantities, sandbox-computed sympy
  normal form), `parameter_template/generator` and `solution_recipe/skeleton:<model>` are
  suspect keys that always send a pair to the judge and never reject alone (R1/R2).
- **Freshness.** Each candidate is judged against every item of its LO when the LO has
  at most `families.max_exhaustive_items` (40) items, else against its suspects, its
  parent and a lexical top-k (`pf.freshness_top_k`). `same_surface` rejects a declared
  isomorph/same-target; a declared near/far judged isomorph of the parent is relabelled.
  A missing verdict blocks.
- **Difficulty** (`difficulty_source = "solver_panel"`): the per-variant offset on the
  2PL difficulty scale, `d = d_parent + (logit s_parent − logit s_variant) / (2 ·
  mastery.irt.difficulty_prior_scale)`, smoothed rates, clipped to [0.02, 0.98]. When no
  panel solve matches the parent's reference (a prose reference, found in the real run),
  the reference rate is the mean of the verified siblings instead. The basis is recorded
  in `panel_json`. No contract has a difficulty field; LLM self-labels are never asked for.
- **Selection.** MMR over a lexical kernel (number-masked word and bigram Jaccard) against
  the LO's items and each other, weighted by panel agreement; Vendi score and
  leave-one-out contributions. The ensemble judge picks; generator and source-anchored
  families take the MMR order.

### Publication

`ops/pf_publish.py`, modelled on the probe re-mint path: the item copies the parent's
measurement contract (LO, mode, facets and weights, rubric verbatim, trace contract for
isomorphs), stamps `evidence_fingerprint.source_family` with the parent's surface group
(as rung variants do), carries `family_id` and the final `variant_relation`, the
verified reference as `expected_answer`, and gets **its own practice card**
(`resolve_legacy_item`), an append-only `activity_family_membership_events` row, a fresh
scheduling row and a queue bump. A `pf_publish` verdict precedes the write; publication
is idempotent after a crash. Gated by `pf.generation_enabled` and capped at
`pf.max_published_per_day` per UTC day; capped selections stay `selected` and
`learnloop pf publish` publishes them on a later day without model calls. Unverified
candidates are refused by the function, the selection step and a SQL `CHECK`.

### Jobs, spend, receipts, ledger

- **078 reuse.** Jobs are `surface_mint_requests` rows (`generator_version = pf_<path>_v1`,
  keyed on the parent's practice card version and surface, angle = family/path/relation/
  round/tier/count): idempotent enqueue, fenced lease (`claim_surface_mint_request`),
  lifecycle `admitted`/`rejected`/`failed`, release to `pending` on cancellation. The
  generic rotation claim now skips `pf_*` jobs so a rotation worker can never drain them.
- **Spend** (`ops/pf_calls.py`): every role resolves to pinned clients (no availability
  fallback after the dry run). Each physical request is admitted under shared call,
  candidate, pair and retry caps and a per-billing-class budget: metered routes need an
  owner price and keep the one-request bound; Codex routes are subscription
  (`estimated_only`, token/dollar caps recorded, not enforced). Every validated result is
  checkpointed in `model_work_checkpoints` by a content key of prompt, schema, settings
  and output bound: an interrupted run resumes without repaying (tested). Receipts carry
  role, prompt version, input hash, model and planned tokens in `budget_json`.
  `pf_candidates.cost_json` holds each candidate's attributed calls, tokens and cost.
- **Ledger**: `answer_equivalence` (LLM agreement and the sandbox confirmation, per
  solve; `degenerate_check` when an LLM-written check accepts a wrong answer),
  `reference_verified`, `generator_tests`, `isomorph` (structure, freshness and exact-key
  verdicts), `closed_book`, `provenance`, `selection`, `pf_publish`, `pilot_rating`,
  `valid_alternative_grade`, and the owner `family_decision` for `--seed-item`.

### Persistence

Migration **169** (`169_pf_generation.sql`): `pf_candidates` (WORKFLOW),
`item_skeletons` (WORKFLOW; paid skeletons keyed by the item text's content hash, so a
candidate's skeleton serves the published item), `item_fingerprints` (DERIVED; one
replayer `item_fingerprints`, family members only). Table roles and the replayer
registry updated; head fixture `fixtures/migration_head_169` (rollback mode); DB and
config references regenerated and validated. `PracticeItem.difficulty_source` gains
`solver_panel`. Recipe **`item/skeleton`** added to `vault/embedding_recipes.py` (reads
persisted skeletons for each item's current text, like Phase 5b's dossier recipes).

### The shared `learnloop embeddings compare` harness (for Slice 2 T6 and T1)

`ops/embedding_compare.py`; CLI `learnloop embeddings compare --suite NAME`.

```text
CompareRequest(suite, output_dir, benchmark_dir=None, models=(), dims=(), views=(),
               family_ids=(), target_recall=0.95, max_cases=None, alternatives=2,
               max_items=20, dry_run=False)
run_compare(vault, *, request, caps, price_per_million=None,
            embedding_price_per_million=None, cancelled=None,
            clients=None, embedding_clients=None) -> report dict
SUITES: dict[str, CompareSuite]   # register a new suite here
class CompareSuite(Protocol):
    name: str; description: str
    def load(self, vault, request) -> data          # validate inputs; manifest.json
    def plan(self, vault, data, request) -> dict     # {"roles": {role: {calls, tokens, pairs}},
                                                     #  "embedding": {model: {calls, tokens, texts}}}
    def run(self, data, request, ctx: CompareContext) -> dict   # aggregate-only body
CompareContext: .caller (PFCaller: spend, receipts, checkpoints, .ledger(...)),
                .role(name) -> pinned clients, .vectors(model, texts, dims, task_prefix)
                (embeds only uncached texts; float32 unit vectors cached under
                <output>/cache, never in the vault), .price_for(model)
Metrics: roc_auc, blocking_cutoff(scores, labels, target_recall), binary_metrics,
         centered_cosines(pairs, dims)   # mean-centered, MRL-truncated, as retrieval scores
```

Benchmarks live under gitignored `fixtures-local/benchmarks/<name>/` with
`manifest.json` (`{"name", "sources": [{"name", "version", "licence", ...}]}`, refused
without all three) and, for pair suites, `pairs.jsonl` rows
`{"id", "label": "positive"|"negative", "category", "domain", "left": {"stem", "answer"?,
"skeleton"?}, "right": {...}}`. Reports are content-named JSON + Markdown files in the
output directory; dry runs construct no client and write nothing.

- **`b2`**: views `stem`, `skeleton` (embedded per model and per `--dims`, mean-centered),
  `fingerprint` (shared symbolic keys) and `judge` (the production freshness judge,
  verdicts ledgered as `isomorph` on `b2_case` subjects). It reports AUC overall and per
  positive category, and the recall-oriented **blocking cutoff per (model_id,
  record_kind, view, dims)** at `--target-recall`, with the judge load it implies (R4).
  The cutoffs are reported, not wired: the freshness gate uses exhaustive LO judging or
  lexical top-k until the owner reviews B2.
- **`valid_alternative`**: for family items (`--family`), frontier-written canonical and
  valid-alternative traces (`pf_generator`), kept only when the verifier and the sandboxed
  sympy check confirm the final answer; the suite is written to
  `valid_alternative_suite.json`; each trace is graded by the blind grader (`grading`
  route, isolated turn, `blind_grading_context` with the synthetic trace as the only
  answer text; no attempt is written). Reports valid-alternative false rejection (below
  full credit, below half) by grader model and family; grades are ledgered as
  `valid_alternative_grade`.

### Pilot and scaling check (`learnloop eval`)

- **`learnloop eval pf-pilot --round R [--judge]`**: per arm (single-shot, generator,
  ensemble, source-anchored) survival per filter, verified rate, panel disagreement per
  family, cost and cost per published item, usage signals per item source (attempts,
  retirements by reason, affect taps), splits by proposer model; with `--judge` the blind
  two-pass pairwise comparison (`pf_selection_judge`) of up to 15 survivors per
  quantitative arm against 15 single-shot items, with two-pass agreement. It recommends a
  default path only from both arms and the blind comparison.
- **`learnloop eval pf-scaling --round R [--judge]`** over a round generated with
  `--tier cheap` and `--tier frontier` (`[pf.scaling] cheap/frontier` route lists; the
  first profile serves single-route roles, all of them propose). Verifiers (panel,
  reference verifier) stay fixed. Per tier: survival, verified-reference pass rate, judge
  agreement with verifiers (structure judge vs program invariance, freshness judge on
  symbolic suspects) and with undo/contest signals, cost, and a blind pairwise rating of
  up to 10 survivors per tier. Per component: `rises_with_tier`, `falls_with_tier`,
  `no_clear_difference` or `insufficient_data` from Wilson intervals.

---

## Slice 2 §13 PF gates

| Gate | Status | Evidence |
|---|---|---|
| Replay never executes a generator | Holds | `test_rebuild_recomputes_fingerprints_without_any_model_or_generator` (sandbox, routing and transport patched to raise; two rebuilds identical) |
| Vaults with no families rebuild byte-identically | Holds | `item_fingerprints` holds family members only; `test_a_vault_without_families_has_no_fingerprint_rows`; existing shadow/rebuild-equivalence suites pass |
| `family_memory_state` / family decisions traceable and undoable | Phase 3 (unchanged); `--seed-item` families are owner-authored with an owner `family_decision` | `test_owner_seed_item_creates_an_authored_family_first` |
| No learner answer reaches `BlindGradingContext` via PF's grading support | Holds for the regression-suite harness | `test_valid_alternative_suite_is_cas_checked_and_graded_learner_blind` |
| An item with an `unverified` reference is never published | Holds (function, selection, SQL `CHECK`) | `test_an_unverified_candidate_cannot_be_published`, panel-disagreement and provenance tests |
| Ensemble: panel disagrees with proposer → never published | Holds | `test_panel_disagreement_is_never_published_even_by_an_eager_judge` |
| Selection judge never offered an unverified candidate (fake judge that would pick it) | Holds | same test: the eager judge selects everything offered plus an unknown ref |
| Declared ensemble isomorph without a passing structure check never published as isomorph | Holds | `test_declared_isomorph_without_a_passing_structure_check_is_never_published_as_isomorph` |
| `pf_proposers` with fewer than two distinct models refused | Holds | `test_fewer_than_two_distinct_proposer_models_is_refused` (dry run and run) |
| Sandbox: bubblewrap, fails closed; network, vault reads, writes outside scratch denied | Holds | `tests/test_pf_sandbox.py` (real bubblewrap; root remounted read-only) and `test_generation_fails_closed_without_bubblewrap_before_any_paid_call` |
| Unfamilied items serialize byte-identically; `practice_item_hash` unchanged | Holds | `test_published_items_keep_scheduling_hashes_and_unfamilied_items_unchanged` |
| Publish cap holds per day | Holds | `test_publish_cap_holds_per_utc_day_and_the_backlog_publishes_next_day`; the fixtures-local E2E |
| Every verdict in `judgment_ledger` with model, prompt version, input hash; rebuild re-runs no judge | Holds | `test_every_pf_verdict_is_ledgered_with_model_prompt_and_input`; rebuild test above |
| Every PF report splits by model id | Holds | `results_by_model` (generate), `by_proposer_model` and judge `by_model` (reports), cutoffs keyed by `model_id` (B2) |
| Calibrator-free blocking keyed by model id, re-derived on model change | B2 reports cutoffs per `model_id`; nothing merges, rejects or skips a judge by score | `test_b2_reports_views_and_recall_oriented_cutoffs_and_caches_vectors` |

---

## Deviations and decisions

1. **Source-anchored path built** (the spec's §5.3 list includes it). It is minimal:
   answer-first generation, quote-verified spans, provenance relabel, closed-book filter.
   Executable what-if perturbations and figure items are not built; figure-only is
   recorded `not_applicable`. Source-anchored items get no panel difficulty
   (`difficulty_source` unset): the spec's panel covers generator, ensemble and isomorph
   variants.
2. **Freshness blocking without embeddings.** B2 must set the embedding blocking cutoffs
   before they gate anything (R4: never hand-set). Until the owner reviews a B2 report,
   the judge sees every same-LO item for LOs up to `families.max_exhaustive_items`, and
   suspects + parent + lexical top-k above that. Embedding diversity in selection waits
   for the same reason; the selection basis is recorded (`lexical_jaccard_v1`).
3. **Membership is recorded for published items.** Phase 3's membership events are
   regrouping events; a published item is born in its family, and an `add` event under
   `proposal_id = pfpub_<candidate>` keeps `current_memberships` complete.
4. **Rubric verbatim.** A published item copies the parent's rubric unchanged (the 078
   surface-variant rule); the structure judge must confirm it applies, else the candidate
   is rejected. Hints are not copied (they are surface-specific).
5. **Mint jobs share `surface_mint_requests`.** The table's generic rotation claim now
   excludes `generator_version LIKE 'pf\_%'` (one shared-code change in
   `db/repositories.py`); PF claims a named request. A run killed with SIGKILL leaves its
   job leased for an hour (`LEASE_SECONDS`); a cancelled run releases it to `pending`.
   A round whose job ended `admitted`/`rejected` is not rerun; start a new `--round`.
6. **List routes.** `ai.routing.pf_proposers` is a list; `pf_solver_panel` accepts one
   profile or a list (`provider_list_for_task`). The Settings payload shows a list as one
   comma-joined string so the frontend type (`Record<string, string | null>`) holds; the
   frontend is unchanged. `LEARNLOOP_AI_PROVIDER` collapses a list route to one provider,
   which the two-model rule then refuses.
7. **Template line budget.** `tests/test_config_refactor.py` allowed 80 template lines;
   the required `[pf] generation_enabled = false` needs 3 more, so the budget is now 84
   with a comment. The `mvp-0.9` defaults fingerprint is updated with a comment (no
   algorithm successor: new disabled configuration only).
8. **Sandbox hardening beyond `_sandboxed_command`.** Reused unchanged, plus
   `--remount-ro /`, an explicit minimal environment (not animation's `_render_env`),
   rlimits (CPU, address space, file size, core) and `python -I -B`. The animation
   module is untouched.
9. **Seeding.** `--seed-item ITEM` creates an owner-authored single-item family (the owner
   names the item), only after routes resolve and the plan is admitted.
10. **Path proposal at family setup** (an LLM proposing `generator` vs `ensemble`) is not
    built: `auto` uses the family's `source_kind`, else `pf.default_path` (`ensemble`)
    until the pilot sets the default.
11. **Prompt changes from the real runs** (all prompt versions bumped):
    `pf-generator-program-v6` and `pf-answer-equivalence-v2` carry source templates (exact
    rationals, tuple-safe comparison, constant checkpoint names); LLM-written equivalence
    checks now face negative controls; the retry feedback names the failing answer or
    checkpoint list.

---

## Verification

Final tree, with `LEARNLOOP_CONFIG_DIR` isolated by `conftest.py`:

| Check | Result |
|---|---|
| `uv sync --extra dev`, then `uv pip install pypdfium2` | OK |
| `uv run lint-imports --no-cache` | **10 contracts kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **7,131 passed**, 0 failed, 14 existing warnings (fork and SQLite datetime-adapter deprecations); 157 s |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **66 passed**, 7,065 deselected; 41 s |
| The six PF test modules with `--durable-sqlite` | **55 passed**; 175 s |
| DB reference generator and validator | Schema head **169**, **269** table notes, **561** config leaves in 31 sections, **0 errors** |
| Head fixture `migration_head_169` | DELETE journal mode; `integrity_check` ok; no FK violations; no `sqlite_sequence`; built from the tracked 168 database through the backup API |
| `git diff --check` | Clean |
| Frontend | Unchanged (no `apps/` edits), so `npm` checks were not required |

The PF tests (55) are `test_pf_sandbox.py` (9), `test_pf_generation.py` (25),
`test_item_fingerprints.py` (5), `test_embedding_compare.py` (6), `test_pf_reports.py`
(5) and `test_pf_cli.py` (5); sandbox tests run real bubblewrap. Updated existing tests:
the Phase 1 recipe tests (`item/skeleton`), the SQL-owner registry, the stale-row
rebuild oracle, the template line budget, the defaults fingerprint and the CLI snapshot
(only `<root>`, `embeddings`, `eval` and the new commands changed).

**Failures met during development, all fixed before the final run:** the template line
budget and defaults fingerprint; two new function-local cross-domain imports (moved to
module level); the stale-row rebuild oracle and Phase 1 recipe assertions; an
`INSERT OR IGNORE` that silently dropped candidate rows on a CHECK violation (now
`ON CONFLICT(id) DO NOTHING`, so constraint errors surface); the zsh `path` variable
clobbering `PATH` in a shell loop (operator error, noted in the commands below).

### Fake-model end-to-end on a fixtures-local copy

`fixtures/conic-sections` copied with `copy_tree_with_databases` to
`fixtures-local/pf5a-e2e` (config dir isolated to `fixtures-local/pf5a-config`), `[pf]
generation_enabled = true`, `max_published_per_day = 3`; fakes from `tests/pf_fakes.py`.

| Step | Result |
|---|---|
| Dry run, generator path, `--seed-item pi_vertex_negative_x_squared_minus_2x_plus_1` | 52 calls, 182,769 tokens, $0.18 at the $1/M test bound; no writes |
| Generator path | Program written and tested; 6 CAS-verified draws; 2 published (`isomorph`, `solver_panel`) |
| Ensemble path, next round | 6 verified; selection judge picked 2; **1 published, 1 capped** (3/day) |
| `pf publish` the same day | 0 published (cap); the capped one stays `selected` |
| `pf status` | `publish_slots_today: 0`; vault validation issues: 0 |
| Shadow rebuild of the copy | Live hash unchanged; learner-state deltas **identical** to a shadow rebuild of a pristine migrated copy (the fixture's stale mvp-0.5 projections), so publication adds none |
| Source fixture | Hash unchanged |

### Real-model runs (minimal; on `fixtures-local/pf5a-real`, a backup-API copy of `fixtures/conic-sections`)

Dry runs first, every run capped (`--max-calls 60–80`, `--max-cost-usd 0.20–0.40` at an
owner bound of $3/M tokens). Totals, provider-reported: **54 calls, 66,605 tokens,
$0.0283**.

| Run | Routes | Calls | Tokens | Cost | Outcome |
|---|---|---|---|---|---|
| Generator, Codex routes | `codex_sdk` | 0 | 0 | $0 | `unavailable`: no Codex checkout configured for the CLI on this machine; failed closed before any request |
| Generator ×3 (program `deepseek/deepseek-chat`) | OpenRouter | 10 | 18,103 | $0.0083 | Program field held the protocol name (v1), then float answers its own check rejected; nothing published |
| Generator ×3 (program `openai/gpt-4o-mini`) | OpenRouter | 12 | 23,818 | $0.0064 | Exposed a template bug (Python tuples from `sympify`), fixed; then numbered checkpoint names, then hard-coded parameters; nothing published |
| Generator (program `openai/gpt-5-mini`; panel deepseek + 4o-mini) | OpenRouter | 11 | 10,694 | $0.0094 | Program passed its tests first time; 2 CAS-verified draws; 1 panel outlier rejected; **1 published** |
| Ensemble (proposers deepseek + 4o-mini; 1 solve/model) | OpenRouter | 9 | 6,347 | $0.0021 | Both unverified (not 2 agreeing solves); one upstream 429 retried within the cap |
| Ensemble (2 solves/model; proposals reused from checkpoints) | OpenRouter | 12 | 7,643 | $0.0022 | 1 verified, **1 published** (`isomorph`); the other unverified |

The copies stay in the gitignored `fixtures-local/` (`pf5a-e2e`, `pf5a-baseline`,
`pf5a-real`) for inspection.

The runs validated the OpenRouter structured transport against the skeleton, program,
proposer, panel, equivalence, structure, freshness and selection contracts (the
source-anchored, closed-book, single-shot, pairwise and valid-alternative contracts ran
against fakes only), the
sandbox on model-written code, checkpoint reuse across runs and the fail-closed paths.
They also produced the fixes listed in deviation 11.

---

## Owner-run commands

Everything below is opt-in and runs on a backup-API copy first. Supply keys as usual
(the app loads them itself). Codex routes need the Codex checkout configured for the
CLI (`LEARNLOOP_CODEX_CHECKOUT_PATH`), as the desktop app has it.

```bash
SOURCE=/absolute/path/you/choose          # your vault
COPY="$PWD/fixtures-local/pf-owner-copy"
uv run python - "$SOURCE" "$COPY" <<'PY'
from pathlib import Path
import sys
from learnloop.db.copies import copy_tree_with_databases
copy_tree_with_databases(Path(sys.argv[1]), Path(sys.argv[2]))
PY
```

In the copy's `learnloop.toml`: set `generation_enabled = true` under `[pf]`; add PF routes
to the existing `[ai.routing]`, for example `pf_proposers = ["codex", "or_b"]` (two
distinct model slugs), `pf_solver_panel = ["codex_low", "or_b"]`, `pf_generator`,
`pf_reference_verifier`, `pf_isomorph_judge`, `pf_selection_judge`; for the scaling
check add `[pf.scaling]` with `cheap = [...]` and `frontier = [...]` (each with two
distinct models if you want the ensemble arm per tier). For B2, enable embeddings on the
copy as in Phase 1 (`routing.embedding = "openrouter_embedding"`, the profile, and
`[embedding] enabled = true`).

**B2** (benchmark files: `fixtures-local/benchmarks/b2/manifest.json` naming GSM-Symbolic,
MATH-Perturb and MELD with version and licence, and `pairs.jsonl` in the format above):

```bash
uv run learnloop embeddings compare --vault "$COPY" --suite b2 \
  --benchmark fixtures-local/benchmarks/b2 --output fixtures-local/reports/b2 \
  --model qwen/qwen3-embedding-8b --dims 256 --dims 1024 --dims 4096 \
  --price-per-million 3 --max-calls 3000 --max-cost-usd 3 --dry-run --json
# then the same without --dry-run
```

**Pilot** (one chapter's quantitative families, all three arms on one round; then one
paper's families on the source-anchored path):

```bash
for ARM in single_shot generator ensemble; do
  uv run learnloop pf generate --vault "$COPY" --path $ARM --round pilot-1 \
    --family FAMILY_ID --count 6 --price-per-million 3 --max-cost-usd 2 --dry-run --json
done
# then each without --dry-run; for the paper:
uv run learnloop pf generate --vault "$COPY" --path source_anchored --round pilot-1 \
  --family PAPER_FAMILY_ID --price-per-million 3 --max-cost-usd 1 --dry-run --json
uv run learnloop eval pf-pilot --vault "$COPY" --round pilot-1 --judge \
  --price-per-million 3 --dry-run --json
uv run learnloop eval pf-pilot --vault "$COPY" --round pilot-1 --judge \
  --price-per-million 3 --output fixtures-local/reports/pf --json
```

(Avoid naming a zsh loop variable `path`: zsh ties it to `PATH`.)

**Scaling check** (identical inputs at both tiers, one round):

```bash
for TIER in cheap frontier; do
  uv run learnloop pf generate --vault "$COPY" --round scale-1 --tier $TIER \
    --family FAMILY_ID --path ensemble --no-publish --price-per-million 3 --dry-run --json
  uv run learnloop pf generate --vault "$COPY" --round scale-1 --tier $TIER \
    --family FAMILY_ID --path generator --no-publish --price-per-million 3 --dry-run --json
done
# then each without --dry-run, then:
uv run learnloop eval pf-scaling --vault "$COPY" --round scale-1 --judge \
  --price-per-million 3 --dry-run --json
uv run learnloop eval pf-scaling --vault "$COPY" --round scale-1 --judge \
  --price-per-million 3 --output fixtures-local/reports/pf --json
```

**Valid-alternative regression suite** (on every grader prompt or model change):

```bash
uv run learnloop embeddings compare --vault "$COPY" --suite valid_alternative \
  --family FAMILY_ID --max-items 20 --output fixtures-local/reports/va \
  --price-per-million 3 --dry-run --json
```

**Live use** (yours to run, after reviewing the copy): the same `pf generate` on the
real vault with `generation_enabled = true`; `learnloop pf status`; `learnloop pf
publish` the next day for capped selections. Retire a published item you dislike as
any item (it keeps its evidence and stops being served).

---

## Files touched

New: `migrations/169_pf_generation.sql`; `src/learnloop/content/authoring/pf_sandbox.py`,
`pf_contracts.py`; `src/learnloop/db/stores/pf.py`; `src/learnloop/substrate/item_fingerprints.py`;
`src/learnloop/ops/pf_calls.py`, `pf_generation.py`, `pf_selection.py`, `pf_publish.py`,
`pf_reports.py`, `embedding_compare.py`; `src/learnloop/cli/pf.py`; tests
`tests/pf_fakes.py`, `test_pf_sandbox.py`, `test_pf_generation.py`, `test_item_fingerprints.py`,
`test_embedding_compare.py`, `test_pf_reports.py`, `test_pf_cli.py`.

Changed: `ai/routing.py`, `cli/__init__.py`, `cli/embeddings.py`, `cli/evaluation.py`,
`config/schema.py`, `config/template.py`, `db/repositories.py`, `db/table_roles.py`,
`params/parameter_registry.py`, `substrate/rebuild_orchestrator.py`,
`vault/embedding_recipes.py`, `vault/hashes.py`, `vault/models.py`,
`learnloop_sidecar/handlers/settings.py`; tests `test_architecture.py` (SQL owner),
`test_config_refactor.py` (template budget), `test_embedding_backfill.py`
(`item/skeleton`), `test_rebuild_orchestrator.py` (stale row), the three head-fixture
paths, `cli_help_snapshot.json`; `fixtures/migration_head_168` → `migration_head_169`;
the two reference scripts and the regenerated `Reference/` notes. No working vault
(`linear_algebra`, `probability`, `arxiv_v2`) was opened or changed.

## Open questions

1. **Codex for the CLI.** The CLI could not reach Codex on this machine (no checkout path
   in the global settings). Should the CLI share the desktop app's Codex configuration,
   or do you configure `LEARNLOOP_CODEX_CHECKOUT_PATH`?
2. **Panel composition (P10 defaults accepted).** With cheap OpenRouter models, one solve
   per model left good candidates unverified; two to three solves per model across two
   or three models (the default) worked. Which models form your panel tiers?
3. **Program writer strength.** `deepseek-chat` and `gpt-4o-mini` could not write a
   passing generator program in three tries each; `gpt-5-mini` passed first time. Route
   `pf_generator` to a frontier-tier model?
4. **B2 data.** The harness needs the GSM-Symbolic, MATH-Perturb and MELD pairs converted
   to `pairs.jsonl`; no converter is built because the raw formats were not available
   here. Once B2 runs, wire its cutoffs into freshness blocking (and embedding
   diversity) in a follow-up?
5. **Difficulty uncertainty.** The field's outcome view treats `solver_panel` like an
   authored difficulty (variance 0, as for `author`); `llm_estimate` gets variance 1.
   Should panel difficulty carry its own variance?
6. **Single-item seeding.** Is an owner `--seed-item` family the right way to start PF on
   an item no Phase 3 family covers, or should the pilot wait for `families propose`?
7. **Merge with Phase 5b.** Expect small conflicts in `vault/embedding_recipes.py`, the
   recipe tests in `test_embedding_backfill.py`, the template budget and fingerprint,
   the head fixture and migration number (both claim 169), and the references.
