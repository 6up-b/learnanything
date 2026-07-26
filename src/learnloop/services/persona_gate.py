"""§3.0's shared planted-persona gate, wired into the live authoring path.

(``spec_measurement_efficiency_v1.md`` §3.0 ~line 168; plan item 5.3.)

WHAT §3.0 ASKS FOR, VERBATIM
---------------------------
"A persona **holding** the target facet must pass the item. A persona holding the
target misconception must **fail** it. For a contrast pair (A4), the
misconception-holder must fail **exactly one** member. If the personas do not
separate, the item does not ship." Zero learner cost, no state writes: the
personas are graded *in memory*.

WHY THE LIVE PATH BYPASSED IT
-----------------------------
The harness has existed since spec_misconception_diagnostics §6
(``services/diagnostic_gate.run_discrimination_gate``), and one caller enforces
it as ship/no-ship: ``proposals.generate_diagnostic_proposal(need_id=...)``. That
function has **no production callers** — only ``tests/test_diagnostic_generation``.
The `learnloop generate-diagnostics` CLI route calls a *different* entry point,
``practice_generation.generate_diagnostic_practice_proposal``, which reaches
``proposals.generate_authoring_proposal`` directly and never constructs a
``MisconceptionRecord``, so nothing on the live route could call a gate whose
signature demands one. The gate was not disabled; it was simply attached to the
branch of the generation tree that production does not use.

THE FIX IS THE SEAM THE OTHER GATES ALREADY USE
-----------------------------------------------
``generate_authoring_proposal(row_transform=...)`` runs once over the final
persisted rows, after validation/repair and before persist + auto-apply — the
same seam ``_RungGate`` and ``_SelectedResponseGate`` occupy. :class:`PersonaGate`
is a ``row_transform``, chained into **every** generation route in
``practice_generation``. That is what makes the tiering un-forgettable: there is
no route on which a diagnostic instrument escapes the hard tier, because the tier
is read off the row's own payload (:func:`classify_instrument`) rather than passed
in by whichever route happens to be running.

THE TIERING (plan §7.3, resolved)
---------------------------------
* **Hard ship/no-ship** for *diagnostic instruments*: error-hunts (A3), contrast
  pairs (A4), discrimination profiles (A5), and any item that makes an explicit
  misconception-discrimination claim (the class spec §6 already hard-gates). An
  instrument whose whole purpose is to discriminate and which demonstrably does
  not discriminate is worthless as evidence, and A3 states the rule outright: "a
  freehand error is an untyped instrument."
* **Advisory flag-for-review** for plain practice items, until augmentation §3
  B2's blinded realism matcher exists. Authoring throughput is the measured
  bottleneck and the simulator is not yet validated, so a plain item is never
  blocked on it. Flagging still costs the item its auto-apply route — "the
  advisory path bypasses neither existing quality gates nor normal review."

A PASS IS PROVISIONAL, AND SAYS SO
----------------------------------
§3.0: "Persona realism inherits augmentation §3 B2's blinded matcher: if a matcher
can separate persona traces from real vault traces, the gate is measuring a
distribution that does not exist and its verdicts do not count." Every audit
record this module writes therefore carries ``persona_realism_validated: false``.
A pre-B2 pass is an authoring check, not evidence of diagnostic validity.

WHAT THE DETERMINISTIC PATH ACTUALLY CATCHES
--------------------------------------------
The provider-free grader is ``diagnostic_gate``'s: an answer fires iff it is
*categorically distinct* from the expected answer under the shared normalizer
(:func:`~learnloop.services.diagnostic_gate.normalize_answer`). Deliberately
conservative — it under-fires rather than false-fires — so what it detects is
**blindness**: an item whose expected answer *is* what the belief-holder would
write, which is exactly ``diagnostic_gate``'s motivating regression (the
paraphrase whose planted student answers correctly). It cannot judge realism and
it cannot catch a semantically-equivalent-but-differently-worded belief answer;
a provider that exposes ``grade_diagnostic_fire`` replaces it per trial.

WHAT IS RECORDED, AND WHERE
---------------------------
Nothing here is logged-only. Each judged row gets
``row["audit"]["persona_gate"]`` — a typed record persisted into
``proposed_patch_items.audit_json`` — and a blocked row additionally goes
``validation_status="invalid"`` (which ``patches`` refuses to accept) while a
flagged row goes ``"warning"`` with a ``persona_gate_review:`` note. Passed,
flagged, blocked and untested rows are therefore distinguishable both in the
audit and in the route the row takes. On the diagnostic route a blocked row also
reopens its intervention need rather than letting an undiscriminating instrument
consume the measurement it was asked for.

WHAT IS DECIDED JOINTLY
-----------------------
Every verdict is per-row except A4's, which cannot be: "the misconception-holder
must fail **exactly one** member" is a property of the *pair*.
:meth:`PersonaGate.__call__` therefore groups rows sharing a
``contrast_pair:<id>`` tag (:data:`CONTRAST_PAIR_TAG_PREFIX`) and judges them
together, giving both members the same verdict.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Iterable, Mapping, Sequence

from learnloop.db.repositories import Repository
from learnloop.services.diagnostic_gate import normalize_answer
from learnloop.services.scoreboard import Metric
from learnloop.vault.models import LoadedVault

#: Stamped into every audit record so a later reader can tell which harness
#: version produced a verdict (the gate's semantics are expected to change when
#: B2 lands and the plain-practice tier is promoted).
PERSONA_GATE_VERSION = "persona_gate_v1"


# ---------------------------------------------------------------------------
# What kind of instrument is this? (structural — never a caller flag)
# ---------------------------------------------------------------------------


class InstrumentClass(StrEnum):
    """The closed vocabulary of authored instrument classes §3.0 governs.

    Read off the payload alone. The plan's requirement is that "a diagnostic
    instrument is hard-gated whether or not anyone remembers to pass an option",
    so the discriminator must be a property of the artifact, not of the call.

    ``ERROR_HUNT`` / ``CONTRAST_PAIR`` / ``DISCRIMINATION_PROFILE``
        Meas A3/A4/A5. Not authorable yet (Stage 6 owns them); the arms exist so
        that the day an authoring route emits one it is hard-gated on arrival
        rather than after someone remembers to extend this enum.
    ``MISCONCEPTION_DIAGNOSTIC``
        The item makes an explicit discrimination claim: it declares the
        categorically-divergent answer a belief-holder would give
        (``misconception_consistent_answer``, spec_misconception_diagnostics
        §5.2.2) and/or keys a fatal error to a registry ``misconception_id``.
        This is the class spec §6 already gates; wiring it here changes *where*
        the rule runs, not the rule.
    ``PLAIN_PRACTICE``
        A practice item that makes no discrimination claim. Advisory tier. Note a
        ``practice_mode`` of ``diagnostic_probe`` alone does NOT promote an item
        here: a probe that names no belief has made no claim to check, and the
        plan forbids throttling authoring throughput on an unvalidated simulator.
    ``NOT_AN_INSTRUMENT``
        The payload is not something a persona can answer at all — neither a
        prompt nor an expected answer. The gate abstains rather than reporting
        "the personas did not separate", which would blame the personas for a
        payload that measures nothing. (Rows that are not created practice items
        never reach classification: `PersonaGate.__call__` filters them, because
        recording a verdict on a concept row would be an opinion the gate does not
        have.)
    """

    ERROR_HUNT = "error_hunt"
    CONTRAST_PAIR = "contrast_pair"
    DISCRIMINATION_PROFILE = "discrimination_profile"
    MISCONCEPTION_DIAGNOSTIC = "misconception_diagnostic"
    PLAIN_PRACTICE = "plain_practice"
    NOT_AN_INSTRUMENT = "not_an_instrument"


class GateTier(StrEnum):
    """Hard ship/no-ship vs advisory flag-for-review vs out of scope."""

    HARD = "hard"
    ADVISORY = "advisory"
    NONE = "none"


#: The A3/A4/A5 classes whose *entire* content is a planted discrimination. For
#: these, "the gate could not be run" is itself disqualifying — A3: "Plant from
#: the registry, never freehand ... A freehand error is an untyped instrument."
UNPLANTABLE_IS_FATAL: frozenset[InstrumentClass] = frozenset(
    {
        InstrumentClass.ERROR_HUNT,
        InstrumentClass.CONTRAST_PAIR,
        InstrumentClass.DISCRIMINATION_PROFILE,
    }
)

#: Hard-tier classes = the diagnostic instruments. Everything else that is an
#: instrument at all is advisory until B2 validates persona realism.
DIAGNOSTIC_INSTRUMENT_CLASSES: frozenset[InstrumentClass] = UNPLANTABLE_IS_FATAL | {
    InstrumentClass.MISCONCEPTION_DIAGNOSTIC
}

#: ``practice_mode`` / tag tokens that name an A3/A4/A5 instrument. Matched on
#: both fields because neither is a closed vocabulary in the schema today, and a
#: gate that only read one of them would be trivially side-stepped.
_A_CLASS_TOKENS: tuple[tuple[str, InstrumentClass], ...] = (
    ("error_hunt", InstrumentClass.ERROR_HUNT),
    ("contrast_pair", InstrumentClass.CONTRAST_PAIR),
    ("discrimination_profile", InstrumentClass.DISCRIMINATION_PROFILE),
)


def tier_for(instrument_class: InstrumentClass) -> GateTier:
    if instrument_class in DIAGNOSTIC_INSTRUMENT_CLASSES:
        return GateTier.HARD
    if instrument_class is InstrumentClass.PLAIN_PRACTICE:
        return GateTier.ADVISORY
    return GateTier.NONE


def _rubric_of(payload: Mapping[str, Any]) -> Mapping[str, Any] | None:
    rubric = payload.get("grading_rubric")
    return rubric if isinstance(rubric, Mapping) else None


def _fatal_errors_of(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rubric = _rubric_of(payload)
    if rubric is None:
        return []
    return [fe for fe in (rubric.get("fatal_errors") or []) if isinstance(fe, Mapping)]


def _keyed_misconception_ids(payload: Mapping[str, Any]) -> list[str]:
    return [
        str(fe["misconception_id"])
        for fe in _fatal_errors_of(payload)
        if fe.get("misconception_id")
    ]


#: Tag prefix that binds two rows into one A4 contrast pair. `tags` already exists
#: on `PracticeItemPatchPayload`, so this needs no schema change and nothing can
#: currently emit it — A4 is Stage 6. Named here so the pair rule §3.0 states
#: ("the misconception-holder must fail exactly one member") has a convention to
#: bind on the day A4 lands, instead of shipping an unenforced clause.
CONTRAST_PAIR_TAG_PREFIX = "contrast_pair:"


def contrast_pair_key(payload: Mapping[str, Any]) -> str | None:
    """The pair id two contrast-pair members share, if the payload declares one."""

    for tag in payload.get("tags") or []:
        text = str(tag).strip()
        if text.lower().startswith(CONTRAST_PAIR_TAG_PREFIX):
            key = text[len(CONTRAST_PAIR_TAG_PREFIX):].strip()
            if key:
                return key
    return None


def classify_instrument(payload: Mapping[str, Any]) -> InstrumentClass:
    """The instrument class of one proposal-row payload (§3.0 tiering input).

    Pure, total, and payload-only. Order matters: an item that is both an
    error-hunt and keys a misconception is an error-hunt (the deeper obligation).
    """

    if not normalize_answer(str(payload.get("prompt") or "")) and not normalize_answer(
        _expected_text(payload)
    ):
        return InstrumentClass.NOT_AN_INSTRUMENT
    mode = str(payload.get("practice_mode") or "").strip().lower()
    tags = {str(tag).strip().lower() for tag in (payload.get("tags") or [])}
    for token, instrument_class in _A_CLASS_TOKENS:
        # A bare token, or the `contrast_pair:<id>` binding form, which carries the
        # pair key as a suffix.
        if mode == token or any(tag == token or tag.startswith(f"{token}:") for tag in tags):
            return instrument_class
    if payload.get("misconception_consistent_answer") or _keyed_misconception_ids(payload):
        return InstrumentClass.MISCONCEPTION_DIAGNOSTIC
    return InstrumentClass.PLAIN_PRACTICE


# ---------------------------------------------------------------------------
# The harness: personas, in-memory trials, separation verdict
# ---------------------------------------------------------------------------


class PersonaKind(StrEnum):
    """Who is answering. §3.0 names exactly two roles plus the clean control."""

    #: Holds the target facet correctly — must PASS.
    FACET_HOLDER = "facet_holder"
    #: Holds the targeted misconception / facet error signature — must FAIL.
    BELIEF_HOLDER = "belief_holder"


@dataclass(frozen=True)
class Persona:
    """One planted student, and the answer it would write.

    ``belief`` is the raw material it was planted from — a registry
    misconception statement, a payload-declared belief-consistent answer, or a
    facet payload's ``error_signatures`` entry (D2 uses the same field, which is
    the "one mechanism, three uses" §3.0/D2 call for).
    """

    persona_id: str
    kind: PersonaKind
    belief: str
    answer: str
    source: str  # registry_misconception | payload_declared | facet_error_signature | expected_answer

    def as_dict(self) -> dict[str, Any]:
        return {
            "persona_id": self.persona_id,
            "kind": str(self.kind),
            "belief": self.belief,
            "source": self.source,
        }


@dataclass(frozen=True)
class PersonaTrial:
    """One persona graded in memory against one item. Never persisted as state."""

    persona_id: str
    kind: PersonaKind
    fires: bool  # the item's grader marked this answer wrong

    @property
    def passes(self) -> bool:
        return not self.fires

    def as_dict(self) -> dict[str, Any]:
        return {
            "persona_id": self.persona_id,
            "kind": str(self.kind),
            "fires": self.fires,
            "passes": self.passes,
        }


class GateDecision(StrEnum):
    """The four outcomes, and the four different things they mean.

    ``PASS``
        The personas separated. Provisional pre-B2 (see module docstring).
    ``FLAG_FOR_REVIEW``
        They did not separate, and the class is advisory tier: the row loses
        auto-apply and carries a review note, but ships to the review queue.
    ``BLOCK``
        They did not separate (or could not be planted at all) and the class is
        hard tier: ``validation_status="invalid"``, which acceptance refuses.
    ``UNTESTED``
        The gate could not be run — no persona raw material exists for this
        item's targets. Explicit abstention, not a pass: recorded with its
        reason, no route change, and *excluded* from the gate-precision
        denominator, because the gate made no prediction about it.
    """

    PASS = "pass"
    FLAG_FOR_REVIEW = "flag_for_review"
    BLOCK = "block"
    UNTESTED = "untested"


class PersonaGateReason(StrEnum):
    """Closed vocabulary of *why*. One arm per distinct remedy."""

    #: PASS: belief-holder fails, facet-holder passes.
    PERSONAS_SEPARATE = "personas_separate"
    #: PASS (A4): the belief-holder fails exactly one member of the pair.
    CONTRAST_PAIR_SEPARATES = "contrast_pair_separates"
    #: FAIL: the planted belief-holder answers the item correctly — the item is
    #: blind to the belief it claims to probe. `diagnostic_gate`'s regression case.
    BELIEF_HOLDER_PASSES = "belief_holder_passes"
    #: FAIL: the facet-holder fails its own item (the answer key is not what a
    #: competent learner would produce). Unreachable on the deterministic grader by
    #: construction — the control answers with the expected answer, which is never
    #: categorically distinct from itself — and reachable only when a provider's
    #: ``grade_diagnostic_fire`` judges the clean answer semantically. Kept as an
    #: explicit arm rather than an assertion, because the semantic grader is a
    #: supported path and a silent asymmetry there would read as a pass.
    FACET_HOLDER_FAILS = "facet_holder_fails"
    #: FAIL (A4): the belief-holder fails both members, so the pair localizes
    #: nothing — it is one hard item wearing two ids.
    CONTRAST_PAIR_FAILS_BOTH = "contrast_pair_fails_both"
    #: FAIL (A4): the belief-holder fails neither member.
    CONTRAST_PAIR_FAILS_NEITHER = "contrast_pair_fails_neither"
    #: FAIL: the item claims to discriminate a named belief but keys no fatal
    #: error to it, so a failure cannot be attributed. Mirrors
    #: `diagnostic_gate`'s `no_keyed_fatal_error` blocking reason.
    NO_KEYED_DETECTOR = "no_keyed_detector"
    #: ABSTAIN / (hard tier for A3-A5) FAIL: nothing to plant from — no declared
    #: belief answer, no registry signature, no facet `error_signatures`.
    INSUFFICIENT_PERSONA_PAYLOAD = "insufficient_persona_payload"
    #: ABSTAIN: the row is not a created practice item.
    NOT_AN_INSTRUMENT = "not_an_instrument"


@dataclass(frozen=True)
class SeparationVerdict:
    """Whether one item's personas separate, with the trials that decided it."""

    separates: bool
    reason: PersonaGateReason
    trials: tuple[PersonaTrial, ...] = ()
    personas: tuple[Persona, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "separates": self.separates,
            "reason": str(self.reason),
            "trials": [trial.as_dict() for trial in self.trials],
            "personas": [persona.as_dict() for persona in self.personas],
        }


