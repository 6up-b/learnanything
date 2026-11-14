"""The kill-switch table (``learnloop.kill_switches``) against the code: it matches the schema, a switch the code
names is in it, and ADR-019's rule about the version floor has its ratchet.
"""

from __future__ import annotations

import ast
import re
from collections.abc import Iterator
from pathlib import Path

from pydantic import BaseModel

import learnloop.config.schema as schema_module
from learnloop.algorithm_versions import OLDEST_SUPPORTED, SUCCESSOR_CHAIN
from learnloop.config.schema import LearnLoopConfig
from learnloop.kill_switches import TAGGED_SWITCHES, UNTAGGED_SWITCHES

SRC = Path(__file__).resolve().parents[1] / "src" / "learnloop"
TABLED = {switch.path for switch in TAGGED_SWITCHES + UNTAGGED_SWITCHES}

#: Fields the code names near the word "switch" or in a tag's comment that the table leaves out on purpose, each with
#: the reason. A field here that no longer resolves, or that is in the table, fails the test below.
NOT_A_TABLED_SWITCH = {
    "data_capture.receipts": "additive logging at every version; no predecessor behaviour to restore",
    "router.log_decisions": "decision logging runs at every version; not a serving change",
    "teach_back.transfer_evidence_multiplier": "a weight a tag's comment mentions, not a switch",
    "reading_paths.enabled": "the Guide's own feature switch; the tagged switch is reading_paths.plan_uses_path",
    "hints.chooser_enabled": "the hint service's own feature toggles, listed beside its kill switch (adaptive_enabled)",
    "hints.choice_policy": "listed beside the hint service's kill switch; a selection, not a switch",
    "hints.chooser_timeout_seconds": "listed beside the hint service's kill switch; a time limit",
    "hints.help_style": "listed beside the hint service's kill switch; a display preference",
    "hints.max_daily_cost_usd": "listed beside the hint service's kill switch; a cost cap",
}

#: ADR-019's kept-because list, as it stands when the table landed: every switch whose tag is at or below the floor is
#: still in the code, so each is here. A removal batch of D7 deletes a switch's field, its table row and its line here
#: in one commit; a line left behind fails ``test_the_kept_because_list_names_only_live_switches_at_or_below_the_floor``.
#: A switch that stays after D7 keeps its line with the reason it stays, and the list is the short one the rule asks for.
_STANDING_WHEN_THE_TABLE_LANDED = (
    "diagnosis.split_enabled",
    "diagnosis.shadow",
    "stuck_prompt.enabled",
    "proof_check.enabled",
    "required_method.enabled",
    "hints.fold_follows_attach",
    "mastery.claim_fixes_enabled",
    "replay.ledger_bounded",
    "practice.attempt_keeps_content_state",
    "ask.cold_help_converts",
    "practice.reschedule_cold_after_assist",
    "eligibility.enabled",
    "placement.enabled",
    "placement.initial_probes",
    "placement.unevidenced_return",
    "recurrence.enabled",
    "learner_text_gaps.sooner_check_enabled",
    "source_service.source_first_needs",
    "voi_stopping.enabled",
    "voi_stopping.probe_episodes",
    "voi_stopping.followups",
    "voi_stopping.teach_back",
    "voi_stopping.project_probes",
    "voi_stopping.robust_gate_with_value",
    "diagnosis.probe_lane_reads_diagnosis",
    "diagnosis.probe_lane_pending",
    "learner_text_gaps.decider_enabled",
    "decider_routes.learner_gap_judge",
    "decider_routes.learner_gap_kind",
    "decider_routes.misconception_match",
    "decider_routes.diagnosis_link_judgment",
    "decider_routes.field_question_classification",
    "decider_routes.contamination_leak_judgment",
    "decider_routes.contamination_reveal_judgment",
    "plan.enabled",
    "plan.new_admission_enabled",
    "plan.reading_blocks",
    "router.probe_tie_admission",
    "router.enabled",
    "router.mode",
    "router.restraint",
    "router.lesson_suggestions.enabled",
    "router.lesson_suggestions.in_objective",
    "reading_paths.plan_uses_path",
    "curriculum.plan_uses_path",
    "curriculum.enabled",
    "followups.enabled",
    "intent.enabled",
    "intent.recall_targets_enabled",
    "data_capture.serving",
    "followup.generate_and_serve",
    "workbench.field_signals_enabled",
    "teacher.enabled",
    "teacher.weight.learned",
    "teacher.weight.source",
    "teacher.probes",
    "adaptive_difficulty.enabled",
    "adaptive_difficulty.selection",
    "adaptive_difficulty.generation_contract",
    "adaptive_difficulty.promoted_predictor",
    "adaptive_difficulty.learned_coupling",
    "adaptive_difficulty.reading_opportunities",
    "adaptive_difficulty.reading_self_check",
    "adaptive_difficulty.lesson_opportunities",
    "scheduler.surprise.remove_interval_factor",
    "router_objective.available_at_reads",
    "router_objective.self_report_not_validated",
    "router_objective.enabled",
    "router_objective.sensors_in_value",
    "router_objective.stop_coin",
    "router_objective.check_rate",
    "router_objective.pick_open_share",
    "router_objective.fitted_models",
    "router_objective.learned_tail",
    "router_objective.combiner_trace_outcomes",
    "router_objective.merged_sessions",
    "router_objective.consistent_review_draw",
    "router_objective.monotone_combiner",
    "router_objective.ad_predictive_link",
    "router_objective.carried_in_prefetch",
    "router_objective.scope_extension",
    "router_objective.held_ad_link",
    "router_objective.held_reading_map",
    "router_objective.pooled_connections",
    "router_objective.failure_share_to_other_policy",
    "router_objective.lessons_compete_with_followups",
    "router_objective.learner_preferences",
    "router_objective.workbench_is_open_item",
    "router_objective.lesson_sources_follow_diagnosis",
    "router_objective.lesson_candidate_after_cold_miss",
    "router_objective.preferences_inform_router",
    "router_objective.miss_cause_sensor",
    "router_objective.miss_cause_in_value",
    "figures.prefetch.pressed_waits",
)
KEPT_BECAUSE_AT_OR_BELOW_THE_FLOOR: dict[str, str] = dict.fromkeys(
    _STANDING_WHEN_THE_TABLE_LANDED, "present when the table landed; D7's removal batches shrink this list")


