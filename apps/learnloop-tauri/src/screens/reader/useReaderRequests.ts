import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api } from "../../api/client";
import { errorMessage } from "../../errors";

export interface BackgroundRequest {
  id: string;
  status: string;
  preset: string;
  resultJson?: string | null;
  errorJson?: string | null;
}

/** One synthesized source object head, flattened for the Reader rail. */
export interface SynthesizedObject {
  objectId: string;
  objectType: string;
  status: string;
  contentMd: string;
  exactText: string;
  spanId: string | null;
}

const ACTIVE_REQUEST_STATUSES = new Set(["queued", "running", "pending"]);

function hasActiveRequest(requests: BackgroundRequest[]): boolean {
  return requests.some((request) => ACTIVE_REQUEST_STATUSES.has(request.status));
}

function flattenSourceObjects(heads: Array<Record<string, unknown>>): Map<string, SynthesizedObject> {
  const flattened = new Map<string, SynthesizedObject>();
  for (const head of heads) {
    const object = (head.object as Record<string, unknown>) ?? {};
    const version = (head.version as Record<string, unknown>) ?? {};
    const citations = (head.citations as Array<Record<string, unknown>>) ?? [];
    let contentMd = "";
    try {
      const content = JSON.parse(String(version.contentJson ?? "")) as { content_md?: string };
      contentMd = content.content_md ?? "";
    } catch {
      // Stub-era source objects carry no content_md; exactText still renders.
    }
    const objectId = String(object.id ?? "");
    flattened.set(objectId, {
      objectId,
      objectType: String(version.objectType ?? "claim"),
      status: String(version.status ?? "proposed"),
      contentMd,
      exactText: String(version.exactText ?? ""),
      spanId: citations.length ? String(citations[0].spanId ?? "") || null : null
    });
  }
  return flattened;
}

/**
 * Own the Reader's background-request projection and its polling lifecycle.
 *
 * While work is active we poll only the source-local request status. The much
 * larger global proposal inbox and synthesized-object projection are hydrated
 * on entry, explicit refresh, and once when work reaches a terminal state.
 * This also uses recursive timeouts so a slow sidecar can never accumulate
 * overlapping polls.
 */
export function useReaderRequests(sourceId: string | null, enabled: boolean) {
  const activeSourceId = enabled ? sourceId : null;
  const activeSourceRef = useRef(activeSourceId);
  activeSourceRef.current = activeSourceId;

  useEffect(() => () => {
    activeSourceRef.current = null;
  }, []);

  const [requests, setRequests] = useState<BackgroundRequest[]>([]);
  const [proposalCount, setProposalCount] = useState(0);
  const [synthesizedObjects, setSynthesizedObjects] = useState<Map<string, SynthesizedObject>>(new Map());
  const [openProposalIds, setOpenProposalIds] = useState<Set<string>>(new Set());
  const [loadError, setLoadError] = useState<string | null>(null);

  const loadArtifacts = useCallback(async (targetSourceId: string) => {
    const [inbox, objects] = await Promise.all([
      api.readerProposalInbox({ status: "proposed" }),
      api.readerSourceObjects(targetSourceId)
    ]);
    if (activeSourceRef.current !== targetSourceId) return;
    const proposals = (inbox.proposals as Array<Record<string, unknown>>) ?? [];
    setProposalCount(proposals.length);
    setOpenProposalIds(new Set(proposals.map((proposal) => String(proposal.id))));
    setSynthesizedObjects(
      flattenSourceObjects((objects.sourceObjects as Array<Record<string, unknown>>) ?? [])
    );
  }, []);

  const refresh = useCallback(async () => {
    if (!activeSourceId) return;
    const targetSourceId = activeSourceId;
    const [snapshot, artifacts] = await Promise.allSettled([
      api.readerSourceRequests(targetSourceId),
      loadArtifacts(targetSourceId)
    ]);
    if (activeSourceRef.current !== targetSourceId) return;
    const failures: string[] = [];
    if (snapshot.status === "fulfilled") {
      setRequests((snapshot.value.requests as BackgroundRequest[]) ?? []);
    } else {
      failures.push(`request status: ${errorMessage(snapshot.reason)}`);
    }
    if (artifacts.status === "rejected") {
      failures.push(`request results: ${errorMessage(artifacts.reason)}`);
    }
    setLoadError(failures.length > 0 ? failures.join(" · ") : null);
  }, [activeSourceId, loadArtifacts]);

  useEffect(() => {
    setRequests([]);
    setProposalCount(0);
    setSynthesizedObjects(new Map());
    setOpenProposalIds(new Set());
    setLoadError(null);
    void refresh();
  }, [activeSourceId, refresh]);

  const polling = useMemo(() => hasActiveRequest(requests), [requests]);
  useEffect(() => {
    if (!activeSourceId || !polling) return;
    const targetSourceId = activeSourceId;
    let cancelled = false;
    let timer: number | undefined;

    const poll = async () => {
      let pollAgain = true;
      try {
        const snapshot = await api.readerSourceRequests(targetSourceId);
        if (cancelled || activeSourceRef.current !== targetSourceId) return;
        const next = (snapshot.requests as BackgroundRequest[]) ?? [];
        pollAgain = hasActiveRequest(next);
        if (pollAgain) {
          setRequests(next);
          setLoadError(null);
        } else {
          // The completion edge is the only polling tick that needs the global
          // proposal set and synthesized objects. If it fails, keep retrying so
          // a completed card cannot remain permanently empty.
          await loadArtifacts(targetSourceId);
          if (!cancelled && activeSourceRef.current === targetSourceId) {
            setRequests(next);
            setLoadError(null);
          }
        }
      } catch (error) {
        pollAgain = true;
        if (!cancelled && activeSourceRef.current === targetSourceId) {
          setLoadError(`Reader request status is temporarily unavailable: ${errorMessage(error)}`);
        }
      }
      if (!cancelled && activeSourceRef.current === targetSourceId && pollAgain) {
        timer = window.setTimeout(() => void poll(), 2000);
      }
    };

    timer = window.setTimeout(() => void poll(), 2000);
    return () => {
      cancelled = true;
      if (timer !== undefined) window.clearTimeout(timer);
    };
  }, [activeSourceId, polling, loadArtifacts]);

  return { requests, proposalCount, synthesizedObjects, openProposalIds, loadError, refresh };
}

export function parseRequestResult(
  resultJson: string | null | undefined
): { sourceObjectId: string | null; proposalId: string | null } {
  try {
    // result_json is an opaque JSON string, so its nested keys remain snake_case.
    const parsed = JSON.parse(resultJson ?? "") as { proposals?: Array<Record<string, unknown>> };
    const objectRow = (parsed.proposals ?? []).find((proposal) => proposal.kind === "source_object");
    const mappingRow = (parsed.proposals ?? []).find((proposal) => proposal.kind === "canonical_mapping");
    return {
      sourceObjectId: (objectRow?.source_object_id as string) ?? null,
      proposalId: (mappingRow?.proposal_id as string) ?? null
    };
  } catch {
    return { sourceObjectId: null, proposalId: null };
  }
}

export function parseRequestError(errorJson: string | null | undefined): string | null {
  try {
    const parsed = JSON.parse(errorJson ?? "") as { message?: unknown };
    const message = typeof parsed.message === "string" ? parsed.message.trim() : "";
    if (!message) return null;
    if (/unexpected end of hex escape|invalid .* json|json_invalid/i.test(message)) {
      return "The AI returned malformed structured text while formatting the result. Retry will regenerate it safely.";
    }
    return message;
  } catch {
    return null;
  }
}
