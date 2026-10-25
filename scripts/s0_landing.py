"""Owner-run landing of storage S0 onto a checkout that still holds the vaults.

``docs/specs/spec_storage_sync_v1.md`` §7.1 step 6. S0 untracks the owner's
vaults, ``new_textbooks/`` and four reference PDFs. ``git rm --cached`` left
them on disk in the stage's worktree, but updating ANOTHER checkout (the main
checkout) to S0's commit makes git DELETE every clean tracked file it
untracks there, and refuse while the vaults' databases have local changes.
So nothing lands until every byte is safe outside the checkout. This script is
the procedure's gate; an agent never runs it against the owner's data, and
never merges S0 into the main checkout (only the owner does).

Steps, with every LearnLoop process closed (desktop app, mobile host, chat
server, CLI)::

    S0=scripts/s0_landing.py            # from the S0 branch, e.g. a worktree
    CHECKOUT=~/Documents/thinking/learnanything

    # 1. Backup-API copies of all eight vaults, verified file by file and
    #    database by database, with a manifest (the source is only read).
    uv run python $S0 copy-out --checkout $CHECKOUT
    # 2. The textbooks' real bytes from the local git-LFS store (no network)
    #    and the reference PDFs, each checked against what git's index holds
    #    (an LFS pointer's oid, else the blob; a file staged for removal from
    #    HEAD), with a books manifest. It refuses while a plain tracked file
    #    has uncommitted edits, or while a reference paper is in neither.
    uv run python $S0 books-out --checkout $CHECKOUT
    # 3. Move the vault directories out of the checkout (a rename on the same
    #    filesystem): the three working vaults become the live vaults under
    #    ~/learnloop-vaults/<name>, each marked as a working vault; the five
    #    older ones go to ~/learnloop-retired/<name>-<date>.
    uv run python $S0 move-out --checkout $CHECKOUT --yes
    # 4. The gate: refuses (exit 1) unless 1-3 are complete and verified.
    uv run python $S0 check --checkout $CHECKOUT
    # 5. Only then the owner merges S0 into the checkout (git deletes the
    #    now-absent files cleanly), and verifies:
    uv run python $S0 verify-after --checkout $CHECKOUT

Every step can be run again after it stopped part-way: what is already done
and verified is kept. If ``check`` finds that a moved vault changed after its
backup, make a fresh backup of the moved vaults and check against it::

    uv run python $S0 copy-out --checkout $CHECKOUT --from-moved --backup-root ~/learnloop-backups/s0-2
    uv run python $S0 check --checkout $CHECKOUT --backup-root ~/learnloop-backups/s0-2

S0 lands only the plain layout: each vault's ``learnloop.toml`` names its
database as a relative ``*.sqlite`` path inside the vault, the vault is not
itself a symlink, and no symlink sits in the vault. Anything else (an absolute or ``..`` path, a symlinked database
or directory, a database named otherwise) is refused before anything is
copied or moved, and is relocated by S1's ``learnloop vault move`` or by hand
first (§7.1 step 4).

After step 5, re-point every pin at once: open each moved vault once in the
desktop app (records ``last_vault``), update ``mobile.toml``, the chat unit's
``--vault`` and any enrolled project hook (``learnloop project install-hook``).
Deleting the backups and retired copies is the owner's step, after a week and
a passing restore drill (§7.1 step 5).

Defaults (override with flags): backups ``~/learnloop-backups/s0``, live
vaults ``~/learnloop-vaults``, retired ``~/learnloop-retired``, books
``~/learnloop-books`` (papers under ``papers/``).
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

WORKING_VAULTS = ("linear_algebra", "probability", "arxiv_v2")
OLDER_VAULTS = ("arxiv", "conic-sections", "law", "physical_therapy", "linear_algebra_legacy")
VAULTS = WORKING_VAULTS + OLDER_VAULTS
PAPERS = (
    "DTransKT.pdf",
    "a_diagnostic_driven_multi_agent_socratic_teaching_system.pdf",
    "ace-kt.pdf",
    "Fancsali-Ribeiro_IRAISE Workshop Slide Deck - Carnegie Learning & Stanford SCALE Initiative - 20260628.pdf",
)
MANIFEST = "S0-MANIFEST.json"
BOOKS_MANIFEST = "S0-BOOKS-MANIFEST.json"
LFS_POINTER = b"version https://git-lfs.github.com/spec/v1"
DATABASE_SUFFIXES = (".sqlite",)
COMPANIONS = ("-wal", "-shm", "-journal")
WORKING_VAULT_REASON = "the owner's live working vault, moved out of the checkout by storage S0"


class Refused(SystemExit):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def database_digest(path: Path) -> tuple[str, str]:
    """(integrity_check result, digest of the logical content), read only."""
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        digest = hashlib.sha256()
        for line in connection.iterdump():
            digest.update(line.encode("utf-8"))
            digest.update(b"\n")
        return integrity, digest.hexdigest()
    finally:
        connection.close()


def _is_database(path: Path) -> bool:
    return path.name.endswith(DATABASE_SUFFIXES)


def _is_companion(path: Path) -> bool:
    return path.name.endswith(COMPANIONS) or ".sqlite-" in path.name


def tree_manifest(root: Path) -> dict:
    """Every file of a vault: sha256 for files, integrity and logical digest for databases."""
    files, databases = {}, {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or _is_companion(path):
            continue
        relative = path.relative_to(root).as_posix()
        if relative.startswith(".learnloop/"):
            continue  # machine-local scratch (locks, caches, the working-vault mark), gitignored
        if _is_database(path):
            integrity, digest = database_digest(path)
            databases[relative] = {"integrity": integrity, "digest": digest}
        else:
            files[relative] = sha256_file(path)
    return {"files": files, "databases": databases}


def _compare(expected: dict, actual: dict, label: str) -> list[str]:
    problems = []
    for kind in ("files", "databases"):
        missing = sorted(set(expected[kind]) - set(actual[kind]))
        extra = sorted(set(actual[kind]) - set(expected[kind]))
        changed = sorted(key for key in set(expected[kind]) & set(actual[kind]) if expected[kind][key] != actual[kind][key])
        problems += [f"{label}: {kind[:-1]} missing: {key}" for key in missing]
        problems += [f"{label}: {kind[:-1]} not in the manifest: {key}" for key in extra]
        problems += [f"{label}: {kind[:-1]} differs: {key}" for key in changed]
    for key, entry in actual["databases"].items():
        if entry["integrity"] != "ok":
            problems.append(f"{label}: integrity_check of {key}: {entry['integrity']}")
    return problems


# --- the database the app opens (Codex review F1) --------------------------------------------------------


def vault_database(root: Path, label: str | None = None) -> tuple[Path | None, list[str]]:
    """The database ``root``'s own config names, and why S0 cannot move it as is.

    The configured path is read as the app reads it, without loading any
    environment settings (no ``.env`` or ``settings.env``; no overlay touches
    ``storage.sqlite_path``). S0 supports only a relative ``*.sqlite`` path
    inside the vault, with no symlink anywhere in the vault: a rename then
    carries the database, the backup holds it, and the moved vault opens it.
    """
    from learnloop.config.loader import load_config

    label = label or root.name
    if root.is_symlink():
        # os.walk follows a symlink given as its root, and a rename moves the
        # link, not the vault (a relative link then points nowhere).
        return None, [f"{label}: {root} is itself a symlink; S0 moves only plain trees (move the vault it points "
                      "to into place, or relocate it in S1, first)"]
    config = root / "learnloop.toml"
    if config.is_symlink() or not config.is_file():
        return None, [f"{label}: {config} is not a regular file"]
    problems = []
    for directory, subdirectories, names in os.walk(root, followlinks=False):
        relative = Path(directory).relative_to(root)
        if relative.parts[:1] == (".learnloop",):
            subdirectories[:] = []
            continue
        for name in [*subdirectories, *names]:
            if os.path.islink(os.path.join(directory, name)):
                problems.append(f"{label}: {(relative / name).as_posix()} is a symlink; S0 moves only plain trees "
                                "(relocate it in S1, or by hand first)")
    try:
        configured = load_config(config, load_environment=False).storage.sqlite_path
    except Exception as exc:  # noqa: BLE001 - an unreadable config cannot say which database the app opens
        return None, [*problems, f"{label}: its learnloop.toml could not be read ({type(exc).__name__})"]
    path = Path(configured)
    if path.is_absolute():
        return None, [*problems, f"{label}: storage.sqlite_path is absolute ({configured}); after a move the app "
                                 "would still open that file. S0 supports only a relative path inside the vault "
                                 "(relocate it in S1, or by hand first)"]
    if not path.parts or ".." in path.parts:
        return None, [*problems, f"{label}: storage.sqlite_path {configured!r} leaves the vault; S0 supports only a "
                                 "relative path inside it (relocate it in S1, or by hand first)"]
    if not path.name.endswith(DATABASE_SUFFIXES):
        problems.append(f"{label}: storage.sqlite_path {configured!r} is not a *.sqlite file, so the backup would "
                        "not verify it as a database (rename it in S1, or by hand first)")
    database = root / path
    if not database.is_file():
        problems.append(f"{label}: its configured database {database} is missing")
    elif not Path(os.path.realpath(database)).is_relative_to(Path(os.path.realpath(root))):
        problems.append(f"{label}: its configured database {database} lies outside the vault")
    return database, problems


def _require_plain_layout(root: Path, label: str) -> Path:
    database, problems = vault_database(root, label)
    if problems:
        raise Refused("nothing was copied or moved:\n" + "\n".join(f"- {problem}" for problem in problems))
    return database


# --- git and the media inventory (Codex review F2) -------------------------------------------------------


def _git(checkout: Path, *args: str) -> bytes:
    """One read-only git command in ``checkout`` (fixed argv, no shell, no model call)."""
    try:
        return subprocess.run(["git", "-C", str(checkout), *args], capture_output=True, check=True,
                              env={**os.environ, "LC_ALL": "C", "LANGUAGE": "C"}).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise Refused(f"git {' '.join(args[:2])} failed in {checkout} ({type(exc).__name__}); the landing reads "
                      "git's index to know what S0 removes") from None


def _lfs_objects(checkout: Path, override: Path | None) -> Path:
    if override is not None:
        return override
    git = checkout / ".git"
    if git.is_file():  # a worktree: "gitdir: <path>"; LFS objects live in the common dir
        gitdir = Path(git.read_text(encoding="utf-8").split(":", 1)[1].strip())
        common = gitdir / "commondir"
        git = (gitdir / common.read_text(encoding="utf-8").strip()).resolve() if common.exists() else gitdir
    return git / "lfs" / "objects"


def _pointer_oid(data: bytes) -> str | None:
    if not data.startswith(LFS_POINTER):
        return None
    for line in data.decode("utf-8", errors="replace").splitlines():
        if line.startswith("oid sha256:"):
            return line.split(":", 1)[1].strip()
    return None


def _destination(source: str) -> str:
    """Where a checkout path goes under the books folder."""
    if source.startswith("new_textbooks/"):
        return source[len("new_textbooks/"):]
    return "papers/" + Path(source).name


def _has_head(checkout: Path) -> bool:
    """Whether the checkout has a commit (a fresh repository has none, so nothing to recover from)."""
    try:
        _git(checkout, "rev-parse", "--verify", "-q", "HEAD")
    except Refused:
        return False
    return True


def media_inventory(checkout: Path) -> dict[str, dict]:
    """Destination path -> what it must hold, from git (never from what the working tree holds).

    A tracked file's expected sha256 is its LFS pointer's oid, or else its
    blob's. The index decides; a file already staged for removal is recovered
    from HEAD (Codex re-review F8). A working-tree file that git does not
    track under ``new_textbooks/`` is listed with its current hash. A tracked
    file the working tree lost, or materialized wrongly, keeps its tracked hash.
    """
    sources = ["new_textbooks", *(f"docs/brainstorming/{paper}" for paper in PAPERS)]
    media = {}

    def add(path: str, blob: str) -> None:
        data = _git(checkout, "cat-file", "blob", blob)
        oid = _pointer_oid(data)
        media.setdefault(_destination(path), {"source": path, "sha256": oid or hashlib.sha256(data).hexdigest(),
                                              "kind": "lfs" if oid else "git", "blob": blob})

    for record in _git(checkout, "ls-files", "-s", "-z", "--", *sources).split(b"\0"):
        if record:
            header, path = record.decode("utf-8").split("\t", 1)
            add(path, header.split()[1])
    if _has_head(checkout):
        for record in _git(checkout, "ls-tree", "-r", "-z", "HEAD", "--", *sources).split(b"\0"):
            if record:
                header, path = record.decode("utf-8").split("\t", 1)
                if header.split()[1] == "blob":
                    add(path, header.split()[2])
    for record in _git(checkout, "ls-files", "-z", "--others", "--", "new_textbooks").split(b"\0"):
        if not record:
            continue
        for path in _untracked_files(checkout, record.decode("utf-8")):
            data = (checkout / path).read_bytes()
            media.setdefault(_destination(path), {"source": path, "sha256": _pointer_oid(data) or
                                                  hashlib.sha256(data).hexdigest(), "kind": "untracked"})
    return media


def _untracked_files(checkout: Path, path: str) -> list[str]:
    """One ``git ls-files --others`` entry as files.

    git names a nested repository (the owner's checkout has a cloned one under
    ``new_textbooks/``) as a single directory entry ending in ``/``. Its
    working files are listed one by one; its ``.git/`` is not, because the
    merge never deletes untracked files and its index changes whenever git
    runs there (S0 landing rehearsal).
    """
    if not path.endswith("/"):
        return [path]
    files = []
    for directory, subdirectories, names in os.walk(checkout / path):
        subdirectories[:] = sorted(name for name in subdirectories if name != ".git")
        for name in sorted(name for name in names if name != ".git"):  # a worktree's .git is a file
            files.append((Path(directory) / name).relative_to(checkout).as_posix())
    return files


def _missing_papers(media: dict) -> list[str]:
    """Every reference paper must be in the inventory; none is optional (Codex re-review F8)."""
    return [f"docs/brainstorming/{paper}: in neither git's index nor HEAD, so its bytes cannot be verified; "
            "restore it to the index (git add) or land from a checkout that still tracks it"
            for paper in PAPERS if _destination(f"docs/brainstorming/{paper}") not in media]


def _local_edits(checkout: Path, media: dict) -> list[str]:
    """A plain tracked file whose working bytes differ from git's: only the working copy holds the edits (F7).

    LFS files are left out: their working file is a pointer or the
    materialized object, and only the object's oid is trusted.
    """
    problems = []
    for relative, entry in sorted(media.items()):
        working = checkout / entry["source"]
        if entry["kind"] == "git" and working.is_file() and sha256_file(working) != entry["sha256"]:
            problems.append(f"{entry['source']}: has uncommitted changes that git's copy lacks; commit them "
                            f"(git add, git commit) or discard them, then run books-out")
    return problems


def _media_drift(persisted: dict, current: dict) -> list[str]:
    return [
        f"{source['source']}: sha256 {source['sha256']} is not in the books manifest"
        for key, source in sorted(current.items())
        if persisted.get(key, {}).get("sha256") != source["sha256"]
    ]


def _read_json(path: Path, empty: dict) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else empty


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _vault_names(args) -> tuple[str, ...]:
    return tuple(args.vault_names.split(",")) if args.vault_names else VAULTS


def _moved_location(args, name: str) -> Path | None:
    """Where move-out put a vault: the live vault, or its one retired copy."""
    if name in WORKING_VAULTS:
        live = args.vaults_root.expanduser().resolve() / name
        return live if live.is_dir() else None
    retired = sorted(path for path in args.retired_root.expanduser().resolve().glob(f"{name}-*") if path.is_dir())
    if len(retired) > 1:
        raise Refused(f"{name}: several retired copies ({', '.join(map(str, retired))}); move the extra ones away")
    return retired[0] if retired else None


# --- commands -------------------------------------------------------------------------------------------


def copy_out(args) -> int:
    from learnloop.db.copies import copy_tree_with_databases

    checkout = args.checkout.resolve()
    backup_root = args.backup_root.expanduser().resolve()
    manifest_path = backup_root / MANIFEST
    manifest = _read_json(manifest_path, {"vaults": {}})
    for name in _vault_names(args):
        in_checkout = checkout / "fixtures" / name
        destination = backup_root / name
        if args.from_moved:
            if in_checkout.exists():
                raise Refused(f"{name}: still at {in_checkout}; back it up from there (without --from-moved)")
            source = _moved_location(args, name)
        else:
            source = in_checkout
        if name in manifest["vaults"] and destination.is_dir():
            problems = _compare(manifest["vaults"][name], tree_manifest(destination), f"{name} backup")
            if problems:
                raise Refused("an existing backup does not match its manifest; choose a new --backup-root:\n"
                              + "\n".join(problems))
            print(f"{name}: already copied out and verified")
            continue
        if source is None or not source.is_dir():
            hint = "" if args.from_moved else (
                "; if move-out already moved it, back up the moved vaults with --from-moved")
            raise Refused(f"{name}: {source or 'its moved copy'} is missing and {backup_root} holds no backup of "
                          f"it{hint}")
        if destination.exists():
            raise Refused(f"{name}: {destination} exists; choose a new --backup-root")
        database = _require_plain_layout(source, name)
        before = tree_manifest(source)
        copy_tree_with_databases(source, destination)
        copied = tree_manifest(destination)
        after = tree_manifest(source)
        problems = _compare(before, copied, f"{name} copy") + _compare(before, after, f"{name} source during copy")
        if database.relative_to(source).as_posix() not in copied["databases"]:
            problems.append(f"{name}: the backup lacks the configured database {database.name}")
        if problems:
            raise Refused("copy did not verify (is a LearnLoop process still open?):\n" + "\n".join(problems))
        manifest["vaults"][name] = {
            "source": str(source),
            "copied_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
            **copied,
        }
        if args.from_moved:
            manifest.setdefault("moved", {})[name] = str(source)
        _write_json(manifest_path, manifest)
        print(f"{name}: copied from {source} to {destination} and verified ({len(copied['files'])} files, "
              f"{len(copied['databases'])} databases)")
    return 0


def _copy_media(source: Path, destination: Path) -> None:
    import shutil

    shutil.copyfile(source, destination)


def books_out(args) -> int:
    checkout = args.checkout.resolve()
    books_root = args.books_root.expanduser().resolve()
    lfs = _lfs_objects(checkout, args.lfs_objects)
    manifest_path = books_root / BOOKS_MANIFEST
    current = media_inventory(checkout)
    unsafe = _local_edits(checkout, current)
    if unsafe:
        raise Refused("nothing was copied:\n" + "\n".join(f"- {problem}" for problem in unsafe))
    if manifest_path.exists():
        persisted = _read_json(manifest_path, {})["media"]
        drift = _media_drift(persisted, current)
        if drift:
            raise Refused("the checkout's media changed since the books manifest; choose a new --books-root:\n"
                          + "\n".join(drift))
    else:
        missing = _missing_papers(current)
        if missing:
            raise Refused("no books manifest was written:\n" + "\n".join(f"- {problem}" for problem in missing))
        # The whole inventory is written before anything is copied, so a
        # check never verifies less than git's index held.
        persisted = current
        _write_json(manifest_path, {"checkout": str(checkout),
                                    "written_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
                                    "media": persisted})
    for relative, entry in sorted(persisted.items()):
        oid = entry["sha256"]
        destination = books_root / relative
        if destination.is_file() and sha256_file(destination) == oid:
            print(f"{relative}: already in {books_root}")
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        working = checkout / entry["source"]
        candidates = [working, lfs / oid[:2] / oid[2:4] / oid]
        source = next((path for path in candidates if path.is_file() and sha256_file(path) == oid), None)
        if source is not None:
            _copy_media(source, destination)
        elif entry["kind"] == "git":
            # A plain tracked file the working tree lost: git's blob holds its bytes.
            destination.write_bytes(_git(checkout, "cat-file", "blob", entry["blob"]))
            source = f"git blob {entry['blob']}"
        else:
            raise Refused(f"{entry['source']}: no local copy with sha256 {oid} (checked the checkout and {lfs}); "
                          "fetch it from the LFS store before landing")
        if sha256_file(destination) != oid:
            destination.unlink()
            raise Refused(f"{relative}: the copy in {books_root} does not match {oid}")
        print(f"{relative}: copied from {source}")
    return 0


def move_out(args) -> int:
    from learnloop.vault.working_vault import mark_working_vault, working_vault_marker_reason

    checkout = args.checkout.resolve()
    backup_root = args.backup_root.expanduser().resolve()
    vaults_root = args.vaults_root.expanduser().resolve()
    retired_root = args.retired_root.expanduser().resolve()
    manifest_path = backup_root / MANIFEST
    manifest = _read_json(manifest_path, {"vaults": {}})
    stamp = dt.date.today().isoformat()
    plan, resumed = [], []
    for name in _vault_names(args):
        source = checkout / "fixtures" / name
        if not source.is_dir():
            moved = _moved_location(args, name)
            if moved is not None and name in manifest["vaults"]:
                resumed.append((name, moved))  # moved by an earlier run
            continue
        if name not in manifest["vaults"] or not (backup_root / name).is_dir():
            raise Refused(f"{name}: no verified backup in {backup_root}; run copy-out first (nothing was moved)")
        _require_plain_layout(source, name)
        target = vaults_root / name if name in WORKING_VAULTS else retired_root / f"{name}-{stamp}"
        if target.exists():
            raise Refused(f"{name}: {target} exists; nothing was moved")
        plan.append((name, source, target))
    for _name, source, target in plan:
        target.parent.mkdir(parents=True, exist_ok=True)
        if os.stat(source).st_dev != os.stat(target.parent).st_dev:
            raise Refused(f"{target.parent} is on another filesystem; move {source} by hand after copy-out")
    if not args.yes:
        for _name, source, target in plan:
            print(f"would move {source} -> {target}")
        if plan:
            print("dry run: pass --yes to move")
        return 0

    def record(name: str, target: Path) -> None:
        # Each move is recorded as it happens, so an interrupted run resumes.
        manifest.setdefault("moved", {})[name] = str(target)
        _write_json(manifest_path, manifest)
        if name in WORKING_VAULTS and working_vault_marker_reason(target) is None:
            mark_working_vault(target, reason=WORKING_VAULT_REASON)

    for name, target in resumed:
        record(name, target)
    for name, source, target in plan:
        print(f"move {source} -> {target}")
        os.rename(source, target)
        record(name, target)
    return 0


def check(args) -> int:
    from learnloop.vault.working_vault import working_vault_marker_reason

    checkout = args.checkout.resolve()
    backup_root = args.backup_root.expanduser().resolve()
    vaults_root = args.vaults_root.expanduser().resolve()
    retired_root = args.retired_root.expanduser().resolve()
    books_root = args.books_root.expanduser().resolve()
    problems = []

    manifest = _read_json(backup_root / MANIFEST, {"vaults": {}})
    moved = manifest.get("moved", {})
    for name in _vault_names(args):
        if (checkout / "fixtures" / name).exists():
            problems.append(f"{name}: still inside the checkout at fixtures/{name}; merging S0 would delete it "
                            "(run move-out)")
        entry = manifest["vaults"].get(name)
        backup = backup_root / name
        if entry is None or not backup.is_dir():
            problems.append(f"{name}: no verified backup under {backup_root} (run copy-out)")
            continue
        problems += _compare(entry, tree_manifest(backup), f"{name} backup")
        if name in WORKING_VAULTS:
            live = vaults_root / name
            if not (live / "learnloop.toml").is_file():
                problems.append(f"{name}: no live vault at {live} (run move-out)")
                continue
            problems += vault_database(live, name)[1]
            problems += _compare(entry, tree_manifest(live), f"{name} live vault (changed since the backup? "
                                 "back up the moved vaults: copy-out --from-moved to a new --backup-root)")
            if working_vault_marker_reason(live) is None:
                problems.append(f"{name}: {live} is not marked as a working vault (run move-out)")
        elif name in moved:
            retired = Path(moved[name])
            if not retired.is_dir():
                problems.append(f"{name}: its retired copy {retired} is missing")
                continue
            problems += _compare(entry, tree_manifest(retired), f"{name} retired copy")
        elif not any(path.is_dir() for path in retired_root.glob(f"{name}-*")):
            problems.append(f"{name}: not in {retired_root} (run move-out)")

    books_manifest = books_root / BOOKS_MANIFEST
    if not books_manifest.exists():
        problems.append(f"no books manifest at {books_manifest} (run books-out)")
    else:
        persisted = _read_json(books_manifest, {})["media"]
        problems += _missing_papers(persisted)
        try:
            current = media_inventory(checkout)
            problems += _media_drift(persisted, current) + _local_edits(checkout, current)
        except Refused as refusal:
            problems.append(str(refusal.code))
        for relative, entry in sorted(persisted.items()):
            copy = books_root / relative
            if not copy.is_file() or sha256_file(copy) != entry["sha256"]:
                problems.append(f"{entry['source']} -> {relative}: no copy with sha256 {entry['sha256']} in "
                                f"{books_root} (run books-out)")

    if problems:
        print("REFUSED: S0 must not be merged into this checkout yet.")
        print("\n".join(f"- {problem}" for problem in problems))
        return 1
    print(f"OK: every vault, textbook and paper is safe outside {checkout}; the owner may merge S0 now.")
    return 0


def verify_after(args) -> int:
    checkout = args.checkout.resolve()
    vaults_root = args.vaults_root.expanduser().resolve()
    problems = []
    tracked = _git(checkout, "ls-files", "-z", "--", "fixtures", "new_textbooks").decode("utf-8").split("\0")
    for name in _vault_names(args):
        if any(path.startswith(f"fixtures/{name}/") for path in tracked):
            problems.append(f"fixtures/{name} is still tracked: S0 is not merged")
        if (checkout / "fixtures" / name).exists():
            problems.append(f"fixtures/{name} exists in the checkout again")
    if any(path.startswith("new_textbooks/") for path in tracked):
        problems.append("new_textbooks/ is still tracked")
    for name in _vault_names(args):
        if name not in WORKING_VAULTS:
            continue
        live = vaults_root / name
        if not live.is_dir():
            problems.append(f"{live} is missing")
            continue
        # The database the live vault's own config names, as the app opens it.
        database, layout = vault_database(live, name)
        problems += layout
        if database is None or layout:
            continue
        integrity, _ = database_digest(database)
        if integrity != "ok":
            problems.append(f"{database}: integrity_check {integrity}")
    if problems:
        print("\n".join(f"- {problem}" for problem in problems))
        return 1
    print("OK. Now re-point every pin: open each vault under", vaults_root,
          "once in the desktop app; update mobile.toml, the chat unit's --vault and enrolled project hooks.")
    return 0


def main(argv: list[str] | None = None) -> int:
    home = Path.home()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("copy-out", "books-out", "move-out", "check", "verify-after"))
    parser.add_argument("--checkout", type=Path, required=True, help="the checkout S0 will be merged into")
    parser.add_argument("--backup-root", type=Path, default=home / "learnloop-backups" / "s0")
    parser.add_argument("--vaults-root", type=Path, default=home / "learnloop-vaults")
    parser.add_argument("--retired-root", type=Path, default=home / "learnloop-retired")
    parser.add_argument("--books-root", type=Path, default=home / "learnloop-books")
    parser.add_argument("--lfs-objects", type=Path, default=None, help="default: the checkout's .git/lfs/objects")
    parser.add_argument("--vault-names", default="", help="comma-separated subset (tests); default all eight")
    parser.add_argument("--from-moved", action="store_true",
                        help="copy-out: back up the vaults where move-out put them (after one changed)")
    parser.add_argument("--yes", action="store_true", help="move-out: actually move")
    args = parser.parse_args(argv)
    command = {"copy-out": copy_out, "books-out": books_out, "move-out": move_out, "check": check,
               "verify-after": verify_after}[args.command]
    try:
        return command(args)
    except Refused as refusal:
        print(f"REFUSED: {refusal.code}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
