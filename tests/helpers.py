from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from learnloop.clock import FrozenClock
from learnloop.config import LearnLoopConfig
from learnloop.db.repositories import MasteryState, Repository
from learnloop.vault.loader import add_subject, init_vault, load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import write_yaml
from learnloop.vault.writer import upsert_practice_item


NOW = datetime(2026, 5, 19, 12, 0, tzinfo=UTC)
NOW_ISO = "2026-05-19T12:00:00Z"
ALGORITHM_VERSION = LearnLoopConfig().algorithms.algorithm_version


async def begin_session(app, pilot):
    """Advance from the warm-up Start screen to the Today screen.

    The app launches on the warm-up StartScreen; most TUI tests want to drive
    the Today queue, so they call this once after the initial mount.
    """
    from learnloop.tui.screens.start import StartScreen

    if isinstance(app.screen, StartScreen):
        today = await app.screen.begin_session()
        await pilot.pause()
        return today
    return app.screen


def seed_due_item(paths: VaultPaths) -> Repository:
    """Seed mastery + a past-due Practice Item so the basic vault item schedules."""
    repository = Repository(paths.sqlite_path)
    repository.upsert_mastery_state(
        MasteryState(
            learning_object_id="lo_svd_definition",
            logit_mean=0.0,
            logit_variance=1.0,
            evidence_count=1,
            last_evidence_at="2026-05-18T12:00:00Z",
            algorithm_version=ALGORITHM_VERSION,
            updated_at=NOW_ISO,
        )
    )
    repository.upsert_practice_item_state(
        "pi_svd_define_001",
        difficulty=5.0,
        stability=2.0,
        due_at="2026-05-18T12:00:00Z",
        last_attempt_at="2026-05-16T12:00:00Z",
        active=True,
    )
    return repository


