"""The action router (spec_action_router_v1).

R1 (this package so far) logs decisions on today's serving paths and derives
their outcomes; it chooses nothing. It is a leaf: it imports only the clock, ids,
the outcome contract and the database layer, never the scheduler or substrate,
so the rebuild orchestrator can own its replayer without a package cycle.
Callers hand it what they decided (the scheduler's ``OfferTrace``, the staged
policy's ``DecisionResult``) as plain data.
"""
