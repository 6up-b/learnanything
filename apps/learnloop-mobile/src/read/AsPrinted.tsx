// *As printed* after feedback (CA7, mobile v2 §3.3): the problem's own blocks cropped from its page, as the
// desktop's Feedback shows them (`practice.as_printed`, whose server decides what may show: the problem's own
// blocks only, never its solution, and nothing during a check on your own). *View the page* is the host's page
// image. Nothing shows when there is no print, the host withholds it, or an older host has no such method.
import { useEffect, useState } from "react";
import type { AsPrintedViewDto } from "@desktop/api/dto";
import { phone } from "../api/phone";
import { PageImage } from "./PageImage";

interface Crop {
  readonly page?: number;
  readonly image: string | null;
  readonly pageLabel?: string | null;
}

export function PrintedAfterFeedback({ practiceItemId }: { practiceItemId: string | null | undefined }) {
  const [view, setView] = useState<AsPrintedViewDto | null>(null);
  const [pageOpen, setPageOpen] = useState(false);
  useEffect(() => {
    if (!practiceItemId) return undefined;
    let cancelled = false;
    phone.asPrinted(practiceItemId).then((loaded) => {
      if (!cancelled) setView(loaded);
    }, () => undefined);
    return () => {
      cancelled = true;
    };
  }, [practiceItemId]);
  if (!view || view.kind !== "page") return null;
  const crops = ((view.crops ?? []) as Crop[]).filter((crop) => crop.image);
  const page = (view.crops as Crop[] | undefined)?.find((crop) => typeof crop.page === "number")?.page ?? null;
  const extractionId = view.originalPage?.extractionId ?? null;
  return (
    <section className="as-printed" aria-label="As printed">
      <p className="dim">
        {view.label ?? "as printed"}
        {view.locator ? ` · ${view.locator.sourceTitle?.trim() || "your book"} p.${view.locator.pageLabel}` : ""}
      </p>
      {crops.map((crop, index) => (
        <img key={index} className="page-image" src={crop.image ?? undefined} alt={`as printed, part ${index + 1}`} />
      ))}
      {view.notice ? <p className="dim">{view.notice}</p> : null}
      {extractionId && page !== null ? (
        <>
          <button className="link quiet" type="button" aria-expanded={pageOpen} onClick={() => setPageOpen((open) => !open)}>
            View the page
          </button>
          {pageOpen ? <PageImage ref_={extractionId} page={page} /> : null}
        </>
      ) : null}
    </section>
  );
}
