# Slice 2 T4: Codex review and fixes

Branch `slice-2/t4`, worktree `learnanything-t4`. Codex job `20261012-122222-VOlyNf`
reviewed the stage as built (`974c5647..2d3aec3b`; implementer's file:
`docs/reviews/slice-2-t4.md`). It returned seven findings: one High, five Medium and one
Low. Codex did not rerun the full suites, because `uv` could not take its cache lock in
the read-only sandbox. The fixes sit on top of `2d3aec3b`.

## Findings

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Identical texts collide across distinct judgment pairs | **Fixed** | `21908854` | `test_identical_answers_on_distinct_pairs_each_get_their_own_ledger_verdict`, `test_identical_answers_resume_without_reusing_the_other_pairs_verdict` |
| F2 | Medium | Incidental mathematical text becomes an authoritative reveal | **Fixed** | `21908854` | `test_incidental_math_shortlists_but_never_decides_a_reveal`; `test_an_occurrence_without_a_link_to_the_item_shortlists_but_never_decides` (5 cases: page reference, unrelated example, rejected alternative, restatement, prompt that states its answer); `test_working_the_items_own_expression_to_its_answer_decides` (7 cases) |
| F3 | Medium | Unrelated items can suppress a bound tutor-answer candidate | **Fixed** | `21908854` | `test_a_bound_tutor_pair_is_judged_however_many_items_share_its_answer` (four tied items, `top_k=3`) |
| F4 | Medium | Completed assessments disappear from the historical reader audit | **Fixed** | `21908854` | `test_a_reader_reveal_before_the_assessment_was_taken_stays_in_the_report` (reserve, then reader reply, then render), `test_a_reserve_already_burned_by_an_exposure_gets_no_burn_proposal` |
| F5 | Medium | Common symbolic answers are classified as non-mathematical | **Fixed** | `21908854` | `test_function_answers_without_numerals_are_checked` (4 cases, including `cos(x)` against `sin(x + pi/2)`), `test_function_runs_are_candidates` |
| F6 | Medium | The decision report lacks the required noise floor | **Fixed** | `21908854`, `cd4ea04e` | `test_the_report_carries_a_repeated_judgment_noise_floor_and_owner_audits`; the default plan in `test_dry_run_changes_nothing_and_builds_no_client`; `--repeat-sample` in `test_cli_dry_runs_and_refuses_unknown_detectors` |
| F7 | Low | Default subscription runs do not estimate monetary cost | **Rejected** | — | Conflicts with the merged, Codex-reviewed rule that every subscription command shares, and no declared Codex price exists. The numeric token estimate is now tested (see F7 below) |

F1 was High and is fixed, so a Codex re-review of the fix commits
(`21908854`, `cd4ea04e`) is due (`implementation_goal.md` §2, step 4).

Every fixed finding was reproduced first with a failing test on `2d3aec3b`. The new
report tests were run there with the new `repeat_sample` argument stripped.

### F1: one ledger id per pair and pass (fixed)

**Reproduced.** Two question events with the same tutor reply about one item got the
same `ctj_` id.
- **Within one run:** the second insert raised
  `sqlite3.IntegrityError: judgment_ledger is append-only`.
- **Interrupted and resumed:** the resumed run made no call, because both events
  matched the first event's row. The second pair never got its own verdict.

**Fix** (`ops/contamination/judge.py`).
- `input_hash` still addresses the judged content: prompt, schema, settings and judge
  revision.
- The id is `ctj_` plus a hash of three things: the input hash, the ordered pair
  identity `(task, left_kind, left_id, right_kind, right_id)`, and the pass.
- Each pair is judged and ledgered on its own. No verdict is shared between pairs,
  so no separate content cache is needed. Identical replies are rare, and the
  default route runs on the subscription.
- Verifier ids (`ctv_`) already included the pair.

**Tests.** Two calls and two ledger rows with distinct ids and one input hash; both
flagged and proposed; a rerun is fully cached. An interrupted run (provider failure on
the second pair, `--max-retries 0`) resumes with exactly one call, for the missing pair.

