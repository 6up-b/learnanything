import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { IntentChoice, IntentChoicePreviewDto, IntentViewDto } from "../api/dto";
import { IntentControl, previewLine } from "./IntentControl";

const { api } = vi.hoisted(() => ({ api: { getIntent: vi.fn(), setIntent: vi.fn(), setIntentDeadline: vi.fn() } }));
vi.mock("../api/client", () => ({ api }));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const LABELS: Record<IntentChoice, string> = {
  master: "Master",
  learn: "Learn",
  keep: "Keep",
  light_touch: "Light touch",
  check_once: "Check once",
  reference: "Reference",
  pause: "Pause",
  let_go: "Let go"
};

function choice(name: IntentChoice, overrides: Partial<IntentChoicePreviewDto> = {}): IntentChoicePreviewDto {
  return {
    choice: name,
    label: LABELS[name],
    does: `${LABELS[name]} does this`,
    consequence: `${LABELS[name]} this topic`,
    replacedTopics: 0,
    replacedItems: 0,
    costMinutesPerDay: 0,
    costLabel: "no reviews",
    servedCount: 0,
    excludedCount: 0,
    ...overrides
  };
}

function view(current: IntentViewDto["current"], overrides: Partial<Record<IntentChoice, Partial<IntentChoicePreviewDto>>> = {}): IntentViewDto {
  return {
    enabled: true,
    available: true,
    scope: { kind: "learning_object", id: "lo_a" },
    title: "Eigenvalues",
    topics: 1,
    items: 2,
    current,
    choices: (Object.keys(LABELS) as IntentChoice[]).map((name) => choice(name, overrides[name]))
  };
}

const UNSET = { choice: "uncommitted" as const, label: "No setting", source: null, deadline: null, canAddDeadline: false };

async function mount() {
  const props = { onChanged: vi.fn(), onError: vi.fn() };
  await act(async () => {
    render(<IntentControl scopeKind="learning_object" scopeId="lo_a" {...props} />);
  });
  return props;
}

it("is optional: with no setting it says so and shows every choice, none selected", async () => {
  api.getIntent.mockResolvedValue(view(UNSET));
  await mount();
  expect(api.getIntent).toHaveBeenCalledWith("learning_object", "lo_a");
  expect(screen.getByTestId("intent-current").textContent).toBe("No setting: reviewed as usual.");
  for (const label of Object.values(LABELS)) expect(screen.getByRole("radio", { name: label })).toBeTruthy();
  expect(screen.getAllByRole("radio").filter((radio) => radio.getAttribute("aria-checked") === "true")).toHaveLength(0);
  expect(screen.queryByTestId("intent-preview")).toBeNull();
});

it("previews the consequence and the projected cost before a choice is taken", async () => {
  api.getIntent.mockResolvedValue(
    view(UNSET, {
      pause: { consequence: "Pause this topic · replaces your earlier setting on 1 item", costLabel: "no reviews" },
      keep: { consequence: "Keep this topic", costLabel: "about 3 min/day of reviews", costMinutesPerDay: 3.2,
              does: "reviews only, at 85%; no new or harder material" }
    })
  );
  await mount();
  fireEvent.mouseEnter(screen.getByRole("radio", { name: "Pause" }));
  expect(screen.getByTestId("intent-preview").textContent).toContain(
    "Pause this topic · replaces your earlier setting on 1 item · no reviews"
  );
  fireEvent.focus(screen.getByRole("radio", { name: "Keep" }));
  const preview = screen.getByTestId("intent-preview").textContent ?? "";
  expect(preview).toContain("Keep this topic · about 3 min/day of reviews");
  expect(preview).toContain("reviews only, at 85%");
  expect(api.setIntent).not.toHaveBeenCalled();
});

it("a click applies the choice, shows the new setting and tells the caller", async () => {
  api.getIntent.mockResolvedValue(view(UNSET));
  api.setIntent.mockResolvedValue(
    view({ choice: "keep", label: "Keep", source: "this control", deadline: null, canAddDeadline: true })
  );
  const props = await mount();
  await act(async () => {
    fireEvent.click(screen.getByRole("radio", { name: "Keep" }));
  });
  expect(api.setIntent).toHaveBeenCalledWith("learning_object", "lo_a", "keep");
  expect(props.onChanged).toHaveBeenCalled();
  expect(screen.getByRole("radio", { name: "Keep" }).getAttribute("aria-checked")).toBe("true");
  expect(screen.getByTestId("intent-current").textContent).toBe("Set to Keep.");
  // The selected choice's line stays visible.
  expect(screen.getByTestId("intent-preview").textContent).toContain("Keep this topic · no reviews");
});

it("names where an inherited setting comes from", async () => {
  api.getIntent.mockResolvedValue(
    view({ choice: "pause", label: "Pause", source: "a broader or earlier setting", deadline: null, canAddDeadline: false })
  );
  await mount();
  expect(screen.getByTestId("intent-current").textContent).toBe("Set to Pause (from a broader or earlier setting).");
});

it("adds a deadline as a goal once a depth is chosen", async () => {
  const kept = { choice: "learn" as const, label: "Learn", source: "this control", deadline: null, canAddDeadline: true };
  api.getIntent.mockResolvedValue(view(kept));
  api.setIntentDeadline.mockResolvedValue(
    view({ ...kept, deadline: { goalId: "goal_x", dueAt: "2026-12-01T23:59:59Z" } })
  );
  const props = await mount();
  fireEvent.change(screen.getByLabelText("deadline"), { target: { value: "2026-12-01" } });
  await act(async () => {
    fireEvent.click(screen.getByText("save"));
  });
  expect(api.setIntentDeadline).toHaveBeenCalledWith("learning_object", "lo_a", "2026-12-01");
  expect(screen.getByTestId("intent-deadline").textContent).toBe("deadline 2026-12-01 (a goal)");
  expect(props.onChanged).toHaveBeenCalled();
});

it("renders nothing when intent is off for the vault", async () => {
  api.getIntent.mockResolvedValue({ enabled: false });
  await mount();
  expect(screen.queryByTestId("intent-control")).toBeNull();
});

it("never takes focus on its own", async () => {
  api.getIntent.mockResolvedValue(view(UNSET));
  await mount();
  expect(document.activeElement === document.body || document.activeElement === null).toBe(true);
});

it("joins the consequence and the cost into one line", () => {
  expect(previewLine(choice("learn", { consequence: "Learn 3 topics", costLabel: "about 4 min/day of reviews" }))).toBe(
    "Learn 3 topics · about 4 min/day of reviews"
  );
});
