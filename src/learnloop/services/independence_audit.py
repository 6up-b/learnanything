"""Re-check every belief promoted on "independent surface" against the one primitive.

Spec: `spec_diagnostic_augmentation_v1.md` §8 (one implementation of
independent-group counting) and `spec_causal_attribution_v1.md` §5.6 arm (b),
narrated through §2 A6's learner-visible correction path.

**What went wrong.** §5.6 arm (b) promotes a provisional belief to a durable,
learner-wide misconception on "recurrence on a fingerprint-distinct independent
evidence group". Until now `misconceptions._promotion_reason` decided that by
counting distinct authored ``surface_family`` strings — the parallel notion
augmentation §8 forbids in as many words: *"do not grow 'item fingerprint
family' as a parallel notion. Six errors on six near-clones of one item are one
observation, everywhere, from one code path."* That code path is
``canonical_projection.surface_group_id``, which collapses a shared stimulus, a
source-example family and a solution-template family BEFORE falling back to the
authored string.

So two observations that the projection counts as one could be counted as two at
the promotion boundary, and the system would write a durable belief about the
learner on a single observation. Meas §3.A2's laddered stems make that reachable
by construction rather than by accident — a stem's parts share one stimulus and
each part is a separate item free to carry its own family string.

**Why this module exists rather than just the fix.** Correcting
``_promotion_reason`` stops NEW bad promotions. It does nothing about beliefs
already promoted under the old rule, which are exactly the ones the learner may
already have been told about — and A6 is explicit that a system whose headline
outcome is "stop telling people false things about their own minds" must be able
to say it was wrong, in the words the learner was shown. A silent re-derivation
would leave the learner holding a claim the system no longer believes.

**The verdicts, and why "cannot check" is not "fine".**

* ``holds`` — recomputed group count is still >= 2. Nothing to do.
* ``collapsed`` — the promoting evidence resolves to ONE independent group. The
  belief was promoted on a counting error and is withdrawn as
  ``retired_misdiagnosed``, which is A6's wording for "it was a misdiagnosis and
  should not have been shown to you". That is the honest reason: the diagnosis
  may even have been right, but the *evidence for durability* never existed.
* ``unresolvable`` — the promoting candidate is gone, or names items the vault
  no longer has. Treated as ``collapsed`` for the withdrawal decision, because a
  durable belief whose independence cannot be demonstrated is exactly the claim
  §5.6's promotion discipline exists to refuse. Reported under its own verdict
  so a reader can tell "we checked and it failed" from "we could not check".
* ``not_arm_b`` — promoted by another arm (probe reproduction, learner
  confirmation, adjudication). Out of scope; this audit has no opinion.

Read-only by default. The apply path is the only writer, it writes through
``surfaced_beliefs.record_belief_withdrawal`` (the one door A6 narration reads),
and it is idempotent because that helper refuses to withdraw a belief whose
disposition stream already carries this reason.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services.canonical_projection import surface_group_id
from learnloop.vault.models import LoadedVault

#: The `promotion_reason` this audit is about. Other arms rest on evidence this
#: module cannot re-derive (a blind probe match, a learner confirmation, a human
#: verdict) and are deliberately untouched.
INDEPENDENT_SURFACE_REASON = "independent_surface"

#: A6's wording for a belief that should not have been shown. Chosen over
#: `contradicted_by_trace` because the learner's work did not contradict
#: anything — the system's own evidence threshold was miscounted.
WITHDRAWAL_REASON = "retired_misdiagnosed"

AuditVerdict = Literal["holds", "collapsed", "unresolvable", "not_arm_b"]


@dataclass(frozen=True)
class BeliefIndependenceRow:
    """One promoted belief, re-judged."""

    belief_id: str
    learning_object_id: str
    statement: str
    verdict: AuditVerdict
    group_count: int
    item_ids: tuple[str, ...]
    groups: tuple[str, ...]
    detail: str

    @property
    def should_withdraw(self) -> bool:
        return self.verdict in ("collapsed", "unresolvable")

    def as_dict(self) -> dict[str, Any]:
        return {
            "belief_id": self.belief_id,
            "learning_object_id": self.learning_object_id,
            "statement": self.statement,
            "verdict": self.verdict,
            "group_count": self.group_count,
            "item_ids": list(self.item_ids),
            "groups": list(self.groups),
            "detail": self.detail,
        }


@dataclass(frozen=True)
class IndependenceAuditReport:
    rows: tuple[BeliefIndependenceRow, ...] = ()
    withdrawn: tuple[str, ...] = ()
    applied: bool = False
    declined: tuple[dict[str, str], ...] = field(default_factory=tuple)

    def summary(self) -> dict[str, int]:
        counts = {verdict: 0 for verdict in ("holds", "collapsed", "unresolvable", "not_arm_b")}
        for row in self.rows:
            counts[row.verdict] += 1
        return counts

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": 1,
            "applied": self.applied,
            "summary": self.summary(),
            "withdrawn": list(self.withdrawn),
            "declined": [dict(entry) for entry in self.declined],
            "rows": [row.as_dict() for row in self.rows],
        }


def _promoting_item_ids(repository: Repository, belief) -> tuple[str, ...] | None:
    """Item ids of the candidate this belief was promoted from, or None.

    None means the provenance is unrecoverable — the candidate row is gone, or
    it never recorded which items produced it. Both are `unresolvable`, not
    `holds`: independence that cannot be shown was never established.
    """

    for candidate in repository.misconception_candidates_for_learning_object(
        belief.learning_object_id, statuses=("promoted", "candidate")
    ):
        if str(candidate.get("promoted_misconception_id") or "") != belief.id:
            continue
        item_ids = tuple(str(item_id) for item_id in (candidate.get("item_ids") or []))
        return item_ids or None
    return None


def audit_independent_surface_promotions(
    vault: LoadedVault, repository: Repository
) -> IndependenceAuditReport:
    """Re-judge every durably-promoted belief under the corrected rule.

    Pure read. Walks the vault's learning objects rather than a global belief
    query because ``misconceptions_for_learning_object`` is the reader that
    understands the append-only lifecycle overlay — a belief already withdrawn
    must not be re-reported as a fresh finding.
    """

    from learnloop.services.durable_promotion import _ANY_BELIEF_STATUS

    rows: list[BeliefIndependenceRow] = []
    for learning_object_id in sorted(vault.learning_objects):
        for belief in repository.misconceptions_for_learning_object(
            learning_object_id, statuses=_ANY_BELIEF_STATUS
        ):
            if (belief.promotion_reason or "") != INDEPENDENT_SURFACE_REASON:
                continue
            if belief.lifecycle_disposition in ("demoted", "superseded"):
                continue  # already retracted; not a finding
            item_ids = _promoting_item_ids(repository, belief)
            if item_ids is None:
                rows.append(
                    BeliefIndependenceRow(
                        belief_id=belief.id,
                        learning_object_id=learning_object_id,
                        statement=belief.statement,
                        verdict="unresolvable",
                        group_count=0,
                        item_ids=(),
                        groups=(),
                        detail="no promoting candidate records which items produced it",
                    )
                )
                continue
            groups: set[str] = set()
            missing: list[str] = []
            for item_id in item_ids:
                item = vault.practice_items.get(item_id)
                if item is None:
                    missing.append(item_id)
                    continue
                groups.add(surface_group_id(item))
            if missing:
                rows.append(
                    BeliefIndependenceRow(
                        belief_id=belief.id,
                        learning_object_id=learning_object_id,
                        statement=belief.statement,
                        verdict="unresolvable",
                        group_count=len(groups),
                        item_ids=item_ids,
                        groups=tuple(sorted(groups)),
                        detail=f"{len(missing)} promoting item(s) no longer in the vault",
                    )
                )
                continue
            verdict: AuditVerdict = "holds" if len(groups) >= 2 else "collapsed"
            rows.append(
                BeliefIndependenceRow(
                    belief_id=belief.id,
                    learning_object_id=learning_object_id,
                    statement=belief.statement,
                    verdict=verdict,
                    group_count=len(groups),
                    item_ids=item_ids,
                    groups=tuple(sorted(groups)),
                    detail=(
                        f"{len(item_ids)} item(s) resolve to {len(groups)} independent group(s)"
                    ),
                )
            )
    return IndependenceAuditReport(rows=tuple(rows))


def apply_independence_audit(
    vault: LoadedVault,
    repository: Repository,
    *,
    clock: Clock | None = None,
) -> IndependenceAuditReport:
    """Withdraw every belief whose independence does not survive recomputation.

    Writes through ``surfaced_beliefs.record_belief_withdrawal`` — the one door
    A6's narration reads — so a belief the learner was actually SHOWN produces a
    ``belief_withdrawn`` feed entry in the words they were shown, and a belief
    nobody saw records the lifecycle fact without generating noise. That split is
    A6's, not this module's; nothing here decides what the learner is told.

    Idempotent: the helper refuses a belief whose disposition stream already
    carries this reason, so a second run withdraws nothing and narrates nothing.
    """

    from learnloop.services.surfaced_beliefs import (
        SurfacedBeliefError,
        record_belief_withdrawal,
    )

    report = audit_independent_surface_promotions(vault, repository)
    withdrawn: list[str] = []
    declined: list[dict[str, str]] = []
    for row in report.rows:
        if not row.should_withdraw:
            continue
        already = any(
            str(event.get("reason") or "") == WITHDRAWAL_REASON
            for event in repository.misconception_dispositions(row.belief_id)
        )
        if already:
            declined.append({"belief_id": row.belief_id, "reason": "already_withdrawn"})
            continue
        try:
            record_belief_withdrawal(
                repository,
                belief_id=row.belief_id,
                reason=WITHDRAWAL_REASON,
                clock=clock,
            )
        except SurfacedBeliefError as exc:
            declined.append({"belief_id": row.belief_id, "reason": str(exc)})
            continue
        withdrawn.append(row.belief_id)
    return IndependenceAuditReport(
        rows=report.rows,
        withdrawn=tuple(withdrawn),
        applied=True,
        declined=tuple(declined),
    )
