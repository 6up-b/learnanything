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
- **A stale vault object inside a process that has itself reloaded** is covered since the review fix round (below),
  wherever the work runs in a scope or through a repository made for its vault. It is not covered on a thread
  that starts outside every scope and opens connections by path, holding a vault object it loaded before its own
  process reloaded. Such a thread writes under the newest load. None is known in the hosts; the scope is the seam.
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

## Review fix round (2026-11-25, ledger WF-R1 to WF-R12)

The adversarial review of `81f18a6221` found that the binding was the process's, that refusals could be swallowed,
that an upgrade could move the database's tag backwards, and that more stale writes lose a fact. The fixes are by
class. Migration 276 adds triggers; no tag is added.

**A. The binding belongs to the vault the write was computed from (WF-R1, WF-R10).**

- **Repositories.** A `Repository` keeps the binding in force when it was made. `vault_repository` makes it under the
  tag of its paths' own config, and an entry point makes it right after it loads the vault.
- **Hosts.**
  - The desktop sidecar and the phone host scope each request to their context's vault. The phone host runs the
    sidecar's handlers, so its RPC worker and job worker each write under their own context's vault.
  - A request that publishes a reloaded vault rebinds the rest of the request to it.
  - A background job runs under the scope of the request that started it.
  - The post-attempt worker scopes each pass to the vault it was handed.
  - The MCP host scopes each request to the vault it loaded, and remakes its repository under each newly loaded vault.
  - The CLI's repository no longer reloads the vault. The repository writes under the command's first load, the vault
    the command computes from.
- **Fallback.** The process's newest load applies only to a connection outside every scope and every bound
  repository.
- **One read per checkout.** `connect()` reads the binding once and passes it to both the pool's key and the
  registration. The test pool does the same.

