import assert from "node:assert/strict";
import test from "node:test";
import { build } from "vite";
import { fileURLToPath } from "node:url";

const bundle = await build({
  configFile: false,
  logLevel: "silent",
  build: {
    write: false,
    minify: false,
    lib: {
      entry: fileURLToPath(
        new URL("./auth-contract-fixture.ts", import.meta.url),
      ),
      formats: ["es"],
    },
  },
});
const {
  MemorySession,
  consumeAuthCallback,
  authConfig,
  decodeAccount,
  processingAllowed,
} = await import(
  `data:text/javascript;base64,${Buffer.from((Array.isArray(bundle) ? bundle[0] : bundle).output.find((item) => item.type === "chunk").code).toString("base64")}`
);

function clock() {
  let now = 1_000_000;
  let timer = null;
  return {
    now: () => now,
    schedule(callback, delay) {
      timer = { callback, at: now + delay };
      return () => {
        timer = null;
      };
    },
    advance(ms) {
      now += ms;
      if (timer && timer.at <= now) {
        const task = timer;
        timer = null;
        task.callback();
      }
    },
  };
}
const account = Object.freeze({
  id: "00000000-0000-4000-8000-000000000001",
  status: "ACTIVE",
  display_name: "Synthetic applicant",
  timezone: "UTC",
  is_demo: false,
  created_at: "2026-10-01T00:00:00Z",
  consent: null,
});
const values = {
  VITE_SUPABASE_URL: "https://synthetic.supabase.invalid",
  VITE_SUPABASE_PUBLISHABLE_KEY: "sb_publishable_synthetic",
  VITE_PROCESSING_NOTICE_VERSION: "2026-10-01",
  VITE_PROCESSING_NOTICE_TEXT: "Synthetic processing notice.",
};

test("memory sessions expire using the injected clock and never survive recreation", () => {
  const time = clock();
  const sessions = new MemorySession(time);
  let events = 0;
  sessions.subscribe(() => events++);
  sessions.replace({
    accessToken: "synthetic-secret",
    subject: account.id,
    expiresAt: 1010,
    recovery: false,
  });
  assert.equal(sessions.token(), "synthetic-secret");
  assert.equal(JSON.stringify(sessions.snapshot()).includes("secret"), false);
  time.advance(10_000);
  assert.equal(sessions.token(), null);
  assert.equal(sessions.snapshot().expired, true);
  assert.equal(new MemorySession(time).token(), null);
  assert.equal(events, 2);
});

test("refresh replaces the expiry timer and recovery never exposes an API bearer", () => {
  const time = clock();
  const sessions = new MemorySession(time);
  sessions.replace({
    accessToken: "first",
    subject: account.id,
    expiresAt: 1010,
    recovery: false,
  });
  sessions.replace({
    accessToken: "second",
    subject: account.id,
    expiresAt: 1020,
    recovery: false,
  });
  time.advance(10_000);
  assert.equal(sessions.token(), "second");
  sessions.replace({
    accessToken: "recovery",
    subject: account.id,
    expiresAt: 1020,
    recovery: true,
  });
  assert.equal(sessions.token(), null);
  time.advance(10_000);
  assert.equal(sessions.snapshot().subject, null);
});

test("callbacks scrub history before yielding only one-time fragment hashes", () => {
  const calls = [];
  const callback = consumeAuthCallback(
    "https://app.invalid/account/recovery#token_hash=synthetic_hash&type=recovery",
    (path) => calls.push(path),
  );
  assert.deepEqual(calls, ["/account/recovery"]);
  assert.deepEqual(callback, {
    kind: "verify",
    tokenHash: "synthetic_hash",
    type: "recovery",
  });
  assert.equal(
    consumeAuthCallback(
      "https://app.invalid/account/confirm#token_hash=hash&type=email",
      () => {},
    ).type,
    "email",
  );
});