def _leaves(model: type[BaseModel], prefix: str = "") -> Iterator[str]:
    for name, field in model.model_fields.items():
        annotation = field.annotation
        if isinstance(annotation, type) and issubclass(annotation, BaseModel):
            yield from _leaves(annotation, f"{prefix}{name}.")
        else:
            yield f"{prefix}{name}"


def _sections(model: type[BaseModel], prefix: str = "") -> Iterator[tuple[str, type[BaseModel]]]:
    for name, field in model.model_fields.items():
        annotation = field.annotation
        if isinstance(annotation, type) and issubclass(annotation, BaseModel):
            yield f"{prefix}{name}", annotation
            yield from _sections(annotation, f"{prefix}{name}.")


LEAVES = frozenset(_leaves(LearnLoopConfig))


def _default(path: str):
    node = LearnLoopConfig()
    for part in path.split("."):
        node = getattr(node, part)
    return node


# --- the table against the schema -----------------------------------------------------------------------------


def test_every_row_resolves_in_the_schema_with_the_schemas_default() -> None:
    for switch in TAGGED_SWITCHES + UNTAGGED_SWITCHES:
        assert switch.path in LEAVES, f"{switch.path} is not a leaf of LearnLoopConfig"
        value = _default(switch.path)
        assert value == switch.default and isinstance(value, bool) == isinstance(switch.default, bool), (
            f"{switch.path}: the schema's default is {value!r}, the table says {switch.default!r}")


def test_each_path_is_in_the_table_once_and_each_tag_is_a_real_one() -> None:
    paths = [switch.path for switch in TAGGED_SWITCHES + UNTAGGED_SWITCHES]
    assert len(paths) == len(set(paths))
    assert all(switch.tag in SUCCESSOR_CHAIN for switch in TAGGED_SWITCHES)
    assert all(switch.tag is None for switch in UNTAGGED_SWITCHES)


# --- a switch the code names but the table lacks ---------------------------------------------------------------

_DOTTED = re.compile(r"``([a-z_][a-z_0-9]*(?:\.[a-z_][a-z_0-9]*)+)``")
_VERSION_NAME = re.compile(r"mvp-0\.\d+|[A-Z_]+_VERSIONS?\b")
_KILL_SWITCH = re.compile(r"kill[- ]switch", re.IGNORECASE)


def _config_paths_named_in(text: str) -> set[str]:
    """Every double-backticked dotted name in ``text`` that is a config leaf."""

    return {match.group(1) for match in _DOTTED.finditer(text)} & LEAVES


def _fields_named_as_kill_switches(source: str, owners: dict[str, list[str]]) -> set[str]:
    """Config paths whose schema text calls them a kill switch beside a version name.

    A field counts when its own leading comment or definition says "kill switch" and names a tag (``mvp-0.N``) or a
    ``*_VERSION(S)`` constant, or when its class docstring has a sentence naming ``field`` and "kill switch" and the
    docstring names one. ``owners`` maps a class name to the config prefixes it appears under ('' for the root)."""

    lines = source.split("\n")
    found: set[str] = set()
    for node in ast.parse(source).body:
        if not isinstance(node, ast.ClassDef) or node.name not in owners:
            continue
        doc = ast.get_docstring(node) or ""
        sentences = re.split(r"(?<=[.;:])\s+|\n\n", doc)
        for stmt in node.body:
            if not (isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)):
                continue
            name = stmt.target.id
            comment: list[str] = []
            row = stmt.lineno - 2
            while row >= 0 and lines[row].strip().startswith("#"):
                comment.append(lines[row])
                row -= 1
            own = " ".join(comment) + " " + "\n".join(lines[stmt.lineno - 1:stmt.end_lineno])
            named = bool(_KILL_SWITCH.search(own) and _VERSION_NAME.search(own)) or any(
                f"``{name}``" in sentence and _KILL_SWITCH.search(sentence) and _VERSION_NAME.search(doc)
                for sentence in sentences)
            if named:
                found.update(f"{prefix}{name}" for prefix in owners[node.name])
    return found


