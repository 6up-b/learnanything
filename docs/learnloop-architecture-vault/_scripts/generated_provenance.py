"""The one provenance stamp for every generated note: ``Reference/_generated.md``.

Generated notes carry no commit, timestamp or worktree state of their own. When they
did, nearly every regeneration rewrote hundreds of notes whose facts hadn't changed
(router speed 2: 499 of 593), and a reviewer had to read past them. The three
generators (module, desktop, db) all write this one note with the same content.

The commit is the newest one that changed a generator input, not HEAD. With HEAD, the
commit that lands a regeneration would itself make the next regeneration on a clean
tree differ, so "regenerate and expect no diff" could never hold. Inputs that differ
from that commit (tracked edits or untracked files) are named in the note, because the
notes then describe sources no commit has.
"""

from __future__ import annotations

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


def render() -> str:
    commit, timestamp, dirty = inputs_provenance()
    state = "clean" if not dirty else "uncommitted changes"
    lines = [
        "---",
        f'title: "{NOTE_TITLE}"',
        'type: "generated-provenance"',
        'status: "current"',
        'version: "1.0.0"',
        f'source_commit: "{commit}"',
        f'source_commit_timestamp: "{timestamp}"',
        f'source_worktree_state: "{state}"',
        "generated: true",
        "source_paths:",
        *(f'  - "{path}"' for path in INPUT_PATHS),
        "tags:",
        '  - "docs/generated"',
        '  - "learnloop/reference"',
        "---",
        "",
        f"# {NOTE_TITLE}",
        "",
        "Every generated note under `Reference/` was generated from the sources at one commit, recorded "
        "here once instead of in each note. It is the newest commit that changed a generator input "
        "(listed in `source_paths`), so committing a regeneration doesn't move it. ^generated-commit",
        "",
        "| Fact | Value |",
        "|---|---|",
        f"| Source commit | `{commit}` |",
        f"| Commit timestamp | `{timestamp}` |",
        f"| Inputs since that commit | {'none' if not dirty else f'{len(dirty)} changed or untracked path(s), listed below'} |",
        "",
    ]
    if dirty:
        lines += [
            "> [!warning] Generated from uncommitted sources",
            "> These inputs differed from the commit above. Commit them and regenerate before landing.",
            "",
            *(f"- `{path}`" for path in dirty),
            "",
        ]
    lines += [
        "## Generators",
        "",
        "| Generator | Writes |",
        "|---|---|",
        *(f"| `_scripts/{script}` | {notes} |" for script, notes in GENERATORS),
        "",
        "Each generator rewrites this note with the same content. A regeneration on a clean tree "
        "changes nothing; one after a source change touches only the notes whose facts changed, "
        "plus this note when the recorded commit moves.",
        "",
        "Hand-written notes keep their own `source_commit_timestamp`; see "
        "[[Documentation Conventions]].",
        "",
    ]
    return "\n".join(lines)


def write() -> None:
    NOTE_PATH.parent.mkdir(parents=True, exist_ok=True)
    NOTE_PATH.write_text(render(), encoding="utf-8")


STAMP_KEYS = ("source_commit", "source_commit_timestamp", "source_worktree_state")


def stamp_errors(frontmatter: dict[str, object], body: str, label: str) -> list[str]:
    """Errors for a generated note that carries a per-note stamp again."""

    errors = [f"{label}: generated note carries per-note `{key}`" for key in STAMP_KEYS if key in frontmatter]
    for row in ("| Source commit |", "| Commit timestamp |", "| Worktree state |"):
        if row in body:
            errors.append(f"{label}: generated note carries a per-note `{row.strip('| ')}` row")
    return errors


def note_errors() -> list[str]:
    """Errors in ``_generated.md`` itself: present, and naming a full commit hash."""

    label = NOTE_PATH.relative_to(REPO_ROOT).as_posix()
    if not NOTE_PATH.is_file():
        return [f"{label}: missing; run any generator"]
    text = NOTE_PATH.read_text(encoding="utf-8")
    if not re.search(r'^source_commit: "[0-9a-f]{40}"$', text, re.M):
        return [f"{label}: source_commit must be a full Git hash"]
    return []
