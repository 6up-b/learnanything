"""Builders and fakes for reader workbench RW5a's figure tests (no network).

``build_figure_vault`` is the canonical-sources textbook vault plus a
probability book (``ext_prob``) whose §5.4 states the two-sided exponential
(the dialogue's flagship, spec G45): a paragraph with the density, its
equation block, a figure block with a box on page 1, the caption and the
consequence. The book is a primary textbook in the source set; ``ext_exam``
(the set's exam) is the held-out material.

``AuthorFake`` answers ``figure_author`` from a queue (a spec dict, JSON
text, ``("unsupported", kind)``, an exception, or a callable of the prompt's
context), the flagship spec when the queue is empty. ``VerifierFake``
answers ``figure_verifier`` with a sympy check (the right one by default).
Both record every request (prompt, context, images). Plumbing checks only,
never evidence about figure quality.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from learnloop.ai.execution import report_call_usage
from learnloop.ai.isolation import TOOL_FREE
from learnloop.ai.transport import BOUNDED_STRUCTURED_COMPLETION, IMAGE_INPUT, ISOLATED_TURN, STRUCTURED_COMPLETION
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.vault.writer import upsert_source_set
from tests import figure_corpus as FC
from tests.pf_fakes import prompt_context
from tests.recap_fixtures import call as call_rpc
from tests.recap_fixtures import context as _context
from tests.source_service_fakes import build_textbook_vault, set_config  # noqa: F401 - re-exported
from learnloop.vault.writer import upsert_source_set  # noqa: F401,E402 - re-exported
from tests.test_source_inventory import _persist

EXTRACTION = "ext_prob"
DENSITY_TEXT = ("The two-sided exponential has density f_X(x) = p\\lambda e^{\\lambda x} for x < 0 and "
                "(1-p)\\lambda e^{-\\lambda x} for x \\ge 0, with 0 < p < 1 and \\lambda > 0.")
EQUATION_TEXT = "f_X(x) = p\\lambda e^{\\lambda x} for x < 0"
FIGURE_BBOX = [100.0, 100.0, 400.0, 300.0]
BLOCKS = (
    ("p1", "SectionHeader", "5.4 Mixtures of continuous distributions"),
    ("p2", "Text", DENSITY_TEXT),
    ("p3", "Equation", EQUATION_TEXT),
    ("p4", "Figure", "Figure 5.3: the two-sided exponential density"),
    ("p5", "Text", "Figure 5.3. At p = 0.30, 30% of the mass lies left of zero and 70% right."),
    ("p6", "Text", "Hence P(X <= 0) = p, whatever lambda is."),
)
LEARNING_STATE_TABLES = [
    "practice_attempts", "grading_evidence", "error_events", "facet_mastery_state", "fsrs_state",
    "scheduler_candidate_log", "attention_blocks", "daily_plans", "probe_observations", "facet_recall_state",
    "facet_capability_evidence", "facet_outcome_observations",
]


def seed_probability_book(repository: Any) -> None:
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO source_artifacts(id, acquisition_kind, canonical_uri, display_title, current_revision_id, "
            "reader_enabled, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            ("src_prob", "pdf", "file:///src_prob.pdf", "Introduction to Probability", "rev_prob", 1,
             "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"))
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, original_uri, created_at) VALUES (?,?,?,?,?)",
            ("rev_prob", "src_prob", "sha256:src_prob", None, "2026-01-01T00:00:00Z"))
        connection.commit()
    header = "/page/1/SectionHeader/1"
    blocks = []
    for ordinal, (span, block_type, text) in enumerate(BLOCKS, start=1):
        blocks.append(DocumentBlock.build(
            span_id=span, block_type=block_type, text=text, ordinal=ordinal, page=1,
            bbox=FIGURE_BBOX if block_type == "Figure" else [72.0, 40.0 * ordinal, 540.0, 40.0 * ordinal + 30],
            section_path=[header], extractor_block_id=header if ordinal == 1 else f"/page/1/{block_type}/{ordinal}"))
    unit = DocumentUnit(unit_id="u54", label="5.4 Mixtures of continuous distributions", ordinal=0,
                        semantic_hash="sha256:u54", page_start=1, page_end=1, span_ids=[span for span, *_ in BLOCKS])
    ir = DocumentIR(extractor="marker", extractor_version="1", units=[unit], blocks=blocks, assets=[],
                    health=ExtractionHealth())
    _persist(repository, ir, revision_id="rev_prob", extraction_id=EXTRACTION)


def build_figure_vault(root: Path) -> tuple[Any, Any]:
    paths, repository, _spans = build_textbook_vault(root)
    seed_probability_book(repository)
    upsert_source_set(paths.root, {
        "id": "sset_la", "subject_id": "linear-algebra", "title": "Linear algebra sources",
        "members": [
            {"source_id": "src_book", "revision_id": "rev_book", "default_role": "primary_textbook"},
            {"source_id": "src_exam", "revision_id": "rev_exam", "default_role": "exam"},
            {"source_id": "src_text", "revision_id": "rev_text", "default_role": "primary_textbook"},
            {"source_id": "src_prob", "revision_id": "rev_prob", "default_role": "primary_textbook"},
        ],
    })
    return paths, repository


def flagship(**changes: Any) -> dict[str, Any]:
    """The flagship spec, its claims quoting this book's §5.4."""

    spec = FC.flagship_spec()
    spec["source_claims"] = [{"span_id": "p3", "quote": EQUATION_TEXT}]
    spec["assumptions"] = [{"text": "λ > 0 and 0 < p < 1", "span_id": "p2", "quote": "0 < p < 1 and \\lambda > 0"},
                           {"text": "the book says this elsewhere", "span_id": "p2", "quote": "not in the book"}]
    spec.update(changes)
    return spec


