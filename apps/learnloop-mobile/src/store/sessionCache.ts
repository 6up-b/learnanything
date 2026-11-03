// The cached session id and what a closed app must find again (§0): which session this phone was
// in, and a submit it left mid-grade. Nothing here is learner state of record.
const SESSION_KEY = "learnloop.session";
const PENDING_KEY = "learnloop.pendingSubmit";

export interface PendingSubmit {
  readonly jobId: string;
  readonly submissionId: string;
  readonly sessionId: string;
  readonly practiceItemId: string;
}

function read<T>(key: string): T | null {
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    return null;
  }
}

export function cachedSessionId(): string | null {
  return read<string>(SESSION_KEY);
}

export function cacheSessionId(sessionId: string | null): void {
  if (sessionId) localStorage.setItem(SESSION_KEY, JSON.stringify(sessionId));
  else localStorage.removeItem(SESSION_KEY);
}

export function pendingSubmit(): PendingSubmit | null {
  return read<PendingSubmit>(PENDING_KEY);
}

export function rememberPendingSubmit(pending: PendingSubmit | null): void {
  if (pending) localStorage.setItem(PENDING_KEY, JSON.stringify(pending));
  else localStorage.removeItem(PENDING_KEY);
}

export function clearSessionCache(): void {
  localStorage.removeItem(SESSION_KEY);
  localStorage.removeItem(PENDING_KEY);
}
