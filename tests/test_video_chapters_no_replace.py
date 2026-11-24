"""Migration 268's once-only chapter decision holds only while no write replaces a row: ``INSERT OR REPLACE`` (or
``REPLACE INTO``, or an ``ON CONFLICT ... REPLACE``) deletes a decided chapter without firing
``video_chapters_keep_decided`` (recursive triggers are off). Until the schema guard joins the next migration
(docs/reviews/reader-rd10.md, its fix round), no code may write to ``video_chapters`` that way."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
#: A replacing write: the statement's text from the replacing keyword to the table it names (within one statement).
REPLACING = re.compile(r"(?:\bINSERT\s+OR\s+REPLACE\b|\bREPLACE\s+INTO\b|\bOR\s+REPLACE\b|\bON\s+CONFLICT\b[^;]*?\bREPLACE\b)"
                       r"[^;]*?\bvideo_chapters\b|\bvideo_chapters\b[^;]*?\bON\s+CONFLICT\b[^;]*?\bREPLACE\b",
                       re.IGNORECASE | re.DOTALL)


def replacing_writes(text: str) -> list[str]:
    return [match.group(0)[:80] for match in REPLACING.finditer(text)]


def test_the_scan_sees_every_replacing_write():
    assert replacing_writes("INSERT OR REPLACE INTO video_chapters(chapter_id) VALUES (?)")
    assert replacing_writes("REPLACE INTO video_chapters VALUES (?)")
    assert replacing_writes('connection.execute(\n  "INSERT OR replace "\n  "INTO video_chapters(a) VALUES (?)")')
    assert not replacing_writes("INSERT OR IGNORE INTO video_chapters(chapter_id) VALUES (?)")
    assert not replacing_writes("INSERT OR REPLACE INTO other_table VALUES (?); SELECT * FROM video_chapters")


def test_no_code_replaces_a_video_chapter_row():
    found = {}
    for path in [*(ROOT / "src").rglob("*.py"), *(ROOT / "migrations").glob("*.sql")]:
        hits = replacing_writes(path.read_text(encoding="utf-8"))
        if hits:
            found[str(path.relative_to(ROOT))] = hits
    assert found == {}