### F2: an occurrence shortlists; only a link decides (fixed)

**Reproduced.** Item "Compute 12 * 12." (answer `144`) and tutor reply "Read page 144
for the method." The verifier wrote a `reveal` (`verifier_decisions: 1`). That verdict
outranks an LLM `clean`.

**Fix** (`ops/contamination/symbolic.py`, `SYMBOLIC_VERSION` →
`contamination-symbolic-v2`).
- **An occurrence only shortlists.** A side equal to the expected answer marks the pair
  `symbolic`, and the pair goes to the judge.
- **When the verifier decides.** Only when one equation in the reply holds both:
  - the item's own expression, as written in its prompt (compared after notation
    normalization: spacing, atom brackets, LaTeX and Unicode operators);
  - the answer in its own form: its normalized text, or for a numeric answer any plain
    number equal to it (a rounding).
- **Example.** "12 \times 12 = 144" decides a reveal for "Compute 12 * 12"; "Read page
  144" does not.
- **Why equality alone cannot link.** Every expression of a "compute" item equals its
  answer (`12*12 = 144`). A restatement is not a reveal either:
  `(x+1)^2 = (x+1)(x+1)` for "Expand (x+1)^2".
- **Prompts that state their answer never link.** A prompt like "Show that 1/2 + 1/2 = 1"
  already contains its answer, so restating it reveals nothing.
- **Reader reserves.** The reserve's prompt, statement and question (never its expected
  answer) serve as its "prompt".
- **Old verifier rows.** Any v1 row (possibly a false reveal of this kind) is no longer
  read by the report.

**Negative cases** (match, not linked, no decision): a page reference; a fraction in an
unrelated example; a rejected alternative ("It's not x = 144"); a restatement; an equal
value in another computation (`6 * 24 = 144`); a prompt that states its answer.

**Positive cases** (decide): `12 \times 12 = 144`; `1/3 + 1/3 = \frac{2}{3}` against a
LaTeX prompt; the chain `3/4 + 1/6 = 9/12 + 2/12 = 11/12`; `2 + 2 = 4`;
`sin(pi/2 - x) = cos(x)` for "Simplify sin(pi/2 - x)"; `(x+1)^2 = x^2 + 2x + 1` for
"Expand (x + 1)^2"; the rounding `1/3 + 1/3 = 0.667`.

**Changed tests.**
- The report's verifier test now uses an item whose expression the reply works
  ("Compute 1/3 + 1/3"; "1/3 + 1/3 = 2/3").
- `test_equivalent_forms_match` now asserts distinctiveness (still reported) and that
  an occurrence with no prompt never decides.

### F3: every bound tutor pair is judged (fixed)

**Reproduced.** Four items shared one expected answer, so their vectors were identical.
The bound item, `pi_d`, sorted last by id and ranked 4th with `top_k=3`. The pair was
never shortlisted and the judge was never called.

**Fix** (`ops/contamination/detectors.py`).
- The tutor pair is already bound: one item per answered turn. Every answered,
  item-bound turn now goes to the judge with reason `bound`.
