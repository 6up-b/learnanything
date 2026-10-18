"""Builders and fake models for Reader workbench RW2b's tests (no network).

``CheckFake`` answers ``workbench_check`` from a queue of answers (dicts or
callables of the prompt's context); with the queue empty it reads the CDF
item's two steps as H2a's fakes do: step 1 valid (reaching the map's ``cdf``
node on the reference route), step 2 questionable, with an error-kind guess
and two rival readings. ``wb_answer`` is the hint writer's answer for a
workbench request: H2a's ``good_answer`` with its quotes taken from the
numbered steps (each quote inside one step, the about-step quoted, what
stands in a standing step). Plumbing checks only, never evidence about
check or hint quality.
"""

from __future__ import annotations

import json
from contextlib import closing
import sqlite3
from typing import Any, Callable, Mapping

from learnloop.ai.execution import report_call_usage
from learnloop.ai.isolation import TOOL_FREE
from learnloop.ai.transport import BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, STRUCTURED_COMPLETION
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY
from tests.hint_fakes import ITEM, ChooserFake, WriterFake, good_answer, hint_vault, prefer, store_map
from tests.structured_ai import StructuredClientFake, _request_context

STEP_1 = "F(x) = x^2 on [0, 1]"
STEP_2 = "so P(X <= 1/2) = F(1/2) + 1"

__all__ = ["CheckFake", "ITEM", "STEP_1", "STEP_2", "call", "check_answer", "help_rows", "open_problem",
           "run_job", "sidecar", "wb_answer"]


def _transformation(**values: str) -> dict[str, str]:
    base = {"kind": "", "expression": "", "result": "", "variable": "", "value": "", "lower": "", "upper": "",
            "relation": ""}
    base.update(values)
    return base


def step_check(step: int, verdict: str, *, reason: str = "", quote: str = "", depends_on: list[int] | None = None,
               assumption: str = "", node: str = "", route: str = "", transformation: dict[str, str] | None = None
               ) -> dict[str, Any]:
    return {"step": step, "verdict": verdict, "reason": reason, "quote": quote, "depends_on": depends_on or [],
            "assumption": assumption, "map": {"node_id": node, "route_id": route},
            "transformation": transformation or _transformation()}


def check_answer(context: Mapping[str, Any]) -> dict[str, Any]:
    """The default check of the CDF item's steps (step 1 valid, step 2 questionable)."""

    steps = context["steps"]
    rows = []
    for entry in steps:
        number = entry["step"]
        if number == 1:
            rows.append(step_check(1, "valid", reason="the CDF of the density", node="cdf" if context.get(
                "approach_map") else "", route="r_ref" if context.get("approach_map") else ""))
        elif number == 2:
            rows.append(step_check(2, "questionable", reason="a CDF value is already a probability",
                                   quote="F(1/2) + 1", depends_on=[1]))
        else:
            rows.append(step_check(number, "unchecked", depends_on=[1] if number > 1 else []))
    questionable = 2 if any(entry["step"] == 2 for entry in steps) else 0
    return {"steps": rows, "first_questionable_step": questionable,
            "error_kind_guess": "conceptual" if questionable else "",
            "error_kind_reason": "adds one to a probability" if questionable else "",
            "error_readings": [{"kind": "conceptual", "statement": "Treats a CDF value as a density to integrate"},
                               {"kind": "transcription", "statement": "Copied an extra term from the line above"}]
            if questionable else [],
            "assumptions": ["X has density 2x on [0, 1]"]}


Answer = Mapping[str, Any] | Callable[[Mapping[str, Any]], Mapping[str, Any]]


class CheckFake(StructuredClientFake):
    provider_name = "fake_checker"
    provider_type = "chatgpt_plan"
    model = "fake-check-model"

    def __init__(self, answers: list[Answer] | None = None, *, provider_type: str = "chatgpt_plan",
                 fail: Exception | None = None) -> None:
        self.answers = list(answers or [])
        self.provider_type = provider_type
        self.fail = fail
        self.contexts: list[dict[str, Any]] = []
        self.prompts: list[str] = []

    def supports(self, capability: str) -> bool:
        return capability in {STRUCTURED_COMPLETION, BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, TOOL_FREE}

    def complete(self, request: Any) -> Any:
        context = json.loads(json.dumps(_request_context(request.prompt, request.purpose)))
        self.contexts.append(context)
        self.prompts.append(request.prompt)
        report_call_usage({"input_tokens": len(request.prompt) // 4, "output_tokens": 200,
                           "resolved_model": self.model})
        if self.fail is not None:
            raise self.fail
        answer = self.answers.pop(0) if self.answers else check_answer
        payload = answer(context) if callable(answer) else answer
        return request.result_model.model_validate(payload)

    @property
    def calls(self) -> int:
        return len(self.contexts)


