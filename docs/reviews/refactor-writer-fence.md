# The writer fence (ledger L42-R2, and L42-R1's residue)

Branch `refactor/writer-fence`, 2026-11-25. Migration 275, no algorithm tag: nothing stored changes meaning. The
fence decides which process may write; it does not change what any write computes.

## The problem

A vault's algorithm tag is published in `learnloop.toml`, and every process reads it once, when it loads the vault.
Every tag-gated computation then reads the process's cached copy. A process that loaded the vault before
`learnloop upgrade` committed an activation keeps writing under the predecessor's rules after that commit. The L4-2
re-review (2026-11-25) gave two harms:

1. **An older binary.** A grader of `a17cba6132` (0.71) is paused after it loads the vault. The 0.72 upgrade
   completes elsewhere, and then the grade commits. That writer inserts a surprise row and no grade curve. No rebuild
   backfills the curve, so a raw fact is lost. This was reproduced with the actual `a17cba6132` code against an upgrade
   by the base commit: three attempts, one surprise row without a curve.
2. **A stale writer of this code.** The new binary still holding a 0.71 config computes tag-dependent outputs by the
   predecessor's rules. It writes the lesson check's learned mass, which later rebuilds reuse, applies a
   label-derived mastery update, and skips the grade-time forecast.

## The mechanism