- R4 allows dropping a candidate only at a benchmark-set blocking cutoff. None exists
  yet (the `embeddings compare` harness is Phase 5a's), so a rank cut could only lose
  recall.
- **The rank is now a signal, not a gate.** The bound item's rank is a competition
  rank, so ties share the better place (rank 1 in the test, not an arbitrary 4). The
  `embedding` reason still marks rank ≤ k, as evaluation data for a future cutoff.
  `embedding_only` ignores `bound`.
- **Exam and reader shortlists** stay rank-based, since they are cross-products. They
  now keep a boundary tie whole (`top_k_with_ties`), and changed or out-of-scope
  records are filtered before ranking (the centroid is still the whole index).

**Changed test.** `test_no_judge_and_no_vectors_degrade_to_the_floor` asserted that the
paraphrase was "not seen" without vectors. With no vectors, both bound pairs now reach
the judge, and only the paraphrase is proposed.

### F4: historical reader reveals stay in the report (fixed)

**Reproduced.** Two surfaces were reserved, then a reader reply paraphrased one, then
that assessment was rendered (`open_administration`). The report no longer saw the
rendered surface.
- The `surface/statement` recipe dropped it, so its vector could not even be placed.
- The scan listed only currently reserved surfaces.

**Fix** (`detectors.py`, `recipes.py`, `report.py`).
- `assessment_reservations()` reads every assessment reservation, live or closed, with
  its immutable surface.
- **Scope.** A reader answer is compared with each surface whose reservation was live
  at the answer, or closed (rendered, cancelled or released) after it. A render before
  the answer is out of scope: the assessment was already taken.
- **Embedding scope.** The `surface/statement` recipe now covers these surfaces too.
  Text per surface is unchanged, so existing vectors stay valid and the recipe version
  stays 1. The reader's rank runs over in-scope surfaces only.
- **Floor.** A pair counts as caught by the floor only when the lexical hit is on a
  reserve that was live at the answer, since that is what the live path compared
  against. A lexical hit on a later reserve is reason `lexical`, with `floor` false.
- **Proposals follow current state.**

  | Reserve now | Proposal |
  |---|---|
  | Live and still unseen under the held-out rules (`evaluate_held_out_eligibility`) | `burn_reserve` |
  | Live but already exposed (for example, the live floor burned it) | None |
  | Rendered | `review_assessment`, with the administration id and `rendered_at`: its cold evidence may be contaminated |
  | Cancelled or released | None |

  The flag stays in the report in every case. Reader summaries add
  `flags_by_reservation_status`, and samples carry `reservation_status`,
  `live_at_answer` and `burn_eligible`.
- **Tests.**
  - The lifecycle test: the pre-render reply is flagged with `review_assessment`, and a
    reply after the render is never paired with that surface.
  - The burn test: a live reserve is proposed for a burn. Once it is exposed the way the
    live reader floor exposes it (`externally_reported`), it no longer is. The old
    `_proposal` returned `burn_reserve` for every reader flag.

### F5: function applications are math (fixed)

**Reproduced.**
- `symbolic_check("The answer is sin(x).", "sin(x)")` returned `not_math`.
- Runs like `cos(x)` were dropped, so a comparison against `sin(x + pi/2)` made zero
  comparisons.

**Fix.** `_has_math` also accepts a supported function application (`sqrt`, `sin`, …,
`Abs`) or `pi`. This applies to expected answers and to candidate runs. SymPy still
sees only `safe_math_text`.

**Tests.** `sin(x)`, `cos(x)` against `sin(x + pi/2)`, `\sqrt{x}`, `exp(t)`, and a
`tan(x)` non-match.

### F6: a noise floor from repeated judgments, beside the owner audit (fixed)

**Reproduced.** The report had one judgment per pair and no repeat. `--judge-revision`
only selects new verdicts; it does not compare passes.

**Fix** (`judge.py`, `report.py`, `cli/contamination.py`).
- **The sample.** `--repeat-sample N` (default 5, 0–50) picks the first N pairs per
  detector, in a stable hash order. A resumed or repeated report therefore re-judges the
  same pairs.
- **Pass 2.** Each sampled pair is judged a second time under identical settings. It
  has its own ledger id, with `"pass": 2` and `"repeat_of"` in the rationale and
  `pass` in the receipt's `budget_json`.
- **Pass 1 alone decides.** Repeats are planned after every pass-1 request, so a capped
  run spends on decisions first.
- **Dry run.** It plans repeats in calls and tokens and reports `repeat_requests`. A
  repeat adds no new pair or candidate to the caps.
- **New per-detector blocks.**
  - `noise_floor`: `repeat_pairs`, `compared`, `agree`, `disagree` and
    `disagreement_rate`.
  - `owner_audit`: `audited_pairs`, plus agreement of `llm` (pass 1) and of `verifier`
    with the owner's verdicts. This is the independently audited baseline.
- **Per pair** (`cd4ea04e`). Each proposal and sample carries `repeat_verdict`, so the
  owner sees which proposals the judge did not reproduce.

**Tests.**
- The default dry run plans 2 calls for one pair, and one pair counts against the caps.
- A judge that flips on the repeat gives a disagreement rate of 1.0, without changing
  the decisions.
- Three ledger rows with passes `[1, 1, 2]`.
- An owner `clean` against an LLM `reveal` reads `llm: compared 1, disagree 1`.
- `--repeat-sample 0` plans no repeat.
- The test helper defaults to no repeats, so older tests keep per-pair call counts.

### F7: subscription dollars without an owner price (rejected)

Codex's scenario is accurate: without `--price-per-million`, a Codex run reports
tokens and `estimated_usd: null`. It is rejected for three reasons:

1. **It is the shared, merged rule.** `ai.spend.subscription_usage_estimate`, built in
   the Slice A integration 2-3 fix (its F3, merged on `main` and Codex-reviewed), prices
   subscription receipts only with an owner price. Its review records: "A dollar figure
   appears only with `--price-per-million`." Every subscription command follows it:
   families propose, `field classify-questions`, `eval --prepare-llm` and `diagnose`. A
   T4-only rate would make this one command disagree with the rest. Changing the shared
   helper is outside this stage.
2. **No declared Codex price exists.** `KNOWN_PRICES_PER_MILLION` names only the
   embedding model, and the ChatGPT subscription has no per-token price. A hard-coded
   "API-equivalent" rate for `gpt-5.6-sol` would be a hand-set guess presented as an
   estimate, against honest labels.
3. **The rule is already met.** Slice A §5 rule 6 asks that cost and tokens be
   estimated from reported usage (falling back to input plus output), shown in the dry
   run, and recorded as `estimated_only`. All of that holds. Dollars appear when the
   owner gives a rate.

**Strengthened tests** (`21908854`). They now check numbers, not just the label:
- `test_a_subscription_route_runs_without_a_price_and_records_estimated_cost` asserts
  `estimated_total_tokens == 30` from `reported_usage`.
- The new `test_a_priced_subscription_run_records_a_numeric_estimate` asserts a numeric
  dry-run `estimated_usd` (planned tokens × rate) and a receipt `estimated_usd` of
  30 × rate.

Open question 1 asks whether a shared estimation rate is wanted.

## Codex's "claims that don't hold"

- **"Reruns never pay twice" and per-pair persistence:** now true (F1).
- **Math answers always get the symbolic check:** function expressions now do (F5).
- **Default Codex runs estimate cost:** tokens yes, dollars only with an owner price
  (F7, rejected with reasons).
- **The report supplies the evaluation baseline:** historical reader coverage (F4) and
  the noise floor with the owner audit (F6) are added.

## Manual runs (fixtures-local backup-API copies only)

All runs used this worktree's `fixtures-local/` copies, made by the stage with
`copy_tree_with_databases`. Nothing touched `fixtures/linear_algebra`,
`fixtures/probability` or `fixtures/arxiv_v2`.

**1. Dry run on `t4-real-linear_algebra`** (Codex judge route, embeddings from the
stage).
- Status `dry_run`, with the database sha256 unchanged.
- 15 requests: 10 pass-1 and 5 pass-2.
- 65,216 tokens by the byte bound; `estimated_usd` null (subscription, no price).
- Tutor shortlist: 10 pairs, all `bound`. 9 had rank ≤ 3, 4 had today's lexical rule,
  and 6 were embedding-only.

**2. Real run on the same copy.**
- **Calls:** 15 Codex calls, 30 receipts, all `completed` and `estimated_only`, on
  `gpt-5.6-sol`. Reported usage was 157,985 input and 1,549 output tokens, in 1 min 23 s.
  New ids meant the first build's verdicts were not reused.
- **Pass 1:** 4 reveals and 6 clean (flag rate 0.4), all `shadow_only`. That gave four
  `reveal_debit` proposals, each with live amount 0.0.
- **Noise floor:** 5 pairs, 2 disagreements (rate 0.4). Both are pass-1 reveals, so the
  two proposals affected carry `repeat_verdict: clean`.

  The ledger also holds the first build's verdicts under the same input hashes. That
  gives a third view of these pairs:

  | Pair (event id tail) | First build | Pass 1 | Pass 2 |
  |---|---|---|---|
  | `WBPDCM` | reveal | reveal | reveal |
  | `B1RQPZ` | reveal | reveal | — |
  | `PHG62R` | clean | reveal | clean |
  | `AV0F44` | clean | reveal | clean |
  | the other 6 | clean | clean | clean (2 repeated) |

  The two reveals the stage reported reproduce. The two new ones are judge noise: each
  is a single pass against two clean ones. This is the variability F6 asked the report
  to show.

**3. Rerun.** All 15 verdicts cached: 0 calls, `charged` all zero.

**4. Dry runs on the other copies.** Each left the database unchanged.

| Copy | Result |
|---|---|
| `t4-linear_algebra` (unmigrated, schema 155) | 15 pending |
| `t4-fake-linear_algebra` | 15 pending |
| `t4-arxiv_v2` | Nothing to judge |
| `t4-probability`, `t4-fake-probability` | Refused by the CLI's existing guard: "Vault has 1 validation issues" |

The probability refusal is a multi-line mapping key in
`subjects/counting/practice-items/pi_exercise_01kyn22qcffk7sae9ttxvz4j5n.yaml`, line 32.
It is byte-identical to the tracked fixture in this worktree and was not touched here.

No copy has assessment reservations or exam-role sources, so F4 and the exam path are
covered by tests only.

**Spend this step:** 15 Codex subscription calls; no metered (OpenRouter) call; $0.

## Gate

Run on `cd4ea04e` (code and tests final; the commit after it adds only this file),
clean tree.

| Check | Result |
|---|---|
| `uv sync --extra dev` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 10 kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **7,149 passed**, 14 warnings, 207.5 s |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **66 passed**, 7,083 deselected, 35.9 s |
| T4 tests (`test_contamination_report.py` 35, `test_contamination_symbolic.py` 38) | 73 passed |
| `test_cli_help_snapshot.py` (snapshot regenerated for `--repeat-sample`) | 1 passed |
| `db_validate_reference.py` | 0 errors (no schema or config change, so no regeneration) |

Not applicable: frontend and mobile (untouched); no migration.

## Notes and deviations

1. **Tutor cost scales with answered turns.** Each turn is one judge call, plus the
   noise floor. `--max-calls` (default 500) still bounds a run. `--top-k` no longer
   narrows the tutor detector; it sets only the rank signal. To narrow a large run, use
   `--detector` and the caps, not `--top-k`. This replaces the stage file's advice to use
   `--top-k 1`.
2. **Earlier verdicts on the copies are not reused.** Judgment ids changed, and so did
   the symbolic version (v1 verifier rows are ignored). The owner has not run the report
   on a live vault, so no owner data is affected.
3. **After a reservation changes, run `contamination embed` first.** A new reservation
   or a render adds a `surface/statement` record. Without it the reader index is
   `incomplete`, and the reader falls back to the floor and the symbolic check.
4. **The verifier link is textual and conservative.**
   - A reply that writes the item's expression differently (for example "12 x 12", where
     `x` reads as a symbol) does not link, so the judge decides.
   - A symbolic answer's rounding, or a reply that only restates it, never decides.
