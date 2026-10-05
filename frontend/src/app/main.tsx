/// <reference types="vite/client" />
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { createApiClient } from "../lib/api";
import { authConfig } from "../features/auth/config";
import { consumeAuthCallback } from "../features/auth/callback";
import { createAuthProvider } from "../features/auth/provider";
import { decodeAccount } from "../features/auth/account";
import type { AuthRuntime } from "../features/auth/AuthContext";

const callback = consumeAuthCallback(window.location.href, (path) => {
  window.history.replaceState(null, "", path);
});
const config = authConfig(
  import.meta.env,
  window.location.origin,
  import.meta.env.PROD,
);
const provider = config ? createAuthProvider(config) : null;

const root = document.getElementById("root");
if (!root) throw new Error("The app root is missing.");

const api = createApiClient({
  origin: window.location.origin,
  environment: import.meta.env.PROD ? "production" : "development",
  getAccessToken: () => provider?.sessions.token() ?? null,
  onUnauthorized: () => provider?.sessions.replace(null, true),
});
const auth: AuthRuntime | null =
  provider && config
    ? {
        provider,
        config,
        api,
        callback,
        acceptConsent: (patch) => api.patch("/api/v1/me", patch, decodeAccount),
      }
    : null;
if (import.meta.hot) import.meta.hot.dispose(() => provider?.dispose());
createRoot(root).render(
  <StrictMode>
    <App api={api} auth={auth} />
  </StrictMode>,
);
