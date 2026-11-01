"""RW5d P2b, the Manim half: the Codex re-review's service findings, each reproduced first.

* F13: "try a different kind of figure" on an animation is its own input:
  its hash differs from the ordinary correction with the same note, so it
  never takes that correction's pending job or its stored animation, and
  re-runs the tier choice.
* F14: a correction of an animation whose rich job ended with a stored
  failure keeps the earlier animation and lists a failed line (the reason,
  and "try again", which asks the rich author afresh).

Fakes only: the authors, the renderer and the function runner are injected;
no model, Manim or bubblewrap runs.
"""

from __future__ import annotations

from learnloop.db.stores import figures as store
from learnloop.figures import service as FS
from tests import rich_fixtures as RF
from tests.figure_fixtures import EXTRACTION, flagship, rows
from tests.test_figure_rich_job import WHY, _Rig

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


# --- F13 ----------------------------------------------------------------------


def test_a_different_kind_hashes_apart_from_the_ordinary_correction(tmp_path, monkeypatch):
    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY)])
    first = _first_animation(rig)
    ordinary = _revision(rig, first["figure_id"], "red")
    other = _revision(rig, first["figure_id"], "red", different_kind=True)
    context = FS.source_context(rig.vault, rig.repository, ordinary)
    assert FS.request_hash(ordinary, context, None) != FS.request_hash(other, context, None)
    # Every request without the flag hashes exactly as before it existed (stored figures stay reusable).
    from learnloop.ai.execution import content_key

    key = {"spec_version": FS.S.SPEC_VERSION, "prompt_version": FS.R.author_prompt_version(),
           "extraction_id": ordinary.extraction_id, "span_ids": list(ordinary.span_ids), "region": None,
           "origin": FS.REUSE_ORIGIN, "passage": context.passage, "around": context.around, "image_sha256": None,
           "supersedes_id": ordinary.supersedes_id, "revision_note": "red"}
    assert FS.request_hash(ordinary, context, None) == content_key(key)


def test_a_different_kind_never_takes_the_pending_ordinary_correction(tmp_path, monkeypatch):
    """F13: before the fix the "different kind" request returned the
    ordinary correction's pending animation job (one hash for both)."""

    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY), flagship(kind="illustrative")])
    first = _first_animation(rig)
    pending = rig.build(_revision(rig, first["figure_id"], "red"))
    assert pending.rich["state"] == "pending"
    outcome = rig.build(_revision(rig, first["figure_id"], "red", different_kind=True))
    assert outcome.rich is None and outcome.view is not None and outcome.view["tier"] == "grammar"
    assert rig.author.calls == 2  # the tier choice ran again


def test_a_different_kind_never_reuses_the_ordinary_corrections_animation(tmp_path, monkeypatch):
    """F13: before the fix, once the ordinary correction was stored, the
    "different kind" request reused that animation without a tier choice."""

    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY), flagship(kind="illustrative")])
    first = _first_animation(rig)
    rig.build(_revision(rig, first["figure_id"], "red"))
    rig.ingest.drain()
    outcome = rig.build(_revision(rig, first["figure_id"], "red", different_kind=True))
    assert outcome.reused is False and outcome.view["tier"] == "grammar"
    assert rig.author.calls == 2


# --- F14 ----------------------------------------------------------------------


def test_a_failed_animation_correction_keeps_the_earlier_version_and_says_so(tmp_path, monkeypatch):
    """F14: before the fix the correction's pending line vanished when its
    job stored a failure, with no reason and no retry."""

    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY)],
               [RF.scene_output(), WRONG, WRONG, RF.scene_output(scene=RF.SCENE.replace("color=BLUE", "color=RED"))])
    first = _first_animation(rig)
    asked = rig.build(_revision(rig, first["figure_id"], "red please"))
    job_id = asked.rich["rich_job_id"]
    rig.ingest.drain()
    (shown,) = rig.listed()
    assert shown["figure_id"] == first["figure_id"]  # the earlier animation stays
    (line,) = FS.rich_pending(rig.vault, rig.repository, EXTRACTION)
    assert line["state"] == "failed" and line["rich_job_id"] == job_id and line["anchor_span_id"] == "p3"
    assert line["reason"]
    failed = [row for row in rows(rig.repository, "interactive_figures") if row["verification"] == "failed"]
    assert len(failed) == 1 and failed[0]["supersedes_id"] == first["figure_id"]

    # "Try again": the same correction asked afresh (a new generation), by the rich author.
    retry = FS.rich_revision_retry(rig.vault, rig.repository, job_id)
    assert retry is not None and retry.supersedes_id == first["figure_id"] and retry.revision_note == "red please"
    again = rig.build(retry)
    assert again.rich["state"] == "pending" and again.rich["rich_job_id"] != job_id
    (line,) = FS.rich_pending(rig.vault, rig.repository, EXTRACTION)
    assert line["state"] == "pending" and line["rich_job_id"] == again.rich["rich_job_id"]
    rig.ingest.drain()
    assert FS.rich_pending(rig.vault, rig.repository, EXTRACTION) == []
    (shown,) = rig.listed()
    assert shown["supersedes_id"] == first["figure_id"] and shown["verification"] == "illustrative"
    contexts = rig.rich_author.contexts
    assert contexts[-1]["request_id"] != contexts[1]["request_id"]  # asked afresh, not the failed checkpoint
    assert rig.author.calls == 1  # a correction never goes back to the tier choice


def test_a_later_correction_replaces_the_failed_line(tmp_path, monkeypatch):
    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY)], [RF.scene_output(), WRONG, WRONG])
    first = _first_animation(rig)
    failed_job = rig.build(_revision(rig, first["figure_id"], "red please")).rich["rich_job_id"]
    rig.ingest.drain()
    assert [line["state"] for line in FS.rich_pending(rig.vault, rig.repository, EXTRACTION)] == ["failed"]
    newer = rig.build(_revision(rig, first["figure_id"], "blue please"))
    (line,) = FS.rich_pending(rig.vault, rig.repository, EXTRACTION)
    assert line["state"] == "pending" and line["rich_job_id"] == newer.rich["rich_job_id"] != failed_job
    # A job that is not a failed correction is never retried as one.
    assert FS.rich_revision_retry(rig.vault, rig.repository, newer.rich["rich_job_id"]) is None


def test_a_failed_correction_of_a_fuller_version_says_so_too(tmp_path, monkeypatch):
    rig = _Rig(tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))],
               [RF.scene_output(), WRONG, WRONG])
    quick = rig.build().view
    rig.ingest.drain()
    (line,) = rig.listed()
    old_rich = line["fuller"]["figure"]["figure_id"]
    job_id = rig.build(_revision(rig, old_rich, "red please")).rich["rich_job_id"]
    rig.ingest.drain()
    (line,) = rig.listed()
    assert line["figure_id"] == quick["figure_id"] and line["fuller"]["figure"]["figure_id"] == old_rich
    (failed,) = FS.rich_pending(rig.vault, rig.repository, EXTRACTION)
    assert failed["state"] == "failed" and failed["rich_job_id"] == job_id and failed["reason"]
