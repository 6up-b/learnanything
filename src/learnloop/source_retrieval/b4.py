"""Benchmark B4 (owned by T6): PDF page images vs Marker text chunks (suite ``b4``).

Spec §9 and §15 P4: page-image retrieval becomes a default for PDFs only if B4
shows a gain over text chunks. Runs on the shared ``learnloop embeddings
compare`` harness on the owner's math-heavy PDFs (a fixtures-local copy of
``probability``, ``linear_algebra`` or ``arxiv_v2``).

* **Corpus.** Every PDF source whose original file is stored in the vault: its
  current extraction's pages with at least ``MIN_PAGE_CHARS`` characters of
  Marker text, at most ``--max-items`` pages per source (a fixed hash sample).
* **Questions.** An LLM writes one learner question per seed page (a fixed
  sample of corpus pages, ``--max-cases``, default 30) from its text; the seed
  page's hit rate is the label-free check.
* **Systems** (``--view``): ``text`` (each ``--model`` embeds the page's Marker
  chunks; a page scores its best chunk), ``image`` (each image-capable model,
  by default ``google/gemini-embedding-2``, embeds the rendered page),
  ``keyword`` (BM25 over page text) and ``hybrid`` (``hybrid_text`` = keyword +
  the vault model's text chunks; ``hybrid_image`` = that plus the page image),
  all fused by reciprocal rank. Scores are mean-centred cosine over the corpus.
* **Labels and metrics** as in ``bench`` (two LLM passes on question → page
  text, agreement reported; nDCG@10, Recall@10, MRR, paired bootstrap).
* **Decision.** ``page_image_default`` is true only when ``hybrid_image`` beats
  ``hybrid_text`` (nDCG@10 interval above zero, Recall@10 not worse, at least
  ten scored questions). Anything else, including "can't tell", keeps text.
  The decision is **provisional**: questions are written from, and both label
  passes read, Marker's page text, so a page whose math Marker garbled can be
  neither a seed nor labelled relevant, which favours text by construction.
  P4 closes only after a pass that seeds questions from and labels the
  rendered page image on math-heavy pages.

Vectors live in the output directory's cache, never in the vault. Pages are
rendered with pypdfium2 (fails closed when it is not installed) at a longest
side of ``RENDER_MAX_PX`` pixels.
"""
from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass, field
import hashlib
import io
import math
from pathlib import Path
from typing import Any

import numpy as np

from learnloop.ai.execution import content_key
from learnloop.ai.providers.openai_embedding import image_capable
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.source_block_fts import (
    EXCLUDED_BLOCK_TYPES,
    extraction_blocks,
    section_header_titles,
)
from learnloop.ingest.originals import is_pdf_file, resolve_original_file
from learnloop.ops.embedding_compare import EMBED_BATCH, VectorCache
from learnloop.ops.pf_calls import PFUnavailable
from learnloop.practice_index.text import BM25, reciprocal_rank_fusion
from learnloop.source_retrieval import bench
from learnloop.source_retrieval.corpus import current_extractions
from learnloop.source_retrieval.recipes import embeddable, source_block_text
from learnloop.vault.models import LoadedVault

IMAGE_MODEL = "google/gemini-embedding-2"
#: Native widths of the candidate models (MRL truncation never widens).
MAX_DIMS = {
    "google/gemini-embedding-2": 3072,
    "qwen/qwen3-embedding-8b": 4096,
    "qwen/qwen3-embedding-4b": 2560,
    "openai/text-embedding-3-large": 3072,
    "openai/text-embedding-3-small": 1536,
}
SYSTEMS = ("text", "image", "keyword", "hybrid")
DEFAULT_QUESTIONS = 30
MIN_PAGE_CHARS = 200
PAGE_CHARS = 3000
QUESTION_PROMPT_VERSION = "b4_question.v1"
LABEL_PROMPT_VERSIONS = ("b4_page_label.v1.pass1", "b4_page_label.v1.pass2")
QUESTION_BATCH = 6
LABEL_BATCH = 8
IMAGE_BATCH = 8
#: Conservative image-token bound for one rendered page (four 768 px tiles).
IMAGE_TOKENS = 1100
RENDER_MAX_PX = 1024
RENDER_VERSION = "pdfium-png-1024-v1"
PROVISIONAL_BIAS = (
    "questions are written from, and both label passes read, Marker's page text, so a page whose "
    "relevant math Marker garbled can be neither a seed nor labelled relevant; the comparison "
    "favours text by construction")
CLOSE_CONDITION = (
    "a pass that seeds questions from the rendered page image and labels (question, page image) "
    "pairs with a multimodal judge, on the math-heavy pages, agrees with this decision")


