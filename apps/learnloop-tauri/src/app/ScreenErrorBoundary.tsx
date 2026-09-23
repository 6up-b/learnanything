import { Component, type ErrorInfo, type ReactNode } from "react";
import { errorMessage } from "../errors";

type Props = {
  /** Changing this (the active tab) clears a caught error so other screens stay usable. */
  resetKey: string;
  children: ReactNode;
};

type State = { error: unknown };

/**
 * Catches render errors from the screen body, most importantly a lazy screen
 * chunk that failed to load. Without a boundary React unmounts the whole root
 * and the window goes blank. `React.lazy` caches a rejected import, so only a
 * page reload can fetch the chunk again.
 */
export class ScreenErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: unknown): State {
    return { error };
  }

  componentDidCatch(error: unknown, info: ErrorInfo) {
    console.error("Screen failed to render", error, info.componentStack);
  }

  componentDidUpdate(previous: Props) {
    if (this.state.error !== null && previous.resetKey !== this.props.resetKey) {
      this.setState({ error: null });
    }
  }

  render() {
    if (this.state.error === null) return this.props.children;
    return (
      <div className="placeholder-screen" role="alert">
        <div className="toast" style={{ maxWidth: 620 }}>
          <div>{errorMessage(this.state.error, "This screen could not be displayed.")}</div>
          <button type="button" className="queue-row" style={{ marginTop: 10 }} onClick={() => window.location.reload()}>
            reload app
          </button>
        </div>
      </div>
    );
  }
}
