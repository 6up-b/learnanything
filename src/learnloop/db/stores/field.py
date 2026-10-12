"""Narrow SQL write ownership for F1 caches; never writes learner evidence.

Callers own the transaction. The outcome replayer alone replaces the derived
cache; optional paid classification appends its already-ledgered output.
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence
import sqlite3


def replace_facet_outcomes(connection: sqlite3.Connection, rows: Iterable[Sequence]) -> None:
    connection.execute("DELETE FROM facet_outcome_observations")
    connection.executemany(
        """INSERT INTO facet_outcome_observations(
        attempt_id,facet_id,practice_item_id,item_snapshot_hash,revision_status,
        observed_at,outcome,facet_share,effective_mass,cold,assisted,primed,
        surface_group_id,serving_origin,serving_propensity,scheduler_candidate_id
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        rows,
    )


def insert_question_classification(connection: sqlite3.Connection, values: Sequence) -> None:
    connection.execute(
        """INSERT INTO question_classifications
        (id,question_event_id,interaction_event_id,input_hash,question_type,
        lo_ids_json,facets_json,model,prompt_version,created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)""",
        values,
    )
