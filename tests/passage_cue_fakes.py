"""Builders and fakes for reader workbench RW3b's tests (no network).

``build_cue_vault`` is RW4a's library vault (``tests/library_ask_fixtures``:
two books and an exam in one source set, LOs linked to their passages, a
concept graph) with an active misconception on ``lo_matrices``, whose
statement shares words with the textbook's row-swap passage and its worked
example. ``CueJudgeFake`` answers the cue judge from the prompt's own JSON by
word overlap (plumbing checks, never evidence about quality); its knobs name
the misbehaviours the tests need.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from learnloop.ai.execution import report_call_usage
from learnloop.db.repositories import Repository
from learnloop.source_retrieval.passage_cues import CueJudgeResult, CueJudgment, RoleProposal
from tests.library_ask_fixtures import build_library_vault
from tests.pf_fakes import prompt_context
from tests.source_service_fakes import loaded, set_config  # noqa: F401 - re-exported

STATEMENT = "Swapping two rows of a matrix leaves its determinant unchanged"
#: Words that carry no topic (the fake's overlap ignores them).
_STOP = {"the", "and", "its", "for", "two", "are", "when", "of", "a", "is", "so", "by", "leaves"}


def words(text: str) -> set[str]:
    return {word for word in re.findall(r"[a-z]+", (text or "").casefold()) if len(word) > 2 and word not in _STOP}


def build_cue_vault(root: Path, *, misconception: bool = True, statement: str = STATEMENT,
                    correction_source_ids: list[str] | None = None) -> tuple[Any, Repository, dict[str, list[str]]]:
    paths, repository, spans = build_library_vault(root)
    if misconception:
        repository.insert_misconception(
            id="mis_swap", learning_object_id="lo_matrices", statement=statement, status="active",
            correction_statement="Swapping two rows multiplies the determinant by -1.",
            correction_source_span_ids=correction_source_ids or [])
    return paths, repository, spans


class CueJudgeFake:
    """The cue judge, deterministic, from word overlap with the target.

    ``relation``: the relation every overlapping passage gets
    (``clarifies_distinction`` by default; ``try_first`` on a worked example
    when ``try_first``); ``none_all``: every passage ``none`` (G15);
    ``bad_quote``: substrings of passages whose quote is not their words;
    ``pick_try_first_everywhere``: ``try_first`` on every passage (the code
    keeps it only where it fits); ``reverse``: picks in reverse order;
    ``provider_type``: ``codex_sdk`` bills the subscription, any other is
    metered; ``fail``: the provider fails."""

    provider_name = "fake_cue_judge"
    model = "fake-cue-judge-model"

    def __init__(self, *, relation: str = "clarifies_distinction", none_all: bool = False,
                 bad_quote: tuple[str, ...] = (), try_first: bool = False, pick_try_first_everywhere: bool = False,
                 reverse: bool = False, roles: tuple[tuple[str, str], ...] = (("explanation", "medium"),),
                 provider_type: str = "codex_sdk", fail: bool = False) -> None:
        self.relation = relation
        self.none_all = none_all
        self.bad_quote = bad_quote
        self.try_first = try_first
        self.pick_try_first_everywhere = pick_try_first_everywhere
        self.reverse = reverse
        self.roles = roles
        self.provider_type = provider_type
        self.fail = fail
        self.prompts: list[str] = []
        self.contexts: list[dict[str, Any]] = []

    def supports(self, capability: str) -> bool:
        return capability in {"structured_completion", "bounded_structured_completion", "isolated_turn"}

    def complete(self, request):
        from learnloop.ai.errors import AIProviderUnavailable

        assert request.result_model is CueJudgeResult
        self.prompts.append(request.prompt)
        report_call_usage({"input_tokens": len(request.prompt) // 4, "output_tokens": 90,
                           "resolved_model": self.model})
        if self.fail:
            raise AIProviderUnavailable("fake failure")
        context = prompt_context(request.prompt)
        self.contexts.append(context)
        target = words(context["target"]["statement"])
        judgments = []
        scored: list[tuple[int, str]] = []
        for candidate in context["candidates"]:
            ref, passage = candidate["ref"], candidate["passage"]
            overlap = len(target & words(passage))
            relation = "none"
            if not self.none_all and overlap >= 2:
                relation = self.relation
                if self.try_first and candidate.get("role") in ("worked_example", "proof"):
                    relation = "try_first"
                scored.append((overlap, ref))
            if self.pick_try_first_everywhere and not self.none_all:
                relation = "try_first"
                if (overlap, ref) not in scored:
                    scored.append((overlap, ref))
            quote = " ".join(passage.split()[:8]) if relation != "none" else ""
            if any(marker in passage for marker in self.bad_quote):
                quote = "words this passage never says at all"
            judgments.append(CueJudgment(
                ref=ref, relation=relation, rationale=f"{relation} by overlap {overlap}", quote=quote,
                roles=[RoleProposal(role=role, confidence=confidence) for role, confidence in self.roles]))
        picks = [ref for _overlap, ref in sorted(scored, key=lambda pair: (-pair[0], pair[1]))]
        if self.reverse:
            picks = list(reversed(picks))
        return CueJudgeResult(judgments=judgments, picks=picks)


def guide_cue(paths: Any, repository: Repository, span_ids: list[str], *, lo_id: str = "lo_matrices",
              error_id: str = "err_guide", statement: str = "The determinant ignores row order") -> str:
    """Make the Guide cite ``span_ids`` (ext_text) for ``lo_id`` with an active
    misunderstanding there, so RW3a's Guide cues mark them. Returns the item id."""

    from learnloop.clock import FrozenClock
    from learnloop.vault.loader import load_vault
    from learnloop.vault.models import SourceRef
    from learnloop.vault.writer import upsert_practice_item
    from tests.helpers import NOW, NOW_ISO

    vault = load_vault(paths.root)
    item = next(item for item in vault.practice_items.values() if item.learning_object_id == lo_id)
    item.provenance.source_refs = [SourceRef(ref_type="canonical_source", ref_id="src_text",
                                             locator=f"span:ext_text/{span}", source_id="src_text",
                                             extraction_id="ext_text") for span in span_ids]
    upsert_practice_item(paths.root, item, clock=FrozenClock(NOW))
    repository.insert_error_event({
        "id": error_id, "learning_object_id": lo_id, "error_type": "conceptual_slip", "severity": 0.9,
        "is_misconception": True, "status": "active", "created_at": NOW_ISO, "misconception_statement": statement,
    })
    return item.id


