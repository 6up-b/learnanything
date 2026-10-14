# Where LearnLoop's data lives, and one learner state on every surface (v1)

**Status:** draft for owner review (2026-10-14). Branch `docs/storage-sync-spec`, base `main` at `bffe086ec` (migration head 202, latest algorithm `mvp-0.23`). This is a specification only: no code, file, git-LFS object, remote or history was changed to write it. The stage record is `docs/reviews/storage-sync-spec.md`.

**Owner request (2026-10-14):** "For the git-LFS textbook storage, we should probably reevaluate how that is set up so we can retain the feature to sync between devices using the same learnloop (mcp interface updates learnloop, dailies can be done on the mcp frontend or on a laptop or phone on the tailnet and all update/sync the same information). Not only is git LFS a pain with textbooks but SQLite on git is also a pain since its hard for other people to pull or make PRs. This is definitely something to think through and spec out ... and should be before starting mobile implementation."

**Precedes:** the mobile spec's M2 prerequisites PR-1..PR-7 (`docs/specs/spec_mobile_tailnet_v1.md` §3.3) and the chat frontend's C1b and C2 (`docs/specs/spec_mcp_frontend_c1.md` on `mcp/c1-read-context`, §8–§9). Those build on the architecture chosen here (§6.9, §6.10).

**Owner decisions in force (2026-10-12):**
- The recommended defaults recorded in each spec are accepted. The owner may override any of them at its checkpoint (§10 lists this spec's).
- Frictionless defaults: honest labels and generous defaults; live changes behind kill switches; no shadow stages by default.
- Owner decisions in other specs that this one leans on: mobile D1 (iOS), D9 (no offline practice), D11 (desktop asleep: accept in M1), D12 (no LearnLoop tailnet policy), D15 (the mobile host pins one vault); chat frontend D1 (Funnel approved for the MCP endpoint) and D8 (a separate `learnloop mcp serve` process in secondary attach).

**Citation convention.** Every `file:line` was re-checked in this worktree at `bffe086ec`. Paths are relative to the repository root. Code that exists only on an unmerged branch is marked with the branch name and was checked there with `git show` at the branch tip of 2026-10-14 (`mcp/c1-read-context` at `f6c6c73b8`). Measurements of the owner's working vaults were taken on backup-API copies (`learnloop.db.copies.backup_database`) made on 2026-10-14 under the worktree's gitignored `fixtures-local/`; the committed copies of every tracked fixture database were measured the same way. External facts carry a reference tag (§12) and were checked on 2026-10-14.

---

## Summary (the recommendation in eight lines)

1. **One home for the learner: a hub.** One always-on machine (default: `carson`, the desktop) holds each vault on its local disk: `state.sqlite`, the authored YAML and Markdown, and the content-addressed originals store. Every surface is a client of that one copy: the desktop app at the hub, the phone (PWA and Shortcut over Serve), the laptop (browser first, a remote mode of the desktop app later), and chat (MCP over Funnel). SQLite is never shared across machines and never file-synced (§6).
2. **A headless primary on the hub.** A `learnloop hub serve` user service holds the vault's *primary role* (an OS lock) and runs the background duties the desktop app runs today (ingest runner, post-attempt diagnosis, maintenance), so dailies done on the phone, the laptop or in chat are graded, diagnosed and planned while the desktop app is closed. Without the service (a contributor's machine), the desktop app is primary exactly as today (§6.2).
3. **Data leaves the code repository.** The owner's working vaults move to a private data root on the hub (default `~/learnloop-vaults/<name>/`), copied with the backup API and verified before anything is removed. Textbooks move to a private books folder; after import LearnLoop only ever reads its own store copy (§6.3, §7.1).
4. **Sources never depend on a path again.** The originals store is the authority for every revision's bytes; `canonical_uri` and `original_uri` become provenance only. This completes the E1 fix that `fix/reread-safety` starts, and adds content-hash identity for local files so a moved book is the same book (§6.4).
5. **The code repository becomes clone-and-test clean.** No tracked database, no third-party PDF or text, no git-LFS. Test vaults are generated from text by builders; the migration-head fixture becomes a SQL text dump built at session start; real-vault checks become an opt-in lane run on backup copies (§7.2, §7.3).
6. **Backups are part of the move, not an afterthought.** Hourly backup-API snapshots plus a nightly encrypted off-site copy (restic), a monthly restore drill, and honest labels: up to one hour of work can be lost if the hub's disk dies. Continuous replication (Litestream) is a later option (§6.7).
7. **Offline is stated, not implied.** Away from home the laptop and phone reach the hub over the tailnet whenever both have internet. With no hub reachable: capture queues (phone and laptop browser outboxes), practice waits (mobile D9 holds). A read-only laptop snapshot and offline practice with deferred grading are deferred with triggers (§6.6, §11).
8. **The public exposure needs the owner first.** The repository is public, has a public fork, and serves the owner's databases, extracted book text and copyrighted PDFs to anonymous requests today (§3.3). Making it private now is reversible and stops new downloads; purging history is destructive and is the owner's decision alone (§7.4, D1, D2).

---

## 0. Thesis

LearnLoop is local-first by design: one learner, one vault, SQLite with append-only evidence, YAML for authored knowledge, and a replay that rebuilds every derived table. That design is sound on one machine. It was stretched to several machines through git: the owner's working vaults and their `state.sqlite` files live under `fixtures/` in the code repository, and textbooks live in git-LFS beside them. Git is a good way to share code and a poor way to share a live database. It merges text, not B-trees; it cannot carry a `-wal` safely; it makes every contributor download the owner's history; and on a public repository it publishes that history.

The tailnet already gives what git was standing in for. Every device the owner uses can reach one machine over WireGuard, from home or away, and the mobile and chat frontends already run as second processes beside the desktop app against one vault (`docs/specs/spec_mobile_tailnet_v1.md` §3.3; `docs/specs/spec_mcp_frontend_c1.md` §3.3 on `mcp/c1-read-context`). The design that keeps every invariant is to stop copying the learner around: keep the learner in one place and let every surface talk to it. Replication, CRDTs and event-log merging buy offline writes on several machines at once, which a single learner on a home tailnet rarely needs, at a price the schema measured below makes very high (§5.2).

---

## 1. Scope

**In scope:**
- An inventory of every class of LearnLoop data and where it lives today (§2).
- The problems with evidence: LFS friction and E1, binary SQLite in git, the public exposure, working vaults used as test fixtures, and multi-device use (§3).
- Requirements (§4), options with costs and risks (§5) and a recommended architecture with phases (§6).
- The migration from today: vaults, textbooks, test fixtures, git-LFS, and the public-history question as an owner decision (§7).
- Gates, risks, owner decisions and deferrals (§8–§11).

**Out of scope:**
- Building any of it. Each phase in §6.11 is its own stage.
- Multi-user or hosted deployment (chat frontend research appendix §4.2, "Hosted pilot"; chat frontend D3).
- Merging the owner's three topic vaults into one library. Each vault stays a separate learner state; the hub serves several.
- The laptop's remote desktop mode in detail. §6.6 sizes it and names its prerequisites; it gets its own spec when its trigger fires (§11).
- Running any `tailscale` or `git lfs` command, changing repository visibility, or rewriting history. These are owner actions (§7.4).

---

## 2. Inventory: what LearnLoop stores, and where, today

### 2.1 Data classes

