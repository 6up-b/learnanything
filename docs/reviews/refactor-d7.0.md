# Refactor D7, step 0.1: the vault report lists every tagged kill switch

Branch `refactor/d7-vault-report`, based on main `00bdf58da8`. Ledger rows D7-4 (fixed) and D7-6 (found here, fixed). No serving behaviour changes: the new table is read only by `scripts/vault_report.py` and the tests.

## 1. What was wrong

The owner decides which kill switches may go from `scripts/vault_report.py`'s answer to "does any vault set one?". Its `D7_SWITCHES` named 50 of the inventory's 99 tagged switches (`docs/reviews/refactor-d7-inventory.md` §1, §5 item 5), so the Nov 12 answer ("none set") covered half of them.

## 2. What changed

- `src/learnloop/kill_switches.py` (new; imports nothing of LearnLoop): `KillSwitch(path, tag, default)` and two tuples.
  - `TAGGED_SWITCHES`: 95 rows, the switches of an algorithm successor, each with the tag it ships with.
  - `UNTAGGED_SWITCHES`: 59 rows, kill switches with no successor tag. They are §6's 54, the four §1 rows that name no tag (three `decider_routes.*` content tasks and `router_objective.receipts`), and `practice.device_eligibility_enabled` (section 3).
  - `OUTSIDE_LEARNLOOP_TOML`: the phone host's `phone_probes` (mvp-0.54), set in `mobile.toml`, which no table of `learnloop.toml` paths can name. The report ends by saying it was not read.
  - It sits beside the version floor, not in the schema: the schema says what a vault can set; this answers a question about tags and the floor, and ADR-019's rule reads both. A removal step deletes a row in the commit that deletes the field.
- `scripts/vault_report.py` reads it. Per vault, after the tag, migration head, journal, C3 and C4 keys, it prints "tagged switches set" and "other kill switches set": each line gives the path, the tag, the value, and whether the value equals or differs from the default. A switch is "set" when its key is present, even at its default. `--json` gains `tagged_switches` and `untagged_switches` lists (path, tag, value, default, differs) in place of `d7_switches`. A switch set to a table or list prints `<table>` or `<list>`, never its contents. A TOML integer where the schema has a boolean counts as differing. Reading is unchanged (`tomllib` on `learnloop.toml` and the read-only migration probe), so a vault below the floor reads as before. The script imports only the table module (on a bare interpreter it adds `src/` to the path).
- The script's docstring says how the owner runs it and what to send back.
- `pyproject.toml`: the module is listed in the import contract's module list.

## 3. Where the inventory disagreed with the code

Every path in §1 and §6 resolves in `LearnLoopConfig`, and every default equals the schema's. Two omissions:

1. **`router.lesson_suggestions.in_objective` (mvp-0.53) is not a row of §1.** `algorithm_versions.py:857` and `router_objective_switches.py` name it as the kill switch of `LESSON_OFFERS_ALGORITHM_VERSION`; §3 and §5 mention it and the old script had it. It is in `TAGGED_SWITCHES`. (§1's 98 `learnloop.toml` rows, less the four with no tag, plus this one, make 95; with `phone_probes` outside the file, 96 tagged switches in all.)
2. **`practice.device_eligibility_enabled` is counted in §6 as an "operational and safety" setting.** Its class text calls it "the kill switch of the phone's device rules", with no tag. It is in `UNTAGGED_SWITCHES` (ledger D7-6).

Tags: where §1's tag cell names a sub-switch, a variant or a rider, the row takes the tag the cell names (for example `diagnosis.shadow` mvp-0.10, `learner_text_gaps.decider_enabled` mvp-0.22, `curriculum.enabled` mvp-0.40, `adaptive_difficulty.enabled` mvp-0.30). The 1.6 batch rows are written without their section in the inventory; they are all `router_objective.*`.

## 4. The tests

`tests/test_kill_switches.py`:

- every row resolves to a leaf of `LearnLoopConfig` with the schema's default (and the same boolean-ness); no path twice; every tagged row's tag is in `SUCCESSOR_CHAIN`; untagged rows carry none;
- the guard: a field is a failure when it is missing from the table and not in `NOT_A_TABLED_SWITCH` (each entry with a reason), and (a) the schema calls it a kill switch beside a tag or `*_VERSION` name (its own leading comment, or a class-docstring sentence naming it), or (b) a double-backticked config path in `algorithm_versions.py` or `router_objective_switches.py` is a leaf, or (c) it is a boolean or mode in a section that is switches throughout (`router_objective`, `decider_routes`, `voi_stopping`, `teacher`, `teacher.weight`, `router.lesson_suggestions`, `placement`, `intent`);
- the exemptions are live (each resolves and is not in the table), and the detector is run on a synthetic schema;
- ADR-019: a switch whose tag is at or below the floor (`OLDEST_SUPPORTED`) and is still in the schema must be on `KEPT_BECAUSE_AT_OR_BELOW_THE_FLOOR`, a literal list of today's 94. Every line on it must still be a live tagged switch at or below the floor, so a removal batch deletes the field, the table row and the line together. That list is the ratchet D7 shrinks; the rule wants it short, and today it holds everything.

`tests/test_vault_report.py`: the existing assertions follow the new fields. A built vault that sets `teacher.enabled` (at its default), `router_objective.merged_sessions` (off), `router_objective.check_rate` (a mode), `stop_coin` (a rate at its default), `hints.adaptive_enabled` and `ui.shell` (untagged) reports exactly those, in table order, in text and in JSON. A switch set to a table is reported by kind only.

**What the guard catches, and what it cannot.** Checked by deleting rows: without `router.lesson_suggestions.in_objective` or `practice.device_eligibility_enabled` the guard fails. By counting: rules (a), (b) and (c) together find 82 of the 95 tagged rows (and 12 of the 59 untagged). The 13 tagged rows left are held only by the table-against-schema test and the kept-because list, which both start from the table: `adaptive_difficulty.*` (7), `diagnosis.shadow`, `diagnosis.probe_lane_pending`, `learner_text_gaps.decider_enabled`, `router.mode`, and the two rates `router_objective.stop_coin` and `pick_open_share`. **A new switch in those places, or one whose documentation never says "kill switch" beside a tag and that no tag's comment names by path, is not found.** The untagged rows are mostly unguarded against omission. A wrong tag is caught only when it is not a real tag.

## 5. Output on the private copies

Fresh backup-API copies of `learnanything-ad1/fixtures-local/owner-copies-mvp058` (the Nov 12 copies, not the live vaults), under `fixtures-local/d7report/`, deleted after. `arxiv_v2`, `linear_algebra` and `probability` each report `mvp-0.58`, migration head 255 and no activation journal; **tagged switches set: none** in all three, out of 95; other kill switches set: three in each, all at their default (`mastery.irt.enabled`, `mastery.irt.difficulty_from_prior`, `scheduler.followup.gate_mode`). This matches the inventory's check by hand.

## 6. Judgment calls

- A switch is reported when its key is present, at the default or not. The removal question is "does any vault still carry the key": a carried key is silently ignored after removal, and refused under `router.lesson_suggestions`.
- The four §1 rows with no tag live in `UNTAGGED_SWITCHES`: a tagged table with a `None` tag would make the ADR test skip them silently.
- No "vault is past the tag" column in the report: the owner reads both tags in the same block.
- The kept-because list is literal paths with one shared reason; the per-switch reasons are D7's to write.
- `NOT_A_TABLED_SWITCH` holds nine fields: five `hints.*` listed beside the hint service's switch, `reading_paths.enabled` (the Guide's own feature switch), `data_capture.receipts` and `router.log_decisions` (additive logging), and one weight.
