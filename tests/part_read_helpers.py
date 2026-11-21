"""A book whose first chapter's topics cite known passages, built through Add with the house fakes, and a learner
who reads part of it through the real progress report (``reader.mark_section_progress``).

The first chapter has six paragraphs, P1..P6. Its build applies, beside the house topic, four topics with their own
facets: ``lo_early`` cites P1 and P2, ``lo_straddle`` P3 and P5, ``lo_late`` P6, and ``lo_cross`` P2 and the
second chapter's first paragraph Q1. A learner "stopping at P4" has seen P1..P4. Every paragraph carries a word
of its own (``PARAGRAPH_WORD``), so a request can be searched for text the learner never saw.
"""

from __future__ import annotations

import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop.content.sources.source_outline import resolve_extraction_id
from learnloop.content.synthesis.ai_contracts import (
    SynthBlueprint,
    SynthFacet,
    SynthLearningObject,
    SynthRecipe,
    SynthRecipeComponent,
    SynthSpanRef,
)
from learnloop.db.repositories import Repository
from learnloop.section_map import extraction_sections
from learnloop_sidecar.context import SidecarContext

from tests.source_set_synthesis_helpers import FakeSynthesisClient, _default_payload
from tests.ux_phase1_add_source_helpers import call
from tests.ux_phase1_support import CLOCK, fake_services, fresh_library, grant_consent, write_book

#: A word only that paragraph holds.
PARAGRAPH_WORD = {
    "P1": "aardvark", "P2": "bramble", "P3": "cobalt", "P4": "dulcimer", "P5": "ermine", "P6": "fjord",
    "Q1": "gazebo", "Q2": "hornbeam",
}

_SENTENCE = "is part of the account of eigenvalues and the characteristic polynomial of a square matrix"

BOOK = "\n\n".join([
    "# 1 Eigenvalues",
    *[f"Paragraph {name} about the {PARAGRAPH_WORD[name]} {_SENTENCE}." for name in ("P1", "P2", "P3", "P4", "P5", "P6")],
    "# 2 Spectral theorem",
    *[f"Paragraph {name} about the {PARAGRAPH_WORD[name]} {_SENTENCE}." for name in ("Q1", "Q2")],
]) + "\n"

#: Each added topic and the paragraphs it cites.
TOPICS = {"lo_early": ("P1", "P2"), "lo_straddle": ("P3", "P5"), "lo_late": ("P6",), "lo_cross": ("P2", "Q1")}


class Book:
    """The built book: its sidecar, source, reading, sections and paragraph spans."""

    def __init__(self, ctx: SidecarContext, source_id: str) -> None:
        self.ctx, self.source_id = ctx, source_id

    @property
    def repo(self) -> Repository:
        return self.ctx.repository

    @property
    def extraction_id(self) -> str:
        return resolve_extraction_id(self.ctx.repository, self.source_id)

    def spans(self) -> dict[str, tuple[str, str]]:
        """Each paragraph's (section, span)."""

        return paragraph_spans(self.repo, self.extraction_id)

    def read(self, *names: str, completed: bool = False, run: bool = True):
        """The learner's own reading observed these paragraphs (one progress report per section, as the Reader
        sends them); ``completed`` finishes the last section named. ``run``: the app's worker then runs what was
        queued (False: it is busy, or the book's build is still to run). Returns the last reply."""

        spans = self.spans()
        by_section: dict[str, list[str]] = {}
        for name in names:
            section, span = spans[name]
            by_section.setdefault(section, []).append(span)
        reply = None
        sections = list(by_section) or []
        for section in sections:
            params = {"extractionId": self.extraction_id, "sectionId": section, "spansSeen": len(by_section[section]),
                      "spanCount": 6, "seenSpanIds": by_section[section]}
            if completed and section == sections[-1]:
                params["completed"] = True
            reply = call(self.ctx, "reader.mark_section_progress", params)
        if run:
            build(self)
        return reply

    def finish(self, name: str):
        section, _span = self.spans()[name]
        reply = call(self.ctx, "reader.mark_section_progress",
                     {"extractionId": self.extraction_id, "sectionId": section, "spansSeen": 6, "spanCount": 6,
                      "completed": True})
        build(self)  # the app's worker runs what was queued
        return reply

    def claims(self) -> list[dict]:
        with self.repo.connection() as connection:
            return [dict(row) for row in connection.execute(
                "SELECT * FROM reader_topic_question_work WHERE owner = 'topic' ORDER BY rowid")]

    def claimed(self) -> dict[str, str]:
        """Each claimed topic and the trigger it was claimed by."""

        return {row["learning_object_id"]: row["trigger_event"] for row in self.claims()}

    def questions(self) -> dict:
        """Today's facts for the book, as the library's read gives them (after the work that read started ran)."""

        call(self.ctx, "get_source_library", {})
        build(self)
        card = next(card for card in call(self.ctx, "get_source_library", {})["sources"]
                    if card["sourceId"] == self.source_id)
        return card["statusLine"]["questions"]


