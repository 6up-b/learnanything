"""LP-min (a) Codex review fixes (docs/reviews/lp-claim-fixes-codex-review.md).

F1 an interrupted or concurrent gap promotion applies its claim exactly once;
F2 an upgrade that dies between the config's publication and the commit is
completed from its journal; F3 activation re-seeds claim-covered LOs without
attempts as a full rebuild does; F4 a claim never lowers a variance, cold or
warm; F5 claims and attempts stamped in the same second replay in the order
they were written; F6 the review that resolves an "I know this" says so, once.
"""

from __future__ import annotations

from datetime import timedelta
import multiprocessing
import os
import sqlite3

import pytest

from learnloop.algorithm_versions import CLAIM_FIXES_ALGORITHM_VERSION, SUCCESSOR_CHAIN
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.learner.mastery import reanchor_mastery_from_claim
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.tutor.ai_contracts import PromotionAnalysis
from learnloop.tutor.promotions import promote_tutor_question
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, append_config_toml, create_placement_vault
from tests.test_assumed_known import _answer
from tests.test_tutor_promotion_service import _AnalysisClient, _insert_event

TAG = CLAIM_FIXES_ALGORITHM_VERSION
PREDECESSOR = SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1]
OFF = "[mastery]\nclaim_fixes_enabled = false\n"
LO = "lo_svd_definition"
ITEM = "pi_svd_define_001"


