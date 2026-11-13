FINDINGS

1. HIGH — Publication can change a comment and commit the successor under the predecessor’s actual tag.
Where: src/learnloop/ops/upgrades.py:354–358, 278, 297. Copied into the table by 1feeb1f0fe; inherited from the deleted helper.
Scenario: An mvp-0.58 config contains a comment mentioning `algorithm_version = "mvp-0.58"` before the actual setting. The first string replacement changes the comment. The upgrade commits mvp-0.59 projections, removes its journal, and reports success, while parsing the config still returns mvp-0.58. Subsequent opens serve predecessor behavior over successor-derived state. Publication must update the actual [algorithms] key and verify the resulting tag before committing.
Missed proof: The tests use generated configs containing one matching string. Checking rename/fsync order does not establish that the renamed file names the successor.
Smallest failing test: Prepend that comment to a predecessor fixture, upgrade, and assert the parsed config tag equals the committed rebuild’s tag.
Confidence: certain from the replacement and transaction paths; not executed.

2. HIGH — An already-bound sidecar continues serving after a refused reload or an interrupted upgrade.
Where: src/learnloop_sidecar/context.py:197–206, 518–521, 777–780; src/learnloop_sidecar/server.py:98–103; src/learnloop/db/repositories.py:1082–1093.
Scenario: Initialize the desktop at a supported tag, then restore/relabel its vault below the floor. Reload raises before replacing or invalidating the existing context. Subsequent handlers still receive the cached vault and repository from require_vault; background work gets them from _worker_target. Similarly, another process can leave an activation journal after publishing mvp-0.59, while the already-open desktop continues serving its mvp-0.58 context. Repository checks the journal at construction, not on subsequent connections. The context must stop serving until the vault is valid and any activation completes.
Missed proof: D1 tests initialize a fresh sidecar against an already-old vault. D3’s sidecar opener constructs a fresh context; its already-attached-process test covers MCP only.
Smallest failing test: Load a context, change its file tag below the floor without the test allowance, assert reload refuses, then assert app_snapshot also refuses. It currently returns the old snapshot. Add the equivalent already-loaded-context case with an activation journal.
Confidence: certain for cached serving and failed-reload retention; full GUI watcher and background-job timing were not exercised. D1 introduced the floor refusal without handling this lifecycle; the journal gap predates D3.

3. HIGH — An unreadable activation journal is deleted as though publication never happened.
Where: src/learnloop/ops/upgrades.py:218–222, 305–312. Consolidated by 1feeb1f0fe; inherited from the old completers.
Scenario: An upgrade dies after publishing mvp-0.59 but before committing. Its valid journal subsequently cannot be read—for example, its file permissions deny reads while its directory permits unlinking. _read_journal catches PermissionError/OSError and returns “torn”; completion deletes the journal and opens the predecessor database under mvp-0.59. An inability to read the recovery record must fail closed and retain it.
Missed proof: test_a_torn_journal_is_removed_and_nothing_activates supplies malformed JSON while the config still names the predecessor. It never tests a read failure or a damaged journal after publication.
Smallest failing test: Build the existing interrupted fixture, inject PermissionError only when reading its journal, and assert the opener refuses and the journal remains. Today it removes the journal and attaches.
Confidence: certain from the exception handling; fault injection and filesystem permissions were not exercised.

4. MEDIUM — MCP resumes using its old snapshot immediately after rejecting a below-floor reload.
Where: src/learnloop/remote/runtime.py:150–161. D1’s handling was added in 2d93f198bc.
Scenario: Attach MCP at mvp-0.59, change the vault to mvp-0.57, and request it after the fingerprint TTL expires. The request updates _checked_at before loading, then raises SchemaMismatch. A second request within the next two seconds skips loading and returns the cached mvp-0.59 vault. Repeated traffic therefore alternates refusal with successful stale serving. The failed load must not advance the freshness window or leave a usable cached result.
Missed proof: The floor test exercises initial attach only. The standing-journal test succeeds because journals are checked before the cache.
Smallest failing test: With a controlled monotonic clock, trigger one below-floor reload failure and call runtime.vault() again at the same time. Both calls should raise; the second currently succeeds.
Confidence: certain from the cache control flow; not executed.

5. MEDIUM — `doctor --fix` changes an unsupported vault before reporting the floor refusal.
Where: src/learnloop/cli/app.py:1325–1337; src/learnloop/ops/plan_transport.py:153–160. Missed by D1, 2d93f198bc.
Scenario: An mvp-0.57 vault has an explicit Codex provider setting. `doctor --fix --vault …` loads its config without checking the floor and rewrites provider settings. Only afterward does run_doctor refuse the vault. The command fails but has already changed the supposedly unopened vault. The floor check must precede the CLI’s repair phase.
Missed proof: The doctor-door test calls run_doctor(fix_state=True) directly and compares database bytes. It never invokes the CLI’s preceding config repair or checks TOML bytes.
Smallest failing test: Invoke `doctor --fix` on that below-floor fixture and assert both refusal and byte-identical learnloop.toml.
Confidence: certain; not executed.