def wb_answer(context: Mapping[str, Any]) -> dict[str, Any]:
    """H2a's good answer for the chosen kind, its quotes taken from the
    workbench's numbered steps (module docstring)."""

    payload = dict(good_answer(context))
    block = context.get("workbench") or {}
    steps = block.get("steps") or []
    texts = {entry["step"]: entry["text"] for entry in steps}
    order = [entry["step"] for entry in steps]
    standing = [entry["step"] for entry in steps if entry.get("stands")]
    kind = context.get("chosen", {}).get("kind")
    about_n = block.get("about_step") or (order[-1] if order else None)
    about = texts.get(about_n, "")
    questionable_n = block.get("first_questionable_step")
    if not questionable_n and kind in ("localize", "error_specific") and about_n:
        questionable_n = about_n
    if questionable_n and about_n and questionable_n != about_n:
        # A hint about another step (e.g. "that's not where I'm stuck") does
        # not localize the questionable one again.
        questionable_n = None
    questionable = texts.get(questionable_n, "") if questionable_n else ""
    stands_n = block.get("continue_from_step")
    if questionable_n and stands_n is not None and stands_n >= questionable_n:
        earlier = [number for number in standing if number < questionable_n]
        stands_n = earlier[-1] if earlier else None
    stands = texts.get(stands_n, "") if stands_n else ""
    placement = dict(payload["placement"])
    if context.get("chosen", {}).get("downgrade"):
        stands = ""
    placement.update({"stands_quote": stands, "first_questionable_quote": questionable,
                      "quotes": [about] if about else []})
    if not steps:
        placement.update({"stands_quote": "", "first_questionable_quote": "", "quotes": []})
    payload["placement"] = placement
    if kind == "localize" and questionable:
        payload["hint_md"] = f"Look again at: {questionable}"
    if kind == "error_specific" and questionable:
        payload["hint_md"] = f"In '{questionable}' a CDF value is a probability on its own."
    return payload


def call(ctx: SidecarContext, name: str, params: dict[str, Any]) -> Any:
    import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def sidecar(tmp_path: Any, config: str = "", *, map_: bool = True, writer: Any = None, check: Any = None,
            chooser: Any = None, maps_enabled: bool = True):
    """The CDF item's vault with a map, a sidecar running jobs inline, the
    hint writer, check and chooser fakes, and an open practice session."""

    paths = hint_vault(tmp_path, config='[hints]\nchoice_policy = "sample"\n' + config)
    if not maps_enabled:
        toml = paths.root / "learnloop.toml"
        toml.write_text(toml.read_text().replace("build_on_serve = false\n", "build_on_serve = false\nenabled = false\n", 1))
    if map_:
        store_map(paths)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    ctx.hints_inline = True
    ctx.hint_seed = "seed-wb"
    ctx.hint_writer_client = writer if writer is not None else WriterFake([wb_answer] * 12)
    ctx.workbench_check_client = check if check is not None else CheckFake()
    ctx.hint_chooser_client = chooser if chooser is not None else ChooserFake(prefer("next_step@L3", 0.6))
    session = call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    return paths, ctx, session


def open_problem(ctx: SidecarContext, steps: tuple[str, ...] = (STEP_1, STEP_2), *, origin: str = "practice",
                 entry: str = "practice_screen") -> tuple[str, list[str]]:
    """A bound problem with ``steps``; returns its id and the steps' chain ids."""

    view = call(ctx, "workbench.open", {"origin": origin, "entry": entry, "practiceItemId": ITEM,
                                        "stemMd": "Find P(X <= 1/2)."})["session"]
    chains = []
    after = None
    for index, body in enumerate(steps):
        saved = call(ctx, "workbench.save_step", {"sessionId": view["sessionId"], "clientIdempotencyKey": f"s{index}",
                                                  "op": "add", "bodyMd": body, "afterStepId": after})
        step = saved["step"] if "step" in saved else saved
        chain = step.get("chainId") or step.get("chain_id")
        chains.append(chain)
        after = chain
    return view["sessionId"], chains


def run_job(ctx: SidecarContext, started: Mapping[str, Any]) -> dict[str, Any]:
    """Read a job once (jobs run inline under ``ctx.hints_inline``)."""

    if started.get("jobId") is None:
        return dict(started["result"] or {})
    payload = call(ctx, "workbench.help_job", {"jobId": started["jobId"]})
    assert payload["state"] == "done", payload
    return dict(payload["result"] or {})


def help_rows(paths: Any, session_id: str | None = None) -> list[dict[str, Any]]:
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        sql = "SELECT * FROM help_assists WHERE surface = 'workbench'"
        params: tuple[Any, ...] = ()
        if session_id:
            sql += " AND workbench_session_id = ?"
            params = (session_id,)
        return [dict(row) for row in connection.execute(sql + " ORDER BY requested_at, rowid", params)]
