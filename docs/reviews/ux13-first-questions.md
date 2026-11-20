# UX-13: a new learner's first document gets its questions

Ledger row UX-13 (`refactor-bug-ledger.md`). Branch `fix/ux13-first-questions-arrive`, from main `713a0efd08`. The backend half of the UX audit's stage "First questions arrive" (`ux-journey-audit-2.md`: UX-13, F20, P11); the screen half (Today offering the first questions at once) is a separate step.

## What the walks measured

Read with read-only connections from the walks' synthetic vaults (`fixtures-local/ux-walks/{student-2,expert-1,retainer-2,project-1,notes-1}/vault/state.sqlite` in the audit worktree): `ingest_jobs`, `model_work_checkpoints`, `synthesis_runs`, `synthesis_manifests` and `model_call_receipts`. Every build ran on the ChatGPT plan (`chatgpt_medium`, `gpt-6.1-sol`). "Reported" is the service's output token count, reasoning included; "estimate" is the reply's characters / 4, the house estimate.

**Inventory windows** (one unit of one window each; the model was told "Keep the complete JSON response within 3000 output tokens."):

| Walk, first documents | Reported | Estimate of the reply | Stored inventory (with the service's ids) | Outcome on main |
|---|---|---|---|---|
| student-2 | 3,117 | 2,989 | 3,254 | refused; the learner's Try again reused the saved window |
| expert-1 | 3,169 | 2,758 | 2,672 | refused; Try again reused it |
| retainer-2 | 3,105 | 2,961 | not stored | refused; never retried, synthesis `blocked` |
| project-1 | 2,851 | 2,751 | 3,029 | kept |
| notes-1, first source | 2,811 | 2,765 | 2,461 | kept |
| notes-1, second source | 2,567 | 2,408 | 2,228 | kept |

Three of six were over 3,000 by 3.5 % to 5.6 %. A window is charged the larger of the reported count and the estimate, so the reported count decides: the largest is 3,169. (The audit's "2,672 to 3,254" are the stored sizes in the job's usage; the stored copy is no longer what is checked, since UX-1.) retainer-2's other source had smaller units: 523, 889, 1,342, 2,536.

**Synthesis passes** (told "within 10000 output tokens"; one shard each):

| Walk | Reported (of it reasoning) | Estimate of the stored result | Outcome on main |
|---|---|---|---|
| student-2 | 10,352 (341) | 7,521 | refused, "A synthesis pass exceeded its output budget."; build failed at 00:40, while the learner was in the Reader |
| expert-1 | 8,748 (161) | 6,472 | kept |
| notes-1, first source | 7,090 (150) | 5,520 | kept |
| notes-1, second source | 1,014 (284) | 613 | kept |
| project-1, an append (told `append_output_tokens`, 10,000) | 8,158 (330) | 5,524 | kept |

## What each budget is for (main, `713a0efd08`)

| `[ingest.budgets]` field | Sent to the provider | Told to the model | Checked after | Over it | In the build estimate | In a compared identity |
|---|---|---|---|---|---|---|
| `inventory_output_tokens` (3,000) | as `max_tokens` on the chat (metered) route; Codex ignores it | the plan route takes no cap: the prompt ends "Keep the complete JSON response within 3000 output tokens." | each fresh window: charge (reported, else the estimate) > 3,000 raises `InventoryValidationError` | the window was saved first, then refused: the unit fails, the job fails; a retry reuses the saved window at no charge (UX-1). Paid in full; on the plan route no money | `units × 3,000` (`build_plan.py`), priced into `estimate_usd` and the job's `job_tokens`; the request gate's reservation for a request naming no cap | none: the window key and the unit row key leave the budget out (`inventory_window_key`, `inventory_row_key`) |
| `synthesis_shard_output_tokens` (10,000) | as `max_tokens` (the pass limit is `min(shard, total − spent)`) | the prompt sentence, with that limit | each fresh pass: charge > limit raises `budget_exceeded`; the result's own size > 10,000 likewise | saved first, then refused; no retry; a manual Retry reuses the pass | `shards × 10,000` | the manifest's `token_budget` (`manifest_hash`, the agent-run cache seam, K2.2/K2.3), recorded value only; pass and shard keys leave it out |
| `synthesis_output_tokens` (16,000) | the structuring call is sent what is left of it | as above | the merged result's own size | refused | not charted | the manifest's `token_budget` |
| `append_output_tokens` (10,000) | every append request's limit | the prompt sentence | the answer's own size (not the report) > 10,000 | saved, then refused | `10,000` for an update | the manifest's `token_budget` (append) |
| `inventory_input_tokens`, `synthesis_shard_input_tokens`, `synthesis_total_input_ceiling`, `append_*_input_*` | no | no | preflights before a request is sent; the input budgets also split windows and shards | refused before anything is paid | input estimates | the shard input size in the manifest; windows' text through their prompts |

So the output budgets did three jobs at once: what the model is asked to write, the hard cap, and the refusal after the answer, all at the size the live model writes. On the plan route a refusal threw away an answer the learner had already waited three to four minutes for.

What a first document (one unit of one window, one shard) could write on main, per attempt: shown as 3,000 + 10,000 = 13,000 output tokens; on a metered route really up to 3,000 + 16,000 = 19,000 (the pass, a span round and the structuring call share the run's 16,000). Each learner Retry could add as much again.

## The rule now

- **The working size stays what the model is asked to aim for.** `inventory_output_tokens` and `synthesis_shard_output_tokens` are stated to the plan route exactly as before: the plan request of a build that fits them is byte-identical.
- **What is kept is held to a ceiling above it.** An inventory window: the new `inventory_output_ceiling_tokens` (6,000), never below the working size. A synthesis pass: what the run's total, `synthesis_output_tokens`, still leaves (16,000 for a first run's first pass). `generation_limit(working, ceiling=...)` carries both; the chat transport sends the ceiling as `max_tokens`; the plan route still states the working size; Codex ignores both, as before.
- **An answer over its ceiling is a runaway: refused before it is saved.** Kept, it would answer every retry into the same refusal. A retry asks for it again, like an answer that fails validation.
- **An automatic build retries a failed model step once on its own** (`runner.py`, `retries_on_its_own`, `a_retry_may_cure`): the inventory, bootstrap synthesis and append synthesis jobs of an automatic build, after a failure a fresh try may cure (an answer cut off, over its ceiling, invalid, late or not given: the `AIProviderUnavailable` family but not an interrupt, `InventoryValidationError`, `budget_exceeded`). Not after a cancellation, a spend pause, a gate's verdict, a rejected proposal or an append over its input ceiling. The second try is in the same claim (`attempt_count` stays 1, the job stays running, the card says "Writing questions…"), re-admitted afresh, and reuses every answer kept: saved windows and inventoried units, saved passes and shards.
- **On a metered route the retry spends only what the estimate left.** It is admitted with the build's estimate as its authorization (`admit_auto_build_job`): what the first try spent is subtracted, and the job's pre-check and every request are held to the rest. When nothing is left the build pauses with "Questions for … would cost more than expected · Build them". Subscription routes are never capped, as before.
- **A second failure stops the build**: job and batch `failed`, and the sidecar's line for the book is "Questions for … need another try" (tone `problem`, action Retry), which Today reads as "Couldn't get questions ready … Try again".

### Why these ceilings

- **Synthesis: the run's own total, no new number.** The owner already set what a synthesis run may write (16,000) and every call of the run was already held to what it leaves; only the per-pass refusal sat at the shard size. A pass may now use the total: the measured 10,352 is kept, and a run still never writes more than 16,000.
- **Inventory: a named setting, twice the working size.** There is no run total to borrow. Twice is the room the AI output policy already gives any other call that runs past its budget (`ai/output_budget.py`: one retry at double the budget, `TRUNCATION_RETRY_FACTOR`), so it is not a new allowance. Against the data: the largest live window was 3,169 (5.6 % over), so 6,000 is far above what the live model writes while a runaway is refused after costing at most one more working size. The field's doc states it in one sentence. The ceiling never falls below the working size, so raising `inventory_output_tokens` past 6,000 (Settings allows up to 100,000) leaves no headroom, as before, rather than a ceiling below the request.

## What the learner sees

| Outcome | Before | After |
|---|---|---|
| An answer a little over the working size (three of six first windows; one of four passes) | build stopped: "Questions for this article need another try"; on synthesis, unseen while reading on | kept; the build goes on |
| A transient failure, a cut-off or invalid answer, or a runaway, once | build stopped | "Writing questions…" continues: the step is asked once more, the answers kept are not asked again |
| The same twice | (as above) | "Questions for … need another try" · Retry; Today: "Couldn't get questions ready for … Try again" |
| On a metered route, a retry that would pass the estimate | (no retry) | "Questions for … would cost more than expected" · Build them |

## Spend

First document, one unit of one window, one shard, output tokens:

| | Shown in the estimate | Most one attempt can write (metered) | With the automatic retry |
|---|---|---|---|
| Before | 3,000 + 10,000 = 13,000 | 3,000 + 16,000 = 19,000 | no retry; each Retry tap up to 19,000 more |
| After | 6,000 + 16,000 = 22,000 | 6,000 + 16,000 = 22,000 | metered: held to what is left of the estimate, so the build's total stays within it; subscription: the second try asks only for what was not kept, at most another 22,000 |

The estimate is shown to the learner only on a metered route and only when it is over the confirmation threshold (`threshold_usd`, $1.00). At the default price ($5 per million tokens) the estimate's output part goes from $0.065 to $0.11 for a first document, still far under the threshold, so the learner is shown nothing either way; a larger book crosses the threshold a little sooner. A multi-shard build's synthesis line now charts the run's 16,000 instead of `shards × 10,000`, which was more than a run could write. On the ChatGPT plan (the live route) nothing is priced: tokens are kept as `estimated_only`.

Before, the shown 13,000 under-stated what one metered attempt could already write (19,000); after, the estimate is the cap for the work charted. It still charts one window per unit, as UX-1 noted: a unit long enough for several windows can write a ceiling per window.

## Tests (fail first)

`tests/test_first_questions_arrive.py` (new), on main `713a0efd08`: 13 of 14 failed; the fourteenth, the byte-identical guard, passed on main by construction (its hash was computed there) and still passes.

| Test | On main |
|---|---|
| an inventory window a little over its working size completes (3,169 reported) | inventory `failed` |
| a synthesis pass a little over its shard size completes (10,352 reported) | synthesis `failed` |
| a runaway inventory window is refused, not kept, asked once more | 2 window checkpoints kept, one call |
| a runaway synthesis pass likewise | 1 pass checkpoint kept, one call |
| an inventory that fails once is retried once without asking again for what was kept | inventory `failed` |
| a synthesis that fails once is retried once; inventories not asked again | synthesis `failed` |
| a synthesis retry reuses the pass it kept | synthesis `failed` |
| an inventory that fails twice stops with Retry, and the card says so | one call per unit, not two |
| a synthesis that fails twice likewise | one call |
| a build that fits the working sizes sends the same requests (every prompt and its stated limit, hashed, ids masked) | passed (guard) |
| the build estimate charts what a build may now write | no `inventory_output_ceiling_tokens` |
| on a metered route the retry spends only what the estimate left (first requests capped at 6,000) | `AIInvalidOutput`, not `spend_paused` |
| the plan route states the working size and a chat route is capped at the ceiling | `generation_limit()` takes no ceiling |
| the plan route request is byte-identical under a ceiling | likewise |

After the first commit (ceilings, no retry) the eight retry and spend tests still failed; after the second all fourteen pass.

New in existing files: `test_inventory_output_allowance.py::test_a_window_a_little_over_its_budget_is_kept_under_a_ceiling_above_it`, `test_source_set_synthesis.py::test_a_pass_over_its_shard_size_is_kept_within_the_run_total`.

## Assertions changed, and why

The rule changes on purpose: an answer over its ceiling is no longer saved, and a pass is held to the run's total, not its shard size.

- `test_inventory_output_allowance.py`: `test_after_a_window_writes_past_its_limit_retry_goes_on_from_where_it_stopped` became `…past_its_ceiling…`. The refused window is now the last one; Retry asks it again (`windows + 1` calls, `windows - 1` reused) instead of reusing it. Still proves Retry goes on from where it stopped.
- `test_source_inventory.py::test_inventory_can_disable_the_output_ceiling`: the run without a ceiling asks again for the refused window (2 calls, 0 reused; it was 1 and 1).
- `test_source_set_synthesis.py::test_over_budget_pass_is_checkpointed_and_reused_under_a_larger_budget` became `test_a_pass_over_what_the_run_total_leaves_is_refused_and_not_kept`: the over-budget run now lowers `synthesis_output_tokens` too (a shard size of 100 alone is now kept within the run total); no pass checkpoint is kept and the later run asks again (2 calls; it was 1).
- `test_model_work_checkpoints.py::test_synthesis_pass_checkpoint_that_no_longer_validates_is_discarded`: only its setup. It made its saved pass with an over-budget failure, which no longer saves the pass; it now fails the run after the pass is saved (`persist_proposal_batch` raising, as the structuring-retry test beside it does) and deletes the completed-shard row so the pass layer answers. Its assertions are unchanged.

## Pins and goldens

- `tests/test_identity_pins.py`: no pin moved (run after each source commit). Nothing sent to a model changes for a build that fits the working sizes; no reuse key includes a budget; the manifest's recorded budgets are the same fields with the same defaults (the new inventory field is not recorded there, being an inventory setting).
- `tests/goldens/effective_defaults.toml`: the line `ingest.budgets.inventory_output_ceiling_tokens = 6000` was added by the first commit and taken out again by the landing fix below (`--write`). The config reference is regenerated at landing.

### Landing fix: the new field moved whole-config hashes

The landing gate failed seven tests this step had not run: six in `tests/test_retired_config_identities.py` (a digest of `identity_dump(config)` and of the plain dump, recorded at arc C's base and at the kill switches' base, e.g. `beffb8c8…109f7` became `16d6822d…5625c`) and `tests/test_diagnosis_journey_golden.py::test_diagnosis_journey[fg1_wait]`, whose only changed leaf was a decision-state receipt's `versions.config` (`router_objective/decision_state.py` `_config_hash`, a hash of `config.model_dump(mode="json")`). A new field of `IngestBudgetsConfig` is in every whole-config dump, so every hash of one moved at a fixed input. `test_identity_pins.py` covers the sections and types it registers, not these whole-config hashes.

Fix (`config/schema.py`, `IngestBudgetsConfig.inventory_output_ceiling_tokens`): `Field(default=6000, exclude_if=<equals 6000>)`, the vault-model pattern for a field added under recorded identities. At its default the field is in no dump, so a vault that does not set it hashes exactly as before: the recorded digests and the journey golden were not regenerated and pass. A vault that sets another value is dumped with it, and those hashes move, deliberately: the ceiling changes what a build keeps and pays for, so a record of the config in force (a decision state's or a report's config hash) should name it. Nothing that serves, schedules or reuses paid work compares these whole-config hashes (the synthesis manifest names its budgets one by one and not this field; no window, pass or row key includes a budget). The cost: `learnloop config effective` and the effective-defaults golden no longer show the field at its default. Test: `test_the_ceiling_at_its_default_leaves_every_whole_config_hash_as_it_was` (fails on the branch before the fix: the field is in `identity_dump`).

The step's other new fields reach no compared value: `StructuredRequest.output_ceiling_tokens` is read only by the chat transport (as `max_tokens`) and is not dumped; `JobContext.retrying_on_its_own` and `PreparedInventory.output_ceiling_tokens` are never dumped or keyed. The plan route's prompt states the working size as before. One provenance value does change on the chat route: a physical request's receipt records the `max_tokens` it was sent with, now the ceiling for inventory windows and synthesis passes.

## What I ran

Every run through `uv run --no-sync pytest -q -n 1` in a 3G scope, on explicit files.

- The new file on main `713a0efd08`: 13 failed, 1 passed (the byte-identical guard). After the first commit: 8 failed (the retry and spend tests), 6 passed. After the second: 14 passed.
- Related files after the first commit (`test_inventory_output_allowance`, `test_source_set_synthesis`, `test_model_work_checkpoints`, `test_source_inventory`, `test_effective_defaults_golden`, `test_ingest_m3`, `test_openai_chat_client`, `test_output_budget`, `test_structured_transport_parity`, `test_source_append`, `test_inventory_merge_parallel`, `test_chatgpt_plan_provider`, `test_identity_pins`): 588 passed after the ports above.
- `scripts/affected_tests.py --files <the 12 changed source files>` listed 1,094 files. I ran the 91 whose names contain inventory, ingest, add_source, synthesis, article, budget, auto_build, ux_phase1, build_plan, runner, append, checkpoint, spend, transport, openai, chatgpt_plan, output_budget, quick_add, keep_ahead, reread, glm, study_map, cost, retry, figure_rich, progressive or book, plus `test_ux_phase3_today`, `test_ux_walk_harness` and `test_keep_local_retired`, in three chunks of at most 40 with `-m "not arc_close"`: 589 passed; 692 passed; 154 passed, 1 skipped.
- Gates: the new and edited test files with `test_identity_pins`, `test_structure_ratchets`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_kill_switches`, `test_sqlite_file_copies`: 476 passed. `test_test_layout` alone: 3 passed. `test_architecture` alone: 18 passed. `ruff check`: all checks passed. `lint-imports --no-cache`: 43 kept, 0 broken. `scripts/check_gate_partition.py`: 31,484 collected, landing 31,419 + arc_close 65.

## Not verified

- No live route, desktop app or walk: everything here runs on house fakes (the plan route's request through its local fake server, the chat route through the fake OpenAI client).
- The chat route's cap at the ceiling is proved on the fake client; a provider whose own maximum is below the ceiling is held to the profile's `max_tokens`, as before.
- A complete answer over the ceiling on a metered route needs the estimate (characters / 4) to exceed the reported count; the cap makes it otherwise impossible. Such an answer is refused unkept and paid for once.
- On a subscription route the second try of a refused runaway asks the plan again: plan usage, not money. Every kept answer is reused, never asked again.
- The estimate still charts one window per unit (UX-1's note).
- Manual builds (the Ingest screen, the CLI) do not retry on their own; their failures still go to the learner, as before.

## What the screen half (P11) needs from the backend that is not there yet

- **An amount for question writing.** P11's "about 2 minutes" needs a per-build time from the build's windows and passes. `build_minutes_phrase` measures past builds per section; nothing estimates from windows and passes before the first build.
- **"Retried once already."** The job's message says "Trying again" while the second try runs, but nothing durable records that a failed build already retried on its own, so the screen cannot say "Couldn't write questions … (it tried twice)". A field on the status line (or the job's error) would carry it.
- **Word of a build's end where the learner is.** Today polls the cards while it shows "on their way" (`TodayPlace.tsx`, `CAUSE_POLL_MS`), and the sidecar already said "need another try" once student-2's synthesis failed at 00:40; but the learner was in the Reader, so "on their way" was the last thing they saw. Nothing outside Today says that a build finished or stopped; the backend has no event for it (no revision is bumped when a build's batch ends: `bump_queue_revision` runs only for completed queue-affecting job types, which exclude the build's).
- **How many questions came, from what was read.** "5 questions from …, the part you read" needs the build's question count and the sections it covered on the status line; the job result has `item_counts` and the planner outcome has the chapters, but the line does not carry them.
