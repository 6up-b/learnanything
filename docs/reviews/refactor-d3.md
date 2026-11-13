# Refactor D3: the upgrade table

Step D3 of arc D (`docs/specs/refactor_strategy_v3.md` §2.6), on branch `refactor/d3-upgrade-table`, based on main `1da959e7d7` (D1 landed: the floor `OLDEST_SUPPORTED = mvp-0.58`; the head is `mvp-0.59`). Structure track: no served or persisted value changes.

## 1. Step 0, before any code

### (a) Which links can still run

With the floor at `mvp-0.58`, a vault below it is refused at every door (ADR-019), and only `learnloop upgrade` may open one (`version_floor.upgrading`). The chain at this tip has 50 tags (`SUCCESSOR_CHAIN`, `mvp-0.9` to `mvp-0.59`) and 48 upgrade entry points (`--to mvp-0.7` to `--to mvp-0.59`, `mvp-0.28` never existed). Every link whose predecessor is below the floor runs only on a vault the floor refuses everywhere else, so on this code exactly one link can still run for a vault that opens:

| link | predecessor | module | activation |
|---|---|---|---|
| `mvp-0.59` (the facet-belief fixes) | `mvp-0.58` (the floor) | `facet_belief_upgrade` | a whole-vault rebuild under the tag (`rebuild_all_derived_state`), completion read from `has_whole_vault_rebuild` |

Two edge cases of the same kind, both below the floor and so both leaving with the chain:

- **A journal from below the floor.** A vault published at `mvp-0.58` over an `mvp-0.57` database (an interrupted upgrade to the floor itself) is refused by `activation_journal.complete` (`refuse_journal_below_floor`) at every opener; today `learnloop upgrade` completes it through `facet_belief_upgrade.complete_interrupted_activation` handing it to `figure_wait_upgrade`'s. After D3 it is refused with the `pre-floor` route, whose code still completes it.
- **`--to <tag below the floor>`.** Today it runs the link's code on a vault below the floor (the allowance covers the upgrade command's vault). After D3 it names the route.

**What a vault below the floor is told today** (`version_floor.upgrade_commands`, the one place that names the route): `learnloop upgrade --vault <root>`, preceded by `learnloop upgrade --to mvp-0.7 --vault <root>`, `--to mvp-0.8` and `--to mvp-0.9` for a vault older than the chain (the chained links refuse anything older than `mvp-0.9`). The message (`BelowOldestSupported`): "`<root>` is at mvp-0.57, older than mvp-0.58, the oldest version this LearnLoop opens. Upgrade it with `learnloop upgrade --vault <root>`." A keyless config gets the `mvp-0.6` advice plus the three `--to` steps.

### (b) Every non-upgrade importer of an upgrade module

Searched over `src/`, `scripts/`, `apps/` and `pyproject.toml` for each module's dotted name and for `from learnloop import <module>`, then each hit read:

