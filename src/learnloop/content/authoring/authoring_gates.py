"""One instrument-quality gate chain for every practice-item authoring lane.

Stage 5.3 wired the planted-persona gate (Meas §3.0) and Stage 6 added the
selected-response ban and the contrast-pair gate (Meas §3.A4) — but only onto
``practice_generation``'s four routes, because that module owned the
``row_transform`` seam. The ingest lanes (``source_set_synthesis``,
``source_append``, ``source_ingestion``) persist proposal rows directly and
never passed through the seam, so a practice item authored at ingest reached
the review queue (or, on the canonical lane, auto-apply) with no instrument
gate at all. The §8.7 synthesis gates do not cover this: they check
provenance, scope and structure; these check whether the item measures
anything. The two families are disjoint by design and both must run.

This module is the single composition both lanes consume, so they cannot
drift. Every gate here follows the ``row_transform`` protocol: a callable
over the full list of proposal rows that mutates row routing in place
(``validation_status`` / ``validation_errors`` / ``_auto_apply`` / ``audit``)
and never raises on a bad item — refusing a row is a verdict, not an error.
Fail-closed in the ``_RungGate`` sense still holds: an *exception* aborts
persistence rather than silently admitting the batch.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Sequence

from learnloop.content.authoring.ai_contracts import (
    BANNED_RESPONSE_MODES,
    LOW_MASTERY_RESPONSE_MODES,
)
from learnloop.diagnosis.contrast_pairs import ContrastPairGate
from learnloop.content.authoring.persona_gate import (
    GateDecision,
    PersonaGate,
    _keyed_misconception_ids,
)

RowGate = Callable[[list[dict[str, Any]]], None]

# The prompt ladder and the gate share the feature-owned authoring prompt
# vocabulary in ``learnloop.content.proposals.ai_contracts``; a
# recommended mode that the gate bans is the drift this module exists to prevent.
assert not set(BANNED_RESPONSE_MODES) & set(
    LOW_MASTERY_RESPONSE_MODES
), "prompt ladder recommends a banned response mode"

#: Deterministic textual signatures of a selected-response surface. Moved
#: verbatim from ``practice_generation`` (Stage 6); see
#: :class:`SelectedResponseGate` for why a prompt rule alone does not hold.
SELECTED_RESPONSE_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\breply with the letter\b", "asks the learner to reply with a letter"),
    (r"\bselect the (?:correct|right)\b", "asks the learner to select an option"),
    (r"\bwhich of the following\b", "poses a which-of-the-following option list"),
    (r"\bchoose the (?:correct|right|best)\b", "asks the learner to choose an option"),
    (r"\btrue or false\b", "is a true/false item"),
    # Two or more lettered options: "A. ... B. ..." / "A) ... B) ...".
    (r"(?:(?<=\s)|^)[A-D][.)]\s+\S.*?(?:(?<=\s)|^)[B-E][.)]\s+\S", "lists lettered answer options"),
)


def selected_response_reasons(payload: dict[str, Any]) -> list[str]:
    """Every reason this payload reads as a selected-response surface.

    Pure so the gate, the edit/refresh validation door, and the remediation
    re-check all judge with the same function. Two channels: the prompt-text
    patterns, and the declared ``practice_mode`` — a banned mode is a violation
    even when the option list lives outside ``prompt`` (a stimulus block, an
    attachment), because the declaration is the item saying what it is.
    """

    prompt = str(payload.get("prompt") or "")
    reasons = [
        reason
        for pattern, reason in SELECTED_RESPONSE_PATTERNS
        if re.search(pattern, prompt, flags=re.IGNORECASE | re.DOTALL)
    ]
    mode = str(payload.get("practice_mode") or "").strip().lower()
    if mode in BANNED_RESPONSE_MODES:
        reasons.append(f"declares selected-response practice_mode `{mode}`")
    return reasons


class SelectedResponseGate:
    """Deterministic ban on selected-response surfaces (multiple choice / T-F).

    A prompt rule alone does not hold: the authoring model reliably falls back
    to option lists when asked for an easy item. Selected-response items
    measure option elimination rather than the capability the Learning Object
    names, and they are near-worthless as evidence, so an item that ships one
    is forced off the auto-apply route and marked invalid for review.
    """

    def __init__(self) -> None:
        self.violations: list[str] = []

    def __call__(self, rows: list[dict[str, Any]]) -> None:
        for row in rows:
            if row.get("item_type") != "practice_item" or row.get("operation") != "create":
                continue
            payload = row.get("payload")
            if not isinstance(payload, dict):
                continue
            reasons = selected_response_reasons(payload)
            if not reasons:
                continue
            ref = str(row.get("client_item_id") or payload.get("id") or "item")
            message = f"{ref}: selected-response surface ({'; '.join(reasons)})"
            self.violations.append(message)
            row["_auto_apply"] = False
            row["validation_status"] = "invalid"
            errors = list(row.get("validation_errors") or [])
            row["validation_errors"] = ["selected_response_surface", *errors]


def chain_gates(*gates: RowGate) -> RowGate:
    """Run several row_transform gates over one proposal batch, in order."""

    def _run(rows: list[dict[str, Any]]) -> None:
        for gate in gates:
            gate(rows)

    return _run


# ---------------------------------------------------------------------------
# Deterministic gate remediation — information-removing repairs only
# ---------------------------------------------------------------------------
#
# The one-shot model repair pass runs BEFORE the row_transform seam, so a gate
# failure is discovered after the model's chance to fix it has passed. The two
# failure classes below need no model: both repairs strictly REMOVE content
# (an option list; a speculative diagnostic claim), so applying them
# deterministically cannot fabricate anything. A remediated row is mechanically
# altered content and therefore NEVER auto-applies and never reads better than
# ``warning`` — a reviewer sees exactly what was removed via the audit entry.

GATE_REMEDIATION_AUDIT_KEY = "instrument_gate_remediation"

#: Error strings (as the gates write them) that remediation can cure.
_REMEDIABLE_SURFACE_ERROR = "selected_response_surface"
_REMEDIABLE_DETECTOR_ERROR = "persona_gate: no_keyed_detector"
#: proposals-side deterministic validation twin of the detector failure.
_REMEDIABLE_ATOMIC_ERROR = "misconception_answer_requires_keyed_fatal_error"

_OPTION_LINE = re.compile(r"^\s*[A-E][.)]\s+\S.*$", flags=re.MULTILINE)
_OPTION_ANSWER_PREFIX = re.compile(r"^\s*[A-E][.)]\s*")
_INSTRUCTION_LINE_PATTERNS = tuple(pattern for pattern, _ in SELECTED_RESPONSE_PATTERNS)


def _strip_selected_response_surface(payload: dict[str, Any]) -> list[str] | None:
    """Remove the selected-response surface from ``payload`` in place.

    Returns the list of actions taken, or ``None`` when the surface cannot be
    removed mechanically (e.g. a true/false framing inside the question stem
    itself) — in which case the payload is left byte-identical.
    """

    original = {
        "prompt": payload.get("prompt"),
        "expected_answer": payload.get("expected_answer"),
        "practice_mode": payload.get("practice_mode"),
        "task_features": dict(payload["task_features"])
        if isinstance(payload.get("task_features"), dict)
        else payload.get("task_features"),
    }
    actions: list[str] = []
    prompt = str(payload.get("prompt") or "")
    stripped = _OPTION_LINE.sub("", prompt)
    removed_options = stripped != prompt
    if removed_options:
        actions.append("removed lettered answer options from prompt")
    lines = []
    for line in stripped.splitlines():
        if any(
            re.search(pattern, line, flags=re.IGNORECASE) for pattern in _INSTRUCTION_LINE_PATTERNS
        ):
            # Dropping a whole line is safe only for instruction lines; a stem
            # that embeds the pattern makes remediation fail below instead.
            actions.append("removed selected-response instruction line")
            continue
        if removed_options and re.search(r"\b(options?|letters?)\b", line, flags=re.IGNORECASE):
            # Once the option list is gone, a line telling the learner what to
            # do with "the options" is a dangling reference, not a task.
            actions.append("removed option-referencing instruction line")
            continue
        lines.append(line)
    candidate_prompt = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()

    candidate = dict(payload)
    candidate["prompt"] = candidate_prompt
    mode = str(payload.get("practice_mode") or "").strip().lower()
    if mode in BANNED_RESPONSE_MODES:
        candidate["practice_mode"] = "short_answer"
        actions.append(f"practice_mode {mode} -> short_answer")
    task_features = candidate.get("task_features")
    if isinstance(task_features, dict) and task_features.get("response") == "recognize":
        task_features = dict(task_features)
        task_features["response"] = "short_constructed"
        candidate["task_features"] = task_features
        actions.append("task_features.response recognize -> short_constructed")

    # Post-conditions: the surface must actually be gone, and enough of a task
    # must remain for the item to still ask something.
    if not candidate_prompt or selected_response_reasons(candidate):
        return None

    payload.update(candidate)
    expected = str(payload.get("expected_answer") or "")
    unlettered = _OPTION_ANSWER_PREFIX.sub("", expected, count=1)
    if unlettered != expected:
        payload["expected_answer"] = unlettered
        actions.append("removed option letter from expected_answer")
    return actions


def _drop_unkeyed_misconception(payload: dict[str, Any]) -> list[str] | None:
    """Drop a speculative diagnostic claim, demoting the item to plain practice.

    Applies only when ``misconception_consistent_answer`` is populated with NO
    fatal error keyed to a canonical misconception — the exact
    ``no_keyed_detector`` shape. An item whose fatal errors DO key a
    misconception is a real diagnostic and is not touched.
    """

    declared = str(payload.get("misconception_consistent_answer") or "").strip()
    if not declared or _keyed_misconception_ids(payload):
        return None
    payload["misconception_consistent_answer"] = None
    return [
        "dropped misconception_consistent_answer (no registered misconception is "
        "keyed by a rubric fatal error); item demoted to ordinary practice"
    ]


def remediate_instrument_gate_failures(
    rows: list[dict[str, Any]], *, persona_gate: PersonaGate
) -> None:
    """Mechanically repair the two remediable gate failures, then re-judge.

    A cured error string is removed; a row whose remaining errors are empty
    becomes ``warning`` (mechanically altered content ships to review, never
    auto-applies, never reads ``valid``). Rows the repair cannot clean keep
    today's behavior byte-for-byte.
    """

    for row in rows:
        if row.get("item_type") != "practice_item" or row.get("operation") != "create":
            continue
        payload = row.get("payload")
        if not isinstance(payload, dict):
            continue
        errors = [str(error) for error in (row.get("validation_errors") or [])]
        wants_surface = _REMEDIABLE_SURFACE_ERROR in errors
        wants_detector = _REMEDIABLE_DETECTOR_ERROR in errors or _REMEDIABLE_ATOMIC_ERROR in errors
        if not wants_surface and not wants_detector:
            continue
        actions: list[str] = []
        cured: set[str] = set()
        pre_remediation = {
            key: payload.get(key)
            for key in ("prompt", "expected_answer", "practice_mode", "misconception_consistent_answer")
        }
        if wants_detector:
            dropped = _drop_unkeyed_misconception(payload)
            if dropped is not None:
                actions.extend(dropped)
                cured.update({_REMEDIABLE_DETECTOR_ERROR, _REMEDIABLE_ATOMIC_ERROR})
        if wants_surface:
            stripped = _strip_selected_response_surface(payload)
            if stripped is not None:
                actions.extend(stripped)
                cured.add(_REMEDIABLE_SURFACE_ERROR)
        if not actions:
            continue
        # Re-judge the repaired payload with the same authorities that failed it.
        if _REMEDIABLE_SURFACE_ERROR in cured and selected_response_reasons(payload):
            cured.discard(_REMEDIABLE_SURFACE_ERROR)
        if cured & {_REMEDIABLE_DETECTOR_ERROR, _REMEDIABLE_ATOMIC_ERROR}:
            outcome = persona_gate.judge(payload, client_item_id=str(row.get("client_item_id") or "item"))
            if outcome.decision is GateDecision.BLOCK:
                cured.discard(_REMEDIABLE_DETECTOR_ERROR)
                cured.discard(_REMEDIABLE_ATOMIC_ERROR)
            else:
                audit = row.get("audit")
                audit = dict(audit) if isinstance(audit, dict) else {}
                audit["persona_gate"] = outcome.as_dict()
                row["audit"] = audit
        remaining = [error for error in errors if error not in cured]
        if remaining == errors:
            continue
        row["validation_errors"] = remaining
        row["validation_status"] = "invalid" if remaining else "warning"
        row["_auto_apply"] = False
        audit = row.get("audit")
        audit = dict(audit) if isinstance(audit, dict) else {}
        audit[GATE_REMEDIATION_AUDIT_KEY] = {
            "actions": actions,
            "cured_errors": sorted(cured),
            "pre_remediation": pre_remediation,
            "note": (
                "deterministic, information-removing repair; criterion descriptions "
                "may still reference removed options — review before accepting"
            ),
        }
        row["audit"] = audit


@dataclass
class InstrumentGateChain:
    """The composed Stage-5.3/6 instrument gates, with named handles.

    Callers read the member gates for reporting (``persona_gate.blocked``,
    ``surface_gate.violations``, …) exactly as they did when each route built
    the tuple by hand.
    """

    surface_gate: SelectedResponseGate
    persona_gate: PersonaGate
    pair_gate: ContrastPairGate
    rung_gate: Any | None = None
    gates: tuple[RowGate, ...] = field(default_factory=tuple)

    def __call__(self, rows: list[dict[str, Any]]) -> None:
        for gate in self.gates:
            gate(rows)
        # After the verdicts: mechanically repair the two remediable failure
        # classes and re-judge. Runs inside the chain so every lane that
        # consumes the composition gets remediation without caller changes;
        # the pre-remediation verdicts stay visible in `diagnostics()` and in
        # the row's remediation audit entry.
        remediate_instrument_gate_failures(rows, persona_gate=self.persona_gate)

    def diagnostics(self) -> list[dict[str, Any]]:
        """Gate outcomes in the synthesis lanes' ``gate_diagnostics`` shape.

        The generation lanes read the member gates directly; the synthesis
        lanes persist one diagnostics list into ``coverage_decisions``, so the
        instrument verdicts must land there too or a refused ingest-authored
        item would be indistinguishable from one nobody judged.
        """

        out: list[dict[str, Any]] = []
        for message in self.surface_gate.violations:
            out.append(
                {
                    "gate": "selected_response_surface",
                    "severity": "hard_fail",
                    "entity_refs": [message.split(":", 1)[0]],
                    "message": message,
                    "suggested_action": "author a constructed-response surface",
                }
            )
        for outcome in self.persona_gate.blocked:
            out.append(
                {
                    "gate": "persona_gate",
                    "severity": "hard_fail",
                    "entity_refs": [outcome.client_item_id],
                    "message": (
                        f"{outcome.client_item_id}: persona gate blocked a "
                        f"{outcome.instrument_class} ({outcome.reason})"
                    ),
                    "suggested_action": "author an instrument whose personas separate",
                }
            )
        for outcome in self.persona_gate.flagged:
            out.append(
                {
                    "gate": "persona_gate",
                    "severity": "review",
                    "entity_refs": [outcome.client_item_id],
                    "message": (
                        f"{outcome.client_item_id}: persona gate flagged a "
                        f"{outcome.instrument_class} ({outcome.reason})"
                    ),
                    "suggested_action": "review before accepting",
                }
            )
        for message in self.pair_gate.violations:
            out.append(
                {
                    "gate": "contrast_pair_gate",
                    "severity": "hard_fail",
                    "entity_refs": [message.split(":", 1)[0]],
                    "message": message,
                    "suggested_action": "author both members of a genuine contrast pair",
                }
            )
        return out


def build_instrument_gates(
    vault: Any,
    repository: Any | None = None,
    *,
    grading_client: Any = None,
    rung_gate: Any | None = None,
    difficulty_band_by_lo: dict[str, tuple[float, float]] | None = None,
    leading: Sequence[RowGate] = (),
) -> InstrumentGateChain:
    """The standard composition: leading → surface → rung → persona → pair.

    This is the order every ``practice_generation`` route already used; the
    factory exists so the ingest lanes get the same one instead of a private
    subset. ``rung_gate`` stays caller-constructed because it is a statement
    about a specific expansion plan; lanes without a plan pass ``None`` and
    get no rung admission, exactly as the diagnostic route always has.

    ``grading_client=None`` is legal everywhere: ``PersonaGate`` falls back to
    its deterministic in-memory rule, and candidate revalidation legitimately
    has no client. UNTESTED remains the persona gate's honest abstention arm
    where persona material is absent — common on a first ingest — so wiring
    the chain into ingest cannot block authoring on missing material.
    """

    surface_gate = SelectedResponseGate()
    persona_gate = PersonaGate(vault, repository, grading_client=grading_client)
    pair_gate = (
        ContrastPairGate(vault, difficulty_band_by_lo=difficulty_band_by_lo)
        if difficulty_band_by_lo is not None
        else ContrastPairGate(vault)
    )
    gates: list[RowGate] = [*leading, surface_gate]
    if rung_gate is not None:
        gates.append(rung_gate)
    gates.extend((persona_gate, pair_gate))
    return InstrumentGateChain(
        surface_gate=surface_gate,
        persona_gate=persona_gate,
        pair_gate=pair_gate,
        rung_gate=rung_gate,
        gates=tuple(gates),
    )
