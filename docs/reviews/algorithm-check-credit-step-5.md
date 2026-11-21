# Check credit: stored-row report (TV2-1, step 5)

This change adds `scripts/check_credit_report.py`, its synthetic builders and tests. Nothing under `src/` changes.
It does not activate a tag, rewrite a decision, rebuild a projection, settle a commitment, or change an identity pin.
The task's untracked design copy stays untracked. `spec_teacher_v2.md` is absent on this tip; the supplied design and
`algorithm-check-credit-steps-1-4.md` provide the contract.

## Read these judgment calls first

1. **Three different comparison classes remain different.** Legacy rounded traces do not qualify as exact replay.
   As-of delivery counts are computable; full as-of numeric values generally are not. The current-copy comparison is
   a deliberately labelled **lesson-versus-stop scenario**, not the original decision's full support or corrected
   mixing probability. It freezes the present-day input builder's inputs, retains the recorded lesson contract,
   remembered plan minutes and price, and evaluates both policies on those same inputs with a fixed report seed.
   Its historical declined continuation is unavailable: the scenario uses the evaluator's default continuation.
   It does not make a model request or run the daily-plan policy builder.
2. **Historical eligibility is not inferred from today's items.** Each decision-time group shows both possible
   one-trial seeds, explicitly as sensitivity scenarios, plus the seed-omitted posterior. Current eligibility is
   counted separately. Computable current scenarios also expose the actual availability, S/F, censor reasons,
   alpha/beta, predictive mean, minutes and duration basis used. Retention never pools transfer failures.
3. **Alternative lessons are bound but not attributed to the offered topic.** Accepted offers must also match the
   response's candidate ref. The report separates offered lessons, alternative lessons, and all vault receipts.
   The delivery estimator pools actual receipt trials vault-wide, including an alternative lesson's own receipt;
   that is not a claim that the originally offered topic received its outcomes. Linked lesson counts deduplicate
   lesson ids. Missing response tables, missing reserved lesson rows/ids, mismatched accepted refs and closed
   lessons without receipts are explicit binding gaps.
4. **Presentations and due dates are operational counts, not the success label.** `presented` requires the receipt's
   item and the presentation block's matching commitment id, while due at that presentation. Item presentations
   lacking that binding have a separate count. Help recorded in the presentation's second cannot retroactively
   erase its display: due-ness is read immediately before that second. `due` means the effective date has elapsed
   at the cutoff; it can overlap answered or terminal entries and does not mean an outstanding eligible duty.
   Helped-only means an observed non-own-answer attempt since initial due and no qualifying cold completion.
5. **Minutes include incomplete work.** The script's unserved `_MeteredModel` observes the new evaluator's return
   callback's actual in-window minutes, including a check clipped before it answers. Completion and minutes are
   weighted per draw by acceptance, preserving their correlation. Accepted-branch counts are also available from
   the pure paired helper. The worked fixture's p=0.5 normalization is distinct from its finite Beta draws.
6. **Read-only is enforced, not assumed.** The precedent's URI handling opens `mode=ro`, using `immutable=1` only
   for checkpointed WAL copies without a WAL file; WAL without SHM is refused. The reader adds `query_only`, keeps
   one pinned read transaction and denies/records attempted writes through SQLite's authorizer. A dependency
   swallowing its denied write still raises the report's `dependency_requested_write` stop flag. `--out` cannot
   overwrite the copy. No migration, settlement, copy creation, environment overlay or credential loading occurs.
   Dependency log messages and CLI exceptions are suppressed because they can carry learner text; failures emit
   a fixed message. Successful output uses fixed labels and numeric aggregates, never ids, paths, titles or prose.
7. **Exact replay has an explicit, unserved prototype contract.** `check_credit_replay` in a trace holds a version,
   a canonical JSON **string** and its SHA-256 digest. The string survives the trace's six-decimal recursive rounding.
   Every field of every supported numeric dataclass is required, as are the original clock, numeric seed, final
   draw count, evaluator options and policy/stream identities. Frozen support must match the decision's feasible
   support, the chosen offer must belong to it, and old/proposed actions must agree on all non-check fields.
   This format has no live writer. Its test is synthetic, not evidence that existing owner traces contain it.
   Unsupported diagnostic payloads or incompatible versions are not claimed replayable.

