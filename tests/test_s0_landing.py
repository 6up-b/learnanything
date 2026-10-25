"""The S0 landing gate refuses until the owner's data is safe outside the checkout.

``scripts/s0_landing.py`` (spec_storage_sync_v1 §7.1 step 6) runs only on
synthetic checkouts here: a git repository holding two vaults built by the
test helpers (not added to git), a fake git-LFS store with one textbook whose
pointer git tracks, the owner's text file and one reference paper.

Codex review of S0: F1 the database the app opens (refused layouts, and
verify-after reads the live vault's own config), F2 the media inventory comes
from git's index and is persisted before anything is copied (corrupt papers,
missing source files, wrong materialized LFS bytes), F3 the live vaults are
marked as working vaults, F4 recovery after a moved vault changes and an
interrupted, resumed landing.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sqlite3
import subprocess
from pathlib import Path

import pytest
import tomlkit

from learnloop.db.copies import copy_tree_with_databases
from learnloop.vault.working_vault import working_vault_marker_reason
from tests.helpers import create_basic_vault

REPOSITORY = Path(__file__).resolve().parents[1]
BOOK = b"%PDF-1.4 a synthetic textbook for the S0 landing tests\n"
BOOK_OID = hashlib.sha256(BOOK).hexdigest()
COURSES = "the owner's own list\n"
PAPER = b"%PDF-1.4 a synthetic paper\n"


def _script():
    path = REPOSITORY / "scripts" / "s0_landing.py"
    spec = importlib.util.spec_from_file_location("s0_landing", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(checkout: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(checkout), *args], check=True, capture_output=True,
                   env={**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"})


@pytest.fixture
def layout(tmp_path):
    checkout = tmp_path / "checkout"
    create_basic_vault(checkout / "fixtures" / "linear_algebra")
    create_basic_vault(checkout / "fixtures" / "law")
    pointer = f"version https://git-lfs.github.com/spec/v1\noid sha256:{BOOK_OID}\nsize {len(BOOK)}\n"
    (checkout / "new_textbooks").mkdir()
    (checkout / "new_textbooks" / "book.pdf").write_text(pointer, encoding="utf-8")
    (checkout / "new_textbooks" / "courses.txt").write_text(COURSES, encoding="utf-8")
    lfs = tmp_path / "lfs-objects"
    (lfs / BOOK_OID[:2] / BOOK_OID[2:4]).mkdir(parents=True)
    (lfs / BOOK_OID[:2] / BOOK_OID[2:4] / BOOK_OID).write_bytes(BOOK)
    papers = checkout / "docs" / "brainstorming"
    papers.mkdir(parents=True)
    script = _script()
    script.PAPERS = ("paper.pdf",)
    (papers / "paper.pdf").write_bytes(PAPER)
    _git(checkout, "init", "-q")
    _git(checkout, "add", "new_textbooks", "docs")
    homes = {name: tmp_path / name for name in ("backups", "vaults", "retired", "books")}
    args = [
        "--checkout", str(checkout),
        "--backup-root", str(homes["backups"]),
        "--vaults-root", str(homes["vaults"]),
        "--retired-root", str(homes["retired"]),
        "--books-root", str(homes["books"]),
        "--lfs-objects", str(lfs),
        "--vault-names", "linear_algebra,law",
    ]
    return script, checkout, homes, args


def _with(args: list[str], flag: str, value: str) -> list[str]:
    index = args.index(flag)
    return [*args[:index + 1], value, *args[index + 2:]]


def _hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*")) if path.is_file()
    }


def _set_database(vault: Path, value: str) -> None:
    path = vault / "learnloop.toml"
    document = tomlkit.parse(path.read_text(encoding="utf-8"))
    if "storage" not in document:
        document["storage"] = tomlkit.table()
    document["storage"]["sqlite_path"] = value
    path.write_text(tomlkit.dumps(document), encoding="utf-8")


def _land(script, args) -> None:
    for command in ("copy-out", "books-out"):
        assert script.main([command, *args]) == 0
    assert script.main(["move-out", *args, "--yes"]) == 0


def _merge(checkout: Path) -> None:
    """What merging S0 does to the synthetic checkout: the media leave git's index and the disk."""
    _git(checkout, "rm", "-r", "-q", "-f", "--", "new_textbooks", "docs/brainstorming/paper.pdf")


