export interface AuthSession {
  accessToken: string;
  expiresAt: number;
  subject: string;
  recovery: boolean;
}

export interface SessionState {
  subject: string | null;
  recovery: boolean;
  expired: boolean;
  generation: number;
}

export interface SessionClock {
  now(): number;
  schedule(callback: () => void, delay: number): () => void;
}

const browserClock: SessionClock = {
  now: () => Date.now(),
  schedule(callback, delay) {
    const timer = setTimeout(callback, delay);
    return () => clearTimeout(timer);
  },
};

// Tokens never enter React state, query keys, URLs or browser storage.
export class MemorySession {
  private session: AuthSession | null = null;
  private state: SessionState = {
    subject: null,
    recovery: false,
    expired: false,
    generation: 0,
  };
  private listeners = new Set<() => void>();
  private cancelTimer: (() => void) | null = null;
  constructor(private readonly clock: SessionClock = browserClock) {}

  snapshot = (): SessionState => this.state;
  subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  replace(session: AuthSession | null, expired = false): void {
    this.cancelTimer?.();
    this.cancelTimer = null;
    if (
      session &&
      (!Number.isSafeInteger(session.expiresAt) ||
        !session.accessToken ||
        !session.subject ||
        session.expiresAt * 1000 <= this.clock.now())
    ) {
      session = null;
      expired = true;
    }
    const changed =
      this.state.subject !== (session?.subject ?? null) ||
      this.state.recovery !== (session?.recovery ?? false);
    this.session = session;
    this.state = {
      subject: session?.subject ?? null,
      recovery: session?.recovery ?? false,
      expired,
      generation: this.state.generation + (changed ? 1 : 0),
    };
    if (session) {
      const remaining = session.expiresAt * 1000 - this.clock.now();
      this.cancelTimer = this.clock.schedule(
        () => {
          if (this.session === session) {
            if (session.expiresAt * 1000 > this.clock.now())
              this.replace(session);
            else this.replace(null, true);
          }
        },
        Math.min(remaining, 2_147_483_647),
      );
    }
    for (const listener of this.listeners) listener();
  }

  token = (): string | null => {
    if (this.session && this.session.expiresAt * 1000 <= this.clock.now()) {
      this.replace(null, true);
    }
    // A recovery session must finish the password flow before application use.
    return this.session && !this.session.recovery
      ? this.session.accessToken
      : null;
  };
}
