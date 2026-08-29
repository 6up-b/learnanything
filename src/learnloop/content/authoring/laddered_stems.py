"""A2 — laddered stems (spec_measurement_efficiency_v1 §3.A2). Plan item 6.4.

THE HYPOTHESIS
--------------
"One stimulus; parts that walk the same facet up the capability vocabulary: state
it (``retrieval``) -> which theorem applies (``method_selection``) -> execute
(``procedure_execution``) -> the edge case where coordination is the difficulty.
One context-loading cost, four columns. The dominant cost in any assessment is
loading the problem into the learner's head. Laddered stems amortize it, and they
are the only instrument that fills a *row* of the capability grid rather than a
cell." §3.A2's stated hypothesis: *capability-grid rows fill without an increase
in items authored; ``questions_to_certification`` falls on LOs whose blueprints
span >= 3 capabilities.*

THE REVERT CRITERION, AND THE CODE THAT MEASURES IT
--------------------------------------------------
"*Revert if:* cross-column outcomes on one stem correlate as tightly as
within-column ones, i.e. the independence claim is empirically false. **Measure
this before trusting it**; it is a claim about learners, not about code."

:func:`stem_independence_signal` is that measurement. Per stem it pairs the
learner's outcomes on parts that share a capability (within-column) against those
on parts that do not (cross-column), and reports the two agreement rates side by
side. The instrument's claim is that within-column agreement should be HIGHER —
two ``procedure_execution`` parts on one stimulus are close to one observation,
while retrieval and coordination on the same stimulus are different
measurements. Cross-column agreement reaching within-column agreement is the
revert condition, and the metric names it as a verdict rather than leaving a
reader to compare two numbers and remember which way round the claim went.

THE KINSHIP RULE LIVES IN ONE PLACE, AND IT IS NOT HERE
-------------------------------------------------------
Augmentation §8 requires one code path for kinship, and
``EvidenceFingerprint.shared_stimulus_id`` already exists. So the rule — parts of
one stem co-cluster within a capability column and never across columns — is two
edge cases inside ``familiarity.tight_kinship_clusters``, the existing
single-linkage pass. This module contributes only the IDENTITY that rule reads
(:func:`stem_column_for_item`, :func:`stem_columns_for_surfaces`) and the
measurement above. There is deliberately no clustering, no grouping and no
independent-group arithmetic in this file: a second implementation that agreed
with the first today would disagree with it eventually.

WHY THE LIVE PROJECTION NEEDED NO CHANGE, AND THE SOFT-KINSHIP PASS DID
-----------------------------------------------------------------------
There are two places in the vault that decide how many independent observations
a set of surfaces is worth, and they were not equally wrong about stems:

* ``canonical_projection`` accumulates ``independent_surface_groups`` **per
  ``(facet, capability)`` cell**, and its ``surface_group_id`` collapses a shared
  stimulus into one group. Because the accumulator is already keyed by
  capability, two parts at one capability share a group inside one cell
  (correlated within a column) while two parts at different capabilities land in
  *different cells* and each contribute their own group (independent across
  columns). A2's rule is a consequence of the cell key there, and touching it
  would be a change in search of a bug.
* ``familiarity.tight_kinship_clusters`` clusters by *warmth features*, which
  carry no capability at all. Parts of one stem share a stimulus, a source and
  usually a facet, so warmth between them is high and the pre-A2 pass would
  correctly-by-its-own-lights collapse a whole capability row into one
  observation. That is the implementation the spec names ("``progression.py``
  soft kinship"), and it is the one this ships an edge case into.

WHY THE PARTS ARE SEPARATE ITEMS
--------------------------------
See ``vault.models.LadderedStemContract``. Briefly: credit is filed per
``(facet, capability)`` cell and a ``PracticeItem`` declares one capability, so a
single item holding four parts would have to file all four under one rung —
§5.8.2's 72% loss, reproduced inside one item.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from learnloop.db.repositories import Repository
from learnloop.diagnosis.scoreboard import Metric
from learnloop.vault.models import LoadedVault, PracticeItem

LADDERED_STEM_VERSION = "laddered_stem_v1"


# ---------------------------------------------------------------------------
# Identity: what the one kinship rule reads
# ---------------------------------------------------------------------------


def stem_id_for_item(item: PracticeItem) -> str | None:
    """This item's stem, from either of the two places it can be declared.

    ``laddered_stem.stem_id`` is A2's authoring field;
    ``evidence_fingerprint.shared_stimulus_id`` is the pre-existing global
    fingerprint the kinship and held-out machinery already key on. They are
    supposed to agree, and the authoring prompt says so — but reading BOTH means
    a stem authored before A2 (a shared stimulus with no ``laddered_stem`` block)
    still participates in the rule, and a stem whose fingerprint was dropped in
    an edit does not silently become four independent observations.

    The authoring field wins when both are present: it is the explicit claim.
    """

    contract = item.laddered_stem
    if contract is not None and str(contract.stem_id or "").strip():
        return str(contract.stem_id)
    shared = getattr(item.evidence_fingerprint, "shared_stimulus_id", None)
    return str(shared) if shared else None


def stem_column_for_item(item: PracticeItem) -> tuple[str, str] | None:
    """``(stem_id, capability)`` for one item, or ``None`` if it is not a stem part.

    ``None`` when the item declares no stem OR no capability. A part with no
    capability cannot be placed in a column, and guessing one (from the practice
    mode, say) would decide the independence question by default — the exact
    thing standing constraint 8 forbids doing to the capability axis.
    """

    stem = stem_id_for_item(item)
    capability = getattr(item, "capability", None)
    if not stem or not capability:
        return None
    return (stem, str(capability))


def stem_columns_for_surfaces(
    vault: LoadedVault, surface_item_ids: Mapping[str, str]
) -> dict[str, tuple[str, str]]:
    """surface id -> ``(stem_id, capability)`` for the surfaces that are stem parts.

    ``surface_item_ids`` maps a surface to the practice item it renders; the
    caller owns that mapping because it differs by administration lane, and
    inventing one here would make this module guess at a join it does not own.

    Surfaces whose item is not a stem part are ABSENT from the result rather than
    mapped to ``None``: ``familiarity._stem_edge`` treats absence as "the stem
    rule has no opinion", which is the correct reading and keeps the pre-A2
    behaviour exactly for every other surface.
    """

    columns: dict[str, tuple[str, str]] = {}
    for surface_id, item_id in surface_item_ids.items():
        item = vault.practice_items.get(str(item_id))
        if item is None:
            continue
        column = stem_column_for_item(item)
        if column is not None:
            columns[str(surface_id)] = column
    return columns


def stem_parts(vault: LoadedVault) -> dict[str, list[PracticeItem]]:
    """stem id -> its parts, ordered by ``part_index`` then item id.

    Deterministic ordering so a report over stems reads the same twice. Items
    with no ``laddered_stem`` block sort by id after those that have one, since
    they have no declared position in the ladder.
    """

    grouped: dict[str, list[PracticeItem]] = {}
    for item in vault.practice_items.values():
        stem = stem_id_for_item(item)
        if not stem:
            continue
        grouped.setdefault(stem, []).append(item)
    return {
        stem: sorted(
            parts,
            key=lambda part: (
                part.laddered_stem.part_index if part.laddered_stem is not None else 1 << 30,
                part.id,
            ),
        )
        for stem, parts in sorted(grouped.items())
    }


@dataclass(frozen=True)
class StemShape:
    """One stem's declared shape — how much of a capability ROW it actually fills."""

    stem_id: str
    part_ids: tuple[str, ...]
    capabilities: tuple[str, ...]
    #: Parts declaring no capability. They cannot be placed in a column, so they
    #: are counted and named rather than assigned to one.
    unplaced_parts: tuple[str, ...]

    @property
    def columns_filled(self) -> int:
        return len(self.capabilities)

    @property
    def is_ladder(self) -> bool:
        """A stem is a LADDER only if its parts span >= 2 capability columns.

        A "stem" whose parts all sit at one capability is a set of near-clones on
        one stimulus, which the kinship rule will correctly collapse to ~one
        observation. Naming that case is the point: it is the failure mode of the
        instrument, and it looks identical to success in an item count.
        """

        return self.columns_filled >= 2

    def as_dict(self) -> dict[str, Any]:
        return {
            "stem_id": self.stem_id,
            "part_ids": list(self.part_ids),
            "capabilities": list(self.capabilities),
            "columns_filled": self.columns_filled,
            "is_ladder": self.is_ladder,
            "unplaced_parts": list(self.unplaced_parts),
        }


