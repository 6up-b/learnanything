// A bottom sheet (mobile v2 §4.3, §4.7): opens from the bottom, closes with a downward swipe on its
// handle and always with a button, traps focus while open and returns it on close. Not a modal in
// the §4.4 sense: nothing opens one on its own; the learner does.
import { useEffect, useId, useRef, type ReactNode } from "react";

const FOCUSABLE = 'button:not([disabled]), [href], input:not([disabled]), textarea:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

export function Sheet({
  title,
  onClose,
  closeLabel = "Close",
  children
}: {
  title: string;
  onClose: () => void;
  /** The button that closes it, which a sheet always has (§4.3). */
  closeLabel?: string;
  children: ReactNode;
}) {
  const titleId = useId();
  const panel = useRef<HTMLDivElement>(null);
  const latestClose = useRef(onClose);
  latestClose.current = onClose;
  const drag = useRef<{ startY: number; dy: number } | null>(null);

  useEffect(() => {
    const returnTo = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const first = panel.current?.querySelector<HTMLElement>(FOCUSABLE);
    (first ?? panel.current)?.focus();
    return () => {
      if (returnTo && document.contains(returnTo)) returnTo.focus();
    };
  }, []);

  function onKeyDown(event: React.KeyboardEvent) {
    if (event.key === "Escape") {
      event.stopPropagation();
      latestClose.current();
      return;
    }
    if (event.key !== "Tab" || !panel.current) return;
    const focusable = [...panel.current.querySelectorAll<HTMLElement>(FOCUSABLE)];
    if (focusable.length === 0) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  // The swipe is on the handle only, so scrolling the sheet's content never closes it. It closes
  // past a quarter of the sheet's own height, and springs back short of that.
  function onPointerDown(event: React.PointerEvent) {
    drag.current = { startY: event.clientY, dy: 0 };
  }
  function onPointerMove(event: React.PointerEvent) {
    if (!drag.current || !panel.current) return;
    drag.current.dy = Math.max(0, event.clientY - drag.current.startY);
    panel.current.style.transform = `translateY(${drag.current.dy}px)`;
  }
  function onPointerUp() {
    const current = drag.current;
    drag.current = null;
    if (!current || !panel.current) return;
    panel.current.style.transform = "";
    if (current.dy > panel.current.getBoundingClientRect().height / 4) latestClose.current();
  }

  return (
    <div className="sheet-layer">
      <div className="sheet-backdrop" aria-hidden="true" onClick={() => latestClose.current()} />
      <div className="sheet" role="dialog" aria-modal="true" aria-labelledby={titleId} ref={panel} tabIndex={-1} onKeyDown={onKeyDown}>
        <div
          className="sheet-handle"
          aria-hidden="true"
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          onPointerCancel={onPointerUp}
        />
        <div className="sheet-head">
          <h2 id={titleId}>{title}</h2>
          <button className="plain" type="button" onClick={() => latestClose.current()}>{closeLabel}</button>
        </div>
        <div className="sheet-body">{children}</div>
      </div>
    </div>
  );
}
