"""What other test files use from ``tests/test_glm_ocr.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import threading


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


def _jobs(repo, root):
    from learnloop.content.pipeline.jobs import DurableIngestJobs
    from learnloop.content.pipeline.runner import RunnerServices
    from tests.ux_phase1_support import CLOCK

    jobs = DurableIngestJobs()
    jobs.bind(repo, root, background=False, clock=CLOCK, services=RunnerServices(background_key_checks=False))
    jobs._ensure_worker = lambda: None
    return jobs


# The PDF outline of arXiv:2302.11517v2 (its bookmarks), zero-based pages.
ARXIV_OUTLINE = [
    {"title": title, "heading_level": level, "page_id": page}
    for title, level, page in (
        ("Introduction", 1, 0), ("Related Works", 1, 0), ("Medical Image Segmentation", 2, 0),
        ("Hard Exudate Detection", 2, 1), ("Contrastive Learning", 2, 1), ("Methodology", 1, 1),
        ("Patch-wise Density Contrasting", 2, 1), ("Discriminative Edge Inspection", 2, 2),
        ("Experiments", 1, 2), ("Experimental Setup", 2, 2), ("Results and Discussion", 2, 3),
        ("Conclusion and Future Works", 1, 3), ("Compliance with Ethical Standards", 1, 3),
        ("Acknowledgement", 1, 4), ("References", 1, 4),
    )
]


def _drain_beside_the_reader(extract, path):
    """Run ``extract`` on a thread named like the import drain while the
    Reader keeps rendering ``path``'s first page on this one; returns what
    ``extract`` returned and how many pages the Reader rendered meanwhile."""

    from learnloop.reader import span_view

    done, read = threading.Event(), {}

    def drain():
        try:
            read["value"] = extract()
        except BaseException as exc:  # noqa: BLE001 - re-raised below, on the test's thread
            read["error"] = exc
        finally:
            done.set()

    worker = threading.Thread(target=drain, name="learnloop-ingest-drain")
    worker.start()
    renders = 0
    while not done.is_set() or not renders:
        image, _ = span_view._local_pdf_page_render(path, 0)
        assert image and image.startswith("data:image/png;base64,")
        renders += 1
    worker.join()
    if "error" in read:
        raise read["error"]
    return read["value"], renders
