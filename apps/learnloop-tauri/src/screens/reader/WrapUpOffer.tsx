// The wrap-up offer where the learner lands (reader workbench RW6a; spec
// §9.1, UX S11, §4.12): after leaving a source with activity, one dim line on
// Today or the library -- "Reading wrap-up ready — under a minute ▸" -- for
// one view. It never blocks, never takes focus and is not a modal: pressed,
// Wrap up opens in place; Esc closes it. Whether to offer is the sidecar's
// pure read (the last session had activity and was not wrapped up); opening
// writes wrap_up_opened once the lists are shown, and its actions are the
// status chips' own RPC.
import { useCallback, useEffect, useState } from "react";
import { api } from "../../api/client";
import type { ReaderWrapUpActionDto, ReaderWrapUpDto, ReaderWrapUpInquiryLineDto, ReaderWrapUpOfferDto } from "../../api/dto";
import { algoConfig } from "../../app/algoConfig";
import { COLOR, FONT_MONO } from "../../components/term";
import { errorMessage } from "../../errors";
import { RECAP_COPY } from "./recapCopy";
import { WrapUpPanel } from "./WrapUpPanel";

export interface WrapUpOfferProps {
  /** The App armed it: this is the first view after leaving the Reader. */
  armed: boolean;
  onError: (message: string) => void;
}

type Offer = NonNullable<ReaderWrapUpOfferDto["offer"]>;

export function WrapUpOffer({ armed, onError }: WrapUpOfferProps) {
  const on = armed && algoConfig().wrapUp;
  const [offer, setOffer] = useState<Offer | null>(null);
  const [panel, setPanel] = useState<ReaderWrapUpDto | null>(null);
  const [closed, setClosed] = useState(false);

  useEffect(() => {
    if (!on) return;
    let cancelled = false;
    void Promise.resolve(api.readerWrapUpOffer())
      .then((result) => {
        if (!cancelled) setOffer(result?.offer ?? null);
      })
      .catch(() => {
        /* No line when the read fails: the offer is a convenience. */
      });
    return () => {
      cancelled = true;
    };
  }, [on]);

  const open = useCallback(async () => {
    if (!offer) return;
    let result: ReaderWrapUpDto;
    try {
      result = await api.readerWrapUp({ extractionId: offer.extractionId });
    } catch (error) {
      // Nothing shown, nothing recorded: the offer stands (review F7).
      onError(errorMessage(error));
      return;
    }
    setPanel(result);
    // Recorded once the lists are shown; a failed write leaves them shown.
    void Promise.resolve()
      .then(() => api.readerRecapEvent({ extractionId: offer.extractionId, event: "wrap_up_opened" }))
      .catch(() => undefined);
  }, [offer, onError]);

  const act = useCallback(async (_line: ReaderWrapUpInquiryLineDto, action: ReaderWrapUpActionDto) => {
    if (!offer || action.rpc !== "reader.set_inquiry_status" || !action.params) return;
    const params = action.params as { extractionId: string; exchangeId: string; resolution: "open" | "resolved" | "dismissed"; trigger: "chip" | "undo" };
    try {
      await api.readerSetInquiryStatus({
        extractionId: params.extractionId, exchangeId: params.exchangeId, resolution: params.resolution, trigger: params.trigger,
      });
      setPanel(await api.readerWrapUp({ extractionId: offer.extractionId }));
    } catch (error) {
      onError(errorMessage(error));
    }
  }, [offer, onError]);

  const close = useCallback(() => {
    setPanel(null);
    setClosed(true);
  }, []);

  if (!on || !offer || closed) return null;
  if (panel) {
    return (
      <div style={{ padding: "8px 16px 0" }}>
        <WrapUpPanel wrapUp={panel} where="destination" onAction={act} onClose={close} />
      </div>
    );
  }
  return (
    <div style={{ padding: "6px 16px 0" }}>
      <button
        type="button"
        onClick={() => void open()}
        style={{ border: 0, background: "transparent", padding: 0, cursor: "pointer", color: COLOR.textDim, fontFamily: FONT_MONO, fontSize: 11 }}
      >
        {RECAP_COPY.wrapUpReady}
      </button>
    </div>
  );
}
