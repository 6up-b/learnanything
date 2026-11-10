"""The provenance stamp for generated notes: ``Reference/_generated.md``, one row per generator.

Generated notes carry no commit, timestamp or worktree state of their own. When they
did, nearly every regeneration rewrote hundreds of notes whose facts hadn't changed
(router speed 2: 499 of 593), and a reviewer had to read past them.

Each generator (module, desktop, db) records the commit its own notes were generated
from, and rewrites only its own row. With one shared stamp, any generator moved it, so
running only the db generator after a commit vouched for module notes that lacked the
commit's new function (arc A close review). ``generate_all.py`` runs all three.

The commit is the newest one that changed a generator input, not HEAD. With HEAD, the
commit that lands a regeneration would itself make the next regeneration on a clean
tree differ, so "regenerate and expect no diff" could never hold. Inputs that differ
from that commit (tracked edits or untracked files) are named in the generator's row,
because its notes then describe sources no commit has.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
VAULT_ROOT = REPO_ROOT / "docs" / "learnloop-architecture-vault"
NOTE_PATH = VAULT_ROOT / "Reference" / "_generated.md"
NOTE_TITLE = "Generated Reference Provenance"

# Everything the three generators read. A path missing here means a change to it
# regenerates notes without moving the recorded commit.
INPUT_PATHS = (
    "src",
    "tests",
    "scripts",
    "migrations",
    "fixtures",
    "apps/learnloop-tauri",
    "docs/learnloop-architecture-vault/_scripts",
)

GENERATORS = (
    ("module_generate.py", "Reference/Modules/ (module notes, package maps, Module Catalog)"),
    ("desktop_generate.py", "Reference/Desktop/ (TypeScript and Rust notes, area maps, Desktop Module Catalog)"),
    (
        "db_generate_reference.py",
        "Reference/Database/Tables/, Reference/Configuration/Fields/, Database Catalog, "
        "Configuration Field Catalog",
    ),
)


def _git(*args: str, strip: bool = True) -> str:
    output = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, check=True, text=True, capture_output=True
    ).stdout
    return output.strip() if strip else output


def inputs_provenance() -> tuple[str, str, list[str]]:
    """Return the newest commit touching an input, its timestamp, and the inputs that differ from HEAD."""

    commit, timestamp = _git("log", "-1", "--format=%H%x09%cI", "--", *INPUT_PATHS).split("\t", 1)
    # Unstripped: porcelain's two status columns start with a space for an
    # unstaged change, and stripping the output cut the first path's first letter.
    status = _git("status", "--porcelain=v1", "--untracked-files=normal", "--", *INPUT_PATHS, strip=False)
    dirty = sorted(line[3:] for line in status.splitlines() if line.strip())
    return commit, timestamp, dirty


def recorded() -> dict[str, dict]:
    """Each generator's row as the note holds it now: ``{script: {source_commit, source_commit_timestamp,
    uncommitted_inputs}}``; a generator that never wrote its row (or a note in the old one-stamp form) is absent."""

    # Parsed by hand from the block render() writes (the module generator uses the standard library only).
    if not NOTE_PATH.is_file():
        return {}
    match = re.match(r"---\n(.*?)\n---\n", NOTE_PATH.read_text(encoding="utf-8"), re.S)
    known = {script for script, _notes in GENERATORS}
    rows: dict[str, dict] = {}
    row: dict | None = None
    inside = False
    for line in match.group(1).splitlines() if match else []:
        if not line.startswith(" "):
            inside = line == "generators:"
        elif inside and (header := re.fullmatch(r"  (\S+):", line)):
            row = rows.setdefault(header.group(1), {}) if header.group(1) in known else None
        elif inside and row is not None and (field := re.fullmatch(r"    (\w+): (.+)", line)):
            row[field.group(1)] = json.loads(field.group(2))
        elif inside and row is not None and (item := re.fullmatch(r"      - (.+)", line)):
            row.setdefault("uncommitted_inputs", []).append(json.loads(item.group(1)))
    return rows


def render(rows: dict[str, dict]) -> str:
    q = json.dumps  # a JSON string is a valid YAML double-quoted scalar, whatever the path holds
    front = ["---", f"title: {q(NOTE_TITLE)}", 'type: "generated-provenance"', 'status: "current"',
             'version: "2.0.0"', "generated: true", "generators:"]
    table = ["| Generator | Writes | Source commit | Commit timestamp | Inputs since that commit |",
             "|---|---|---|---|---|"]
    warnings: list[str] = []
    for script, notes in GENERATORS:
        row = rows.get(script)
        if row is None:
            table.append(f"| `_scripts/{script}` | {notes} | never recorded | | |")
            continue
        dirty = list(row.get("uncommitted_inputs") or [])
        front += [f"  {script}:", f"    source_commit: {q(row['source_commit'])}",
                  f"    source_commit_timestamp: {q(row['source_commit_timestamp'])}"]
        front += ["    uncommitted_inputs:", *(f"      - {q(path)}" for path in dirty)] if dirty \
            else ["    uncommitted_inputs: []"]
        since = "none" if not dirty else f"{len(dirty)} changed or untracked path(s), listed below"
        table.append(f"| `_scripts/{script}` | {notes} | `{row['source_commit']}` | "
                     f"`{row['source_commit_timestamp']}` | {since} |")
        if dirty:
            warnings += [f"> [!warning] `{script}` ran on uncommitted sources",
                         "> These inputs differed from its commit. Commit them and regenerate before landing.",
                         "", *(f"- `{path}`" for path in dirty), ""]
    front += ["source_paths:", *(f"  - {q(path)}" for path in INPUT_PATHS),
              "tags:", '  - "docs/generated"', '  - "learnloop/reference"', "---"]
    body = [
        "",
        f"# {NOTE_TITLE}",
        "",
        "Each generator records here the commit its notes were generated from, instead of in each note. "
        "It is the newest commit that changed a generator input (listed in `source_paths`) when that "
        "generator last ran, so committing a regeneration doesn't move it. A generator rewrites only its "
        "own row: running one alone never vouches for another's notes. ^generated-commit",
        "",
        *table,
        "",
        *warnings,
        "`_scripts/generate_all.py` runs all three. A regeneration on a clean tree changes nothing; one "
        "after a source change touches only the notes whose facts changed, plus a generator's row here "
        "when its recorded commit moves.",
        "",
        "Hand-written notes keep their own `source_commit_timestamp`; see [[Documentation Conventions]].",
        "",
    ]
    return "\n".join(front + body)


def render_for(script: str) -> str:
    """The note with ``script``'s row recording the current sources and every other row as it was."""

    if script not in {name for name, _notes in GENERATORS}:
        raise ValueError(f"unknown generator: {script}")
    commit, timestamp, dirty = inputs_provenance()
    rows = recorded()
    rows[script] = {"source_commit": commit, "source_commit_timestamp": timestamp, "uncommitted_inputs": dirty}
    return render(rows)


