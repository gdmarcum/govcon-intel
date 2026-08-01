"use client";

import { useState } from "react";

type Recommendation = {
  uei: string;
  name: string;
  score: number;
  capability_match: number;
  agency_contracts: number;
};

export default function Home() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<Recommendation[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function handleSearch() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ opportunity: query }),
      });
      if (!response.ok) throw new Error(`Request failed: ${response.status}`);
      const data = await response.json();
      setResults(data.recommendations);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex flex-col items-center px-4 py-16">
      <h1 className="text-2xl tracking-tight text-[var(--color-accent)]">
        GovCon Intelligence
      </h1>
      <p className="mt-2 text-sm text-[var(--color-muted)] text-center max-w-md">
        Paste an opportunity. Get a partner shortlist backed by contract history, not claims.
      </p>
      <div className="mt-8 w-full max-w-xl flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Opportunity description or NAICS code..."
          className="flex-1 bg-transparent border border-[var(--color-muted)] rounded px-4 py-3 text-sm focus:outline-none focus:border-[var(--color-accent)]"
        />
        <button
          onClick={handleSearch}
          disabled={loading || !query}
          className="px-4 py-3 text-sm border border-[var(--color-accent)] text-[var(--color-accent)] rounded disabled:opacity-40"
        >
          {loading ? "..." : "Search"}
        </button>
      </div>

      {error && <p className="mt-6 text-sm text-red-400">{error}</p>}

      <div className="mt-10 w-full max-w-xl flex flex-col gap-3">
        {results.map((r) => (
          <div key={r.uei} className="border border-[var(--color-muted)] rounded p-4">
            <div className="flex justify-between items-baseline">
              <span className="text-[var(--color-fg)]">{r.name}</span>
              <span className="text-[var(--color-accent)] text-sm">
                {Math.round(r.score * 100)}%
              </span>
            </div>
            <p className="mt-1 text-xs text-[var(--color-muted)]">
              {r.capability_match} matching capabilities · {r.agency_contracts} contracts with this agency
            </p>
          </div>
        ))}
      </div>
    </main>
  );
}
