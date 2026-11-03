#!/usr/bin/env python3
"""Validate generated module-reference coverage and Obsidian integrity."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML


REPO_ROOT = Path(__file__).resolve().parents[3]
VAULT_ROOT = REPO_ROOT / "docs" / "learnloop-architecture-vault"
CATALOG_ROOT = VAULT_ROOT / "Reference" / "Modules"
SOURCE_ROOTS = (REPO_ROOT / "src" / "learnloop", REPO_ROOT / "src" / "learnloop_sidecar")
REQUIRED_FRONTMATTER = {
    "title",
    "type",
    "status",
    "refactor_status",
    "version",
    "source_paths",
    "source_commit",
    "source_commit_timestamp",
    "generated",
    "tags",
}
REQUIRED_MODULE_HEADINGS = {
    "Why this module exists",
    "Source facts",
    "Public API",
    "Internal implementation anchors",
    "Who imports or calls it",
    "Dependencies",
    "Larger workflow participation",
    "Tests that define behavior",
    "Modification guidance",
}
ALLOWED_REFACTOR_STATUSES = {"ACTIVE", "COMPAT", "DORMANT", "EVALUATION"}
EXPECTED_EXPLICIT_STATUS = {
    "src/learnloop/scheduling/kinship_feature.py": "DORMANT",
    "src/learnloop/scheduling/prequential.py": "DORMANT",
    "src/learnloop/scheduling/intent_planner.py": "EVALUATION",
    "src/learnloop/scheduling/shadow_components.py": "EVALUATION",
    "src/learnloop/diagnosis/causal_diagnostic_selector.py": "EVALUATION",
    "src/learnloop/diagnosis/causal_selection_audit.py": "EVALUATION",
}
CANONICAL_PENDING_TARGETS = {
    "Architecture Overview",
    "Learning System",
    "AI Architecture",
    "State and Persistence",
    "Configuration",
    "Initialize a Vault",
    "Start a Learning Cycle",
    "Import Canonical Sources",
    "Process Model Output",
    "Inspect Persistent State",
}


def source_files() -> list[Path]:
    return sorted(path for root in SOURCE_ROOTS for path in root.rglob("*.py"))


def expected_note(source: Path) -> Path:
    return CATALOG_ROOT / source.relative_to(REPO_ROOT / "src").with_suffix(".md")


def package_names(sources: list[Path]) -> set[str]:
    packages: set[str] = set()
    for source in sources:
        parent = source.parent
        while parent != REPO_ROOT / "src":
            packages.add(".".join(parent.relative_to(REPO_ROOT / "src").parts))
            if parent in SOURCE_ROOTS:
                break
            parent = parent.parent
    return packages


def expected_moc(package: str) -> Path:
    return CATALOG_ROOT.joinpath(*package.split("."), "_package.md")


def tracked_files(root: Path, suffix: str) -> set[Path]:
    """Files under ``root`` with ``suffix`` that git tracks and that exist now.

    Raises when git can't answer (no git, or not a checkout), and the caller decides."""

    # A hook's GIT_DIR or GIT_INDEX_FILE would otherwise answer for another repository.
    env = {key: value for key, value in os.environ.items()
           if key not in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE")}
    listed = subprocess.run(["git", "ls-files", "-z", "--cached", "--", root.relative_to(REPO_ROOT).as_posix()],
                            cwd=REPO_ROOT, env=env, capture_output=True, check=True).stdout
    paths = (REPO_ROOT / name for name in listed.decode("utf-8").split("\0") if name)
    return {path for path in paths if path.suffix == suffix and path.is_file()}


def inventory_gaps() -> tuple[list[str], list[str]]:
    """``(missing, orphaned)``: the catalog's notes against the source tree, by path alone.

    Never opens a note, so an edit that makes a note's contents stale can't trip it; only a module
    with no note, or a note with no module. Only what git tracks, on both sides (Codex verify V2):
    an untracked probe, an ignored ``build/`` directory or a temporary note can't fail an unrelated
    suite. ``tests/test_module_catalog_inventory.py`` runs this on every full suite; :func:`main` is
    the deeper check, and still reads the whole tree."""

    sources = sorted(path for root in SOURCE_ROOTS for path in tracked_files(root, ".py"))
    expected = {expected_note(source) for source in sources}
    expected |= {expected_moc(package) for package in package_names(sources)}
    expected.add(CATALOG_ROOT / "Module Catalog.md")
    actual = tracked_files(CATALOG_ROOT, ".md")

    def relative(paths: set[Path]) -> list[str]:
        return sorted(path.relative_to(REPO_ROOT).as_posix() for path in paths)

    return relative(expected - actual), relative(actual - expected)


def split_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("missing opening YAML delimiter")
    try:
        _, raw_yaml, body = text.split("---", 2)
    except ValueError as error:
        raise ValueError("missing closing YAML delimiter") from error
    yaml = YAML(typ="safe")
    data = yaml.load(raw_yaml)
    if not isinstance(data, dict):
        raise ValueError("frontmatter is not a mapping")
    return data, body


def headings(body: str) -> set[str]:
    result: set[str] = set()
    for match in re.finditer(r"^#{1,6}\s+(.+?)\s*$", body, re.MULTILINE):
        heading = re.sub(r"[`*_]", "", match.group(1)).strip()
        result.add(heading)
    return result


def vault_note_index() -> tuple[dict[str, Path], dict[str, list[Path]]]:
    by_path: dict[str, Path] = {}
    by_stem: dict[str, list[Path]] = defaultdict(list)
    for path in VAULT_ROOT.rglob("*.md"):
        relative = path.relative_to(VAULT_ROOT).with_suffix("").as_posix()
        by_path[relative] = path
        by_stem[path.stem].append(path)
    return by_path, dict(by_stem)


def resolve_wikilink(
    source_note: Path,
    raw_target: str,
    by_path: dict[str, Path],
    by_stem: dict[str, list[Path]],
) -> Path | None:
    target = raw_target.strip()
    if not target:
        return source_note
    if target in by_path:
        return by_path[target]
    relative_target = (source_note.parent / target).resolve()
    try:
        relative_key = relative_target.relative_to(VAULT_ROOT).as_posix()
    except ValueError:
        relative_key = ""
    if relative_key in by_path:
        return by_path[relative_key]
    matches = by_stem.get(Path(target).name, [])
    if len(matches) == 1:
        return matches[0]
    return None


def validate_wikilinks(
    paths: list[Path], *, allow_pending_canonical: bool
) -> tuple[list[str], int, int, int]:
    errors: list[str] = []
    checked = 0
    fragment_checked = 0
    pending_canonical = 0
    by_path, by_stem = vault_note_index()
    pattern = re.compile(r"\[\[([^\]]+)\]\]")
    for path in paths:
        text = path.read_text(encoding="utf-8")
        # Obsidian does not interpret link-shaped type annotations inside code
        # spans/fences as Wikilinks (for example ``dict[str, list[list[int]]]``).
        prose = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        prose = re.sub(r"`[^`\n]*`", "", prose)
        for match in pattern.finditer(prose):
            inside = match.group(1)
            target_and_fragment = inside.split("|", 1)[0]
            if "#" in target_and_fragment:
                raw_target, fragment = target_and_fragment.split("#", 1)
            else:
                raw_target, fragment = target_and_fragment, ""
            target_path = resolve_wikilink(path, raw_target, by_path, by_stem)
            checked += 1
            if target_path is None:
                if allow_pending_canonical and raw_target in CANONICAL_PENDING_TARGETS:
                    pending_canonical += 1
                    continue
                errors.append(
                    f"{path.relative_to(REPO_ROOT)}: unresolved Wikilink [[{inside}]]"
                )
                continue
            if not fragment:
                continue
            fragment_checked += 1
            target_text = target_path.read_text(encoding="utf-8")
            if fragment.startswith("^"):
                if fragment not in target_text:
                    errors.append(
                        f"{path.relative_to(REPO_ROOT)}: missing block {fragment} in {target_path.relative_to(REPO_ROOT)}"
                    )
            else:
                target_body_headings = headings(target_text)
                normalized = re.sub(r"[`*_]", "", fragment).strip()
                if normalized not in target_body_headings:
                    errors.append(
                        f"{path.relative_to(REPO_ROOT)}: missing heading #{fragment} in {target_path.relative_to(REPO_ROOT)}"
                    )
    return errors, checked, fragment_checked, pending_canonical


def validate_markdown_links(paths: list[Path]) -> tuple[list[str], int]:
    errors: list[str] = []
    checked = 0
    pattern = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for raw_target in pattern.findall(text):
            target = raw_target.strip().split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            checked += 1
            destination = (path.parent / target).resolve()
            if not destination.exists():
                errors.append(
                    f"{path.relative_to(REPO_ROOT)}: missing Markdown target {raw_target}"
                )
    return errors, checked


def main() -> int:
    allow_pending_canonical = "--allow-pending-canonical" in sys.argv[1:]
    unknown_args = set(sys.argv[1:]) - {"--allow-pending-canonical"}
    if unknown_args:
        print(f"unknown arguments: {sorted(unknown_args)}", file=sys.stderr)
        return 2
    sources = source_files()
    packages = package_names(sources)
    module_paths = [expected_note(source) for source in sources]
    moc_paths = [expected_moc(package) for package in sorted(packages)]
    catalog_path = CATALOG_ROOT / "Module Catalog.md"
    expected_paths = module_paths + moc_paths + [catalog_path]
    errors: list[str] = []

    missing_notes = [path for path in expected_paths if not path.is_file()]
    errors.extend(f"missing expected note: {path.relative_to(REPO_ROOT)}" for path in missing_notes)

    actual_module_notes: dict[str, list[Path]] = defaultdict(list)
    yaml_checked = 0
    for path in sorted(CATALOG_ROOT.rglob("*.md")):
        try:
            frontmatter, body = split_frontmatter(path)
        except Exception as error:
            errors.append(f"{path.relative_to(REPO_ROOT)}: invalid YAML frontmatter: {error}")
            continue
        yaml_checked += 1
        missing_keys = REQUIRED_FRONTMATTER - set(frontmatter)
        if missing_keys:
            errors.append(
                f"{path.relative_to(REPO_ROOT)}: missing frontmatter keys {sorted(missing_keys)}"
            )
        if frontmatter.get("status") != "current":
            errors.append(f"{path.relative_to(REPO_ROOT)}: status is not current")
        if frontmatter.get("refactor_status") not in ALLOWED_REFACTOR_STATUSES:
            errors.append(
                f"{path.relative_to(REPO_ROOT)}: invalid refactor_status "
                f"{frontmatter.get('refactor_status')!r}"
            )
        if frontmatter.get("generated") is not True:
            errors.append(f"{path.relative_to(REPO_ROOT)}: generated must be boolean true")
        if not isinstance(frontmatter.get("source_commit_timestamp"), str):
            errors.append(
                f"{path.relative_to(REPO_ROOT)}: source_commit_timestamp must be a quoted string"
            )
        if not isinstance(frontmatter.get("tags"), list) or not frontmatter.get("tags"):
            errors.append(f"{path.relative_to(REPO_ROOT)}: tags must be a non-empty list")
        if frontmatter.get("type") == "module-reference":
            source_path = frontmatter.get("source_path")
            if not isinstance(source_path, str):
                errors.append(f"{path.relative_to(REPO_ROOT)}: missing scalar source_path")
            else:
                actual_module_notes[source_path].append(path)
                source = REPO_ROOT / source_path
                if not source.is_file():
                    errors.append(f"{path.relative_to(REPO_ROOT)}: source_path does not exist: {source_path}")
                elif expected_note(source) != path:
                    errors.append(
                        f"{path.relative_to(REPO_ROOT)}: note path does not mirror {source_path}"
                    )
                expected_status = EXPECTED_EXPLICIT_STATUS.get(source_path)
                if expected_status and frontmatter.get("refactor_status") != expected_status:
                    errors.append(
                        f"{path.relative_to(REPO_ROOT)}: explicit source status must be "
                        f"{expected_status}, got {frontmatter.get('refactor_status')!r}"
                    )
                if source_path.startswith("src/learnloop/sim/") and frontmatter.get(
                    "refactor_status"
                ) != "EVALUATION":
                    errors.append(
                        f"{path.relative_to(REPO_ROOT)}: simulation module must be EVALUATION"
                    )
            missing_headings = REQUIRED_MODULE_HEADINGS - headings(body)
            if missing_headings:
                errors.append(
                    f"{path.relative_to(REPO_ROOT)}: missing headings {sorted(missing_headings)}"
                )
            if "^module-purpose" not in body:
                errors.append(f"{path.relative_to(REPO_ROOT)}: missing purpose block id")
            if "> [!info] Generated source reference" not in body:
                errors.append(f"{path.relative_to(REPO_ROOT)}: missing generated-note banner")
            test_section = body.partition("## Tests that define behavior")[2].partition(
                "## Modification guidance"
            )[0]
            # Test cases are listed under their test file's bullet: a name repeated within one file's
            # list is a duplicate; the same name in two test files is two tests (followups batch 5, J).
            for test_file_block in re.split(r"^- ", test_section, flags=re.MULTILINE)[1:]:
                test_cases = re.findall(r"^  - `([^`]+)`\s*$", test_file_block, re.MULTILINE)
                if len(test_cases) != len(set(test_cases)):
                    errors.append(
                        f"{path.relative_to(REPO_ROOT)}: duplicate test-case anchors in test section"
                    )
                    break
            if (
                frontmatter.get("refactor_status") == "DORMANT"
                and frontmatter.get("workflows")
            ):
                errors.append(
                    f"{path.relative_to(REPO_ROOT)}: dormant module claims live workflows"
                )

    expected_sources = {source.relative_to(REPO_ROOT).as_posix() for source in sources}
    actual_sources = set(actual_module_notes)
    for source_path in sorted(expected_sources - actual_sources):
        errors.append(f"source has no module note: {source_path}")
    for source_path in sorted(actual_sources - expected_sources):
        errors.append(f"module note points outside live inventory: {source_path}")
    for source_path, paths in sorted(actual_module_notes.items()):
        if len(paths) != 1:
            errors.append(
                f"source has {len(paths)} module notes: {source_path}: "
                + ", ".join(str(path.relative_to(REPO_ROOT)) for path in paths)
            )

    existing_expected = [path for path in expected_paths if path.is_file()]
    wiki_errors, wiki_checked, fragment_checked, pending_canonical = validate_wikilinks(
        existing_expected, allow_pending_canonical=allow_pending_canonical
    )
    markdown_errors, markdown_checked = validate_markdown_links(existing_expected)
    errors.extend(wiki_errors)
    errors.extend(markdown_errors)

    print(f"Module source coverage: {len(actual_sources & expected_sources)}/{len(expected_sources)} unique")
    print(f"Package maps: {sum(path.is_file() for path in moc_paths)}/{len(moc_paths)}")
    print(f"Catalog notes with valid YAML: {yaml_checked}/{len(list(CATALOG_ROOT.rglob('*.md')))}")
    resolved_wikilinks = wiki_checked - len(wiki_errors) - pending_canonical
    print(
        f"Wikilinks resolved: {resolved_wikilinks}/{wiki_checked} "
        f"({fragment_checked} fragment links checked)"
    )
    if pending_canonical:
        print(
            f"Canonical links awaiting sibling-note generation: {pending_canonical} "
            "(allowed by --allow-pending-canonical)"
        )
    print(f"Markdown source/test links resolved: {markdown_checked - len(markdown_errors)}/{markdown_checked}")
    if errors:
        print(f"FAILED with {len(errors)} issue(s):", file=sys.stderr)
        for error in errors[:100]:
            print(f"- {error}", file=sys.stderr)
        if len(errors) > 100:
            print(f"- … {len(errors) - 100} more", file=sys.stderr)
        return 1
    print("PASS: 1:1 coverage, YAML, generated sections, Wikilinks, block/header links, and file links are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
