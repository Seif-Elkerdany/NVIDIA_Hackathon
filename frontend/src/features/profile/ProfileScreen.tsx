import { useEffect, useRef, useState } from "react";
import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { Link } from "react-router";
import { ApiError } from "../../lib/api";
import { ErrorView, StateView } from "../../components/StateView";
import {
  attributesIn,
  FieldEditor,
  FactSummary,
  groups,
  ValueText,
} from "./Fields";
import {
  buildPatch,
  fields,
  FormError,
  initialEdits,
  type Edit,
  type Patch,
  type Profile,
} from "./model";
import type { ProfileApi } from "./api";
import "./profile.css";

function errorView(error: unknown): ApiError {
  return error instanceof ApiError
    ? error
    : new ApiError(
        "invalid-response",
        "Your profile could not be loaded. Try again.",
        "unavailable",
      );
}

export function ProfileForm({
  profile,
  onSave,
  onReload,
  pending,
  error,
  reloadError,
  refreshing,
}: {
  profile: Profile;
  onSave(patch: Patch): void;
  onReload(): void;
  pending: boolean;
  error: unknown;
  reloadError?: unknown;
  refreshing: boolean;
}) {
  const [edits, setEdits] = useState(() => initialEdits(profile));
  const [validation, setValidation] = useState<FormError | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const conflict = error instanceof ApiError && error.status === 409;
  const versionConflict =
    conflict && error.problem?.code === "VERSION_CONFLICT";
  const summary = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (conflict || validation) summary.current?.focus();
  }, [conflict, validation]);
  function submit(event: React.FormEvent) {
    event.preventDefault();
    if (pending || conflict || !confirmed) return;
    try {
      setValidation(null);
      onSave(buildPatch(profile, edits));
    } catch (error: unknown) {
      if (error instanceof FormError) setValidation(error);
      else throw error;
    }
  }
  return (
    <form onSubmit={submit} className="profile-form" noValidate>
      <div className="profile-version">
        <span>Editing version {profile.version_number}</span>
        <span>
          Last saved{" "}
          <time dateTime={profile.updated_at}>
            {profile.updated_at.slice(0, 10)} (UTC)
          </time>
        </span>
      </div>
      <div ref={summary} tabIndex={-1} className="profile-feedback">
        {validation && <p role="alert">{validation.message}</p>}
        {conflict && (
          <section role="alert" className="profile-conflict">
            <h2>
              {versionConflict
                ? "Your profile changed while you were editing"
                : "This save conflicts with an earlier request"}
            </h2>
            <p>
              Your entries are still visible. Review or copy them before
              reloading. Reloading replaces this form with the current saved
              version; stale changes will not be submitted automatically.
            </p>
            <button
              className="button"
              type="button"
              disabled={refreshing}
              onClick={onReload}
            >
              {refreshing ? "Reloading…" : "Reload current profile"}
            </button>
          </section>
        )}
      </div>
      {error && !conflict ? <ErrorView error={errorView(error)} /> : null}
      {reloadError ? (
        <ErrorView error={errorView(reloadError)} onRetry={onReload} />
      ) : null}
      {groups.map((group) => (
        <section
          className="profile-section"
          key={group}
          aria-labelledby={`group-${group.replaceAll(" ", "-")}`}
        >
          <div className="profile-section-heading">
            <h2 id={`group-${group.replaceAll(" ", "-")}`}>{group}</h2>
            {group === "Location and authorization" && (
              <p>
                Residence, citizenship and permission to work are separate
                facts.
              </p>
            )}
          </div>
          <div className="profile-fields">
            {attributesIn(group).map((attribute) => (
              <FieldEditor
                key={attribute}
                edit={edits.find((edit) => edit.attribute === attribute)!}
                fact={profile.facts.find(
                  (fact) => fact.attribute === attribute,
                )}
                disabled={pending || refreshing}
                error={
                  validation?.attribute === attribute
                    ? validation.message
                    : undefined
                }
                onChange={(next: Edit) => {
                  setEdits((old) =>
                    old.map((edit) =>
                      edit.attribute === attribute ? next : edit,
                    ),
                  );
                  setValidation(null);
                  setConfirmed(false);
                }}
              />
            ))}
          </div>
        </section>
      ))}
      <div className="profile-save">
        <p>
          Edited values are saved as your confirmed self-report. Supporting
          passages from old values are not attached to replacements.
        </p>
        <label className="profile-check">
          <input
            type="checkbox"
            checked={confirmed}
            disabled={pending || conflict || refreshing}
            onChange={(e) => setConfirmed(e.target.checked)}
          />
          I confirm the changes I entered.
        </label>
        <button
          className="button"
          type="submit"
          disabled={!confirmed || pending || conflict || refreshing}
        >
          {pending ? "Saving your profile…" : "Save profile changes"}
        </button>
        <Link to="/documents">Add documents later (optional)</Link>
      </div>
    </form>
  );
}

