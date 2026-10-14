"""GLM-OCR document reading (learnloop.ingest.extractors.glm_ocr).

Fakes only: no request leaves the machine. The response fixtures are shaped
after the glmocr 0.1.5 SDK source (its MaaS client and Flask server) and z.ai's
documentation: hosted ``bbox_2d`` in pixels of the provider's own page render,
self-hosted ``bbox_2d`` normalised to 0-1000, one ``[[regions]]`` per image from
the self-hosted server. They are not captures of live sessions.
"""

from __future__ import annotations

import base64
import io
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace
from urllib.error import HTTPError, URLError

import pytest
from pypdf import PdfReader, PdfWriter
from PIL import Image

from learnloop.ai.execution import gate_model_requests, observe_model_calls
from learnloop.ai.spend import MeteredRequestGate, SpendEnvelope, SpendLimitExceeded, spend_envelopes
from learnloop.ingest import extractors
from learnloop.ingest.extractors import glm_ocr as glm
from learnloop.ingest.extractors.base import ExtractionContext
from learnloop.ingest.ir import render_ir_markdown

KEY = "fake-zai-key-123456"


@pytest.fixture(autouse=True)
def isolated(monkeypatch):
    for name in ("ZAI_API_KEY", "ZHIPU_API_KEY", "ZHIPUAI_API_KEY", "LEARNLOOP_MARKER_PROVIDER", "MY_OCR_KEY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(glm, "_open", lambda *a, **kw: pytest.fail("unexpected HTTP request"))
    monkeypatch.setattr(glm, "_PROBES", {})
    monkeypatch.setattr(glm.time, "sleep", lambda seconds: None)


def pdf(pages: int = 1, *, outline: tuple[str, ...] = ()) -> bytes:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(612, 792)
    for index, title in enumerate(outline):
        writer.add_outline_item(title, index)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def png(size=(1000, 1400)) -> bytes:
    out = io.BytesIO()
    Image.new("RGB", size, "white").save(out, format="PNG")
    return out.getvalue()


def region(index, label, content, bbox=None, *, native=None, width=1224, height=1584):
    item = {"index": index, "label": label, "content": content, "bbox_2d": bbox, "width": width, "height": height}
    if native:
        item["native_label"] = native
    return item


def hosted(pages: int = 1, *, usage=True) -> dict:
    """A layout_parsing response: one region list per page, pixel boxes on a
    1224x1584 render of a 612x792-point page (scale 2)."""

    result = {
        "id": "task_1", "created": 1760000000, "model": "glm-ocr", "request_id": "req_1",
        "md_results": "\n\n".join(f"Page {p}" for p in range(pages)),
        "layout_details": [
            [region(0, "text", f"Page {p}", [122, 158, 1102, 317])] for p in range(pages)
        ],
        "data_info": {"num_pages": pages, "pages": [{"width": 1224, "height": 1584}] * pages},
    }
    if usage:
        result["usage"] = {"prompt_tokens": 1000, "completion_tokens": 200, "total_tokens": 1200,
                           "prompt_tokens_details": {"cached_tokens": 100}}
    return result


def ok(**config) -> ExtractionContext:
    return ExtractionContext("rev", config={"whole_file_upload_allowed": True}, **config)


def api(monkeypatch, **config) -> glm.GlmOcrDocumentExtractor:
    monkeypatch.setenv("ZAI_API_KEY", KEY)
    return glm.GlmOcrDocumentExtractor(config=config, backend="api")


def record(monkeypatch, respond=None) -> list:
    sent = []

    def fake(request, timeout):
        body = json.loads(request.data)
        sent.append(SimpleNamespace(request=request, body=body, timeout=timeout))
        pages = body.get("end_page_id", 1) - body.get("start_page_id", 1) + 1
        return io.BytesIO(json.dumps(respond(body) if respond else hosted(pages)).encode())

    monkeypatch.setattr(glm, "_open", fake)
    return sent


def finishes(events):
    return [event for action, event in events if action == "finish"]


# -- the hosted request ------------------------------------------------------------


def test_a_whole_short_pdf_goes_as_one_data_uri_with_its_page_range_and_bearer_key(monkeypatch):
    sent = record(monkeypatch)
    ir = api(monkeypatch).extract(pdf(3), ok())

    (one,) = sent
    assert one.request.full_url == glm.API_URL
    assert one.request.get_header("Authorization") == f"Bearer {KEY}"
    assert one.request.get_header("Content-type") == "application/json"
    assert one.body["model"] == "glm-ocr"
    assert one.body["file"].startswith("data:application/pdf;base64,")
    assert base64.b64decode(one.body["file"].split(",", 1)[1]) == pdf(3)
    assert (one.body["start_page_id"], one.body["end_page_id"]) == (1, 3)
    assert one.body["return_crop_images"] is False and one.body["need_layout_visualization"] is False
    assert 6 <= len(one.body["request_id"]) <= 64
    assert one.timeout == 300  # the glmocr SDK's own MaaS default
    assert [block.page for block in ir.blocks] == [0, 1, 2]  # IR pages stay zero-based


def test_long_pdfs_go_in_windows_of_at_most_30_pages_each_its_own_smaller_file(monkeypatch):
    sent = record(monkeypatch)
    ir = api(monkeypatch).extract(pdf(65), ok())

    assert [(s.body["start_page_id"], s.body["end_page_id"]) for s in sent] == [(1, 30), (1, 30), (1, 5)]
    assert [len(PdfReader(io.BytesIO(base64.b64decode(s.body["file"].split(",", 1)[1]))).pages) for s in sent] == [30, 30, 5]
    assert [block.page for block in ir.blocks] == list(range(65))
    assert [block.text for block in ir.blocks][:2] == ["Page 0", "Page 1"]
    assert ir.blocks[31].text == "Page 1"  # the second window's own page 1 is page 31


def test_a_page_selection_sends_each_contiguous_run(monkeypatch):
    sent = record(monkeypatch)
    ir = api(monkeypatch, max_pages_per_request=2).extract(pdf(8), ok(page_selection=(0, 2, 3, 4, 7)))

    assert [len(PdfReader(io.BytesIO(base64.b64decode(s.body["file"].split(",", 1)[1]))).pages) for s in sent] == [1, 2, 1, 1]
    assert [block.page for block in ir.blocks] == [0, 2, 3, 4, 7]


def test_raw_base64_the_zhipu_endpoint_and_an_oversize_window_splits(monkeypatch):
    sent = record(monkeypatch)
    extractor = api(monkeypatch, base64_style="raw", api_url="https://open.bigmodel.cn/api/paas/v4")
    extractor.extract(pdf(2), ok())
    assert sent[0].request.full_url == "https://open.bigmodel.cn/api/paas/v4/layout_parsing"
    assert base64.b64decode(sent[0].body["file"]).startswith(b"%PDF-")

    sent.clear()
    monkeypatch.setattr(glm, "PDF_LIMIT", len(pdf(2)) + 50)
    ir = extractor.extract(pdf(6), ok())
    assert all(len(base64.b64decode(s.body["file"])) <= glm.PDF_LIMIT for s in sent)
    assert len(sent) > 1 and [block.page for block in ir.blocks] == list(range(6))

    monkeypatch.setattr(glm, "PDF_LIMIT", 10)
    with pytest.raises(glm.GlmOcrExtractionError, match="single PDF page"):
        extractor.extract(pdf(1), ok())


def test_images_are_sent_whole_and_capped_at_10_mb(monkeypatch):
    sent = record(monkeypatch, lambda body: {"layout_details": [[region(0, "text", "Scanned words", [100, 140, 900, 280], width=1000, height=1400)]]})
    ir = api(monkeypatch).extract(png(), ok())

    assert sent[0].body["file"].startswith("data:image/png;base64,")
    assert "start_page_id" not in sent[0].body
    assert ir.blocks[0].page == 0 and ir.blocks[0].bbox == [100.0, 140.0, 900.0, 280.0]  # pixels of the image
    monkeypatch.setattr(glm, "IMAGE_LIMIT", 10)
    with pytest.raises(glm.GlmOcrExtractionError, match="10 MB"):
        api(monkeypatch).extract(png(), ok())
    with pytest.raises(glm.GlmOcrExtractionError, match="PDF, PNG and JPG"):
        api(monkeypatch).extract(b"GIF89a....", ok())
    assert glm._mime(b"\xff\xd8\xff\xe0data") == "image/jpeg"


def test_the_endpoint_must_be_https_and_plain(monkeypatch):
    for url in ("http://api.z.ai/api/paas/v4/layout_parsing", "https://user:pw@api.z.ai/layout_parsing",
                "https://api.z.ai/layout_parsing?x=1", "ftp://api.z.ai/layout_parsing"):
        with pytest.raises(glm.GlmOcrExtractionError):
            api(monkeypatch, api_url=url).extract(pdf(), ok())


def test_redirects_are_refused_so_the_key_and_file_never_follow_them():
    handler = glm._NoRedirect()
    assert handler.redirect_request(None, None, 302, "Found", {}, "https://elsewhere.invalid/") is None


# -- retries, errors and receipts ------------------------------------------------------


def test_429_and_5xx_retry_with_their_own_admission_and_receipt(monkeypatch):
    tries, sleeps, events = [], [], []

    def fake(request, timeout):
        tries.append(request)
        if len(tries) == 1:
            raise HTTPError(request.full_url, 429, "busy", {"Retry-After": "3"}, io.BytesIO(b"{}"))
        if len(tries) == 2:
            raise HTTPError(request.full_url, 503, "busy", {}, io.BytesIO(b"{}"))
        return io.BytesIO(json.dumps(hosted()).encode())

    monkeypatch.setattr(glm, "_open", fake)
    monkeypatch.setattr(glm.time, "sleep", sleeps.append)
    gate = MeteredRequestGate(limit_usd=None, price_per_token=lambda p: 0.03 / 1e6, is_subscription=lambda c: False)
    with gate_model_requests(gate), observe_model_calls(lambda a, e: events.append((a, e))):
        api(monkeypatch).extract(pdf(), ok())

    assert len(tries) == gate.admitted == 3
    assert sleeps == [3.0, 2.0]  # Retry-After, then backoff
    assert [e["status"] for e in finishes(events)] == ["failed", "failed", "completed"]
    assert [e.get("http_status") for e in finishes(events)] == [429, 503, None]


@pytest.mark.parametrize("failure, message", [
    (400, "HTTP 400: 1214 file is not supported"),
    (500, "HTTP 500"),
    ("network", "Could not reach"),
    ("json", "invalid JSON"),
    ("body_error", "reported an error: 1301 the request failed"),
])
def test_errors_name_the_provider_reason_but_never_the_key(monkeypatch, failure, message):
    def fake(request, timeout):
        if isinstance(failure, int):
            body = json.dumps({"error": {"code": "1214", "message": f"file is not supported {KEY}"}}).encode()
            raise HTTPError(request.full_url, failure, "bad", {}, io.BytesIO(body))
        if failure == "network":
            raise URLError(KEY)
        if failure == "json":
            return io.BytesIO(b"not json " + KEY.encode())
        return io.BytesIO(json.dumps({"code": 1301, "msg": "the request failed"}).encode())

    monkeypatch.setattr(glm, "_open", fake)
    with pytest.raises(glm.GlmOcrExtractionError, match=message) as caught:
        api(monkeypatch).extract(pdf(), ok())
    assert KEY not in str(caught.value)


def test_receipts_carry_usage_and_cost_and_never_the_key_or_file(monkeypatch):
    record(monkeypatch)
    events = []
    with observe_model_calls(lambda a, e: events.append((a, e))):
        ir = api(monkeypatch).extract(pdf(65), ok())

    starts = [event for action, event in events if action == "start"]
    done = finishes(events)
    assert len(starts) == len(done) == 3
    assert {s["provider"] for s in starts} == {"zai-glm-ocr"} and {s["model"] for s in starts} == {"glm-ocr"}
    assert {s["purpose"] for s in starts} == {"document_layout_recognition"}
    assert done[0]["input_tokens"] == 1000 and done[0]["output_tokens"] == 200
    assert done[0]["cached_input_tokens"] == 100
    assert done[0]["cost"] == pytest.approx(1200 * 0.03 / 1e6)
    assert json.loads(done[0]["usage_json"])["cost_basis"] == "reported_usage"
    assert KEY not in json.dumps(events) and "base64" not in json.dumps(events)
    assert "glm_ocr_api_selected" in ir.health.flags


def test_missing_usage_is_charged_at_the_labelled_estimate(monkeypatch):
    record(monkeypatch, lambda body: hosted(usage=False))
    events = []
    with observe_model_calls(lambda a, e: events.append((a, e))):
        api(monkeypatch).extract(pdf(), ok())
    (done,) = finishes(events)
    assert done["cost"] == pytest.approx(glm.ESTIMATED_TOKENS_PER_PAGE * 0.03 / 1e6)
    assert json.loads(done["usage_json"])["cost_basis"] == "estimated_usage_missing"


def test_spend_refusals_send_nothing_and_no_ok_sends_nothing(monkeypatch):
    sent = record(monkeypatch)
    extractor = api(monkeypatch)
    with pytest.raises(glm.GlmOcrConsentRequired, match=r"z\.ai \(GLM-OCR\)"):
        extractor.extract(pdf(), ExtractionContext("rev"))
    gate = MeteredRequestGate(limit_usd=0, price_per_token=lambda p: 0.03 / 1e6, is_subscription=lambda c: False)
    with gate_model_requests(gate), pytest.raises(SpendLimitExceeded):
        extractor.extract(pdf(), ok())
    with spend_envelopes(SpendEnvelope("daily", 0)), pytest.raises(SpendLimitExceeded):
        extractor.extract(pdf(), ok())
    assert sent == []


def test_the_daily_gate_prices_glm_receipts_and_local_runs_cost_nothing(monkeypatch):
    from learnloop.config import LearnLoopConfig
    from learnloop.content.pipeline.add_source import _request_gate

    config = LearnLoopConfig()
    config.ingest.pdf.glm_ocr.price_per_million_tokens = 0.1
    gate = _request_gate(config, 0.0007, 0)
    record(monkeypatch, lambda body: {**hosted(), "usage": {"prompt_tokens": 5000, "completion_tokens": 1000}})
    extractor = api(monkeypatch, price_per_million_tokens=0.1)
    with gate_model_requests(gate):
        extractor.extract(pdf(), ok())  # $0.0006 spent of $0.0007
        with pytest.raises(SpendLimitExceeded):
            extractor.extract(pdf(), ok())
        glm.GlmOcrDocumentExtractor(backend="local").extract(png(), ExtractionContext("rev"))
    assert gate.admitted == 2 and gate.spent_usd == pytest.approx(0.0006)


# -- mapping the layout to the IR -------------------------------------------------------


def paper_page() -> list[dict]:
    """One page as the hosted pipeline reports it (pixel boxes, 1224x1584)."""

    return [
        region(0, "text", "# Optimised Exudate Detection", [200, 100, 1024, 160], native="doc_title"),
        region(1, "text", "## 1. Introduction", [100, 200, 600, 240]),
        region(2, "text", "Diabetic retinopathy is a leading cause\n\nof blindness.", [100, 250, 1124, 400]),
        region(3, "formula", "$$\nL = -\\sum_i \\log p_i \\tag{1}\n$$", [300, 420, 900, 480]),
        region(4, "formula", "x^2 + y^2", [300, 500, 900, 540]),
        region(5, "table", "<table><tr><th>Method</th><th>F1 | %</th></tr><tr><td>Ours</td><td>$0.81$</td></tr></table>",
               [100, 560, 1124, 760]),
        region(6, "image", "![](page=0,bbox=[100, 800, 600, 1100])", [100, 800, 600, 1100]),
        region(7, "text", "Figure 1: The pipeline.", [100, 1110, 600, 1140], native="figure_title"),
        region(8, "text", "# not a heading\nbut a code comment", [100, 1150, 600, 1200], native="algorithm"),
    ]


def test_regions_map_to_blocks_in_reading_order_with_roles_text_and_point_boxes():
    page = paper_page()
    result = {"layout_details": [list(reversed(page))], "data_info": {"pages": [{"width": 1224, "height": 1584}]}}
    ir = glm.responses_to_ir([(result, [0])], sizes=[(612.0, 792.0)], outline=[], version="v")

    assert [b.block_type for b in ir.blocks] == [
        "SectionHeader", "SectionHeader", "Text", "Equation", "Equation", "Table", "Figure", "Caption", "Code",
    ]
    title, intro, prose, eq1, eq2, table, figure, caption, code = ir.blocks
    assert (title.text, intro.text) == ("Optimised Exudate Detection", "1. Introduction")
    assert title.bbox == [100.0, 50.0, 512.0, 80.0]  # pixels / 2 = PDF points, top-left origin
    assert prose.section_path == ["Optimised Exudate Detection", "1. Introduction"]
    assert prose.text == "Diabetic retinopathy is a leading cause\n\nof blindness."
    assert eq1.text == "$$\nL = -\\sum_i \\log p_i \\tag{1}\n$$" and eq1.role_hint == "equation"
    assert eq2.text == "$$x^2 + y^2$$"
    assert table.text == "| Method | F1 \\| % |\n| --- | --- |\n| Ours | $0.81$ |" and table.role_hint == "table"
    assert figure.text == "" and figure.role_hint == "figure"  # a crop reference is not prose
    assert caption.text == "Figure 1: The pipeline."
    assert code.text.startswith("# not a heading")
    assert all(b.extractor_block_id.startswith("glm/page/0/region/") for b in ir.blocks)
    markdown = render_ir_markdown(ir)
    assert markdown.count("Optimised Exudate Detection") == 1 and "## 1. Introduction" in markdown
    assert "[Figure]" in markdown and "| Ours | $0.81$ |" in markdown
    assert ir.health.pages[0].text_extraction_method == "glm_ocr"
    assert ir.health.pages[0].block_counts["Equation"] == 2
    assert "glm_ocr_response_nested" in ir.health.flags


def test_heading_units_split_by_block_and_nest_by_level():
    ir = glm.responses_to_ir([({"layout_details": [paper_page()[:3], [
        region(0, "text", "## 2. Method", [100, 100, 600, 140]),
        region(1, "text", "We train.", [100, 150, 600, 200]),
    ]]}, [0, 1])], sizes=[(612.0, 792.0)] * 2, outline=[], version="v")

    assert [u.label for u in ir.units] == ["Optimised Exudate Detection", "1. Introduction", "2. Method"]
    assert [u.parent_unit_id for u in ir.units] == [None, "u1", "u1"]
    assert [u.span_ids for u in ir.units] == [["s1"], ["s2", "s3"], ["s4", "s5"]]
    assert (ir.units[2].page_start, ir.units[2].page_end) == (1, 1)
    assert ir.units[0].locator["scheme"] == "detected_headings"


def test_an_embedded_outline_wins_but_a_lone_bookmark_is_no_structure(monkeypatch):
    record(monkeypatch, lambda body: {"layout_details": [
        [region(0, "text", "## Detected", [0, 0, 10, 10]), region(1, "text", "Words", [0, 20, 10, 30])],
        [region(0, "text", "More words", [0, 0, 10, 10])],
    ]})
    extractor = api(monkeypatch)
    ir = extractor.extract(pdf(2, outline=("Author one", "Author two")), ok())
    assert [u.label for u in ir.units] == ["Author one", "Author two"]
    assert ir.units[0].locator["scheme"] == "pdf_outline"

    ir = extractor.extract(pdf(2, outline=("Cover",)), ok())
    assert [u.label for u in ir.units] == ["Detected"]


def test_the_self_hosted_shapes_one_unit_per_image_and_0_to_1000_boxes():
    # python -m glmocr.server: json_result and layout_details carry the same
    # value; several images come back as one [[regions]] per image.
    units = [[[{"index": 0, "label": "text", "native_label": "text", "content": f"Local {p}",
                "bbox_2d": [100, 200, 900, 400]}]] for p in range(2)]
    result = {"json_result": units, "layout_details": units, "markdown_result": "", "data_info": {"pages": []},
              "usage": {}, "model": "glm-ocr"}
    ir = glm.responses_to_ir([(result, [4, 5])], sizes=[(612.0, 792.0)] * 6, outline=[], version="v")
    assert [(b.page, b.text) for b in ir.blocks] == [(4, "Local 0"), (5, "Local 1")]
    assert ir.blocks[0].bbox == [61.2, 158.4, 550.8, 316.8]
    assert "glm_ocr_response_units" in ir.health.flags

    single = {"json_result": json.dumps([[{"label": "text", "content": "One", "bbox_2d": [0, 0, 500, 500]}]])}
    ir = glm.responses_to_ir([(single, [0])], sizes=[(100.0, 200.0)], outline=[], version="v")
    assert ir.blocks[0].bbox == [0.0, 0.0, 50.0, 100.0]


def test_older_and_variant_shapes_normalise_too():
    flat = {"layout_details": [
        {"page": 31, "type": "text", "text": "P31", "bbox": [0.1, 0.1, 0.5, 0.2]},
        {"page": 32, "type": "table", "cells": [["a", "b"], ["1", "2"]]},
    ]}
    ir = glm.responses_to_ir([(flat, [30, 31])], sizes=[(600.0, 800.0)] * 32, outline=[], version="v")
    assert [(b.page, b.block_type) for b in ir.blocks] == [(30, "Text"), (31, "Table")]
    assert ir.blocks[0].bbox == [60.0, 80.0, 300.0, 160.0]
    assert ir.blocks[1].text == "| a | b |\n| --- | --- |\n| 1 | 2 |"

    objects = {"data": {"pages": [{"regions": [{"label": "text", "content": "Hi", "bbox": [1, 2, 3, 4],
                                                "coordinate_system": "pixels", "width": 10, "height": 20}]}]}}
    ir = glm.responses_to_ir([(objects, [0])], sizes=[(100.0, 100.0)], outline=[], version="v")
    assert ir.blocks[0].bbox == [10.0, 10.0, 30.0, 20.0]
    assert "glm_ocr_response_page_objects" in ir.health.flags


def test_incomplete_or_unreadable_layouts_fail_rather_than_read_as_empty():
    for result, count in (
        ({"layout_details": [[]]}, 2),
        ({"layout_details": None}, 1),
        ({"layout_details": [["not a region"]]}, 1),
        ({"md_results": "text only"}, 1),
    ):
        with pytest.raises(glm.GlmOcrExtractionError):
            glm.responses_to_ir([(result, list(range(count)))], sizes=[(1.0, 1.0)] * count, outline=[], version="v")
    with pytest.raises(glm.GlmOcrExtractionError, match="no text"):
        glm.responses_to_ir([({"layout_details": [[]]}, [0])], sizes=[(1.0, 1.0)], outline=[], version="v")


def test_boxes_use_the_rotated_crop_box_the_reader_draws_in(monkeypatch):
    writer = PdfWriter()
    page = writer.add_blank_page(600, 800)
    page.cropbox.lower_left = (100, 100)
    page.cropbox.upper_right = (500, 700)  # 400 x 600 points
    page.rotate(90)  # shown 600 x 400
    out = io.BytesIO()
    writer.write(out)
    record(monkeypatch, lambda body: {"layout_details": [[region(0, "text", "R", [120, 80, 1080, 400], width=1200, height=800)]]})
    ir = api(monkeypatch).extract(out.getvalue(), ok())
    assert ir.blocks[0].bbox == [60.0, 40.0, 540.0, 200.0]


def test_html_tables_become_gfm_with_spans_escaped_pipes_and_untouched_maths():
    table = glm._table_markdown(
        '<table><tr><th rowspan="2">A</th><th colspan="2">B</th></tr>'
        '<tr><td>x|y</td><td>&lt;z&gt; $a<b$</td></tr></table>'
    )
    assert table == "| A | B | B |\n| --- | --- | --- |\n| A | x\\|y | &lt;z&gt; $a<b$ |"
    assert glm._table_markdown("plain text") == "plain text"


# -- selection and fallbacks --------------------------------------------------------------


def test_auto_prefers_hosted_glm_with_a_key_then_marker_then_pypdf_with_reasons(monkeypatch):
    monkeypatch.setattr(extractors, "marker_available", lambda: False)
    chosen = extractors.pdf_extractor_for()
    assert chosen.name == "pypdf" and chosen.selection_reason == "glm_ocr_and_marker_unavailable_pypdf_selected"
    monkeypatch.setattr(extractors, "marker_available", lambda: True)
    chosen = extractors.pdf_extractor_for({"engine": "auto"})
    assert chosen.name == "marker" and chosen.selection_reason == "glm_ocr_unavailable_marker_selected"
    with pytest.raises(extractors.MarkerUnavailableError, match="z.ai API key"):
        extractors.pdf_extractor_for({"engine": "glm_ocr"})

    monkeypatch.setenv("ZHIPUAI_API_KEY", KEY)  # an alias counts
    assert extractors.pdf_extractor_for().backend == "api"
    assert extractors.pdf_extractor_for({"engine": "pypdf"}).name == "pypdf"
    assert extractors.pdf_extractor_for({"engine": "marker"}).name == "marker"
    with pytest.raises(ValueError):
        extractors.pdf_extractor_for({"engine": "tesseract"})


def test_the_configured_key_variable_comes_first_then_the_aliases(monkeypatch):
    monkeypatch.setenv("MY_OCR_KEY", "custom-key")
    monkeypatch.setenv("ZHIPU_API_KEY", "alias-key")
    assert glm.glm_api_key({"api_key_env": "MY_OCR_KEY"}) == "custom-key"
    assert glm.glm_api_key({"api_key_env": "UNSET_NAME"}) == "alias-key"
    assert glm.selected_backend({"backend": "api", "api_key_env": "MY_OCR_KEY"}) == "api"


def test_local_runs_only_when_chosen_and_answering_and_a_local_only_reading_never_uploads(monkeypatch):
    monkeypatch.setenv("ZAI_API_KEY", KEY)
    probes = []
    monkeypatch.setattr(glm, "local_available", lambda config=None: probes.append(config) or True)
    assert glm.selected_backend({}) == "api" and probes == []  # auto never probes
    # local_only: a repair the learner OK'd as local (the per-book keep-local is retired).
    assert glm.selected_backend({}, local_only=True) is None
    assert glm.selected_backend({"backend": "local"}, local_only=True) == "local"
    assert glm.selected_backend({"backend": "local", "local_url": "http://gpu-box:5002/glmocr/parse"},
                                local_only=True) is None
    assert glm.selected_backend({"backend": "local"}, probe=False) == "local"
    monkeypatch.setattr(glm, "local_available", lambda config=None: False)
    assert glm.selected_backend({"backend": "local"}) is None

    # auto passes over z.ai for a local-only reading; an explicit choice is
    # kept so the import reads it locally itself (jobs._document_extractor).
    monkeypatch.setattr(extractors, "marker_available", lambda: False)
    assert extractors.pdf_extractor_for({}, local_only=True).name == "pypdf"
    assert extractors.pdf_extractor_for({"engine": "glm_ocr"}, local_only=True).backend == "api"


def test_auto_falls_back_on_a_glm_failure_but_never_past_a_refusal(monkeypatch):
    from learnloop.ai.spend import SpendCancelled
    from learnloop.ingest.ir import DocumentIR

    monkeypatch.setattr(extractors, "marker_available", lambda: False)
    monkeypatch.setattr(extractors.PyPdfDocumentExtractor, "extract",
                        lambda self, raw, context: DocumentIR(extractor="pypdf", extractor_version="t"))
    extractor = api(monkeypatch)
    monkeypatch.setattr(extractor, "extract", lambda *a: (_ for _ in ()).throw(glm.GlmOcrExtractionError("offline")))

    ir = extractors.extract_with_fallback(pdf(), extractor, {}, ok())
    assert ir.extractor == "pypdf" and "glm_ocr_failed_pypdf_fallback" in ir.health.flags
    with pytest.raises(glm.GlmOcrExtractionError):
        extractors.extract_with_fallback(pdf(), extractor, {"engine": "glm_ocr"}, ok())
    with pytest.raises(glm.GlmOcrExtractionError):  # an image has no other reader
        extractors.extract_with_fallback(png(), extractor, {}, ok())
    for refusal in (glm.GlmOcrConsentRequired("ok?"), SpendLimitExceeded("cap"), SpendCancelled("stop")):
        monkeypatch.setattr(extractor, "extract", lambda *a, refusal=refusal: (_ for _ in ()).throw(refusal))
        with pytest.raises(type(refusal)):
            extractors.extract_with_fallback(pdf(), extractor, {}, ok())

    monkeypatch.setattr(extractor, "extract", lambda *a: (_ for _ in ()).throw(glm.GlmOcrExtractionError("offline")))
    monkeypatch.setattr(extractors.PyPdfDocumentExtractor, "extract",
                        lambda self, raw, context: (_ for _ in ()).throw(ValueError("no extractable text")))
    with pytest.raises(extractors.ExtractionFallbackFailed, match="glm_ocr: offline; pypdf fallback: no extractable"):
        extractors.extract_with_fallback(pdf(), extractor, {}, ok())


def test_versions_name_backend_models_and_mapping_so_caches_re_extract(monkeypatch):
    from learnloop.ingest.hashing import extraction_request_hash

    hosted_extractor = api(monkeypatch)
    local = glm.GlmOcrDocumentExtractor(backend="local")
    assert hosted_extractor.version() == f"glm-ocr-0.9B+PP-DocLayout-V3+api+map{glm.MAP_VERSION}"
    assert local.model_versions() == {"backend": "local", "recognition": "glm-ocr-0.9B", "layout": "PP-DocLayout-V3"}

    def key(extractor):
        return extraction_request_hash(revision_id="r", extractor=extractor.name, extractor_version=extractor.version(),
                                       model_versions=extractor.model_versions(), config={}, ir_schema_version="ir-2")

    assert key(hosted_extractor) != key(local)


# -- the self-hosted server ---------------------------------------------------------------


class _GlmServer(BaseHTTPRequestHandler):
    """Answers like `python -m glmocr.server` (its _build_response)."""

    seen: list = []

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        type(self).seen.append((self.path, self.headers.get("Authorization"), body))
        units = [[[{"index": 0, "label": "text", "native_label": "paragraph_title", "content": f"## Image {i}",
                    "bbox_2d": [100, 100, 900, 200]},
                   {"index": 1, "label": "text", "native_label": "text", "content": "Words",
                    "bbox_2d": [100, 300, 900, 400]}]] for i, _ in enumerate(body["images"])]
        payload = units[0] if len(units) == 1 else units
        raw = json.dumps({"json_result": payload, "markdown_result": "", "layout_details": payload,
                          "md_results": "", "data_info": {"pages": []}, "usage": {}, "model": "glm-ocr",
                          "id": "chatcmpl-local", "created": 0}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args):
        pass


@pytest.fixture
def local_server(monkeypatch):
    from urllib.request import build_opener

    monkeypatch.setattr(glm, "_open", lambda request, timeout: build_opener(glm._NoRedirect).open(request, timeout=timeout))
    _GlmServer.seen = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), _GlmServer)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}/glmocr/parse"
    server.shutdown()
    server.server_close()


