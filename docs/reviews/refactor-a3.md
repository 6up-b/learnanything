# Refactor A3: one readable file of defaults

Step A3 of `docs/specs/refactor_strategy_v3.md` (§2.3). Branch `refactor/a3-defaults-golden`, based on A2's tip `7e7d68c123`. No behaviour change: the effective config of a new vault, at every tag, is identical before and after (proof below).

## Step 0: nothing in `src` reads what this step deletes

Re-proved at `7e7d68c123` (after IH's mvp-0.55, the placement fix's mvp-0.56, slip-or-gap's mvp-0.57 and Decider v1.2):

- `git grep` for `DEFAULTS_SNAPSHOT`, `defaults_fingerprint`, `effective_defaults_fingerprint`, `LEGACY_DEFAULT_CONFIG`, `fingerprint_for_version` and `SNAPSHOT_BY_ALGORITHM` over `src`, `apps`, `integrations`, `scripts`, `deploy`, `migrations` and `pyproject.toml`: the only hits are `config/template.py` itself, a comment in `algorithm_versions.py`, and `scripts/refactor_measures.py`, which counts them by text and reads the dict with `getattr(template, "DEFAULTS_SNAPSHOT_BY_ALGORITHM", {})` (so it now reports 0 and still runs).
- `learnloop.config` re-exports `template` with `import *`, but no module imports any of the four names from `learnloop.config` either (same grep). No function-local or `importlib` import, no `METHOD_REGISTRY`/Typer/`MODULE_INVENTORY`/`_reg_const` string, no sidecar handler, no frontend or phone caller (`apps/` has only unrelated `SNAPSHOT` constants in vitest files), no upgrade, successor, replay or rebuild path.
- Nothing reads `config/schema.py`'s comments or docstrings at runtime. No config model is sent as an LLM output schema. The vault generators read class docstrings only for the module notes' one-line summaries, and `db_generate_reference.py` reads `schema.py` for field line numbers (both regenerated). Two tests allow `schema.py` to name a table in prose (`test_notes_never_read`, `test_rw5c_never_evidence`); removing the prose is harmless to them.
- **The count at this tip.** 48 digests (mvp-0.9 to mvp-0.57, each tag of `SUCCESSOR_CHAIN`). 51 test files referenced a digest or snapshot name: 50 test files plus `tests/helpers.py` (`undo_decider_v12`). 11 of them carried the 40 s timeout normalization (`assert dumped["router"]["timeout_seconds"] == 40.0` then `= 8.0`). Eight `drop_*_keys` helpers (`drop_ih5_keys`, `drop_sg_keys`, `drop_te2_keys`, `drop_te3a_keys`, `drop_te3b_keys`, `drop_rospeed2_keys`, `drop_unevidenced_return_keys`, plus `undo_decider_v12`) existed only to undo later defaults inside those preambles, and were imported across 14 files. `LEGACY_DEFAULT_CONFIG_TEXT` had 2 test readers, as the strategy said: `test_config_refactor.py` and `test_ro1_successor.py`.

Nothing in `src` reads them, so nothing moved to the owner's list.

## `config/schema.py`: history out of the comments

The strategy estimated about 2,000 lines of history comments here. At this tip the file had 1,158 comment lines and 1,789 docstring lines, and most of them carry behaviour (what a switch serves when off or below its tag, why a default is what it is) with the history woven in. So the pass rewrote rather than deleted: about 450 comment and docstring blocks lost their stage names (RW*, TE*, RO*, IH*, SG*, AD*, PF-*, Slice/Phase/T*), spec section numbers (279 `§` before, 0 after), review rounds, rulings and dates (56 ISO dates before, 0 after), and kept what the line does and its why. A comment that was only history was deleted. The router's timeout is the model: `# Owner, Nov 8 2026: 40, up from 8. The LLM's calls took 11.6-15.8 s, so 8 discarded answers that were on the way.` became `# The LLM's calls take 12-16 s; a shorter wait discards answers that are on the way.`

Net: 5,218 to 5,111 lines (1,054 removed, 947 added). Version tags stay only where they say from which version a switch acts ("inert below mvp-0.46"). "Owner" and "Codex" remain where they name the user and the provider. The pass was done by a helper agent with the Edit tool only. I checked it two ways. First, the module's AST with docstrings removed is identical to A2's (script `ast_same.py`, kept in the scratch directory). Second, the whole-config proof below. I re-read the ten places the helper flagged as uncertain. One reading was wrong, and I restored "the mvp-0.8 projection paths keep `ROBUST_QUANTILE`". The others stand. Three of them keep a pointer or a status claim, which the owner may want to look at: `schema.py:1107` points to `docs/reviews/decider-v1-2.md` for the pinned slug, `:4736` points to `docs/reviews/adaptive-difficulty-ad23.md` for the pre-registration, and `:3855` says the plan serves no `pre_questions` yet. Not history, and so left alone: `:4792`'s "true runs all three" is out of date, because there are four outside forecasters now.

## What was deleted

| What | Where | Lines |
|---|---|---|
| `LEGACY_DEFAULT_CONFIG_TEXT` (the frozen mvp-0.9 full template, a before-image for an old equivalence test) and its comment | `config/template.py` | 717 |
| `DEFAULTS_SNAPSHOT_BY_ALGORITHM`: 48 digests and 3,307 lines of history comments (plus a 6-line header) | `config/template.py` | 3,363 |
| `effective_defaults_fingerprint`, `defaults_fingerprint_for_version`, their imports and `__all__` entries | `config/template.py` | about 50 |
| History in comments and docstrings (about 450 blocks rewritten or deleted) | `config/schema.py` | net 107 (1,054 out, 947 in) |
| Digest tests, preambles, frozen base digests (`MVP052/054/055_BASE_DIGEST`, `mains` dicts), the eight undo helpers, `ROSPEED2_KEYS` and sg's `BASE` | 50 test files and `tests/helpers.py` | 1,048 deleted, 66 added |

`config/template.py` went from 4,255 lines to 125: the decision-only template (unchanged, byte for byte), `default_config_text`, `DEFAULT_CONFIG_TEXT` and `write_default_config`.

## What was added

- `tests/goldens/effective_defaults.toml` (1,206 lines): a three-line header, then every key of `LearnLoopConfig.model_validate(tomllib.loads(DEFAULT_CONFIG_TEXT)).model_dump(mode="json", exclude_none=False)`, flattened to dotted keys and sorted by path. 1,078 keys have a value; 125 are unset and written `# key = null`, since TOML has no null. Lists and dicts inside a value are inline TOML.
- `tests/test_effective_defaults_golden.py` (124 lines), the one helper (`effective_defaults_toml`) and three tests:
  - `test_the_effective_defaults_match_the_golden_file`: compares the text and, on a mismatch, prints only the changed lines and the regenerate command.
  - `test_the_golden_file_reads_back_as_the_effective_config`: guards the rendering. The file parses as TOML into exactly the effective config, unset keys aside.
  - `test_every_tag_has_the_latest_defaults_apart_from_its_label`: every tag in `SUCCESSOR_CHAIN` loads to the latest defaults with only `algorithms.algorithm_version` changed. This replaces the per-successor "differs from the predecessor by the tag alone" checks (ih5, sg, te3a, te3b, mobile_v3, placement) with one check over all 48 tags.
- The regenerate command, mirroring `tests/test_cli_help_snapshot.py`: `uv run python tests/test_effective_defaults_golden.py --write`. It is in the test's docstring, its failure message, the golden's header, playbook step 4 and the vault notes.

## How each test was handled

"Digest lines" means `DEFAULTS_SNAPSHOT_BY_ALGORITHM[...] == defaults_fingerprint_for_version(...)` (or the `effective_defaults_fingerprint` form), the loop over the chain doing it, and `snapshot[TAG] != snapshot[PREDECESSOR]`.

| Test file | What it had | Handling |
|---|---|---|
| `test_ad23_successor`, `test_attempt_content_state_successor`, `test_batch3_landing`, `test_cold_retry_reschedule`, `test_curriculum_c1_plan_follows_path`, `test_field_workbench_signals`, `test_help_fold_attach_successor`, `test_intent_codex_rereview`, `test_learner_report_superseded`, `test_lp_claim_fixes`, `test_plan_follows_path`, `test_reader_ca2_one_ask`, `test_reader_followups_successor`, `test_rebuild_equivalence_review`, `test_serve_eligibility_review` (15) | a successor test (chain position, version set, upgrade predecessor, and where present the switch's default and its `classify_config_path` rule) with digest lines at the end | digest lines and their import removed; everything else kept as it was, including every `classify_config_path` assertion and switch default. Two tests renamed because the name said "with its defaults snapshot" |
| `test_mvp013/014/015/016/017/020/021_upgrade`, `test_method_explicit_upgrade`, `test_recurrence_commands` (9) | digest lines plus direct checks of the successor's keys (`stuck_prompt.enabled`, `plan.default_minutes == 25`, `router.probe_tie_admission`, the learner-text-gap section, `proof_check.enabled`, the retired route, the VOI-stopping section and its kill-switch caps, `required_method.enabled`, `recurrence.blocking_cutoffs == {}`) | the direct assertions kept on the tag's loaded config; digest lines removed; tests renamed to say what they check |
| `test_plan_determinism`, `test_reading_step_switch`, `test_diagnosis_input_provenance` (3) | a loop over the chain asserting a digest and the switch's value at each tag | the value-per-tag loop kept; digest removed; renamed `test_every_tag_defaults_the_switch_on`/`_off` |
| `test_mvp010/011/018/022/023/024_upgrade`, `test_regrade_contract_successor`, `test_followup_successor` (8) | a test that only compared digests | deleted (the golden test covers it) |
| `test_data_capture_successor`, `test_ro1/ro4/ro5/ro6_successor`, `test_rofu_successor`, `test_teacher_te2_successor`, `test_te3a_successor`, `test_te3b_successor`, `test_ih5_successor`, `test_sg_successor`, `test_teacher_te1_successor`, `test_teacher_te1b_suggestions` (13) | "moves only by the new keys": recompute every digest, then drop every later successor's keys from the predecessor's dumped config (through the cross-file `drop_*_keys` helpers), undo Decider v1.2's model, put the timeout back to 8 s, and compare a sha256 with a frozen base digest | deleted with the helpers and frozen digests. Each file keeps its own direct tests of its keys' defaults (`test_the_switch_defaults_on...`, `test_the_seeds_are_the_specs...`, `RouterObjectiveConfig().x is True` checks, the RO1 gates that all read on at the tag with no override). Values the preambles asserted only to undo them (`history_card_token_budget == 48_000`, `teacher.episode_log`, `held_ad_link`, `router.timeout_seconds == 40.0`, the Decider slug) were normalization, not a test's meaning; each is now a golden line |
| `test_placement_unevidenced_return`, `test_mobile_v3_successor` (2) | "the snapshot is recorded and the tag's defaults differ from the predecessor's by the label alone" (placement also asserted `unevidenced_return is True` at the tag) | deleted; the label-alone check is `test_every_tag_has_the_latest_defaults_apart_from_its_label` over every tag; placement's default is checked behaviourally by `test_the_gate_is_the_tag_the_switch_and_ignored_opening_episodes[at-tag]` (no override, at the tag, the gate is on) |
| `test_ro1_successor::test_the_factors_constants_stay_in_config_with_their_note` | the factors' values, their absence from the template, and a note in `LEGACY_DEFAULT_CONFIG_TEXT` | the values and the template check kept; the legacy-text line removed (the note lives in `schema.py`); renamed |
| `test_config_refactor` | five tests on the snapshot contract and the legacy text | `test_config_responsibilities_have_canonical_module_owners` keeps its owner checks (`write_default_config` replaces the fingerprint's identity check). `test_minimal_template_preserves_non_provider_effective_defaults` compared the decision-only template at mvp-0.9 with the legacy full template; it becomes `test_each_plan_tier_runs_its_codex_tiers_model_and_effort`, the one relation in it that still describes today's defaults. `test_every_recorded_version_keeps_its_defaults_snapshot` keeps its template checks as `test_the_template_renders_at_every_tag_by_its_label_alone` (parametrized over `SUCCESSOR_CHAIN`). `test_defaults_snapshot_is_keyed_by_algorithm_version` and `test_the_defaults_snapshot_covers_the_successor_chain` deleted |
| `tests/helpers.py` | `undo_decider_v12` | deleted (no user left) |

No `classify_config_path` test was touched (0 removed lines name it). The only direct key-value assertion removed outright is placement's `at_tag["placement"]["unevidenced_return"] is True`, covered as above.

Stale wording that named a snapshot in five test docstrings and comments was corrected.

## Docs

- `docs/algorithm-change-playbook.md` step 4 and the closing paragraph.
- `algorithm_versions.py`'s `SUCCESSOR_CHAIN` comment (the strategy's line 877, now 912).
- Vault: Algorithm Versions and Reproducibility (the "Defaults fingerprint" section is now "Effective defaults"; the change protocol and test list), Testing and Invariants (line 72, at the orchestrator's request), Configuration (the boundaries line and "Defaults reproducibility"), Parameter Governance and Evaluation, Data and State Map, and ADR-006 (a dated line under Consequences; the decision itself is history).
- `_scripts/db_generate_reference.py`: the config field notes' "Omitted does not mean frozen" callout, the extension guidance and the facet-locks rationale named the fingerprint or the snapshots. All generated references were regenerated once, after the source commits.
- The Developer Map's "where to change what" table is A4's: its rows already name `tests/goldens/effective_defaults.toml` and "the golden test's write command", which match this step's names exactly.
- `CLAUDE.md` is unchanged: it names no defaults snapshot or digest (its one "snapshot" is the CLI surface test).

## Proofs

### The effective config before and after is identical, compared whole

Two dumps from each side. The base side is a clean `git archive 7e7d68c123 src` export. The tip side is this branch, after the `schema.py` pass (`7430827a40`). Each ran with `PYTHONPATH=<tree>/src`, under the empty-`HOME` wrapper.

1. **Python dump.** This script prints sorted JSON of the decision-only template text, the effective config of a new vault, the effective config at every tag (`default_config_text(v)` for each of the 48 in `SUCCESSOR_CHAIN`), and the effective config of an empty `learnloop.toml`. All of it uses `model_dump(mode="json", exclude_none=False)`:

   ```python
   import json, tomllib, sys
   from learnloop.config.schema import LearnLoopConfig
   from learnloop.config import template
   from learnloop.algorithm_versions import SUCCESSOR_CHAIN, LATEST_ALGORITHM_VERSION
   def eff(text):
       return LearnLoopConfig.model_validate(tomllib.loads(text)).model_dump(mode="json", exclude_none=False)
   json.dump({"latest": LATEST_ALGORITHM_VERSION, "default_config_text": template.DEFAULT_CONFIG_TEXT,
              "effective_new_vault": eff(template.DEFAULT_CONFIG_TEXT),
              "effective_by_version": {v: eff(template.default_config_text(v)) for v in SUCCESSOR_CHAIN},
              "effective_empty_toml": eff("")}, sys.stdout, sort_keys=True, indent=1)
   ```

   Run as `env -i ... PYTHONPATH=$TREE/src .venv/bin/python -P dump_effective_config.py > $SIDE.json`, then `cmp base_effective.json tip_effective.json`. The files are identical, 2,220,041 bytes each. The dump prints which `schema.py` it loaded, which confirmed each side.
2. **CLI dump.** With each tree's code: `learnloop init <dir>`, then `learnloop config effective --json --vault <dir>`, and `cmp`. Identical, 41,224 bytes. The command prints no vault path, so nothing needed normalizing.

Also, at the base, all 48 tags' effective configs differed from the latest only by `algorithm_version`. That is what `test_every_tag_has_the_latest_defaults_apart_from_its_label` now holds.

### The 40 s target

On a scratch branch I made one commit, `router.timeout_seconds` default 40.0 to 41.0, with the golden regenerated by its write command. Then I regenerated the references, recorded the result, and deleted the branch.

| What changed | Lines |
|---|---|
| `config/schema.py` | 1 (`Field(default=41.0, ...)`) |
| `tests/goldens/effective_defaults.toml` | 1 (`router.timeout_seconds = 41.0`) |
| test literals | 0 (no test pins the router timeout now; before A3, 11 files did) |
| generated notes | 1 (`Reference/Configuration/Fields/Config - router.md`, its table row), plus `Reference/_generated.md`'s commit stamp, which changes on every source commit by A1's design |

Without the regenerated golden, `test_the_effective_defaults_match_the_golden_file` fails and prints exactly:

```
AssertionError: an effective default changed. If it was meant to, run `uv run python tests/test_effective_defaults_golden.py --write` and commit the file with the change:
--- golden
+++ now
-router.timeout_seconds = 40.0
+router.timeout_seconds = 41.0
```

That regeneration on the scratch commit also changed no other note, so the references at this branch's tip are a fixed point of the generators.

### Tests and checks

Every run used the memory cap, `-n 6` and an explicit file list, and waited on the full-suite lock.

- **Targeted tests:** 68 files, 1,208 passed, 13 skipped, 3 xfailed (99 s), on the final tree. The list:
  - every test file this step edited or deleted from (the 51 that named a digest name at the base, `helpers.py` aside), and the new golden test;
  - the config tests: `test_config_refactor`, `test_ai_config`, `test_evidence_config`, `test_field_config`, `test_vault_template`, `test_settings_store`;
  - `test_cli_help_snapshot` (including its slow help render), `test_architecture`, `test_registry_audit`, `test_cli_json`, `test_public_tip_guards`;
  - the doctor tests: `test_doctor`, `test_identifiability_doctor`, `test_km1_doctor`, `test_mobile_doctor`;
  - the two tests that allow `schema.py` to name a table: `test_notes_never_read`, `test_rw5c_never_evidence`.

  An earlier run of the same list, taken while the `schema.py` pass was in progress, gave the same counts. The 13 skips were not classified one by one.
- `lint-imports --no-cache`: 43 kept, 0 broken.
- Validators on the regenerated tree:
  - `module_validate.py`: PASS.
  - `desktop_validate.py`: passed, reproducible byte for byte.
  - `db_validate_reference.py`: `errors: []`.
  - `validate_vault.py`: passed (2,271 notes, 2,269/2,269 reachable).
- **Not run (the orchestrator's landing gate):** the full suite, durability, `--fresh-connections`, vitest and cargo. Nothing outside Python changed.

## Rules

- Mechanical edits were made by scripts, then checked by reading the diff: deleting the two data blocks and two functions in `template.py` by exact line range; removing exact digest-line patterns from 26 test files; deleting whole named test functions and helpers by AST span from 23 files; and removing the imports that left unused (only digest names and `hashlib`/`json`/`tomllib`/`LearnLoopConfig`/`default_config_text`/`LATEST_ALGORITHM_VERSION`, only where no longer referenced). One pattern removal mis-indented a loop in `test_reading_step_switch.py`; it was found in the diff and fixed by hand. Everything else, including every rename, docstring and note, was edited with the Edit tool.
- The `schema.py` comment pass was done by a helper agent with the Edit tool only; I checked it by AST comparison (code identical with docstrings removed) and by the whole-config comparison.
