"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

type AccountMessage = {
  id: string;
  subject: string;
  from: string;
  snippet: string;
  date: string;
};

export default function AccountDetailsPage() {
  const params = useParams<{ id: string }>();
  const accountId = params.id;

  const [messages, setMessages] = useState<AccountMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadMessages() {
      try {
        setError(null);
        const response = await fetch(`/api/accounts/${encodeURIComponent(accountId)}/messages`, {
          cache: "no-store",
        });

        if (!response.ok) {
          if (response.status === 404) {
            throw new Error("Account not found.");
          }
          if (response.status === 400) {
            throw new Error("Unable to list messages for this account.");
          }
          throw new Error(`Request failed with status ${response.status}`);
        }

        const payload = (await response.json()) as AccountMessage[];
        if (!cancelled) {
          setMessages(payload);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load messages.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadMessages();
    return () => {
      cancelled = true;
    };
  }, [accountId]);

  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: "2rem 1rem" }}>
      <h1>Account Messages</h1>
      <p>
        <Link href="/accounts">Back to accounts</Link>
      </p>

      {loading ? <p>Loading messages...</p> : null}
      {error ? <p style={{ color: "crimson" }}>Error: {error}</p> : null}

      {!loading && !error ? (
        messages.length ? (
          <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: "0.75rem" }}>
            {messages.map((message) => (
              <li key={message.id} style={{ border: "1px solid #ddd", borderRadius: 6, padding: "0.75rem" }}>
                <div>
                  <strong>{message.subject || "(No subject)"}</strong>
                </div>
                <div>From: {message.from || "(Unknown sender)"}</div>
                <div>Date: {new Date(message.date).toLocaleString()}</div>
                <p style={{ marginBottom: 0 }}>{message.snippet || "(No snippet)"}</p>
              </li>
            ))}
          </ul>
        ) : (
          <p>No messages returned for this account.</p>
        )
      ) : null}
    </main>
  );
}