| Class | What | Where today | Authority and rebuild | Citations |
|---|---|---|---|---|
| **Configuration** | Vault policy, algorithm version, AI routing | `<vault>/learnloop.toml` | Authored; text | `src/learnloop/vault/paths.py:15-17` |
| **Authored knowledge** | Subjects, concepts, relations, learning objects, practice items, activity families, notes, goals, learner profile, error types, facets, source sets | YAML and Markdown under `<vault>/concepts/`, `profile/`, `errors/`, `subjects/<id>/…`, `sources/` | Authority for authored content. Written under the vault mutation lock (an `fcntl.flock` on `<vault>/.learnloop/vault.lock`); multi-file accepts use a write-ahead intent recorded in SQLite first | `src/learnloop/vault/paths.py:23-91`; `src/learnloop/vault_lock.py:9-13`, `:94-95`; `src/learnloop/content/proposals/apply_protocol.py:1-21` |
| **Learner evidence and authored rows in SQLite** | Attempts, observations, measurement events, grades, diagnoses, captured provider and source output, DB-authored definitions (activity cards, families, patterns) | `<vault>/state.sqlite` (path relocatable through `storage.sqlite_path`) | RAW_LEDGER: never cleared by rebuild; corrections append (ADR-007). 143 of 321 tables at head 202 | `src/learnloop/vault/paths.py:19-21`; `src/learnloop/db/table_roles.py:28-36`, `:469` |
| **Receipts** | Decision and audit history (scheduler explanations, submission receipts, model-call receipts) | `state.sqlite` | RECEIPT: append-only, never rebuilt. 67 tables | same |
| **Workflow state** | Queues, sessions, leases, plans, ingest jobs, slate candidates, mobile devices | `state.sqlite` | WORKFLOW: mutable, preserved across replay. 82 tables | same |
| **Derived projections** | Learning state, canonical projection, identifiability, FTS index and the rest | `state.sqlite` | DERIVED: cleared and replayed by exactly one owner each (ADR-003). 19 tables | `src/learnloop/substrate/rebuild_orchestrator.py:190`, `:567`, `:641` |
| **Source originals** | The bytes of every source revision (PDFs, HTML, transcripts), capture media | `<vault>/canonical-sources/raw/sha256-<hex>`, content-addressed, fsynced, trusted by name | Authority for bytes; not rebuildable | `src/learnloop/ingest/originals.py:23-53`; `src/learnloop/vault/paths.py:93-95` |
| **Source provenance** | Where a source came from: `canonical_uri` (artifact identity) and `original_uri` (per revision) | `source_artifacts`, `source_revisions` (RAW_LEDGER) | For local files both are absolute paths on the machine that imported them | `src/learnloop/content/sources/source_library.py:73-87`, `:109-119`; `src/learnloop/content/pipeline/add_source.py:235-247`; `src/learnloop/ingest/fetchers.py:304` |
| **Extractions** | Document IR, blocks, crosswalks, unit inventories | `state.sqlite` (RAW_LEDGER, e.g. `source_document_blocks`) plus a cache under `<vault>/.learnloop/source-cache/` | IR is authoritative captured output; the cache is disposable | `src/learnloop/vault/paths.py:97-99`; `src/learnloop/content/pipeline/source_ingestion.py:1169` |
| **Rendered media** | Explainer animations | `<vault>/media/animations/sha256-<hex>.mp4` | Content-addressed; regenerable at a cost | `src/learnloop/vault/paths.py:101-110` |
| **Project understanding** | A second SQLite store and a commit log fed by git hooks in the learner's own code repositories | `<vault>/projects/project_store.sqlite`, `<vault>/projects/pending.jsonl`; the hook appends to the **absolute local path** of `pending.jsonl` | Its own store (M1 touches no `state.sqlite` table) | `src/learnloop/projects/experiment_store.py:1-5`, `:37-38`; `src/learnloop/projects/hooks.py:56-75` |
| **Machine-local state inside the vault** | The vault lock, job locks, diagnose scratch runs, the source cache, the MCP endpoint token | `<vault>/.learnloop/` (gitignored) | Disposable, except the endpoint token, which is a secret | `.gitignore:197`; `src/learnloop/vault_lock.py:94-95`; `src/learnloop/cli/diagnose.py:265`; `src/learnloop/remote/endpoint_token.py:23-24` (on `mcp/c1-read-context`) |
| **Machine-global configuration and secrets** | Provider keys (`settings.env`), default AI selection, ChatGPT-plan sign-in, the desktop's last vault, the mobile host's `mobile.toml` and `mobile.env` | `$LEARNLOOP_CONFIG_DIR`, else `$XDG_CONFIG_HOME/learnloop`, else `~/.config/learnloop/` | Per machine; never in a vault or the repository | `src/learnloop/config/loader.py:32-47`; `src/learnloop/ai/chatgpt_plan/store.py:1-25`; `apps/learnloop-tauri/src-tauri/src/sidecar.rs:666-667`; `src/learnloop_mobile/config.py:11-19`, `:37-38` |
| **A vault-local `.env`** | Keys that override the machine-global file for one vault | `<vault>/.env` (gitignored by `.env` and `*.env`) | A secret inside the vault directory | `src/learnloop/config/loader.py:58-63`; `.gitignore:158`, `:263` |
| **Textbook library** | 22 PDFs and a text file the owner collected | `new_textbooks/` in the code repository, the PDFs through git-LFS (although `new_textbooks/` is also in `.gitignore`) | The owner's personal files; LearnLoop needs them only until import | `.gitattributes:2-3`; `.gitignore:259` |
| **Test fixtures** | 13 directories under `fixtures/`, 10 of them with a tracked `state.sqlite` and most with a tracked originals store | `fixtures/` | Mixed: three are the owner's live working vaults (§2.4) | `tests/test_tracked_fixture_databases.py:23-31` |

### 2.2 Measured: the owner's working vaults (backup-API copies, 2026-10-14)

| | `linear_algebra` | `probability` | `arxiv_v2` |
|---|---:|---:|---:|
| `state.sqlite` | 45.7 MB | 23.1 MB | 11.3 MB |
| Migration applied | 165 | 165 | 165 |
| RAW_LEDGER rows (tables non-empty) | 6,077 (61) | 2,460 (58) | 7,282 (53) |
| WORKFLOW bytes | 31.0 MB | 15.6 MB | 3.0 MB |
| Largest table | `scheduler_slate_candidates` (WORKFLOW), 27.3 MB | `scheduler_slate_candidates`, 12.1 MB | `source_document_blocks` (RAW_LEDGER), 2.3 MB |
| Practice attempts | 70 | 2 | 3 |
| Extracted source blocks (`source_document_blocks`) | 1,074 | 579 | 4,717 |
| Originals store | 5.6 MB | 7.5 MB | 216.0 MB |
| Authored YAML, Markdown and TOML | 137 files, 0.62 MB | 109 files, 0.78 MB | 77 files, 0.50 MB |
| Source artifacts by `canonical_uri` | 1 PDF in `learnanything/new_textbooks/`, 2 YouTube URLs | 3 PDFs in `new_textbooks/`, 1 web URL | 1 PDF in `new_textbooks/`, 1 arXiv URL, 10 YouTube URLs |
| Revisions with a store copy of their bytes | 3 of 3 | 4 of 4 | 12 of 12 |

Three facts follow. The three vaults together, originals included, come to about 310 MB; that fits on any machine and any backup service. The two largest databases are mostly workflow telemetry (scheduler slates), not evidence. And every revision's bytes are already in its vault's own store, so moving a vault out of the repository loses no source, whatever `canonical_uri` says.

### 2.3 The schema, measured on a fresh database at head 202

| Property | Count | Why it matters (§5) |
|---|---:|---|
| Tables | 321 (143 RAW_LEDGER, 82 WORKFLOW, 67 RECEIPT, 19 DERIVED, 10 COMPAT) | Only 19 can be rebuilt from the others |
| Tables with a UNIQUE constraint or index besides the primary key | 151 | CRDT extensions refuse them |
| Tables with foreign keys | 162 | Replicated merges cannot check them |
| Triggers (most enforce immutability) | 120 (73 on RAW_LEDGER, 45 on RECEIPT, 2 on WORKFLOW tables) | Changeset application must not trip them |
| Virtual tables | 1 (`source_block_fts`, FTS5) | SQLite's session extension does not capture virtual tables [SessionExt] |
| `INTEGER` rowid primary keys | 6 | Would collide between replicas |

Row ids elsewhere are ULIDs from the wall clock, and history is ordered by `(created_at, id)` with `created_at` at one-second resolution (`src/learnloop/ids.py:22-25`, `:35-55`; `src/learnloop/clock.py:29-31`).

### 2.4 Test fixtures

All ten tracked databases contain practice attempts: 174 in total in the committed copies. `mvp017_route_check_replay` was generated with test fakes at `e238fa07a` and only that commit can regenerate it (its README); the other nine hold the owner's own attempts, dated 2026-05-28 to 2026-08-04.

| Fixture | Tracked DB | What it is | Used by |
|---|---|---|---|
| `linear_algebra`, `probability`, `arxiv_v2` | yes | **The owner's working vaults** (CLAUDE.md). Also hold book text in `source_document_blocks` and, for the first two, copyrighted PDFs in plain git (§3.3) | 13 test files load `linear_algebra` directly; 4 of them also load the other two (`tests/test_placement_fixture_copies.py:28` names all three); plus the fixture walkers |
| `linear_algebra_legacy` | yes | A frozen older copy, pinned *because* the live vault moved under the tests (`tests/test_goal_decay_projection.py:21-24`) | 1 test file, plus fixture walkers |
| `migration_head_202` | yes | The conic-sections vault (six early owner attempts) upgraded to head 202 | 21 test files and the two DB-reference scripts |
| `mvp017_route_check_replay` | yes | A synthetic vault graded under mvp-0.17; it proves old history still replays | 2 test files |
| `conic-sections`, `arxiv` | yes | Early owner vaults | `tests/test_doctor.py:171`; `tests/test_migrate_fresh.py:144`, `tests/test_sidecar_contract.py:1937` |
| `law`, `physical_therapy` | yes | Early owner vaults holding third-party exam questions | Only the fixture walkers |
| `grading_hardcases`, `proto_sources`, `synthesis_eval_gold` | no | Text fixtures | `src/learnloop/diagnosis/grading_hardcases.py:128`; `tests/test_normalizer_units.py:15`; `src/learnloop/content/synthesis/synthesis_eval.py:302` |

The fixture walkers are `tests/test_migrations.py:88-90`, `tests/test_receipt_exactness.py:41-44`, `tests/test_receipt_derivation.py:34-37`, `tests/test_tracked_fixture_databases.py:23-31` and the session guard in `tests/conftest.py:100-151`; two more walk only text (`tests/test_yaml_fast_read.py:28`, `tests/test_config_refactor.py:351`). The ordinary test vault is already synthetic: `create_basic_vault` builds a template once per session and copies it (`tests/helpers.py:66-72`), and a helper already writes small synthetic PDFs (`tests/ux_phase1_support.py:60`).

### 2.5 Code that assumes a git working tree or a file at `canonical_uri`

**Git working tree.** No vault code reads git. The assumptions are around it:
- The desktop shell launches the sidecar from the source checkout (`repo_root()`, `current_dir(repo_root)`) and looks for personal vaults under `<repo>/fixtures-local/` before the default library `~/LearnLoop` (`apps/learnloop-tauri/src-tauri/src/sidecar.rs:372`, `:640-645`, `:694-704`, `:735-745`).
- Tests find fixtures relative to the repository and ask git which fixture files are tracked (`tests/test_tracked_fixture_databases.py:35-41`).
- Text fixtures used by product code resolve against the repository (`src/learnloop/diagnosis/grading_hardcases.py:128`; `src/learnloop/content/synthesis/synthesis_eval.py:302`).
- The chat frontend's user unit runs from the main checkout's `.venv` (`docs/reviews/mcp-c1a.md:105` on `mcp/c1-read-context`).
- Unrelated to vault storage: project understanding runs git in the learner's own repositories (`src/learnloop/projects/git.py:67`), and the Codex provider checks a checkout's `.git` (`src/learnloop/ai/providers/codex.py:1113-1120`).

