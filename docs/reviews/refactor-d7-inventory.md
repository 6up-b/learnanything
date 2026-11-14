# Refactor D7, step 0: the kill-switch inventory

This is step 0 of step D7 in arc D (`docs/specs/refactor_strategy_v3.md` §2.6). It is the table the owner decides the removal rule from, and the table the removal steps work from. Branch `refactor/d7-switch-inventory`, based on main `31787227e2`. No source file changes in this step: this document is the only file it touches. **It decides nothing.**

Paths in the tables are relative to `src/learnloop/` unless they start with `tests/`, `scripts/`, `apps/` or `sidecar/` (short for `src/learnloop_sidecar/`). Line numbers are this tip's.

## 0. What is counted, and how

**What counts as a kill switch.** A config field, boolean or mode, whose documented purpose is to turn a newer behaviour off and restore its predecessor. There are two kinds:

- **Tagged (§1).** The switch of an algorithm successor `mvp-0.N`. It is named in that tag's comment in `algorithm_versions.py:46-936`, or in the field's own documentation, or it is gated by a successor's tag predicate in `router_objective_switches.py`. These are D7's subject. The rule proposed for D7 is "a switch goes when every vault is past its tag and no vault sets it" (strategy §2.6 D7). That rule can only apply to a switch that has a tag.
- **Untagged (§6).** A live change shipped behind a switch with no successor tag, whose documentation says the off value restores the previous behaviour exactly. The proposed rule cannot apply to these, because there is no tag to be past. They are listed so the count is complete.

Every other boolean or mode leaf of `LearnLoopConfig` is counted by kind in §6's census: feature opt-ins, cost controls, and operational, display and selection settings. Together, §1 and §6 cover every such leaf.

**Where the fields come from.** An AST walk of `LearnLoopConfig` (`config/schema.py`, 5,104 lines) at this tip lists every leaf with its default: 876 leaves. Of these, 279 are booleans and 36 are string or `Literal` modes. The walk ran under the empty-home wrapper and imports only the config models. Of the 315 booleans and modes, §1 covers 97 and §6 covers the other 218: 54 untagged kill switches and 164 other settings.

