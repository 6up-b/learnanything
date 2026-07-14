"""Unit-derivation tests for the markdown normalizer (normalizers.markdown_to_ir).

Covers the level-2 (##) fallback: a single ``#`` title with meaningful ``##``
sections must yield one unit per level-2 section (plus a leading intro unit for
content before the first ``##``), while multi-``#`` files and structureless text
keep their existing behavior.
"""

from __future__ import annotations

from pathlib import Path

from learnloop.ingest.extractors.normalizers import markdown_to_ir

_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "proto_sources"


def _units(markdown: str, *, title: str | None = None):
    ir = markdown_to_ir(markdown, title=title, extractor_name="text")
    return ir.units


def test_single_hash_with_level2_sections_yields_intro_plus_level2_units():
    markdown = (
        "# Linear Algebra\n"
        "\n"
        "A short preamble before any subsection.\n"
        "\n"
        "## Vectors\n"
        "\n"
        "Vectors live in a space.\n"
        "\n"
        "## Matrices\n"
        "\n"
        "Matrices act on vectors.\n"
        "\n"
        "More on matrices.\n"
    )
    units = _units(markdown, title="Linear Algebra")

    assert [u.label for u in units] == ["(intro)", "vectors", "matrices"]
    assert [u.unit_id for u in units] == ["u1", "u2", "u3"]
    assert [u.ordinal for u in units] == [1, 2, 3]
    assert [u.locator["path"] for u in units] == [
        "root/linear-algebra",
        "root/linear-algebra/vectors",
        "root/linear-algebra/matrices",
    ]
    # Every block landed in exactly one unit, ordering preserved.
    all_spans = [span for u in units for span in u.span_ids]
    assert all_spans == sorted(all_spans, key=lambda s: int(s[1:]))
    # Distinct semantic hashes → selections can actually distinguish the units.
    assert len({u.semantic_hash for u in units}) == 3


def test_single_hash_no_intro_when_first_content_is_a_section():
    markdown = (
        "# Title\n"
        "## Alpha\n"
        "\n"
        "Alpha body.\n"
        "\n"
        "## Beta\n"
        "\n"
        "Beta body.\n"
    )
    units = _units(markdown, title="Title")

    assert [u.label for u in units] == ["alpha", "beta"]
    assert [u.unit_id for u in units] == ["u1", "u2"]


def test_multi_hash_file_unchanged():
    markdown = (_FIXTURES / "proto-boundary-cases.md").read_text()
    units = _units(markdown, title="Boundary Cases")

    # Three level-1 headings → three level-1 units, level-1 slugs as labels.
    assert [u.label for u in units] == [
        "notation",
        "inner-products-and-orthogonality",
        "summary",
    ]
    assert [u.locator["path"] for u in units] == [
        "root/notation",
        "root/inner-products-and-orthogonality",
        "root/summary",
    ]


def test_no_headings_yields_single_document_unit():
    markdown = (
        "Just some prose with no headings at all.\n"
        "\n"
        "A second paragraph, still no structure.\n"
    )
    units = _units(markdown, title="Notes")

    assert len(units) == 1
    assert units[0].unit_id == "u1"
    assert units[0].label == "Notes"
    assert units[0].locator["path"] == "root"


def test_extractor_version_is_two():
    ir = markdown_to_ir("# X\n\nbody\n", title="X", extractor_name="text")
    assert ir.extractor_version == "2"
