import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router";
import { useState } from "react";
import { ProfileScreen } from "../src/features/profile/ProfileScreen";
import {
  decodeProfile,
  type Profile,
  type Patch,
} from "../src/features/profile/model";
import type { ProfileApi } from "../src/features/profile/api";
import { ApiError, type Problem } from "../src/lib/api";
import "../src/styles/shell.css";

const uid = (n: number) =>
  `00000000-0000-4000-8000-${String(n).padStart(12, "0")}`;
const now = "2026-10-05T12:00:00Z";
const initial: Profile = decodeProfile({
  id: uid(1),
  version_id: uid(2),
  version_number: 1,
  updated_at: now,
  facts: [
    {
      id: uid(3),
      attribute: "education.gpa",
      value: { type: "GPA", number: "3.50", scale_max: "5.00" },
      evidence_ids: [uid(4)],
      provenance: "USER_CONFIRMED_DOCUMENT",
      confirmed_at: now,
      valid_from: "2026-09-01",
      valid_until: null,
      conflict: false,
    },
    {
      id: uid(5),
      attribute: "work_authorization.countries",
      value: { type: "UNKNOWN", reason: "USER_UNSURE" },
      evidence_ids: [],
      provenance: "USER_CONFIRMED",
      confirmed_at: now,
      valid_from: null,
      valid_until: null,
      conflict: false,
    },
    {
      id: uid(6),
      attribute: "education.institution",
      value: {
        type: "STRING",
        value: '<img src=x onerror="window.syntheticInjection=true">',
      },
      evidence_ids: [],
      provenance: "CONFLICTING",
      confirmed_at: now,
      valid_from: null,
      valid_until: null,
      conflict: true,
    },
  ],
});
const state = {
  current: initial,
  versions: [initial],
  calls: [] as { body: Patch; key: string }[],
  failure: "" as "" | "conflict" | "timeout" | "defer",
  reloadFailure: new URLSearchParams(location.search).get("mode") === "error",
  releaseSave: null as (() => void) | null,
  identity: uid(10),
  loadCount: 0,
};
const replay = new Map<string, { body: string; response: Profile }>();
function problem(code: string, status: number): ApiError {
  const payload: Problem = {
    type: `urn:benefitbridge:problem:${code.toLowerCase().replaceAll("_", "-")}`,
    title: "Synthetic error",
    detail: "Synthetic request could not complete.",
    code,
    status,
    request_id: "synthetic-profile",
    errors: [],
    retryable: false,
  };
  return new ApiError(
    "problem",
    payload.detail,
    payload.request_id,
    status,
    payload,
  );
}
function publish(body: Patch): Profile {
  const removed = new Set([
    ...body.remove_attributes,
    ...body.changes.map((change) => change.attribute),
  ]);
  const next: Profile = decodeProfile({
    ...state.current,
    version_id: uid(100 + state.current.version_number),
    version_number: state.current.version_number + 1,
    facts: [
      ...state.current.facts.filter((fact) => !removed.has(fact.attribute)),
      ...body.changes.map((change, i) => ({
        ...change,
        id: uid(200 + state.current.version_number * 20 + i),
        confirmed_at: now,
        valid_from: null,
        valid_until: null,
        provenance: "USER_CONFIRMED",
        conflict: false,
      })),
    ],
  });
  state.current = next;
  state.versions.unshift(next);
  return next;
}
const api: ProfileApi = {
  current: async (signal) => {
    signal?.throwIfAborted();
    state.loadCount++;
    if (new URLSearchParams(location.search).get("mode") === "loading") {
      await new Promise<void>((_, reject) =>
        signal?.addEventListener(
          "abort",
          () => reject(new DOMException("Cancelled", "AbortError")),
          { once: true },
        ),
      );
    }
    if (state.reloadFailure) throw problem("SERVICE_UNAVAILABLE", 503);
    return structuredClone(state.current);
  },
  history: async (cursor, signal) => {
    signal?.throwIfAborted();
    return {
      items: cursor ? state.versions.slice(1) : state.versions.slice(0, 1),
      next_cursor: !cursor && state.versions.length > 1 ? "older" : null,
    };
  },
  version: async (id, signal) => {
    signal?.throwIfAborted();
    const row = state.versions.find((profile) => profile.version_id === id);
    if (!row) throw problem("NOT_FOUND", 404);
    return structuredClone(row);
  },
  save: async (body, key) => {
    state.calls.push({ body: structuredClone(body), key });
    const old = replay.get(key);
    if (old) {
      if (old.body !== JSON.stringify(body))
        throw problem("IDEMPOTENCY_CONFLICT", 409);
      return structuredClone(old.response);
    }
    if (state.failure === "conflict") {
      state.failure = "";
      publish({
        ...body,
        changes: [
          {
            attribute: "education.gpa",
            value: { type: "GPA", number: "4.25", scale_max: "5.00" },
            evidence_ids: [],
          },
        ],
      });
      throw problem("VERSION_CONFLICT", 409);
    }
    if (state.failure === "defer")
      await new Promise<void>((resolve) => {
        state.releaseSave = resolve;
      });
    if (body.base_profile_version_id !== state.current.version_id)
      throw problem("VERSION_CONFLICT", 409);
    const next = publish(body);
    replay.set(key, { body: JSON.stringify(body), response: next });
    if (state.failure === "timeout") {
      state.failure = "";
      throw new ApiError(
        "timeout",
        "The request timed out. Try again.",
        "synthetic-timeout",
      );
    }
    return structuredClone(next);
  },
};
declare global {
  interface Window {
    profileTest: typeof state & { switchIdentity(): void };
  }
}
function Fixture() {
  const [identity, setIdentity] = useState(state.identity);
  const [client] = useState(() => new QueryClient());
  window.profileTest = {
    ...state,
    get current() {
      return state.current;
    },
    get calls() {
      return state.calls;
    },
    get loadCount() {
      return state.loadCount;
    },
    get failure() {
      return state.failure;
    },
    set failure(value) {
      state.failure = value;
    },
    get reloadFailure() {
      return state.reloadFailure;
    },
    set reloadFailure(value) {
      state.reloadFailure = value;
    },
    get releaseSave() {
      return state.releaseSave;
    },
    switchIdentity() {
      state.identity = uid(11);
      state.current = {
        ...initial,
        id: uid(12),
        version_id: uid(13),
        facts: [],
      };
      setIdentity(state.identity);
    },
  };
  return (
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <main>
          <ProfileScreen api={api} identity={[identity, 1]} />
        </main>
      </MemoryRouter>
    </QueryClientProvider>
  );
}
createRoot(document.getElementById("root")!).render(<Fixture />);