**A file at `canonical_uri` or `original_uri`.**
- **Registration** stores the import path as artifact identity: `canonical_uri = resolved.source`, `original_uri = file://…` (`src/learnloop/content/pipeline/add_source.py:242-249`), and an artifact is found again only by that string (`src/learnloop/content/sources/source_library.py:73-76`; `src/learnloop/content/pipeline/source_ingestion.py:1699-1711`). A book moved to another folder or machine becomes a second artifact.
- **The card's re-read** ("Read it again with text recognition") re-imports from `canonical_uri` (`src/learnloop_sidecar/handlers/first_run.py:336-345`). This is E1 (§3.1).
- **Extraction repair** re-acquires from `original_uri`, else `canonical_uri` (`src/learnloop/content/pipeline/jobs.py:2460-2465`).
- **Already store-first, correctly:** resuming an extraction reads the store and checks the hash (`src/learnloop/content/pipeline/source_ingestion.py:215-221`); the Reader, the PDF manifest and retrieval resolve the store first and fall back to a local file (`src/learnloop/ingest/originals.py:71-77`; `src/learnloop/reader/span_view.py:181-194`; `src/learnloop_sidecar/handlers/reader.py:549-553`; `src/learnloop/source_retrieval/b4.py:154`); `backfill_original` refuses bytes whose hash differs (`src/learnloop/ingest/originals.py:90-110`).
- **The desktop's protocols** read the originals and animation stores straight from the local vault path (`apps/learnloop-tauri/src-tauri/src/main.rs:19-52`), so a remote client needs an HTTP equivalent (§6.6).
- **Project capture hooks** write to an absolute local path (`src/learnloop/projects/hooks.py:56-75`), so repositories on a machine other than the vault's are not captured.

---

## 3. Problems, with evidence

### 3.1 git-LFS friction, and E1

- **Pointer files.** git-LFS leaves a ~130-byte text pointer in place of the file whenever the smudge filter does not run (git-lfs not installed, `GIT_LFS_SKIP_SMUDGE`, a quota-blocked download) [LFS-smudge] [GH-LFS-billing]. In the main checkout today all 22 `new_textbooks/*.pdf` are 130–134-byte pointers, while the local LFS store holds the 443 MB of real bytes.
- **E1 (found by the GLM-OCR live check, 2026-10-14; fix in flight on `fix/reread-safety`).** Every PDF source's `canonical_uri` points into `new_textbooks/` (§2.2). The card's re-read imports from that path (`src/learnloop_sidecar/handlers/first_run.py:336-345`), so it registered a new revision *from the pointer*, moved `current_revision_id` to it, failed extraction, and left the book unopenable from the Library, while doctor flagged nothing. `fix/reread-safety` makes the re-read read the store and refuse mismatched bytes. Two causes remain for this spec: repair still re-acquires from the path (`src/learnloop/content/pipeline/jobs.py:2460-2465`), and identity still is the path (§2.5).
- **Contributors pay for LFS.** Cloning needs git-lfs; every download by any clone or fork counts against the *owner's* LFS bandwidth (10 GiB on the Free and Pro plans); and once a quota is exhausted without a payment method, clones get pointer files only [GH-LFS-billing].
- **LFS objects cannot be removed by a commit.** Deleting a file leaves its LFS object on GitHub's storage; GitHub's only removal path is to delete and recreate the repository, or ask Support [GH-LFS-remove].

### 3.2 Binary SQLite in git

- **No merge.** Git cannot merge two versions of a database; one side wins. `linear_algebra/state.sqlite` alone was committed 31 times on `main`'s history, and the history now holds 81 distinct database blobs across 19 paths, 1,051 MB uncompressed.
- **A database in git is not a backup of a live database.** A committed `state.sqlite` misses whatever is still in its `-wal`; the repository guards against that with a session check and a fixture test (`tests/conftest.py:100-151`; `tests/test_tracked_fixture_databases.py:23-31`), which is effort spent keeping git from corrupting what git should not hold.
- **Every pull is the owner's whole history.** A contributor who clones gets the learner's database at every committed moment, and any test that touches a working vault can change it in place, which is why the session guard exists.
- **Tests move under the owner.** `tests/test_goal_decay_projection.py:21-24` records that pointing a golden at `fixtures/linear_algebra` "made the suite fail the moment anyone practised or created a goal in the working vault".

### 3.3 Exposure: the repository is public

Checked on 2026-10-14 with read-only GitHub API calls and anonymous `HEAD` requests (headers only; no file body was downloaded):

