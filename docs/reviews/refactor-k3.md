# Refactor K3.1-K3.3: ingest fixes that cost money or coverage

Branch `refactor/k3-ingest-fixes`, based on `2bc93d4d2b` (K0 landed: identity pins). Steps K3.1, K3.2 and K3.3 of
arc K (`docs/specs/refactor_strategy_v3.md` §2.17), specified in `docs/reviews/k2-ingestion-strategy-2026-11-11.md`
§3.1 from the K2 map's KX3 and KB7 (K3.1), KX1 (K3.2) and KM3 (K3.3). K3.4 and K3.5 are not here.

Rules held: each step starts from a test that fails on the base; no learner scoring change, no successor, no
`algorithm_version` change, no migration; no live model call; the append paths that pass no unit filter keep
their manifest bytes (pinned, K3.2). Each step is its own commit series and lands alone.

## K3.1 The right inventory row

**Problem.** A unit keeps one inventory row per text (semantic hash), prompt label, provider and model, so a
re-read that changed the text, a prompt bump or a model change adds a row beside the old one. Synthesis took the
oldest row in the preferred profile (`_best_inventory`, a stable sort over rows ordered by `created_at`), so the
new row was paid for and ignored. `source_coverage.py` held a copy of the same function.

**Failing test.** `tests/test_inventory_choice.py`, run red on the base sources (the source files swapped back to
`HEAD` and the test re-run, then restored):
- `test_a_reinventory_by_a_newer_model_reaches_the_synthesis_prompt`: red (the prompt held `summary of
  chapter_symmetry`, the old row), green after.
