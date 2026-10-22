// UX Phase 2 fix round 5: the attribute that marks a part of the page whose
// controls are not the screen's own (app/keymap.ts `controlOwner`): the
// wrap-up line on Start and Today, the window titlebar, command overlays.
// Simple shell only, so classic's DOM stays base's. Kept apart from keymap.ts
// so components/ui.tsx can use it without an import cycle.
import { algoConfig } from "./algoConfig";

export function keyScope(scope: string): { "data-key-scope"?: string } {
  return algoConfig().shell === "classic" ? {} : { "data-key-scope": scope };
}
