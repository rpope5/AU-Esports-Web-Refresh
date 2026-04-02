"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

type ScoreComponent = {
  raw?: number;
  weight?: number;
  contribution?: number;
};

type Recruit = {
  application_id: number;
  first_name: string;
  last_name: string;
  email: string;
  discord: string;
  graduation_year: number | null;
  current_school: string | null;
  ign: string | null;
  current_rank_label: string | null;
  primary_role: string | null;
  secondary_role: string | null;
  tracker_url: string | null;
  score: number | null;
  status: string;
  score_model_version?: string | null;
  score_scoring_method?: string | null;
  score_scored_at?: string | null;
  score_is_current?: boolean | null;
  score_components?: Record<string, ScoreComponent> | null;
};

type SortOption = "score_desc" | "score_asc" | "name_asc" | "name_desc" | "scored_at_desc";

type Props = {
  gameSlug: string;
  title: string;
  description: string;
};

function prettyKey(key: string): string {
  return key.replace(/_/g, " ").replace(/\b\w/g, (m) => m.toUpperCase());
}

function reasonPreview(components?: Record<string, ScoreComponent> | null): string {
  if (!components) return "No score breakdown available";
  const ranked = Object.entries(components)
    .filter(([, value]) => typeof value?.contribution === "number")
    .sort((a, b) => (b[1].contribution ?? 0) - (a[1].contribution ?? 0))
    .slice(0, 2)
    .map(([key, value]) => `${prettyKey(key)} +${(value.contribution ?? 0).toFixed(1)}`);

  return ranked.length > 0 ? ranked.join(" | ") : "No score breakdown available";
}

