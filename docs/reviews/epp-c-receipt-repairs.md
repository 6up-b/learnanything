# EPp, third part: receipt repairs

Base `f44283f88e`, branch `ep/epp-c-receipt-repairs`. SR-2 and SR-3 are implemented;
EPp-1 is stopped at the explicitly requested scorer-safety check. No migration,
table, config key, algorithm tag, kill switch or prompt changes. No existing
receipt, assignment or ledger data row is updated. No staging or commit performed.

## SR-2: unknown router propensity

Previously `daily_plan.slot_facts.for_slot` changed an absent propensity to 1.0.
It now passes None through `ad_slot`'s request. Existing `decide_slot` behavior
already records NULL router and pair propensities for that case. A supplied
numeric propensity, including a deterministic 1.0, remains the supplied number.
No new determinism inference is made from the presence or absence of a decision id.

The neutral wire contract is explicitly **slot_facts_v2**. Its only value-domain
change is nullable `router_propensity`; the dataclass default is now None, and the
encoder writes JSON null. The decoder accepts v1 and v2, requires a finite number
for v1, and preserves the decoded version and numeric value. Historical v1 1.0
records still mean exactly what they meant before; they are neither reinterpreted
as unknown nor rewritten. Unknown versions and v1 null are rejected.

Tests in `tests/test_epp_receipt_repairs.py` cover nullable round trips, legacy
0.0/0.37/1.0 records, retained v1 encoding, and the version boundary. The actual
`ad_slot.decide` path is observed in two frozen-clock AD journeys using
`tests/epp_snapshot_helpers.py`: old numeric v1 facts (1.0 and 0.37, separately)
versus new unknown facts produced by the real `for_slot` from a block without a
router decision. Served responses are equal. Every table is compared, with only
`ad_selections.router_propensity` and `pair_propensity` allowed to differ on slot
rows; commission rows are compared unchanged. This includes selection ids, seeds,
uniforms, support, item choices, receipt hashes, `z_v1` inputs, AD state/trace and
score rows. The shared helper normalizes only decision-record wall-clock stamps
and warms up process-level initialization before comparing copies.

## SR-3: conditional redraw receipt

Previously the assignment retained its original item's probability, but the
placement recorded only `item_how = redrawn_in_pool`. A new redrawn placement
adds `ro5_check.redraw` to the existing `item_planned` detail:

| Field | Meaning |
| --- | --- |
| `candidate_ids` | Actual eligible pool intersection in draw order, without sorting |
| `u` | The existing uniform used to choose the replacement |
| `conditional_propensity` | 1 / length of that pool |
| `original_item_id` | The original assignment's item |
| `replacement_item_id` | The item selected by the redraw |

The original assignment, topic propensity and original `item_propensity` remain
unchanged. The top-level `replaced` still means the displaced chooser slot; it is
separate from the original check item. Placements without a redraw have no new
key. No extra uniform, id or seed is drawn. Old placements remain readable and
are not backfilled; their omitted redraw information remains unavailable.

The direct placement test uses ordered candidates `c, outside_pool, b, a`, with
the outside item absent from the plan pool. It reconstructs the replacement
solely from a JSON round trip of the placement, verifies 1/3, checks exactly one
uniform call, and compares all assignment rows before/after. No reconstruction
query reads current eligibility.