def test_the_local_backend_renders_pdf_pages_for_a_real_http_server(local_server):
    pytest.importorskip("pypdfium2")
    config = {"backend": "local", "local_url": local_server}
    assert glm.selected_backend(config) == "local"
    extractor = extractors.pdf_extractor_for({"glm_ocr": config})
    events = []
    with observe_model_calls(lambda a, e: events.append((a, e))):
        ir = extractor.extract(pdf(3), ExtractionContext("rev", page_selection=(1, 2)))

    ((path, authorization, body),) = _GlmServer.seen
    assert path == "/glmocr/parse" and authorization is None
    assert len(body["images"]) == 2
    assert all(base64.b64decode(uri.split(",", 1)[1]).startswith(b"\x89PNG") for uri in body["images"])
    assert [(b.page, b.block_type, b.text) for b in ir.blocks] == [
        (1, "SectionHeader", "Image 0"), (1, "Text", "Words"), (2, "SectionHeader", "Image 1"), (2, "Text", "Words"),
    ]
    assert ir.blocks[0].bbox == [61.2, 79.2, 550.8, 158.4]
    (done,) = finishes(events)
    assert done["cost"] == 0 and done["input_tokens"] == 0
    assert json.loads(done["usage_json"])["cost_basis"] == "self_hosted"


