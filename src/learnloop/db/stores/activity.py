"""Activity catalog, observations, surfaces and their lineage.

Owns activity patterns, features, cards, surfaces, administrations and observations;
card lineage, surface minting and surface kinship tables."""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.row_serialization import _loads
from learnloop.ids import new_ulid


# measurement_events.kind is validated here rather than by a SQL CHECK, so later
# P0 packages (P0.2 grader channel, P0.3+) extend the vocabulary by appending to
# this set without a table rebuild (spec_p0_measurement_correctness §3.3, §4.1).
_MEASUREMENT_EVENT_KINDS: set[str] = {
    "administration_opened",
    "response_appended",
    "exposure_recorded",
    "raw_grade_appended",
    "grade_classified",
    "grade_interpreted",
    "projection_rebuilt",
    "correction_appended",
    # P0.2 grader-channel lifecycle kinds (spec §3.3, §4.4). Model/interpretation
    # heads are projections over these append-only transitions; rows never mutate.
    "model_activated",
    "model_retired",
    "grade_quarantined",
    "grade_adjudicated",
    "interpretation_activated",
    "measurement_reinterpretation",
}


def _decode_exposure_event(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["detail"] = _loads(payload.get("detail_json"), None)
    payload["consumes_unseen"] = bool(payload.get("consumes_unseen"))
    return payload


def _decode_surface(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["surface"] = _loads(payload.get("surface_json"), {})
    payload["legacy_surface_unverifiable"] = bool(payload.get("legacy_surface_unverifiable"))
    return payload


class _InjectedLineageFault(RuntimeError):
    """Fault injected inside :meth:`Repository.write_administration_lineage_atomic` to
    prove the raw-event transaction rolls back as one unit (§7.4 fault injection)."""


class ActivityStoreMixin:

    # ------------------------------------------------------------------
    # Activity lineage substrate (P0.1; migration 065;
    # spec_p0_measurement_correctness §3.5-§3.8). SQL only; business logic
    # lives in ``learnloop.substrate.activities`` and
    # ``learnloop.substrate.compat.activity_backfill``.
    # ------------------------------------------------------------------

    def ensure_activity_family(
        self,
        *,
        purpose: str,
        legacy_kind: str | None,
        title: str | None,
        clock: Clock | None = None,
    ) -> str:
        """Content-addressed activity family, idempotent on ``(purpose, legacy_kind, title)``.

        Purpose is immutable for the life of a family (§3.5), so a re-run with the
        same authoring key reuses the existing family rather than transitioning it.
        """

        select_sql = """
            SELECT id FROM activity_families
             WHERE purpose = ?
               AND IFNULL(legacy_kind, '') = IFNULL(?, '')
               AND IFNULL(title, '') = IFNULL(?, '')
        """
        key = (purpose, legacy_kind, title)
        connection = self.connection()
        connection.isolation_level = None
        try:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(select_sql, key).fetchone()
            if existing is not None:
                connection.execute("ROLLBACK")
                return existing["id"]
            family_id = new_ulid()
            try:
                connection.execute(
                    """
                    INSERT INTO activity_families(id, purpose, legacy_kind, title, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (family_id, purpose, legacy_kind, title, utc_now_iso(clock)),
                )
                connection.execute("COMMIT")
                return family_id
            except sqlite3.IntegrityError:
                # A racing writer won the UNIQUE(authoring key) backstop (migration
                # 070); adopt its row rather than duplicating (M1).
                connection.execute("ROLLBACK")
                row = connection.execute(select_sql, key).fetchone()
                if row is None:
                    raise
                return row["id"]
        finally:
            connection.close()

    def ensure_activity_family_version(
        self,
        *,
        family_id: str,
        version: int,
        family_spec_json: str,
        clock: Clock | None = None,
    ) -> str:
        """Immutable family-spec snapshot, idempotent on ``(family_id, version)``."""

        with self.connection() as connection:
            existing = connection.execute(
                "SELECT id FROM activity_family_versions WHERE family_id = ? AND version = ?",
                (family_id, version),
            ).fetchone()
            if existing is not None:
                return existing["id"]
            version_id = new_ulid()
            connection.execute(
                """
                INSERT INTO activity_family_versions(
                  id, family_id, version, family_spec_json, created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (version_id, family_id, version, family_spec_json, utc_now_iso(clock)),
            )
            connection.commit()
        return version_id

    def ensure_activity_card(self, *, family_id: str, clock: Clock | None = None) -> str:
        """The family's canonical card (one card per family in the P0.1 legacy world).

        Idempotent: returns the family's existing card, creating one if absent.
        """

        select_sql = (
            "SELECT id FROM activity_cards WHERE family_id = ? ORDER BY created_at, id LIMIT 1"
        )
        connection = self.connection()
        connection.isolation_level = None
        try:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(select_sql, (family_id,)).fetchone()
            if existing is not None:
                connection.execute("ROLLBACK")
                return existing["id"]
            card_id = new_ulid()
            try:
                connection.execute(
                    "INSERT INTO activity_cards(id, family_id, created_at) VALUES (?, ?, ?)",
                    (card_id, family_id, utc_now_iso(clock)),
                )
                connection.execute("COMMIT")
                return card_id
            except sqlite3.IntegrityError:
                # A racing writer won the UNIQUE(family_id) backstop (migration 070).
                connection.execute("ROLLBACK")
                row = connection.execute(select_sql, (family_id,)).fetchone()
                if row is None:
                    raise
                return row["id"]
        finally:
            connection.close()

    def ensure_activity_card_version(
        self,
        *,
        card_id: str,
        version: int,
        card_contract_hash: str,
        contract_json: str,
        schema_version: int,
        predecessor_card_version_id: str | None = None,
        lineage_kind: str | None = None,
        legacy_contract_version_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        """Content-addressed card version, idempotent on ``(card_id, card_contract_hash)``.

        Two presentations that make the same semantic claim reuse one card version
        (§3.5); the exact wording lives on the surface, not here. If the requested
        ordinal is already occupied by a different immutable contract, append at
        the next ordinal. This is required when a newer compiler re-audits a
        legacy card whose version 1 already exists.
        """

        with self.connection() as connection:
            existing = connection.execute(
                """
                SELECT id FROM activity_card_versions
                 WHERE card_id = ? AND card_contract_hash = ?
                """,
                (card_id, card_contract_hash),
            ).fetchone()
            if existing is not None:
                return existing["id"]
            occupied = connection.execute(
                """
                SELECT 1 FROM activity_card_versions
                WHERE card_id = ? AND version = ?
                """,
                (card_id, version),
            ).fetchone()
            if occupied is not None:
                latest = connection.execute(
                    """
                    SELECT COALESCE(MAX(version), 0) AS max_version
                    FROM activity_card_versions
                    WHERE card_id = ?
                    """,
                    (card_id,),
                ).fetchone()
                version = int(latest["max_version"]) + 1
            version_id = new_ulid()
            connection.execute(
                """
                INSERT INTO activity_card_versions(
                  id, card_id, version, card_contract_hash, contract_json,
                  schema_version, predecessor_card_version_id, lineage_kind,
                  legacy_contract_version_id, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version_id,
                    card_id,
                    version,
                    card_contract_hash,
                    contract_json,
                    schema_version,
                    predecessor_card_version_id,
                    lineage_kind,
                    legacy_contract_version_id,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return version_id

    def ensure_activity_surface(
        self,
        *,
        card_version_id: str,
        surface_hash: str,
        fingerprint: str | None,
        surface_json: str,
        legacy_practice_item_id: str | None = None,
        legacy_surface_unverifiable: bool = False,
        clock: Clock | None = None,
    ) -> str:
        """Content-addressed surface, idempotent on ``(card_version_id, surface_hash)``.

        surface_hash is the exact-presentation identity (§3.6 rule 1); fingerprint
        is the shared-stimulus near-clone key (§3.6 rule 2).
        """

        with self.connection() as connection:
            existing = connection.execute(
                """
                SELECT id FROM activity_surfaces
                 WHERE card_version_id = ? AND surface_hash = ?
                """,
                (card_version_id, surface_hash),
            ).fetchone()
            if existing is not None:
                return existing["id"]
            surface_id = new_ulid()
            connection.execute(
                """
                INSERT INTO activity_surfaces(
                  id, card_version_id, surface_hash, fingerprint, surface_json,
                  legacy_practice_item_id, legacy_surface_unverifiable, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    surface_id,
                    card_version_id,
                    surface_hash,
                    fingerprint,
                    surface_json,
                    legacy_practice_item_id,
                    1 if legacy_surface_unverifiable else 0,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return surface_id

    def insert_surface_reservation(
        self,
        *,
        surface_id: str,
        goal_id: str | None,
        target_contract_version_id: str | None,
        target_support_hash: str | None,
        purpose: str,
        eligibility_json: str,
        clock: Clock | None = None,
    ) -> str:
        """Reserve a surface (§4.5). Raises ``sqlite3.IntegrityError`` when a live
        reservation already exists (partial unique index enforces at most one)."""

        reservation_id = new_ulid()
        now = utc_now_iso(clock)
        connection = self.connection()
        connection.isolation_level = None
        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                INSERT INTO activity_surface_reservations(
                  id, surface_id, goal_id, target_contract_version_id,
                  target_support_hash, purpose, status, eligibility_json,
                  administration_id, reserved_at, closed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, 'reserved', ?, NULL, ?, NULL)
                """,
                (
                    reservation_id,
                    surface_id,
                    goal_id,
                    target_contract_version_id,
                    target_support_hash,
                    purpose,
                    eligibility_json,
                    now,
                ),
            )
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()
        return reservation_id

    def close_surface_reservation(
        self,
        *,
        reservation_id: str,
        status: str,
        administration_id: str | None = None,
        expected_status: str | None = None,
        clock: Clock | None = None,
    ) -> bool:
        """Transition a reservation to a terminal status (the one permitted
        mutation on this append-mostly substrate).

        When ``expected_status`` is given the transition is a compare-and-set:
        it only fires ``WHERE status = expected_status`` (L8), so a caller that
        lost a race to a concurrent render/cancel gets ``False`` instead of
        clobbering the winner's terminal status. Returns whether a row transitioned.
        """

        clauses = "WHERE id = ?"
        params: list[Any] = [status, administration_id, utc_now_iso(clock), reservation_id]
        if expected_status is not None:
            clauses += " AND status = ?"
            params.append(expected_status)
        with self.connection() as connection:
            cursor = connection.execute(
                f"""
                UPDATE activity_surface_reservations
                   SET status = ?, administration_id = COALESCE(?, administration_id),
                       closed_at = ?
                 {clauses}
                """,
                params,
            )
            connection.commit()
            return cursor.rowcount > 0

    def open_administration_atomic(
        self,
        *,
        reservation_id: str | None,
        surface_id: str,
        card_version_id: str,
        family_id: str,
        purpose: str,
        surface_hash: str,
        fingerprint: str | None,
        snapshot_hash: str,
        snapshot_json: str,
        consumes_unseen: bool,
        pins: Mapping[str, Any] | None = None,
        algorithm_version: str,
        enforce_eligibility: bool = False,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """The render burn boundary (§4.5). Atomically: recheck no prior render,
        (when ``enforce_eligibility``) re-run the §3.6 collision checks INSIDE the
        lock and refuse on collision, insert the administration, insert the
        once-only ``rendered`` exposure, append ``expose`` (+ ``consume`` when
        consuming), and flip the reservation.

        Returns ``{"administration": <row dict>, "already_open": bool}``. Under a
        concurrent second render the loser observes the winner's rendered exposure
        and returns that same administration (expose-at-most-once, §9.5). When
        ``enforce_eligibility`` and a global exposure/fingerprint/quarantine
        collision is present, ROLLBACKs and returns
        ``{"administration": None, "refused": True, "refusal_reason": <reason>}``
        (§4.5, §7.3 row "exposure collision at render").
        """

        pins = dict(pins or {})
        now = utc_now_iso(clock)
        connection = self.connection()
        connection.isolation_level = None
        try:
            connection.execute("BEGIN IMMEDIATE")
            existing_render = connection.execute(
                """
                SELECT administration_id FROM activity_exposure_events
                 WHERE surface_id = ? AND kind = 'rendered'
                 LIMIT 1
                """,
                (surface_id,),
            ).fetchone()
            if existing_render is not None:
                admin_id = existing_render["administration_id"]
                admin = connection.execute(
                    "SELECT * FROM activity_administrations WHERE id = ?",
                    (admin_id,),
                ).fetchone()
                connection.execute("ROLLBACK")
                return {"administration": dict(admin) if admin else None, "already_open": True}

            if enforce_eligibility:
                # The §3.6 rules re-evaluated inside the burn lock (§4.5). A prior
                # render OF THIS surface was already handled above (concurrent
                # render -> winner). Any remaining exact-hash exposure is a
                # different surface; a fingerprint hit is a near-clone; a
                # quarantine disqualifies. Refuse rather than burn.
                refusal_reason: str | None = None
                exact = connection.execute(
                    "SELECT id FROM activity_exposure_events WHERE surface_hash = ? LIMIT 1",
                    (surface_hash,),
                ).fetchone()
                if exact is not None:
                    refusal_reason = "exact_surface_collision"
                elif fingerprint is not None:
                    near = connection.execute(
                        "SELECT id FROM activity_exposure_events WHERE fingerprint = ? LIMIT 1",
                        (fingerprint,),
                    ).fetchone()
                    if near is not None:
                        refusal_reason = "near_clone_collision"
                if refusal_reason is None:
                    quarantined = connection.execute(
                        """
                        SELECT id FROM activity_surface_lifecycle_events
                         WHERE surface_id = ? AND kind = 'quarantine' LIMIT 1
                        """,
                        (surface_id,),
                    ).fetchone()
                    if quarantined is not None:
                        refusal_reason = "assessment_disqualified"
                if refusal_reason is not None:
                    connection.execute("ROLLBACK")
                    return {
                        "administration": None,
                        "already_open": False,
                        "refused": True,
                        "refusal_reason": refusal_reason,
                    }

            administration_id = new_ulid()
            connection.execute(
                """
                INSERT INTO activity_administrations(
                  id, surface_id, card_version_id, family_id, purpose,
                  administration_snapshot_hash, snapshot_json,
                  target_contract_version_id, target_support_hash,
                  grader_model_version_id, selection_policy_version_id,
                  decision_params_hash, assistance_json, feedback_condition,
                  eligibility_json, reservation_id, legacy_backfilled, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                """,
                (
                    administration_id,
                    surface_id,
                    card_version_id,
                    family_id,
                    purpose,
                    snapshot_hash,
                    snapshot_json,
                    pins.get("target_contract_version_id"),
                    pins.get("target_support_hash"),
                    pins.get("grader_model_version_id"),
                    pins.get("selection_policy_version_id"),
                    pins.get("decision_params_hash"),
                    pins.get("assistance_json"),
                    pins.get("feedback_condition"),
                    pins.get("eligibility_json"),
                    reservation_id,
                    now,
                ),
            )
            connection.execute(
                """
                INSERT INTO activity_exposure_events(
                  id, surface_id, administration_id, surface_hash, fingerprint,
                  kind, purpose, consumes_unseen, detail_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, 'rendered', ?, ?, NULL, ?)
                """,
                (
                    new_ulid(),
                    surface_id,
                    administration_id,
                    surface_hash,
                    fingerprint,
                    purpose,
                    1 if consumes_unseen else 0,
                    now,
                ),
            )
            connection.execute(
                """
                INSERT INTO activity_surface_lifecycle_events(
                  id, surface_id, reservation_id, administration_id, kind,
                  reason, detail_json, created_at
                )
                VALUES (?, ?, ?, ?, 'expose', NULL, NULL, ?)
                """,
                (new_ulid(), surface_id, reservation_id, administration_id, now),
            )
            if consumes_unseen:
                connection.execute(
                    """
                    INSERT INTO activity_surface_lifecycle_events(
                      id, surface_id, reservation_id, administration_id, kind,
                      reason, detail_json, created_at
                    )
                    VALUES (?, ?, ?, ?, 'consume', NULL, NULL, ?)
                    """,
                    (new_ulid(), surface_id, reservation_id, administration_id, now),
                )
            connection.execute(
                """
                INSERT INTO measurement_events(
                  id, administration_id, observation_id, kind, algorithm_version,
                  payload_json, created_at
                )
                VALUES (?, ?, NULL, 'administration_opened', ?, NULL, ?)
                """,
                (new_ulid(), administration_id, algorithm_version, now),
            )
            if reservation_id is not None:
                connection.execute(
                    """
                    UPDATE activity_surface_reservations
                       SET status = 'rendered', administration_id = ?, closed_at = ?
                     WHERE id = ? AND status = 'reserved'
                    """,
                    (administration_id, now, reservation_id),
                )
            admin = connection.execute(
                "SELECT * FROM activity_administrations WHERE id = ?",
                (administration_id,),
            ).fetchone()
            connection.execute("COMMIT")
            return {"administration": dict(admin), "already_open": False}
        except Exception:
            connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    def write_administration_lineage_atomic(
        self,
        *,
        surface_id: str,
        card_version_id: str,
        family_id: str,
        purpose: str,
        surface_hash: str,
        fingerprint: str | None,
        snapshot_hash: str,
        snapshot_json: str,
        consumes_unseen: bool,
        algorithm_version: str,
        evidence_eligibility: str | None,
        eligibility_reason: str | None,
        reading_phase: str | None = None,
        admin_context: Mapping[str, Any] | None = None,
        attempt_id: str | None = None,
        response_ref: str | None = None,
        response_ledger_json: str | None = None,
        fault_after: "frozenset[str]" = frozenset(),
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Write the full RAW-EVENT lineage for one administration as ONE transaction
        (§7.4/§7.5): administration (+ its context, folded in so no NULL-context window
        exists) + rendered & submitted exposures + expose/consume lifecycle +
        observation + measurement events (administration_opened, response_appended).

        A fault anywhere in this unit rolls the WHOLE thing back -- a partial raw-event
        set is impossible; the only write allowed to defer is the downstream projection
        (card_state), handled by the caller. Idempotent: a prior render of the surface
        reuses that administration and its submitted exposure / observation.

        ``fault_after`` injects a fault INSIDE the transaction after the named boundary
        (``administration`` / ``exposure``) to prove rollback leaves nothing.
        """

        now = utc_now_iso(clock)
        admin_context_json = (
            None if admin_context is None else json.dumps(dict(admin_context), sort_keys=True)
        )
        connection = self.connection()
        connection.isolation_level = None
        try:
            connection.execute("BEGIN IMMEDIATE")
            existing_render = connection.execute(
                """
                SELECT administration_id FROM activity_exposure_events
                 WHERE surface_id = ? AND kind = 'rendered' LIMIT 1
                """,
                (surface_id,),
            ).fetchone()
            already_open = existing_render is not None
            if already_open:
                administration_id = existing_render["administration_id"]
            else:
                administration_id = new_ulid()
                connection.execute(
                    """
                    INSERT INTO activity_administrations(
                      id, surface_id, card_version_id, family_id, purpose,
                      administration_snapshot_hash, snapshot_json, reading_phase,
                      admin_context_json, legacy_backfilled, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                    """,
                    (
                        administration_id, surface_id, card_version_id, family_id, purpose,
                        snapshot_hash, snapshot_json, reading_phase, admin_context_json, now,
                    ),
                )
                connection.execute(
                    """
                    INSERT INTO activity_exposure_events(
                      id, surface_id, administration_id, surface_hash, fingerprint,
                      kind, purpose, consumes_unseen, detail_json, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, 'rendered', ?, ?, NULL, ?)
                    """,
                    (new_ulid(), surface_id, administration_id, surface_hash, fingerprint,
                     purpose, 1 if consumes_unseen else 0, now),
                )
                connection.execute(
                    """
                    INSERT INTO activity_surface_lifecycle_events(
                      id, surface_id, reservation_id, administration_id, kind,
                      reason, detail_json, created_at
                    )
                    VALUES (?, ?, NULL, ?, 'expose', NULL, NULL, ?)
                    """,
                    (new_ulid(), surface_id, administration_id, now),
                )
                if consumes_unseen:
                    connection.execute(
                        """
                        INSERT INTO activity_surface_lifecycle_events(
                          id, surface_id, reservation_id, administration_id, kind,
                          reason, detail_json, created_at
                        )
                        VALUES (?, ?, NULL, ?, 'consume', NULL, NULL, ?)
                        """,
                        (new_ulid(), surface_id, administration_id, now),
                    )
                connection.execute(
                    """
                    INSERT INTO measurement_events(
                      id, administration_id, observation_id, kind, algorithm_version,
                      payload_json, created_at
                    )
                    VALUES (?, ?, NULL, 'administration_opened', ?, NULL, ?)
                    """,
                    (new_ulid(), administration_id, algorithm_version, now),
                )
            if "administration" in fault_after:
                raise _InjectedLineageFault("administration")

            # Submitted exposure (idempotent reuse on retry).
            submitted = connection.execute(
                """
                SELECT id FROM activity_exposure_events
                 WHERE administration_id = ? AND kind = 'submitted' LIMIT 1
                """,
                (administration_id,),
            ).fetchone()
            if submitted is not None:
                submitted_exposure_id = submitted["id"]
            else:
                submitted_exposure_id = new_ulid()
                connection.execute(
                    """
                    INSERT INTO activity_exposure_events(
                      id, surface_id, administration_id, surface_hash, fingerprint,
                      kind, purpose, consumes_unseen, detail_json, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, 'submitted', ?, 0, NULL, ?)
                    """,
                    (submitted_exposure_id, surface_id, administration_id, surface_hash,
                     fingerprint, purpose, now),
                )
            if "exposure" in fault_after:
                raise _InjectedLineageFault("exposure")

            # Observation (idempotent reuse on retry) + response_appended measurement.
            existing_obs = connection.execute(
                "SELECT id FROM activity_observations WHERE administration_id = ? LIMIT 1",
                (administration_id,),
            ).fetchone()
            if existing_obs is not None:
                observation_id = existing_obs["id"]
            else:
                observation_id = new_ulid()
                connection.execute(
                    """
                    INSERT INTO activity_observations(
                      id, administration_id, surface_id, attempt_id, response_ref,
                      active_interpretation_id, evidence_eligibility, eligibility_reason,
                      created_at
                    )
                    VALUES (?, ?, ?, ?, ?, NULL, ?, ?, ?)
                    """,
                    (observation_id, administration_id, surface_id, attempt_id, response_ref,
                     evidence_eligibility, eligibility_reason, now),
                )
                connection.execute(
                    """
                    INSERT INTO measurement_events(
                      id, administration_id, observation_id, kind, algorithm_version,
                      payload_json, created_at
                    )
                    VALUES (?, ?, ?, 'response_appended', ?, ?, ?)
                    """,
                    (new_ulid(), administration_id, observation_id, algorithm_version,
                     response_ledger_json, now),
                )
            connection.execute("COMMIT")
            return {
                "administration_id": administration_id,
                "submitted_exposure_id": submitted_exposure_id,
                "observation_id": observation_id,
                "already_open": already_open,
            }
        except Exception:
            connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    def append_exposure_event(
        self,
        *,
        surface_id: str,
        administration_id: str | None,
        surface_hash: str,
        fingerprint: str | None,
        kind: str,
        purpose: str,
        consumes_unseen: bool = False,
        detail_json: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        event_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO activity_exposure_events(
                  id, surface_id, administration_id, surface_hash, fingerprint,
                  kind, purpose, consumes_unseen, detail_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    surface_id,
                    administration_id,
                    surface_hash,
                    fingerprint,
                    kind,
                    purpose,
                    1 if consumes_unseen else 0,
                    detail_json,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return event_id

    def append_surface_lifecycle_event(
        self,
        *,
        surface_id: str,
        kind: str,
        reservation_id: str | None = None,
        administration_id: str | None = None,
        reason: str | None = None,
        detail_json: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        event_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO activity_surface_lifecycle_events(
                  id, surface_id, reservation_id, administration_id, kind,
                  reason, detail_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    surface_id,
                    reservation_id,
                    administration_id,
                    kind,
                    reason,
                    detail_json,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return event_id

    def insert_activity_observation(
        self,
        *,
        administration_id: str,
        surface_id: str,
        attempt_id: str | None = None,
        response_ref: str | None = None,
        evidence_eligibility: str | None = None,
        eligibility_reason: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        observation_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO activity_observations(
                  id, administration_id, surface_id, attempt_id, response_ref,
                  active_interpretation_id, evidence_eligibility, eligibility_reason,
                  created_at
                )
                VALUES (?, ?, ?, ?, ?, NULL, ?, ?, ?)
                """,
                (
                    observation_id,
                    administration_id,
                    surface_id,
                    attempt_id,
                    response_ref,
                    evidence_eligibility,
                    eligibility_reason,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return observation_id

    def insert_retirement_record(
        self,
        *,
        scope: str,
        family_id: str | None,
        card_version_id: str | None,
        surface_id: str | None,
        reason: str,
        provenance: str,
        replacement_proposal_json: str | None = None,
        lifecycle_event_id: str | None = None,
        interaction_event_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        record_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO retirement_records(
                  id, scope, family_id, card_version_id, surface_id, reason,
                  provenance, replacement_proposal_json, lifecycle_event_id,
                  interaction_event_id, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    scope,
                    family_id,
                    card_version_id,
                    surface_id,
                    reason,
                    provenance,
                    replacement_proposal_json,
                    lifecycle_event_id,
                    interaction_event_id,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return record_id

    def append_interaction_event(
        self,
        *,
        kind: str,
        origin: str,
        subject_type: str | None = None,
        subject_id: str | None = None,
        administration_id: str | None = None,
        surface_id: str | None = None,
        attempt_id: str | None = None,
        affect_tap_kind: str | None = None,
        attempt_duration_ms: int | None = None,
        payload_json: str | None = None,
        occurred_at: str | None = None,
        received_at: str | None = None,
        actor: str | None = None,
        client_id: str | None = None,
        session_id: str | None = None,
        visit_id: str | None = None,
        payload_schema_version: str | None = None,
        source_id: str | None = None,
        revision_id: str | None = None,
        render_view_id: str | None = None,
        locator_json: str | None = None,
        annotation_id: str | None = None,
        commitment_id: str | None = None,
        activity_id: str | None = None,
        payload_hash: str | None = None,
        client_idempotency_key: str | None = None,
        privacy_locality: str | None = None,
        consent_context: str | None = None,
        producer_version: str | None = None,
        app_version: str | None = None,
        policy_version: str | None = None,
        supersedes_event_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        # §8.1 reader-envelope columns are all nullable so P0/P1/P2 callers are
        # untouched. A UNIQUE index on client_idempotency_key dedupes retries.
        event_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO interaction_events(
                  id, kind, subject_type, subject_id, administration_id, surface_id,
                  attempt_id, affect_tap_kind, attempt_duration_ms, payload_json,
                  origin, created_at,
                  occurred_at, received_at, actor, client_id, session_id, visit_id,
                  payload_schema_version, source_id, revision_id, render_view_id,
                  locator_json, annotation_id, commitment_id, activity_id,
                  payload_hash, client_idempotency_key, privacy_locality,
                  consent_context, producer_version, app_version, policy_version,
                  supersedes_event_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    kind,
                    subject_type,
                    subject_id,
                    administration_id,
                    surface_id,
                    attempt_id,
                    affect_tap_kind,
                    attempt_duration_ms,
                    payload_json,
                    origin,
                    utc_now_iso(clock),
                    occurred_at,
                    received_at,
                    actor,
                    client_id,
                    session_id,
                    visit_id,
                    payload_schema_version,
                    source_id,
                    revision_id,
                    render_view_id,
                    locator_json,
                    annotation_id,
                    commitment_id,
                    activity_id,
                    payload_hash,
                    client_idempotency_key,
                    privacy_locality,
                    consent_context,
                    producer_version,
                    app_version,
                    policy_version,
                    supersedes_event_id,
                ),
            )
            connection.commit()
        return event_id

    def append_measurement_event(
        self,
        *,
        administration_id: str,
        kind: str,
        algorithm_version: str,
        observation_id: str | None = None,
        payload_json: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        if kind not in _MEASUREMENT_EVENT_KINDS:
            raise ValueError(f"unknown measurement_event kind: {kind!r}")
        event_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO measurement_events(
                  id, administration_id, observation_id, kind, algorithm_version,
                  payload_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    administration_id,
                    observation_id,
                    kind,
                    algorithm_version,
                    payload_json,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return event_id

    def measurement_events_for_administration(
        self, administration_id: str
    ) -> list[dict[str, Any]]:
        """The administration's measurement events in append order (ledger read)."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM measurement_events
                 WHERE administration_id = ?
                 ORDER BY created_at, id
                """,
                (administration_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def set_active_interpretation(self, *, observation_id: str, interpretation_id: str) -> None:
        """Point the observation's projection head at an interpretation. This is a
        head pointer on activity_observations, NOT a mutation of an append-only
        event row (the interpretation itself is never updated)."""

        with self.connection() as connection:
            connection.execute(
                "UPDATE activity_observations SET active_interpretation_id = ? WHERE id = ?",
                (interpretation_id, observation_id),
            )
            connection.commit()

    def administration_by_legacy_presentation(self, presentation_id: str) -> dict[str, Any] | None:
        """Idempotency lookup for the §7.1 step-3 presentation backfill: the
        synthetic administration stores the presentation id in its snapshot."""

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM activity_administrations
                 WHERE json_extract(snapshot_json, '$.legacy_presentation_id') = ?
                 LIMIT 1
                """,
                (presentation_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def exposures_for_surface(self, surface_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM activity_exposure_events
                 WHERE surface_id = ? ORDER BY created_at, id
                """,
                (surface_id,),
            ).fetchall()
        return [_decode_exposure_event(row) for row in rows]

    def exposures_by_surface_hash(self, surface_hash: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM activity_exposure_events
                 WHERE surface_hash = ? ORDER BY created_at, id
                """,
                (surface_hash,),
            ).fetchall()
        return [_decode_exposure_event(row) for row in rows]

    def exposures_by_fingerprint(self, fingerprint: str) -> list[dict[str, Any]]:
        if not fingerprint:
            return []
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM activity_exposure_events
                 WHERE fingerprint = ? ORDER BY created_at, id
                """,
                (fingerprint,),
            ).fetchall()
        return [_decode_exposure_event(row) for row in rows]

    def fetch_surface(self, surface_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM activity_surfaces WHERE id = ?", (surface_id,)
            ).fetchone()
        return _decode_surface(row) if row is not None else None

    def reserved_assessment_surfaces(self) -> list[dict[str, Any]]:
        """Surfaces holding a LIVE assessment reservation (§8.1). Used by reader
        server-side reveal detection (L3) to know which surfaces a reader answer must
        never leak; each row carries the decoded surface plus its hash/fingerprint."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT s.* FROM activity_surface_reservations r
                JOIN activity_surfaces s ON s.id = r.surface_id
                WHERE r.status = 'reserved' AND r.purpose = 'assessment'
                """,
            ).fetchall()
        return [_decode_surface(row) for row in rows]

    def fetch_administration(self, administration_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM activity_administrations WHERE id = ?",
                (administration_id,),
            ).fetchone()
        if row is None:
            return None
        payload = dict(row)
        payload["snapshot"] = _loads(payload.get("snapshot_json"), {})
        return payload

    def observations_for_administration(self, administration_id: str) -> list[dict[str, Any]]:
        """All observation rows recorded under an administration, oldest first."""

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM activity_observations WHERE administration_id = ? "
                "ORDER BY created_at, id",
                (administration_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def fetch_reservation(self, reservation_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM activity_surface_reservations WHERE id = ?",
                (reservation_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def surface_lifecycle_history(self, surface_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM activity_surface_lifecycle_events
                 WHERE surface_id = ? ORDER BY created_at, id
                """,
                (surface_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def retirement_records_for_surface(self, surface_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM retirement_records WHERE surface_id = ? ORDER BY created_at, id",
                (surface_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def retirement_records_for_card_version(
        self, card_version_id: str
    ) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM retirement_records WHERE card_version_id = ?
                 ORDER BY created_at, id
                """,
                (card_version_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def surfaces_for_card_version(self, card_version_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM activity_surfaces WHERE card_version_id = ? ORDER BY created_at, id",
                (card_version_id,),
            ).fetchall()
        return [_decode_surface(row) for row in rows]

    def surfaces_for_legacy_practice_item(
        self, practice_item_id: str
    ) -> list[dict[str, Any]]:
        """Existing substrate surfaces backed by one legacy Practice Item.

        Resolving a legacy item can mint its family/card/surface. Retirement must
        only mirror surfaces that already exist, never create a fresh substrate
        object solely to retire it.
        """

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM activity_surfaces
                 WHERE legacy_practice_item_id = ?
                 ORDER BY created_at, id
                """,
                (practice_item_id,),
            ).fetchall()
        return [_decode_surface(row) for row in rows]

    def surfaces_for_family(self, family_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT s.* FROM activity_surfaces s
                  JOIN activity_card_versions cv ON cv.id = s.card_version_id
                  JOIN activity_cards c ON c.id = cv.card_id
                 WHERE c.family_id = ?
                 ORDER BY s.created_at, s.id
                """,
                (family_id,),
            ).fetchall()
        return [_decode_surface(row) for row in rows]

    def observation_by_attempt(self, attempt_id: str) -> dict[str, Any] | None:
        """The attempt's newest observation (None when it has none): the one the
        authoritative ledger reads (``observation_ledger``, same order). Also
        the backfill's idempotency key. A vault rebuilt before replay reused
        observations holds one per rebuild, so the order is the query's, never
        an index's."""

        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM activity_observations WHERE attempt_id = ? "
                "ORDER BY created_at DESC, id DESC LIMIT 1",
                (attempt_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def first_live_administration_at(self, purpose: str | None = None) -> str | None:
        """When the vault first wrote an activity administration itself (not one the §7.1 backfill reconstructed),
        of ``purpose`` when given: the stored fact that the activity substrate (or that purpose's writer) existed from
        then on. None when it never wrote one."""

        sql = "SELECT MIN(created_at) FROM activity_administrations WHERE legacy_backfilled = 0"
        with self.connection() as connection:
            row = (connection.execute(sql).fetchone() if purpose is None
                   else connection.execute(sql + " AND purpose = ?", (purpose,)).fetchone())
        return str(row[0]) if row is not None and row[0] is not None else None

    def first_live_observation_by_attempt_type(self) -> dict[str, str]:
        """For each attempt type, the recorded time of its earliest answer holding an observation the vault wrote
        itself (its administration not reconstructed by the backfill): the stored fact that the writer of that kind
        of answer recorded it from then on. A type none of whose answers was recorded live is absent."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT a.attempt_type, MIN(a.created_at)
                  FROM practice_attempts a
                  JOIN activity_observations o ON o.attempt_id = a.id
                  JOIN activity_administrations ad ON ad.id = o.administration_id
                 WHERE ad.legacy_backfilled = 0
                 GROUP BY a.attempt_type
                """
            ).fetchall()
        return {str(row[0]): str(row[1]) for row in rows if row[1] is not None}

    def answer_grade_records(self) -> list[dict[str, Any]]:
        """Every answer with its newest observation (``observation_id``, None without one) and whether that
        observation holds a raw grade (``graded``): what an answer's grade record is, read in one query."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT a.id, a.attempt_type, a.learning_object_id, a.created_at,
                       o.id AS observation_id,
                       EXISTS(SELECT 1 FROM raw_grade_events r WHERE r.observation_id = o.id) AS graded
                  FROM practice_attempts a
                  LEFT JOIN activity_observations o ON o.id = (
                       SELECT o2.id FROM activity_observations o2 WHERE o2.attempt_id = a.id
                        ORDER BY o2.created_at DESC, o2.id DESC LIMIT 1)
                 ORDER BY a.created_at, a.id
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def observation_attempt_id(self, observation_id: str) -> str | None:
        """Reverse of :meth:`observation_by_attempt` — the practice attempt an
        activity observation was minted for (ruling A: the grade-points
        adjudication lane needs the attempt to write its superseding
        ``grading_evidence`` revision). ``None`` for observations with no
        practice-attempt source (e.g. probe/exam-only administrations)."""

        with self.connection() as connection:
            row = connection.execute(
                "SELECT attempt_id FROM activity_observations WHERE id = ?",
                (observation_id,),
            ).fetchone()
        return str(row["attempt_id"]) if row is not None and row["attempt_id"] else None

    def mark_surface_unverifiable(self, surface_id: str) -> None:
        with self.connection() as connection:
            connection.execute(
                "UPDATE activity_surfaces SET legacy_surface_unverifiable = 1 WHERE id = ?",
                (surface_id,),
            )
            connection.commit()

    def insert_legacy_administration(
        self,
        *,
        surface_id: str,
        card_version_id: str,
        family_id: str,
        purpose: str,
        snapshot_hash: str,
        snapshot_json: str,
        target_contract_version_id: str | None = None,
        target_support_hash: str | None = None,
        eligibility_json: str | None = None,
        created_at: str,
    ) -> str:
        """Direct (non-atomic) administration insert for §7.1 backfill, timestamped
        at the recorded historical time (never now()) so re-runs stay byte-stable."""

        administration_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO activity_administrations(
                  id, surface_id, card_version_id, family_id, purpose,
                  administration_snapshot_hash, snapshot_json,
                  target_contract_version_id, target_support_hash,
                  grader_model_version_id, selection_policy_version_id,
                  decision_params_hash, assistance_json, feedback_condition,
                  eligibility_json, reservation_id, legacy_backfilled, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, NULL, ?, NULL, 1, ?)
                """,
                (
                    administration_id,
                    surface_id,
                    card_version_id,
                    family_id,
                    purpose,
                    snapshot_hash,
                    snapshot_json,
                    target_contract_version_id,
                    target_support_hash,
                    eligibility_json,
                    created_at,
                ),
            )
            connection.commit()
        return administration_id

    def append_exposure_event_at(
        self,
        *,
        surface_id: str,
        administration_id: str | None,
        surface_hash: str,
        fingerprint: str | None,
        kind: str,
        purpose: str,
        consumes_unseen: bool,
        created_at: str,
        detail_json: str | None = None,
    ) -> str:
        """Exposure insert timestamped at a recorded historical time (backfill)."""

        event_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO activity_exposure_events(
                  id, surface_id, administration_id, surface_hash, fingerprint,
                  kind, purpose, consumes_unseen, detail_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    surface_id,
                    administration_id,
                    surface_hash,
                    fingerprint,
                    kind,
                    purpose,
                    1 if consumes_unseen else 0,
                    detail_json,
                    created_at,
                ),
            )
            connection.commit()
        return event_id

    def interaction_events_for_attempt(self, attempt_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM interaction_events WHERE attempt_id = ? ORDER BY created_at, id",
                (attempt_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # P1 step 2 -- capability aliases, task features, activity patterns (migration 073)
    # ------------------------------------------------------------------

    def upsert_capability_alias(
        self,
        *,
        registry_version: int,
        legacy_value: str,
        canonical: str | None,
        clock: Clock | None = None,
    ) -> str:
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT id FROM capability_aliases WHERE registry_version = ? AND legacy_value = ?",
                (registry_version, legacy_value),
            ).fetchone()
            if existing is not None:
                return existing["id"]
            alias_id = new_ulid()
            connection.execute(
                """
                INSERT INTO capability_aliases(
                  id, registry_version, legacy_value, canonical, created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (alias_id, registry_version, legacy_value, canonical, utc_now_iso(clock)),
            )
            connection.commit()
        return alias_id

    def capability_alias(self, *, registry_version: int, legacy_value: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM capability_aliases WHERE registry_version = ? AND legacy_value = ?",
                (registry_version, legacy_value),
            ).fetchone()
        return dict(row) if row is not None else None

    def ensure_task_feature_schema_version(
        self,
        *,
        schema_slug: str,
        version: int,
        dimensions_json: str,
        content_hash: str,
        clock: Clock | None = None,
    ) -> str:
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT id FROM task_feature_schema_versions WHERE schema_slug = ? AND version = ?",
                (schema_slug, version),
            ).fetchone()
            if existing is not None:
                return existing["id"]
            schema_id = new_ulid()
            connection.execute(
                """
                INSERT INTO task_feature_schema_versions(
                  id, schema_slug, version, dimensions_json, content_hash, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (schema_id, schema_slug, version, dimensions_json, content_hash, utc_now_iso(clock)),
            )
            connection.commit()
        return schema_id

    def task_feature_schema_version(self, schema_version_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM task_feature_schema_versions WHERE id = ?", (schema_version_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def ensure_activity_pattern(self, *, pattern_slug: str, clock: Clock | None = None) -> str:
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT id FROM activity_patterns WHERE pattern_slug = ?", (pattern_slug,)
            ).fetchone()
            if existing is not None:
                return existing["id"]
            pattern_id = new_ulid()
            connection.execute(
                "INSERT INTO activity_patterns(id, pattern_slug, created_at) VALUES (?, ?, ?)",
                (pattern_id, pattern_slug, utc_now_iso(clock)),
            )
            connection.commit()
        return pattern_id

    def ensure_activity_pattern_version(
        self,
        *,
        pattern_id: str,
        version: int,
        content_hash: str,
        fields: Mapping[str, Any],
        status: str,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Content-addressed pattern version, idempotent on ``(pattern_id, content_hash)``.

        B8: the SELECT + INSERT race under ``BEGIN IMMEDIATE``; a lost race (two workers
        registering the same content) raises ``IntegrityError`` on the
        ``UNIQUE(pattern_id, content_hash)`` backstop and re-SELECTs the winner rather
        than surfacing an error or minting a duplicate."""

        def _existing(connection: sqlite3.Connection) -> dict[str, Any] | None:
            row = connection.execute(
                "SELECT * FROM activity_pattern_versions WHERE pattern_id = ? AND content_hash = ?",
                (pattern_id, content_hash),
            ).fetchone()
            return dict(row) if row is not None else None

        connection = self.connection()
        connection.isolation_level = None
        try:
            connection.execute("BEGIN IMMEDIATE")
            existing = _existing(connection)
            if existing is not None:
                connection.execute("ROLLBACK")
                return {"row": existing, "already_exists": True}
            version_id = new_ulid()
            try:
                connection.execute(
                    """
                    INSERT INTO activity_pattern_versions(
                      id, pattern_id, version, allowed_purposes_json, operation, learning_process,
                      allowed_target_kinds_json, allowed_capabilities_json, completion_semantics_json,
                      response_contract_json, progression_role, prerequisite_evidence_json,
                      feedback_strategy_json, assistance_strategy_json, evidence_semantics_by_context_json,
                      task_feature_bounds_json, variation_axes_json, rubric_shape_json, mint_gates_json,
                      burden_model_json, calibration_status, generator_version, content_hash, status,
                      created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        version_id, pattern_id, version, fields["allowed_purposes_json"],
                        fields["operation"], fields["learning_process"],
                        fields["allowed_target_kinds_json"], fields["allowed_capabilities_json"],
                        fields["completion_semantics_json"], fields["response_contract_json"],
                        fields.get("progression_role"), fields.get("prerequisite_evidence_json"),
                        fields.get("feedback_strategy_json"), fields.get("assistance_strategy_json"),
                        fields["evidence_semantics_by_context_json"], fields["task_feature_bounds_json"],
                        fields["variation_axes_json"], fields["rubric_shape_json"],
                        fields["mint_gates_json"], fields.get("burden_model_json"),
                        fields["calibration_status"], fields.get("generator_version"),
                        content_hash, status, utc_now_iso(clock),
                    ),
                )
            except sqlite3.IntegrityError:
                connection.execute("ROLLBACK")
                winner = _existing(connection)
                if winner is None:
                    raise
                return {"row": winner, "already_exists": True}
            row = connection.execute(
                "SELECT * FROM activity_pattern_versions WHERE id = ?", (version_id,)
            ).fetchone()
            connection.execute("COMMIT")
            return {"row": dict(row), "already_exists": False}
        finally:
            connection.close()

    def activity_pattern_version(self, pattern_version_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM activity_pattern_versions WHERE id = ?", (pattern_version_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def activity_pattern_versions(self, *, status: str | None = None) -> list[dict[str, Any]]:
        with self.connection() as connection:
            if status is None:
                rows = connection.execute(
                    "SELECT * FROM activity_pattern_versions ORDER BY created_at, id"
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM activity_pattern_versions WHERE status = ? ORDER BY created_at, id",
                    (status,),
                ).fetchall()
        return [dict(row) for row in rows]

    def activity_pattern_version_by_slug(
        self, *, pattern_slug: str, status: str | None = None
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            if status is None:
                row = connection.execute(
                    """
                    SELECT v.* FROM activity_pattern_versions v
                      JOIN activity_patterns p ON p.id = v.pattern_id
                     WHERE p.pattern_slug = ? ORDER BY v.version DESC LIMIT 1
                    """,
                    (pattern_slug,),
                ).fetchone()
            else:
                row = connection.execute(
                    """
                    SELECT v.* FROM activity_pattern_versions v
                      JOIN activity_patterns p ON p.id = v.pattern_id
                     WHERE p.pattern_slug = ? AND v.status = ? ORDER BY v.version DESC LIMIT 1
                    """,
                    (pattern_slug, status),
                ).fetchone()
        return dict(row) if row is not None else None

    # ------------------------------------------------------------------
    # P1 step 3 -- family/card authoring side tables (migration 074)
    # ------------------------------------------------------------------

    def upsert_activity_family_authoring(
        self, *, family_version_id: str, fields: Mapping[str, Any], clock: Clock | None = None
    ) -> None:
        """Insert/replace the authoring side row keyed by the immutable P0 family
        version id. The 065 ``activity_family_versions`` row is never touched."""

        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO activity_family_authoring(
                  family_version_id, commitment_id, commitment_target_version_id,
                  authoring_purpose, pattern_version_id, progression_policy_version_id,
                  goal_contract_version_id, depth_policy_version_id, depth_envelope_version_id,
                  served_milestone_edges_json, cross_purpose_links_json, angle_inventory_json,
                  coverage_targets_json, evidence_cap_policy_id, mint_policy_json,
                  retirement_policy_json, status, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(family_version_id) DO UPDATE SET
                  commitment_id = excluded.commitment_id,
                  commitment_target_version_id = excluded.commitment_target_version_id,
                  authoring_purpose = excluded.authoring_purpose,
                  pattern_version_id = excluded.pattern_version_id,
                  progression_policy_version_id = excluded.progression_policy_version_id,
                  goal_contract_version_id = excluded.goal_contract_version_id,
                  depth_policy_version_id = excluded.depth_policy_version_id,
                  depth_envelope_version_id = excluded.depth_envelope_version_id,
                  served_milestone_edges_json = excluded.served_milestone_edges_json,
                  cross_purpose_links_json = excluded.cross_purpose_links_json,
                  angle_inventory_json = excluded.angle_inventory_json,
                  coverage_targets_json = excluded.coverage_targets_json,
                  evidence_cap_policy_id = excluded.evidence_cap_policy_id,
                  mint_policy_json = excluded.mint_policy_json,
                  retirement_policy_json = excluded.retirement_policy_json,
                  status = excluded.status
                """,
                (
                    family_version_id, fields.get("commitment_id"),
                    fields.get("commitment_target_version_id"), fields["authoring_purpose"],
                    fields.get("pattern_version_id"), fields.get("progression_policy_version_id"),
                    fields.get("goal_contract_version_id"), fields.get("depth_policy_version_id"),
                    fields.get("depth_envelope_version_id"), fields.get("served_milestone_edges_json"),
                    fields.get("cross_purpose_links_json"), fields.get("angle_inventory_json"),
                    fields.get("coverage_targets_json"), fields.get("evidence_cap_policy_id"),
                    fields.get("mint_policy_json"), fields.get("retirement_policy_json"),
                    fields.get("status", "draft"), utc_now_iso(clock),
                ),
            )
            connection.commit()

    def set_activity_family_authoring_status(
        self, *, family_version_id: str, status: str
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                "UPDATE activity_family_authoring SET status = ? WHERE family_version_id = ?",
                (status, family_version_id),
            )
            connection.commit()

    def activity_family_authoring(self, family_version_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM activity_family_authoring WHERE family_version_id = ?",
                (family_version_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def upsert_activity_card_authoring(
        self, *, card_version_id: str, fields: Mapping[str, Any], clock: Clock | None = None
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO activity_card_authoring(
                  card_version_id, family_version_id, pattern_version_id,
                  task_feature_schema_version_id, task_features_json, capability,
                  outcome_schema_id, outcome_schema_version, surface_policy,
                  surface_variation_bounds_json, angle_identity_json, generator_version,
                  gate_policy_version, expected_burden_json, calibration_metadata_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(card_version_id) DO UPDATE SET
                  family_version_id = excluded.family_version_id,
                  pattern_version_id = excluded.pattern_version_id,
                  task_feature_schema_version_id = excluded.task_feature_schema_version_id,
                  task_features_json = excluded.task_features_json,
                  capability = excluded.capability,
                  outcome_schema_id = excluded.outcome_schema_id,
                  outcome_schema_version = excluded.outcome_schema_version,
                  surface_policy = excluded.surface_policy,
                  surface_variation_bounds_json = excluded.surface_variation_bounds_json,
                  angle_identity_json = excluded.angle_identity_json,
                  generator_version = excluded.generator_version,
                  gate_policy_version = excluded.gate_policy_version,
                  expected_burden_json = excluded.expected_burden_json,
                  calibration_metadata_json = excluded.calibration_metadata_json
                """,
                (
                    card_version_id, fields.get("family_version_id"),
                    fields.get("pattern_version_id"), fields.get("task_feature_schema_version_id"),
                    fields.get("task_features_json"), fields.get("capability"),
                    fields.get("outcome_schema_id"), fields.get("outcome_schema_version"),
                    fields.get("surface_policy"), fields.get("surface_variation_bounds_json"),
                    fields.get("angle_identity_json"), fields.get("generator_version"),
                    fields.get("gate_policy_version"), fields.get("expected_burden_json"),
                    fields.get("calibration_metadata_json"), utc_now_iso(clock),
                ),
            )
            connection.commit()

    def activity_card_authoring(self, card_version_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM activity_card_authoring WHERE card_version_id = ?",
                (card_version_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def activity_family_authoring_purposes(self, family_id: str) -> dict[str, str]:
        """Authoring purposes across every version of one stable family (§1.1
        invariant 2 / §9.1 purpose-immutability check), keyed by family_version_id."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT a.family_version_id AS fvid, a.authoring_purpose AS purpose
                  FROM activity_family_authoring a
                  JOIN activity_family_versions v ON v.id = a.family_version_id
                 WHERE v.family_id = ?
                """,
                (family_id,),
            ).fetchall()
        return {row["fvid"]: row["purpose"] for row in rows}

    def activity_family_version_family_id(self, family_version_id: str) -> str | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT family_id FROM activity_family_versions WHERE id = ?", (family_version_id,)
            ).fetchone()
        return row["family_id"] if row is not None else None

    # ------------------------------------------------------------------
    # P1 step 4: card lineages, richer lineage edges, card-level state
    # (migration 075). Append-only edges; state keyed by learner x lineage x
    # scheduler algorithm version (§3.7, §3.8).
    # ------------------------------------------------------------------
    def create_card_lineage(
        self,
        *,
        card_id: str | None = None,
        family_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        lineage_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO card_lineages(id, family_id, card_id, created_at) VALUES (?, ?, ?, ?)",
                (lineage_id, family_id, card_id, utc_now_iso(clock)),
            )
            connection.commit()
        return lineage_id

    def card_lineage(self, lineage_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM card_lineages WHERE id = ?", (lineage_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def append_card_lineage_edge(
        self,
        *,
        lineage_id: str,
        to_card_version_id: str,
        edge_kind: str,
        classifier_version: str,
        from_card_version_id: str | None = None,
        rationale: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> str:
        edge_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO card_lineage_edges(
                  id, lineage_id, from_card_version_id, to_card_version_id,
                  edge_kind, classifier_version, rationale_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    edge_id,
                    lineage_id,
                    from_card_version_id,
                    to_card_version_id,
                    edge_kind,
                    classifier_version,
                    None if rationale is None else json.dumps(rationale, sort_keys=True),
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return edge_id

    def card_lineage_edges(self, lineage_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM card_lineage_edges WHERE lineage_id = ? ORDER BY created_at, id",
                (lineage_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def lineage_for_card_version(self, card_version_id: str) -> str | None:
        """Resolve the lineage a card version belongs to via its lineage edges."""

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT lineage_id FROM card_lineage_edges
                 WHERE to_card_version_id = ? OR from_card_version_id = ?
                 ORDER BY created_at, id LIMIT 1
                """,
                (card_version_id, card_version_id),
            ).fetchone()
        return row["lineage_id"] if row is not None else None

    def upsert_activity_card_state(
        self,
        *,
        card_lineage_id: str,
        scheduler_algorithm_version: str,
        model_label: str,
        learner_id: str = "local",
        difficulty: float | None = None,
        stability: float | None = None,
        retrievability: float | None = None,
        due_at: str | None = None,
        last_eligible_review_at: str | None = None,
        lapse_episode_id: str | None = None,
        active: bool = True,
        projection_head: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> str:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            existing = connection.execute(
                """
                SELECT id FROM activity_card_state
                 WHERE learner_id = ? AND card_lineage_id = ? AND scheduler_algorithm_version = ?
                """,
                (learner_id, card_lineage_id, scheduler_algorithm_version),
            ).fetchone()
            state_id = existing["id"] if existing is not None else new_ulid()
            connection.execute(
                """
                INSERT INTO activity_card_state(
                  id, learner_id, card_lineage_id, scheduler_algorithm_version,
                  model_label, difficulty, stability, retrievability, due_at,
                  last_eligible_review_at, lapse_episode_id, active,
                  projection_head_json, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(learner_id, card_lineage_id, scheduler_algorithm_version)
                DO UPDATE SET
                  model_label = excluded.model_label,
                  difficulty = excluded.difficulty,
                  stability = excluded.stability,
                  retrievability = excluded.retrievability,
                  due_at = excluded.due_at,
                  last_eligible_review_at = excluded.last_eligible_review_at,
                  lapse_episode_id = excluded.lapse_episode_id,
                  active = excluded.active,
                  projection_head_json = excluded.projection_head_json,
                  updated_at = excluded.updated_at
                """,
                (
                    state_id,
                    learner_id,
                    card_lineage_id,
                    scheduler_algorithm_version,
                    model_label,
                    difficulty,
                    stability,
                    retrievability,
                    due_at,
                    last_eligible_review_at,
                    lapse_episode_id,
                    1 if active else 0,
                    None if projection_head is None else json.dumps(projection_head, sort_keys=True),
                    now,
                ),
            )
            connection.commit()
        return state_id

    def activity_card_state(
        self,
        *,
        card_lineage_id: str,
        scheduler_algorithm_version: str,
        learner_id: str = "local",
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM activity_card_state
                 WHERE learner_id = ? AND card_lineage_id = ? AND scheduler_algorithm_version = ?
                """,
                (learner_id, card_lineage_id, scheduler_algorithm_version),
            ).fetchone()
        return dict(row) if row is not None else None

    # ------------------------------------------------------------------
    # P1 step 5: administration purpose + context (migration 076 ALTER).
    # ------------------------------------------------------------------
    def activity_administration(self, administration_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM activity_administrations WHERE id = ?", (administration_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def set_administration_context(
        self,
        *,
        administration_id: str,
        reading_phase: str | None = None,
        admin_context: Mapping[str, Any] | None = None,
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE activity_administrations
                   SET reading_phase = ?, admin_context_json = ?
                 WHERE id = ?
                """,
                (
                    reading_phase,
                    None if admin_context is None else json.dumps(admin_context, sort_keys=True),
                    administration_id,
                ),
            )
            connection.commit()

    # ------------------------------------------------------------------
    # P1 step 6: namespaced fingerprint memberships, soft-kinship features,
    # surface authoring (migration 077). One familiarity namespace (§4.1/§4.2).
    # ------------------------------------------------------------------
    def record_fingerprint_membership(
        self,
        *,
        surface_id: str,
        namespace: str,
        value_hash: str,
        provenance: str | None = None,
        status: str | None = None,
        confidence: float | None = None,
        clock: Clock | None = None,
    ) -> str:
        with self.connection() as connection:
            existing = connection.execute(
                """
                SELECT id FROM surface_fingerprint_memberships
                 WHERE surface_id = ? AND namespace = ? AND value_hash = ?
                """,
                (surface_id, namespace, value_hash),
            ).fetchone()
            if existing is not None:
                return existing["id"]
            membership_id = new_ulid()
            connection.execute(
                """
                INSERT INTO surface_fingerprint_memberships(
                  id, surface_id, namespace, value_hash, provenance, status, confidence, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    membership_id,
                    surface_id,
                    namespace,
                    value_hash,
                    provenance,
                    status,
                    confidence,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return membership_id

    def fingerprint_memberships_for_surface(self, surface_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM surface_fingerprint_memberships WHERE surface_id = ? ORDER BY namespace, value_hash",
                (surface_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def surfaces_sharing_membership(
        self, *, namespace: str, value_hash: str, exclude_surface_id: str | None = None
    ) -> list[str]:
        """All surfaces in a given (namespace, value_hash) hard group. Every membership
        is considered -- never first-field-wins (§4.1, fixing the legacy L58 bug)."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT DISTINCT surface_id FROM surface_fingerprint_memberships
                 WHERE namespace = ? AND value_hash = ?
                 ORDER BY surface_id
                """,
                (namespace, value_hash),
            ).fetchall()
        out = [row["surface_id"] for row in rows]
        if exclude_surface_id is not None:
            out = [s for s in out if s != exclude_surface_id]
        return out

    def upsert_soft_kinship_features(
        self,
        *,
        surface_id: str,
        feature_schema_version: str,
        features: Mapping[str, Any],
        clock: Clock | None = None,
    ) -> str:
        with self.connection() as connection:
            existing = connection.execute(
                """
                SELECT id FROM soft_kinship_features
                 WHERE surface_id = ? AND feature_schema_version = ?
                """,
                (surface_id, feature_schema_version),
            ).fetchone()
            feature_id = existing["id"] if existing is not None else new_ulid()
            connection.execute(
                """
                INSERT INTO soft_kinship_features(
                  id, surface_id, feature_schema_version, features_json, created_at
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(surface_id, feature_schema_version) DO UPDATE SET
                  features_json = excluded.features_json
                """,
                (
                    feature_id,
                    surface_id,
                    feature_schema_version,
                    json.dumps(features, sort_keys=True),
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return feature_id

    def soft_kinship_features_for_surface(
        self, *, surface_id: str, feature_schema_version: str | None = None
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            if feature_schema_version is not None:
                row = connection.execute(
                    """
                    SELECT * FROM soft_kinship_features
                     WHERE surface_id = ? AND feature_schema_version = ?
                    """,
                    (surface_id, feature_schema_version),
                ).fetchone()
            else:
                row = connection.execute(
                    """
                    SELECT * FROM soft_kinship_features WHERE surface_id = ?
                     ORDER BY created_at DESC, id DESC LIMIT 1
                    """,
                    (surface_id,),
                ).fetchone()
        return dict(row) if row is not None else None

    def upsert_activity_surface_authoring(
        self, *, surface_id: str, fields: Mapping[str, Any], clock: Clock | None = None
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO activity_surface_authoring(
                  surface_id, surface_policy, generator_provenance_json, anchor_surface_id,
                  candidate_batch_id, seed, angle_coords_json, task_features_json,
                  gate_decision_json, reviewer, status, pinned_by_learner,
                  authorship_provenance_json, rotation_eligible, cache_state, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(surface_id) DO UPDATE SET
                  surface_policy = excluded.surface_policy,
                  generator_provenance_json = excluded.generator_provenance_json,
                  anchor_surface_id = excluded.anchor_surface_id,
                  candidate_batch_id = excluded.candidate_batch_id,
                  seed = excluded.seed,
                  angle_coords_json = excluded.angle_coords_json,
                  task_features_json = excluded.task_features_json,
                  gate_decision_json = excluded.gate_decision_json,
                  reviewer = excluded.reviewer,
                  status = excluded.status,
                  pinned_by_learner = excluded.pinned_by_learner,
                  authorship_provenance_json = excluded.authorship_provenance_json,
                  rotation_eligible = excluded.rotation_eligible,
                  cache_state = excluded.cache_state
                """,
                (
                    surface_id,
                    fields.get("surface_policy"),
                    fields.get("generator_provenance_json"),
                    fields.get("anchor_surface_id"),
                    fields.get("candidate_batch_id"),
                    fields.get("seed"),
                    fields.get("angle_coords_json"),
                    fields.get("task_features_json"),
                    fields.get("gate_decision_json"),
                    fields.get("reviewer"),
                    fields.get("status"),
                    1 if fields.get("pinned_by_learner") else 0,
                    fields.get("authorship_provenance_json"),
                    1 if fields.get("rotation_eligible") else 0,
                    fields.get("cache_state"),
                    utc_now_iso(clock),
                ),
            )
            connection.commit()

    def activity_surface_authoring(self, surface_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM activity_surface_authoring WHERE surface_id = ?", (surface_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def activity_exposure_events_for_surface(self, surface_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM activity_exposure_events WHERE surface_id = ? ORDER BY created_at, id",
                (surface_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # P1 step 7: durable surface-mint requests (migration 078). Modeled on the
    # 033 ingest-job lease: exactly one worker drains at a time; an expired lease
    # is recovered. Enqueue is idempotent on the §5.6 key. Never blocks attempts.
    # ------------------------------------------------------------------
    def enqueue_surface_mint_request(
        self,
        *,
        card_version_id: str,
        generator_version: str,
        gate_policy_version: str,
        anchor_surface_id: str | None = None,
        requested_angle_json: str = "",
        token_cost_json: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        """Idempotent on ``(card_version, anchor, requested_angle, generator,
        gate_policy)`` (§5.6). Returns the existing request id when one already
        exists (any status), else inserts a fresh ``pending`` request.

        B2: ``anchor_surface_id`` is the ``''`` sentinel when absent (mirroring
        ``requested_angle_json``) so the UNIQUE idempotency index treats "no anchor"
        as one value. The insert races under ``BEGIN IMMEDIATE``; a lost race raises
        ``IntegrityError`` on the UNIQUE constraint and re-SELECTs the winner rather
        than enqueuing a duplicate."""

        angle = requested_angle_json or ""
        anchor = anchor_surface_id if anchor_surface_id is not None else ""

        def _existing(connection: sqlite3.Connection) -> dict[str, Any] | None:
            return connection.execute(
                """
                SELECT id FROM surface_mint_requests
                 WHERE card_version_id = ? AND anchor_surface_id = ?
                   AND requested_angle_json = ? AND generator_version = ?
                   AND gate_policy_version = ?
                """,
                (card_version_id, anchor, angle, generator_version, gate_policy_version),
            ).fetchone()

        connection = self.connection()
        connection.isolation_level = None
        try:
            connection.execute("BEGIN IMMEDIATE")
            existing = _existing(connection)
            if existing is not None:
                connection.execute("ROLLBACK")
                return existing["id"]
            request_id = new_ulid()
            now = utc_now_iso(clock)
            try:
                connection.execute(
                    """
                    INSERT INTO surface_mint_requests(
                      id, card_version_id, anchor_surface_id, requested_angle_json,
                      generator_version, gate_policy_version, status, token_cost_json,
                      created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)
                    """,
                    (request_id, card_version_id, anchor, angle,
                     generator_version, gate_policy_version, token_cost_json, now, now),
                )
            except sqlite3.IntegrityError:
                connection.execute("ROLLBACK")
                winner = _existing(connection)
                if winner is None:
                    raise
                return winner["id"]
            connection.execute("COMMIT")
            return request_id
        finally:
            connection.close()

    def surface_mint_request(self, request_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM surface_mint_requests WHERE id = ?", (request_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def surface_mint_requests_for_card_version(
        self, card_version_id: str, *, statuses: Sequence[str] | None = None
    ) -> list[dict[str, Any]]:
        with self.connection() as connection:
            if statuses:
                placeholders = ",".join("?" for _ in statuses)
                rows = connection.execute(
                    f"""
                    SELECT * FROM surface_mint_requests
                     WHERE card_version_id = ? AND status IN ({placeholders})
                     ORDER BY created_at, id
                    """,
                    (card_version_id, *statuses),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM surface_mint_requests WHERE card_version_id = ? ORDER BY created_at, id",
                    (card_version_id,),
                ).fetchall()
        return [dict(row) for row in rows]

    def claim_next_surface_mint_request(
        self, *, worker_id: str, now_iso: str, lease_expires_at: str, lease_cutoff_iso: str
    ) -> dict[str, Any] | None:
        """Atomically claim the next ``pending`` mint request for ``worker_id``.

        Returns None when another worker holds a live running lease (exactly one
        worker drains at a time) or when no pending request exists. A ``running``
        request whose lease predates ``lease_cutoff_iso`` is treated as dead and
        does not block the claim.
        """

        connection = self.connection()
        connection.isolation_level = None
        try:
            connection.execute("BEGIN IMMEDIATE")
            # PF-b generation jobs (generator_version 'pf_*') share this table and
            # its lifecycle but are drained only by `learnloop pf generate`
            # (claim_surface_mint_request); a rotation worker never claims them.
            live = connection.execute(
                """
                SELECT 1 FROM surface_mint_requests
                 WHERE status = 'running'
                   AND lease_expires_at IS NOT NULL
                   AND lease_expires_at >= ?
                   AND generator_version NOT LIKE 'pf\\_%' ESCAPE '\\'
                 LIMIT 1
                """,
                (lease_cutoff_iso,),
            ).fetchone()
            if live is not None:
                connection.execute("ROLLBACK")
                return None
            candidate = connection.execute(
                """
                SELECT * FROM surface_mint_requests
                 WHERE (status = 'pending'
                        OR (status = 'running' AND (lease_expires_at IS NULL
                                                    OR lease_expires_at < ?)))
                   AND generator_version NOT LIKE 'pf\\_%' ESCAPE '\\'
                 ORDER BY created_at, id
                 LIMIT 1
                """,
                (lease_cutoff_iso,),
            ).fetchone()
            if candidate is None:
                connection.execute("ROLLBACK")
                return None
            # B1 fencing token: every (re)claim bumps lease_epoch so a late write from
            # the prior lease holder carries a stale epoch and is rejected.
            connection.execute(
                """
                UPDATE surface_mint_requests
                   SET status = 'running', lease_owner = ?, lease_expires_at = ?,
                       lease_epoch = lease_epoch + 1, updated_at = ?
                 WHERE id = ? AND status IN ('pending', 'running')
                """,
                (worker_id, lease_expires_at, now_iso, candidate["id"]),
            )
            claimed = connection.execute(
                "SELECT * FROM surface_mint_requests WHERE id = ?", (candidate["id"],)
            ).fetchone()
            connection.execute("COMMIT")
            return dict(claimed) if claimed is not None else None
        finally:
            connection.close()

    def claim_surface_mint_request(
        self, request_id: str, *, worker_id: str, now_iso: str, lease_expires_at: str,
        reclaim_statuses: Sequence[str] = ("pending", "failed"),
    ) -> dict[str, Any] | None:
        """Claim ONE named request under a fenced lease (PF-b, 078 pattern).

        Claimable when its status is in ``reclaim_statuses`` or it is ``running``
        under an expired lease. Returns the claimed row (with its new
        ``lease_epoch``) or None when another worker holds a live lease or the
        request is terminal.
        """

        statuses = tuple(reclaim_statuses)
        placeholders = ",".join("?" for _ in statuses)
        with self.connection() as connection:
            cursor = connection.execute(
                f"""
                UPDATE surface_mint_requests
                   SET status = 'running', lease_owner = ?, lease_expires_at = ?,
                       lease_epoch = lease_epoch + 1, failure_reason = NULL, updated_at = ?
                 WHERE id = ?
                   AND (status IN ({placeholders})
                        OR (status = 'running' AND (lease_expires_at IS NULL
                                                    OR lease_expires_at < ?)))
                """,
                (worker_id, lease_expires_at, now_iso, request_id, *statuses, now_iso),
            )
            claimed = connection.execute(
                "SELECT * FROM surface_mint_requests WHERE id = ?", (request_id,)
            ).fetchone() if cursor.rowcount else None
            connection.commit()
        return dict(claimed) if claimed is not None else None

    def release_surface_mint_request(
        self, request_id: str, *, expected_lease_epoch: int, clock: Clock | None = None,
    ) -> bool:
        """Return a cancelled, still-leased request to ``pending`` (resumable)."""

        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE surface_mint_requests
                   SET status = 'pending', lease_owner = NULL, lease_expires_at = NULL,
                       updated_at = ?
                 WHERE id = ? AND status = 'running' AND lease_epoch = ?
                """,
                (utc_now_iso(clock), request_id, expected_lease_epoch),
            )
            connection.commit()
            return cursor.rowcount > 0

    def set_surface_mint_candidate(
        self,
        *,
        request_id: str,
        candidate_surface_id: str,
        gate_results_json: str | None = None,
        token_cost_json: str | None = None,
        expected_lease_epoch: int | None = None,
        clock: Clock | None = None,
    ) -> bool:
        """Record the gated candidate and move the request to ``candidate_ready``.

        B1: guarded by ``status = 'running'`` and (when supplied) the fencing
        ``lease_epoch``. Returns True iff the write applied; a stale-lease worker's
        write is rejected (rowcount 0) so it can never advance a re-claimed job. The
        lease is deliberately RETAINED here (the same worker admits/rejects next);
        only the terminal transition releases it."""

        epoch_clause = "" if expected_lease_epoch is None else " AND lease_epoch = ?"
        params: list[Any] = [candidate_surface_id, gate_results_json, token_cost_json,
                             utc_now_iso(clock), request_id]
        if expected_lease_epoch is not None:
            params.append(expected_lease_epoch)
        with self.connection() as connection:
            cursor = connection.execute(
                f"""
                UPDATE surface_mint_requests
                   SET status = 'candidate_ready', candidate_surface_id = ?,
                       gate_results_json = COALESCE(?, gate_results_json),
                       token_cost_json = COALESCE(?, token_cost_json),
                       updated_at = ?
                 WHERE id = ? AND status = 'running'{epoch_clause}
                """,
                params,
            )
            connection.commit()
            return cursor.rowcount > 0

    def resolve_surface_mint_request(
        self,
        *,
        request_id: str,
        status: str,
        gate_results_json: str | None = None,
        failure_reason: str | None = None,
        candidate_surface_id: str | None = None,
        expected_lease_epoch: int | None = None,
        require_active: bool = False,
        clock: Clock | None = None,
    ) -> bool:
        """Terminal transition to ``admitted`` / ``rejected`` / ``failed``. Releases
        any lease. A failed/rejected candidate row is retained for audit.

        B1: when ``expected_lease_epoch`` is supplied the write is guarded by the
        fencing token, and when ``require_active`` is set only a ``running`` /
        ``candidate_ready`` request may transition (so an already-terminal request is
        never re-resolved by a re-run or a stale worker). Returns True iff applied."""

        clauses = ["id = ?"]
        params: list[Any] = [status, gate_results_json, failure_reason,
                             candidate_surface_id, utc_now_iso(clock), request_id]
        if require_active:
            clauses.append("status IN ('running', 'candidate_ready')")
        if expected_lease_epoch is not None:
            clauses.append("lease_epoch = ?")
            params.append(expected_lease_epoch)
        where = " AND ".join(clauses)
        with self.connection() as connection:
            cursor = connection.execute(
                f"""
                UPDATE surface_mint_requests
                   SET status = ?,
                       gate_results_json = COALESCE(?, gate_results_json),
                       failure_reason = COALESCE(?, failure_reason),
                       candidate_surface_id = COALESCE(?, candidate_surface_id),
                       lease_owner = NULL, lease_expires_at = NULL, updated_at = ?
                 WHERE {where}
                """,
                params,
            )
            connection.commit()
            return cursor.rowcount > 0

    def obsolete_surface_mint_requests_for_card_versions(
        self, card_version_ids: Sequence[str], *, clock: Clock | None = None
    ) -> int:
        """Mark all not-yet-terminal mint work for the given card versions ``obsolete``
        (§5.6: card/family retirement makes pending work obsolete). Returns the count."""

        if not card_version_ids:
            return 0
        placeholders = ",".join("?" for _ in card_version_ids)
        with self.connection() as connection:
            cursor = connection.execute(
                f"""
                UPDATE surface_mint_requests
                   SET status = 'obsolete', lease_owner = NULL, lease_expires_at = NULL,
                       updated_at = ?
                 WHERE card_version_id IN ({placeholders})
                   AND status IN ('pending', 'running', 'candidate_ready')
                """,
                (utc_now_iso(clock), *card_version_ids),
            )
            connection.commit()
            return cursor.rowcount

    # ------------------------------------------------------------------
    # P2 step B.11 -- reader dialogue (U-033, §7.6). Reader events ride the P0
    # interaction_events envelope (migration 086 extends the kind vocabulary);
    # these read helpers back the reader service + the replay-derived routing
    # prior projection. No new event table.
    # ------------------------------------------------------------------

    def reader_interaction_events(
        self,
        *,
        kind: str | None = None,
        subject_id: str | None = None,
        subject_type: str | None = None,
        since: str | None = None,
    ) -> list[dict[str, Any]]:
        """Reader interaction events (payload_json decoded), oldest first."""

        query = "SELECT * FROM interaction_events WHERE 1 = 1"
        params: list[Any] = []
        if kind is not None:
            query += " AND kind = ?"
            params.append(kind)
        if subject_id is not None:
            query += " AND subject_id = ?"
            params.append(subject_id)
        if subject_type is not None:
            query += " AND subject_type = ?"
            params.append(subject_type)
        if since is not None:
            query += " AND created_at >= ?"
            params.append(since)
        query += " ORDER BY created_at, id"
        with self.connection() as connection:
            rows = connection.execute(query, params).fetchall()
        out: list[dict[str, Any]] = []
        for row in rows:
            event = dict(row)
            event["payload"] = _loads(event.get("payload_json"), None)
            out.append(event)
        return out

    def first_cold_observation_for_target(
        self, target_contract_version_id: str
    ) -> str | None:
        """created_at of the FIRST cold administration pinned to this target
        contract version (design A.1 supersession). Cold = no reading phase, a
        measuring purpose (assessment/practice/diagnostic), and no
        ``source_visible`` in the recorded administration context. Returns None
        when no cold observation exists yet -- the reading-answer routing prior
        then still contributes."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT created_at, purpose, reading_phase, admin_context_json
                  FROM activity_administrations
                 WHERE target_contract_version_id = ?
                   AND reading_phase IS NULL
                   AND purpose IN ('assessment', 'practice', 'diagnostic')
                 ORDER BY created_at, id
                """,
                (target_contract_version_id,),
            ).fetchall()
        for row in rows:
            context = _loads(row["admin_context_json"], None) or {}
            if isinstance(context, Mapping) and context.get("source_visible") is True:
                continue
            return row["created_at"]
        return None

    def activity_family_purpose_for_card_version(self, card_version_id: str) -> str | None:
        """The immutable family purpose backing a card version (§12.4 role check).
        Joins card_version -> card -> family; returns None when the row is absent."""

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT f.purpose AS purpose
                  FROM activity_card_versions cv
                  JOIN activity_cards c ON c.id = cv.card_id
                  JOIN activity_families f ON f.id = c.family_id
                 WHERE cv.id = ?
                """,
                (card_version_id,),
            ).fetchone()
        return row["purpose"] if row is not None else None

    # ------------------------------------------------------------------
    # P2 ASSESSMENT + RESTORATION + MILESTONE track (migration 087;
    # spec_p2 §8.2/§8.3/§8.4/§7.5; design B.8-B.10). Append-only inspectable
    # run artifacts -- NO measurement/posterior/FSRS/certification here.
    # ------------------------------------------------------------------

    def resolved_activity_for_surface(self, surface_id: str) -> dict[str, Any] | None:
        """Reconstruct the family/card identity of an existing surface (for opening a
        reserved assessment administration from the run's stored ``reserved_surface_id``
        alone). Returns the fields :class:`activities.ResolvedActivity` needs."""

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT s.id           AS surface_id,
                       s.surface_hash AS surface_hash,
                       s.fingerprint  AS fingerprint,
                       cv.id          AS card_version_id,
                       cv.card_id     AS card_id,
                       cv.card_contract_hash AS card_contract_hash,
                       c.family_id    AS family_id
                  FROM activity_surfaces s
                  JOIN activity_card_versions cv ON cv.id = s.card_version_id
                  JOIN activity_cards c ON c.id = cv.card_id
                 WHERE s.id = ?
                """,
                (surface_id,),
            ).fetchone()
        return dict(row) if row is not None else None