## Reads and outputs

The database reader uses `router_decisions`, `router_objective_traces`, `router_suggestion_responses`, `lessons`,
`lesson_receipts`, `attention_blocks`, `attention_block_events` and `plan_presentations`. The existing delivery
classifier reads commitment versions/targets/events, attempts, grade availability and cold-at-attempt eligibility.
It never uses the first-attempt convenience join in `offer_report` as its cold-completion label. Neither wrong
answers nor helped answers are relabelled according to correctness: qualifying wrong answers are successes.

The JSON and text table contain support candidate counts; draws; shown receipts; separate accepted, declined,
ignored, superseded, never-shown, alternative and unanswered counts; distinct linked open/closed/missing lessons;
entry counts by purpose and cohort; missing/canonical/due/presented/cold/helped/terminal/censored counts; cold
correctness bins; and censored overdue ages. `offers_without_shown_receipt` is not silently classified as
`never_shown` or `ignored`. No missing response is synthesized by a sweep.

S/F, censoring, alpha, beta and means are shown for retention and transfer at each distinct decision time and now.
Identical decision timestamps share a group and an offer count, without printing the timestamps. Both one-trial
availability seeds and the seed-omitted column are shown. With no resolved trials, the seed-omitted mean is null,
not an epsilon or invented prior. Database-only reads use the classifier defaults and say so; directory reads use
the copy's configuration with `load_environment=False`. Historical configuration and grade-hold evidence-release
limitations are stated. Persistent censoring can make this resolved-outcome estimator optimistic.

Recorded old Q and accepted/declined values are aggregated independently of reconstruction success, with coverage
counts per number. Each computable class reports recomputed old/proposed values, accepted/declined terms, paired
differences, expected completed checks and minutes, numeric ordering/choice changes, and mixing change coverage.
The JSON also aggregates each accepted/declined ledger term. Zero comparisons means **not computable**, never
agreement. No guessed bonus is subtracted.

| Class | Inputs required | What this report can compute |
|---|---|---|
| EXACT historical counterfactual | Lossless full `Inputs`, every candidate and branch, typed check inputs, original numeric seed/clock, completed draw count, evaluator options and policy identities; digest-valid string payload bound to the decision | Supported complete payloads only. The miniature fixture has 1 eligible offer, 1 rounded trace, 2 invalid/incomplete payloads and 4 absent traces. Current live writers do not create the payload. |
| AS-OF reconstruction | Historical authored items/goals, protection/lifecycle view, fitted model state, session/price/support, numeric precision/seed/refinement and time-available evidence | S/F and censoring are reconstructed; full values are not computable with the present rows. Missing fields are listed, rather than filled from today's state. |
| CURRENT-COPY paired scenario | A full copy directory, recorded offer action/main topic, linked plan remembered minutes, trace price; current authored content and read-only numeric inputs | The real-builder test computes 1 of 8 offers. Both policies receive the same present-day inputs; ranking is within lesson-versus-stop. Historical mixing is not computable from this restricted scenario. |

For exact payloads, mixing is computable only when the complete `mix.recompute` inputs are supplied: support,
staged ref, epsilon, weight, failed-policy statuses, LLM distribution and failure rule. Original numeric and mixing
seeds are different things. The prototype numeric payload can omit mixing and reports zero mixing coverage.

## Synthetic vault and known totals

`tests/check_credit_report_helpers.py` uses `create_basic_vault` and the canonical commitment writer, and inserts
only synthetic rows. The base fixture has no objective traces, intentionally exercising the stop condition that
no stored value comparison is computable. Additional fixtures add rounded, lossless and incomplete traces, and a
real plan binding for the current-copy comparison. No test imports another test file.

| Population | Expected |
|---|---:|
| Lesson candidates in support / drawn / shown / without a shown receipt | 10 / 8 / 5 / 3 |
| Accepted / declined / ignored / superseded / never shown / alternative / unanswered | 2 / 1 / 1 / 1 / 1 / 1 / 1 |
| Distinct linked open / closed / not opened lessons | 1 / 2 / 0 |
| Offered-lesson retention / transfer entries | 4 / 1 |
| Offered-lesson missing / canonical entries | 1 / 4 |
| Offered-lesson due / presented / cold / helped-only / terminal / censored entries | 3 / 2 / 1 / 1 / 1 / 2 |
| Alternative-lesson missing retention entries | 1 |
| All-vault retention S / F / censored, later and now | 1 / 2 / 2 |
| All-vault transfer S / F / censored, later and now | 0 / 1 / 0 |

