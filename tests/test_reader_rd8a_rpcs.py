"""The pen-and-ink RPCs (spec §3.4, §18.1): registered, desktop only, params refusing extra fields, replies
versioned; ``ink.transcribe`` a polled, cancellable job that belongs to its vault, answering at once with strokes
already read. Every model is a fake."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from learnloop_sidecar.handlers.ink import INK_RPCS
from learnloop_sidecar.errors import SidecarError
from tests.helpers import create_basic_vault
from tests.ink_helpers import STROKES, WAIT, close_and_wait, glm_local, ink_jobs, wait_reading
from tests.reading_path_fixtures import call, context

MINIMAL = {
    "ink.save": {"clientId": "c", "seq": 1, "owner": {"blockId": "b1"}, "inkId": "i",
                 "strokes": [{"strokeId": "s", "points": [[1, 2, 0, 0.5, 0, 0]]}],
                 "pointerMeta": {"pointerType": "pen"}},
    "ink.erase": {"clientId": "c", "seq": 1, "owner": {"extractionId": "e"}, "eraseId": "x", "strokeIds": ["s"]},
    "ink.list": {"padId": "p"},
    "ink.transcribe": {"inkId": "i"},
    "ink.transcribe_job": {"jobId": "j"},
    "ink.transcribe_cancel": {"jobId": "j"},
}


@pytest.fixture
def contexts(tmp_path, monkeypatch):
    """A context on a new vault whose GLM-OCR is the local backend, faked at its transport (``glm=False``: none set
    up): ``(ctx, fake)``."""

    made, fakes = [], []

    def make(name="vault", *, text="$x$", hold=False, glm=True):
        root = create_basic_vault(tmp_path / name).root
        fake = glm_local(monkeypatch, root, text, hold=hold) if glm else None
        if fake is not None:
            fakes.append(fake)
        ctx = context(root)
        made.append(ctx)
        return ctx, fake

    yield make
    for fake in fakes:
        fake.release.set()
    for ctx in made:
        close_and_wait(ctx)


def _ink_block(ctx, *, seq=1):
    call(ctx, "pad.apply", {"clientId": "c", "seq": seq, "padId": "p", "ops": [
        {"op": "create_pad", "kind": "ink"},
        {"op": "insert_block", "blockId": "b1", "kind": "ink", "provenance": "ink_transcription",
         "positionKey": "a0"}]})
    return call(ctx, "ink.save", {"clientId": "c", "seq": seq + 1, "owner": {"blockId": "b1"}, "inkId": "ink_1",
                                  "strokes": [{"strokeId": s["stroke_id"], "points": s["points"]} for s in STROKES],
                                  "pointerMeta": {"pointerType": "pen", "devicePixelRatio": 1}})


def test_the_rpcs_are_registered_and_desktop_only():
    from learnloop_mobile.allowlist import ALLOWLIST
    from learnloop_sidecar.registry import METHOD_REGISTRY

    assert INK_RPCS == tuple(MINIMAL)
    assert all(name in METHOD_REGISTRY and name not in ALLOWLIST for name in INK_RPCS)


@pytest.mark.parametrize("name", tuple(MINIMAL))
def test_params_refuse_an_extra_field(name):
    from learnloop_sidecar.registry import METHOD_REGISTRY

    model = METHOD_REGISTRY[name].params_model
    model.model_validate(MINIMAL[name])
    with pytest.raises(ValidationError):
        model.model_validate({**MINIMAL[name], "unexpected": True})


def test_nested_models_refuse_extra_fields_and_repeated_stroke_ids():
    from learnloop_sidecar.registry import METHOD_REGISTRY

    model = METHOD_REGISTRY["ink.save"].params_model
    for bad in ({"owner": {"blockId": "b1", "x": 1}}, {"pointerMeta": {"pointerType": "pen", "x": 1}},
                {"strokes": [{"strokeId": "s", "points": [[1, 2, 0, 0.5, 0, 0]], "x": 1}]},
                {"strokes": [{"strokeId": "s", "points": [[1, 2, 0, 0.5, 0, 0]]}] * 2}):
        with pytest.raises(ValidationError):
            model.model_validate({**MINIMAL["ink.save"], **bad})
    with pytest.raises(ValidationError):
        METHOD_REGISTRY["ink.list"].params_model.model_validate({"padId": "p", "sourceId": "s"})


def test_save_and_list_replies_are_versioned_and_camel_cased(contexts):
    ctx, _fake = contexts()
    saved = _ink_block(ctx)
    assert saved["version"] == 1 and saved["inkId"] == "ink_1" and saved["appliedSeq"] == 2
    assert saved["results"] == [{"status": "ok", "duplicate": False}]
    listed = call(ctx, "ink.list", {"padId": "p"})
    assert listed["version"] == 1 and [owner["ownerId"] for owner in listed["owners"]] == ["b1"]
    assert [stroke["strokeId"] for stroke in listed["owners"][0]["strokes"]] == ["s1", "s2", "s3"]
    with pytest.raises(SidecarError) as missing:
        call(ctx, "ink.list", {"padId": "nope"})
    assert missing.value.code == "pad_not_found"


def test_a_reading_is_a_job_and_strokes_already_read_answer_at_once(contexts):
    ctx, reader = contexts()
    _ink_block(ctx)
    started = call(ctx, "ink.transcribe", {"inkId": "ink_1"})
    assert started["version"] == 1 and started["jobId"].startswith("ink_")
    done = wait_reading(ctx, started["jobId"])
    assert (done["status"], done["done"], done["result"]["latexMd"], done["result"]["applied"]) == (
        "done", True, "$x$", True)
    # Asked again: answered at once from the kept reading, with no job and nothing sent.
    again = call(ctx, "ink.transcribe", {"inkId": "ink_1"})
    assert (again["jobId"], again["status"], again["done"]) == (None, "done", True)
    assert again["result"]["transcriptionId"] == done["result"]["transcriptionId"] and reader.reached == 1
    # The block now reads as the transcription.
    pad = call(ctx, "pad.get", {"padId": "p"})
    assert [(b["bodyMd"], b["provenance"]) for b in pad["blocks"]] == [("$x$", "ink_transcription")]
    # ... and it was emitted as the learner's words, as a committed pad batch's blocks are.
    _vault, repository = ctx.require_vault()
    with repository.connection() as connection:
        queued = [tuple(row) for row in connection.execute(
            "SELECT source_id FROM learner_text_gap_jobs WHERE source_kind = 'pad_text'")]
    assert queued == [(done["result"]["headVersionId"],)]


def test_a_second_ask_while_reading_joins_the_job_and_cancel_sends_nothing_more(contexts):
    ctx, held = contexts(hold=True)
    _ink_block(ctx)
    first = call(ctx, "ink.transcribe", {"inkId": "ink_1"})
    assert held.inside.wait(WAIT)
    running = call(ctx, "ink.transcribe_job", {"jobId": first["jobId"]})
    assert (running["status"], running["done"]) == ("running", False)
    assert call(ctx, "ink.transcribe", {"inkId": "ink_1"})["jobId"] == first["jobId"]
    cancelled = call(ctx, "ink.transcribe_cancel", {"jobId": first["jobId"]})
    assert cancelled["status"] == "cancelled"
    held.release.set()
    assert wait_reading(ctx, first["jobId"])["status"] == "cancelled"
    # A new ask after a cancel starts a new job (the held request finished; this one reads again).
    held.release.set()
    second = call(ctx, "ink.transcribe", {"inkId": "ink_1"})
    if second["jobId"] is not None:  # the cancelled job's request was already sent and may have kept its reading
        assert second["jobId"] != first["jobId"]
        assert wait_reading(ctx, second["jobId"])["status"] == "done"


def test_a_cancel_before_the_request_is_sent_sends_nothing(contexts):
    from learnloop_sidecar import polled_jobs

    ctx, reader = contexts()
    _ink_block(ctx)
    gate = __import__("threading").Event()
    original = polled_jobs.PolledJobs.start

    def start_held(self, ctx_, **kwargs):
        work = kwargs["work"]

        def held(job):
            gate.wait(WAIT)
            return work(job)

        return original(self, ctx_, **{**kwargs, "work": held})

    polled_jobs.PolledJobs.start = start_held
    try:
        first = call(ctx, "ink.transcribe", {"inkId": "ink_1"})
    finally:
        polled_jobs.PolledJobs.start = original
    call(ctx, "ink.transcribe_cancel", {"jobId": first["jobId"]})
    gate.set()
    final = wait_reading(ctx, first["jobId"])
    assert final["status"] == "cancelled" and reader.reached == 0


def test_a_reading_belongs_to_its_vault(contexts):
    ctx, held = contexts(hold=True)
    _ink_block(ctx)
    first = call(ctx, "ink.transcribe", {"inkId": "ink_1"})
    assert held.inside.wait(WAIT)
    other = create_basic_vault(ctx.vault.root.parent / "other")
    held.release.set()
    job = next(job for job in ink_jobs(ctx) if job.job_id == first["jobId"])
    assert job.done.wait(WAIT)
    ctx.load(other.root)
    with pytest.raises(SidecarError) as elsewhere:
        call(ctx, "ink.transcribe_job", {"jobId": first["jobId"]})
    assert elsewhere.value.code == "job_not_found"


def test_a_failed_reading_says_why(contexts):
    ctx, _none = contexts(glm=False)
    _ink_block(ctx)
    started = call(ctx, "ink.transcribe", {"inkId": "ink_1"})
    failed = wait_reading(ctx, started["jobId"])
    assert (failed["status"], failed["done"], failed["error"]["code"]) == ("failed", True, "unavailable")
    assert "Settings, under Ingestion" in failed["error"]["message"]
    with pytest.raises(SidecarError) as unknown:
        call(ctx, "ink.transcribe", {"inkId": "ink_none"})
    assert unknown.value.code == "ink_not_found"
    with pytest.raises(SidecarError) as no_job:
        call(ctx, "ink.transcribe_job", {"jobId": "ink_none"})
    assert no_job.value.code == "job_not_found"