def stem_shapes(vault: LoadedVault) -> list[StemShape]:
    """The declared shape of every stem in the vault. Report-only."""

    shapes: list[StemShape] = []
    for stem, parts in stem_parts(vault).items():
        capabilities = sorted(
            {str(part.capability) for part in parts if getattr(part, "capability", None)}
        )
        shapes.append(
            StemShape(
                stem_id=stem,
                part_ids=tuple(part.id for part in parts),
                capabilities=tuple(capabilities),
                unplaced_parts=tuple(
                    part.id for part in parts if not getattr(part, "capability", None)
                ),
            )
        )
    return shapes


# ---------------------------------------------------------------------------
# The revert criterion
# ---------------------------------------------------------------------------

#: Metric name. Not on `scoreboard.B5_ORDER` (frozen).
STEM_INDEPENDENCE_METRIC = "laddered_stem_cross_column_agreement"

#: Pairs of each kind below which no claim is made. The comparison needs BOTH
#: populations, so the floor applies to each independently: a within-column rate
#: over two pairs cannot license a statement about a cross-column rate over forty.
MIN_PAIRS_PER_ARM = 4  # decision parameter

#: How much lower cross-column agreement must be than within-column agreement for
#: the independence claim to be supported. Zero would call a one-point difference
#: a success; this asks for a visible gap before the claim is treated as holding.
MIN_INDEPENDENCE_MARGIN = 0.10  # decision parameter