def test_check_refuses_before_anything_is_copied_out(layout, capsys):
    script, checkout, _, args = layout
    assert script.main(["check", *args]) == 1
    out = capsys.readouterr().out
    assert "REFUSED" in out
    assert "linear_algebra: still inside the checkout" in out
    assert "no verified backup" in out
    assert "books manifest" in out
    assert (checkout / "fixtures" / "linear_algebra").is_dir()


def test_the_full_procedure_passes_and_never_changes_the_sources_before_the_move(layout, capsys):
    script, checkout, homes, args = layout
    before = _hashes(checkout / "fixtures" / "linear_algebra")

    assert script.main(["copy-out", *args]) == 0
    assert _hashes(checkout / "fixtures" / "linear_algebra") == before
    assert script.main(["books-out", *args]) == 0
    assert (homes["books"] / "book.pdf").read_bytes() == BOOK
    assert (homes["books"] / "courses.txt").read_text(encoding="utf-8") == COURSES
    assert (homes["books"] / "papers" / "paper.pdf").read_bytes() == PAPER

    # Copied out, but still in the checkout: merging now would delete them.
    assert script.main(["check", *args]) == 1
    assert "still inside the checkout" in capsys.readouterr().out

    assert script.main(["move-out", *args]) == 0  # a dry run moves nothing
    assert (checkout / "fixtures" / "linear_algebra").is_dir()
    assert script.main(["move-out", *args, "--yes"]) == 0
    assert not (checkout / "fixtures" / "linear_algebra").exists()
    live = homes["vaults"] / "linear_algebra"
    assert (live / "state.sqlite").is_file()
    assert len(list(homes["retired"].glob("law-*"))) == 1
    # F3: the live vault is marked as a working vault; the retired one is not live.
    assert working_vault_marker_reason(live) is not None
    assert working_vault_marker_reason(next(homes["retired"].glob("law-*"))) is None
    manifest = json.loads((homes["backups"] / "S0-MANIFEST.json").read_text(encoding="utf-8"))
    assert set(manifest["moved"]) == {"linear_algebra", "law"}

    capsys.readouterr()
    assert script.main(["check", *args]) == 0
    assert "OK" in capsys.readouterr().out

    _merge(checkout)
    assert script.main(["check", *args]) == 0  # the persisted inventory still verifies the books
    assert script.main(["verify-after", *args]) == 0


def test_move_out_refuses_a_vault_without_a_verified_backup(layout, capsys):
    script, checkout, _, args = layout
    assert script.main(["move-out", *args, "--yes"]) == 1
    assert "copy-out first" in capsys.readouterr().err
    assert (checkout / "fixtures" / "linear_algebra").is_dir()


def test_check_refuses_a_live_vault_that_changed_after_its_backup(layout, capsys):
    script, _, homes, args = layout
    _land(script, args)
    with sqlite3.connect(homes["vaults"] / "linear_algebra" / "state.sqlite") as connection:
        connection.execute("CREATE TABLE written_after_the_backup (x)")
    capsys.readouterr()
    assert script.main(["check", *args]) == 1
    assert "changed since the backup" in capsys.readouterr().out


