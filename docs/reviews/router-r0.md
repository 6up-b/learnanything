# Router R0: the model clients and the `llm_probability` V1–V3 harness arms

Branch `router/r0`, worktree `learnanything-router-r0`, base `974c5647` (main after
the Phase 2/3 integration merged). Specs: `spec_action_router_v1.md` §0, §6, §11
(R0 row); `spec_learner_field_v1.md` §7.2, G11, D8, D9. Owner decisions of
2026-10-12 in force (defaults accepted, Codex unrestrained on the subscription,
the Decider is `perplexity/pplx-decider-v1.1-27b` on OpenRouter, frictionless
defaults).

## Plan (written before coding)

**Files to add:**
- `src/learnloop/ai/decisions.py`: the provider-neutral Decider contract. Typed
  question classes (`NoulQuestion`, `ChoiceQuestion`, `ScoreQuestion`), typed
  answers, `DecisionResult`, the `DecisionClient` protocol, request building and
  strict response parsing (unknown fields refused, fails closed).
- `src/learnloop/ai/providers/decider.py`: the `decider` transport over HTTP
  (injectable transport seam, one physical request per call, no hidden
  retries), for OpenRouter (default) or Perplexity's direct API.
- `src/learnloop/field/probability_arms.py`: the six `llm_probability` arms
  (V1–V3 × decider/llm), each raw and recalibrated; the store-free cached arm.
- `src/learnloop/field/probability_states.py`: the V1/V2/V3 `state` renderers,
  past-only by construction, with the router card's token budget for V3.
- `src/learnloop/cli/probability_arms.py`: preparation (dry-run, caps, cache,
  receipts, judgments) and the readiness command.
- Tests: decider client against a fake endpoint, routing and readiness, the arms,
  the renderers' leakage rules, the CLI, the migration.

**Files to change:** `config/schema.py` (provider type, profiles from code
defaults, routes), `config/template.py` (defaults fingerprint), `ai/routing.py`,
`ai/runtime.py`, `ai/client.py`, `ai/execution.py` (receipt labels),
`db/stores/model_calls.py`, `db/stores/judgments.py`, `field/evaluation.py` (an
additive pairwise-comparison option), `cli/field.py` and `cli/evaluation.py`
(flags), the sidecar settings handler and context, and the Settings screen (a
read-only "Decision models" disclosure section).

**Migration:** one, the next free number (169), expected to be renumbered at
merge:
- `model_call_receipts` gains `judge` (`decider` | `llm`), `question_set_version`
  and `state_hash`;
- `judgment_ledger` is rebuilt (rows and ids preserved, 164 precedent) so that
  `judge` admits `decider`, with the same provenance rule as `llm`.
No new tables, so no table-role or replayer changes. Head fixture renamed to
`migration_head_169`.

**Algorithm successors and kill switches:** none. Nothing served changes. The
arms are offline, never active (G11), off by default (`field.enabled` and
`field.llm_probability_enabled`, D8). The routes have no live consumer until R2.

**Spend caps and model routes:**
- `ai.routing.llm_probability_decider` and `ai.routing.router_decider`: unset
  resolves to the code-default profile `openrouter_decider`; they never fall back
  and `LEARNLOOP_AI_PROVIDER` doesn't override them.
- `ai.routing.llm_probability_llm` and `ai.routing.router_llm`: unset falls back
  to the active provider; Codex runs on the subscription with estimated cost
  (Slice A plan §5 rule 6).
- Preparation uses the Phase 1 spend framework: whole-plan admission, one
  reservation per physical request, `--dry-run` with the estimate, a separate
  budget per judge (their billing differs).

**`judgment_ledger` writes:** one row per returned verdict (`task =
"llm_probability"`, `judge = "decider"` or `"llm"`), including invalid ones.

**Tests:** listed above; all use fakes. One minimal live Decider call is made
by hand to confirm the endpoint (owner-authorized), recorded below.

---

## 1. First task: how OpenRouter serves the Decider (confirmed 2026-10-12)

