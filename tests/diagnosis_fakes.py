"""Deterministic fakes for the Slice 1 grader, diagnoser, judge, generator and embedder.

No network and no paid call: every structured request is answered from the
JSON context the production prompt carries, so the tests exercise the real
prompts, wire models, validators and persistence.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from learnloop.ai.execution import model_call, report_call_usage
from learnloop.ai.transport import READ_ONLY_WORKSPACE, STRUCTURED_COMPLETION, StructuredRequest
from learnloop.attempts.ai_contracts import GradingProposal
from learnloop.attempts.blind_grading import BlindGradingProposal
from learnloop.diagnosis.offline_review.judge import DiagnosisJudgment, LinkJudgment, PlantedCauseJudgment
from learnloop.diagnosis.offline_review.planted import PlantedScenarioDraft
from learnloop.diagnosis.offline_review.probes import ParaphraseDraft, SyntheticErrorDraft, ValidAlternativeDraft


def prompt_payload(prompt: str) -> dict[str, Any]:
    for chunk in reversed(prompt.split("\n\n")):
        try:
            payload = json.loads(chunk)
        except (TypeError, ValueError):
            continue
        if isinstance(payload, dict):
            return payload
    raise AssertionError("no JSON payload in prompt")


def _quote(answer: str) -> str:
    words = answer.split()
    return " ".join(words[: min(3, len(words))]) or answer


class ReviewFakeClient:
    """One fake that answers every M1 purpose; flags tune its behaviour."""

    provider_name = "fake"

    def __init__(
        self,
        *,
        provider_type: str = "codex_sdk",
        model: str = "fake-model",
        workspace: bool = True,
        invent_id: bool = False,
        fail_purposes: tuple[str, ...] = (),
    ) -> None:
        self.provider_type = provider_type
        self.model = model
        self.workspace = workspace
        self.invent_id = invent_id
        self.fail_purposes = set(fail_purposes)
        self.calls: list[str] = []
        self.workspaces: list[Path] = []
        self.workspace_files: list[list[str]] = []
        self.prompts: list[str] = []

    def supports(self, capability: str) -> bool:
        return capability == STRUCTURED_COMPLETION or (capability == READ_ONLY_WORKSPACE and self.workspace)

    def workspace_activity(self) -> list[str] | None:
        return ["cat INDEX.md"] if self.workspaces else None

    def consume_usage(self):  # pragma: no cover - legacy surface
        return None

    def complete(self, request: StructuredRequest[Any]) -> Any:
        purpose = request.purpose
        self.calls.append(purpose)
        self.prompts.append(request.prompt)
        with model_call(self, purpose=f"{purpose}:fake_turn", prompt=request.prompt):
            report_call_usage({"input_tokens": len(request.prompt) // 4, "output_tokens": 200})
        if request.workspace is not None:
            self.workspaces.append(Path(request.workspace))
            self.workspace_files.append(sorted(str(path.relative_to(request.workspace)) for path in Path(request.workspace).rglob("*") if path.is_file()))
        if purpose in self.fail_purposes:
            from learnloop.ai.errors import AIProviderUnavailable

            raise AIProviderUnavailable(f"fake failure for {purpose}")
        payload = prompt_payload(request.prompt)
        context = payload.get("context") or {}
        handler = getattr(self, f"_{purpose}")
        return handler(request, context)

    # -- grading ---------------------------------------------------------------

    def _grade_parts(self, context: dict[str, Any]) -> dict[str, Any]:
        answer = str(context["learner_answer_md"])
        expected = str(context["expected_answer"])
        criteria = context["rubric"]["criteria"]
        correct = expected.strip() and expected.strip() in answer
        evidence = [
            {"criterion_id": criterion["id"], "points_awarded": float(criterion["points"]) if correct else 0.0, "evidence": "graded"}
            for criterion in criteria
        ]
        facets = list(context.get("evidence_facets") or [])
        return {"answer": answer, "correct": correct, "evidence": evidence, "facets": facets, "criteria": criteria}

    def _blind_grading(self, request, context):
        parts = self._grade_parts(context)
        attributions = []
        if not parts["correct"]:
            attributions.append(
                {
                    "error_type": "conceptual_slip",
                    "evidence": "The work diverges here.",
                    "first_divergence": {"anchor_kind": "span", "criterion_id": parts["criteria"][-1]["id"], "quote": _quote(parts["answer"])},
                    "target_evidence_families": parts["facets"][:1],
                    "resolution_status": "unresolved",
                    "validity_scope": "valid_measurement",
                }
            )
        return BlindGradingProposal.model_validate(
            {
                "local_analysis_md": "Correct." if parts["correct"] else f"The answer goes wrong at '{_quote(parts['answer'])}'.",
                "attempt_id": context["attempt_id"],
                "practice_item_id": context["practice_item_id"],
                "criterion_evidence": parts["evidence"],
                "rubric_score": int(sum(row["points_awarded"] for row in parts["evidence"])),
                "error_attributions": attributions,
                "grader_confidence": 0.9,
            }
        )

    def _grading(self, request, context):
        parts = self._grade_parts(context)
        attributions = []
        if not parts["correct"]:
            attributions.append(
                {
                    "error_type": "conceptual_slip",
                    "evidence": "The work diverges here.",
                    "is_misconception": True,
                    "misconception_statement": "The learner believes the old rule still applies.",
                    "first_divergence": {"anchor_kind": "span", "criterion_id": parts["criteria"][-1]["id"], "quote": _quote(parts["answer"])},
                    "resolution_status": "unresolved",
                    "cause_scope": "learner_state",
                    "candidate_causes": [{"statement": "The learner believes the old rule still applies.", "cause_scope": "learner_state"}],
                }
            )
        return GradingProposal.model_validate(
            {
                "diagnosis_md": "Stored explanation prose.",
                "attempt_id": context["attempt_id"],
                "practice_item_id": context["practice_item_id"],
                "criterion_evidence": parts["evidence"],
                "rubric_score": int(sum(row["points_awarded"] for row in parts["evidence"])),
                "error_attributions": attributions,
                "grader_confidence": 0.9,
            }
        )

    # -- diagnosis ---------------------------------------------------------------

    def _diagnosis(self, request, context):
        current = context["current_attempt"]
        history = context.get("history") or context.get("failure_history") or []
        failures = [row for row in history if row.get("outcome") == "non_pass" and row.get("first_divergence_quotes")]
        if request.workspace is not None:
            # Snapshot mode: read the export like an agent would.
            attempts_dir = Path(request.workspace) / "attempts"
            for path in sorted(attempts_dir.glob("*.md")) if attempts_dir.exists() else []:
                text = path.read_text(encoding="utf-8")
                attempt_id = text.splitlines()[0].replace("# Attempt ", "").strip()
                if "- outcome: non_pass" in text and "## First-divergence quotes" in text:
                    quote_block = text.split("## First-divergence quotes", 1)[1].strip().splitlines()
                    quote = quote_block[0][2:] if quote_block and quote_block[0].startswith("- ") else None
                    if quote:
                        failures.append({"attempt_id": attempt_id, "first_divergence_quotes": [quote]})
        events = []
        for attribution in current["blind_grade"]["error_attributions"]:
            events.append(
                {
                    "event_index": attribution["index"],
                    "first_divergence_quote": (attribution.get("first_divergence") or {}).get("quote"),
                    "causal_class": "learner_state",
                    "candidate_causes": [
                        {"statement": "The answer goes wrong because the learner misapplies the rule.", "cause_scope": "learner_state", "prior_weight": 2.0},
                        {"statement": "A slip while copying.", "cause_scope": "transient_execution", "prior_weight": 1.0},
                    ],
                    "registry_match": {"kind": "abstain"},
                    "history_changed_cause": {"changed": False, "note": ""},
                }
            )
        evidence = [row["attempt_id"] for row in failures[:2]]
        claims = []
        if failures and events:
            first = failures[0]
            claims.append(
                {
                    "hypothesis_ref": "cause:0:0",
                    "relation": "same_mechanism",
                    "cited": [{"attempt_id": first["attempt_id"], "quote": first["first_divergence_quotes"][0]}],
                }
            )
        if self.invent_id:
            evidence.append("att_does_not_exist")
        payload = {
            "evidence_attempt_ids": evidence,
            "analysis_md": "Diagnosis across time.",
            "event_diagnoses": events,
            "repair_suggestions": [
                {"practice_mode": "redo", "rationale": "Ask what the rule says.", "operator": "elicit_rule", "eliciting_question": "What does the rule say?"}
            ],
            "pattern_claims": claims,
        }
        return request.result_model.model_validate(payload)

    # -- judge ---------------------------------------------------------------------

    def _diagnosis_review_judgment(self, request, context):
        labels = sorted(context["explanations"])
        return DiagnosisJudgment.model_validate(
            {
                "analysis_md": "Reading.",
                "ratings": [
                    {"label": label, "rating": "right" if index == 0 else "partly", "reason": "ok"}
                    for index, label in enumerate(labels)
                ],
                "best": labels[0],
                "pairs": [
                    {"left": pair["left"], "right": pair["right"], "preferred": "left", "reason": "ok"}
                    for pair in context["requested_pairs"]
                ],
            }
        )

    def _diagnosis_link_judgment(self, request, context):
        return LinkJudgment.model_validate(
            {"links": [{"label": label, "verdict": "same", "reason": "ok"} for label in sorted(context["links"])]}
        )

    def _diagnosis_planted_cause_judgment(self, request, context):
        return PlantedCauseJudgment.model_validate(
            {"matches": [{"label": label, "matches": "target_cause", "reason": "ok"} for label in sorted(context["statements"])]}
        )

    # -- generator ----------------------------------------------------------------

    def _diagnosis_planted_scenario(self, request, context):
        shape = context["shape"]
        items = [row["practice_item_id"] for row in context["items"]]
        first, second = items[0], items[1 % len(items)]
        third = items[2 % len(items)]

        def fail(key, item, answer, cause, final=None):
            return {"key": key, "practice_item_id": item, "learner_answer_md": answer, "outcome": "fail", "cause": cause, "first_divergence_quote": answer.split(",")[0], "final_answer": final}

        if shape == "changed_cause":
            draft = {
                "cause_a_statement": "Believes transposing changes nothing.",
                "cause_b_statement": "Believes singular values can be negative.",
                "history": [fail("h1", first, "keep V as is, so A = U S V", "A"), fail("h2", second, "no transpose needed, B = U S V", "A"), fail("h3", first, "V stays, again U S V", "A")],
                "target": fail("t1", second, "sigma is -2, so the SVD has a negative value", "B"),
            }
        elif shape == "paraphrased_recurrence":
            draft = {
                "cause_a_statement": "Believes transposing changes nothing.",
                "cause_c_statement": "Mixes up rows and columns of U.",
                "history": [
                    fail("h1", first, "V unchanged, A = U S V", "A"),
                    fail("h2", second, "the last factor is just V, B = U S V", "A"),
                    fail("h3", third, "rows of U swapped, U = [[0,1],[1,0]]", "C"),
                    {"key": "h4", "practice_item_id": first, "learner_answer_md": "U Sigma V^T", "outcome": "pass", "cause": "none"},
                ],
                "target": fail("t1", second, "no need for V transpose, B = U S V", "A"),
            }
        else:
            draft = {
                "cause_a_statement": "Believes transposing changes nothing.",
                "cause_b_statement": "Multiplies the factors in the wrong order.",
                "history": [fail("h1", first, "V as is, giving U S V", "A", final="U S V")],
                "target": fail("t1", first, "order swapped, giving U S V", "B", final="U S V"),
            }
        return PlantedScenarioDraft.model_validate(draft)

    def _diagnosis_valid_alternative(self, request, context):
        return ValidAlternativeDraft.model_validate(
            {"method_note": "Different route.", "derivation_md": f"By another route: {context['reference_solution']}", "final_answer": context["reference_solution"]}
        )

    def _diagnosis_synthetic_error(self, request, context):
        criterion = context["rubric"][0]["id"]
        return SyntheticErrorDraft.model_validate(
            {"planted_criterion_id": criterion, "error_description": "One planted error.", "answer_md": "almost right but wrong here"}
        )

    def _diagnosis_paraphrase(self, request, context):
        return ParaphraseDraft.model_validate({"answer_md": f"Reworded: {context['learner_answer_md']}"})


class FakeEmbeddingClient:
    """Bag-of-words hashed into a few dimensions: similar text, near vectors."""

    provider_name = "openrouter_embedding"
    provider_type = "openai_embedding"

    def __init__(self, dims: int = 16, *, fail: bool = False) -> None:
        self.model_id = "qwen/qwen3-embedding-8b"
        self.model = self.model_id
        self.dims = dims
        self.modalities = frozenset({"text"})
        self.max_input_tokens = 32_768
        self.fail = fail
        self.calls = 0

    def embed(self, inputs, task_prefix):
        self.calls += 1
        if self.fail:
            from learnloop.ai.errors import AIProviderUnavailable

            raise AIProviderUnavailable("embedding down")
        with model_call(self, purpose="embedding", prompt=None):
            report_call_usage({"input_tokens": sum(len(str(text)) // 4 for text in inputs)})
        vectors = []
        for text in inputs:
            vector = [0.0] * self.dims
            for word in str(text).lower().split():
                digest = int(hashlib.sha256(word.encode()).hexdigest(), 16)
                vector[digest % self.dims] += 1.0
            vector[0] += 0.001
            vectors.append(vector)
        return vectors
