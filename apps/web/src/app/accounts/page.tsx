"use client";

import { useEffect, useState } from "react";

type Account = {
  id: number;
  email: string;
  google_sub: string;
  scopes: string;
};

type AccountsResponse = {
  accounts: Account[];
};

export default function AccountsPage() {
  const [data, setData] = useState<AccountsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refreshAccounts() {
    const response = await fetch("/api/accounts", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }
    const payload = (await response.json()) as AccountsResponse;
    setData(payload);
  }

  async function disconnectAccount(id: number) {
    try {
      setActionLoading(true);
      setError(null);

      const response = await fetch(`/api/accounts/${id}`, { method: "DELETE" });
      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      await refreshAccounts();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to disconnect account.");
    } finally {
      setActionLoading(false);
    }
  }

  async function logout() {
    try {
      setActionLoading(true);
      setError(null);

      const response = await fetch("/api/logout", { method: "POST" });
      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      await refreshAccounts();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to log out.");
    } finally {
      setActionLoading(false);
    }
  }

  useEffect(() => {
    let cancelled = false;

    async function loadAccounts() {
      try {
        setError(null);
        const response = await fetch("/api/accounts", { cache: "no-store" });
        if (!response.ok) {
          throw new Error(`Request failed with status ${response.status}`);
        }
        const payload = (await response.json()) as AccountsResponse;
        if (!cancelled) {
          setData(payload);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load accounts.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadAccounts();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: "2rem 1rem" }}>
      <h1>Connected Gmail Accounts</h1>
      <p>
        <a href="/api/oauth/google/start">Connect Gmail account</a>
      </p>
      <p>
        <button onClick={logout} disabled={actionLoading}>
          {actionLoading ? "Working..." : "Logout"}
        </button>
      </p>

      {loading ? <p>Loading accounts...</p> : null}
      {!loading && actionLoading ? <p>Updating accounts...</p> : null}
      {error ? <p style={{ color: "crimson" }}>Error: {error}</p> : null}

      {!loading && !error ? (
        data?.accounts.length ? (
          <ul>
            {data.accounts.map((account) => (
              <li key={account.id}>
                {account.email}{" "}
                <button onClick={() => disconnectAccount(account.id)} disabled={actionLoading}>
                  Disconnect
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p>No connected accounts yet.</p>
        )
      ) : null}
    </main>
  );
}
