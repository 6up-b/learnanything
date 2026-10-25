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
    # 2. The textbooks' real bytes from the local git-LFS store (no network),
    #    each checked against its pointer's oid, and the reference PDFs.
    uv run python $S0 books-out --checkout $CHECKOUT
    # 3. Move the vault directories out of the checkout (a rename on the same
    #    filesystem): the three working vaults become the live vaults under
    #    ~/learnloop-vaults/<name>; the five older ones go to
    #    ~/learnloop-retired/<name>-<date>.
    uv run python $S0 move-out --checkout $CHECKOUT --yes
    # 4. The gate: refuses (exit 1) unless 1-3 are complete and verified.
    uv run python $S0 check --checkout $CHECKOUT
    # 5. Only then the owner merges S0 into the checkout (git deletes the
    #    now-absent files cleanly), and verifies:
    uv run python $S0 verify-after --checkout $CHECKOUT

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
LFS_POINTER = b"version https://git-lfs.github.com/spec/v1"
DATABASE_SUFFIXES = (".sqlite",)
COMPANIONS = ("-wal", "-shm", "-journal")


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
            continue  # machine-local scratch (locks, caches), gitignored and disposable
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


def _vault_names(args) -> tuple[str, ...]:
    return tuple(args.vault_names.split(",")) if args.vault_names else VAULTS


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


def _book_expectations(checkout: Path) -> dict[str, str]:
    """new_textbooks/<path> -> the sha256 its real bytes must have."""
    books = {}
    root = checkout / "new_textbooks"
    if not root.is_dir():
        return books
    for path in sorted(root.rglob("*")):
        if path.is_file():
            data = path.read_bytes()
            books[path.relative_to(root).as_posix()] = _pointer_oid(data) or hashlib.sha256(data).hexdigest()
    return books


# --- commands -------------------------------------------------------------------------------------------


def copy_out(args) -> int:
    from learnloop.db.copies import copy_tree_with_databases

    checkout = args.checkout.resolve()
    backup_root = args.backup_root.expanduser().resolve()
    manifest_path = backup_root / MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"vaults": {}}
    for name in _vault_names(args):
        source = checkout / "fixtures" / name
        destination = backup_root / name
        if not source.is_dir():
            if name in manifest["vaults"] and destination.is_dir():
                print(f"{name}: already copied out")
                continue
            raise Refused(f"{name}: {source} is missing and no backup exists")
        if destination.exists():
            raise Refused(f"{name}: {destination} exists; choose a new --backup-root")
        before = tree_manifest(source)
        copy_tree_with_databases(source, destination)
        copied = tree_manifest(destination)
        after = tree_manifest(source)
        problems = _compare(before, copied, f"{name} copy") + _compare(before, after, f"{name} source during copy")
        if problems:
            raise Refused("copy did not verify (is a LearnLoop process still open?):\n" + "\n".join(problems))
        manifest["vaults"][name] = {
            "source": str(source),
            "copied_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
            **copied,
        }
        backup_root.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
        print(f"{name}: copied to {destination} and verified ({len(copied['files'])} files, "
              f"{len(copied['databases'])} databases)")
    return 0


