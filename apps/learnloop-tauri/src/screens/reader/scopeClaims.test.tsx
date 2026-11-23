// The Reader's own key scopes reach a desk's router (spec §5.4): an intent box armed over a selection
// claims typing, and an open Wrap up claims esc as a menu. Outside the desks nothing is claimed.
import { act, cleanup, render, renderHook } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { createRef, type ReactNode } from "react";
import { DIRECT_HUB, WindowScope, type ClaimedScope, type ScopeClaims } from "../desks/lifecycle";
import type { ReaderIntentContractDto, ReaderWrapUpDto } from "../../api/dto";
import { useIntentBox } from "./useIntentBox";
import { WrapUpPanel } from "./WrapUpPanel";

vi.mock("../../api/client", () => ({ api: {} }));

afterEach(cleanup);

function recorder() {
  const open = new Map<ClaimedScope, Set<string>>();
  const claims: ScopeClaims = {
    claim: (scope, owner, isOpen) => {
      const owners = open.get(scope) ?? new Set<string>();
      if (isOpen) owners.add(owner);
      else owners.delete(owner);
      open.set(scope, owners);
    },
  };
  return { claims, has: (scope: ClaimedScope) => (open.get(scope)?.size ?? 0) > 0 };
}

function scope(claims: ScopeClaims) {
  return ({ children }: { children: ReactNode }) => (
    <WindowScope lifecycle={{ windowId: "w", state: "active" }} hub={DIRECT_HUB} claims={claims}>{children}</WindowScope>
  );
}

const CONTRACT: ReaderIntentContractDto = { palette: [], notesPalette: [], speculative: false, speculateAfterMs: 0, timeoutSeconds: 30 };

it("an intent box claims typing from the selection until it closes", () => {
  const { claims, has } = recorder();
  const host = createRef<HTMLDivElement>();
  const { result } = renderHook(() => useIntentBox({
    contract: CONTRACT, extractionId: "ext1", spanIds: ["s1"], quote: "q", muted: true, protectedSelection: false,
    notes: false, canWorkThrough: false, hostRef: host, onRun: () => undefined, onCancelRun: () => undefined,
  }), { wrapper: scope(claims) });
  expect(has("typing")).toBe(false);
  act(() => result.current.noteSelection());
  expect(has("typing")).toBe(true);
  act(() => result.current.close());
  act(() => result.current.noteSelectionCleared());
  expect(has("typing")).toBe(false);
});

it("an open Wrap up claims the menu scope, and lets it go when it closes", () => {
  const { claims, has } = recorder();
  const wrapUp = {
    version: 1, wrapUpVersion: "v", available: true, extractionId: "ext1",
    session: { sessionId: "v1", extractionId: "ext1", visitIds: ["v1"], startedAt: "2026-10-14T21:10:00Z", endedAt: "2026-10-14T21:50:00Z", minutes: 40 },
    resolved: [], stillOpen: [], worthReinforcing: [],
  } as ReaderWrapUpDto;
  const Wrapper = scope(claims);
  const view = render(<Wrapper><WrapUpPanel wrapUp={wrapUp} where="reader" onAction={async () => undefined} onClose={() => undefined} /></Wrapper>);
  expect(has("menu")).toBe(true);
  view.unmount();
  expect(has("menu")).toBe(false);
});