| Fact | Evidence |
|---|---|
| `6up-b/learnanything` is **public** | GitHub API: `visibility: public` |
| `main` on GitHub is `bffe086ec`, the base of this branch | GitHub API branch list |
| **A public fork exists** (created 2026-07-21, last pushed 2026-09-24) | GitHub API fork list. Whatever it copied is outside the owner's control [GH-sensitive] |
| **Textbooks in LFS are anonymously downloadable** | `media.githubusercontent.com/…/new_textbooks/stephen_abbott-understanding_analysis_solutions.pdf` → `200`, `content-length: 516812` (the file's full size) |
| **The 215 MB LFS object in a vault store is downloadable** | `…/fixtures/arxiv_v2/canonical-sources/raw/sha256-84b6…` → `200`, `content-length: 215442636` (the same bytes as `new_textbooks/welch_labs_ai-guide.pdf`) |
| **Textbooks are also in plain git, outside LFS** | `fixtures/linear_algebra/canonical-sources/raw/sha256-b40b…` (Axler, *Linear Algebra Done Right*; the same blob is also tracked as `fixtures/linear_algebra/canonical-sources/sheldon_axler-linear_algebra_done_right.pdf`) → `raw.githubusercontent.com` `200`, `content-length: 2795246`. `fixtures/probability/canonical-sources/raw/` holds Blitzstein and Hwang's *Introduction to Probability* (7.2 MB) and an MIT problem set and recitation, all matched to `new_textbooks/` by SHA-256 |
| **The owner's learning history is downloadable** | `raw.githubusercontent.com/…/fixtures/linear_algebra/state.sqlite` → `200`, `content-length: 45334528`. All ten tracked databases hold practice attempts (§2.4) |
| **Book text is inside the databases too** | `source_document_blocks`: 1,074, 579 and 4,717 extracted blocks in the three working vaults (§2.2). Removing the PDFs alone would not stop redistributing their text |
| **Third-party exam material** | `fixtures/law` (MBE sample questions) and `fixtures/physical_therapy` (a PEAT practice exam) carry their source text in tracked originals stores |

This spec does not decide the copyright status of any book; licences differ from book to book. It treats all of them as material the code repository must not redistribute (D16).

### 3.4 Multi-device use today

- **The tailnet path exists but stops at one machine.** The mobile host and the chat server attach to a vault on the desktop's disk (`src/learnloop_mobile/config.py:11-26`; `docs/specs/spec_mcp_frontend_c1.md` §3.3 on `mcp/c1-read-context`).
- **Only the desktop app does the primary work.** `SidecarContext.load` binds the ingest runner, syncs vault state, binds the post-attempt worker, refreshes the canonical projection, schedules cold probes, runs startup maintenance and resumes post-attempt jobs (`src/learnloop_sidecar/context.py:58-118`). The post-attempt worker is the sidecar's own (diagnose, embed and learner-text-gap slots over a durable, lease-fenced queue; `src/learnloop_sidecar/post_attempt_worker.py:1-14`). The mobile spec's secondary attach runs none of this (`docs/specs/spec_mobile_tailnet_v1.md` §3.1). As specified, then, a phone answer graded while the desktop app is closed waits for the desktop to open before its asynchronous diagnosis (ADR-016) runs.
- **Ports collide.** The mobile host's doctor requires a background Serve route on port 443 and Funnel off on port 443 (`src/learnloop_mobile/doctor.py:86-117`). The chat frontend's runbook points Funnel's port 443 at the MCP server (`docs/reviews/mcp-c1a.md:86-98`, open question Q3, on `mcp/c1-read-context`). Funnel visibility is per port [TS-Funnel], so both cannot hold on one machine.
- **A laptop has no way in** except the phone's PWA once M2a exists. The desktop app opens a local vault through a local sidecar only.
- **Copying the vault to the laptop is unsafe.** WAL needs every process on one host [SQLite-WAL], and the architecture rule already forbids syncing a live vault folder (`docs/learnloop-architecture-vault/Architecture/State and Persistence.md:85-90`).

---

## 4. Requirements

| # | Requirement |
|---|---|
| R1 | **One learner state per vault.** The desktop app, the laptop, the phone and chat read and write the same `state.sqlite`, YAML and originals. No surface keeps a second authoritative copy |
| R2 | **Dailies anywhere update the same model.** An answer given on any surface is graded, diagnosed (asynchronously) and scheduled by the same code against the same vault, whether or not the desktop app is open |
| R3 | **Offline behaviour is explicit** for each surface and each failure (hub asleep, no internet, a laptop away from home), with honest labels (§6.6) |
| R4 | **Invariants hold:** ADR-003 (explicit table roles; only DERIVED is rebuilt), ADR-007 (immutable evidence, append-only correction), ADR-008 (locked atomic migrations; read-only inspection), ADR-015 (WAL with `synchronous=FULL`; backup-API copies only; a vault on local disk), table-role classification and the migration procedure in CLAUDE.md, replay and shadow rebuild unchanged |
| R5 | **No algorithm successor** unless a phase changes persisted meaning; if one does, it follows `docs/algorithm-change-playbook.md` |
| R6 | **The code repository is clone-and-test clean:** no private data, no git-LFS, no tracked binary databases, no third-party copyrighted files. `uv sync --extra dev --extra mobile` and `uv run pytest` pass on a fresh clone with no network beyond package installs |
| R7 | **Backups and restore:** a consistent snapshot of every vault, an off-site encrypted copy, a tested restore, and stated loss bounds |
| R8 | **Sources never depend on a path** in a git checkout or anywhere else once imported (E1) |
| R9 | **Secrets stay machine-local:** provider keys, tokens and the endpoint token are never in the code repository or an unencrypted off-site copy |
| R10 | **Frictionless:** the owner at the desk sees no change; a new learner's first launch still creates `~/LearnLoop` and works alone with no hub |
| R11 | **Private surfaces stay private.** Only the MCP endpoint is public (Funnel); the phone, laptop and originals endpoints are tailnet-only (Serve) |
| R12 | **Mobile and chat build on this,** not around it: PR-1..PR-7, C1b and C2 keep their designs; this spec adds one prerequisite (PR-8) and a port change (§6.9, §6.10) |

---

## 5. Options

### 5.1 (a) A single-writer hub

**Shape.** One machine holds the vault on local disk. Every process that touches the database runs on that machine: the desktop app when the owner sits at it, the mobile host, the chat server and a headless primary. Other devices are clients over the tailnet: HTTPS to the hub, never file access.

**Why it fits.** It is the arrangement the mobile host (M1, built) and the chat server (C1a, built on its branch) already use; the multi-process story is SQLite's own (WAL, `busy_timeout`, one host) plus the locks that exist (`src/learnloop/db/connection.py:12`, `:105`; `src/learnloop/vault_lock.py:9-13`). Replay, table roles and migrations are untouched, because nothing merges.

**Variants for offline:**
- **a0, online-only.** Clients need the hub. Capture queues in outboxes (the phone already has them).
- **a1, read-only snapshot on the laptop.** The hub pushes a consistent copy (`sqlite3_rsync` or the backup API, plus the vault files) when the laptop is reachable; offline the laptop can read the library and its history but not practise. Needs a read-only desktop mode: the sidecar today requires a writable vault (ADR-015 check 2).
- **a2, offline practice with deferred grading.** The laptop or phone records answers offline with the presented item's contract; the hub grades them on reconnect. This changes evidence semantics (served-offline coldness, reservations, backdated scheduling) and needs a playbook successor.

**Costs.** A headless primary and the primary-role lock (§6.2); PR-1..PR-7, which mobile M2 and chat C2 need anyway; a remote mode for the desktop app if the full UI is wanted on the laptop (§6.6). **Risks.** The hub is a single point of failure (backups, §6.7); the hub must be awake (D4); public ingress to the hub for chat (C1 risk R1).

### 5.2 (b) Event-log replication over LearnLoop's own ledgers

**Shape.** Each device keeps a full vault, appends its own rows, and ships them to the others; derived tables are rebuilt after each merge.

**What it would take, measured against the schema (§2.3):**
- **Device-scoped, globally ordered ids.** ULIDs are unique enough, but history is ordered by `(created_at, id)` from each machine's wall clock (`src/learnloop/ids.py:22-25`); merged histories need hybrid logical clocks, and replay order would change, so every merge is a potential persisted-meaning change (R5).
- **A merge rule for every non-derived table.** Only 19 of 321 tables are rebuildable. The other 302 include 82 mutable WORKFLOW tables (sessions, leases, plans, reservations) whose rows two devices would both edit, and RAW_LEDGER tables that hold mutable authoritative state (`activity_card_state`, `src/learnloop/db/table_roles.py:45-48`).
- **Decisions made against stale state.** Serving, reservation and exposure are decisions about the learner's current state: two offline devices can both serve the same cold check or held-out exam item, both spend a session's probe cap, or both reveal a solution before an independent check. A merge can only detect these after the fact; the evidence is then not what the coldness and certification rules assume.
- **Authored content.** Concurrent YAML edits would become proposals with a base content hash, applied through the existing write-ahead protocol (`src/learnloop/content/proposals/apply_protocol.py:1-21`), with conflicts sent to review.
- **Mechanism.** SQLite's session extension records changesets, but needs declared primary keys and skips virtual tables [SessionExt]; Python's standard `sqlite3` module does not expose it [Py-sqlite3], so it would mean adopting APSW [APSW-session] as a second driver.

**Verdict.** Months of work and a permanent tax on every new table, to support simultaneous offline writing by one person. Deferred with a trigger (§11).

### 5.3 (c) SQLite replication tools

Facts from each project's own documentation and repository on 2026-10-14.

| Tool | What it does | Fit with WAL + FULL, multi-process on one host | Licence, self-hosting, maturity | Verdict |
|---|---|---|---|---|
| **Litestream** [Litestream-how] [Litestream-tips] | Streams one database's WAL to S3, SFTP, a file path and others as LTX files; point-in-time restore; an optional read-only VFS over the replica | WAL required (fits). It holds a long read transaction so other processes cannot checkpoint, and runs its own checkpoints; LearnLoop's explicit TRUNCATE checkpoints (`src/learnloop/db/checkpoint.py:29`, `:41-57`) would then mostly report busy, which they already tolerate. Wants a busy timeout of about 5 s (LearnLoop's is 5,000 ms). One replicating process per replica path | Apache-2.0; self-hosted binary; v0.5.17 (2026-08-31), active | **Good for continuous backup of the hub.** Not a sync mechanism. Optional upgrade (D8) |
| **LiteFS** [LiteFS] | "A FUSE-based file system for replicating SQLite databases across a cluster of machines", with one primary | FUSE: LearnLoop's doctor already warns on FUSE mounts for WAL reasons (ADR-015 check 3) | Apache-2.0; "pre-1.0"; Fly.io "not able to provide support"; v0.5.14 (2025-04-22) | No |
| **libSQL / Turso embedded replicas** [Turso-replicas] | Local read replica; writes go to a remote primary; optional offline writes | Replaces the SQLite library and driver; "Do not open the local database while the embedded replica is syncing", which conflicts with several processes on one file | MIT (libSQL); the documented primary is Turso Cloud | No |
| **cr-sqlite** [cr-sqlite] [cr-sqlite-constraints] | CRDT extension: tables become conflict-free replicated relations merged per column | CRRs may not have UNIQUE constraints besides the primary key (151 tables have them); foreign keys "cannot be checked" (162 tables have them); inserts 2.5× slower | MIT; last release v0.16.3 (2024-01-17) | No |
| **rqlite** [rqlite-faq] | Raft-replicated SQLite behind an HTTP API | "Not a drop-in replacement": all writes through its HTTP API; every repository write path would change | MIT; v10.6.0 (2026-10-12), active | No; built for availability, not one learner |
| **PowerSync** [PowerSync] | Syncs client SQLite from a backend database | The authority is Postgres, MongoDB, MySQL or SQL Server; client writes go through the developer's backend | Service under FSL-1.1-ALv2 | No: re-platforming |
| **Electric** [Electric] | Read-path sync from Postgres ("shapes"); writes through the developer's API | Postgres authority | Apache-2.0 | No: re-platforming |
| **`sqlite3_rsync`** [sqlite3_rsync] | Makes a replica an exact, consistent copy of a live origin over SSH, sending only changed pages | The origin may be in active use; the replica stays readable during the sync; no WAL or page-size limits since 3.50.0. Installed on `carson` (SQLite 3.54.0) | Part of SQLite (public domain); since 3.47.0 (2024-10-21) | **Good for one-way snapshots** (a1's laptop copy, an off-host backup copy). Not multi-writer |

### 5.4 (d) File sync (Syncthing, Dropbox, iCloud Drive, Nextcloud)

**For live databases: never.** A WAL database is `state.sqlite` plus `-wal` and `-shm`; a sync client can upload them from different moments or replace one without the other, and WAL "does not work over a network filesystem" because its index is shared memory on one host [SQLite-WAL] [SQLite-corrupt §1.2, §1.4, §2.5]. The repository's architecture rule says the same (`docs/learnloop-architecture-vault/Architecture/State and Persistence.md:89-90`). Two hosts each running LearnLoop on a synced folder would also each take their own `fcntl` lock, so the vault mutation lock would protect nothing (`src/learnloop/vault_lock.py:9-13`).

**For closed artefacts: fine.** Content-addressed originals, finished backups and a laptop snapshot made with the backup API can be copied by any tool, because nothing writes them in place. Syncthing (MPL-2.0, v2.1.6) would work for that, but the hub can serve the same files itself (§5.5).

### 5.5 (e) Blobs: the content-addressed originals store

The store already is what (e) asks for: `canonical-sources/raw/sha256-<hex>`, written atomically with fsync, idempotent, and verifiable against each revision's `asset_hash` (`src/learnloop/ingest/originals.py:23-53`). It lives inside the vault, so it leaves git when the vault does.

**What changes:**
- **The hub serves it.** An authenticated `GET /api/v1/originals/sha256-<hex>` on the private host, with the same content-addressed-name rule as the desktop's `llpdf://` handler (`apps/learnloop-tauri/src-tauri/src/main.rs:19-52`) and the Reader's permission check (`_require_source_reader` in `src/learnloop_sidecar/handlers/reader.py:546-547`).
- **The store becomes the only authority for bytes** (§6.4).
- **Off-site:** it is part of every backup, and restic transfers only what changed [restic].
- **Not needed now:** a store shared across vaults, or object storage as the primary store. The three vaults' originals total 229 MB (§2.2).

### 5.6 (f) Authored content: text export or the database as authority

Authored knowledge is already text (YAML and Markdown) and stays the authority for what it holds; evidence stays in SQLite. Some authored definitions live only in the database (activity cards, families and patterns are RAW_LEDGER rows), so a YAML-only git history would never be a complete copy of the learner.

**Options:**
- **f0.** Versions come from backups only.
- **f1.** The hub keeps an optional *private* git repository of each vault's text files (excluding `state.sqlite*`, `.learnloop/`, `canonical-sources/`, `projects/*.sqlite`, `.env`), committed automatically after each accepted change, never pushed to the code repository, and never used to move data between machines.
- **f2.** A full JSONL export of the database as the authority. Rejected: it inverts the authority model and duplicates replay.

**Recommendation:** f0, with f1 as an opt-in (D11). The owner's request was about sharing *code*; the vault's history is the owner's, and the backups version it.

### 5.7 Comparison

| | One learner state (R1, R2) | Offline | Invariants (R4, R5) | Contributors (R6) | Cost |
|---|---|---|---|---|---|
| (a0) Hub, online-only | Yes | Capture only | Unchanged | Clean | Low to medium (§6.11) |
| (a1) Hub + read-only laptop snapshot | Yes | Read-only | Unchanged | Clean | (a0) + a read-only desktop mode |
| (a2) Hub + deferred-grading offline practice | Yes, after reconnect | Practice, delayed feedback | Successor needed | Clean | High |
| (b) Event-log replication | Eventually, with merge anomalies | Full | Many successors | Clean | Very high |
| (c) Litestream / `sqlite3_rsync` | Backup or snapshot only | — | Unchanged | — | Low; complements (a) |
| (c) LiteFS, libSQL, cr-sqlite, rqlite, PowerSync, Electric | — | — | Driver, schema or platform change | — | High to very high |
| (d) File-sync a live vault | Corrupts | — | Breaks ADR-015 | — | Rejected |

---

## 6. Recommendation

### 6.1 The picture

```
                    public internet                          tailnet (WireGuard; reachable away from home)
  ChatGPT / Claude ──Funnel :8443──┐          phone (PWA, Shortcut) ──Serve :443──┐
                                   │          laptop (browser; remote app, S6) ───┤
                                   ▼                                              ▼
  ┌──────────────────────────── the hub (default: carson) ─────────────────────────────────┐
  │  learnloop mcp serve      (127.0.0.1:8769, secondary)      learnloop-mobile serve        │
  │                                                            (127.0.0.1:8765, secondary;   │
  │                                                             /rpc, /app, /api/v1/…,      │
  │                                                             originals from S6)           │
  │  learnloop hub serve      (headless, holds the PRIMARY role: ingest runner,             │
  │                            post-attempt worker, maintenance, content sync)               │
  │  desktop app (Tauri)      (secondary while the hub service runs; primary otherwise)     │
  │                                                                                          │
  │  ~/learnloop-vaults/<vault>/   state.sqlite (WAL, FULL)  YAML/MD  canonical-sources/raw/ │
  │  backups: hourly backup-API snapshots ─► restic, nightly, encrypted, off-site            │
  └──────────────────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Roles: the hub, the primary role, and clients

**The hub** is the one machine that holds a vault. It is a role, not a product: any LearnLoop install is its own hub, which is why a contributor's laptop or a new learner's first launch works unchanged (R10).

**The primary role.** Exactly one process per vault runs the primary duties of `SidecarContext.load` (`src/learnloop_sidecar/context.py:58-118`): binding the ingest runner, content sync, adopting reference questions, the post-attempt worker, the projection refresh, cold-probe scheduling, startup maintenance, resuming post-attempt jobs, key-check recovery and reading-build reconciliation.
- **The lock.** The role is an exclusive `fcntl.flock` on `<vault>/.learnloop/primary.lock`, held for the life of the process. It is released on exit or death, like the vault lock (`src/learnloop/vault_lock.py:9-13`). An OS lock suffices because the hub model guarantees one host; a database lease would add a migration and a heartbeat for nothing.
- **Who takes it.** `learnloop hub serve` takes it at start and waits if it is held. The desktop sidecar tries it without waiting: if it gets it, it runs `load()` as today; if not, it runs the mobile spec's `load_secondary` (PR-1) and shows nothing different to the learner.
- **Synchronous work started by a secondary.** A synchronous synthesis run started from the desktop app while the hub service is primary records its owner (process id and boot id). The primary's abandoned-run sweep finalizes only runs whose owner is gone. The mobile spec's PR-3 put durable ownership of synchronous runs out of scope; with a separate primary it is in scope (PR-8).
- **The hub service also re-syncs vault content** when the content fingerprint changes (the mobile spec's `vault_content_fingerprint`, §3.1), once PR-2 makes content sync safe beside attempts. It serves nothing over the network; the network surfaces stay in the mobile host and the chat server.
- **Supervision.** A `systemd --user` unit, restarted on failure. Like any primary it migrates an older schema under the vault lock (ADR-008); it exits 78 on a database newer than its code, so the supervisor does not loop.

**Secondary hosts** stay as built or specified: the mobile host (`learnloop-mobile serve`, mobile §3.1) and the chat server (`learnloop mcp serve`, C1 §3.3) attach without migrating, run no primary duties, and write through domain services. Because the primary now runs continuously, their writes are completed promptly: a phone attempt's diagnosis runs on the hub's post-attempt worker within seconds, not when the desktop app next opens (R2).

**Clients** never open the database: the phone's PWA and Shortcut, a laptop browser, the laptop's remote desktop mode (S6), and the chat hosts.

**Ingest and AI calls run on the hub.** Provider keys stay in the hub's machine-global config (R9). A laptop that adds a local PDF uploads it to the hub (S6; until then, through capture), which stores it, registers it and imports it.

### 6.3 The data root

**Layout on the hub (D5):**
- `~/learnloop-vaults/<name>/` for each of the owner's existing vaults. The product default stays `~/LearnLoop`, created on first launch (`apps/learnloop-tauri/src-tauri/src/sidecar.rs:735-745`); a new learner never sees the vaults folder.
- `~/learnloop-books/` (or any folder the owner chooses) for personal PDFs not yet imported. LearnLoop never reads from it after import.
- `~/learnloop-backups/` for local snapshots (§6.7).

**Rules:**
- **No vault inside a git working tree.** Doctor gains `storage:inside_git_worktree` (a warning). Existing checks stay: `storage:network_filesystem` (`src/learnloop/ops/doctor.py:889`) and the sync-folder rule.
- **Every surface pins the vault by absolute path:** the desktop's `last_vault`, `mobile.toml`'s `vault` (mobile D15), the chat unit's `--vault`, and the hub unit's `--vault`. `learnloop hub doctor` reports any pin that differs.
- **Services run from a deployment checkout** (D13), for example `~/learnloop-app` at a tag, not the development checkout, where agents' worktrees and tests run.

### 6.4 Sources and originals: no path dependency (E1, completed)

1. **The store is the only authority for bytes.** Every path that needs an existing revision's bytes reads `stored_original_path(vault, asset_hash)` and checks the hash. This means re-read (done on `fix/reread-safety`), extraction repair (`src/learnloop/content/pipeline/jobs.py:2460-2465`, to change) and any re-import of an existing source. If the store copy is missing, the learner sees "the file this book came from is missing; add it again", never a silent re-registration.
2. **`canonical_uri` for a local file is provenance.** It is kept, shown as "added from …", and never opened for an existing revision.
3. **Local files have content identity.** When a local file is imported, `register_source_revision` first looks for an existing revision with the same `asset_hash` under an artifact of the same `acquisition_kind` whose `canonical_uri` is a local path. If one exists, it reuses that artifact and appends the new path to `source_artifact_locations` (new, RAW_LEDGER, append-only: artifact id, location, recorded at). `source_artifacts` rows are never rewritten (ADR-007). A moved or re-copied book is then the same book, on any machine.
   - No algorithm successor: source identity is not scoring, scheduling or a projection.
   - It does change import dedup, so it ships behind `ingest.content_identity_for_local_files` (default on) with a doctor line counting merges.
4. **Doctor:**
   - `sources:original_missing` (error): a current revision without a store copy;
   - `sources:path_is_lfs_pointer` (warning): a local `canonical_uri` that is a git-LFS pointer;
   - `sources:revision_without_reading` (error; from `fix/reread-safety`).
5. **Capture media and uploads** already go to the store (mobile spec §6.7); S6's laptop upload uses the same call.

### 6.5 Network plan

| Surface | Process | Bind | Tailscale | Who can reach it |
|---|---|---|---|---|
| Phone and laptop app API, PWA, capture, originals (S6) | `learnloop-mobile serve` | `127.0.0.1:8765` | **Serve port 443** (as the mobile doctor requires, `src/learnloop_mobile/doctor.py:86-117`) | Tailnet devices with a token |
| Chat (MCP) | `learnloop mcp serve` | `127.0.0.1:8769` | **Funnel port 8443** (D7) | Anyone with the secret path; Origin and Host allowlists (C1 §3.2) |
| Primary duties | `learnloop hub serve` | no listener | none | — |

Funnel visibility is per port, and Funnel can listen only on 443, 8443 and 10000 [TS-Funnel]. Keeping 443 private and giving the MCP endpoint 8443 keeps every private surface off a public port. It also answers C1a's open question Q3 ("a dedicated Funnel port for this endpoint only"; `docs/reviews/mcp-c1a.md:97-98` on `mcp/c1-read-context`). The owner re-points Funnel and updates the connector URLs in Claude and ChatGPT to `https://<hub>.<tailnet>.ts.net:8443/<token>/mcp`. Agents never run `tailscale`. `learnloop hub doctor` checks that no Funnel-enabled port carries a route to the mobile host and that the MCP route is the only Funnel route.

### 6.6 Offline behaviour, by surface

The tailnet is not a home LAN: devices connect directly or through Tailscale's relays when a direct path fails [TS-DERP], so "away from home" is "reachable" whenever both ends have internet.

| Surface | Hub reachable | Hub unreachable (asleep, off, or no internet on either end) |
|---|---|---|
| Desktop app at the hub | Everything, as today | It is the hub |
| Phone | Mobile M1–M3 | Capture outbox (mobile §7); "Your LearnLoop at home is offline"; no practice (mobile D9) |
| Laptop browser (the PWA) | Capture; dailies from M2a; the tutor from M3 | The same outbox and message as the phone |
| Laptop remote desktop mode (S6) | The full desktop UI | "Your LearnLoop at home is offline", unless S7's read-only snapshot is enabled, then reading and history only |
| Chat (ChatGPT, Claude) | C1 tools now, C1b and C2 later | The host reports a connection error; LearnLoop records nothing; the conversation continues without LearnLoop |
| The hub without internet | Everything local; AI routes fail as they do today | — |

**The remote desktop mode (S6, sized here, specified when its trigger fires).**
- **Transport.** The desktop's single `call()` (`apps/learnloop-tauri/src/api/client.ts:308-315`) switches from Tauri `invoke` to the hub's `/rpc` adapter (mobile §6.2) with a `desktop` token scope and the `desktop` device class.
- **Protocols.** `llpdf://` and `llmedia://` fetch from the hub's originals and media endpoints instead of the local disk (`apps/learnloop-tauri/src-tauri/src/main.rs:19-52`).
- **No local vault machinery:** the vault watcher and the local sidecar launch are off.
- **File pickers become uploads.**
- **Allowlist.** The `desktop` scope allows the 355 registered sidecar methods minus a short deny list: `run_cli_command`, `sqlite_admin`, vault create, select and load (the hub pins vaults), and local file operations.
- **Size:** medium to large, mostly Rust command plumbing.

**Day boundaries.** "Today" is the hub's local date (`src/learnloop/daily_plan/engine.py:150-153`). A learner travelling across time zones sees the hub's day (D15).

### 6.7 Backups and restore

| | Default | Notes |
|---|---|---|
| **Snapshot** | Hourly `learnloop backup`, from a `systemd --user` timer, into `~/learnloop-backups/<vault>/<timestamp>/`. Under the vault mutation lock, which every YAML writer takes, it copies each database through the backup API (`backup_database`, as `copy_tree_with_databases` does, `src/learnloop/db/copies.py:137-163`) and then the text files. Originals are copied outside the lock; they are content-addressed and never rewritten, so unchanged ones are hard-linked from the previous snapshot. `.learnloop/` and `.env` are excluded | The lock makes the database and the YAML one consistent pair: no YAML write lands between them. A locked database (`DatabaseCopyTimeout`) skips that hour and is reported. Keep 48 hourly and 30 daily |
| **Off-site** | Nightly `restic backup` of the latest snapshot to an encrypted repository (D8: Backblaze B2, S3, or SFTP to another tailnet node) | restic encrypts and deduplicates and supports these backends [restic] [restic-repo]. Its password lives in the hub's machine-global config and in the owner's password manager: losing it loses the off-site copy [restic-repo]. Never in a vault or the repository |
| **Loss bound** | Up to 1 hour of work if the hub's disk fails; up to 24 hours off-site if the house is lost | Said in plain words in `learnloop hub doctor` and the Settings screen |
| **Continuous (optional, later; D8)** | Litestream to the same off-site provider | Seconds of loss instead of an hour. Its own checkpointing makes LearnLoop's TRUNCATE checkpoints report busy; G11 tests that lane before it is offered |
| **Restore** | `learnloop restore <snapshot> <new-dir>` then doctor, `rebuild --shadow` (replay identical) and an originals hash sweep, then switching every pin | Never restores over a live vault. A store file is trusted by name (`src/learnloop/ingest/originals.py:34-35`), so restore verifies every one |
| **Drill** | Monthly, automatic: restore the latest off-site snapshot to a scratch directory, run doctor and a shadow rebuild, report | Report-only; a failure is a doctor error |

### 6.8 Invariants and persisted meaning

| Invariant | How it holds |
|---|---|
| ADR-003, table roles | No table changes role. New tables: `source_artifact_locations` (RAW_LEDGER); nothing in S0–S7 is DERIVED |
| ADR-007, immutable evidence | Nothing is rewritten. Identity aliases append (§6.4); restores create new directories |
| ADR-008, locked atomic migrations | Unchanged. The hub service migrates through `open_vault_repository` under the vault lock; secondary hosts refuse an unexpected schema (exit 78) |
| ADR-015, WAL + FULL, backup-API copies, local disk | Every process stays on the hub; every copy goes through `learnloop.db.copies`; no file sync of live files |
| ADR-016, asynchronous diagnosis | Strengthened: the primary is always running on the hub, so diagnosis no longer waits for the desktop app |
| Replay and shadow rebuild | Unchanged. No phase reorders or merges history |
| Algorithm playbook | **No successor for S0–S7.** S8 (offline practice) would need one, which is one reason it is deferred |

### 6.9 What changes in the mobile spec (`spec_mobile_tailnet_v1.md`)

Section numbers in this list are the mobile spec's, except where marked "here".

- **"The desktop" becomes "the hub"** wherever it means the machine holding the vault: §0, T1, §3 and §7. The hub is the desktop by default (D3).
- **T7 and §3.3: the primary may be the hub service.** "The desktop app and the `learnloop` CLI remain the primary hosts" becomes "whichever process holds the primary role (§6.2 here)". PR-1's `load_secondary` is also how the desktop app attaches while the hub service runs.
- **New prerequisite PR-8, the primary role:** the `primary.lock` flock, `learnloop hub serve`, the desktop's fallback to `load_secondary`, and owner records on synchronous synthesis runs so the primary's sweep never finalizes a live one (§6.2; this extends PR-3). It lands with PR-1..PR-7 and is gated by G6b's two-process tests extended to three processes (G10 here).
- **Mobile D11 (desktop asleep)** is replaced by D4 here: the hub stays awake.
- **§6.4 device classes** gain `desktop` for the laptop's remote mode (same eligibility as the desktop), set from the request origin (PR-5).
- **§8's `mobile.toml`** pins a vault under the data root (D5); the M1 migration and tables are unchanged.
- **§3.2 ports:** Serve keeps port 443; Funnel never shares a port with the host (§6.5). The as-built doctor already enforces it.
- **§4.5:** a `desktop` token scope for S6 (deny-listed, not allowlisted, because the client is the owner's full UI). Phone scopes are unchanged.
- **§7:** the "desktop offline" message becomes "Your LearnLoop at home is offline".

### 6.10 What changes for the chat frontend (C1a, C1b, C2)

- **C1a's runtime is unchanged:** `RemoteRuntime.attach` (secondary attach, exit 78 on schema mismatch; `src/learnloop/remote/runtime.py:58-61`, `:131-140` on `mcp/c1-read-context`) pins the vault given by `--vault`.
- **Its unit moves** to the deployment checkout (D13) and the vault under the data root (D5).
- **Funnel port 8443** instead of port 443 (D7), answering Q3.
- **The endpoint token** stays machine-local in `<vault>/.learnloop/mcp/` and is excluded from backups (§6.7). A restored vault therefore gets a new token, and the owner updates the connector URL.
- **C1b's writes** (capture, confirms, `note_question`) land in the hub's vault and are picked up promptly by the hub service's content sync and post-attempt worker. PR-7's `queue_revision` bumps tell an open desktop app.
- **C2's chat practice** grades and diagnoses on the hub, whether or not the desktop app is open. Its integrity successor (C1 §7) is unchanged and is the only algorithm change on that path.

### 6.11 Phases

| Phase | Build | Owner does | Gate | Size |
|---|---|---|---|---|
| **S0: stop the exposure** | Nothing in code. This spec, and a short note in the README once D2 is decided | Decides D1 and D2. Recommended: makes the repository private now, which is reversible | With D1 taken, anonymous `HEAD` requests to the URLs in §3.3 return 404 | Owner action |
| **S1: backup and move the owner's data** | `learnloop vault move <src> <dst>` (a `copy_tree_with_databases` copy; verify the database page by page and every file by hash; then the pins); `learnloop backup` and `learnloop restore` with their timers and the monthly drill (§6.7); doctor `storage:inside_git_worktree`. Run `backfill-originals` on each vault first | Chooses D5 and D8. Quits the desktop app, runs the move per vault, confirms, then lets the next stage untrack the old copies (§7.1) | G1, G2, G3 | Small |
| **S2: sources without paths** | §6.4: repair and re-import read the store; content identity for local files; `source_artifact_locations`; the doctor lines. Lands after `fix/reread-safety` | — | G4, G5 | Small |
| **S3: tests without private data** | §7.2: builders for synthetic vaults; the migration head as SQL text; the opt-in `owner_vaults` lane; guard tests; CLAUDE.md and architecture docs updated | Reviews the historical fixtures' dumps and the three text fixtures for private content (D6) | G6, G7, G8 | Medium |
| **S4: remove git-LFS** | Delete the LFS rules from `.gitattributes`; untrack `new_textbooks/` and the fixture stores; guard against LFS rules | Copies the real textbook bytes out first (§7.1 step 7) | G9 | Small |
| **S5: the hub service** | PR-1..PR-8 (mobile §3.3 plus §6.2 here); `learnloop hub serve`, its unit and `learnloop hub doctor`; ports per §6.5 | Enables the units; re-points Funnel to port 8443 and updates the connector URLs; sets the hub's power policy (D4) | G10, G12 | Medium (PR-1..PR-7 are already budgeted by mobile M2) |
| **S6: laptop remote desktop mode** | §6.6, own spec | — | Its spec's gates | Medium to large; on trigger (§11) |
| **S7: read-only laptop snapshot** | `sqlite3_rsync` or backup-API pull over the tailnet; a read-only desktop mode | — | Its spec's gates | Medium; on trigger |
| **S8: offline practice** | (a2) with an algorithm successor | — | — | Large; on trigger |

**Order.** S0 now. S1 before anything else touches the owner's vaults. S2 and S3 in parallel. S4 after S1 and S3. S1–S4 land before mobile PR-1..PR-7 start. S5 *is* those prerequisites plus PR-8, so mobile M2a and chat C2 follow S5; C1b can land alongside it.

---

## 7. Migration from today

### 7.1 The owner's vaults and textbooks

1. **Inventory** (owner): which vaults are in use. Agents never search the filesystem for vaults; the owner lists them, for example `fixtures/linear_algebra`, `fixtures/probability`, `fixtures/arxiv_v2` and any under `fixtures-local/` or `~/LearnLoop`.
2. **Close everything** that opens them: the desktop app, the mobile host, the chat server, the CLI.
3. **Fill the store:** `learnloop backfill-originals --vault <v>` (`src/learnloop/cli/app.py:501-527`). It refuses bytes whose hash differs, so pointer files cannot enter the store. The 2026-10-14 measurement found nothing to fill (19 of 19).
4. **Move:** `learnloop vault move <v> ~/learnloop-vaults/<name>`. It copies (backup API for every database, including nested ones such as `projects/project_store.sqlite`), verifies, migrates the copy under the vault lock, runs doctor and `rebuild --shadow` (replay identical), checks that the source did not change during the copy, and only then updates `last_vault`, `mobile.toml` and the unit files. **The source stays untouched.**
5. **Use the new location for a while** (a week by default) with the old one as a fallback.
6. **Untrack the old copies.** A repository change removes `fixtures/<working vault>/` from the index (`git rm -r --cached`, which leaves the files on disk) and ignores the path. It runs only after S3 has replaced every test that used them. Deleting the old working copies in the main checkout is the owner's step; an agent never deletes them.
7. **Textbooks.** The real bytes are in the local LFS store (443 MB) and in any checkout where LFS smudged them. The owner, or a stage the owner authorizes, materializes them from the local store (no network: `git lfs checkout` reads `.git/lfs/objects`), checks each against its pointer's `oid`, copies them to `~/learnloop-books/`, and only then lets S4 untrack them. Already-imported books need nothing: their vault stores hold the bytes.

### 7.2 Test fixtures: generated, text-only, no private data

| Today | After S3 |
|---|---|
| `create_basic_vault` template (synthetic) | Unchanged |
| Tests that read a working vault for a property, not for the owner's data (9 of the 13 test files in §2.4) | Each gets a **synthetic vault builder** in `tests/fixture_vaults/` that reproduces the property the test pins: a sourced subject with practice history, a goal with facets, a placement-ready vault. Builders write YAML and drive history through domain APIs with `FrozenClock`, so the vault is deterministic and built once per session like the basic template. Goldens are re-pinned once, with each change explained in the stage record |
| The other 4, which parametrize over all three working vaults (`tests/test_placement_fixture_copies.py`, `tests/test_router_r2a_serving.py`, `tests/test_daily_loop_start_minutes.py`, `tests/test_daily_plan_kill_switch.py`) | Their synthetic cases stay in the default lane. Their working-vault cases move to an opt-in **`owner_vaults` lane** (a marker declared in `pyproject.toml`), skipped unless `LEARNLOOP_OWNER_VAULTS=<dir>` names backup-API copies. Stages that touch those paths run it on copies, as stages already do by hand |
| **Historical fixtures:** `migration_head_202` (binary), `mvp017_route_check_replay` (binary; only `e238fa07a` can regenerate it) and `linear_algebra_legacy` (binary). They hold history written by older code, so today's code cannot rebuild them | **SQL text dumps** (`state.sql`) of the same databases, loaded into a temporary database by a session fixture; FTS5 `source_block_fts` is left out of each dump and rebuilt by its replayer. Third-party files in their originals stores are dropped; a test that reads one moves to a synthetic source. The owner reviews each dump's content first (D6); one the owner marks private is rebuilt synthetically instead and its goldens re-pinned. CLAUDE.md's migration procedure becomes "load the head dump, apply the new migrations, dump again as `migration_head_<N>`" through a script, with the same README and five-path updates as today |
| `conic-sections`, `arxiv` (binary; three test files) | Replaced by builders |
| `law`, `physical_therapy` | Removed (used only by the fixture walkers) |
| Fixture originals stores with third-party files | Synthetic sources: generated text, and small PDFs written by a test helper (as `tests/ux_phase1_support.py:60` already does) from project-authored text. A public-domain file only with a licence note on G8's allowlist (D16) |
| `grading_hardcases`, `proto_sources`, `synthesis_eval_gold` | Kept after an owner content review (D6) |
| Fixture walkers and the WAL guard (`tests/test_tracked_fixture_databases.py`, `tests/conftest.py:100-151`) | Replaced by guards: no tracked `*.sqlite`, `*.sqlite-*`, `*.pdf` (outside an allowlist with licence notes), files over 5 MB, or `filter=lfs` in `.gitattributes`. The ADR-015 check 7 text is updated |

### 7.3 Removing git-LFS

1. After §7.1 step 7: delete the LFS lines from `.gitattributes` (`.gitattributes:1-3`), then untrack `new_textbooks/` and the fixture originals stores.
2. The owner runs `git lfs uninstall` locally if no other repository needs LFS.
3. A guard test fails on any `filter=lfs` rule.
4. **What this does not do:** remove LFS objects already on GitHub. Only deleting and recreating the repository, or GitHub Support, does that [GH-LFS-remove]; that is §7.4.

### 7.4 The public history (owner decision; never done by an agent)

What history holds (§3.2, §3.3): 81 database blobs with the owner's attempts and extracted book text; textbooks in plain git (Axler, Blitzstein, MIT course PDFs) and in LFS (23 objects); third-party exam text. A public fork has existed since 2026-07-21.

| Option | What happens | Risks |
|---|---|---|
| **H1. Private now, then a clean public repository (recommended)** | (1) Make `6up-b/learnanything` private: anonymous downloads stop, the existing public fork is detached into its own network and stays public, stars and watchers are reset [GH-visibility]. (2) When S1–S4 are done, publish the code as a **new** public repository from a filtered copy (or a fresh first commit), and archive the old one, private | The fork keeps whatever it copied, and GitHub cannot give its owner's contact details [GH-sensitive]; old links break; issues and PRs stay on the private repository |
| **H2. Rewrite in place** | `git filter-repo --sensitive-data-removal` over the private paths, force-push every branch, then delete and recreate the repository to drop LFS objects, and ask Support to purge cached views and PR refs [GH-sensitive] [GH-LFS-remove] | Destructive and irreversible: every commit hash changes (this spec's citations to `bffe086ec`, every review record, every agent worktree and branch); deleting the repository removes its issues and stars and does not delete public forks [GH-delete]; clones and the fork keep the data |
| **H3. Stop adding, keep history** | S1–S4 only | Everything in §3.3 stays downloadable from old commits and LFS |

Agents never change visibility, rewrite history, force-push or delete a repository. If the owner chooses H2, it runs as an owner-run procedure with a fresh mirror backup first.

### 7.5 Documents to update when each phase lands

- `CLAUDE.md`: the working-vault and fixture-database paragraphs, and the migration-fixture procedure (S1, S3).
- `docs/learnloop-architecture-vault/Architecture/State and Persistence.md` (where a vault may live: the hub and data root; backups) and ADR-015 check 7 (S3).
- `docs/specs/spec_mobile_tailnet_v1.md` (§6.9) and `docs/specs/spec_mcp_frontend_c1.md` (§6.10) when S5 starts.
- A new ADR, "One hub holds the vault; every other surface is a client", at S5.

---

## 8. Gates and tests

| Id | Gate |
|---|---|
| G1 | `vault move` on a seeded vault with a live writer during the copy: the copy is consistent (integrity check), and the destination's `rebuild --shadow` is identical. Every file's SHA-256 matches. Nested databases are copied through the backup API (`tests/test_sqlite_file_copies.py` stays green). The source is byte-identical afterwards. A write to the source during the copy makes the move refuse to switch the pins |
| G2 | `backup` then `restore` round-trips a seeded vault: doctor clean, shadow rebuild identical, every originals file re-hashed. A restore refuses an existing non-empty target |
| G3 | Doctor reports `storage:inside_git_worktree` for a vault inside a git working tree, and not otherwise |
| G4 | Repair, re-read and re-import of a source whose `canonical_uri` is an LFS pointer, a deleted file or a changed file read the store and never register a revision from it; with no store copy they refuse with the plain message |
| G5 | Importing the same PDF from two paths yields one artifact, one revision and two `source_artifact_locations` rows. With the kill switch off, it behaves as today |
| G6 | A fresh clone with no `fixtures/*/state.sqlite`, no LFS and no network beyond package installs passes `uv run pytest`; the `owner_vaults` lane is skipped with its reason |
| G7 | The migration-head dump loads into a database whose `applied_versions` equals the head, and every upgrade test passes against it |
| G8 | The guard tests fail on a tracked database, PDF outside the allowlist, file over 5 MB or `filter=lfs` rule |
| G9 | `.gitattributes` has no LFS rule; `git lfs ls-files` is empty on the new tree |
| G10 | Three processes (hub service, desktop sidecar, mobile host) on one vault in the durability lane: exactly one holds the primary role; the desktop falls back to `load_secondary` while the service runs and takes the role when the service stops; leased jobs never run twice; a synchronous synthesis run started from the desktop survives the service's abandoned-run sweep; a phone attempt is diagnosed with no desktop process running |
| G11 | With Litestream enabled (a later option, D8): checkpoints report busy without raising, doctor reports the WAL size honestly, and a Litestream restore passes G2's checks |
| G12 | `learnloop hub doctor`: fails if a Funnel-enabled port routes to the mobile host, if the MCP route is not the only Funnel route, or if any surface's vault pin differs; prints the loss bounds |

Tests use fakes; no test calls Tailscale, GitHub or a network.

---

## 9. Risks

- **The hub is a single point of failure.** Mitigated by §6.7; the loss bound is stated, not hidden.
- **The hub sleeps.** Dailies away from home fail exactly when the owner wants them (D4).
- **Public ingress lands on the machine that holds the learner.** The MCP surface stays narrow (C1 risk R1) and on its own port (§6.5); OAuth stays the chat frontend's follow-up.
- **Re-pinned goldens hide a regression.** Each re-pin is listed with its old and new values in the stage record, and the `owner_vaults` lane keeps the real-data checks.
- **The move happens while something writes.** `vault move` takes the primary lock itself, the owner stops the other services first (§7.1 step 2), and the copy goes through the backup API in any case. Because a write to the old location after the copy would be lost, the move refuses to switch the pins if a second backup-API snapshot of the source differs from the first (G1).
- **History stays public** under H3, and under H1 in the fork; only the owner can choose (§7.4).
- **Time zones.** A travelling learner sees the hub's day (§6.6).
- **Projects capture on the laptop.** The project-understanding hook writes to a local path (§2.5), so commits in repositories on the laptop are not captured until an upload path exists (§11).

---

## 10. Owner decisions

| # | Decision | Recommended default |
|---|---|---|
| D1 | Stop public exposure now? | **Yes: make `6up-b/learnanything` private now.** It is reversible, keeps history, and stops anonymous downloads; contributors are invited until the clean repository exists |
| D2 | Public history: H1, H2 or H3 (§7.4)? | **H1:** private now, a new clean public repository after S1–S4. Never an agent action |
| D3 | Which machine is the hub? | **`carson`, the desktop**, which already runs the mobile host and the chat server. Moving the hub later is a backup and restore |
| D4 | Hub availability | **Keep the hub awake:** no automatic suspend on carson, and Wake-on-LAN from another always-on node if suspend is wanted at night. Replaces mobile D11 |
| D5 | Where vaults and books live | **`~/learnloop-vaults/<name>/` and `~/learnloop-books/`**; `~/LearnLoop` stays the product default for new learners |
| D6 | Which tracked fixtures are private | **The three working vaults, `law` and `physical_therapy` leave the repository; `conic-sections` and `arxiv` are replaced by builders; the historical fixtures (`migration_head_202`, `mvp017_route_check_replay`, `linear_algebra_legacy`) become SQL text dumps after the owner reviews their content**, and any the owner marks private is rebuilt synthetically. The owner also reviews the three text fixtures (§7.2) |
| D7 | Ports | **Serve port 443 for the private host; Funnel port 8443 for the MCP endpoint** (answers C1a Q3) |
| D8 | Backups | **Hourly local snapshots, nightly restic to an encrypted off-site repository** (provider: the owner's choice; another tailnet node by SFTP costs nothing). Litestream later, if one hour is too much to lose |
| D9 | Offline | **a0:** capture outboxes only, practice needs the hub (keeps mobile D9). S7 and S8 wait for their triggers |
| D10 | Laptop | **The PWA in the laptop's browser first** (with mobile M2a); the remote desktop mode (S6) on its trigger |
| D11 | Private git history of the vault's text | **Off** (backups version it); f1 is opt-in |
| D12 | A headless primary on the hub | **Yes** (§6.2, PR-8) |
| D13 | Where services run from | **A deployment checkout at a tag** (for example `~/learnloop-app`), not the development checkout |
| D14 | Content identity for local files | **Yes, behind `ingest.content_identity_for_local_files` (default on)** |
| D15 | Whose "today" | **The hub's local date** (status quo); revisit if the owner travels across time zones often |
| D16 | Third-party material in the code repository | **None:** test sources are synthetic or public-domain with a licence note, enforced by G8 |

---

## 11. Deferred, with triggers

| Item | Trigger |
|---|---|
| S6, the laptop remote desktop mode | The owner wants the Reader, ingest or graph editing on the laptop, or uses the laptop PWA for more than practice in a typical week |
| S7, the read-only laptop snapshot | The owner reports wanting to read the library or review history with no connectivity |
| S8, offline practice with deferred grading (a2) | Practice attempts blocked by "Your LearnLoop at home is offline" on more than a few days a month, from the phone or laptop request log |
| Event-log replication (b) | Two devices genuinely need to write while both are offline, which S8 cannot serve |
| Litestream | The owner judges one hour of possible loss too much (D8); G11 gates it |
| Project capture from other machines | The owner wants commits in repositories on the laptop captured: a hook that posts to the hub instead of appending to a local file |
| A hub on a dedicated always-on machine | Carson's availability is a problem after D4 |
| Moving `~/LearnLoop` for new learners | A multi-device first-run experience is specified |

---

## 12. References (checked 2026-10-14)

- [SQLite-WAL] Write-Ahead Logging, §1 and §2.2: "All processes using a database must be on the same host computer; WAL does not work over a network filesystem." https://sqlite.org/wal.html
- [SQLite-corrupt] How To Corrupt An SQLite Database File, §1.2, §1.3, §1.4, §2.5, §3.2. https://sqlite.org/howtocorrupt.html
- [SessionExt] The Session Extension: declared primary keys required, no virtual tables, conflict handling. https://sqlite.org/sessionintro.html
- [sqlite3_rsync] https://sqlite.org/rsync.html (consistent snapshot of a live origin; replica readable during sync; limits removed in 3.50.0); added in 3.47.0, https://sqlite.org/releaselog/3_47_0.html
- [Py-sqlite3] Python `sqlite3`: `backup`, `serialize`; no session API. https://docs.python.org/3/library/sqlite3.html
- [APSW-session] APSW provides the session extension. https://rogerbinns.github.io/apsw/session.html
- [Litestream-how] https://litestream.io/how-it-works/ (long read transaction; LTX files; point-in-time restore; litestream-vfs)
- [Litestream-tips] https://litestream.io/tips/ (WAL only; busy timeout; one replicator per path); https://litestream.io/guides/wal-truncate-threshold/ ; release v0.5.17, 2026-08-31, Apache-2.0 (github.com/benbjohnson/litestream)
- [LiteFS] https://docs.fly.io/litefs ("pre-1.0", no support); https://github.com/superfly/litefs ("a FUSE-based file system"); v0.5.14, 2025-04-22, Apache-2.0
- [Turso-replicas] https://docs.turso.tech/features/embedded-replicas/introduction (writes to the remote primary; "Do not open the local database while the embedded replica is syncing"); libSQL MIT (github.com/tursodatabase/libsql)
- [cr-sqlite] https://github.com/vlcn-io/cr-sqlite (merge by primary key; 2.5× insert cost; last release v0.16.3, 2024-01-17, MIT)
- [cr-sqlite-constraints] https://vlcn.io/docs/cr-sqlite/constraints (no unique constraints besides the primary key; foreign keys not checked)
- [rqlite-faq] https://rqlite.io/docs/faq/ ("No… you must only write to the database via the HTTP API"); v10.6.0, 2026-10-12, MIT
- [PowerSync] https://docs.powersync.com/intro/powersync-overview (source databases); https://docs.powersync.com/installation/app-backend-setup/writing-client-changes (client writes go through the developer's `uploadData()` and backend API); service licence FSL-1.1-ALv2 (github.com/powersync-ja/powersync-service)
- [Electric] https://electric.ax/docs/intro (read-path sync for Postgres; writes through your API); Apache-2.0
- [restic] https://restic.net (cryptography throughout; transfers only changed parts); v0.19.1, BSD-2-Clause
- [restic-repo] https://restic.readthedocs.io/en/stable/030_preparing_a_new_repo.html (local, SFTP, REST server, S3-compatible, Backblaze B2, Azure, GCS, rclone backends; "Losing your password means that your data is irrecoverably lost")
- [LFS-smudge] git-lfs smudge, `--skip` and `GIT_LFS_SKIP_SMUDGE`: pointers pass through unchanged. https://github.com/git-lfs/git-lfs/blob/main/docs/man/git-lfs-smudge.adoc
- [GH-LFS-billing] https://docs.github.com/en/billing/concepts/product-billing/git-lfs (10 GiB free storage and bandwidth; "the bandwidth you use is included in the repository owner's bandwidth usage"; pointer files only once storage is exceeded)
- [GH-LFS-remove] https://docs.github.com/en/repositories/working-with-files/managing-large-files/removing-files-from-git-large-file-storage ("To remove Git LFS objects from a repository, delete and recreate the repository")
- [GH-sensitive] https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository (filter-repo `--sensitive-data-removal`; forks and clones keep the data; Support for cached views)
- [GH-visibility] https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/setting-repository-visibility (public forks detached into a new network; stars and watchers erased)
- [GH-delete] https://docs.github.com/en/repositories/creating-and-managing-repositories/deleting-a-repository ("Deleting a public repository will not delete any forks")
- [TS-Funnel] https://tailscale.com/kb/1223/funnel (ports 443, 8443 and 10000 only; a port's visibility follows its most recent `serve` or `funnel` command)
- [TS-DERP] https://tailscale.com/kb/1232/derp-servers (relays as the fallback when a direct connection is not possible)

*Related: `spec_mobile_tailnet_v1.md` · `spec_mcp_frontend_c1.md` (on `mcp/c1-read-context`) · `spec_mcp_frontend_v1.md` (untracked research appendix) · `docs/learnloop-architecture-vault/Architecture/State and Persistence.md` · ADR-003, ADR-007, ADR-008, ADR-015, ADR-016 · `docs/algorithm-change-playbook.md`*
