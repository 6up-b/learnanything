"""D2: gate facet minting at ingest (plan item 5.4).

(``spec_measurement_efficiency_v1.md`` D2 ~line 1042; sibling rule to D3, whose
ingest gate lives inline in ``source_set_synthesis`` and whose retroactive pass is
``services/integration_backfill``. This module follows D3's shape deliberately:
a closed disposition vocabulary, a closed typed-reason vocabulary, a verdict that
carries the evidence it was read off, and a pure function that decides while the
caller writes.)

WHAT D2 SAYS, VERBATIM
----------------------
"Today ``source_set_synthesis`` mints one facet per extracted claim at
``status: 'reviewed'``, with existing ids offered as context and nothing
structural preventing a near-duplicate." The mint criterion: a new facet is
admitted only when (1) it is **separable** from its nearest existing neighbours —
"there exists an authorable item on which a holder of one and a holder of the
other visibly diverge" — **and** (2) it implies a **distinct repair**. "Otherwise
it is registered as an **alias** of the neighbour, not as a facet." And: "Failure
is typed, not silent. A facet that cannot be shown separable is recorded with the
reason (no authorable discriminating item / same repair class / insufficient
payload to test), because that record is the missing-vocabulary signal."

THE RAW MATERIAL IS ALREADY IN THE PAYLOAD
------------------------------------------
D2: ingest emits ``preconditions``, ``applicability``, ``positive_examples``,
``negative_examples``, ``error_signatures`` and ``instructional_repairs`` per
facet, and "those are precisely what a planted persona needs — so the separability
test is §3.0's harness, run at ingest. **One mechanism, three uses.**" This module
holds the third use: it normalizes with
``diagnostic_gate.normalize_answer`` — the same "categorically distinct" test the
§3.0 authoring gate (``services/persona_gate``) grades with — so the mint gate and
the authoring gate cannot disagree about whether two beliefs are the same belief.

HOW EACH HALF IS DECIDED, AND WHY THESE ARE THE RIGHT PROXIES
-------------------------------------------------------------
*Separability.* Plant a persona on each facet from its ``error_signatures``. An
item that plants a signature **exclusive to A** is failed by an A-holder and
passed by a B-holder: that is exactly "an authorable item on which holders
visibly diverge". So the pair is separable iff each side owns at least one
signature the other does not. The symmetry is load-bearing: if A's signatures are
a *subset* of B's, every item that catches A also catches B, so A is subsumed —
which is the near-duplicate case D2 exists to stop, not an independent facet.

*Distinct repair.* The candidate must prescribe at least one
``instructional_repairs`` entry the neighbour does not. Identical repair sets mean
the two facets are one instructional obligation wearing two ids, which is what
``synthesis_gates._default_identifiability`` already calls "coarsen to one facet
(identical repairs)". Same criterion, decided at mint time instead of after the
debt accrues.

*Which facets are even compared.* Only "nearest existing neighbours" — a candidate
with no neighbour has nothing to collapse into and mints unconditionally.
Neighbourhood is proposed three ways (:class:`NeighbourKind`), and the lexical one
is explicitly only a *hint* per D1 ("never promoted to a merge criterion"): it can
put a pair in front of the harness but it can never be the reason a candidate is
aliased. Every alias in this module is caused by a separability or repair verdict.

THE ONE PLACE THIS DEPARTS FROM A LITERAL READING, AND WHY
----------------------------------------------------------
D2's "otherwise it is registered as an alias" is written for a candidate that
*was tested and collapsed*. A candidate with no ``error_signatures`` /
``instructional_repairs`` was not tested at all, and aliasing on ignorance would
delete the very record D2 asks for ("that record is the missing-vocabulary signal
... arriving from the other end of the pipe") — a missing-vocabulary signal about
a facet id that no longer exists is useless. So the third arm
(:attr:`MintDisposition.ABSTAIN`) mints the facet at ``status: "proposed"``
instead of the ``"reviewed"`` D2 names as today's defect, and records
``insufficient_payload_to_test``. The candidate stays in the vocabulary as a
standing, reviewable obligation rather than becoming an invisible synonym. Note
this is *not* a softening of the gate: nothing minted through this arm is born
reviewed, which is the structural change D2 asks for.

Everything here is a pure function of payload dicts: no vault, no repository, no
writes. :func:`judge_facet_mints` decides and explains; the ingest caller
(``source_set_synthesis._normalize``) is the only thing that acts on it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping, Sequence

from learnloop.services.diagnostic_gate import normalize_answer
from learnloop.services.synthesis_gates import facet_tokens, jaccard

#: Lexical-hint threshold. Mirrors ``GateContext.near_duplicate_threshold`` so the
#: mint gate and the §8.7 near-duplicate review surface see the same pairs.
DEFAULT_NEAR_DUPLICATE_THRESHOLD = 0.85


class MintDisposition(StrEnum):
    """What to do with one candidate facet.

    ``MINT``
        Admitted: separable from every neighbour and prescribing a distinct
        repair, or having no neighbour at all. Minted at ``status: "reviewed"``.
    ``ALIAS``
        Demonstrated to collapse into a neighbour. Registered as an alias of that
        neighbour, never as a facet. Reversible — D2: "an alias can be split back
        out. Prefer alias-and-revisit over mint-and-regret."
    ``ABSTAIN``
        A neighbour exists but the payload cannot support the test. Minted at
        ``status: "proposed"`` and recorded as a missing-vocabulary signal (see
        the module docstring for why this is not aliased).
    """

    MINT = "MINT"
    ALIAS = "ALIAS"
    ABSTAIN = "ABSTAIN"


class MintReason(StrEnum):
    """Typed reason per disposition — closed, never a free-text rationale."""

    #: MINT: the candidate has no nearest neighbour, so there is nothing it could
    #: be a duplicate of. The overwhelmingly common case on a first ingest.
    NO_NEIGHBOUR = "no_neighbour"
    #: MINT: separable from every neighbour AND prescribing a distinct repair.
    SEPARABLE_AND_DISTINCT_REPAIR = "separable_and_distinct_repair"
    #: ALIAS: no authorable item makes a holder of the candidate and a holder of
    #: the neighbour visibly diverge (D2's own wording). The candidate's distinct
    #: repair, if any, is preserved on the verdict so review can split it back out
    #: when an instrument that separates them exists.
    NO_AUTHORABLE_DISCRIMINATING_ITEM = "no_authorable_discriminating_item"
    #: ALIAS: the candidate prescribes nothing the neighbour does not. One
    #: instructional obligation, two ids — coarsen.
    SAME_REPAIR_CLASS = "same_repair_class"
    #: ABSTAIN: no ``error_signatures`` and/or no ``instructional_repairs`` on one
    #: side of the comparison, so neither criterion can be evaluated.
    INSUFFICIENT_PAYLOAD_TO_TEST = "insufficient_payload_to_test"


class NeighbourKind(StrEnum):
    """How a pair came to be compared. Ordered nearest-first.

    ``SHARED_ERROR_SIGNATURE``
        A planted persona on one facet produces an answer the other facet also
        claims. This is the §3.0-native notion of proximity and the strongest:
        the two facets are already observationally entangled.
    ``SHARED_CLAIM``
        Identical normalized ``claim``. Two entries asserting the same thing.
    ``LEXICAL_HINT``
        Jaccard over title/claim/description at or above the review threshold.
        A HINT only (D1) — it can nominate a pair, never decide one.
    """

    SHARED_ERROR_SIGNATURE = "shared_error_signature"
    SHARED_CLAIM = "shared_claim"
    LEXICAL_HINT = "lexical_hint"


_KIND_RANK: dict[NeighbourKind, int] = {
    NeighbourKind.SHARED_ERROR_SIGNATURE: 0,
    NeighbourKind.SHARED_CLAIM: 1,
    NeighbourKind.LEXICAL_HINT: 2,
}


@dataclass(frozen=True)
class Neighbour:
    """One nominated comparison, with why it was nominated and how close it is."""

    facet_id: str
    kind: NeighbourKind
    proximity: float  # shared-signature count, or the lexical Jaccard
    registered: bool  # already in the registry vs minted earlier in this batch

    def as_dict(self) -> dict[str, Any]:
        return {
            "facet_id": self.facet_id,
            "kind": str(self.kind),
            "proximity": round(self.proximity, 6),
            "registered": self.registered,
        }


@dataclass(frozen=True)
class MintVerdict:
    """One candidate facet, judged under D2, with the evidence it was judged on."""

    candidate_id: str
    disposition: MintDisposition
    reason: MintReason
    #: The facet this candidate collapses into — set iff ``disposition is ALIAS``.
    alias_of: str | None
    #: ``status`` the caller must mint at. ``None`` when nothing is minted.
    minted_status: str | None
    #: Every nominated comparison, nearest first.
    neighbours: tuple[Neighbour, ...] = ()
    #: The neighbour that decided the verdict (the first failing one).
    deciding_neighbour: str | None = None
    #: Error signatures the candidate owns and the deciding neighbour does not —
    #: empty on an ALIAS for ``no_authorable_discriminating_item`` by construction.
    exclusive_error_signatures: tuple[str, ...] = ()
    #: Repairs the candidate prescribes and the deciding neighbour does not. On an
    #: ALIAS this is the information review would recover by splitting it back out.
    exclusive_repairs: tuple[str, ...] = ()

    @property
    def mints(self) -> bool:
        return self.disposition is not MintDisposition.ALIAS

    def as_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "disposition": str(self.disposition),
            "reason": str(self.reason),
            "alias_of": self.alias_of,
            "minted_status": self.minted_status,
            "neighbours": [n.as_dict() for n in self.neighbours],
            "deciding_neighbour": self.deciding_neighbour,
            "exclusive_error_signatures": list(self.exclusive_error_signatures),
            "exclusive_repairs": list(self.exclusive_repairs),
        }


@dataclass(frozen=True)
class MintGateReport:
    verdicts: tuple[MintVerdict, ...]

    @property
    def minted(self) -> tuple[MintVerdict, ...]:
        return tuple(v for v in self.verdicts if v.disposition is MintDisposition.MINT)

    @property
    def aliased(self) -> tuple[MintVerdict, ...]:
        return tuple(v for v in self.verdicts if v.disposition is MintDisposition.ALIAS)

    @property
    def abstained(self) -> tuple[MintVerdict, ...]:
        return tuple(v for v in self.verdicts if v.disposition is MintDisposition.ABSTAIN)

    def aliases(self) -> dict[str, list[str]]:
        """target facet id -> candidate ids registered as its aliases."""

        out: dict[str, list[str]] = {}
        for verdict in self.aliased:
            if verdict.alias_of:
                out.setdefault(verdict.alias_of, []).append(verdict.candidate_id)
        return out

    def counts(self) -> dict[str, int]:
        tally = {str(d): 0 for d in MintDisposition}
        for verdict in self.verdicts:
            tally[str(verdict.disposition)] += 1
        return tally

    def reason_counts(self) -> dict[str, int]:
        tally = {str(r): 0 for r in MintReason}
        for verdict in self.verdicts:
            tally[str(verdict.reason)] += 1
        return tally

    def summary(self) -> dict[str, Any]:
        return {
            "candidate_count": len(self.verdicts),
            "dispositions": self.counts(),
            "reasons": self.reason_counts(),
            "aliases": {target: sorted(ids) for target, ids in sorted(self.aliases().items())},
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": 1,
            "summary": self.summary(),
            "verdicts": [verdict.as_dict() for verdict in self.verdicts],
        }


# --- the two criteria, as pure set operations -------------------------------


def _signatures(payload: Mapping[str, Any]) -> frozenset[str]:
    """The candidate's planted-persona answers, normalized (§3.0's harness)."""

    return frozenset(
        normalized
        for raw in (payload.get("error_signatures") or [])
        if (normalized := normalize_answer(str(raw)))
    )


def _repairs(payload: Mapping[str, Any]) -> frozenset[str]:
    return frozenset(
        normalized
        for raw in (payload.get("instructional_repairs") or [])
        if (normalized := normalize_answer(str(raw)))
    )


def _claim(payload: Mapping[str, Any]) -> str:
    return normalize_answer(str(payload.get("claim") or payload.get("title") or ""))


def separable(candidate: Mapping[str, Any], neighbour: Mapping[str, Any]) -> bool:
    """D2 criterion 1: does some authorable item make the holders diverge?

    Symmetric by construction — see the module docstring on why a subset is a
    collapse rather than an independent facet.
    """

    left, right = _signatures(candidate), _signatures(neighbour)
    return bool(left - right) and bool(right - left)


def distinct_repair(candidate: Mapping[str, Any], neighbour: Mapping[str, Any]) -> bool:
    """D2 criterion 2: does the candidate prescribe something the neighbour does not?"""

    return bool(_repairs(candidate) - _repairs(neighbour))


def is_testable(candidate: Mapping[str, Any], neighbour: Mapping[str, Any]) -> bool:
    """Both criteria need both fields on both sides. Ingest emits all four (D2).

    Named ``is_testable`` rather than ``testable`` so pytest does not collect it.
    """

    return all(
        (
            _signatures(candidate),
            _signatures(neighbour),
            _repairs(candidate),
            _repairs(neighbour),
        )
    )


# --- neighbour nomination ---------------------------------------------------


def _neighbours(
    candidate: Mapping[str, Any],
    pool: Sequence[tuple[str, Mapping[str, Any], bool]],
    *,
    near_duplicate_threshold: float,
) -> tuple[Neighbour, ...]:
    """Nominate every facet worth comparing ``candidate`` against, nearest first.

    ``pool`` is ``(facet_id, payload, registered)``. Deterministic: ties break on
    the facet id, so a re-run of the same ingest produces the same verdicts.
    """

    candidate_id = str(candidate.get("id") or "")
    signatures = _signatures(candidate)
    claim = _claim(candidate)
    tokens = facet_tokens(dict(candidate))
    found: dict[str, Neighbour] = {}

    def offer(facet_id: str, kind: NeighbourKind, proximity: float, registered: bool) -> None:
        existing = found.get(facet_id)
        if existing is not None and _KIND_RANK[existing.kind] <= _KIND_RANK[kind]:
            return
        found[facet_id] = Neighbour(
            facet_id=facet_id, kind=kind, proximity=proximity, registered=registered
        )

    for facet_id, payload, registered in pool:
        if facet_id == candidate_id:
            continue
        shared = signatures & _signatures(payload)
        if shared:
            offer(facet_id, NeighbourKind.SHARED_ERROR_SIGNATURE, float(len(shared)), registered)
            continue
        other_claim = _claim(payload)
        if claim and other_claim and claim == other_claim:
            offer(facet_id, NeighbourKind.SHARED_CLAIM, 1.0, registered)
            continue
        similarity = jaccard(tokens, facet_tokens(dict(payload)))
        if similarity >= near_duplicate_threshold:
            offer(facet_id, NeighbourKind.LEXICAL_HINT, similarity, registered)

    return tuple(
        sorted(
            found.values(),
            key=lambda n: (_KIND_RANK[n.kind], -n.proximity, n.facet_id),
        )
    )


# --- the gate ---------------------------------------------------------------


def judge_facet_mints(
    candidates: Sequence[Mapping[str, Any]],
    *,
    registered: Sequence[Mapping[str, Any]] = (),
    near_duplicate_threshold: float = DEFAULT_NEAR_DUPLICATE_THRESHOLD,
) -> MintGateReport:
    """Judge every candidate facet under D2. Writes nothing.

    Candidates are judged **in order**, and a candidate may only alias into a
    registered facet or into an earlier candidate that was itself minted. That
    ordering is what makes alias chains impossible without a compression pass:
    every ``alias_of`` names a facet that will exist after this batch is applied,
    which is the invariant ``vault.loader._facet_aliases`` needs to resolve it.
    """

    pool: list[tuple[str, Mapping[str, Any], bool]] = [
        (str(payload.get("id") or ""), payload, True)
        for payload in registered
        if payload.get("id")
    ]
    verdicts: list[MintVerdict] = []
    for candidate in candidates:
        candidate_id = str(candidate.get("id") or "")
        verdict = _judge_one(
            candidate, pool, near_duplicate_threshold=near_duplicate_threshold
        )
        verdicts.append(verdict)
        if verdict.mints and candidate_id:
            # Minted (or abstained-and-minted) facets become neighbours for the
            # candidates after them; aliased ones deliberately do not, so nothing
            # can alias into something that will not exist.
            pool.append((candidate_id, candidate, False))
    return MintGateReport(verdicts=tuple(verdicts))


def _judge_one(
    candidate: Mapping[str, Any],
    pool: Sequence[tuple[str, Mapping[str, Any], bool]],
    *,
    near_duplicate_threshold: float,
) -> MintVerdict:
    candidate_id = str(candidate.get("id") or "")
    neighbours = _neighbours(
        candidate, pool, near_duplicate_threshold=near_duplicate_threshold
    )
    if not neighbours:
        return MintVerdict(
            candidate_id=candidate_id,
            disposition=MintDisposition.MINT,
            reason=MintReason.NO_NEIGHBOUR,
            alias_of=None,
            minted_status="reviewed",
            neighbours=(),
        )
    payload_by_id = {facet_id: payload for facet_id, payload, _ in pool}
    for neighbour in neighbours:
        other = payload_by_id[neighbour.facet_id]
        if not is_testable(candidate, other):
            return MintVerdict(
                candidate_id=candidate_id,
                disposition=MintDisposition.ABSTAIN,
                reason=MintReason.INSUFFICIENT_PAYLOAD_TO_TEST,
                alias_of=None,
                # Not born reviewed: D2 names `status: "reviewed"` as the defect.
                minted_status="proposed",
                neighbours=neighbours,
                deciding_neighbour=neighbour.facet_id,
            )
        if not distinct_repair(candidate, other):
            return MintVerdict(
                candidate_id=candidate_id,
                disposition=MintDisposition.ALIAS,
                reason=MintReason.SAME_REPAIR_CLASS,
                alias_of=neighbour.facet_id,
                minted_status=None,
                neighbours=neighbours,
                deciding_neighbour=neighbour.facet_id,
                exclusive_error_signatures=tuple(
                    sorted(_signatures(candidate) - _signatures(other))
                ),
            )
        if not separable(candidate, other):
            return MintVerdict(
                candidate_id=candidate_id,
                disposition=MintDisposition.ALIAS,
                reason=MintReason.NO_AUTHORABLE_DISCRIMINATING_ITEM,
                alias_of=neighbour.facet_id,
                minted_status=None,
                neighbours=neighbours,
                deciding_neighbour=neighbour.facet_id,
                exclusive_error_signatures=tuple(
                    sorted(_signatures(candidate) - _signatures(other))
                ),
                # The distinct repair the alias defers rather than discards.
                exclusive_repairs=tuple(sorted(_repairs(candidate) - _repairs(other))),
            )
    nearest = neighbours[0]
    nearest_payload = payload_by_id[nearest.facet_id]
    return MintVerdict(
        candidate_id=candidate_id,
        disposition=MintDisposition.MINT,
        reason=MintReason.SEPARABLE_AND_DISTINCT_REPAIR,
        alias_of=None,
        minted_status="reviewed",
        neighbours=neighbours,
        deciding_neighbour=nearest.facet_id,
        exclusive_error_signatures=tuple(
            sorted(_signatures(candidate) - _signatures(nearest_payload))
        ),
        exclusive_repairs=tuple(sorted(_repairs(candidate) - _repairs(nearest_payload))),
    )


# --- typed diagnostics for the ingest caller --------------------------------

#: Gate name in the §8.7 diagnostic stream, alongside D3's ``blueprint_integration``.
MINT_GATE = "facet_mint"


def mint_diagnostic(verdict: MintVerdict) -> dict[str, Any] | None:
    """The §8.7-shaped review diagnostic for one non-clean verdict, or ``None``.

    Same dict shape ``source_set_synthesis`` already emits for D3
    (``{gate, severity, entity_refs, message, suggested_action}``). Severity is
    always ``review``: D2 changes what is minted, it never fails the build — "Review,
    never auto-merge ... The analysis proposes; a human decides."
    """

    if verdict.disposition is MintDisposition.ALIAS:
        detail = (
            "prescribes no repair the neighbour does not"
            if verdict.reason is MintReason.SAME_REPAIR_CLASS
            else "no authorable item makes a holder of each visibly diverge"
        )
        return {
            "gate": MINT_GATE,
            "severity": "review",
            "entity_refs": [verdict.candidate_id, verdict.alias_of or ""],
            "message": (
                f"facet candidate {verdict.candidate_id!r} was registered as an alias of "
                f"{verdict.alias_of!r} rather than minted: {detail} "
                f"({verdict.reason})"
            ),
            "suggested_action": (
                "confirm the collapse, or split the alias back out once an instrument "
                "that separates them exists (aliases are reversible; mints are not)"
            ),
        }
    if verdict.disposition is MintDisposition.ABSTAIN:
        return {
            "gate": MINT_GATE,
            "severity": "review",
            "entity_refs": [verdict.candidate_id, verdict.deciding_neighbour or ""],
            "message": (
                f"facet candidate {verdict.candidate_id!r} could not be shown separable from "
                f"{verdict.deciding_neighbour!r}: no error_signatures / instructional_repairs "
                f"on one side, so it was minted at status='proposed' rather than 'reviewed' "
                f"({verdict.reason})"
            ),
            "suggested_action": (
                "author error_signatures + instructional_repairs for both facets so the "
                "separability test can run, or coarsen them by hand"
            ),
        }
    return None
