import { useEffect, useState } from "react";
import {
  fields,
  countries,
  unknownReasons,
  type Attribute,
  type Edit,
  type Fact,
  type Value,
  type Country,
} from "./model";

export function FactSummary({ fact }: { fact: Fact }) {
  const labels = {
    USER_CONFIRMED: "Confirmed self-report",
    USER_CONFIRMED_DOCUMENT: "Supported by your document",
    CONFLICTING: "Conflicting evidence",
  };
  return (
    <div className="profile-provenance">
      <strong>{labels[fact.provenance]}</strong>
      <span>
        Confirmed{" "}
        <time dateTime={fact.confirmed_at}>
          {fact.confirmed_at.slice(0, 10)} (UTC)
        </time>
      </span>
      {fact.valid_from && (
        <span>
          Valid from <time dateTime={fact.valid_from}>{fact.valid_from}</time>
        </span>
      )}
      {fact.valid_until && (
        <span>
          Valid until{" "}
          <time dateTime={fact.valid_until}>{fact.valid_until}</time>
        </span>
      )}
      {fact.evidence_ids.length > 0 && (
        <span>
          {fact.evidence_ids.length} supporting passage(s). Document source date
          not provided.
        </span>
      )}
      {fact.provenance === "USER_CONFIRMED_DOCUMENT" && (
        <span>This does not verify the issuing institution.</span>
      )}
      {fact.conflict && (
        <span>Review this disagreement before confirming a replacement.</span>
      )}
    </div>
  );
}

export function ValueText({ value }: { value: Value }) {
  switch (value.type) {
    case "UNKNOWN":
      return <>Unknown — {unknownReasons[value.reason]}</>;
    case "STRING":
      return <>{value.value}</>;
    case "BOOLEAN":
      return <>{value.value ? "Yes" : "No"}</>;
    case "COUNTRY_SET":
      return (
        <>
          {value.values.length
            ? value.values.join(", ")
            : "None (explicitly confirmed)"}
        </>
      );
    case "STRING_SET":
      return (
        <>
          {value.values.length
            ? value.values.join(", ")
            : "None (explicitly confirmed)"}
        </>
      );
    case "GPA":
      return (
        <>
          {value.number} / {value.scale_max} · Original scale
        </>
      );
    case "DATE":
      return (
        <>
          {value.value} · {value.precision.toLowerCase()} precision
          {value.expected ? " · Expected" : " · Actual"}
        </>
      );
    case "EXPERIENCE":
      return (
        <>
          {value.entries.length
            ? value.entries
                .map(
                  (entry) =>
                    `${entry.role}: ${entry.start} to ${entry.end ?? "ongoing"}; relevance ${entry.relevant === null ? "unknown" : entry.relevant ? "yes" : "no"}`,
                )
                .join("; ")
            : "No experience listed"}
        </>
      );
    case "LANGUAGE_TESTS":
      return (
        <>
          {value.entries.length
            ? value.entries
                .map(
                  (entry) =>
                    `${entry.test}: ${entry.total} (${entry.taken_on}); ${Object.entries(
                      entry.components,
                    )
                      .map(([name, score]) => `${name}: ${score}`)
                      .join(", ")}`,
                )
                .join("; ")
            : "No language tests listed"}
        </>
      );
  }
}

