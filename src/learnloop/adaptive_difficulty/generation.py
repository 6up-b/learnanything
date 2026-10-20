"""Generation at a feature point, and the re-forecast of a landed commission (spec §7.1, §7.4).

**The contract** (AD2+AD3, switch ``generation_contract``): wherever the
generation path picks a waypoint for an LO, AD's commission draw names the
feature point (§6.1) at the waypoint's capability, for the LO's
highest-weight facet. The commissioned ``RungTarget`` carries the capability,
the point as its task features, and bounds with ``max`` equal to the point on
every dimension, so the existing deterministic gate rejects overshoot. The
prompt drops every difficulty-band instruction and the target payload drops
``recommended_difficulty_band``; the band check is not run. In their place,
:data:`CONTRACT_TEXT`. ``difficulty_source = "llm_estimate"`` stays on the item
for the incumbent; under AD it is only the signal ``z_llm``.

**The re-forecast** (§7.4): when a commissioned item lands (an active item of
the commission's LO at its capability, with the cell's facet and the
commissioned features), AD computes its ``p̄`` with its audited features and
signals, and appends an ``ad_commission_results`` receipt linked to the
commission's selection: ``in_band`` when ``p̄ ∈ [0.55, 0.90]``, else
``realized_out_of_band``. Either way the item joins the pool; the selection
row is never mutated.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping, Sequence
from contextlib import closing
from typing import Any

from learnloop.db.stores import ad_serving as store

from learnloop.adaptive_difficulty import predict as PR
from learnloop.adaptive_difficulty import replay as RP
from learnloop.adaptive_difficulty import selection as S
from learnloop.adaptive_difficulty.successor import generation_contract_on, successor_active

LOG = logging.getLogger(__name__)

CONTRACT_VERSION = "ad_generation_contract_v1"
CONTRACT_TEXT = (
    "Write the item so that it has exactly these features. Do not make it easier or harder than these features "
    "imply; difficulty is measured from the learner's answers. Separately, give your estimate `difficulty` in [0,1] "
    "of how hard this item is for a typical learner studying this topic. It is recorded as one weighted signal whose "
    "weight is learned from this learner's answers; it is not the item's difficulty."
)
WAYPOINT_CLAUSE = ("NEVER change the waypoint (capability, response form, transfer, span, scaffolding) to change "
                   "difficulty.")
SOURCE = "ad_commission"
MODELLED = ("complexity", "transfer", "scaffolding", "span", "response")


class ProtectedRequest(ValueError):
    """A commissioned generation request quotes withheld material: it is not sent (A8)."""


class CommissionedRequestGuard:
    """The authoring call's material view and send-time revalidation (fix round 9, R2).

    ``vault_view(vault, repository)`` is called with the vault the authoring call reloads: it
    computes AD's material view of THAT vault (the predicate as it stands at send time) and returns
    the vault as the view sees it, so the authoring context is built from visible items only.
    Calling the guard with the serialized request refuses it (:class:`ProtectedRequest`, logged)
    when it quotes a withheld item's id or stem, or a facet or surface family only withheld
    material names, or when the predicate is unavailable. Nothing is sent then."""

    def __init__(self) -> None:
        self.view: Any = None
        #: The source identities ``(extraction_id, span_id or None)`` the request grounds itself in
        #: beyond its authoring context's own refs (cross-source grounding spans; fix round 11, F34).
        self.sources: list[tuple[str, str | None]] = []

    def ground(self, sources: Sequence[tuple[Any, Any]]) -> None:
        """Register grounding spans the request quotes: each is revalidated at every dispatch."""

        self.sources.extend((str(extraction), None if span is None else str(span)) for extraction, span in sources)

    def vault_view(self, vault: Any, repository: Any) -> Any:
        from learnloop.adaptive_difficulty.material_view import material_view

        self.view = material_view(vault, repository)
        return self.view.vault_view()

    def __call__(self, request_text: str, sources: Sequence[tuple[Any, Any]] = ()) -> None:
        """Revalidate one serialized request with protection read afresh (the vault reloaded from
        its root), so a source held out between the first request and a repair, or a predicate
        that became unreadable, refuses the request (fix round 10, R5).

        ``sources``: the source identities the request's context quotes (its source refs); with the
        grounding spans registered by :meth:`ground`, each is judged against the fresh protection,
        so a span held out since the request was built refuses it, whether or not any practice item
        derives from it (Codex verify F34, fix round 11)."""

        from contextlib import closing

        from learnloop.db.connection import connect
        from learnloop.vault.loader import load_vault

        from learnloop.adaptive_difficulty.material_view import material_view

        if self.view is None:
            raise ProtectedRequest("the commissioned request was built without AD's material view")
        fresh = material_view(load_vault(self.view.vault.root), self.view.repository)
        with closing(connect(fresh.repository.sqlite_path, read_only=True)) as connection:
            leaks = fresh.request_leaks(request_text, connection)
        for extraction, span in [*self.sources, *sources]:
            if fresh.material_withheld(extraction, span):
                leaks.append(f"source {extraction}/{span}" if span is not None else f"source {extraction}")
        if leaks:
            LOG.warning("AD commissioned generation request refused: it quotes withheld material (%s)",
                        "; ".join(leaks))
            raise ProtectedRequest("the generation request quotes withheld material: " + "; ".join(leaks))


def contract_on(config: Any) -> bool:
    return generation_contract_on(config)


def lo_cell_facet(view: Any, learning_object_id: str) -> str | None:
    """The LO's highest-weight facet (summed item weights), ties by facet id.

    ``view``: the operation's material view. A withheld item never steers generation (A8; Codex
    verify F17's audit, F21): it adds no facet and no weight. With the predicate unavailable the
    view is empty, so only the LO's authored facets remain, unweighted."""

    from learnloop.adaptive_difficulty.relatedness import lo_facets

    vault = view.vault
    lo = vault.learning_objects.get(learning_object_id)
    if lo is None:
        return None
    own = view.items(learning_object_id=learning_object_id)
    facets = lo_facets(view, lo)
    if not facets:
        # An LO whose every item is retired still has its items' facets: the cell whose pool is
        # empty, and so has no slot, is exactly the one generation must commission (§6.1).
        facets = sorted({facet for item in own for facet in PR.facet_weights(vault, item)})
    if not facets:
        return None
    weight = {facet: 0.0 for facet in facets}
    for item in own:
        for facet, value in PR.facet_weights(vault, item).items():
            if facet in weight:
                weight[facet] += value
    return sorted(weight.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]


