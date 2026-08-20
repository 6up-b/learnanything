"""Structured AI contracts owned by curriculum depth features."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from pydantic import Field

from learnloop.ai.schemas import WireModel
from learnloop.ai.transport import render_structured_prompt
from learnloop.content.proposals.ai_contracts import TaskFeaturesPayload

class RungBackfillItem(WireModel):
    """One legacy item's rung classification (candidate-only; deterministic
    validators admit or skip each entry)."""

    practice_item_id: str = ""
    capability: str = ""
    task_features: TaskFeaturesPayload | None = None


class DepthEdgeInstancePayload(WireModel):
    """One LLM-authored depth-edge instance (candidate-only; spec v2 §depth).

    Instantiates an owner-reviewed edge TEMPLATE for one commitment. Every
    instance is admitted or rejected by deterministic gates in
    ``learnloop.curriculum.depth_edge_authoring`` — model judgment never authorizes an edge.
    """

    edge_id: str = ""
    predecessor_milestone: str = ""
    successor_milestone_slug: str = ""
    # Successor task contract: capability (closed vocab) + task_features point
    # vector and/or task_feature_bounds ({dim: {target?, max?}}).
    successor_task_contract: dict = Field(default_factory=dict)
    # Observable entry/exit evidence: {"kind": one of n_of_m_success |
    # fresh_surface_pass | certified_attempt, "threshold": {...}}.
    entry_evidence: dict | None = None
    exit_evidence: dict = Field(default_factory=dict)
    # {"kind": "fresh_surface" | "reserved_family_mint", "family": ...}
    fresh_proof: dict = Field(default_factory=dict)
    expected_burden: dict = Field(default_factory=dict)
    # {"pattern_slug": ..., "purpose": ...} — must resolve to an admitted
    # activity pattern whose allowed purposes include the edge's purpose.
    activity_path: dict = Field(default_factory=dict)
    rationale: str = ""


@dataclass(frozen=True)
class RungBackfillContext:
    items: list[dict] = field(default_factory=list)
    task_feature_schema: dict = field(default_factory=dict)


@dataclass(frozen=True)
class DepthEdgeInstanceContext:
    commitment_id: str
    templates: list[dict] = field(default_factory=list)
    envelope_bounds: dict = field(default_factory=dict)
    current_milestones: list[dict] = field(default_factory=list)
    pattern_slugs: list[str] = field(default_factory=list)
    task_feature_schema: dict = field(default_factory=dict)
    count: int = 1


class RungBackfillClassification(WireModel):
    items: list[RungBackfillItem] = Field(default_factory=list)


class DepthEdgeInstanceBatch(WireModel):
    instances: list[DepthEdgeInstancePayload] = Field(default_factory=list)


RUNG_BACKFILL_PROMPT_VERSION = "mvp-0.1-rung-backfill"
DEPTH_EDGE_INSTANCE_PROMPT_VERSION = "mvp-0.1-depth-edge-instance"

RUNG_BACKFILL_PROMPT = """\
Classify each existing practice item into depth-rung metadata: the closed
capability vocabulary and a point task-feature vector. You are DESCRIBING what
each item already demands of a learner — never rewriting or judging the item.
Hard constraints:

1. `capability` is EXACTLY one of: retrieval, schema_interpretation,
procedure_execution, method_selection, coordination. Judge by what the learner
must DO: recall a fact/definition -> retrieval; read/interpret a structure,
diagram, or formalism -> schema_interpretation; carry out a known multi-step
procedure -> procedure_execution; choose between approaches -> method_selection;
integrate several capabilities across a whole task (e.g. design/build an
end-to-end workflow) -> coordination.
2. `task_features` sets every dimension: complexity 0-4; transfer
(same_context|near|far|novel_combination) — distance from the source material's
framing; response (recognize|short_constructed|long_constructed|
structured_steps|performance) — what the answer physically is; scaffolding
(none|cue|partial|worked) — support the prompt gives; span (atomic|single_step|
multi_step|whole_task) — how much is coordinated at once.
3. coordination REQUIRES span=whole_task. A "design/build the whole thing"
prompt is coordination + whole_task, not retrieval.
4. The provided float proxies (retrieval_demand/transfer_distance/
scaffold_level) are weak hints from the original authoring — prefer the prompt
text when they disagree.
5. Return one entry per provided item, echoing its practice_item_id exactly.
"""

DEPTH_EDGE_INSTANCE_PROMPT = """\
Author concrete DEPTH-EDGE INSTANCES from the reviewed edge template(s) for one
learner commitment (spec v2 depth-milestone graph). You are proposing
CANDIDATES ONLY: deterministic gates admit or reject every instance — nothing
you output authorizes anything. Hard constraints:

1. ONE EDGE PER INSTANCE: each instance names one predecessor milestone and one
strictly-deeper successor. The successor task contract must differ from the
predecessor on at least one task-feature dimension and must stay within the
template's per-dimension step deltas and the commitment envelope's bounds.
2. CLOSED VOCABULARIES: `successor_task_contract.capability` must be exactly one
of retrieval, schema_interpretation, procedure_execution, method_selection,
coordination (coordination only with span=whole_task). Task-feature values come
from the p1_launch schema dimensions provided in context.
3. OBSERVABLE EXIT EVIDENCE: `exit_evidence` names a kind from the closed set
(n_of_m_success, fresh_surface_pass, certified_attempt) with numeric thresholds
— never a vibe like "seems ready".
4. FRESH PROOF: `fresh_proof` names how mastery at the successor is proven on a
NEVER-PRACTICED surface. Never reference reserved assessment surfaces.
5. ACTIVITY PATH: `activity_path.pattern_slug` must be one of the admitted
pattern slugs listed in context.
6. Stable, descriptive `edge_id` and `successor_milestone_slug` values (snake
case); `expected_burden` estimates sessions/attempts to cross the edge.
"""


def rung_backfill_prompt(context: RungBackfillContext) -> str:
    return render_structured_prompt(
        "learnloop rung backfill",
        RUNG_BACKFILL_PROMPT_VERSION,
        {"task": RUNG_BACKFILL_PROMPT, "context": asdict(context)},
    )


def depth_edge_instance_prompt(context: DepthEdgeInstanceContext) -> str:
    return render_structured_prompt(
        "learnloop depth edge instances",
        DEPTH_EDGE_INSTANCE_PROMPT_VERSION,
        {"task": DEPTH_EDGE_INSTANCE_PROMPT, "context": asdict(context)},
    )