def _fires(
    answer: str,
    *,
    expected: str,
    grading_client: Any = None,
    fire_context: Mapping[str, Any] | None = None,
) -> bool:
    """Grade one persona answer in memory. No attempt/mastery/error_event write.

    Deterministic default: an answer fires iff it is non-empty and categorically
    distinct from the expected answer under the shared normalizer. A provider
    exposing ``grade_diagnostic_fire`` (the seam ``diagnostic_gate`` already
    defines) replaces the string comparison with a semantic judgement.
    """

    if grading_client is not None:
        grade = getattr(grading_client, "grade_diagnostic_fire", None)
        if callable(grade):
            try:
                return bool(grade(answer=answer, expected=expected, **dict(fire_context or {})))
            except Exception:
                # A provider outage must never block authoring (spec §6); fall
                # through to the deterministic rule rather than failing the batch.
                pass
    normalized = normalize_answer(answer)
    if not normalized:
        return False
    return normalized != normalize_answer(expected)


def separation_verdict(
    *,
    expected_answer: str,
    personas: Sequence[Persona],
    require_keyed_detector: bool,
    has_keyed_detector: bool,
    grading_client: Any = None,
    fire_context: Mapping[str, Any] | None = None,
) -> SeparationVerdict:
    """§3.0's single question, asked over one item's personas.

    Separation requires BOTH directions: every ``BELIEF_HOLDER`` must fire and
    every ``FACET_HOLDER`` must not. One-directional checking is what lets a
    merely-hard item pass as a diagnostic (everyone fails it) and a
    merely-easy one pass as a control (nobody does).
    """

    if not personas:
        return SeparationVerdict(False, PersonaGateReason.INSUFFICIENT_PERSONA_PAYLOAD)
    if not any(persona.kind is PersonaKind.BELIEF_HOLDER for persona in personas):
        return SeparationVerdict(
            False, PersonaGateReason.INSUFFICIENT_PERSONA_PAYLOAD, personas=tuple(personas)
        )
    if require_keyed_detector and not has_keyed_detector:
        return SeparationVerdict(
            False, PersonaGateReason.NO_KEYED_DETECTOR, personas=tuple(personas)
        )
    trials = tuple(
        PersonaTrial(
            persona_id=persona.persona_id,
            kind=persona.kind,
            fires=_fires(
                persona.answer,
                expected=expected_answer,
                grading_client=grading_client,
                fire_context=fire_context,
            ),
        )
        for persona in personas
    )
    for trial in trials:
        if trial.kind is PersonaKind.FACET_HOLDER and trial.fires:
            return SeparationVerdict(
                False, PersonaGateReason.FACET_HOLDER_FAILS, trials, tuple(personas)
            )
    for trial in trials:
        if trial.kind is PersonaKind.BELIEF_HOLDER and not trial.fires:
            return SeparationVerdict(
                False, PersonaGateReason.BELIEF_HOLDER_PASSES, trials, tuple(personas)
            )
    return SeparationVerdict(
        True, PersonaGateReason.PERSONAS_SEPARATE, trials, tuple(personas)
    )


