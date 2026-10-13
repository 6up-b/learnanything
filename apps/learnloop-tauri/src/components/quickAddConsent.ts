import type { QuickAddConsentDto } from "../api/dto";

/** A consent the learner already gave once (recorded with its date) starts ticked. */
export function initialConsentTicks(consents: QuickAddConsentDto[]): boolean[] {
  return consents.map((consent) => consent.granted === true);
}
