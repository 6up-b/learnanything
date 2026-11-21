# Notebook H1: owner-side structural check

Base: `1f9c8de1b36452f03e745593d766071460c3f729`; branch `na/h1-notebook-check`.
Implementer: Codex. No commit or index mutation; the orchestrator owns landing.
Token usage is not exposed to this implementer. No full landing gate was run.

## Read first: landing blocker and judgment calls

**STOP for a structure-ratchet ruling.** The proposed package raises
`first_level_packages` from 46 to 47. The ordinary ratchet passes because it
measures indexed files and these new files cannot be staged here. A supplemental
run unions precisely the new Python files into its input, without modifying the
index; its only failure is the package count. The structure golden is unchanged.
Keep the requested package name pending the orchestrator's ruling; do not infer
landing approval from the ordinary gate's pass.

- Only structure is checked. Exit 0 means the structural checks passed; every
  report still has `review_status: incomplete` and `accepted: false`.
- Every marimo loader violation is a structural finding, including recoverable
  format violations such as a missing run guard. Nothing is auto-repaired.
- The parser runs in a small isolated Python subprocess because **importing
  marimo itself initializes a file logger**. This is static inspection, not a
  notebook execution backend or a claimed hostile-code runtime sandbox.
- `--scope` and `--out` are required. Output may be outside the notebook's own
  directory tree, but cannot be in a Git checkout. Existing report files are
  refused, even ordinary files: reruns need a fresh output directory.
- The version authority is the exact marimo requirement in `pyproject.toml`,
  exposed at runtime through LearnLoop's installed `Requires-Dist` metadata.
  There is no second hard-coded parser pin. Dependency pins/lock supplied by
  the orchestrator were preserved.