def test_the_local_backend_reads_an_image_as_one_page(local_server):
    extractor = glm.GlmOcrDocumentExtractor(config={"backend": "local", "local_url": local_server})
    ir = extractor.extract(png((1000, 2000)), ExtractionContext("rev"))
    assert _GlmServer.seen[0][2]["images"][0].startswith("data:image/png;base64,")
    assert ir.blocks[1].bbox == [100.0, 600.0, 900.0, 800.0]


def test_an_unanswering_local_server_is_not_selected(monkeypatch):
    with socket_closed_port() as url:
        assert glm.local_available({"local_url": url}) is False
        assert glm.selected_backend({"backend": "local", "local_url": url}) is None


class socket_closed_port:
    def __enter__(self):
        import socket

        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        self.port = sock.getsockname()[1]
        sock.close()
        return f"http://127.0.0.1:{self.port}/glmocr/parse"

    def __exit__(self, *exc):
        return False


# -- the durable import, the Reader and the legacy path ------------------------------------


def _jobs(repo, root):
    from learnloop.content.pipeline.jobs import DurableIngestJobs
    from learnloop.content.pipeline.runner import RunnerServices
    from tests.ux_phase1_support import CLOCK

    jobs = DurableIngestJobs()
    jobs.bind(repo, root, background=False, clock=CLOCK, services=RunnerServices(background_key_checks=False))
    jobs._ensure_worker = lambda: None
    return jobs