export function FieldEditor({
  edit,
  fact,
  onChange,
  disabled,
  error,
}: {
  edit: Edit;
  fact?: Fact;
  onChange(edit: Edit): void;
  disabled: boolean;
  error?: string;
}) {
  const attribute = edit.attribute;
  const label = fields[attribute].label;
  const id = `profile-${attribute.replaceAll(".", "-")}`;
  const value = edit.value;
  const set = (next: Value) => onChange({ ...edit, value: next });
  const isKnown = edit.action === "known";
  return (
    <fieldset
      className="profile-field"
      disabled={disabled}
      aria-describedby={error ? `${id}-error` : undefined}
    >
      <legend>{label}</legend>
      <p className="profile-current">
        Current: {fact ? <ValueText value={fact.value} /> : "Not provided"}
      </p>
      {fact ? (
        <FactSummary fact={fact} />
      ) : (
        <p className="muted">Missing information remains unknown.</p>
      )}
      <label htmlFor={id + "-action"}>Update {label.toLowerCase()}</label>
      <select
        id={id + "-action"}
        value={edit.action}
        onChange={(event) => {
          const action = event.target.value as Edit["action"];
          onChange({
            ...edit,
            action,
            value:
              action === "unknown"
                ? { type: "UNKNOWN", reason: "USER_UNSURE" }
                : action === "known" && value?.type === "UNKNOWN"
                  ? null
                  : value,
          });
        }}
      >
        <option value="unchanged">Leave unchanged</option>
        <option value="known">Enter a known value</option>
        <option value="unknown">Mark as unknown</option>
        <option value="remove" disabled={!fact}>
          Remove this field
        </option>
      </select>
      {edit.action === "unknown" && (
        <>
          <label htmlFor={id + "-reason"}>
            Why is {label.toLowerCase()} unknown?
          </label>
          <select
            id={id + "-reason"}
            value={value?.type === "UNKNOWN" ? value.reason : "USER_UNSURE"}
            onChange={(e) =>
              set({
                type: "UNKNOWN",
                reason: e.target.value as keyof typeof unknownReasons,
              })
            }
          >
            {Object.entries(unknownReasons).map(([reason, title]) => (
              <option key={reason} value={reason}>
                {title}
              </option>
            ))}
          </select>
        </>
      )}
      {edit.action === "remove" && (
        <p>
          This removes the field from the next version. History remains
          available.
        </p>
      )}
      {isKnown && fields[attribute].type === "STRING" && (
        <>
          <label htmlFor={id + "-value"}>{label}</label>
          <input
            id={id + "-value"}
            maxLength={500}
            value={value?.type === "STRING" ? value.value : ""}
            onChange={(e) => set({ type: "STRING", value: e.target.value })}
          />
        </>
      )}
      {isKnown && fields[attribute].type === "BOOLEAN" && (
        <>
          <label htmlFor={id + "-value"}>{label}</label>
          <select
            id={id + "-value"}
            value={value?.type === "BOOLEAN" ? String(value.value) : ""}
            onChange={(e) =>
              e.target.value
                ? set({ type: "BOOLEAN", value: e.target.value === "true" })
                : onChange({ ...edit, value: null })
            }
          >
            <option value="">Choose yes or no</option>
            <option value="true">Yes</option>
            <option value="false">No</option>
          </select>
        </>
      )}
      {isKnown && fields[attribute].type === "COUNTRY_SET" && (
        <>
          <p id={id + "-help"}>
            {attribute === "location.country"
              ? "Select your residence. This does not establish citizenship or work authorization."
              : "Select only countries you can confirm. A known empty list is different from unknown."}
          </p>
          <label htmlFor={id + "-value"}>{label} countries</label>
          <select
            id={id + "-value"}
            multiple={attribute !== "location.country"}
            size={attribute !== "location.country" ? 5 : undefined}
            aria-describedby={id + "-help"}
            value={
              attribute === "location.country"
                ? value?.type === "COUNTRY_SET"
                  ? (value.values[0] ?? "")
                  : ""
                : value?.type === "COUNTRY_SET"
                  ? [...value.values]
                  : []
            }
            onChange={(e) =>
              set({
                type: "COUNTRY_SET",
                values: Array.from(e.target.selectedOptions)
                  .map((option) => option.value as Country)
                  .filter((code) => countries.includes(code)),
              })
            }
          >
            {attribute === "location.country" && (
              <option value="">Choose a country</option>
            )}
            {countries.map((country) => (
              <option key={country} value={country}>
                {new Intl.DisplayNames(["en"], { type: "region" }).of(country)}{" "}
                ({country})
              </option>
            ))}
          </select>
          {attribute !== "location.country" && (
            <button
              type="button"
              className="button button--secondary"
              onClick={() => set({ type: "COUNTRY_SET", values: [] })}
            >
              Confirm none for {label.toLowerCase()}
            </button>
          )}
        </>
      )}
      {isKnown && fields[attribute].type === "STRING_SET" && (
        <>
          <label htmlFor={id + "-value"}>Skills — one per line</label>
          <textarea
            id={id + "-value"}
            rows={4}
            value={value?.type === "STRING_SET" ? value.values.join("\n") : ""}
            onChange={(e) =>
              set({
                type: "STRING_SET",
                values: e.target.value.split("\n").filter(Boolean),
              })
            }
          />
        </>
      )}
      {isKnown && fields[attribute].type === "GPA" && (
        <div className="profile-pair">
          <label htmlFor={id + "-number"}>
            GPA number
            <input
              id={id + "-number"}
              inputMode="decimal"
              value={value?.type === "GPA" ? value.number : ""}
              onChange={(e) =>
                set({
                  type: "GPA",
                  number: e.target.value,
                  scale_max: value?.type === "GPA" ? value.scale_max : "",
                })
              }
            />
          </label>
          <label htmlFor={id + "-scale"}>
            Original scale maximum
            <input
              id={id + "-scale"}
              inputMode="decimal"
              value={value?.type === "GPA" ? value.scale_max : ""}
              onChange={(e) =>
                set({
                  type: "GPA",
                  number: value?.type === "GPA" ? value.number : "",
                  scale_max: e.target.value,
                })
              }
            />
          </label>
          <p>
            Use the original decimal values. Your GPA is never converted to
            another scale.
          </p>
        </div>
      )}
      {isKnown && fields[attribute].type === "DATE" && (
        <>
          <label htmlFor={id + "-precision"}>Date precision</label>
          <select
            id={id + "-precision"}
            value={value?.type === "DATE" ? value.precision : ""}
            onChange={(e) =>
              e.target.value &&
              set({
                type: "DATE",
                value: value?.type === "DATE" ? value.value : "",
                precision: e.target.value as "DAY" | "MONTH" | "YEAR",
                expected: value?.type === "DATE" ? value.expected : false,
              })
            }
          >
            <option value="">Choose precision</option>
            <option value="YEAR">Year</option>
            <option value="MONTH">Month</option>
            <option value="DAY">Day</option>
          </select>
          <label htmlFor={id + "-value"}>
            {label} (
            {value?.type === "DATE"
              ? { YEAR: "YYYY", MONTH: "YYYY-MM", DAY: "YYYY-MM-DD" }[
                  value.precision
                ]
              : "choose precision first"}
            )
          </label>
          <input
            id={id + "-value"}
            disabled={value?.type !== "DATE"}
            value={value?.type === "DATE" ? value.value : ""}
            onChange={(e) =>
              value?.type === "DATE" && set({ ...value, value: e.target.value })
            }
          />
          {value?.type === "DATE" && (
            <label className="profile-check">
              <input
                type="checkbox"
                checked={value.expected}
                onChange={(e) => set({ ...value, expected: e.target.checked })}
              />
              This is an expected date
            </label>
          )}
        </>
      )}
      {isKnown && fields[attribute].type === "EXPERIENCE" && (
        <>
          {(value?.type === "EXPERIENCE" ? value.entries : []).map(
            (entry, index) => (
              <fieldset className="profile-entry" key={index}>
                <legend>Experience {index + 1}</legend>
                <label>
                  Role
                  <input
                    value={entry.role}
                    onChange={(e) =>
                      value?.type === "EXPERIENCE" &&
                      set({
                        ...value,
                        entries: value.entries.map((old, i) =>
                          i === index ? { ...old, role: e.target.value } : old,
                        ),
                      })
                    }
                  />
                </label>
                <label>
                  Start date
                  <input
                    type="date"
                    value={entry.start}
                    onChange={(e) =>
                      value?.type === "EXPERIENCE" &&
                      set({
                        ...value,
                        entries: value.entries.map((old, i) =>
                          i === index ? { ...old, start: e.target.value } : old,
                        ),
                      })
                    }
                  />
                </label>
                <label>
                  End date
                  <input
                    type="date"
                    disabled={entry.end === null}
                    value={entry.end ?? ""}
                    onChange={(e) =>
                      value?.type === "EXPERIENCE" &&
                      set({
                        ...value,
                        entries: value.entries.map((old, i) =>
                          i === index ? { ...old, end: e.target.value } : old,
                        ),
                      })
                    }
                  />
                </label>
                <label className="profile-check">
                  <input
                    type="checkbox"
                    checked={entry.end === null}
                    onChange={(e) =>
                      value?.type === "EXPERIENCE" &&
                      set({
                        ...value,
                        entries: value.entries.map((old, i) =>
                          i === index
                            ? { ...old, end: e.target.checked ? null : "" }
                            : old,
                        ),
                      })
                    }
                  />
                  Ongoing
                </label>
                <label>
                  Relevant experience
                  <select
                    value={
                      entry.relevant === null
                        ? "unknown"
                        : String(entry.relevant)
                    }
                    onChange={(e) =>
                      value?.type === "EXPERIENCE" &&
                      set({
                        ...value,
                        entries: value.entries.map((old, i) =>
                          i === index
                            ? {
                                ...old,
                                relevant:
                                  e.target.value === "unknown"
                                    ? null
                                    : e.target.value === "true",
                              }
                            : old,
                        ),
                      })
                    }
                  >
                    <option value="unknown">Unknown</option>
                    <option value="true">Yes</option>
                    <option value="false">No</option>
                  </select>
                </label>
                <button
                  type="button"
                  className="button button--secondary"
                  onClick={() =>
                    value?.type === "EXPERIENCE" &&
                    set({
                      ...value,
                      entries: value.entries.filter((_, i) => i !== index),
                    })
                  }
                >
                  Remove experience {index + 1}
                </button>
              </fieldset>
            ),
          )}
          <button
            type="button"
            className="button button--secondary"
            disabled={
              value?.type === "EXPERIENCE" && value.entries.length >= 20
            }
            onClick={() =>
              set({
                type: "EXPERIENCE",
                entries: [
                  ...(value?.type === "EXPERIENCE" ? value.entries : []),
                  { role: "", start: "", end: "", relevant: null },
                ],
              })
            }
          >
            Add experience
          </button>
          <button
            type="button"
            className="button button--secondary"
            onClick={() => set({ type: "EXPERIENCE", entries: [] })}
          >
            Confirm no experience entries
          </button>
        </>
      )}
      {isKnown && fields[attribute].type === "LANGUAGE_TESTS" && (
        <>
          {(value?.type === "LANGUAGE_TESTS" ? value.entries : []).map(
            (entry, index) => {
              const update = (next: typeof entry) =>
                value?.type === "LANGUAGE_TESTS" &&
                set({
                  ...value,
                  entries: value.entries.map((old, i) =>
                    i === index ? next : old,
                  ),
                });
              return (
                <fieldset className="profile-entry" key={index}>
                  <legend>Language test {index + 1}</legend>
                  <label>
                    Test name
                    <input
                      value={entry.test}
                      onChange={(e) =>
                        update({ ...entry, test: e.target.value })
                      }
                    />
                  </label>
                  <label>
                    Total score
                    <input
                      inputMode="decimal"
                      value={entry.total}
                      onChange={(e) =>
                        update({ ...entry, total: e.target.value })
                      }
                    />
                  </label>
                  <label>
                    Date taken
                    <input
                      type="date"
                      value={entry.taken_on}
                      onChange={(e) =>
                        update({ ...entry, taken_on: e.target.value })
                      }
                    />
                  </label>
                  <label>
                    Component scores — one name: score per line
                    <ComponentScores
                      value={entry.components}
                      onChange={(components) =>
                        update({ ...entry, components })
                      }
                    />
                  </label>
                  <button
                    type="button"
                    className="button button--secondary"
                    onClick={() =>
                      value?.type === "LANGUAGE_TESTS" &&
                      set({
                        ...value,
                        entries: value.entries.filter((_, i) => i !== index),
                      })
                    }
                  >
                    Remove language test {index + 1}
                  </button>
                </fieldset>
              );
            },
          )}
          <button
            type="button"
            className="button button--secondary"
            disabled={
              value?.type === "LANGUAGE_TESTS" && value.entries.length >= 10
            }
            onClick={() =>
              set({
                type: "LANGUAGE_TESTS",
                entries: [
                  ...(value?.type === "LANGUAGE_TESTS" ? value.entries : []),
                  { test: "", total: "", taken_on: "", components: {} },
                ],
              })
            }
          >
            Add language test
          </button>
          <button
            type="button"
            className="button button--secondary"
            onClick={() => set({ type: "LANGUAGE_TESTS", entries: [] })}
          >
            Confirm no language tests
          </button>
        </>
      )}
      {error && (
        <p id={id + "-error"} role="alert" className="profile-field-error">
          {error}
        </p>
      )}
    </fieldset>
  );
}

