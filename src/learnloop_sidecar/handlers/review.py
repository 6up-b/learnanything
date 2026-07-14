from __future__ import annotations

from learnloop.services.learner_review_feed import build_learner_review_feed
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.registry import method


@method("get_review_log")
def get_review_log_handler(ctx: SidecarContext, _params: ParamsModel):
    vault, repository = ctx.require_vault()
    return versioned(build_learner_review_feed(vault, repository))
