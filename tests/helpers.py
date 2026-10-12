from __future__ import annotations

import re
import textwrap
import tomllib
from datetime import UTC, datetime
from pathlib import Path

from learnloop.clock import FrozenClock
from learnloop.config import LearnLoopConfig
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import MasteryState, Repository
from learnloop.vault.loader import add_subject, init_vault, load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import write_yaml
from learnloop.vault.writer import upsert_practice_item


NOW = datetime(2026, 5, 19, 12, 0, tzinfo=UTC)
NOW_ISO = "2026-05-19T12:00:00Z"
ALGORITHM_VERSION = LearnLoopConfig().algorithms.algorithm_version
_BASIC_VAULT_TEMPLATE: VaultPaths | None = None
_FRESH_VAULTS = False


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


def create_basic_vault(root: Path, *, fresh: bool = False) -> VaultPaths:
    template = _BASIC_VAULT_TEMPLATE
    if template is not None and not fresh and not _FRESH_VAULTS and (not root.exists() or not any(root.iterdir())):
        # The template database goes through the backup API, like every copy of
        # a database that may be in WAL mode (tests/test_sqlite_file_copies.py).
        copy_tree_with_databases(template.root, root, dirs_exist_ok=True)
        return VaultPaths(root.resolve(), template.config.model_copy(deep=True))
    clock = FrozenClock(NOW)
    init_vault(root, clock=clock)
    # The basic vault is an mvp-0.6 vault: its items declare ad-hoc facets with
    # no facets.yaml registry, which is the pre-KM2 contract. `learnloop init`
    # writes mvp-0.7, so pin mvp-0.6 here; KM tests that want mvp-0.7 flip it
    # explicitly via set_algorithm_version.
    _set_algorithm_version_at(root, ALGORITHM_VERSION)
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


def append_config_toml(vault_root: Path, fragment: str) -> None:
    """Append an explicit, valid fragment to the schema-v2 minimal template.

    The generated template intentionally omits policy settings that equal their
    modeled defaults. Tests exercising a non-default must therefore add the
    canonical table/key instead of replacing a line that may not be rendered.
    Duplicate table headers fail loudly so this helper cannot silently create
    ambiguous TOML.
    """

    config_path = vault_root / "learnloop.toml"
    current = config_path.read_text(encoding="utf-8")
    normalized = textwrap.dedent(fragment).strip()
    if not normalized:
        raise AssertionError("config fragment must not be empty")
    for table in re.findall(r"(?m)^\[([^]]+)\]\s*$", normalized):
        if re.search(rf"(?m)^\[{re.escape(table)}\]\s*$", current):
            raise AssertionError(f"learnloop.toml already has [{table}]")
    updated = f"{current.rstrip()}\n\n{normalized}\n"
    tomllib.loads(updated)
    config_path.write_text(updated, encoding="utf-8")


