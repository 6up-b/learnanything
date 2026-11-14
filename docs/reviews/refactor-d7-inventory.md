# Refactor D7, step 0: the kill-switch inventory

Step D7 of arc D (`docs/specs/refactor_strategy_v3.md` §2.6), step 0 only: the table the owner decides the removal rule from, and that the removal steps work from. Branch `refactor/d7-switch-inventory`, based on main `31787227e2`. Read-only for source code: this document is the only file the step changes. **It decides nothing.**

(Draft in progress: the per-switch tables follow in later commits.)

## 0. What is counted, and how

**A kill switch** here is a config field (boolean or mode) whose documented purpose is to turn a newer behaviour off and restore its predecessor. Two kinds:

- **Tagged** (§1): the switch of an algorithm successor `mvp-0.N`, named in that tag's comment in `src/learnloop/algorithm_versions.py:46-936` or in the field's own documentation, or gated by a successor's tag predicate (`src/learnloop/router_objective_switches.py`). These are D7's subject: the rule proposed for D7 ("a switch goes when every vault is past its tag and no vault sets it", strategy §2.6 D7) can only apply to a switch that has a tag.
- **Untagged** (§2): a live change shipped behind a switch with no successor tag, whose documentation says the off value restores the previous behaviour exactly. The proposed rule cannot apply to these (there is no tag to be past); they are listed so the count is complete.

Every other boolean or mode leaf of `LearnLoopConfig` is listed by kind in §2's census (feature opt-ins, cost controls, operational and display settings), so the three lists together cover every such leaf.

**Where the fields come from.** An AST walk of `LearnLoopConfig` (`src/learnloop/config/schema.py`, 5,104 lines) at this tip, every leaf with its default: 876 leaves, of which 279 are booleans and 36 are string or `Literal` modes. The walk ran under the empty-home wrapper; it imports the config models only.

**The state described is after D6.** D4, D5 and D6 removed the tag half of every "tag and switch" gate and left the switch for D7 (`docs/reviews/refactor-d4.md` §1, `refactor-d5.md` §1, and D6's record, `docs/reviews/refactor-d6.md` on `refactor/d6-constant-gates-rest`, §1(c)). D6 part 1 is in its landing gate and part 2's source edits are on `refactor/d6-part2-wip-orig`; both were read with `git show` and `git diff` only. Line numbers are this tip's (main `31787227e2`), where some tag halves still stand: the switch reads cited are the ones that stay.

**The floor.** `OLDEST_SUPPORTED = FIGURE_WAIT_ALGORITHM_VERSION`, `mvp-0.58` (`src/learnloop/algorithm_versions.py:1006`). The head is `mvp-0.59` (`:936`, the facet-belief fixes). Every tag from `mvp-0.9` to `mvp-0.58` is at or below the floor; only `mvp-0.59` is above it.
