"""UX Phase 3 (docs/specs/ux_learnloop_v1.md §7.1, §10 3.3): Today's one
backend addition, ``workbench.open_problems`` -- every source's open problems
for "Pick up a thread". A pure read: open problems only (set-aside and
submitted ones are not threads), newest first, each with the source it opens
in; a problem whose source cannot be found is left out; switched off it
refuses like every workbench RPC. Fakes only (docs/reviews/ux-phase3.md).
"""

from __future__ import annotations

import pytest

from learnloop_sidecar.errors import SidecarError

from tests.test_reader_inquiry_status import table_counts
from tests.test_reader_workbench_rw2a import (  # noqa: F401 - grader is a fixture
    EXTRACTION,
    OTHER_ITEM,
    _call,
    _context,
    _open,
    _step,
    _submit,
    _vault,
    grader,
)


@pytest.fixture
def sources(monkeypatch):
    """Map extractions to sources (the RW2a harness has no extraction runs)."""

    import learnloop_sidecar.handlers.workbench as handler

    mapping = {EXTRACTION: "src_book", "ext_other": "src_paper"}
    monkeypatch.setattr(handler, "_source_id", lambda _repository, extraction_id: mapping.get(extraction_id))
    return mapping


def test_open_problems_lists_every_sources_open_problems_newest_first_with_their_source(tmp_path, grader, sources):
    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    first = _open(ctx)
    _step(ctx, first["sessionId"], "a", bodyMd="one")
    _step(ctx, first["sessionId"], "b", bodyMd="two")
    other = _open(ctx, practiceItemId=OTHER_ITEM, extractionId="ext_other", spanIds=["p1"])
    _step(ctx, other["sessionId"], "c", bodyMd="three")
    dropped = _open(ctx, practiceItemId="pi_eigen_001", extractionId="ext_other")
    _call(ctx, "workbench.abandon", {"sessionId": dropped["sessionId"]})
    before = table_counts(repository)

    problems = _call(ctx, "workbench.open_problems", {})["problems"]

    assert [row["sessionId"] for row in problems] == [other["sessionId"], first["sessionId"]]
    by_id = {row["sessionId"]: row for row in problems}
    assert by_id[first["sessionId"]]["sourceId"] == "src_book"
    assert by_id[first["sessionId"]]["stepCount"] == 2
    assert by_id[other["sessionId"]]["sourceId"] == "src_paper"
    assert by_id[other["sessionId"]]["spanIds"] == ["p1"]
    assert all(row["status"] == "open" for row in problems)
    # A pure read.
    assert table_counts(repository) == before


def test_a_submitted_problem_and_one_without_a_source_are_not_threads(tmp_path, grader, sources):
    paths, _repository = _vault(tmp_path)
    ctx = _context(paths.root)
    done = _open(ctx)
    _step(ctx, done["sessionId"], "a", bodyMd="A = U Sigma V^T")
    _submit(ctx, done["sessionId"])
    orphan = _open(ctx, practiceItemId=OTHER_ITEM, extractionId="ext_gone")
    _step(ctx, orphan["sessionId"], "b", bodyMd="x")

    assert _call(ctx, "workbench.open_problems", {})["problems"] == []


def test_switched_off_open_problems_refuses_like_every_workbench_rpc(tmp_path):
    paths, _repository = _vault(tmp_path, config="[workbench]\nenabled = false")
    ctx = _context(paths.root)
    with pytest.raises(SidecarError) as refused:
        _call(ctx, "workbench.open_problems", {})
    assert refused.value.code == "workbench_disabled"