def test_an_add_asks_once_naming_z_ai_then_reads_and_records_the_spend(monkeypatch, tmp_path):
    from learnloop.content.pipeline.add_source import AddSourceOptions, metered_spend_usd
    from learnloop.vault.loader import load_vault
    from tests.ux_phase1_support import fresh_library, grant_consent, repository

    monkeypatch.setenv("ZAI_API_KEY", KEY)
    sent = record(monkeypatch)
    root = fresh_library(tmp_path)
    repo = repository(root)
    path = tmp_path / "paper.pdf"
    path.write_bytes(pdf(2))
    jobs = _jobs(repo, root)

    batch = jobs.enqueue_add_source(str(path), options=AddSourceOptions(), auto_build=False)
    jobs._require_runner().drain()
    (waiting,) = repo.ingest_jobs_for_batch(batch)
    assert waiting["error"]["code"] == "needs_upload_ok"
    assert "z.ai (GLM-OCR)" in waiting["error"]["message"] and sent == []

    grant_consent(root, "whole_files_zai")  # the OK naming z.ai
    jobs.resume_batch(batch)
    jobs._require_runner().drain()
    (done,) = repo.ingest_jobs_for_batch(batch)
    assert done["status"] == "completed", done.get("error")
    assert len(sent) == 1
    rows = repo.model_call_spend_rows()
    assert [row["provider"] for row in rows] == ["zai-glm-ocr"]
    assert metered_spend_usd(load_vault(root).config, rows) == pytest.approx(1200 * 0.03 / 1e6)


def test_a_book_carrying_the_retired_keep_local_choice_is_read_like_any_other(monkeypatch, tmp_path):
    """The per-book "keep this book on this computer" is retired (owner,
    2026-10-13; docs/reviews/reading-hardening.md, part 3): a book whose
    ``source_artifacts.keep_local`` is still set asks for the one-time OK
    naming z.ai like any other book and is read by GLM-OCR once it is given,
    and a stale ``keep_local`` on a job changes nothing (the landing onto
    main replaced the branch's kept-local tests with this one)."""

    import sqlite3

    from learnloop.content.pipeline.add_source import AddSourceOptions, add_source, source_status_line
    from learnloop.content.pipeline.jobs import default_extraction_identity
    from learnloop.vault.loader import load_vault
    from tests.ux_phase1_support import fresh_library, grant_consent, repository, set_config

    monkeypatch.setenv("ZAI_API_KEY", KEY)
    monkeypatch.setattr(extractors, "marker_available", lambda: False)
    sent = record(monkeypatch)
    root = fresh_library(tmp_path)
    repo = repository(root)
    path = tmp_path / "private.pdf"
    path.write_bytes(pdf(1))
    jobs = _jobs(repo, root)

    item = add_source(load_vault(root), jobs, str(path), AddSourceOptions())
    with sqlite3.connect(root / "state.sqlite") as connection:  # what an older library may hold
        connection.execute("UPDATE source_artifacts SET keep_local = 1 WHERE id = ?", (item["source_id"],))
    jobs._require_runner().drain()

    def the_import():
        return next(j for j in repo.ingest_jobs_for_batch(item["batch_id"]) if j["job_type"] == "import")

    assert the_import()["error"]["code"] == "needs_upload_ok" and sent == []
    line = source_status_line(repo, load_vault(root), item["source_id"])
    # Pages and the estimated cost where the OK is asked (re-read safety item 5).
    assert line["text"] == "Reading this document (1 page, less than $0.01) sends the whole file to z.ai (GLM-OCR)"
    assert line["action"] == {"kind": "allow_upload", "label": "OK"}

    grant_consent(root, "whole_files_zai")  # the OK naming z.ai
    jobs.resume_batch(item["batch_id"])
    jobs._require_runner().drain()
    done = the_import()
    assert done["status"] == "completed", done.get("error")
    assert len(sent) == 1 and "glm_ocr_api_selected" in done["result"]["health"]["flags"]

    set_config(root, {("ingest", "pdf", "engine"): "glm_ocr"})
    stale = SimpleNamespace(vault_root=root, payload={"keep_local": True}, job={"_keep_local": True})
    assert default_extraction_identity(_fetched(), "pdf", stale)["extractor"] == "glm_ocr"


def test_identity_hashes_the_choice_not_endpoints_prices_or_timeouts(monkeypatch, tmp_path):
    from learnloop.content.pipeline.jobs import default_extraction_identity
    from learnloop.content.pipeline.runner import FetchedBytes
    from tests.ux_phase1_support import fresh_library, grant_consent, set_config

    monkeypatch.setenv("ZAI_API_KEY", KEY)
    root = fresh_library(tmp_path)
    grant_consent(root, "whole_files_zai")  # the OK naming z.ai
    ctx = SimpleNamespace(vault_root=root, payload={}, job={})
    fetched = FetchedBytes(raw_bytes=pdf(1), content_type="application/pdf", original_uri="x.pdf", retrieved_at="now")
    before = default_extraction_identity(fetched, "pdf", ctx)
    set_config(root, {("ingest", "pdf", "glm_ocr", "price_per_million_tokens"): 0.5,
                      ("ingest", "pdf", "glm_ocr", "request_timeout_seconds"): 30,
                      ("ingest", "pdf", "glm_ocr", "api_url"): "https://open.bigmodel.cn/api/paas/v4/layout_parsing"})
    after = default_extraction_identity(fetched, "pdf", ctx)
    assert before == after
    assert before["extractor"] == "glm_ocr" and before["config"] == {}
    assert before["model_versions"]["backend"] == "api"


