# Figure wait estimate (successor mvp-0.58): build record

Branch `fix/figure-wait-estimate`, built on main `c3a940057c` (refactor arcs A and B closed). Built here; the
orchestrator gates and lands it. Found in refactor B4 (`docs/reviews/refactor-b4.md`, step 0).

## Owner decision (Nov 10, verbatim)

"W from pressed builds with a prior; cost from foreground minutes only."

## The bug

The figure pre-builder builds a figure ahead of need when one Thompson draw of
`EU = P(open) x W - C` is positive (`figures/prefetch_model.py`). W is the minutes a press would otherwise wait (the
quick tiers: the figure author call's measured duration); C is the chance of a usage-limit pause times the foreground
minutes a pause blocked. `figures/prefetch_ledger.py` meant to leave the pre-builder's own background calls out of
both, with `owner_kind NOT LIKE 'prefetch%'` (W) and `startswith("prefetch")` (the blocked minutes). No receipt's
owner kind starts with `prefetch`: a figure call's owner kind is the route's task (`figure_author`,
`figure_rich_author`, `figure_prefetch_judge`) for a press and a pre-build alike, so neither filter removed anything.

## As built

- **Whose call a receipt was** (`prefetch_ledger.call_build_modes`, `background_call`). Read from what the ledger
  records, verified on the copy below. The author's receipts are owned by
  `figure:<content_key({input_hash, generation})>` (`service.build_figure`), the generation being how many figures of
  that input were stored before the build (`store.builds_for_input` over `service.ALL_SPEC_VERSIONS`). So the k-th
  stored figure of an input (by `created_at, id`) names the owner of the build that stored it, and its building request
  (`interactive_figures.request_id`, never a later reuse's row, which only names the figure) carries `build_mode`. A
  rich figure's calls are owned by `figure_rich:<rich.content_key_for(payload)>` (the input, the quick figure it
  follows, the quick build's generation). The judge's calls are always background. A figure call no stored build names
  (a build that stored nothing and had no later build of that input) reads as foreground: see open items.
  Decision records (B4) carry the request key too, but a pass never reads records back (ADR-017), so they are not used.
- **W: pressed builds with a prior** (`prefetch_model.wait_estimate`, pure). On the log scale a press's call duration
  is N(mu, s^2). The spread `s^2` is the call's, which every call measures: the within-group pooled variance of the
  pressed calls and the other calls, each about its own mean, so a shift between the groups never widens it. The
  centre's prior is N(the other calls' mean, s^2 / k) with k = `WAIT_PRIOR_STRENGTH` = 1, so its posterior mean is
  `(k * others' mean + n * pressed mean) / (k + n)`; W is the log-normal mean `exp(mu + s^2 / 2)`, as before. With no
  press it is the other calls' log-normal mean, which is v1's W bit for bit; with no other call it is the presses'
  own. The rich tiers are unchanged (they already read pressed requests to their rich figures).
- **Where the prior's strength comes from.** The unit-information prior (Kass and Wasserman 1995): the prior is worth
  one measurement. Background calls time the same author call, so they seed the centre (the owner's rule: priors
  seeded, weights learned). How far a press's wait sits from them is not measured, and one group of presses gives no
  between-group spread to fit a strength from, so the prior claims the least information that still pins a centre.
  The presses' weight is learned as they come, `n / (n + 1)`, and the number of background calls never changes it.
  Registered as a prior (`figure_prefetch_model:WAIT_PRIOR_STRENGTH`, basis `unit_information`).
- **Cost from foreground minutes only** (`prefetch_ledger.blocked_basis`). The failures counted inside a pause window
  and the calls behind the mean latency are both foreground only (the judge's and pre-builds' calls left out).
- **The version** `prefetch_decision_v2` (`prefetch_model.MODEL_VERSION`; `MODEL_VERSION_V1` keeps the old name).
  Each decision row's `model_version` is the one it was decided under, and the posterior digest names it.
- **Records** (`figures/records.py`). Under v2 a `figure_prebuild` record's facts gain `wait_estimate_by_tier`
  (per quick tier `pressed_n`, `pressed_min`, `prior_n`, `prior_min`, `prior_strength`, `posterior_min`) and
  `blocked_basis` (`refused`, `background_left_out`, `latency_calls`, `pauses`), numbers only, so `learnloop why`
  shows them with the rest of the inputs. Under v1 the facts are as they were. The reader report's prefetch block reads
  the ledger as the decisions do (`model_version`, `estimate_by_tier`, `blocked_basis`).

## The successor (docs/algorithm-change-playbook.md)

1. **Persisted meaning.** The decisions' stored `sampled_eu` and `w_minutes` change, so it is a successor:
   `FIGURE_WAIT_ALGORITHM_VERSION = "mvp-0.58"` after slip or gap's mvp-0.57, one constant, `FIGURE_WAIT_VERSIONS`.
2. **Raw ledgers** untouched: nothing recorded is rewritten; old rows keep `prefetch_decision_v1`.
3. **Upgrade** `learnloop.figure_wait_upgrade`, the chain's next journalled link (a copy of slip or gap's with its
   names; the CLI and sidecar openers install its completion; the CLI's default target).
4. **Golden.** `tests/goldens/effective_defaults.toml` gains `algorithms.algorithm_version = "mvp-0.58"` and
   `figures.prefetch.pressed_waits = true`.
5. **Tables.** None new; no migration.
6. **Replay and rebuild.** `figure_prefetch_decisions` is a `RAW_LEDGER` and no replayer reads it (nor any figure
   table: the `evidence-never-reads-figures` contract); the posteriors are recomputed at decision time and never
   stored (spec §13.2b). So there is no replay to reproduce: a decision's version is on its row, and switching back
   reproduces v1's numbers for new decisions.
7. **Shadow check.** Rebuild derives nothing from these tables, so the copy run below stands in for it.
8. **Fixture.** No migration, so the head fixture is unchanged.

**The switch** `[figures.prefetch] pressed_waits` (default true; registry: structural/operational kill switch).
Off, or below the tag, `prefetch_decision_v1`: W, the blocked minutes and the posterior digest are v1's exactly.

## The owner's vault (copy of ~/learnloop-backups/20261109-copy/arxiv_v2)

A backup-API copy (`copy_tree_with_databases(database_names=("state.sqlite",))`) under the worktree's gitignored
`fixtures-local/`, deleted after. The copy is at migration 250. Counts and numbers only:

- `figure_author` receipts by build mode (from `call_build_modes`): pressed 2 completed; pre-build 20 completed and
  1 failed; none unowned. Figure receipts with an owner kind starting `prefetch`: 0. No rich receipts.
- **W, both quick tiers:** before (v1, and HEAD) 0.4827 min; after (v2) **0.5817 min** (pressed 2 calls, 0.6355 min;
  prior 20 calls, 0.4672 min; strength 1). The pressed-only figure B4 reported, 0.636 min, is the presses' own
  log-normal mean; v2 sits 2/3 of the way to it on the log scale.
- **Switched off equals HEAD:** W, counts, the waits summary and the posterior digest identical (HEAD's
  `prefetch_model.py` and `prefetch_ledger.py` loaded beside this branch's).
- **Decisions unchanged:** no pause has been measured (`plan_usage_pauses` empty), so the blocked minutes are None
  and the cost is 0 under HEAD and v2. Each of the 36 stored decisions' candidates, decided by HEAD's model and v2's
  from the same seed, 20 seeds: 720 of 720 identical in verdict, propensity, drawn p_open and rule; each pass's
  sampled-EU order identical in 340 of 340.

**Why no draw changes.** W enters only as a positive factor of `p_open x W` when the cost is 0; it never draws a
random number, so every pass consumes the generator identically, every draw's sign is the same, and the propensity
(the share of 64 further draws that build) is the same. The order a pass applies its caps in sorts by sampled EU, and
every trigger kind on this vault reads the same quick-tier W (its tier mixes are all `grammar`), so the order is the
same too. The router's draws never read the figure ledger, so no router draw is touched and no P-draw was needed.
Once a pause is measured, or a vault's kinds read different tier mixes (rich tiers), W changes decisions, which is
the point of the fix.

## Tests

TO FILL

## Docs

- `docs/learnloop-architecture-vault/Workflows/Debug a decision.md`: what a pre-build's wait was made of
  (`wait_estimate_by_tier`, `blocked_basis`). No hand-written vault note describes the prefetch ledger or W (B4 §5).
- The config field's docs: the `FiguresPrefetchConfig` docstring and field comment (the generated
  `Config - figures` note).
- The playbook has no version log; the version's own comment in `algorithm_versions.py` is the record.
- References regenerated once after the source commits (`_scripts/generate_all.py`); a second run changed nothing.

## Open items

- **Unowned figure calls.** A build that stored no figure (refused at a pause, or crashed before its row) shares its
  owner with the next build of that input; with none, its receipts are unowned and read as foreground. In the blocked
  minutes a refused pre-build with no later build of its input therefore still counts as foreground, as under v1. A
  pre-B4 ledger records nothing else that tells them apart; a forward fix would give pre-build calls their own owner
  kind (the original design the filters assumed), which changes what receipts record and is the owner's call.
- **A press waits for every author attempt.** W's quick tiers treat each completed call as one wait; a press whose
  first attempt is repaired waits for both (on the copy every build made two calls). Unchanged here.
- **Rich tiers.** Still pressed-only with no prior (background rich builds wait for the plan and the foreground, so
  their request-to-figure time is not a build time). No rich receipts exist on the owner's vaults yet; the rich-key
  mapping is tested against `rich.content_key_for` on a synthetic rich row, not on real data.

## Rules

TO FILL
