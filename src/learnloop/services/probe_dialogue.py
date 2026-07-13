"""Short adaptive dialogue microprobes (spec_probe_eig_redesign.md §8.1).

A dialogue block is a sequence of committed microprobe turns —
commit → decisive reason → minimally-changed case → counterexample — that
persists through the SAME pipeline as every other modality (§5.1): each turn
first receives its own committed presentation, then a lightweight
``diagnostic_probe`` attempt on the turn's ephemeral generated instance, plus
one probe observation referencing the attempt. Turns within one block are
correlated observations sharing the family's bounded task evidence mass
(§7.7): each turn's committed ``task_evidence_share`` damps its likelihood so
a block can never exceed one task's evidence.

The tutor withholds instructional content for the whole block; once a turn
teaches, the caller must end the block (`stop_diagnosing_and_teach`), which
opens a post-intervention state segment (§8.1).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services.probe_episodes import (
    EligibleInstrument,
    commit_presentation,
    episode_hypothesis_set,
    serve_presentation,
)
from learnloop.services.probe_families import (
    DIALOGUE_MICROPROBE_V1,
    map_episode_labels_to_slots,
    real_calibration_counts,
    validate_and_compile_card,
)
from learnloop.services.probe_instance_generation import (
    ensure_instrument_card,
    instance_gate_errors,
    parametric_instance_payloads,
    GENERATOR_ID,
    GENERATOR_VERSION,
    LLM_GENERATOR_ID,
    LLM_GENERATOR_VERSION,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault
from learnloop.vault.writer import upsert_practice_item

DIALOGUE_TURN_KINDS = ("commit", "reason", "counterfactual", "counterexample")
DIALOGUE_PRACTICE_MODE = "diagnostic_microprobe"

_KIND_TO_SURFACE_INDEX = {kind: index for index, kind in enumerate(DIALOGUE_TURN_KINDS)}


class DialogueBlockError(ValueError):
    pass


@dataclass
class DialogueTurn:
    kind: str
    practice_item_id: str | None = None
    presentation_id: str | None = None
    prompt_md: str | None = None
    submitted: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "practice_item_id": self.practice_item_id,
            "presentation_id": self.presentation_id,
            "prompt_md": self.prompt_md,
            "submitted": self.submitted,
        }


@dataclass
class DialogueBlockState:
    """Serializable dialogue-block state (mirrors the teach-back pattern)."""

    block_id: str
    learning_object_id: str
    probe_episode_id: str
    planned_kinds: list[str]
    task_evidence_share: float
    turns: list[DialogueTurn] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(
            {
                "block_id": self.block_id,
                "learning_object_id": self.learning_object_id,
                "probe_episode_id": self.probe_episode_id,
                "planned_kinds": list(self.planned_kinds),
                "task_evidence_share": self.task_evidence_share,
                "turns": [turn.as_dict() for turn in self.turns],
            }
        )

    @classmethod
    def from_json(cls, payload: str) -> "DialogueBlockState":
        data = json.loads(payload)
        return cls(
            block_id=str(data["block_id"]),
            learning_object_id=str(data["learning_object_id"]),
            probe_episode_id=str(data["probe_episode_id"]),
            planned_kinds=[str(kind) for kind in data["planned_kinds"]],
            task_evidence_share=float(data["task_evidence_share"]),
            turns=[
                DialogueTurn(
                    kind=str(turn["kind"]),
                    practice_item_id=turn.get("practice_item_id"),
                    presentation_id=turn.get("presentation_id"),
                    prompt_md=turn.get("prompt_md"),
                    submitted=bool(turn.get("submitted", False)),
                )
                for turn in data.get("turns", [])
            ],
        )

    @property
    def completed_turns(self) -> int:
        return sum(1 for turn in self.turns if turn.submitted)


def begin_dialogue_block(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    clock: Clock | None = None,
) -> DialogueBlockState:
    """Open a dialogue block against the LO's in-progress episode (§8.1)."""

    episode = repository.open_probe_episode(learning_object_id)
    if episode is None or episode.status != "in_progress":
        raise DialogueBlockError(f"no in-progress diagnostic episode for {learning_object_id}")
    resolved = ensure_instrument_card(
        vault, repository, learning_object_id, DIALOGUE_MICROPROBE_V1, clock=clock
    )
    if resolved is None:
        raise DialogueBlockError(
            f"the dialogue microprobe family cannot bind {learning_object_id}"
        )
    dialogue_config = vault.config.probe.dialogue
    planned = list(DIALOGUE_TURN_KINDS[: dialogue_config.planned_turns])
    card, template = resolved
    return DialogueBlockState(
        block_id=new_ulid(),
        learning_object_id=learning_object_id,
        probe_episode_id=episode.id,
        planned_kinds=planned,
        # §7.7 bounded task mass split across the block's planned turns.
        task_evidence_share=template.total_task_evidence_mass / max(len(planned), 1),
    )


