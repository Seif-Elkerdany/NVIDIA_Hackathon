import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type ReactNode,
} from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "../../lib/api";
import { ErrorView, StateView } from "../../components/StateView";
import { useAccount, useAuth, useProcessingAccess } from "./AuthContext";
import { AuthFailure } from "./provider";
import "./auth.css";

function Heading({ title, children }: { title: string; children: ReactNode }) {
  return (
    <header className="page-heading">
      <p className="eyebrow">Your account</p>
      <h1 tabIndex={-1}>{title}</h1>
      <p className="page-intro">{children}</p>
    </header>
  );
}

function Unavailable() {
  return (
    <>
      <Heading title="Connect your account">
        Sign-in needs a configured account service.
      </Heading>
      <StateView state="unavailable" title="Account service unavailable">
        <p>Try again when the service is available.</p>
      </StateView>
    </>
  );
}

function AccountStatus() {
  const { runtime } = useAuth();
  const account = useAccount();
  const [error, setError] = useState(false);
  return (
    <>
      <Heading title="Your private account">
        You are signed in for this browser session.
      </Heading>
      {account.isPending ? (
        <StateView state="loading" title="Loading your account">
          <p>Please wait.</p>
        </StateView>
      ) : account.error instanceof ApiError ? (
        <ErrorView
          error={account.error}
          onRetry={() => void account.refetch()}
        />
      ) : account.data ? (
        <section className="panel">
          <h2>Welcome, {account.data.display_name}</h2>
          <Link className="button" to="/consent">
            Review processing consent
          </Link>
        </section>
      ) : (
        <p role="alert">Your account could not be loaded.</p>
      )}
      <p>Reloading this page ends your session. Sign in again to continue.</p>
      {error && (
        <p role="alert">
          You are signed out here, but the service could not confirm sign-out.
        </p>
      )}
      <button
        className="button button--secondary"
        onClick={() => {
          void runtime?.provider.logout().catch(() => setError(true));
        }}
      >
        Sign out
      </button>
    </>
  );
}

export function AccountScreen() {
  const { runtime, state, ready, callbackFailed } = useAuth();
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const recoveryRoute = pathname === "/account/recovery";
  const [mode, setMode] = useState<"login" | "signup" | "reset">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const feedback = useRef<HTMLParagraphElement>(null);
  useEffect(() => {
    if (error || message) feedback.current?.focus();
  }, [error, message]);
  if (!runtime) return <Unavailable />;
  if (!ready)
    return (
      <StateView state="loading" title="Checking your email link">
        <p>Please wait.</p>
      </StateView>
    );
  if (state.recovery && !recoveryRoute)
    return <Navigate to="/account/recovery" replace />;
  if (state.subject && !state.recovery) return <AccountStatus />;
  const recovering = recoveryRoute && state.recovery && !!state.subject;
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!runtime || busy) return;
    setBusy(true);
    setError("");
    setMessage("");
    const submittedPassword = password;
    setPassword("");
    try {
      if (recovering) {
        await runtime.provider.updatePassword(submittedPassword);
        setMessage(
          "Your password was changed. Sign in with your new password.",
        );
        navigate("/account", { replace: true });
      } else if (mode === "reset") {
        await runtime.provider.reset(email);
        setMessage(
          "If an account can receive recovery email, a message has been sent. Check your inbox.",
        );
      } else if (mode === "signup") {
        const signedIn = await runtime.provider.signup(
          email,
          submittedPassword,
        );
        if (!signedIn)
          setMessage(
            "Check your inbox to confirm your email, then return to sign in.",
          );
      } else await runtime.provider.login(email, submittedPassword);
    } catch (failure: unknown) {
      // Provider exceptions may contain secrets or URLs; use only safe copy.
      setError(
        failure instanceof AuthFailure
          ? failure.message
          : "The account service is unavailable. Please try again.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <Heading
        title={
          recovering
            ? "Choose a new password"
            : mode === "signup"
              ? "Create your private account"
              : mode === "reset"
                ? "Reset your password"
                : "Sign in to BenefitBridge"
        }
      >
        Your session stays in this open page. After a reload, sign in again.
      </Heading>
      {state.expired && (
        <p role="status">Your session ended. Sign in again to continue.</p>
      )}
      {(callbackFailed || (recoveryRoute && !recovering)) && (
        <p role="alert">
          This email link is unavailable or has expired. Request a new email to
          continue.
        </p>
      )}
      <form className="panel auth-form" onSubmit={submit} aria-busy={busy}>
        {!recovering && (
          <label>
            Email
            <input
              type="email"
              name="email"
              autoComplete="email"
              required
              maxLength={254}
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              disabled={busy}
            />
          </label>
        )}
        {(recovering || mode !== "reset") && (
          <label>
            {recovering ? "New password" : "Password"}
            <input
              type="password"
              name="password"
              autoComplete={
                recovering || mode === "signup"
                  ? "new-password"
                  : "current-password"
              }
              required
              minLength={recovering || mode === "signup" ? 8 : 1}
              maxLength={128}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              disabled={busy}
            />
          </label>
        )}
        <button className="button" disabled={busy}>
          {busy
            ? "Please wait…"
            : recovering
              ? "Save new password"
              : mode === "signup"
                ? "Create account"
                : mode === "reset"
                  ? "Send recovery email"
                  : "Sign in"}
        </button>
        {(error || message) && (
          <p ref={feedback} tabIndex={-1} role={error ? "alert" : "status"}>
            {error || message}
          </p>
        )}
      </form>
      {!recovering && (
        <div className="auth-actions">
          {(["login", "signup", "reset"] as const)
            .filter((option) => option !== mode)
            .map((option) => (
              <button
                className="button button--secondary"
                key={option}
                disabled={busy}
                onClick={() => {
                  setMode(option);
                  setPassword("");
                  setError("");
                  setMessage("");
                }}
              >
                {option === "login"
                  ? "Sign in"
                  : option === "signup"
                    ? "Create account"
                    : "Forgot password?"}
              </button>
            ))}
        </div>
      )}
      <p>
        Next: review consent, add your profile and goal, then explore
        opportunities. Documents are optional.
      </p>
    </>
  );
}

