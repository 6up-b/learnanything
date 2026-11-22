"""Facet belief projections, merge lookups and rebuild receipts.

Owns the facet recall, uncertainty and capability projections and rebuild
receipts. Uses the facet identity store's settled merge rows."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.records import (
    FacetUncertaintyState,
    _CAPABILITY_RESIDUAL_PROJECTION,
    _FACET_CAPABILITY_PROJECTION,
    _FACET_RECALL_PROJECTION,
    _ProjectionTable,
    _facet_uncertainty_state,
    _projection_id,
)
from learnloop.db.attempt_order import LEGACY_ORDER, AttemptOrder
from learnloop.db.row_serialization import _json, _loads
from learnloop.db.stores.facet_identity import settled_merge_rows
from learnloop.db.stores.observation_ledger import (
    load_authoritative_observation_ledger,
    load_canonical_observation_ledger,
)
from learnloop.ids import new_ulid


@dataclass
class _ProjectionChanges:
    vanished: list[int] = field(default_factory=list)
    changed: list[tuple[int, Mapping[str, Any], str]] = field(default_factory=list)
    new: list[Mapping[str, Any]] = field(default_factory=list)

    def __bool__(self) -> bool:
        return bool(self.vanished or self.changed or self.new)


def _projection_changes(
    connection: sqlite3.Connection,
    table: _ProjectionTable,
    cells: Sequence[Mapping[str, Any]],
) -> _ProjectionChanges:
    """Compare a projection with the stored rows, cell by cell.

    A cell's ``created_at`` of ``None`` means "keep the stored one"; a non-null
    one is projected and differs only when the projection moved it.
    """

    projected: dict[tuple[Any, ...], Mapping[str, Any]] = {}
    for cell in cells:
        key = tuple(cell[column] for column in table.key)
        if key in projected:
            # The full DELETE+INSERT this replaces failed on the unique index.
            raise sqlite3.IntegrityError(
                f"UNIQUE constraint failed: {table.name} {dict(zip(table.key, key, strict=True))}"
            )
        projected[key] = cell
    columns = ", ".join((*table.key, *table.values))
    stored = {
        tuple(row[column] for column in table.key): row
        for row in connection.execute(
            f"SELECT rowid AS stored_rowid, {columns}, created_at FROM {table.name}"
        )
    }
    changes = _ProjectionChanges()
    for key, row in stored.items():
        if key not in projected:
            changes.vanished.append(int(row["stored_rowid"]))
    for key, cell in projected.items():
        row = stored.get(key)
        if row is None:
            changes.new.append(cell)
            continue
        created_at = cell["created_at"] if cell.get("created_at") is not None else row["created_at"]
        if created_at != row["created_at"] or any(
            cell[column] != row[column] for column in table.values
        ):
            changes.changed.append((int(row["stored_rowid"]), cell, created_at))
    return changes


def _apply_projection_changes(
    connection: sqlite3.Connection,
    table: _ProjectionTable,
    changes: _ProjectionChanges,
    *,
    now: str,
) -> None:
    # Deletes first, so a new cell can never collide with a vanished one.
    connection.executemany(
        f"DELETE FROM {table.name} WHERE rowid = ?",
        [(rowid,) for rowid in changes.vanished],
    )
    assignments = ", ".join(f"{column} = ?" for column in table.values)
    connection.executemany(
        f"UPDATE {table.name} SET {assignments}, created_at = ?, updated_at = ? WHERE rowid = ?",
        [
            (*(cell[column] for column in table.values), created_at, now, rowid)
            for rowid, cell, created_at in changes.changed
        ],
    )
    columns = (*table.key, *table.values)
    placeholders = ", ".join("?" for _ in range(len(columns) + 2))
    connection.executemany(
        f"INSERT INTO {table.name}({', '.join(columns)}, created_at, updated_at) "
        f"VALUES ({placeholders})",
        [
            (
                *(cell[column] for column in columns),
                cell["created_at"] if cell.get("created_at") is not None else now,
                now,
            )
            for cell in changes.new
        ],
    )


def _write_projection_on_change(
    connection: sqlite3.Connection,
    projections: Sequence[tuple[_ProjectionTable, Sequence[Mapping[str, Any]]]],
    *,
    now: str,
) -> bool:
    """Persist whole projections, writing only the cells that changed.

    Returns whether anything was written. Outside an owning transaction the
    comparison first runs on a read snapshot, so the common no-op takes no
    write lock and commits nothing; when something differs it is compared
    again under ``BEGIN IMMEDIATE`` and applied from that comparison, so a
    writer that committed in between is never applied against stale rowids.
    Inside an owning transaction (``Repository.atomic``) the one comparison
    already runs under its lock.
    """

    def compare() -> list[tuple[_ProjectionTable, _ProjectionChanges]]:
        return [
            (table, _projection_changes(connection, table, cells))
            for table, cells in projections
        ]

    if not connection.in_transaction:
        connection.execute("BEGIN")
        try:
            pending = any(changes for _, changes in compare())
        finally:
            connection.rollback()  # a read snapshot only: nothing to commit
        if not pending:
            return False
        connection.execute("BEGIN IMMEDIATE")
    planned = compare()
    written = False
    for table, changes in planned:
        if changes:
            _apply_projection_changes(connection, table, changes, now=now)
            written = True
    connection.commit()
    return written


@dataclass(frozen=True)
class FacetRecallState:
    id: str
    learning_object_id: str
    facet_id: str
    practice_item_id: str | None
    recall_alpha: float
    recall_beta: float
    recall_mean: float
    recall_variance: float
    independent_evidence_mass: float
    raw_coverage_mass: float
    last_attempt_at: str | None
    last_error_at: str | None
    consecutive_failures: int
    algorithm_version: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class CanonicalFacetRecallState:
    """Canonical shared facet belief (KM2 §7.1), keyed on the post-merge facet id
    and observed capability. ``practice_item_id=None`` is the shared aggregate."""

    id: str
    facet_id: str
    capability_key: str
    practice_item_id: str | None
    recall_alpha: float
    recall_beta: float
    recall_mean: float
    recall_variance: float
    independent_evidence_mass: float
    raw_coverage_mass: float
    last_observed_at: str | None
    last_error_at: str | None
    consecutive_failures: int
    algorithm_version: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class FacetCapabilityEvidence:
    """Capability-sliced certification ledger (KM2 §7.1). A replayable cache
    derived from immutable observations, not a new evidence source."""

    facet_id: str
    capability: str
    direct_positive_mass: float
    direct_negative_mass: float
    embedded_positive_mass: float
    embedded_negative_mass: float
    certification_credit: float
    # A1 guard 2 (migration 141): the split ``certification_credit`` is capped
    # from. ``certification_credit`` stays the ONE number Demonstrated reads;
    # these say how it was earned, so the cap is auditable without re-running
    # the projection.
    direct_certification_credit: float = 0.0
    embedded_certification_credit: float = 0.0
    # A1 guard 1: mass a ``supporting`` target would have earned had the trace
    # shown its facet exercised. Recorded, never silent.
    unexercised_supporting_mass: float = 0.0
    independent_surface_groups: list[str] = field(default_factory=list)
    algorithm_version: str = ""
    created_at: str = ""
    updated_at: str = ""


def _facet_recall_state(row: sqlite3.Row) -> FacetRecallState:
    return FacetRecallState(
        id=row["id"],
        learning_object_id=row["learning_object_id"],
        facet_id=row["facet_id"],
        practice_item_id=row["practice_item_id"],
        recall_alpha=row["recall_alpha"],
        recall_beta=row["recall_beta"],
        recall_mean=row["recall_mean"],
        recall_variance=row["recall_variance"],
        independent_evidence_mass=row["independent_evidence_mass"],
        raw_coverage_mass=row["raw_coverage_mass"],
        last_attempt_at=row["last_attempt_at"],
        last_error_at=row["last_error_at"],
        consecutive_failures=row["consecutive_failures"],
        algorithm_version=row["algorithm_version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _canonical_facet_recall_state(row: sqlite3.Row) -> CanonicalFacetRecallState:
    return CanonicalFacetRecallState(
        id=row["id"],
        facet_id=row["facet_id"],
        capability_key=row["capability_key"],
        practice_item_id=row["practice_item_id"],
        recall_alpha=row["recall_alpha"],
        recall_beta=row["recall_beta"],
        recall_mean=row["recall_mean"],
        recall_variance=row["recall_variance"],
        independent_evidence_mass=row["independent_evidence_mass"],
        raw_coverage_mass=row["raw_coverage_mass"],
        last_observed_at=row["last_observed_at"],
        last_error_at=row["last_error_at"],
        consecutive_failures=row["consecutive_failures"],
        algorithm_version=row["algorithm_version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _facet_capability_evidence(row: sqlite3.Row) -> FacetCapabilityEvidence:
    return FacetCapabilityEvidence(
        facet_id=row["facet_id"],
        capability=row["capability"],
        direct_positive_mass=row["direct_positive_mass"],
        direct_negative_mass=row["direct_negative_mass"],
        embedded_positive_mass=row["embedded_positive_mass"],
        embedded_negative_mass=row["embedded_negative_mass"],
        certification_credit=row["certification_credit"],
        direct_certification_credit=row["direct_certification_credit"],
        embedded_certification_credit=row["embedded_certification_credit"],
        unexercised_supporting_mass=row["unexercised_supporting_mass"],
        independent_surface_groups=[str(g) for g in _loads(row["independent_surface_groups_json"], [])],
        algorithm_version=row["algorithm_version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _capability_residual_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "facet_id": row["facet_id"],
        "capability": row["capability"],
        "active": bool(row["active"]),
        "activation_reason": row["activation_reason"],
        "residual_alpha": row["residual_alpha"],
        "residual_beta": row["residual_beta"],
        "residual_mean": row["residual_mean"],
        "parent_alpha": row["parent_alpha"],
        "parent_beta": row["parent_beta"],
        "parent_mean": row["parent_mean"],
        "divergence": row["divergence"],
        "independent_groups": int(row["independent_groups"]),
        "independent_mass": row["independent_mass"],
        "algorithm_version": row["algorithm_version"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _resolve_merge(facet_id: str, merge_map: Mapping[str, str]) -> str:
    """Follow retired->surviving edges to the terminal survivor.

    Assumes the map is acyclic (enforced at write time by ``insert_facet_merge``);
    a defensive visited-set still guards against a malformed table."""

    seen: set[str] = set()
    current = facet_id
    while current in merge_map and current not in seen:
        seen.add(current)
        current = merge_map[current]
    return current


def _reaches(start: str, target: str, merge_map: Mapping[str, str]) -> bool:
    seen: set[str] = set()
    current = start
    while current in merge_map and current not in seen:
        if current == target:
            return True
        seen.add(current)
        current = merge_map[current]
    return current == target


def _decode_derived_state_rebuild(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["learning_object_ids"] = _loads(payload.pop("learning_object_ids_json"), [])
    if "projection_switches_json" in payload:
        payload["projection_switches"] = _loads(payload.pop("projection_switches_json"), None)
    return payload


class FacetProjectionStoreMixin:

    def facet_ids_with_recall_evidence(self) -> set[str]:
        """Facet ids with legacy per-LO recall evidence (mvp-0.6 first-touch lock).

        Reads only the legacy table on purpose: canonical mvp-0.7 facets are NOT
        first-touch-locked (§3.4 — that would defeat the grace window). They lock
        through the independence gate in ``_facet_independence_locked`` (distinct
        surface groups / independent mass / active-goal scope) instead.
        """

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT DISTINCT facet_id FROM evidence_facet_recall_state"
            ).fetchall()
        return {str(row["facet_id"]) for row in rows}

    def facet_recall_state(
        self,
        learning_object_id: str,
        facet_id: str,
        practice_item_id: str | None = None,
    ) -> FacetRecallState | None:
        with self.connection() as connection:
            if practice_item_id is None:
                row = connection.execute(
                    """
                    SELECT * FROM evidence_facet_recall_state
                    WHERE learning_object_id = ? AND facet_id = ? AND practice_item_id IS NULL
                    """,
                    (learning_object_id, facet_id),
                ).fetchone()
            else:
                row = connection.execute(
                    """
                    SELECT * FROM evidence_facet_recall_state
                    WHERE learning_object_id = ? AND facet_id = ? AND practice_item_id = ?
                    """,
                    (learning_object_id, facet_id, practice_item_id),
                ).fetchone()
        return _facet_recall_state(row) if row is not None else None

    # -- KM2 canonical shared facet state (§7.1) --------------------------------
    # These read/write the canonical `facet_recall_state`, `facet_capability_evidence`,
    # and `facet_merges` tables. They are consumed only under mvp-0.7; the legacy
    # per-LO `evidence_facet_recall_state` methods above stay untouched so mvp-0.6
    # replay reproduces byte-identical state.

    def canonical_facet_recall_states(self) -> list[CanonicalFacetRecallState]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM facet_recall_state ORDER BY facet_id, capability_key, practice_item_id"
            ).fetchall()
        return [_canonical_facet_recall_state(row) for row in rows]

    def canonical_facet_recall_state(
        self,
        facet_id: str,
        capability_key: str = "shared",
        practice_item_id: str | None = None,
    ) -> CanonicalFacetRecallState | None:
        with self.connection() as connection:
            if practice_item_id is None:
                row = connection.execute(
                    """
                    SELECT * FROM facet_recall_state
                    WHERE facet_id = ? AND capability_key = ? AND practice_item_id IS NULL
                    """,
                    (facet_id, capability_key),
                ).fetchone()
            else:
                row = connection.execute(
                    """
                    SELECT * FROM facet_recall_state
                    WHERE facet_id = ? AND capability_key = ? AND practice_item_id = ?
                    """,
                    (facet_id, capability_key, practice_item_id),
                ).fetchone()
        return _canonical_facet_recall_state(row) if row is not None else None

    def facet_capability_evidence(
        self, facet_id: str, capability: str
    ) -> FacetCapabilityEvidence | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM facet_capability_evidence WHERE facet_id = ? AND capability = ?",
                (facet_id, capability),
            ).fetchone()
        return _facet_capability_evidence(row) if row is not None else None

    def facet_capability_evidence_all(self) -> list[FacetCapabilityEvidence]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM facet_capability_evidence ORDER BY facet_id, capability"
            ).fetchall()
        return [_facet_capability_evidence(row) for row in rows]

    def facet_capability_evidence_for_facet(
        self, facet_id: str
    ) -> list[FacetCapabilityEvidence]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM facet_capability_evidence WHERE facet_id = ? ORDER BY capability",
                (facet_id,),
            ).fetchall()
        return [_facet_capability_evidence(row) for row in rows]

    def facet_independence_evidence(self, facet_id: str) -> tuple[int, float]:
        """(#distinct direct surface/correlation groups, independent mass) for the
        independence-gated lock trigger (§3.4). Direct evidence only."""

        groups: set[str] = set()
        for cell in self.facet_capability_evidence_for_facet(facet_id):
            groups.update(cell.independent_surface_groups)
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT COALESCE(SUM(independent_evidence_mass), 0.0) AS mass
                FROM facet_recall_state
                WHERE facet_id = ? AND practice_item_id IS NULL
                """,
                (facet_id,),
            ).fetchone()
        return len(groups), float(row["mass"] if row is not None else 0.0)

    def canonical_observation_ledger(self) -> list[dict[str, Any]]:
        """Every graded attempt in global chronological order with its
        non-superseded grading evidence (KM2 projection input).

        Chronological across LOs so the derived canonical belief state is
        deterministic regardless of per-LO replay order; beta masses accumulate
        additively so only timestamps/consecutive-failures depend on order.  The
        read model is assembled in two bulk queries by ``db.observation_ledger``;
        no query is issued from inside the attempt loop.
        """

        with self.connection() as connection:
            # Hold one read transaction across both scans.  A concurrent grade
            # supersession must be observed wholly before or wholly after the
            # replay snapshot, never as an attempt row from one epoch and
            # evidence rows from another.
            if not connection.in_transaction:
                connection.execute("BEGIN")
            return load_canonical_observation_ledger(connection)

    def canonical_observation_ledger_v2(self, *, order: AttemptOrder = LEGACY_ORDER) -> list[dict[str, Any]]:
        """P0.3 (§4.3) authoritative-events ledger. Extends the mvp-0.7 row with the
        administration, the ACTIVE calibrated grade interpretation/adjudication, the
        grader/calibration lineage, the target-contract pin, and quarantine state.

        The mvp-0.8 projection reads only these authoritative events; the legacy
        summary columns are never replay inputs. The base attempt/evidence shape is
        the byte-identical v1 shape so the projection loop stays shared; the P0.3
        lineage fields are ADDED (never removed) -- projector tests fail if a variant
        omits them (§9.2 bullet 3)."""

        with self.connection() as connection:
            if not connection.in_transaction:
                connection.execute("BEGIN")
            return load_authoritative_observation_ledger(connection, order=order)

    def replace_canonical_facet_state(
        self,
        *,
        recall_rows: Iterable[Mapping[str, Any]],
        capability_rows: Iterable[Mapping[str, Any]],
        algorithm_version: str,
        clock: Clock | None = None,
    ) -> None:
        """Make the canonical belief cache equal a derived projection.

        The canonical state is a pure, order-independent (beta masses accumulate
        additively) projection over the immutable observation ledger, so the
        whole projection is handed in: no per-LO reset can shear a facet shared
        across LOs. Idempotent.

        Write only on change (followups-oct31, fix 1): every load and reload
        re-projects, and almost always to the same values. Each cell is compared
        with the stored row on its value columns; a vanished cell is deleted, a
        new one inserted, a changed one updated with ``updated_at = now``, and an
        unchanged one is not touched. When nothing differs nothing is written at
        all, so a no-op reload leaves the database file (``PRAGMA data_version``)
        unchanged. ``updated_at`` therefore means "this estimate last changed
        then". A recall row's ``created_at`` is projected (its first
        observation's time) and written as projected; a capability row carries
        none, so it keeps the stored one (``now`` when the cell first appears).
        """

        now = utc_now_iso(clock)
        recall_cells = [
            {
                "id": str(
                    state.get("id")
                    or _projection_id(
                        "frs",
                        state["facet_id"],
                        state.get("capability_key", "shared"),
                        state.get("practice_item_id"),
                    )
                ),
                "facet_id": state["facet_id"],
                "capability_key": state.get("capability_key", "shared"),
                "practice_item_id": state.get("practice_item_id"),
                "recall_alpha": state["recall_alpha"],
                "recall_beta": state["recall_beta"],
                "recall_mean": state["recall_mean"],
                "recall_variance": state["recall_variance"],
                "independent_evidence_mass": state.get("independent_evidence_mass", 0.0),
                "raw_coverage_mass": state.get("raw_coverage_mass", 0.0),
                "last_observed_at": state.get("last_observed_at"),
                "last_error_at": state.get("last_error_at"),
                "consecutive_failures": int(state.get("consecutive_failures", 0)),
                "algorithm_version": algorithm_version,
                "created_at": state.get("created_at"),
            }
            for state in recall_rows
        ]
        capability_cells = [
            {
                "facet_id": row["facet_id"],
                "capability": row["capability"],
                "direct_positive_mass": row.get("direct_positive_mass", 0.0),
                "direct_negative_mass": row.get("direct_negative_mass", 0.0),
                "embedded_positive_mass": row.get("embedded_positive_mass", 0.0),
                "embedded_negative_mass": row.get("embedded_negative_mass", 0.0),
                "certification_credit": row.get("certification_credit", 0.0),
                "direct_certification_credit": row.get("direct_certification_credit", 0.0),
                "embedded_certification_credit": row.get("embedded_certification_credit", 0.0),
                "unexercised_supporting_mass": row.get("unexercised_supporting_mass", 0.0),
                "independent_surface_groups_json": _json(
                    sorted(row.get("independent_surface_groups", []))
                ),
                "algorithm_version": algorithm_version,
                "created_at": row.get("created_at"),
            }
            for row in capability_rows
        ]
        with self.connection() as connection:
            _write_projection_on_change(
                connection,
                (
                    (_FACET_RECALL_PROJECTION, recall_cells),
                    (_FACET_CAPABILITY_PROJECTION, capability_cells),
                ),
                now=now,
            )

    # -- capability residual activation (§4.2, KM5; DEFAULT OFF) -----------------

    def replace_capability_residual_state(
        self,
        *,
        rows: Iterable[Mapping[str, Any]],
        algorithm_version: str,
        clock: Clock | None = None,
    ) -> None:
        """Make the derived capability-residual activation state equal a projection (§4.2).

        Like :meth:`replace_canonical_facet_state`, this persists a pure
        projection over the observation ledger + closed episodes, so a rebuild
        reproduces its values, and it writes only the cells that changed
        (nothing when none did). When residual activation is disabled in config
        the projection passes ``rows=[]`` and the table stays empty —
        determinism holds with the feature on and off.
        """

        now = utc_now_iso(clock)
        cells = [
            {
                "id": str(
                    row.get("id")
                    or _projection_id("crs", row["facet_id"], row["capability"])
                ),
                "facet_id": row["facet_id"],
                "capability": row["capability"],
                "active": 1 if row.get("active") else 0,
                "activation_reason": row.get("activation_reason"),
                "residual_alpha": float(row["residual_alpha"]),
                "residual_beta": float(row["residual_beta"]),
                "residual_mean": float(row["residual_mean"]),
                "parent_alpha": float(row["parent_alpha"]),
                "parent_beta": float(row["parent_beta"]),
                "parent_mean": float(row["parent_mean"]),
                "divergence": float(row.get("divergence", 0.0)),
                "independent_groups": int(row.get("independent_groups", 0)),
                "independent_mass": float(row.get("independent_mass", 0.0)),
                "algorithm_version": algorithm_version,
                "created_at": row.get("created_at"),
            }
            for row in rows
        ]
        with self.connection() as connection:
            _write_projection_on_change(
                connection, ((_CAPABILITY_RESIDUAL_PROJECTION, cells),), now=now
            )

    def capability_residual_states(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM capability_residual_state ORDER BY facet_id, capability"
            ).fetchall()
        return [_capability_residual_row(row) for row in rows]

    def capability_residual_state(
        self, facet_id: str, capability: str
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM capability_residual_state WHERE facet_id = ? AND capability = ?",
                (facet_id, capability),
            ).fetchone()
        return _capability_residual_row(row) if row is not None else None

    # -- pre-first-practice identifiability watermark (§11.3, KM5) ---------------

    def identifiability_watermark(self, subject_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM subject_identifiability_watermarks WHERE subject_id = ?",
                (subject_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "subject_id": row["subject_id"],
            "registry_hash": row["registry_hash"],
            "finding_count": int(row["finding_count"]),
            "checked_at": row["checked_at"],
        }

    def upsert_identifiability_watermark(
        self,
        *,
        subject_id: str,
        registry_hash: str,
        finding_count: int,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO subject_identifiability_watermarks(
                  subject_id, registry_hash, finding_count, checked_at
                ) VALUES (?, ?, ?, ?)
                ON CONFLICT(subject_id) DO UPDATE SET
                  registry_hash = excluded.registry_hash,
                  finding_count = excluded.finding_count,
                  checked_at = excluded.checked_at
                """,
                (subject_id, registry_hash, int(finding_count), now),
            )
            connection.commit()

    # -- facet_merges: transitive resolution, cycle-rejected at write (§3.4) ------

    def facet_merge_map(self, *, include_in_flight: bool = False) -> dict[str, str]:
        """The settled merge map, retired facet -> survivor.

        Rows of a facet-identity merge or undo still in flight (``applying`` or
        ``undoing``) are left out until it settles: facets.yaml is the authority
        meanwhile (``stores.facet_identity.settled_merge_rows``, review F12).
        ``include_in_flight`` returns every row, for the write-time checks.
        """

        with self.connection() as connection:
            if not include_in_flight:
                return dict(settled_merge_rows(connection))
            rows = connection.execute(
                "SELECT retired_facet_id, surviving_facet_id FROM facet_merges"
            ).fetchall()
        return {str(r["retired_facet_id"]): str(r["surviving_facet_id"]) for r in rows}

    def resolve_facet_merge(self, facet_id: str, merge_map: Mapping[str, str] | None = None) -> str:
        """Resolve a facet id transitively to its terminal survivor (§7.1)."""

        table = dict(merge_map) if merge_map is not None else self.facet_merge_map()
        return _resolve_merge(facet_id, table)

    def insert_facet_merge(
        self,
        *,
        retired_facet_id: str,
        surviving_facet_id: str,
        proposal_item_id: str | None = None,
        rationale: str | None = None,
        clock: Clock | None = None,
    ) -> None:
        """Record a pre-lock reviewed merge; reject a row that creates a cycle.

        A cycle would make transitive resolution non-terminating; it is rejected
        at write time so the map can always be resolved to a fixed point (§7.1).
        """

        if retired_facet_id == surviving_facet_id:
            raise ValueError("merge would create a cycle: a facet cannot be merged into itself")
        table = self.facet_merge_map(include_in_flight=True)
        if retired_facet_id in table:
            raise ValueError(f"facet {retired_facet_id!r} is already retired by a merge")
        # Would (retired -> surviving) create a cycle? It does iff `retired` is
        # already reachable from `surviving` under the existing map.
        if _resolve_merge(surviving_facet_id, table) == retired_facet_id or _reaches(
            surviving_facet_id, retired_facet_id, table
        ):
            raise ValueError(
                f"merge {retired_facet_id!r} -> {surviving_facet_id!r} would create a cycle"
            )
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO facet_merges(
                  retired_facet_id, surviving_facet_id, merged_at, proposal_item_id, rationale
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (retired_facet_id, surviving_facet_id, now, proposal_item_id, rationale),
            )
            connection.commit()

    def facet_recall_states(self, learning_object_id: str | None = None) -> list[FacetRecallState]:
        with self.connection() as connection:
            if learning_object_id is None:
                rows = connection.execute(
                    "SELECT * FROM evidence_facet_recall_state ORDER BY learning_object_id, facet_id, practice_item_id"
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT * FROM evidence_facet_recall_state
                    WHERE learning_object_id = ?
                    ORDER BY facet_id, practice_item_id
                    """,
                    (learning_object_id,),
                ).fetchall()
        return [_facet_recall_state(row) for row in rows]

    def facet_uncertainty_state(
        self,
        learning_object_id: str,
        facet_id: str,
    ) -> FacetUncertaintyState | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM facet_uncertainty
                WHERE learning_object_id = ? AND facet_id = ?
                """,
                (learning_object_id, facet_id),
            ).fetchone()
        return _facet_uncertainty_state(row) if row is not None else None

    def facet_uncertainty_states(
        self,
        learning_object_id: str | None = None,
        *,
        statuses: Iterable[str] | None = None,
    ) -> list[FacetUncertaintyState]:
        clauses: list[str] = []
        parameters: list[Any] = []
        if learning_object_id is not None:
            clauses.append("learning_object_id = ?")
            parameters.append(learning_object_id)
        status_values = list(statuses or [])
        if status_values:
            clauses.append(f"status IN ({','.join('?' for _ in status_values)})")
            parameters.extend(status_values)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM facet_uncertainty{where}
                ORDER BY learning_object_id, status, uncertainty DESC, facet_id
                """,
                parameters,
            ).fetchall()
        return [_facet_uncertainty_state(row) for row in rows]

    def upsert_facet_uncertainty_state(self, state: Mapping[str, Any]) -> None:
        with self.connection() as connection:
            self._upsert_facet_uncertainty_state(connection, state)
            connection.commit()

    def latest_whole_vault_rebuild(self) -> dict[str, Any] | None:
        """The latest rebuild that replayed every learning object (scope ``all``), or None."""

        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM derived_state_rebuilds WHERE scope = 'all' ORDER BY created_at DESC, id DESC LIMIT 1"
            ).fetchone()
        return _decode_derived_state_rebuild(row) if row is not None else None

    def record_derived_state_rebuild(
        self,
        *,
        scope: str,
        learning_object_ids: list[str],
        algorithm_version: str,
        rebuilt_learning_objects: int,
        replayed_attempts: int,
        canonical_projection_version: str | None = None,
        coverage_denominator_version: str | None = None,
        projection_switches: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> str:
        rebuild_id = new_ulid()
        created_at = utc_now_iso(clock)
        columns = [
            "id", "scope", "learning_object_ids_json", "algorithm_version",
            "rebuilt_learning_objects", "replayed_attempts",
            "canonical_projection_version", "coverage_denominator_version", "created_at",
        ]
        values: list[Any] = [
            rebuild_id,
            scope,
            _json(learning_object_ids),
            algorithm_version,
            rebuilt_learning_objects,
            replayed_attempts,
            canonical_projection_version,
            coverage_denominator_version,
            created_at,
        ]
        if projection_switches is not None:
            # Router objective RO1 (migration 244): the switches a replay derived
            # persisted state under, the projection's defaults snapshot. Written
            # only by a rebuild that replays attempts, and only when given.
            columns.append("projection_switches_json")
            values.append(_json(dict(sorted(projection_switches.items()))))
        with self.connection() as connection:
            connection.execute(
                f"INSERT INTO derived_state_rebuilds({', '.join(columns)}) "
                f"VALUES ({', '.join('?' for _ in columns)})",
                values,
            )
            connection.commit()
        return rebuild_id

    def latest_derived_state_rebuild(self) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM derived_state_rebuilds
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """
            ).fetchone()
        return _decode_derived_state_rebuild(row) if row is not None else None

    def has_whole_vault_rebuild(self, *, algorithm_version: str) -> bool:
        """Whether a whole-vault rebuild (scope ``all``) ran under ``algorithm_version``.

        An activation that rebuilds the whole vault commits this receipt in
        its own transaction, so it marks the activation complete whatever
        startup, per-LO or recovery receipts are written after it."""

        with self.connection() as connection:
            row = connection.execute(
                "SELECT 1 FROM derived_state_rebuilds WHERE scope = 'all' AND algorithm_version = ? LIMIT 1",
                (algorithm_version,),
            ).fetchone()
        return row is not None

    def latest_canonical_projection_rebuild(self) -> dict[str, Any] | None:
        """Latest rebuild that explicitly names its projection semantics.

        ``derived_state_rebuilds`` also carries narrow scheduler/substrate
        recovery markers written by services that do not rebuild canonical
        facet state.  Their NULL projection field means "not reported", not a
        rollback.  Startup rollout checks must therefore read the latest
        explicit projection baseline rather than whichever unrelated marker
        happened to be written last.
        """

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM derived_state_rebuilds
                WHERE canonical_projection_version IS NOT NULL
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """
            ).fetchone()
        return _decode_derived_state_rebuild(row) if row is not None else None

    def _upsert_facet_uncertainty_state(self, connection: sqlite3.Connection, state: Mapping[str, Any]) -> None:
        marginal = {
            str(label): float(probability)
            for label, probability in dict(state.get("hypothesis_marginal") or {}).items()
        }
        existing = connection.execute(
            """
            SELECT id, created_at, opened_by_attempt_id, opened_reason
            FROM facet_uncertainty
            WHERE learning_object_id = ? AND facet_id = ?
            """,
            (state["learning_object_id"], state["facet_id"]),
        ).fetchone()
        state_id = str(state.get("id") or (existing["id"] if existing is not None else new_ulid()))
        opened_by_attempt_id = str(
            state.get("opened_by_attempt_id")
            or (existing["opened_by_attempt_id"] if existing is not None else "")
        )
        opened_reason = str(
            state.get("opened_reason")
            or (existing["opened_reason"] if existing is not None else "low_facet_outcome")
        )
        if existing is not None:
            connection.execute(
                """
                UPDATE facet_uncertainty
                SET hypothesis_marginal = ?, uncertainty = ?, status = ?,
                    opened_by_attempt_id = ?, opened_reason = ?,
                    last_evidence_at = ?, algorithm_version = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    _json(marginal),
                    state["uncertainty"],
                    state["status"],
                    opened_by_attempt_id,
                    opened_reason,
                    state.get("last_evidence_at"),
                    state["algorithm_version"],
                    state["updated_at"],
                    state_id,
                ),
            )
            return
        connection.execute(
            """
            INSERT INTO facet_uncertainty(
              id, learning_object_id, facet_id, hypothesis_marginal, uncertainty,
              status, opened_by_attempt_id, opened_reason, last_evidence_at,
              algorithm_version, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                state_id,
                state["learning_object_id"],
                state["facet_id"],
                _json(marginal),
                state["uncertainty"],
                state["status"],
                opened_by_attempt_id,
                opened_reason,
                state.get("last_evidence_at"),
                state["algorithm_version"],
                state.get("created_at", state["updated_at"]),
                state["updated_at"],
            ),
        )

    def derived_state_rebuild_version_changes(self) -> list[dict[str, Any]]:
        """Recalibration boundaries: each derived-state rebuild whose
        ``algorithm_version`` OR ``canonical_projection_version`` differs from
        the immediately preceding rebuild. Collapses consecutive same-version
        rebuilds so a version bump surfaces as exactly one entry, regardless of
        how many learning objects/facets it recomputed. Ordered oldest-first.

        The projection version is a second, finer boundary: a canonical
        projection semantics change (P2 §4.4 — probe/primed attempts become
        assisted) retro-changes derived facet state without touching the vault
        algorithm version, and must still surface as one honest "estimates
        recomputed, your evidence unchanged" entry rather than silently.

        THE FIRST ROW IS NOT ALWAYS HOUSEKEEPING.  Skipping it unconditionally
        (there is no predecessor to differ from) is right for a fresh vault, but
        wrong for the case that actually matters: a vault whose learner has been
        practising for months and whose ``derived_state_rebuilds`` table is
        empty, because rebuilds only started being recorded later.  Its first
        rebuild recomputes estimates the learner has already SEEN, under a
        projection version that was never in force when they saw them — and
        under the old rule it emitted nothing at all.  A silent state change is
        the failure mode `spec_diagnostic_augmentation_v1.md` A6 exists to
        prevent: the system must be able to say it was wrong.

        So the first row emits a boundary exactly when it recomputed prior
        learner evidence (``replayed_attempts > 0``) under a recorded projection
        version.  A first rebuild on a vault with nothing to replay narrates
        housekeeping the learner never saw, and stays silent. The dedicated
        startup projection scope stays silent on later zero-replay baselines as
        well, while still advancing the version used for future comparisons.
        ``previous_*`` is ``None`` on that entry, which is the truthful statement
        that no earlier version was on record.
        """

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT id, scope, algorithm_version, canonical_projection_version,
                       coverage_denominator_version, replayed_attempts, created_at
                FROM derived_state_rebuilds
                ORDER BY created_at, id
                """
            ).fetchall()
        changes: list[dict[str, Any]] = []
        previous_version: str | None = None
        previous_projection: str | None = None
        previous_coverage: str | None = None
        first = True
        for row in rows:
            version = str(row["algorithm_version"])
            raw_projection = row["canonical_projection_version"]
            projection = (
                str(raw_projection)
                if raw_projection is not None
                else previous_projection
            )
            # Measurement §5.2 (migration 138): a third, independent boundary.
            # The contract-frontier denominator moves DISPLAYED mastery with no
            # change to the evidence or the projection, so it needs its own
            # version — attributing the entry to either existing one would name a
            # cause that was not the cause.
            #
            # A NULL projection or coverage value means "this writer did not
            # report that dimension", not "the version was rolled back to
            # nothing". Historical rows predate the columns, and narrow rebuild
            # writers need not stamp either. Comparing NULL as a real value
            # would mint a phantom boundary on the next stamped rebuild and then
            # another on the one after — narrating recalibrations that never
            # happened. Unreported versions therefore carry forward and can
            # never themselves be a boundary.
            raw_coverage = row["coverage_denominator_version"]
            coverage = (
                str(raw_coverage) if raw_coverage is not None else previous_coverage
            )
            first_recalibrates_seen_evidence = (
                first
                and (projection is not None or coverage is not None)
                and int(row["replayed_attempts"] or 0) > 0
            )
            # Startup also stamps the current projection on an empty fresh
            # vault.  That is a baseline for future comparisons, not a change
            # to anything the learner demonstrated, so even a later software
            # upgrade while the vault is still empty remains silent.  The row
            # still advances ``previous_projection`` below, preventing a false
            # cutover after the learner's first attempt.
            silent_empty_projection_baseline = (
                str(row["scope"]) == "canonical_projection_startup"
                and int(row["replayed_attempts"] or 0) == 0
            )
            if not silent_empty_projection_baseline and (
                first_recalibrates_seen_evidence
                or (
                    not first
                    and (
                        version != previous_version
                        or projection != previous_projection
                        or coverage != previous_coverage
                    )
                )
            ):
                changes.append(
                    {
                        "id": str(row["id"]),
                        "algorithm_version": version,
                        "previous_algorithm_version": previous_version,
                        "canonical_projection_version": projection,
                        "previous_canonical_projection_version": (
                            previous_projection
                        ),
                        "coverage_denominator_version": coverage,
                        "previous_coverage_denominator_version": previous_coverage,
                        "at": str(row["created_at"]),
                    }
                )
            first = False
            previous_version = version
            previous_projection = projection
            previous_coverage = coverage
        return changes
