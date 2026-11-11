"""What other test files use from ``tests/test_concept_animation_service.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from tests.structured_ai import StructuredClientFake


class _FakeVideoClient:
    """Scripted OpenRouterVideoClient: records requests, serves clips, can fail a shot."""

    provider_name = "openrouter_video"
    model = "google/veo-3.1"

    def __init__(self, *, clips=None, fail_shot: int | None = None, submit_fail_at: int | None = None,
                 cancel_on_checkpoint: bool = False, constraints=None):
        from learnloop.ai.providers.openrouter_video import VideoModelConstraints

        self.clips = clips
        self.fail_shot = fail_shot
        self.submit_fail_at = submit_fail_at
        self.cancel_on_checkpoint = cancel_on_checkpoint
        self.constraints = constraints if constraints is not None else VideoModelConstraints((4, 6, 8), ("720p",), ("16:9",))
        self.requests = []
        self.checkpoints = []
        self.downloaded = []

    def supports(self, capability):
        return capability == "video_generation"

    def model_constraints(self):
        return self.constraints

    def submit(self, request):
        from learnloop.ai.errors import VideoGenerationFailed
        from learnloop.ai.providers.openrouter_video import VideoJob

        if self.submit_fail_at is not None and len(self.requests) + 1 == self.submit_fail_at:
            raise VideoGenerationFailed("OpenRouter video submit failed (HTTP 402): insufficient credits", status="rejected")
        self.requests.append(request)
        return VideoJob(id=f"vid_{len(self.requests)}", status="pending", polling_url=None)

    def wait_all(self, job_ids, *, max_wait_seconds, checkpoint=None):
        from learnloop.ai.errors import VideoGenerationFailed
        from learnloop.ai.providers.openrouter_video import VideoJobStatus

        statuses = [VideoJobStatus(id=job_id, status="in_progress", error=None, cost=None, url_count=0) for job_id in job_ids]
        if checkpoint is not None:
            self.checkpoints.append(list(job_ids))
            checkpoint(statuses, 15.0)
        if self.fail_shot is not None:
            raise VideoGenerationFailed(
                f"shot {self.fail_shot + 1}/{len(job_ids)} failed: content policy",
                status="failed", job_id=job_ids[self.fail_shot], shot_index=self.fail_shot,
            )
        return [VideoJobStatus(id=job_id, status="completed", error=None, cost=0.25, url_count=1) for job_id in job_ids]

    def download(self, job_id, index=0):
        self.downloaded.append(job_id)
        if self.clips is not None:
            return self.clips[int(job_id.split("_")[-1]) - 1]
        return b"mp4-" + job_id.encode()


def _storyboard(shots=3, seconds=6):
    from learnloop.content.authoring.ai_contracts import VideoShot, VideoStoryboard

    return VideoStoryboard(
        title="SVD as stretching",
        narration_md="**Grid.** A grid of dots.",
        shots=[
            VideoShot(
                prompt=f"Shot {index}: a flat grid of glowing blue dots stretches along one axis, then rotates slowly; clean educational animation, dark background.",
                duration_seconds=seconds,
                caption=f"Beat {index}",
            )
            for index in range(1, shots + 1)
        ],
    )


class _FakeStoryboardClient(StructuredClientFake):
    provider_name = "openrouter"
    model = "anthropic/claude-sonnet-4.5"

    def __init__(self, *storyboards):
        self._storyboards = list(storyboards)
        self.contexts: list = []

    def run_video_storyboard(self, context):
        self.contexts.append(context)
        return self._storyboards.pop(0)