def test_an_image_import_needs_glm_and_reads_with_it(monkeypatch, tmp_path):
    from learnloop.content.pipeline.jobs import default_extract, default_extraction_identity
    from learnloop.content.pipeline.runner import FetchedBytes, IngestRunnerError
    from learnloop.ingest.resolution import resolve_source
    from tests.ux_phase1_support import fresh_library, grant_consent, set_config

    assert resolve_source("page.png").category == "image"
    assert resolve_source("https://example.invalid/scan.JPG").category == "image"
    root = fresh_library(tmp_path)
    grant_consent(root, "whole_files_zai")  # the OK naming z.ai
    ctx = SimpleNamespace(vault_root=root, payload={}, job={})
    fetched = FetchedBytes(raw_bytes=png(), content_type="image/png", original_uri="page.png", retrieved_at="now")
    with pytest.raises(IngestRunnerError) as caught:
        default_extraction_identity(fetched, "image", ctx)
    assert caught.value.code == "pdf_extractor_unavailable"

    monkeypatch.setenv("ZAI_API_KEY", KEY)
    sent = record(monkeypatch, lambda body: {"layout_details": [[region(0, "text", "Scan", [0, 0, 10, 10])]]})
    set_config(root, {("ingest", "pdf", "engine"): "pypdf"})  # a PDF-only choice does not apply to images
    identity = default_extraction_identity(fetched, "image", ctx)
    ir = default_extract(fetched, "image", ctx)
    assert identity["extractor"] == ir.extractor == "glm_ocr"
    assert [b.text for b in ir.blocks] == ["Scan"] and len(sent) == 1


def test_read_again_with_text_recognition_uses_glm_when_it_can(monkeypatch, tmp_path):
    from learnloop.content.pipeline.add_source import AddSourceOptions, text_recognition_available
    from learnloop.vault.loader import load_vault
    from tests.ux_phase1_support import fresh_library, repository, set_config

    monkeypatch.setattr(extractors, "marker_available", lambda: False)
    root = fresh_library(tmp_path)
    repo = repository(root)
    jobs = _jobs(repo, root)
    path = tmp_path / "scan.pdf"
    path.write_bytes(pdf(1))
    config = load_vault(root).config
    assert not text_recognition_available(config=config)

    monkeypatch.setenv("ZAI_API_KEY", KEY)
    assert text_recognition_available(config=config)
    set_config(root, {("ingest", "pdf", "engine"): "pypdf"})  # the reread overrides a pypdf setting
    batch = jobs.enqueue_add_source(str(path), options=AddSourceOptions(text_recognition=True), auto_build=False)
    assert repo.ingest_jobs_for_batch(batch)[0]["payload"]["pdf_config"] == {"engine": "glm_ocr"}
    monkeypatch.delenv("ZAI_API_KEY")  # without GLM-OCR, Marker's OCR is named
    batch = jobs.enqueue_add_source(str(path), options=AddSourceOptions(text_recognition=True), auto_build=False)
    assert repo.ingest_jobs_for_batch(batch)[0]["payload"]["pdf_config"] == {"engine": "marker", "force_ocr": True}


def test_the_preview_estimates_pages_and_names_the_upload(monkeypatch, tmp_path):
    from learnloop.content.pipeline.acquisition_preview import build_acquisition_preview
    from learnloop.vault.loader import load_vault
    from tests.ux_phase1_support import fresh_library, grant_consent, repository

    root = fresh_library(tmp_path)
    path = tmp_path / "book.pdf"
    path.write_bytes(pdf(2))
    image = tmp_path / "page.jpg"
    image.write_bytes(png())

    def items():
        return build_acquisition_preview(repository(root), load_vault(root).config,
                                         [str(path), str(image), "https://example.invalid/a.pdf"]).as_dict()["items"]

    monkeypatch.setattr(extractors, "marker_available", lambda: False)
    book, scan, link = items()
    assert book["configured_extractor"] == "pypdf" and book["extraction_estimate"] is None
    assert scan["configured_extractor"] == "text_recognition_unavailable"

    monkeypatch.setenv("ZAI_API_KEY", KEY)
    # Without the OK naming z.ai, an Ingest-screen import reads a PDF locally
    # (an image needs GLM-OCR, so it still asks).
    book, scan, link = items()
    assert book["configured_extractor"] == "pypdf" and book["potential_external"] == []
    assert scan["configured_extractor"] == "glm_ocr" and scan["potential_external"][0]["kind"] == "glm_ocr_upload"

    grant_consent(root, "whole_files_zai")
    book, scan, link = items()
    assert book["configured_extractor"] == "glm_ocr"
    assert book["extraction_estimate"]["total_tokens"] == 2 * glm.ESTIMATED_TOKENS_PER_PAGE
    assert book["extraction_estimate"]["estimated_usd"] == pytest.approx(2 * glm.ESTIMATED_TOKENS_PER_PAGE * 0.03 / 1e6)
    assert scan["extraction_estimate"]["pages"] == 1
    assert link["extraction_estimate"]["pages"] is None and link["extraction_estimate"]["estimated_usd"] is None
    assert book["potential_external"][0]["kind"] == "glm_ocr_upload"
    assert "z.ai (GLM-OCR)" in book["potential_external"][0]["reason"]


def test_the_legacy_path_uploads_only_with_the_ok_and_caches_by_backend(monkeypatch, tmp_path):
    from learnloop.config.schema import PdfIngestConfig
    from learnloop.content.sources.pdf_extraction import PdfExtractionError, extract_pdf_markdown

    monkeypatch.setenv("ZAI_API_KEY", KEY)
    monkeypatch.setattr("learnloop.content.sources.pdf_extraction.importlib.util.find_spec", lambda name: None)
    sent = record(monkeypatch)
    raw = pdf(1)

    with pytest.raises(PdfExtractionError, match="z.ai"):
        extract_pdf_markdown(raw, config=PdfIngestConfig(engine="glm_ocr"), cache_dir=tmp_path)
    with pytest.raises(PdfExtractionError):  # auto without the OK reads locally (a blank page: no text)
        extract_pdf_markdown(raw, config=PdfIngestConfig(), cache_dir=tmp_path)
    assert sent == []

    result = extract_pdf_markdown(raw, config=PdfIngestConfig(), cache_dir=tmp_path, whole_file_upload_allowed=True)
    assert result.engine == "glm_ocr" and result.markdown == "Page 0\n"
    config = PdfIngestConfig()
    config.glm_ocr.request_timeout_seconds = 30
    again = extract_pdf_markdown(raw, config=config, cache_dir=tmp_path, whole_file_upload_allowed=True)
    assert again.from_cache and len(sent) == 1


def test_remote_documents_download_raw_so_nothing_is_read_before_the_ok(monkeypatch, tmp_path):
    from learnloop.content.pipeline import source_ingestion
    from learnloop.content.pipeline.jobs import default_fetch
    from tests.ux_phase1_support import CLOCK

    raw = pdf()
    monkeypatch.setattr(source_ingestion, "_fetch_url", lambda *a, **kw: SimpleNamespace(
        raw_bytes=raw, content_type="application/pdf", original_uri="https://example.invalid/book.pdf",
        fetch_uri="https://example.invalid/book.pdf", retrieved_at="now", source_bytes=None))
    monkeypatch.setattr(source_ingestion, "_pdf_fetch_result", lambda *a, **kw: pytest.fail("read during download"))
    fetched = default_fetch("https://example.invalid/book.pdf", "pdf", SimpleNamespace(vault_root=tmp_path, clock=CLOCK))
    assert fetched.raw_bytes == raw


def test_settings_save_the_key_and_report_it(monkeypatch, tmp_path):
    from learnloop.config import global_settings_path
    from tests.test_ux_phase1_add_source import _held_ctx, call
    from tests.ux_phase1_support import fresh_library

    # A settings.env of this test's own: the session-wide isolated one is
    # shared by every xdist worker, and a vault load in another worker would
    # take the key into that process's environment for good.
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global_settings"))
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    ctx = _held_ctx(fresh_library(tmp_path))
    state = call(ctx, "get_settings", {})["ingest"]["textRecognition"]
    assert state["keyPresent"] is False and state["selectedBackend"] is None and state["envName"] == "ZAI_API_KEY"
    saved = call(ctx, "set_text_recognition_api_key", {"apiKey": KEY})
    assert saved["keyPresent"] is True and saved["keyHint"] == KEY[-4:] and saved["selectedBackend"] == "api"
    assert f"ZAI_API_KEY={KEY}" in global_settings_path().read_text()
    assert call(ctx, "get_settings", {})["ingest"]["textRecognition"]["keyPresent"] is True
    cleared = call(ctx, "set_text_recognition_api_key", {"apiKey": ""})
    assert cleared["keyPresent"] is False
    assert "ZAI_API_KEY" not in global_settings_path().read_text()


# -- the second review (docs/reviews/glm-ocr-ingest.md, "Second review") -------------------


def _ctx(root, payload=None, **job):
    return SimpleNamespace(vault_root=root, payload=dict(payload or {}), job=dict(job))


def _fetched(raw: bytes | None = None):
    from learnloop.content.pipeline.runner import FetchedBytes

    return FetchedBytes(raw_bytes=raw or pdf(1), content_type="application/pdf", original_uri="x.pdf", retrieved_at="now")


def plain_pypdf(monkeypatch):
    """pypdf reading some plain words (the test PDFs are blank pages)."""

    from learnloop.ingest.extractors import markdown_to_ir

    version = extractors.PyPdfDocumentExtractor().version()
    monkeypatch.setattr(extractors.PyPdfDocumentExtractor, "extract", lambda self, raw, context: markdown_to_ir(
        "Plain words", title=None, extractor_name="pypdf", extractor_version=version))


