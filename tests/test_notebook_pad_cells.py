"""A pad's marimo cells (spec §10.4 `cell`, §11.5): written, edited, moved and removed with the pad ops every block
uses; the notebook the runtime opens is generated from them (the same cells give the same bytes), written as a
derived file under the vault, with a revision that follows the cells' shape, not their code; a cell's code is never
learner text. The runtime is a recording fake here; the real sandbox is tests/test_notebook_runtime_sandbox.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from learnloop.notebook_runtime import adapter
from learnloop_sidecar.errors import SidecarError
from tests.helpers import create_basic_vault
from tests.notebook_runtime_helpers import RecordingRuntime
from tests.reading_path_fixtures import call, context

PAD = "pad_cells_one"


@pytest.fixture
def ctx(tmp_path):
    made = context(create_basic_vault(tmp_path / "vault").root)
    made.notebook_runtime = RecordingRuntime()
    call(made, "pad.apply", {"clientId": "c", "seq": 1, "padId": PAD, "ops": [{"op": "create_pad", "kind": "named", "title": "cells"}]})
    made.seq = 1
    yield made
    made.notebook_runtime = None


def apply(ctx, *ops):
    ctx.seq += 1
    return call(ctx, "pad.apply", {"clientId": "c", "seq": ctx.seq, "padId": PAD, "ops": list(ops)})


def insert(ctx, block_id, code, key, provenance="learner"):
    return apply(ctx, {"op": "insert_block", "blockId": block_id, "versionId": f"v_{block_id}_1", "kind": "cell",
                       "provenance": provenance, "positionKey": key, "bodyMd": code})


def head(ctx, block_id):
    return next(block for block in call(ctx, "pad.get", {"padId": PAD})["blocks"] if block["blockId"] == block_id)


def open_pad(ctx, pad_id=PAD):
    reply = call(ctx, "notebook.open", {"owner": f"pad:{pad_id}"})
    return reply, ctx.notebook_runtime.opens[-1]


def test_cells_are_pad_blocks_with_append_only_versions_and_their_provenance(ctx):
    insert(ctx, "cell_a", "x = 2", "a0")
    insert(ctx, "cell_b", "y = x * 3\ny", "a1", provenance="tutor")
    apply(ctx, {"op": "edit_block", "blockId": "cell_b", "expectedHead": head(ctx, "cell_b")["headVersionId"],
                "versionId": "v_cell_b_2", "bodyMd": "y = x * 4\ny"})
    blocks = call(ctx, "pad.get", {"padId": PAD})["blocks"]
    assert [(b["kind"], b["provenance"], b["bodyMd"]) for b in blocks] == [
        ("cell", "learner", "x = 2"), ("cell", "tutor", "y = x * 4\ny")]  # an edit keeps the tutor's provenance
    with ctx.repository.connection() as connection:
        from learnloop.db.stores import pad_reads

        assert [v["body_md"] for v in pad_reads.chain(connection, "cell_b")] == ["y = x * 3\ny", "y = x * 4\ny"]


def test_the_notebook_is_generated_from_the_pads_cells_in_pad_order(ctx):
    insert(ctx, "cell_b", "y = x * 3\ny", "a1")
    insert(ctx, "cell_a", "import marimo as mo\nx = mo.ui.slider(1, 9)\nx", "a0")
    apply(ctx, {"op": "insert_block", "blockId": "note_1", "versionId": "v_note_1", "kind": "text", "provenance": "learner",
                "positionKey": "a05", "bodyMd": "not a cell"})
    reply, opened = open_pad(ctx)
    source = opened["source"].decode()
    expected = adapter.notebook_from_cells([(adapter.cell_name("cell_a"), "import marimo as mo\nx = mo.ui.slider(1, 9)\nx"),
                                            (adapter.cell_name("cell_b"), "y = x * 3\ny")])
    assert source == expected and "not a cell" not in source
    assert opened["owner"] == f"pad:{PAD}" and opened["revision"]
    assert reply["padCells"] == {"cell_a": "c_cell_a", "cell_b": "c_cell_b"}  # keys kept as the block ids
    assert reply["cellRuns"] == {"c_one": {"status": "idle", "ms": 1.0, "error": False}}  # names kept too
    derived = Path(ctx.vault_root) / ".learnloop" / "notebooks" / "pads" / f"{PAD}.py"
    assert derived.read_bytes() == opened["source"]


def test_the_same_cells_give_the_same_bytes_and_revision(ctx):
    insert(ctx, "cell_a", "x = 2", "a0")
    _, first = open_pad(ctx)
    _, second = open_pad(ctx)
    assert first["source"] == second["source"] and first["revision"] == second["revision"]


def test_editing_code_keeps_the_revision_and_a_new_shape_makes_a_new_one(ctx):
    insert(ctx, "cell_a", "x = 2", "a0")
    _, base = open_pad(ctx)
    apply(ctx, {"op": "edit_block", "blockId": "cell_a", "expectedHead": head(ctx, "cell_a")["headVersionId"],
                "versionId": "v_cell_a_2", "bodyMd": "x = 5"})
    _, edited = open_pad(ctx)
    assert edited["revision"] == base["revision"] and edited["source"] != base["source"] and b"x = 5" in edited["source"]
    insert(ctx, "cell_b", "y = x", "a1")
    _, grown = open_pad(ctx)
    assert grown["revision"] != base["revision"]
    apply(ctx, {"op": "move_block", "blockId": "cell_b", "expectedHead": head(ctx, "cell_b")["headVersionId"],
                "versionId": "v_cell_b_2", "positionKey": "Zz"})
    _, moved = open_pad(ctx)
    assert moved["revision"] != grown["revision"]
    assert moved["source"].index(b"def c_cell_b") < moved["source"].index(b"def c_cell_a")
    apply(ctx, {"op": "remove_block", "blockId": "cell_b", "expectedHead": head(ctx, "cell_b")["headVersionId"],
                "versionId": "v_cell_b_3"})
    _, shrunk = open_pad(ctx)
    assert shrunk["revision"] == base["revision"] and b"c_cell_b" not in shrunk["source"]


def test_a_pad_without_cells_or_without_a_pad_or_a_lesson_without_a_path_is_refused(ctx):
    with pytest.raises(SidecarError) as caught:
        open_pad(ctx)
    assert caught.value.code == "notebook_no_cells"
    with pytest.raises(SidecarError) as caught:
        open_pad(ctx, "pad_nowhere")
    assert caught.value.code == "pad_not_found"
    with pytest.raises(SidecarError) as caught:
        call(ctx, "notebook.open", {"owner": "lesson:l1"})
    assert caught.value.code == "notebook_path_invalid"
    assert ctx.notebook_runtime.opens == []


def test_a_cells_code_is_never_learner_text(ctx):
    from learnloop.db.stores import pad_reads
    from learnloop.pads import emission

    insert(ctx, "cell_a", "# why does softmax use exp?\nx = 2", "a0")
    with ctx.repository.connection() as connection:
        assert emission.emittable(pad_reads.head(connection, "cell_a")) is False
    assert "cell" not in emission.EMITTED


def test_the_generated_notebook_loads_as_its_cells(ctx, tmp_path):
    pytest.importorskip("marimo")
    insert(ctx, "cell_a", "x = 2", "a0")
    insert(ctx, "cell_b", "if True:\n\ty = x * 3\n\tif y:\n\t    y", "a1")  # tab-indented, as typed
    insert(ctx, "cell_c", "def (", "a2")
    _, opened = open_pad(ctx)
    path = tmp_path / "pad.py"
    path.write_bytes(opened["source"])
    from marimo._ast.load import load_app

    app = load_app(str(path))
    cells = {cell.name: cell for _id, cell in app._cell_manager.valid_cells()}
    assert sorted(cells) == ["c_cell_a", "c_cell_b"]  # the unparsable cell loads as marimo's own error cell
    assert sorted(cells["c_cell_b"].refs) == ["x"]


def test_cell_names_are_identifiers_unique_per_block():
    assert adapter.cell_name("blk_01ABC") == "c_blk_01abc"
    assert adapter.cell_name("a-b") != adapter.cell_name("a_b") and adapter.cell_name("a-b").isidentifier()
    assert adapter.notebook_from_cells([("c_x", "x = 1")]) == adapter.notebook_from_cells([("c_x", "x = 1")])


def test_the_derived_notebook_never_follows_a_link_out_of_the_vault(ctx, tmp_path):
    """A link at `.learnloop/notebooks/pads` (or any component) is refused, and a link planted at the old fixed
    temporary name is never written through."""

    import os

    insert(ctx, "cell_a", "x = 2", "a0")
    outside = tmp_path / "outside"
    outside.mkdir()
    pads = Path(ctx.vault_root) / ".learnloop" / "notebooks" / "pads"
    pads.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(outside, pads)
    with pytest.raises(SidecarError) as caught:
        open_pad(ctx)
    assert caught.value.code == "notebook_path_invalid" and list(outside.iterdir()) == []
    pads.unlink()
    pads.mkdir()
    victim = tmp_path / "victim.txt"
    victim.write_text("MINE")
    target = f"{adapter.cell_name(PAD)[2:]}.py"
    os.symlink(victim, pads / f".{target}.{os.getpid()}.tmp")
    os.symlink(victim, pads / target)
    open_pad(ctx)
    assert victim.read_text() == "MINE"
    assert not (pads / target).is_symlink() and (pads / target).read_bytes().startswith(b"import marimo")
