"""Source-role authority (spec_source_ingestion_v2 §4.2, the single normative
authority matrix).

`role_authority(role)` is the one place that decides, for a source role, whether
it may support **semantic contracts** and whether it may contribute **assessment
alignment**. Every consumer (inventory requests, the coverage report, and — in
later milestones — the synthesis span protocol and append policy) reads this
module rather than restating policy.

Fail-closed rule (§4.2): an **unknown** role receives NO semantic-contract or
assessment-alignment privileges until a human confirms a known role or grants
explicit manual authority. A manual grant carries audit metadata (scope,
rationale, actor, timestamp). This is why an exam-unit claim can never enter a
semantic-contract context: `exam` has `semantic_contract=False`, and an unknown
role fails closed to the same.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

# Known roles (§4.2). Unknown roles are NOT rejected — they produce doctor
# warnings and fail closed for authority until confirmed.
KNOWN_ROLES: frozenset[str] = frozenset(
    {
        "primary_textbook",
        "alternate_explanation",
        "reference",
        "problem_set",
        "lecture",
        "paper",
        "exam",
        "notes",
    }
)

# The §4.2 authority matrix, verbatim in effect:
#   semantic_contract  -> may support canonical semantic claims (scoped, conflict-reviewed)
#   assessment_alignment -> may contribute task-family/blueprint/capability/format/emphasis
_MATRIX: dict[str, tuple[bool, bool]] = {
    "primary_textbook": (True, True),
    "lecture": (True, True),
    "paper": (True, True),
    "reference": (True, True),
    # supporting/alternate, never silently primary — still True for semantic support.
    "alternate_explanation": (True, True),
    # not independent authority for omitted definitions/conditions; strong task signals.
    "problem_set": (False, True),
    # NO independent semantic authority; assessment alignment only.
    "exam": (False, True),
    # manual/unclear authority; review when used canonically. Fail closed by default
    # so `notes` gains nothing without explicit confirmation/manual grant.
    "notes": (False, True),
}

# Inventory profile emphasis per role (§4.2: exam contributes assessment; problem_set
# emphasizes task/solution; explanatory roles emphasize semantic contracts). Used to
# pick a default inventory profile from a confirmed role.
_ROLE_PROFILE: dict[str, str] = {
    "primary_textbook": "combined",
    "lecture": "combined",
    "paper": "combined",
    "reference": "semantic",
    "alternate_explanation": "semantic",
    "problem_set": "practice",
    "exam": "assessment",
    "notes": "semantic",
}


@dataclass(frozen=True)
class ManualAuthorityGrant:
    """An explicit human override that lifts a fail-closed role (§4.2).

    Audit metadata is mandatory: which entities/claims (`scope`), why
    (`rationale`), who (`actor`), and when (`granted_at`)."""

    semantic_contract: bool
    assessment_alignment: bool
    scope: str
    rationale: str
    actor: str
    granted_at: str


@dataclass(frozen=True)
class RoleAuthority:
    """The resolved authority for a role."""

    role: str
    known: bool
    semantic_contract: bool
    assessment_alignment: bool
    manual: bool = False
    grant: ManualAuthorityGrant | None = None
    audit: dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "role": self.role,
            "known": self.known,
            "semantic_contract": self.semantic_contract,
            "assessment_alignment": self.assessment_alignment,
            "manual": self.manual,
        }
        if self.audit:
            payload["audit"] = dict(self.audit)
        return payload


def _coerce_grant(grant: ManualAuthorityGrant | Mapping[str, object] | None) -> ManualAuthorityGrant | None:
    if grant is None or isinstance(grant, ManualAuthorityGrant):
        return grant
    required = ("scope", "rationale", "actor", "granted_at")
    missing = [key for key in required if not str(grant.get(key) or "").strip()]
    if missing:
        raise ValueError(
            "A manual authority grant requires audit metadata; missing: " + ", ".join(missing)
        )
    return ManualAuthorityGrant(
        semantic_contract=bool(grant.get("semantic_contract")),
        assessment_alignment=bool(grant.get("assessment_alignment")),
        scope=str(grant["scope"]),
        rationale=str(grant["rationale"]),
        actor=str(grant["actor"]),
        granted_at=str(grant["granted_at"]),
    )


def role_authority(
    role: str | None,
    *,
    manual_grant: ManualAuthorityGrant | Mapping[str, object] | None = None,
) -> RoleAuthority:
    """Resolve `{semantic_contract, assessment_alignment}` for a source role (§4.2).

    Unknown or empty roles **fail closed** (both False) unless an explicit
    `manual_grant` with full audit metadata lifts them. A manual grant can only
    *widen* an unknown role; it never silently applies to a known role's defaults.
    """

    normalized = (role or "").strip()
    grant = _coerce_grant(manual_grant)

    if normalized in _MATRIX:
        semantic, assessment = _MATRIX[normalized]
        return RoleAuthority(
            role=normalized,
            known=True,
            semantic_contract=semantic,
            assessment_alignment=assessment,
        )

    # Unknown / empty role: fail closed unless a manual grant lifts it.
    if grant is not None:
        return RoleAuthority(
            role=normalized or "unknown",
            known=False,
            semantic_contract=grant.semantic_contract,
            assessment_alignment=grant.assessment_alignment,
            manual=True,
            grant=grant,
            audit={
                "scope": grant.scope,
                "rationale": grant.rationale,
                "actor": grant.actor,
                "granted_at": grant.granted_at,
            },
        )
    return RoleAuthority(
        role=normalized or "unknown",
        known=False,
        semantic_contract=False,
        assessment_alignment=False,
    )


def default_inventory_profile(role: str | None) -> str:
    """The inventory profile a confirmed role implies (§4.2/§7).

    A role that fails closed still gets a `semantic` default profile for
    *display/cost preview*, but requesting an inventory through a collection uses
    the confirmed membership/unit role and the authority module gates use."""

    return _ROLE_PROFILE.get((role or "").strip(), "semantic")


def can_authorize_semantic(role: str | None, *, manual_grant=None) -> bool:
    """True iff this role may enter a semantic-contract context (§4.2).

    The load-bearing guard: an exam-unit claim cannot enter synthesis semantic
    authority because `exam` and every unknown role return False here."""

    return role_authority(role, manual_grant=manual_grant).semantic_contract


def can_authorize_assessment(role: str | None, *, manual_grant=None) -> bool:
    """True iff this role may contribute assessment alignment (§4.2)."""

    return role_authority(role, manual_grant=manual_grant).assessment_alignment
