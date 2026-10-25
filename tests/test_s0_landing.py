"""The S0 landing gate refuses until the owner's data is safe outside the checkout.

``scripts/s0_landing.py`` (spec_storage_sync_v1 §7.1 step 6) runs only on
synthetic checkouts here: two vaults built by the test helpers, a fake git-LFS
store with one textbook, and one reference paper.
"""

from __future__ import annotations

import hashlib
import importlib.util
import sqlite3
from pathlib import Path

import pytest

from tests.helpers import create_basic_vault

REPOSITORY = Path(__file__).resolve().parents[1]
BOOK = b"%PDF-1.4 a synthetic textbook for the S0 landing tests\n"
BOOK_OID = hashlib.sha256(BOOK).hexdigest()


def _script():
    path = REPOSITORY / "scripts" / "s0_landing.py"
    spec = importlib.util.spec_from_file_location("s0_landing", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def layout(tmp_path):
    checkout = tmp_path / "checkout"
    create_basic_vault(checkout / "fixtures" / "linear_algebra")
    create_basic_vault(checkout / "fixtures" / "law")
    pointer = f"version https://git-lfs.github.com/spec/v1\noid sha256:{BOOK_OID}\nsize {len(BOOK)}\n"
    (checkout / "new_textbooks").mkdir()
    (checkout / "new_textbooks" / "book.pdf").write_text(pointer, encoding="utf-8")
    (checkout / "new_textbooks" / "courses.txt").write_text("the owner's own list\n", encoding="utf-8")
    lfs = tmp_path / "lfs-objects"
    (lfs / BOOK_OID[:2] / BOOK_OID[2:4]).mkdir(parents=True)
    (lfs / BOOK_OID[:2] / BOOK_OID[2:4] / BOOK_OID).write_bytes(BOOK)
    papers = checkout / "docs" / "brainstorming"
    papers.mkdir(parents=True)
    script = _script()
    script.PAPERS = ("paper.pdf",)
    (papers / "paper.pdf").write_bytes(b"%PDF-1.4 a synthetic paper\n")
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


def _hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*")) if path.is_file()
    }


def test_check_refuses_before_anything_is_copied_out(layout, capsys):
    script, checkout, _, args = layout
    assert script.main(["check", *args]) == 1
    out = capsys.readouterr().out
    assert "REFUSED" in out
    assert "linear_algebra: still inside the checkout" in out
    assert "no verified backup" in out
    assert "new_textbooks/book.pdf" in out
    assert (checkout / "fixtures" / "linear_algebra").is_dir()


def test_the_full_procedure_passes_and_never_changes_the_sources_before_the_move(layout, capsys):
    script, checkout, homes, args = layout
    before = _hashes(checkout / "fixtures" / "linear_algebra")

    assert script.main(["copy-out", *args]) == 0
    assert _hashes(checkout / "fixtures" / "linear_algebra") == before
    assert script.main(["books-out", *args]) == 0
    assert (homes["books"] / "book.pdf").read_bytes() == BOOK
    assert (homes["books"] / "courses.txt").read_text(encoding="utf-8") == "the owner's own list\n"
    assert (homes["books"] / "papers" / "paper.pdf").is_file()

    # Copied out, but still in the checkout: merging now would delete them.
    assert script.main(["check", *args]) == 1
    assert "still inside the checkout" in capsys.readouterr().out

    assert script.main(["move-out", *args]) == 0  # a dry run moves nothing
    assert (checkout / "fixtures" / "linear_algebra").is_dir()
    assert script.main(["move-out", *args, "--yes"]) == 0
    assert not (checkout / "fixtures" / "linear_algebra").exists()
    assert (homes["vaults"] / "linear_algebra" / "state.sqlite").is_file()
    assert len(list(homes["retired"].glob("law-*"))) == 1

    capsys.readouterr()
    assert script.main(["check", *args]) == 0
    assert "OK" in capsys.readouterr().out


def test_check_refuses_a_live_vault_that_changed_after_its_backup(layout, capsys):
    script, _, homes, args = layout
    for command in ("copy-out", "books-out"):
        assert script.main([command, *args]) == 0
    assert script.main(["move-out", *args, "--yes"]) == 0
    with sqlite3.connect(homes["vaults"] / "linear_algebra" / "state.sqlite") as connection:
        connection.execute("CREATE TABLE written_after_the_backup (x)")
    capsys.readouterr()
    assert script.main(["check", *args]) == 1
    assert "changed since the backup" in capsys.readouterr().out


def test_check_refuses_a_textbook_whose_copy_does_not_match_its_pointer(layout, capsys):
    script, _, homes, args = layout
    for command in ("copy-out", "books-out"):
        assert script.main([command, *args]) == 0
    assert script.main(["move-out", *args, "--yes"]) == 0
    (homes["books"] / "book.pdf").write_bytes(b"not the book")
    capsys.readouterr()
    assert script.main(["check", *args]) == 1
    assert f"no copy with sha256 {BOOK_OID}" in capsys.readouterr().out


def test_books_out_refuses_when_the_lfs_store_lacks_a_book(layout, tmp_path, capsys):
    script, _, _, args = layout
    empty = tmp_path / "empty-lfs"
    empty.mkdir()
    args = [*args[: args.index("--lfs-objects") + 1], str(empty), *args[args.index("--lfs-objects") + 2:]]
    assert script.main(["books-out", *args]) == 1
    assert "no local copy" in capsys.readouterr().err


def test_copy_out_refuses_to_overwrite_an_existing_backup(layout, capsys):
    script, _, homes, args = layout
    (homes["backups"] / "linear_algebra").mkdir(parents=True)
    assert script.main(["copy-out", *args]) == 1
    assert "exists" in capsys.readouterr().err
