# Notebook authoring H2–H4

Branch `notebook/authoring-h2-h4`. The base and current tip are
`9038b096e7446d5f433f95d881de7e7c1bd0da15`. The changes are uncommitted.
The prepared venv ran the static checks. The orchestrator owns the external
report and socket comparisons, post-commit identity checks and landing gate.

## Decisions to review

- Section 15 of this revision contains the **H3** acceptance line. There are no
  individual H2 or H4 lines or full H2–H12 list under Track H. The stage names
  are in `docs/reviews/refactor-status.md`. H2 follows §11.1 and H4 follows
  §§6, 11.2, 11.5 and 11.10. The owner-side declarations below are a proposed
  source format for NA2 to reconcile with its SDK. B7's lesson loader has its
  own conventions for commit names and disabled cells.
- Write and edit are Python tools for a caller that already owns a job directory.
  The catalog has a standalone module entry for generating ordinary files.
  The only change to the LearnLoop CLI is the additional `contract` scope of
  the existing check command.
- H3 exposes **static candidates** for inspection. Their execution and render
  fields say `pending`. H5 must execute and render the extracted slice itself
  before it can become a verified exemplar. Search is lexical and its purpose
  text is deterministic. Model-written summaries and embeddings require a later
  authorized stage.
- H4 emits a **static manifest**. Its coverage rows describe work owed.
  Runtime fingerprints, interaction traces, reviewer rounds, screenshot completeness,
  oracle results and publication belong to later stages. A clean static report
  explicitly says review is incomplete.

## H2 — writing cells

`cell_writer.write_cells(scratch, [(name, code), ...], held=...)` creates
`activity.py`. The caller supplies the job directory and any held names. The
author supplies ordered pairs. The pinned adapter calls marimo's
`generate_filecontents`, parses the generated source back, checks names, order
and disabled flags, and inspects the graph. Marimo supplies signatures, returns
and promotion to function/class cells. For a promoted definition whose own
name differs from the requested cell name, a trailing Python comment preserves
marimo's ordinary named-cell representation.

The writer applies the installed default rules used by `marimo check` to the IR
in H1's isolated, write-denying worker. It drives the in-memory rules serially,
without the CLI's file discovery, formatting fixes or asyncio socketpair.
`test_generated_file_passes_pinned_marimo_check` is the separate comparison
with the actual strict CLI. The worker never invokes notebook functions.

The scratch path is opened component by component with no-follow directory
descriptors. Creation is exclusive. Edits lock the directory, read a regular
single-link artifact, check its canonical writer representation, regenerate
signatures across the whole graph, and atomically replace the artifact after
validation. An edit preserves names, order and held cells. These tools take no
model-supplied destination filename.

**Acceptance tests** in `tests/test_notebook_cell_writer.py` cover repeated
generation, cross-cell dependencies, both kinds of function cell, stable edits,
traversal, symlinks, hardlinks, existing files, malformed inputs, duplicate
definitions, cycles, an empty cell rejected by marimo lint, and non-execution.
The H4 writer-to-checker test exercises a held reveal through an edit.

## H3 — capability cards and example slices

`python -m learnloop.notebook_authoring.catalog NEW_DIRECTORY` builds the static
folder. The generator reads the installed extra's exact requirements from
LearnLoop metadata and verifies the installed versions. This checkout declares
marimo 0.25.2 and wigglystuff 0.6.0.

The wheel sources supply public exports, constructor and method declarations,
docstrings, synced trait declarations including widget-parent traits, package
versions, relative filenames, line numbers and source hashes. The extractor
reads the implementation of re-exports, including drawdata's ScatterWidget.
For classes that inherit their constructor it reads the installed class signature.
The catalog also has marimo layout, state, control, cache and SQL cards, marimo's
installed authoring guidance, an installed distribution list, and LearnLoop
recipes. Optional chart backends are identified on their cards. The folder
includes the licences shipped by the source distributions.

An export added to the widget or marimo UI roster is discovered automatically.
Gaps such as an affordance, typed alternative, fallback, prerequisite or
deliberate exclusion live in **one entry** in `tool_notes.TOOL_NOTES`. A new
named tool from another pinned module can give its `api_source` (module,
definition) and its supplementary fields in that same entry. Extraction failures
or stale notes fail generation. A normal dependency bump updates the extra,
lock and notices. Parser admission derives from the installed requirement.
Regenerate into a fresh directory and rerun the coverage, pin and exemplar tests.