**One row in the database is the truth for writes.** `writer_fence` has a single row, `algorithm_version`. Every
activation in `learnloop.ops.upgrades` sets it inside its own `BEGIN IMMEDIATE` transaction. This happens after the
predecessor's manifest is frozen and before the successor's state is derived. The row therefore flips exactly at the
activation's commit: never earlier, and never without the successor's state. The config's tag remains the published
value the upgrade writes last (ADR-019's order is unchanged).

**The check runs at the write, inside its transaction, under its lock.** Each writable connection this code opens
(`db.connection._open_writable`) registers two kinds of SQL function:

- the marker `learnloop fenced writer`;
- one function per tag it writes under, named `learnloop writes under <tag>`.

Each fenced table has a `BEFORE INSERT` or `BEFORE UPDATE` trigger. The trigger looks those names up in
`pragma_function_list` and compares them with the row as it stands. The write holds the write lock, so the row cannot
move before the commit. The triggers never call a function, so a connection without them still prepares the statement
and gets a plain refusal:

> LearnLoop writer fence: this vault was upgraded while this LearnLoop process had it open, so nothing was saved.
> Restart LearnLoop from the upgraded version, or reload the vault, and try again.

**The rule** applies once the row exists. A write is allowed only on a connection registered for the row's tag, or on
a fence-aware connection bound to no tag. An unbound process has never loaded this vault (a scratch copy, a test
seeding rows) and computed nothing from its config. Every other write is refused:

- a stale writer of this code;
- any connection without the marker. This is how pre-fence code and every other SQLite client meet the database.

**Where a connection's binding comes from.** `writer_fence.writing_under(path, *tags)` sets a context variable. The
activation uses it to bind the predecessor and the successor together: the predecessor for what it freezes before the
row moves, and the successor for what it derives after. Without that context, the binding is the tag of the newest
config this process loaded for that database. `load_vault` observes it, and so does the upgrade once its activation
commits. A connection pool (production's `reused_connections` and the test lane's) keys idle connections by binding,
so a reused connection never writes under a binding it was not opened with.

**What is fenced** (`writer_fence.GUARDED`): facts computed under the vault's tag that a rebuild keeps or reads, plus
the record of a rebuild.

| Table | What it records |
|---|---|
| `practice_attempts` (insert) | The first write of every live grade, so a refused grade writes nothing. |
| `grading_evidence` (insert) | The first write of a regrade or an adjudication. |
| `attempt_surprise` (insert, update) | The grade's surprise. |
| `attempt_grade_curves` (insert) | The grade curve. |
| `lesson_checks` (insert) | A lesson check's mass, written once. |
| `learning_object_mastery` (insert, update) | Mastery. |
| `forecast_receipts` (insert) | The grade-time forecast. |
| `attempt_application_order` (insert) | The application order. |
| `derived_state_rebuilds` (insert) | Every rebuild's and activation's receipt. |

An older binary's own upgrade writes that receipt and those projections, so it is refused too. The row therefore never
falls behind the config.

## What is authoritative, and how a half-finished activation looks

| State | Config | Database row | Journal | Who may write fenced tables |
|---|---|---|---|---|
| Never activated by fence-aware code | T | none | none | everyone (the config is the tag, as before) |
| Activated | T | T | none | connections bound to T, unbound fence-aware ones |
| Activation running | T (after its rename) | P until the commit | present | nobody else: the activation holds the write lock |
| Death before the publication | P | P (the flip rolled back) | removed by the next opener, or torn | writers bound to P |
| Death after the publication, before the commit | T | P | present | writers bound to P (their rows are predecessor history, and the completion freezes and rebuilds them with the rest); writers bound to T are refused |
| Config edited by hand, no journal | X | T | none | writers bound to T; a process that loaded X is refused until the config names T again (or `learnloop upgrade --to X` activates it) |

The row is authoritative for writes. The config is the published label and the source of a process's binding. The
two disagree only in the last three rows, and the activation journal (ADR-019) already resolves the half-finished
case: every opener that may write completes it, which flips the row.

## The hosts

- **Desktop sidecar and phone host** (the phone host runs the sidecar's handlers). A fenced write becomes the
  retryable error `vault_upgraded_while_open`. The context first reloads the vault with `reload(maintenance=False)`,
  so the retry runs under the new tag. If the reload fails, the message says to restart. The phone host maps the code
  to 503, retryable. The desktop's file watcher still reloads on the config's change, as before. The fence covers the
  window before that reload and every request that races it.
- **MCP host.** Each request loads the vault (reloaded when its files change). A fenced write is answered and
  recorded as `vault_upgraded_while_open`: "LearnLoop was upgraded while this request ran, so nothing was saved. Try
  again."
- **CLI.** A command loads the vault once, at its start. If an upgrade commits while it runs, its next fenced write
  stops the command with the refusal's own words.
- **An older binary** gets the trigger's message from SQLite, whatever its own error handling does with it.

## Failure modes considered

- **A WAL reader whose snapshot predates the activation** tries to write after it. SQLite refuses to upgrade a stale
  snapshot (`database is locked`). A stale writer that takes the lock afresh reads the new row and is refused.
  Durability-lane test.
- **A pool handing a T-bound connection to a P-bound checkout.** The pool key includes the binding.
- **A process that dies at each point of the activation.** Real-death tests (fork, `os._exit`) cover the death before
  and after the publication.
- **A rebuild or activation writing under the old tag.** The receipt is fenced, so the whole transaction rolls back.
- **An older binary that never saw migration 275.** It cannot exist alongside the fence. Fence-aware code applies 275
  through the migration coordinator before its first activation. The table, and with it the row, exists only once
  that has happened. An older binary attached before then picks up the triggers on its next statement, because
  SQLite re-prepares a statement after a schema change.

## What is not covered

- **Only the fenced tables are fenced.** A stale writer's other tag-dependent rows are not refused. These include
  router decisions, plans, scheduler slates, facet belief and AD's selections. Most of them carry their own
  `algorithm_version` stamp, and the derived ones are rebuilt. Fencing another write is one `GUARDED` entry and one
  trigger in a migration. `tests/test_writer_fence.py` checks that every entry has its trigger at the head, so a later
  table-rebuilding migration that drops one fails.
- **A stale vault object inside a process that has itself reloaded.** An example is a background thread in the
  sidecar that captured the vault before the sidecar reloaded to the new tag and writes after the reload. It writes
  under the process's newest binding and is not caught. The `writing_under` scope can bind such work to its own
  vault. No background job uses it yet: the desktop's background work is bounded, and the main thread reloads.
- **Code older than the fence after the first fence-aware activation** is refused at every fenced write, at any tag.
  This includes running pre-fence code on a vault that fence-aware code upgraded. The undo is the playbook's: restore
  a copy taken before the upgrade. Before that first activation there is no row, so an older binary keeps working.
- **Not a security boundary.** Any SQLite client can drop a trigger or delete through it. The fence stops honest
  stale writers. A connection with `PRAGMA trusted_schema = OFF` is refused with SQLite's "unsafe use of virtual
  table" rather than the plain message. It still fails closed.
- **Cost.** Each fenced row's trigger scans `pragma_function_list`, about 27 µs per row measured on SQLite 3.54.1.
  This is paid on fenced tables only.

## The fork for the owner

The alternative was to make `learnloop upgrade` refuse, or wait, while another process holds the vault open. That
would use a presence lock each process takes while it serves the vault. It cannot see an older binary, which takes no
such lock, so it would not close harm 1 for 0.71 and 0.72 binaries. It would also add a "close the desktop and the
phone host first" step to every upgrade. The fence closes both harms at the database, for older binaries too, so it
is the recommended option and the one built. The presence lock could be added later as a courtesy, so that an upgrade
says which processes will need a reload. It is not needed for correctness.

## Tests

`tests/test_writer_fence.py`:

- the schema check for every fenced write;
- an older binary refused after the activation, for a grade, a regrade's evidence and a surprise update;
- an older binary refused at every tag after a fenced activation, its own upgrade's receipt included;
- an unfenced vault left alone;
- a stale writer of this code refused after an upgrade by another process, then proceeding after a reload, with its
  curve recorded as `graded`;
- every fenced write refusing a writer bound to another tag and admitting the current one;
- an unbound fence-aware writer admitted;
- the pool's binding;
- a real death before the publication and after it (the window's predecessor write is frozen by the completion);
- in the durability lane, a WAL snapshot from before the activation, and a stale writer taking the lock after it.

Host tests:

- `tests/test_sidecar_contract.py::test_a_write_the_writer_fence_refused_reloads_the_vault_and_is_a_retryable_error`;
- `tests/test_mcp_tools.py::test_a_write_the_writer_fence_refused_is_recorded_and_says_try_again`;
- the phone host's status table in `tests/test_mobile_rpc.py`.

Fail-first: two scratch copies of the core scenarios ran on the base commit `b887fc9b4a` and failed with
`DID NOT RAISE`, then passed here:

- a stale writer after an upgrade by another process;
- an older binary's regrade write.

The real `a17cba6132` grader was also run against this branch's upgrade. It graded before the upgrade, then was
refused after it, with nothing written and no surprise row without a curve. Against the base commit's upgrade, the
same run graded after the upgrade and left one surprise row without a curve.