def stem_independence_signal(
    vault: LoadedVault, repository: Repository, *, since: str | None = None
) -> Metric:
    """``laddered_stem_cross_column_agreement``: A2's revert producer.

    DEFINITION
    ----------
    Over every stem with attempted parts, form all unordered pairs of parts the
    learner attempted, and split them:

    * **within-column** — the two parts declare the same capability;
    * **cross-column** — they declare different capabilities.

    A pair *agrees* when both outcomes fall on the same side of 0.5. The metric's
    value is the CROSS-column agreement rate; ``detail.within_column_agreement``
    carries the other, and ``detail.independence_margin`` their difference.

    The instrument claims within > cross. ``detail.verdict`` therefore names one
    of:

    * ``independence_supported`` — margin at or above
      :data:`MIN_INDEPENDENCE_MARGIN`;
    * ``independence_not_supported`` — margin below it: §3.A2's revert
      condition, "cross-column outcomes on one stem correlate as tightly as
      within-column ones";
    * ``insufficient_pairs`` — one of the two arms is too thin to compare.

    WHY AGREEMENT RATES AND NOT A CORRELATION. Standing constraint 1: this is a
    single-learner vault. A correlation coefficient over a handful of pairs is a
    number with a confidence interval covering everything, and §3.A2 explicitly
    asks for this to be measured rather than trusted — so the statistic has to be
    one the available data can actually support.

    THE LOWER BOUND ON HONESTY. Both arms are reported with their pair counts, so
    a reader can see that a margin of 0.4 rests on five pairs. The metric never
    reports a value without both counts beside it.
    """

    parts_by_stem = stem_parts(vault)
    outcomes: dict[str, float] = {}
    for attempt in repository.list_all_attempts():
        if since is not None and str(attempt.get("created_at") or "") < since:
            continue
        correctness = attempt.get("correctness")
        if correctness is None:
            continue
        item_id = str(attempt.get("practice_item_id") or "")
        # Most recent scored attempt per item: a stem's columns are compared as a
        # snapshot of one learner, and an old attempt from before a repair would
        # compare two different learners.
        outcomes[item_id] = float(correctness)
    within = [0, 0]
    cross = [0, 0]
    per_stem: dict[str, dict[str, Any]] = {}
    for stem, parts in parts_by_stem.items():
        attempted = [
            part
            for part in parts
            if part.id in outcomes and getattr(part, "capability", None)
        ]
        stem_within = [0, 0]
        stem_cross = [0, 0]
        for index, first in enumerate(attempted):
            for second in attempted[index + 1 :]:
                agrees = (outcomes[first.id] >= 0.5) == (outcomes[second.id] >= 0.5)
                bucket = (
                    (within, stem_within)
                    if str(first.capability) == str(second.capability)
                    else (cross, stem_cross)
                )
                for target in bucket:
                    target[0] += 1 if agrees else 0
                    target[1] += 1
        if stem_within[1] or stem_cross[1]:
            per_stem[stem] = {
                "within_pairs": stem_within[1],
                "within_agree": stem_within[0],
                "cross_pairs": stem_cross[1],
                "cross_agree": stem_cross[0],
                "attempted_parts": [part.id for part in attempted],
            }
    within_rate = within[0] / within[1] if within[1] else None
    cross_rate = cross[0] / cross[1] if cross[1] else None
    margin = (
        round(within_rate - cross_rate, 6)
        if within_rate is not None and cross_rate is not None
        else None
    )
    detail: dict[str, Any] = {
        "version": LADDERED_STEM_VERSION,
        "stems": len(parts_by_stem),
        "ladders": sum(1 for shape in stem_shapes(vault) if shape.is_ladder),
        "within_column_pairs": within[1],
        "within_column_agreement": round(within_rate, 6) if within_rate is not None else None,
        "cross_column_pairs": cross[1],
        "cross_column_agreement": round(cross_rate, 6) if cross_rate is not None else None,
        "independence_margin": margin,
        "min_pairs_per_arm": MIN_PAIRS_PER_ARM,
        "min_independence_margin": MIN_INDEPENDENCE_MARGIN,
        "by_stem": per_stem,
    }
    if within[1] < MIN_PAIRS_PER_ARM or cross[1] < MIN_PAIRS_PER_ARM:
        detail["verdict"] = "insufficient_pairs"
        return Metric(
            name=STEM_INDEPENDENCE_METRIC,
            availability="no_data",
            value=None,
            numerator=None,
            denominator=cross[1],
            unit="rate",
            denominator_label="cross-column part pairs on one stem the learner attempted",
            note=(
                f"{within[1]} within-column and {cross[1]} cross-column pair(s); "
                f"{MIN_PAIRS_PER_ARM} of each needed before the independence claim "
                "can be checked"
            ),
            detail=detail,
        )
    detail["verdict"] = (
        "independence_supported"
        if margin is not None and margin >= MIN_INDEPENDENCE_MARGIN
        else "independence_not_supported"
    )
    return Metric(
        name=STEM_INDEPENDENCE_METRIC,
        availability="available",
        value=round(cross_rate, 6),  # type: ignore[arg-type]
        numerator=float(cross[0]),
        denominator=float(cross[1]),
        unit="rate",
        denominator_label="cross-column part pairs on one stem the learner attempted",
        note=(
            f"cross-column agreement {cross_rate:.3f} over {cross[1]} pair(s) vs "
            f"within-column {within_rate:.3f} over {within[1]}; margin {margin}; "
            f"verdict {detail['verdict']}"
        ),
        detail=detail,
    )
