# mvp-0.73: the difficulty label retirement's fix round

Branch `refactor/h3-fix-round`, from main `bc70e26255`. The predecessor is mvp-0.72, L4-2's lesson-weight curves.
The findings are H3's adversarial review (ledger H3-R1 to H3-R23; the fix round's section of
[algorithm-mvp-0.71.md](algorithm-mvp-0.71.md)). Only the fixes that change persisted meaning are under this tag.
Everything was measured on synthetic vaults and fakes.

The tag is one constant (`FORECAST_SCORING_ALGORITHM_VERSION`), the chain entry, its set and predicate
(`forecast_scoring_fixed`), one upgrade row (`Link(mvp-0.73, whole_vault_rebuild)`) and its test row. There is no
migration, no config key, no kill switch and no new constant: the clip is mastery's configured `p_clip`.

## What changes at the tag

- **H3-R9: scoring against AD's forecast.**
  - **Below the tag:** the forecast's `p` was clamped, inverted to `b' = μ − logit(p_eff)/a`, and scored through
    mastery's 2PL. That path has a second, fixed 0.02/0.98 clamp and a division by `a`.
  - **From the tag:**
    - the forecast's probability is used directly: its exact logit, plus `a·offset` for a primed answer;
    - it is clipped once by `p_clip` (`mastery.irt_observation_at`);
    - it is scored with the same sensitivity `a·p(1−p)`, noise and innovation variance as mastery's observation;
    - an implied `b_scored` is recorded only where `a ≠ 0`.

  A primed `p̄ = 0.9` now scores at 0.9852, not 0.98, and `a = 0` no longer raises.
- **H3-R10: scoring when mastery's IRT link is off.** From the tag, surprise is centred on the forecast's logit (a
  primed offset added) in the legacy logit observation space, and every row names its source (`mastery` included).
  The mastery update and the interval factor keep mastery's residual.
- **H3-R12: retention-check seeds.** From the tag, a lesson's retention check is seeded per landed node
  (`lesson:<id>:retention:<lo>:node:<node>`), and the node's cold-reference forecast uses the same seed. Two nodes on
  one LO no longer share one draw, so each receipt's propensity is its real one.

Below the tag each of these is mvp-0.72's exactly. The tests cover both sides: `test_surprise_forecast_scoring.py`
and `test_data_capture_a6_delayed_pick.py`.

**Why a whole-vault rebuild:** surprise rows scored against a stored forecast are recomputed from that forecast, so
history's rows move under the tag. Receipts and raw ledgers are unchanged. Retention seeds affect new lessons only;
committed checks keep their recorded picks.

## Pins and goldens

- **Identity pins** (`A1-A4.manifest_hash.init`, `C3.boundary(.init, _offer.init)`, `C3b.chooser(_offer)`,
  `C3b.start_key(_offer)`, `C5.init`, `C6.init`): regenerated, because they hash the vault's tag.
- **Effective defaults:** the tag line.
- **CLI surface:** the upgrade's default tag.
- **Grade application and diagnosis journey goldens:**
  - the tag strings;
  - the grade-time receipts' `algorithm_version`, now stamped (H3-R17, without a tag).

  No surprise value moved in them: no golden has a primed forecast beyond the clip, `a = 0`, or the IRT link off.
- **Placement manifest:** the tag.

## The owner-copy procedure (for the orchestrator, from an mvp-0.72 copy; counts only)

Follow `algorithm-mvp-0.71.md`'s procedure with `--to mvp-0.73` and a predecessor copy at mvp-0.72. Expected:
- grade-time receipts and raw ledgers unchanged;
- mastery unchanged: the tag changes surprise scoring only;
- surprise rows changed only where a row's source is `serve_receipt` or `grade_receipt` and its forecast was primed
  past the clip, or the vault runs without the IRT link;
- `surprise_direction_changed` with its transitions reported;
- every row's source is named, so `none (below the tag)` is 0 after the upgrade.

`label_retirement_counts.py compare` prints the counts.
