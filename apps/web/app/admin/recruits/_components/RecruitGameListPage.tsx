"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { getScoreBand, getScoreBandLegend, usesSmashScoreBands } from "./scoreBands";
import InlineDestructiveConfirm from "../../_components/InlineDestructiveConfirm";

type ScoreComponent = {
  raw?: number;
  weight?: number;
  contribution?: number;
};

type RecruitReviewStatus =
  | "NEW"
  | "REVIEWED"
  | "CONTACTED"
  | "TRYOUT"
  | "WATCHLIST"
  | "ACCEPTED"
  | "REJECTED";

const REVIEW_STATUS_OPTIONS: RecruitReviewStatus[] = [
  "NEW",
  "REVIEWED",
  "CONTACTED",
  "TRYOUT",
  "WATCHLIST",
  "ACCEPTED",
  "REJECTED",
];

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
  status: RecruitReviewStatus;
  review_labeled_at?: string | null;
  reviewer_username?: string | null;
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

function parseBackendTimestamp(value?: string | null): Date | null {
  if (!value) return null;
  const trimmed = value.trim();
  const hasTimezone = /[zZ]$|[+-]\d{2}:\d{2}$/.test(trimmed);
  const normalized = hasTimezone ? trimmed : `${trimmed}Z`;
  const parsed = new Date(normalized);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function formatTimestampShort(value?: string | null): string {
  const parsed = parseBackendTimestamp(value);
  if (!parsed) return "Not labeled";
  return parsed.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
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
  const [loadErr, setLoadErr] = useState<string | null>(null);
  const [actionErr, setActionErr] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const [sortBy, setSortBy] = useState<SortOption>("score_desc");
  const [statusFilter, setStatusFilter] = useState<"" | RecruitReviewStatus>("");
  const [minScoreInput, setMinScoreInput] = useState("");
  const triageLegend = useMemo(() => getScoreBandLegend(gameSlug), [gameSlug]);
  const isSmashPolicy = usesSmashScoreBands(gameSlug);

  useEffect(() => {
    const token = localStorage.getItem("au_admin_token");
    if (!token) {
      router.push("/admin/login");
      return;
    }

    (async () => {
      setLoading(true);
      setLoadErr(null);
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
          setLoadErr(`Failed to load recruits (${res.status})`);
          return;
        }

        const data = (await res.json()) as Recruit[];
        setRecruits(data);
      } catch (e: unknown) {
        setLoadErr(e instanceof Error ? e.message : "Failed to load recruits");
      } finally {
        setLoading(false);
      }
    })();
  }, [apiUrl, router, gameSlug, statusFilter, minScoreInput]);

  async function deleteRecruit(applicationId: number): Promise<void> {
    const token = localStorage.getItem("au_admin_token");
    if (!token) {
      router.push("/admin/login");
      throw new Error("Session expired");
    }

    setDeletingId(applicationId);
    setActionErr(null);
    setSuccess(null);
    try {
      const res = await fetch(`${apiUrl}/api/v1/admin/recruit/${applicationId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.status === 401 || res.status === 403) {
        localStorage.removeItem("au_admin_token");
        localStorage.removeItem("au_admin_role");
        localStorage.removeItem("au_admin_username");
        router.push("/admin/login");
        throw new Error("Unauthorized");
      }

      if (res.status === 404) {
        setRecruits((prev) => prev.filter((recruit) => recruit.application_id !== applicationId));
        setSuccess("Recruit was already removed.");
        return;
      }

      if (!res.ok) {
        const responseText = await res.text();
        throw new Error(responseText || "Failed to delete recruit");
      }

      setRecruits((prev) => prev.filter((recruit) => recruit.application_id !== applicationId));
      setSuccess("Recruit deleted.");
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : "Failed to delete recruit";
      setActionErr(message);
      throw new Error(message);
    } finally {
      setDeletingId(null);
    }
  }

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
            onChange={(e) => setStatusFilter(e.target.value as "" | RecruitReviewStatus)}
          >
            <option value="">All</option>
            {REVIEW_STATUS_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="mt-4 rounded-xl border border-neutral-800 bg-neutral-950 p-3">
        <p className="text-sm text-neutral-200">Coach triage playbook</p>
        <p className="mt-1 text-xs text-neutral-400">
          Scores help prioritize review order. Coaches make final decisions using gameplay context and notes.
        </p>
        <div className="mt-2 flex flex-wrap gap-2 text-xs">
          {triageLegend.map((item) => (
            <span
              key={`${item.label}-${item.range}`}
              className="rounded-full border border-neutral-700 bg-neutral-900 px-2 py-1 text-neutral-300"
            >
              {item.label}: {item.range}
            </span>
          ))}
          {isSmashPolicy && (
            <span className="rounded-full border border-amber-800 bg-amber-950/40 px-2 py-1 text-amber-200">
              Smash uses lower score bands by design.
            </span>
          )}
        </div>
      </div>

      {actionErr && <p className="mt-4 text-sm text-red-400">{actionErr}</p>}
      {success && <p className="mt-4 text-sm text-emerald-400">{success}</p>}

      {loading ? (
        <p className="mt-4 text-neutral-400">Loading...</p>
      ) : loadErr ? (
        <p className="mt-4 text-red-400">{loadErr}</p>
      ) : displayedRecruits.length === 0 ? (
        <p className="mt-4 text-neutral-400">No recruits found for current filters.</p>
      ) : (
        <div className="mt-6 grid gap-4">
          {displayedRecruits.map((r) => {
            const scoreBand = getScoreBand(r.score, gameSlug);
            return (
              <article
                key={r.application_id}
                className="rounded-xl border border-neutral-800 bg-neutral-950 p-4"
              >
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <Link
                    href={`/admin/recruits/${r.application_id}`}
                    className="min-w-0 flex-1 rounded-lg p-1 transition hover:bg-neutral-900/40"
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
                        {scoreBand && (
                          <div
                            className={`mt-1 inline-flex rounded-full border px-2 py-0.5 text-xs font-medium ${scoreBand.badgeClassName}`}
                          >
                            {scoreBand.label}
                          </div>
                        )}
                        <div className="mt-1 text-xs uppercase tracking-wide text-neutral-500">{r.status}</div>
                        <div className="mt-1 text-xs text-neutral-500">Labeled: {formatTimestampShort(r.review_labeled_at)}</div>
                        <div className="mt-1 text-xs text-neutral-500">By: {r.reviewer_username || "N/A"}</div>
                        {r.score_model_version && (
                          <div className="mt-1 text-xs text-neutral-600">
                            {r.score_scoring_method || "rules"} | {r.score_model_version}
                          </div>
                        )}
                      </div>
                    </div>
                  </Link>

                  <div className="w-full sm:w-auto">
                    <InlineDestructiveConfirm
                      triggerLabel="Delete"
                      confirmMessage="This recruit submission is about to be permanently deleted."
                      confirmLabel="Delete Permanently"
                      pendingLabel="Deleting..."
                      busy={deletingId === r.application_id}
                      onConfirm={() => deleteRecruit(r.application_id)}
                    />
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}
