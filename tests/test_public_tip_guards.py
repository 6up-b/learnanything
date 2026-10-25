"""The public tip stays clone-and-test clean (storage S0: G8, G9, G13).

``docs/specs/spec_storage_sync_v1.md`` §7.2 and §8. One rule per class of
file, over what git tracks (the index, read from the working tree):

- no SQLite database, by name or by header, except the two historical
  fixtures (the migration head and ``mvp017_route_check_replay``) until S3
  turns them into text dumps;
- no PDF, EPUB, DjVu, audio or video file outside ``samples/``;
- no other binary file (one git would diff as binary) except images under
  ``docs/`` and application assets under ``apps/``;
- no file under a ``canonical-sources/`` directory outside the historical
  fixtures;
- no sample without a ``samples/NOTICE`` entry naming its licence;
- no file over 5 MB (the two historical databases excepted until S3; at
  migration head 220 they are 6.7 MB and 6.0 MB);
- no git-LFS rule and no LFS pointer file;
- none of the paths S0 removed (§3.5), and a migration-head fixture that holds
  none of the replaced transcript and answers.

A guard cannot see what an image shows: images under ``docs/`` are reviewed by
D19's list, ``docs/screenshots/BOOK_PAGES.md``.
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
from pathlib import Path

import pytest

REPOSITORY = Path(__file__).resolve().parents[1]
MAX_BYTES = 5 * 1024 * 1024
SQLITE_HEADER = b"SQLite format 3\x00"
LFS_POINTER = b"version https://git-lfs.github.com/spec/v1"
MEDIA_SUFFIXES = {
    ".pdf", ".epub", ".djvu", ".djv",
    ".mp3", ".mp4", ".m4a", ".wav", ".flac", ".ogg", ".opus", ".aac", ".webm", ".mov", ".mkv", ".avi",
}
DATABASE_SUFFIXES = {".sqlite", ".sqlite3", ".db", ".db3"}
DOCS_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
APP_ASSET_SUFFIXES = {".png", ".ico", ".icns", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".woff", ".woff2", ".ttf", ".otf"}
HISTORICAL_FIXTURE = re.compile(r"^fixtures/(migration_head_\d+|mvp017_route_check_replay)/")
ALLOWED_DATABASE = re.compile(r"^fixtures/(migration_head_\d+|mvp017_route_check_replay)/state\.sqlite$")

#: Every path spec §3.5 and §6.11 mark as leaving the tip in S0.
REMOVED_IN_S0 = (
    "fixtures/linear_algebra/",
    "fixtures/probability/",
    "fixtures/arxiv_v2/",
    "fixtures/arxiv/",
    "fixtures/conic-sections/",
    "fixtures/law/",
    "fixtures/physical_therapy/",
    "fixtures/linear_algebra_legacy/",
    "new_textbooks/",
    "docs/brainstorming/DTransKT.pdf",
    "docs/brainstorming/a_diagnostic_driven_multi_agent_socratic_teaching_system.pdf",
    "docs/brainstorming/ace-kt.pdf",
    "docs/brainstorming/Fancsali-Ribeiro_IRAISE Workshop Slide Deck - Carnegie Learning & Stanford SCALE Initiative - 20260628.pdf",
)


def _tracked() -> list[str]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z", "--cached"], capture_output=True, check=True, cwd=REPOSITORY,
        )
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("not a git checkout")
    paths = [path for path in result.stdout.decode("utf-8").split("\0") if path]
    # A path removed from the working tree but still in the index is not checked here.
    return [path for path in paths if (REPOSITORY / path).is_file()]


@pytest.fixture(scope="module")
def tracked() -> list[str]:
    return _tracked()


def _head(path: str, size: int = 8000) -> bytes:
    with open(REPOSITORY / path, "rb") as handle:
        return handle.read(size)


def _is_binary(path: str) -> bool:
    # git's own rule (buffer_is_binary): a NUL byte in the first 8000 bytes.
    return b"\x00" in _head(path)


def test_no_tracked_database_outside_the_historical_fixtures(tracked):
    databases = [
        path for path in tracked
        if Path(path).suffix.lower() in DATABASE_SUFFIXES or _head(path, len(SQLITE_HEADER)) == SQLITE_HEADER
    ]
    stray = [path for path in databases if not ALLOWED_DATABASE.match(path)]
    assert stray == [], f"tracked SQLite databases outside the S0 allowlist: {stray}"
    heads = [path for path in databases if path.startswith("fixtures/migration_head_")]
    assert len(heads) <= 1, f"only the current migration-head fixture is tracked: {heads}"


def test_no_document_or_media_file_outside_samples(tracked):
    stray = [
        path for path in tracked
        if not path.startswith("samples/")
        and (Path(path).suffix.lower() in MEDIA_SUFFIXES or _head(path, 5) == b"%PDF-")
    ]
    assert stray == [], f"PDF, EPUB, DjVu, audio or video files belong in samples/ with a NOTICE entry: {stray}"


def test_no_other_binary_file(tracked):
    def allowed(path: str) -> bool:
        suffix = Path(path).suffix.lower()
        return (
            path.startswith("samples/")
            or ALLOWED_DATABASE.match(path) is not None
            or (path.startswith("docs/") and suffix in DOCS_IMAGE_SUFFIXES)
            or (path.startswith("apps/") and suffix in APP_ASSET_SUFFIXES)
        )

    stray = [path for path in tracked if _is_binary(path) and not allowed(path)]
    assert stray == [], f"binary files outside docs/ images, apps/ assets and samples/: {stray}"


def test_no_originals_store_outside_the_historical_fixtures(tracked):
    stray = [
        path for path in tracked
        if "canonical-sources/" in path and not HISTORICAL_FIXTURE.match(path)
    ]
    assert stray == [], f"files under a canonical-sources/ directory outside the historical fixtures: {stray}"


def test_every_sample_has_a_notice_entry_naming_its_licence(tracked):
    samples = [path for path in tracked if path.startswith("samples/") and path != "samples/NOTICE"]
    notice = (REPOSITORY / "samples" / "NOTICE").read_text(encoding="utf-8") if samples else ""
    entries = {
        match.group(1): match.group(0)
        for match in re.finditer(r"(?ms)^File: (\S+)\n.*?(?=^File: |\Z)", notice)
    }
    missing = [path for path in samples if path not in entries]
    unlicensed = [path for path in samples if path in entries and not re.search(r"(?m)^Licence: \S", entries[path])]
    assert missing == [], f"samples without a samples/NOTICE entry: {missing}"
    assert unlicensed == [], f"samples/NOTICE entries that name no licence: {unlicensed}"
    stale = [path for path in entries if path.startswith("samples/") and path not in samples]
    assert stale == [], f"samples/NOTICE names files that are not tracked: {stale}"


def test_no_file_over_five_megabytes(tracked):
    large = [
        (path, (REPOSITORY / path).stat().st_size)
        for path in tracked
        if (REPOSITORY / path).stat().st_size > MAX_BYTES and not ALLOWED_DATABASE.match(path)
    ]
    assert large == [], f"tracked files over 5 MB: {large}"


def test_no_git_lfs_rule_or_pointer(tracked):
    rules = [
        f"{path}: {line.strip()}"
        for path in tracked
        if Path(path).name == ".gitattributes"
        for line in (REPOSITORY / path).read_text(encoding="utf-8").splitlines()
        if "filter=lfs" in line
    ]
    assert rules == [], f"git-LFS rules: {rules}"
    pointers = [path for path in tracked if _head(path, len(LFS_POINTER)) == LFS_POINTER]
    assert pointers == [], f"git-LFS pointer files: {pointers}"


def test_the_paths_s0_removed_stay_untracked(tracked):
    present = sorted({prefix for prefix in REMOVED_IN_S0 for path in tracked if path == prefix or path.startswith(prefix)})
    assert present == [], f"paths storage S0 removed from the public tip are tracked again: {present}"


def test_the_repository_has_the_apache_2_licence():
    text = (REPOSITORY / "LICENSE").read_text(encoding="utf-8")
    assert "Apache License" in text and "Version 2.0, January 2004" in text


def test_every_screenshot_on_the_book_page_list_exists(tracked):
    listing = (REPOSITORY / "docs" / "screenshots" / "BOOK_PAGES.md").read_text(encoding="utf-8")
    listed = re.findall(r"^\| `(docs/[^`]+\.png)` \|", listing, flags=re.MULTILINE)
    assert listed, "docs/screenshots/BOOK_PAGES.md lists no screenshot"
    assert [path for path in listed if path not in tracked] == []


def _sanitizer():
    path = REPOSITORY / "scripts" / "sanitize_migration_head_fixture.py"
    spec = importlib.util.spec_from_file_location("sanitize_migration_head_fixture", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_migration_head_fixture_holds_no_replaced_text(tracked):
    """G13's sweep: no eight-word window of the replaced transcript and none of
    the owner's replaced answers in any file, text column or raw database byte."""

    heads = sorted({path.split("/")[1] for path in tracked if path.startswith("fixtures/migration_head_")})
    assert len(heads) == 1, heads
    fixture = REPOSITORY / "fixtures" / heads[0]
    sanitizer = _sanitizer()
    hashes = json.loads((REPOSITORY / "tests" / "fixtures" / "sanitized_head_sweep.json").read_text(encoding="utf-8"))
    assert hashes["transcript_windows"] and hashes["phrases"]
    assert sanitizer.sweep(fixture, hashes) == []


def test_the_sweep_finds_planted_text(tmp_path):
    """The sweep is not vacuous: text it was built to find is found."""

    sanitizer = _sanitizer()
    hashes = {
        "window": 8,
        "transcript_windows": [sanitizer.digest(sanitizer.words("one two three four five six seven eight"))],
        "phrases": {"3": [sanitizer.digest(sanitizer.words("a planted answer"))]},
    }
    (tmp_path / "note.md").write_text("zero One two three four five six seven eight nine", encoding="utf-8")
    (tmp_path / "other.yaml").write_text("x: A planted\\nanswer", encoding="utf-8")
    import sqlite3

    with sqlite3.connect(tmp_path / "state.sqlite") as connection:
        connection.execute("CREATE TABLE t (v TEXT)")
        connection.execute("INSERT INTO t VALUES ('nothing here')")
    found = sanitizer.sweep(tmp_path, hashes)
    assert any(item.startswith("note.md") for item in found)
    assert any(item.startswith("other.yaml") for item in found)