test("bearer, query secrets, malformed, duplicate and mismatched callback data fail closed", () => {
  for (const suffix of [
    "#access_token=secret&refresh_token=secret",
    "?token_hash=secret&type=recovery",
    "#token_hash=a&token_hash=b&type=recovery",
    "#token_hash=a&type=email",
    "#code=secret",
    "#error_description=secret",
    "",
  ]) {
    let clean;
    assert.equal(
      consumeAuthCallback(
        `https://app.invalid/account/recovery${suffix}`,
        (path) => {
          clean = path;
        },
      ).kind,
      "invalid",
    );
    assert.equal(clean, "/account/recovery");
  }
  let clean;
  assert.equal(
    consumeAuthCallback(
      "https://app.invalid/discover#access_token=secret",
      (path) => {
        clean = path;
      },
    ).kind,
    "invalid",
  );
  assert.equal(clean, "/account");
});

test("production config requires a public key and a versioned notice, with safe origins", () => {
  assert.equal(authConfig({}, "http://localhost:5173", false), null);
  assert.throws(() => authConfig({}, "https://app.invalid", true));
  assert.equal(
    authConfig(values, "https://app.invalid", true).noticeVersion,
    "2026-10-01",
  );
  for (const override of [
    { VITE_SUPABASE_PUBLISHABLE_KEY: "sb_secret_synthetic" },
    { VITE_SUPABASE_URL: "http://evil.invalid" },
    { VITE_PROCESSING_NOTICE_TEXT: "" },
    { VITE_SUPABASE_URL: "https://user:secret@evil.invalid" },
  ]) {
    assert.throws(() =>
      authConfig({ ...values, ...override }, "https://app.invalid", true),
    );
  }
});

test("consent is granted only for an active account with the confirmed current version", () => {
  const decoded = decodeAccount(account);
  assert.equal(processingAllowed(decoded, "2026-10-01", false), false);
  const consented = decodeAccount({
    ...account,
    consent: { version: "2026-10-01", accepted_at: "2026-10-01T00:00:00Z" },
  });
  assert.equal(processingAllowed(consented, "2026-10-01", false), true);
  assert.equal(processingAllowed(consented, "new-notice", false), false);
  assert.equal(processingAllowed(consented, "2026-10-01", true), false);
  for (const override of [
    { owner_id: "foreign" },
    { status: "DELETING" },
    { created_at: "2026-10-01T00:00:00" },
    { timezone: "Wrong/Zone" },
    { consent: { version: "x", accepted_at: "ambiguous" } },
  ]) {
    assert.throws(() => decodeAccount({ ...account, ...override }));
  }
});

test("the real SDK adapter uses synthetic HTTP, no persisted sessions and safe failure messages", async () => {
  const providerBundle = await build({
    configFile: false,
    logLevel: "silent",
    build: {
      write: false,
      minify: false,
      lib: {
        entry: fileURLToPath(
          new URL("./auth-provider-fixture.ts", import.meta.url),
        ),
        formats: ["es"],
      },
    },
  });
  const { createAuthProvider } = await import(
    `data:text/javascript;base64,${Buffer.from((Array.isArray(providerBundle) ? providerBundle[0] : providerBundle).output.find((item) => item.type === "chunk").code).toString("base64")}`
  );
  const previousFetch = globalThis.fetch;
  const previousStorage = Object.getOwnPropertyDescriptor(
    globalThis,
    "localStorage",
  );
  const calls = [];
  Object.defineProperty(globalThis, "localStorage", {
    configurable: true,
    get() {
      throw new Error("Browser storage was accessed");
    },
  });
  globalThis.fetch = async (url, options) => {
    calls.push({ url: String(url), body: options.body });
    return new Response(
      JSON.stringify({
        message: "secret-provider-url-token",
        code: "invalid_credentials",
      }),
      {
        status: 400,
        headers: { "Content-Type": "application/json" },
      },
    );
  };
  const provider = createAuthProvider(
    authConfig(values, "https://app.invalid", true),
  );
  try {
    await provider.start({ kind: "none" });
    await assert.rejects(
      provider.login("synthetic@example.invalid", "synthetic-password"),
      (error) => !error.message.includes("secret-provider"),
    );
    assert.equal(provider.sessions.token(), null);
    assert.ok(
      calls[0].url.startsWith(
        "https://synthetic.supabase.invalid/auth/v1/token",
      ),
    );
  } finally {
    provider.dispose();
    globalThis.fetch = previousFetch;
    if (previousStorage)
      Object.defineProperty(globalThis, "localStorage", previousStorage);
    else delete globalThis.localStorage;
  }
});
