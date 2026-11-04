"""The one new authoring operation (spec §4.1), on a frontier LLM.

It takes the router's decision and the rival causes, and writes the question, the key, an
independently authored criterion contract and a manipulation contract. There is no
template fallback on this lane: parametric templates can't aim at specific hypotheses,
so a failure here is a typed failure (§6.2).

The context builder is where exam material is kept out (§4.1, §8): it reads the one
authority (``learner_protection.withheld_items``), fails closed when that can't be read,
and an authored question is then checked, locally, against what was withheld.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import re
from typing import Any

from learnloop.ai.transport import execute_structured_operation
from learnloop.db.repositories import Repository
from learnloop.diagnosis.ai_contracts import (
    FollowupProbeAuthored,
    FollowupProbeContext,
    followup_probe_prompt,
)

AUTHORING_PURPOSE = "followup_probe_authoring"
#: The structured route's task: a frontier LLM, not the Decider (owner, Nov 3).
AUTHOR_ROUTE = "followup_probe_author"
#: The axes an author may declare; the rest are the system's to write.
AUTHOR_AXES: frozenset[str] = frozenset({"surface_wording", "answer_contract", "rubric"})


class AuthoringRejected(ValueError):
    """An authored question failed an output check: nothing was written, nothing is served."""


@dataclass(frozen=True)
class AuthoredProbe:
    authored: FollowupProbeAuthored
    #: hypothesis id -> the criteria a learner with only that cause would miss.
    failing: Mapping[str, tuple[str, ...]]
    #: The transparent reference the prompt used -> hypothesis id.
    refs: Mapping[str, str]


def protection_view(vault: Any, repository: Repository) -> Any:
    """The withheld items; raises when they can't be read, so no prompt is built."""

    from learnloop.learner_protection import withheld_items

    withheld = withheld_items(vault, repository)
    if not withheld.available:
        raise AuthoringRejected("protection_unavailable")
    return withheld


def admissible_item(withheld: Any, item: Any) -> bool:
    return withheld.reason(str(item.id)) is None


def build_context(
    vault: Any,
    repository: Repository,
    *,
    learning_object_id: str,
    hypotheses: Sequence[Mapping[str, Any]],
    router_decision: Mapping[str, Any],
    target_facets: Sequence[str],
    source_item_id: str | None,
    measurement_pattern: str | None = None,
) -> tuple[FollowupProbeContext, dict[str, str]]:
    """The prompt's context, and the reference -> hypothesis id map.

    Only what ``protection_view`` admits reaches it. The hypotheses carry their statement,
    scope and typed target: never a postdictive claim, and never the learner's answer.
    """

    withheld = protection_view(vault, repository)
    learning_object = vault.learning_objects[learning_object_id]
    existing = sorted(
        item.prompt.strip()
        for item in vault.practice_items.values()
        if item.learning_object_id == learning_object_id and item.prompt and admissible_item(withheld, item)
    )
    source = vault.practice_items.get(source_item_id) if source_item_id else None
    refs: dict[str, str] = {}
    rows: list[dict[str, Any]] = []
    for index, hypothesis in enumerate(hypotheses):
        ref = f"H{index + 1}"
        refs[ref] = str(hypothesis["id"])
        rows.append({
            "hypothesis_ref": ref,
            "statement": str(hypothesis.get("statement") or ""),
            "cause_scope": str(hypothesis.get("cause_scope") or ""),
            "target_ref": hypothesis.get("target_ref"),
        })
    return (
        FollowupProbeContext(
            learning_object_title=learning_object.title,
            learning_object_concept=learning_object.concept,
            learning_object_summary=learning_object.summary,
            target_facets=[str(value) for value in target_facets],
            hypotheses=rows,
            router_decision=dict(router_decision),
            measurement_pattern=measurement_pattern,
            source_question_md=source.prompt if source is not None and admissible_item(withheld, source) else None,
            existing_prompts=existing,
        ),
        refs,
    )


def request_authored_probe(client: Any, context: FollowupProbeContext) -> FollowupProbeAuthored:
    return execute_structured_operation(
        client,
        purpose=AUTHORING_PURPOSE,
        prompt=followup_probe_prompt(context),
        result_model=FollowupProbeAuthored,
    )


def _normalized(text: str) -> str:
    return re.sub(r"\W+", " ", str(text or "")).strip().casefold()


def check_output(
    vault: Any,
    repository: Repository,
    authored: FollowupProbeAuthored,
    *,
    refs: Mapping[str, str],
    learning_object_id: str,
) -> AuthoredProbe:
    """The output checks that run before anything is written (§4.1).

    The criterion contract must let the rivals be told apart, and the question must not
    repeat any item the context withheld (compared here, never shown to the model).
    """

    prompt = authored.prompt_md.strip()
    expected = authored.expected_answer_md.strip()
    if not prompt or not expected:
        raise AuthoringRejected("empty_question_or_key")
    if _normalized(prompt) == _normalized(expected):
        raise AuthoringRejected("prompt_equals_key")
    ids = [criterion.id.strip() for criterion in authored.criteria]
    if len(ids) < 2 or len(set(ids)) != len(ids) or any(not value for value in ids):
        raise AuthoringRejected("criteria_contract_invalid")
    if any(criterion.points <= 0 for criterion in authored.criteria):
        raise AuthoringRejected("criteria_contract_invalid")
    failing: dict[str, tuple[str, ...]] = {}
    known = set(ids)
    for prediction in authored.predictions:
        hypothesis_id = refs.get(prediction.hypothesis_ref.strip())
        if hypothesis_id is None:
            raise AuthoringRejected("prediction_names_unknown_hypothesis")
        wanted = tuple(sorted({value.strip() for value in prediction.fails_criteria}))
        if not wanted or not set(wanted) <= known:
            raise AuthoringRejected("prediction_not_over_the_criteria")
        failing[hypothesis_id] = wanted
    if set(failing) != set(refs.values()):
        raise AuthoringRejected("a_hypothesis_has_no_prediction")
    if len(set(failing.values())) != len(failing):
        raise AuthoringRejected("predictions_do_not_discriminate")
    declared = {entry.axis for entry in authored.intended_manipulations} | set(authored.incidental_changes)
    if not declared <= AUTHOR_AXES or set(authored.held_constant) & declared:
        raise AuthoringRejected("manipulation_contract_invalid")
    withheld = protection_view(vault, repository)
    shown = _normalized(prompt)
    for item in vault.practice_items.values():
        if admissible_item(withheld, item) or item.learning_object_id != learning_object_id:
            continue
        if item.practice_mode == "diagnostic_probe":
            # Not exam material: the structural gate's duplicate rule covers it.
            continue
        other = _normalized(item.prompt)
        if other and (other in shown or shown in other):
            raise AuthoringRejected("repeats_protected_material")
    return AuthoredProbe(authored=authored, failing=failing, refs=dict(refs))


def resolve_author_client(vault: Any) -> Any | None:
    """The route's client, or None when it is not ready (nothing is spent)."""

    from learnloop.ai.routing import ready_client_for_task

    resolved = ready_client_for_task(vault.root, vault.config, AUTHOR_ROUTE)
    return resolved.client if resolved.ready else None


__all__ = [
    "AUTHORING_PURPOSE", "AUTHOR_AXES", "AUTHOR_ROUTE", "AuthoredProbe", "AuthoringRejected", "admissible_item",
    "build_context", "check_output", "protection_view", "request_authored_probe", "resolve_author_client",
]
