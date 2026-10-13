"""Fakes and builders for the canonical-sources service tests (no network).

``build_service_vault`` is T6's retrieval vault (three LOs, six facets, a
textbook and an exam in one source set) with the practice index on. Every
paid role is answered by a deterministic fake from the prompt's own JSON:
results are plumbing checks, never evidence about quality.
"""
from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from tests.source_retrieval_fakes import build_retrieval_vault


def build_service_vault(root: Path, *, embeddings: bool = False) -> tuple[VaultPaths, Repository]:
    return build_retrieval_vault(root, embeddings=embeddings)


def set_config(paths: VaultPaths, section: str, **values: Any) -> None:
    """Append (or extend) a TOML section in the vault's learnloop.toml."""

    config = paths.root / "learnloop.toml"
    text = config.read_text(encoding="utf-8")
    lines = []
    for key, value in values.items():
        if isinstance(value, bool):
            rendered = "true" if value else "false"
        elif isinstance(value, str):
            rendered = json.dumps(value)
        else:
            rendered = repr(value)
        lines.append(f"{key} = {rendered}")
    header = f"[{section}]"
    if f"\n{header}\n" in text:
        text = text.replace(f"\n{header}\n", f"\n{header}\n" + "\n".join(lines) + "\n", 1)
    else:
        text = text.rstrip("\n") + f"\n\n{header}\n" + "\n".join(lines) + "\n"
    config.write_text(text, encoding="utf-8")


def insert_question(repository: Repository, *, context: str, question: str,
                    practice_item_id: str | None = None, attempt_id: str | None = None,
                    note_id: str | None = None, facets: list[str] | None = None,
                    source_context: dict[str, Any] | None = None,
                    answered: bool = True, event_id: str | None = None) -> str:
    return repository.insert_question_event({
        "id": event_id, "context": context, "question_md": question,
        "practice_item_id": practice_item_id, "attempt_id": attempt_id, "note_id": note_id,
        "answer_md": "an answer" if answered else None, "facets": facets or [],
        "answer_status": "answered" if answered else "pending",
        "source_context": source_context,
    })


def rpc(messages: list[dict]) -> list[dict]:
    from learnloop_sidecar.server import serve

    stdin = io.StringIO("".join(json.dumps(message) + "\n" for message in messages))
    stdout = io.StringIO()
    serve(stdin, stdout)
    return [json.loads(line) for line in stdout.getvalue().splitlines()]


def init_message(root: Path) -> dict:
    return {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(root)}}


def call(root: Path, method: str, params: dict[str, Any]) -> dict:
    responses = rpc([init_message(root), {"jsonrpc": "2.0", "id": 2, "method": method, "params": params}])
    return responses[1]


def loaded(paths: VaultPaths):
    return load_vault(paths.root)


def table_counts(repository: Repository, tables: list[str]) -> dict[str, int]:
    with repository.connection() as connection:
        return {table: connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                for table in tables}


#: The learning-state tables G1 says a tool never writes.
LEARNING_STATE_TABLES = [
    "practice_attempts", "grading_evidence", "error_events", "facet_mastery_state",
    "fsrs_state", "scheduler_candidate_log", "attention_blocks", "daily_plans",
]


def learning_state_tables(repository: Repository) -> list[str]:
    with repository.connection() as connection:
        names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    return [table for table in LEARNING_STATE_TABLES if table in names]


# -- a textbook with exercises, solutions and worked examples ------------------

import re as _re

from learnloop.ai.execution import report_call_usage as _report_usage
from learnloop.ingest.block_roles import classify_block_role as _classify
from learnloop.ingest.ir import DocumentBlock as _Block, DocumentIR as _IR, DocumentUnit as _Unit, ExtractionHealth as _Health
from learnloop.vault.writer import upsert_source_set as _upsert_source_set
from tests.pf_fakes import SYMPY_CHECK, prompt_context, solve_linear
from tests.test_source_inventory import _persist as _persist_ir