def _owners() -> dict[str, list[str]]:
    owners: dict[str, list[str]] = {"LearnLoopConfig": [""]}
    for path, model in _sections(LearnLoopConfig):
        owners.setdefault(model.__name__, []).append(f"{path}.")
    return owners


def test_every_switch_the_schema_or_a_tags_comment_names_is_in_the_table() -> None:
    named = _fields_named_as_kill_switches(Path(schema_module.__file__).read_text(encoding="utf-8"), _owners())
    for module in ("algorithm_versions.py", "router_objective_switches.py"):
        named |= _config_paths_named_in((SRC / module).read_text(encoding="utf-8"))
    missing = sorted(named - TABLED - set(NOT_A_TABLED_SWITCH))
    assert not missing, (
        f"{missing} named as kill switches (or in a tag's comment) but not in learnloop.kill_switches: add each to "
        "TAGGED_SWITCHES (it has a successor tag) or UNTAGGED_SWITCHES, or to NOT_A_TABLED_SWITCH with the reason")


#: Sections whose every boolean and mode is a switch that restores a predecessor (checked when the table landed). A new
#: boolean here is a new switch, whatever its comment says.
SECTIONS_OF_SWITCHES = ("router_objective", "decider_routes", "voi_stopping", "teacher", "teacher.weight",
                        "router.lesson_suggestions", "placement", "intent")


def test_every_boolean_and_mode_of_a_section_of_switches_is_in_the_table() -> None:
    missing = sorted(path for path in LEAVES
                     if path.rsplit(".", 1)[0] in SECTIONS_OF_SWITCHES
                     and isinstance(_default(path), (bool, str))
                     and path not in TABLED and path not in NOT_A_TABLED_SWITCH)
    assert not missing, f"{missing}: new booleans or modes in a section of switches; add each to the table"


def test_the_exemptions_are_live() -> None:
    for path in NOT_A_TABLED_SWITCH:
        assert path in LEAVES, f"{path} no longer exists: drop it from NOT_A_TABLED_SWITCH"
        assert path not in TABLED, f"{path} is in the table now: drop it from NOT_A_TABLED_SWITCH"


def test_the_guard_finds_a_switch_the_table_lacks() -> None:
    source = '''
class DemoConfig(BaseModel):
    """The demo.

    ``fresh`` is the kill switch of ``DEMO_ALGORITHM_VERSION``: off restores the predecessor. ``other`` is a cap.
    """

    fresh: bool = True
    other: int = 3
    # The kill switch of mvp-0.99: off restores it.
    own_comment: bool = True
    quiet: bool = True
'''
    assert _fields_named_as_kill_switches(source, {"DemoConfig": ["demo."]}) == {"demo.fresh", "demo.own_comment"}
    assert _config_paths_named_in("Kill switch ``router.restraint``, not ``made.up`` or ``router``.") == {
        "router.restraint"}


# --- ADR-019: the floor ----------------------------------------------------------------------------------------


def _at_or_below_the_floor(tag: str | None) -> bool:
    return tag is not None and tag in SUCCESSOR_CHAIN and (
        SUCCESSOR_CHAIN.index(tag) <= SUCCESSOR_CHAIN.index(OLDEST_SUPPORTED))


def test_a_switch_at_or_below_the_floor_is_gone_or_on_the_kept_because_list() -> None:
    standing = {switch.path for switch in TAGGED_SWITCHES
                if _at_or_below_the_floor(switch.tag) and switch.path in LEAVES}
    assert not standing - set(KEPT_BECAUSE_AT_OR_BELOW_THE_FLOOR), (
        "a switch whose tag the floor has passed stands in the schema: remove it with its gates, or put it on the "
        f"kept-because list with the reason: {sorted(standing - set(KEPT_BECAUSE_AT_OR_BELOW_THE_FLOOR))}")


def test_the_kept_because_list_names_only_live_switches_at_or_below_the_floor() -> None:
    by_path = {switch.path: switch for switch in TAGGED_SWITCHES}
    for path, reason in KEPT_BECAUSE_AT_OR_BELOW_THE_FLOOR.items():
        assert reason
        assert path in by_path, f"{path} is not a tagged switch: drop the line"
        assert _at_or_below_the_floor(by_path[path].tag), f"{path} is above the floor: it needs no reason"
        assert path in LEAVES, f"{path} is gone from the schema: drop the line"
