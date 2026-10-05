import { createClient, type Session } from "@supabase/supabase-js";
import type { AuthCallback } from "./callback";
import type { AuthConfig } from "./config";
import { MemorySession } from "./session";

export class AuthFailure extends Error {
  constructor() {
    super(
      "The account service could not complete this step. Check your details or request a new email and try again.",
    );
  }
}

export interface AuthProvider {
  sessions: MemorySession;
  start(callback: AuthCallback): Promise<void>;
  login(email: string, password: string): Promise<void>;
  signup(email: string, password: string): Promise<boolean>;
  reset(email: string): Promise<void>;
  updatePassword(password: string): Promise<void>;
  logout(): Promise<void>;
  dispose(): void;
}

export function createAuthProvider(config: AuthConfig): AuthProvider {
  const memory = new Map<string, string>();
  const sessions = new MemorySession();
  const client = createClient(config.supabaseUrl, config.publishableKey, {
    auth: {
      persistSession: false,
      autoRefreshToken: true,
      detectSessionInUrl: false,
      flowType: "pkce",
      storage: {
        getItem: (key) => memory.get(key) ?? null,
        setItem: (key, value) => {
          memory.set(key, value);
        },
        removeItem: (key) => {
          memory.delete(key);
        },
      },
    },
  });
  let recovery = false;
  let blocked = false;
  let startPromise: Promise<void> | null = null;
  function accept(session: Session | null): void {
    if (blocked) return;
    sessions.replace(
      session && session.expires_at
        ? {
            accessToken: session.access_token,
            expiresAt: session.expires_at,
            subject: session.user.id,
            recovery,
          }
        : null,
    );
  }
  // The synchronous SDK notification must never await another SDK operation.
  const subscription = client.auth.onAuthStateChange((event, session) => {
    if (event === "PASSWORD_RECOVERY") recovery = true;
    if (event === "SIGNED_OUT") recovery = false;
    accept(session);
  }).data.subscription;
  const unsubscribeExpiry = sessions.subscribe(() => {
    if (sessions.snapshot().expired) {
      blocked = true;
      client.auth.stopAutoRefresh();
    }
  });
  return {
    sessions,
    start(callback) {
      startPromise ??= (async () => {
        if (callback.kind === "invalid") throw new AuthFailure();
        if (callback.kind !== "verify") return;
        recovery = callback.type === "recovery";
        blocked = false;
        const { data, error } = await client.auth.verifyOtp({
          token_hash: callback.tokenHash,
          type: callback.type,
        });
        if (error || !data.session) {
          recovery = false;
          throw new AuthFailure();
        }
        accept(data.session);
      })();
      return startPromise;
    },
    async login(email, password) {
      recovery = false;
      const { data, error } = await client.auth.signInWithPassword({
        email,
        password,
      });
      if (error || !data.session) throw new AuthFailure();
      blocked = false;
      accept(data.session);
      client.auth.startAutoRefresh();
    },
    async signup(email, password) {
      recovery = false;
      const { data, error } = await client.auth.signUp({
        email,
        password,
        options: { emailRedirectTo: `${config.origin}/account/confirm` },
      });
      if (error) throw new AuthFailure();
      blocked = false;
      accept(data.session);
      if (data.session) client.auth.startAutoRefresh();
      return data.session !== null;
    },
    async reset(email) {
      const { error } = await client.auth.resetPasswordForEmail(email, {
        redirectTo: `${config.origin}/account/recovery`,
      });
      if (error) throw new AuthFailure();
    },
    async updatePassword(password) {
      if (!sessions.snapshot().recovery || !sessions.snapshot().subject)
        throw new AuthFailure();
      const { error } = await client.auth.updateUser({ password });
      if (error) throw new AuthFailure();
      // Password recovery ends with explicit login, including after a reload.
      await this.logout();
    },
    async logout() {
      blocked = true;
      recovery = false;
      sessions.replace(null);
      client.auth.stopAutoRefresh();
      const { error } = await client.auth.signOut({ scope: "local" });
      memory.clear();
      if (error) throw new AuthFailure();
    },
    dispose() {
      blocked = true;
      subscription.unsubscribe();
      unsubscribeExpiry();
      client.auth.stopAutoRefresh();
      sessions.replace(null);
      memory.clear();
    },
  };
}