TEXTBOOK = {
    "ch5": ("Chapter 5 Eigenvalues", [
        ("Eigenvalues are the roots of the characteristic polynomial det(A - tI) of a square matrix.", 7),
        ("Swapping two rows of a matrix multiplies its determinant by -1, so the determinant changes sign.", 7),
    ]),
    "worked": ("Worked examples", [
        ("Example 5.1 Solve 4x + 2 = 14 for the eigenvalue x. Subtract 2 and divide by 4, so x = 3.", 8),
    ]),
    "exercises": ("Exercises", [
        ("1. An eigenvalue t satisfies 3t + 5 = 20; solve 3x + 5 = 20 for x to find the eigenvalue.", 9),
        ("2. The characteristic polynomial gives 2x + 4 = 10; solve 2x + 4 = 10 for x, the eigenvalue.", 9),
        ("3. Explain why the determinant changes sign when two rows of a matrix are swapped.", 9),
        ("4. Compute the eigenvalues of the diagonal matrix [[2,0],[0,3]].", 9),
    ]),
    "solutions": ("Solutions", [
        ("1. Subtracting 5 gives 3x = 15, so the eigenvalue is x = 5.", 30),
        ("2. Subtracting 4 gives 2x = 6, so the eigenvalue is x = 3.", 30),
        ("4. The eigenvalues of a diagonal matrix are its diagonal entries 2 and 3.", 30),
    ]),
}


def seed_textbook(repository: Repository, *, source_id: str = "src_text", revision_id: str = "rev_text",
                  extraction_id: str = "ext_text", title: str = "Matrix Theory",
                  units: dict | None = None) -> dict[str, list[str]]:
    """A textbook whose blocks carry real role hints (classify_block_role),
    so effective hints, exercise regions and solution regions behave as in a
    Marker import. Returns each unit's span ids."""

    units = units or TEXTBOOK
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO source_artifacts(id, acquisition_kind, canonical_uri, display_title, current_revision_id, "
            "reader_enabled, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (source_id, "pdf", f"file:///{source_id}.pdf", title, revision_id, 1,
             "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"))
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, original_uri, created_at) VALUES (?,?,?,?,?)",
            (revision_id, source_id, f"sha256:{source_id}", None, "2026-01-01T00:00:00Z"))
        connection.commit()
    blocks, document_units, spans_by_unit = [], [], {}
    ordinal = 1
    for unit_ordinal, (unit_id, (header, rows)) in enumerate(units.items()):
        header_ref = f"/page/{rows[0][1]}/SectionHeader/{ordinal}"
        span_ids = []
        blocks.append(_Block.build(span_id=f"t{ordinal}", block_type="SectionHeader", text=header, ordinal=ordinal,
                                   page=rows[0][1], section_path=[header_ref], extractor_block_id=header_ref,
                                   role_hint=_classify("SectionHeader", [header], header)))
        span_ids.append(f"t{ordinal}")
        ordinal += 1
        for text, page in rows:
            blocks.append(_Block.build(span_id=f"t{ordinal}", block_type="Text", text=text, ordinal=ordinal, page=page,
                                       section_path=[header_ref], role_hint=_classify("Text", [header], text)))
            span_ids.append(f"t{ordinal}")
            ordinal += 1
        spans_by_unit[unit_id] = span_ids
        document_units.append(_Unit(unit_id=unit_id, label=header, ordinal=unit_ordinal,
                                    semantic_hash=f"sha256:{unit_id}", page_start=rows[0][1], page_end=rows[-1][1],
                                    span_ids=span_ids))
    ir = _IR(extractor="marker", extractor_version="1", units=document_units, blocks=blocks, assets=[],
             health=_Health())
    _persist_ir(repository, ir, revision_id=revision_id, extraction_id=extraction_id)
    return spans_by_unit


