"""Stable mechanism taxonomy and the single legacy → canonical error-type map.

Knowledge-model spec §10.1 defines a nine-value *mechanism* taxonomy that routes
repair and diagnosis. It is a **grader contract**: the grader emits these values
under ``mvp-0.7`` (``GRADING_PROMPT_VERSION`` is bumped with it); legacy vaults
keep the old vocabulary and replay frozen. ``map_legacy_error_type`` is the ONE
place that resolves any legacy error-type name (the §10.1 legacy names, the
actual mvp-0.6 grader vocabulary, and the config ``[error_impacts]`` keys) onto
the canonical nine, so consumers can reason in a single space. It is the identity
on the canonical values and a pass-through for unknown vault-specific ids.

§10.1 legacy mapping (verbatim):
  recall_failure          -> retrieval_failure
  conceptual_error        -> conceptual_schema_error
  procedure_error         -> procedure_execution_error
  notation_error          -> representation_notation_error
  assumption_error        -> condition_assumption_error
  theorem_selection_error -> selection_planning_error
  transfer_failure        -> transfer_context_error

Reviewed decisions for the two legacy names §10.1 leaves open (they are consumed
in config ``[error_impacts]`` / the deterministic don't-know path):

* ``arithmetic_slip -> local_slip`` — the new taxonomy renames the "local slip"
  mechanism; arithmetic_slip is exactly a local, non-conceptual execution error
  (config: severity 0.15, ``families = {numeric}``, ``is_misconception`` False).
  A direct 1:1.
* ``scaffold_failure -> retrieval_failure`` — scaffold_failure is "could not
  reconstruct after hints": mechanistically a retrieval lapse (seed tags
  ``[recall, scaffold]``, ``families = {recall}``, ``is_misconception`` False),
  differing from recall_failure only in *severity* (failed despite support). The
  mechanism taxonomy routes repair/diagnosis and both route to
  retrieval/spacing; the severity distinction is preserved by the severity
  machinery (``local_severity_gain``, the hinted-don't-know severity example),
  not by the mechanism label. Conservative: it never upgrades a support-assisted
  failure into a conceptual/procedural belief error, and it invents no scaffold
  mechanism absent from the nine.

The mvp-0.6 grader vocabulary (``conceptual_slip``, ``procedure_misapplication``,
``incomplete_answer``) is a set of synonyms for the §10.1 legacy names; each maps
to the same canonical mechanism so a taxonomy regrade-check comparing mechanisms
across a prompt-version bump shows no attribution regression.
"""

from __future__ import annotations

# --- The stable mechanism taxonomy (§10.1) --------------------------------------

MECHANISM_TAXONOMY: tuple[str, ...] = (
    "retrieval_failure",
    "conceptual_schema_error",
    "procedure_execution_error",
    "selection_planning_error",
    "condition_assumption_error",
    "representation_notation_error",
    "transfer_context_error",
    "local_slip",
    "assessment_ambiguity",
)

MECHANISM_TAXONOMY_SET: frozenset[str] = frozenset(MECHANISM_TAXONOMY)

# Assessment-side causes: the fault lies with the item or the grading, not the
# learner. These must never feed learner-repair signals (the scheduler's
# recent-error boost, repair targeting) — they belong to the item-quality /
# bad-item-suspicion path.
ASSESSMENT_SIDE_ERROR_TYPES: frozenset[str] = frozenset({"assessment_ambiguity"})

# Mechanism-level ``is_misconception`` defaults (a durable wrong belief vs a slip
# / retrieval lapse / item-or-grader issue). Used for severity fallbacks and the
# signature matcher's misconception fatal set under mvp-0.7.
MECHANISM_IS_MISCONCEPTION: dict[str, bool] = {
    "retrieval_failure": False,
    "conceptual_schema_error": True,
    "procedure_execution_error": True,
    "selection_planning_error": True,
    "condition_assumption_error": True,
    "representation_notation_error": True,
    "transfer_context_error": True,
    "local_slip": False,
    "assessment_ambiguity": False,
}

# Mechanism-level severity defaults (parallel to the legacy seed severities).
MECHANISM_SEVERITY_DEFAULT: dict[str, float] = {
    "retrieval_failure": 0.4,
    "conceptual_schema_error": 0.7,
    "procedure_execution_error": 0.65,
    "selection_planning_error": 0.65,
    "condition_assumption_error": 0.6,
    "representation_notation_error": 0.5,
    "transfer_context_error": 0.6,
    "local_slip": 0.15,
    "assessment_ambiguity": 0.2,
}

# --- The single legacy → canonical map (§10.1 + reviewed decisions) --------------