export function ConsentScreen() {
  const auth = useAuth();
  const account = useAccount();
  const queryClient = useQueryClient();
  const [checked, setChecked] = useState(false);
  const mutation = useMutation({
    mutationFn: async () => {
      if (!auth.runtime || !checked || !auth.state.subject)
        throw new AuthFailure();
      return auth.runtime.acceptConsent({
        consent_version: auth.runtime.config.noticeVersion,
      });
    },
    onSuccess(data) {
      queryClient.setQueryData(["auth-account", auth.state.generation], data);
      auth.accepted();
    },
  });
  if (!auth.runtime) return <Unavailable />;
  if (!auth.state.subject || auth.state.recovery)
    return <Navigate to="/account" replace />;
  const accepted =
    account.data?.consent?.version === auth.runtime.config.noticeVersion &&
    !auth.declined;
  return (
    <>
      <Heading title="Choose how your information is used">
        Read the processing notice before continuing.
      </Heading>
      <section className="panel">
        <h2>Processing notice</h2>
        <p>Version {auth.runtime.config.noticeVersion}</p>
        <p className="auth-notice">{auth.runtime.config.noticeText}</p>
        <p>
          You can decline and stay signed in. Document and inference processing
          remain blocked until you accept the current notice.
        </p>
        <p>
          Documents are optional. You can build your profile and goal without
          uploading a document.
        </p>
        {account.isPending ? (
          <p role="status">Checking your recorded consent…</p>
        ) : account.error instanceof ApiError ? (
          <ErrorView
            error={account.error}
            onRetry={() => void account.refetch()}
          />
        ) : accepted ? (
          <>
            <p role="status">
              Consent recorded at {account.data?.consent?.accepted_at}.
            </p>
            <Link className="button" to="/profile">
              Continue to your profile and goal
            </Link>
          </>
        ) : (
          <>
            <label className="auth-check">
              <input
                type="checkbox"
                checked={checked}
                onChange={(event) => setChecked(event.target.checked)}
                disabled={mutation.isPending}
              />
              I have read and accept this processing notice.
            </label>
            <div className="auth-actions">
              <button
                className="button"
                disabled={!checked || !account.data || mutation.isPending}
                onClick={() => mutation.mutate()}
              >
                {mutation.isPending
                  ? "Recording consent…"
                  : "Accept and continue"}
              </button>
              <button
                className="button button--secondary"
                disabled={mutation.isPending}
                onClick={() => {
                  auth.decline();
                  setChecked(false);
                  mutation.reset();
                }}
              >
                Decline
              </button>
            </div>
          </>
        )}
        {auth.declined && (
          <p role="status">
            You declined. Processing is blocked. You can review this notice
            again whenever you choose.
          </p>
        )}
        {mutation.error instanceof ApiError ? (
          <ErrorView error={mutation.error} />
        ) : mutation.isError ? (
          <p role="alert">Consent could not be recorded. Try again.</p>
        ) : null}
      </section>
      <Link to="/account">Back to your account</Link>
    </>
  );
}

export function ProcessingGuard({ children }: { children: ReactNode }) {
  const access = useProcessingAccess();
  if (!access.ready)
    return (
      <StateView state="loading" title="Checking your account">
        <p>Please wait.</p>
      </StateView>
    );
  if (!access.state.subject || access.state.recovery)
    return <Navigate to="/account" replace />;
  if (access.account.isPending)
    return (
      <StateView state="loading" title="Checking consent">
        <p>Please wait.</p>
      </StateView>
    );
  if (access.account.error instanceof ApiError)
    return (
      <ErrorView
        error={access.account.error}
        onRetry={() => void access.account.refetch()}
      />
    );
  if (!access.allowed) return <Navigate to="/consent" replace />;
  return children;
}
