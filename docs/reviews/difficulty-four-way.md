# H2: the four-way difficulty replay

Refactor step H2 (`docs/specs/refactor_strategy_v3.md` §2.11; owner decision 11, run now by the owner's call of
2026-11-20). Before anything retires the old difficulty scalar (`PracticeItem.difficulty`,
`LearningObject.difficulty_prior`, `pf_candidates.difficulty`), one replay shows what it does today. H3-H6 are
decided from this report. FSRS's D (`practice_item_state.difficulty` and its siblings) is a different quantity and
is not touched.

H2 changes no `src` code, adds no migration, changes no config default and makes no model call. It is
`scripts/difficulty_four_way.py`, its tests (`tests/test_difficulty_four_way.py`) and this record.

## Running it

```bash
uv run python scripts/difficulty_four_way.py <vault copy> --out <private.json> [--as-of 2026-11-23T00:00:00Z] \
    [--top-k 10 --top-k 25] [--scratch <dir>] [--ad-without-z-llm]
```

- Run it through the scratch wrapper (empty `HOME`, `CODEX_HOME` and config dir) on a **backup-API copy** of a vault
  (`learnloop.db.copies.copy_tree_with_databases`). It refuses a path under `~/learnloop-vaults` or
  `~/learnloop-retired`, and an `--out` inside the vault copy.
- The JSON holds per-row values and ids. It is private: never commit it, never paste it into a tracked file.
  stdout prints counts and summary statistics only (no id, no item text; a test checks this).
- `--as-of` is the instant the due queue is read at (default: now, UTC). Use one instant for every vault you
  compare.
- It loads the vault with `load_environment=False`, so no dotenv or global settings are read.

## The arms

| Arm | Config | Surprise reads |
|---|---|---|
| `a_today` | the vault's own | the label's IRT `b`, as today |
| `b_label_off_mastery` | `mastery.irt.difficulty_from_prior=false` | `b = difficulty_default` (the switch sends every reader of the IRT seam there) |
| `c_surprise_from_ad` | the vault's own | adaptive difficulty's predictive for the item (below) |
| `d_both` | as (b) | as (c) |

Every arm is reported against (a), not against the stored state: the stored rows carry history (older tags,
older code) that a replay at today's code does not reproduce, and that difference is not the label's.

## How each arm runs

1. The input copy's databases are hashed (main file, then its `-wal`; the `-shm` is an index and is left out).
2. The input is copied once more into a scratch directory (databases through the backup API) and loaded from there.
3. Each arm is one ordinary shadow rebuild (`learnloop.substrate.shadow_rebuild.shadow_rebuild`) of that scratch
   vault with the arm's config assignments. The shadow rebuild backs the scratch database up into its own
   temporary file, replays the whole history there with `rebuild_all_derived_state`, and checks the scratch
   database's hash is unchanged. So arm (a) *is* a plain shadow rebuild, which a test also checks row for row.
4. The shadow rebuild's observer reads the replayed copy: `learning_object_mastery`, `attempt_surprise`, the
   stored due dates (`practice_item_state`, `activity_card_state`) and the due queue
   (`scheduling.scheduler.read_due_queue` at `--as-of`, which writes nothing). It also loads adaptive difficulty's
   replay events and records their fingerprint.
5. After the last arm the input's databases are hashed again; any change fails the run.

## Adaptive difficulty's predictive, per attempt

Arm (c) needs, for every attempt the mastery replay grades, AD's predictive success as it stood **before** that
attempt. AD's observer hook (`adaptive_difficulty.replay.run(observer=...)`) fires only before attempts AD trains
on, and a repeat trains nothing, yet repeats are where surprise matters most. So the script replays the prefix of
AD's own event stream (claims, reading opportunities, attempts, in AD's own order) up to each attempt and reads
`predict(subject_view, spec, warmth)`'s `p̄`. Attempts with nothing state-changing between them share one prefix
replay. A test checks that for every trained attempt the prefix replay gives exactly what AD's own observer gives.

- **The view:** the subject view (its mixture over the hyperparameter grid), which serving reads.
- **The quantity:** `p̄ = P(Y = 2)`, AD's forecast event (an unassisted success), the item-conditioned predictive
  `P(y | z, item)` with the item's features, signals and loadings. With `--ad-without-z-llm`, `z_llm` is dropped
  from every item's signals first.
