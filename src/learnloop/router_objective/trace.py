"""RO4 §8.8: one decision's trace, each sensor, the objective and the output, and its plain-words reading.

The owner's requirement (Nov 3 2026): "within logs we should be able to see each individual value within the action
router (each sensor), the associated objective function and the ultimate output". :func:`assemble` builds the
immutable ``router_objective_traces`` row (migration 246) from what the decision computed:

```
for each candidate:
  sensors     each value, model and prompt version, receipt id, whether it reached Q̄
  terms       crossed-date reward, undated reward, κ integral, E[V(x′)], T_C, Q̄, Q̄ − V, Q̄ − Q̄(stop), precision
  split       learning, information, return effect (display only; never added)
  filter      if it was filtered: the gate and reason (A1's receipt, by id)
policies:     π_L and its rationale, a_Q, availability, latency, spend, staged and Decider advice
mixing:       posterior mean, sd and n, p_i, ℓ, w_i, weights after fallback, final μ, seed, chosen, which draw chose it
evaluation:   𝒰_i, B_i, m⁰, C⁰, objective version
frontier:     G against minutes for the day's support
versions:     objective, tail, H and T, memory model, κ posterior and regime, ω and c contract versions, snapshot id
```

:func:`explain` renders it in plain words (the "why" surface offers it on demand; the CLI prints it whole). A leaf:
the standard library only.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
from typing import Any

from learnloop.ids import new_ulid

TRACE_VERSION = "router_objective_trace_v1"


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)


def _round(value: Any, digits: int = 6) -> Any:
    if isinstance(value, float):
        return round(value, digits)
    if isinstance(value, Mapping):
        return {key: _round(item, digits) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_round(item, digits) for item in value]
    return value


def assemble(trace: Mapping[str, Any], *, decision_id: str, decision_kind: str, decision_state_id: str | None,
             algorithm_version: str, local_date: str, session_id: str | None, created_at: str) -> dict[str, Any]:
    """The ``router_objective_traces`` row for one decision's trace dict."""

    body = _round(dict(trace))
    content = _canonical(body)
    mixing = body.get("mixing") or {}
    policies = body.get("policies") or {}
    price = (body.get("versions") or {}).get("kappa") or {}
    session = body.get("session") or {}
    return {
        "id": new_ulid(), "decision_id": decision_id, "decision_kind": decision_kind,
        "decision_state_id": decision_state_id, "trace_version": TRACE_VERSION,
        "objective_version": str((body.get("versions") or {}).get("objective") or "unknown"),
        "algorithm_version": algorithm_version, "local_date": local_date, "session_id": session_id,
        "session_minutes": session.get("minutes"), "remembered_minutes": session.get("remembered_minutes"),
        "kappa0": price.get("kappa0"), "kappa_how": price.get("how"), "kappa_regime": price.get("regime"),
        "chosen_ref": str(mixing.get("chosen") or ""), "drawn_component": mixing.get("drawn_component"),
        "propensity": mixing.get("propensity"), "w": mixing.get("w"),
        "numeric_ref": (policies.get("numeric") or {}).get("choice"),
        "llm_status": (policies.get("llm") or {}).get("status"),
        "numeric_status": (policies.get("numeric") or {}).get("status"),
        "stop_in_support": 1 if body.get("stop_in_support") else 0,
        "guard_crossed": 1 if session.get("guard_crossed") else 0,
        "window_closes_at": (body.get("evaluation") or {}).get("window_closes_at"),
        "trace_json": content, "content_hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "created_at": created_at,
    }


def _pct(value: Any) -> str:
    return f"{float(value) * 100:.0f}%" if isinstance(value, (int, float)) else "unknown"


def _split_sentence(mixing: Mapping[str, Any]) -> str:
    """Whether the split between the two suggestions has moved, in plain words (from the weight's own source)."""

    source = str(((mixing.get("posterior") or {}) if isinstance(mixing.get("posterior"), Mapping) else {}
                  ).get("source") or "")
    if source == "posterior":
        return ("The split has moved with what the random check questions showed about whose suggestions helped "
                "more; it keeps moving slowly as more of them are answered.")
    return ("The split has not moved from where it started: it moves only once enough random check questions have "
            "been answered to compare the two suggestions.")


