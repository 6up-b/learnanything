// UX Phase 2 fix round 3 (whole-stage verify 20261021-130232-Uk06Al): the one
// assertion every retry wired to the shell's Try again must pass. A retry is
// self-contained: calling it issues the failed request again, whatever the
// screen shows now and whether it is still mounted. It rejects while the
// request fails, and resolves RETRY_RAN only once the request ran and
// succeeded. Test-only (imported by *.test.tsx files).
import { expect, type Mock } from "vitest";
import { RETRY_RAN } from "../errors";

export interface ReportedRetry {
  source?: string | null;
  retry?: (() => Promise<unknown>) | null;
}

/** The report handed to `onError` with the given sentence (the latest one). */
export function reportFor(onError: Mock, message: string): ReportedRetry {
  const calls = onError.mock.calls.filter((call) => call[0] === message);
  expect(calls.length, `onError was called with "${message}"`).toBeGreaterThan(0);
  return (calls[calls.length - 1][1] ?? {}) as ReportedRetry;
}

export async function expectRetryIssuesRequest(
  report: ReportedRetry,
  request: Mock,
  outcome: "fails" | "succeeds"
): Promise<void> {
  expect(report.source, "an error with a retry names its source").toBeTruthy();
  expect(typeof report.retry, "the report carries a retry").toBe("function");
  const before = request.mock.calls.length;
  const result = report.retry!();
  if (outcome === "succeeds") await expect(result).resolves.toBe(RETRY_RAN);
  else await expect(result).rejects.toBeTruthy();
  expect(request.mock.calls.length, "the retry issued the failed request again").toBe(before + 1);
}