- **AD's events are the same in every arm.** AD reads the ledgers, receipts and content, never mastery or
  surprise, so the predictive is computed once, on arm (a)'s replayed copy. Each arm's observer records the
  fingerprint of AD's events; the report's `events_identical_across_arms` says whether they agreed.

**The cold-item rule** (the strategy's "AD's population-level predictive where AD has no cell; if even that is
absent, `b = difficulty_default`"), as tiers recorded per attempt:

| Tier | When | What surprise reads |
|---|---|---|
| `item` | AD can read the attempt and the item's cell (primary facet, capability) exists in the subject view | AD's `p̄` |
| `population` | AD can read the attempt but has no cell for it yet | AD's `p̄`, which then reads the cell's population prior through AD's own projection (a coupled cell through its regression on the observed ones) |
| `default` | AD cannot read the attempt (no item spec: inputs excluded or no facet weights; an attempt type AD never reads; AD's material view unavailable) | `b = difficulty_default`, the structural "no label" value |

## Surprise from AD (arm c), and the firewall

The grade path computes mastery and surprise from one IRT `(a, b)` (`attempts/attempts.py`, `_belief_update`).
Inside arm (c)'s scratch replay only, the surprise alone is handed

    b' = μ_prior − logit(p̄) / a

the `b` at which the 2PL link at the prior mean equals AD's `p̄`. Its innovation, predictive variance, direction
and interval factor are then the usual formulae around AD's prediction; mastery keeps its own `b`. A primed attempt
takes the same priming offset on `b'` that the label's `b` takes. `b'` is not clamped to `b_abs_max`: clamping
would move the prediction off AD's.

**Firewall note.** AD feeding a stored surprise row is what the firewall's A2 and A12 forbid today, and
`spec_router_objective_v1.md` §11 says so. Arm (c) is the experiment the owner rules on, so it exists only inside
the script: a context manager swaps the grade module's `_belief_update` and `compute_surprise` for the length of
one shadow rebuild of a discarded scratch copy, and restores them on exit. Nothing in `src` changes, nothing is
written to the input, and no surprise row AD fed outlives the run. If the owner rules no, surprise reads `b` from
the EB posterior or the default, and (c) drops out (strategy §2.11).

The swap relies on two private names in the grade module. If either moves, the tests fail (they check every
replayed attempt went through the swap and that the stored prediction equals AD's).

## Reading the output

Per arm, against (a):

- **Mastery** (`learning_object_mastery`): rows changed (logit mean or variance), and the distribution of the
  arm's logit means and variances and of the per-LO shifts (n, mean, variance, min, p10, median, p90, max).
- **Surprise** (`attempt_surprise`): rows changed (predictive or Bayesian surprise, direction, interval factor),
  direction transitions (`positive->none`, ...), the arm's predicted correctness and its shift, and the shifts in
  predictive and Bayesian surprise.
- **Due dates** (stored): moved, earlier, later, and the shift in days. **At or above mvp-0.46 the FSRS interval
  carries no surprise factor** (`scheduler.surprise.remove_interval_factor`, on by default), and FSRS's review
  does not read mastery or the label, so no arm should move a stored due date there; the report says
  `interval_factor_removed`. A vault with that switch off would show (c) moving due dates through the factor.
- **The due queue** at `--as-of`: length, items entering and leaving, top-k overlap, and Spearman and Kendall
  rank correlation over the items both queues hold. The queue ranks by mastery and by the scheduler's own reads
  of the IRT seam (practice information), so (b) moves it twice: through mastery and directly. It reads no
  surprise, so (c) should leave it exactly as (a) (a test checks that); (d) moves it as (b). The queue includes the
  scheduler's seeded exploration over its candidate set, read as serving reads it.
- **AD's scoring**, once (it is the same in every arm): prequential log loss and Brier on AD's forecast event for
  every attempt AD trains on, with `z_llm` as served and with it out, split into the first attempt on an LO and
  later ones, the count of trained attempts that carry `z_llm` (items whose label is an LLM estimate, or frozen
  serve inputs that recorded one), and the size of the shift in `p̄`.
- **Tiers**: how many replayed attempts took AD's `item`, `population` or `default` prediction.

## Verification

`tests/test_difficulty_four_way.py`, on a synthetic vault built from `tests/helpers.py` (the placement vault, a
second facet, two LLM-estimated labels, twelve graded attempts with repeats and one primed retry):

- every arm runs on scratch copies and no file of the input changes, appears or goes;
- arm (a) equals a plain shadow rebuild read the same way, and (a) and (b) run without the swap;
- (b) moves mastery and surprise;
- (c) leaves mastery and the queue exactly as (a) and moves surprise; (d)'s mastery is exactly (b)'s; in (c) and (d)
  every stored predicted correctness equals AD's `p̄` (the primed retry: `p̄` shifted by the priming offset);
- with no AD prediction at all, (d)'s surprise rows equal (b)'s (the `default` tier is `difficulty_default`);
- no arm moves a stored due date at the head;
- the prefix replay predicts every trained attempt exactly as AD's own observer does;
- AD's scoring changes when `z_llm` is dropped, and the events are identical across arms;
- stdout holds no attempt, item or LO id and no prompt, the JSON holds the values, and an `--out` inside the
  vault copy is refused;
- no model client is constructed (the client factories raise).

## Results on a synthetic vault

The tests' vault, `--as-of 2027-01-15T00:00:00Z --top-k 3 --top-k 10`, at mvp-0.67 (4 LOs with mastery rows, 12
attempts, 9 queue items). These numbers say only that the machinery moves what it should; they say nothing about a
learner.

| | (b) label off mastery | (c) surprise from AD | (d) both |
|---|---|---|---|
| Mastery rows changed | 3 of 4 | 0 of 4 | 3 of 4 |
| Logit-mean shift, median (max) | −0.115 (0.000) | 0 | −0.115 (0.000) |
| Surprise rows changed | 12 of 12 | 12 of 12 | 12 of 12 |
| Direction transitions | 1 (`positive->none`) | 1 (`positive->none`) | 1 (`positive->none`) |
| Predicted-correctness shift, median | +0.059 | +0.108 | +0.108 |
| Stored due dates moved | 0 of 9 | 0 of 9 | 0 of 9 |
| Queue top-3 overlap | 2 of 3 | 3 of 3 | 2 of 3 |
| Queue Spearman / Kendall (common items) | 0.567 / 0.444 | 1.0 / 1.0 | 0.567 / 0.444 |
| Surprise tiers | n/a | item 10, population 2 | item 10, population 2 |

AD's scoring (8 trained attempts; 4 repeats excluded as `repeat_surface`; 2 carry `z_llm`): log loss 0.852 with
`z_llm`, 0.824 without; Brier 0.318 and 0.307; mean `|Δp̄|` 0.014, max 0.044. The run took about two seconds.

## What this does not cover

- The facet projections (`facet_recall_state` and the per-LO facet uncertainty) are not compared; the shadow
  rebuild's own `learnloop rebuild --shadow` reports them against the stored state if wanted.
- AD's `p̄` is the probability of an unassisted success, while surprise scores a fractional rubric score against
  its prediction. The IRT path makes the same comparison with its own `p`, so (c) keeps the form and changes only
  the prediction; whether surprise should compare against AD's expected category instead is H3's question.
- Other readers of the IRT seam that the replay does not rebuild (probes, lesson suggestions, teacher checks,
  delayed checks, placement, field baselines) are moved by (b)'s switch at serve time but are not reported here,
  except through the queue.
- Owner vaults: none was opened by the implementer. The section below is for the orchestrator.

## Judgment calls

1. **The cold-item tiers.** "AD has no cell" is read as "the item's primary cell has no coordinate in AD's subject
   view", where AD's own projection already gives the population-level prediction; "even that is absent" as "AD
   cannot read the attempt". The alternative reading (a population prediction that drops the item's features and
   signals) is a one-function change in the script.
2. **`p̄ = P(Y = 2)` mapped to an implied `b'`**, so surprise keeps its formulae and only the prediction moves;
   the priming offset applies on top; no clamp.
3. **AD's predictive keeps `z_llm` by default** in (c) and (d) (AD as it serves today); `--ad-without-z-llm`
   gives the H4 view. AD's scoring reports both either way.
4. **The comparison is against (a)'s replay**, never against the stored rows.
5. **The firewall crossing is a context-managed swap of two grade-module names inside the script**, not a hook in
   `src` (the bounds forbid one without the owner's word).

## Owner copies

*For the orchestrator: per vault copy, the date, the options used (`--as-of`, `--top-k`, `--ad-without-z-llm`),
whether the run completed and the input stayed unchanged, and that the private JSON was kept outside every
checkout. The numbers go to the owner privately; none goes in this file.*