| importer | what it takes | after D3 |
|---|---|---|
| `cli/app.py` `upgrade` | every `upgrade_to_*` (48 branches of an `if`, a 155-line docstring, a 20-line `--to` help naming every tag), and 29 tag constants for the help | the table |
| `cli/runtime.py:139`, `learnloop_sidecar/context.py:827` | `facet_belief_upgrade.complete_interrupted_activation`, installed with `activation_journal.install_completer` | the table's completion |
| `learner/recall_calibration.py:16` | `ops.vault_upgrade.LEGACY_ALGORITHM_VERSION` (`"mvp-0.6"`, one constant; the brief's second constant is gone at this tip) | `algorithm_versions.LEGACY_ALGORITHM_VERSION` (the tag stays: the harness's vault is ledger row D-24) |
| `scripts/voi_cap_report.py:49-51` | `upgrade_to_mvp09`, `upgrade_to_mvp021` (it upgrades a copy to the VOI successor) | dropped: every vault that opens is past `mvp-0.21` |
| `scripts/table_review.py:241` | a path pattern (`*_upgrade`, `recurrence/upgrade.py`, `ops/vault_upgrade.py`) classifying a module's role, not an import | unchanged; `ops/upgrades.py` falls under its generic rules |
| `activation_journal.py`, `ops/settings_store.py`, `substrate/rebuild_orchestrator.py:110` | docstrings and comments naming modules | rewritten |
| helpers between upgrade modules: `UpgradeResult` and `rewrite_algorithm_version` (`ops/vault_upgrade`), `write_activation_journal` (`claim_fixes_upgrade`), `publish_algorithm_version` (`regrade_contract_upgrade`) | only upgrade modules and tests import them | move into `ops/upgrades.py` |
| the parameter registry (`MODULE_INVENTORY`, `_reg_const`, `classify_config_path`) | no string naming an upgrade module at this tip (a scan of `params/` for `upgrade` finds none) | nothing to remove |
| `pyproject.toml` | the `experiments-stay-outside-production` contract lists 45 root upgrade modules as sources; `tui-keeps-the-open-queue` forbids `learnloop.daily_plan_upgrade`; the frozen-cycle contract ignores `recall_calibration -> ops.vault_upgrade` and `ops.vault_upgrade -> substrate.{canonical_projection,p0_projection}` | the lines go; `ops.upgrades`'s own edges are added where import-linter asks |
| `apps/`, `learnloop_mobile`, `learnloop_mcp`, sidecar `METHOD_REGISTRY` | nothing | - |

No upgrade module is reachable from replay, rebuild, doctor or serving (strategy §2.6's AST closure; no `importlib` path in `src/` names one: the registry's `MODULE_INVENTORY`, `valuation`'s named gaps, `open_world_gate`, the fetchers, the PF sandbox and `ai/__init__`'s lazy attributes were each read).

Tests: 72 tracked test files or helpers name an upgrade module (`tests/goldens/structure.toml` and `tests/architecture_function_local_domain_imports.txt` among them), 4 more drive `learnloop upgrade` through the CLI (`ad_denial_log_helpers`, `test_cli_help_snapshot`, `test_exam_protection_identity`, `test_version_floor`), and 23 assertions in 16 files pin `inspect.getsource(...)` to name the chain's latest module.

### (c) What the tracked fixtures cost

- **`fixtures/migration_head`** is at `mvp-0.6` (the legacy model, sanitized). 30-odd migration tests copy it to check schema upgrades and open it through the test allowance; the chain-walk tests (`test_mvp0NN_upgrade`, `test_regrade_contract_upgrade::test_head_fixture_predecessor_to_successor_path`, `test_p0_cutover_mvp08`, `test_lp_claim_fixes`'s fixture case, `test_method_explicit_upgrade`) upgraded it link by link from `mvp-0.6` or `mvp-0.9`. Once the chain leaves the code, nothing here can upgrade it, so playbook step 8's "predecessor-to-successor path" on the head fixture is impossible on this code: the kept tests run each link on `create_basic_vault` instead.
- **`fixtures/mvp017_route_check_replay`** is at `mvp-0.17`; its point is that rows written at `mvp-0.17` replay exactly (an old-row reader, kept by D5). It is opened through the allowance and never upgraded.

**Is upgrading the head fixture to the floor worth its own step?** Yes, but not before this one. It needs the chain's code, which the annotated tag `pre-floor` keeps for good, so it can run after D3 from a `pre-floor` worktree. Its own step because it is a tracked-fixture change with its own procedure (CLAUDE.md's backup-API copy, `upgrade_allowance`, rollback mode, the sanitizer rerun from the tracked copy, the README section), `mvp-0.6 -> mvp-0.7` checks contract-completeness and may refuse on the sanitized content, and the 30-odd migration tests that read it then open it without the allowance, which the allowance's removal needs. `mvp017_route_check_replay` stays below the floor on purpose until D5 decides its old-row readers.

### (d) The deletion proof, module by module

