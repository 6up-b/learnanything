# Stage "storage-sync-spec": Codex review and fixes

**Branch:** `docs/storage-sync-spec` (base `bffe086ec`; the spec's first draft is `11fb0190d`).
**Review:** Codex job `20261014-161725-LxV7WQ`, 11 findings (F1–F11), plus the two owner-directed items.
**Fix commit:** `5e75f46f8` (spec and stage record). This record is the commit after it.
**Date:** 2026-10-14. Documentation only: no code, test, fixture, file move, git-LFS object, remote or history changed.

## Owner direction applied (2026-10-14)

"I want to keep the repo public so that people can use it, contribute to it, and in the future possibly contribute their data for a larger n>1 learned model ecosystem."

1. **D1 decided: the repository stays public.** "Make it private" is gone. S0 is now its own early phase that cleans the public tip within days, once the owner has copies outside every checkout. The history options are re-weighed for a public project that wants contributors: H1 (a clean public repository under the same name, from a rewritten mirror) is recommended, and the spec says plainly that the public fork and every clone keep their copies under every option. The licence of every tracked third-party file was checked against primary sources (§3.5). The few openly licensed files are proposed as small, attributed samples (D16). A code licence is proposed (D17, Apache-2.0, owner confirmation required).
2. **Opt-in data contribution added** as R13, §6.12 and the deferred phase S9, with gate G14, decision D18 and triggers in §11. The spec fixes requirements and design constraints only: a versioned, documented, allowlisted export of attempts, grades, diagnoses, misconceptions and events; pseudonymous contributor ids; consent that is recorded, scoped and revocable; source text and personal free text redacted by default, with quotes of books stripped even from opted-in text; a data licence distinct from the code licence (CDLA-Permissive-2.0 proposed); a dataset store separate from the code repository; withdrawal and its limits. A contribution is a one-way export from a snapshot. It is never a sync peer, never imported and never replayed.

## Findings

Severity is the reviewer's for F1–F11 and mine for A1–A12, which came from the adversarial re-review the stage asked for (questions (a)–(e) below). All fixes are in `5e75f46f8`.

| Id | Severity | Title | Verdict | Commit | Reproduction or evidence |
|---|---|---|---|---|---|
| F1 | High | Exposure response contradicts the decision to stay public | Fixed in part; **reopened** by the re-review (S0 still exempted `migration_head_202`) and fixed in `e38969350` (see "Re-review" below) | `5e75f46f8` | Checked against the first draft (D1 recommended making it private; S0 did nothing). Now: D1 decided; S0 cleans the tip; H1/H2/H3 re-weighed (H2 no longer mandates deletion and names the Support route); history stays owner-only. The GitHub docs were re-read: Support purges only "if … no forks have references to the sensitive data", and it "won't remove non-sensitive data". The public fork does reference the data, so H2's purge may never happen, and the H2 row says so. The stage record's open questions were updated |
| F2 | High | Future opt-in contribution has no data contract | Fixed | `5e75f46f8` | Confirmed: the first draft had none. The only export, `dataset-export`, copies every RAW_LEDGER and RECEIPT table verbatim with `snapshot.sqlite` (`src/learnloop/substrate/dataset.py:670`, `:716`), so it carries book text and answers. Added R13, §6.12, S9, G14, D18 and §11 triggers, with withdrawal limits for releases already downloaded and models already trained |
| F3 | High | Default backups cannot meet the stated disk-loss bound | Fixed | `5e75f46f8` | Confirmed: `~/learnloop-backups` and the vaults share the hub's disk, and the off-site copy was nightly. Now restic copies each complete snapshot to another device within the hour. Doctor and Settings show the age of the newest complete copy in each place, not a promise. Litestream is qualified as covering the database only: its how-it-works page describes only SQLite WAL pages |
| F4 | High | Desktop secondary disables the ingest machinery its UI needs | Fixed | `5e75f46f8` | **Reproduced** (`scratchpad/repro_f4_f5.py`, synthetic vault): an unbound `IngestJobManager` raises `RuntimeError: Ingest jobs are not bound to a vault yet.` on `enqueue_add_source` and `cancel` (`jobs.py:3577-3580`). Now PR-8 has a submit-only ingest binding with durable cancel and status, covering attach, reload and vault switch. G10 covers Add, re-read, repair, Reader builds, batch cancel and stopping a running call from the desktop secondary |
| F5 | High | An idle hub may never discover remote diagnosis jobs | Fixed | `5e75f46f8` | **Reproduced** (same script): `SidecarContext.load` on an empty queue, then `resume_post_attempt_jobs()`, left the worker not running. A `post_attempt_jobs` row committed by another process was still `queued` 5 s later with no worker thread (`post_attempt_worker.py:12-14`; `context.py:180-192`). Now: workers start at `load()`; a `PRAGMA data_version` watch (its semantics re-read on sqlite.org) plus a 30 s rescan; a 5 s dispatch bound kept separate from model time. G10 gets the idle-start case, and §6.9 adds it to mobile G6b |
| F6 | High | Moving a vault can keep a live connection to the old database | Fixed | `5e75f46f8` | **Reproduced** (`scratchpad/repro_f6.py`, synthetic files) with `copy_tree_with_databases`: an absolute `sqlite_path` copied no database, and the copy's config resolved to the *same file* as the source. A `..` path resolved to a missing file beside the destination (the source's only when both share a parent). A `learner.db` was byte-copied with its `-wal` and `-shm`. A symlinked `state.sqlite` was followed and backup-copied. The move now resolves the database first, copies it once through the backup API to `<dst>/state.sqlite`, rewrites only the destination's config, and proves it does not share the source's file. Added doctor `storage:database_outside_vault`, G1 cases and the restore rule. Wording corrected for the `..` case |
| F7 | Medium | Copying originals outside coordination gives incomplete snapshots | Fixed | `5e75f46f8` | Confirmed by code: capture purge unlinks inside a database transaction (`capture/inbox.py:293-302`) and source deletion unlinks after its cascade commits (`source_deletion.py:291`, `:318-330`). Neither takes the vault mutation lock. Now: staged snapshot (originals first, then databases under the lock, then any referenced digest still missing), verified and published atomically. A snapshot that stays incomplete is marked and excluded from retention, the off-host copy and the shown ages. G2 covers the race |
| F8 | Medium | Licence policy substituted blanket exclusion for an audit | Fixed | `5e75f46f8` | §3.5 now records, for every tracked third-party file and its copies: edition, licence evidence from the file or the licensor, whether it is redistributable, and its disposition. Spot-checked locally with `pdftotext`: Axler is the fourth edition, "© 2024 … Creative Commons Attribution-NonCommercial 4.0"; the MIT files carry the OCW terms footer (18.06 Spring 2010 quiz, 6.041 problem set); Blitzstein and Hwang is "© 2019 Taylor & Francis", with no licence. The licensor pages were re-read: Axler (CC BY-NC, fourth edition), MIT OCW terms (CC BY-NC-SA 4.0), GVSU (CC BY 4.0), 3Blue1Brown's FAQ, CDLA-P-2.0. "Free to read" is kept distinct from permission to redistribute |
| F9 | Medium | Vault relocation leaves project hooks writing to the old vault | Fixed | `5e75f46f8` | Confirmed by code: the hook appends to an absolute `pending.jsonl` and exits quietly when its directory is gone (`projects/hooks.py:56-75`). The move now lists hooks, reinstalls them on the owner's confirmation (`install_hook` keeps the rest of the hook, `hooks.py:106-133`; CLI `learnloop project install-hook`) and carries late lines over. The byte-offset sweep reads each once (`projects/capture.py:1007-1013`). G1 covers it |
| F10 | Medium | "Untrack" does not preserve files in other checkouts | Fixed | `5e75f46f8` | **Reproduced** in a scratch repository: after `git rm -r --cached` was committed in one clone, a fast-forward in another clone deleted the clean tracked files. A clone with a modified `state.sqlite` refused the merge ("Your local changes … would be overwritten"). Moving the directory out first, then merging, applied cleanly and kept every byte. §7.1 step 6 now states the consequence, requires verified copies outside every checkout, gives the owner-run update procedure, and makes landing such commits the owner's step |
| F11 | Medium | S7 offered a copy path that contradicts the ADR guarantee | Fixed | `5e75f46f8` | Confirmed against `sqlite.org/rsync.html` ("Only a single database is synchronized for each invocation"; the replica is read-only during a sync). `sqlite3_rsync` now only moves a finished snapshot's closed database file, never the live vault. a1, S7, §5.3 and §6.8 agree |
| A1 | Medium | The licence audit and S0 missed tracked files outside `fixtures/` and `new_textbooks/` | Fixed | `5e75f46f8` | `git ls-files` found four PDFs under `docs/brainstorming/`, read locally: DTransKT (CC BY-NC-ND 4.0, 8.6 MB, over G8's 5 MB limit), a CC BY 4.0 ACM paper, an AISTATS paper with no licence, and Carnegie Learning slides marked "©". It also found 44 screenshots: two were opened, one showing a full Axler page and one the owner's answer with its grading. Added to §3.5, S0 (papers cited by DOI or link), G13, D19 (keep the owner's own content; attribute or replace book pages) and R6 |
| A2 | Medium | Snapshot step 4 dropped store files no reference names | Fixed | `5e75f46f8` | Project understanding stores diff bundles in the originals store and references them from `projects/project_store.sqlite`, not `state.sqlite` (`projects/capture.py:550`, `:708`). A reference list that missed them would have deleted them from every backup. Unreferenced files are now kept and counted, never dropped |
| A3 | Medium | Renaming a vault out of the checkout (S0 before S1) leaves the desktop's pin stale | Fixed | `5e75f46f8` | `resolve_vault` falls back silently when `last_vault` no longer names a vault: to the first `fixtures-local/` vault, else it creates `~/LearnLoop` (`sidecar.rs:671-679`, `:748-755`, `:735-745`). The S0-first path now re-points every pin at once. Added a risk in §9 |
| A4 | Medium | Moving Funnel to port 8443 without changing `--public-host` | Fixed | `5e75f46f8` | C1 §3.2's Host allowlist is exact, and the runbook's unit passes `--public-host <host>.ts.net:443` (`docs/reviews/mcp-c1a.md:107` at `c06f73aae`), so every request through 8443 would get a 421. §6.10 and D7 now change it in the same step. Connector support for port 8443 is marked unverified, with a port-swap fallback |
| A5 | Low | Desktop-submitted work runs with the hub service's environment | Fixed | `5e75f46f8` | `LEARNLOOP_AI_PROVIDER` is read per process (`ai/routing.py:247-249`, `:308-310`), and the `pdf` and `glm-ocr` extras are per environment. §6.2 now says routes and extras follow the primary; G12 shows them, and the desktop flags a difference |
| A6 | Low | Hand-back of the primary role was unspecified | Fixed | `5e75f46f8` | A desktop that promoted itself during a service restart now keeps the role until it quits or switches vaults, and the waiting service then takes it |
| A7 | Low | Contribution identity and time alignment | Fixed | `5e75f46f8` | Shifting timestamps per contribution would have misaligned a learner's successive contributions; the origin is now fixed per contributor id. A learner with several vaults may share one id. The withdrawal secret's storage is specified and it is never exported; G14 covers this |
| A8 | Low | S0's claim "removes the personal data" overstated | Fixed; superseded by the re-review's F1 | `5e75f46f8` | Measured on a backup-API copy: `migration_head_202` holds 6 of the owner's attempts with answers (2026-05-30 to 05-31) and one video transcript. This pass made the claim honest by keeping the fixture until S3; the re-review rejected that deferral, and `e38969350` sanitizes it in S0 instead |
| A9 | Low | `vault move` migrating contradicted "only the hub service migrates" | Fixed | `5e75f46f8` | §6.2, §6.8, §9 and D13 now name the one exception: the move migrates its copy once, after the first snapshot, from the deployment checkout |
| A10 | Low | D17 silent on dependency terms | Fixed | `5e75f46f8` | Marker's code is Apache-2.0, but its model weights are free only for research, personal use and small startups (its README). D17 now says the code licence covers LearnLoop's code only |
| A11 | Low | Chat-frontend branch moved | Fixed | `5e75f46f8` | `mcp/c1-read-context` moved from `f6c6c73b8` to `c06f73aae`, shifting `mcp-c1a.md` lines by 2. Re-pinned: `:105`→`:107`, `:86-98`→`:88-100`, `:97-98`→`:99-100`. `remote/runtime.py:58-61`, `:131-140` and `endpoint_token.py:23-24` are unchanged |
| A12 | Low | GitHub repository facts re-checked | No change needed | — | Read-only `gh api` on 2026-10-14: public, 1 star, 0 watchers, 1 fork, 6 pull requests (1 open), 0 issues, `license: null`. Matches §3.3 |

**Rejected:** none. Every finding reproduced or was confirmed against the code, the spec or a primary source. (F1's "Fixed" was premature: see the re-review.)

## The adversarial review the stage asked for

- **(a) Does the hub satisfy "dailies anywhere update the same learner model", right-sized?**
  - Yes, once F4 and F5 are fixed. One learner state, one host, no merge. The primary discovers every queue from startup, and the desktop keeps every feature as a secondary.
  - Offline is honest: capture queues, and practice waits for the hub (mobile D9).
  - Right-sized for one learner: one more user unit, an OS lock rather than a lease, polling rather than a broker. A0 stays the default, and a1, a2 and (b) wait for triggers.
- **(b) Are the replication-tool claims accurate?**
  - Re-read this session: Litestream's how-it-works page, `sqlite3_rsync`, SQLite Sync's README and API (release 1.2.0 of 2026-09-28 confirmed with `gh api`), and `PRAGMA data_version`.
  - The reviewer's own checks of Turso, cr-sqlite, rqlite, PowerSync and Electric support the table.
  - Nothing better was found: SQLite Sync carries the CRDT objections of (b) plus a sync backend.
- **(c) Invariants and safety.**
  - Every live-database copy goes through `learnloop.db.copies`, and the external-path hole (F6) is closed.
  - Replay, table roles and migrations are unchanged. Migration authority is now consistent (A9).
  - No step is destructive for an agent: untracking lands only by the owner, the owner deletes retired directories, and history, visibility and repository creation are the owner's.
  - The owner's working vaults were not opened. The `migration_head_202` measurement used a backup-API copy of the worktree's tracked fixture.
- **(d) Exposure and decisions.**
  - The facts were re-checked (A12). The audit now covers every tracked binary (A1). H2's dependence on Support is stated precisely (F1).
  - D1 is decided, D2 stays the owner's, and D17–D19 have defaults.
- **(e) Conflicts.**
  - Mobile: PR-8 extends PR-1 and PR-3, G6b gains the idle-start case, and M3's restricted runner is unnecessary under a hub service.
  - C1a, C1b and C2: Funnel 8443 needs the `--public-host` change (A4).
  - Reader, GLM-OCR and re-read safety: S2 lands after `fix/reread-safety`, Reader builds and re-reads are in G10 under a desktop secondary, and extraction extras follow the primary (A5).

## Gate

| Check | Result |
|---|---|
| Internal consistency | D1–D19: 19 defined, 0 duplicates, 0 used but undefined. R1–R14: 14. G1–G14: 14. S0–S9: 10 phases, 0 undefined uses. H1–H3 defined once each. 35 reference tags in §12: every tag used is defined and every defined tag is used (the checker's one hit, `[hub]`, is a TOML table name in code formatting). Every `§` reference resolves to a heading here, except 7 that name another document (C1 §4.2 research appendix, mobile §4.5, SQLite-corrupt §1.2–§1.4). Contradictions found and fixed in this pass: A8 (S0's claim), A9 (migration authority), R6 and the summary against D19, and the order of D17–D19 |
| Code citations re-checked in the worktree | 164 cited ranges: 159 with full paths in 70 files, plus 5 short forms after a full path (`jobs.py:3489`, `:4693-4696`; `runner.py:564-575`; `dataset.py:670`, `:716`). A script bounds-checked every range and printed each range's first line next to its claim. The 36 distinct ranges added or changed since the first draft (`11fb0190d`) were read in full. 157 resolve in this worktree at `bffe086ec` code. 7 are on `mcp/c1-read-context` and were checked with `git show` at `c06f73aae`. 0 out of range, 0 mismatches |
| `git diff --check` | Clean (on the fix commit's staged diff and on this record) |
| Reproductions | 4 of 4 testable findings reproduced (F4, F5, F6, F10) with scripts in the session scratchpad on synthetic vaults and files and a scratch git repository; none touched a tracked fixture or an owner vault |
| Tests | None run: no code changed |
| Paid calls | None |
| Safety | No `tailscale` or `git lfs` command; no remote mutation (read-only `gh api` and web reads of primary docs only); no history rewrite; no file moved; no LFS object or third-party PDF downloaded (licence text read from the worktree's already-materialized copies); no `~/.config/learnloop`, `.env`, `settings.env` or credential file read; the main checkout untouched (two tracked `learnloop.toml` lines read there to confirm the live vaults' `sqlite_path` is still the relative `state.sqlite`) |

## Open for the owner

- **D2:** H1 (recommended), H2 or H3, run by the owner from a fresh mirror clone.
- **S0's preconditions:** copies of the affected vaults and the textbooks outside every checkout; then land S0 by §7.1 step 6.
- **D17:** confirm Apache-2.0 (or AGPL-3.0) before a `LICENSE` lands.
- **D19:** keep the screenshots (recommended), with book pages attributed or replaced.
- **D7:** when re-pointing Funnel, confirm both chat connectors accept port 8443; otherwise use the swap.
- **D18:** decided at S9's checkpoint.

---

## Re-review (Codex job `20261014-194657-QmEBhT`) and its fixes

**Reviewed:** `11fb0190d..42ebd40c8`. **Verdict:** REOPENED (F1), with three new Medium findings (F12–F14); F2–F6 confirmed fixed.
**Fix commit:** `e38969350` (the spec only). This section is the commit after it.
**Date:** 2026-10-14. Documentation only: no code, test, fixture, file move, git-LFS object, remote or history changed.

### Findings

Severity is the reviewer's for F1–F14 and mine for A13–A16, which came from this pass's adversarial review.

| Id | Severity | Title | Verdict | Commit | Reproduction, test or reason |
|---|---|---|---|---|---|
| F1 | High | S0 still exempts `migration_head_202` (six owner attempts, a non-redistributable transcript) until S3 | Fixed | `e38969350` | **Reproduced** against the spec at `42ebd40c8`: the S0 row ended "`migration_head_202` and `mvp017_route_check_replay` stay until S3 (D6)". **Measured** on a backup-API copy of the tracked fixture (`learnloop.db.copies.backup_database` into the worktree's `fixtures-local/`; the tracked file was unchanged afterwards, `git status` clean): 6 attempts (2026-05-30T01:12:39Z to 05-31T18:45:55Z) with answers of 26–139 characters in `practice_attempts.learner_answer_md`, one answer quoted in `error_events.repair_plan_json`; the 1,153-word transcript in the store file, nearly all of it again in the note (584 shared eight-word windows), 8 windows in `concepts.yaml`, and quotes in `proposed_patch_items.payload_json` and `proposed_patches.source_refs_json`; no `source_artifacts` or `source_revisions` rows; the store file's name is a note id, not its SHA-256 (`073c823c…`); no trigger on the four tables involved; journal mode DELETE. **Fix:** S0 sanitizes the fixture with a script on a backup-API copy (transcript, note, quoting YAML and rows rewritten from project-authored text; answers replaced by synthetic ones of the same kind; `sqlite_master`, applied migrations and journal mode unchanged; an eight-word sweep finds no original text). The owner approves the remaining shape of six attempts at S0's checkpoint, or S0 untracks the fixture and moves its 21 test files and the two DB-reference scripts to the owner lane until S3. Summary, §2.4, §3.5, §6.11 S0, §7.2, G13, D1, D6 and §9 agree. Section 1 of this record now says F1 was premature |
| F2 | High | Opt-in contribution data contract | Confirmed fixed by the reviewer | — | No change |
| F3 | High | Backup loss bound | Confirmed fixed by the reviewer | — | No change; its Litestream pairing became F12 |
| F4 | High | Desktop secondary and ingest | Confirmed fixed by the reviewer | — | No change |
| F5 | High | Idle hub queue discovery | Confirmed fixed by the reviewer | — | No change |
| F6 | High | Vault move and external databases | Confirmed fixed by the reviewer | — | No change |
| F12 | Medium | Litestream restore pairs a newer database with older files | Fixed | `e38969350` | **Confirmed** against Litestream's current primary docs: it replicates SQLite databases only, even in directory mode ("replicate all matching SQLite databases"; non-SQLite files skipped); restore takes `-timestamp` or `-txid` and "can only land on the boundaries of files that still exist in the replica"; snapshots kept 24 hours by default. The old row paired the restored database with "the nearest complete snapshot's files", which fails G2 in the reviewer's 10:00/10:20/10:30 scenario. **Fix:** a shorter snapshot interval first (down to 15 minutes); Litestream only with coordinated file protection (store files and text files sent off the hub within a minute of a write) and a verified common recovery point (the database restored to the newest file capture's time, never later; G2's checks; fallback to the previous capture, then the complete snapshot). G11 now tests an import, an accepted proposal, a hand-edited YAML file and a capture purge between snapshots. §5.3, §6.7, D8, §9, §11 and §12 agree |
| F13 | Medium | Binary guard rejects the screenshots and the app icons | Fixed | `e38969350` | **Reproduced** with `git ls-files` and a NUL-byte check: besides the fixtures and `new_textbooks/`, the tracked binaries are 44 PNGs under `docs/` (`docs/screenshots/` 8, `docs/ux/screenshots/` 16, `…/phase1/` 20), four PDFs under `docs/brainstorming/`, and `apps/learnloop-tauri/src-tauri/icons/icon.png` and `icon.ico`, which `tauri.conf.json:34-35` names. The old G8 ("a PDF or other binary outside the `samples/` allowlist") fails on the 46 images. **Fix:** G8 and the §7.2 guard row are per-class: databases (by name or header) only on the S0 allowlist; PDFs, EPUB, DjVu, audio and video only under `samples/`; other binaries only as images under `docs/` and application assets under `apps/`; no file under `canonical-sources/` outside the historical fixtures; NOTICE, 5 MB and LFS rules unchanged. The guard cannot see image content, so D19's list reviews `docs/` images. §3.5's method now names the two icons |
| F14 | Medium | A promoted desktop can block a service upgrade indefinitely | Fixed | `e38969350` | **Confirmed** against the spec at `42ebd40c8`: A6's hand-back ("keeps the role until it quits or switches vaults") plus an upgrade of "deploying a tag … and restarting the units", with the desktop forbidden to migrate. Also found: a process left running across a checkout change would mix old and new code, and the desktop's sidecar runs from the checkout it was built in (`repo_root()`, `sidecar.rs:640-645`, compile-time `CARGO_MANIFEST_DIR`). **Fix:** `learnloop hub upgrade <tag>` stops the units, waits on a shared `attach.lock` that every process holds (asking the owner to quit the app; never killing it), writes an update mark that blocks promotion and attach, moves the checkout, starts the service, which holds the primary role from before its pre-migration snapshot through the migration, then the secondaries; `--abort` for a failed migration. Promotion now also requires no mark and a matching schema. G10 covers the case; §6.8, §6.9 (PR-8), §6.10 (C1a's attach), §9, D13 agree |
| A13 | Medium | From S1 to S5 the owner's vaults could not migrate at all | Fixed | `e38969350` | Found checking (c): `vault move` (S1) recorded `migrate = "service"`, but the hub service arrives only in S5, and the desktop "never migrates" such a vault; any migration landing on `main` in between would have locked the owner out. **Fix:** the `[hub]` rule is staged: `migrate = "deployment"` from S1 (the desktop app built from the deployment checkout migrates after a snapshot; other builds do not), `migrate = "service"` from S5. §6.2, the pre-migration row of §6.7, §6.8, §6.11 S1 and S5, G1, §9 and D13 agree |
| A14 | Low | Tool survey missed dqlite and Marmot | Fixed | `e38969350` | Read their repositories and confirmed releases with read-only `gh api`: dqlite (Raft, own protocol, LGPL-3.0 with exception, v1.18.7 of 2026-07-02) is rqlite's case; Marmot (leaderless, row-level last-write-wins on an HLC, "Rows may sync out of order", MIT, v2.10.0-beta of 2026-09-30, every recent release a pre-release) is option (b)'s case. Neither is better. Litestream's v0.5.17 (2026-08-31) is still the latest release |
| A15 | Low | H1's by-path rewrite would delete the sanitized fixture | Fixed | `e38969350` | Keeping a sanitized `migration_head_*` at the tip means a path filter would remove it with its history. H1 now strips old blobs by id (`--strip-blobs-with-ids`, re-read in filter-repo's manual), so every earlier version goes and the sanitized tip stays |
| A16 | Low | §3.5's method omitted the two app icons | Fixed | `e38969350` | Same `git ls-files` listing as F13 |

**Rejected:** none. Every re-review finding reproduced against the spec, the tracked files or a primary source.

**Owner-directed items, re-verified.** D1 stays decided (public); "make it private" appears nowhere as a recommendation; H1/H2/H3 stay owner-only and say plainly that the fork and clones keep their copies; §3.5's licences stand (no file was re-licensed by this pass); §6.12, R13, S9, G14 and D18 are unchanged and the reviewer confirmed them (F2).

### The adversarial review, again

- **(a) Dailies anywhere, right-sized?** Yes. Unchanged by this pass except that upgrades are now a single owner command that may ask the owner to quit the app; offline stays a0 with honest labels. A13 closes a gap in which the owner's vaults could not have taken new code between S1 and S5.
- **(b) Replication tools.** Litestream's restore and directory docs re-read (F12); dqlite and Marmot added (A14). Nothing fits better than a hub with complete snapshots.
- **(c) Invariants and safety.** The sanitizer runs on a backup-API copy, keeps rollback mode and the schema byte-identical, and lands only with the owner's approval; ADR-007 governs vaults, not fixture builds. Migration authority is consistent across phases (A13). No step is destructive for an agent: history (H1, now by blob id), visibility, repositories and retired directories remain the owner's.
- **(d) Exposure and decisions.** After S0 the tip carries no third-party text and none of the owner's words; what remains of six attempts is the owner's call (D6). D1 decided, D2 owner-only, D8 and D13 updated with defaults.
- **(e) Conflicts.** Mobile: PR-8 gains the attach lock and update mark; the mobile host's existing refusal at start (status 78, mobile G1) is unchanged and the upgrade starts it after the migration. C1a: its attach takes the same lock and checks the mark (§6.10). The head-fixture upgrade procedure in CLAUDE.md and mobile §8 (`migration_head_<N>`, rollback mode) continues on the sanitized fixture. Reader, GLM-OCR and re-read safety: unaffected.

### Gate

| Check | Result |
|---|---|
| Internal consistency | D1–D19: 19 defined, 0 duplicates, 0 used but undefined. R1–R14: 14. G1–G14: 14. S0–S9: 10 phases, 0 undefined uses. H1–H3 defined once each. 40 reference tags in §12 (5 added: Litestream-restore, Litestream-dir, filter-repo, dqlite, Marmot), every one used and every used tag defined. 197 `§` references: all resolve to a heading here except 7 that name another document (C1 §4.2, mobile §4.5, SQLite-corrupt §1.2–§1.4). Contradictions removed in this pass: S0's "any that one reads leaves with its fixture's dump in S3", the §6.7 pre-migration row naming only the hub service, ADR-008's row, the version-skew risk and D13 against the staged rule (A13) |
| Code citations re-checked in the worktree | 131 distinct cited ranges in 71 files (a script resolving full paths, basenames and `:N` short forms, then bounds-checking each and printing its first line next to its claim): 125 in this worktree at `bffe086ec` code, 6 on `mcp/c1-read-context` checked with `git show` at `c06f73aae`; 0 out of range, 0 mismatches. New or re-cited in this pass, read in full: `sidecar.rs:640-645`, `tauri.conf.json:34-35`, `apply_protocol.py:575`. (The first pass's "164" counted citations, not distinct ranges.) |
| `git diff --check` | Clean on `e38969350` (`git diff 42ebd40c8 e38969350 --check`) and on this record |
| Reproductions | 4 of 4 re-review findings reproduced or confirmed (F1 measured on a backup-API copy; F13 by `git ls-files`; F12 and F14 against the spec and primary docs) |
| Tests | None run: no code changed |
| Paid calls | None |
| Safety | No `tailscale`, `git lfs`, history or remote mutation; read-only `gh api` and web reads of primary docs only; no file moved and no fixture changed (the backup-API copy lives in the gitignored `fixtures-local/` and was deleted afterwards); the owner's working vaults not opened; no `~/.config/learnloop`, `.env`, `settings.env` or credential file read; the main checkout untouched |

### Open for the owner (replaces the list above)

- **S0's checkpoint:** approve the sanitized `migration_head_202`'s remaining shape (six graded attempts on parabola items, 2026-05-30 and 05-31, none of your words), or have it untracked with its tests in the owner lane until S3 (D6).
- **D2:** H1 (recommended, now by blob id), H2 or H3, run by the owner from a fresh mirror clone.
- **S0's preconditions:** copies of the affected vaults and the textbooks outside every checkout; then land S0 by §7.1 step 6.
- **D17:** confirm Apache-2.0 (or AGPL-3.0) before a `LICENSE` lands.
- **D19:** keep the screenshots (recommended), with book pages attributed or replaced.
- **D7:** when re-pointing Funnel, confirm both chat connectors accept port 8443; otherwise use the swap.
- **D8:** if an hour of loss is too much, a 15-minute interval first; Litestream only with coordinated file protection.
- **D18:** decided at S9's checkpoint.

---

## Final verify fixes (Codex job `20261014-200527-T3pFwf`)

**Reviewed:** `42ebd40c8..0abe2f23a`. **Verdict:** REOPENED: F12 (Medium) and F14 (High) reopened, F15 (Medium) new; F1–F6 and F13 confirmed fixed and left as they were.
**Fix commit:** the commit that adds this section (the spec, the stage record's summary lines and this record).
**Date:** 2026-10-14. Documentation only: no code, test, fixture, file move, git-LFS object, remote or history changed.

### Findings

| Id | Severity | Title | Verdict | Reproduction, test or reason |
|---|---|---|---|---|
| F12 | Medium | A Litestream restore can pair an older database with newer captured files, and intent recovery then overwrites a captured manual edit | Fixed | **Reproduced** (`scratchpad/finalfix/repro_f12_f15.py`, scratch files only): a target written with a hand edit after its intent (neither `pre_hash` nor `post_hash`) was replaced by the intent's content when passed to `materialize_targets`, which skips only a file at `post_hash` (`apply_protocol.py:335-363`, `:347`); `recover_apply_intents` calls it for every pending intent (`:575-596`). Litestream's restore page re-read: with `-timestamp` "a file must have been created strictly before the requested timestamp", and "not every replicated transaction is a valid restore point". **Fix:** a whole-vault snapshot is the only restore unit in v1. It copies the databases and the text files under one hold of the vault mutation lock, which acceptance holds from its intent's commit to its applied mark (`patches.py:92-93`, `:204-217`), writes a manifest (every file's SHA-256, each database's applied migrations), re-hashes each text file after copying it to catch an edit made outside LearnLoop, and restore verifies the manifest before anything else. Apply-intent recovery, after a restore or under `doctor --fix-state`, compares each target with the intent's recorded hashes (`apply_protocol.py:228-253`) and, on any other content, writes nothing, performs no database effect, leaves the intent pending and reports `apply_intents:conflict`; the owner keeps the file and can mark the intent rolled back (the existing status, `migrations/044_provenance_manifests_apply_intents.sql:159`). Litestream and any continuous database-only replication are deferred to §11 with a trigger (less loss than a 15-minute interval gives); a shorter snapshot interval is D8's lever. G11 is now S1's gate and combines a proposal application, a later hand edit of the same file and a delayed snapshot in one scenario, with crash variants. Summary, R7, §5.3, §5.7, §6.7, §6.11 S1, G2, G11, §9, D8, §11 and §12 agree |
| F14 | High | The upgrade barrier is per vault, but the deployment checkout is shared by every vault | Fixed | **Confirmed** against the spec at `0abe2f23a` (steps 2–3 named one vault's attach lock and mark) and the code: units run from one checkout's environment (`deploy/learnloop-mobile.service:7-9`). **Fix:** one barrier for the deployment. Every LearnLoop process holds a shared lock on `.learnloop/deploy.lock` in the checkout its code runs from (`migrate.py:40-41` already resolves that root; `.learnloop/` is ignored at any depth, `.gitignore:197`) and checks the deployment's mark before every attach; each vault keeps its attach lock and mark for development builds. `learnloop hub upgrade` writes the deployment's mark and every vault's mark first, stops every unit of the deployment, waits for every process of the deployment and on its vaults (never killing one), changes the checkout, starts every vault's hub service, each of which snapshots, migrates and then idles holding the primary role, and removes the marks only when every vault has migrated. Before S5 the upgrade also stops units already moved to the deployment checkout and opens each vault once. G10 gains the two-vault case (a desktop opened on B before and after the upgrade starts; nothing attaches to A until B has migrated). §6.2, §6.8, §6.9 (PR-8), §6.10 (C1a), §6.11 S5, §9 and D13 agree |
| F15 | Medium | Upgrade abort assumed the migration sequence rolls back | Fixed | **Reproduced** with the same script: a scratch database at 202, migrations 203 (valid) and 204 (fails) applied with `apply_migrations`: `OperationalError no such table: missing_table`, applied versions `[202, 203]`, 203's table present. `apply_migrations` commits each migration before the next (`migrate.py:84-88`; `BEGIN IMMEDIATE` at `:189`, `commit()` at `:209`); ADR-008's atomicity is per migration. **Fix:** a failure stops that vault's service and keeps the whole barrier; doctor names the vault, the failed migration and the last committed one. Abort (`learnloop hub upgrade --abort`) restores the verified pre-upgrade snapshot of every vault whose migrations changed, the already-migrated ones included, into a new directory and switches the pins, then returns the checkout; nothing restores over the partly migrated directories, and no work is lost because the services ran no duty after their snapshots. Repair forward is an upgrade to a fixed tag, which applies from the first unapplied migration. The pre-migration snapshot must be complete and verified, or the vault does not migrate. Before S5 the same two choices apply by hand. G10 tests a failure after one migration has committed, on one vault and on B after A has migrated, with abort and with repair forward. §6.2, §6.7, §6.8, §9 and D13 agree |
| A17 | Medium | A development build reads only the vault's mark, so removing it per vault would let one attach before the other vaults finish | Fixed | Found while designing F14: services no longer remove their vault's mark; the upgrade removes every vault's mark, then the deployment's, once every vault's applied migrations are the tag's |
| A18 | Low | An abort or a restore must not lose work done between the snapshot and the switch | Fixed | A hub service that ran its duties after migrating while another vault was still migrating would write to a vault that an abort then restores from its earlier snapshot. Services now hold the role and run no duty until the marks are gone |
| A19 | Low | Read-only inspection during the barrier | Fixed | `learnloop hub doctor` must report a failed upgrade while every attach is blocked; read-only inspection (ADR-008's read-only open) is exempt from the deployment's mark |
| A20 | Low | `restore` switched pins but not project hooks | Fixed | The restore row now re-points enrolled hooks on confirmation, as `vault move` does (§7.1 step 4), which an abort's restore relies on |

**Rejected:** none. Each reopened or new finding reproduced (F12, F15) or was confirmed against the spec and the code (F14).

### The adversarial review, once more

- **(a) Right-sized for one learner?** Yes, and smaller than before: the Litestream lane, coordinated file capture and recovery-point search are gone from v1. What remains is one restore unit (a snapshot) and one upgrade command with two flock files and two marks.
- **(b) Replication tools.** Litestream's restore semantics re-read; it moves to §11 with a trigger and a precondition (a database boundary the file manifest names).
- **(c) Invariants and safety.** ADR-007: restores still create new directories, an abort never restores over a vault, and recovery now never overwrites authored content it cannot place. ADR-008: per-migration atomicity is stated as it is, with a defined abort. No step is destructive for an agent, and no step kills a process.
- **(d) Exposure and decisions.** Unchanged. D8 now names the shorter interval as the only v1 lever; D13 names the deployment-wide upgrade.
- **(e) Conflicts.** Mobile PR-8 and C1a's attach gain the deployment's lock and mark beside the vault's. The mobile host's existing exit status 78 (`RestartPreventExitStatus=78` in its unit) still keeps the supervisor from looping on a refused vault.

### Gate

| Check | Result |
|---|---|
| Internal consistency | D1–D19: 19 defined, 0 duplicates, 0 used but undefined. R1–R14: 14. G1–G14: 14 (G11 redefined, still one row). S0–S9: 10 phases, 0 undefined uses. H1–H3 defined once each. 40 reference tags in §12, every one used and every used tag defined. 211 `§` references: all resolve to a heading here except the same 7 that name another document. Stale text removed: every mention of coordinated file protection, a verified common recovery point and "a migration is atomic" as a sequence |
| Code citations re-checked in the worktree | 142 distinct cited ranges in 75 files, by the same script: 136 in this worktree, 6 on `mcp/c1-read-context` at `c06f73aae` (untouched by this pass); 0 out of range, 0 mismatches. The 12 ranges new or changed in this pass were read in full: `apply_protocol.py:228-253`, `:335-363`, `:347`, `:575-596` (was `:575`); `patches.py:92-93`, `:204-217`; `migrate.py:40-41`, `:84-88`, `:189`, `:209`; `deploy/learnloop-mobile.service:7-9`; `migrations/044_provenance_manifests_apply_intents.sql:159`; `.gitignore:197` re-cited |
| External facts | Litestream's restore reference re-read on 2026-10-14; §12's entry quotes it |
| `git diff --check` | Clean on the fix commit |
| Reproductions | F12 and F15 reproduced by one script on scratch files under the session scratchpad; F14 confirmed against the spec and the unit file |
| Tests | None run: no code changed |
| Paid calls | None |
| Safety | No `tailscale`, `git lfs`, history or remote mutation; no fixture or owner vault opened; no `~/.config/learnloop`, `.env`, `settings.env` or credential file read |

### Open for the owner (replaces the list above)

- **S0's checkpoint:** approve the sanitized `migration_head_202`'s remaining shape, or have it untracked with its tests in the owner lane until S3 (D6).
- **D2:** H1 (recommended, by blob id), H2 or H3, run by the owner from a fresh mirror clone.
- **S0's preconditions:** copies of the affected vaults and the textbooks outside every checkout; then land S0 by §7.1 step 6.
- **D17:** confirm Apache-2.0 (or AGPL-3.0) before a `LICENSE` lands.
- **D19:** keep the screenshots (recommended), with book pages attributed or replaced.
- **D7:** when re-pointing Funnel, confirm both chat connectors accept port 8443; otherwise use the swap.
- **D8:** if an hour of loss is too much, a shorter snapshot interval (down to 15 minutes); continuous database replication waits for its §11 trigger.
- **D18:** decided at S9's checkpoint.

---

## Owner decision: S0 deferred (2026-10-14)

**Decision:** "we can defer S0 for the keep-public decision later after we finish all these big changes." S0 keeps its content (what it removes from the public tip, the sanitization of `migration_head_202`, the owner-only history options) and becomes **deferred by the owner**: it starts only when the owner triggers it, after the current round of big implementation stages has landed. This supersedes "an early phase that cleans the public tip within days" in the first fix pass above. D1 stays decided (public).
**Commit:** the commit that adds this section (the spec, the stage record and this record). Documentation only.

**What changed in the spec, and why each dependency moved:**
- **Timing:** the status line, a fourth "owner decision in force", summary item 8, the S0 row ("deferred by the owner; on the owner's trigger", with "Triggers S0" in its owner column), the order paragraph, D1 and a new §9 risk ("The tip stays exposed while S0 waits").
- **Exposure:** §3.3 and §7.4 now say the exposure remains until the owner triggers S0, by the owner's choice. From S1 the live vaults are outside the checkout, so the tracked databases stop growing.
- **S3 no longer depends on S0.** It used to restore "the default-lane coverage S0 moved to the owner lane". S0 and S3 may now land in either order. If S3 lands first, its builders and dumps replace what the tests read while the private fixtures are still tracked, it runs `migration_head_202`'s sanitization before dumping it, and S0 later moves no test to the owner lane. The guard tests' final allowlist lands with S0, because the guards would fail on an uncleaned tip, and the fixture walkers and WAL guard stay until no tracked database remains. The S3 row, its gate (G13's sanitizer sweep when S3 runs it), §7.2's new "S0 and S3 in either order" paragraph, the head-fixture paragraph, §2.4, §3.5's transcript row, G6, G13 and D6 agree.
- **S1 never needed S0.** The order paragraph now says so. §7.1 step 5 adds that a retired directory still tracked by git leaves only through step 6 when the owner lands S0, and stays a frozen test fixture until then. §7.1 step 6 already covered both orders.
- **Unchanged:** S4 still follows S0, H1–H3 are still owner-only, and S1–S3 still land before mobile PR-1..PR-7.

**Gate:**

| Check | Result |
|---|---|
| Internal consistency | D1–D19: 19, R1–R14: 14, G1–G14: 14, S0–S9: 10, H1–H3 once each; 0 duplicates, 0 used but undefined; 40 reference tags, all used and defined; 224 `§` references, all resolving except the same 7 that name another document. No "within days", "S0 now" or "(days)" remains in the spec |
| Code citations | None touched; the same script still resolves 142 distinct ranges in 75 files with 0 out of range |
| `git diff --check` | Clean |

**Open for the owner:** the list in "Final verify fixes" stands. Its "S0's checkpoint" and "S0's preconditions" items apply when you trigger S0. If S3 lands first, approving the sanitized `migration_head_202` moves to S3's checkpoint.

---

## Third verify fixes (Codex job `20261014-202440-Kp2cto`)

**Reviewed:** `0abe2f23a..feb20097c`. **Verdict:** REOPENED: F12 (Medium) and F14 (High) reopened, F15 (Medium) reopened, F16 (Medium) new.
**Fix commit:** the commit that adds this section (the spec and this record). Each fix uses the simplest standard mechanism and adds no new machinery.
**Date:** 2026-10-14. Documentation only: no code, test, fixture, file move, git-LFS object, remote or history changed.

| Id | Severity | Title | Verdict | Reproduction, test or reason |
|---|---|---|---|---|
| F12 | Medium | Re-hashing each file can authenticate a snapshot that mixes two moments | Fixed | **Confirmed** against the spec at `feb20097c`. An external editor saves `concepts.yaml` (C1) and then a note referring to it (N1) after C0 was copied and before N was; each file re-hashed alone matched its copy, so the snapshot held C0 with N1, a state that never existed. **Fix:** optimistic consistency for the whole snapshot. Under the vault lock the snapshot records every authored file's path, size, modification time and SHA-256 before copying and again after the whole copy. The attempt counts only if both records and the staged copies agree for every file. Otherwise it is discarded and retried from step 2, three attempts in all, after which it is published marked incomplete and never counted as complete. This replaces the per-file re-hash. When the records agree, every file was unchanged over an interval containing the moment between the two passes, so the snapshot is the vault's text at that moment. The lock covers LearnLoop's own writes; the retry covers external edits. The originals race uses the same retry count. G11 gains the two-file interleaving and the three-attempt exhaustion |
| F14 | High | The deployment lock was released before the checkout changed | Fixed | **Confirmed**: in step 3 the upgrade took and released the exclusive lock, so a desktop launched before step 4 could load the old code, wait on the mark, and later attach with it after an upgrade with no schema change. **Fix:** the upgrade holds the deployment's lock exclusively from quiescence until the new code and environment are complete: stop units, take the lock (waiting, never killing), write the marks and wait out development builds, change the checkout, then release. Every entry point (units, the desktop app's launcher, the `learnloop` command) starts through util-linux `flock --shared --no-fork <lock> <program>`, which takes the lock before any application code is loaded and hands it to the program [flock-1]. A launch during the change therefore blocks before loading anything and starts on the new code. A process started without the launcher takes the lock without waiting and exits if it cannot. The marks still keep new attaches out until every vault has migrated. G10 gains the launch interleaving, including an upgrade with no schema change. §6.2, §6.9 (PR-8), §6.10 (C1a's unit), §6.11 S5 and §12 agree |
| F15 | Medium | Abort validated the restored snapshot with the failed upgrade's code | Fixed | **Confirmed** against the code: doctor's `_check_sqlite` reports every migration the code knows but the database lacks as `sqlite:migrations_missing` (`src/learnloop/ops/doctor.py:966-974`), so the failed tag's doctor fails a restored schema-202 snapshot, and its replay may expect tables the snapshot lacks. **Fix:** the abort runs in this order, with every mark in place: (1) stop the units and take the deployment's lock; (2) return the checkout and environment to the previous tag; (3) with that code, restore and validate each changed vault's pre-upgrade snapshot (a failed validation stops the abort with the barrier up); (4) switch pins; (5) lift the barrier and start the units. The by-hand path before S5 uses the same order. G10 states the order |
| F16 | Medium | With S3 first, the WAL guard fails on a tip with no tracked database | Fixed | **Confirmed**: `tests/test_tracked_fixture_databases.py:24-25` asserts at least one `fixtures/**/*.sqlite`. Once S3 has turned the historical databases into dumps, a fresh clone without S0's paths (G6) has none. The other walkers parametrize over what exists (`tests/test_migrations.py:88-90`; `tests/test_receipt_exactness.py:41-44`; `tests/test_receipt_derivation.py:34-37`), and the session guard compares dictionaries, so only this assertion fails. **Fix:** from S3 the WAL guard accepts an empty set while still checking every remaining database for un-checkpointed companions and tracked companion files (`:26-32`, `:35-41`). G8's guards, which assume a cleaned tip, stay deferred to S0. §7.2's either-order paragraph and the S3 row say so |

**Rejected:** none.

### Gate

| Check | Result |
|---|---|
| Internal consistency | D1–D19: 19, R1–R14: 14, G1–G14: 14, S0–S9: 10, H1–H3 once each; 0 duplicates, 0 used but undefined. 41 reference tags (`flock-1` added, used in §6.2), all used and defined. 225 `§` references, all resolving except the same 7 that name another document. No stale per-file re-hash, single retry or take-and-release lock wording remains |
| Code citations re-checked in the worktree | 145 distinct ranges in 75 files: 139 in this worktree, 6 on `mcp/c1-read-context` at `c06f73aae` (untouched); 0 out of range, 0 mismatches. New ranges read in full: `src/learnloop/ops/doctor.py:966-974`, `tests/test_tracked_fixture_databases.py:24-25`, `:26-32` (`:35-41` was already cited) |
| External facts | `flock(1)` re-read on man7.org: the command form, waiting by default, `--shared`, and `--no-fork` ("the flock process is replaced by command which continues to hold the lock") |
| `git diff --check` | Clean on the fix commit |
| Tests | None run: no code changed |
| Safety | No `tailscale`, `git lfs`, history or remote mutation; no fixture or owner vault opened; no `~/.config/learnloop`, `.env`, `settings.env` or credential file read |