def _iso(minutes: float) -> str:
    return (NOW + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")


def _vault(tmp_path, name="vault", *, version=TAG, toml=None):
    paths = create_placement_vault(tmp_path / name, version=version)
    if toml:
        append_config_toml(paths.root, toml)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return paths, vault, repository


def _gap(root, repository, event_id="ev_gap", *, minutes=30.0, item=ITEM):
    if repository.question_event(event_id) is None:
        _insert_event(repository, event_id, practice_item_id=item)
    client = _AnalysisClient(PromotionAnalysis(attributed_facets=["recall"], question_nature="mechanism"))
    return promote_tutor_question(
        root, client, event_id=event_id, intent="gap", clock=FrozenClock(NOW + timedelta(minutes=minutes))
    )


def _mastery(repository, lo=LO) -> tuple[float, float, int]:
    state = repository.mastery_state(lo)
    assert state is not None
    return (state.logit_mean, state.logit_variance, state.evidence_count)


def _all_mastery(path) -> dict[str, tuple[float, float, int]]:
    with sqlite3.connect(path) as connection:
        rows = connection.execute(
            "SELECT learning_object_id, logit_mean, logit_variance, evidence_count FROM learning_object_mastery"
        ).fetchall()
    return {row[0]: (row[1], row[2], row[3]) for row in rows}


def _gap_claims(repository) -> list[dict]:
    return [claim for claim in repository.learner_claims() if claim["source"] == "tutor_gap_declaration"]


def _rebuild(paths):
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    rebuild_all_derived_state(vault, repository, clock=FrozenClock(NOW + timedelta(hours=1)))
    return repository


# ── F1: atomic, retry-safe gap application ──────────────────────────────────


def test_f1_a_gap_promotion_interrupted_before_its_row_applies_its_claim_once_on_retry(tmp_path, monkeypatch):
    paths, vault, repository = _vault(tmp_path)
    _answer(vault, repository, ITEM, 4.0, minutes=5)
    control_paths, control_vault, control_repo = _vault(tmp_path, "control")
    _answer(control_vault, control_repo, ITEM, 4.0, minutes=5)
    _gap(control_paths.root, control_repo)
    once = _mastery(control_repo)

    original = Repository.insert_question_promotion
    calls = {"n": 0}

    def crash_once(self, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("the process died before the promotion row")
        return original(self, **kwargs)

    monkeypatch.setattr(Repository, "insert_question_promotion", crash_once)
    with pytest.raises(RuntimeError):
        _gap(paths.root, repository)
    assert len(_gap_claims(repository)) == 1
    assert _mastery(repository) == pytest.approx(once)  # the claim and its effect committed together

    result = _gap(paths.root, repository)

    claims = _gap_claims(repository)
    assert len(claims) == 1 and result["learner_claim_id"] == claims[0]["id"]
    assert claims[0]["id"].endswith("_gap_ev_gap")
    assert _mastery(repository) == pytest.approx(once)  # not merged a second time


def test_f1_a_concurrent_writer_cannot_land_between_the_gap_read_and_write(tmp_path, monkeypatch):
    import learnloop.learner.mastery as mastery

    paths, vault, repository = _vault(tmp_path)
    _answer(vault, repository, ITEM, 4.0, minutes=5)
    original = mastery.apply_claim_evidence
    blocked: list[str] = []

    def contend(state, **kwargs):
        # A sidecar attempt committing its mastery update right now.
        other = sqlite3.connect(paths.sqlite_path, timeout=0)
        try:
            other.execute("UPDATE learning_object_mastery SET logit_mean = 9.0 WHERE learning_object_id = ?", (LO,))
            other.commit()
        except sqlite3.OperationalError as error:
            blocked.append(str(error))
        finally:
            other.close()
        return original(state, **kwargs)

    monkeypatch.setattr(mastery, "apply_claim_evidence", contend)
    _gap(paths.root, repository)

    assert blocked and "locked" in blocked[0]
    assert _mastery(repository)[0] != 9.0


def test_f1_off_the_predecessor_writes_a_plain_claim(tmp_path):
    paths, _vault_, repository = _vault(tmp_path, toml=OFF)
    _gap(paths.root, repository)
    (claim,) = _gap_claims(repository)
    assert "_gap_" not in claim["id"]


# ── F2: an interrupted activation is completed, never left half-done ────────


def _predecessor_vault_with_claims(tmp_path, name):
    paths, vault, repository = _vault(tmp_path, name, version=PREDECESSOR)
    _answer(vault, repository, ITEM, 4.0, minutes=5)
    repository.insert_learner_claim({
        "claim_type": "self_rating", "scope_type": "learning_object", "scope_id": LO, "evidence_family": "recall",
        "claimed_level": 0.05, "prior_pseudo_count": 4.0, "source": "manual_cli", "created_at": _iso(1),
    })
    _gap(paths.root, repository, "ev_cold", item="pi_diag_easy")  # inert on the predecessor
    return paths


def _journal(paths):
    return paths.sqlite_path.with_name(paths.sqlite_path.name + ".claim-fixes-activation")


def _die_after_publication(root):
    import learnloop.claim_fixes_upgrade as upgrade

    real = upgrade._publish_algorithm_version

    def publish_then_die(*args, **kwargs):
        real(*args, **kwargs)
        os._exit(17)  # no handler runs: the transaction never commits

    upgrade._publish_algorithm_version = publish_then_die
    upgrade.upgrade_to_claim_fixes(root)


def _crash_upgrade(paths):
    process = multiprocessing.get_context("fork").Process(target=_die_after_publication, args=(paths.root,))
    process.start()
    process.join(60)
    assert process.exitcode == 17


@pytest.mark.filterwarnings("ignore:This process .* is multi-threaded:DeprecationWarning")
@pytest.mark.parametrize("completion", ["upgrade_again", "desktop_start"])
def test_f2_a_death_between_publication_and_commit_is_completed_from_the_journal(tmp_path, completion):
    from learnloop.claim_fixes_upgrade import upgrade_to_claim_fixes
    from learnloop_sidecar.context import _recover_claim_fixes_activation

    clean = _predecessor_vault_with_claims(tmp_path, "clean")
    assert upgrade_to_claim_fixes(clean.root).upgraded
    expected = _all_mastery(clean.sqlite_path)

    crashed = _predecessor_vault_with_claims(tmp_path, "crashed")
    before = _all_mastery(crashed.sqlite_path)
    _crash_upgrade(crashed)

    # The state the review describes: the successor's label over the
    # predecessor's database, and now the journal that says so.
    assert load_vault(crashed.root).config.algorithms.algorithm_version == TAG
    assert _all_mastery(crashed.sqlite_path) == before != expected
    assert _journal(crashed).exists()

    if completion == "upgrade_again":
        result = upgrade_to_claim_fixes(crashed.root)
        assert result.upgraded and result.notes[0] == f"completed the interrupted activation of {TAG}"
    else:
        assert _recover_claim_fixes_activation(crashed.root, load_vault(crashed.root))

    assert _all_mastery(crashed.sqlite_path) == pytest.approx(expected)
    assert not _journal(crashed).exists()
    again = upgrade_to_claim_fixes(crashed.root)
    assert not again.upgraded and again.problems == [f"vault is already {TAG}"]


def test_f2_failures_before_or_after_the_rename_leave_the_predecessor_and_no_journal(tmp_path, monkeypatch):
    import learnloop.claim_fixes_upgrade as upgrade

    before_rename = _predecessor_vault_with_claims(tmp_path, "before")
    state = _all_mastery(before_rename.sqlite_path)
    monkeypatch.setattr(upgrade.registry_service, "refresh", lambda *a, **k: (_ for _ in ()).throw(OSError("disk")))
    with pytest.raises(OSError):
        upgrade.upgrade_to_claim_fixes(before_rename.root)
    assert load_vault(before_rename.root).config.algorithms.algorithm_version == PREDECESSOR
    assert _all_mastery(before_rename.sqlite_path) == state and not _journal(before_rename).exists()
    monkeypatch.undo()

    after_rename = _predecessor_vault_with_claims(tmp_path, "after")
    state = _all_mastery(after_rename.sqlite_path)
    real = upgrade._fsync_directory
    calls = {"n": 0}

    def fail_second(directory):
        calls["n"] += 1
        if calls["n"] == 2:  # the config's directory fsync, after the rename
            raise OSError("fsync")
        real(directory)

    monkeypatch.setattr(upgrade, "_fsync_directory", fail_second)
    with pytest.raises(OSError):
        upgrade.upgrade_to_claim_fixes(after_rename.root)
    assert load_vault(after_rename.root).config.algorithms.algorithm_version == PREDECESSOR
    assert _all_mastery(after_rename.sqlite_path) == state and not _journal(after_rename).exists()


def test_f2_a_journal_left_after_the_commit_is_just_removed(tmp_path):
    from learnloop.claim_fixes_upgrade import complete_interrupted_activation, upgrade_to_claim_fixes

    paths = _predecessor_vault_with_claims(tmp_path, "vault")
    assert upgrade_to_claim_fixes(paths.root).upgraded
    state = _all_mastery(paths.sqlite_path)
    _journal(paths).write_text(f'{{"predecessor": "{PREDECESSOR}", "target": "{TAG}"}}', encoding="utf-8")

    assert complete_interrupted_activation(paths.root) is None
    assert not _journal(paths).exists() and _all_mastery(paths.sqlite_path) == state


# ── F3: activation equals a same-version rebuild ────────────────────────────


@pytest.mark.parametrize("with_attempts", [True, False])
def test_f3_activation_reseeds_claimed_los_without_attempts_as_a_rebuild_does(tmp_path, with_attempts):
    from learnloop.claim_fixes_upgrade import upgrade_to_claim_fixes

    paths, vault, repository = _vault(tmp_path, version=PREDECESSOR)
    if with_attempts:
        _answer(vault, repository, ITEM, 4.0, minutes=5)
    _gap(paths.root, repository, "ev_cold", item="pi_diag_easy")
    inert = _mastery(repository, "lo_diag")
    assert inert[0] == 0.0  # the predecessor's defect: the gap did nothing

    result = upgrade_to_claim_fixes(paths.root)

    assert result.upgraded and any("lo_diag" in note and "without attempts" in note for note in result.notes)
    upgraded = _all_mastery(paths.sqlite_path)
    assert upgraded["lo_diag"][0] < 0.0
    assert _all_mastery(_rebuild(paths).sqlite_path) == pytest.approx(upgraded)


# ── F4: a claim never lowers a variance ─────────────────────────────────────


def test_f4_a_gap_on_a_cold_lo_moves_the_mean_and_keeps_the_cold_variance(tmp_path):
    from learnloop.learner.mastery import logit

    paths, vault, repository = _vault(tmp_path)
    cold = _mastery(repository)
    assert cold == (0.0, vault.config.mastery.cold_start_prior_logit_variance, 0)

    _gap(paths.root, repository)

    mean, variance, evidence = _mastery(repository)
    assert mean == pytest.approx(logit(vault.config.tutor_promotion.gap_claim_level))
    assert variance >= cold[1] and evidence == 0


def test_f4_a_claim_seed_never_starts_below_the_cold_variance_and_replay_agrees(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    _gap(paths.root, repository, minutes=1)
    _answer(vault, repository, ITEM, 4.0, minutes=5)
    live = _mastery(repository)

    assert _mastery(_rebuild(paths)) == pytest.approx(live, rel=1e-12, abs=1e-12)


@pytest.mark.parametrize("variant", ["switch_off", "below_tag"])
def test_f4_off_the_predecessor_seed_variance_is_kept(tmp_path, variant):
    paths, vault, repository = _vault(
        tmp_path, version=PREDECESSOR if variant == "below_tag" else TAG, toml=OFF if variant == "switch_off" else None,
    )
    repository.insert_learner_claim({
        "claim_type": "self_rating", "scope_type": "learning_object", "scope_id": LO, "evidence_family": "recall",
        "claimed_level": 0.9, "prior_pseudo_count": 2.0, "source": "learner_report", "created_at": _iso(1),
    })
    state = reanchor_mastery_from_claim(vault, repository, LO, claimed_level=0.9, prior_pseudo_count=2.0,
                                        now_iso=_iso(1))
    assert state.logit_variance == vault.config.mastery.claim_prior_min_variance


# ── F5: same-second claims and attempts keep the order they were written ────


@pytest.mark.parametrize("order", ["attempt_then_gap", "gap_then_attempt"])
def test_f5_a_gap_and_an_attempt_in_the_same_second_replay_in_written_order(tmp_path, order):
    paths, vault, repository = _vault(tmp_path)
    if order == "attempt_then_gap":
        _answer(vault, repository, ITEM, 1.0, minutes=5)
        _gap(paths.root, repository, minutes=5)
    else:
        _gap(paths.root, repository, minutes=5)
        _answer(vault, repository, ITEM, 1.0, minutes=5)
    (claim,) = _gap_claims(repository)
    (attempt,) = repository.list_attempts_by_learning_object(LO)
    assert claim["created_at"] == attempt["created_at"]  # one-second stamps tie
    live = _mastery(repository)

    assert _mastery(_rebuild(paths)) == pytest.approx(live, rel=1e-12, abs=1e-12)


def test_f5_a_rung_request_claim_still_precedes_its_same_second_attempt(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    repository.insert_learner_claim({
        "claim_type": "self_rating", "scope_type": "learning_object", "scope_id": LO, "evidence_family": "recall",
        "claimed_level": 0.85, "prior_pseudo_count": 2.0, "source": "rung_variant_request", "created_at": _iso(5),
    })
    reanchor_mastery_from_claim(vault, repository, LO, claimed_level=0.85, prior_pseudo_count=2.0, now_iso=_iso(5))
    _answer(vault, repository, ITEM, 4.0, minutes=5)
    live = _mastery(repository)

    assert _mastery(_rebuild(paths)) == pytest.approx(live, rel=1e-12, abs=1e-12)