**B. A refusal is never swallowed (WF-R2, WF-R12, the lesson probe's conversion).**

- **The exception.** On every writable connection this code opens (`FencedConnection` and `FencedCursor`), the trigger's
  refusal is raised as `WriterFenceRefusal`.
- **Why a `BaseException`.** No `except Exception` can take it. That covers the forecast receipts' best-effort
  handler, AD's logging savepoints and the lesson probe's `grading_unavailable`. The enclosing serve or grade
  therefore rolls back whole, and the host answers.
- **Boundaries.** Only `except BaseException` and a bare `except` can catch it.
  - Each such handler in `src` re-raises or is a registered boundary (`writer_fence.REFUSAL_BOUNDARIES`). A boundary
    hands the refusal to a waiter, or answers a job with `vault_upgraded_while_open`.
  - Every keep-alive worker loop takes the refusal and continues (post-attempt worker, ingest drains, figure prefetch),
    or is registered as writing no fenced table (leases, heartbeats, the notebook runtime).
  - Two AST tests enforce both rules.
- **Reloads.**
  - Each refusal is counted per database, and a sidecar context compares that count at its next request. If the vault's
    tag is no longer the database's, it reloads first.
  - When the config itself disagrees with the database, the sidecar says to run `learnloop upgrade` and does not offer a
    retry.
  - The MCP host drops its cached vault on a refusal.
- **Forecast receipts.** `scheduling/forecast_receipts.py` needed no change.

**C. The database's tag never moves backwards (WF-R4).**

- `learnloop upgrade` starts from the row when it has one.
- A config that disagrees with the row is set back to the database's tag before the walk, and the result notes it. A
  config disagrees when it was restored from an older copy or edited by hand, and no journal stands.
- A database tag this code does not know is refused in plain words.
- `writer_fence.advance` moves the row only from the link's predecessor, under the activation's lock. An empty row
  (before the first fence-aware activation, or before migration 275) counts as the predecessor.

**D. More stale writes that lose or corrupt a fact (WF-R2, WF-R6, WF-R8, WF-R9; migration 276).**

| Fenced write | Why it is permanent or learner-visible |
|---|---|
| `plan_presentations` insert | The serve-time forecast is recorded only by the serve that inserts it. |
| `probe_presentations` insert | A probe pinned for the learner. |
| `grade_adjudications` insert | It moves an interpretation's head even without new evidence. |
| `reader_section_progress` insert and update, only where `completed_at` first appears | The first completion and its cause are kept for good. |

The proportionate bar is the review's. A stamped, rebuilt row is not fenced; a stale reader's scroll progress still
records.

**E. The phone and the desktop (WF-R11).**

- **Phone adapter.** It leaves `vault_upgraded_while_open`'s retryability to the host's flag, so an explicit "restart"
  stays non-retryable.
- **Phone outbox.** It keeps a retryable refusal queued under its id, so a later flush sends it again. It flags one the
  host cannot retry, with the host's words.
- **Desktop.** No change was needed: it already shows the sidecar's message and offers Try again for a retryable error
  (`apps/learnloop-tauri/src/app/notices.ts`, `src/errors.ts`).

**Refuted or owned elsewhere.**

- **WF-R3 (exam finish):** fixed on main by `74ab78be7e` before this round.
- **WF-R5 (exam seeding's replay set) and the early-committed lesson turn of WF-R7:** these sit in files the parallel
  score fix round owns (`goals/exam_seeding.py`, `teacher/service.py`).

**Not enforced after this round.**

- **Unscoped stale threads:** the thread case named above.
- **Unfenced tag-dependent rows:** a stale writer's stamped or rebuilt rows outside the fenced writes.
- **Pre-fence code:** older code before the vault's first fence-aware activation.
- **Not a security boundary:** a client that drops the triggers can still write.
- **One-shot threads:** a one-shot background thread that is neither a registered boundary nor a keep-alive loop ends
  on a refusal, with its traceback in the log. Its writes rolled back, and the host reloads at its next request.

**Tests.** `tests/test_writer_fence_scopes.py` holds one or more tests per finding. Its 18 tests failed on
`a45e3c1b1c`. The outbox test's retryable case failed on the old outbox. The round-one fence tests now expect the
fence's own exception on this code's connections.


## Round 4 (2026-11-25, ledger R4-F1 to R4-F5)

The verification review of round 3 (`a45e3c1b1c..6cea38cad2`) found WF-R1, WF-R2 and WF-R4 only partly closed, and
two new fence defects. No migration and no tag: nothing stored changes meaning. Tests:
`tests/test_writer_fence_recovery.py`, and the guards in `tests/test_writer_fence_scopes.py`.

**R4-F1 (blocker): a second refusal during recovery ended the desktop host.**

- **The failure.** A predecessor `learnloop.toml` restored over a successor database, plus a learning object without
  a mastery row. The first refused write entered recovery. `reload(maintenance=False)` synced the new object, a
  second fenced write. The recovery's `except Exception` let that refusal through, and `serve()` closed. Restarting
  against the same files repeated it.
- **Compare before writing.** A load compares the config's tag with the database's right after the repository opens,
  before state sync or any recovery writes. `SidecarContext.load` and `load_secondary` both do.
  - A disagreement raises `ConfigBehindDatabase`, one more unservable state beside below-the-floor and an unfinished
    upgrade.
  - It is answered as the existing non-retryable `vault_upgraded_while_open`, with the `learnloop upgrade` command.
  - Once `learnloop upgrade` sets the config back, the watcher's reload (or a new initialize) serves the vault again.
- **No host loop ends on a refusal.** Each host's last boundary answers one, including a refusal raised while
  another failure was being answered.
  - The sidecar's `_handle`, through which the desktop's stdio loop and the phone host's workers dispatch.
  - The phone host's jobs and redrives. A reload refused there also gets its unservable words.
  - The MCP tool call's record. A refused tool call names `learnloop upgrade` when the config is behind.
  - The CLI's entry point, which prints the refusal's words and exits with status 1.
- **The guards.** Every handler that takes a refusal without re-raising it calls only what writes nothing: logging,
  building the answer, handing the refusal on. The AST test follows calls into functions of the handler's own module
  and a short list of answer builders elsewhere. Anything else must run inside a `try` that itself takes the refusal.
  A second test requires the hosts' last boundaries.

**R4-F2: a same-vault reload left new ingest work fenced out (WF-R1's residue).**

- **The failure.** The host's reload binds the ingest jobs again with the successor's repository. The manager kept
  its runner, so that a live call's interrupt handle survives a reload, and the runner kept the predecessor's
  repository. After an upgrade every new claim wrote under the old tag and was refused until the host restarted. A
  reread's carried-over completion meets migration 276 this way.
- **The fix.** A same-vault rebind whose repository writes under another binding (`Repository.writer_tags`) binds a
  new runner for new claims. The new runner takes the old one's clock, services and handlers.
  - The old runner is retired (`IngestRunner.retire`). It claims nothing more and finishes only the claim it holds.
  - It is kept while busy, so `interrupt_codex` still reaches its live call and a halt still stops it.
  - A reload at the same tag keeps the runner, as before.
- **A narrow race.** A claim the old runner takes just as it is retired meets the fence at its first fenced write.
  The drain loop takes the refusal; the job's lease expires and the successor's runner requeues it.

**R4-F3: a vault with no database could not take the upgrade path (WF-R4's residue).**

- **The failure.** The walk's fence-tag probe opened `state.sqlite` read-only before the repository opener could
  create it. A content-only vault (an intact `learnloop.toml`, no database) failed at once.
- **The fix.** An absent database file has no recorded tag, so the walk goes on and the existing opener creates the
  database. An existing database that cannot be read still stops the walk.
- **The owner's walk.** The owner's live vaults are at mvp-0.61. `test_the_owners_tag_walks_to_the_head_with_its_history`
  walks a vault with a database and graded history from mvp-0.61 to the head end to end. Every link activates, both
  tags reach the head, and the history stays. The floor tests already walked from mvp-0.58; this one starts where
  the owner's vaults are.

**R4-F4: repeating a stored completion was refused (WF-R8's residue).**

- **The failure.** An upsert's `BEFORE INSERT` trigger fires before the conflict turns the insert into an update.
  So migration 276's insert trigger refused a stale report that only repeated a section's stored completion. The
  store would have kept the original completion anyway. The report's progress was lost, and the host answered
  `vault_upgraded_while_open`. The reread carry-over had the same shape.
- **The fix is in the store.** The landed migration is not amended. Both writers read which sections already hold a
  completion and send no completion for them. A completion never clears, so a completion committed between the read
  and the write is kept either way. A first completion by a stale writer is still refused.

**R4-F5: nothing else.** WF-R1, WF-R2 and WF-R4's "Partly" verdicts name exactly the residues above: the ingest
runner (R4-F2), a second refusal in a host's refusal handler and the restored-config recovery (R4-F1), and the
content-only vault (R4-F3).

**Still not enforced.** A one-shot background thread (an exam answer's grader, a key-check recovery) that meets a
refusal still ends with its traceback in the log, as before: its writes rolled back, and the host reloads at its next
request.
