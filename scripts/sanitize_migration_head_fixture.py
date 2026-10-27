"""Sanitize the migration-head fixture (storage S0, spec_storage_sync_v1 §7.2).

The head fixture began as the owner's small conic-sections vault: it carried a
third-party YouTube transcript and the owner's six answers. This fixture build
step replaces them with project-authored text and keeps everything the
upgrade, replay and schema tests need: every table, row, id, grade, timestamp
and applied migration, and the rollback journal.

It runs on a backup-API copy, never on a vault and never in place::

    env -i PATH=/usr/bin:/bin HOME=$(mktemp -d) .venv/bin/python \\
        scripts/sanitize_migration_head_fixture.py \\
        --source fixtures/migration_head_226 --out fixtures-local/head-sanitized \\
        --sweep-hashes tests/fixtures/sanitized_head_sweep.json

``--sweep-hashes`` is written from the unsanitized source the first time (the
hashed eight-word windows of the original transcript and the hashed original
answers; no original text is stored) and read on later runs, so the sweep can
be repeated by ``tests/test_public_tip_guards.py`` on the tracked fixture.
Then the owner reviews the output and it is copied into place with
``learnloop.db.copies`` (the stage record lists the exact commands).

Nothing in LearnLoop rewrites evidence: ADR-007 governs vaults, and this is a
fixture build step.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sanitized_head_transcript import CUE_TEXTS  # noqa: E402

TRANSCRIPT = Path(
    "canonical-sources/raw/note_source_youtube_video_hvjkcmzfix8_498a1cb1-498a1cb16be4f027.bin"
)
NOTE = Path("subjects/parabolas/notes/note_source_youtube_video_hvjkcmzfix8_498a1cb1.md")
CONCEPTS = Path("concepts/concepts.yaml")
NOTE_PATH_IN_REFS = NOTE.as_posix()

# The concept description the capture copied almost word for word from the
# video, and the project-authored replacement (in concepts.yaml, folded, and in
# the accepted proposal's payload).
CONCEPT_ID = "concept_parabola_focus_directrix"
NEW_FOCUS_DIRECTRIX_DESCRIPTION = (
    "Every point of a parabola lies exactly as far from one fixed point, its "
    "focus, as from one fixed line, its directrix."
)
NEW_FOCUS_DIRECTRIX_YAML = (
    "    description: Every point of a parabola lies exactly as far from one fixed \n"
    "      point, its focus, as from one fixed line, its directrix.\n"
)

# Synthetic answers, one per attempt id, each of the same kind as the one it
# replaces: the same item, the same grade and the same mistake (a correct
# answer stays correct; a wrong one is wrong the same way), so the stored
# grades, evidence and error events still describe it.
NEW_ANSWERS = {
    # Graded 0.5, incomplete: names the sign of a, not the opening direction.
    "01KSV70YRMW01FC06QPSG9F3Q5": "Here a = -3, so a is negative.",
    # Graded 0.25: completing-the-square setup with the -1 slip, x = -1 only.
    "01KSV7D5K93VM8WZ7NKVD45DTH": (
        "Pull out -1: $f(x) = -(x^2 + 2x - 1)$ and $x^2 + 2x - 1 = (x + 1)^2 - 1$, "
        "so the vertex has $x = -1$."
    ),
    # Graded 0, conceptual slip: an unrelated condition instead of equal distances.
    "01KSV7HAZNGJYQ5GDQBXTATYD5": "The points all have to lie on the y-axis, x = 0.",
    # Graded 0.5: adds 4 instead of 1 when completing the square.
    "01KSV7Z45SVARGMXXF94XWDSNT": (
        "Start from $-x^2 - 2x = y - 1$ and multiply by -1: $x^2 + 2x = -y + 1$.\n"
        "Adding 4 to each side gives $(x + 2)^2 = -y + 5$.\n"
        "So $y = -(x + 2)^2 + 5$."
    ),
    # Graded 1.0 (hinted): the correct vertex form.
    "01KSV8Z4661HH0S0VJ4HV4XNV5": (
        "Start from $-x^2 - 2x = y - 1$ and multiply by -1: $x^2 + 2x = -y + 1$.\n"
        "Adding 1 to each side completes the square: $(x + 1)^2 = -y + 2$.\n"
        "So the vertex form is $y = -(x + 1)^2 + 2$."
    ),
    # Graded 1.0: opens downward because a is negative.
    "01KSZNPC24P4QPSPB6KRSM7SB9": "It opens downward, because a is negative (a = -3).",
}

# Grader-written text that quoted an answer, rewritten to quote the new one.
NEW_GRADING_EVIDENCE = {
    # (attempt id, criterion id): evidence
    ("01KSV7HAZNGJYQ5GDQBXTATYD5", "equidistant_condition"): (
        'The answer says the points "have to lie on the y-axis, x = 0" and does not state '
        "that parabola points are equidistant from two objects."
    ),
    ("01KSZNPC24P4QPSPB6KRSM7SB9", "connects_negative_to_downward"): (
        'Learner concludes that it "opens downward" because a is negative.'
    ),
}
NEW_ERROR_EVIDENCE = {
    # (attempt id, error type): repair_plan_json "evidence"
    ("01KSV7HAZNGJYQ5GDQBXTATYD5", "conceptual_slip"): (
        "The learner replaces the focus-directrix condition with an unrelated condition, "
        '"The points all have to lie on the y-axis, x = 0."'
    ),
}
# A short quote of an answer inside grader text, swept for besides the answers.
EXTRA_SWEPT_QUOTES = ("must cross x=0",)

WINDOW = 8


def words(text: str) -> list[str]:
    """Lowercase word tokens; JSON escapes and typographic quotes normalized."""
    text = text.replace("\\u2019", "'").replace("\\n", " ").replace("’", "'").lower()
    return re.findall(r"[a-z0-9]+", text)


def digest(tokens: Iterable[str]) -> str:
    return hashlib.sha256(" ".join(tokens).encode("utf-8")).hexdigest()[:20]


def windows(tokens: list[str], size: int) -> Iterable[list[str]]:
    for index in range(len(tokens) - size + 1):
        yield tokens[index:index + size]


def sweep_hashes(source: Path) -> dict:
    """Hashes of what must not survive: no original text is kept, only digests."""
    cues = json.loads((source / TRANSCRIPT).read_text(encoding="utf-8"))["cues"]
    transcript_tokens = words(" ".join(cue["text"] for cue in cues))
    with sqlite3.connect(f"file:{source / 'state.sqlite'}?mode=ro&immutable=1", uri=True) as connection:
        answers = [row[0] for row in connection.execute("SELECT learner_answer_md FROM practice_attempts ORDER BY id")]
    phrases: dict[str, list[str]] = {}
    for answer in list(answers) + list(EXTRA_SWEPT_QUOTES):
        tokens = words(answer)
        phrases.setdefault(str(len(tokens)), []).append(digest(tokens))
    return {
        "about": "S0 sweep of fixtures/migration_head_*: sha256[:20] of each normalized eight-word window "
                 "of the replaced transcript and of each replaced answer (and of one quote of an answer). "
                 "scripts/sanitize_migration_head_fixture.py writes and reads it.",
        "window": WINDOW,
        "transcript_windows": sorted({digest(window) for window in windows(transcript_tokens, WINDOW)}),
        "phrases": {size: sorted(set(values)) for size, values in sorted(phrases.items())},
    }


def text_hits(text: str, hashes: dict) -> list[str]:
    tokens = words(text)
    found = []
    transcript = set(hashes["transcript_windows"])
    if any(digest(window) in transcript for window in windows(tokens, hashes["window"])):
        found.append("transcript")
    for size, values in hashes["phrases"].items():
        wanted = set(values)
        if any(digest(window) in wanted for window in windows(tokens, int(size))):
            found.append(f"answer/{size}")
    return found


def sweep(fixture: Path, hashes: dict) -> list[str]:
    """Every file, text column and the raw database bytes; empty when clean."""
    problems = []
    for path in sorted(fixture.rglob("*")):
        if not path.is_file() or path.name == "README.md":
            continue
        if path.suffix == ".sqlite":
            raw = path.read_bytes().decode("utf-8", errors="ignore")
            problems += [f"{path.relative_to(fixture)} (raw bytes): {hit}" for hit in text_hits(raw, hashes)]
            continue
        hits = text_hits(path.read_text(encoding="utf-8", errors="ignore"), hashes)
        problems += [f"{path.relative_to(fixture)}: {hit}" for hit in hits]
    database = fixture / "state.sqlite"
    with sqlite3.connect(f"file:{database}?mode=ro&immutable=1", uri=True) as connection:
        tables = [row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")]
        for table in tables:
            columns = [row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')]
            for column in columns:
                values = connection.execute(
                    f'SELECT "{column}" FROM "{table}" WHERE typeof("{column}") = \'text\''
                )
                for index, (value,) in enumerate(values):
                    for hit in text_hits(value, hashes):
                        problems.append(f"{table}.{column} row {index}: {hit}")
    return problems


def _schema(connection) -> list[tuple]:
    return connection.execute("SELECT type, name, tbl_name, sql FROM sqlite_master ORDER BY type, name").fetchall()


def _rowid_digest(connection) -> dict[str, str]:
    """Per table, a digest of every row with its rowid (rowid tables only)."""
    out = {}
    tables = connection.execute(
        "SELECT name, sql FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    for name, sql in tables:
        if sql and ("WITHOUT ROWID" in sql.upper() or sql.upper().startswith("CREATE VIRTUAL")):
            select = f'SELECT * FROM "{name}" ORDER BY 1'
        else:
            select = f'SELECT rowid, * FROM "{name}" ORDER BY rowid'
        hasher = hashlib.sha256()
        for row in connection.execute(select):
            hasher.update(repr(row).encode("utf-8"))
        out[name] = hasher.hexdigest()
    return out


def _quote_for(locator: str, cues: list[dict]) -> str:
    match = re.fullmatch(r"t=([0-9.]+)-([0-9.]+)", locator)
    if match is None:
        raise ValueError(f"unexpected locator {locator!r}")
    start, end = float(match.group(1)), float(match.group(2))
    inside = [
        " ".join(cue["text"].split())
        for cue in cues
        if round(cue["start"], 1) >= start - 0.05 and round(cue["start"] + cue["duration"], 1) <= end + 0.05
    ]
    if not inside:
        raise ValueError(f"no cue inside {locator}")
    # The captured quotes were one or two sentences from the span's start.
    quote = inside[0]
    if len(quote) < 60 and len(inside) > 1:
        quote = f"{quote} {inside[1]}"
    return quote


def sanitize_files(fixture: Path) -> list[dict]:
    raw_path = fixture / TRANSCRIPT
    original = json.loads(raw_path.read_text(encoding="utf-8"))
    cues = original["cues"]
    if len(cues) != len(CUE_TEXTS):
        raise SystemExit(f"expected {len(CUE_TEXTS)} cues, found {len(cues)}")
    new_cues = [
        {"duration": cue["duration"], "start": cue["start"], "text": text}
        for cue, text in zip(cues, CUE_TEXTS, strict=True)
    ]
    raw_path.write_text(
        json.dumps({"cues": new_cues, "video_id": original["video_id"]}, sort_keys=True), encoding="utf-8"
    )

    note_path = fixture / NOTE
    frontmatter, _ = note_path.read_text(encoding="utf-8").split("\n---\n", 1)
    lines = [
        "[t=%.1f-%.1f] %s" % (cue["start"], cue["start"] + cue["duration"], " ".join(cue["text"].split()))
        for cue in new_cues
    ]
    note_path.write_text(
        frontmatter + "\n---\n\n# YouTube video " + original["video_id"] + "\n\n" + "\n\n".join(lines) + "\n",
        encoding="utf-8",
    )

    concepts_path = fixture / CONCEPTS
    concepts = concepts_path.read_text(encoding="utf-8")
    pattern = re.compile(
        r"(  " + CONCEPT_ID + r":\n(?:    (?!description:).*\n|      .*\n)*?)"
        r"    description: .*\n(?:      .*\n)*"
    )
    concepts, count = pattern.subn(lambda m: m.group(1) + NEW_FOCUS_DIRECTRIX_YAML, concepts, count=1)
    if count != 1:
        raise SystemExit("concepts.yaml: the focus-directrix description was not found")
    concepts_path.write_text(concepts, encoding="utf-8")
    return new_cues


def sanitize_database(database: Path, new_cues: list[dict]) -> None:
    connection = sqlite3.connect(database, isolation_level=None)
    try:
        # Freed and rewritten cells are zeroed, so the old text leaves the file's bytes.
        connection.execute("PRAGMA secure_delete = ON")
        schema_before = _schema(connection)
        migrations_before = connection.execute("SELECT * FROM schema_migrations ORDER BY 1").fetchall()
        journal_before = connection.execute("PRAGMA journal_mode").fetchone()[0]
        connection.execute("BEGIN IMMEDIATE")

        for attempt_id, answer in NEW_ANSWERS.items():
            changed = connection.execute(
                "UPDATE practice_attempts SET learner_answer_md = ? WHERE id = ?", (answer, attempt_id)
            ).rowcount
            if changed != 1:
                raise SystemExit(f"attempt {attempt_id} not found")

        for (attempt_id, criterion), evidence in NEW_GRADING_EVIDENCE.items():
            changed = connection.execute(
                "UPDATE grading_evidence SET evidence = ? WHERE attempt_id = ? AND criterion_id = ?",
                (evidence, attempt_id, criterion),
            ).rowcount
            if changed != 1:
                raise SystemExit(f"grading evidence {attempt_id}/{criterion}: {changed} rows")

        for (attempt_id, error_type), evidence in NEW_ERROR_EVIDENCE.items():
            rows = connection.execute(
                "SELECT id, repair_plan_json FROM error_events WHERE attempt_id = ? AND error_type = ?",
                (attempt_id, error_type),
            ).fetchall()
            if len(rows) != 1:
                raise SystemExit(f"error event {attempt_id}/{error_type}: {len(rows)} rows")
            plan = json.loads(rows[0][1])
            plan["evidence"] = evidence
            connection.execute(
                "UPDATE error_events SET repair_plan_json = ? WHERE id = ?",
                (json.dumps(plan, separators=(",", ":")), rows[0][0]),
            )

        for row_id, refs_json in connection.execute(
            "SELECT id, source_refs_json FROM proposed_patches WHERE source_refs_json LIKE ?",
            (f"%{NOTE_PATH_IN_REFS}%",),
        ).fetchall():
            refs = json.loads(refs_json)
            for ref in refs:
                if ref.get("path") == NOTE_PATH_IN_REFS and isinstance(ref.get("quote"), str):
                    ref["quote"] = _quote_for(ref["locator"], new_cues)
            connection.execute(
                "UPDATE proposed_patches SET source_refs_json = ? WHERE id = ?",
                (json.dumps(refs, separators=(",", ":"), ensure_ascii=False), row_id),
            )

        for row_id, payload_json in connection.execute(
            "SELECT id, payload_json FROM proposed_patch_items WHERE payload_json LIKE ?",
            (f'%"id":"{CONCEPT_ID}"%',),
        ).fetchall():
            payload = json.loads(payload_json)
            payload["description"] = NEW_FOCUS_DIRECTRIX_DESCRIPTION
            connection.execute(
                "UPDATE proposed_patch_items SET payload_json = ? WHERE id = ?",
                (json.dumps(payload, separators=(",", ":"), ensure_ascii=False), row_id),
            )

        connection.execute("COMMIT")

        # Earlier table rebuilds left old rows in the unused space of reused
        # pages, which secure_delete cannot reach; VACUUM rewrites every page.
        # It must keep every rowid (checked below), so replay order is unchanged.
        rows_before = _rowid_digest(connection)
        connection.execute("VACUUM")
        if _rowid_digest(connection) != rows_before:
            raise SystemExit("VACUUM changed rows or rowids")

        problems = []
        if _schema(connection) != schema_before:
            problems.append("sqlite_master changed")
        if connection.execute("SELECT * FROM schema_migrations ORDER BY 1").fetchall() != migrations_before:
            problems.append("applied migrations changed")
        if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            problems.append("integrity_check failed")
        if connection.execute("PRAGMA foreign_key_check").fetchall():
            problems.append("foreign_key_check is not clean")
        if journal_before != "delete" or connection.execute("PRAGMA journal_mode").fetchone()[0] != "delete":
            problems.append("journal mode is not DELETE")
        if problems:
            raise SystemExit("; ".join(problems))
    finally:
        connection.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", type=Path, required=True, help="the tracked head fixture (read only)")
    parser.add_argument("--out", type=Path, required=True, help="a new directory for the sanitized copy")
    parser.add_argument("--sweep-hashes", type=Path, required=True,
                        help="written from the source when missing, read otherwise")
    parser.add_argument("--sweep-only", action="store_true", help="only sweep --source; change nothing")
    args = parser.parse_args()

    if args.sweep_hashes.exists():
        hashes = json.loads(args.sweep_hashes.read_text(encoding="utf-8"))
    else:
        hashes = sweep_hashes(args.source)
        args.sweep_hashes.parent.mkdir(parents=True, exist_ok=True)
        args.sweep_hashes.write_text(json.dumps(hashes, indent=1) + "\n", encoding="utf-8")
        print(f"wrote {args.sweep_hashes}")

    if args.sweep_only:
        problems = sweep(args.source, hashes)
        print("\n".join(problems) or "sweep clean")
        return 1 if problems else 0

    if args.out.exists():
        raise SystemExit(f"{args.out} exists; choose a new directory")
    from learnloop.db.copies import copy_tree_with_databases

    copy_tree_with_databases(args.source, args.out)
    new_cues = sanitize_files(args.out)
    sanitize_database(args.out / "state.sqlite", new_cues)
    problems = sweep(args.out, hashes)
    if problems:
        print("\n".join(problems))
        return 1
    print(f"sanitized {args.out}; sweep clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