The wigglystuff wheel here omits its reference pages and upstream demos. The
generator reads reference pages and demos when packaged, plus installed marimo
tutorials and Python examples in widget docstrings. A docstring fence gets a
marimo wrapper and the tool import. Each candidate records its focal cell,
transitive ancestors, options, source order, tools, line count, origin, version
and demo hash. Markdown used by the focal code stays in the closure. Independent
markdown does not enter it. `read_card`, budgeted `search_examples` and
`read_example` (ancestors or demo) work on the in-memory catalog. Static folder
readers can follow the file references in `index.json`.

**Acceptance tests** in `tests/test_notebook_catalog.py` compare the
generated inventory against both packages' actual public exports, check source
hashes, inherited traits, signatures, a single-entry extension, package/lock/
notice/parser agreement and a synthetic next pin. They check an aliased widget
and a read in another cell, omission of unrelated cells, search budgets, installed
examples, and on-disk card and slice content. The single-entry test also
retrieves an example that imports the added tool by its source path and alias.

**Measured export.** The fresh folder held 136 cards, 100 demo sources and 179
candidate slices. The cards comprise 75 wigglystuff exports, 37 marimo UI
exports, 13 other marimo APIs, four installed marimo guidance documents, six
LearnLoop recipes and one environment card. A separate read of `index.json`
and the card files compared their names with the installed packages' public
exports. **Exports without a card: none. Explicit exclusions: none.** All 112
export cards have a signature. H5 still owes execution and rendering for the slices.

## H4 — static contract and coverage

`learnloop notebook check PATH/TO/activity.py --scope contract --out REPORT_DIR`
uses H1's external, fresh-report output policy and exit conventions. The fixed
input companions are `key.py` and an optional `manifest.json` in the activity
directory. The command writes `contract.json`, `contract.txt`, and a fresh
`manifest.json`. It reads source bytes under no-follow descriptors.

A cell assigns a literal `contract` dictionary with a target (`facet`,
`cold_item_family`), `intents` by cell name, `assumptions` (statement and
defined handle), `source_anchors`, and `fidelity`. `reveal_units` maps an
output or cell to its kind. A named `ll.hint_unit` can supply its kind directly.
The checker reads unconditional, direct SDK calls in marimo's parsed cells.
It checks draw, commit, reveal, hint_unit, mask and explain declarations,
commit and cell identities, literal prompt, response kind, scalar unit and
precision, facets, gate references and mask targets. A gate protects only its
declared reveal. Marimo's graph propagates held status and identifies visible
reads of reveal-derived data or committed answers. This includes reads in the cell that creates the commit, and reveal units declared
in metadata even when the SDK release call is missing. Unknown declared reveal
outputs are findings. Static key references in
the client are findings. These are syntactic and graph checks. They cannot
establish information-flow safety for arbitrary Python or visual derivability.

Commits and masks require a sidecar key. The checker parses its AST for
`generate(seed)`, `check(draw, answer)`, named `mutants`, and `mask_values` for
the declared masks. Help-only activities may omit the key. Rubric activities
may declare empty mutants. Only mutant identifiers and the key revision hash
leave key inspection. The checker does not check the answer or evaluate an
expression in either file.

The manifest binds raw activity/key bytes, the parser and notebook pins, named
cells, and locked and per-gate correct, mutant, junk and free-text states. Each
cell/state has layout, visual and teaching obligations, with empty round lists.
It records outstanding interaction coverage and empty screenshots, oracle and
execution receipts. Supplying a static manifest from a prior check verifies
its schema, revision and exact coverage, and rejects claimed acceptance,
fabricated results and missing entries. It is an input to future review work.

**Acceptance tests** in `tests/test_notebook_contract.py` include broken
notebooks for metadata, names, SDK signatures and dynamic declarations, stale
gate/output/mask references, visible dataflow, client key access, missing
key functions and mask values. The file covers help-only, rubric and held
commits, a trap in each artifact, CLI refusal of a linked key, and stale,
incomplete and fabricated manifests. The CLI-routing test captures the output
writer to keep its synthetic files inside the checkout. Existing H1 output-path
tests cover the shared writer's actual external directories. An additional H4
CLI test reads back all three report files, then submits the old manifest
against an edited activity. It requires an external temporary directory.

## What consumes the work