def next_dialogue_turn(
    vault: LoadedVault,
    repository: Repository,
    state: DialogueBlockState,
    *,
    ai_client: object | None = None,
    clock: Clock | None = None,
) -> tuple[DialogueBlockState, dict[str, Any] | None]:
    """Mint and commit the next turn: ephemeral instance + presentation.

    Returns the payload the client serves ({prompt, presentation_id,
    practice_item_id, kind}) or None when the block's planned turns are done.
    The caller submits the learner's committed answer through the ordinary
    attempt pipeline with the returned presentation id.

    When ``ai_client`` supports ``run_probe_dialogue_turn``, the turn surface
    is generated adaptively — conditioned on the learner's prior committed
    answers in the block (§8.1) — and falls back to the parametric turn
    templates on provider failure or gate rejection.
    """

    pending = [turn for turn in state.turns if not turn.submitted and turn.presentation_id]
    if pending:
        turn = pending[0]
        return state, {
            "kind": turn.kind,
            "practice_item_id": turn.practice_item_id,
            "presentation_id": turn.presentation_id,
            "prompt_md": turn.prompt_md,
            "turn_number": len(state.turns),
            "planned_turns": len(state.planned_kinds),
        }
    if len(state.turns) >= len(state.planned_kinds):
        return state, None

    episode = repository.probe_episode(state.probe_episode_id)
    if episode is None or episode.status != "in_progress":
        return state, None
    hypothesis_set = episode_hypothesis_set(repository, episode)
    if hypothesis_set is None:
        return state, None
    resolved = ensure_instrument_card(
        vault, repository, state.learning_object_id, DIALOGUE_MICROPROBE_V1, clock=clock
    )
    if resolved is None:
        return state, None
    card, template = resolved

    kind = state.planned_kinds[len(state.turns)]
    payloads = parametric_instance_payloads(
        vault,
        card,
        template,
        count=len(DIALOGUE_TURN_KINDS),
        seed=0,
        clock=clock,
        surface_offset=0,
    )
    by_surface = {payload["surface_family"]: payload for payload in payloads}
    payload = by_surface.get(f"{template.id}_dialogue_{kind}")
    if payload is None:
        return state, None
    # Ephemeral per-block instance id: one instance per (block, turn), so a
    # block's turn attempts never collide with another block's.
    payload = dict(payload, id=f"pi_dlg_{state.block_id.lower()}_{len(state.turns)}_{kind}")
    if payload["id"] not in vault.practice_items:
        generator_id, generator_version = GENERATOR_ID, GENERATOR_VERSION
        generator_metadata: dict[str, Any] = {}
        adaptive = _adaptive_turn_surface(
            vault, repository, state, card, kind, ai_client=ai_client
        )
        if adaptive is not None:
            candidate = dict(payload, prompt=adaptive[0], expected_answer=adaptive[1])
            # The adaptive surface passes the same structural gate; a leaky or
            # ungrounded turn falls back to the parametric template.
            if not instance_gate_errors(vault, candidate, card, template):
                payload = candidate
                generator_id, generator_version = LLM_GENERATOR_ID, LLM_GENERATOR_VERSION
                generator_metadata = {
                    "generator_model": getattr(ai_client, "model", None),
                    "prompt_version": _dialogue_prompt_version(),
                }
        errors = instance_gate_errors(vault, payload, card, template)
        if errors:
            raise DialogueBlockError(f"dialogue turn instance failed the gate: {errors}")
        upsert_practice_item(vault.root, payload, clock=clock)
        repository.link_probe_item_family(
            practice_item_id=payload["id"],
            instrument_card_id=card.id,
            instrument_card_version=card.version,
            generator_id=generator_id,
            generator_version=generator_version,
            generation_seed=state.block_id,
            instance_metadata={
                "review_status": "dialogue_turn",
                "dialogue_block_id": state.block_id,
                "dialogue_turn_kind": kind,
                **generator_metadata,
            },
            clock=clock,
        )
        # Never schedulable as ordinary practice: turn instances exist only to
        # carry their one committed attempt.
        repository.upsert_practice_item_state(payload["id"], active=False, clock=clock)
        refreshed = load_vault(vault.root)
        refreshed.config = vault.config
        vault = refreshed

    # Family posterior only: a dialogue turn's ephemeral instance carries no
    # item residual worth pooling. Keyed by the same grader_version the write
    # path records under (§9.7).
    counts = real_calibration_counts(
        repository, template.id, template.version, grader_version=template.grader_policy
    )
    instrument = validate_and_compile_card(card, template, calibration_counts=counts)
    labels = [hypothesis.label for hypothesis in hypothesis_set.hypotheses]
    slot_map = map_episode_labels_to_slots(instrument, labels, bindings=card.bindings)
    if slot_map is None:
        return state, None
    eligible = EligibleInstrument(
        item=vault.practice_items[payload["id"]],
        instrument=instrument,
        slot_map=slot_map,
        expected_information_gain=0.0,
        selection_objective="dialogue_block",
    )
    presentation = commit_presentation(
        vault,
        repository,
        episode,
        eligible,
        extra_selection_components={
            "task_evidence_share": state.task_evidence_share,
            "dialogue_block_id": state.block_id,
            "dialogue_turn_kind": kind,
            "dialogue_turn_number": len(state.turns) + 1,
        },
        clock=clock,
    )
    serve_presentation(repository, presentation.id, clock=clock)
    turn = DialogueTurn(
        kind=kind,
        practice_item_id=payload["id"],
        presentation_id=presentation.id,
        # Read from the vault item: on a crash-resume the persisted instance
        # (possibly LLM-generated) wins over this call's freshly built payload.
        prompt_md=str(vault.practice_items[payload["id"]].prompt),
    )
    state.turns.append(turn)
    return state, {
        "kind": kind,
        "practice_item_id": turn.practice_item_id,
        "presentation_id": turn.presentation_id,
        "prompt_md": turn.prompt_md,
        "turn_number": len(state.turns),
        "planned_turns": len(state.planned_kinds),
    }


