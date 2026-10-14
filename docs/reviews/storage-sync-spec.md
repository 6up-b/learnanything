# Stage "storage-sync-spec": where LearnLoop's data lives, specified

**Branch:** `docs/storage-sync-spec` (base `bffe086ec`, `main`: migration head 202, latest algorithm `mvp-0.23`).
**Date:** 2026-10-14. Resumed after a Claude Code restart; the earlier run had written nothing (no commits, no uncommitted files), so the work started from the base.
**Deliverable:** `docs/specs/spec_storage_sync_v1.md`, "Where LearnLoop's data lives, and one learner state on every surface (v1)".
**Owner request (2026-10-14):** re-evaluate git-LFS textbook storage and SQLite-in-git so that the desktop app, a laptop, the phone on the tailnet and the MCP chat frontend all update one learner state; settle it before mobile implementation.

This is a documentation stage. No code, migration, config, test, fixture, git-LFS object, remote setting or history changed.

## What the spec contains

- **Inventory (§2):** every data class with its location, authority and citations; measurements of the owner's three working vaults on backup-API copies; schema facts at head 202; the ten tracked fixture databases and the tests that read them; the code that assumes a git working tree or a file at `canonical_uri`.
- **Problems (§3):** LFS pointers and E1; binary SQLite in git (81 database blobs, 1,051 MB, in history); the public exposure, verified without downloading content; why multi-device use stops at one machine today.
- **Requirements R1–R12 (§4)** and **options (§5):** (a) single-writer hub with offline variants a0–a2; (b) event-log replication, costed against the schema; (c) Litestream, LiteFS, libSQL/Turso, cr-sqlite, rqlite, PowerSync, Electric and `sqlite3_rsync` from their own docs; (d) file sync; (e) the originals store; (f) authored-content text history.
- **Recommendation (§6):** a hub (default `carson`) that holds each vault; a headless primary (`learnloop hub serve`) holding a `primary.lock` flock so background work runs while the desktop app is closed; a private data root; store-only source bytes and content identity for local files (completing E1); a port plan (Serve 443 private, Funnel 8443 for MCP); offline behaviour per surface; hourly backup-API snapshots plus nightly restic off-site, restore and a monthly drill; invariants (no algorithm successor for S0–S7); the changes to the mobile spec (PR-8) and to C1a/C1b/C2; phases S0–S8.
- **Migration (§7):** moving vaults and textbooks out of the repository (copy, verify, then switch pins; never delete); test fixtures rebuilt from text (builders, an opt-in `owner_vaults` lane, SQL text dumps for historical fixtures); removing git-LFS; the public-history question as owner decision H1–H3.
- **Gates G1–G12 (§8), risks (§9), owner decisions D1–D16 with defaults (§10), deferrals with triggers (§11), dated references (§12).**

## Method

- **Code read in this worktree at `bffe086ec`:** the vault paths and loader, the originals store, source registration and ingestion, the re-read, repair and Reader paths, the vault lock, `db/connection.py`, `db/copies.py`, `db/checkpoint.py`, `db/table_roles.py`, the rebuild orchestrator, `SidecarContext.load`, the post-attempt worker, the mobile host's config and doctor, the Tauri shell's vault resolution and `llpdf://` handler, the daily plan's day boundary, project understanding's store and hooks, the config loader and the ChatGPT-plan store, and the tests and conftest code that consume fixtures.
- **Branches read through `git show` only:** `mcp/c1-read-context` (the C1 spec, `remote/runtime.py`, `remote/endpoint_token.py`, the C1a record). The branch moved during the stage (to `f6c6c73b8`), and its citations were re-pinned to that tip.
- **Docs read:** the mobile spec, ADR-003, ADR-007, ADR-008, ADR-015, the State and Persistence and Data and State Map notes, the algorithm-change playbook. From the main checkout (read-only): the untracked chat-frontend research spec (§4.2) for the hosted-pilot boundary. From the session's backup notes: the GLM-OCR live check's E1 finding and the in-flight `fix/reread-safety` stage prompt.
- **Measurements:**
  - Backup-API copies (`learnloop.db.copies.backup_database`) of the three working-vault databases from the main checkout, and of all ten committed fixture databases from this worktree, into the gitignored `fixtures-local/storage-sync-measure/`. Measured on the copies: table sizes (`dbstat`), rows by table role, `canonical_uri` forms (counted by prefix, no values reported), store-copy presence by hash, attempt counts and date ranges.
  - A fresh database at head 202 was built in the session scratchpad for the schema facts.
  - The main checkout's `git status fixtures/` was the same before and after. The database files kept their sizes and modification times; only the gitignored `-shm` index mtimes moved, as any read-only open does.