function History({
  api,
  identity,
}: {
  api: ProfileApi;
  identity: readonly [string, number];
}) {
  const [open, setOpen] = useState(false);
  const history = useInfiniteQuery({
    queryKey: ["profile-history", ...identity],
    enabled: open,
    initialPageParam: null as string | null,
    queryFn: ({ pageParam, signal }) => api.history(pageParam, signal),
    getNextPageParam: (last) => last.next_cursor ?? undefined,
    retry: false,
    refetchOnWindowFocus: false,
  });
  return (
    <section className="profile-history" aria-label="Profile version history">
      <button
        className="button button--secondary"
        type="button"
        aria-expanded={open}
        aria-controls="profile-history-list"
        onClick={() => setOpen(!open)}
      >
        {open ? "Hide" : "View"} version history
      </button>
      {open && (
        <div id="profile-history-list">
          <p>
            Earlier versions are read-only. Deleted evidence is suppressed by
            the service.
          </p>
          {history.isPending && <p role="status">Loading version history…</p>}
          {history.isError && (
            <ErrorView
              error={errorView(history.error)}
              onRetry={() => void history.refetch()}
            />
          )}
          {history.data?.pages
            .flatMap((page) => page.items)
            .map((profile) => (
              <details
                key={profile.version_id}
                className="profile-history-version"
              >
                <summary>
                  Version {profile.version_number} ·{" "}
                  {profile.updated_at.slice(0, 10)} (UTC)
                </summary>
                {profile.facts.length === 0 ? (
                  <p>No facts in this version.</p>
                ) : (
                  <dl>
                    {profile.facts.map((fact) => (
                      <div key={fact.id}>
                        <dt>{fields[fact.attribute].label}</dt>
                        <dd>
                          <ValueText value={fact.value} />
                          <FactSummary fact={fact} />
                        </dd>
                      </div>
                    ))}
                  </dl>
                )}
              </details>
            ))}
          {history.hasNextPage && (
            <button
              type="button"
              className="button button--secondary"
              disabled={history.isFetchingNextPage}
              onClick={() => void history.fetchNextPage()}
            >
              {history.isFetchingNextPage ? "Loading…" : "Load older versions"}
            </button>
          )}
        </div>
      )}
    </section>
  );
}

export function ProfileScreen(props: {
  api: ProfileApi;
  identity: readonly [string, number];
  newCommandKey?: () => string;
}) {
  return <ProfileSession key={props.identity.join(":")} {...props} />;
}