# ---------------------------------------------------------------------------
# Building personas from the material the vault actually has
# ---------------------------------------------------------------------------


def _facet_error_signatures(vault: LoadedVault, facet_id: str) -> list[str]:
    facet = vault.evidence_facets.get(vault.canonical_facet_id(facet_id))
    if facet is None:
        return []
    return [str(signature) for signature in (facet.error_signatures or []) if str(signature).strip()]


def build_personas(
    payload: Mapping[str, Any],
    *,
    vault: LoadedVault,
    repository: Repository | None = None,
) -> tuple[Persona, ...]:
    """Plant the personas §3.0 needs from whatever the payload/registry supplies.

    Sources, in descending authority — the first that yields a belief answer wins,
    because a payload-declared belief answer is the author's own claim about what
    the item discriminates and is therefore the claim to hold them to:

    1. ``misconception_consistent_answer`` on the payload (§5.2.2);
    2. the registry ``MisconceptionRecord.signature`` for a keyed fatal error;
    3. the target facets' ``error_signatures`` — the ingest-emitted field D2 also
       plants from (§3.0/D2: "one mechanism, three uses").

    The ``FACET_HOLDER`` control is always the item's own expected answer: a
    learner who holds every target facet writes the answer key. Under the
    deterministic grader that control necessarily passes (the answer is compared
    with itself); under a provider's semantic grader it need not, which is the only
    path to :data:`PersonaGateReason.FACET_HOLDER_FAILS`. It is graded rather than
    assumed precisely so that asymmetry is visible instead of silent.
    """

    expected = _expected_text(payload)
    personas: list[Persona] = [
        Persona(
            persona_id="clean",
            kind=PersonaKind.FACET_HOLDER,
            belief="holds every target facet",
            answer=expected,
            source="expected_answer",
        )
    ]
    declared = payload.get("misconception_consistent_answer")
    if declared and str(declared).strip():
        personas.append(
            Persona(
                persona_id="belief_declared",
                kind=PersonaKind.BELIEF_HOLDER,
                belief=str(declared),
                answer=str(declared),
                source="payload_declared",
            )
        )
        return tuple(personas)
    if repository is not None:
        for mc_id in _keyed_misconception_ids(payload):
            record = repository.misconception(mc_id)
            if record is None or not str(getattr(record, "signature", "") or "").strip():
                continue
            personas.append(
                Persona(
                    persona_id=f"belief_{mc_id}",
                    kind=PersonaKind.BELIEF_HOLDER,
                    belief=str(record.statement),
                    answer=str(record.signature),
                    source="registry_misconception",
                )
            )
        if len(personas) > 1:
            return tuple(personas)
    for facet_id in payload.get("evidence_facets") or []:
        for index, signature in enumerate(_facet_error_signatures(vault, str(facet_id))):
            personas.append(
                Persona(
                    persona_id=f"belief_{facet_id}_{index}",
                    kind=PersonaKind.BELIEF_HOLDER,
                    belief=signature,
                    answer=signature,
                    source="facet_error_signature",
                )
            )
    return tuple(personas)


