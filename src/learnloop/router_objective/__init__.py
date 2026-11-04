"""The router objective (docs/specs/spec_router_objective_v1.md). RO0, logging what is being lost (§4):

* :mod:`~learnloop.router_objective.question_state`: rows 1, 2 and 3 at an ask;
* :mod:`~learnloop.router_objective.ask_availability`: row 3 at a serve, and its later changes;
* :mod:`~learnloop.router_objective.exposure`: row 4, who initiated a source exposure;
* :mod:`~learnloop.router_objective.sessions`: rows 7 and 8, availability and how a session ended;
* :mod:`~learnloop.router_objective.decision_state`: rows 9 and 13, what the router believed at a decision;
* :mod:`~learnloop.router_objective.cold_timing`: row 10, how a check's delay was chosen and why it was not served;
* :mod:`~learnloop.router_objective.goal_lifecycle`: row 11, goals' lifecycle seen at load;
* :mod:`~learnloop.router_objective.trajectory`: row 12, decision-to-next-state links.

Additive at every algorithm version behind ``[router_objective] receipts``. Nothing serving, scheduling or
certification reads any of it; the one offline reader is the probability arms' card
(:mod:`learnloop.field.probability_states`), which reads ``hints_used_before``.
"""
