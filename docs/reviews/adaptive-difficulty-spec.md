# Stage "adaptive-difficulty-spec": adaptive difficulty and mastery, specified

**Branch:** `docs/adaptive-difficulty-spec` (base `4108e1ccd`, `main` at `mvp-0.24`, migration head 202).
**Date:** 2026-10-14; this record was added on 2026-10-15 in the Codex fix step (review finding F8), which found it missing.
**Deliverables:**
- `docs/specs/spec_adaptive_difficulty_v1.md`, "Adaptive difficulty and mastery: practice in the band, probes that discriminate, levels that mean something (v1)";
- `docs/specs/research/adaptive_difficulty_sources_v1.md`, its research appendix: method, the 121 verified sources with verdicts, the verification log and the local measurement.

This is a documentation stage, directed by the owner on 2026-10-14. No code, migration, config or test changed, and no paid API call was made. Codex research workers ran on the owner's ChatGPT subscription.

## What the spec contains

- **The current mechanism, with file:line (§3).** Item difficulty is the band the generator was told to hit, echoed back. Empirical difficulty is dark for a correct reason (θ and b confounded at n=1). The canonical prediction path and certification are blind to an item's feature point. There is no per-presentation forecast receipt.
- **The model (§5).** An explanatory-IRT likelihood over a dynamic per-(facet, capability) Gaussian state. Feature effects are shared; the item offset is integrated out, never estimated. Outcomes are ordinal and help-adjusted, with unknown help timing and revealed answers censored. Updates are a deterministic assumed-density filter with zero model calls. §5.8 states what one learner's history cannot identify.
- **Selection (§6).** Practice maximizes the posterior probability of a 70–80% success chance, with exact logged propensities. It draws only inside a block the router already chose, over the items that block admits. Calibration is bounded to acceptable difficulty. Probes keep hypothesis EIG; AD5 composes capability hypotheses' success split from AD and freezes it in the probe snapshot.
- **Generation, audit, signals (§7).** The generator writes to a feature point and is no longer asked to hit a band. An independent Decider audit checks the features. Item-side signals enter the offset prior with learned weights. Serve inputs are frozen in a receipt.
- **Forecasts (§8).** Receipts are written before every attempt and scored by proper rules. Item-only forecasts are prepared with the pool; learner-conditioned forecasts compete as experts.
- **Levels (§9).** Credit is stored by feature point. Ladders are immutable and per goal. Requirements and certificates bind feature points, never level numbers. Exam and problem-set targets come from practice-available units only.
- **Supporting sections:** integration with the router, daily plan, Decider and harness (§10); successors, switches, tables and replay invariants (§11); the learner's view (§12); the n>1 path (§13); phases AD1–AD5 with fail-first tests (§14); owner decisions D1–D14 with recommended defaults (§15); deferrals with triggers (§16); open questions (§17); the agent prompt template (§18).

## What this stage did, and what it leaves for later

| | This stage (docs only) | Implementing phases (AD1–AD5) | Owner-run |
|---|---|---|---|
| Code, migrations, tests | None | Per §14, through the §18 prompt | — |
| Paid calls | None | Feature audit, outside forecasters, backfills; spend-capped, dry-run first | The AD1 backfills on the owner's copies |
| Measurements | §3.3, on backup-API copies of the three vaults *as committed at `4108e1ccd`* (two months stale), aggregates only | `learnloop ad data-check`, `learnloop ad report` | Both commands on copies of the current working vaults (Q1); reading the AD2 report; AD4's shadow rebuild |

## Method

- Read the code cited in §3.1 and the specs the spec touches, in this worktree at `4108e1ccd`.
- Ran six Codex research workers with live, unrestricted web search (appendix §1.1). Every source they returned was then verified by this stage at its primary record (appendix §1.2).
- Measured on backup-API copies (`learnloop.db.copies.copy_tree_with_databases`) under the gitignored `fixtures-local/adaptive-difficulty/`, with the vaults loaded with `load_vault(..., load_environment=False)` and the databases opened read-only. No settings or key file and no working-vault database was read.

## Gate

| Check | Result |
|---|---|
| Internal consistency | Author read-through, three read-only Codex reviews before commit (appendix §5), then the post-commit Codex review, its fix pass, the Codex re-review and its fix pass (`docs/reviews/adaptive-difficulty-spec-codex-review.md`) |
| Code citations | After the re-review fix pass: 179 `file:line` citations (164 after the first fix pass), continuation citations on the same line included, extracted by script, plus two line-opening continuations read by hand; every one resolves to a unique tracked file with a valid range, and each cited line was printed and read against its claim. Symbol citations (`exam_pool.reserved_item_ids`, `PracticeItem.canonical_exercise`, `canonical_projection.surface_group_id`, `practice_attempts.plan_presentation_id`) and the migration head (202) checked by grep |
| External citations | 121 of 121 sources verified at the primary record; every key the spec cites is a row of the appendix (appendix §1.2, §5). The fix pass added no external source |
| `git diff --check` | Clean |
| Tests | None run: no code changed |
| Paid calls | None |

## Open questions

The spec's §17: current data on the working vaults (Q1, owner-run), generator compliance with feature points (Q2), unit-to-facet mappings for exam targets (Q3), rating timing (Q4), data volume for promotion (Q5), and whether the band should move with session state (Q6). Each has a default or a measurement path.
