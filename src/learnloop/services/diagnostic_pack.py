"""P2 DIAGNOSTIC track -- the pre-authored diagnostic pack + bounded baseline
(spec_p2_narrow_golden_path §5.1, §5.2, §5.3, §12.2; design B.4; migration 083).

The pack is a bounded (2-4) set of reviewed, diagnostic-purpose P1 cards covering the
nearest action-relevant alternatives for ONE reviewed blueprint version. Provenance
mirrors blueprint review (U-028): a card is a reviewed artifact (a deterministic stub
in tests, ``golden_path_fixture.stub_diagnostic_pack``) and NOTHING serves as an
instrument until the owner admits it. At diagnostic entry the run pins exactly one
reviewed pack against the goal-contract HEAD version then current.

This module ORCHESTRATES the landed P0/P1 probe-episode machinery -- it mints NO second
posterior, FSRS write, or certification (the §2 non-negotiable). ``enter_baseline``
opens one diagnostic episode via ``probe_episodes.enter_episode`` pinning the
goal-contract version; the robust selection/stop machinery from P0 is already live under
mvp-0.8, so P2 only pins the pack, opens the episode, and records the visible cap.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services.activities import _canonical_hash, _json

# ``version`` parameter: pack spec schema. Registered structural in the P0 registry.
PACK_SPEC_SCHEMA_VERSION = 1

# decision parameter -- the §5.2 visible-administration cap band (2-4). Registered
# heuristic in the P0 decision-parameter registry (design §E). A requested cap is
# clamped into this band; the episode's own robust stopping rules do the rest.
BASELINE_VISIBLE_CAP = (2, 4)


class InvalidPack(Exception):
    """A pack card cannot be admitted: it is out of the blueprint's bounds, or a
    plausible grader/likelihood perturbation would change the recommended repair
    without a disclosure/abstention path (§5.1)."""


@dataclass(frozen=True)
class PackCard:
    card_slug: str
    coverage: tuple[str, ...]
    admission_status: str
    instrument_ref: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "card_slug": self.card_slug,
            "coverage": list(self.coverage),
            "admission_status": self.admission_status,
            "instrument_ref": self.instrument_ref,
        }


@dataclass(frozen=True)
class PackRecord:
    pack_id: str
    pack_slug: str
    blueprint_version_id: str
    status: str
    content_hash: str
    cards: tuple[PackCard, ...] = ()
    minted: bool = True

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["cards"] = [c.as_dict() for c in self.cards]
        return data


# ---------------------------------------------------------------------------
# Deterministic assembly (§5.1) -- register -> admit -> review -> activate
# ---------------------------------------------------------------------------

def _canonical_cards(cards: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for card in cards:
        out.append(
            {
                "card_slug": card["card_slug"],
                "coverage": sorted(str(c) for c in (card.get("coverage") or [])),
                "instrument_ref": card.get("instrument_ref"),
            }
        )
    out.sort(key=lambda c: c["card_slug"])
    return out


def pack_content_hash(
    *, pack_slug: str, blueprint_version_id: str, cards: Sequence[Mapping[str, Any]]
) -> str:
    """The timestamp/id-independent content identity of a pack (§12.8 determinism)."""

    return _canonical_hash(
        {
            "schema_version": PACK_SPEC_SCHEMA_VERSION,
            "pack_slug": pack_slug,
            "blueprint_version_id": blueprint_version_id,
            "cards": _canonical_cards(cards),
        }
    )


def _reject_unstable_repair(card: Mapping[str, Any]) -> None:
    """§5.1 admission gate: reject a card whose recommended repair is unstable under
    plausible grader/likelihood perturbations unless it carries a disclosure/abstention
    path. The P0 ±0.15 perturbation engine (probe_robust/identifiability) is the live
    check on the served instrument; at admission time the reviewed artifact declares its
    stability, so a card flagged ``repair_unstable`` without a ``disclosure_path`` fails
    closed here -- the deterministic, owner-reviewable projection of that check."""

    if card.get("repair_unstable") and not card.get("disclosure_path"):
        raise InvalidPack(
            f"card {card.get('card_slug')!r}: repair unstable under perturbation with no "
            "disclosure/abstention path (§5.1)"
        )


def assemble_pack(
    repository: Repository,
    *,
    pack_slug: str,
    blueprint_version_id: str,
    cards: Sequence[Mapping[str, Any]],
    clock: Clock | None = None,
) -> PackRecord:
    """Assemble a diagnostic pack from admitted-candidate diagnostic-purpose cards for a
    reviewed blueprint version (§5.1). Deterministic + idempotent: two assemblies with
    the same cards produce identical content hashes and the same pack row. Cards enter
    as ``candidate`` (nothing is an instrument until the owner admits it)."""

    if not (2 <= len(cards) <= 4):
        raise InvalidPack(f"pack must carry 2-4 cards, got {len(cards)} (§5.1)")
    for card in cards:
        _reject_unstable_repair(card)

    content_hash = pack_content_hash(
        pack_slug=pack_slug, blueprint_version_id=blueprint_version_id, cards=cards
    )
    result = repository.ensure_diagnostic_pack(
        pack_slug=pack_slug,
        blueprint_version_id=blueprint_version_id,
        content_hash=content_hash,
        clock=clock,
    )
    pack_id = result["pack"]["id"]
    for card in _canonical_cards(cards):
        repository.register_diagnostic_pack_card(
            pack_id=pack_id,
            card_slug=card["card_slug"],
            coverage_json=_json(card["coverage"]),
            instrument_ref=card.get("instrument_ref"),
            content_hash=_canonical_hash(card),
            clock=clock,
        )
    return _load_pack(repository, pack_id, minted=not result["already_exists"])


def admit_pack_card(
    repository: Repository,
    *,
    pack_id: str,
    card_slug: str,
    checks: Mapping[str, Any] | None = None,
    author: str = "owner",
    clock: Clock | None = None,
) -> PackRecord:
    """Owner admits one reviewed card into the pack (U-028). Append-only event."""

    repository.set_diagnostic_pack_card_admission(
        pack_id=pack_id,
        card_slug=card_slug,
        admission_status="admitted",
        detail_json=_json(dict(checks)) if checks else None,
        author=author,
        clock=clock,
    )
    return _load_pack(repository, pack_id)


def reject_pack_card(
    repository: Repository,
    *,
    pack_id: str,
    card_slug: str,
    reason: str,
    author: str = "owner",
    clock: Clock | None = None,
) -> PackRecord:
    repository.set_diagnostic_pack_card_admission(
        pack_id=pack_id,
        card_slug=card_slug,
        admission_status="rejected",
        detail_json=_json({"reason": reason}),
        author=author,
        clock=clock,
    )
    return _load_pack(repository, pack_id)


def review_pack(
    repository: Repository,
    *,
    pack_id: str,
    checks: Mapping[str, Any] | None = None,
    author: str = "owner",
    clock: Clock | None = None,
) -> PackRecord:
    """Owner marks the pack reviewed once every card is admitted (§5.1)."""

    cards = repository.diagnostic_pack_cards_for(pack_id)
    if not cards or any(c["admission_status"] != "admitted" for c in cards):
        raise InvalidPack("cannot review a pack with un-admitted cards (§5.1)")
    repository.transition_diagnostic_pack(
        pack_id=pack_id,
        status="reviewed",
        kind="reviewed",
        detail_json=_json(dict(checks)) if checks else None,
        author=author,
        clock=clock,
    )
    return _load_pack(repository, pack_id)


def activate_pack(
    repository: Repository,
    *,
    pack_id: str,
    author: str = "owner",
    clock: Clock | None = None,
) -> PackRecord:
    pack = repository.diagnostic_pack(pack_id)
    if pack is None or pack["status"] not in ("reviewed", "active"):
        raise InvalidPack(
            f"cannot activate pack in status {pack['status'] if pack else None!r}"
        )
    if pack["status"] == "reviewed":
        repository.transition_diagnostic_pack(
            pack_id=pack_id, status="active", kind="activated", author=author, clock=clock
        )
    return _load_pack(repository, pack_id)


# ---------------------------------------------------------------------------
# Pinning + baseline entry (§5.2) -- composes probe_episodes
# ---------------------------------------------------------------------------

def clamp_visible_cap(requested: int | None = None) -> int:
    lo, hi = BASELINE_VISIBLE_CAP
    if requested is None:
        return hi
    return max(lo, min(hi, int(requested)))


def pin_pack_to_run(
    repository: Repository,
    *,
    run_id: str,
    pack_id: str,
    goal_contract_version_id: str | None = None,
    visible_cap: int | None = None,
    probe_episode_id: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Pin exactly one reviewed pack to the run at diagnostic entry (§5.2). The pin
    binds the goal-contract version then current -- if not supplied, read from the run.
    Idempotent: one pin per run."""

    pack = repository.diagnostic_pack(pack_id)
    if pack is None:
        raise InvalidPack(f"unknown diagnostic pack: {pack_id}")
    if pack["status"] not in ("reviewed", "active"):
        raise InvalidPack(f"cannot pin an unreviewed pack (status {pack['status']!r})")
    run = repository.golden_path_run(run_id)
    if run is None:
        raise InvalidPack(f"unknown golden-path run: {run_id}")
    gc_version = goal_contract_version_id or run["goal_contract_version_id"]
    result = repository.pin_diagnostic_pack(
        run_id=run_id,
        pack_id=pack_id,
        goal_contract_version_id=gc_version,
        visible_cap=clamp_visible_cap(visible_cap),
        probe_episode_id=probe_episode_id,
        clock=clock,
    )
    return result["pin"]


