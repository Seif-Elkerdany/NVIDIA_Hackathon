export type AuthCallback =
  | { kind: "none" }
  | { kind: "invalid" }
  | { kind: "verify"; tokenHash: string; type: "recovery" | "email" };

// Only one-time email hashes are accepted. Implicit bearer and PKCE redirects
// cannot safely restore a session after reload under the P0 memory-only policy.
export function consumeAuthCallback(
  href: string,
  replace: (path: string) => void,
): AuthCallback {
  const url = new URL(href);
  const callback =
    url.pathname === "/account/recovery" || url.pathname === "/account/confirm";
  if (!callback && !url.hash && !url.search) return { kind: "none" };
  const fragment = new URLSearchParams(url.hash.slice(1));
  const sensitive = [
    "access_token",
    "refresh_token",
    "token_hash",
    "code",
    "error",
    "error_description",
  ];
  const hasAuth = sensitive.some(
    (key) => fragment.has(key) || url.searchParams.has(key),
  );
  if (!callback && !hasAuth) return { kind: "none" };
  // Remove secrets before routing, provider requests or rendering; discard
  // history.state too, since browser navigation may preserve callback URLs.
  replace(callback ? url.pathname : "/account");
  const tokenHash = fragment.get("token_hash");
  const type = fragment.get("type");
  if (
    url.search ||
    fragment.size !== 2 ||
    fragment.getAll("token_hash").length !== 1 ||
    !tokenHash ||
    !/^[A-Za-z0-9_-]{1,512}$/.test(tokenHash) ||
    type !== (url.pathname === "/account/recovery" ? "recovery" : "email")
  ) {
    return { kind: "invalid" };
  }
  return { kind: "verify", tokenHash, type: type as "recovery" | "email" };
}