def configure_codex_http(vault_root: Path, checkout: Path, base_url: str) -> None:
    """Configure the canonical Codex profile for an in-process HTTP test server.

    The schema-v2 template deliberately omits machine-local Codex fields, so
    there are no template lines to edit and tests replace the whole provider
    table.
    """

    config_path = vault_root / "learnloop.toml"
    text = config_path.read_text(encoding="utf-8")
    replacement = (
        "[ai.providers.codex]\n"
        'type = "http"\n'
        'model = "gpt-5.6-sol"\n'
        'reasoning_effort = "low"\n'
        f'checkout_path = "{checkout.as_posix()}"\n'
        'revision = "abc123"\n'
        f'base_url = "{base_url}"\n\n'
    )
    updated, count = re.subn(
        r"(?ms)^\[ai\.providers\.codex\]\n.*?(?=^\[|\Z)",
        replacement,
        text,
        count=1,
    )
    if count != 1:
        raise AssertionError("learnloop.toml has no [ai.providers.codex] table")
    config_path.write_text(updated, encoding="utf-8")


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

    from learnloop.diagnosis.probe_families import (
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

    _set_algorithm_version_at(paths.root, version)


def use_init_algorithm_version(paths: VaultPaths, scratch_root: Path) -> str:
    """Pin a basic vault to the algorithm version ``learnloop init`` writes.

    The basic vault is pinned to mvp-0.6 for its ad-hoc facets; tests that must
    follow whatever version a new vault gets initialize a throwaway vault at
    ``scratch_root`` and copy its version. Returns that version.
    """

    init_vault(scratch_root, clock=FrozenClock(NOW))
    version = load_vault(scratch_root).config.algorithms.algorithm_version
    _set_algorithm_version_at(paths.root, version)
    return version


def _set_algorithm_version_at(root: Path, version: str) -> None:
    toml_path = root / "learnloop.toml"
    text = toml_path.read_text(encoding="utf-8")
    updated, count = re.subn(
        r'algorithm_version = "[^"]+"',
        f'algorithm_version = "{version}"',
        text,
        count=1,
    )
    if count == 0:
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


def report_sqlite_version(monkeypatch, version: tuple[int, int, int]) -> None:
    """Make the linked SQLite report ``version`` for the WAL-reset gate.

    Only the reported version changes; the library that runs is the linked one.
    """

    import sqlite3

    monkeypatch.setattr(sqlite3, "sqlite_version_info", tuple(version))
    monkeypatch.setattr(sqlite3, "sqlite_version", ".".join(str(part) for part in version))


def production_journal_mode() -> str:
    """The journal mode the production path gives a vault on this runtime."""

    from learnloop.db.connection import wal_reset_bug_fixed

    return "wal" if wal_reset_bug_fixed() else "delete"


# ── Learner field F2 (Slice A Phase 6) ───────────────────────────────────────

PLACEMENT_LOS = {
    # lo id: (concept, prerequisite concepts, {item id: authored difficulty})
    "lo_eigen_basics": ("eigenvalues", [], {"pi_eig_easy": 0.2, "pi_eig_mid": 0.5, "pi_eig_hard": 0.8}),
    "lo_spectral": ("spectral_theorem", ["eigenvalues"], {"pi_spec_easy": 0.3, "pi_spec_hard": 0.7}),
    "lo_diag": ("diagonalization", [], {"pi_diag_easy": 0.25, "pi_diag_mid": 0.45, "pi_diag_hard": 0.75}),
}


def create_placement_vault(
    root: Path,
    *,
    version: str = "mvp-0.10",
    placement_toml: str | None = None,
) -> VaultPaths:
    """The basic vault plus three never-practised LOs outside any goal.

    ``lo_spectral`` declares ``eigenvalues`` (``lo_eigen_basics``) as its
    prerequisite, so it sits one layer below it. Items carry authored
    difficulties so the incumbent's predicted success orders them.
    """

    paths = create_basic_vault(root)
    concepts = {
        "singular_value_decomposition": {
            "title": "Singular Value Decomposition", "type": "procedure", "aliases": ["SVD"],
            "description": "Matrix factorization.", "tags": [], "created_at": NOW_ISO, "updated_at": NOW_ISO,
        }
    }
    for lo_id, (concept, prerequisites, items) in PLACEMENT_LOS.items():
        concepts[concept] = {
            "title": concept.replace("_", " ").title(), "type": "concept", "aliases": [],
            "description": f"{concept}.", "tags": [], "created_at": NOW_ISO, "updated_at": NOW_ISO,
        }
        write_yaml(
            paths.learning_object_path("linear-algebra", lo_id),
            {
                "schema_version": 1, "id": lo_id, "title": concept.replace("_", " ").title(),
                "subjects": ["linear-algebra"], "concept": concept, "knowledge_type": "definition",
                "status": "active", "contradicts": None, "summary": f"About {concept}.",
                "prerequisites": prerequisites, "confusables": [], "difficulty_prior": 0.5, "tags": [],
                "provenance": {"origin": "human", "source_refs": []},
                "created_at": NOW_ISO, "updated_at": NOW_ISO,
            },
        )
        for item_id, difficulty in items.items():
            write_yaml(
                paths.practice_item_path("linear-algebra", item_id),
                {
                    "schema_version": 1, "id": item_id, "learning_object_id": lo_id, "subjects": None,
                    "practice_mode": "short_answer",
                    "attempt_types_allowed": ["independent_attempt", "hinted_attempt", "dont_know"],
                    "evidence_facets": ["recall"], "evidence_weights": {"recall": 1.0},
                    "prompt": f"Question {item_id}.", "expected_answer": f"Answer {item_id}.",
                    "difficulty": difficulty, "tags": [], "hints": ["A hint."],
                    "hint_policy": {
                        "max_useful_hints": 1,
                        "fsrs_rating_cap_by_hint": {"1": "good"},
                        "mastery_alpha_dampening_by_hint": {"1": 0.5},
                    },
                    "grading_rubric": {
                        "max_points": 4,
                        "criteria": [{"id": "correctness", "points": 4, "description": "Correct."}],
                        "fatal_errors": [],
                    },
                    "provenance": {"origin": "human", "source_refs": []},
                    "created_at": NOW_ISO, "updated_at": NOW_ISO,
                },
            )
    write_yaml(paths.concepts_path, {"schema_version": 1, "concepts": concepts})
    set_algorithm_version(paths, version)
    if placement_toml:
        append_config_toml(paths.root, placement_toml)
    vault = load_vault(paths.root)
    return VaultPaths(vault.root, vault.config)
