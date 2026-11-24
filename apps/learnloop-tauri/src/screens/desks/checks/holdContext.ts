// Whether an inline check holds the desks now, for the parts that must act on it themselves: a player stops and
// will not start (a hidden frame can still play its sound), whatever the page's hold covers.
import { createContext, useContext } from "react";

export const CheckHoldContext = createContext(false);

export function useCheckHeld(): boolean {
  return useContext(CheckHoldContext);
}
