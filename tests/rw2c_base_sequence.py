"""Reader RW2c's switch-off pin: one workbench help sequence, run as a script
against EITHER the base code (``git archive 7e7bdff1b``) or the tip with all
four RW2c switches off, so a test can require both to give the same inputs
and payloads (``test_rw2c_switch_off.py``).

The sequence: a Reader problem, a check, the ladder's suggestion, a level-3
hint (its bridge to the book, three verified passages), an edited step, a
second check, a second suggestion and level-3 hint (with history now on the
item's facet), the restored help state and the problem. It records what the
hint writer was sent (every prompt context), what the chooser was sent
(every state), every RPC payload, the help rows and the app config DTO,
with ULIDs, timestamps and latencies normalized.

Usage: ``python -m tests.rw2c_base_sequence <vault-dir>``; prints JSON.
Only APIs present at ``7e7bdff1b`` are used. Fakes only: no model.
"""

from __future__ import annotations

from contextlib import closing
import json
from pathlib import Path
import re
import sqlite3
import sys
from typing import Any

SWITCHES = ("help_outcomes_enabled", "examples_enabled", "compare_methods_enabled", "passage_draw_enabled")
_ULID = re.compile(r"[0-9A-HJKMNP-TV-Z]{26}")
_TIME = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})?")
_HEX = re.compile(r"\b[0-9a-f]{32,64}\b")
_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_VOLATILE = {"latency_ms", "elapsed_ms", "timings_ms", "latencyMs", "verification_ms", "over_soft_deadline",
             "seconds_since_last_hint"}


def normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: ("<volatile>" if key in _VOLATILE else normalize(item)) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalize(item) for item in value]
    if isinstance(value, str):
        return _HEX.sub("<hex>", _TIME.sub("<ts>", _ULID.sub("<id>", _UUID.sub("<uuid>", value))))
    return value


class BridgeFake:
    def __call__(self, vault, repository, *, context, question_md, learning_object_ids, item):
        spans = [{"span_id": f"s{index}", "extraction_id": "ext", "label": f"Book · §5.{index}",
                  "text": "a step like yours"} for index in range(1, 4)]
        # T6's manifest names the spans its judge passed (RW2c fix round 2, 4).
        return spans, {"basis": "retrieved_verified", "span_keys": [f"ext/s{index}" for index in range(1, 4)]}


def main(root: Path) -> dict:
    import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
    from learnloop.config.schema import WorkbenchConfig
    from learnloop_sidecar.context import config_dto
    from tests.hint_fakes import ChooserFake, WriterFake, prefer
    from tests.workbench_help_fakes import call, open_problem, run_job, sidecar, wb_answer

    present = [name for name in SWITCHES if name in WorkbenchConfig.model_fields]
    config = ("[workbench]\n" + "".join(f"{name} = false\n" for name in present)) if present else ""
    writer = WriterFake([wb_answer] * 8)
    chooser = ChooserFake(prefer("next_step@L3", 0.6))
    paths, ctx, _session = sidecar(root, config, writer=writer, chooser=chooser)
    ctx.workbench_bridge_provider = BridgeFake()
    ctx.passage_draw_seed = "seed-pin"
    payloads: dict[str, Any] = {}
    wb, chains = open_problem(ctx, origin="reader", entry="work_through")
    payloads["check_1"] = run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))
    payloads["suggest_1"] = run_job(ctx, call(ctx, "workbench.suggest_help", {"sessionId": wb}))
    hint = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3}))
    payloads["hint_1"] = hint
    if hint.get("bridgeJobId"):
        payloads["bridge_1"] = call(ctx, "workbench.help_job", {"jobId": hint["bridgeJobId"]})
    call(ctx, "workbench.save_step", {"sessionId": wb, "clientIdempotencyKey": "edit", "op": "add",
                                      "bodyMd": "so P = F(1/2)", "afterStepId": chains[-1]})
    payloads["check_2"] = run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))
    payloads["suggest_2"] = run_job(ctx, call(ctx, "workbench.suggest_help", {"sessionId": wb}))
    second = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3}))
    payloads["hint_2"] = second
    if second.get("bridgeJobId"):
        payloads["bridge_2"] = call(ctx, "workbench.help_job", {"jobId": second["bridgeJobId"]})
    payloads["help_state"] = call(ctx, "workbench.help_state", {"sessionId": wb})
    payloads["problem"] = call(ctx, "workbench.get", {"sessionId": wb})
    vault, _repository = ctx.require_vault()
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        rows = [dict(row) for row in connection.execute(
            "SELECT assist_kind, hint_kind, level, chooser, shown, counted_by, options_json, probabilities_json, "
            "drawn_option_json, propensity, seed, policy_version, cited_span_ids_json, body_md "
            "FROM help_assists ORDER BY requested_at, rowid")]
    return normalize({
        "writer_contexts": writer.contexts,
        "writer_prompts": writer.prompts,
        "check_prompts": list(getattr(ctx.workbench_check_client, "prompts", [])),
        "chooser_states": [json.loads(json.dumps(entry["state"], sort_keys=True, default=str))
                           for entry in chooser.calls],
        "payloads": json.loads(json.dumps(payloads, sort_keys=True, default=str)),
        "rows": rows,
        "config_workbench": json.loads(json.dumps(config_dto(vault), default=str)).get("workbench"),
    })


if __name__ == "__main__":
    print(json.dumps(main(Path(sys.argv[1])), sort_keys=True))
