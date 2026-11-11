"""What other test files use from ``tests/test_capability_residual.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from pathlib import Path

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW, create_basic_vault, set_algorithm_version, write_facets
from tests.km2_write_path_helpers import _attempt, _item, _rubric


FACET = "facet_svd_factorization"
# Two surface groups per capability so the persistent-disagreement trigger has
# >= 2 independent groups; retrieval is answered correctly, selection wrongly.
_RETRIEVAL_ITEMS = ("pi_ret_a", "pi_ret_b")
_SELECT_ITEMS = ("pi_sel_a", "pi_sel_b")


def _enable_residual(paths, **overrides) -> None:
    keys = "\n".join(
        [
            "residual_activation_enabled = true",
            f"residual_divergence_threshold = {overrides.get('divergence', 0.1)}",
            f"residual_min_independent_mass = {overrides.get('min_mass', 0.4)}",
            f"residual_min_independent_groups = {overrides.get('min_groups', 2)}",
            f"residual_shrinkage_pseudo_count = {overrides.get('shrinkage', 4.0)}",
        ]
    )
    toml_path = paths.root / "learnloop.toml"
    text = toml_path.read_text(encoding="utf-8")
    updated = text.replace("[capabilities]\n", f"[capabilities]\n{keys}\n", 1)
    if updated == text:
        updated = text + f"\n[capabilities]\n{keys}\n"
    toml_path.write_text(updated, encoding="utf-8")


def _build_vault(root: Path, *, enable: bool):
    paths = create_basic_vault(root)
    write_yaml(paths.goals_path, {"schema_version": 2, "goals": []})
    write_facets(paths, [{"id": FACET, "kind": "definition", "claim": "SVD factorization."}])
    # Four items on the same facet: two at retrieval, two at method_selection,
    # each with its own source-example family (an independent surface group).
    specs = [
        ("pi_ret_a", "retrieval", "ret-a"),
        ("pi_ret_b", "retrieval", "ret-b"),
        ("pi_sel_a", "method_selection", "sel-a"),
        ("pi_sel_b", "method_selection", "sel-b"),
    ]
    for item_id, capability, family in specs:
        write_yaml(
            paths.practice_item_path("linear-algebra", item_id),
            _item(
                item_id,
                "lo_svd_definition",
                evidence_facets=[FACET],
                rubric=_rubric(
                    "correctness",
                    [{"facet": FACET, "capability": capability, "role": "primary"}],
                    correlation_group=f"grp_{family}",
                ),
                fingerprint={"source_family": family},
            ),
        )
    set_algorithm_version(paths, "mvp-0.7")
    if enable:
        _enable_residual(paths)
    return paths


def _drive(paths):
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    clock = FrozenClock(NOW)
    # Strong retrieval (full marks), weak selection (zero marks); repeat to build
    # mass on each independent surface group.
    for _ in range(3):
        for item_id in _RETRIEVAL_ITEMS:
            _attempt(vault, repository, item_id, {"correctness": 4}, clock)
        for item_id in _SELECT_ITEMS:
            _attempt(vault, repository, item_id, {"correctness": 0}, clock)
    return vault, repository