def paragraph_spans(repository: Repository, extraction_id: str) -> dict[str, tuple[str, str]]:
    """Each paragraph's (section id, span id), found by its own word."""

    ir = repository.load_document_ir(extraction_id)
    rows, block_by_span, _ = extraction_sections(ir)
    found: dict[str, tuple[str, str]] = {}
    for row in rows:
        for span in row["span_ids"]:
            for name, word in PARAGRAPH_WORD.items():
                if f" {word} " in f" {block_by_span[span].text} ":
                    found[name] = (str(row["id"]), span)
    return found


def builder(root_holder: list):
    """The house synthesis, plus the four topics, each with a facet of its own citing the same paragraphs."""

    def build(context, _count):
        payload = _default_payload(context)
        repository = root_holder[0].repository
        extraction_id = next(entry["extraction_id"] for entry in context.unit_inventories)
        spans = paragraph_spans(repository, extraction_id)

        def cite(names):
            return [SynthSpanRef(extraction_id=extraction_id, unit_id=spans[name][0], span_id=spans[name][1],
                                 relation="primary") for name in names]

        for lo_id, names in TOPICS.items():
            facet = f"f_{lo_id}"
            payload.facets.append(SynthFacet(
                client_item_id=facet, id=f"facet_{lo_id}", concept_client_id="c_sym", kind="definition",
                claim=f"The claim of {lo_id}.", preconditions=["a square matrix"],
                error_signatures=[f"confuses {lo_id}"], instructional_repairs=[f"contrast {lo_id}"],
                provenance=cite(names)))
            payload.learning_objects.append(SynthLearningObject(
                client_item_id=lo_id, id=lo_id, concept_client_id="c_sym", title=f"Topic {lo_id}",
                summary=f"Explain {lo_id}.", provenance=cite(names)))
            payload.blueprints.append(SynthBlueprint(
                client_item_id=f"bp_{lo_id}", id=f"bp_{lo_id}", learning_object_client_id=lo_id, weight=0.3,
                recipes=[SynthRecipe(id=f"recipe_{lo_id}", all_of=[
                    SynthRecipeComponent(facet_client_id=facet, capability="schema_interpretation")])]))
        return payload

    return build


def book_ctx(tmp_path, *, writer=None, hold: bool = True):
    """A library with the book added (not built yet): the sidecar, its source id, and a holder the synthesis
    builder reads the reading through. ``hold``: the queue runs only when the test drains it."""

    root = fresh_library(tmp_path, scope_cap=None)
    grant_consent(root)
    holder: list = []
    # The queue asks one factory for the build's synthesis and for the questions' writer.
    services = fake_services(synthesis_client_factory=lambda ctx=None: _Both(holder, writer))
    ctx = SidecarContext()
    ctx.load(root)
    ctx.ingest_jobs.bind(ctx.repository, root, background=False, clock=CLOCK, services=services)
    if hold:
        ctx.ingest_jobs._ensure_worker = lambda: None  # type: ignore[method-assign]
    holder.append(ctx)
    source_id = call(ctx, "add_source", {"sources": [str(write_book(tmp_path, "eigen.md", BOOK))]})["items"][0]["sourceId"]
    return Book(ctx, source_id)


