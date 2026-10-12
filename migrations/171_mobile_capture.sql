-- M1 is an inbox, not learner evidence or an automatic practice workflow.
CREATE TABLE mobile_devices (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    scope TEXT NOT NULL CHECK (scope IN ('capture', 'app')),
    token_hash TEXT NOT NULL UNIQUE,
    tailscale_login TEXT,
    created_at TEXT NOT NULL,
    claimed_at TEXT,
    last_seen_at TEXT,
    revoked_at TEXT
);
CREATE TABLE mobile_pairings (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    scope TEXT NOT NULL CHECK (scope IN ('capture', 'app')),
    secret_hash TEXT NOT NULL UNIQUE,
    code_hash TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    consumed_at TEXT,
    failed_attempts INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE mobile_pairing_attempts (
    id INTEGER PRIMARY KEY,
    at TEXT NOT NULL
);
CREATE INDEX mobile_pairing_attempts_at ON mobile_pairing_attempts(at);
CREATE TABLE mobile_pairing_guard (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    locked INTEGER NOT NULL DEFAULT 0 CHECK (locked IN (0, 1))
);
INSERT INTO mobile_pairing_guard(id) VALUES (1);
CREATE TABLE capture_inbox (
    id TEXT PRIMARY KEY,
    client_capture_id TEXT NOT NULL UNIQUE,
    device_id TEXT REFERENCES mobile_devices(id),
    kind TEXT NOT NULL CHECK (kind IN ('text', 'url', 'image')),
    text TEXT,
    url TEXT,
    note TEXT,
    media_sha256 TEXT,
    media_mime TEXT,
    source_app TEXT,
    request_sha256 TEXT NOT NULL,
    captured_at TEXT,
    received_at TEXT NOT NULL,
    purged_at TEXT
);
CREATE INDEX capture_inbox_received ON capture_inbox(received_at, id);
CREATE INDEX capture_inbox_media ON capture_inbox(media_sha256);
CREATE TABLE capture_routes (
    capture_id TEXT PRIMARY KEY REFERENCES capture_inbox(id),
    state TEXT NOT NULL CHECK (state IN ('new', 'routed', 'dismissed', 'processing', 'failed')),
    route TEXT,
    routed_at TEXT,
    dismissed_at TEXT,
    result_refs_json TEXT,
    intent_route TEXT,
    intent_json TEXT,
    media_delete_pending INTEGER NOT NULL DEFAULT 0 CHECK (media_delete_pending IN (0, 1)),
    media_retained_shared INTEGER NOT NULL DEFAULT 0 CHECK (media_retained_shared IN (0, 1)),
    lease_owner TEXT,
    lease_expires_at TEXT
);
CREATE TABLE mobile_request_log (
    id INTEGER PRIMARY KEY,
    device_id TEXT REFERENCES mobile_devices(id),
    endpoint TEXT NOT NULL,
    status INTEGER NOT NULL,
    duration_ms REAL NOT NULL,
    at TEXT NOT NULL
);
CREATE INDEX mobile_request_log_at ON mobile_request_log(at);
