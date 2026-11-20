"""Each protection surface's exam set, named in one table (``exam_material.SURFACE_SETS``), held to the matrix.

The protection matrix (``tests/test_protection_surface_matrix.py``) pins what every surface answers per fixture;
the table says which set each surface reads. Where the sets part, the two must agree: an exam member with no marks
(fixture 1) and an exam unit of a textbook (fixture 2) are all exam material and not held out, so a surface that reads
all exam material withholds or refuses them, and one that reads the held-out partition, or no exam set, shows them.
A held-out unit (fixture 3) is in both sets, so only a surface that reads no exam set shows it.

The matrix's table is read from its file (a test file never imports another), so a column added there without a row
here fails.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from learnloop.content.sources import exam_material as EM

MATRIX = Path(__file__).resolve().parent / "test_protection_surface_matrix.py"

#: Matrix column -> its row of ``SURFACE_SETS``.
SURFACE_OF = {
    "TE": "teaching", "MR": "teaching", "RA": "reader_ask", "PS": "reader_presets", "CK": "reader_checks",
    "GU": "reader_guidance", "FI": "figures", "IP": "figure_prebuild_items", "SC": "section_coverage",
    "SQ": "quote", "MC": "mcp_passages", "CI": "canonical_import", "BS": "book_solution", "RI": "reader_import",
    "LF": "leakage_floor", "RF": "reserved_questions", "RT": "routine_serving", "OT": "routine_serving",
    "PK": "practice_pick", "SS": "session_serve", "DV": "device_eligibility", "PF": "device_eligibility",
    "EX": "exposure", "EH": "exposure_with_held_out", "CO": "cold_administration", "SE": "serve_eligibility",
    "LP": "learner_protection", "AP": "learner_protection", "AD": "ad_forecast", "LC": "learner_protection",
    "PW": "phone", "PG": "phone", "PI": "phone", "RV": "phone", "GP": "phone", "PA": "phone", "PH": "phone",
    "AS": "phone", "DO": "phone_dose_offer", "ML": "mcp_library", "LA": "library_ask", "OR": "library_result",
    "LJ": "library_result", "PT": "library_tutor_pins", "TJ": "library_result", "TB": "section_coverage",
    "LS": "library_search", "DH": "reader_history", "FB": "followup_feedback", "FD": "followup_door",
    "KY": "item_detail", "BG": "book_guide", "CM": "compare", "RD": "reader_render", "RN": "reader_import",
    "CN": "canonical_import",
}

#: Rows no matrix column asks: a surface's second decision, which its column's target does not reach.
SECOND_DECISIONS = {
    "library_ask_anchor": "LA: the matrix's ask has no anchor; it searches for the target",
    "library_tutor_refusal": "PT: a held-out pin refuses (R on 3.held); the column's exam-only cells are the drop",
}

#: Columns whose cells say nothing of their set: the MCP library lists every title and only labels a card with
#: all exam material.
LABELS_ONLY = {"ML"}

#: Fixtures 1 and 2: all exam material, not held out.
EXAM_NOT_HELD_OUT = ("1.paper", "2.exam", "2.split-exam", "6.1canonical", "6.1block", "6.2canonical", "6.2block")
#: Fixture 3: held out, so in both sets.
HELD_OUT_ROWS = ("3.held", "6.3canonical", "6.3block")
#: The reserved-question floor asks an item row about its stem (the item union's exam reason) and a span row about
#: the span's text (the leakage floor's held-out text, LF's row): only its item rows ask its own row's question.
ITEM_ROWS_ONLY = {"RF"}


def _matrix() -> tuple[list[str], dict[tuple[str, str], str], frozenset[str]]:
    tree = ast.parse(MATRIX.read_text(encoding="utf-8"))
    values: dict[str, ast.expr] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            values[node.targets[0].id] = node.value
    table = ast.literal_eval(values["EXPECTED_TABLE"])
    not_driven_call = values["NOT_DRIVEN"]
    assert isinstance(not_driven_call, ast.Call) and len(not_driven_call.args) == 1
    not_driven = frozenset(ast.literal_eval(not_driven_call.args[0]))
    lines = [line for line in table.strip().splitlines() if line.strip()]
    columns = [cell for cell in lines[0].split("|", 1)[1].split() if cell != "|"]
    cells: dict[tuple[str, str], str] = {}
    for line in lines[1:]:
        row, rest = line.split("|", 1)
        values_in_row = [cell for cell in rest.split() if cell != "|"]
        for column, value in zip(columns, values_in_row, strict=True):
            cells[(row.strip(), column)] = value
    return columns, cells, not_driven


COLUMNS, CELLS, NOT_DRIVEN = _matrix()
#: The columns whose cells are each asked of the production function.
ASKED = [column for column in COLUMNS if column not in NOT_DRIVEN and column not in LABELS_ONLY]


def test_every_matrix_surface_has_a_row_and_every_row_a_surface() -> None:
    assert set(SURFACE_OF) == set(COLUMNS)
    assert set(SURFACE_OF.values()) | set(SECOND_DECISIONS) == set(EM.SURFACE_SETS)
    assert set(EM.SURFACE_SETS.values()) <= {EM.ALL_EXAM, EM.HELD_OUT, EM.NO_EXAM_SET}


def _cells(column: str, rows: tuple[str, ...]) -> dict[str, str]:
    if column in ITEM_ROWS_ONLY:
        rows = tuple(row for row in rows if row.startswith("6."))
    return {row: CELLS[(row, column)] for row in rows if CELLS[(row, column)] != "-"}


@pytest.mark.parametrize("column", ASKED)
def test_a_surfaces_row_agrees_with_its_matrix_cells_where_the_sets_part(column: str) -> None:
    chosen = EM.SURFACE_SETS[SURFACE_OF[column]]
    shown = {row for row, cell in _cells(column, EXAM_NOT_HELD_OUT).items() if cell == "S"}
    asked = set(_cells(column, EXAM_NOT_HELD_OUT))
    assert asked, f"{column} has no cell where the sets part"
    if chosen == EM.ALL_EXAM:
        assert not shown, f"{column} reads all exam material yet shows {sorted(shown)}"
    else:
        assert shown == asked, f"{column} reads {chosen} yet withholds {sorted(asked - shown)}"


@pytest.mark.parametrize("column", ASKED)
def test_held_out_material_is_withheld_by_every_surface_that_reads_an_exam_set(column: str) -> None:
    chosen = EM.SURFACE_SETS[SURFACE_OF[column]]
    cells = _cells(column, HELD_OUT_ROWS)
    shown = {row for row, cell in cells.items() if cell == "S"}
    if chosen == EM.NO_EXAM_SET:
        assert shown == set(cells), f"{column} reads no exam set yet withholds {sorted(set(cells) - shown)}"
    else:
        assert not shown, f"{column} reads {chosen} yet shows {sorted(shown)}"


# --- the readers the table selects ------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def exam_member(tmp_path_factory):
    """A vault whose only protected source is an exam member with no marks (``ext_exam``)."""

    from tests.source_retrieval_fakes import build_retrieval_vault, loaded

    paths, repository = build_retrieval_vault(tmp_path_factory.mktemp("surface_sets") / "vault", embeddings=False)
    return loaded(paths), repository


def test_a_held_out_row_reads_the_held_out_partition_and_an_exam_row_all_exam_material(exam_member) -> None:
    vault, repository = exam_member
    assert not EM.surface_material(vault, repository, "reader_ask").covers("ext_exam")
    assert EM.surface_material(vault, repository, "phone").covers("ext_exam")
    assert EM.surface_exam_material(vault, repository, "canonical_import").covers("ext_exam")
    assert not EM.surface_material(vault, repository, "teaching").covers("ext_book")


def test_a_surface_cannot_read_a_set_its_row_does_not_name(exam_member) -> None:
    vault, repository = exam_member
    with pytest.raises(ValueError, match="reader_import"):
        EM.surface_exam_material(vault, repository, "reader_import")
    with pytest.raises(ValueError, match="device_eligibility"):
        EM.surface_material(vault, repository, "device_eligibility")
    with pytest.raises(KeyError):
        EM.surface_material(vault, repository, "no_such_surface")
