"""Reader RW5a: region selection sends only its crop (spec §8.1 row 46, §8.5 privacy; G45).

A Ctrl+drag box over a figure on the original page is cropped by
``build_block_region`` (the box clipped to the figure block's own box) and
only that crop goes to the figure author, as an image, with the caption and
the paragraphs around it. A route that cannot read images is refused before
any call; ``figures.region_enabled`` off refuses a region.
"""

from __future__ import annotations

import base64
import json

import pytest

import learnloop.reader.span_view as SV
from learnloop_sidecar.errors import SidecarError
from tests.figure_fixtures import (
    EXTRACTION,
    FIGURE_BBOX,
    AuthorFake,
    build,
    build_figure_vault,
    call,
    context,
    flagship,
    rows,
    set_config,
)

PAGE_RENDERS: list[object] = []


@pytest.fixture
def crops(monkeypatch):
    """The PDF crop as a recorder: each crop's bytes name its box; a whole
    page render is recorded too (it must never be sent)."""

    made: list[list[float]] = []

    def crop(path, page, bbox):
        made.append([float(value) for value in bbox])
        data = ("CROP:" + json.dumps([round(float(value), 2) for value in bbox])).encode()
        return "data:image/png;base64," + base64.b64encode(data).decode("ascii"), [612.0, 792.0]

    def page_render(path, page):
        PAGE_RENDERS.append((path, page))
        return "data:image/png;base64," + base64.b64encode(b"WHOLE PAGE").decode("ascii"), [612.0, 792.0]

    monkeypatch.setattr(SV, "_original_pdf_for", lambda repo, extraction_id: "book.pdf")
    monkeypatch.setattr(SV, "_original_pdf_path", lambda repo, revision, uri: "book.pdf")
    monkeypatch.setattr(SV, "_local_pdf_block_crop", crop)
    monkeypatch.setattr(SV, "_local_pdf_page_render", page_render)
    PAGE_RENDERS.clear()
    return made


REGION = {"spanId": "p4", "bbox": [150.0, 120.0, 260.0, 220.0]}


def test_a_region_sends_only_its_crop(tmp_path, crops):
    paths, repository = build_figure_vault(tmp_path / "vault")
    author = AuthorFake([flagship(kind="illustrative")], images=True)
    figure = build(context(paths.root, author=author), {"extractionId": EXTRACTION, "spanIds": [], "region": REGION})[
        "figure"]
    assert figure["verification"] == "illustrative"
    assert crops == [[150.0, 120.0, 260.0, 220.0]] and not PAGE_RENDERS
    (images,) = author.request_images
    assert images == (("image/png", b"CROP:[150.0, 120.0, 260.0, 220.0]"),)
    (sent,) = author.contexts
    assert sent["request"] == "region of a figure"
    assert sent["image"]["sha256"] and [block["span_id"] for block in sent["passage"]] == ["p4"]
    # The caption and the paragraphs around it go too, as text.
    assert [block["span_id"] for block in sent["around"]] == ["p2", "p3", "p5", "p6"]
    (row,) = rows(repository, "interactive_figures")
    assert json.loads(row["region_json"]) == {"bbox": [150.0, 120.0, 260.0, 220.0], "span_id": "p4"}
    assert row["asset_id"] == "p4"
    events = {e["payload"]["event"] for e in repository.reader_interaction_events(kind="reader_action_invoked")}
    assert {"figure_requested", "figure_region_selected"} <= events


def test_a_box_beyond_the_figure_is_clipped_to_it(tmp_path, crops):
    paths, repository = build_figure_vault(tmp_path / "vault")
    author = AuthorFake([flagship(kind="illustrative")], images=True)
    region = {"spanId": "p4", "bbox": [50.0, 50.0, 300.0, 900.0]}
    build(context(paths.root, author=author), {"extractionId": EXTRACTION, "spanIds": [], "region": region})
    assert crops == [[100.0, 100.0, 300.0, 300.0]]
    assert FIGURE_BBOX[0] <= crops[0][0] and crops[0][3] <= FIGURE_BBOX[3]


def test_a_region_outside_the_figure_crops_nothing_and_calls_nothing(tmp_path, crops):
    paths, _repository = build_figure_vault(tmp_path / "vault")
    author = AuthorFake(images=True)
    with pytest.raises(SidecarError) as caught:
        build(context(paths.root, author=author),
              {"extractionId": EXTRACTION, "spanIds": [], "region": {"spanId": "p4", "bbox": [500, 500, 600, 600]}})
    assert caught.value.code == "region_unreadable" and author.calls == 0 and crops == []