def _expected_text(payload: Mapping[str, Any]) -> str:
    expected = payload.get("expected_answer")
    if isinstance(expected, Mapping):
        return " ".join(str(value) for value in expected.values())
    return str(expected or "")


def _ref(row: Mapping[str, Any]) -> str:
    payload = row.get("payload") if isinstance(row.get("payload"), Mapping) else {}
    return str(row.get("client_item_id") or payload.get("id") or "item")


# ---------------------------------------------------------------------------
# The gate itself
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PersonaGateOutcome:
    """One row's typed gate outcome — the thing persisted into ``audit_json``."""

    client_item_id: str
    practice_item_id: str | None
    instrument_class: InstrumentClass
    tier: GateTier
    decision: GateDecision
    reason: PersonaGateReason
    verdict: SeparationVerdict | None
    target_facets: tuple[str, ...] = ()

    @property
    def gated(self) -> bool:
        """Did the gate make a prediction about this item?

        Only ``BLOCK`` and ``FLAG_FOR_REVIEW`` are predictions ("this item is
        bad"), and only they belong in the gate-precision denominator.
        """

        return self.decision in {GateDecision.BLOCK, GateDecision.FLAG_FOR_REVIEW}

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": PERSONA_GATE_VERSION,
            "client_item_id": self.client_item_id,
            "practice_item_id": self.practice_item_id,
            "instrument_class": str(self.instrument_class),
            "tier": str(self.tier),
            "decision": str(self.decision),
            "reason": str(self.reason),
            "target_facets": list(self.target_facets),
            # §3.0's own validity precondition. A pass is an authoring check
            # until augmentation §3 B2's blinded matcher says the personas
            # resemble real learners; recorded per row so no reader can mistake
            # a pre-B2 pass for diagnostic validity.
            "persona_realism_validated": False,
            "verdict": self.verdict.as_dict() if self.verdict is not None else None,
        }


