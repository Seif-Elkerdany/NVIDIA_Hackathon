import assert from "node:assert/strict";
import test from "node:test";
import { build } from "vite";
import { fileURLToPath } from "node:url";

const bundle = await build({
  configFile: false,
  logLevel: "silent",
  resolve: { conditions: ["node"] },
  esbuild: { jsx: "automatic" },
  build: {
    write: false,
    rollupOptions: { external: [/^node:/, "stream", "util", "async_hooks"] },
    minify: false,
    lib: {
      entry: fileURLToPath(
        new URL("./profile-contract-fixture.tsx", import.meta.url),
      ),
      formats: ["es"],
    },
  },
});
const output = (Array.isArray(bundle) ? bundle[0] : bundle).output.find(
  (item) => item.type === "chunk",
).code;
const {
  buildPatch,
  decodeProfile,
  decodeHistory,
  initialEdits,
  validValue,
  fields,
  countries,
  renderProfile,
  createProfileApi,
} = await import(
  `data:text/javascript;base64,${Buffer.from(output).toString("base64")}`
);
const uid = (n) => `00000000-0000-4000-8000-${String(n).padStart(12, "0")}`;
const fact = (attribute, value, extra = {}) => ({
  id: uid(3),
  attribute,
  value,
  evidence_ids: [],
  provenance: "USER_CONFIRMED",
  confirmed_at: "2026-10-05T12:00:00Z",
  valid_from: null,
  valid_until: null,
  conflict: false,
  ...extra,
});
const profile = (facts = []) => ({
  id: uid(1),
  version_id: uid(2),
  version_number: 1,
  facts,
  updated_at: "2026-10-05T12:00:00Z",
});

test("GPA remains exact decimal strings on its original scale", () => {
  const source = decodeProfile(
    profile([
      fact("education.gpa", { type: "GPA", number: "3.50", scale_max: "5.00" }),
    ]),
  );
  const edit = initialEdits(source).map((entry) =>
    entry.attribute === "education.gpa"
      ? {
          ...entry,
          action: "known",
          value: { type: "GPA", number: "3.70", scale_max: "5.00" },
        }
      : entry,
  );
  const patch = buildPatch(source, edit);
  assert.deepEqual(patch.changes[0].value, {
    type: "GPA",
    number: "3.70",
    scale_max: "5.00",
  });
  const html = renderProfile(source);
  assert.match(html, /3\.50 \/ 5\.00/);
  assert.match(html, /Original scale/);
  assert.doesNotMatch(html, /2\.80|4\.00/);
});

test("unknown authorization and absent residence never become citizenship or false", () => {
  const source = decodeProfile(
    profile([
      fact("work_authorization.countries", {
        type: "UNKNOWN",
        reason: "USER_UNSURE",
      }),
    ]),
  );
  const html = renderProfile(source);
  assert.match(html, /Unknown/);
  assert.match(html, /not sure/);
  assert.match(html, /Not provided/);
  const edits = initialEdits(source).map((entry) =>
    entry.attribute === "skills"
      ? {
          ...entry,
          action: "known",
          value: { type: "STRING_SET", values: ["Python"] },
        }
      : entry,
  );
  assert.deepEqual(
    buildPatch(source, edits).changes.map((entry) => entry.attribute),
    ["skills"],
  );
  assert.deepEqual(buildPatch(source, edits).remove_attributes, []);
});

test("known empty authorization is distinct from unknown, while residence needs one country", () => {
  assert.equal(
    validValue("work_authorization.countries", {
      type: "COUNTRY_SET",
      values: [],
    }),
    true,
  );
  assert.equal(
    validValue("location.country", { type: "COUNTRY_SET", values: [] }),
    false,
  );
  assert.equal(
    validValue("work_authorization.countries", {
      type: "UNKNOWN",
      reason: "NOT_PROVIDED",
    }),
    true,
  );
});

test("invalid decimal representations, scale overflow and duplicates fail before publication", () => {
  for (const value of [
    { type: "GPA", number: 3.5, scale_max: "5.00" },
    { type: "GPA", number: "3e0", scale_max: "5.00" },
    { type: "GPA", number: "5.01", scale_max: "5.00" },
    { type: "GPA", number: "0", scale_max: "0" },
  ])
    assert.equal(validValue("education.gpa", value), false);
  assert.equal(
    validValue("skills", { type: "STRING_SET", values: ["Python", "Python"] }),
    false,
  );
  assert.equal(
    validValue("skills", { type: "STRING_SET", values: ["x".repeat(81)] }),
    false,
  );
  assert.equal(
    validValue("location.country", { type: "COUNTRY_SET", values: ["ZZ"] }),
    false,
  );
});

test("decimal comparison does not lose precision above the floating-point safe range", () => {
  assert.equal(
    validValue("education.gpa", {
      type: "GPA",
      number: "9007199254740993.01",
      scale_max: "9007199254740993.00",
    }),
    false,
  );
  assert.equal(
    validValue("education.gpa", {
      type: "GPA",
      number: "3.50000000000000000001",
      scale_max: "3.50000000000000000000",
    }),
    false,
  );
});