def rung_features(point: Mapping[str, Any]) -> dict[str, Any]:
    """The commissioned point as a ``RungTarget``'s task features (the five audited dimensions,
    and ``tools`` only when it differs from the closed-book reference)."""

    features = {dim: point[dim] for dim in MODELLED if dim in point}
    tools = point.get("tools")
    if tools and set(tools) & {"open_book", "references"}:
        features["tools"] = list(tools)
    return features


def commission_point(vault: Any, repository: Any, *, learning_object_id: str, incumbent: Any,
                     now: str, selection_id: str | None = None,
                     view: Any = None) -> tuple[dict[str, Any], str, str] | None:
    """Under ``generation_contract``: ``(features, capability, selection id)`` of the commissioned
    point for the LO's cell at the incumbent waypoint's capability (the open commission, else a new
    commission draw). The generation path builds its ``RungTarget`` from it, with ``max`` equal to
    the point on every dimension.

    ``selection_id``: a named open commission of the LO (a serve-time commission's background
    generation, Codex review F5): its own point and capability, never a new draw; None once it
    has landed or when it is not the LO's."""

    if not contract_on(vault.config) or incumbent is None:
        return None
    from learnloop.adaptive_difficulty.material_view import material_view

    # The generation's material view (the caller's, or computed once here: A8). Unavailable, AD
    # commissions nothing and generation keeps its predecessor's target.
    view = material_view(vault, repository, view)
    if not view.available:
        return None
    if selection_id is not None:
        with repository.atomic():
            row = next((row for row in view.open_commissions(repository.connection(), now=now)
                        if str(row["id"]) == str(selection_id)), None)
        if row is None or row.get("learning_object_id") != learning_object_id or not row.get("chosen_point"):
            return None
        return rung_features(row["chosen_point"]), str(row["cell_capability"]), str(row["id"])
    capability = str(getattr(incumbent, "capability", "") or "")
    facet = lo_cell_facet(view, learning_object_id)
    if not capability or facet is None or capability == "coordination":
        return None
    lo = vault.learning_objects.get(learning_object_id)
    subject = (list(getattr(lo, "subjects", None) or []) or ["default"])[0] if lo is not None else "default"
    with repository.atomic():
        connection = repository.connection()
        for row in view.open_commissions(connection, now=now):
            if row.get("cell_facet") == facet and row.get("cell_capability") == capability and row.get("chosen_point"):
                return rung_features(row["chosen_point"]), capability, str(row["id"])
        snapshot = RP.snapshot(vault, repository, connection=connection, view=view)
        from learnloop.adaptive_difficulty.serving import commission_draw, view_for

        from learnloop.db.scopes import current_ingest_job_id

        state_view, view_name = view_for(snapshot, vault.config, learning_object_id)
        # The durable job generating now, if any (a practice-expansion job): its finish, not the
        # draw, starts the commission's expiry (Codex verify F14).
        selection_id = commission_draw(vault, repository, snapshot, state_view, view_name,
                                       learning_object_id=learning_object_id, subject=subject, facet=facet,
                                       capability_name=capability, key=f"generation:{learning_object_id}:{now}",
                                       now=now, generating_job_id=current_ingest_job_id(repository.sqlite_path))
        if selection_id is None:
            return None
        row = store.selection(connection, selection_id)
    if row is None or not row.get("chosen_point"):
        return None
    return rung_features(row["chosen_point"]), capability, selection_id