Design inputs were the owner-supplied, **untracked** notebook activities draft
(whole document, especially §§2, 11.1–11.5, 11.10, 15's correction and 17) and
untracked build sheet (A, C and Brief 1). They remain unmodified and untracked;
this record does not establish them as repository documentation.

## Built

- `src/learnloop/notebook_authoring/marimo_adapter.py`: dependency admission,
  static parser/graph adapter, and its write-denying worker.
- `src/learnloop/notebook_authoring/check.py`: explicit input read, confined
  output creation and structure-only report/summary. The package initializer
  has no imports or initialization effects.
- `src/learnloop/cli/notebook.py` and the two registration lines in
  `src/learnloop/cli/__init__.py`: the lazy `learnloop notebook check` entry.
- `pyproject.toml`: the new forbidden contract and the harness added to the
  existing experiments contract's inventory.
- `tests/test_notebook_check.py`, `tests/test_notebook_isolation.py` and
  `tests/notebook_authoring_helpers.py`: synthetic notebooks and boundary proof.
- Root `LICENSES.txt`: direct Python dependency notices. Existing notices were
  specific to frontend engines and samples; no Python dependency convention
  existed. `CLAUDE.md` changes only its install line, in the existing extras style.

`structure.json` lists cells in source order, ordinal IDs, names, source lines,
marimo definitions/references, dependencies and parse status. Findings identify
cells by those IDs and cover unparsable cells, file-format problems, duplicate
definitions and cycles. Function cells are covered as well as ordinary cells.
The IDs identify this report's ordering; they are not persisted learner identities.
`structure.txt` and stdout give the short result and explicit incomplete-review
statement. Exit 1 reports structural findings; exit 2 refuses dependencies,
input/output errors or an unavailable parser.

## Marimo interfaces and no-execution evidence

All upstream interfaces below are private, confined to the adapter:

- `marimo._ast.parse.parse_notebook` and `MarimoFileError`;
- `marimo._schemas.serialization.UnparsableCell`;
- `marimo._ast.compiler.compile_cell`;
- `marimo._ast.cell.SourcePosition`;
- `marimo._runtime.dataflow.DirectedGraph`, `register_cell`, `definitions`,
  `cycles` and `parents`.

Inspected the installed 0.25.2 source, including the loader, serializer, parser,
scanner, compiler, visitor, graph/edges and logging initialization. The loader
chain is `marimo._ast.load.get_notebook_status` →
`PythonNotebookSerializer.deserialize` → `parse_notebook`.
`load_app` also deserializes and then calls `load_notebook_ir`, constructing an
App. We use the same underlying parser directly on the explicitly read string;
we do not construct an App or call either App-loading interface.

`Parser.node_stack` uses `ast.parse`; syntax failures go through
`scan_parse_fallback`, which builds AST nodes and `UnparsableCell` metadata.
`_eval_kwargs` accepts literal AST constants/lists rather than evaluating calls.
`compile_cell` uses `ScopedVisitor` for definitions/references and Python's
`compile` for code objects. Neither body nor expression code objects are
executed. Graph registration indexes definitions and adds edges/cycles; it does
not evaluate cells. Notebook imports and decorator/default expressions are
source data. No notebook filename is passed to an import loader.

Two upstream side effects needed explicit treatment:

1. Without `SourcePosition`, compilation calls `get_filename`/`get_tmpdir` and
   creates implicit scratch. Supplying a position avoids that path; a test makes
   `get_tmpdir` fail if called.
2. Importing marimo calls `_loggers.marimo_logger` → `_file_handler` and attempts
   to create a cache/log directory. The fresh worker installs an audit hook
   before that import, denying file writes, filesystem mutations, subprocesses
   and sockets. It uses `-I -B`, a minimal environment without credentials, XDG
   paths pointing at the null device, stdin for source and stdout for JSON.
   The parent process's imports, environment and audit policy are unchanged.

A fresh-process regression first observed the unwanted cache directory and then
passed after isolation. A synthetic notebook contains top-level and cell-body
marker writes plus a nonexistent import: the marker never appears, no dependency
is imported from the notebook, and input bytes remain identical. These checks
prove static parsing, not the security of any future execution runtime.

## Boundary, files and persisted meaning

`notebook-authoring-stays-outside-production` has
`allow_indirect_imports = false`, covers production packages/root modules and
individual CLI modules except the notebook adapter/CLI registration initializer,
and forbids `learnloop.notebook_authoring`. The experiments contract also covers
the new harness. The AST test covers every source file, including namespace
packages that grimp cannot name, function-local/relative imports and literal
dynamic targets. A separate scan refuses LearnLoop dependencies from the harness
other than its own modules. A subprocess proves base CLI import/help leaves both
the harness and marimo unloaded when the optional libraries are unimportable.

The harness reads only the supplied notebook and installed parser metadata/code.
It imports no vault/config/model service. The root CLI's existing receipt
observer stays idle: the regression makes vault discovery and receipt-store
opening fail if called. No learner store, migration, default, algorithm tag,
shared identity, serving candidate, app, phone or sidecar code changes.

Under `docs/algorithm-change-playbook.md`, this changes **no persisted learner
meaning**: owner reports have no consumer in evidence, admission, grading,
assistance, scheduling, stopping, projection or certification. Writing a report
does not make a receipt inert by assumption; the enforced absence of consumers
is the reason it is inert. No successor, config switch or upgrade row is needed.

The output writer rejects every `..` component, walks directories with
`O_DIRECTORY | O_NOFOLLOW` and anchored directory descriptors, and creates only
fixed report names with `O_EXCL | O_NOFOLLOW`. Symlink parents, output symlinks,
report-file symlinks, hardlinks and preexisting reports are refused. File modes
are private. Input/output aliasing cannot overwrite source. A disk/write failure
can leave a partial report pair; neither file can claim acceptance.

## Dependencies and notices

Provisioned facts supplied by the orchestrator: marimo 0.25.2, 120.6 MB installed,
Apache-2.0; wigglystuff 0.6.0, 4.5 MB installed, MIT; anywidget 0.11.0, MIT;
30 additional locked packages; environment 582 MB → 775 MB (193 MB increase).
The direct distribution licence files and all three licence metadata fields
were checked locally. No install, resolver, pin or lock update was performed.
`uv.lock` and the four-line notebook extra were already modified at start.
This is not a complete transitive frontend/wheel/font licence or asset audit.

## Tests first and verification commands

Here `T` means the supplied scratch `t.sh` wrapper, `P` the supplied `py.sh`, and
`SCRATCH` the owner-supplied external scratch directory. No machine-specific
absolute path is recorded. Only explicit test files were run, at most two
workers. The layout and architecture files ran separately with one worker.

Before implementation, the initial 23-case run exposed seven vacuous negative
assertions that merely accepted Typer's unknown-command error (16 failed,
7 passed). Those assertions were strengthened to require output-refusal text;
all 23 then failed. Adding invalid-file and implicit-scratch cases gave **27
failed in 4.05s** before any harness implementation existed. Missing command,
missing report and missing package/contract were the expected failures.