def enter_baseline(
    vault: Any,
    repository: Repository,
    *,
    run_id: str,
    learning_object_id: str,
    pack_id: str,
    visible_cap: int | None = None,
    clock: Clock | None = None,
    ai_client: object | None = None,
) -> dict[str, Any]:
    """Open one bounded diagnostic episode for the run and pin the pack (§5.2).

    Composition-only: the actual measurement is the landed ``probe_episodes`` machinery
    (idempotent per LO -- an already-open episode is reused). P2 supplies the run's
    goal_id so the episode pins the goal-contract version, records the pack pin against
    that version, and stamps the visible cap. No new posterior is minted here.
    """

    from learnloop.services import probe_episodes as PE

    run = repository.golden_path_run(run_id)
    if run is None:
        raise InvalidPack(f"unknown golden-path run: {run_id}")

    episode = PE.enter_episode(
        vault,
        repository,
        learning_object_id,
        trigger="initial",
        origin="golden_path_baseline",
        goal_id=run["goal_id"],
        clock=clock,
        ai_client=ai_client,
    )
    pin = pin_pack_to_run(
        repository,
        run_id=run_id,
        pack_id=pack_id,
        goal_contract_version_id=run["goal_contract_version_id"],
        visible_cap=visible_cap,
        probe_episode_id=episode.id,
        clock=clock,
    )
    return {"pin": pin, "episode_id": episode.id, "episode_status": episode.status}


