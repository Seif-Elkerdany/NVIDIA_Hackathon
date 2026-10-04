import type { components } from "../../generated/api";
import { ContractError } from "../../lib/api";

export type Account = components["schemas"]["Account"];
export type ConsentPatch = Pick<
  components["schemas"]["PatchMe"],
  "consent_version"
>;

function object(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
function timestamp(value: unknown): value is string {
  return (
    typeof value === "string" &&
    /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z$/.test(value) &&
    Number.isFinite(Date.parse(value))
  );
}

export function decodeAccount(value: unknown): Account {
  if (
    !object(value) ||
    Object.keys(value).sort().join() !==
      "consent,created_at,display_name,id,is_demo,status,timezone" ||
    typeof value.id !== "string" ||
    !/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
      value.id,
    ) ||
    value.status !== "ACTIVE" ||
    typeof value.display_name !== "string" ||
    [...value.display_name].length < 1 ||
    [...value.display_name].length > 80 ||
    typeof value.timezone !== "string" ||
    typeof value.is_demo !== "boolean" ||
    !timestamp(value.created_at)
  )
    throw new ContractError();
  try {
    new Intl.DateTimeFormat("en", { timeZone: value.timezone });
  } catch (error: unknown) {
    if (error instanceof RangeError) throw new ContractError();
    throw error;
  }
  if (
    value.consent !== null &&
    (!object(value.consent) ||
      Object.keys(value.consent).sort().join() !== "accepted_at,version" ||
      typeof value.consent.version !== "string" ||
      !value.consent.version.trim() ||
      !timestamp(value.consent.accepted_at))
  )
    throw new ContractError();
  return value as Account;
}

export function processingAllowed(
  account: Account | undefined,
  version: string,
  declined: boolean,
): boolean {
  return (
    !declined &&
    account?.status === "ACTIVE" &&
    account.consent?.version === version
  );
}