The fresh-import write regression was added after source inspection found the
upstream logger: **1 failed in 2.78s**, specifically on its unexpected cache
creation, before the isolation fix. A concurrent test attempt had a pytest
scratch-cleanup error, was excluded, and was rerun sequentially. No socket-blocked
run is counted as a test pass.

| Command | Result |
|---|---|
| `T tests/test_notebook_check.py tests/test_notebook_isolation.py -q -n 2` (pre-code) | `27 failed in 4.05s` |
| Same (initial implementation) | `11 failed, 16 passed in 7.48s`; checkout detection mistook an empty permission marker for a Git checkout; fixed |
| Same (before logger regression) | `27 passed in 7.82s` |
| `T tests/test_notebook_check.py::test_fresh_parser_import_writes_nothing_outside_output -q -n 1` | fail-first `1 failed in 2.78s`; subsequently covered by the passing file run |
| `T tests/test_notebook_check.py tests/test_notebook_isolation.py -q -n 2` (isolated parser) | `28 passed in 10.11s` |
| `T tests/test_cli_help_snapshot.py tests/test_identity_pins.py tests/test_effective_defaults_golden.py tests/test_public_tip_guards.py tests/test_structure_ratchets.py tests/test_e0_isolation.py -q -n 2` | `395 passed in 64.04s` |
| `T tests/test_test_layout.py -q -n 1` | `3 passed in 20.80s`; final separate rerun `3 passed in 20.33s` |
| `T tests/test_architecture.py -q -n 1` | `18 passed in 33.26s` |
| `T tests/test_notebook_check.py tests/test_notebook_isolation.py tests/test_cli_help_snapshot.py -q -n 2` | `54 passed in 34.47s` |
| `T tests/test_notebook_check.py tests/test_notebook_isolation.py -q -n 2` (final output-path check) | `28 passed in 10.02s` |
| `P ruff check` | `All checks passed!`; earlier enum-option B008 corrected with `Annotated` |
| `P lint-imports --no-cache` | `Contracts: 44 kept, 0 broken.`; initially naming namespace `learnloop.content` was refused, so the AST scan covers it as in the existing experiment boundary |
| `P python "$SCRATCH/prospective_structure.py"` | Exit 1: `first_level_packages` 47, ceiling 46; only prospective ratchet failure |
| `git diff --check` | Exit 0 |

The CLI compatibility test explicitly permits new commands without recording
new entries. `tests/cli_surface.json`, both identity/default goldens and their
tests remain unchanged. The public-tip guard and ordinary structure test see
indexed files only; the new files are all small text, and the supplemental
structure result above makes the untracked package's effect explicit.

## Real command

A project-authored two-cell notebook defines `base = 3` in `quantities`, then
`doubled = base * 2` in `comparison`. Both source and output are external scratch.

```sh
P learnloop notebook check "$SCRATCH/structure-smoke.py" --scope structure --out "$SCRATCH/structure-smoke-report"
```

Exit 0, exact stdout:

```text
Structure only: passed; 2 cells; 0 findings.
Review incomplete: no execution, no review layers; not acceptance.
```

The JSON names both cells in order, reports `comparison` reading `base` and
depending on cell `0`, and records no execution, no review layers and no
acceptance. Scratch source/report are retained for orchestrator inspection.

## Not checked or claimed

No execution, rendering, screenshots, layout/teaching/correctness review,
KaTeX/math checks, held-out/leakage or derivability audit, activity contracts,
mutants, reproducibility drive, host submission/certification, widget validation,
model calls, runtime dependency resolution or publication. Static refs include
unresolved/builtin names; this is not a Python name-resolution validator.
No resource-bound or native-runtime sandbox claim is made for the parser worker.
No private vaults, personal source material or real provider were used.

No actual uninstall/reinstall was needed: missing libraries are simulated with
import blockers and metadata failures, and wrong-version admission is simulated.
No Windows portability, full suite, durability gate, fresh-connections gate,
transitive asset audit, wheel-size measurement or upstream release/commit mapping
was verified. Generated vault references, refactor status and bug ledger were
not edited. The orchestrator must resolve the ratchet ruling, stage/commit, run
the landing gate and regenerate references if appropriate.

Change size: +979/−1, net +978 lines; including the pre-provisioned extra/lock, +1521/−2, net +1519 lines.
