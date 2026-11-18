"""Grading contracts, observations and adjudication ledgers.

Owns outcome schema versions, calibration lookups, raw grade events, interpretations and augmentation receipts."""

from __future__ import annotations

import sqlite3
from typing import Any, Iterable, Mapping

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.records import _UNSET, _decode_observation_event, _decode_observation_template
from learnloop.db.row_serialization import _json, _loads
from learnloop.ids import new_ulid


def _decode_diagnostic_augmentation_receipt(
    row: sqlite3.Row,
) -> dict[str, Any]:
    data = dict(row)
    for key in (
        "c2_verifier_observations",
        "c3_disagreement_causes",
        "c4_history_attempt_ids",
    ):
        data[key] = _loads(data.pop(f"{key}_json"), [])
    for key in ("hypotheses", "revert_criteria"):
        data[key] = _loads(data.pop(f"{key}_json"), {})
    data["c1_repair_before_structure"] = bool(
        data["c1_repair_before_structure"]
    )
    return data


class GradingStoreMixin:

    def insert_observation_template(self, template: Mapping[str, Any], *, clock: Clock | None = None) -> str:
        now = utc_now_iso(clock)
        template_id = str(template.get("id") or new_ulid())
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO observation_templates(
                  id, domain, version, title, template_yaml, emits_attempt,
                  active, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    template_id,
                    template["domain"],
                    template["version"],
                    template["title"],
                    template["template_yaml"],
                    1 if template.get("emits_attempt") else 0,
                    1 if template.get("active", True) else 0,
                    now,
                    now,
                ),
            )
            connection.commit()
        return template_id

    def observation_templates(self, *, active_only: bool = False) -> list[dict[str, Any]]:
        query = "SELECT * FROM observation_templates"
        if active_only:
            query += " WHERE active = 1"
        query += " ORDER BY created_at, id"
        with self.connection() as connection:
            rows = connection.execute(query).fetchall()
        return [_decode_observation_template(row) for row in rows]

    def fetch_observation_template(self, template_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM observation_templates WHERE id = ?",
                (template_id,),
            ).fetchone()
        return _decode_observation_template(row) if row is not None else None

    def insert_observation_event(self, event: Mapping[str, Any], *, clock: Clock | None = None) -> str:
        now = event.get("created_at") or utc_now_iso(clock)
        event_id = str(event.get("id") or new_ulid())
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO observation_events(
                  id, template_id, subject, session_id, related_learning_object_id,
                  related_practice_item_id, binding_mode, response_json,
                  emitted_attempt_id, template_version, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    event["template_id"],
                    event.get("subject"),
                    event.get("session_id"),
                    event.get("related_learning_object_id"),
                    event.get("related_practice_item_id"),
                    event.get("binding_mode"),
                    _json(event.get("response", {})),
                    event.get("emitted_attempt_id"),
                    event["template_version"],
                    now,
                ),
            )
            connection.commit()
        return event_id

    def observation_events(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM observation_events ORDER BY created_at DESC"
            ).fetchall()
        return [_decode_observation_event(row) for row in rows]

    def ensure_outcome_schema_version(
        self,
        *,
        schema_id: str,
        version: int,
        observed_classes_json: str,
        true_classes_json: str,
        has_signature_error: bool,
        has_unanswered: bool,
        score_fraction_json: str,
        content_hash: str,
        clock: Clock | None = None,
    ) -> str:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT id FROM outcome_schema_versions WHERE schema_id = ? AND content_hash = ?",
                (schema_id, content_hash),
            ).fetchone()
            if row is not None:
                return row["id"]
            version_id = new_ulid()
            connection.execute(
                """
                INSERT INTO outcome_schema_versions(
                  id, schema_id, version, observed_classes_json, true_classes_json,
                  has_signature_error, has_unanswered, score_fraction_json,
                  content_hash, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version_id,
                    schema_id,
                    version,
                    observed_classes_json,
                    true_classes_json,
                    1 if has_signature_error else 0,
                    1 if has_unanswered else 0,
                    score_fraction_json,
                    content_hash,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
            return version_id

    def fetch_outcome_schema_version(
        self, *, slug: str, version: int | None = None
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            if version is None:
                row = connection.execute(
                    """
                    SELECT v.* FROM outcome_schema_versions v
                      JOIN outcome_schemas s ON s.id = v.schema_id
                     WHERE s.slug = ?
                     ORDER BY v.version DESC LIMIT 1
                    """,
                    (slug,),
                ).fetchone()
            else:
                row = connection.execute(
                    """
                    SELECT v.* FROM outcome_schema_versions v
                      JOIN outcome_schemas s ON s.id = v.schema_id
                     WHERE s.slug = ? AND v.version = ?
                    """,
                    (slug, version),
                ).fetchone()
        return dict(row) if row is not None else None

    def fetch_outcome_schema_version_by_id(self, schema_id: str, version: int) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM outcome_schema_versions WHERE schema_id = ? AND version = ?",
                (schema_id, version),
            ).fetchone()
        return dict(row) if row is not None else None

    def find_calibration_model_by_hash(self, content_hash: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM grader_calibration_models WHERE content_hash = ? LIMIT 1",
                (content_hash,),
            ).fetchone()
        return dict(row) if row is not None else None

    def calibration_models_by_hashes(
        self, content_hashes: Iterable[str]
    ) -> dict[str, dict[str, Any]]:
        """Bulk calibration-model lookup for a whole projection replay."""

        hashes = sorted({str(value) for value in content_hashes if value})
        if not hashes:
            return {}
        placeholders = ",".join("?" for _ in hashes)
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM grader_calibration_models
                 WHERE content_hash IN ({placeholders})
                """,
                hashes,
            ).fetchall()
        return {str(row["content_hash"]): dict(row) for row in rows}

    def fetch_calibration_alphas(self, model_id: str) -> dict[str, dict[str, float]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT true_class, alpha_json FROM grader_calibration_alphas WHERE model_id = ?",
                (model_id,),
            ).fetchall()
        return {row["true_class"]: _loads(row["alpha_json"], {}) for row in rows}

    def calibration_alphas_by_model_ids(
        self, model_ids: Iterable[str]
    ) -> dict[str, dict[str, dict[str, float]]]:
        """Bulk Dirichlet rows keyed by model id, preserving empty models."""

        ids = sorted({str(value) for value in model_ids if value})
        grouped: dict[str, dict[str, dict[str, float]]] = {
            model_id: {} for model_id in ids
        }
        if not ids:
            return grouped
        placeholders = ",".join("?" for _ in ids)
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT model_id, true_class, alpha_json
                  FROM grader_calibration_alphas
                 WHERE model_id IN ({placeholders})
                 ORDER BY model_id, true_class
                """,
                ids,
            ).fetchall()
        for row in rows:
            grouped[str(row["model_id"])][str(row["true_class"])] = _loads(
                row["alpha_json"], {}
            )
        return grouped

    def find_calibration_models(
        self,
        *,
        scope_level: str | None = None,
        grader_identity_hash: Any = _UNSET,
        outcome_schema_id: Any = _UNSET,
        outcome_schema_version: Any = _UNSET,
        domain: Any = _UNSET,
        length_bucket: Any = _UNSET,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if scope_level is not None:
            clauses.append("scope_level = ?")
            params.append(scope_level)
        if grader_identity_hash is not _UNSET:
            clauses.append("grader_identity_hash IS ?" if grader_identity_hash is None else "grader_identity_hash = ?")
            params.append(grader_identity_hash)
        if outcome_schema_id is not _UNSET:
            clauses.append("outcome_schema_id IS ?" if outcome_schema_id is None else "outcome_schema_id = ?")
            params.append(outcome_schema_id)
        if outcome_schema_version is not _UNSET:
            clauses.append("outcome_schema_version IS ?" if outcome_schema_version is None else "outcome_schema_version = ?")
            params.append(outcome_schema_version)
        if domain is not _UNSET:
            clauses.append("domain IS ?" if domain is None else "domain = ?")
            params.append(domain)
        if length_bucket is not _UNSET:
            clauses.append("length_bucket IS ?" if length_bucket is None else "length_bucket = ?")
            params.append(length_bucket)
        if status is not None:
            clauses.append("status = ?")
            params.append(status)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM grader_calibration_models{where} ORDER BY created_at, id",
                params,
            ).fetchall()
        return [dict(row) for row in rows]

    def insert_raw_grade_event(self, *, values: Mapping[str, Any], clock: Clock | None = None) -> str:
        event_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO raw_grade_events(
                  id, administration_id, observation_id, attempt_id, response_ref,
                  role, grader_provider, grader_model_revision, grading_prompt_version,
                  grader_output_schema_version, grader_identity_hash, agent_run_id,
                  raw_output_json, criterion_evidence_json, observed_class,
                  model_confidence, confidence_bucket, criterion_observed_classes_json,
                  response_classifier_version, criterion_classifier_version,
                  context_features_json, exact_word_count, declared_length_bucket,
                  predecessor_event_id, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    values["administration_id"],
                    values.get("observation_id"),
                    values.get("attempt_id"),
                    values.get("response_ref"),
                    values["role"],
                    values.get("grader_provider"),
                    values.get("grader_model_revision"),
                    values.get("grading_prompt_version"),
                    values.get("grader_output_schema_version"),
                    values.get("grader_identity_hash"),
                    values.get("agent_run_id"),
                    values["raw_output_json"],
                    values.get("criterion_evidence_json"),
                    values["observed_class"],
                    values.get("model_confidence"),
                    values["confidence_bucket"],
                    values.get("criterion_observed_classes_json"),
                    values["response_classifier_version"],
                    values.get("criterion_classifier_version"),
                    values["context_features_json"],
                    int(values["exact_word_count"]),
                    values["declared_length_bucket"],
                    values.get("predecessor_event_id"),
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return event_id

    def raw_grade_events_for_observation(self, observation_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM raw_grade_events WHERE observation_id = ? ORDER BY created_at, id",
                (observation_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def latest_raw_grade_identity(self, attempt_id: str) -> tuple[str | None, str | None] | None:
        """(prompt, output schema) calibration identity of the attempt's newest primary raw grade."""

        with self.connection() as connection:
            row = connection.execute(
                "SELECT grading_prompt_version, grader_output_schema_version FROM raw_grade_events "
                "WHERE attempt_id = ? AND role = 'primary' ORDER BY rowid DESC LIMIT 1",
                (attempt_id,),
            ).fetchone()
        return (row[0], row[1]) if row is not None else None

    def raw_grade_event(self, event_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM raw_grade_events WHERE id = ?", (event_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def raw_grade_events_by_ids(
        self, event_ids: Iterable[str]
    ) -> dict[str, dict[str, Any]]:
        """Bulk raw-grade lookup for legacy certainty-LCB reconstruction."""

        ids = sorted({str(value) for value in event_ids if value})
        if not ids:
            return {}
        placeholders = ",".join("?" for _ in ids)
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM raw_grade_events WHERE id IN ({placeholders})",
                ids,
            ).fetchall()
        return {str(row["id"]): dict(row) for row in rows}

    def insert_grade_interpretation(self, *, values: Mapping[str, Any], clock: Clock | None = None) -> str:
        interpretation_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO grade_interpretations(
                  id, raw_grade_event_id, observation_id, administration_id,
                  calibration_model_id, calibration_model_hash,
                  projection_algorithm_version, channel_posterior_snapshot_id,
                  response_posterior_json, criterion_posteriors_json,
                  reference_prior_ids_json, certainty_discount, shared_certainty_lcb,
                  credible_interval_json,
                  review_flag, influence_flag, quarantine_state, fallback_reason,
                  created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    interpretation_id,
                    values["raw_grade_event_id"],
                    values.get("observation_id"),
                    values["administration_id"],
                    values["calibration_model_id"],
                    values["calibration_model_hash"],
                    values["projection_algorithm_version"],
                    values.get("channel_posterior_snapshot_id"),
                    values["response_posterior_json"],
                    values.get("criterion_posteriors_json"),
                    values.get("reference_prior_ids_json"),
                    float(values["certainty_discount"]),
                    (
                        float(values["shared_certainty_lcb"])
                        if values.get("shared_certainty_lcb") is not None
                        else None
                    ),
                    values.get("credible_interval_json"),
                    1 if values.get("review_flag") else 0,
                    1 if values.get("influence_flag") else 0,
                    values.get("quarantine_state", "active"),
                    values.get("fallback_reason"),
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return interpretation_id

    def grade_interpretation(self, interpretation_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM grade_interpretations WHERE id = ?", (interpretation_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def grade_interpretations_for_observation(self, observation_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM grade_interpretations WHERE observation_id = ? ORDER BY created_at, id",
                (observation_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def insert_grade_adjudication(self, *, values: Mapping[str, Any], clock: Clock | None = None) -> str:
        adjudication_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO grade_adjudications(
                  id, observation_id, administration_id, reviewed_raw_event_ids_json,
                  adjudicator_source, resolved_class, resolved_distribution_json,
                  rationale, provenance_json, bounded_trust_weight,
                  resulting_interpretation_id, superseded_adjudication_id, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    adjudication_id,
                    values.get("observation_id"),
                    values["administration_id"],
                    values["reviewed_raw_event_ids_json"],
                    values["adjudicator_source"],
                    values.get("resolved_class"),
                    values.get("resolved_distribution_json"),
                    values.get("rationale"),
                    values.get("provenance_json"),
                    values.get("bounded_trust_weight"),
                    values.get("resulting_interpretation_id"),
                    values.get("superseded_adjudication_id"),
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return adjudication_id

    def insert_calibration_stream_sample(self, *, values: Mapping[str, Any], clock: Clock | None = None) -> str:
        sample_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO calibration_stream_samples(
                  id, observation_id, administration_id, raw_grade_event_id,
                  attempt_id, stream, stratum_json, inclusion_probability,
                  sampling_frame_id, selected, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sample_id,
                    values.get("observation_id"),
                    values.get("administration_id"),
                    values.get("raw_grade_event_id"),
                    values.get("attempt_id"),
                    values["stream"],
                    values["stratum_json"],
                    float(values["inclusion_probability"]),
                    values.get("sampling_frame_id"),
                    1 if values.get("selected", True) else 0,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return sample_id

    def calibration_stream_samples(
        self, *, stream: str | None = None, sampling_frame_id: str | None = None
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if stream is not None:
            clauses.append("stream = ?")
            params.append(stream)
        if sampling_frame_id is not None:
            clauses.append("sampling_frame_id = ?")
            params.append(sampling_frame_id)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM calibration_stream_samples{where} ORDER BY created_at, id",
                params,
            ).fetchall()
        return [dict(row) for row in rows]

    # -- Meas §3.A2-§3.A5 instrument classes (migration 143) ------------------
    #
    # All three stores are append-only by trigger and written with
    # ``INSERT OR IGNORE`` against a per-attempt (or per-serving) unique key: a
    # regrade re-reports the same judgement and must not multiply it, and the
    # first record is the one that happened. Every reader returns plain dicts in
    # insertion order, because the metrics over them are counts and shares, not
    # joins.

    def insert_discrimination_profile_match(
        self,
        *,
        attempt_id: str,
        practice_item_id: str,
        outcome: str,
        attempt_failed: bool,
        profile_id: str | None = None,
        misconception_id: str | None = None,
        evidence: str | None = None,
        grading_prompt_version: str | None = None,
        agent_run_id: str | None = None,
        id: str | None = None,
        clock: Clock | None = None,
    ) -> str | None:
        """Record A5's per-attempt profile judgement; ``None`` when one exists.

        Returns ``None`` rather than raising on a duplicate so a regrade is a
        no-op at the call site: the outcome is a record of what the grader said
        the first time, and §3.A5's rejection rate would be silently re-weighted
        by every re-run if later judgements overwrote earlier ones.
        """

        row_id = id or new_ulid()
        with self.connection() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO discrimination_profile_matches(
                  id, attempt_id, practice_item_id, outcome, profile_id,
                  misconception_id, evidence, attempt_failed,
                  grading_prompt_version, agent_run_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row_id,
                    attempt_id,
                    practice_item_id,
                    outcome,
                    profile_id,
                    misconception_id,
                    evidence,
                    1 if attempt_failed else 0,
                    grading_prompt_version,
                    agent_run_id,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return row_id if cursor.rowcount else None

    def discrimination_profile_match(self, attempt_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM discrimination_profile_matches WHERE attempt_id = ?",
                (attempt_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def insert_diagnostic_augmentation_receipt(
        self,
        values: Mapping[str, Any],
        *,
        clock: Clock | None = None,
    ) -> str | None:
        """Append Phase-C provenance; idempotent for one live attempt."""

        row_id = str(values.get("id") or new_ulid())
        with self.connection() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO diagnostic_augmentation_receipts(
                  id, attempt_id, grading_prompt_version, grader_provider,
                  grader_model, c1_repair_before_structure,
                  c2_verifier_observations_json, c3_sample_count,
                  c3_agreement_support, c3_disagreement_causes_json,
                  c4_history_attempt_ids_json, hypotheses_json,
                  revert_criteria_json, created_at, grader_mode
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row_id,
                    values["attempt_id"],
                    values["grading_prompt_version"],
                    values.get("grader_provider"),
                    values.get("grader_model"),
                    1 if values.get("c1_repair_before_structure") else 0,
                    _json(values.get("c2_verifier_observations") or []),
                    int(values.get("c3_sample_count") or 1),
                    float(values.get("c3_agreement_support") or 0.0),
                    _json(values.get("c3_disagreement_causes") or []),
                    _json(values.get("c4_history_attempt_ids") or []),
                    _json(values.get("hypotheses") or {}),
                    _json(values.get("revert_criteria") or {}),
                    values.get("created_at") or utc_now_iso(clock),
                    # §10: null reads as joint; only the blind grader writes it.
                    values.get("grader_mode"),
                ),
            )
            connection.commit()
        return row_id if cursor.rowcount else None

    def diagnostic_augmentation_receipt_for_attempt(
        self, attempt_id: str
    ) -> dict[str, Any] | None:
        """The Phase-C receipt for one graded attempt, or None.

        The receipt is the record of what the grading call was actually given —
        the grader provider/model, the prompt version, and the prior-attempt
        ids whose traces were attached as C4 history. That makes it the only
        stored answer to "was this grading run blind to the repair episode?",
        which the coldness receipt's `verification_blinding` dimension consumes.
        Absent for self-graded and pre-Stage-7 attempts: absence is `unknown`,
        never a pass.
        """

        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM diagnostic_augmentation_receipts WHERE attempt_id = ?",
                (attempt_id,),
            ).fetchone()
        return (
            _decode_diagnostic_augmentation_receipt(row) if row is not None else None
        )