# ---------------------------------------------------------------------------
# Boundary view (§5.3) -- a VIEW over the blueprint + evidence, no mastery table
# ---------------------------------------------------------------------------

BOUNDARY_CELL_STATES: frozenset[str] = frozenset(
    {"demonstrated", "developing", "untested", "weak", "contested"}
)


def _recipe_cells(spec: Mapping[str, Any]) -> list[tuple[str, str]]:
    """The ordered, de-duplicated (facet, capability) cells of the blueprint's
    solution recipes (§5.3). Shared by the view and the assessment coverage."""

    cells: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for recipe in spec.get("solution_recipes") or []:
        components = list(recipe.get("all_of") or []) + list(recipe.get("any_of") or [])
        integ = recipe.get("integration")
        if integ:
            components.append(integ)
        for comp in components:
            facet = comp.get("facet")
            capability = comp.get("capability")
            if facet is None or capability is None:
                continue
            key = (facet, capability)
            if key in seen:
                continue
            seen.add(key)
            cells.append(key)
    return cells


def _baseline_evidence_projection(
    repository: Repository, run: Mapping[str, Any], spec: Mapping[str, Any]
) -> dict[tuple[str, str], dict[str, Any]]:
    """Project the pinned baseline episode's observations onto the recipe cells (§5.3).

    A projection over LANDED P0/P1 evidence -- NO new mastery table and no new certainty
    math. Each observation carries its instrument's target facets, its coarse rubric
    outcome, its qualifying (``eligible_for_completion``) flag, and its quarantine/belief
    status; those decide the cell label:

    - a quarantined / non-belief-updating observation with no clean evidence -> ``contested``
      (linked to its measurement receipt, §5.3);
    - clean passes with a qualifying observation -> ``demonstrated``; passes without a
      qualifying observation -> ``developing``;
    - clean fails -> ``weak``; mixed pass/fail -> ``developing``.

    Cells with no touching observation are absent here (the caller defaults them
    ``untested``). ``demonstrated`` reuses the P0 ``DEMONSTRATED_CLAIM_CERTAINTY`` floor
    on the coarse rubric fraction -- the same knob the boundary-diff label uses."""

    pin = repository.diagnostic_pack_pin_for_run(run["id"])
    episode_id = pin.get("probe_episode_id") if pin else None
    if not episode_id:
        return {}
    rows = repository.probe_observations_for_episode(episode_id)
    if not rows:
        return {}

    from learnloop.services.golden_path_assessment import DEMONSTRATED_CLAIM_CERTAINTY

    max_points = float((spec.get("rubric") or {}).get("max_points") or 0.0)
    per_token: dict[str, dict[str, Any]] = {}
    for row in rows:
        obs = row["observation"]
        grader_channel = obs.grader_channel or {}
        quarantined = (
            str(grader_channel.get("quarantine_state") or "").lower() in ("quarantined", "review")
            or not obs.updates_belief
        )
        score = row.get("rubric_score")
        fraction = (float(score) / max_points) if (score is not None and max_points > 0) else 0.0
        passed = fraction >= DEMONSTRATED_CLAIM_CERTAINTY
        for token in (str(f) for f in (row.get("target_facets") or [])):
            agg = per_token.setdefault(
                token, {"pass": 0, "fail": 0, "qualifying": 0, "quarantined": 0, "receipt": None}
            )
            if quarantined:
                agg["quarantined"] += 1
                agg["receipt"] = agg["receipt"] or obs.id
            elif passed:
                agg["pass"] += 1
            else:
                agg["fail"] += 1
            if obs.eligible_for_completion:
                agg["qualifying"] += 1

    projection: dict[tuple[str, str], dict[str, Any]] = {}
    for facet, capability in _recipe_cells(spec):
        matched = [per_token[t] for t in (facet, capability) if t in per_token]
        if not matched:
            continue
        passes = sum(m["pass"] for m in matched)
        fails = sum(m["fail"] for m in matched)
        quarantined = sum(m["quarantined"] for m in matched)
        qualifying = sum(m["qualifying"] for m in matched)
        receipt = next((m["receipt"] for m in matched if m["receipt"]), None)
        if passes == 0 and fails == 0 and quarantined:
            status, cell_receipt = "contested", receipt
        elif passes and not fails:
            status, cell_receipt = ("demonstrated" if qualifying else "developing"), None
        elif fails and not passes:
            status, cell_receipt = "weak", None
        else:  # mixed pass/fail
            status, cell_receipt = "developing", None
        projection[(facet, capability)] = {
            "status": status,
            # Reliability-aware read fields (P0 read-DTO rule): baseline diagnostic
            # evidence is heuristic/provisional -- it never claims calibrated language.
            "claim_language": "provisional",
            "calibration_status": "heuristic",
            "measurement_receipt": cell_receipt,
        }
    return projection


