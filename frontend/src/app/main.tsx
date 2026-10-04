/// <reference types="vite/client" />
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { createApiClient } from "../lib/api";

const root = document.getElementById("root");
if (!root) throw new Error("The app root is missing.");

// Same-origin API by default. Authentication supplies an in-memory token later.
// The production entry never imports a mock transport or synthetic account data.
const api = createApiClient({
  origin: window.location.origin,
  environment: import.meta.env.PROD ? "production" : "development",
});
createRoot(root).render(
  <StrictMode>
    <App api={api} />
  </StrictMode>,
);