class PersonaGate:
    """§3.0 as a ``row_transform`` over persisted proposal rows (plan item 5.3).

    Fail-closed in the same sense as ``_RungGate``: this runs before persist, so
    an exception aborts the batch rather than silently admitting an ungated item.

    Not a knob: there is no "strict" flag. The tier of each row is
    :func:`tier_for` of :func:`classify_instrument` of that row's payload.
    """

    def __init__(
        self,
        vault: LoadedVault,
        repository: Repository | None = None,
        *,
        grading_client: Any = None,
    ) -> None:
        self._vault = vault
        self._repository = repository
        self._grading_client = grading_client
        self.outcomes: list[PersonaGateOutcome] = []

    # -- reporting -------------------------------------------------------
    @property
    def blocked(self) -> list[PersonaGateOutcome]:
        return [o for o in self.outcomes if o.decision is GateDecision.BLOCK]

    @property
    def flagged(self) -> list[PersonaGateOutcome]:
        return [o for o in self.outcomes if o.decision is GateDecision.FLAG_FOR_REVIEW]

    @property
    def violations(self) -> list[str]:
        """Hard-tier failures, in ``_RungGate``'s ``"<ref>: <message>"`` shape."""

        return [
            f"{o.client_item_id}: persona gate blocked a {o.instrument_class} ({o.reason})"
            for o in self.blocked
        ]

    @property
    def warnings(self) -> list[str]:
        return [
            f"{o.client_item_id}: persona gate flagged a {o.instrument_class} ({o.reason})"
            for o in self.flagged
        ]

    def summary(self) -> dict[str, Any]:
        decisions = {str(decision): 0 for decision in GateDecision}
        reasons: dict[str, int] = {}
        classes: dict[str, int] = {}
        for outcome in self.outcomes:
            decisions[str(outcome.decision)] += 1
            reasons[str(outcome.reason)] = reasons.get(str(outcome.reason), 0) + 1
            classes[str(outcome.instrument_class)] = classes.get(str(outcome.instrument_class), 0) + 1
        return {
            "version": PERSONA_GATE_VERSION,
            "items_judged": len(self.outcomes),
            "decisions": decisions,
            "reasons": reasons,
            "instrument_classes": classes,
        }

    # -- the row_transform ----------------------------------------------
    def __call__(self, rows: list[dict[str, Any]]) -> None:
        # Contrast pairs (A4) are a JOINT property of two rows — "the
        # misconception-holder must fail exactly one member" cannot be decided one
        # row at a time — so they are grouped first and judged together. A pair key
        # with a single member has no second member to fail, so it falls through to
        # the single-instrument path and must separate on its own.
        pairs: dict[str, list[dict[str, Any]]] = {}
        singles: list[dict[str, Any]] = []
        for row in rows:
            if not self._is_authored_item(row):
                continue
            payload = row["payload"]
            key = (
                contrast_pair_key(payload)
                if classify_instrument(payload) is InstrumentClass.CONTRAST_PAIR
                else None
            )
            if key is None:
                singles.append(row)
            else:
                pairs.setdefault(key, []).append(row)
        for row in singles:
            self._apply(row, self.judge(row["payload"], client_item_id=_ref(row)))
        for key in sorted(pairs):
            members = pairs[key]
            if len(members) < 2:
                self._apply(
                    members[0], self.judge(members[0]["payload"], client_item_id=_ref(members[0]))
                )
                continue
            for row, outcome in zip(members, self._judge_contrast_pair(key, members)):
                self._apply(row, outcome)

    @staticmethod
    def _is_authored_item(row: Mapping[str, Any]) -> bool:
        return (
            row.get("item_type") == "practice_item"
            and row.get("operation") == "create"
            and isinstance(row.get("payload"), Mapping)
        )

    def _apply(self, row: dict[str, Any], outcome: PersonaGateOutcome) -> None:
        self.outcomes.append(outcome)
        self._record(row, outcome)

    def _judge_contrast_pair(
        self, key: str, members: Sequence[Mapping[str, Any]]
    ) -> list[PersonaGateOutcome]:
        """§3.0's A4 clause: the belief-holder must fail EXACTLY one member.

        The verdict is a property of the pair, so every member carries the same
        decision. Failing both means the pair localizes nothing (one hard item with
        two ids); failing neither means it discriminates nothing at all.
        """

        beliefs: tuple[Persona, ...] = ()
        for row in members:
            personas = build_personas(
                row["payload"], vault=self._vault, repository=self._repository
            )
            beliefs = tuple(p for p in personas if p.kind is PersonaKind.BELIEF_HOLDER)
            if beliefs:
                break
        outcomes: list[PersonaGateOutcome] = []
        if not beliefs:
            # Unplantable A4 pair: A3's rule ("a freehand error is an untyped
            # instrument") applies to every A-class instrument.
            for row in members:
                outcomes.append(
                    self._pair_outcome(
                        row,
                        GateDecision.BLOCK,
                        SeparationVerdict(False, PersonaGateReason.INSUFFICIENT_PERSONA_PAYLOAD),
                    )
                )
            return outcomes
        belief = beliefs[0]
        trials = [
            PersonaTrial(
                persona_id=f"{belief.persona_id}@{_ref(row)}",
                kind=belief.kind,
                fires=_fires(
                    belief.answer,
                    expected=_expected_text(row["payload"]),
                    grading_client=self._grading_client,
                    fire_context={"payload": dict(row["payload"]), "contrast_pair": key},
                ),
            )
            for row in members
        ]
        fired = sum(1 for trial in trials if trial.fires)
        if fired == 1:
            verdict = SeparationVerdict(
                True, PersonaGateReason.CONTRAST_PAIR_SEPARATES, tuple(trials), (belief,)
            )
        elif fired == 0:
            verdict = SeparationVerdict(
                False, PersonaGateReason.CONTRAST_PAIR_FAILS_NEITHER, tuple(trials), (belief,)
            )
        else:
            verdict = SeparationVerdict(
                False, PersonaGateReason.CONTRAST_PAIR_FAILS_BOTH, tuple(trials), (belief,)
            )
        decision = GateDecision.PASS if verdict.separates else GateDecision.BLOCK
        return [self._pair_outcome(row, decision, verdict) for row in members]

    @staticmethod
    def _pair_outcome(
        row: Mapping[str, Any], decision: GateDecision, verdict: SeparationVerdict
    ) -> PersonaGateOutcome:
        payload = row["payload"]
        return PersonaGateOutcome(
            client_item_id=_ref(row),
            practice_item_id=str(payload.get("id")) if payload.get("id") else None,
            instrument_class=InstrumentClass.CONTRAST_PAIR,
            tier=GateTier.HARD,
            decision=decision,
            reason=verdict.reason,
            verdict=verdict,
            target_facets=tuple(str(f) for f in (payload.get("evidence_facets") or [])),
        )

    def judge(
        self, payload: Mapping[str, Any], *, client_item_id: str = "item"
    ) -> PersonaGateOutcome:
        """Judge one payload. Public so callers outside the row seam can reuse it."""

        instrument_class = classify_instrument(payload)
        tier = tier_for(instrument_class)
        facets = tuple(str(facet) for facet in (payload.get("evidence_facets") or []))
        base = {
            "client_item_id": client_item_id,
            "practice_item_id": str(payload.get("id")) if payload.get("id") else None,
            "instrument_class": instrument_class,
            "tier": tier,
            "target_facets": facets,
        }
        if tier is GateTier.NONE:
            return PersonaGateOutcome(
                **base,
                decision=GateDecision.UNTESTED,
                reason=PersonaGateReason.NOT_AN_INSTRUMENT,
                verdict=None,
            )
        personas = build_personas(payload, vault=self._vault, repository=self._repository)
        verdict = separation_verdict(
            expected_answer=_expected_text(payload),
            personas=personas,
            # A diagnostic instrument must *attribute* a failure, not merely mark
            # it wrong, so it owes a fatal error keyed to the belief it claims.
            # A plain practice item claims nothing and owes nothing.
            require_keyed_detector=instrument_class is InstrumentClass.MISCONCEPTION_DIAGNOSTIC,
            has_keyed_detector=bool(_keyed_misconception_ids(payload)),
            grading_client=self._grading_client,
            fire_context={"payload": dict(payload)},
        )
        return PersonaGateOutcome(
            **base,
            decision=self._decide(instrument_class, tier, verdict),
            reason=verdict.reason,
            verdict=verdict,
        )

    @staticmethod
    def _decide(
        instrument_class: InstrumentClass, tier: GateTier, verdict: SeparationVerdict
    ) -> GateDecision:
        """Map a separation verdict onto a route decision, given the tier."""

        if verdict.separates:
            return GateDecision.PASS
        if verdict.reason is PersonaGateReason.INSUFFICIENT_PERSONA_PAYLOAD:
            # Untestable. For A3/A4/A5 the plant IS the instrument, so an
            # unplantable one is untyped and must not ship; for every other class
            # this is an honest abstention, not a failed prediction.
            if instrument_class in UNPLANTABLE_IS_FATAL:
                return GateDecision.BLOCK
            return GateDecision.UNTESTED
        return GateDecision.BLOCK if tier is GateTier.HARD else GateDecision.FLAG_FOR_REVIEW

    @staticmethod
    def _record(row: dict[str, Any], outcome: PersonaGateOutcome) -> None:
        """Persist the typed outcome onto the row (audit + route), never log-only."""

        audit = row.get("audit")
        audit = dict(audit) if isinstance(audit, Mapping) else {}
        audit["persona_gate"] = outcome.as_dict()
        row["audit"] = audit
        if outcome.decision is GateDecision.BLOCK:
            row["_auto_apply"] = False
            row["validation_status"] = "invalid"
            errors = list(row.get("validation_errors") or [])
            row["validation_errors"] = [f"persona_gate: {outcome.reason}", *errors]
            return
        if outcome.decision is GateDecision.FLAG_FOR_REVIEW:
            row["_auto_apply"] = False
            if row.get("validation_status") == "valid":
                row["validation_status"] = "warning"
            errors = list(row.get("validation_errors") or [])
            errors.append(f"persona_gate_review: {outcome.reason}")
            row["validation_errors"] = errors


