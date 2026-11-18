# Refactor E4: trace assembly leaves the chooser

Branch `refactor/e3-e4-chooser`, after E3 (its last source commit `4fa5f05bde`, record `5ec274b8d1`). Step E4 of arc E
(`docs/specs/refactor_strategy_v3.md` §2.7, leak 3). Structure track: no served or persisted value changes. Line numbers
in §1 are at E3's tip, in `src/learnloop/daily_plan/objective_chooser.py`.

## 1. Step 0: the trace's assembly at E3's tip

### What the step moves, its size and its callers

| Definition | Lines | Size | Called by | Reached by tests |
|---|---|---|---|---|
| `_trace` | 834-1025 | 192 | `_decide_objective` (1222), `ObjectiveRestraintGate._mixed` (1501) | — |
| `_offer_trace` | 773-824 | 52 | `_trace` | — |
| `_support_labels` | 692-707 | 16 | `_trace` | — |
| `_goal_dates` | 719-737 | 19 | `_decide_objective` | `test_ro5_codex_review` calls `OC._goal_dates` |
| `_score_note` | 710-716 | 7 | `_trace` | — |
| `_failure_rule_field` | 827-831 | 5 | `_trace`, `_decide_objective`'s record, `_mixed`'s record | `test_ih5_successor` imports and calls it |
| `_serving_switches` | 224-230 | 7 | `_trace` | — |
| `_decide_objective`'s trace assembly after `choose` | 1214-1249 | 36 | — | — |

All of them are pure: no thread, lock, process cache, database or clock. The one read in the write phase is
`J.carried_for` (the carry registry and `router_objective_traces`), which feeds only the trace. `_trace` knows every
kind of option: stop (its label), a lesson offer (its label and its `offer` section, `_offer_trace`), a block (its
label), and IH2's contest (`followup_contest`, in `_decide_objective`).

### Imports the module may not have

`router_objective/trace.py` may not import `daily_plan` (the contract `choose.py` lives under). What the moved code
takes from `daily_plan`:

| Name | Lives in | What the trace module does |
|---|---|---|
| `BlockCandidate` (annotations; `.subtype`, `.learning_object_ids`, `.est_minutes`, `.reading`, `.lane`, `.annotations`, `.item_ids`, `.candidate_id`) | `daily_plan/types.py` | reads the attributes; annotated `Any` |
| `NumericPolicy` (`.evaluation`, `.inputs`, `.sources`, …) | `daily_plan/objective_job.py` | reads the attributes; annotated `Any` |
| `ComponentResult` (`.status`, `.parsed`, `.model`, …) | `daily_plan/router_runtime.py` | reads the attributes; annotated `Any` |
| `STOP_FOR_TODAY` | `daily_plan/types.py` | `stop_coin.STOP` (the same string, already the router objective's) |
| `LESSON_OFFER_SUBTYPE` | `daily_plan/types.py` | repeated, held equal by a test |
| `OI.MISS_CAUSE_SOURCE` | `daily_plan/objective_inputs.py` | repeated, held equal by a test |
| `ANSWERED`, `NOT_READY` | `daily_plan/router_runtime.py` | `choose.py`'s copies (already held equal) |
| `_is_contest` / `FOLLOWUP_CONTEST_NOTE` | `daily_plan` | not needed: the chooser passes the contested ref it already computes |

None of the three types needs to move: the trace reads their attributes and constructs none of them. Where they
should live later: `BlockCandidate` and the plan's string constants belong with the plan (`daily_plan/types.py`), which
the router objective reads but should not import; a small shared `router_objective` types module would hold them if
E6 (an action is one place) gives each action kind its own definition there.

### The trace's fields and where each value comes from

Key order is the serialized order. **C** the `Choice`; **R** a read the chooser holds (the numeric policy's answer
`numeric`, the models' results, the weight, the seed, the LLM's card, the carry registry, the config, the clock's
`now_iso`); **K** a candidate's own fields; **S** the support the chooser built before the choice.

| Field | From |
|---|---|
| `residual` (when the numeric answer has one) | R `numeric.residual`; with it applied, each candidate's terms (`tail_serve.candidate_terms`) over R the evaluation's rows |
| `miss_cause` (when present) | R `numeric.sources["miss_cause"]` |
| `preference` (when present) | R `numeric.preference`, with V_pref at R the evaluation's rows |
| `candidates[ref]` | per option of S: `label` K (kind, subtype, LOs with R titles, minutes, section, lane); `kind`, `main_lo`, `minutes` R the numeric answer's action for it; `sensors` R the numeric inputs' topics and sources, the miss sensor, R the LLM's forecast for it; `terms` R the evaluation's row, `v`, stop's Q̄, the paired SE against the top; `split`, `branches` R the row's extras; `offer` (a lesson offer only) K its `lesson_offer` annotation with R the lesson curve and the row's branch terms |
| `reference`, `v`, `cutoff_days`, `precision` | R the evaluation (and `numeric.tie`) |
| `filtered` | K each feasible candidate outside S (its `reversible` annotation) |
| `stop_in_support` | S |
| `session` | R the numeric inputs (minutes, remembered minutes and source) and the session guard (R config, R remembered minutes) |
| `policies.llm`, `.decider` | R the models' results |
| `policies.numeric` | R the numeric answer |
| `policies.staged` | S staged's ref |
| `mixing` | R the weight (posterior, seeds, note, `w`); C `effective`, `drawn.pi` (μ), `drawn` (chosen, component, propensity, u1, u2); R the mix's seed; R config (ε, the failure rule) |
| `evaluation` | R the numeric answer's uses and baselines, R config (window), R `now_iso` (window close), R the price (c0), R config (the score note) |
| `frontier`, `inputs_sources` | R the numeric answer |
| `versions` | constants (objective, tail, terminal, LLM schema, review draw, AD link); R config (horizon); R the numeric inputs (memory model, learning source, κ, goals); R the card's version; R the switches the numeric answer was computed under |
| `learner_statements` (when the card has them) | R the LLM's card |
| `followup_contest` (IH2) | S the contested ref; K its item ids |
| `goal_dates` | R the numeric answer (dated uses, baselines, goals) |
| `carried_for` (when any) | R the carry registry and `router_objective_traces` |
| `mixing.drawn_chosen`, `.chosen`, `.propensity`, `stop_coin`, `evaluation.score` (under the coin) | C `drawn`, `served`, `coin` |

The router's record (`record.update(...)` after the trace) is built from C and R too; the chooser keeps writing it
(the brief: build the trace, write it, write the record, return the block).

## 2. What changed

**The module's name.** The brief names `router_objective/trace.py` as a new module, but that module already exists:
it turns a trace dict into the `router_objective_traces` row (`assemble`), reads it back (`explain`) and writes it
(`record`), and `tail_data` imports it. Putting the assembly there was tried and measured: the trace's own pieces import
`tail_serve` and `preferences` (function-locally), which import `tail_data`, which imports `trace`, so `trace` joined a
new four-module cycle (modules in any cycle 220 → 224). The assembly is therefore its own module,
`router_objective/trace_assembly.py`, beside `trace`, and the docstring says why they are apart. With it: largest
component 84 → 84, modules in any cycle 220 → 220, member lists identical, `trace_assembly` in no cycle.

Commits, in order:

1. `6f6dbb165e`: step 0 (§1), before any edit.
2. `8eb1c94b4d`: the move, the two ported calls (§5), the new test file and the structure golden.
3. `2c435c472a`: comments only, in the bodies that changed (no ruling, review or stage named). Stage-naming comment
   lines 2,362 to 2,354.
4. This record, the status row, the router note; then the regenerated references.

Mechanical edits by script (exact-pattern, each asserted to match once): the moved definitions copied from E3's tip's
exact line ranges, the chooser's moved definitions deleted by name, the write phase replaced, the two
`_failure_rule_field` calls and `_mixed`'s `_trace` call repointed; `ruff check --fix` removed the imports left unused
(`timedelta`, `math`, the module-level `stop_coin`). Every other change is an Edit.

### `router_objective/trace_assembly.py` (new, 426 lines)

| Definition | From (E3's tip) | Lines | Body |
|---|---|---|---|
| `_serving_switches` | `objective_chooser.py:224-230` | 7 | identical |
| `_score_note` | `:710-716` | 7 | identical |
| `goal_dates` | `_goal_dates` (`:719-737`) | 19 | identical but its name and its parameter's annotation (`Any`: the type is `daily_plan`'s) |
| `_offer_trace` | `:773-824` | 52 | identical but the candidate's annotation (`Any`) |
| `failure_rule_field` | `_failure_rule_field` (`:827-831`) | 5 | identical but its name |
| `decision_trace` | `_trace` (`:834-1025`) | 148 | changed: the per-candidate loop is a call to `candidate_row` (below) |
| `option_kind`, `option_label` | `_support_labels` (`:692-707`) | 8, 15 | changed: one option at a time, by kind, with a `match` |
| `candidate_row` | `_trace`'s loop body (`:854-907`) | 60 | the loop body, with the label and the offer section taken by kind |
| `objective_trace` | `_decide_objective`'s write phase (`:1215-1249`) | 41 | the same statements, in order (§3) |
| `STOP_FOR_TODAY`, `LESSON_OFFER_SUBTYPE`, `MISS_CAUSE_SOURCE`, `STOP`/`LESSON_OFFER`/`BLOCK` | repeated names, and the three option kinds | — | `STOP_FOR_TODAY` is `stop_coin.STOP` (the same string); the two others held equal to `daily_plan`'s by `tests/test_objective_trace.py` |

`ANSWERED` and `NOT_READY` come from `choose.py`, which already repeats them (held equal by `tests/test_choose.py`).
Nothing in it imports `daily_plan`; the candidates, the numeric answer and the models' results are read by attribute.

### `daily_plan/objective_chooser.py`: 1,811 to 1,473 lines

- Removed: the seven definitions above.
- `_decide_objective` after `choose` (84 lines to 62): the titles, the contested follow-up (`_is_contest`, which stays:
  the choice's support uses it), `J.carried_for(...)` when carries are on (else `[]`), then
  `T.objective_trace(choice, ...)`; then, as before, the router's record (`record.update(...)`, its `failure_rule`
  through `T.failure_rule_field`), the provenance, the coin's record fields and the `BlockChoice`.
- `ObjectiveRestraintGate._mixed`: `T.decision_trace(...)` for `_trace(...)` (same arguments), `T.failure_rule_field`.

## 3. Bodies that changed, and why

**`_support_labels` → `option_kind` + `option_label`.** The labels were computed for the whole support before the loop,
by a chain of `if` over stop, a lesson offer and a block. Now each option's row asks for its own: `option_kind(ref,
candidate)` (stop when the ref is stop's; none when there is no candidate; a lesson offer by its subtype; else a block)
and `option_label(kind, candidate, titles)` (a `match` on the kind, with the three old f-strings unchanged). A ref with no
candidate still gets its ref as its label (`candidate_row`'s `label if label is not None else ref`, the old
`labels.get(ref, ref)`). The one order the old code had that the new does not: an option whose ref is stop's and that
also has a lesson-offer candidate would have had the stop label and the offer section; no support holds such an option
(stop is never a candidate), and both are now decided by one kind.

**`_trace` → `decision_trace` + `candidate_row`.** The loop's body moved into `candidate_row` statement for statement;
the differences are the label (above), the offer section keyed on `kind == LESSON_OFFER` instead of
`ref in by_id and by_id[ref].subtype == LESSON_OFFER_SUBTYPE` (the same set), `numeric.inputs` read inside the row
instead of the loop's `inputs` (the same value), and the row built as a local before it is returned. `decision_trace`
keeps every other statement and the key order; `OI.MISS_CAUSE_SOURCE` reads the repeated name; the annotations that
named `daily_plan` types are `Any`.

**The write phase → `objective_trace`.** The same statements in the same order (the session guard, the common trace,
`learner_statements`, `followup_contest`, `goal_dates`, `carried_for`, the coin's fields), so the dict's keys are inserted
in the old order. Two inputs come from the chooser instead of being computed inside: `contested` (the support's IH2
follow-up, which needs `daily_plan`'s contest annotation) and `carried_for`. The carried-for read now happens just
before the trace is assembled instead of between `goal_dates` and the coin's fields; nothing in between reads or writes
the carry registry or the database (the guard, the trace and `goal_dates` are arithmetic on values already held), so the
read sees the same state, and P1's decision-path counts are equal.

## 4. The KEEP items and what pins each

| Kept | How | Pinned by |
|---|---|---|
| Every trace field, its key order and its value | the moved code and the per-row function insert the same keys in the same order from the same values | P1: every `router_objective_traces` row (the trace's canonical JSON), byte-equal on ten scenarios; `tests/test_objective_trace.py` (the key order of a trace and a row; each kind's label); `tests/test_ro4_objective_serving.py`, `tests/test_ro6_serving.py`, `tests/test_rofu_carried.py`, `tests/test_ih2_lessons_compete.py`, `tests/test_te3b_offers.py` (the offer section) |
| The router's record | built in the chooser as before; only `failure_rule_field`'s home moved | P1: `router_decisions` and `decision_records` byte-equal; `tests/test_objective_decision_record.py`, `tests/test_ih5_successor.py`, `tests/test_router_failure_records.py` |
| What `learnloop why` prints | it reads the persisted rows above | P1: `why <trace> --json` byte-equal on every run; `tests/test_why_cases.py` |

## 5. Tests added and ported

- **`tests/test_objective_trace.py`** (5 tests, no vault): the repeated names equal `daily_plan`'s; each option told apart
  by its own fields and labelled (stop, a block, a reading block, a lesson offer, a ref with no candidate); a trace with no
  numeric answer keeps its top-level key order, each row its own, and only the lesson offer's row has an `offer` section;
  a ref with no candidate is labelled by its ref; the failure rule's field. Fail-first: the module does not exist at E3's
  tip; by mutation, `candidate_row` labelling a candidate-less ref `None` fails
  `test_a_ref_with_no_candidate_is_labelled_by_its_ref`.
- **Ported (T4: they called the moved private names with plain values):** `test_ih5_successor` imports
  `trace_assembly.failure_rule_field` instead of `objective_chooser._failure_rule_field`; `test_ro5_codex_review`'s F7 test
  calls `trace_assembly.goal_dates` instead of `OC._goal_dates`. Assertions unchanged. No test patched a moved name.

## 6. Proofs

**P1. P-draw.** The same harness and scenarios as E3 (`refactor-e3.md` §7), tip = `8eb1c94b4d` (the later source
commit changes comments only). Base = E3's tip; its outputs are E3's tip runs (`13925e8bbf`, whose code equals
`4fa5f05bde`'s: that commit changed comments and docstrings only). Every table (the `router_objective_traces` rows with
their canonical trace JSON, `router_decisions`, `decision_records`), every prompt, every Decider call and
`why <trace> --json`, byte-equal after normalization on all ten scenarios (31 runs), and equal to `69befd0430`'s (E2's
tip) too. The decision path's connection opens and statements are equal on every scenario.

| Scenario | Runs | Against E3's tip | Against `69befd0430` |
|---|---|---|---|
| `both`, `coin`, `llm_fails`, `llm_fails_ih5_off`, `no_models`, `guard`, `evidence`, `offers`, `contest`, `early` | 3, 6, 3, 3, 3, 3, 3, 3, 2, 2 | identical, each | identical, each |

They reach every option kind's row (blocks, stop, lesson offers in `offers` and `contest`), the offer section, IH2's
`followup_contest`, `learner_statements` (none: the fakes' cards carry no statements, so that key's path is held by
`tests/test_ih4_preferences_inform_router.py` in the targeted run), `goal_dates`, `carried_for` (`no_models`, `early`), the
coin's fields (`coin`), the residual, and the mid-block gates' traces through `decision_trace` (`contest`).

**P2.** `tests/pinned_draws.py` and every router golden unchanged; `tests/test_identity_pins.py` 340 passed with nothing
written.

**P3.** Cycles with untracked files included: largest 84 → 84, modules in any cycle 220 → 220, member lists identical;
`router_objective.trace_assembly` in no cycle (its imports: `clock`, `router.requests`, `router_objective.{mix, price,
stop_coin, value, choose}`, `router_objective_switches`, and `tail_serve` and `preferences` inside functions). The
rejected placement in `trace.py` measured 220 → 224 (§2). `tests/test_structure_ratchets.py` passes; golden lowered:
stage-naming comment lines 2,362 → 2,354 (`objective_chooser.py` 23 → 15; `trace_assembly.py` 8 → 0 after the comment
commit, so it has no key). Functions over 200 lines: 71 → 71 (`_trace` was 192). `lint-imports --no-cache`: 43 kept.

**P4. Threads.** E4 touches no thread; the same ten thread files as E3 (`refactor-e3.md` §7), three times at `-n 3`: 196 passed each time, `tests/thread_guard.py` active.

**P5. AST identity** against `4fa5f05bde` (identifiers renamed where the move renamed them): `_serving_switches`,
`_score_note`, `failure_rule_field` identical; `goal_dates` and `_offer_trace` identical but for a parameter annotation
(`Any` for a `daily_plan` type); `decision_trace` changed (§3). `option_kind`, `option_label`, `candidate_row` and
`objective_trace` are the restructured `_support_labels`, loop body and write phase (§3).

## 7. Targeted gate

| Selection | Files | Result |
|---|---|---|
| `affected_tests.py --base 6f6dbb165e` over the diff (141), the brief's word list (`trace_assembly`, `objective_trace`, `_offer_trace`, `_goal_dates`, `failure_rule_field`, `router_objective.trace`, and E3's words), the rules block's files plus `test_why_cases` and `test_objective_decision_record`, every edited or added test file; three chunks of at most 52 | 153 | 2,742 passed, 9 skipped, 1 xfailed, 0 failed |
| After the comment commit: `test_structure_ratchets`, `test_identity_pins`, `test_objective_trace`, `test_architecture`, `test_test_layout`, `test_why_cases`, `test_ro4_objective_serving` | 7 | 391 passed |
| P4: the job's thread tests, three runs | 10 | 196 passed, three times |

`ruff check`: all checks passed. The four vault validators pass (`db_validate_reference` errors `[]`). `check_gate_partition.py`:
31,108 collected, landing 31,043 + arc_close 65 (the five new tests). References regenerated after the source commits
(a new note for `trace_assembly`); a second run changed nothing. Not run: the whole suite, durability,
`--fresh-connections`, `arc_close`; the owner lane (no owner-lane test edited).

## 8. Stop rule

Implementer: the same Opus session as E3, no subagents. Gate count for E4: 153 targeted files (2,742 tests) once, seven
files after the comment commit, the ten thread files three times, one P-draw sweep (31 runs). Removed from
`objective_chooser.py`: 338 lines (1,811 → 1,473); `_decide_objective`'s write phase 84 → 62 lines. Token use: not
visible from inside the session.

| File | E2's tip | E3's tip | E4's tip |
|---|---|---|---|
| `daily_plan/objective_chooser.py` | 2,233 | 1,811 | 1,473 |
| `daily_plan/objective_job.py` | — | 493 | 493 |
| `daily_plan/objective_seeds.py` | — | 100 | 100 |
| `router_objective/trace_assembly.py` | — | — | 426 |
| `_decide_objective` | 141 | 138 | 114 |

## 9. Judgment calls, and what E5 and E6 should know

**Judgment calls.**

1. **`router_objective/trace_assembly.py`, not `trace.py`.** The brief's `trace.py` exists (the row and `explain`) and
   would have joined a new import cycle with the assembly in it (§2). The two modules sit side by side: one builds the
   dict, the other stores and reads it.
2. **One row function with the option's kind, not a function beside each candidate's definition.** The candidates are
   `daily_plan.types.BlockCandidate` (stop has none), which this module may not import; so `candidate_row` takes the
   option's own fields and `option_kind` tells stop, a block and a lesson offer apart by them, with one plain `match` for
   the label. The rows' common part (sensors, terms, split, branches) is the same for every kind; only the label and the
   offer section differ.
3. **The router's record stays in the chooser**, as the brief's sequence says (build the trace, write it, write the
   record, return the block); `contested` and `carried_for` are passed in, so the module needs no `daily_plan` name and
   makes no read.

**For E5 (the objective apart from the rollouts).** The trace reads the numeric answer by attribute (`evaluation`,
`inputs`, `sources`, `baselines`, `residual`, `preference`, `switches`, `actions`, `tie`, `price`, `frontier`,
`corrected`, `stage`) and `V`'s version constants and `paired_standard_error`. If E5 renames or splits `value.py`, those
are the trace's dependencies; `V.REFERENCE_REF` and `V._Model` are the chooser's (`_policy_request`).

**For E6 (an action is one place).** The trace's per-kind code is now two small functions (`option_kind`,
`option_label`) and one branch in `candidate_row` (the offer section, `_offer_trace`). An action kind added by E6 adds a
`match` arm there and, if it has a section of its own, a branch beside the offer's. The chooser's per-kind code for the
LLM's options (`_offer_option`, `_contest_option`, `_option`) and IH2's `_is_contest` are still in the chooser.

## 10. Not verified

- The owner's copies (P-draw on synthetic vaults).
- `learner_statements` in a P-draw run (the fakes' cards have none); its key and position are held by the IH4 tests.
- The whole suite, durability, `--fresh-connections`, `arc_close`: the orchestrator's gate.