def build_textbook_vault(root: Path, *, embeddings: bool = False) -> tuple[VaultPaths, Repository, dict[str, list[str]]]:
    """T6's retrieval vault plus a primary textbook with exercises and solutions."""

    from learnloop.vault.yaml_io import read_yaml, write_yaml

    paths, repository = build_retrieval_vault(root, embeddings=embeddings)
    lo_path = paths.learning_object_path("linear-algebra", "lo_matrices")
    lo = read_yaml(lo_path)
    lo["blueprints"] = [{"id": "bp_matrices", "recipes": [{"id": "r_matrices", "any_of": [
        {"facet": facet, "capability": "procedure_execution"}
        for facet in ("facet_eigen", "facet_determinant", "facet_matmul")]}]}]
    write_yaml(lo_path, lo)
    spans = seed_textbook(repository)
    _upsert_source_set(paths.root, {
        "id": "sset_la", "subject_id": "linear-algebra", "title": "Linear algebra sources",
        "members": [
            {"source_id": "src_book", "revision_id": "rev_book", "default_role": "primary_textbook"},
            {"source_id": "src_exam", "revision_id": "rev_exam", "default_role": "exam"},
            {"source_id": "src_text", "revision_id": "rev_text", "default_role": "primary_textbook"},
        ],
    })
    return paths, repository, spans


def _words(text: str) -> set[str]:
    return {word for word in _re.findall(r"[a-z]+", (text or "").casefold()) if len(word) > 2}


def _number(text: str) -> str | None:
    match = _re.match(r"\s*(?:exercise\s+)?(\d+)", (text or "").casefold())
    return match.group(1) if match else None


