import type { components } from "../generated/api";

type Status =
  | components["schemas"]["Eligibility"]
  | components["schemas"]["Currentness"]
  | components["schemas"]["EvaluationState"];

const labels: Record<Status, string> = {
  MET: "Published requirements met",
  NOT_MET: "Published requirements not met",
  UNKNOWN: "Needs clarification",
  CURRENT: "Current inputs",
  STALE: "Needs a fresh check",
  HISTORICAL: "Historical result",
  NOT_EVALUATED: "Not evaluated",
};

export function StatusLabel({ status }: { status: Status }) {
  const tone =
    status === "MET" || status === "CURRENT"
      ? "positive"
      : status === "NOT_MET"
        ? "negative"
        : "neutral";
  return (
    <span className={`status-label status-label--${tone}`}>
      {labels[status]}
    </span>
  );
}