export default function RecruitGameListPage({ gameSlug, title, description }: Props) {
  const router = useRouter();
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const [recruits, setRecruits] = useState<Recruit[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const [sortBy, setSortBy] = useState<SortOption>("score_desc");
  const [statusFilter, setStatusFilter] = useState("");
  const [minScoreInput, setMinScoreInput] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("au_admin_token");
    if (!token) {
      router.push("/admin/login");
      return;
    }

    (async () => {
      setLoading(true);
      setErr(null);
      try {
        const params = new URLSearchParams();
        if (statusFilter) params.set("status", statusFilter);
        if (minScoreInput.trim()) params.set("min_score", minScoreInput.trim());

        const query = params.toString();
        const url = `${apiUrl}/api/v1/admin/recruits/game/${gameSlug}${query ? `?${query}` : ""}`;
        const res = await fetch(url, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (res.status === 401 || res.status === 403) {
          localStorage.removeItem("au_admin_token");
          router.push("/admin/login");
          return;
        }

        if (!res.ok) {
          const text = await res.text();
          console.error(`Failed to load ${gameSlug} recruits:`, res.status, text);
          setErr(`Failed to load recruits (${res.status})`);
          return;
        }

        const data = (await res.json()) as Recruit[];
        setRecruits(data);
      } catch (e: unknown) {
        setErr(e instanceof Error ? e.message : "Failed to load recruits");
      } finally {
        setLoading(false);
      }
    })();
  }, [apiUrl, router, gameSlug, statusFilter, minScoreInput]);

  const displayedRecruits = useMemo(() => {
    const rows = [...recruits];
    rows.sort((a, b) => {
      if (sortBy === "score_desc") {
        return (b.score ?? -Infinity) - (a.score ?? -Infinity);
      }
      if (sortBy === "score_asc") {
        return (a.score ?? Infinity) - (b.score ?? Infinity);
      }
      if (sortBy === "name_asc") {
        return `${a.last_name} ${a.first_name}`.localeCompare(`${b.last_name} ${b.first_name}`);
      }
      if (sortBy === "name_desc") {
        return `${b.last_name} ${b.first_name}`.localeCompare(`${a.last_name} ${a.first_name}`);
      }
      const aDate = a.score_scored_at ? Date.parse(a.score_scored_at) : 0;
      const bDate = b.score_scored_at ? Date.parse(b.score_scored_at) : 0;
      return bDate - aDate;
    });
    return rows;
  }, [recruits, sortBy]);

  return (
    <div className="p-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">{title}</h1>
          <p className="mt-1 text-sm text-neutral-400">{description}</p>
        </div>

        <Link
          href="/admin"
          className="rounded-lg border border-neutral-800 bg-neutral-950 px-4 py-2 text-sm hover:border-neutral-700"
        >
          Back to Admin
        </Link>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-3">
        <div>
          <label className="text-xs uppercase tracking-wide text-neutral-500">Sort</label>
          <select
            className="mt-1 w-full rounded-lg border border-neutral-800 bg-neutral-950 p-2 text-sm"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortOption)}
          >
            <option value="score_desc">Score: High to Low</option>
            <option value="score_asc">Score: Low to High</option>
            <option value="scored_at_desc">Most Recently Scored</option>
            <option value="name_asc">Name: A to Z</option>
            <option value="name_desc">Name: Z to A</option>
          </select>
        </div>

        <div>
          <label className="text-xs uppercase tracking-wide text-neutral-500">Min Score</label>
          <input
            className="mt-1 w-full rounded-lg border border-neutral-800 bg-neutral-950 p-2 text-sm"
            type="number"
            min={0}
            max={100}
            step="0.1"
            value={minScoreInput}
            onChange={(e) => setMinScoreInput(e.target.value)}
            placeholder="e.g. 70"
          />
        </div>

        <div>
          <label className="text-xs uppercase tracking-wide text-neutral-500">Status</label>
          <select
            className="mt-1 w-full rounded-lg border border-neutral-800 bg-neutral-950 p-2 text-sm"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All</option>
            <option value="NEW">NEW</option>
            <option value="REVIEWED">REVIEWED</option>
            <option value="CONTACTED">CONTACTED</option>
            <option value="TRYOUT">TRYOUT</option>
            <option value="ACCEPTED">ACCEPTED</option>
            <option value="REJECTED">REJECTED</option>
          </select>
        </div>
      </div>

      {loading ? (
        <p className="mt-4 text-neutral-400">Loading...</p>
      ) : err ? (
        <p className="mt-4 text-red-400">{err}</p>
      ) : displayedRecruits.length === 0 ? (
        <p className="mt-4 text-neutral-400">No recruits found for current filters.</p>
      ) : (
        <div className="mt-6 grid gap-4">
          {displayedRecruits.map((r) => (
            <Link
              key={r.application_id}
              href={`/admin/recruits/${r.application_id}`}
              className="rounded-xl border border-neutral-800 bg-neutral-950 p-4 hover:border-neutral-700"
            >
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-lg font-medium">
                    {r.first_name} {r.last_name}
                  </h2>
                  <p className="text-sm text-neutral-400">
                    {(r.ign || "N/A")} | {(r.current_rank_label || "N/A")} | {(r.primary_role || "N/A")}
                    {r.secondary_role ? ` / ${r.secondary_role}` : ""}
                  </p>
                  <p className="mt-1 text-sm text-neutral-500">
                    {r.current_school || "Unknown school"} | Class of {r.graduation_year ?? "N/A"}
                  </p>
                  <p className="mt-2 text-xs text-neutral-500">{reasonPreview(r.score_components)}</p>
                </div>

                <div className="text-right">
                  <div className="text-sm text-neutral-400">Score</div>
                  <div className="text-2xl font-semibold">{r.score ?? "--"}</div>
                  <div className="mt-1 text-xs uppercase tracking-wide text-neutral-500">{r.status}</div>
                  {r.score_model_version && (
                    <div className="mt-1 text-xs text-neutral-600">
                      {r.score_scoring_method || "rules"} | {r.score_model_version}
                    </div>
                  )}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
