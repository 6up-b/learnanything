"""Mobile v2 §2.3 (stage V4): an image, page or asset prompt becomes phone-eligible once the host serves its bytes.

PR-6's reasons stay for every target the host does not serve by content address (a path, a remote image, raw
HTML, an ``llpdf:`` link that names no stored file); only targets in the vault's originals store, and of the
right kind (a page of a stored PDF, a stored image), are lifted, and only under the host's ``phone_reader``
(``media=True``). Off, the reasons are PR-6's exactly; the desktop never asks.
"""

from __future__ import annotations

import hashlib
import io
from types import SimpleNamespace

import pytest

from learnloop.scheduling import device_eligibility as DE


def _png() -> bytes:
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (2, 2)).save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def store(tmp_path):
    """A synthetic vault with a stored image and a real three-page book its Reader covers (Codex review F10: a
    target is lifted only when the host's page or asset endpoint serves it, so a header-only file is not)."""

    pytest.importorskip("pypdfium2")
    from learnloop.db.repositories import Repository
    from learnloop.ingest.originals import store_original_bytes
    from learnloop.vault.loader import load_vault
    from tests.helpers import create_basic_vault
    from tests.test_mobile_v4_reader import add_book

    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    digest = add_book(paths.root, repository, held_out=False)
    image = _png()
    names = {"image": "sha256-" + hashlib.sha256(image).hexdigest(), "pdf": "sha256-" + digest.split(":", 1)[1]}
    store_original_bytes(paths.root, "sha256:" + names["image"][7:], image)
    return load_vault(paths.root), names


def _item(prompt: str):
    return SimpleNamespace(id="pi_x", practice_mode="short_answer", teach_back_source=None, error_hunt=None,
                           laddered_stem=None, prompt=prompt, provenance=None, lesson_id=None, lifecycle=None)


def _reason(vault, prompt: str, *, media: bool) -> str | None:
    """The phone's reason, with the host's own media predicate injected as the sidecar injects it (F10)."""

    from unittest import mock

    from learnloop.reader.phone_media import media_predicate

    with mock.patch.object(DE, "minted_for_lesson", lambda item: False):
        return DE.ineligibility_reason(vault, _item(prompt), DE.PHONE, media=media, served=media_predicate(vault))


def test_served_targets_lift_the_reason_only_with_the_reader_on(store):
    vault, names = store
    prompts = {
        f"Read the graph.\n\n![graph](canonical-sources/raw/{names['image']})": DE.EMBEDS_IMAGE,
        f"See [page 3](llpdf://localhost/{names['pdf']}#page=3).": DE.LINKS_LLPDF,
        f"See [the figure](asset://localhost/vault/canonical-sources/raw/{names['image']}).": DE.REFERENCES_ITEM_ASSET,
    }
    for prompt, reason in prompts.items():
        assert _reason(vault, prompt, media=False) == reason, prompt
        assert _reason(vault, prompt, media=True) is None, prompt


@pytest.mark.parametrize("prompt", [
    "Read the graph.\n\n![graph](figures/graph.png)",                       # a path, not a content address
    "Read the graph.\n\n![graph](https://example.com/graph.png)",           # remote
    "See [page 3](llpdf://source/abc#page=3).",                             # names no stored file
    "<img src=\"x.png\"> and more",                                         # raw HTML is never rendered
])
def test_anything_else_keeps_pr6s_reason(store, prompt):
    vault, _names = store
    assert _reason(vault, prompt, media=True) is not None


def test_a_target_of_the_wrong_kind_or_missing_keeps_the_reason(store):
    vault, names = store
    # A PDF is not an image (it leaves the host only as pages), and a page link needs a PDF.
    assert _reason(vault, f"![book](canonical-sources/raw/{names['pdf']})", media=True) == DE.EMBEDS_IMAGE
    assert _reason(vault, f"[p](llpdf://localhost/{names['image']}#page=1)", media=True) == DE.LINKS_LLPDF
    missing = "sha256-" + "0" * 64
    assert _reason(vault, f"![x](canonical-sources/raw/{missing})", media=True) == DE.EMBEDS_IMAGE
    # One unserved target among served ones keeps the item for the desktop.
    mixed = f"![a](canonical-sources/raw/{names['image']}) and ![b](figures/b.png)"
    assert _reason(vault, mixed, media=True) == DE.EMBEDS_IMAGE


def test_llpdf_pages_count_from_one():
    name = "sha256-" + "a" * 64
    assert DE.llpdf_page(f"llpdf://localhost/{name}#page=3") == (name, 2)
    assert DE.llpdf_page(f"llpdf://localhost/{name}") == (name, 0)
    assert DE.llpdf_page("llpdf://localhost/book.pdf#page=3") is None


def test_the_desktop_never_has_a_reason(store):
    vault, names = store
    item = _item("![graph](figures/graph.png)")
    assert DE.ineligibility_reason(vault, item, DE.DESKTOP, media=True) is None