def write(script: str) -> None:
    """Record ``script``'s (the calling generator's) commit; the other generators' rows stay as they were."""

    text = render_for(script)
    NOTE_PATH.parent.mkdir(parents=True, exist_ok=True)
    NOTE_PATH.write_text(text, encoding="utf-8")


STAMP_KEYS = ("source_commit", "source_commit_timestamp", "source_worktree_state")


def stamp_errors(frontmatter: dict[str, object], body: str, label: str) -> list[str]:
    """Errors for a generated note that carries a per-note stamp again."""

    errors = [f"{label}: generated note carries per-note `{key}`" for key in STAMP_KEYS if key in frontmatter]
    for row in ("| Source commit |", "| Commit timestamp |", "| Worktree state |"):
        if row in body:
            errors.append(f"{label}: generated note carries a per-note `{row.strip('| ')}` row")
    return errors


def note_errors() -> list[str]:
    """Errors in ``_generated.md`` itself: present, and a full commit hash for every generator."""

    label = NOTE_PATH.relative_to(REPO_ROOT).as_posix()
    if not NOTE_PATH.is_file():
        return [f"{label}: missing; run _scripts/generate_all.py"]
    rows = recorded()
    errors: list[str] = []
    for script, _notes in GENERATORS:
        row = rows.get(script)
        if row is None:
            errors.append(f"{label}: {script} never recorded its commit; run it (or _scripts/generate_all.py)")
        elif not re.fullmatch(r"[0-9a-f]{40}", str(row.get("source_commit", ""))):
            errors.append(f"{label}: {script}'s source_commit must be a full Git hash")
    return errors
