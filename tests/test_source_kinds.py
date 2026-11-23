"""A source kind is one row of ``learnloop.ingest.source_kinds.SOURCE_KINDS``.

The desktop's kind table (``apps/learnloop-tauri/src/api/sourceKinds.ts``) is generated from the rows;
``python tests/test_source_kinds.py --write`` rewrites it after a row changes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import get_args

import pytest

from learnloop.ingest.resolution import resolve_source
from learnloop.ingest.source_kinds import SOURCE_KINDS, UNKNOWN_KIND, SourceCategory, source_kind

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "apps" / "learnloop-tauri" / "src" / "api" / "sourceKinds.ts"


def render_typescript() -> str:
    rows = [
        {
            "category": kind.category,
            "label": kind.label,
            "noun": kind.noun,
            "extensions": list(kind.extensions),
            "urlExtensions": list(kind.url_extensions),
        }
        for kind in SOURCE_KINDS.values()
    ]
    body = ",\n".join("  " + json.dumps(row, ensure_ascii=False) for row in rows)
    return (
        "// GENERATED from learnloop.ingest.source_kinds.SOURCE_KINDS by `python tests/test_source_kinds.py --write`.\n"
        "// Edit the table, never this file: tests/test_source_kinds.py fails when they differ.\n"
        "\n"
        f"export const SOURCE_KINDS = [\n{body}\n] as const;\n"
        "\n"
        'export type SourceCategory = (typeof SOURCE_KINDS)[number]["category"];\n'
        "\n"
        "export type SourceKindRow = (typeof SOURCE_KINDS)[number];\n"
        "\n"
        "/** Every local file suffix the classifier reads as some kind (lower case, with the dot). */\n"
        "export const SOURCE_FILE_EXTENSIONS: readonly string[] = SOURCE_KINDS.flatMap((kind) => kind.extensions);\n"
        "\n"
        "export function sourceKindRow(category: string | null | undefined): SourceKindRow | null {\n"
        "  return SOURCE_KINDS.find((kind) => kind.category === category) ?? null;\n"
        "}\n"
    )


def test_every_category_has_one_row_in_the_literal_order():
    assert list(SOURCE_KINDS) == list(get_args(SourceCategory))
    assert all(category == kind.category for category, kind in SOURCE_KINDS.items())


@pytest.mark.parametrize("category", list(SOURCE_KINDS))
def test_each_suffix_classifies_as_its_kind(category):
    kind = SOURCE_KINDS[category]
    for extension in kind.extensions:
        assert resolve_source(f"/books/name{extension}").category == category
        assert resolve_source(f"/books/NAME{extension.upper()}").category == category
    for extension in kind.url_extensions:
        assert resolve_source(f"https://example.org/name{extension}?x=1").category == category


def test_no_suffix_names_two_kinds():
    seen: dict[str, str] = {}
    for kind in SOURCE_KINDS.values():
        for extension in kind.extensions:
            assert extension not in seen, (extension, seen.get(extension), kind.category)
            seen[extension] = kind.category


def test_an_unnamed_category_reads_as_text_and_is_called_a_book():
    for category in (None, "", "website", "bogus"):
        kind = source_kind(category)
        assert kind is UNKNOWN_KIND
        assert (kind.reader, kind.noun, kind.suggested_role, kind.confident_role, kind.document) == (
            "text", "book", "reference", False, False,
        )


def test_the_desktop_table_is_generated_from_the_rows():
    assert GENERATED.read_text(encoding="utf-8") == render_typescript(), (
        "run `python tests/test_source_kinds.py --write`"
    )


if __name__ == "__main__":
    if sys.argv[1:] == ["--write"]:
        GENERATED.write_text(render_typescript(), encoding="utf-8")
        print(f"wrote {GENERATED.relative_to(ROOT)}")
    else:
        sys.exit("usage: python tests/test_source_kinds.py --write")
