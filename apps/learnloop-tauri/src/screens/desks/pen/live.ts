// The pen layer's calls on the sidecar (the desks' default; tests pass their own `PenApi`).
import { api } from "../../../api/client";
import type { PenApi } from "./host";

export const LIVE_PEN_API: PenApi = {
  readerCapture: (input) => api.readerCapture(input),
  readerDeleteIntentAnnotation: (input) => api.readerDeleteIntentAnnotation(input),
  readerEditAnnotation: (input) => api.readerEditAnnotation(input),
  readerSourceAnnotations: (input) => api.readerSourceAnnotations(input),
  inkList: (input) => api.inkList(input),
  inkTranscribe: (input) => api.inkTranscribe(input),
  inkTranscribeJob: (input) => api.inkTranscribeJob(input),
  inkTranscribeCancel: (input) => api.inkTranscribeCancel(input),
};
