import type { components, operations } from "../../generated/api";
import openapiText from "../../generated/openapi.json?raw";
import { ContractError } from "../../lib/api";

export type Profile = components["schemas"]["Profile"];
export type Fact = components["schemas"]["Fact"];
export type Attribute = Fact["attribute"];
export type Value = Fact["value"];
export type Patch =
  operations["patch_profile"]["requestBody"]["content"]["application/json"];
export type ProfilePage = components["schemas"]["Page_Profile_"];
export type Country =
  components["schemas"]["CountrySetValue"]["values"][number];
export type UnknownReason = components["schemas"]["UnknownReason"];

// Presentation metadata only; every wire value comes from the generated types.
export const fields = {
  "education.enrolled": {
    label: "Currently enrolled",
    group: "Education",
    type: "BOOLEAN",
  },
  "education.institution": {
    label: "Institution",
    group: "Education",
    type: "STRING",
  },
  "education.level": {
    label: "Education level",
    group: "Education",
    type: "STRING",
  },
  "education.field": {
    label: "Field of study",
    group: "Education",
    type: "STRING",
  },
  "education.graduation": {
    label: "Graduation date",
    group: "Education",
    type: "DATE",
  },
  "education.gpa": { label: "GPA", group: "Education", type: "GPA" },
  "location.country": {
    label: "Country of residence",
    group: "Location and authorization",
    type: "COUNTRY_SET",
  },
  "citizenship.countries": {
    label: "Citizenship",
    group: "Location and authorization",
    type: "COUNTRY_SET",
  },
  "work_authorization.countries": {
    label: "Work authorization",
    group: "Location and authorization",
    type: "COUNTRY_SET",
  },
  date_of_birth: {
    label: "Date of birth",
    group: "Location and authorization",
    type: "DATE",
  },
  skills: {
    label: "Skills",
    group: "Skills and experience",
    type: "STRING_SET",
  },
  experience: {
    label: "Experience",
    group: "Skills and experience",
    type: "EXPERIENCE",
  },
  language_tests: {
    label: "Language tests",
    group: "Skills and experience",
    type: "LANGUAGE_TESTS",
  },
} as const satisfies Record<
  Attribute,
  { label: string; group: string; type: Value["type"] }
>;

