import { createRoot } from "react-dom/client";
import {
  StateView,
  ErrorView,
  type ViewState,
} from "../src/components/StateView";
import { StatusLabel } from "../src/components/StatusLabel";
import { PlainText } from "../src/components/PlainText";
import { ApiError } from "../src/lib/api";
import "../src/styles/shell.css";

export function StateFixture() {
  const states: ViewState[] = [
    "empty",
    "loading",
    "unknown",
    "partial",
    "stale",
    "unavailable",
    "cancelled",
  ];
  return (
    <main>
      <h1>State convention verification</h1>
      {states.map((state) => (
        <StateView key={state} state={state} title={`${state} result`}>
          <p>Synthetic {state} explanation.</p>
        </StateView>
      ))}
      <ErrorView
        error={
          new ApiError(
            "network",
            "Synthetic connection unavailable.",
            "synthetic-request",
          )
        }
      />
      <StatusLabel status="UNKNOWN" />
      <StatusLabel status="STALE" />
      <StatusLabel status="NOT_EVALUATED" />
      <PlainText
        text={
          '<img src=x onerror="window.syntheticInjection=true">\nSynthetic model output'
        }
      />
    </main>
  );
}

export function mountFixture(element: HTMLElement) {
  return createRoot(element).render(<StateFixture />);
}
