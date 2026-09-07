-- Generation/application and learner-visible completion are separate durable phases.
CREATE TABLE attempt_completion_work (
    attempt_id TEXT PRIMARY KEY REFERENCES practice_attempts(id),
    submission_id TEXT UNIQUE,
    session_id TEXT,
    practice_item_id TEXT NOT NULL,
    result_json TEXT NOT NULL,
    route_json TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'completed')),
    collection_version TEXT NOT NULL DEFAULT 'learnloop-events-v1',
    created_at TEXT NOT NULL,
    completed_at TEXT
);
CREATE INDEX idx_attempt_completion_pending ON attempt_completion_work(status, created_at);