LEGACY_ERROR_TYPE_MAP: dict[str, str] = {
    # §10.1 verbatim.
    "recall_failure": "retrieval_failure",
    "conceptual_error": "conceptual_schema_error",
    "procedure_error": "procedure_execution_error",
    "notation_error": "representation_notation_error",
    "assumption_error": "condition_assumption_error",
    "theorem_selection_error": "selection_planning_error",
    "transfer_failure": "transfer_context_error",
    # Reviewed decisions (see module docstring).
    "arithmetic_slip": "local_slip",
    "scaffold_failure": "retrieval_failure",
    # mvp-0.6 grader vocabulary synonyms.
    "conceptual_slip": "conceptual_schema_error",
    "procedure_misapplication": "procedure_execution_error",
    "incomplete_answer": "local_slip",
}


def map_legacy_error_type(error_type: str | None) -> str | None:
    """Resolve any legacy error-type name onto the canonical mechanism space.

    Identity on the nine canonical values; the §10.1 map (plus the reviewed
    ``arithmetic_slip``/``scaffold_failure`` decisions and grader synonyms) for
    legacy names; pass-through for unknown vault-specific ids (they are still
    valid rubric fatal ids / vault taxonomy entries). ``None`` in, ``None`` out.
    """

    if error_type is None:
        return None
    if error_type in MECHANISM_TAXONOMY_SET:
        return error_type
    return LEGACY_ERROR_TYPE_MAP.get(error_type, error_type)


# --- Canonical grader taxonomy card (the mvp-0.7 grading contract) ---------------
# Mirrors services.grading.CANONICAL_ERROR_TYPES (the legacy five) but in the new
# nine-mechanism vocabulary; _grading_error_taxonomy serves this to mvp-0.7
# vaults so the grader emits mechanisms directly.

MECHANISM_TAXONOMY_CARD: tuple[dict[str, object], ...] = (
    {
        "id": "retrieval_failure",
        "title": "Retrieval failure",
        "use_when": "The learner cannot retrieve the requested fact, formula, step, or facet (including after hints).",
        "avoid_when": "The answer gives a wrong model or rule; use conceptual_schema_error or selection_planning_error.",
    },
    {
        "id": "conceptual_schema_error",
        "title": "Conceptual schema error",
        "use_when": "The answer reveals a wrong definition, relationship, interpretation, or mental model of the idea.",
        "avoid_when": "The concept is right but execution or method choice is wrong; use procedure/selection/local_slip.",
    },
    {
        "id": "procedure_execution_error",
        "title": "Procedure execution error",
        "use_when": "The learner runs a procedure/algorithm but mis-executes a step, case split, or condition within it.",
        "avoid_when": "The wrong procedure/theorem was chosen in the first place; use selection_planning_error.",
    },
    {
        "id": "selection_planning_error",
        "title": "Selection or planning error",
        "use_when": "The learner selects the wrong rule/theorem/method or plans an approach that cannot reach the goal.",
        "avoid_when": "The right method is chosen but a step is mis-run; use procedure_execution_error.",
    },
    {
        "id": "condition_assumption_error",
        "title": "Condition or assumption error",
        "use_when": "The learner omits, adds, or violates a required precondition/assumption/domain restriction.",
        "avoid_when": "The setup is right but the concept itself is wrong; use conceptual_schema_error.",
    },
    {
        "id": "representation_notation_error",
        "title": "Representation or notation error",
        "use_when": "The error is in notation, representation, units, or translating between forms, not the underlying idea.",
        "avoid_when": "The notation reflects a genuinely wrong model; use conceptual_schema_error.",
    },
    {
        "id": "transfer_context_error",
        "title": "Transfer or context error",
        "use_when": "The learner knows the idea in a familiar surface but fails to apply it in a shifted or novel context.",
        "avoid_when": "The learner never had the idea; use retrieval_failure or conceptual_schema_error.",
    },
    {
        "id": "local_slip",
        "title": "Local slip",
        "use_when": "Setup and method are correct but a local arithmetic/algebra/sign/index/completeness step is wrong.",
        "avoid_when": "The slip follows from choosing the wrong method; use selection_planning_error.",
    },
    {
        "id": "assessment_ambiguity",
        "title": "Assessment ambiguity",
        "use_when": "The item or rubric is ambiguous/defective, so the failure is an item/grader issue, not a learner error.",
        "avoid_when": "The item is sound and the learner is genuinely wrong; use the fitting learner mechanism.",
    },
)

MECHANISM_TAXONOMY_CARD_JSON: tuple[dict[str, object], ...] = tuple(
    {
        **entry,
        "severity_default": MECHANISM_SEVERITY_DEFAULT[str(entry["id"])],
        "is_misconception": MECHANISM_IS_MISCONCEPTION[str(entry["id"])],
    }
    for entry in MECHANISM_TAXONOMY_CARD
)
