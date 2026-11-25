"""The synthetic vault and the script loader shared by the difficulty replay's tests (``scripts/difficulty_four_way.py``,
``scripts/difficulty_receipt_coverage.py``): the placement vault, a second facet, two LLM-estimated labels and twelve
graded attempts with repeats and one primed retry. With ``served=True`` the attempts are answered from plan
presentations whose serve AD's own hook recorded (its ``ad_threshold@*`` receipts), except where :data:`UNBOUND`
says not; the primed retry answers the presentation of the attempt before it (:data:`RETRY`)."""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from datetime import timedelta
from pathlib import Path

from learnloop.algorithm_versions import PROBE_ROUTER_ALGORITHM_VERSION
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.helpers import NOW, create_placement_vault, write_facets

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
#: The tag the replay's arms were built for: the last before the label's retirement (H3).
BEFORE_RETIREMENT = PROBE_ROUTER_ALGORITHM_VERSION
#: (item, points of 4, primed): repeats, a primed retry, misses on easy items and successes on hard ones, so the
#: label's b and AD's prediction disagree somewhere.
HISTORY = (
    ("pi_eig_easy", 4, False), ("pi_eig_hard", 4, False), ("pi_diag_easy", 0, False), ("pi_diag_hard", 4, False),
    ("pi_spec_easy", 4, False), ("pi_eig_mid", 2, False), ("pi_spec_hard", 0, False), ("pi_spec_hard", 4, True),
    ("pi_eig_easy", 4, False), ("pi_diag_mid", 4, False), ("pi_diag_hard", 0, False), ("pi_eig_hard", 4, False),
)
#: Items whose label is an LLM estimate, so AD reads it as the signal z_llm.
LLM_LABELLED = ("pi_eig_hard", "pi_diag_easy")
#: With ``served=True``: the attempts answered outside any plan presentation (a probe or a check would be).
UNBOUND = (3, 10)
#: With ``served=True``: the primed retry answers the presentation of the attempt before it, which the live door
#: refuses to bind (router R2a: ``presentation_already_answered``), so it is recorded unbound.
RETRY = 7


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(f"{name}_script", SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    # The scripts' dataclasses resolve their annotations through the registered module.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def forbid_model_clients(monkeypatch) -> None:
    from learnloop.ai import client

    def forbidden(*_args, **_kwargs):
        raise AssertionError("the difficulty replay scripts must not construct a model client")

    monkeypatch.setattr(client, "make_ai_provider_client", forbidden)
    monkeypatch.setattr(client, "make_ai_provider_client_from_profile", forbidden)
    monkeypatch.setattr("learnloop.ai.routing.ready_client_for_task", forbidden)
    monkeypatch.setattr("learnloop.ai.routing.client_for_provider", forbidden)


def _iso(moment) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def _serve(vault, repository: Repository, item_id: str, index: int, served) -> str:
    """One plan presentation of ``item_id``, its serve recorded by AD's own hook (receipts and serve inputs)."""

    from learnloop.adaptive_difficulty.serve import record_plan_serve

    block, presentation = f"blk_h3_{index}", f"pp_h3_{index}"
    with repository.connection() as connection:
        connection.execute("INSERT INTO attention_blocks(id, action, budget_minutes, content_hash, created_at) "
                           "VALUES (?, 'practice', 10, 'hash', ?)", (block, _iso(served)))
        connection.execute("INSERT INTO plan_presentations(id, block_id, practice_item_id, position, origin, served_at) "
                           "VALUES (?, ?, ?, 1, 'chooser', ?)", (presentation, block, item_id, _iso(served)))
        connection.commit()
    record_plan_serve(vault, repository, presentation_id=presentation, practice_item_id=item_id,
                      served_at=_iso(served))
    return presentation


def build_vault(root: Path, *, served: bool = False, version: str = BEFORE_RETIREMENT) -> VaultPaths:
    """At ``version`` (by default the tag before the label's retirement, where the replay's arms mean what H2
    measured: at the retirement the label is already off and surprise already reads AD)."""

    paths = create_placement_vault(root, version=version)
    # A second facet, so the spectral items open a cell AD has not seen (its population-level prediction).
    write_facets(paths, [
        {"id": "recall", "kind": "definition", "claim": "Recall the SVD definition."},
        {"id": "spectral", "kind": "definition", "claim": "State the spectral theorem."},
    ])
    for item_id in ("pi_spec_easy", "pi_spec_hard"):
        path = paths.practice_item_path("linear-algebra", item_id)
        data = read_yaml(path)
        data["evidence_facets"], data["evidence_weights"] = ["spectral"], {"spectral": 1.0}
        write_yaml(path, data)
    for item_id in LLM_LABELLED:
        path = paths.practice_item_path("linear-algebra", item_id)
        data = read_yaml(path)
        data["difficulty_source"] = "llm_estimate"
        write_yaml(path, data)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    presentation = None
    for index, (item_id, points, primed) in enumerate(HISTORY):
        when = NOW + timedelta(days=index, minutes=1 + 30 * primed)
        if served and index not in UNBOUND and index != RETRY:
            presentation = _serve(vault, repository, item_id, index, when - timedelta(seconds=30))
        bound = presentation if served and index not in UNBOUND else None
        draft = AttemptDraft(practice_item_id=item_id, learner_answer_md="An answer.",
                             attempt_type="independent_attempt", primed=primed, plan_presentation_id=bound)
        complete_self_graded_attempt(vault, repository, draft,
                                     SelfGradeInput(criterion_points={"correctness": points}, confidence=4),
                                     clock=FrozenClock(when))
    return paths


def file_digests(root: Path) -> dict[str, str]:
    """Every file's bytes, an absent ``-wal`` digesting as an empty one; ``-shm`` (an index) left out."""

    out = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and not path.name.endswith("-shm"):
            if path.name.endswith("-wal") and path.stat().st_size == 0:
                continue
            out[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out