def goal_focus_facets(vault: Any, repository: Any, *, scope: Sequence[str], target_recall: float,
                      view: Any) -> list[str]:
    """Under the generation contract, the goal's facets a generation request focuses on (Codex
    verify F37, fix round 11): those whose AD forecast of an unassisted success at the retrieval
    entry point sits below the goal's ``target_recall``. Everything is read through ``view``: the
    LOs' visible facets and AD's own state on visible evidence, never the incumbent's goal
    projection (which counts answers AD withholds). The predecessor's path keeps that projection."""

    from learnloop.db.connection import connect

    if not view.available:
        return []
    out: set[str] = set()
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        snapshot = RP.snapshot(vault, repository, connection=connection, view=view)
        point = S.entry_point("retrieval") or {}
        for lo_id in sorted(set(scope)):
            lo = vault.learning_objects.get(lo_id)
            if lo is None:
                continue
            subject = (list(getattr(lo, "subjects", None) or []) or ["default"])[0]
            for facet in view.lo_facets(lo):
                spec = PR.point_spec(point, learning_object_id=lo_id, subject=subject, facet=facet,
                                     capability_name="retrieval")
                if PR.predict(snapshot.subject, spec).p_bar < float(target_recall):
                    out.add(facet)
    return sorted(out)


def serve_commissions(connection: Any, *, view: Any, now: str | None = None) -> list[dict[str, Any]]:
    """The open commissions a serve draw made (§6.1, "at a serve draw"): those the generation
    path drew for itself are generated by that path, so only these need a job of their own. An
    expired commission is not open (``store.open_commissions``), so it is never queued again.
    ``view``: the material view (a landing of a withheld item closes nothing)."""

    return [row for row in view.open_commissions(connection, now=now)
            if ":serve:" in str(row.get("decision_key") or "") and row.get("chosen_point")
            and row.get("learning_object_id")]