def test_r2_f1_a_local_repair_never_goes_to_a_glm_server_on_another_computer(monkeypatch, tmp_path):
    """Adapted at the landing onto main: the kept-local book this finding
    was about is retired, and the same guard now serves a repair the learner
    OK'd as local (third review F10)."""

    from learnloop.content.pipeline.jobs import default_extract, default_extraction_identity
    from tests.ux_phase1_support import fresh_library, set_config

    monkeypatch.setattr(extractors, "marker_available", lambda: False)
    monkeypatch.setattr(glm, "local_available", lambda config=None: True)  # the other computer answers
    plain_pypdf(monkeypatch)
    sent = record(monkeypatch, lambda body: {"layout_details": [[region(0, "text", "Words", [0, 0, 10, 10])]]})
    root = fresh_library(tmp_path)
    set_config(root, {("ingest", "pdf", "engine"): "glm_ocr",
                      ("ingest", "pdf", "glm_ocr", "backend"): "local",
                      ("ingest", "pdf", "glm_ocr", "local_url"): "http://gpu-box.invalid:5002/glmocr/parse"})
    assert default_extraction_identity(_fetched(), "pdf", _ctx(root, _local_repair=True))["extractor"] == "pypdf"
    assert default_extract(_fetched(), "pdf", _ctx(root, _local_repair=True)).extractor == "pypdf"
    assert sent == []
    # Any other reading may use the owner's own server (no whole-file OK).
    assert default_extraction_identity(_fetched(), "pdf", _ctx(root))["extractor"] == "glm_ocr"
    # On this computer, a local repair may use it too.
    set_config(root, {("ingest", "pdf", "glm_ocr", "local_url"): "http://127.0.0.1:5002/glmocr/parse"})
    assert default_extraction_identity(_fetched(), "pdf", _ctx(root, _local_repair=True))["extractor"] == "glm_ocr"


def test_r2_f2_an_import_without_the_ok_reads_locally_and_offers_text_recognition(monkeypatch, tmp_path):
    from learnloop.content.pipeline.add_source import source_status_line
    from learnloop.content.pipeline.runner import JobSpec
    from learnloop.vault.loader import load_vault
    from tests.ux_phase1_support import fresh_library, repository

    monkeypatch.setenv("ZAI_API_KEY", KEY)
    monkeypatch.setattr(extractors, "marker_available", lambda: False)
    plain_pypdf(monkeypatch)
    sent = record(monkeypatch)
    root = fresh_library(tmp_path)
    repo = repository(root)
    runner = _jobs(repo, root)._require_runner()
    path = tmp_path / "paper.pdf"
    path.write_bytes(pdf(2))

    # What `learnloop import` and the Ingest screen enqueue.
    batch = runner.enqueue_batch("import", [JobSpec("import", {"source": str(path)})])
    runner.drain()
    (job,) = repo.ingest_jobs_for_batch(batch)
    assert job["status"] == "completed", job.get("error")
    assert sent == []
    assert job["result"]["health"]["flags"][-1] == "glm_ocr_needs_upload_ok"
    line = source_status_line(repo, load_vault(root), job["result"]["source_id"])
    assert line["action"] == {"kind": "text_recognition", "label": "Read it with text recognition"}
    assert "z.ai" in line["details"] and "glm_ocr" not in line["details"]  # plain words (third review F14)

    # An explicit engine still asks rather than switch, and says where the OK is.
    batch = runner.enqueue_batch("import", [JobSpec("import", {"source": str(path), "pdf_config": {"engine": "glm_ocr"}})])
    runner.drain()
    (job,) = repo.ingest_jobs_for_batch(batch)
    assert job["error"]["code"] == "needs_upload_ok" and "Library" in job["error"]["message"]
    assert sent == []


def test_r2_f2_the_card_reads_it_again_with_text_recognition_after_the_ok(monkeypatch, tmp_path):
    from learnloop.content.pipeline.runner import JobSpec
    from tests.test_ux_phase1_add_source import _draining_ctx, call
    from tests.ux_phase1_support import fresh_library

    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global_settings"))
    monkeypatch.setenv("ZAI_API_KEY", KEY)
    monkeypatch.setattr(extractors, "marker_available", lambda: False)
    plain_pypdf(monkeypatch)
    sent = record(monkeypatch)
    root = fresh_library(tmp_path)
    ctx = _draining_ctx(root)
    path = tmp_path / "paper.pdf"
    path.write_bytes(pdf(2))
    ctx.ingest_jobs._require_runner().enqueue_batch("import", [JobSpec("import", {"source": str(path)})])
    ctx.ingest_jobs.drain_foreground()

    def card():
        return next(c for c in call(ctx, "get_source_library", {})["sources"])

    source_id = card()["sourceId"]
    assert card()["statusLine"]["action"] == {"kind": "text_recognition", "label": "Read it with text recognition"}
    call(ctx, "source_action", {"sourceId": source_id, "action": "text_recognition"})
    assert sent == []
    assert card()["statusLine"]["text"] == (
        "Reading this document (2 pages, less than $0.01) sends the whole file to z.ai (GLM-OCR)")
    call(ctx, "source_action", {"sourceId": source_id, "action": "allow_upload"})
    assert len(sent) == 1
    latest = ctx.repository.ingest_jobs_for_source(("import",), source_id)[0]
    assert latest["status"] == "completed" and "glm_ocr_api_selected" in latest["result"]["health"]["flags"]
    assert card()["statusLine"]["text"] == "No questions for this PDF yet"  # the plainer-reading line is gone


def test_r2_f3_an_earlier_whole_file_ok_never_covers_z_ai(monkeypatch, tmp_path):
    from learnloop.content.pipeline import add_source as core
    from tests.test_ux_phase1_add_source import _draining_ctx, call
    from tests.ux_phase1_support import fresh_library, grant_consent

    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global_settings"))
    monkeypatch.setenv("ZAI_API_KEY", KEY)
    sent = record(monkeypatch)
    root = fresh_library(tmp_path)
    grant_consent(root, "whole_files")  # said earlier to a recording or a whole PDF to "your AI"
    ctx = _draining_ctx(root)
    path = tmp_path / "paper.pdf"
    path.write_bytes(pdf(2))

    item = call(ctx, "add_source", {"sources": [str(path)]})["items"][0]
    assert sent == []
    card = next(c for c in call(ctx, "get_source_library", {})["sources"] if c["sourceId"] == item["sourceId"])
    assert card["statusLine"]["text"] == (
        "Reading this document (2 pages, less than $0.01) sends the whole file to z.ai (GLM-OCR)")
    assert card["statusLine"]["action"] == {"kind": "allow_upload", "label": "OK"}

    call(ctx, "source_action", {"sourceId": item["sourceId"], "action": "allow_upload"})
    config = ctx.vault.config
    assert config.ai.consent[core.GLM_OCR_UPLOAD_CONSENT].data_flow == "whole_files"
    assert core.file_upload_allowed(config, "glm_ocr_upload") and len(sent) == 1


def test_r2_f3_the_z_ai_ok_names_only_z_ai():
    from learnloop.config import LearnLoopConfig
    from learnloop.content.pipeline.add_source import GLM_OCR_UPLOAD_CONSENT, file_upload_allowed
    from learnloop.config.schema import AIConsentRecord

    config = LearnLoopConfig()
    config.ai.consent[GLM_OCR_UPLOAD_CONSENT] = AIConsentRecord(granted_at="2026-10-14T00:00:00Z", data_flow="whole_files")
    assert file_upload_allowed(config, "glm_ocr_upload")
    assert not file_upload_allowed(config, "pdf_upload") and not file_upload_allowed(config, "audio_transcription")


def test_r2_f5_a_timeout_is_tried_once_more_and_the_default_wait_is_the_sdks(monkeypatch):
    tries = []

    def fake(request, timeout):
        tries.append(timeout)
        if len(tries) == 1:
            raise URLError(TimeoutError("timed out"))
        return io.BytesIO(json.dumps(hosted()).encode())

    monkeypatch.setattr(glm, "_open", fake)
    api(monkeypatch).extract(pdf(), ok())
    assert tries == [300, 300]

    tries.clear()
    monkeypatch.setattr(glm, "_open", lambda request, timeout: tries.append(timeout) or (_ for _ in ()).throw(TimeoutError()))
    with pytest.raises(glm.GlmOcrExtractionError, match="did not answer in time"):
        api(monkeypatch).extract(pdf(), ok())
    assert len(tries) == 2


def test_r2_f5_a_window_glm_ocr_answered_wrongly_stops_before_the_next_is_paid(monkeypatch):
    sent = record(monkeypatch, lambda body: {"layout_details": []})
    with pytest.raises(glm.GlmOcrExtractionError, match="0 page"):
        api(monkeypatch).extract(pdf(65), ok())
    assert len(sent) == 1


class _CutOff:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        import http.client

        raise http.client.IncompleteRead(b"{\"layout_details\": [")


def test_r2_f6_a_cut_off_answer_or_an_unrenderable_page_falls_back_under_auto(monkeypatch):
    monkeypatch.setattr(glm, "_open", lambda request, timeout: _CutOff())
    with pytest.raises(glm.GlmOcrExtractionError, match="cut off"):
        api(monkeypatch).extract(pdf(), ok())
    monkeypatch.setattr(extractors, "marker_available", lambda: False)
    plain_pypdf(monkeypatch)
    ir = extractors.extract_with_fallback(pdf(), api(monkeypatch), {}, ok())
    assert ir.extractor == "pypdf" and "glm_ocr_failed_pypdf_fallback" in ir.health.flags

    pytest.importorskip("pypdfium2")
    with pytest.raises(glm.GlmOcrExtractionError, match="render"):
        glm._render_pages(b"%PDF-1.4 not really a pdf", [0])


def test_r2_f8_page_sizes_come_from_data_info_before_a_regions_own_size():
    # The region's width/height are its own (980x159), the page is 1224x1584.
    result = {"layout_details": [[region(0, "text", "Words", [122, 158, 1102, 317], width=980, height=159)]],
              "data_info": {"pages": [{"width": 1224, "height": 1584}]}}
    ir = glm.responses_to_ir([(result, [0])], sizes=[(612.0, 792.0)], outline=[], version="t")
    assert ir.blocks[0].bbox == [61.0, 79.0, 551.0, 158.5]
    # Without data_info, a region's width/height still serve.
    alone = {"layout_details": [[region(0, "text", "Words", [122, 158, 1102, 317])]]}
    ir = glm.responses_to_ir([(alone, [0])], sizes=[(612.0, 792.0)], outline=[], version="t")
    assert ir.blocks[0].bbox == [61.0, 79.0, 551.0, 158.5]