@dataclass
class Page:
    key: str
    extraction_id: str
    source_id: str
    title: str
    page: int
    text: str
    chunks: list[str]
    pdf_path: Path


@dataclass
class B4Data:
    manifest: dict[str, Any]
    pages: list[Page]
    seeds: list[Page]
    systems: tuple[str, ...]
    text_models: tuple[str, ...]
    image_models: tuple[str, ...]
    dims: dict[str, int]
    revision: str
    skipped: dict[str, int] = field(default_factory=dict)


def model_dims(model: str, requested: int) -> int:
    return min(requested, MAX_DIMS.get(model, requested))


def render_page(path: Path, page: int) -> bytes | None:
    """The page as PNG bytes, longest side ``RENDER_MAX_PX``; None if unreadable."""

    try:
        import pypdfium2 as pdfium
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise PFUnavailable("B4 renders PDF pages with pypdfium2; install it (uv pip install pypdfium2)") from exc
    document = pdfium.PdfDocument(str(path))
    try:
        if page < 0 or page >= len(document):
            return None
        pdf_page = document[page]
        width, height = (float(value) for value in pdf_page.get_size())
        scale = RENDER_MAX_PX / max(width, height, 1.0)
        image = pdf_page.render(scale=scale).to_pil()
        output = io.BytesIO()
        image.save(output, format="PNG", optimize=True)
        return output.getvalue()
    finally:
        document.close()


def _pdf_pages(vault: LoadedVault, repository: Repository, per_source: int) -> tuple[list[Page], dict[str, int]]:
    pages: list[Page] = []
    skipped = {"not_pdf_or_missing_original": 0, "short_pages": 0}
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        for extraction_id, source in sorted(current_extractions(repository).items()):
            run = repository.get_extraction_run(extraction_id) or {}
            revision = repository.get_source_revision(str(run.get("revision_id") or "")) or {}
            path = resolve_original_file(vault.root, digest=revision.get("asset_hash"),
                                         original_uri=revision.get("original_uri"))
            if path is None or not is_pdf_file(path):
                skipped["not_pdf_or_missing_original"] += 1
                continue
            titles = section_header_titles(connection, extraction_id)
            by_page: dict[int, list] = {}
            for block in extraction_blocks(connection, extraction_id):
                if block.page is not None and block.block_type not in EXCLUDED_BLOCK_TYPES:
                    by_page.setdefault(block.page, []).append(block)
            source_pages: list[Page] = []
            for page_number, blocks in sorted(by_page.items()):
                text = "\n".join(" ".join(block.text.split()) for block in blocks if block.text.strip())
                if len(text) < MIN_PAGE_CHARS:
                    skipped["short_pages"] += 1
                    continue
                chunks = [source_block_text(block, titles) for block in blocks if embeddable(block)]
                if not chunks:
                    continue
                source_pages.append(Page(f"{extraction_id}#p{page_number}", extraction_id, source.source_id,
                                         source.title, page_number, text, chunks, path))
            source_pages.sort(key=lambda page: bench.stable_key("b4-corpus-v1", page.key))
            pages.extend(sorted(source_pages[:per_source], key=lambda page: page.page))
    return pages, skipped


