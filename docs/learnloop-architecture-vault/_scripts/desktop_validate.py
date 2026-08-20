#!/usr/bin/env python3
"""Strictly validate desktop-module coverage, metadata, links, and reproducibility."""

from __future__ import annotations

import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

import desktop_generate as generator


REPO_ROOT = generator.REPO_ROOT
VAULT_ROOT = generator.VAULT_ROOT
CATALOG_ROOT = generator.CATALOG_ROOT
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
    "generated_at",
    "tags",
}
MODULE_FRONTMATTER = {
    "module",
    "language",
    "area",
    "source_path",
    "source_worktree_state",
    "activation_kind",
    "activation_evidence",
}
MODULE_HEADINGS = {
    "Why this module exists",
    "Source facts",
    "Activation and status evidence",
    "Public API",
    "Internal implementation anchors",
    "Who imports or calls it",
    "Dependencies",
    "Larger desktop and workflow participation",
    "Tests that define behavior",
    "Modification guidance",
}
AREA_HEADINGS = {"Responsibility", "Child areas", "Direct modules", "Modification guidance", "Related notes"}
CATALOG_HEADINGS = {
    "Runtime bridge",
    "Area maps",
    "Status and evidence",
    "Find a desktop module",
    "How to change the desktop safely",
    "Maintenance",
}


def split_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("missing opening YAML delimiter")
    parts = text.split("---", 2)
    if len(parts) != 3:
        raise ValueError("missing closing YAML delimiter")
    data = YAML(typ="safe").load(parts[1])
    if not isinstance(data, dict):
        raise ValueError("frontmatter is not a mapping")
    return data, parts[2]


def headings(text: str) -> set[str]:
    result: set[str] = set()
    for match in re.finditer(r"^#{1,6}\s+(.+?)\s*$", text, re.MULTILINE):
        result.add(re.sub(r"[`*_]", "", match.group(1)).strip())
    return result