def test_r2_f9_a_scan_offers_text_recognition_or_where_to_set_it_up(monkeypatch):
    """Adapted at the landing onto main: the kept-local scan lines are
    retired with the per-book choice; what remains is that a scan offers the
    re-read when a key is set and Settings (where the key goes) when not."""

    from learnloop.config import LearnLoopConfig
    from learnloop.content.pipeline import add_source as core

    monkeypatch.setattr(extractors, "marker_available", lambda: False)
    config = LearnLoopConfig()
    scan = {"error": {"code": "pdf_extraction_failed", "message": "no extractable text (likely scanned)"}}
    line = core._import_failure_line(scan, "pdf", config=config)
    assert line["action"] == {"kind": "open_settings", "label": "Set it up"} and "z.ai API key" in line["details"]

    monkeypatch.setattr(core, "_completed_extraction", lambda repo, source_id: ("src_1", "ext_1"))
    repo = SimpleNamespace(get_extraction_run=lambda extraction_id: {
        "health": {"flags": [], "pages": [{"page": 0, "flags": ["image_only_page"]}]}})
    assert core._health_line(repo, "src_1", config=config)["action"]["kind"] == "open_settings"
    monkeypatch.setenv("ZAI_API_KEY", KEY)  # the key reads it
    assert core._import_failure_line(scan, "pdf", config=config)["action"]["kind"] == "text_recognition"
    assert core._health_line(repo, "src_1", config=config)["action"]["kind"] == "text_recognition"


def test_r2_f4_cancelling_stops_the_windows_not_yet_sent(monkeypatch, tmp_path):
    """Adapted at the landing onto main: the keep-local half (a book kept
    on this computer part-way through) is retired with the per-book choice."""

    from learnloop.ai.spend import SpendCancelled
    from learnloop.content.pipeline.jobs import default_extract
    from tests.ux_phase1_support import fresh_library, grant_consent

    monkeypatch.setenv("ZAI_API_KEY", KEY)
    sent = record(monkeypatch)
    root = fresh_library(tmp_path)
    grant_consent(root, "whole_files_zai")
    book = _fetched(pdf(65))  # three windows

    # The batch is cancelled after the first window went out.
    cancelled = _ctx(root)
    cancelled.repo = SimpleNamespace(model_checkpoint=lambda key: None, save_model_checkpoint=lambda *a, **kw: None)
    cancelled.cancelled = lambda: len(sent) >= 1
    with pytest.raises(SpendCancelled):
        default_extract(book, "pdf", cancelled)
    assert len(sent) == 1


def test_r2_f5_paid_windows_are_kept_so_trying_again_pays_only_for_the_rest(monkeypatch, tmp_path):
    from learnloop.content.pipeline.add_source import AddSourceOptions
    from tests.ux_phase1_support import fresh_library, grant_consent, repository

    monkeypatch.setenv("ZAI_API_KEY", KEY)
    monkeypatch.setattr(extractors, "marker_available", lambda: False)
    failing = {"on": True}

    def respond(body):
        if failing["on"] and len(sent) == 3:
            raise HTTPError(glm.API_URL, 400, "bad", {}, io.BytesIO(b"{}"))
        return hosted(body["end_page_id"] - body["start_page_id"] + 1)

    sent = record(monkeypatch, respond)
    root = fresh_library(tmp_path)
    grant_consent(root, "whole_files_zai")
    repo = repository(root)
    jobs = _jobs(repo, root)
    path = tmp_path / "long.pdf"
    path.write_bytes(pdf(65))

    batch = jobs.enqueue_add_source(str(path), options=AddSourceOptions(), auto_build=False)
    jobs._require_runner().drain()
    (job,) = repo.ingest_jobs_for_batch(batch)
    assert job["status"] == "failed" and len(sent) == 3  # the third window failed (blank pages: no fallback text)

    failing["on"] = False
    jobs.resume_batch(batch)
    jobs._require_runner().drain()
    (job,) = repo.ingest_jobs_for_batch(batch)
    assert job["status"] == "completed", job.get("error")
    assert len(sent) == 4  # only the window not yet answered
    assert job["result"]["block_count"] == 65


def test_r2_f7_a_stand_in_reading_is_stored_with_its_own_model_versions(monkeypatch, tmp_path):
    from learnloop.content.pipeline.add_source import AddSourceOptions
    from tests.ux_phase1_support import fresh_library, grant_consent, repository

    monkeypatch.setenv("ZAI_API_KEY", KEY)
    monkeypatch.setattr(extractors, "marker_available", lambda: False)
    plain_pypdf(monkeypatch)
    sent = record(monkeypatch, lambda body: (_ for _ in ()).throw(URLError("offline")))
    root = fresh_library(tmp_path)
    grant_consent(root, "whole_files_zai")
    repo = repository(root)
    jobs = _jobs(repo, root)
    path = tmp_path / "paper.pdf"
    path.write_bytes(pdf(1))

    batch = jobs.enqueue_add_source(str(path), options=AddSourceOptions(), auto_build=False)
    jobs._require_runner().drain()
    (job,) = repo.ingest_jobs_for_batch(batch)
    assert job["status"] == "completed", job.get("error")
    assert len(sent) == 1 and "glm_ocr_failed_pypdf_fallback" in job["result"]["health"]["flags"]
    run = repo.get_extraction_run(job["result"]["extraction_id"])
    assert run["extractor"] == "pypdf"
    assert run["model_versions"] == {"fallback_from": "glm_ocr"}


# -- the third review (docs/reviews/glm-ocr-ingest.md, "Third review") ---------------------


def _repairable(repo, root, result) -> None:
    """Point a read book's revision at its file the way a link's URL is
    stored: a file Add stores ``file://``, which a repair cannot fetch."""

    import sqlite3

    revision = repo.get_source_revision(result["revision_id"])
    path = revision["original_uri"].removeprefix("file://")
    with sqlite3.connect(root / "state.sqlite") as connection:
        connection.execute("UPDATE source_revisions SET original_uri=? WHERE id=?", (path, result["revision_id"]))


@pytest.mark.parametrize("engine", ["auto", "glm_ocr"])
def test_r3_f10_a_local_repair_never_leaves_this_computer(monkeypatch, tmp_path, engine):
    """Adapted at the landing onto main: the kept-local book is retired, so
    one book is repaired. A repair OK'd as local is read here whatever the
    engine; one OK'd with "external VLM" goes to z.ai (the OK naming z.ai
    given)."""

    from learnloop.content.pipeline.add_source import AddSourceOptions
    from tests.ux_phase1_support import fresh_library, grant_consent, repository, set_config

    monkeypatch.setenv("ZAI_API_KEY", KEY)
    monkeypatch.setattr(extractors, "marker_available", lambda: False)
    plain_pypdf(monkeypatch)
    sent = record(monkeypatch)
    root = fresh_library(tmp_path)
    grant_consent(root, "whole_files_zai")  # given once, on any Add
    repo = repository(root)
    jobs = _jobs(repo, root)
    path = tmp_path / "book.pdf"
    path.write_bytes(pdf(3))
    batch = jobs.enqueue_add_source(str(path), options=AddSourceOptions(), auto_build=False)
    jobs._require_runner().drain()
    (job,) = repo.ingest_jobs_for_batch(batch)
    assert job["status"] == "completed", job.get("error")
    _repairable(repo, root, job["result"])
    read = job["result"]
    assert len(sent) == 1
    set_config(root, {("ingest", "pdf", "engine"): engine})
    sent.clear()

    # OutlineAndPlan's repair without "external VLM", and `learnloop repair-extraction` without --use-llm.
    local = {"provider": "local", "purpose": "extraction_repair", "pages": ["2"], "external": False}
    external = {"provider": "external_vlm", "purpose": "extraction_repair", "pages": ["2"], "external": True}
    for consent, reader in ((local, "pypdf"), (external, "glm_ocr")):
        repair = jobs.enqueue_extraction_repair(
            revision_id=read["revision_id"], pages=[1], repair_options={"force_ocr": True},
            consent=consent, parent_extraction_id=read["extraction_id"],
        )
        jobs._require_runner().drain()
        (job,) = repo.ingest_jobs_for_batch(repair)
        assert job["status"] == "completed", job.get("error")
        assert repo.get_extraction_run(job["result"]["repair_extraction_id"])["extractor"] == reader
        assert len(sent) == (0 if consent is local else 1)


@pytest.mark.parametrize("engine", ["auto", "glm_ocr"])
def test_r3_f10_a_local_repair_of_an_image_sends_nothing_and_says_why(monkeypatch, tmp_path, engine):
    """Only text recognition reads an image, so a repair OK'd as local has no
    reader here: it refuses rather than upload the image (or say a key is
    missing when one is set)."""

    from learnloop.content.pipeline.add_source import AddSourceOptions
    from tests.ux_phase1_support import fresh_library, grant_consent, repository, set_config

    monkeypatch.setenv("ZAI_API_KEY", KEY)
    monkeypatch.setattr(extractors, "marker_available", lambda: False)
    sent = record(monkeypatch, lambda body: {"layout_details": [[region(0, "text", "Scan", [0, 0, 10, 10])]]})
    root = fresh_library(tmp_path)
    grant_consent(root, "whole_files_zai")
    repo = repository(root)
    jobs = _jobs(repo, root)
    path = tmp_path / "page.png"
    path.write_bytes(png())
    batch = jobs.enqueue_add_source(str(path), options=AddSourceOptions(), auto_build=False)
    jobs._require_runner().drain()
    (job,) = repo.ingest_jobs_for_batch(batch)
    assert job["status"] == "completed", job.get("error")
    assert len(sent) == 1
    _repairable(repo, root, job["result"])
    set_config(root, {("ingest", "pdf", "engine"): engine})
    sent.clear()
    # The Add's stored answer would hide what the repair selects (it is reused
    # for the same file and page); a repair of other pages has none.
    import sqlite3

    with sqlite3.connect(root / "state.sqlite") as connection:
        connection.execute("DELETE FROM model_work_checkpoints")

    local = {"provider": "local", "purpose": "extraction_repair", "pages": ["1"], "external": False}
    repair = jobs.enqueue_extraction_repair(
        revision_id=job["result"]["revision_id"], pages=[0], repair_options={"force_ocr": True},
        consent=local, parent_extraction_id=job["result"]["extraction_id"],
    )
    jobs._require_runner().drain()
    (failed,) = repo.ingest_jobs_for_batch(repair)
    assert sent == []
    assert failed["status"] == "failed"
    message = failed["error"]["message"]
    assert "on this computer" in message and "external VLM" in message and "API key" not in message