The frozen-clock full plan journey compares the new code against the frozen
pre-repair `place` implementation from the base, in
`tests/epp_receipt_repairs_helpers.py`. A synthetic historical assignment names
an item absent at administration; real eligibility and the engine's pool supply
its replacement. Fake model adapters, a fixed runtime clock, counting ids and
joined carried valuations remove timing races. Every table is compared after
removing only the newly appended redraw member from new placement events (and
normalizing the shared helper's decision-record wall-clock stamp). Presentations
and subsequent objective traces must exist. Thus served items, later decisions,
all stored seeds/uniforms, ids and old assignment values agree.

## EPp-1: stopped, scorer contract blocks the repair

`scheduling/forecast_receipts.py:212` still raises on unreadable input. No clamp or
writer change has been made; the earlier strict xfail and batch-drop
characterization remain in `tests/test_epp_prediction_snapshots.py`.

The required reader inspection found a contradiction between documentation and
behavior. `adaptive_difficulty/scoring.py:88` calls `valid_for_serve`;
`scheduling/forecast_receipts.py:158` calls `parse_utc` without catching its error,
and `clock.py:38` raises ValueError on unreadable text. Such a bound receipt is
**neither excluded nor marked invalid: scoring raises** before reaching the
invalid-row append at `scoring.py:89`.

`test_epp1_stop_condition_scorer_raises_on_unreadable_time` first scores a real
synthetic AD journey successfully, then appends a copy of one bound receipt with
`inputs_as_of = !not a time` (which satisfies the existing lexical SQL check),
and proves that the actual `score_rows` raises. No old test receipt is changed
and no constraint or trigger is bypassed. Clamping that text to issue time could
instead make it scoreable, because the scorer does not inspect snapshot
validity. The requested unchanged-reader proof therefore cannot be made within
the authorized scope. A reader-policy decision is needed before repairing this
item; it is not marked fixed in the bug ledger.

## Validation and pins

All Python checks use the supplied `t.sh`/`py.sh` wrappers. Pytest uses explicit
files and at most two workers. **No pins moved**: identity tests pass without
regeneration. No SlotFacts shape pin is registered at this tip; no exception to
the existing identity pins was needed. No goldens were changed.

The first regression run preceded all production edits: `9 failed, 4 passed`.
It exposed the missing nullable version, unknown-propensity fallback and redraw
record. It also exposed harness issues: commission rows have no router slot;
the objective runtime's elapsed clock needed freezing; and malformed text must
sort before `created_at` to pass the existing SQL check. After correcting the
harness and implementing SR-2/SR-3: `13 passed in 15.44s`.

The intermediate focused runs were `3 failed, 10 passed in 11.29s` (commission
rows and runtime elapsed-time differences), then `1 failed, 12 passed in 9.01s`
(the runtime belongs to the supplied fake runtime, not the PlanPolicy wrapper).
These were harness corrections; the production repairs did not change between
those runs and the passing run.

`MATCHED` below means exactly these 28 explicit files (one chunk, below the
30-file limit), matching the requested filename filter:

```text
tests/test_epp_prediction_snapshots.py
tests/test_epp_receipt_repairs.py
tests/test_forecast_receipts.py
tests/test_forecast_receipts_landing.py
tests/test_placement_diagnosis_decides.py
tests/test_placement_fixture_copies.py
tests/test_placement_opening_probes.py
tests/test_placement_report.py
tests/test_placement_sidecar.py
tests/test_placement_signals.py
tests/test_placement_split_grades.py
tests/test_placement_unevidenced_return.py
tests/test_reader_question_note_id_placement.py
tests/test_ro5_calibration.py
tests/test_ro5_checks.py
tests/test_ro5_codex_rereview.py
tests/test_ro5_codex_review.py
tests/test_ro5_landing.py
tests/test_ro5_picks.py
tests/test_ro5_stop_coin.py
tests/test_ro5_successor.py
tests/test_ro6_codex_rereview.py
tests/test_ro6_codex_review.py
tests/test_ro6_landing.py
tests/test_ro6_learned_tail.py
tests/test_ro6_serving.py
tests/test_ro6_successor.py
tests/test_ro6_tail_data.py
```

`GUARDS` means exactly `tests/test_identity_pins.py`,
`tests/test_structure_ratchets.py`, `tests/test_public_tip_guards.py`,
`tests/test_test_layout.py`, `tests/test_architecture.py`, and the additional
changed-contract check `tests/test_ad23_inversion.py` (six explicit files).

| Command through supplied wrapper | Last result line |
| --- | --- |
| `t.sh tests/test_epp_receipt_repairs.py -q -n 2` (before production edits) | `9 failed, 4 passed in 13.34s` |
| `t.sh tests/test_epp_receipt_repairs.py -q -n 2` (after fixes) | `13 passed in 15.44s` |
| `t.sh MATCHED -q -n 2 -m 'not arc_close'` | `326 passed, 12 skipped, 1 xfailed in 136.53s (0:02:16)` |
| `t.sh GUARDS -q -n 2 -m 'not arc_close'` | `485 passed in 38.16s` |
| `py.sh ruff check` | `All checks passed!` |
| `py.sh lint-imports --no-cache` | `Contracts: 45 kept, 0 broken.` |
| `py.sh python <temporary inclusive-ratchet script>` | `Ceilings exceeded including new tests: {}` |
| `git diff --check` | clean (exit 0, no output) |

The structure sweep normally reads only tracked files. Since staging is
prohibited here, an additional temporary driver ran the same sweep with the two
new test files included in its inventory, compared every ceiling with the
committed golden, and found no excess. `private_patch_sites = 465` and
`source_text_assertions = 23`, unchanged. The script only extends the file list;
it does not change a measure or threshold. The committed landing gate must also
run after the orchestrator stages the new files.

The 12 skips are the owner-vault cases in
`tests/test_placement_fixture_copies.py`; that lane remained disabled. The one
xfail is the existing EPp-1 unreadable-time test. **No socket tests were blocked
or omitted from this selected set**; no socket failure occurred.

## Not verified

No full suite, arc-close gate, durability lane, owner data, network or real model
calls. No EPp-1 implementation or successful unreadable-batch survival is claimed.
The orchestrator owns staging, commits and the landing gate. The untracked build
sheet was read only and is not part of this change.