def books_out(args) -> int:
    import shutil

    checkout = args.checkout.resolve()
    books_root = args.books_root.expanduser().resolve()
    lfs = _lfs_objects(checkout, args.lfs_objects)
    for relative, oid in _book_expectations(checkout).items():
        destination = books_root / relative
        if destination.is_file() and sha256_file(destination) == oid:
            print(f"{relative}: already in {books_root}")
            continue
        working = checkout / "new_textbooks" / relative
        candidates = [working, lfs / oid[:2] / oid[2:4] / oid]
        source = next((path for path in candidates if path.is_file() and sha256_file(path) == oid), None)
        if source is None:
            raise Refused(f"{relative}: no local copy with sha256 {oid} (checked the checkout and {lfs}); "
                          "fetch it from the LFS store before landing")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        if sha256_file(destination) != oid:
            raise Refused(f"{relative}: the copy in {books_root} does not match {oid}")
        print(f"{relative}: copied from {source}")
    for paper in PAPERS:
        source = checkout / "docs" / "brainstorming" / paper
        destination = books_root / "papers" / paper
        if destination.is_file() and (not source.is_file() or sha256_file(source) == sha256_file(destination)):
            continue
        if not source.is_file():
            raise Refused(f"papers/{paper}: missing from the checkout and from {books_root / 'papers'}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        print(f"papers/{paper}: copied")
    return 0


def move_out(args) -> int:
    checkout = args.checkout.resolve()
    vaults_root = args.vaults_root.expanduser().resolve()
    retired_root = args.retired_root.expanduser().resolve()
    stamp = dt.date.today().isoformat()
    plan = []
    for name in _vault_names(args):
        source = checkout / "fixtures" / name
        if not source.is_dir():
            continue
        target = vaults_root / name if name in WORKING_VAULTS else retired_root / f"{name}-{stamp}"
        if target.exists():
            raise Refused(f"{name}: {target} exists; nothing was moved")
        plan.append((source, target))
    for source, target in plan:
        target.parent.mkdir(parents=True, exist_ok=True)
        if os.stat(source).st_dev != os.stat(target.parent).st_dev:
            raise Refused(f"{target.parent} is on another filesystem; move {source} by hand after copy-out")
    for source, target in plan:
        print(f"{'move' if args.yes else 'would move'} {source} -> {target}")
        if args.yes:
            os.rename(source, target)
    if not args.yes and plan:
        print("dry run: pass --yes to move")
    return 0


def check(args) -> int:
    checkout = args.checkout.resolve()
    backup_root = args.backup_root.expanduser().resolve()
    vaults_root = args.vaults_root.expanduser().resolve()
    retired_root = args.retired_root.expanduser().resolve()
    books_root = args.books_root.expanduser().resolve()
    problems = []

    manifest_path = backup_root / MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"vaults": {}}
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
            problems += _compare(entry, tree_manifest(live), f"{name} live vault (changed since the backup? "
                                 "run copy-out again to a new --backup-root)")
        elif not any(path.is_dir() for path in retired_root.glob(f"{name}-*")):
            problems.append(f"{name}: not in {retired_root} (run move-out)")

    for relative, oid in _book_expectations(checkout).items():
        copy = books_root / relative
        if not copy.is_file() or sha256_file(copy) != oid:
            problems.append(f"new_textbooks/{relative}: no copy with sha256 {oid} in {books_root} (run books-out)")
    for paper in PAPERS:
        if not (books_root / "papers" / paper).is_file():
            problems.append(f"docs/brainstorming/{paper}: not in {books_root / 'papers'} (run books-out)")

    if problems:
        print("REFUSED: S0 must not be merged into this checkout yet.")
        print("\n".join(f"- {problem}" for problem in problems))
        return 1
    print(f"OK: every vault, textbook and paper is safe outside {checkout}; the owner may merge S0 now.")
    return 0


def verify_after(args) -> int:
    import subprocess

    checkout = args.checkout.resolve()
    vaults_root = args.vaults_root.expanduser().resolve()
    problems = []
    tracked = subprocess.run(["git", "-C", str(checkout), "ls-files", "--", "fixtures", "new_textbooks"],
                             capture_output=True, text=True, check=True).stdout.splitlines()
    for name in _vault_names(args):
        if any(path.startswith(f"fixtures/{name}/") for path in tracked):
            problems.append(f"fixtures/{name} is still tracked: S0 is not merged")
        if (checkout / "fixtures" / name).exists():
            problems.append(f"fixtures/{name} exists in the checkout again")
    if any(path.startswith("new_textbooks/") for path in tracked):
        problems.append("new_textbooks/ is still tracked")
    for name in WORKING_VAULTS:
        database = vaults_root / name / "state.sqlite"
        if not database.is_file():
            problems.append(f"{database} is missing")
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