def prose_without_code(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    return re.sub(r"`[^`\n]*`", "", text)


def note_index() -> tuple[dict[str, Path], dict[str, list[Path]]]:
    by_path: dict[str, Path] = {}
    by_stem: dict[str, list[Path]] = defaultdict(list)
    for path in VAULT_ROOT.rglob("*.md"):
        key = path.relative_to(VAULT_ROOT).with_suffix("").as_posix()
        by_path[key] = path
        by_stem[path.stem].append(path)
    return by_path, dict(by_stem)


def resolve_wikilink(source: Path, target: str, by_path: dict[str, Path], by_stem: dict[str, list[Path]]) -> Path | None:
    target = target.strip()
    if not target:
        return source
    if target in by_path:
        return by_path[target]
    candidate = (source.parent / target).resolve()
    try:
        key = candidate.relative_to(VAULT_ROOT).as_posix()
    except ValueError:
        key = ""
    if key in by_path:
        return by_path[key]
    matches = by_stem.get(Path(target).name, [])
    return matches[0] if len(matches) == 1 else None


def validate_links(paths: list[Path]) -> tuple[list[str], int, int, int]:
    errors: list[str] = []
    wikilinks = 0
    fragments = 0
    markdown_links = 0
    by_path, by_stem = note_index()
    for path in paths:
        text = path.read_text(encoding="utf-8")
        prose = prose_without_code(text)
        for match in re.finditer(r"\[\[([^\]]+)\]\]", prose):
            inside = match.group(1)
            target_fragment = inside.split("|", 1)[0]
            target, separator, fragment = target_fragment.partition("#")
            destination = resolve_wikilink(path, target, by_path, by_stem)
            wikilinks += 1
            if destination is None:
                errors.append(f"{path.relative_to(REPO_ROOT)}: unresolved Wikilink [[{inside}]]")
                continue
            if not separator:
                continue
            fragments += 1
            target_text = destination.read_text(encoding="utf-8")
            if fragment.startswith("^"):
                if fragment not in target_text:
                    errors.append(f"{path.relative_to(REPO_ROOT)}: missing block #{fragment} in {destination.relative_to(REPO_ROOT)}")
            else:
                normalized = re.sub(r"[`*_]", "", fragment).strip()
                if normalized not in headings(target_text):
                    errors.append(f"{path.relative_to(REPO_ROOT)}: missing heading #{fragment} in {destination.relative_to(REPO_ROOT)}")

        for raw in re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", prose):
            target = raw.strip().split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            markdown_links += 1
            destination = (path.parent / target).resolve()
            if not destination.exists():
                errors.append(f"{path.relative_to(REPO_ROOT)}: missing Markdown target {raw}")
    return errors, wikilinks, fragments, markdown_links


def main() -> int:
    if sys.argv[1:]:
        print("usage: desktop_validate.py", file=sys.stderr)
        return 2
    pairs = generator.source_files()
    sources = [path.resolve() for path, _ in pairs]
    ts_sources = [path for path, language in pairs if language == "TypeScript"]
    rust_sources = [path for path, language in pairs if language == "Rust"]
    expected_modules = {
        generator.note_path(path.resolve(), language): path.resolve()
        for path, language in pairs
    }
    areas = sorted({generator.area_for(path, language) for path, language in pairs})
    expected_areas = {generator.area_note_path(area) for area in areas}
    catalog = CATALOG_ROOT / "Desktop Module Catalog.md"
    expected = set(expected_modules) | expected_areas | {catalog}
    actual = set(CATALOG_ROOT.rglob("*.md")) if CATALOG_ROOT.exists() else set()
    errors: list[str] = []
    audited_infos = generator.collect_infos()
    activation_counts: dict[str, int] = defaultdict(int)
    for info in audited_infos.values():
        activation_counts[info.activation_kind] += 1

    if len(ts_sources) != 102:
        errors.append(f"source inventory drift: expected 102 TypeScript/TSX files, found {len(ts_sources)}")
    if len(rust_sources) != 5:
        errors.append(f"source inventory drift: expected 5 authored Rust modules, found {len(rust_sources)}")
    for path in sorted(expected - actual):
        errors.append(f"missing expected note: {path.relative_to(REPO_ROOT)}")
    for path in sorted(actual - expected):
        errors.append(f"unexpected note: {path.relative_to(REPO_ROOT)}")

    covered_sources: dict[str, list[Path]] = defaultdict(list)
    yaml_checked = 0
    for path in sorted(actual):
        try:
            frontmatter, body = split_frontmatter(path)
        except Exception as error:
            errors.append(f"{path.relative_to(REPO_ROOT)}: invalid YAML frontmatter: {error}")
            continue
        yaml_checked += 1
        missing = REQUIRED_FRONTMATTER - set(frontmatter)
        if missing:
            errors.append(f"{path.relative_to(REPO_ROOT)}: missing frontmatter keys {sorted(missing)}")
        if frontmatter.get("status") != "current":
            errors.append(f"{path.relative_to(REPO_ROOT)}: status must be current")
        if frontmatter.get("generated") is not True:
            errors.append(f"{path.relative_to(REPO_ROOT)}: generated must be boolean true")
        if not isinstance(frontmatter.get("generated_at"), str):
            errors.append(f"{path.relative_to(REPO_ROOT)}: generated_at must be a quoted string")
        if not isinstance(frontmatter.get("source_commit_timestamp"), str):
            errors.append(f"{path.relative_to(REPO_ROOT)}: source_commit_timestamp must be a quoted string")
        if not isinstance(frontmatter.get("tags"), list) or not frontmatter.get("tags"):
            errors.append(f"{path.relative_to(REPO_ROOT)}: tags must be a non-empty list")
        source_paths = frontmatter.get("source_paths")
        if not isinstance(source_paths, list) or not source_paths:
            errors.append(f"{path.relative_to(REPO_ROOT)}: source_paths must be a non-empty list")
        else:
            for source_path in source_paths:
                if not isinstance(source_path, str) or not (REPO_ROOT / source_path).exists():
                    errors.append(f"{path.relative_to(REPO_ROOT)}: source path does not exist: {source_path!r}")

        note_type = frontmatter.get("type")
        if note_type == "desktop-module-reference":
            missing_module = MODULE_FRONTMATTER - set(frontmatter)
            if missing_module:
                errors.append(f"{path.relative_to(REPO_ROOT)}: missing module keys {sorted(missing_module)}")
            source_path = frontmatter.get("source_path")
            if isinstance(source_path, str):
                covered_sources[source_path].append(path)
                source = (REPO_ROOT / source_path).resolve()
                if source not in sources:
                    errors.append(f"{path.relative_to(REPO_ROOT)}: source_path is outside the live inventory: {source_path}")
                else:
                    audited = audited_infos[source]
                    if frontmatter.get("refactor_status") != audited.refactor_status:
                        errors.append(
                            f"{path.relative_to(REPO_ROOT)}: refactor_status does not match audited {audited.refactor_status}"
                        )
                    if frontmatter.get("activation_kind") != audited.activation_kind:
                        errors.append(
                            f"{path.relative_to(REPO_ROOT)}: activation_kind does not match audited {audited.activation_kind}"
                        )
                    if frontmatter.get("activation_evidence") != audited.activation_evidence:
                        errors.append(f"{path.relative_to(REPO_ROOT)}: activation_evidence is stale")
                    language = "TypeScript" if source.is_relative_to(generator.TS_ROOT) else "Rust"
                    if generator.note_path(source, language) != path:
                        errors.append(f"{path.relative_to(REPO_ROOT)}: note path does not mirror {source_path}")
            missing_headings = MODULE_HEADINGS - headings(body)
            if missing_headings:
                errors.append(f"{path.relative_to(REPO_ROOT)}: missing module headings {sorted(missing_headings)}")
        elif note_type == "desktop-area-map":
            if frontmatter.get("refactor_status") != "ACTIVE":
                errors.append(f"{path.relative_to(REPO_ROOT)}: current all-active area must be ACTIVE")
            missing_headings = AREA_HEADINGS - headings(body)
            if missing_headings:
                errors.append(f"{path.relative_to(REPO_ROOT)}: missing area headings {sorted(missing_headings)}")
        elif note_type == "map-of-content" and path == catalog:
            if frontmatter.get("refactor_status") != "ACTIVE":
                errors.append(f"{path.relative_to(REPO_ROOT)}: current all-active catalog must be ACTIVE")
            missing_headings = CATALOG_HEADINGS - headings(body)
            if missing_headings:
                errors.append(f"{path.relative_to(REPO_ROOT)}: missing catalog headings {sorted(missing_headings)}")
        else:
            errors.append(f"{path.relative_to(REPO_ROOT)}: unexpected type {note_type!r}")

    expected_source_paths = {source.relative_to(REPO_ROOT).as_posix() for source in sources}
    for source_path in sorted(expected_source_paths):
        notes = covered_sources.get(source_path, [])
        if len(notes) != 1:
            errors.append(f"source coverage must be 1:1 for {source_path}: found {len(notes)} notes")
    for source_path, notes in sorted(covered_sources.items()):
        if source_path not in expected_source_paths:
            errors.append(f"catalog covers unexpected source {source_path}")
        if len(notes) != 1:
            errors.append(f"duplicate source coverage for {source_path}: {len(notes)} notes")

    expected_activation_counts = {
        "entry-reachable build graph": 101,
        "compiler-implicit": 1,
        "native-entry-reachable": 5,
    }
    if dict(activation_counts) != expected_activation_counts:
        errors.append(
            f"activation audit drift: expected {expected_activation_counts}, found {dict(activation_counts)}"
        )
    status_counts: dict[str, int] = defaultdict(int)
    for info in audited_infos.values():
        status_counts[info.refactor_status] += 1
    if dict(status_counts) != {"ACTIVE": 107}:
        errors.append(f"lifecycle classification drift requires review: {dict(status_counts)}")

    link_errors, wikilinks, fragments, markdown_links = validate_links(sorted(actual))
    errors.extend(link_errors)
    reproducible = subprocess.run(
        [sys.executable, str(REPO_ROOT / "docs/learnloop-architecture-vault/_scripts/desktop_generate.py"), "--check"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    if reproducible.returncode != 0:
        errors.append("reproducibility check failed:\n" + reproducible.stderr.strip())

    if errors:
        print(f"Desktop catalog validation failed with {len(errors)} error(s):", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        "Desktop catalog validation passed: "
        f"{len(ts_sources)}/{len(ts_sources)} TypeScript/TSX + "
        f"{len(rust_sources)}/{len(rust_sources)} Rust modules, "
        f"{len(areas)} area maps, {yaml_checked} YAML documents, "
        "status audit ACTIVE=107 (101 entry-build + 1 compiler-implicit + 5 native-entry), "
        f"{wikilinks} Wikilinks ({fragments} fragments), "
        f"{markdown_links} Markdown/source links, reproducible byte-for-byte"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
