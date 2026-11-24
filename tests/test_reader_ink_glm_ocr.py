"""Handwriting read by GLM-OCR (owner decision 2026-11-23: "this should get passed to glm-ocr then passed as text
directly"): the image of an ink owner's standing strokes goes to GLM-OCR through the extractor's one entry for an
image, admitted as ingest admits a page image, and the text it recognises is the reading, unchanged. GLM-OCR is faked
at its transport seam (``glm_ocr._open``, as ``tests/test_glm_ocr.py`` fakes it); no request leaves the machine."""

from __future__ import annotations

import base64

import pytest

from learnloop.ai.execution import observe_model_calls
from learnloop.ai.model_use import ModelUseNotAccepted
from learnloop.config import LearnLoopConfig
from learnloop.config.retired import identity_dump
from learnloop.db.stores import pad_reads
from learnloop.ingest.extractors import glm_ocr as glm
from learnloop.ops.settings_store import apply_config_updates
from learnloop.pads import ink_transcribe as reading
from tests.glm_ocr_helpers import region
from tests.ink_helpers import GLM_KEY, STROKES, FakeGlmOcr, glm_hosted, glm_local, ink_pad
from tests.reader_rd4_helpers import rows, vault


@pytest.fixture(autouse=True)
def no_glm_ocr(monkeypatch):
    """No z.ai key from the environment and no local server unless a test sets one up; any request fails."""

    for name in glm.KEY_ENV_ALIASES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(glm, "_open", lambda *a, **kw: pytest.fail("unexpected GLM-OCR request"))
    monkeypatch.setattr(glm, "_PROBES", {})
    monkeypatch.setattr(glm.time, "sleep", lambda seconds: None)


def _line(tmp_path):
    paths, repository, batches, client = ink_pad(tmp_path)
    client.save("ink_1", STROKES, block_id="b1")
    return paths, repository, batches


def _read(paths, repository):
    return reading.transcribe(vault(paths), repository, reading.prepare(repository, "ink_1"))


def test_hosted_glm_ocr_reads_the_image_of_the_strokes_and_nothing_else(tmp_path, monkeypatch):
    paths, repository, _batches = _line(tmp_path)
    ocr = glm_hosted(monkeypatch, paths.root, r"$a^2 + b^2$")
    result = _read(paths, repository)
    [request] = ocr.requests
    assert request.url == glm.API_URL and request.headers["Authorization"] == f"Bearer {GLM_KEY}"
    image = reading.render(reading.prepare(repository, "ink_1"))
    assert request.body["file"] == "data:image/png;base64," + base64.b64encode(image).decode()
    assert "start_page_id" not in request.body and request.body["model"] == "glm-ocr"
    assert (result["latex_md"], result["applied"]) == (r"$a^2 + b^2$", True)
    assert rows(repository, "SELECT provider, model FROM ink_transcriptions") == [("zai-glm-ocr", glm.RECOGNITION_MODEL)]


def test_the_reading_is_the_text_glm_ocr_recognised_unchanged(tmp_path, monkeypatch):
    paths, repository, _batches = _line(tmp_path)
    # A formula region keeps its $$, a table its markup, a dollar sign stays as written, and a region's line
    # breaks stay: nothing here rewrites, escapes or interprets what GLM-OCR read. An image region holds no text.
    glm_local(monkeypatch, paths.root, regions=[
        region(0, "text", "costs $5 and <b>x</b>", [10, 10, 400, 40]),
        region(1, "formula", "$$\n\\frac{a}{b}\n$$", [10, 50, 400, 120]),
        region(2, "image", "https://example.invalid/crop.png", [10, 130, 400, 200]),
        region(3, "text", "line one\nline two", [10, 210, 400, 260]),
    ])
    result = _read(paths, repository)
    expected = "costs $5 and <b>x</b>\n\n$$\n\\frac{a}{b}\n$$\n\nline one\nline two"
    assert result["latex_md"] == expected
    assert rows(repository, "SELECT latex_md, confidence_label FROM ink_transcriptions") == [(expected, "may_be_wrong")]
    with repository.connection() as connection:
        assert pad_reads.head(connection, "b1")["body_md"] == expected