6. MEDIUM — Config-only CLI doors bypass the floor entirely.
Where: src/learnloop/cli/mcp.py:33–41, 164–165; src/learnloop/cli/project.py:91–105, 267–272. Missed by D1, 2d93f198bc.
Scenario: On a below-floor vault with a current database schema, `learnloop mcp activity` successfully reads and reports stored activity: vault_sqlite_path loads config, and Repository.attach checks journals but not the floor. Project enrollment likewise loads config directly and creates/writes projects/project_store.sqlite without a floor check. These contradict the claimed refusal of every CLI door. Project storage is separate from learner state, but it still mutates the refused vault.
Missed proof: The “cli” door is represented solely by `config effective`. D1’s assumption that every command calls load_vault is false.
Smallest failing test: Run `mcp activity --json` on the existing below-floor fixture and require BelowOldestSupported. For the writing case, require project enrollment to refuse before creating its store.
Confidence: certain for these direct paths; no commands were run.

7. MEDIUM — The prescribed restore checkout cannot perform a prerequisite its upgrade can require.
Where: src/learnloop/version_floor.py:85–91; docs/learnloop-architecture-vault/Decisions/ADR-019 The oldest supported tag.md, “Restoring a backup below the floor”; src/learnloop/cli/recurrence.py:114. Route introduced by 1feeb1f0fe.
Scenario: Restore an mvp-0.11 vault with recurrence.require_guard=true and missing guard results. The actual pre-floor tag, 5231b1bf1b, contains D1. Its recurrence upgrade refuses and instructs the owner to run `recurrence guard`; that command calls load_vault and is itself refused below mvp-0.58. Only `upgrade` has the old checkout’s allowance. The printed route cannot preserve the configured prerequisite and complete the upgrade. It needs a supported way to perform the prerequisite, rather than requiring the owner to disable it.
Missed proof: The route test asserts command strings. The record explicitly says the route was not exercised end to end. Historical guard tests use the test allowance.
Smallest failing test: Against pre-floor, create the guarded mvp-0.11 scenario, obtain the upgrade refusal, then invoke the prescribed guard command with a fake provider. Assert it reaches guard execution rather than BelowOldestSupported.
Confidence: certain from the tagged upgrade, decorator, and guard-command paths; the checkout route was not executed.

8. MEDIUM — Replacement upgrade tests lost the supported successor’s behavioral assertion.
Where: tests/test_upgrades.py:111–123, 157–166, 331–342; tests/test_facet_belief_successor.py:265. Deleted by d8678ad0bd.
Scenario: The removed test_the_upgrade_rebuilds_under_the_tag_and_completes_once checked that existing mvp-0.58 history gains facet_uncertainty and that its failure streak is corrected. The replacement primarily checks tags, receipts, and recovery against another invocation of the same upgrader. Its state snapshot omits facet_uncertainty entirely. An activation that writes a successful receipt without deriving the required uncertainty can satisfy these checks; the remaining belief tests exercise new head-tag attempts or call rebuild directly.
Missed proof: D3 treated this test as plumbing for a deleted module, although its behavioral subject—the supported 0.58 → 0.59 activation—remains live.
Smallest failing test: A mutation test requiring the upgrade tests to reject a receipt-only activation. Restore the removed history-to-successor assertions through ops.upgrades.upgrade, including nonempty successor-tagged uncertainty.
Confidence: certain that the assertions were removed; likely that this targeted mutant survives the replacement tests. No mutation run was performed.

CHECKED AND FOUND SOUND

The table’s normal 0.58 → 0.59 path preserves the deleted module’s manifest freeze, whole-vault rebuild, registry refresh, journal, publication, and commit order.
The production SQLite connection uses synchronous=FULL; journal removal follows the database commit.
For a readable valid journal, death before publication retains the predecessor, death after publication triggers recovery, and a committed activation’s receipt prevents another rebuild.
Two ordinary upgrade processes targeting the same vault are serialized by the vault mutation lock and reread state inside it.
A journal targeting an unknown table row remains pending when the config names that target, and guarded opens refuse it.
A vault born at the head receives its explicit upgrade activation once; a rerun recognizes the receipt.
Direct run_doctor(fix_state=True), fresh mobile/MCP attaches, normal load_vault, and an explicitly forced below-floor shadow rebuild contain the intended checks.
No ordinary production caller or environment/config switch enabling the test allowance was found.
The examined non-upgrade imports of deleted helpers were redirected; no remaining executable reference to the searched deleted upgrade-module names was found.
The pre-floor tag exists and retains the chain; the printed 0.7, 0.8, 0.9 preliminary steps match its immediate-predecessor requirements.

COULD NOT CHECK

No tests, application processes, mutation probes, upgrades, network calls, or filesystem writes were performed.
Actual power-loss durability, concurrent-process timing, GUI watcher behavior, and background-job continuation require execution.
The restore route’s environment installation and real historical-vault readiness require an isolated executable checkout and representative backups.
The claimed real-vault projection comparisons and full-suite results were read as records, not independently reproduced.
The complete deletion set’s behavioral coverage and all dynamic import paths were not exhaustively proven.