import type { components } from "../src/generated/api";

type FactValue = components["schemas"]["FactValue"];
type Evaluation = components["schemas"]["Evaluation"];

export const grade: FactValue = {
  type: "GPA",
  number: "3.70",
  scale_max: "5.00",
};

export const numericGrade: FactValue = {
  type: "GPA",
  // @ts-expect-error Wire decimals cannot silently become JavaScript numbers.
  number: 3.7,
  scale_max: "4",
};

// @ts-expect-error Missing the source scale is not a complete GPA value.
export const unscaledGrade: FactValue = { type: "GPA", number: "3.7" };

// @ts-expect-error Unknown enum values must not widen the generated contract.
export const eligibility: Evaluation["eligibility"] = "ELIGIBLE";

// @ts-expect-error A string cannot substitute for a tagged boolean value.
export const stringBoolean: FactValue = { type: "BOOLEAN", value: "true" };

export function narrowFact(value: FactValue): string | null {
  if (value.type === "GPA") return value.number;
  if (value.type === "UNKNOWN") return value.reason;
  return null;
}

// @ts-expect-error Server snapshots cannot be mutated through generated types.
grade.number = "4.00";