Each module below has, at this tip: no importer outside the upgrade modules except those in (b), which this step rewrites; no function-local or `importlib` import elsewhere; no string dispatch (`METHOD_REGISTRY`, Typer decorators, `MODULE_INVENTORY`, `_reg_const`); no frontend or phone caller; no replay, rebuild or doctor path (strategy §2.6's closure, re-read here). Their only callers are `cli/app.py`'s `upgrade` and each other (each link calls its predecessor's upgrade and completion):

| module | lines | tag it activates | predecessor (refused on this code) |
|---|---|---|---|
| `ops/vault_upgrade.py` | 510 | `mvp-0.7` to `mvp-0.11` | `mvp-0.6` to `mvp-0.10` |
| `diagnosis/recurrence/upgrade.py` | 217 | `mvp-0.12` | `mvp-0.11` |
| `stuck_prompt_upgrade` .. `ad_successor_upgrade` (18 modules) | | `mvp-0.13` to `mvp-0.30` | `mvp-0.12` to `mvp-0.29` |
| `workbench_field_signals_upgrade` .. `figure_wait_upgrade` (26 modules) | | `mvp-0.31` to `mvp-0.58` | `mvp-0.30` to `mvp-0.57` |
| `facet_belief_upgrade` | 233 | `mvp-0.59` | `mvp-0.58`: **the one link that can run**. Its activation moves into the table as a row (`whole_vault_rebuild`); the module goes because nothing else of it is used |

All 47 modules, 10,073 lines (45 at the package root, 9,346 lines; `ops/vault_upgrade` and `diagnosis/recurrence/upgrade`, 727). Per-module lines are in the commit that deletes them. What the recurrence upgrade module used from `diagnosis/recurrence` (the guard, `configured_judge_model`) stays: `learnloop recurrence` commands use it.

## 2. The table

`src/learnloop/ops/upgrades.py` (396 lines with its docstrings) replaces the 47 modules:

- **`Link(tag, activate)`**, its `predecessor` the tag before it in `SUCCESSOR_CHAIN`. **`UPGRADES`** holds one row today: `Link(FACET_BELIEF_FIX_ALGORITHM_VERSION, whole_vault_rebuild)`.
- **`Activation(description, run, committed)`**: `run` derives the tag's state inside the activation's transaction; `committed` reads the receipt that transaction writes, so it is true exactly when an activation committed. Two are defined: **`idempotent_projection`** (`activate_p0_projection` from the predecessor, receipt `p0_projection_activation` at the tag: the shape of mvp-0.48 to mvp-0.58's links) and **`whole_vault_rebuild`** (`rebuild_all_derived_state`, receipt `has_whole_vault_rebuild`: RO1's and mvp-0.59's). A link that needs neither passes its own `Activation`.
- **One activation for every link** (`_activate_as_writer`, the body the 19 clones shared): under `activation_journal.completing_activation()`, in `repository.atomic()`: the predecessor's manifest frozen, `activate.run`, the registry refreshed, then (publishing) `write_activation_journal` and `publish_algorithm_version` last; the commit follows. A failure before the commit restores the predecessor's label (if the rename landed) and removes the journal.
- **`upgrade(root, *, to=LATEST, clock=None, links=None)`**: under the vault mutation lock, completes any interrupted activation, then walks the rows from the one whose predecessor is the vault's tag through `to`. A vault already at `to` gets its activation completed if it never committed ("completed the activation of ..."), else "vault is already ...". A vault at a tag no row starts from, or past `to`, is refused ("cannot upgrade from ... : only <floor> to <predecessor> upgrade to it"). A vault below the floor is refused by `load_vault` with `BelowOldestSupported`, which `upgrade` returns as the result's problem (so the command prints the route and exits 1, not a traceback). A journal the table has no row for is left standing and reported.
- **`complete_interrupted_activation(root, *, vault=None, clock=None, links=None)`**: the one completion the CLI (`cli/runtime.py`) and the sidecar (`learnloop_sidecar/context.py`) install. Without a journal it checks one path. A torn journal is removed (its fsync precedes the publication, so the config never named the target); a journal from below the floor is refused (`refuse_journal_below_floor`); a journal whose target the config does not name is removed (the publication never took effect); otherwise the row's activation completes and the journal goes. This is the chain's behaviour collapsed: the 20 completions each handed a journal not naming their tag to their predecessor, and the last (`claim_fixes_upgrade`) removed whatever was left.
- **`publish_algorithm_version`, `write_activation_journal`, `rewrite_algorithm_version`, `UpgradeResult`** move here from `regrade_contract_upgrade`, `claim_fixes_upgrade` and `ops/vault_upgrade` (`UpgradeResult` without `compatibility_delta`, which only mvp-0.8's cutover set).
- **`learnloop upgrade`** (`cli/app.py`): the 48-branch `if`, the 155-line docstring, the 20-line `--to` help and the 29 tag imports go (446 lines). It checks `--to` against `targets()` (exit 2, naming the targets and `pre-floor`, before marking the AD log), marks the AD guard's denial log, calls `upgrade`, and archives the log once after a success, as before. `tests/cli_surface.json` is unchanged (the parameters and the `mvp-0.59` default are the same).
- **`version_floor.upgrade_commands`** names the `pre-floor` route: `git worktree add ../learnloop-pre-floor pre-floor`, then `uv run --directory ../learnloop-pre-floor learnloop upgrade [--to mvp-0.7 | mvp-0.8 | mvp-0.9 first, for a vault older than the chain] --vault <root>`; the message adds "then open the vault here". `PRE_FLOOR_TAG = "pre-floor"`. The upgrade command's allowance (`version_floor.upgrading`, `_opens_the_vault_it_upgrades`) is deleted: nothing on this code can upgrade a vault below the floor, so nothing on it opens one; `may_open_below_floor` is the tests' allowance alone.

**Judgment calls.**
- The table's `links` parameter (default `None`, read as `UPGRADES` at call time) lets the tests pass a table of plain values (a failing activation, either activation kind on the head's link) instead of patching private names (T4). A test that must change what the CLI's opener completes patches the public `UPGRADES`.
- Rows below the floor are not kept, so a journal naming `mvp-0.58` as its target (an interrupted upgrade to the floor, which D1 let `learnloop upgrade` finish) is refused with the `pre-floor` route; `pre-floor`'s code finishes it.
- The upgrade command no longer opens a vault below the floor. D1's record expected the allowance to go "if the command goes"; it stays, but without a link below the floor the allowance would only open a vault the table then refuses, so it went.
- `voi_cap_report.py` drops its upgrade step instead of upgrading through the table: every vault this code opens is past mvp-0.21.
- `LEGACY_ALGORITHM_VERSION` (`"mvp-0.6"`) moves to `algorithm_versions`: the recall-calibration harness still builds its scratch vault there (ledger D-24, unchanged).
- The Version Registry's algorithm row was a paragraph of tag history up to mvp-0.27 that named `learnloop upgrade` per tag; it is now the current tag and a pointer to Algorithm Versions' per-tag table, and the note gains rows for the floor and the table.

## 3. Tests

**Kept, parametrized over each row on one small vault** (`tests/test_upgrades.py`, 549 lines; `create_basic_vault` at the predecessor with two answers): the table is the chain from the floor (`EXPECTED_ACTIVATIONS`, the one test row a tag adds); a link activates from its predecessor and a re-run does nothing (receipt count unchanged); a vault born at the tag completes its activation once; the floor reaches each tag through the table; jumps are refused and change nothing (a vault below the floor, at the table and at the command; a vault at a tag no row starts from); a target the table has no row for is refused before any step; the command reaches the tag by name and the latest by default; the journal is written before the publication and the commit follows it (another connection sees no receipt at publication); a failure in the activation, before the rename or after it leaves the predecessor's config readable, no journal and the state unchanged, and the upgrade runs again; recovery after a real death (forked child, `os._exit`) after the publication (the next command completes it, state equal to a clean upgrade) and after the journal before the publication (journal removed, predecessor kept); a journal left after the commit is removed without a second activation; a torn journal is removed; the upgrade command completes its own interrupted activation; every opener that may write (`open_vault_repository`, `vault_repository`, the sidecar's start, a CLI command) completes it; an activation that cannot complete stops each opener and keeps the journal; an opener in a process that installed no completion refuses; the CLI and the sidecar install the table's completion (a fresh process completes a journal, the vault layer alone refuses); attaches that never write refuse; an MCP server already attached stops serving; the phone host refuses to start; each activation kind commits its own receipt once. 34 tests.
- **The AD guard's denial mark** stays in `tests/test_ad_denial_log.py`, its upgrade tests now over each row on the small vault (was a placement vault at mvp-0.34/0.35 through the chain): archived once on success, the floor walked to each tag archives once after the final step, a refused or failed upgrade leaves the log, no log archives nothing, a second archive in the same second gets the counter (now the same link re-run on the relabelled vault, since one row cannot chain twice), a denial after the upgrade returned stays live, an append in flight never writes into the archive, an unmarked upgrade archives nothing.
- **`tests/test_version_floor.py`**: `learnloop upgrade` joins the doors (exit 1, the message's three parts and the `pre-floor` commands); the upgrade command's success below the floor and its allowance test go; the command now refuses a journal from below the floor with the route; the commands test pins the `pre-floor` route.

**Deleted, their only subject a deleted link** (22 files, 8,490 lines out, 729 in, across 76 test files):
- whole files: `test_mvp09_upgrade` .. `test_mvp024_upgrade` (14), `test_method_explicit_upgrade`, `test_regrade_contract_upgrade`, `test_km2_activation`, `test_p0_cutover_mvp08`, `test_rbeq_pr2_landing` (mvp-0.34's journal), and the helpers `rbeq_pr2_landing_helpers`, `batch3_landing_helpers`, `lp_claim_fixes_rereview_helpers` (what was left was one or two constants, inlined);
- per file, the upgrade halves: each successor's upgrade from its predecessor and through the chain, its refusals, its journal recovery and opener tests, its CLI `--to` test and its `test_the_openers_install_this_links_completion` (in `test_ad23_successor`, `test_attempt_content_state_successor`, `test_batch3_landing`, `test_cold_retry_reschedule`, `test_curriculum_c1_landing`, `test_curriculum_c1_plan_follows_path`, `test_data_capture_successor`, `test_facet_belief_successor`, `test_field_workbench_signals`, `test_figure_wait_successor`, `test_followup_successor`, `test_help_fold_attach_successor`, `test_ih5_successor`, `test_intent_codex_rereview`, `test_learner_report_superseded`, `test_learner_text_gaps_flow`, `test_lp_claim_fixes`, `test_lp_claim_fixes_rereview`, `test_lp_claim_fixes_review`, `test_mobile_v3_successor`, `test_mvp017_route_check_replay`, `test_placement_unevidenced_return`, `test_plan_follows_path`, `test_pr4_superseded_claims_landing`, `test_reader_ca2_one_ask`, `test_reader_followups_successor`, `test_rebuild_equivalence_review`, `test_recurrence_commands`, `test_ro1/4/5/6_successor`, `test_rofu_successor`, `test_serve_eligibility_review`, `test_sg_successor`, `test_te3a/te3b_successor`, `test_teacher_te1_successor`, `test_teacher_te1b_suggestions`, `test_teacher_te2_successor`);
- the 23 `inspect.getsource` assertions that named the chain's latest module (deleted with their tests, not re-pointed, T4);
- the "one constant" tests keep their chain assertions and lose only `UPGRADE_PREDECESSOR == PREDECESSOR` (the module constant is gone).
- The script that deleted named top-level definitions (an AST span cut, `drop_defs.py` in the scratch dir) and `ruff check --fix --select F401` (the imports this left unused) are the mechanical parts; every list of names was chosen by reading the file.

**Changed assertions, and why** (every other assertion untouched):
- `test_recurrence_commands`: the guard tests lose their `upgrade_to_mvp012` refusals and successes (the mvp-0.12 switch was the upgrade's gate, which is gone) and keep every guard assertion; one trailing "the upgrade now succeeds" became the guard's own `guard_status(...)["passed"] is True` for the same model. The tests whose subject was the switch or the advisory upgrade (16) are deleted.
- `test_reader_recap_review_r3` (two tests): the mvp-0.26 upgrade that held an uncited regrade is replaced by the vault moved to the head and a whole-vault rebuild, which holds the same epochs (replay holds a contract-unrecorded epoch at every tag from mvp-0.26). Same assertions; passes. `regrade_contract_upgrade_helpers`' docstring names its one user.
- `test_route_rules_in_grader::test_f5`, `test_required_method_grading::test_grades_recorded_at_the_predecessor_replay_unchanged_at_the_successor`, `test_data_capture_successor::test_the_outcomes_cache_is_rebuilt_under_the_vaults_version`: the upgrade that moved the vault to the successor is a retag to that successor (the assertions are about history read at the tag, not the activation).
- `test_placement_unevidenced_return::test_a_shadow_rebuild_reports_nothing_moved_for_the_shape`: retag plus a whole-vault rebuild at the tag in place of the upgrade (with the retag alone the live facet rows were the predecessor's projection and the shadow showed 2 changed; the activation is what re-projected them).

**Left for D7** (a successor file's other half: the behaviour, its switch, the predecessor served exactly): every `test_*_successor.py` above keeps its constant, switch, gate, replay and predecessor tests; the same for the successor-like files (`test_lp_claim_fixes*`, `test_rebuild_equivalence_review`, `test_learner_report_superseded`, `test_cold_retry_reschedule`, `test_curriculum_c1_*`, `test_plan_follows_path`, `test_field_workbench_signals`, `test_reader_ca2_one_ask`, `test_batch3_landing`, `test_help_fold_attach_successor`, `test_attempt_content_state_successor`, `test_reader_followups_successor`, `test_teacher_te1*`, `test_placement_unevidenced_return`, `test_ro1_upgrade_report`, `test_regrade_contract_successor`).

## 4. The census, recounted

D1's plugin rebuilt as described in its record (a scratch pytest plugin wrapping `version_floor.may_open_below_floor`, and `shadow_rebuild`'s imported name, that records each test the allowance lets open a vault below the floor), over the whole landing selection in 14 chunks of 100 files plus the arc-close lane, at `1e8108137e`: **4,834 test cases in 464 files** (D1, at its own tip: 5,421 in 507). Between D1's census and this step's base other steps landed (d2c's builders among them), so not all of the drop is this step's: in the files this step touched, the count fell by 376 cases and 19 files left the census (the deleted chain walks and per-link suites, and the upgrade halves of the successor files). `test_upgrades.py` adds none (it builds every vault at or above the floor; the one below-floor vault of its jump test is refused, as intended). What remains is D7's (successor behaviour halves), D2b part 2's and the re-tagging step's (builders and helpers that set an old tag), D5's (`pin_old_basic_vault`) and the fixture step's (§1 (c)).

## 5. Proof

**(a) The kept tests** pass: `tests/test_upgrades.py` (34), `tests/test_version_floor.py` (23), `tests/test_ad_denial_log.py` (25), and every edited test file (44 files: 621 passed, 12 skipped, 3 xfailed, the known strict xfails, after one fix in `test_placement_unevidenced_return`, §3). Fail-first: the table's tests have no base to fail against (they test new code); the door that is new, `learnloop upgrade` refusing a vault below the floor with the `pre-floor` route, contradicts base's behaviour, which D1's `test_the_upgrade_command_still_upgrades_a_vault_below_the_floor` pinned (base's command upgraded it); not run against base here.

**(b) The owner's copies, through the table and through the base.** `/home/saturn/Documents/thinking/learnanything-ad1/fixtures-local/owner-copies-mvp058` (three vaults at `mvp-0.58`), copied twice with `copy_tree_with_databases` under `fixtures-local/d3/{base,table}/`. The `base` copies were upgraded by main's code at `1da959e7d7` (a `git archive` of its `src/` first on `PYTHONPATH`, the same environment), the `table` copies by this branch: `learnloop upgrade --vault <copy>`, exit 0, "mvp-0.58 -> mvp-0.59" on all six (1 to 3 s each). Then `learnloop rebuild --shadow --json` on each with its own code, and a row-by-row comparison of every `DERIVED` table plus `derived_state_rebuilds` between the two upgrades of each vault. Counts only; the copies are deleted.

| | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| shadow reports, base vs table, apart from hashes, the marker id and `as_of` | identical | identical | identical |
| `schedule_effects` (moved, newly due, no longer due), both | 0, 0, 0 | 0, 0, 0 | 0, 0, 0 |
| shadow facet / mastery / schedule changed, both | 0 / 0 / 0 (80 / 21 / 99 unchanged) | 0 / 0 / 0 (3 / 18 / 77) | 0 / 0 / 0 (7 / 34 / 32) |
| live database unchanged by the shadow, both | yes | yes | yes |
| derived tables compared; rows | 29; 1,836 | 29; 624 | 29; 4,722 |
| tables that differ, and only in | 4: `derived_state_rebuilds` (`id`, `created_at`), `facet_capability_evidence` (`created_at`, `updated_at`), `facet_recall_state` (`updated_at`), `subject_identifiability_watermarks` (`checked_at`) | the same 4, the same columns | the same 4, the same columns |

Every other column of those tables is equal row for row: the two upgrades differ only in write times and a surrogate id.

**(c) A vault below the floor gets the new message at every door.** `tests/test_version_floor.py`'s doors (load_vault, `config effective`, `rebuild-derived-state`, `rebuild --shadow`, doctor, the sidecar's `initialize`, the MCP and phone hosts' attach, and now `learnloop upgrade`) each assert the tag, the floor, `git worktree add ../learnloop-pre-floor pre-floor` and `uv run --directory ../learnloop-pre-floor learnloop upgrade --vault <root>`. On one of the copies above relabelled `mvp-0.57`, the CLI: `config effective`, `doctor`, `rebuild --shadow --json`, `rebuild-derived-state --json` exit 1 with `BelowOldestSupported` (as D1 left them: typer shows the exception) and the message's tag, floor and both commands; `upgrade` and `upgrade --to mvp-0.59` exit 1 with "Vault not upgraded (currently mvp-0.57):" and the same message, no traceback.

**(d) The measures** (`scripts/refactor_measures.py`, before at `1da959e7d7`, after at the tip):

| measure | before | after |
|---|---|---|
| root `*_upgrade.py`; all upgrade modules (lines) | 45; 47 (10,073) | 0; 1 (396, `ops/upgrades.py`) |
| first-level root modules in `src/learnloop` | 80 | 35 |
| `mvp-0.N` literals: code / docstring / comment | 269 / 960 / 797 | 192 / 406 / 643 |
| Python files, four packages; raw lines | 1,279; 624,131 | 1,233; 613,973 |
| upgrade and successor test files (lines) | 38 (9,185) | 23 (4,097) |
| test Python files (`test_*`); lines | 1,856 (1,408); 477,104 | 1,835 (1,390); 469,410 |
| frozen `*_VERSIONS` set assertions (files); test files with a latest pin | 48 (46); 42 | 34 (34); 32 |
| functions over 200 lines; comment lines naming a stage artifact | 83; 2,424 | 82; 2,398 |
| import edges only inside functions | 2,843 | 2,792 |
| vault notes; generated | 2,263; 2,166 | 2,217; 2,120 |

The structure golden is lowered with `--write` (root modules 80 to 35, functions over 200 lines 83 to 82, stage comments 2,424 to 2,398, stage-named test files 185 to 184; no number rose). One comment in the new module ("never landed") matched the stage-artifact pattern and was reworded.

## 6. Gates run

All under the empty-home wrapper in 5 GB scopes.
- **Every test file** of the landing selection (`-m "not arc_close"`, 1,390 files in 14 chunks of 100 at `-n 4` behind `flock /tmp/learnloop-fullsuite.lock`, with the census plugin), at `1e8108137e`: 30,419 passed, 104 skipped, 12 xfailed (the known strict xfails), no failure or error. `scripts/affected_tests.py` against the base selects the whole suite (`pyproject.toml` and `version_floor.py`, which `tests/conftest.py` imports, changed), so this run is the affected selection; it covers every file this step added or edited, `test_identity_pins` (no pin moved, nothing `--write`), `test_retired_config_identities`, `test_architecture`, `test_test_layout`, `test_effective_defaults_golden` (golden unchanged), `test_cli_help_snapshot` (`cli_surface.json` unchanged), `test_structure_ratchets` (golden lowered), `test_e0_isolation` and `test_module_catalog_inventory` (after the regeneration).
- **Arc-close lane** (`-m arc_close`, its 5 files): 24 passed, 36 xfailed (`test_ad23_sim`'s pre-registered strict xfails).
- `ruff check`: clean. `lint-imports --no-cache`: 42 kept, 0 broken (no ignore line was needed for `ops.upgrades`; the three `ops.vault_upgrade` / `recall_calibration` lines went). `scripts/check_gate_partition.py`: 30,655 collected, landing 30,595 + arc_close 60.
- Vault: the four validators pass (`module_validate`, `db_validate_reference`, `desktop_validate`, `validate_vault`). References regenerated once after the source and docs commits (`09ef3536a6`: 128 notes, the new `ops/upgrades` note, and the 47 deleted modules' notes removed by hand, which the module generator does not delete and `module_validate`/`validate_vault` flagged); a second `generate_all.py` run changed nothing.
- Not run (the orchestrator's): the durability lane, `--fresh-connections`, vitest, the owner lane.

## 7. Bug ledger

No row added: the step found no bug. The orphans below are dead code, not wrong behaviour.

## 8. Open items

- **The orchestrator creates the annotated tag `pre-floor`** at this landing, on the last commit before it (main `1da959e7d7` or whatever main is when D3 lands, as long as the chain is still in it). Every refusal now names it; until it exists the route's first command fails. No agent created it.
- **Upgrading `fixtures/migration_head` to the floor**: its own step, after D3, from a `pre-floor` worktree (§1 (c)). It empties the census's fixture rows and is needed before the test allowance can go.
- **Now unused in `src/`** (only the deleted links called them; tests may still): `attempts.attempts.unrecorded_epoch_attempts` (the mvp-0.26 activation's scan) and `learner.mastery.learning_objects_with_covering_claims` (the mvp-0.33 activation's). Each needs its own deletion proof (tests, `importlib`) before it goes; for arc C's or D5's list.
- **D7** (successor files' behaviour halves, §3): every kept `test_*_successor.py` and successor-like file still builds the predecessor below the floor through `set_algorithm_version` and the allowance.
- **The parallel test re-tagging step**: this step edited, in files that name old tags, only the upgrade halves and imports (`test_lp_claim_fixes*`, `test_rebuild_equivalence_review`, `test_learner_report_superseded`, `test_cold_retry_reschedule`, `test_curriculum_c1_*`, `test_plan_follows_path`, `test_field_workbench_signals`, `test_reader_ca2_one_ask`, `test_batch3_landing`, `test_recurrence_commands`, `test_route_rules_in_grader`, `test_required_method_grading`, `test_serve_eligibility_review`, `test_intent_codex_rereview`, `test_learner_text_gaps_flow`, `test_teacher_te1b_suggestions`, `test_pr4_superseded_claims_landing`, `test_reader_recap_review_r3`, `test_mvp017_route_check_replay`, `test_facet_locks_landing`, `test_ro2_ad_raw_document_reads`); a merge may conflict there. `followups_nov2_help_fold_helpers` and three test files now import `rewrite_algorithm_version` from `learnloop.ops.upgrades`.
- **The ingestion step and the test-draw sweep**: no file of theirs touched.
- **The CLI still shows `BelowOldestSupported` as a traceback** at every door but `upgrade` (D1's call, unchanged).
- **Strategy and measures**: the strategy's D3 text says "42 modules, about 8,900 lines"; at this tip it was 47 and 10,073. `scripts/refactor_measures.py` counts `ops/upgrades.py` as "all upgrade modules: 1" (its name contains `upgrade`).

## 9. Not verified

- The desktop's display of the new message (no GUI); the TUI beyond `load_vault`.
- The route itself end to end (`git worktree add ... pre-floor`, `uv run --directory`): the tag does not exist yet.
- The durability lane, `--fresh-connections` and vitest (the orchestrator's).