class B4Suite:
    name = "b4"
    description = ("Benchmark B4: PDF page-image embeddings vs Marker text chunks on question -> page "
                   "pairs (two LLM label passes); decides whether page images become a default (P4).")

    def load(self, vault: LoadedVault, request: Any) -> B4Data:
        systems = tuple(request.views) or SYSTEMS
        unknown = set(systems) - set(SYSTEMS)
        if unknown:
            raise ValueError(f"Unknown b4 systems: {', '.join(sorted(unknown))}")
        repository = bench.read_only_repository(vault)
        pages, skipped = _pdf_pages(vault, repository, request.max_items)
        if not pages:
            raise ValueError("No PDF source with a stored original and extracted pages")
        models = tuple(dict.fromkeys(request.models or (vault.config.embedding.model, IMAGE_MODEL)))
        text_models = models if "text" in systems or "hybrid" in systems else ()
        image_models = tuple(model for model in models if image_capable(model)) \
            if "image" in systems or "hybrid" in systems else ()
        if ("image" in systems or "hybrid" in systems) and not image_models:
            raise ValueError("b4's image system needs an image-capable --model (google/gemini-embedding-2)")
        requested = (request.dims[0] if request.dims else vault.config.embedding.dimensions)
        dims = {model: model_dims(model, requested) for model in models}
        count = request.max_cases or DEFAULT_QUESTIONS
        seeds = sorted(pages, key=lambda page: bench.stable_key("b4-seed-v1", page.key))[:count]
        revision = content_key({"pages": [page.key for page in pages], "seeds": [page.key for page in seeds],
                                "render": RENDER_VERSION})
        manifest = {"name": "b4", "version": "b4-v1",
                    "sources": [{"name": f"{page.title}", "version": page.extraction_id,
                                 "licence": "owner's own sources"} for page in
                                {page.extraction_id: page for page in pages}.values()]}
        return B4Data(manifest, pages, seeds, systems, text_models, image_models, dims, revision, skipped)

    def plan(self, vault: LoadedVault, data: B4Data, request: Any) -> dict[str, Any]:
        questions = len(data.seeds)
        plan: dict[str, Any] = {"pages": len(data.pages), "questions": questions, "systems": list(data.systems),
                                "text_models": list(data.text_models), "image_models": list(data.image_models),
                                "dims": data.dims, "skipped": data.skipped, "roles": {}, "embedding": {}}
        plan["roles"][bench.QUESTION_ROLE] = bench.plan_question_calls(
            [page.text[:PAGE_CHARS] for page in data.seeds], QUESTION_PROMPT_VERSION, QUESTION_BATCH,
            bench.role_budget(vault, bench.QUESTION_ROLE))
        pool_bound = bench.TOP_K * (len(data.text_models) + len(data.image_models) + 3)
        plan["roles"][bench.LABEL_ROLE] = bench.plan_label_calls(
            questions, pool_bound, LABEL_BATCH, LABEL_PROMPT_VERSIONS,
            {"source": "x" * 120, "page": 1, "text": "x" * PAGE_CHARS},
            bench.role_budget(vault, bench.LABEL_ROLE))
        query_tokens = questions * (400 + 128)
        chunks = [chunk for page in data.pages for chunk in page.chunks]
        chunk_tokens = sum(len(chunk.encode("utf-8")) + 128 for chunk in chunks)
        for model in dict.fromkeys((*data.text_models, *data.image_models)):
            texts = questions + (len(chunks) if model in data.text_models else 0)
            images = len(data.pages) if model in data.image_models else 0
            calls = (math.ceil(texts / EMBED_BATCH) if texts else 0) + (math.ceil(images / IMAGE_BATCH) if images else 0)
            plan["embedding"][model] = {
                "texts": texts, "images": images, "calls": calls,
                "tokens": query_tokens + (chunk_tokens if model in data.text_models else 0) + images * IMAGE_TOKENS,
            }
        return plan

    def run(self, data: B4Data, request: Any, ctx: Any) -> dict[str, Any]:
        by_key = {page.key: page for page in data.pages}
        written = bench.write_questions(ctx, [(page.key, page.text[:PAGE_CHARS]) for page in data.seeds],
                                        version=QUESTION_PROMPT_VERSION, batch=QUESTION_BATCH)
        questions = [{"text": entry["question"], "seed": key} for key, entry in written.items()]
        texts = [question["text"] for question in questions]
        page_keys = [page.key for page in data.pages]
        system_scores: dict[str, dict[str, np.ndarray]] = {}
        for model in data.text_models:
            dims = data.dims[model]
            queries = ctx.vectors(model, texts, dims=dims, task_prefix="retrieval-query")
            chunk_owner: list[str] = []
            chunk_texts: list[str] = []
            for page in data.pages:
                for chunk in page.chunks:
                    chunk_owner.append(page.key)
                    chunk_texts.append(chunk)
            docs = ctx.vectors(model, chunk_texts, dims=dims, task_prefix="retrieval-document")
            matrix = np.vstack([docs[text][:dims] for text in chunk_texts])
            scores = _centered_scores(matrix, {text: queries[text][:dims] for text in texts})
            system_scores[f"text:{model}"] = {
                text: _page_max(chunk_owner, page_keys, values) for text, values in scores.items()}
        for model in data.image_models:
            dims = data.dims[model]
            queries = ctx.vectors(model, texts, dims=dims, task_prefix="retrieval-query")
            images = _image_vectors(ctx, model, dims, data.pages)
            available = [key for key in page_keys if key in images]
            matrix = np.vstack([images[key][:dims] for key in available])
            scores = _centered_scores(matrix, {text: queries[text][:dims] for text in texts})
            system_scores[f"image:{model}"] = {
                text: _page_max(available, page_keys, values) for text, values in scores.items()}
        keyword = BM25({page.key: page.text for page in data.pages})
        default_text = f"text:{data.text_models[0]}" if data.text_models else None
        default_image = f"image:{data.image_models[0]}" if data.image_models else None
        per_question: list[dict[str, Any]] = []
        all_labels: list[dict[str, list[str | None]]] = []
        incomplete = 0
        label_models: dict[str, int] = {}
        seed_hits: dict[str, list[bool]] = {}
        system_names: list[str] = []
        for question in questions:
            text = question["text"]
            rankings: dict[str, list[str]] = {}
            for name, scores in system_scores.items():
                if (name.startswith("text:") and "text" not in data.systems) or (
                        name.startswith("image:") and "image" not in data.systems):
                    continue
                rankings[name] = _ranked(page_keys, scores[text])
            keyword_ranked = keyword.ranking(text)
            if "keyword" in data.systems:
                rankings["keyword"] = keyword_ranked
            if "hybrid" in data.systems and default_text is not None:
                text_ranked = _ranked(page_keys, system_scores[default_text][text])
                fused, _ = reciprocal_rank_fusion({"keyword": keyword_ranked, "text": text_ranked})
                rankings["hybrid_text"] = fused
                if default_image is not None:
                    image_ranked = _ranked(page_keys, system_scores[default_image][text])
                    fused, _ = reciprocal_rank_fusion({"keyword": keyword_ranked, "text": text_ranked,
                                                       "image": image_ranked})
                    rankings["hybrid_image"] = fused
            system_names = sorted(rankings)
            pool = sorted({key for ranked in rankings.values() for key in ranked[: bench.TOP_K]})
            candidates = {key: {"source": bench.clip(by_key[key].title, 120), "page": by_key[key].page + 1,
                                "text": bench.clip(by_key[key].text, PAGE_CHARS)} for key in pool}
            labels, models = bench.label_pool(
                ctx, question=text, candidates=candidates, versions=LABEL_PROMPT_VERSIONS, batch=LABEL_BATCH,
                left_kind="b4_question", right_kind="pdf_page", right_id=lambda key: key,
                rationale={"suite": self.name, "revision": data.revision})
            for model, count in models.items():
                label_models[model] = label_models.get(model, 0) + count
            all_labels.append(labels)
            for name, ranked in rankings.items():
                seed_hits.setdefault(name, []).append(question["seed"] in ranked[: bench.TOP_K])
            scored = bench.score_question(rankings, labels)
            if scored is None:
                incomplete += 1
                continue
            per_question.append(scored)
        comparisons: list[tuple[str, str]] = []
        if "hybrid_image" in system_names and "hybrid_text" in system_names:
            comparisons.append(("hybrid_image", "hybrid_text"))
        if default_image in system_names:
            for name in system_names:
                if name.startswith("text:"):
                    comparisons.append((default_image, name))
        if "keyword" in system_names and default_text in system_names:
            comparisons.append((default_text, "keyword"))
        summary = bench.summarize(per_question, system_names, comparisons)
        decisive = summary["differences"].get("hybrid_image - hybrid_text")
        page_image_default = bool(decisive) and bench.beats(decisive)
        return {
            "pages": len(data.pages), "questions": len(questions), "scored_questions": len(per_question),
            "incomplete_questions": incomplete, "systems": system_names, "dims": data.dims,
            "render": RENDER_VERSION, "skipped": data.skipped,
            "seed_hit@10": {name: (sum(hits) / len(hits) if hits else None) for name, hits in seed_hits.items()},
            "summary": summary,
            "label_agreement": bench.label_agreement(all_labels), "label_models": label_models,
            "decision": {
                "page_image_default": page_image_default,
                "status": "provisional",
                "rule": ("page images become a PDF default only if hybrid_image beats hybrid_text: nDCG@10 "
                         "95% bootstrap interval above 0, Recall@10 not worse, at least "
                         f"{bench.MIN_SCORED_QUESTIONS} scored questions (P4)"),
                "reason": ("hybrid_image beats hybrid_text" if page_image_default else
                           "no demonstrated gain over text chunks; text stays the default"),
                "bias": PROVISIONAL_BIAS,
                "close_condition": CLOSE_CONDITION,
            },
        }

    def markdown_lines(self, results: dict[str, Any]) -> list[str]:
        lines = [f"Pages: {results.get('pages')}; questions: {results.get('questions')} (scored "
                 f"{results.get('scored_questions')}).", "",
                 "| System | nDCG@10 | Recall@10 | MRR@10 | seed hit@10 |", "|---|---|---|---|---|"]
        means = (results.get("summary") or {}).get("means", {})
        for name in results.get("systems", []):
            row = means.get(name, {})
            lines.append(f"| {name} | {_fmt(row.get('ndcg@10'))} | {_fmt(row.get('recall@10'))} | "
                         f"{_fmt(row.get('mrr@10'))} | {_fmt((results.get('seed_hit@10') or {}).get(name))} |")
        lines += ["", "| Comparison | Δ nDCG@10 [95% CI] | Δ Recall@10 |", "|---|---|---|"]
        for name, entry in ((results.get("summary") or {}).get("differences") or {}).items():
            ndcg = entry.get("ndcg@10", {})
            ci = ndcg.get("ci95") or [None, None]
            lines.append(f"| {name} | {_fmt(ndcg.get('mean'))} [{_fmt(ci[0])}, {_fmt(ci[1])}] | "
                         f"{_fmt((entry.get('recall@10') or {}).get('mean'))} |")
        decision = results.get("decision") or {}
        agreement = results.get("label_agreement") or {}
        lines += ["", f"Decision ({decision.get('status', 'provisional')}): page_image_default = "
                      f"{decision.get('page_image_default')} ({decision.get('reason')}).",
                  f"Bias: {decision.get('bias', PROVISIONAL_BIAS)}",
                  f"Closes when: {decision.get('close_condition', CLOSE_CONDITION)}",
                  f"Label agreement: {agreement.get('pairs')} pairs, kappa {_fmt(agreement.get('cohen_kappa'))}."]
        return lines