def seed_link(repository: Repository, target: Any, span_id: str, *, relation: str = "clarifies_distinction",
              pick_rank: int = 1, extraction_id: str = "ext_text", quote: str = "seeded quote words of it",
              roles: list[dict] | None = None) -> str:
    """A cue judge's pick for ``target`` (a ``passage_cues.CueTarget``) as the
    judge would have written it: its ledger verdict and its link."""

    from learnloop.db.stores import reader_cue_links as store
    from learnloop.source_retrieval import passage_cues as PC

    ledger_id = f"pcj_{target.kind}_{target.id}_{span_id}".replace(":", "_")
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO judgment_ledger (id, created_at, task, left_kind, left_id, right_kind, right_id, judge, "
            "judge_model, prompt_version, input_hash, verdict, score, rationale) VALUES (?, '2026-10-01T00:00:00Z', "
            "'passage_cue', 'cue_target', ?, 'reader_span', ?, 'llm', 'm', ?, 'h', ?, 1.0, ?)",
            (ledger_id, target.left_id(extraction_id), f"{extraction_id}/{span_id}", PC.PROMPT_VERSION, relation,
             '{"pick_rank": %d, "text": "seeded"}' % pick_rank))
        link_id = store.insert_link(connection, {
            "id": PC._link_id(extraction_id, target, span_id), "extraction_id": extraction_id, "span_id": span_id,
            "target_kind": target.kind, "target_id": target.id, "relation": relation, "quote": quote,
            "pick_rank": pick_rank, "roles": roles or [], "target_facets": list(getattr(target, "facet_ids", ())),
            "ledger_id": ledger_id, "state_key": target.state_key,
            "model": "m", "prompt_version": PC.PROMPT_VERSION, "created_at": "2026-10-01T00:00:00Z"})
        connection.commit()
    return link_id


def target(kind: str, ident: str, *, p_open: float | None, lo_id: str = "lo_matrices", topic: str = "Matrices",
           statement: str | None = None, source: str = "episode_posterior") -> Any:
    from learnloop.source_retrieval.passage_cues import CueTarget

    return CueTarget(kind=kind, id=ident, statement=statement or f"statement of {ident}", status="active",
                     learning_object_ids=(lo_id,), topic=topic, p_open=p_open, p_open_source=source)


def snake(value: Any) -> Any:
    """A wire payload (camelCase keys) back in the server's snake_case."""

    if isinstance(value, dict):
        return {re.sub(r"(?<!^)(?=[A-Z])", "_", key).lower(): snake(item) for key, item in value.items()}
    if isinstance(value, list):
        return [snake(item) for item in value]
    return value