Seven offers precede the receipts; one follows the answers. Early counts are all zero. At the later cutoff, the
retention mean is 1/4 with e=0, 1/2 with e=1, and 1/3 without the seed. The lone cold answer is wrong and still S.
The helped check is not yet due after redating; the untouched pending check is overdue six days. No elapsed-time
expiry is invented. Current eligibility is available for all eight offered topics on the full synthetic directory.

The shared worked fixture verifies accepted Q 0.6 versus 0.5, unchanged declined Q 0.449489743, and at exactly
p=0.5: **0.524744871 versus 0.474744871**, paired difference **-0.05**. No return yields zero completed checks and
zero check minutes. A separate horizon-clipping fixture has zero completions and 2.88 accepted-branch minutes.

## Running on a copy

Use an idle, backup-API copy prepared by the owner/orchestrator. The report creates no copy. From this checkout,
using its installed venv (or the provided `py.sh python` wrapper):

```sh
python scripts/check_credit_report.py --vault "$COPY" --out "$TEXT_REPORT"
python scripts/check_credit_report.py --vault "$COPY" --json --out "$JSON_REPORT"
```

Output files must be outside the copy. Omit `--out` for stdout. `--as-of` accepts a UTC ISO cutoff; otherwise now
is used. `--draws` defaults to 8 for the explicitly labelled current-copy scenario; exact replay uses the frozen
draw count. A database file alone supports populations and delivery statistics, but not current authored inputs.
No model or network access is needed. The synthetic CLI was run in both formats and its database SHA-256 was
identical before and after both executions.

## Activation must store

- The complete lossless numeric input snapshot: topic/order/uses, AD and lesson curve, combiner/learning/FSRS,
  return model, price/session/cutoff/horizon, all candidate actions including alternative/declined/sequence branches,
  forecasts and any relevant residual/preference inputs. Preserve numeric precision inside a string payload with
  a version and digest, not another rounded trace dictionary. Unsupported numeric paths must retain explicit
  non-replayable coverage until the report supports them.
- The original numeric seed, initial/final draw counts and refinement/termination settings, clock, evaluator
  options, algorithm/objective/delivery/prior/stream versions, support order and mixing inputs/seed. Do not confuse
  the router's mixing seed with the rollout seed. An empty options map in the prototype means that version's defaults.
- Each proposed check's key/group, topic, purpose/regime, delay, availability, S/F and censor reasons, alpha/beta,
  predictive mean, evidence digest, as-of time, seed version/basis, duration and estimator provenance. The numeric
  prototype already freezes typed checks, but activation also needs the full explanatory sensor receipts above.
- Preserve decision-response-actual-lesson and display bindings. Keep old decisions, receipts, plans and forecasts
  byte-identical. Do not backfill guessed historical inputs or rewrite them as new-tag decisions.

The base fixture triggers `no_stored_value_comparison`; missing-binding and denied-write fixtures trigger their
respective stop flags. Real-copy coverage cannot be stated before the orchestrator runs the report on supplied
copies. No documented private-vault census (including the 24-entry claim) is asserted here.

## Fail-first record and validation

`T` below means the supplied `t.sh` wrapper; `P` means its `py.sh` wrapper. No whole suite, socket-dependent test
credit, network call, model call, `git add`, `git commit`, pin writer or vault-reference generator was used.

The first seven tests were present before the script and failed with **7 FileNotFoundError setup errors**; this is
an API-absence red run, not a semantic characterization failure. After the first implementation: **7 passed**.
Subsequent failing runs exposed clipped minutes (0 instead of 2.88), missing current eligibility, another offer's
payload accepted as exact, non-check action changes accepted in a pair, a different commitment's presentation
attributed to the check, a missing response table crashing, missing current posterior output, a swallowed denied
write not flagged, incomplete support accepted as exact and same-second help hiding a presentation. One initial
current-scenario failure was a fixture setup mistake (`day` instead of `local_date`); it was fixed before claiming
behavioral coverage. The current-scenario test later failed on its missing posterior output before that was added.