§1 has 99 rows, because two of its fields are floats rather than booleans or modes: the router objective's rates `stop_coin` and `pick_open_share` (§1.5). §1 also keeps two fields that are not tagged switches, for reference: `router_objective.receipts` (RO0's logging switch) and `facet_diagnostic.canonical_belief_fixes` (the head's switch). One tag's switch lives outside `learnloop.toml`: the phone host's `phone_probes` (mvp-0.54, `src/learnloop_mobile/config.py:32`). It is noted in §1.6 and not counted.

**The state described is after D6.** D4, D5 and D6 removed the tag half of every "tag and switch" gate and left the switch for D7:
- `docs/reviews/refactor-d4.md` §1 and its "For D7" list (:191);
- `docs/reviews/refactor-d5.md` §1 and its "For D7" line (:208);
- D6's record, `docs/reviews/refactor-d6.md` on `refactor/d6-constant-gates-rest`, §1(c) (sites G1-G56).

D6 part 1 is in its landing gate. Part 2's source edits are on `refactor/d6-part2-wip-orig`, and its pin change and D-31 fix are on `refactor/d6-part2-wip`. All three branches were read with `git show` and `git diff` only. Line numbers are this tip's, where some tag halves still stand; the switch reads cited are the ones that stay.

D6 left four router-objective tag predicates (`followups_tag`, `lesson_offers_tag`, `failure_share_tag`, `slip_gap_tag`) as its class (d). They are held only by the `legacy` arm of identity pins C3-C5 (D6 §1(d), §8 item 2). Part 2's commit `ae305d5cf7` drops that arm on purpose ("C3-C5 are pinned for a new vault's config only"), which lets the predicates go. G38 (`figures/prefetch_ledger.py:71`) stays for the figures lane.

**The floor.** `OLDEST_SUPPORTED = FIGURE_WAIT_ALGORITHM_VERSION`, which is `mvp-0.58` (`algorithm_versions.py:1006`). The head is `mvp-0.59` (`:936`, the facet-belief fixes). Every tag from `mvp-0.9` to `mvp-0.58` is at or below the floor; only `mvp-0.59` is above it.

**How each column was filled.**
- **Readers:** `git grep` of the key and of its predicate over `src/`, `apps/`, `scripts/` and the vault's `_scripts/`, then each hit was read.
- **Code kept alive:** counted three ways:
  1. the branch sites on the switch's predicate;
  2. the non-blank, non-comment lines in the off bodies, read by hand;
  3. the functions reachable only from those bodies, with callers checked by `git grep -w`.

  Every line count is an **estimate** unless it is a function's whole span. "≈" marks it. Where the off code is also reached by another switch that stays, only the lines this switch alone frees are counted, and the row says so.
- **Off-only tests:** test functions whose subject is the off branch, found by `git grep` of the key in `tests/` and reading each enclosing function. Tests that set the switch off only to reach something else are counted separately as "port": they need another route, not deletion. Both counts are estimates.
- **Who did the reading.** The reading was first split by area and done in parallel. The coordinator stopped that because it used the owner's whole allowance, and I finished the rest in sequence. Every claim that decides a row's class was re-read at its file:line before it went into this document. §7 lists what was not.

**Where a removal touches the config, whatever the switch.**
- **The whole-config digest is pinned.** `tests/test_retired_config_identities.py:261` pins `content_key(identity_dump(config))` for a default and a legacy config against digests recorded at arc C's base `88607cb3fe` (`:104`). Only fields named in `ADDED_SINCE_BASE` (`:112-115`) are exempt. Every switch in §1 except `facet_diagnostic.canonical_belief_fixes` existed at that base. So **removing any of them fails that test unless the field goes into `config/retired.py`'s `RETIRED_FIELDS` with its old default**. `identity_dump` then puts the field back (`config/retired.py:119-128`). The same digest names embedding-compare report files (`ops/embedding_compare.py:732`).
- **A section must become retired-aware.** `RETIRED_FIELDS` works only on a model that subclasses `KeepsRetiredFields` (asserted at `tests/test_retired_config_identities.py:276`). Most switch sections are plain `BaseModel`s (`MasteryConfig` `config/schema.py:197`, `PlacementConfig` `:3772`, `RouterConfig` `:3991`, `RouterObjectiveConfig` `:4089`, `ReplayConfig` `:4609`). So each removal step must also make its section a `KeepsRetiredFields`. This is mechanical, and the strategy already requires it (§2.1 "Identity rules").
- **`RETIRED_FIELDS` cannot help an explicit read.** It keeps bytes only where an identity dumps a config model through `identity_dump` or `identity_view`. It does not help where code reads a switch's value into a key by name: `objective_settings`, `followup_switch_snapshot`, `followup_generator_switches`, `draw_inputs` and `projection_switches`. There the code must keep emitting the served value as a constant, or the identity moves. **That is the line between class A and class B below.**
- **A vault that still sets a removed key loads silently.** Every switch section except one uses pydantic's default (`extra` ignored), so a vault whose `learnloop.toml` still sets a removed key loads and the key silently means nothing. The exception is `RouterLessonSuggestionsConfig` (`config/schema.py:3984`, `extra="forbid"`): removing `router.lesson_suggestions.enabled` or `.in_objective` makes a vault that sets either key **fail to load** until the key is deleted. `LearnLoopConfig` itself is `extra="allow"` (`:4808`).
- **Goldens move.** Every removal changes `tests/goldens/effective_defaults.toml`. That file is a golden, not an identity, and is regenerated in the same commit.

**What the owner's copies set.** `scripts/vault_report.py`'s logic was run on fresh backup-API copies of `/home/saturn/Documents/thinking/learnanything-ad1/fixtures-local/owner-copies-mvp058`:
- **How:** `learnloop.db.copies.copy_tree_with_databases`, into `fixtures-local/d7inv/`, deleted after. Only counts and names are reported.
- **Result:** `arxiv_v2`, `linear_algebra` and `probability` are each at `mvp-0.58`, migration head 255, with no activation journal. "D7 switches set: none" for all three.
- **The rest of §1:** the script's list (`scripts/vault_report.py:60-93`) names 50 of §1's 99 fields; the other 49 are marked "no" in the tables' last column. Each copy's `learnloop.toml` key paths were therefore also checked against all 99 fields: **none of the three sets any of them**.
- **§6's 218 fields:** the copies set four of them, and each to its default (written by an old template): `mastery.irt.enabled`, `scheduler.followup.gate_mode`, `scheduler.followup.threshold_mode` and `tutor_qa.reader_enabled`.
- **What this does not show:** these are copies from Nov 12, not the live vaults.

**Nothing in the app writes a tagged switch.** The app's config writers are listed below; none touches a §1 field:
- `ops/settings_store.apply_config_updates`, whose callers write `ai.*`, `cues.*`, `figures.manim_opt_in`, `hints.help_style`, `notes.gaps_enabled` and `reader.correspondence.*` (`sidecar/handlers/settings.py:336`, `reader.py:2975`, `figures.py:892`, `hints.py:536`, `notes.py:399`, `correspondents.py:400`, `first_run.py:261`, `:319`);
- `ops/plan_transport.py:160`, which writes Codex pins.

So a §1 switch is set in a vault only by hand-editing `learnloop.toml`.