# ---------------------------------------------------------------------------
# Gate precision — tracked from day one, reported honestly
# ---------------------------------------------------------------------------

#: Scoreboard row name. Not in `B5_ORDER` (that list is frozen); the scoreboard
#: composes this the way it composes `false_certification_rate`.
GATE_PRECISION_METRIC = "persona_gate_precision"


@dataclass(frozen=True)
class GatePrecisionRow:
    """One persisted gate outcome, joined to the reviewer's later decision."""

    proposal_item_id: str
    patch_id: str
    client_item_id: str
    instrument_class: str
    tier: str
    decision: str
    reason: str
    reviewer_decision: str
    created_at: str | None = None

    @property
    def gated(self) -> bool:
        return self.decision in {str(GateDecision.BLOCK), str(GateDecision.FLAG_FOR_REVIEW)}


def gate_precision(
    repository: Repository,
    *,
    blinded_labels: Mapping[str, bool] | None = None,
    since: str | None = None,
) -> Metric:
    """``persona_gate_precision``: of the items the gate blocked or flagged, how
    many were genuinely bad.

    DEFINITION
    ----------
    ``precision = |gated ∧ genuinely_bad| / |gated|`` where *gated* = the items on
    which the gate made a prediction (``BLOCK`` or ``FLAG_FOR_REVIEW``; ``PASS``
    and ``UNTESTED`` are excluded — ``UNTESTED`` is an abstention and scoring it
    would punish the gate for honesty). The denominator is countable **today** and
    is reported on every arm.

    THE GROUND TRUTH IT AWAITS, AND THE PROXY IT REFUSES
    ---------------------------------------------------
    "Genuinely bad" must come from a judgement that **cannot see the gate's
    verdict**. Two future producers qualify:

    * augmentation §3 **B2**'s blinded realism matcher — §3.0's own validity
      precondition ("if a matcher can separate persona traces from real vault
      traces ... its verdicts do not count"). Until it runs, a pass/fail from this
      harness is a statement about a distribution that may not exist, so there is
      no defensible label at all.
    * Stage 7 **B1**'s planted-vs-adjudicated side, which
      ``scoreboard.planted_vs_adjudicated_agreement`` already reports as
      ``no_producer``: the adjudicated half exists
      (``diagnosis_adjudication.adjudicated_ground_truth``), the planted half is
      B1's.

    The obvious proxy — "the reviewer rejected it" — is **inadmissible and is not
    computed here**. The gate writes its reason into ``validation_errors``, which
    is exactly what the reviewer reads, so a reviewer-decision label is caused by
    the prediction it is supposed to score; it would render as a high precision
    number that measures the review UI. Reviewer decisions ARE captured (from day
    one, per plan 5.3) and reported in ``detail.reviewer_decisions`` as descriptive
    counts, with no rate derived from them.

    AVAILABILITY (same discipline as ``services/scoreboard``)
    --------------------------------------------------------
    * no gated items yet -> ``no_data`` (remedy: author some items);
    * gated items but no blinded labels -> ``no_producer`` (remedy: land B2/B1);
    * labels supplied -> ``available``.

    A rate over zero gated items is never 0.0 and never 1.0.

    ``blinded_labels`` maps ``proposed_patch_items.id`` -> "genuinely bad", and is
    the seam a blinded producer fills.
    """

    rows = persona_gate_rows(repository, since=since)
    gated = [row for row in rows if row.gated]
    detail: dict[str, Any] = {
        "version": PERSONA_GATE_VERSION,
        "items_judged": len(rows),
        "decisions": _tally(row.decision for row in rows),
        "reasons": _tally(row.reason for row in gated),
        "instrument_classes": _tally(row.instrument_class for row in gated),
        "tiers": _tally(row.tier for row in gated),
        # Descriptive only — see the docstring on why no rate is derived.
        "reviewer_decisions": _tally(row.reviewer_decision for row in gated),
        "label_source": "blinded_labels" if blinded_labels else None,
    }
    if not gated:
        return Metric(
            name=GATE_PRECISION_METRIC,
            availability="no_data",
            value=None,
            numerator=None,
            denominator=0,
            unit="rate",
            denominator_label="items blocked or flagged by the persona gate",
            note=(
                "the persona gate has made no block/flag prediction yet; "
                "PASS and UNTESTED outcomes are deliberately not scored"
            ),
            detail=detail,
        )
    labelled = {
        row.proposal_item_id: bool(blinded_labels[row.proposal_item_id])
        for row in gated
        if blinded_labels and row.proposal_item_id in blinded_labels
    }
    if not labelled:
        return Metric(
            name=GATE_PRECISION_METRIC,
            availability="no_producer",
            value=None,
            numerator=None,
            denominator=len(gated),
            unit="rate",
            denominator_label="items blocked or flagged by the persona gate",
            note=(
                "no blinded 'genuinely bad' label exists: B2's realism matcher and "
                "B1's planted side are the admissible producers, and reviewer "
                "decisions are confounded by the gate's own reason string"
            ),
            detail=detail,
        )
    detail["labelled"] = len(labelled)
    return Metric(
        name=GATE_PRECISION_METRIC,
        availability="available",
        value=round(sum(1 for bad in labelled.values() if bad) / len(labelled), 6),
        numerator=float(sum(1 for bad in labelled.values() if bad)),
        denominator=float(len(labelled)),
        unit="rate",
        denominator_label="blinded-labelled items blocked or flagged by the persona gate",
        note="share of blocked/flagged items a blinded judgement calls genuinely bad",
        detail=detail,
    )


def _tally(values: Iterable[str]) -> dict[str, int]:
    tally: dict[str, int] = {}
    for value in values:
        tally[value] = tally.get(value, 0) + 1
    return tally


def persona_gate_rows(
    repository: Repository, *, since: str | None = None
) -> list[GatePrecisionRow]:
    """Every persisted persona-gate outcome, joined to its reviewer decision."""

    return [
        GatePrecisionRow(
            proposal_item_id=str(raw["proposal_item_id"]),
            patch_id=str(raw["patch_id"]),
            client_item_id=str(raw.get("client_item_id") or ""),
            instrument_class=str(raw.get("instrument_class") or ""),
            tier=str(raw.get("tier") or ""),
            decision=str(raw.get("decision") or ""),
            reason=str(raw.get("reason") or ""),
            reviewer_decision=str(raw.get("reviewer_decision") or "pending"),
            created_at=raw.get("created_at"),
        )
        for raw in repository.persona_gate_audit_rows(since=since)
    ]