5. **`docs/reviews/slice-2-t4.md` describes the build before these fixes.** Where it
   differs on the tutor shortlist, the verifier rule, reader scope or judgment ids, this
   file supersedes it.

## Migrations

None. Schema head stays 168. No table, no DERIVED replay, no config field.

## Open questions

1. **Subscription dollars (F7).** Should all subscription commands share one configured
   API-equivalent rate (say `ai.spend.subscription_price_per_million`) so that every
   receipt carries a dollar estimate? That would change `ai/spend.py` for every command,
   not only T4.
2. **Noise-floor size.** The default is 5 pairs per detector. On the real copy, 2 of 5
   pairs flipped. Should a live switch need a larger floor? Should it require two
   agreeing passes before a `reveal_debit` or `burn_reserve` is executed? (The second is
   the PF auto-accept pattern.)
3. **Owner verdicts.** These are still recorded only by direct ledger writes (stage open
   question 2). `owner_audit` stays at 0 until a `contamination verdict` command exists.

## Re-review (Codex, 2026-10-12)

Codex job `20261012-130213-5MVsaq`, verdict REOPENED. It confirmed the F1 fix and raised
two Medium regressions in the F2 verifier link. Both reproduced on `e146182e` before
the fix: F8 returned `decides=True` and F9 returned `decides=False`.

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Identical-text pairs shared one judgment id | Confirmed fixed (no change this step) | `21908854` | `test_contamination_report.py` (pair and pass identity, resume filtering) |
| F8 | Medium | A different equation can become an authoritative reveal | Fixed | `122621c1` | `test_contamination_symbolic.py::test_a_relation_that_does_not_hold_for_the_item_never_decides` (4 cases; 3 failed before the fix) |
| F9 | Medium | Earlier occurrences suppress a later valid symbolic reveal | Fixed | `122621c1` | `test_contamination_symbolic.py::test_an_earlier_occurrence_does_not_hide_a_later_worked_equation` (3 cases; 2 failed before the fix), `::test_repeated_sides_are_compared_once` |