| Command | Result lines, in run order when repeated |
|---|---|
| `T tests/test_check_credit_report.py -q -n 2` | `7 errors`; `7 passed`; `3 failed, 8 passed` (includes the fixture setup error); `3 failed, 8 passed`; `3 failed, 11 passed`; `14 passed`; `1 failed, 13 passed`; `14 passed`; `1 failed, 14 passed`; `15 passed`; `2 failed, 14 passed` |
| `T tests/test_check_credit_report.py tests/test_identity_pins.py -q -n 2` | `356 passed` |
| `T tests/test_check_delivery.py tests/test_check_inputs.py tests/test_check_value.py tests/test_check_credit_characterization.py tests/test_probe_router_report.py tests/test_structure_ratchets.py tests/test_sqlite_file_copies.py -q -n 2` | `56 passed, 1 xfailed` |
| `T tests/test_check_credit_report.py tests/test_check_delivery.py tests/test_check_inputs.py tests/test_check_value.py tests/test_check_credit_characterization.py tests/test_probe_router_report.py tests/test_identity_pins.py tests/test_structure_ratchets.py tests/test_sqlite_file_copies.py -q -n 2` | `416 passed, 1 xfailed`; **`417 passed, 1 xfailed`** (final, 27.19s) |
| `T tests/test_test_layout.py -q -n 1` | `3 passed`; `3 passed` (final, 20.04s) |
| `T tests/test_architecture.py -q -n 1` | `18 passed` |
| `P ruff check` | `2 errors` (unused import, loop binding); `All checks passed!`; `1 error` (render loop binding); `All checks passed!`; `All checks passed!` |
| `P lint-imports --no-cache` | `Contracts: 43 kept, 0 broken.` |
| `P python -c 'from pathlib import Path; from tests.check_credit_report_helpers import seed_report_vault; seed_report_vault(Path(".check-credit-synthetic")); print("Synthetic vault created")'` | `Synthetic vault created` |
| `P python scripts/check_credit_report.py --vault .check-credit-synthetic --as-of 2026-11-10T09:00:00Z --out .check-credit-synthetic-report.txt` | exit 0 |
| `P python` hash/CLI check (shown below) | `CLI text + JSON: exit 0; database SHA-256 unchanged` |

The hash/CLI check was:

```python
import hashlib, subprocess, sys
from pathlib import Path
db = Path(".check-credit-synthetic/state.sqlite")
before = hashlib.sha256(db.read_bytes()).digest()
base = [sys.executable, "scripts/check_credit_report.py", "--vault", ".check-credit-synthetic",
        "--as-of", "2026-11-10T09:00:00Z"]
subprocess.run(base + ["--out", ".check-credit-synthetic-report.txt"], check=True)
subprocess.run(base + ["--json", "--out", ".check-credit-synthetic-report.json"], check=True)
assert hashlib.sha256(db.read_bytes()).digest() == before
print("CLI text + JSON: exit 0; database SHA-256 unchanged")
```

The sole expected failure is the existing live offer activation test, unchanged from steps 1–4. No pin moved.
There is no test filename containing `offer_report` on this tip; the only `probe_router_report` match is included.
Synthetic scratch files are removed after this record is assembled.

## Not verified

No owner vault or private data was opened. No owner-copy value distribution, recommendation/offer-rate change,
24-entry census, upgrade, shadow rebuild, activation, broad suite or landing gate was run. As-of counts inherit the
receipt reader's documented grade-hold/replacement limitations. Current scenarios are a restricted comparison,
not historical support or original mixing. The exact payload contract is only a prototype exercised with synthetic
data; activation must add and verify its live writer, full provenance and all supported numeric paths. The fixture
does not establish current-copy compatibility with every historical schema/tag. Dedicated SQLite-copy tests passed;
the report's own byte tests and CLI check used synthetic copies, not every possible WAL/SHM failure mode.

## Quoted synthetic CLI output