def half_density() -> dict[str, Any]:
    spec = flagship()
    spec["definitions"] = [{"name": "f", "expr": FC.TWO_SIDED_HALF}]
    return spec


#: A right sympy check for the flagship: equal at sampled points, controls refused.
GOOD_CHECK = '''
import sympy as sp

def check(reference, answer):
    x, p, lam = sp.symbols("x p lam", real=True)
    names = {"x": x, "p": p, "lam": lam}
    r = sp.sympify(reference, locals=names)
    a = sp.sympify(answer, locals=names)
    for xv in (-3, -sp.Rational(1, 2), sp.Rational(1, 4), 2):
        for pv in (sp.Rational(1, 10), sp.Rational(1, 2)):
            for lv in (sp.Rational(1, 2), 2):
                if abs(sp.N((r - a).subs({x: xv, p: pv, lam: lv}))) > 1e-12:
                    return False
    return True
'''
SOURCE_EXPRESSION = "Piecewise((p*lam*exp(lam*x), x < 0), ((1 - p)*lam*exp(-lam*x), True))"

Answer = Any


class _Recording:
    provider_name = "fake_figures"
    provider_type = "chatgpt_plan"
    model = "fake-figure-model"

    def __init__(self, *, images: bool = False, provider_type: str = "chatgpt_plan") -> None:
        self.images = images
        self.provider_type = provider_type
        self.prompts: list[str] = []
        self.contexts: list[dict[str, Any]] = []
        self.request_images: list[tuple[tuple[str, bytes], ...]] = []

    def supports(self, capability: str) -> bool:
        if capability == IMAGE_INPUT:
            return self.images
        return capability in {STRUCTURED_COMPLETION, BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, TOOL_FREE}

    def _record(self, request: Any) -> dict[str, Any]:
        context = prompt_context(request.prompt)
        self.prompts.append(request.prompt)
        self.contexts.append(context)
        self.request_images.append(tuple(request.images))
        report_call_usage({"input_tokens": len(request.prompt) // 4, "output_tokens": 400,
                           "resolved_model": self.model})
        return context

    @property
    def calls(self) -> int:
        return len(self.prompts)


class AuthorFake(_Recording):
    def __init__(self, answers: list[Answer] | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.answers = list(answers or [])

    def complete(self, request: Any) -> Any:
        assert request.purpose == "figure_author"
        context = self._record(request)
        answer = self.answers.pop(0) if self.answers else flagship()
        if callable(answer) and not isinstance(answer, type):
            answer = answer(context)
        if isinstance(answer, BaseException):
            raise answer
        if isinstance(answer, tuple) and answer[0] == "unsupported":
            payload = {"status": "unsupported", "spec_json": "", "unsupported_kind": answer[1],
                       "unsupported_reason": f"the figure language has no {answer[1]}"}
        else:
            text = answer if isinstance(answer, str) else json.dumps(answer)
            payload = {"status": "spec", "spec_json": text, "unsupported_kind": "", "unsupported_reason": ""}
        return request.result_model.model_validate(payload)


class VerifierFake(_Recording):
    def __init__(self, *, program: str = GOOD_CHECK, expression: str = SOURCE_EXPRESSION,
                 quote: str = EQUATION_TEXT, fail: BaseException | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.program = program
        self.expression = expression
        self.quote = quote
        self.fail = fail

    def complete(self, request: Any) -> Any:
        assert request.purpose == "figure_verifier"
        self._record(request)
        if self.fail is not None:
            raise self.fail
        return request.result_model.model_validate({"source_quote": self.quote,
                                                    "source_expression": self.expression,
                                                    "check_program": self.program})


def context(root: Path, *, author: Any = None, verifier: Any = None, sandbox_run: Callable[..., Any] | None = None):
    ctx = _context(root)
    ctx.library_ask_inline = True  # the build job runs inline (deterministic)
    # A missed prediction wakes the gap worker (review F6); here it stays
    # stopped, so no thread reads a text with the configured routes.
    ctx.post_attempt_worker.autostart = False
    if author is not None:
        ctx.figure_author_client = author
    if verifier is not None:
        ctx.figure_verifier_client = verifier
    if sandbox_run is not None:
        ctx.figure_sandbox_run = sandbox_run
    return ctx


def call(ctx: Any, name: str, params: dict[str, Any]) -> dict[str, Any]:
    return call_rpc(ctx, name, params)


def build(ctx: Any, params: dict[str, Any] | None = None, *, rpc: str = "reader.figure_request") -> dict[str, Any]:
    """A figure build as the Reader runs it: the request, then its job read until done."""

    job = call(ctx, rpc, params if params is not None else {"extractionId": EXTRACTION, "spanIds": ["p3"]})
    if job["state"] == "pending":
        kept = ctx.figure_jobs.get(job["jobId"])
        assert kept is not None and kept.done.wait(120), "the figure build did not finish"
        job = call(ctx, "reader.figure_job", {"jobId": job["jobId"]})
    assert job["state"] == "done", job
    return job["result"]


def rows(repository: Any, table: str) -> list[dict[str, Any]]:
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY created_at, id")]


def counts(repository: Any, tables: list[str]) -> dict[str, int]:
    with repository.connection() as connection:
        names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        return {table: connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                for table in tables if table in names}


def sandbox_ready() -> bool:
    from learnloop.content.authoring.pf_sandbox import sandbox_available

    return sandbox_available()
