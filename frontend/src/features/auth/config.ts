export interface AuthConfig {
  supabaseUrl: string;
  publishableKey: string;
  origin: string;
  noticeVersion: string;
  noticeText: string;
}

export function authConfig(
  values: Record<string, unknown>,
  origin: string,
  production: boolean,
): AuthConfig | null {
  const names = [
    "VITE_SUPABASE_URL",
    "VITE_SUPABASE_PUBLISHABLE_KEY",
    "VITE_PROCESSING_NOTICE_VERSION",
    "VITE_PROCESSING_NOTICE_TEXT",
  ] as const;
  const configured = names.some(
    (key) => values[key] !== undefined && values[key] !== "",
  );
  if (!configured && !production) return null;
  if (
    names.some(
      (key) =>
        typeof values[key] !== "string" || !(values[key] as string).trim(),
    )
  ) {
    throw new Error(
      "Auth requires a provider URL, public key and versioned processing notice.",
    );
  }
  const provider = new URL(values.VITE_SUPABASE_URL as string);
  const app = new URL(origin);
  for (const url of [provider, app]) {
    const local = ["localhost", "127.0.0.1", "[::1]"].includes(url.hostname);
    if (
      (url.protocol !== "https:" &&
        !(local && !production && url.protocol === "http:")) ||
      url.username ||
      url.password ||
      url.search ||
      url.hash ||
      url.pathname !== "/"
    ) {
      throw new Error(
        "Auth origins must use HTTPS without paths or credentials.",
      );
    }
  }
  // Accept publishable keys only; never bundle admin/service-role credentials.
  const key = values.VITE_SUPABASE_PUBLISHABLE_KEY as string;
  if (!/^sb_publishable_[A-Za-z0-9_-]+$/.test(key)) {
    throw new Error("Browser auth requires a Supabase publishable key.");
  }
  const version = values.VITE_PROCESSING_NOTICE_VERSION as string;
  const text = values.VITE_PROCESSING_NOTICE_TEXT as string;
  if (
    version !== version.trim() ||
    version.length > 100 ||
    text.length > 20_000
  ) {
    throw new Error("Invalid processing notice configuration.");
  }
  return {
    supabaseUrl: provider.origin,
    publishableKey: key,
    origin: app.origin,
    noticeVersion: version,
    noticeText: text,
  };
}
