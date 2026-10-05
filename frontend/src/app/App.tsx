import { createContext, useContext, useEffect, useRef, useState } from "react";
import {
  BrowserRouter,
  Link,
  NavLink,
  Route,
  Routes,
  useLocation,
} from "react-router";
import {
  QueryClient,
  QueryClientProvider,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { ApiError, decodeCapabilities, type ApiClient } from "../lib/api";
import { ErrorView, StateView } from "../components/StateView";
import { StatusLabel } from "../components/StatusLabel";
import { AuthBoundary, type AuthRuntime } from "../features/auth/AuthContext";
import {
  AccountScreen,
  ConsentScreen,
  ProcessingGuard,
} from "../features/auth/Screens";
import "../styles/shell.css";

const ApiContext = createContext<ApiClient | null>(null);
const navigation = [
  ["/", "Overview"],
  ["/profile", "Profile"],
  ["/documents", "Documents"],
  ["/discover", "Discover"],
  ["/saved", "Saved"],
  ["/applications", "Applications"],
  ["/settings", "Settings"],
] as const;

function useCapabilities() {
  const api = useContext(ApiContext);
  if (!api) throw new Error("The shell requires an API client.");
  return useQuery({
    queryKey: ["capabilities"],
    queryFn: ({ signal }) =>
      api.get("/api/v1/capabilities", decodeCapabilities, signal),
    retry: false,
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });
}

function RouteFocus() {
  const { pathname } = useLocation();
  const previous = useRef(pathname);
  useEffect(() => {
    const heading = document.querySelector<HTMLHeadingElement>("main h1");
    document.title = `${heading?.textContent ?? "BenefitBridge"} · BenefitBridge`;
    if (previous.current !== pathname) {
      heading?.focus();
      window.scrollTo(0, 0);
    }
    previous.current = pathname;
  }, [pathname]);
  return null;
}

function Connection() {
  const result = useCapabilities();
  return (
    <p className="connection" role="status">
      <span
        className={`connection-dot ${result.isError ? "connection-dot--error" : ""}`}
        aria-hidden="true"
      />
      {result.isFetching
        ? "Checking service"
        : result.isError
          ? "Service unavailable"
          : result.data
            ? "Connected to service"
            : "Service not checked"}
    </p>
  );
}

function Settings() {
  const result = useCapabilities();
  const queryClient = useQueryClient();
  const [cancelled, setCancelled] = useState(false);
  function retry() {
    setCancelled(false);
    void result.refetch();
  }
  return (
    <>
      <PageHeading eyebrow="Settings" title="Your service connection">
        Check what the connected service currently supports.
      </PageHeading>
      {result.isFetching ? (
        <StateView
          state="loading"
          title="Checking available features"
          action={
            <button
              className="button button--secondary"
              onClick={() => {
                setCancelled(true);
                void queryClient.cancelQueries({ queryKey: ["capabilities"] });
              }}
            >
              Stop this request
            </button>
          }
        >
          <p>
            Stopping this browser request does not cancel work already accepted
            by the service.
          </p>
        </StateView>
      ) : cancelled ? (
        <StateView
          state="cancelled"
          title="The browser request was stopped"
          action={
            <button className="button" onClick={retry}>
              Check again
            </button>
          }
        >
          <p>Previously accepted work continues on the service.</p>
        </StateView>
      ) : result.isError ? (
        <>
          <ErrorView
            error={
              result.error instanceof ApiError
                ? result.error
                : new ApiError(
                    "invalid-response",
                    "The service could not complete this request.",
                    "unavailable",
                  )
            }
            onRetry={retry}
          />
          {result.error instanceof ApiError && result.error.status === 401 && (
            <Link className="text-link" to="/account">
              Go to account
            </Link>
          )}
          {result.error instanceof ApiError &&
            result.error.problem?.code === "CONSENT_REQUIRED" && (
              <Link className="text-link" to="/consent">
                Review consent
              </Link>
            )}
        </>
      ) : result.data ? (
        <section className="panel">
          <h2>Available features</h2>
          <dl className="feature-list">
            <div>
              <dt>API version</dt>
              <dd>{result.data.api_version}</dd>
            </div>
            <div>
              <dt>Inference</dt>
              <dd>
                {result.data.inference_available ? "Available" : "Unavailable"}
              </dd>
            </div>
            <div>
              <dt>Deep checks</dt>
              <dd>
                {result.data.deep_available ? "Available" : "Unavailable"}
              </dd>
            </div>
            <div>
              <dt>Watching</dt>
              <dd>{result.data.watch ? "Available" : "Unavailable"}</dd>
            </div>
            <div>
              <dt>Document size limit</dt>
              <dd>
                {result.data.max_document_bytes.toLocaleString("en-US")} bytes
              </dd>
            </div>
            <div>
              <dt>Document page limit</dt>
              <dd>{result.data.max_document_pages}</dd>
            </div>
          </dl>
          <button className="button button--secondary" onClick={retry}>
            Check again
          </button>
        </section>
      ) : (
        <StateView
          state="unknown"
          title="Service capabilities have not been checked"
          action={
            <button className="button" onClick={retry}>
              Check connection
            </button>
          }
        >
          <p>Availability remains unknown until the service responds.</p>
        </StateView>
      )}
    </>
  );
}

function PageHeading({
  eyebrow,
  title,
  children,
}: {
  eyebrow: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <header className="page-heading">
      <p className="eyebrow">{eyebrow}</p>
      <h1 tabIndex={-1}>{title}</h1>
      <p className="page-intro">{children}</p>
    </header>
  );
}

function Overview() {
  return (
    <>
      <PageHeading
        eyebrow="Your workspace"
        title="Build a clearer path to opportunity"
      >
        Bring your goals and evidence together before deciding what to pursue.
      </PageHeading>
      <section className="panel">
        <div className="section-heading">
          <h2>Start with your profile</h2>
          <span className="small-label">Documents optional</span>
        </div>
        <p className="muted">
          You can start discovery without uploading documents. Add evidence when
          it helps clarify a requirement.
        </p>
        <ol className="setup-list">
          <li>
            <Link to="/account">Connect your account</Link>
            <span>Use your account to keep your workspace private.</span>
          </li>
          <li>
            <Link to="/consent">Review processing consent</Link>
            <span>Understand how your profile and evidence are used.</span>
          </li>
          <li>
            <Link to="/profile">Add your profile and goal</Link>
            <span>Describe your background and what you want to pursue.</span>
          </li>
          <li>
            <Link to="/documents">Add documents, if useful</Link>
            <span>Optional evidence can resolve missing information.</span>
          </li>
          <li>
            <Link to="/discover">Explore opportunities</Link>
            <span>Review published requirements alongside your evidence.</span>
          </li>
        </ol>
      </section>
      <section className="panel">
        <h2>Read each result separately</h2>
        <p className="muted">
          Eligibility, current availability, fit and application readiness
          answer different questions. A fit score does not confirm eligibility.
        </p>
        <div className="status-explainer">
          <StatusLabel status="UNKNOWN" />
          <p>Missing evidence means a requirement needs clarification.</p>
        </div>
        <div className="status-explainer">
          <StatusLabel status="STALE" />
          <p>Changed inputs mean an earlier result needs a fresh check.</p>
        </div>
      </section>
    </>
  );
}

const shells = {
  profile: [
    "Profile",
    "Your background and goal",
    "No profile has been loaded. Connect your account before adding or changing your background and goal.",
  ],
  documents: [
    "Documents",
    "Evidence when you need it",
    "No documents have been loaded. Documents are optional; you can start with your profile and goal.",
  ],
  discover: [
    "Discover",
    "Find your next opportunity",
    "No discovery results have been loaded. Set your goal before starting a search.",
  ],
  saved: [
    "Saved",
    "Keep opportunities in view",
    "No saved opportunities have been loaded. Discovery is where you can review and save opportunities.",
  ],
  applications: [
    "Applications",
    "Prepare your next step",
    "No applications have been loaded. Review an opportunity before preparing an application.",
  ],
} as const;

function RouteShell({ page }: { page: keyof typeof shells }) {
  const [eyebrow, title, description] = shells[page];
  return (
    <>
      <PageHeading eyebrow={eyebrow} title={title}>
        {description}
      </PageHeading>
      <StateView
        state="empty"
        title="Nothing loaded yet"
        action={
          <Link
            className="button button--secondary"
            to={
              page === "saved" || page === "applications"
                ? "/discover"
                : "/settings"
            }
          >
            {page === "saved" || page === "applications"
              ? "Go to discovery"
              : "Check service connection"}
          </Link>
        }
      >
        <p>
          This view will show your account data when its service is available.
        </p>
      </StateView>
    </>
  );
}

export function ShellRoutes() {
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <aside className="sidebar">
        <Link className="brand" to="/" aria-label="BenefitBridge overview">
          <span className="brand-mark" aria-hidden="true">
            B
          </span>
          BenefitBridge
        </Link>
        <p className="sidebar-caption">Your opportunity workspace</p>
        <nav aria-label="Main navigation">
          {navigation.map(([path, title]) => (
            <NavLink key={path} end={path === "/"} to={path}>
              {title}
            </NavLink>
          ))}
        </nav>
        <p className="sidebar-note">
          Evidence first.
          <br />
          Decisions stay yours.
        </p>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <span>Workspace</span>
          <Connection />
        </header>
        <main id="main-content" tabIndex={-1}>
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/account" element={<AccountScreen />} />
            <Route path="/account/confirm" element={<AccountScreen />} />
            <Route path="/account/recovery" element={<AccountScreen />} />
            <Route path="/consent" element={<ConsentScreen />} />
            {Object.keys(shells).map((page) => (
              <Route
                key={page}
                path={`/${page}`}
                element={
                  <ProcessingGuard>
                    <RouteShell page={page as keyof typeof shells} />
                  </ProcessingGuard>
                }
              />
            ))}
            <Route path="/settings" element={<Settings />} />
            <Route
              path="*"
              element={
                <>
                  <PageHeading
                    eyebrow="Page unavailable"
                    title="We couldn’t find this page"
                  >
                    The link may be incomplete or the page may have moved.
                  </PageHeading>
                  <Link className="button" to="/">
                    Return to overview
                  </Link>
                </>
              }
            />
          </Routes>
        </main>
        <footer className="footer">
          Published requirements and your evidence guide the next step.
        </footer>
      </div>
      <RouteFocus />
    </div>
  );
}

export function App({
  api,
  auth = null,
}: {
  api: ApiClient;
  auth?: AuthRuntime | null;
}) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { retry: false },
          mutations: { retry: false },
        },
      }),
  );
  return (
    <ApiContext.Provider value={api}>
      <QueryClientProvider client={queryClient}>
        <AuthBoundary runtime={auth}>
          <BrowserRouter>
            <ShellRoutes />
          </BrowserRouter>
        </AuthBoundary>
      </QueryClientProvider>
    </ApiContext.Provider>
  );
}