- `test_a_row_under_the_current_prompt_label_beats_an_older_label`: red (the old label's row reached the prompt),
  green after; it also checks the chosen row's id and extraction and the manifest's label.
- `test_coverage_reads_the_row_synthesis_reads`: red (synthesis read the old row's claims), green after.
- three unit tests of the ordering (`test_current_text_wins_...`, `test_current_prompt_wins_...`,
  `test_newest_breaks_ties_...`): red on the base (no `best_inventory`), green after.

**What changed.**

| File | What |
| --- | --- |
| `src/learnloop/content/synthesis/source_unit_inventory.py` | `best_inventory(rows, unit_id, *, semantic_hash, prompt_version, provider, model, profile)`: the profile rule filters first (unchanged), then the current semantic hash, the current prompt label, the current provider and model, the newest. `choose_unit_inventory` (one effective unit of an IR under today's label and route), `current_unit_semantic_hash`, `current_inventory_identity(config)` (the `canonical_ingest` route's provider type and model, moved here from `jobs.default_inventory_identity`, which now calls it) |
| `src/learnloop/content/synthesis/source_set_synthesis.py` | `_collect_inputs` chooses through `choose_unit_inventory`; `_best_inventory` deleted; `_SynthesisInputs.inventory_rows` ("revision:unit" -> the chosen row's id and extraction) |
| `src/learnloop/content/synthesis/source_coverage.py` | its `_best_inventory` copy deleted; uses `choose_unit_inventory` |
| `src/learnloop/content/pipeline/jobs.py` | `default_inventory_identity` delegates to `current_inventory_identity` |

**One deviation from the strategy, on purpose.** The strategy says "the entry carries the row's own extraction id
and row id". The entries are rendered into the synthesis and append prompts whole (`asdict(context)`), so a new key
in them moves every pass checkpoint and re-pays every shard on every vault; and replacing the entry's
`extraction_id` with an older reading's id would make its citations resolve against a reading the run doesn't hold.
So the row's id and extraction ride beside the entries in `_SynthesisInputs.inventory_rows`, read by nothing yet;
K2.3 (the manifest gains exact inputs) is where they enter the manifest, with its deliberate pin bump.

**P-spend.** On fresh backup-API copies of the Nov 9 backup: of the units with inventory rows (about 10^2 over
the three vaults), none holds a second row, so no unit's chosen row changes and no manifest moves. The fix pays off
at the next prompt bump, model change or text-changing re-read.

**Pins.** Unchanged (the K3.2 `--write` added two pins and moved none).

## K3.2 Keep-ahead appends only the new units

**Problem.** The planner chose the new chapter's units, but the `bootstrap_synthesis` job it queued carried no
unit or revision filter; `handle_append_synthesis` passed `new_revision_ids=None`, so `_append` took every
selected revision, and a book is one revision. Every keep-ahead append re-sent the inventory of every chapter built
so far, and a book's total input grew quadratically with chapters read.

**Failing test.** `tests/test_keep_ahead_append_units.py::test_the_second_build_appends_only_its_own_chapter`:
a book through Add and one keep-ahead step with the house fakes, recording the append context. Red on the base (the
chapter-3 append sent units `u2, u3, u4`, chapters 1-3), green after (`u4` only). It also checks the queued
payload's `new_unit_ids`. `test_the_unit_filter_applies_per_revision` covers the filter alone.

**What changed.**

| File | What |
| --- | --- |
| `src/learnloop/content/pipeline/add_source.py` | the planner's `bootstrap_synthesis` payload gains `new_unit_ids: {revision_id: unit_ids}` (a first build, which bootstraps, ignores it) |
| `src/learnloop/content/pipeline/jobs.py` | `handle_append_synthesis` passes the payload's `new_unit_ids` (absent: `None`, as before) |
| `src/learnloop/content/synthesis/source_append.py` | `select_new_inventories(entries, revision_ids, new_unit_ids)`: a revision named in the filter sends only its listed units (a merged unit when any member is listed), any other revision sends all of its own; `append_scope` (the manifest scope, extracted) records `new_unit_ids` only when given; `append_source`, `_append` and `plan_append_embedding` take `new_unit_ids` |
| `tests/identity_pins_helpers.py`, `tests/goldens/identities.toml` | new site `K3.2`: `append_scope` with no unit filter, both configs |

The filter is keyed by revision because unit ids repeat across books (`u1`, `u2`, ...), and K3.3 passes it for a
collection of several.

**P-pins.** `K3.2.scope.init` and `K3.2.scope.legacy` pin the append scope with no unit filter. Their digests equal
the base commit's inline construction, recomputed by a scratch script that copies the base lines; `--write` added
those two lines and changed no other pin. So the RPC append paths, revision refresh and jobs queued before this
change keep their manifests, and their completed runs are still reused.

**P-spend.** On the copy's one source large enough for two builds (arxiv_v2; builds split by the projection rule:
reading order, 40,000 source tokens per build), the second append's input built by the real `append_source` with
the model call replaced by a recorder: inventory input 3.7x its new units' inventories before (about 10^5 tokens),
1.0x after (about 3x10^4); the whole prompt about 2.75x smaller (the neighbourhood is capped either way). Over a
textbook the projection stays the map's estimate (§7: about 10^7-10^8 inventory tokens before, 10^6-10^7 after).

## K3.3 The collection build sends every missing unit

**Problem.** `build_study_map` (the collection "synthesize" RPC) called a member new only when its revision had no
inventory row at all. One cached unit made the whole revision old: its newly selected units got no inventory job,
and when another member was new, `new_revision_ids` left the revision out of the append; otherwise synthesis
skipped the units with no row without saying so.

**Failing test.** `tests/test_collection_append_units.py`, run red on the base handler and `jobs.py`:
- `test_new_units_of_a_partly_inventoried_member_are_inventoried_and_appended`: an applied map, then a second
  book whose `u1` is inventoried and whose `u2`, `u3` were just added. Red on the base (no inventory job: the
  member list was empty), green after: the RPC inventories `u2` and `u3`, pins `rev_more` with
  `new_unit_ids = {rev_more: [u2, u3]}`, and the real batch (house fakes) inventories both and sends exactly them
  to the append.
- `test_a_wholly_new_member_keeps_the_unfiltered_append`: red on the base only because the base passes no
  `new_unit_ids` argument; it guards that a wholly new member sends no filter.
- `test_inventoried_unit_ids_counts_merged_members`: passes on both (a helper test).

**What changed.**

| File | What |
| --- | --- |
| `src/learnloop_sidecar/handlers/ingest.py` | append mode decides newness per unit: a scoped unit with no row is inventoried, its revision joins `new_revision_ids`, and a partly inventoried revision is narrowed to its new units in `new_unit_ids`; bootstrap mode unchanged |
| `src/learnloop/content/synthesis/source_unit_inventory.py` | `inventoried_unit_ids(rows)`: the units the rows cover, members of merged rows included |
| `src/learnloop/content/pipeline/jobs.py` | `enqueue_source_set_append(new_unit_ids=...)` writes it into the append payload only when given |

**"Current row" read as "any row for the unit".** The strategy says "a unit without a current row is
inventoried". Reading "current" as "for today's text" would make every re-read that changed a unit's text
re-inventory and re-append that unit at the next collection build, a spend the strategy didn't count and material
the map may already hold. So a unit counts as inventoried when any row of its revision covers it; which of its rows
synthesis reads is K3.1's choice. The owner can choose the stricter reading.

**P-spend.** None saved, as the strategy says; coverage is gained. The copies hold no partly inventoried
collection member, so nothing was measured.

## Vault

No hand-written note describes which inventory row synthesis reads or what an append sends beyond
`Workflows/Build a Study Map.md:60` ("Append mode limits regeneration to the affected neighborhood"), which these
steps don't make false; its other half (the bootstrap-or-append rule) is K2.4's fix in the strategy's vault plan.
The new workflow note "Add a Source and Automatic Builds" is shared by K3.2 and K2.12 in that plan and is left for
K2.12, which adds the decisions it describes. The reference notes were regenerated once after the source commits
(`a10f883d1f`, 30 generated notes); a second `generate_all.py` run changed nothing.

## Gates

- Targeted tests (`scripts/affected_tests.py` on each diff, plus every added or edited test file,
  `test_identity_pins`, `test_retired_config_identities`, `test_architecture`, `test_test_layout`), `-m "not
  arc_close"`, under the 5 GB cap in chunks of 100 files at `-n 4` (one run of 697 files at `-n 6` hit the cap):
  - K3.1 and K3.2 together (diff from `2bc93d4d2b`, 697 files): 13,078 passed; one collection error, the K3.3
    fail-first test, then untracked and red by design.
  - K3.3 (diff from the K3.2 commit, 774 files): 14,039 passed.
- `lint-imports --no-cache`: 42 kept. `ruff check`: clean.
- The four vault validators pass (`db_validate_reference.py`, `module_validate.py`, `desktop_validate.py`,
  `validate_vault.py`); `scripts/check_gate_partition.py`: 30,956 collected, landing 30,896 + arc_close 60.
- No full suite (the orchestrator's landing gate).

## Open items

- **For the owner:** K3.3's reading of "current row" (any row, not one for today's text), above.
- **K2.3:** `_SynthesisInputs.inventory_rows` (each unit's chosen row id and extraction) waits to enter the manifest
  there, with the deliberate pin bump.
- **Keep-ahead reconciles against the applied map only.** An append from chapter 3 on leaves concepts pending review
  (map KX4), and K3.2 no longer re-sends earlier chapters, so a later chapter's append sees an earlier chapter's
  pending material in neither its new inventories nor its neighbourhood. Before K3.2 the re-sent inventories made
  each append re-propose earlier chapters' concepts, so pending duplicates were the cost; now a later chapter may
  mint a concept an earlier chapter's pending proposal also holds. The owner's call on auto-applying new coverage
  (strategy §5) settles it.
- **The CLI append** (`learnloop synthesize --mode auto` without `--new-revision`) still sends every revision's
  inventories; it was out of K3.2's scope (no planner chose its units).
- **Not verified:** K3.2's P-spend splits builds by the projection rule, not the planner's `outline_chapters`
  grouping; the textbook-scale saving remains the map's projection.