const schemas: unknown = JSON.parse(openapiText);
function record(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
function countryCodes(): readonly Country[] {
  if (
    !record(schemas) ||
    !record(schemas.components) ||
    !record(schemas.components.schemas)
  )
    throw new ContractError();
  const countrySet = schemas.components.schemas.CountrySetValue;
  if (!record(countrySet) || !record(countrySet.properties))
    throw new ContractError();
  const values = countrySet.properties.values;
  if (
    !record(values) ||
    !record(values.items) ||
    !Array.isArray(values.items.enum) ||
    !values.items.enum.every((value: unknown) => typeof value === "string")
  )
    throw new ContractError();
  return values.items.enum as Country[];
}
export const countries = countryCodes();
export const unknownReasons = {
  NOT_PROVIDED: "Not provided",
  USER_UNSURE: "I'm not sure",
  CONFLICTING_EVIDENCE: "Evidence disagrees",
} satisfies Record<UnknownReason, string>;

const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const decimal = /^(0|[1-9][0-9]*)(\.[0-9]+)?$/;
function exactKeys(value: Record<string, unknown>, keys: string[]): boolean {
  return (
    Object.keys(value).length === keys.length &&
    keys.every((key) => key in value)
  );
}
function text(value: unknown, max: number): value is string {
  return (
    typeof value === "string" && value.length > 0 && [...value].length <= max
  );
}
function date(value: unknown): value is string {
  if (
    typeof value !== "string" ||
    !/^\d{4}-\d{2}-\d{2}$/.test(value) ||
    value.slice(0, 4) === "0000"
  )
    return false;
  const parsed = new Date(value + "T00:00:00Z");
  return (
    !Number.isNaN(parsed.valueOf()) &&
    parsed.toISOString().slice(0, 10) === value
  );
}
function instant(value: unknown): value is string {
  return (
    typeof value === "string" &&
    /^\d{4}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(\.\d{1,6})?Z$/.test(
      value,
    ) &&
    date(value.slice(0, 10)) &&
    Number.isFinite(Date.parse(value))
  );
}
function decimalsOrdered(a: string, b: string): boolean {
  const [ai, af = ""] = a.split(".");
  const [bi, bf = ""] = b.split(".");
  const digits = Math.max(af.length, bf.length);
  return (
    BigInt(ai + af.padEnd(digits, "0")) <= BigInt(bi + bf.padEnd(digits, "0"))
  );
}
function uniqueStrings(
  value: unknown,
  max: number,
  check: (item: unknown) => boolean,
): value is string[] {
  return (
    Array.isArray(value) &&
    value.length <= max &&
    value.every(check) &&
    new Set(value).size === value.length
  );
}

export function validValue(
  attribute: Attribute,
  value: unknown,
): value is Value {
  if (!record(value)) return false;
  if (value.type === "UNKNOWN")
    return (
      exactKeys(value, ["type", "reason"]) &&
      typeof value.reason === "string" &&
      Object.hasOwn(unknownReasons, value.reason)
    );
  if (value.type !== fields[attribute].type) return false;
  switch (value.type) {
    case "STRING":
      return exactKeys(value, ["type", "value"]) && text(value.value, 500);
    case "BOOLEAN":
      return (
        exactKeys(value, ["type", "value"]) && typeof value.value === "boolean"
      );
    case "COUNTRY_SET":
      return (
        exactKeys(value, ["type", "values"]) &&
        uniqueStrings(
          value.values,
          20,
          (item) =>
            typeof item === "string" && countries.some((code) => code === item),
        ) &&
        (attribute !== "location.country" || value.values.length === 1)
      );
    case "STRING_SET":
      return (
        exactKeys(value, ["type", "values"]) &&
        uniqueStrings(value.values, 50, (item) => text(item, 80))
      );
    case "GPA":
      return (
        exactKeys(value, ["type", "number", "scale_max"]) &&
        typeof value.number === "string" &&
        decimal.test(value.number) &&
        typeof value.scale_max === "string" &&
        decimal.test(value.scale_max) &&
        /[1-9]/.test(value.scale_max) &&
        decimalsOrdered(value.number, value.scale_max)
      );
    case "DATE": {
      if (
        !exactKeys(value, ["type", "value", "precision", "expected"]) ||
        typeof value.expected !== "boolean" ||
        typeof value.value !== "string"
      )
        return false;
      return value.precision === "DAY"
        ? date(value.value)
        : value.precision === "MONTH"
          ? /^\d{4}-\d{2}$/.test(value.value) && date(value.value + "-01")
          : value.precision === "YEAR" &&
            /^\d{4}$/.test(value.value) &&
            date(value.value + "-01-01");
    }
    case "EXPERIENCE":
      return (
        exactKeys(value, ["type", "entries"]) &&
        Array.isArray(value.entries) &&
        value.entries.length <= 20 &&
        value.entries.every(
          (entry: unknown) =>
            record(entry) &&
            exactKeys(entry, ["role", "start", "end", "relevant"]) &&
            text(entry.role, Infinity) &&
            date(entry.start) &&
            (entry.end === null ||
              (date(entry.end) && entry.end >= entry.start)) &&
            (entry.relevant === null || typeof entry.relevant === "boolean"),
        )
      );
    case "LANGUAGE_TESTS":
      return (
        exactKeys(value, ["type", "entries"]) &&
        Array.isArray(value.entries) &&
        value.entries.length <= 10 &&
        value.entries.every(
          (entry: unknown) =>
            record(entry) &&
            exactKeys(entry, ["test", "total", "components", "taken_on"]) &&
            text(entry.test, Infinity) &&
            typeof entry.total === "string" &&
            decimal.test(entry.total) &&
            date(entry.taken_on) &&
            record(entry.components) &&
            Object.values(entry.components).every(
              (score: unknown) =>
                typeof score === "string" && decimal.test(score),
            ),
        )
      );
    default:
      return false;
  }
}

export function decodeProfile(value: unknown): Profile {
  if (
    !record(value) ||
    !exactKeys(value, [
      "id",
      "version_id",
      "version_number",
      "facts",
      "updated_at",
    ]) ||
    typeof value.id !== "string" ||
    !uuid.test(value.id) ||
    typeof value.version_id !== "string" ||
    !uuid.test(value.version_id) ||
    !Number.isSafeInteger(value.version_number) ||
    (value.version_number as number) < 1 ||
    !instant(value.updated_at) ||
    !Array.isArray(value.facts) ||
    value.facts.length > 100
  )
    throw new ContractError();
  const seen = new Set<string>();
  for (const fact of value.facts as unknown[]) {
    if (
      !record(fact) ||
      !exactKeys(fact, [
        "id",
        "attribute",
        "value",
        "evidence_ids",
        "provenance",
        "confirmed_at",
        "valid_from",
        "valid_until",
        "conflict",
      ]) ||
      typeof fact.id !== "string" ||
      !uuid.test(fact.id) ||
      typeof fact.attribute !== "string" ||
      !Object.hasOwn(fields, fact.attribute) ||
      seen.has(fact.attribute) ||
      !validValue(fact.attribute as Attribute, fact.value) ||
      !uniqueStrings(
        fact.evidence_ids,
        65536,
        (id) => typeof id === "string" && uuid.test(id),
      ) ||
      !["USER_CONFIRMED", "USER_CONFIRMED_DOCUMENT", "CONFLICTING"].includes(
        String(fact.provenance),
      ) ||
      typeof fact.conflict !== "boolean" ||
      fact.conflict !== (fact.provenance === "CONFLICTING") ||
      (fact.provenance === "USER_CONFIRMED_DOCUMENT" &&
        fact.evidence_ids.length === 0) ||
      !instant(fact.confirmed_at) ||
      (fact.valid_from !== null && !date(fact.valid_from)) ||
      (fact.valid_until !== null && !date(fact.valid_until)) ||
      (typeof fact.valid_from === "string" &&
        typeof fact.valid_until === "string" &&
        fact.valid_until < fact.valid_from)
    )
      throw new ContractError();
    seen.add(fact.attribute);
  }
  return value as unknown as Profile;
}

export function decodeHistory(value: unknown): ProfilePage {
  if (
    !record(value) ||
    !exactKeys(value, ["items", "next_cursor"]) ||
    !Array.isArray(value.items) ||
    value.items.length > 100 ||
    (value.next_cursor !== null && !text(value.next_cursor, 1024))
  )
    throw new ContractError();
  return {
    items: value.items.map(decodeProfile),
    next_cursor: value.next_cursor as string | null,
  };
}

export interface Edit {
  attribute: Attribute;
  action: "unchanged" | "known" | "unknown" | "remove";
  value: Value | null;
}
export function initialEdits(profile: Profile): Edit[] {
  return (Object.keys(fields) as Attribute[]).map((attribute) => ({
    attribute,
    action: "unchanged",
    value:
      profile.facts.find((fact) => fact.attribute === attribute)?.value ?? null,
  }));
}
export class FormError extends Error {
  constructor(
    readonly attribute: Attribute,
    message: string,
  ) {
    super(message);
  }
}
export function buildPatch(profile: Profile, edits: readonly Edit[]): Patch {
  const changes: Patch["changes"][number][] = [];
  const remove_attributes: Attribute[] = [];
  const seen = new Set<Attribute>();
  for (const edit of edits) {
    if (seen.has(edit.attribute))
      throw new FormError(edit.attribute, "This field appears more than once.");
    seen.add(edit.attribute);
    if (edit.action === "unchanged") continue;
    if (edit.action === "remove") {
      if (profile.facts.some((fact) => fact.attribute === edit.attribute))
        remove_attributes.push(edit.attribute);
      continue;
    }
    if (
      !validValue(edit.attribute, edit.value) ||
      (edit.action === "unknown") !== (edit.value?.type === "UNKNOWN")
    )
      throw new FormError(
        edit.attribute,
        `Check ${fields[edit.attribute].label.toLowerCase()} before saving.`,
      );
    // An explicit edit is confirmed self-report; old evidence never supports a changed value.
    changes.push({
      attribute: edit.attribute,
      value: edit.value,
      evidence_ids: [],
    });
  }
  if (changes.length + remove_attributes.length === 0)
    throw new FormError(
      "education.enrolled",
      "Choose a field to update before saving.",
    );
  return {
    base_profile_version_id: profile.version_id,
    changes,
    remove_attributes,
  };
}
