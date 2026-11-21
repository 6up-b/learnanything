"""Synthetic stored offers and delayed receipts for the read-only report."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from learnloop.clock import FrozenClock
from learnloop.curriculum import commitments as C
from learnloop.db.repositories import Repository

from tests.helpers import create_basic_vault

EARLY = "2026-10-31T09:00:00Z"
LATER = "2026-11-06T09:00:00Z"
NOW = "2026-11-10T09:00:00Z"
SECRET = "PRIVATE-CANARY-learner-prose"
LO = "lo_svd_definition"
PREFIX = "lesson_offer:"


def seed_report_vault(root, *, presentation_at="2026-11-05T08:59:00Z"):
    paths = create_basic_vault(root)
    repo = Repository(paths.sqlite_path)
    entries = [{"purpose": "retention", "node_id": "missing", "missing": True}]
    for name, purpose in (("cold", "retention"), ("helped", "retention"), ("pending", "retention"),
                          ("stopped", "transfer")):
        c = C.create_commitment(
            repo, action="test_me_later", intent_text=SECRET,
            targets=[{"target_kind": "legacy_practice_item", "target_ref": name, "role": "required"}],
            depth_preset="keep_in_touch", due_hint="2026-11-04T09:00:00Z",
            clock=FrozenClock(datetime(2026, 11, 1, 9, tzinfo=UTC)))
        entries.append({"purpose": purpose, "node_id": name, "learning_object_id": LO,
                        "item_id": name, "commitment_id": c.id, "due": "2026-11-04"})
        if name == "stopped":
            C.retire(repo, commitment_id=c.id, clock=FrozenClock(datetime(2026, 11, 3, 9, tzinfo=UTC)))
    with repo.connection() as db:
        for lesson, closed, checks in (("closed", True, entries), ("open", False, []),
                                       ("alternative", True, [{"purpose": "retention", "missing": True}])):
            db.execute(
                "INSERT INTO lessons(id, driver, origin, entry, goal_text, goal_json, learning_object_ids_json, "
                "doctrine_version, brief_version, algorithm_version, opened_at, closed_at, close_reason) "
                "VALUES (?, 'desktop', 'learner_pick', 'learning_object', ?, '{}', ?, 'd', 'b', 'v', ?, ?, ?)",
                (lesson, SECRET, json.dumps([LO]), "2026-11-01T08:00:00Z",
                 "2026-11-01T09:00:00Z" if closed else None, "goal_reached" if closed else None))
            if closed:
                db.execute("INSERT INTO lesson_receipts VALUES (?, 'lesson_receipt_v1', 'goal_reached', ?, ?)",
                           (lesson, json.dumps({"delayed_checks": checks}), "2026-11-01T09:00:00Z"))
        for item, hints, correctness in (("cold", 0, 0.0), ("helped", 1, 1.0)):
            db.execute(
                "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, "
                "attempt_type, hints_used, correctness, latency_seconds, created_at) "
                "VALUES (?, ?, ?, 'short_answer', 'independent_attempt', ?, ?, 60, '2026-11-05T09:00:00Z')",
                (f"answer-{item}", item, LO, hints, correctness))
        statuses = ["accepted", "accepted", "declined", "ignored", "superseded", "never_shown",
                    "chose_alternative", "unanswered", "not_drawn"]
        for i, status in enumerate(statuses):
            did, ref = f"decision-{i}", f"{PREFIX}{i}"
            at = LATER if i == 3 else EARLY
            candidates = [{"ref": ref, "learning_object_ids": [LO], "label": SECRET}, {"ref": "stop_for_today"}]
            if i == 8:
                candidates.append({"ref": f"{PREFIX}extra", "learning_object_ids": [LO]})
            db.execute(
                "INSERT INTO router_decisions(id, receipt_key, decision_kind, surface, mode, policy, "
                "algorithm_version, log_version, snapshot_hash, candidates_json, exclusions_json, "
                "candidate_count, chosen_ref, propensity, propensity_kind, detail_json, created_at) "
                "VALUES (?, ?, 'plan_block', 'today', 'objective', 'p', 'mvp-0.61', 'v', 'h', ?, '[]', ?, "
                "?, 1, 'deterministic', '{}', ?)",
                (did, did, json.dumps(candidates), len(candidates), ref if i < 8 else "stop_for_today", at))
            if status not in ("unanswered", "not_drawn"):
                detail = ({"superseded_by_decision": "new"} if status == "superseded" else
                          {"withdrawn": "never_shown"} if status == "never_shown" else {})
                lesson = {0: "closed", 1: "open", 6: "alternative"}.get(i)
                db.execute(
                    "INSERT INTO router_suggestion_responses(id, decision_id, response, candidate_ref, "
                    "learning_object_ids_json, lesson_id, responded_at, detail_json, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (f"response-{i}", did, "expired" if detail else status,
                     "another-topic" if i == 6 else ref, json.dumps([LO]), lesson, LATER, json.dumps(detail), LATER))
            if i in (0, 1, 2, 3, 6):
                db.execute("INSERT INTO attention_blocks(id,action,subtype,budget_minutes,content_hash,created_at) "
                           "VALUES (?, 'instruct', 'lesson_offer', 15, 'h', ?)", (f"shown-{i}", at))
                for ordinal, surface in enumerate(("today", "offer_page")):
                    db.execute("INSERT INTO attention_block_events VALUES (?, ?, ?, 'offer_shown', ?, ?)",
                               (f"shown-{i}-{ordinal}", f"shown-{i}", ordinal,
                                json.dumps({"decision_id": did, "surface": surface}), LATER))
        for entry in entries[1:3]:
            item = entry["item_id"]
            db.execute("INSERT INTO attention_blocks(id,commitment_id,action,subtype,budget_minutes,content_hash,created_at) "
                       "VALUES (?, ?, 'retrieve', 'check_once', 5, 'h', ?)",
                       (f"check-{item}", entry["commitment_id"], LATER))
            db.execute("INSERT INTO plan_presentations(id,block_id,practice_item_id,origin,served_at) "
                       "VALUES (?, ?, ?, 'chooser', ?)",
                       (f"presentation-{item}", f"check-{item}", item, presentation_at))
        db.commit()
    return paths, repo


def add_trace(repo, decision_id, trace, *, at=EARLY):
    from learnloop.db.stores.router_objective import insert_trace
    from learnloop.router_objective.trace import assemble

    trace = {"mixing": {"chosen": "lesson_offer:0"}, "versions": {"kappa": {"kappa0": 0.0}}, **trace}
    row = assemble(trace, decision_id=decision_id, decision_kind="plan_block", created_at=at,
                   decision_state_id=None, algorithm_version="mvp-0.61", local_date=at[:10], session_id=None)
    with repo.connection() as db:
        insert_trace(db, row)
        db.commit()
