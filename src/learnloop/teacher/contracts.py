"""Public lesson contracts. The V1 wire shapes are retained for provider and receipt identity."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Annotated, Any, Literal

from pydantic import Field, ValidationInfo, model_validator

from learnloop.ai.schemas import WireModel

from .legacy_turns import (
    __all__ as _V1_EXPORTS,
    ACTIONS as ACTIONS,
    ActionRequestTE2EpisodesV1 as ActionRequestTE2EpisodesV1,
    ActionRequestTE2V1 as ActionRequestTE2V1,
    ActionRequestTE2VisualsEpisodesV1 as ActionRequestTE2VisualsEpisodesV1,
    ActionRequestTE2VisualsV1 as ActionRequestTE2VisualsV1,
    GAP_KINDS as GAP_KINDS,
    MAX_READINGS as MAX_READINGS,
    TE2_ACTIONS as TE2_ACTIONS,
    TeacherTurnTE2EpisodesV1 as TeacherTurnTE2EpisodesV1,
    TeacherTurnTE2V1 as TeacherTurnTE2V1,
    TeacherTurnTE2VisualsEpisodesV1 as TeacherTurnTE2VisualsEpisodesV1,
    TeacherTurnTE2VisualsV1 as TeacherTurnTE2VisualsV1,
    ActionRequestEpisodesV1 as ActionRequestEpisodesV1,
    ActionRequestVisualsEpisodesV1 as ActionRequestVisualsEpisodesV1,
    BRIEF_VERSION as BRIEF_VERSION,
    CLOSE_REASONS as CLOSE_REASONS,
    DETOUR_REPAIRS as DETOUR_REPAIRS,
    EPISODE_ACTIONS as EPISODE_ACTIONS,
    FORECAST_KINDS as FORECAST_KINDS,
    PlanNodeEpisodesV1 as PlanNodeEpisodesV1,
    PlanNodeVisualsEpisodesV1 as PlanNodeVisualsEpisodesV1,
    TeacherTurnEpisodesV1 as TeacherTurnEpisodesV1,
    TeacherTurnVisualsEpisodesV1 as TeacherTurnVisualsEpisodesV1,
    PROMPT_VERSION as PROMPT_VERSION,
    READ_ACTIONS as READ_ACTIONS,
    RECEIPT_VERSION as RECEIPT_VERSION,
    TEACHER_CLOSE_REASONS as TEACHER_CLOSE_REASONS,
    TURN_VERSION as TURN_VERSION,
    ActionRequestV1 as ActionRequestV1,
    ActionRequestVisualsV1 as ActionRequestVisualsV1,
    CheckV1 as CheckV1,
    CriterionV1 as CriterionV1,
    PlanNodeV1 as PlanNodeV1,
    PlanNodeVisualsV1 as PlanNodeVisualsV1,
    PlannedVisualV1 as PlannedVisualV1,
    PredictionV1 as PredictionV1,
    TeacherTurnV1 as TeacherTurnV1,
    TeacherTurnVisualsV1 as TeacherTurnVisualsV1,
    TeacherVisualV1 as TeacherVisualV1,
    VISUAL_ANCHORS as VISUAL_ANCHORS,
)


Capability = Literal["visuals", "episodes", "probes", "notebooks", "chat", "goal_topics"]
Capabilities = frozenset[Capability]


def capabilities(*, visuals: bool, episodes: bool, probes: bool) -> Capabilities:
    enabled: set[Capability] = set()
    if visuals:
        enabled.add("visuals")
    if episodes:
        enabled.add("episodes")
    if probes:
        enabled.add("probes")
    return frozenset(enabled)


def lesson_capabilities(lesson: Mapping[str, Any], turns: Sequence[Mapping[str, Any]]) -> Capabilities:
    saved = (lesson.get("goal") or {}).get("capabilities")
    if saved is not None:
        return frozenset(saved)
    # Old lessons record paragraphs on accepted turns. An interrupted open has
    # only its brief version as evidence of the available tools.
    last = next((t.get("payload") or {} for t in reversed(turns)
                 if t["action"] == "teacher_turn" and t["validation"] == "ok"), {})
    return capabilities(visuals=bool(last.get("visuals")), episodes=bool(last.get("episodes")),
                        probes=lesson.get("brief_version") == "lesson_brief_v2")


class ReadSource(ActionRequestTE2VisualsEpisodesV1):
    action: Literal["read_source"]


class FindSources(ActionRequestTE2VisualsEpisodesV1):
    action: Literal["find_sources"]


class FindPractice(ActionRequestTE2VisualsEpisodesV1):
    action: Literal["find_practice"]


class ReadHistory(ActionRequestTE2VisualsEpisodesV1):
    action: Literal["read_history"]


class ReadNote(ActionRequestTE2VisualsEpisodesV1):
    action: Literal["read_note"]


class WritePlan(ActionRequestTE2VisualsEpisodesV1):
    action: Literal["write_plan"]


class Forecast(ActionRequestTE2VisualsEpisodesV1):
    action: Literal["forecast"]


class Close(ActionRequestTE2VisualsEpisodesV1):
    action: Literal["close"]


class NoteDetour(ActionRequestTE2VisualsEpisodesV1):
    action: Literal["note_detour"]


class ServeProbe(ActionRequestTE2VisualsEpisodesV1):
    action: Literal["serve_probe"]


class ProposeGap(ActionRequestTE2VisualsEpisodesV1):
    action: Literal["propose_gap"]


class CreateGoalLo(WireModel):
    """Offer a topic for a phrase the learner wants to study."""

    action: Literal["create_goal_lo"]
    phrase: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=200)
    statement: str = Field(min_length=1, max_length=2000)
    anchors: list[str] = Field(default_factory=list, max_length=12)


Action = Annotated[
    ReadSource | FindSources | FindPractice | ReadHistory | ReadNote | WritePlan | Forecast | Close |
    NoteDetour | ServeProbe | ProposeGap | CreateGoalLo, Field(discriminator="action")
]


class TeacherTurnV2(TeacherTurnVisualsV1):
    """The execution contract shared by live turns and interrupted turns."""

    requests: list[Action] = Field(default_factory=list, max_length=8)

    @model_validator(mode="after")
    def admitted(self, info: ValidationInfo) -> "TeacherTurnV2":
        allowed: Capabilities = (info.context or {}).get("capabilities", frozenset())
        if "visuals" not in allowed and "visual" in self.model_fields_set:
            raise ValueError("visual requires visuals")
        for request in self.requests:
            if isinstance(request, CreateGoalLo):
                if "goal_topics" not in allowed:
                    raise ValueError("create_goal_lo requires goal_topics")
                continue
            fields = request.model_fields_set
            if "episodes" not in allowed and (request.action == "note_detour" or fields & {"hypothesis", "repair"}):
                raise ValueError("detour fields require episodes")
            probe_fields = fields & {"readings", "gap_kind", "gap", "ref"}
            if "probes" not in allowed and (request.action in TE2_ACTIONS or probe_fields):
                raise ValueError("probe and gap fields require probes")
            for node in request.plan:
                if "episodes" not in allowed and "p_held" in node.model_fields_set:
                    raise ValueError("p_held requires episodes")
                if "visuals" not in allowed and "visual" in node.model_fields_set:
                    raise ValueError("planned visual requires visuals")
        return self


def parse_turn(data: Mapping[str, Any], allowed: Capabilities) -> TeacherTurnV2:
    return TeacherTurnV2.model_validate(data, context={"capabilities": allowed})


__all__ = ["Capabilities", "TeacherTurnV2", "capabilities", "lesson_capabilities",
           "parse_turn"]
__all__.extend(_V1_EXPORTS)
