import type { ReactNode } from "react";
import { ApiError } from "../lib/api";

export type ViewState =
  | "empty"
  | "loading"
  | "unknown"
  | "partial"
  | "stale"
  | "unavailable"
  | "cancelled";

export interface StateViewProps {
  state: ViewState;
  title: string;
  children: ReactNode;
  action?: ReactNode;
}

export function StateView({ state, title, children, action }: StateViewProps) {
  return (
    <section
      className={`state-view state-view--${state}`}
      aria-busy={state === "loading"}
    >
      <span className="state-marker" aria-hidden="true">
        {state === "loading" ? "…" : "—"}
      </span>
      <div>
        <p className="eyebrow">
          {state === "unknown" ? "Needs clarification" : state}
        </p>
        <h2>{title}</h2>
        <div className="state-description">{children}</div>
        {action && <div className="state-action">{action}</div>}
      </div>
    </section>
  );
}

export function ErrorView({
  error,
  onRetry,
}: {
  error: ApiError;
  onRetry?: () => void;
}) {
  const requiresAccount = error.status === 401;
  const needsConsent = error.problem?.code === "CONSENT_REQUIRED";
  return (
    <section className="error-view" role="alert">
      <p className="eyebrow">Request unavailable</p>
      <h2>
        {requiresAccount
          ? "Sign in to continue"
          : needsConsent
            ? "Review your processing consent"
            : "We couldn’t complete this request"}
      </h2>
      <p>{error.message}</p>
      {error.problem?.errors.length ? (
        <ul>
          {error.problem.errors.map((field, index) => (
            <li key={`${field.path}-${index}`}>
              {field.path}: {field.message}
            </li>
          ))}
        </ul>
      ) : null}
      <p className="request-reference">
        Request reference <code>{error.requestId}</code>
      </p>
      {onRetry && !requiresAccount && !needsConsent && (
        <button className="button button--secondary" onClick={onRetry}>
          Try again
        </button>
      )}
    </section>
  );
}
