// The four places (mobile v2 §4.2), in the thumb zone. Each is a button: the current one says so
// to VoiceOver with aria-current, and the + reads as "Capture".
import { TABS, type Tab } from "./navigation";

export function TabBar({ current, onSelect }: { current: Tab; onSelect: (tab: Tab) => void }) {
  return (
    <nav className="tabs" aria-label="Places">
      {TABS.map((spec) => (
        <button
          key={spec.tab}
          type="button"
          className={spec.tab === "capture" ? "tab-plus" : undefined}
          aria-label={spec.label === spec.name ? undefined : spec.name}
          aria-current={current === spec.tab ? "page" : undefined}
          onClick={() => onSelect(spec.tab)}
        >
          {spec.label}
        </button>
      ))}
    </nav>
  );
}
