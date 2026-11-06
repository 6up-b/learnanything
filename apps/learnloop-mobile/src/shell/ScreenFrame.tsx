// What every screen of a stack sits in (mobile v2 §4.2, §4.3, §4.7): a top bar with the back
// chevron when there is somewhere to go back to, the screen's content, its title announced to
// VoiceOver and focus moved to the new screen, and the edge swipe back.
import { useEffect, useRef, type ReactNode } from "react";

/**
 * iOS's own edge-gesture zone (Human Interface Guidelines): a swipe that starts this close to the
 * left edge is a back gesture, and it goes back once it has crossed a third of the screen.
 */
const EDGE_ZONE_PX = 20;

export interface FrameAction {
  readonly label: string;
  readonly name: string;
  readonly onClick: () => void;
}

export function ScreenFrame({
  screenKey,
  title,
  onBack,
  backName = "Back",
  actions = [],
  children
}: {
  /** Changes when another screen is on top: the title is announced and focus moves. */
  screenKey: string;
  title: string;
  onBack?: (() => void) | null;
  backName?: string;
  actions?: readonly FrameAction[];
  children: ReactNode;
}) {
  const content = useRef<HTMLDivElement>(null);
  const announcer = useRef<HTMLDivElement>(null);
  const first = useRef(true);
  const swipe = useRef<{ x: number; y: number } | null>(null);

  useEffect(() => {
    // Not on the very first screen: VoiceOver reads a freshly opened app on its own.
    if (first.current) {
      first.current = false;
      return;
    }
    if (announcer.current) announcer.current.textContent = title;
    content.current?.focus({ preventScroll: false });
    // The title is read once per screen, not once per render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [screenKey]);

  function onTouchStart(event: React.TouchEvent) {
    const touch = event.touches[0];
    swipe.current = onBack && touch && touch.clientX <= EDGE_ZONE_PX ? { x: touch.clientX, y: touch.clientY } : null;
  }
  function onTouchEnd(event: React.TouchEvent) {
    const start = swipe.current;
    swipe.current = null;
    const touch = event.changedTouches[0];
    if (!start || !touch || !onBack) return;
    const dx = touch.clientX - start.x;
    if (dx > window.innerWidth / 3 && Math.abs(touch.clientY - start.y) < dx) onBack();
  }

  return (
    <>
      <header className="topbar">
        {onBack ? (
          <button className="chevron" type="button" aria-label={backName} onClick={onBack}>
            <span aria-hidden="true">‹</span>
          </button>
        ) : (
          <span className="topbar-spacer" />
        )}
        <div className="topbar-actions">
          {actions.map((action) => (
            <button key={action.name} className="icon" type="button" aria-label={action.name} onClick={action.onClick}>
              <span aria-hidden="true">{action.label}</span>
            </button>
          ))}
        </div>
      </header>
      <div className="sr-only" aria-live="polite" ref={announcer} />
      <main className="frame" ref={content} tabIndex={-1} onTouchStart={onTouchStart} onTouchEnd={onTouchEnd}>
        {children}
      </main>
    </>
  );
}
