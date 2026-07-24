import { useEffect, useRef, type CSSProperties, type KeyboardEventHandler, type ReactNode } from "react";
import { COLOR, Faint, FONT_MONO } from "./term";

export const learnloopShowOverlayWidth = "min(1120px, 100%)";

/**
 * Shared shell for GUI mirrors of LearnLoop commands. The inspector established
 * this form factor; command-led overlays such as `learnloop diff` reuse it so
 * command identity, dismissal, dimensions, and keyboard hints stay consistent.
 */
export function CommandOverlayFrame({
  command,
  context,
  badge,
  headerActions,
  footerKeys,
  footerRight,
  onClose,
  children,
  ariaLabel,
  width = "min(960px, 100%)",
  zIndex = 200,
  focusOnMount = false,
  onKeyDown
}: {
  command: string;
  context?: ReactNode;
  badge?: ReactNode;
  headerActions?: ReactNode;
  footerKeys?: ReactNode;
  footerRight?: ReactNode;
  onClose: () => void;
  children: ReactNode;
  ariaLabel?: string;
  width?: string;
  zIndex?: number;
  focusOnMount?: boolean;
  onKeyDown?: KeyboardEventHandler<HTMLElement>;
}) {
  const modalRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!focusOnMount) return;
    const previousFocus = document.activeElement instanceof HTMLElement
      ? document.activeElement
      : null;
    modalRef.current?.focus();
    return () => {
      if (previousFocus?.isConnected) previousFocus.focus();
    };
  }, [focusOnMount]);

  return (
    <div style={{ ...commandOverlayBackdropStyle, zIndex }} onClick={onClose}>
      <section
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-label={ariaLabel ?? `learnloop ${command}`}
        tabIndex={focusOnMount ? -1 : undefined}
        style={{ ...commandOverlayModalStyle, width }}
        onClick={(event) => event.stopPropagation()}
        onKeyDown={(event) => {
          // A command overlay is modal: keyboard shortcuts owned by the mounted
          // screen beneath it must not also run.
          event.stopPropagation();
          if (focusOnMount && event.key === "Tab") {
            const focusable = Array.from(
              modalRef.current?.querySelectorAll<HTMLElement>(
                'a[href], button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
              ) ?? []
            );
            const first = focusable[0];
            const last = focusable[focusable.length - 1];
            if (event.shiftKey && (document.activeElement === first || document.activeElement === modalRef.current)) {
              event.preventDefault();
              last?.focus();
            } else if (!event.shiftKey && document.activeElement === last) {
              event.preventDefault();
              first?.focus();
            }
          }
          onKeyDown?.(event);
        }}
      >
        <header style={commandOverlayHeaderStyle}>
          <span style={{ color: COLOR.amber, fontWeight: 700 }}>❯</span>
          <span style={{ color: COLOR.text, fontSize: 13 }}>
            learnloop <span style={{ color: COLOR.amber }}>{command}</span>
          </span>
          {context ? (
            <>
              <Faint>·</Faint>
              <span
                style={{
                  color: COLOR.amberLink,
                  fontSize: 13,
                  fontFamily: FONT_MONO,
                  minWidth: 0,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap"
                }}
              >
                {context}
              </span>
            </>
          ) : null}
          {badge}
          <span style={{ flex: 1 }} />
          {headerActions}
          <button
            type="button"
            onClick={onClose}
            style={{ ...commandOverlayActionStyle, color: COLOR.textDim, marginLeft: 6, flexShrink: 0 }}
          >
            esc ×
          </button>
        </header>

        {children}

        <footer style={commandOverlayFooterStyle}>
          {footerKeys}
          <span style={{ flex: 1 }} />
          {footerRight}
        </footer>
      </section>
    </div>
  );
}

export const commandOverlayActionStyle: CSSProperties = {
  border: "none",
  background: "transparent",
  color: COLOR.amberLink,
  padding: "2px 0",
  fontFamily: FONT_MONO,
  fontSize: 11,
  cursor: "pointer"
};

const commandOverlayBackdropStyle: CSSProperties = {
  position: "fixed",
  inset: 0,
  zIndex: 200,
  background: "rgba(8, 8, 13, 0.78)",
  display: "flex",
  alignItems: "flex-start",
  justifyContent: "center",
  padding: "6vh 5vw",
  backdropFilter: "blur(2px)"
};

const commandOverlayModalStyle: CSSProperties = {
  maxHeight: "88vh",
  background: COLOR.bg,
  border: `1px solid ${COLOR.borderStrong}`,
  boxShadow: "0 24px 80px rgba(0,0,0,0.6)",
  display: "flex",
  flexDirection: "column",
  fontFamily: FONT_MONO,
  color: COLOR.text
};

const commandOverlayHeaderStyle: CSSProperties = {
  padding: "12px 16px",
  borderBottom: `1px solid ${COLOR.border}`,
  display: "flex",
  alignItems: "center",
  gap: 10,
  flexShrink: 0
};

const commandOverlayFooterStyle: CSSProperties = {
  borderTop: `1px solid ${COLOR.border}`,
  padding: "6px 14px",
  fontSize: 11,
  color: COLOR.textDim,
  display: "flex",
  gap: 18,
  flexShrink: 0,
  alignItems: "center"
};