test("changed values become self-report without reusing old document evidence", () => {
  const source = decodeProfile(
    profile([
      fact(
        "education.gpa",
        { type: "GPA", number: "3.50", scale_max: "5.00" },
        { provenance: "USER_CONFIRMED_DOCUMENT", evidence_ids: [uid(4)] },
      ),
    ]),
  );
  const patch = buildPatch(source, [
    {
      attribute: "education.gpa",
      action: "known",
      value: { type: "GPA", number: "3.60", scale_max: "5.00" },
    },
  ]);
  assert.deepEqual(patch.changes[0].evidence_ids, []);
  assert.equal(patch.base_profile_version_id, source.version_id);
  assert.equal(source.facts[0].value.number, "3.50");
});

test("explicit unknown and removal preserve the typed patch contract", () => {
  const source = profile([
    fact("education.enrolled", { type: "BOOLEAN", value: true }),
  ]);
  assert.deepEqual(
    buildPatch(source, [
      { attribute: "education.enrolled", action: "remove", value: null },
      {
        attribute: "work_authorization.countries",
        action: "unknown",
        value: { type: "UNKNOWN", reason: "USER_UNSURE" },
      },
    ]),
    {
      base_profile_version_id: source.version_id,
      changes: [
        {
          attribute: "work_authorization.countries",
          value: { type: "UNKNOWN", reason: "USER_UNSURE" },
          evidence_ids: [],
        },
      ],
      remove_attributes: ["education.enrolled"],
    },
  );
  assert.throws(
    () => buildPatch(source, initialEdits(source)),
    /Choose a field/,
  );
});

test("malformed private responses and repeated attributes are rejected", () => {
  const source = profile([
    fact("education.enrolled", { type: "BOOLEAN", value: true }),
  ]);
  assert.throws(() => decodeProfile({ ...source, owner_id: uid(9) }));
  assert.throws(() =>
    decodeProfile({ ...source, updated_at: "2026-10-05T24:00:00Z" }),
  );
  assert.throws(() =>
    decodeProfile({ ...source, facts: [...source.facts, ...source.facts] }),
  );
  assert.throws(() =>
    decodeProfile(
      profile([
        fact("education.enrolled", { type: "BOOLEAN", value: "false" }),
      ]),
    ),
  );
  assert.throws(() =>
    decodeProfile(
      profile([
        fact(
          "education.enrolled",
          { type: "BOOLEAN", value: true },
          { provenance: "USER_CONFIRMED_DOCUMENT" },
        ),
      ]),
    ),
  );
  assert.throws(() => decodeHistory({ items: [source], next_cursor: 1 }));
});

test("precision and experience relevance remain explicit", () => {
  assert.equal(
    validValue("education.graduation", {
      type: "DATE",
      precision: "YEAR",
      value: "2028",
      expected: true,
    }),
    true,
  );
  assert.equal(
    validValue("education.graduation", {
      type: "DATE",
      precision: "DAY",
      value: "2026-02-30",
      expected: false,
    }),
    false,
  );
  assert.equal(
    validValue("experience", {
      type: "EXPERIENCE",
      entries: [
        {
          role: "Synthetic intern",
          start: "2026-01-01",
          end: null,
          relevant: null,
        },
      ],
    }),
    true,
  );
  assert.equal(
    validValue("experience", {
      type: "EXPERIENCE",
      entries: [
        {
          role: "Synthetic intern",
          start: "2026-06-01",
          end: "2026-01-01",
          relevant: false,
        },
      ],
    }),
    false,
  );
});

test("provenance and source-date limits are visible and malicious text stays escaped", () => {
  const html = renderProfile(
    profile([
      fact(
        "education.institution",
        { type: "STRING", value: '<img src=x onerror="window.attack=true">' },
        { provenance: "USER_CONFIRMED_DOCUMENT", evidence_ids: [uid(4)] },
      ),
    ]),
  );
  assert.match(html, /Supported by your document/);
  assert.match(html, /2026-10-05/);
  assert.match(html, /source date not provided/);
  assert.match(html, /does not verify/);
  assert.doesNotMatch(html, /<img/);
  assert.match(html, /&lt;img/);
});

test("all catalog controls and country options derive from the shared contract", () => {
  assert.equal(Object.keys(fields).length, 13);
  assert.equal(countries.includes("EG"), true);
  assert.equal(countries.includes("ZZ"), false);
  const html = renderProfile(profile());
  assert.match(html, /Country of residence/);
  assert.match(html, /Citizenship/);
  assert.match(html, /Work authorization/);
  assert.match(html, /Confirm the changes|confirm the changes/);
});

test("typed profile adapter uses only documented owner routes and forwards cancellation", async () => {
  const seen = [];
  const abort = new AbortController();
  const source = profile();
  const wire = {
    get: async (path, decode, signal) => {
      seen.push({ path, signal });
      return decode(
        path.includes("?limit")
          ? { items: [source], next_cursor: null }
          : source,
      );
    },
    patchProfile: async (body, key, decode, signal) => {
      seen.push({ body, key, signal });
      return decode(source);
    },
  };
  const api = createProfileApi(wire);
  await api.current(abort.signal);
  await api.history("opaque+/cursor", abort.signal);
  await api.version(uid(2), abort.signal);
  await api.save(
    {
      base_profile_version_id: uid(2),
      changes: [],
      remove_attributes: ["skills"],
    },
    uid(8),
    abort.signal,
  );
  assert.equal(seen[0].path, "/api/v1/profile");
  assert.equal(seen[0].signal, abort.signal);
  assert.match(seen[1].path, /cursor=opaque%2B%2Fcursor/);
  assert.equal(seen[3].key, uid(8));
  assert.throws(() => api.version("../../me"), /UUID/);
});