def _dialogue_prompt_version() -> str:
    from learnloop.codex.prompts import PROBE_DIALOGUE_TURN_PROMPT_VERSION

    return PROBE_DIALOGUE_TURN_PROMPT_VERSION


def _prior_turns_with_answers(
    repository: Repository, state: DialogueBlockState
) -> list[dict[str, Any]]:
    """The block so far as {kind, prompt_md, learner_answer_md}, oldest first.

    Each turn instance carries exactly one accepted attempt (unique index on
    probe_presentation_id), so the item's latest attempt IS the turn's answer.
    """

    prior: list[dict[str, Any]] = []
    for turn in state.turns:
        if not turn.submitted or turn.practice_item_id is None:
            continue
        attempts = repository.list_recent_attempts_by_practice_item(turn.practice_item_id, limit=1)
        answer = attempts[0].get("learner_answer_md") if attempts else None
        prior.append(
            {
                "kind": turn.kind,
                "prompt_md": turn.prompt_md,
                "learner_answer_md": answer or "(no answer recorded)",
            }
        )
    return prior


def _adaptive_turn_surface(
    vault: LoadedVault,
    repository: Repository,
    state: DialogueBlockState,
    card,
    kind: str,
    *,
    ai_client: object | None,
) -> tuple[str, str] | None:
    """LLM-generated (prompt, expected_answer) for one turn, or None to fall
    back to the parametric template (§8.1 adaptive dialogue)."""

    from learnloop.codex.client import CodexUnavailable, ProbeDialogueTurnContext

    if ai_client is None:
        return None
    run_turn = getattr(ai_client, "run_probe_dialogue_turn", None)
    if run_turn is None:
        return None
    learning_object = vault.learning_objects.get(state.learning_object_id)
    if learning_object is None:
        return None
    context = ProbeDialogueTurnContext(
        turn_kind=kind,
        turn_number=len(state.turns) + 1,
        planned_turns=len(state.planned_kinds),
        learning_object_id=learning_object.id,
        learning_object_title=learning_object.title,
        learning_object_concept=learning_object.concept,
        learning_object_summary=learning_object.summary,
        target_facets=[str(facet) for facet in card.target_facets],
        confusable_concept=(
            str(card.bindings["confusable_concept"])
            if card.bindings.get("confusable_concept")
            else None
        ),
        prior_turns=_prior_turns_with_answers(repository, state),
    )
    try:
        turn = run_turn(context)
    except CodexUnavailable:
        return None
    prompt = turn.prompt_md.strip()
    expected = turn.expected_answer_md.strip()
    if not prompt or not expected:
        return None
    return prompt, expected


def record_turn_submitted(state: DialogueBlockState, presentation_id: str) -> DialogueBlockState:
    for turn in state.turns:
        if turn.presentation_id == presentation_id:
            turn.submitted = True
    return state


def end_dialogue_block(
    vault: LoadedVault,
    repository: Repository,
    state: DialogueBlockState,
    *,
    ai_client: object | None = None,
    clock: Clock | None = None,
) -> dict[str, Any] | None:
    """Block boundary (§5.7): invalidate any unsubmitted turn presentation,
    then run the ordered block-end hook — release withheld feedback, normalize
    the block's misconceptions, evaluate the open-set trigger and the
    completion policy, and route (probe_blocks.end_diagnostic_block). The hook
    opens the boundary state segment so later evidence measures the post-block
    learner state."""

    from learnloop.services.probe_blocks import end_diagnostic_block

    episode = repository.probe_episode(state.probe_episode_id)
    if episode is None:
        return None
    for turn in state.turns:
        if turn.submitted or turn.presentation_id is None:
            continue
        presentation = repository.probe_presentation(turn.presentation_id)
        if presentation is not None and presentation.status in ("selected", "served"):
            repository.end_probe_presentation(turn.presentation_id, end_reason="invalidated", clock=clock)
    if episode.status != "in_progress":
        return None
    return end_diagnostic_block(vault, repository, episode, ai_client=ai_client, clock=clock)
