# UX-1: the first document's questions failed on the inventory budget

Ledger row UX-1 (`refactor-bug-ledger.md`). Branch `fix/ux1-inventory-budget`.

## The cause, with numbers

Both walks added `samples/understanding-linear-algebra-symmetric-matrices-and-variance.html`. Read from the walks' vaults (read-only):

- The page is **one unit** ("Document", 59 blocks) and **one window**: about 3,330 tokens of text (4,380 for the view as the model sees it, with span ids), far under the 20,000-token input budget. It was not a several-windows problem.
- Beginner walk: the model (the ChatGPT plan, which reports no token counts) was told 3,000 tokens and wrote 11,532 characters, **2,883 tokens** by the estimate. It was charged for the stored copy, after the service had replaced the model's short ids with its own (`u1|w0|i3|…`): **3,183 tokens**, over 3,000. The unit failed, and so did both attempts.
- Student walk, same page: the model wrote 2,656 and was charged 2,982. It passed with 18 tokens to spare. The page sits right at the limit, so the result was close to a coin flip.
- The window was saved before the check, and a retry reused it and charged it again, so Retry could never succeed.
- Separately, the code allowed **one** 3,000 budget per unit however many windows the unit had: each later window was sent with what was left, and the merged result was checked against the same 3,000 again. Any unit longer than one window (20,000 input tokens) could not finish.

How the budget is set (all per unit before this fix): book sections, articles and appended sources all go through the inventory job (`jobs.py` about line 1491): `output_budget_tokens` from the payload, else `[ingest.budgets] inventory_output_tokens` (3000), or none when `unlimited_token_budget`. A book has a unit per section. A web page is one unit. An appended source's units are enqueued the same way (`enqueue_source_set_append`). An explicit setting comes through the sidecar's ingest handler (`inventory_output_tokens` or `budget_overrides`, accepted from 1,000 to 100,000) into the same payload field. The metered request gate reserves the same amount for a request that names no limit (`add_source.py` `_request_output_ceiling`). The build-plan estimate charts `units × inventory_output_tokens` (`build_plan.py` line 279).

## The rule now

- `inventory_output_tokens` is **one window's** amount. Every window's request is sent under it. A unit gets it once per window, and its window count is known before the first call.
- A window is charged **what the model wrote**: the provider's reported output tokens, else the estimate of its reply before the service's ids go in. The limit it was sent under applies to its reply, not to our ids.
- A fresh window over its limit still fails the unit, after it is saved. The cap on a runaway reply stays.
- A saved window is reused without being charged again: it was judged and paid for when it was made. A retry asks only for the windows not yet answered.
- The merged inventory is no longer checked: it is just the windows, each already held to its limit, plus the service's ids. Its size is still recorded in `usage`.
- When a build stops, the Library card's details give a plain sentence and point to "See how it was added and built". The job keeps the reason. This applies to both "need another try" lines (`add_source.py`, `BUILD_STOPPED_DETAILS`).

## Worst-case output spend for one unit, one attempt

- **Before:** about B = 3,000 in total (the first request under B, each later one under what was left). The ChatGPT plan only states the limit in the prompt, so the request that crossed it could run over before the unit failed. A unit whose honest output was over B could never finish.
- **After:** at most B for each window requested, so at most N × B for a unit of N windows. The same caveat applies to the plan: at most one request can run over before the unit stops. Across attempts, each window is paid for once it validates. A window that fails validation is asked again, as before.
- The sample page has N = 1, so its budget stays 3,000. A unit of three windows goes from 3,000 to 9,000.

## Fail-first evidence

On main (`8c40bd4343`), all five tests in `tests/test_inventory_output_allowance.py` fail:
- The single window within its limit, the three-window unit and both cases of the retry test fail with `InventoryValidationError: inventory output exceeded its configured token budget`. The retry fails on the second run, at the same point.
- The card test fails with `details: 'inventory output exceeded its configured token budget'`.

After the fix all five pass. The existing `test_inventory_can_disable_the_output_ceiling` passes unchanged.

## What was run

New tests and `tests/test_source_inventory.py`: 22 passed. `scripts/affected_tests.py` listed 884 files, so I ran the 30 whose names contain inventory, ingest, add_source, synthesis, article or budget: 416 passed. The status-line files (`test_ux_phase1_*`, `test_keep_ahead_append_units`, `test_reread_safety`, `test_glm_ocr`, `test_keep_local_retired`): 271 passed. `test_identity_pins`, `test_structure_ratchets`, `test_effective_defaults_golden`: 348 passed. `test_test_layout` (alone, `-n 1`): 3 passed. `ruff check`: clean. `lint-imports --no-cache`: 43 kept, 0 broken.

## Not verified

- No real model route or desktop app was run. The fix is proved with fakes only.
- The rest of the 884 affected files.
- The build-plan estimate still charts one window per unit (`units × B`), as its input estimate already does, so it understates long units.
- 3,000 per window against a 20,000-token input window: an honest inventory here was about 0.66 to 0.73 of the view, so a full window is squeezed (the plan's model compresses; a metered route would truncate). That is the owner's token economics and I left it unchanged.
