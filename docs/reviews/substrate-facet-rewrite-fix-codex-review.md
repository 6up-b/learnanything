# substrate-facet-rewrite-fix: Codex review and fix step

Branch `substrate/facet-write-on-change` (worktree `learnanything-dl2`), base main `2eb4bf6e61`.
Reviewed range `2eb4bf6e61..57b1adbb27` (stage commits `57386bd5df`, `57b1adbb27`).
Codex job `20261101-081801-kSPNVJ` (gpt-6.1-sol). Codex reviewed the code by reading it only: it
could not start `systemd-run --user --scope` on the user bus ("Operation not permitted"), so it
ran none of the tests. This step ran them (gate below).

## Review

Codex verdict: **no actionable defects**. It confirmed that the helper compares every persisted
value column, handles NULL `practice_item_id` recall keys, compares again under `BEGIN IMMEDIATE`
before applying, keeps `Repository.atomic()` ownership for nested calls, and leaves the three
DERIVED tables with exactly one rebuild owner each. It also confirmed spec conformance: fix 1 is
implemented, fixes 2 and 3 are deferred as optional, no successor or kill switch is needed, and no
migration or parameter was added.

### Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| (none) | – | Codex reported no defects | – | – | – |
| G1 | coverage gap (Codex said it is not a defect) | No deterministic test puts another writer's commit between the read-snapshot comparison and the locked comparison | addressed with a test (no code change) | `fe1953bed0` | `tests/test_facet_state_write_on_change.py::test_a_writer_committing_between_the_two_comparisons_is_reconciled_not_clobbered` |

About G1: the test wraps the repository connection so that a second connection commits right
before the writer's `BEGIN IMMEDIATE`, when no lock is held. That second writer deletes every
residual row, re-inserts `f_a` under a new rowid with a foreign `id`, drops `f_b` and adds `f_c`.
The table must still end equal to the projection: `f_a` updated with its projected `id`, `f_b`
restored with its values, `f_c` removed. Mutation check: a temporary edit that applied the
preliminary (snapshot) plan instead of comparing again fails this test, because `f_c` survives and
`f_b` is missing. The edit was reverted from a backup copy, and `git status` was clean apart from
the test.

No source file changed in this step.

## Gate (this step)

Every pytest command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`,
with TMPDIR outside the worktree. None of them made a live call.

| command | result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 36 kept, 0 broken |
| `uv run pytest -q -k between tests/test_facet_state_write_on_change.py` (new test) | 1 passed |
| the same, with the mutant described above | 1 failed (expected) |
| `uv run pytest -n 6 <10 files below>` (plain lane) | 107 passed, 4 xfailed |
| `uv run pytest -n 6 --durable-sqlite <10 files below>` (WAL + production pragmas) | 107 passed, 4 xfailed |
| `uv run pytest -m durability tests/test_facet_state_write_on_change.py` | 1 passed |

Test files run:

- `tests/test_facet_state_write_on_change.py` (the only file this step changed)
- `tests/test_rebuild_orchestrator.py`
- `tests/test_rebuild_equivalence.py`
- `tests/test_rebuild_equivalence_review.py`
- `tests/test_canonical_projection_rollout.py`
- `tests/test_km2_canonical.py`
- `tests/test_km2_write_path.py`
- `tests/test_capability_residual.py`
- `tests/test_shadow_rebuild.py`
- `tests/test_table_roles.py`

The wider set of 81 targeted files that exercise `repositories.py` ran in the stage step (see
`docs/reviews/substrate-facet-write-on-change.md`: 1293 passed, 15 skipped, 7 xfailed). It was not
rerun here because no source changed. The full suite, the whole durability lane and vitest run
once, in the landing gate. Nothing touched the frontend, the schema or the migrations.
