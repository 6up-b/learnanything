// Reader CA5: the Guide's quiet read of reader.correspondents (judged coverage
// only, no search, no model call, no write), shared by CA5's one-line "also in
// your books" and CA5a's "find this section in my other books", which both ask
// it when the Guide crosses into a section. One request in flight per section
// answers both (the sidecar is serial; CA5a open item 7). Nothing is kept once
// it lands: every crossing asks again (the sidecar keeps the parsed library, so
// the read is cheap there), so a correction is never hidden by a stale answer.
import { api } from "../../api/client";
import type { CorrespondentsDto } from "../../api/dto";

const inFlight = new Map<string, Promise<CorrespondentsDto>>();

export function quietCorrespondents(extractionId: string, sectionId: string): Promise<CorrespondentsDto> {
  const key = `${extractionId}\u0000${sectionId}`;
  const running = inFlight.get(key);
  if (running) return running;
  let started: Promise<CorrespondentsDto>;
  try {
    started = Promise.resolve(api.readerCorrespondents({ extractionId, sectionId, searchFallback: false }));
  } catch (error) {
    started = Promise.reject(error);
  }
  const request = started.finally(() => {
    if (inFlight.get(key) === request) inFlight.delete(key);
  });
  inFlight.set(key, request);
  return request;
}