def test_a_route_without_image_input_is_refused_before_any_call(tmp_path, crops):
    paths, _repository = build_figure_vault(tmp_path / "vault")
    author = AuthorFake(images=False)
    with pytest.raises(SidecarError) as caught:
        build(context(paths.root, author=author), {"extractionId": EXTRACTION, "spanIds": [], "region": REGION})
    assert caught.value.code == "no_image_input" and author.calls == 0


def test_a_figure_block_sends_its_crop_only_when_the_route_reads_images(tmp_path, crops):
    paths, _repository = build_figure_vault(tmp_path / "vault")
    reads = AuthorFake([flagship(kind="illustrative")], images=True)
    build(context(paths.root, author=reads), {"extractionId": EXTRACTION, "spanIds": ["p4"]})
    assert reads.request_images[0] == (("image/png", b"CROP:" + json.dumps(FIGURE_BBOX).encode()),)
    text_only = AuthorFake([flagship(kind="illustrative")], images=False)
    build(context(paths.root, author=text_only), {"extractionId": EXTRACTION, "spanIds": ["p4", "p5"]})
    assert text_only.request_images == [()] and text_only.contexts[0]["image"] is None
    assert not PAGE_RENDERS


def test_a_selection_without_a_figure_sends_no_image(tmp_path, crops):
    paths, _repository = build_figure_vault(tmp_path / "vault")
    author = AuthorFake([flagship(kind="illustrative")], images=True)
    build(context(paths.root, author=author), {"extractionId": EXTRACTION, "spanIds": ["p3"]})
    assert author.request_images == [()] and crops == []


def test_region_switch_off_refuses_a_region(tmp_path, crops):
    paths, _repository = build_figure_vault(tmp_path / "vault")
    set_config(paths, "figures", region_enabled=False)
    ctx = context(paths.root, author=AuthorFake(images=True))
    assert call(ctx, "reader.prompt_contract", {})["figures"]["region"] is False
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.figure_request", {"extractionId": EXTRACTION, "spanIds": [], "region": REGION})
    assert caught.value.code == "region_disabled" and crops == []


def test_an_image_request_is_refused_by_a_transport_that_cannot_read_images():
    from learnloop.ai.errors import AIProviderUnavailable
    from learnloop.ai.transport import execute_structured_operation
    from learnloop.figures.routes import FigureAuthorOutputV1

    class TextOnly:
        provider_name = "text_only"
        provider_type = "openai_chat"
        model = "m"
        called = False

        def supports(self, capability):
            return capability == "structured_completion"

        def complete(self, request):  # pragma: no cover - never reached
            TextOnly.called = True

    with pytest.raises(AIProviderUnavailable):
        execute_structured_operation(TextOnly(), purpose="figure_author", prompt="{}", result_model=FigureAuthorOutputV1,
                                     images=(("image/png", b"x"),))
    assert TextOnly.called is False


def test_the_openai_chat_transport_sends_image_parts_only_for_an_image_profile(monkeypatch):
    from learnloop.ai.providers.openai_chat import OpenAIChatProviderClient
    from learnloop.ai.transport import IMAGE_INPUT, StructuredRequest
    from learnloop.config import AIProviderConfig
    from learnloop.figures.routes import FigureAuthorOutputV1

    monkeypatch.setenv("FAKE_KEY", "x")
    profile = AIProviderConfig(type="openai_chat", model="m", base_url="http://127.0.0.1:9", api_key_env="FAKE_KEY",
                               input_modalities=["text", "image"])
    client = OpenAIChatProviderClient("vision", profile)
    assert client.supports(IMAGE_INPUT)
    plain = OpenAIChatProviderClient("plain", AIProviderConfig(type="openai_chat", model="m",
                                                               base_url="http://127.0.0.1:9", api_key_env="FAKE_KEY"))
    assert not plain.supports(IMAGE_INPUT)
    sent: list = []
    monkeypatch.setattr(client, "_run_json_messages", lambda messages, model: sent.append(messages) or None)
    client.complete(StructuredRequest(purpose="figure_author", prompt="hello", result_model=FigureAuthorOutputV1,
                                      images=(("image/png", b"PNG"),)))
    user = sent[0][1]["content"]
    assert user[0] == {"type": "text", "text": "hello"}
    assert user[1] == {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(b"PNG").decode()}}