- **Remote and network (read-only):**
  - `gh api` for repository visibility, branches and forks, and for the release and licence metadata of the tools compared.
  - Four anonymous `HEAD` requests (headers only) to prove anonymous downloadability: one LFS textbook, the 215 MB LFS vault object, a plain-git textbook blob and `fixtures/linear_algebra/state.sqlite`.
  - No body was downloaded, no LFS command was run, and nothing on the remote changed.
  - External documentation was fetched from primary sources (sqlite.org, docs.python.org, litestream.io, docs.fly.io, docs.turso.tech, vlcn.io, rqlite.io, docs.powersync.com, electric.ax, restic, docs.github.com, tailscale.com, the projects' GitHub repositories).
- **Not read:** no `~/.config/learnloop` file, no `.env` or `settings.env`, no credential file. No owner vault database was opened except through the backup API to make the copies.

## Gate

| Check | Result |
|---|---|
| Code citations re-checked in the worktree | 123 `file:line` citations (98 distinct ranges in 60 files), extracted by script, with each cited range printed and compared with its claim. 117 resolve in the worktree; 6 are on `mcp/c1-read-context` and were checked there at `f6c6c73b8`. 0 out of range, 0 mismatches remain. Corrected during review: `add_source.py:241-247` → `:242-249`; `source_library.py:72-87`/`:72-76` → `:73-87`/`:73-76`; `projects/hooks.py:55-75` → `:56-75`; `config/loader.py:31-47` → `:32-47`; `learnloop_mobile/config.py:13-19`, `:41-42` (that was `load_config`) → `:11-19`, `:37-38` (`config_path`), and `:13-26` → `:11-26`; `table_roles.py:44-47` → `:45-48`; `learnloop_mobile/doctor.py:85-117` → `:86-117`; `reader/span_view.py:186-193` → `:181-194`; `cli/app.py:501-525` → `:501-527`; `test_tracked_fixture_databases.py:34-40` → `:35-41`; `tests/conftest.py:100-147` → `:100-151`; the C1a record's `:84-96`, `:95-96`, `:103` → `:86-98`, `:97-98`, `:105` after the branch moved. Port numbers written as `` `:443` `` were bound by the checker as line continuations of the preceding file; they are now written "port 443" |
| Claims re-checked | Corrected during review: the working vaults are loaded directly by 13 test files, not 22/9/4 (comment-only mentions excluded); all 22 textbook PDFs in the main checkout are pointers (130–134 bytes); the probability store holds an MIT problem set and a recitation; LiteFS's FUSE basis is sourced to its README, PowerSync's write path to its docs, restic's backends and password warning to its docs; an unsupported "most books are not open-licensed" was removed; `mvp017_route_check_replay` can only be regenerated at `e238fa07a` (its README), so historical fixtures become SQL text dumps rather than builders |
| Internal consistency | Every internal § reference resolves to a heading (references to other specs are prefixed with the spec's name; §6.9 states that its numbers are the mobile spec's). D1–D16, G1–G12, R1–R12, S0–S8 and H1–H3 are each defined once and every use refers to a definition. Every reference tag used is defined in §12. Mobile-spec decisions are written "mobile D9", "mobile D11", "mobile D15". Contradictions found and fixed are listed below |
| `git diff --check` | Clean (`git diff --cached --check` on the staged spec and this record) |
| Tests | None run: no code changed |
| Paid calls | None |

**Contradictions fixed during the review pass:**
- **Backups had two owners.** The hub service "ran the backup timer" in §6.2 while S1 built the backup command before the service exists. Backups now run from `systemd --user` timers built in S1; the hub service has no backup duty, and S5's build and gates no longer list it.
- **A primary that refuses migrations.** The hub service was said to "exit 78 on a schema it does not know, like the other hosts", but it is the primary and must migrate (ADR-008). It now migrates an older schema under the vault lock and exits 78 only on a newer one.
- **A separate primary and the abandoned-synthesis sweep.** With the hub service primary, its sweep could finalize a synchronous synthesis run that the desktop (now secondary) started. PR-3 had put durable ownership of synchronous runs out of scope. PR-8 now records an owner on such runs; §6.2, §6.9 and G10 say so.
- **Snapshot consistency.** The database and the YAML were copied at different moments. The snapshot now takes both under the vault mutation lock, which every YAML writer holds; originals are copied outside it because they are content-addressed.
- **Move safety.** Writes to the old location after the copy would have been lost silently. `vault move` now takes the primary lock, and refuses to switch pins if a second snapshot of the source differs (§7.1, §9, G1).
- **Fixture policy against the facts.** "Rebuild all ten databases synthetically" contradicted `mvp017`'s README (it cannot be regenerated) and the upgrade tests' need for old history. Historical fixtures now become SQL text dumps after an owner review; D6, S3 and §7.2 agree.
- **Phase order.** "S1–S5 before mobile implementation" while S5 *is* PR-1..PR-7 plus PR-8. Now: S1–S4 land before PR-1..PR-7 start; M2a and C2 follow S5.
- **Smaller fixes.**
  - The laptop PWA row offered the tutor from M2a; the tutor arrives in M3.
  - The originals endpoint is S6's, not S5's.
  - R12 no longer claims "no redesign" (PR-8 and a port change are added).
  - The summary no longer says "no PDF" while D16 allows licensed public-domain files.
  - `mobile.toml`'s D15 and the desktop-asleep D11 now name the mobile spec.

## Code-truth findings worth the owner's attention

1. **The exposure is real and wider than LFS.**
   - Anonymous requests return the owner's `state.sqlite` (45 MB) and textbooks, both through LFS and as plain git blobs in the vault stores (Axler; Blitzstein and Hwang; MIT course PDFs).
   - The databases also hold extracted book text: 1,074, 579 and 4,717 blocks.
   - A public fork has existed since 2026-07-21.
2. **The mobile host and the chat frontend cannot both use port 443.** The as-built mobile doctor requires Serve-only on 443 (`src/learnloop_mobile/doctor.py:86-117`), and the C1a runbook points Funnel's 443 at MCP. The spec puts MCP on Funnel 8443 (D7), which also answers C1a's Q3.
3. **As specified, phone answers wait for the desktop app to be diagnosed.** The post-attempt worker is bound only by `SidecarContext.load`, and secondary attach runs none of it. The hub service fixes this.
4. **E1 has two remaining causes after `fix/reread-safety`:**
   - extraction repair still re-acquires from `original_uri`/`canonical_uri` (`src/learnloop/content/pipeline/jobs.py:2460-2465`);
   - local-file identity is the absolute path, so a moved book becomes a second artifact.
5. **Every revision's bytes are already in its vault's store** (19 of 19). Moving the vaults out of the repository loses no source.
6. **Project understanding's git hook writes to an absolute local path,** so repositories on a machine other than the hub's are not captured.
7. **"Today" is the hub's local date** (`src/learnloop/daily_plan/engine.py:150-153`).
8. **The working-vault databases are at migration 165** (main is at 202). Their latest attempts are from 2026-07-28 (linear_algebra) and 2026-08-04 (probability), so the owner's day-to-day vault may be elsewhere. §7.1's inventory step asks the owner to list the vaults in use; agents never search for them.

## Open questions for the owner

1. **D1 and D2:** make the repository private now (recommended, reversible), and choose H1 (a new clean public repository later; recommended), H2 (rewrite in place; destructive) or H3 (leave history). No agent can act on these.
2. **D3 and D4:** is `carson` the hub, and may it stay awake (no automatic suspend, or Wake-on-LAN at night)?
3. **D5 and D8:** the data-root paths, and the off-site backup target for restic (B2, S3, or SFTP to `mimas` or `minty`).
4. **D6:** review the historical fixtures' content (`migration_head_202`, `linear_algebra_legacy`; `mvp017_route_check_replay` is synthetic) and the three text fixtures before they become text dumps in a public repository.
5. **D7:** re-point Funnel to 8443 and update the connector URLs in Claude and ChatGPT when S5 lands.
6. **The vault inventory (§7.1 step 1):** which vaults are in use today, including any under `fixtures-local/` or `~/LearnLoop`.
7. **For the chat frontend's next stage:** adopt §6.10 (Funnel 8443, a deployment checkout, the vault under the data root) in C1a's runbook before C1b.
