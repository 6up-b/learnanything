"""What other test files use from ``tests/test_figure_rich_rereview_fixes.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.db.stores import figures as store
from learnloop.figures import service as FS

from tests import rich_fixtures as RF


WRONG = RF.scene_output(declared={**RF.DECLARED, "claims": [
    {"kind": "equals", "function": "x", "expr": "exp(a*t)*sin(b*t)"}]})


def _base(rig, figure_id):
    with rig.repository.connection() as connection:
        return store.figure(connection, figure_id)


def _first_animation(rig):
    rig.build()
    rig.ingest.drain()
    (first,) = rig.listed()
    assert first["tier"] == "manim"
    return first


def _revision(rig, figure_id, note, *, different_kind=False):
    revision = FS.revision_request(rig.repository, _base(rig, figure_id), note)
    revision.different_kind = different_kind
    return revision