function ProfileSession({
  api,
  identity,
  newCommandKey = () => crypto.randomUUID(),
}: {
  api: ProfileApi;
  identity: readonly [string, number];
  newCommandKey?: () => string;
}) {
  const client = useQueryClient();
  const cacheKey = ["profile", ...identity];
  const identityRef = useRef(identity.join(":"));
  identityRef.current = identity.join(":");
  const [cancelled, setCancelled] = useState(false);
  const [success, setSuccess] = useState(false);
  const [reloadError, setReloadError] = useState<unknown>(null);
  const [refreshing, setRefreshing] = useState(false);
  // Keep an intentional command's body/key after an ambiguous timeout; never silently retry.
  const command = useRef<{ body: Patch; key: string } | null>(null);
  const current = useQuery({
    queryKey: cacheKey,
    queryFn: ({ signal }) => api.current(signal),
    retry: false,
    refetchOnWindowFocus: false,
    staleTime: 0,
  });
  const mutation = useMutation({
    mutationFn: async (body: Patch) => {
      const owner = identityRef.current;
      if (
        !command.current ||
        JSON.stringify(command.current.body) !== JSON.stringify(body)
      )
        command.current = { body, key: newCommandKey() };
      const saved = await api.save(command.current.body, command.current.key);
      return { saved, owner };
    },
    onSuccess: ({ saved, owner }) => {
      if (identityRef.current !== owner) return;
      client.setQueryData(cacheKey, saved);
      command.current = null;
      setSuccess(true);
      void client.invalidateQueries({
        queryKey: ["profile-history", ...identity],
      });
    },
    retry: false,
  });
  useEffect(
    () => () => {
      identityRef.current = "unmounted";
      command.current = null;
    },
    [],
  );
  async function reload() {
    setRefreshing(true);
    setReloadError(null);
    setSuccess(false);
    const owner = identityRef.current;
    try {
      // Throw on errors so a failed reload never discards the visible draft.
      const saved = await client.fetchQuery({
        queryKey: cacheKey,
        queryFn: ({ signal }) => api.current(signal),
        staleTime: 0,
      });
      if (identityRef.current !== owner) return;
      client.setQueryData(cacheKey, saved);
      command.current = null;
      mutation.reset();
    } catch (error: unknown) {
      if (identityRef.current === owner) setReloadError(error);
    } finally {
      if (identityRef.current === owner) setRefreshing(false);
    }
  }
  return (
    <>
      <header className="page-heading">
        <p className="eyebrow">Profile and evidence</p>
        <h1 tabIndex={-1}>Your background, in your words</h1>
        <p className="page-intro">
          Confirm what you know. Leave the rest unknown. Documents are optional.
        </p>
      </header>
      {success && (
        <p role="status" className="profile-success">
          Profile saved as a new version. Previous versions remain in your
          history.
        </p>
      )}
      {!current.data && current.isFetching ? (
        <StateView
          state="loading"
          title="Loading your profile"
          action={
            <button
              className="button button--secondary"
              onClick={() => {
                setCancelled(true);
                void client.cancelQueries({ queryKey: cacheKey });
              }}
            >
              Stop this request
            </button>
          }
        >
          <p>Only your own confirmed facts will be loaded.</p>
        </StateView>
      ) : !current.data && cancelled ? (
        <StateView
          state="cancelled"
          title="Profile request stopped"
          action={
            <button
              className="button"
              onClick={() => {
                setCancelled(false);
                void current.refetch();
              }}
            >
              Load profile
            </button>
          }
        >
          <p>This stops the browser read request only.</p>
        </StateView>
      ) : !current.data && current.isError ? (
        <ErrorView
          error={errorView(current.error)}
          onRetry={() => void current.refetch()}
        />
      ) : current.data ? (
        <>
          {current.data.facts.length === 0 && (
            <p className="profile-empty">
              No facts have been provided yet. Start with any field; you do not
              need to upload a document.
            </p>
          )}
          <ProfileForm
            key={current.data.version_id}
            profile={current.data}
            pending={mutation.isPending}
            error={mutation.error}
            reloadError={reloadError}
            refreshing={refreshing}
            onSave={(body) => {
              setSuccess(false);
              mutation.mutate(body);
            }}
            onReload={() => void reload()}
          />
          <History api={api} identity={identity} />
        </>
      ) : (
        <StateView state="unknown" title="Your profile has not been loaded">
          <p>Load your account profile before editing.</p>
        </StateView>
      )}
    </>
  );
}