def schedule_commission_generation(vault: Any, repository: Any,
                                   enqueue: Callable[[str, str], Any] | None) -> list[str]:
    """§6.1 "The chosen point is commissioned for generation and runs in the background"
    (Codex review F5): after a serve commits, each open serve-time commission's generation is
    queued on the vault's durable job queue, ``enqueue(commission_id, learning_object_id)``.

    The queue names the batch by the commission, so a commission is generated once however
    often this runs; a commission whose job was never queued (a crash between the serve and
    this call) is queued by the next call, which is what makes it resumable. The job writes one
    item at the commission's point through the ordinary generation path, its spend, fencing and
    gates; the item's landing is recorded at a later serve (§7.4). Returns the commissions
    handed to ``enqueue``; never raises (scheduling never fails a serve)."""

    if enqueue is None or not successor_active(vault.config) or not contract_on(vault.config):
        return []
    try:
        from learnloop.db.connection import connect

        from learnloop.adaptive_difficulty.material_view import material_view

        view = material_view(vault, repository)
        if not view.available:
            return []  # nothing is queued while the held-out predicate is unavailable (A8)
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            if not store.has_table(connection, store.SELECTIONS):
                return []
            rows = serve_commissions(connection, view=view)
    except Exception:  # noqa: BLE001 - scheduling never fails a serve
        LOG.warning("AD commissions not read for generation", exc_info=True)
        return []
    queued: list[str] = []
    for row in rows:
        try:
            enqueue(str(row["id"]), str(row["learning_object_id"]))
            queued.append(str(row["id"]))
        except Exception:  # noqa: BLE001 - the next call retries it
            LOG.warning("AD commission %s not queued for generation", row["id"], exc_info=True)
    return queued


def _cells(vault: Any, item: Any) -> list[tuple[str, str]]:
    """The cells a landed (active) item belongs to: each of its facets at its capability."""

    if getattr(item, "status", "active") != "active":
        return []
    capability = PR.capability(item)
    return [(str(facet), str(capability)) for facet, weight in sorted(PR.facet_weights(vault, item).items())
            if weight > 0]


def _matches_point(features: Any, row: Mapping[str, Any]) -> bool:
    """Whether the landing's realized features are the commission's requested point (recorded,
    never a condition of ownership: Codex verify F15, round 6). ``features`` is the one resolved
    (audited) mapping the receipt records and the re-forecast reads (Codex verify F18), never the
    item's stamp."""

    point = row.get("chosen_point") or {}
    if not isinstance(features, Mapping):
        return False
    return all(features.get(dim) == point.get(dim) for dim in MODELLED if dim in point)


def _at_or_after(stamp: str, other: str) -> bool:
    left, right = store.instant(stamp), store.instant(other)
    return left >= right if left is not None and right is not None else stamp >= other