def create_basic_vault(root: Path) -> VaultPaths:
    clock = FrozenClock(NOW)
    init_vault(root, clock=clock)
    add_subject(root, "linear-algebra", "Linear Algebra", clock=clock)
    vault = load_vault(root)
    paths = VaultPaths(vault.root, vault.config)

    write_yaml(
        paths.concepts_path,
        {
            "schema_version": 1,
            "concepts": {
                "singular_value_decomposition": {
                    "title": "Singular Value Decomposition",
                    "type": "procedure",
                    "aliases": ["SVD"],
                    "description": "Matrix factorization.",
                    "tags": [],
                    "created_at": NOW_ISO,
                    "updated_at": NOW_ISO,
                }
            },
        },
    )
    write_yaml(
        paths.goals_path,
        {
            "schema_version": 2,
            "goals": [
                {
                    "id": "goal_linear_algebra_ml",
                    "title": "Linear algebra for ML",
                    "status": "active",
                    "priority": 0.8,
                    "target_recall": 0.8,
                    "facet_scope": {"concepts": ["singular_value_decomposition"]},
                    "due_at": None,
                    "created_at": NOW_ISO,
                    "updated_at": NOW_ISO,
                }
            ],
        },
    )
    write_yaml(
        paths.error_types_path,
        {
            "schema_version": 1,
            "error_types": [
                {
                    "id": "conceptual_slip",
                    "title": "Conceptual slip",
                    "description": "The answer confuses the core definition.",
                    "related_concepts": ["singular_value_decomposition"],
                    "severity_default": 0.7,
                    "is_misconception": True,
                    "tags": [],
                    "created_at": NOW_ISO,
                    "updated_at": NOW_ISO,
                }
            ],
        },
    )
    write_yaml(
        paths.learning_object_path("linear-algebra", "lo_svd_definition"),
        {
            "schema_version": 1,
            "id": "lo_svd_definition",
            "title": "SVD definition",
            "subjects": ["linear-algebra"],
            "concept": "singular_value_decomposition",
            "knowledge_type": "definition",
            "status": "active",
            "contradicts": None,
            "summary": "SVD factorizes a matrix into orthogonal factors and singular values.",
            "prerequisites": [],
            "confusables": [],
            "difficulty_prior": 0.55,
            "tags": [],
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )
    write_yaml(
        paths.practice_item_path("linear-algebra", "pi_svd_define_001"),
        {
            "schema_version": 1,
            "id": "pi_svd_define_001",
            "learning_object_id": "lo_svd_definition",
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt", "hinted_attempt", "dont_know"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": "Define SVD.",
            "expected_answer": "A matrix factorization into U, Sigma, and V transpose.",
            "difficulty": 0.55,
            "tags": [],
            "hints": ["Name the three factors."],
            "hint_policy": {
                "max_useful_hints": 1,
                "fsrs_rating_cap_by_hint": {"1": "good"},
                "mastery_alpha_dampening_by_hint": {"1": 0.5},
            },
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct definition."}],
                "fatal_errors": [
                    {
                        "id": "conceptual_slip",
                        "description": "Confuses SVD with a different decomposition.",
                        "max_grade": 1,
                    }
                ],
            },
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )
    return paths


def admit_probe_instrument_card(
    repository: Repository,
    *,
    learning_object_id: str = "lo_svd_definition",
    card_id: str = "card_svd_contrast",
    items: tuple[str, ...] = ("pi_svd_define_001",),
    rows: dict | None = None,
    target_facets: tuple[str, ...] = ("recall",),
) -> None:
    """Admit a contrast_confusable Instrument Card and link items to it.

    Probe redesign §9: only items with an executable instrument binding are
    probe candidates, so episode tests admit one card against the basic vault.
    """

    from learnloop.services.probe_families import (
        CONTRAST_CONFUSABLE_DEFAULT_ROWS,
        CONTRAST_CONFUSABLE_V1,
        InstrumentCard,
        ensure_builtin_families,
        validate_and_compile_card,
    )

    clock = FrozenClock(NOW)
    ensure_builtin_families(repository, clock=clock)
    card = InstrumentCard(
        id=card_id,
        version=1,
        family_template_id=CONTRAST_CONFUSABLE_V1.id,
        family_template_version=CONTRAST_CONFUSABLE_V1.version,
        learning_object_id=learning_object_id,
        target_decision="choose_schema_vs_confusable_repair",
        bindings={"target_facet": "recall", "confusable_concept": "eigendecomposition"},
        hypotheses=CONTRAST_CONFUSABLE_V1.hypothesis_slots,
        conditional_observations=rows or CONTRAST_CONFUSABLE_DEFAULT_ROWS,
        target_facets=target_facets,
        signature_error_types={"confusable_signature": ["conceptual_slip"]},
    )
    instrument = validate_and_compile_card(card, CONTRAST_CONFUSABLE_V1)
    repository.insert_probe_instrument_card(
        card_id=card.id,
        version=card.version,
        probe_family_template_id=CONTRAST_CONFUSABLE_V1.id,
        probe_family_template_version=CONTRAST_CONFUSABLE_V1.version,
        learning_object_id=learning_object_id,
        hypothesis_scope=list(card.hypotheses),
        card=card.as_dict(),
        compiled_likelihood_hash=instrument.compiled_likelihood_hash(),
        clock=clock,
    )
    for item_id in items:
        repository.link_probe_item_family(
            practice_item_id=item_id,
            instrument_card_id=card.id,
            instrument_card_version=card.version,
            clock=clock,
        )


def set_algorithm_version(paths: VaultPaths, version: str) -> None:
    """Rewrite learnloop.toml's algorithm_version in place (KM1 mvp-0.7 tests)."""

    toml_path = paths.root / "learnloop.toml"
    text = toml_path.read_text(encoding="utf-8")
    updated = text.replace(
        'algorithm_version = "mvp-0.6"', f'algorithm_version = "{version}"'
    )
    if updated == text:
        raise AssertionError("algorithm_version line not found in learnloop.toml")
    toml_path.write_text(updated, encoding="utf-8")


def write_facets(paths: VaultPaths, facets: list[dict], *, schema_version: int = 2) -> None:
    write_yaml(paths.facets_path, {"schema_version": schema_version, "facets": facets})


def add_followup_item(root: Path, item_id: str = "pi_svd_define_002") -> None:
    upsert_practice_item(
        root,
        {
            "id": item_id,
            "learning_object_id": "lo_svd_definition",
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": "Follow-up: define SVD again.",
            "expected_answer": "A matrix factorization into U, Sigma, and V transpose.",
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct definition."}],
                "fatal_errors": [],
            },
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
        clock=FrozenClock(NOW),
    )
