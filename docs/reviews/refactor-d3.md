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