def explain(row: Mapping[str, Any]) -> list[str]:
    """The trace in plain words, for the learner who asks how a block was chosen (glass box on request)."""

    trace = row.get("trace") or {}
    mixing = trace.get("mixing") or {}
    policies = trace.get("policies") or {}
    candidates = trace.get("candidates") or {}
    chosen = str(mixing.get("chosen") or row.get("chosen_ref") or "")
    lines: list[str] = []
    who = {"llm": "the language model's suggestion", "numeric": "LearnLoop's estimate of what helps most",
           "staged": "the usual rule (a model was not available)", "uniform": "a small chance of varying the order"}
    lines.append(f"This was chosen by {who.get(str(mixing.get('drawn_component')), 'the plan')}, "
                 f"which had a {_pct(mixing.get('propensity'))} chance of picking it.")
    w = mixing.get("w")
    if isinstance(w, (int, float)):
        # RO4's open item 3 (landing ruling R5): the split in plain words, never the trace's weight note (an
        # internal sentence naming stages and symbols; it stays in the trace and the report).
        lines.append(f"The language model's suggestion counts for {_pct(w)} and the estimate for {_pct(1 - w)}. "
                     f"{_split_sentence(mixing)}")
    numeric = policies.get("numeric") or {}
    if numeric.get("choice"):
        label = (candidates.get(numeric["choice"]) or {}).get("label") or numeric["choice"]
        lines.append(f"The estimate preferred: {label}.")
    llm = policies.get("llm") or {}
    if llm.get("status") == "answered" and llm.get("favoured"):
        label = (candidates.get(llm["favoured"]) or {}).get("label") or llm["favoured"]
        lines.append(f"The language model preferred: {label}.")
    elif llm.get("status") not in (None, "answered"):
        # IH5 (mvp-0.55): a lone failure's share goes to the other suggestion, not the usual rule.
        if mixing.get("failure_rule") == "other_policy" and numeric.get("status") == "answered":
            lines.append("The language model did not answer in time, so the estimate took its share.")
        else:
            lines.append("The language model did not answer in time, so the usual rule took its share.")
    rows = sorted(candidates.items(), key=lambda pair: -float((pair[1].get("terms") or {}).get("q") or 0.0))
    if rows:
        lines.append("What each option was expected to be worth (in uses of what you know, after effort):")
        for ref, entry in rows:
            terms = entry.get("terms") or {}
            marker = " (chosen)" if ref == chosen else ""
            lines.append(f"- {entry.get('label') or ref}{marker}: {float(terms.get('q') or 0.0):+.4f}, "
                         f"effort {float(terms.get('kappa_integral') or 0.0):.4f}")
    price = (trace.get("versions") or {}).get("kappa") or {}
    session = trace.get("session") or {}
    if session.get("minutes") is not None:
        lines.append(f"You had studied about {float(session['minutes']):.0f} minutes in this session; today's "
                     f"suggested time is {float(session.get('remembered_minutes') or 0):.0f} minutes. Longer sessions "
                     "cost a little more for each extra minute.")
    if price.get("regime") == "seed":
        lines.append("The cost of a minute is still the starting estimate: it is re-set each day from what the next "
                     "minutes are expected to add, until there is evidence of how long you like to study.")
    elif price.get("regime") == "posterior":
        lines.append("The cost of a minute now comes from how you answered offers to stop (including a few made at "
                     "random); it is no longer re-set each day.")
    coin = trace.get("stop_coin") or {}
    if coin.get("arm") == "offer_stop":
        lines.append("Stopping was offered here at random (about 1 in 20 breaks), to learn how long you like to study; "
                     "you can keep going.")
    elif coin.get("arm") == "present_next" and coin.get("served") != (trace.get("mixing") or {}).get("drawn_chosen"):
        lines.append("A next block was shown here at random instead of an offer to stop (about 1 in 20 breaks).")
    residual = trace.get("residual") or {}
    if residual.get("status") == "applied":
        w_hat = float(residual.get("w_hat") or 0.0)
        if w_hat > 0:
            lines.append(f"A correction learned from how earlier choices worked out counts for {_pct(w_hat)} of the "
                         "estimate, as far as the random breaks have shown it helps.")
        else:
            lines.append("A correction learned from how earlier choices worked out is calculated but not used yet: "
                         "it counts only once the random breaks show it helps.")
    for ref, entry in candidates.items():
        offer = entry.get("offer") if isinstance(entry, Mapping) else None
        if not isinstance(offer, Mapping):
            continue
        # Teacher TE3b (spec_teacher_v1 rev 5 §15.1a): a lesson offer, in plain words.
        accept = ((offer.get("sensors") or {}).get("p_accept") or {}).get("mean")
        lines.append(f"A short lesson ({entry.get('label') or ref}) was one of the options. From how you've answered "
                     f"lesson suggestions so far, you'd start it about {_pct(accept)} of the time; its value counts "
                     "both what the lesson would teach and the block you'd do instead if you said not now.")
    if session.get("guard_crossed"):
        lines.append("This session ran long, so stopping was offered among the options; you can keep going.")
    frontier = trace.get("frontier") or {}
    if frontier.get("display"):
        lines.append(f"Predictions for today: {frontier['display']}")
    return lines


def record(connection: Any, *, decision_id: str, decision_kind: str, router_record: Mapping[str, Any] | None,
           config: Any, local_date: str, session_id: str | None, at: str) -> bool:
    """Write the decision's trace beside it, in its transaction (its own savepoint). Nothing without a trace on the
    chooser's record (off, below the tag, a deterministic pick); a refusal rolls back alone with a warning."""

    trace = (router_record or {}).get("objective_trace")
    if not isinstance(trace, Mapping):
        return False
    from learnloop.db.stores import router_objective as store

    state = store.decision_state(connection, decision_id) if store.table_present(connection, store.DECISION_STATE) else None
    row = assemble(trace, decision_id=decision_id, decision_kind=decision_kind,
                   decision_state_id=str(state["id"]) if state else None,
                   algorithm_version=str(config.algorithms.algorithm_version), local_date=local_date,
                   session_id=session_id, created_at=at)
    return store.insert_trace(connection, row)


__all__ = ["TRACE_VERSION", "assemble", "explain", "record"]
