"""What other test files use from ``tests/test_chatgpt_plan_workspace.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json

from tests.chatgpt_plan_fakes import completed_events, served_outputs, tool_call_events
from tests.diagnosis_fakes import prompt_payload


def _read(path: str, start: int | None = None, lines: int | None = None) -> tuple[str, dict]:
    return "read_entry", {"path": path, "start_line": start, "max_lines": lines}


def _diagnosis_answer(body):
    """The fake diagnoser: read INDEX.md, then one failed attempt's file, then answer citing it."""

    outputs = served_outputs(body)
    if not outputs:
        return tool_call_events([_read("INDEX.md")], response_id="d1")
    if len(outputs) == 1:
        path = next(line[2:].split(":")[0] for line in outputs[0].splitlines()
                    if line.startswith("- attempts/") and "att_02_svd_fail" in line)
        return tool_call_events([_read(path)], response_id="d2")
    cited = outputs[-1].splitlines()[1].replace("# Attempt ", "").strip()
    context = prompt_payload(body["input"][0]["content"])["context"]
    events = [{
        "event_index": row["index"], "first_divergence_quote": (row.get("first_divergence") or {}).get("quote"),
        "causal_class": "learner_state",
        "candidate_causes": [{"statement": "The learner leaves V untransposed.", "cause_scope": "learner_state",
                              "prior_weight": 1.0}],
        "registry_match": {"kind": "abstain"}, "history_changed_cause": {"changed": False, "note": ""},
    } for row in context["current_attempt"]["blind_grade"]["error_attributions"]]
    return completed_events(json.dumps({
        "evidence_attempt_ids": [cited], "analysis_md": "The same untransposed factor as before.",
        "event_diagnoses": events, "repair_suggestions": [], "pattern_claims": [],
        "prerequisite_gap_hypotheses": [], "abstentions": [],
    }))