class FakeServiceLLM:
    """One deterministic client for every role the canonical-sources service calls.

    It answers from the prompt's own JSON, by result model, using lexical
    overlap where a real model would judge, ``solve_linear`` for numeric
    solves and sympy for equivalence. Knobs:

    * ``panel_answers``: substring of the stem -> the panel's answer;
    * ``key_override``: the authored key for every exercise;
    * ``family_verdict``: ``same`` | ``different`` (+ ``family_relation``);
    * ``drop_cited_quote``: author no quote even with the book's solution.
    """

    provider_name = "fake_service_llm"
    provider_type = "codex_sdk"
    model = "fake-service-model"

    def __init__(self, *, panel_answers: dict[str, str] | None = None, key_override: str | None = None,
                 family_verdict: str = "different", family_relation: str = "isomorph",
                 drop_cited_quote: bool = False, sympy_check: str | None = None,
                 learning_object_id: str = "lo_matrices", fail_purposes: set[str] | None = None,
                 bad_comparison_quote: bool = False, screen_complete: bool = True,
                 equivalence_verdict: str | None = None) -> None:
        self.bad_comparison_quote = bad_comparison_quote
        self.screen_complete = screen_complete
        self.equivalence_verdict = equivalence_verdict
        self.panel_answers = dict(panel_answers or {})
        self.key_override = key_override
        self.family_verdict = family_verdict
        self.family_relation = family_relation
        self.drop_cited_quote = drop_cited_quote
        self.sympy_check = sympy_check or SYMPY_CHECK
        self.learning_object_id = learning_object_id
        self.fail_purposes = set(fail_purposes or ())
        self.calls: list[tuple[str, str]] = []

    def supports(self, capability: str) -> bool:
        return capability in {"structured_completion", "bounded_structured_completion", "isolated_turn"}

    def complete(self, request):
        from learnloop.ai.errors import AIProviderUnavailable

        name = request.result_model.__name__
        self.calls.append((request.purpose, name))
        _report_usage({"input_tokens": len(request.prompt) // 4, "output_tokens": 60, "resolved_model": self.model})
        if request.purpose in self.fail_purposes or name in self.fail_purposes:
            raise AIProviderUnavailable("fake failure")
        handler = getattr(self, "_" + name, None)
        if handler is None:
            raise AssertionError(f"unexpected result model {name}")
        return handler(request, prompt_context(request.prompt))

    # practice_rerank (items) and the mixed pool
    @staticmethod
    def _grade(request_text: str, text: str) -> str:
        hits = len(_words(request_text) & _words(text))
        return "relevant" if hits >= 2 else "partial" if hits == 1 else "not_relevant"

    def _PracticeRerank(self, request, context):
        from learnloop.practice_index.contracts import CandidateJudgment, PracticeRerank

        judged = [(c["ref"], self._grade(context["request"], c.get("prompt", ""))) for c in context["candidates"]]
        order = {"relevant": 0, "partial": 1}
        picks = [ref for ref, grade in sorted(judged, key=lambda pair: (order.get(pair[1], 9), pair[0]))
                 if grade != "not_relevant"][: context["pick_at_most"]]
        return PracticeRerank(judgments=[CandidateJudgment(ref=ref, relevance=grade, rationale=f"{grade} by overlap")
                                         for ref, grade in judged], picks=picks)

    def _MixedPracticeRerank(self, request, context):
        from learnloop.practice_index.contracts import (
            CandidateJudgment, ExerciseMetadata, FacetQuote, MixedPracticeRerank,
        )

        def text(candidate):
            return candidate.get("statement") or candidate.get("prompt") or ""

        judged = [(c["ref"], self._grade(context["request"], text(c)), c) for c in context["candidates"]]
        order = {"relevant": 0, "partial": 1}
        picks = [ref for ref, grade, _c in sorted(judged, key=lambda entry: (order.get(entry[1], 9), entry[0]))
                 if grade != "not_relevant"][: context["pick_at_most"]]
        metadata = []
        modes = context.get("practice_modes") or ["short_answer"]
        for ref, _grade, candidate in judged:
            if candidate.get("kind") != "textbook_exercise":
                continue
            statement = candidate.get("statement") or ""
            facets = []
            for facet in context.get("facet_vocabulary") or []:
                stems = {word[:6] for word in _words(facet["title"])}
                shared = sorted(word for word in _words(statement) if word[:6] in stems)
                if shared:
                    match = _re.search(r"\S+\s+" + _re.escape(shared[0]), statement, _re.IGNORECASE)
                    quote = match.group(0) if match else statement[:30]
                    facets.append(FacetQuote(facet_id=facet["id"], quote=quote))
            metadata.append(ExerciseMetadata(ref=ref, facets=facets, practice_mode=modes[0]))
        return MixedPracticeRerank(
            judgments=[CandidateJudgment(ref=ref, relevance=grade, rationale=f"{grade} by overlap")
                       for ref, grade, _c in judged],
            picks=picks, exercise_metadata=metadata)

    # T6 verification
    def _SpanVerification(self, request, context):
        from learnloop.source_retrieval.contracts import SpanJudgment, SpanVerification

        question = " ".join([context["question"], context.get("practice_question") or ""])
        judged = []
        for c in context["candidates"]:
            hits = len(_words(question) & _words(c["passage"]))
            judged.append((c["ref"], "answers" if hits >= 2 else "related" if hits == 1 else "unrelated"))
        order = {"answers": 0, "related": 1}
        picks = [ref for ref, verdict in sorted(judged, key=lambda pair: (order.get(pair[1], 9), pair[0]))
                 if verdict != "unrelated"][: context["pick_at_most"]]
        return SpanVerification(judgments=[SpanJudgment(ref=ref, verdict=verdict, rationale="overlap")
                                           for ref, verdict in judged], picks=picks)

    # S1: the book's solution
    def _SolutionMatch(self, request, context):
        from learnloop.content.authoring.source_exercise_import import SolutionJudgment, SolutionMatch

        number = _number(context["exercise"]["statement"]) or _number(context["exercise"].get("label") or "")
        judged = []
        for c in context["candidates"]:
            other = _number(c["passage"])
            verdict = ("solves_this_exercise" if number and other == number
                       else "other_exercise" if other else "unrelated")
            judged.append((c["ref"], verdict))
        picks = [ref for ref, verdict in judged if verdict == "solves_this_exercise"][:1]
        return SolutionMatch(judgments=[SolutionJudgment(ref=ref, verdict=verdict, rationale="numbers")
                                        for ref, verdict in judged], picks=picks)

    # S1: authoring
    def _ExerciseAuthoring(self, request, context):
        from learnloop.content.authoring.ai_contracts import (
            ExerciseAuthoredItem, ExerciseAuthoring, FacetWeightPayload, RubricCriterionPayload, RubricPatchPayload,
        )

        text = context["exercise_text"]
        solution = (context.get("book_solution") or {}).get("text") or ""
        cited = ""
        if self.key_override is not None:
            key = self.key_override
        elif solution:
            numbers = _re.findall(r"-?\d+", solution.split(".", 1)[1] if "." in solution else solution)
            key = numbers[-1] if numbers and "eigenvalues of a diagonal" not in solution else (
                "2 and 3" if "diagonal" in solution else solution)
            cited = "" if self.drop_cited_quote else solution.split(". ", 1)[1] if ". " in solution else solution
        else:
            key = solve_linear(text) or ("the determinant is multiplied by -1" if "determinant" in text
                                         else "2 and 3")
        catalog = context.get("learning_objects") or []
        lo = next((entry for entry in catalog if entry["id"] == self.learning_object_id), catalog[0] if catalog else {})
        facets = [facet["id"] for facet in lo.get("facets", [])
                  if {word[:6] for word in _words(facet["title"])} & {word[:6] for word in _words(text)}]
        return ExerciseAuthoring(items=[ExerciseAuthoredItem(
            statement_md=text, title=f"Exercise {_number(text) or 1}", learning_object_id=lo.get("id", ""),
            practice_mode="short_answer", expected_answer_md=key,
            grading_rubric=RubricPatchPayload(max_points=2, criteria=[
                RubricCriterionPayload(id="answer", points=2.0, description="Gives the correct answer.")]),
            evidence_facets=facets, evidence_weights=[FacetWeightPayload(facet_id=f, weight=1.0) for f in facets],
            hints=["Start from the definition.", "Isolate the unknown."], capability="",
            classification_reason="fake", cited_quote=cited,
        )], warnings=[])

    # PF verification roles
    def _PanelSolve(self, request, context):
        from learnloop.content.authoring import pf_contracts as C

        stem = context.get("problem") or context.get("question") or ""
        for fragment, answer in self.panel_answers.items():
            if fragment in stem:
                kind = "numeric" if _re.fullmatch(r"-?\d+(?:/\d+)?", answer) else "text"
                return C.PanelSolve(final_answer=answer, answer_kind=kind, work_summary="configured")
        answer = solve_linear(stem)
        if answer is not None:
            return C.PanelSolve(final_answer=answer, answer_kind="numeric", work_summary="solved")
        return C.PanelSolve(final_answer="UNSOLVABLE", answer_kind="text", work_summary="cannot")

    def _EquivalenceResult(self, request, context):
        from sympy import simplify, sympify

        from learnloop.content.authoring import pf_contracts as C

        reference = context["reference_final_answer"]
        try:
            sympify(reference)
            kind = "numeric"
        except Exception:
            kind = "text"
        agreements = []
        for entry in context["answers"]:
            try:
                agreements.append(bool(simplify(sympify(reference) - sympify(entry["answer"])) == 0))
            except Exception:
                agreements.append(" ".join(entry["answer"].split()).casefold()
                                  == " ".join(reference.split()).casefold())
        return C.EquivalenceResult(answer_kind=kind, agreements=agreements,
                                   sympy_check=self.sympy_check if kind == "numeric" else None)

    def _SpanSupportVerdict(self, request, context):
        from learnloop.content.authoring import pf_contracts as C

        span = set(_re.findall(r"\w+", context["cited_span"].casefold()))
        words = set(_re.findall(r"\w+", context["reference_answer"].casefold()))
        supported = bool(words) and words <= span
        return C.SpanSupportVerdict(span_answer=context["cited_span"][:200], answer_supported=supported,
                                    rationale_supported=supported, executable_consequence=False,
                                    rationale="word check")

    # S3: intent-fit verification and the comparison
    def _IntentVerification(self, request, context):
        from learnloop.source_retrieval.find_sources import INTENT_VERDICTS, IntentJudgment, IntentVerification

        match = _re.search(r"source_intent_fit\.v1\.(\w+)", request.prompt)
        intent = match.group(1) if match else "explain"
        best, middle, *_rest = INTENT_VERDICTS[intent]
        worst = INTENT_VERDICTS[intent][-1]
        question = " ".join([context.get("question") or ""] + [
            " ".join(str(v) for v in m.values()) for m in context.get("misconceptions") or []])
        judged = []
        for c in context["candidates"]:
            hits = len(_words(question) & _words(c["passage"]))
            judged.append((c["ref"], best if hits >= 2 else middle if hits == 1 else worst))
        drop = {worst} | ({"same_treatment"} if intent == "alternative" else set())
        order = {best: 0, middle: 1}
        picks = [ref for ref, verdict in sorted(judged, key=lambda pair: (order.get(pair[1], 9), pair[0]))
                 if verdict not in drop][: context["pick_at_most"]]
        return IntentVerification(judgments=[IntentJudgment(ref=ref, verdict=verdict, rationale="overlap")
                                             for ref, verdict in judged], picks=picks)

    def _SourceComparison(self, request, context):
        from learnloop.source_retrieval.compare import Contribution, PairRelation, SourceComparison

        sources = context["sources"]
        requested = context.get("requested_perspectives") or []

        def quote(text, words=6):
            return " ".join(text.split()[:words])

        contributions = [Contribution(source_ref=src["ref"], contribution=f"{src['source']} states it its way",
                                      perspective=requested[0] if requested else "its own view",
                                      quote=quote(src["passage"])) for src in sources]
        if self.bad_comparison_quote and sources:
            contributions.append(Contribution(source_ref=sources[0]["ref"], contribution="invented",
                                              perspective="made up", quote="words that are nowhere in the passage"))
        relations = []
        for left, right in zip(sources, sources[1:]):
            relations.append(PairRelation(left_ref=left["ref"], right_ref=right["ref"], relation="different_notation",
                                          statement="same idea, different notation", left_quote=quote(left["passage"], 5),
                                          right_quote=quote(right["passage"], 5)))
        return SourceComparison(contributions=contributions, relations=relations,
                                missing_perspectives=requested[1:])

    # S2a: the exercise screen and the worked-example equivalence judge
    def _ExerciseScreens(self, request, context):
        from learnloop.instructional.screen import ExerciseScreen, ExerciseScreens, HypothesisSignature

        screens = []
        for exercise in context["exercises"]:
            signatures = []
            for index, hypothesis in enumerate(context["hypotheses"]):
                key = f"k{index}" if self.screen_complete else "same"
                signatures.append(HypothesisSignature(hypothesis_ref=hypothesis["ref"],
                                                      observable_signature=f"writes {key}", signature_key=key))
            screens.append(ExerciseScreen(exercise_ref=exercise["ref"], signatures=signatures,
                                          other_cause_signature="something else",
                                          differ_observably=self.screen_complete))
        return ExerciseScreens(screens=screens)

    def _EquivalenceVerdicts(self, request, context):
        from learnloop.instructional.exposure import EquivalenceJudgment, EquivalenceVerdicts

        question = context["question"]
        judged = []
        for example in context["worked_examples"]:
            overlap = len(_words(question) & _words(example["text"]))
            verdict = self.equivalence_verdict or (
                "equivalent" if overlap >= 6 else "related" if overlap >= 2 else "unrelated")
            judged.append(EquivalenceJudgment(ref=example["ref"], verdict=verdict, rationale="overlap"))
        return EquivalenceVerdicts(judgments=judged, picks=[])

    def _FamilyVerdict(self, request, context):
        from learnloop.ops.family_proposals import FamilyVerdict

        if self.family_verdict == "same":
            return FamilyVerdict(verdict="same", variant_relation=self.family_relation, rationale="same target",
                                 idea_statement="find an eigenvalue", retrieval_target="solve for the eigenvalue")
        return FamilyVerdict(verdict="different", variant_relation=None, rationale="different",
                             idea_statement="", retrieval_target="")


def service_clients(llm: FakeServiceLLM) -> dict[str, Any]:
    """The injected clients the import pipeline resolves by role."""

    return {name: llm for name in ("authoring", "panel", "equivalence", "span_support", "solution_match",
                                   "family_judge")}
