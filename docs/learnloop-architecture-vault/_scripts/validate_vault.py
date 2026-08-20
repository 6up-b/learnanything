#!/usr/bin/env python3
"""Validate Obsidian metadata and internal links for this documentation vault."""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML


VAULT = Path(__file__).resolve().parents[1]
REPO = VAULT.parents[1]
LINK_RE = re.compile(r"!?\[\[([^\]]+)\]\]")
FENCED_CODE_RE = re.compile(r"^```.*?^```\s*$", re.MULTILINE | re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)
BLOCK_RE = re.compile(r"(?:^|\s)\^([A-Za-z0-9_-]+)\s*$", re.MULTILINE)


def frontmatter(path: Path, text: str) -> dict[str, Any]:
    if not text.startswith("---\n"):
        raise ValueError("missing opening YAML frontmatter delimiter")
    try:
        raw, _body = text[4:].split("\n---\n", 1)
    except ValueError as exc:
        raise ValueError("missing closing YAML frontmatter delimiter") from exc
    value = YAML(typ="safe").load(raw) or {}
    if not isinstance(value, dict):
        raise ValueError("frontmatter must be a mapping")
    return value


def norm(value: str) -> str:
    value = re.sub(r"[`*_~]", "", value)
    value = re.sub(r"\s+#+$", "", value.strip())
    return re.sub(r"\s+", " ", value).casefold()


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def main() -> int:
    notes = sorted(VAULT.rglob("*.md"))
    errors: list[str] = []
    texts: dict[Path, str] = {}
    metadata: dict[Path, dict[str, Any]] = {}
    lookup: dict[str, set[Path]] = defaultdict(set)
    relative_lookup: dict[str, Path] = {}
    link_graph: dict[Path, set[Path]] = defaultdict(set)

    for path in notes:
        text = path.read_text(encoding="utf-8")
        texts[path] = text
        relative = path.relative_to(VAULT).with_suffix("")
        relative_lookup[relative.as_posix().casefold()] = path
        try:
            data = frontmatter(path, text)
        except Exception as exc:  # noqa: BLE001 - collect every docs error
            errors.append(f"{path.relative_to(VAULT)}: {exc}")
            continue
        metadata[path] = data
        for required in ("title", "status", "source_paths", "source_commit_timestamp", "tags"):
            if required not in data:
                errors.append(f"{path.relative_to(VAULT)}: missing `{required}` property")
        if "doc_version" not in data and "version" not in data:
            errors.append(f"{path.relative_to(VAULT)}: missing `doc_version` or `version`")
        if not isinstance(data.get("source_commit_timestamp"), str):
            errors.append(
                f"{path.relative_to(VAULT)}: `source_commit_timestamp` must be a quoted string"
            )
        if not isinstance(data.get("tags"), list) or not data.get("tags"):
            errors.append(f"{path.relative_to(VAULT)}: `tags` must be a non-empty list")
        if not isinstance(data.get("source_paths"), list):
            errors.append(f"{path.relative_to(VAULT)}: `source_paths` must be a list")
        if "generated" in data and data.get("generated") is not True:
            errors.append(f"{path.relative_to(VAULT)}: `generated` must be boolean true")
        keys = [path.stem, str(data.get("title") or ""), *as_list(data.get("aliases"))]
        for key in keys:
            if key.strip():
                lookup[norm(key)].add(path)

    checked_links = 0
    for source, text in texts.items():
        # Obsidian does not resolve WikiLink-like syntax inside code spans.
        linkable_text = FENCED_CODE_RE.sub("", text)
        linkable_text = INLINE_CODE_RE.sub("", linkable_text)
        for raw in LINK_RE.findall(linkable_text):
            checked_links += 1
            # Markdown tables escape the alias separator as ``\|``; Obsidian
            # still treats it as the normal WikiLink alias delimiter.
            target_spec = re.split(r"\\?\|", raw, maxsplit=1)[0].strip()
            target_name, marker, fragment = target_spec.partition("#")
            if not target_name:
                targets = {source}
            elif "/" in target_name:
                key = target_name.removesuffix(".md").lstrip("/").casefold()
                resolved = relative_lookup.get(key)
                targets = {resolved} if resolved else set()
            else:
                targets = lookup.get(norm(target_name), set())
            targets.discard(None)
            location = source.relative_to(VAULT)
            if not targets:
                errors.append(f"{location}: unresolved WikiLink [[{raw}]]")
                continue
            if len(targets) > 1:
                choices = ", ".join(str(p.relative_to(VAULT)) for p in sorted(targets))
                errors.append(f"{location}: ambiguous WikiLink [[{raw}]] -> {choices}")
                continue
            target = next(iter(targets))
            link_graph[source].add(target)
            if marker and fragment:
                target_text = texts[target]
                if fragment.startswith("^"):
                    blocks = set(BLOCK_RE.findall(target_text))
                    if fragment[1:] not in blocks:
                        errors.append(
                            f"{location}: missing block `{fragment}` in [[{raw}]]"
                        )
                else:
                    headings = {norm(item) for item in HEADING_RE.findall(target_text)}
                    if norm(fragment) not in headings:
                        errors.append(
                            f"{location}: missing heading `{fragment}` in [[{raw}]]"
                        )

    home = VAULT / "Home.md"
    if home not in metadata:
        errors.append("Home.md: missing graph entry point")
        reachable: set[Path] = set()
    else:
        reachable = {home}
        pending = [home]
        while pending:
            current = pending.pop()
            for target in link_graph.get(current, set()):
                if target not in reachable:
                    reachable.add(target)
                    pending.append(target)
    expected_reachable = {
        path
        for path in metadata
        if not path.relative_to(VAULT).as_posix().startswith("_meta/Templates/")
    }
    orphaned = sorted(expected_reachable - reachable)
    if orphaned:
        preview = ", ".join(str(path.relative_to(VAULT)) for path in orphaned[:20])
        suffix = f" (and {len(orphaned) - 20} more)" if len(orphaned) > 20 else ""
        errors.append(
            f"knowledge graph has {len(orphaned)} note(s) unreachable from Home.md: "
            f"{preview}{suffix}"
        )
    checked_sources = 0
    for note, data in metadata.items():
        for raw_source in as_list(data.get("source_paths")):
            # Aggregate/generated pseudo-sources are documented evidence labels.
            if not raw_source or raw_source.startswith(("aggregate", "workspace:")):
                continue
            checked_sources += 1
            candidate = REPO / raw_source
            if not candidate.exists():
                errors.append(
                    f"{note.relative_to(VAULT)}: source path does not exist: {raw_source}"
                )

    if errors:
        print(f"Vault validation failed with {len(errors)} error(s):", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        f"Vault validation passed: {len(notes)} notes, "
        f"{checked_links} WikiLinks/fragments, {checked_sources} source paths, "
        f"{len(reachable)}/{len(expected_reachable)} non-template notes reachable from Home."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