def boundary_view(repository: Repository, *, run_id: str) -> dict[str, Any]:
    """Render only the facet x capability cells relevant to the target blueprint
    (§5.3), projected over the pinned baseline episode's P0/P1 evidence.

    'untested' is the default (not 'cannot'); 'weak' describes observed performance
    under a named context; a 'contested' cell links to its measurement receipt. This
    never mints a new mastery table -- it folds the landed probe observations onto the
    reviewed recipe cells. A cell no baseline observation touched stays 'untested'."""

    run = repository.golden_path_run(run_id)
    if run is None:
        raise InvalidPack(f"unknown golden-path run: {run_id}")
    version = repository.task_blueprint_version(run["blueprint_version_id"])
    import json as _json_mod

    spec = _json_mod.loads(version["spec_json"]) if version else {}
    projection = _baseline_evidence_projection(repository, run, spec)
    cells: list[dict[str, Any]] = []
    for facet, capability in _recipe_cells(spec):
        cell: dict[str, Any] = {"facet": facet, "capability": capability, "status": "untested"}
        data = projection.get((facet, capability))
        if data is not None:
            cell["status"] = data["status"]
            cell["claim_language"] = data["claim_language"]
            cell["calibration_status"] = data["calibration_status"]
            if data["status"] == "contested":
                cell["measurement_receipt"] = data["measurement_receipt"]
        cells.append(cell)
    return {"run_id": run_id, "cells": cells}


def snapshot_baseline_boundary(
    repository: Repository, *, run_id: str, clock: Clock | None = None
) -> dict[str, Any]:
    """Persist the baseline boundary view as a run artifact at diagnostic-segment close
    (§5.3 / §8.4). Idempotent: the first snapshot wins so the ``before`` side of the
    post-assessment ``boundary_diff`` is frozen at the moment instruction began and can
    never be re-projected with post-instruction evidence."""

    existing = repository.latest_golden_path_artifact(run_id, kind="baseline_boundary")
    if existing is not None:
        import json as _json_mod

        return _json_mod.loads(existing["payload_json"])
    view = boundary_view(repository, run_id=run_id)
    repository.append_golden_path_artifact(
        run_id=run_id,
        kind="baseline_boundary",
        payload_json=_json(view),
        idempotency_key=f"baseline_boundary:{run_id}",
        clock=clock,
    )
    return view


def _load_pack(repository: Repository, pack_id: str, *, minted: bool = True) -> PackRecord:
    row = repository.diagnostic_pack(pack_id)
    if row is None:
        raise InvalidPack(f"unknown diagnostic pack: {pack_id}")
    import json as _json_mod

    cards = tuple(
        PackCard(
            card_slug=c["card_slug"],
            coverage=tuple(_json_mod.loads(c["coverage_json"])),
            admission_status=c["admission_status"],
            instrument_ref=c["instrument_ref"],
        )
        for c in repository.diagnostic_pack_cards_for(pack_id)
    )
    return PackRecord(
        pack_id=row["id"],
        pack_slug=row["pack_slug"],
        blueprint_version_id=row["blueprint_version_id"],
        status=row["status"],
        content_hash=row["content_hash"],
        cards=cards,
        minted=minted,
    )
