"""What earlier migrations' upgrade diffs use from the job-progress migration (``tests/test_ingest_job_progress_migration.py``),
kept here because a test file never imports another (``tests/test_test_layout.py``)."""

from __future__ import annotations


JOB_PROGRESS = "ingest_job_progress"
#: What the migration adds (the table and its primary key's autoindex): earlier migrations' "nothing else changed"
#: diffs on the way to head read this.
JOB_PROGRESS_ADDED_OBJECTS = frozenset({JOB_PROGRESS, f"sqlite_autoindex_{JOB_PROGRESS}_1"})