export const groups = [
  ...new Set(Object.values(fields).map((field) => field.group)),
];
export function attributesIn(group: string): Attribute[] {
  return (Object.keys(fields) as Attribute[]).filter(
    (attribute) => fields[attribute].group === group,
  );
}

function parseComponents(raw: string): Record<string, string> {
  const result: Record<string, string> = Object.create(null);
  for (const line of raw.split("\n").filter((line) => line.trim())) {
    const at = line.indexOf(":");
    const name = (at < 0 ? line : line.slice(0, at)).trim();
    // An invalid decimal keeps incomplete and repeated names from being saved.
    result[name] = name in result || at < 0 ? "" : line.slice(at + 1).trim();
  }
  return result;
}
function ComponentScores({
  value,
  onChange,
}: {
  value: Record<string, string>;
  onChange(value: Record<string, string>): void;
}) {
  const format = (scores: Record<string, string>) =>
    Object.entries(scores)
      .map(([name, score]) => `${name}: ${score}`)
      .join("\n");
  const [raw, setRaw] = useState(() => format(value));
  useEffect(() => {
    if (JSON.stringify(parseComponents(raw)) !== JSON.stringify(value))
      setRaw(format(value));
  }, [raw, value]);
  return (
    <textarea
      value={raw}
      onChange={(event) => {
        setRaw(event.target.value);
        onChange(parseComponents(event.target.value));
      }}
    />
  );
}