**Sources read:** OpenRouter's documentation index (`openrouter.ai/docs/llms.txt`),
its API reference for "Submit a Decisions request"
(`docs/api/api-reference/alphadecisions/submit-a-decisions-request.md`, OpenAPI
`post /api/alpha/decisions`), the "System One" reference and the TypeSafe SDK
guide, OpenRouter's public model endpoint listing, and Perplexity's Decisions API
quickstart (`docs.perplexity.ai/docs/decisions/quickstart`) as the reference shape.

| | OpenRouter (owner's route, pinned) | Perplexity direct (reference, fallback) |
|---|---|---|
| Endpoint | `POST https://openrouter.ai/api/alpha/decisions`. The operation overrides the server to `https://openrouter.ai`, so with the spec's base URL `https://openrouter.ai/api` the path is `/alpha/decisions`. OpenRouter also has `POST /api/v1/systemone` (TypeSafe-compatible, same schemas) | `POST https://api.perplexity.ai/v1/decisions` |
| Auth | `Authorization: Bearer $OPENROUTER_API_KEY` | `Authorization: Bearer $PERPLEXITY_API_KEY` |
| Model | `perplexity/pplx-decider-v1.1-27b`. The public listing (`/api/v1/models/perplexity/pplx-decider-v1.1-27b/endpoints`) shows modality `text+image->decisions`, one endpoint, provider **Perplexity**, dated slug `pplx-decider-v1.1-27b-20261006`, context 262,144, $0.00000002 per prompt token, $0 completion. It is absent from the chat model list, as the spec noted | `pplx-decider-v1.1-27b` |
| Request | `model`, `state` (string, object or array), `questions` (1–128, keyed by name). Each question has `type` and `instructions` (OpenRouter's schema requires `instructions` for every type); `noul` may add `criteria: {true, false}` (both, or neither); `choice` needs `criteria` mapping 1–255 options to descriptions (or null); `score` needs `criteria` as an ordered list of up to 10 levels. Optional OpenRouter-only fields: `provider`, `session_id`, `trace`, `user` | Same `model`/`state`/`questions`; any other top-level field is a 400 |
| Response | `model` (the dated slug that answered), `answers` keyed by question name, `usage` (`input_tokens`, `output_tokens`, `cost`), `id` (`gen-dec-…`), `provider` | `model` (echoed), `answers`, `usage` (`input_tokens`, `output_tokens`) |
| Answers | `noul`: `{type, noul}` = P(yes). `choice`: `{type, choice, probabilities, confidence}`. `score`: `{type, score, probabilities, confidence, legend}` (probabilities and legend keyed by level index strings) | Same |

**How the client uses it.** The client sends only `model`, `state` and
`questions`, built from the typed classes, so the same body is valid on both
dialects and can never carry an unknown field. It does not set OpenRouter's
`provider.data_collection = "deny"` (router spec §6.2): the listing doesn't show
that Perplexity's endpoint satisfies it, and a request that requires it fails if
none does. Parsing accepts exactly the documented top-level fields (`model`,
`answers`, `usage`, `id`, `provider`) and each answer type's documented fields,
requires an answer for every asked question and nothing else, and checks that
probabilities are finite, cover the asked options and sum to about 1. Anything
else raises `DecisionResponseInvalid` (fail closed), with usage already on the
receipt.

**The one live call** (owner-authorized, on the backup copy
`fixtures-local/r0-linear_algebra`):
`uv run learnloop eval judges --vault fixtures-local/r0-linear_algebra --live-decider --json`

| Field | Value |
|---|---|
| Time | 2026-10-12T15:55:55Z |
| Endpoint | `https://openrouter.ai/api/alpha/decisions`, route `llm_probability_decider` → code-default profile `openrouter_decider` (the copy's config predates it) |
| Request | state "LearnLoop readiness check. This text contains no learner data."; three questions, one of each type |
| Response | answered by `Perplexity`, model `perplexity/pplx-decider-v1.1-27b-20261006`, id `gen-dec-1791820556-aV73BjxQZVgd73rc5SCD`; top-level keys exactly `answers, id, model, provider, usage`; noul 0.92, choice `readiness_check` (0.99993), score 0.92 on two levels. Strict parsing passed |
| Usage | 294 input tokens, 3 output tokens |
| Cost | **$0.00000588** (OpenRouter's `usage.cost`; equals 294 × $0.02/M) |
| Caps | 1 call, 4,000 tokens, $0.001 |
| Receipt | `model_call_receipts` on the copy, `owner_kind = judge_readiness`, `judge = decider`, `question_set_version = judge_readiness_v1`, resolved model and cost recorded |

Two free, unauthenticated GETs of OpenRouter's public listing (`--probe`) were
also made. **Total paid spend for this stage: $0.00000588.** No paid call ran
the harness itself, and no Codex turn was made (the owner's note allowed one
minimal live call; the harness runs are the owner's).

**Fallback (B5) not needed.** OpenRouter serves the Decider's typed-question
interface, so the Perplexity direct dialect is built and tested (fake endpoint)
but not used; switching is one profile (`api = "perplexity"`, `PERPLEXITY_API_KEY`).

## 2. What was built

**The Decider client** (`ai/decisions.py`, `ai/providers/decider.py`).
- `DecisionClient.decide(state, questions, *, purpose) -> DecisionResult`, with
  `NoulQuestion`, `ChoiceQuestion` and `ScoreQuestion` and typed answers
  (`NoulAnswer.p_yes`, `ChoiceAnswer`, `ScoreAnswer`). Untyped questions are
  refused (`TypeError`), so no unknown field can reach the wire.
- One `decide` is one physical request over an injectable HTTP seam: no SDK,
  no retries, no splitting. A 4xx/5xx raises `DecisionRequestFailed` with the
  status and `Retry-After`; the error text is the provider's error type and
  message only. Input over the profile's limit is refused before sending.
- Each call is a `model_call` whose receipt records the request body (as for
  other model calls), the questions, usage, OpenRouter's cost, the response id
  and the dated model that answered. Usage is recorded before parsing, so a
  malformed paid answer still has an honest receipt.
- `probe_decider_endpoint`: a free GET of OpenRouter's public listing (no key, no
  learner text).

**Config and routes** (`config/schema.py`, `ai/routing.py`, `ai/runtime.py`).
- Provider type `decider` (`DeciderProviderConfig`: `api` = `openrouter` |
  `perplexity`, `api_key_env`, `price_per_million_input` = 0.02,
  `max_input_tokens` = 262,144, attribution headers).
- **Profiles from code defaults (owner-directed, B6):** `openrouter_decider`
  (OpenRouter, `perplexity/pplx-decider-v1.1-27b`, `OPENROUTER_API_KEY`, 30 s)
  and `openrouter_embedding` (the template's embedding profile) are added with
  `setdefault`, so a vault whose `learnloop.toml` predates them still resolves
  routes that name them, and an explicit vault profile stays authoritative.
  `routing.embedding` itself stays an explicit opt-in.
- Routes `router_decider`, `llm_probability_decider` (decider tasks: unset →
  `openrouter_decider`, explicit, no env override, no fallback; a chat profile
  there is refused) and `router_llm`, `llm_probability_llm` (ordinary chat routes:
  unset → active provider). A decider profile can't serve any other task, and an
  embedding profile can't serve a decider task.
- Readiness for a decider profile is key presence only (no network).

**Receipts and verdicts** (migration 169, `ai/execution.py`,
`db/stores/model_calls.py`, `db/stores/judgments.py`).
- `call_labels(judge=…, question_set_version=…, state_hash=…)` labels every call in
  its context; unknown labels and judges other than `decider`/`llm` are refused.
  The store writes label columns only when set, so unlabelled calls still work
  on a database below 169.
- `judgment_ledger.judge` admits `decider`, which needs `judge_model` and
  `prompt_version` like `llm` (API and SQL trigger).

**The six arms** (`field/probability_arms.py`, `field/probability_states.py`,
`field/probability_prep.py`, field spec §7.2).
- Arms `llm_probability/<v1|v2|v3>/<decider|llm>`, each also as `+recal`: twelve
  report entries. They are point predictors (`calibrated_uncertainty = False`),
  not in the predictor registry (so off by default and not in a default run),
  rejected by `validate_active_predictor` (G11), and covered by the
  `field-predictors-are-pure` import contract (no db, ai or evidence imports).
- **States** (identical for both judges; only the question wrapper differs):
  - V1: the item stem, LO title, facet names, capability and the difficulty prior
    exactly as the harness's frozen features carry it (`b`, `a`, source; an
    authored/empirical/calibrated 0–1 difficulty when present). An LLM-estimated
    difficulty is withheld (field §4.3). Never the reference solution, rubric or
    hints.
  - V2: V1 plus the last 25 graded interactions the harness itself observed
    before the cutoff, as (item excerpt, knowledge-component names, result).
  - V3: V1 plus a `LearnerStateCardV1`-style card for the LO, its same-concept LOs
    and one-hop prerequisites: the incumbent's (`mastery_ekf`) P(success) with a
    95% interval and per-LO ability, fitted only on observations before the
    cutoff, status (`tested`/`untested`) and explicit unknowns; recent attempts
    (item excerpt from the verified revision, answer excerpt, blind-grade fields:
    score, frozen-rubric max points and failed criteria, error types,
    first-divergence quotes, assisted, primed, hint totals, tutor-question
    timing); typed prior hypotheses with their source attempt, evidence for and
    against, repairs tried and an as-of status; tutor questions (type, context,
    excerpt, timing). Budget: `router.card_token_budget`'s default, 16K tokens
    (bytes/4); older successes drop first, then older excerpts, then older
    attempts and questions; typed fields never drop, and the card says what was
    omitted. *(Revised by the Codex review fixes, F2, F3 and F5; see
    `router-r0-codex-review.md`.)*
- **No leakage.** The cutoff is the attempt's start as recorded before grading:
  the submission intent's time minus `latency_seconds` minus a 2 s rounding
  margin. `created_at` includes grading time and never sets it. Without an
  intent and a latency the start is unknown and V2/V3 show no history at all
  and say so. Every record must be strictly before the cutoff. Questions linked
  to the predicted attempt are excluded even if timestamped earlier. Hypotheses
  must be written, and their source attempt submitted, before the cutoff.
  *(Revised by the Codex review fixes, F1; the earlier rule used `created_at −
  latency` and a previous-submission fallback, both of which could leak.)*
- **Questions.** Decider: one `noul` question `will_pass` ("Will the learner answer
  this item correctly on this attempt? …", with true/false criteria), question set
  `llm_probability_qs_v1`. LLM: the same question as structured output
  (`p_correct`), prompt `llm_probability_llm_v1`, sent as an **isolated turn**
  (the model sees the prompt only, never the vault or its files; Codex enforces
  it per turn).
- **Preparation** (`prepare_judge`): renders every state from one read-only
  snapshot and closes it first; deduplicates identical states (V1 repeats per
  item); admits the whole remaining plan before any call (a dry run stops here);
  reserves each physical attempt; counts retries (a 429 honours `Retry-After` up
  to 10 s, a 5xx or failed turn retries, a 400 or a malformed paid answer fails
  closed); appends every returned verdict to `judgment_ledger` (invalid ones with
  no score and no cache entry); labels receipts; checkpoints each probability
  atomically outside the vault. Metered LLM routes run under `single_request()`
  with a hidden-retry guard; Codex runs on the subscription with
  `estimated_only` receipts. The cache holds probabilities, digests and model ids,
  never learner text.
- **Replay** (`load_arms`): re-renders the states (no calls), looks each one up,
  and fails closed if any is missing, so a cache from a different past or a
  changed vault is never silently reused. The arm itself keys each prediction by
  the outcome-free features plus the rows the harness has already observed.
- **Recalibration:** one parameter, a logit-intercept shift fit by penalized
  maximum likelihood (prior N(0, 1)) on the arm's own past (raw prediction,
  outcome) pairs, refit after each observation. Raw probabilities are clipped to
  [0.001, 0.999].
- **Report:** `evaluate(..., pairwise=…)` adds report-only paired comparisons on
  common attempts (log-loss improvement, overall and first attempt on a
  never-seen LO, bootstrap CI, whether the CI clears the frozen switching margin):
  V2 vs V1, V3 vs V2 and V3 vs V1 within each judge, and Decider vs LLM within each
  variant, raw and recalibrated. The Markdown report gets a "Paired comparisons"
  table. Nothing recommends or activates.

**CLI.**
- `learnloop eval --section field --probability-arm <all|v1|v2|v3|decider|llm|vN/judge>
  --llm-cache DIR [--prepare-llm] [--dry-run]` with the existing caps flags,
  `--price-per-million` (the LLM route when metered; the Decider uses its listed
  price), `--output-tokens` and a new `--max-retries` (per judge). Without
  `--probability-arm` the Phase 2 numeric `llm_probability` arm behaves exactly as
  before.
- `learnloop eval judges --vault V [--probe] [--live-decider]`: the four routes'
  resolution, readiness, billing, consumer status and privacy disclosure; `--probe`
  is the free listing check; `--live-decider` is the one capped call above.

**Settings** (sidecar + desktop). A read-only "Decision models" section lists each
judgment route with its provider, model, key status and disclosure (who receives
learner text, what and when; for the Decider: OpenRouter forwarding to
Perplexity; for Codex: OpenAI through the ChatGPT subscription). Decision-model
profiles never appear in generation selectors and are refused for generation use
cases. The settings health chip ignores the router routes (no consumer until R2)
and the llm_probability routes unless the harness is switched on.

## 3. Deviations and decisions

- **One migration (169) for labels and the `decider` judge.** Router spec §6.2
  asks receipts to carry `judge`, the question-set version and the state hash, and
  handoff rule 6 sends every model verdict to `judgment_ledger`. Rather than
  label the Decider `llm`, the ledger is rebuilt so `judge = 'decider'` is honest.
  Parallel stages may also take 169; expect renumbering at merge
  (`fixtures/migration_head_169`, `SCHEMA_HEAD` in both reference scripts, the
  three tests).
- **Phase 2's numeric `llm_probability` arm is kept unchanged** (route
  `ai.routing.field_llm_probability`, flags `--llm-cache`/`--prepare-llm` without
  `--probability-arm`). It predates the V1–V3 revision and sends numeric features
  only. Retiring it is an owner call (open question 2).
- **The harness LLM route ignores `LEARNLOOP_AI_PROVIDER`** (as Phase 2's offline
  route does), so the dry run and the paid run can't resolve different models when
  `settings.env` sets it. The live `router_llm` route keeps the ordinary override.
- **V2's "graded interactions" are the rows the harness scores** (the same outcomes
  every arm sees), filtered by the cutoff, with `partial` for fractional rubric
  scores; JevKT's format is binary.
- **V3's neighbourhood** is the LO, its same-concept LOs and one-hop prerequisites
  (the field spec says "prerequisite neighbours"); confusables and dependents are
  out of scope.
- **Outcomes of earlier attempts use the latest surviving grade**, the harness's
  shared limitation ("later regrades retrospectively replace earlier outcomes").
  The cache key includes them, so a regrade invalidates the cached states.
- **Caps apply per judge**, because the two judges bill differently. The dry run
  prints both estimates and their total.
- **The template is unchanged** (it is held to 80 lines); the routes and profiles
  are documented in the generated config reference. The effective-defaults
  fingerprint for `mvp-0.9` is updated with a comment: no scoring, scheduling,
  projection or serving change.
- **Module reference notes** (`_scripts/module_generate.py`) were not regenerated;
  only the DB/config references the gate names.

## 4. Owner-run commands

Run these on a backup-API copy of your vault, never on the vault itself. The
example uses `linear_algebra`; repeat for `probability` and `arxiv_v2`.

1. **Copy, then bring the copy's database to head** (a tracked copy can be behind):

   ```sh
   uv run python -c "from pathlib import Path; from learnloop.db.copies import copy_tree_with_databases; copy_tree_with_databases(Path('fixtures/linear_algebra'), Path('fixtures-local/la-r0'))"
   uv run learnloop doctor --fix-state --vault fixtures-local/la-r0
   ```

2. **Switch the harness on in the copy's `learnloop.toml`** (both are off by
   default, D8). Nothing else is needed for the Decider: its profile and route come
   from code defaults. The LLM judge uses `ai.active_provider` unless you set a
   route, for example `llm_probability_llm = "codex_medium"` under `[ai.routing]`.

   ```toml
   [field]
   enabled = true
   llm_probability_enabled = true
   ```

3. **Readiness** (free; `--probe` reads OpenRouter's public listing;
   `--live-decider --dry-run` prints the paid check's estimate without sending it):

   ```sh
   uv run learnloop eval judges --vault fixtures-local/la-r0 --probe
   ```

4. **Dry run first.** On the worktree's tracked `linear_algebra` copy this gave
   (strict revision policy excludes all 70 graded attempts, so
   `--legacy-fallback current_content` is needed; 53 attempts are scored):

   ```sh
   uv run learnloop eval --vault fixtures-local/la-r0 --section field \
     --legacy-fallback current_content --probability-arm all \
     --llm-cache fixtures-local/llm-cache-la --dry-run \
     --max-candidates 200 --max-calls 200 --max-tokens 2000000 --max-cost-usd 0.05 --json
   ```

   | Judge | Route | Requests | Estimate |
   |---|---|---:|---|
   | Decider | `openrouter_decider`, metered at $0.02/M input | 143 | 340,218 tokens (bytes/3, conservative), **$0.0068** |
   | LLM | `codex` (`gpt-5.6-sol`), subscription | 143 | 1,373,011 tokens (UTF-8 bytes, conservative), cost estimated only |

   Your live vault has more history, so expect larger numbers; read them from the
   dry run. If it says `over_budget`, raise the cap it names. *(After the review
   fixes the same dry run gives 111 requests per judge, Decider $0.0014, and
   `history.start_established = 0` of 53: these July attempts predate submission
   intents, so V2 and V3 carry no history on this copy. Check that count on your
   live vault's dry run before paying; see `router-r0-codex-review.md`.)*

5. **The real run** (same flags, `--prepare-llm` instead of `--dry-run`, plus a
   report directory):

   ```sh
   uv run learnloop eval --vault fixtures-local/la-r0 --section field \
     --legacy-fallback current_content --probability-arm all \
     --llm-cache fixtures-local/llm-cache-la --prepare-llm \
     --max-candidates 200 --max-calls 200 --max-tokens 2000000 --max-cost-usd 0.05 \
     --output fixtures-local/reports/router-r0-la --json
   ```

   It is resumable: an interrupted or partly invalid run pays only for what is
   missing when rerun, including a verdict that committed before the cache file
   was written (recovered from `judgment_ledger`, review F4). Rerunning without `--prepare-llm` replays from the cache
   with zero calls. A metered LLM route (OpenRouter chat) also needs
   `--price-per-million`.

## 5. What each outcome means

Read `report1.pairwise` (and the "Paired comparisons" table). A comparison
"clears" when its 95% bootstrap interval of log-loss improvement lies above the
switching margin fixed before the run (D9). At n=1 only large differences show.

- **V3 clearly beats V2** (overall and on first attempts): your rich history
  (answers, grades, hypotheses, questions) carries information the right/wrong
  window doesn't. That is evidence for the router's card (router spec §4) and for
  reconsidering `idea_hier_llm_prior` (field §11).
- **V2 beats V1 but V3 doesn't beat V2:** the past results help, the text adds
  nothing; the card's value would lie in judgment, not prediction.
- **V1 ≈ V2 ≈ V3:** the models' value is in judgment; the numbers keep coming
  from the explicit arms (`mastery_ekf`, `lo_general`).
- **Decider vs LLM within a variant:** the router's first evidence on which model
  to weight (router spec §10). The raw comparison shows calibration as returned;
  `+recal` shows ranking ability once one intercept is fit on the past.
- **Any arm vs `mastery_ekf`** appears in `report1.comparisons` as for every arm.
  These arms are never recommended or activated (G11); live use of
  `llm_probability` waits for its own trigger (field §11).

## 6. Tests and gate

New test files: `test_decider_client.py` (38), `test_judge_routes.py` (19),
`test_probability_arms.py` (9), `test_probability_prep.py` (13),
`test_probability_cli.py` (6), plus the Settings vitest (4 in the file, 1 new).
Fakes only: a local fake Decisions endpoint (`tests/decider_fakes.py`) that
enforces the documented contract (unknown top-level field → 400, auth, typed
criteria), the fake OpenAI SDK, and in-process Decider/Codex doubles.

Gate run on `ad8d1873` (the code at this review's commit; the review file is
docs only), the full suite and durability lane under
`flock /tmp/learnloop-fullsuite.lock`:

| Check | Result |
|---|---|
| `uv sync --extra dev` and `uv pip install pypdfium2` | OK |
| `uv run lint-imports --no-cache` | 10 contracts kept, 0 broken (the `field-predictors-are-pure` contract now also covers `field.probability_arms`) |
| `uv run pytest -n auto` | **7,161 passed**, 14 existing warnings (Python 3.12 fork and sqlite datetime-adapter deprecations), exit 0 |
| `uv run pytest -m durability` | **66 passed**, 7,095 deselected, exit 0 |
| `npm run typecheck` (apps/learnloop-tauri) | Passed |
| `npm test` (vitest) | **64 passed** in 16 files |
| `db_generate_reference.py` / `db_validate_reference.py` | Regenerated at head 169; validator **0 errors** (schema 169, 266 table notes, 561 config leaves in 31 section notes) |
| `validate_vault.py` | Passed (1,029 notes) |
| Head fixture `migration_head_169` | Migrated to 169, `PRAGMA journal_mode=DELETE`, `foreign_key_check` empty, `integrity_check` ok |

An earlier full run (before the last fix commit) had two failures, both fixed:
the CLI help snapshot needed `eval judges` and the new flags, and the copy
audit needed `tests/test_judge_routes.py` (it copies migration `.sql` files to
build pre-169 schemas).

Manual runs, all on backup-API copies under the worktree's `fixtures-local/`
(never the tracked working vaults): `field data-check`, `eval judges` (with
`--probe`, and the one `--live-decider` call above), the six-arm `--dry-run` on
`fixtures-local/r0-linear_algebra` (section 4), and rendered V1–V3 states
inspected by hand for leakage on that copy.

## 7. Files touched

- **Added:** `migrations/169_decider_judgments_and_receipt_labels.sql`;
  `src/learnloop/ai/decisions.py`, `ai/disclosures.py`, `ai/providers/decider.py`;
  `src/learnloop/field/probability_arms.py`, `probability_states.py`,
  `probability_prep.py`; `src/learnloop/cli/probability_arms.py`;
  `tests/decider_fakes.py`, `test_decider_client.py`, `test_judge_routes.py`,
  `test_probability_arms.py`, `test_probability_prep.py`, `test_probability_cli.py`.
- **Changed:** `src/learnloop/ai/{client,execution,routing,runtime}.py`;
  `src/learnloop/config/{schema,template}.py`;
  `src/learnloop/db/stores/{judgments,model_calls}.py`;
  `src/learnloop/field/evaluation.py`; `src/learnloop/cli/{evaluation,field}.py`;
  `src/learnloop_sidecar/context.py`, `handlers/settings.py`;
  `apps/learnloop-tauri/src/api/dto.ts`, `screens/SettingsScreen.tsx`,
  `SettingsScreen.test.tsx`; `pyproject.toml` (import contract); the three
  head-fixture tests; `tests/cli_help_snapshot.json`; `tests/test_sqlite_file_copies.py`; both reference scripts; the regenerated DB/config reference
  notes.
- **Renamed and upgraded:** `fixtures/migration_head_168` → `migration_head_169`
  (rollback mode, FK-clean, integrity ok).

## 8. Open questions

1. **D6, retention terms.** Learner text for V2/V3 goes to OpenRouter and then
   Perplexity (Decider) and to the LLM route's provider. Check Perplexity's API
   data-retention terms before the real run; the client does not request
   `data_collection = "deny"` because the listing doesn't show that Perplexity's
   endpoint satisfies it.
2. **Retire Phase 2's numeric `llm_probability` arm?** It predates the V1–V3
   revision. Keeping it costs nothing; retiring it would remove
   `ai.routing.field_llm_probability` and its flags.
3. **Default the embedding route?** Profiles now come from code, but
   `ai.routing.embedding` stays an explicit opt-in, so an old vault still needs
   `routing.embedding = "openrouter_embedding"` plus the `[embedding]` switches. A
   code default for the route (gated by `embedding.enabled`) would remove that step.
4. **Phase 2's `--prepare-llm` path never loads `settings.env`** (it reads keys
   only from the shell), so its OpenRouter route fails unless the key is exported;
   it also sends non-isolated turns. Not changed here (out of scope); the V1–V3
   path loads keys the way the app does and isolates every turn.