def test_without_glm_ocr_nothing_is_sent_and_the_line_says_how_to_turn_it_on(tmp_path):
    paths, repository, _batches = _line(tmp_path)
    with pytest.raises(reading.InkUnavailable) as refused:
        _read(paths, repository)
    assert refused.value.reason == "unavailable"
    assert "Settings, under Ingestion" in refused.value.message and "GLM-OCR" in refused.value.message
    assert rows(repository, "SELECT COUNT(*) FROM ink_transcriptions") == [(0,)]


def test_a_local_backend_that_does_not_answer_is_not_available(tmp_path, monkeypatch):
    paths, repository, _batches = _line(tmp_path)
    apply_config_updates(paths.root / "learnloop.toml", {("ingest", "pdf", "glm_ocr", "backend"): "local"})
    monkeypatch.setattr(glm, "local_available", lambda config=None: False)
    with pytest.raises(reading.InkUnavailable) as refused:
        _read(paths, repository)
    assert refused.value.reason == "unavailable"


def test_hosted_without_the_learners_ok_for_z_ai_sends_nothing(tmp_path, monkeypatch):
    paths, repository, _batches = _line(tmp_path)
    ocr = glm_hosted(monkeypatch, paths.root, "x", upload_ok=False)
    with pytest.raises(reading.InkUnavailable) as refused:
        _read(paths, repository)
    assert refused.value.reason == "needs_upload_ok" and "z.ai" in refused.value.message
    assert ocr.reached == 0


@pytest.mark.no_ai_ok
def test_hosted_before_the_ok_to_use_ai_sends_nothing(tmp_path, monkeypatch):
    paths, repository, _batches = _line(tmp_path)
    ocr = glm_hosted(monkeypatch, paths.root, "x", model_use_ok=False)
    with pytest.raises(ModelUseNotAccepted):
        _read(paths, repository)
    assert ocr.reached == 0


@pytest.mark.no_ai_ok
def test_the_local_backend_asks_for_nothing(tmp_path, monkeypatch):
    paths, repository, _batches = _line(tmp_path)
    ocr = glm_local(monkeypatch, paths.root, "y = x")
    result = _read(paths, repository)  # no OK to use AI and no OK for z.ai were given
    [request] = ocr.requests
    assert request.url == glm.LOCAL_URL and "Authorization" not in request.headers
    assert result["latex_md"] == "y = x"


def test_one_admission_and_receipt_at_ingests_price_and_a_retry_spends_nothing(tmp_path, monkeypatch):
    paths, repository, _batches = _line(tmp_path)
    ocr = glm_hosted(monkeypatch, paths.root, "x")
    apply_config_updates(paths.root / "learnloop.toml", {("ingest", "pdf", "glm_ocr", "price_per_million_tokens"): 2.0})
    events = []
    with observe_model_calls(lambda action, event: events.append((action, event))):
        first = _read(paths, repository)
        again = _read(paths, repository)
    assert again == first and ocr.reached == 1
    starts = [event for action, event in events if action == "start"]
    finishes = [event for action, event in events if action == "finish"]
    assert len(starts) == len(finishes) == 1 and starts[0]["provider"] == "zai-glm-ocr"
    assert finishes[0]["cost"] == pytest.approx(940 * 2.0 / 1_000_000)


def test_recognise_image_refuses_a_hosted_read_without_the_ok_before_sending(monkeypatch):
    monkeypatch.setenv("ZAI_API_KEY", GLM_KEY)
    extractor = glm.GlmOcrDocumentExtractor(backend="api")
    fake = FakeGlmOcr("x").install(monkeypatch)
    with pytest.raises(glm.GlmOcrConsentRequired):
        extractor.recognise_image(b"\x89PNG\r\n\x1a\n" + b"0" * 16, upload_allowed=False)
    assert fake.reached == 0


def test_the_retired_vision_route_keeps_whole_config_bytes(tmp_path):
    assert "ink_transcription" not in LearnLoopConfig().ai.routing.model_dump()
    assert "ink_transcription" not in identity_dump(LearnLoopConfig().ai.routing)
    # A vault that set the old route still loads, and an identity that hashed it keeps its bytes.
    routed = LearnLoopConfig.model_validate({"ai": {"routing": {"ink_transcription": "plan"}}})
    assert "ink_transcription" not in routed.ai.routing.model_dump()
    assert identity_dump(routed)["ai"]["routing"]["ink_transcription"] == "plan"