**F8 fix.** The item's expression in the reply's equation must itself be verified
equal to the expected answer, by the same comparison as the answer side. Only then does
the equation establish the item's answer.
- `x + 1 = 2` for "Solve x + 1 = 3" shares the fragment `x + 1`, but `x + 1` is not
  equal to 2, so the pair is only shortlisted.
- A wrong relation (`12 * 12 = 124`) holds the item's expression but does not hold, so
  it is also only shortlisted.
- Both now go to the judge, and an LLM `clean` stands.
- Solve-type items whose answer is a variable's value therefore never link. The judge
  decides them, as it did at the base commit.

**F9 fix.** The global `seen` set is now a cache from side to comparison result. Each
distinct side is still compared once (bounded work, and `checked` counts distinct
sides). Every equation reads every cached result, so "Read page 144. Then 12 * 12 = 144."
decides again. The F8 check reads the same cache, so it makes no extra SymPy calls.

**Label.** The decision rule changed, so `SYMBOLIC_VERSION` moves to
`contamination-symbolic-v3`. Verifier ledger ids hash the version, so v2 verifier rows
(including any false F8-type reveal written by the earlier build) are never consulted.
New verifier verdicts are written under the v3 label. Earlier verdicts from the LLM
judge are unaffected.

**Manual check (no paid call).** `contamination report --dry-run --no-judge` on
`fixtures-local/t4-real-linear_algebra`:
- status `dry_run`, `symbolic_version` v3;
- the database sha256 was unchanged;
- the tutor detector had 0 math pairs, so the verifier is not exercised on any copy.

F8 and F9 are covered by tests only. Spend this step: 0 calls, $0.

### Re-review gate

Run on `122621c1` (code and tests final; the commit after it adds only this section),
clean tree.

| Check | Result |
|---|---|
| `uv sync --extra dev` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 10 kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **7,157 passed**, 14 warnings, 201.3 s |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **66 passed**, 7,091 deselected, 35.5 s |
| T4 tests (`test_contamination_symbolic.py` 46, `test_contamination_report.py` 35) + `test_cli_help_snapshot.py` 1 | 82 passed |
| `db_validate_reference.py` | 0 errors (no schema or config change) |

Not applicable: frontend and mobile (untouched); no migration. Schema head stays 168.
