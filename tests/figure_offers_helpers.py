"""What other test files use from ``tests/test_figure_offers.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from typing import Any

from learnloop.ids import new_ulid
from learnloop.source_retrieval import library_ask as LA
from learnloop.tutor import ai_contracts as C

from tests.figure_fixtures import EXTRACTION, build_figure_vault, set_config
from tests.pf_fakes import prompt_context


NOW = "2026-10-23T10:00:00Z"
#: ext_prob's §5.4: p2 prose, p3 the density's equation, p4 its figure, p5 the caption.
KEYS = [f"{EXTRACTION}:{span}" for span in ("p2", "p3", "p4", "p5")]


class ExplorableOrganizer:
    """The library organizer, deterministic: every passage contributes, its own
    line; ``explorable`` yes on every candidate it was told is a block (or on
    ``say_yes`` refs), unless ``old`` (an output without the field)."""

    provider_name = "fake_organizer"
    provider_type = "codex_sdk"
    model = "fake-organizer-model"

    def __init__(self, *, old: bool = False, say_yes: tuple[str, ...] | None = None) -> None:
        self.old = old
        self.say_yes = say_yes
        self.prompts: list[str] = []
        self.models: list[str] = []

    def supports(self, capability: str) -> bool:
        return capability in {"structured_completion", "bounded_structured_completion", "isolated_turn"}

    def complete(self, request: Any) -> Any:
        from learnloop.ai.execution import report_call_usage

        self.prompts.append(request.prompt)
        self.models.append(request.result_model.__name__)
        report_call_usage({"input_tokens": len(request.prompt) // 4, "output_tokens": 80, "resolved_model": self.model})
        context = prompt_context(request.prompt)
        judgments = []
        for candidate in context["candidates"]:
            ref = candidate["ref"]
            fields: dict[str, Any] = {"ref": ref, "verdict": "contributes", "rationale": f"adds {ref}'s own point",
                                      "cites": [ref], "roles": [], "speaks_to": ""}
            if not self.old and "explorable" in request.result_model.model_fields["judgments"].annotation.__args__[0].model_fields:
                yes = ref in self.say_yes if self.say_yes is not None else "block" in candidate
                fields["explorable"] = "yes" if yes else "no"
            judgments.append(fields)
        return request.result_model.model_validate({"judgments": judgments,
                                                    "picks": [c["ref"] for c in context["candidates"]]})


def _vault(tmp_path, *, roles: bool = False, **figures: Any):
    """The figure vault; RW4e's on-demand roles off unless asked (so the organizer
    request is RW4a's base and its explorable twin)."""

    paths, repository = build_figure_vault(tmp_path / "vault")
    set_config(paths, "roles", on_demand_enabled=roles)
    if figures:
        set_config(paths, "figures", **figures)
    return paths, repository


def _ask(repository, keys=KEYS) -> str:
    ask_id = "la_" + new_ulid()
    with repository.connection() as connection:
        LA.ask_store.insert_ask(connection, {
            "id": ask_id, "entry": "reader", "query_md": "what is the two-sided exponential?", "query_hash": ask_id,
            "extraction_id": EXTRACTION, "anchor": {"span_ids": ["p2"], "learning_object_ids": []},
            "personalized": False, "organizer": {"status": "not_run"}, "prompt_version": LA.PROMPT_VERSION,
            "manifest": {"main": {"returned": [key.split(":", 1) for key in keys]}, "expansions": []},
            "created_at": NOW})
        connection.commit()
    return ask_id


def _tutor_event(repository, explorable) -> str:
    """A Reader tutor answer as stored (its question event), its view naming
    ``explorable``, and the tutor's verdicts in the ledger as the answer path
    records them (Codex review F3)."""

    from types import SimpleNamespace

    from learnloop.tutor import tutor_qa as TQ

    event_id = repository.insert_question_event({
        "context": "reader", "note_id": f"span:{EXTRACTION}/p2", "question_md": "what is f?", "answer_md": "a",
        "source_context": {"reader_tutor": {"explorable": explorable}}, "created_at": NOW})
    answer = SimpleNamespace(explorable=[C.ExplorableCitation(extraction_id=entry["extraction_id"],
                                                              span_id=entry["span_id"], explorable="yes")
                                         for entry in explorable])
    TQ._record_explorable_verdicts(repository, event_id, answer, model="fake-tutor-model",
                                   prompt_version=C.READER_TUTOR_EXPLORABLE_PROMPT_VERSION, clock=None)
    return event_id