def landing_owner(vault: Any, item: Any, commissions: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    """The commission that owns a landed item: of the commissions of the item's cells drawn at or
    before it landed, the last in draw order (``commissions`` is in ``(created_at, rowid)`` order,
    a total order even within one second). Ownership is by cell and order only, never by feature
    match (Codex verify F15, round 6); None when no commission of its cells preceded it."""

    created = str(getattr(item, "created_at", "") or "")
    cells = set(_cells(vault, item))
    if not created or not cells:
        return None
    owner = None
    for row in commissions:
        if (str(row.get("cell_facet")), str(row.get("cell_capability"))) not in cells:
            continue
        if not _at_or_after(created, str(row.get("created_at") or "")):
            continue
        owner = row
    return owner


def record_landed_commissions(vault: Any, repository: Any, connection: Any, *, now: str,
                              view: Any = None) -> list[str]:
    """§7.4: append an ``ad_commission_results`` receipt for each item that landed in a commissioned
    cell.

    Ownership is by cell and order (Codex verify F15, F16): an active item belongs to the commission
    of its cells that was latest when it landed (:func:`landing_owner`), whether that commission is
    open, expired or superseded now, and whether or not the item's realized features are the point
    it asked for. The receipt records the realized features and their re-forecast, with
    ``features_match`` saying whether they are the requested point and ``landed_after_expiry``
    whether the commission had expired. Each item has at most one receipt, enforced by
    ``UNIQUE(practice_item_id)``: an item that already has one is skipped, so the first attribution
    is final (a commission drawn later in the same second as the landing never takes it over). An
    item that landed before any commission of its cells is not a commissioned landing. Reads only;
    content and evidence are untouched."""

    from learnloop.adaptive_difficulty.material_view import material_view

    if not successor_active(vault.config) or not store.has_table(connection, store.COMMISSION_RESULTS):
        return []
    commissions = [row for row in store.commissions_in_draw_order(connection) if row.get("chosen_point")]
    if not commissions:
        return []
    # A8 (Codex verify F17): reconciliation reads items only through the operation's material view,
    # so a protected item (held-out material, an exam reservation) is never read here, before
    # ownership, forecasting or a receipt, and never closes, supersedes or receipts a commission.
    # With the predicate unavailable the view is empty and nothing is reconciled (fail closed): the
    # commissions stay open until a reconciliation that can tell.
    view = material_view(vault, repository, view)
    if not view.available:
        return []
    receipted = {str(row["practice_item_id"]) for row in store.commission_results(connection)}
    constants = S.constants_from_config(vault.config)
    written: list[str] = []
    snapshot = None
    for item in view.items():
        if str(item.id) in receipted or view.covers(item):
            continue
        row = landing_owner(vault, item, commissions)
        if row is None:
            continue
        if snapshot is None:
            snapshot = RP.snapshot(vault, repository, connection=connection, view=view)
        from learnloop.adaptive_difficulty.feature_audit import item_revision
        from learnloop.adaptive_difficulty.serving import view_for

        state_view, _name = view_for(snapshot, vault.config, item.learning_object_id)
        content_hash, _json = item_revision(item)
        spec = PR.current_spec(vault, connection, item, at=now, view=view,
                               loadings=snapshot.events.structure.loadings(content_hash, RP.days(now)))
        p_bar = PR.predict(state_view, spec, band=constants.band).p_bar
        in_band = constants.overlap[0] <= p_bar <= constants.overlap[1]
        created = str(getattr(item, "created_at", "") or "")
        # One resolved mapping per landing (Codex verify F18): the forecast read it, the receipt
        # records it, and ``features_match`` compares it.
        realized = dict(spec.features or {})
        result = store.insert_commission_result(connection, {
            "selection_id": row["id"], "practice_item_id": str(item.id), "content_hash": content_hash,
            "features": realized, "p_bar": round(p_bar, 12),
            "status": "in_band" if in_band else "realized_out_of_band", "state_hash": snapshot.state_hash(),
            "features_match": 1 if _matches_point(realized, row) else 0,
            "landed_after_expiry": 1 if store.landed_after_expiry(connection, row, created) else 0,
            "created_at": now,
        })
        if result is not None:
            written.append(result)
            receipted.add(str(item.id))
    return written


__all__ = [
    "CONTRACT_TEXT",
    "CommissionedRequestGuard",
    "ProtectedRequest",
    "goal_focus_facets",
    "CONTRACT_VERSION",
    "SOURCE",
    "WAYPOINT_CLAUSE",
    "commission_point",
    "landing_owner",
    "contract_on",
    "lo_cell_facet",
    "record_landed_commissions",
    "rung_features",
    "schedule_commission_generation",
    "serve_commissions",
]