def _centered_scores(matrix: np.ndarray, queries: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """Mean-centred cosine of each query against every row (corpus centroid)."""

    docs = matrix.astype(np.float64)
    docs /= np.where(np.linalg.norm(docs, axis=1, keepdims=True) == 0, 1, np.linalg.norm(docs, axis=1, keepdims=True))
    mean = docs.mean(axis=0)
    centered = docs - mean
    norms = np.linalg.norm(centered, axis=1)
    out: dict[str, np.ndarray] = {}
    for text, vector in queries.items():
        q = np.asarray(vector, dtype=np.float64)
        q = q / (np.linalg.norm(q) or 1.0) - mean
        denominator = norms * (np.linalg.norm(q) or 1.0)
        out[text] = np.divide(centered @ q, denominator, out=np.zeros(len(norms)), where=denominator != 0)
    return out


def _page_max(owners: list[str], page_keys: list[str], values: np.ndarray) -> dict[str, float]:
    best: dict[str, float] = {}
    for owner, value in zip(owners, values, strict=True):
        best[owner] = max(best.get(owner, -math.inf), float(value))
    return {key: best[key] for key in page_keys if key in best}


def _ranked(page_keys: list[str], scores: dict[str, float]) -> list[str]:
    return sorted((key for key in page_keys if key in scores), key=lambda key: (-scores[key], key))


def _image_vectors(ctx: Any, model: str, dims: int, pages: list[Page]) -> dict[str, np.ndarray]:
    """Page-image vectors by page key, cached by the rendered PNG's digest."""

    cache = VectorCache(ctx.output_dir / "cache", model, "retrieval-document", dims=dims,
                        config={**ctx.embedding_config(model), "input": RENDER_VERSION})
    rendered: dict[str, bytes] = {}
    keys: dict[str, str] = {}
    for page in pages:
        png = render_page(page.pdf_path, page.page)
        if png is None:
            continue
        keys[page.key] = "image:" + hashlib.sha256(png).hexdigest()
        rendered[page.key] = png
    missing = [key for key, cache_key in keys.items() if cache.get(cache_key) is None]
    if missing:
        price = ctx.price_for(model)
        if price is None:
            from learnloop.ai.spend import SpendLimitExceeded

            raise SpendLimitExceeded(f"Unknown embedding price for {model}: pass --embedding-price-per-million")
        client = ctx.embedder(model, dims)
        for start in range(0, len(missing), IMAGE_BATCH):
            batch = missing[start:start + IMAGE_BATCH]
            vectors = ctx.caller.embed(client, [("image/png", rendered[key]) for key in batch],
                                       task_prefix="retrieval-document", price_per_million=price,
                                       estimated_tokens=IMAGE_TOKENS * len(batch))
            if any(len(vector) < dims for vector in vectors):
                raise PFUnavailable(f"{model} returned vectors narrower than {dims}")
            cache.put_many([keys[key] for key in batch], vectors)
    return {key: cache.get(cache_key) for key, cache_key in keys.items() if cache.get(cache_key) is not None}


def _fmt(value: Any) -> str:
    return "—" if value is None else f"{value:.3f}" if isinstance(value, float) else str(value)


__all__ = ["B4Suite", "IMAGE_MODEL", "MAX_DIMS", "RENDER_VERSION", "SYSTEMS", "model_dims", "render_page"]
