import type { CSSProperties, ReactNode } from "react";
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
  zIndex = 200
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
}) {
  return (
    <div style={{ ...commandOverlayBackdropStyle, zIndex }} onClick={onClose}>
      <section
        role="dialog"
        aria-modal="true"
        aria-label={ariaLabel ?? `learnloop ${command}`}
        style={{ ...commandOverlayModalStyle, width }}
        onClick={(event) => event.stopPropagation()}
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