| Later stage | Handoff |
|---|---|
| H5 | Run the named revision and the example slice in the real sandbox. Drive submissions, including every declared mutant, through the host and bind receipts to the revision. |
| H6 | Use stable names, dependency edges and the cell/state obligations for layout, palette, viewport, control-extreme and pivotal-value checks. |
| H7 | Route review with named cells, intents, target, independent questions/oracles and actual screenshots. Represent unavailable routes explicitly. |
| H8 | Validate actual rounds, interaction coverage, independent reference, screenshot hashes and admission before acceptance and promotion. |
| H9 | Give the durable author job a trusted scratch directory and the write/edit, card lookup and example operations. Carry the last verified revision across retries. |
| H10 | Add authorized retrieval, protected-source filters, verification-aware exemplar selection and embeddings. |
| H11 | Run the eval set on changed pins or harness versions. Keep private examples outside the public tree. |
| H12 | Join the owner console's verdicts to revision, state, cell, layer and round. |
| NA2 | Implement the actual SDK, sidecar key protocol, gate state machine, blind grading and receipts. Reconcile the source declaration spelling and B7's hosting convention. |
| NA3 | Use mask targets, key-side mask declarations and mutant IDs for the future instrument checks. Derivability, human-only evidence, coldness and posterior invariance remain NA3 gates. |
| NA4 / TE9 | Use named revisions for authored patches and reviewed lessons via durable jobs. Enforce authorization, ask-before-code, assistance and protected reads in their own boundaries. Serving code cannot import this package. |

## Verification and landing

Each command used the checkout venv on PATH and an empty environment with the
specified checkout-local HOME, CODEX_HOME, LEARNLOOP_CONFIG_DIR and TMPDIR, and
LANG=C.UTF-8. `T FILE` means `python -m pytest -q -n 1 -p no:cacheprovider tests/FILE`.
Each file ran alone. Only the cell-writer invocation set
`LEARNLOOP_TEST_NO_SOCKETS=1`. No dependency install or pin update was needed.

| Command | Final result |
|---|---|
| `.venv/bin/python -m pytest --version` | pytest 9.0.3 |
| `T test_notebook_cell_writer.py` | 11 passed, 1 skipped in 7.43s |
| `T test_notebook_catalog.py` | 6 passed in 4.00s |
| `T test_notebook_contract.py` | 54 passed, 1 skipped in 19.00s |
| `T test_notebook_check.py` | 11 passed, 16 skipped in 5.27s |
| `T test_notebook_isolation.py` | 4 passed in 5.40s |
| `T test_cli_help_snapshot.py` | 26 passed in 52.47s |
| `T test_identity_pins.py` | 363 passed in 17.65s |
| `T test_architecture.py` | 18 passed in 35.63s |
| `T test_test_layout.py` | 3 passed in 21.83s |
| `ruff check` | All checks passed! |
| `lint-imports --no-cache` | Contracts: 54 kept, 0 broken. |
| `python -m learnloop.notebook_authoring.catalog .codex-scratch/catalog-final` | Exit 0. The separate inventory above reads the emitted files. |
| `git diff --check` | Exit 0 |

The final nine single-file runs total **496 passed and 18 skipped**.

The initial contract file had 51 passing cases. Adding three broken synthetic
activities exposed three missed findings (`3 failed, 51 passed in 18.98s`).
The final file includes all three. The first catalog export exposed missing
signatures on five inherited constructors. The final export and tests cover
those constructors and the import path used to index an added tool.

**Orchestrator runs.** Rerun the following files alone with a writable TMPDIR
outside the checkout and `LEARNLOOP_TEST_NO_SOCKETS` unset.

- `test_notebook_cell_writer.py` — `test_generated_file_passes_pinned_marimo_check`
  compares generated bytes and the real `marimo check --strict` result. The CLI
  creates a local asyncio socketpair.
- `test_notebook_check.py` — the 16 external-output cases cover cell and edge
  reporting, broken graphs (three), side effects, the structure-only verdict,
  link and existing-file refusals (five), absence of vault/config discovery,
  invalid notebooks (three) and fresh-process import logging. The traversal
  and checkout refusals run inside the checkout.
- `test_notebook_contract.py` — `test_contract_cli_writes_revision_bound_reports`
  exercises the real external file writer and stale-manifest exit status.

The CLI compatibility test accepts the widened scope choice. The AST boundary
checks and import-linter enforce the owner-side import boundary. Identity
goldens, CLI snapshot, dependency pins, learner store and serving code have
no diff. This work introduces no numeric safety cap, scoring weight or sampling
rate. Search callers supply their own result and line budgets.

**Existing assertions changed.** The H1 dependency refusal still requires the
exact marimo requirement in the error text. Its expected version now comes
from the independent project extra so an intentional upgrade exercises the
new pin. Its report-absence assertion now inspects the per-test checkout
directory used for that case. No other pre-existing assertion changed.

**Landing units.** H2 contains the cell writer, descriptor helper, marimo
adapter and parser regressions. H3 contains dependency admission, cards, tool
notes, examples and catalog export. H4 contains the contract and manifest
checks, shared report writer and CLI scope. The tests and ledger entries
belong with their respective changes. The orchestrator stages each unit and
runs `test_identity_pins.py` after each source commit. This worker made no Git
index writes. The generated catalog and worker scratch were removed after the inventory.