def test_after_a_moved_vault_changes_a_fresh_backup_of_the_moved_vaults_recovers(layout, tmp_path, capsys):
    """F4: the refusal's advice works once the sources have left the checkout."""
    script, _, homes, args = layout
    _land(script, args)
    with sqlite3.connect(homes["vaults"] / "linear_algebra" / "state.sqlite") as connection:
        connection.execute("CREATE TABLE written_after_the_backup (x)")
    assert script.main(["check", *args]) == 1
    capsys.readouterr()

    fresh = _with(args, "--backup-root", str(tmp_path / "backups-2"))
    # The checkout no longer holds the vaults: a plain copy-out says where to look.
    assert script.main(["copy-out", *fresh]) == 1
    assert "--from-moved" in capsys.readouterr().err
    assert script.main(["copy-out", *fresh, "--from-moved"]) == 0
    capsys.readouterr()
    assert script.main(["check", *fresh]) == 0, capsys.readouterr().out
    manifest = json.loads((tmp_path / "backups-2" / "S0-MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["vaults"]["linear_algebra"]["source"] == str((homes["vaults"] / "linear_algebra").resolve())


def test_an_interrupted_landing_resumes(layout, capsys):
    """F4: each step can be run again after it stopped part-way."""
    script, checkout, homes, args = layout
    first = _with(args, "--vault-names", "linear_algebra")
    assert script.main(["copy-out", *first]) == 0
    assert script.main(["copy-out", *args]) == 0  # the first vault's verified backup is kept
    assert script.main(["books-out", *args]) == 0
    (homes["books"] / "courses.txt").unlink()  # stopped before the last copy
    assert script.main(["books-out", *args]) == 0
    assert script.main(["move-out", *first, "--yes"]) == 0
    assert (checkout / "fixtures" / "law").is_dir()
    assert script.main(["move-out", *args, "--yes"]) == 0
    capsys.readouterr()
    assert script.main(["check", *args]) == 0, capsys.readouterr().out


def test_check_refuses_a_retired_copy_that_changed(layout, capsys):
    script, _, homes, args = layout
    _land(script, args)
    retired = next(homes["retired"].glob("law-*"))
    (retired / "learnloop.toml").write_text((retired / "learnloop.toml").read_text(encoding="utf-8") + "\n",
                                            encoding="utf-8")
    capsys.readouterr()
    assert script.main(["check", *args]) == 1
    assert "law retired copy" in capsys.readouterr().out


# --- F1: the database the app opens --------------------------------------------------------------------


@pytest.mark.parametrize("layout_kind", ["absolute", "dotdot", "symlink", "not_sqlite"])
def test_copy_out_and_move_out_refuse_a_database_layout_s0_cannot_move(layout, tmp_path, layout_kind, capsys):
    script, checkout, _, args = layout
    vault = checkout / "fixtures" / "linear_algebra"
    database = vault / "state.sqlite"
    if layout_kind == "absolute":
        _set_database(vault, str(database.resolve()))
    elif layout_kind == "dotdot":
        _set_database(vault, "../linear_algebra/state.sqlite")
    elif layout_kind == "symlink":
        outside = tmp_path / "outside.sqlite"
        database.rename(outside)
        database.symlink_to(outside)
    else:
        database.rename(vault / "state.db")
        _set_database(vault, "state.db")
    before = _hashes(checkout / "fixtures" / "law")

    assert script.main(["copy-out", *args]) == 1
    assert "linear_algebra" in capsys.readouterr().err
    assert not (Path(args[args.index("--backup-root") + 1]) / "linear_algebra").exists()
    assert script.main(["move-out", *args, "--yes"]) == 1
    assert vault.is_dir() and (checkout / "fixtures" / "law").is_dir()
    assert _hashes(checkout / "fixtures" / "law") == before


def test_check_and_verify_after_read_the_database_the_live_vault_config_names(layout, tmp_path, capsys):
    script, checkout, homes, args = layout
    _land(script, args)
    _merge(checkout)
    live = homes["vaults"] / "linear_algebra"
    elsewhere = tmp_path / "elsewhere.sqlite"
    copy_tree_with_databases(live, tmp_path / "elsewhere-vault")
    (tmp_path / "elsewhere-vault" / "state.sqlite").rename(elsewhere)
    # The moved state.sqlite is intact, but the config now opens another file.
    _set_database(live, str(elsewhere))
    capsys.readouterr()
    assert script.main(["verify-after", *args]) == 1
    out = capsys.readouterr().out
    assert "linear_algebra" in out and "absolute" in out
    assert script.main(["check", *args]) == 1


# --- F2: the media inventory ---------------------------------------------------------------------------


def test_books_out_persists_the_inventory_from_git_before_copying(layout):
    script, _, homes, args = layout
    assert script.main(["books-out", *args]) == 0
    inventory = json.loads((homes["books"] / "S0-BOOKS-MANIFEST.json").read_text(encoding="utf-8"))["media"]
    assert inventory["book.pdf"]["sha256"] == BOOK_OID and inventory["book.pdf"]["kind"] == "lfs"
    assert inventory["courses.txt"]["sha256"] == hashlib.sha256(COURSES.encode()).hexdigest()
    assert inventory["papers/paper.pdf"]["sha256"] == hashlib.sha256(PAPER).hexdigest()


def test_check_refuses_a_corrupt_paper(layout, capsys):
    script, _, homes, args = layout
    _land(script, args)
    paper = homes["books"] / "papers" / "paper.pdf"
    paper.write_bytes(paper.read_bytes()[:5])
    capsys.readouterr()
    assert script.main(["check", *args]) == 1
    assert "papers/paper.pdf" in capsys.readouterr().out


def test_a_tracked_file_missing_from_the_working_tree_is_still_backed_up(layout, capsys):
    script, checkout, homes, args = layout
    (checkout / "new_textbooks" / "courses.txt").unlink()  # still in git's index
    assert script.main(["books-out", *args]) == 0
    assert (homes["books"] / "courses.txt").read_text(encoding="utf-8") == COURSES
    (homes["books"] / "courses.txt").unlink()
    assert script.main(["copy-out", *args]) == 0
    assert script.main(["move-out", *args, "--yes"]) == 0
    capsys.readouterr()
    assert script.main(["check", *args]) == 1
    assert "courses.txt" in capsys.readouterr().out


def test_a_wrongly_materialized_lfs_file_is_never_trusted(layout, tmp_path, capsys):
    script, checkout, homes, args = layout
    (checkout / "new_textbooks" / "book.pdf").write_bytes(b"%PDF-1.4 not the tracked book\n")
    empty = tmp_path / "empty-lfs"
    empty.mkdir()
    assert script.main(["books-out", *_with(args, "--lfs-objects", str(empty))]) == 1
    assert f"no local copy with sha256 {BOOK_OID}" in capsys.readouterr().err
    assert not (homes["books"] / "book.pdf").exists()
    # With the LFS store, the tracked pointer's bytes are copied, not the working file's.
    assert script.main(["books-out", *args]) == 0
    assert (homes["books"] / "book.pdf").read_bytes() == BOOK


def test_check_refuses_a_textbook_whose_copy_does_not_match_its_pointer(layout, capsys):
    script, _, homes, args = layout
    _land(script, args)
    (homes["books"] / "book.pdf").write_bytes(b"not the book")
    capsys.readouterr()
    assert script.main(["check", *args]) == 1
    assert f"no copy with sha256 {BOOK_OID}" in capsys.readouterr().out


def test_books_out_refuses_when_the_inventory_changed_since_its_manifest(layout, capsys):
    script, checkout, _, args = layout
    assert script.main(["books-out", *args]) == 0
    (checkout / "new_textbooks" / "added.txt").write_text("added after the manifest\n", encoding="utf-8")
    _git(checkout, "add", "-f", "new_textbooks/added.txt")
    assert script.main(["books-out", *args]) == 1
    assert "new --books-root" in capsys.readouterr().err


def test_books_out_refuses_when_the_lfs_store_lacks_a_book(layout, tmp_path, capsys):
    script, _, _, args = layout
    empty = tmp_path / "empty-lfs"
    empty.mkdir()
    assert script.main(["books-out", *_with(args, "--lfs-objects", str(empty))]) == 1
    assert "no local copy" in capsys.readouterr().err


def test_copy_out_refuses_to_overwrite_an_existing_backup(layout, capsys):
    script, _, homes, args = layout
    (homes["backups"] / "linear_algebra").mkdir(parents=True)
    assert script.main(["copy-out", *args]) == 1
    assert "exists" in capsys.readouterr().err


# --- Codex re-review: F1 a symlinked vault root, F7 local edits to tracked media, F8 papers left the index -----


def test_copy_out_and_move_out_refuse_a_vault_root_that_is_a_symlink(layout, tmp_path, capsys):
    script, checkout, homes, args = layout
    vault = checkout / "fixtures" / "linear_algebra"
    actual = checkout / "fixtures" / "actual-vault"
    vault.rename(actual)
    vault.symlink_to("actual-vault")  # relative: a rename of the link breaks it

    assert script.main(["copy-out", *args]) == 1
    assert "linear_algebra" in capsys.readouterr().err
    assert not (homes["backups"] / "linear_algebra").exists()
    # Even with a backup in place, move-out leaves the link and its target alone.
    copy_tree_with_databases(actual, tmp_path / "backup-of-actual")
    manifest = homes["backups"] / "S0-MANIFEST.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    tree = script.tree_manifest(tmp_path / "backup-of-actual")
    manifest.write_text(json.dumps({"vaults": {"linear_algebra": tree}}), encoding="utf-8")
    (tmp_path / "backup-of-actual").rename(homes["backups"] / "linear_algebra")
    assert script.main(["move-out", *args, "--yes"]) == 1
    assert "symlink" in capsys.readouterr().err
    assert vault.is_symlink() and (vault / "learnloop.toml").is_file()
    assert not (homes["vaults"] / "linear_algebra").exists()
    assert (checkout / "fixtures" / "law").is_dir()


def test_check_refuses_a_live_vault_that_is_a_symlink(layout, tmp_path, capsys):
    script, _, homes, args = layout
    _land(script, args)
    live = homes["vaults"] / "linear_algebra"
    live.rename(tmp_path / "real-live")
    live.symlink_to(tmp_path / "real-live")
    capsys.readouterr()
    assert script.main(["check", *args]) == 1
    assert "symlink" in capsys.readouterr().out


def test_books_out_refuses_uncommitted_edits_to_a_tracked_text_file(layout, capsys):
    script, checkout, homes, args = layout
    courses = checkout / "new_textbooks" / "courses.txt"
    courses.write_text(COURSES + "an uncommitted addition\n", encoding="utf-8")
    assert script.main(["books-out", *args]) == 1
    err = capsys.readouterr().err
    assert "courses.txt" in err and "uncommitted" in err
    assert not (homes["books"] / "S0-BOOKS-MANIFEST.json").exists()
    assert courses.read_text(encoding="utf-8").endswith("an uncommitted addition\n")


def test_check_refuses_uncommitted_edits_made_after_books_out(layout, capsys):
    script, checkout, _, args = layout
    _land(script, args)
    (checkout / "new_textbooks" / "courses.txt").write_text(COURSES + "added later\n", encoding="utf-8")
    capsys.readouterr()
    assert script.main(["check", *args]) == 1
    assert "courses.txt" in capsys.readouterr().out


def test_committed_edits_to_a_tracked_text_file_are_backed_up(layout):
    script, checkout, homes, args = layout
    courses = checkout / "new_textbooks" / "courses.txt"
    courses.write_text(COURSES + "committed\n", encoding="utf-8")
    _git(checkout, "add", "new_textbooks/courses.txt")
    assert script.main(["books-out", *args]) == 0
    assert (homes["books"] / "courses.txt").read_text(encoding="utf-8") == COURSES + "committed\n"


def test_books_out_refuses_when_a_paper_is_in_neither_the_index_nor_head(layout, capsys):
    script, checkout, homes, args = layout
    # Every medium untracked before the first books-out, and no commit to recover them from.
    _git(checkout, "rm", "-r", "-q", "--cached", "--", "new_textbooks", "docs/brainstorming/paper.pdf")
    for path in (checkout / "new_textbooks").iterdir():
        path.unlink()
    (checkout / "new_textbooks").rmdir()
    assert script.main(["books-out", *args]) == 1
    assert "paper.pdf" in capsys.readouterr().err
    assert not (homes["books"] / "S0-BOOKS-MANIFEST.json").exists()


def test_a_paper_staged_for_removal_is_recovered_from_head(layout):
    script, checkout, homes, args = layout
    _git(checkout, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", "media")
    _git(checkout, "rm", "-q", "--cached", "--", "docs/brainstorming/paper.pdf")
    assert script.main(["books-out", *args]) == 0
    inventory = json.loads((homes["books"] / "S0-BOOKS-MANIFEST.json").read_text(encoding="utf-8"))["media"]
    assert inventory["papers/paper.pdf"]["sha256"] == hashlib.sha256(PAPER).hexdigest()
    assert (homes["books"] / "papers" / "paper.pdf").read_bytes() == PAPER


def test_check_refuses_a_books_manifest_without_every_paper(layout, capsys):
    script, _, homes, args = layout
    _land(script, args)
    path = homes["books"] / "S0-BOOKS-MANIFEST.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    del payload["media"]["papers/paper.pdf"]
    path.write_text(json.dumps(payload), encoding="utf-8")
    (homes["books"] / "papers" / "paper.pdf").unlink()
    capsys.readouterr()
    assert script.main(["check", *args]) == 1
    assert "paper.pdf" in capsys.readouterr().out
