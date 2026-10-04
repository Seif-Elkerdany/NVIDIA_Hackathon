import {
  createContext,
  useContext,
  useEffect,
  useState,
  useSyncExternalStore,
  type ReactNode,
} from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import type { ApiClient } from "../../lib/api";
import { ApiError } from "../../lib/api";
import {
  decodeAccount,
  processingAllowed,
  type Account,
  type ConsentPatch,
} from "./account";
import type { AuthCallback } from "./callback";
import type { AuthConfig } from "./config";
import type { AuthProvider } from "./provider";
import type { SessionState } from "./session";

export interface AuthRuntime {
  provider: AuthProvider;
  config: AuthConfig;
  api: ApiClient;
  acceptConsent(patch: ConsentPatch): Promise<Account>;
  callback: AuthCallback;
}

const unavailable: SessionState = {
  subject: null,
  recovery: false,
  expired: false,
  generation: 0,
};
const AuthContext = createContext<{
  runtime: AuthRuntime | null;
  state: SessionState;
  ready: boolean;
  callbackFailed: boolean;
  declined: boolean;
  decline(): void;
  accepted(): void;
} | null>(null);

export function AuthBoundary({
  runtime,
  children,
}: {
  runtime: AuthRuntime | null;
  children: ReactNode;
}) {
  const queryClient = useQueryClient();
  const state = useSyncExternalStore(
    runtime?.provider.sessions.subscribe ?? (() => () => {}),
    runtime?.provider.sessions.snapshot ?? (() => unavailable),
  );
  const [ready, setReady] = useState(!runtime);
  const [callbackFailed, setCallbackFailed] = useState(false);
  const [declinedGeneration, setDeclinedGeneration] = useState<number | null>(
    null,
  );
  useEffect(() => {
    let active = true;
    if (runtime)
      void runtime.provider.start(runtime.callback).then(
        () => {
          if (active) setReady(true);
        },
        () => {
          if (active) {
            setCallbackFailed(true);
            setReady(true);
          }
        },
      );
    return () => {
      active = false;
    };
  }, [runtime]);
  useEffect(() => {
    // Aborted responses from an old identity cannot repopulate private caches.
    const old = {
      predicate: (query: { queryKey: readonly unknown[] }) =>
        query.queryKey[0] !== "capabilities" &&
        !(
          query.queryKey[0] === "auth-account" &&
          query.queryKey[1] === state.generation
        ),
    };
    void queryClient.cancelQueries(old);
    queryClient.removeQueries(old);
  }, [queryClient, state.generation]);
  return (
    <AuthContext.Provider
      value={{
        runtime,
        state,
        ready,
        callbackFailed,
        declined: declinedGeneration === state.generation,
        decline: () => setDeclinedGeneration(state.generation),
        accepted: () => setDeclinedGeneration(null),
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("Auth routes require AuthBoundary.");
  return context;
}

export function useAccount() {
  const { runtime, state, ready } = useAuth();
  return useQuery({
    queryKey: ["auth-account", state.generation],
    enabled: !!runtime && ready && !!state.subject && !state.recovery,
    queryFn: async ({ signal }) => {
      if (!runtime) throw new Error("Auth is not configured.");
      try {
        return await runtime.api.get("/api/v1/me", decodeAccount, signal);
      } catch (error: unknown) {
        if (error instanceof ApiError && error.status === 401)
          runtime.provider.sessions.replace(null, true);
        throw error;
      }
    },
    retry: false,
    staleTime: 0,
    refetchOnWindowFocus: true,
  });
}

export function useProcessingAccess() {
  const auth = useAuth();
  const account = useAccount();
  return {
    ...auth,
    account,
    allowed:
      !!auth.state.subject &&
      !auth.state.recovery &&
      processingAllowed(
        account.data,
        auth.runtime?.config.noticeVersion ?? "",
        auth.declined,
      ) &&
      !account.isError,
  };
}
