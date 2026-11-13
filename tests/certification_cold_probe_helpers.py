"""What other test files use from ``tests/test_certification_cold_probe.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.goals.certification_cold_probe import COLD_PROBE_TASK_KIND, current_certificate
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.certain_grade_helpers import make_grade_certain
from tests.helpers import NOW, add_followup_item, create_basic_vault, set_algorithm_version


LO_ID = "lo_svd_definition"
CERTIFYING_ITEM = "pi_svd_define_001"
HELD_OUT_ITEM = "pi_svd_define_002"
# The basic vault's only item is `short_answer` on facet "recall", which compiles
# to capability `schema_interpretation` — so a one-component recipe at that cell
# is certifiable by a single full-marks independent attempt, and the certificate
# under test is a real one rather than a hand-written ledger row.
FACET = "recall"
CAPABILITY = "schema_interpretation"


def _blueprint(paths, *, components=None, integration=None):
    components = components or [(FACET, CAPABILITY, "hard")]
    lo_path = paths.learning_object_path("linear-algebra", LO_ID)
    data = read_yaml(lo_path)
    recipe = {
        "id": "r1",
        "composition": "conjunctive",
        "all_of": [
            {"facet": facet, "capability": capability, "modality": modality}
            for facet, capability, modality in components
        ],
    }
    if integration is not None:
        recipe["integration"] = {
            "facet": integration[0],
            "capability": integration[1],
            "modality": "hard",
        }
    data["blueprints"] = [{"id": "bp1", "weight": 1.0, "recipes": [recipe]}]
    write_yaml(lo_path, data)


def _vault(tmp_path, *, second_item=True, components=None, integration=None):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.7")
    _blueprint(paths, components=components, integration=integration)
    if second_item:
        add_followup_item(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return paths, vault, repository


def _attempt(vault, repository, item_id, *, points=4, clock=None, primed=False, hints=0):
    return complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=item_id,
            learner_answer_md="U Sigma V transpose.",
            attempt_type="independent_attempt",
            hints_used=hints,
            primed=primed,
        ),
        SelfGradeInput(
            criterion_points={"correctness": points}, fatal_errors=[], confidence=4
        ),
        clock=clock or FrozenClock(NOW),
    )


def _certify(tmp_path, **kwargs):
    """Vault whose one LO holds a real certificate from one unassisted attempt."""

    paths, vault, repository = _vault(tmp_path, **kwargs)
    certifying = _attempt(vault, repository, CERTIFYING_ITEM)
    make_grade_certain(vault, repository, certifying.attempt_id, clock=FrozenClock(NOW))
    certificate = current_certificate(vault, repository, vault.learning_objects[LO_ID])
    assert certificate is not None, "fixture must actually certify"
    return paths, vault, repository, certificate


def _tasks(repository):
    return repository.followup_tasks_of_kind(COLD_PROBE_TASK_KIND)