```text
Check credit: aggregate read-only audit
population | count
lesson_candidates_in_support | 10
offers_drawn | 8
offers_shown | 5
offers_without_shown_receipt | 3
responses | {"accepted": 2, "chose_alternative": 1, "declined": 1, "ignored": 1, "never_shown": 1, "superseded": 1, "unanswered": 1}
linked lessons | {"closed": 2, "not_opened": 0, "open": 1}
entries | retention | transfer | missing | canonical | due | presented | cold | helped | abandoned | censored
offered_lesson_entries | 4 | 1 | 1 | 4 | 3 | 2 | 1 | 1 | 1 | 2
  cold correctness: {"correct": 0, "partial": 0, "unknown": 0, "wrong": 1}; presentations without commitment binding: 0
  censored overdue days: {"max": 6.0, "mean": 3.0}
alternative_lesson_entries | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0
  cold correctness: {"correct": 0, "partial": 0, "unknown": 0, "wrong": 0}; presentations without commitment binding: 0
  censored overdue days: {"max": null, "mean": null}
all_receipt_entries | 5 | 1 | 2 | 4 | 3 | 2 | 1 | 1 | 1 | 2
  cold correctness: {"correct": 0, "partial": 0, "unknown": 0, "wrong": 1}; presentations without commitment binding: 0
  censored overdue days: {"max": 6.0, "mean": 3.0}
delivery | purpose | S | F | censored | seed e=0 (alpha,beta,mean) | seed e=1 | no seed
decision group 1 (7 offers) | retention | 0 | 0 | 0 | (0.0,1.0,0.0) | (1.0,0.0,1.0) | (0,0,None)
decision group 1 (7 offers) | transfer | 0 | 0 | 0 | (0.0,1.0,0.0) | (1.0,0.0,1.0) | (0,0,None)
decision group 2 (1 offers) | retention | 1 | 2 | 2 | (1.0,3.0,0.25) | (2.0,2.0,0.5) | (1,2,0.3333333333333333)
  censored: {"not_yet_due": 1, "pending": 1}
decision group 2 (1 offers) | transfer | 0 | 1 | 0 | (0.0,2.0,0.0) | (1.0,1.0,0.5) | (0,1,0.0)
now | retention | 1 | 2 | 2 | (1.0,3.0,0.25) | (2.0,2.0,0.5) | (1,2,0.3333333333333333)
  censored: {"not_yet_due": 1, "pending": 1}
now | transfer | 0 | 1 | 0 | (0.0,2.0,0.0) | (1.0,1.0,0.5) | (0,1,0.0)
Current eligibility: {"available": 8, "offers": 8, "unavailable": 0, "unknown": 0}
Historical eligibility unavailable unless frozen; the two seed columns are sensitivity scenarios.
resolved-outcome sampling can overestimate completion with persistent censoring
grade-hold evidence releases are read in their current state
historical capture delay and attempt-availability settings are not frozen
recorded old values | {"accepted": {"mean": null, "n": 0}, "declined": {"mean": null, "n": 0}, "q": {"mean": null, "n": 0}}
EXACT historical counterfactual | 0 computable; 8 not computable
  changed ranking: 0/0; changed numeric choice: 0/0; changed mixing probability: 0/0
  missing: lossless numeric Inputs (all topics, uses, FSRS, AD, combiner, learning and return models); complete candidate actions including declined branches and forecasts; original numeric seed, completed draws, cutoff and evaluator options; decision-time eligibility, protection/lifecycle view, delivery sensors and duration provenance
  coverage: {"no_trace": 8}
AS-OF reconstruction | 0 computable; 8 not computable
  changed ranking: 0/0; changed numeric choice: 0/0; changed mixing probability: 0/0
  missing: historical authored items/goals and protection/lifecycle view; historical fitted models, session state, price and candidate support; unrounded numeric inputs, original numeric seed and refinement settings; grade-hold evidence releases have no complete as-of representation
CURRENT-COPY paired scenario | 0 computable; 8 not computable
  changed ranking: 0/0; changed numeric choice: 0/0; changed mixing probability: 0/0
  missing: authored vault, recorded offer action, plan remembered minutes and price
  coverage: {"offer_action_or_plan_price_inputs_unavailable": 8}
  present-day inputs; recorded offer contract and plan price; lesson versus stop only; not a historical correction or historical mixing comparison
stop conditions | {"binding_gaps": false, "dependency_requested_write": false, "no_stored_value_comparison": true}
```
