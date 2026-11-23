// The client's workspace model gives the sidecar's results and final state for one shared desk.apply
// script (opParity.json; the sidecar runs the same script in tests/test_reader_rd1_model_parity.py).
// The model applies ops optimistically, so its layout must be the one the server stores.
import { expect, it } from "vitest";
import type { DeskOpDto } from "../../api/dto";
import script from "./opParity.json";
import { FixtureDeskServer } from "./workspace";

it("gives the script's results and final state", () => {
  const server = new FixtureDeskServer({ version: 1, desks: [], runningPadIds: [], serverSeq: [] });
  const results = (script.batches as unknown as DeskOpDto[][]).map((ops, index) =>
    server.apply({ clientId: "client_a", seq: index + 1, ops }).results.map((result) => result.status));
  expect(results).toEqual(script.results);
  const final = server.state().desks.map((desk) => ({
    deskId: desk.deskId,
    title: desk.title,
    focusWindowId: desk.focusWindowId,
    version: desk.version,
    slots: desk.slots.map((slot) => slot.windows.map((window) => [window.windowId, window.active])),
  }));
  expect(final).toEqual(script.final);
});