@pytest.mark.parametrize("kind", ["scan", "image"])
def test_r3_f2_a_scan_or_image_imported_without_the_ok_asks_for_it_on_its_card(monkeypatch, tmp_path, kind):
    from learnloop.content.pipeline.runner import JobSpec
    from tests.test_ux_phase1_add_source import _draining_ctx, call
    from tests.ux_phase1_support import fresh_library

    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global_settings"))
    monkeypatch.setenv("ZAI_API_KEY", KEY)
    monkeypatch.setattr(extractors, "marker_available", lambda: False)
    image = kind == "image"
    sent = record(monkeypatch, (lambda body: {"layout_details": [[region(0, "text", "Scan", [0, 0, 10, 10])]]})
                  if image else None)
    root = fresh_library(tmp_path)
    ctx = _draining_ctx(root)
    path = tmp_path / ("page.png" if image else "scan.pdf")
    path.write_bytes(png() if image else pdf(2))  # blank pages: pypdf finds no text, as in a scan

    # What `learnloop import` and the Ingest screen enqueue.
    batch = ctx.ingest_jobs._require_runner().enqueue_batch("import", [JobSpec("import", {"source": str(path)})])
    ctx.ingest_jobs.drain_foreground()
    (job,) = ctx.repository.ingest_jobs_for_batch(batch)
    assert job["error"]["code"] == "needs_upload_ok" and job["error"]["details"]["flow"] == "glm_ocr_upload"
    # The pages and cost the card's OK line shows (re-read safety item 5).
    assert job["error"]["details"]["pages"] == (1 if image else 2)
    message = job["error"]["message"]
    assert "z.ai" in message and "card in the Library" in message and "marker-pdf" not in message
    assert ("PDF engine" in message) is False
    assert sent == []

    library = call(ctx, "get_source_library", {})
    assert library["pending"] == []
    (card,) = library["sources"]
    assert card["statusLine"]["action"] == {"kind": "allow_upload", "label": "OK"}
    call(ctx, "source_action", {"sourceId": card["sourceId"], "action": "allow_upload"})
    assert len(sent) == 1
    (job,) = ctx.repository.ingest_jobs_for_batch(batch)
    assert job["status"] == "completed", job.get("error")
    assert "glm_ocr_api_selected" in job["result"]["health"]["flags"]


def test_r3_f7_a_double_fallback_stores_the_versions_of_what_read_it(monkeypatch, tmp_path):
    from learnloop.content.pipeline.add_source import AddSourceOptions
    from tests.ux_phase1_support import fresh_library, grant_consent, repository

    monkeypatch.setenv("ZAI_API_KEY", KEY)
    monkeypatch.setattr(extractors, "marker_available", lambda: True)  # installed, but it fails

    def marker_fails(self, raw, context):
        raise RuntimeError("marker could not read it")

    monkeypatch.setattr(extractors.MarkerDocumentExtractor, "extract", marker_fails)
    plain_pypdf(monkeypatch)
    record(monkeypatch, lambda body: (_ for _ in ()).throw(URLError("offline")))
    root = fresh_library(tmp_path)
    grant_consent(root, "whole_files_zai")
    repo = repository(root)
    jobs = _jobs(repo, root)
    path = tmp_path / "paper.pdf"
    path.write_bytes(pdf(1))

    batch = jobs.enqueue_add_source(str(path), options=AddSourceOptions(), auto_build=False)
    jobs._require_runner().drain()
    (job,) = repo.ingest_jobs_for_batch(batch)
    assert job["status"] == "completed", job.get("error")
    assert {"glm_ocr_failed_marker_fallback", "marker_failed_pypdf_fallback"} <= set(job["result"]["health"]["flags"])
    run = repo.get_extraction_run(job["result"]["extraction_id"])
    assert run["extractor"] == "pypdf"
    assert run["model_versions"] == {"fallback_from": "glm_ocr"}


def test_r3_f13_a_stored_window_that_no_longer_reads_is_paid_for_once(monkeypatch, tmp_path):
    import hashlib

    from learnloop.content.pipeline.jobs import _ModelCheckpoints
    from tests.ux_phase1_support import fresh_library, repository

    sent = record(monkeypatch)
    repo = repository(fresh_library(tmp_path))
    extractor = api(monkeypatch)
    raw = pdf(2)
    key = extractor._checkpoint_key(hashlib.sha256(raw).hexdigest(), [0, 1])
    # An answer saved under an earlier mapping that today's can't read.
    repo.save_model_checkpoint(key, purpose="glm_ocr_window", result={"layout_details": []})
    for _ in range(2):
        ir = extractor.extract(raw, ok(checkpoints=_ModelCheckpoints(repo)))
        assert [block.page for block in ir.blocks] == [0, 1]
    assert len(sent) == 1  # asked once, then the new answer is the one kept


def test_r3_f14_the_cards_details_are_plain_words(monkeypatch):
    from learnloop.config import LearnLoopConfig
    from learnloop.content.pipeline import add_source as core

    monkeypatch.setenv("ZAI_API_KEY", KEY)
    monkeypatch.setattr(extractors, "marker_available", lambda: False)
    monkeypatch.setattr(core, "_completed_extraction", lambda repo, source_id: ("src_1", "ext_1"))
    config = LearnLoopConfig()
    for flag in ("glm_ocr_needs_upload_ok", "glm_ocr_failed_pypdf_fallback", "glm_ocr_failed_marker_fallback"):
        repo = SimpleNamespace(get_extraction_run=lambda extraction_id: {
            "health": {"flags": [flag, "glm_ocr_api_selected"], "pages": []}})
        line = core._health_line(repo, "src_1", config=config)
        assert line["details"] and "_" not in line["details"], line


# -- the landing onto main (docs/reviews/glm-ocr-ingest.md, "Landing onto main") -----------


@pytest.mark.parametrize("path", ["hosted_windows", "fallback", "scan_after_the_ok"])
def test_every_glm_ocr_reading_queues_the_source_block_backfill(monkeypatch, tmp_path, path):
    """Composed with the tutor delivery fixes: a completed extraction queues
    its source's block-vector backfill when both embedding switches are on,
    whichever way GLM-OCR read it (windowed hosted windows, a local stand-in
    after a failure, a scan read once its OK was given)."""

    from learnloop.content.pipeline.add_source import AddSourceOptions
    from learnloop.content.pipeline.jobs import DurableIngestJobs
    from learnloop.content.pipeline.runner import JobSpec, RunnerServices
    from learnloop.ingest.extractors import markdown_to_ir
    from learnloop.source_retrieval.source_vectors import SOURCE_VECTORS_JOB
    from tests.practice_index_fakes import EMBED_DIMS, HashingEmbedder
    from tests.ux_phase1_support import CLOCK, fresh_library, grant_consent, repository, set_config

    words = "Eigenvalues are the roots of the characteristic polynomial of page {}."
    monkeypatch.setenv("ZAI_API_KEY", KEY)
    monkeypatch.setattr(extractors, "marker_available", lambda: False)
    version = extractors.PyPdfDocumentExtractor().version()
    monkeypatch.setattr(extractors.PyPdfDocumentExtractor, "extract", lambda self, raw, context: (
        markdown_to_ir(words.format("one"), title=None, extractor_name="pypdf", extractor_version=version)
        if path == "fallback" else (_ for _ in ()).throw(ValueError("no extractable text (likely scanned)"))))

    def respond(body):
        if path == "fallback":
            raise URLError("offline")
        first, last = body.get("start_page_id", 1), body.get("end_page_id", 1)
        return {"layout_details": [[region(0, "text", words.format(page), [122, 158, 1102, 317])]
                                   for page in range(first, last + 1)],
                "data_info": {"pages": [{"width": 1224, "height": 1584}] * (last - first + 1)}}

    sent = record(monkeypatch, respond)
    root = fresh_library(tmp_path)
    set_config(root, {("embedding", "enabled"): True, ("embedding", "backfill_enabled"): True,
                      ("embedding", "dimensions"): EMBED_DIMS})
    repo = repository(root)
    jobs = DurableIngestJobs()
    jobs.bind(repo, root, background=False, clock=CLOCK, services=RunnerServices(
        background_key_checks=False, embedding_client_factory=lambda _ctx: HashingEmbedder()))
    jobs._ensure_worker = lambda: None
    runner = jobs._require_runner()
    book = tmp_path / "book.pdf"

    if path == "scan_after_the_ok":
        book.write_bytes(pdf(2))  # blank pages: the local reading finds no text
        batch = runner.enqueue_batch("import", [JobSpec("import", {"source": str(book)})])  # the Ingest screen
        runner.drain()
        (waiting,) = repo.ingest_jobs_for_batch(batch)
        assert waiting["error"]["code"] == "needs_upload_ok" and sent == []
        grant_consent(root, "whole_files_zai")
        jobs.resume_batch(batch)
    else:
        grant_consent(root, "whole_files_zai")
        book.write_bytes(pdf(65 if path == "hosted_windows" else 1))
        batch = jobs.enqueue_add_source(str(book), options=AddSourceOptions(), auto_build=False)
    runner.drain()
    (job,) = repo.ingest_jobs_for_batch(batch)
    assert job["status"] == "completed", job.get("error")
    flags = job["result"]["health"]["flags"]
    if path == "hosted_windows":
        assert len(sent) == 3 and "glm_ocr_api_selected" in flags
    elif path == "fallback":
        assert "glm_ocr_failed_pypdf_fallback" in flags
    else:
        assert len(sent) == 1 and "glm_ocr_api_selected" in flags
    queued = [j for j in repo.ingest_jobs_by_types((SOURCE_VECTORS_JOB,))]
    assert [j["payload"]["extraction_id"] for j in queued] == [job["result"]["extraction_id"]]
    assert queued[0]["status"] == "completed", queued[0].get("error")
