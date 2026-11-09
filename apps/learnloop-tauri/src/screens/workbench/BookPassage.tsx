// "Show me the book's way" off the Reader: the passage itself, under the hint.
// Reading it records an exposure (get_span_view does, on every view), and the
// server has already counted the book on this attempt when it delivered the
// bridge. The page view is the same read-only viewer the feedback screen uses.
import { useEffect, useState } from "react";
import { api } from "../../api/client";
import type { SpanViewDto } from "../../api/dto";
import { quietLink } from "../../components/PlainParts";
import { OpenInSource } from "../../components/OpenInSource";
import { MarkdownMath } from "../../render/MarkdownMath";
import { MeaningLabel, SourceVoice } from "../reader/voices";
import { HELP_COPY } from "./helpModel";

export function BookPassage({ extractionId, spanId, practiceItemId }: {
  extractionId: string;
  spanId: string;
  practiceItemId: string | null;
}) {
  const [view, setView] = useState<SpanViewDto | null>(null);
  const [failed, setFailed] = useState(false);
  const [pageOpen, setPageOpen] = useState(false);
  const entity = { context: "reader", entityType: practiceItemId ? "practice_item" : null, entityId: practiceItemId };

  useEffect(() => {
    let live = true;
    setView(null);
    setFailed(false);
    api.getSpanView({ extractionId, spanId, ...entity })
      .then((result) => { if (live) setView(result.spanView); })
      .catch(() => { if (live) setFailed(true); });
    return () => { live = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [extractionId, spanId, practiceItemId]);

  if (failed) return <MeaningLabel>{HELP_COPY.bookWayUnavailable}</MeaningLabel>;
  if (!view) return <MeaningLabel>{HELP_COPY.bridging}</MeaningLabel>;
  const where = [view.sectionPath.join(" › "), view.page != null ? `p. ${view.page}` : ""].filter(Boolean).join(" · ");
  return (
    <div data-testid="workbench-book-passage" style={{ marginTop: 6 }}>
      <MeaningLabel>{HELP_COPY.bookWayCounts}{where ? ` · ${where}` : ""}</MeaningLabel>
      <SourceVoice>
        <MarkdownMath value={view.text} />
      </SourceVoice>
      <button type="button" style={{ ...quietLink, fontSize: 11 }} onClick={() => setPageOpen(true)}>{HELP_COPY.bookWayPage}</button>
      {pageOpen ? <OpenInSource extractionId={extractionId} spanId={spanId} {...entity} onClose={() => setPageOpen(false)} /> : null}
    </div>
  );
}