class _Both(FakeSynthesisClient):
    """One client for both the build's synthesis and the questions' writer (the queue asks one factory)."""

    def __init__(self, holder, writer):
        super().__init__(builder=builder(holder))
        self.writer = writer

    def complete(self, request):
        if request.purpose == "authoring" and self.writer is not None:
            return self.writer.complete(request)
        return super().complete(request)


def drain(ctx: SidecarContext, max_jobs: int | None = None) -> int:
    return ctx.ingest_jobs._require_runner().drain(max_jobs=max_jobs)


def jobs(ctx: SidecarContext) -> list[dict]:
    return [job for batch in ctx.repository.list_ingest_batches() for job in ctx.repository.ingest_jobs_for_batch(batch["id"])]


def build_until_synthesis(book: Book) -> None:
    """Run the import, the planner and the inventory: the build's synthesis (its topics) is all that is left."""

    for _ in range(12):
        if any(job["job_type"] == "inventory" and job["status"] == "completed" for job in jobs(book.ctx)) and any(
                job["job_type"] == "bootstrap_synthesis" and job["status"] == "queued" for job in jobs(book.ctx)):
            return
        assert drain(book.ctx, 1), "the queue ran dry before the build's inventory finished"
    raise AssertionError("the build's inventory never finished")


def build(book: Book) -> None:
    """Run everything queued, the build included."""

    while drain(book.ctx, 1):
        pass


class SeenWriter:
    """The questions' writer: for each topic asked, one grounded, audited question citing that topic's bundles from
    the request. Records each request's prompt (the bytes a model would receive) and the topics asked, in order.
    ``before`` runs inside each call, before its answer (a test reads on, or finishes the section, there).
    ``held``: every question is marked for review anyway (the live route's held questions), so none applies."""

    def __init__(self, *, held: bool = False) -> None:
        self.calls: list[list[str]] = []
        self.prompts: list[str] = []
        self.before = lambda: None
        self.held = held

    def complete(self, request):
        import ast

        from learnloop.content.proposals.ai_contracts import AuthoringProposal

        from tests.proposal_persistence_helpers import _generated_practice_proposal_payload
        from tests.structured_ai import _request_context

        context = _request_context(request.prompt, request.purpose)
        topics = [target["learning_object_id"] for target in ast.literal_eval(next(
            line.removeprefix("Targets: ") for line in context.instructions.splitlines() if line.startswith("Targets: ")))]
        self.calls.append(topics)
        self.prompts.append(request.prompt)
        self.before()
        items, refs = [], []
        for topic in topics:
            own = [ref for ref in context.source_refs if topic in (ref.get("learning_object_ids") or [])]
            refs.extend(own)
            facet = "facet_symmetry_definition" if topic == "lo_diagonalize_symmetric" else f"facet_{topic}"
            data = _generated_practice_proposal_payload({
                "learning_object_id": topic, "prompt": f"Explain {topic}.", "surface_family": topic,
                "repair_targets": [facet], "evidence_facets": [facet], "evidence_weights": {facet: 1.0},
                "criterion_facet_weights": {"correctness": {facet: 1.0}}, "difficulty": 0.25,
            })
            row = data["items"][0]
            row.update(client_item_id=topic, proposed_entity_id=f"pi_{topic}",
                       source_ref_ids=[str(ref["ref_id"]) for ref in own])
            if self.held:
                row.update(review_route="review_required",
                           rationale="Grounded in the passages read; the audit passed. Marked for review.")
            items.append(row)
        return AuthoringProposal.model_validate({"summary": "Questions from what was read", "source_refs": refs,
                                                 "items": items})
