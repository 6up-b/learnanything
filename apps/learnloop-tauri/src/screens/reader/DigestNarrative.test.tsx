// RW6b part 2's narrative (spec §9.2; UX §4.8, W14): collapsed and labelled
// "summary written by LearnLoop's model from what you did", never the first
// thing shown, in the model's voice, never a filled mark; W14's states in
// place (pending, failed with no retry, unreachable, capped naming the cap);
// absent when the sidecar sends none (switched off) -- in the card and in Wrap up.
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { ReaderDigestNarrativeDto, ReaderRecapCardDto, ReaderWrapUpDto } from "../../api/dto";
import { DigestNarrative, NARRATIVE_COPY } from "./DigestNarrative";
import { RecapCard } from "./RecapCard";
import { WrapUpPanel } from "./WrapUpPanel";

afterEach(cleanup);

const TEXT = "You read 5.4 on mixtures, asked why the densities are weighted by p, and worked Exercise 5.14 with the book open.";

function narrative(overrides: Partial<ReaderDigestNarrativeDto> = {}): ReaderDigestNarrativeDto {
  return {
    state: "landed", label: "summary written by LearnLoop's model", authority: "salience_only", digestId: "rsd_1",
    text: TEXT, citedEventIds: ["ex1", "wb1"], model: "fake", promptVersion: "reader_digest.v1", ...overrides,
  };
}

function card(overrides: Partial<ReaderRecapCardDto> = {}): ReaderRecapCardDto {
  return {
    recapVersion: "rw6a-recap-v1", extractionId: "ext1",
    session: { sessionId: "v1", extractionId: "ext1", visitIds: ["v1"], startedAt: "2026-10-09T20:00:00Z", endedAt: "2026-10-09T20:40:00Z", minutes: 40 },
    continueAt: { sectionId: "u54", label: "5.4 Mixtures" },
    stillOpen: [{ rootExchangeId: "r1", questionEventId: "q1", questionMd: "why weighted by p?", spanId: "s1", anchorSpanIds: ["s1"], openedAt: "2026-10-09T20:05:00Z" }],
    unfinished: [], worthASecondLook: [], sinceLastTime: { demonstrated: [], checksRetired: [] },
    ...overrides,
  };
}

const handlers = {
  onExpand: vi.fn(), onContinue: vi.fn(), onDismiss: vi.fn(), onOpenInquiry: vi.fn(), onSetStatus: vi.fn(), onResume: vi.fn(),
};

function wrapUp(overrides: Partial<ReaderWrapUpDto> = {}): ReaderWrapUpDto {
  return {
    version: 1, wrapUpVersion: "rw6a-wrap-up-v1", available: true, extractionId: "ext1",
    session: { sessionId: "v1", extractionId: "ext1", visitIds: ["v1"], startedAt: "2026-10-14T21:10:00Z", endedAt: "2026-10-14T21:50:00Z", minutes: 40 },
    resolved: [], stillOpen: [], worthReinforcing: [{ kind: "claim", marker: "◌", facetId: "recall" }],
    ...overrides,
  };
}

it("is collapsed and labelled at first, and opens in the model's voice", () => {
  const { container } = render(<DigestNarrative narrative={narrative()} />);
  const toggle = screen.getByRole("button", { name: NARRATIVE_COPY.collapsed });
  expect(toggle.textContent).toBe("▸ summary written by LearnLoop's model from what you did");
  expect(toggle.getAttribute("aria-expanded")).toBe("false");
  expect(container.textContent).not.toContain(TEXT);
  expect(document.activeElement).not.toBe(toggle); // nothing takes focus
  fireEvent.click(toggle);
  expect(container.textContent).toContain(TEXT);
  expect(container.querySelector("[data-voice='model']")).not.toBeNull();
  fireEvent.click(screen.getByRole("button", { name: NARRATIVE_COPY.expanded }));
  expect(container.textContent).not.toContain(TEXT);
});

it("never shows a filled mark, whatever the model wrote", () => {
  const { container } = render(<DigestNarrative narrative={narrative({ text: "You ● read the section ◌ twice." })} />);
  fireEvent.click(screen.getByRole("button", { name: NARRATIVE_COPY.collapsed }));
  const text = container.querySelector("[data-narrative-text]")?.textContent ?? "";
  expect(text).toBe("You read the section twice.");
  expect(text).not.toMatch(/[●◌○]/);
});

it("shows W14's states in place", () => {
  const { container, rerender } = render(<DigestNarrative narrative={narrative({ state: "pending", text: null })} />);
  expect(container.querySelector("[data-model-state='pending']")?.textContent).toContain("writing a summary of this session…");
  rerender(<DigestNarrative narrative={narrative({ state: "unreachable", text: null, message: "plan signed out" })} />);
  expect(container.querySelector("[data-model-state='unreachable']")?.textContent).toContain("Couldn't reach LearnLoop's model. The lists above are complete without it.");
  rerender(<DigestNarrative narrative={narrative({ state: "capped", text: null, capUsd: 0.25 })} />);
  expect(container.querySelector("[data-model-state='capped']")?.textContent).toContain("Today's summary budget ($0.25) is used. Everything above still works.");
  rerender(<DigestNarrative narrative={narrative({ state: "failed", text: null, message: null })} />);
  const failed = container.querySelector("[data-model-state='failed']");
  expect(failed?.textContent).toContain("couldn't write a summary of this session that matched what you did");
  expect(within(failed as HTMLElement).queryByRole("button", { name: /try again/ })).toBeNull(); // once per session
});

it("is absent when the sidecar sends none (switched off)", () => {
  const { container } = render(<DigestNarrative narrative={undefined} />);
  expect(container.innerHTML).toBe("");
  render(<RecapCard recap={card()} collapsed={false} {...handlers} />);
  const region = screen.getByRole("region", { name: "Last time here" });
  expect(region.querySelector("[data-digest-narrative]")).toBeNull();
  expect(region.textContent).not.toContain("summary written by LearnLoop's model");
});

it("sits collapsed at the foot of the card, never first", () => {
  render(<RecapCard recap={card({ narrative: narrative() })} collapsed={false} {...handlers} />);
  const region = screen.getByRole("region", { name: "Last time here" });
  const nodes = Array.from(region.querySelectorAll("[data-digest-narrative], h4"));
  expect(nodes[nodes.length - 1].getAttribute("data-digest-narrative")).toBe("landed");
  expect(region.textContent).not.toContain(TEXT);
  expect(within(region).getByRole("button", { name: NARRATIVE_COPY.collapsed })).toBeTruthy();
});

it("sits collapsed at the foot of Wrap up when ready, and is absent when not sent", () => {
  const { unmount } = render(<WrapUpPanel wrapUp={wrapUp({ narrative: narrative() })} where="destination" onAction={vi.fn()} onClose={vi.fn()} />);
  const panel = screen.getByRole("region", { name: "Wrap up" });
  expect(panel.lastElementChild?.getAttribute("data-digest-narrative")).toBe("landed");
  expect(panel.textContent).not.toContain(TEXT);
  fireEvent.click(within(panel).getByRole("button", { name: NARRATIVE_COPY.collapsed }));
  expect(panel.textContent).toContain(TEXT);
  unmount();
  render(<WrapUpPanel wrapUp={wrapUp()} where="destination" onAction={vi.fn()} onClose={vi.fn()} />);
  expect(screen.getByRole("region", { name: "Wrap up" }).querySelector("[data-digest-narrative]")).toBeNull();
});
