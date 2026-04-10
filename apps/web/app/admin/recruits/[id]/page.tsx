"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { getScoreBand, getScoreBandLegend, usesSmashScoreBands } from "../_components/scoreBands";

type ScoreComponent = {
  raw?: number;
  weight?: number;
  contribution?: number;
};

type RankingDetail = {
  game_id?: number;
  score?: number;
  explanation_json?: {
    type?: string;
    total?: number;
    components?: Record<string, ScoreComponent>;
  };
  model_version?: string;
  raw_inputs_json?: Record<string, unknown>;
  normalized_features_json?: Record<string, unknown>;
  scoring_method?: string;
  is_current?: boolean;
  scored_at?: string;
};

type ApplicationData = {
  first_name?: string;
  last_name?: string;
  email?: string;
  discord?: string;
  created_at?: string;
};

type AvailabilityData = {
  hours_per_week?: number;
  weeknights_available?: boolean;
  weekends_available?: boolean;
};

type ProfileData = {
  game_slug?: string | null;
  ign?: string | null;
  epic_games_name?: string | null;
  current_rank_label?: string | null;
  peak_rank_label?: string | null;
  primary_role?: string | null;
  secondary_role?: string | null;
  cs2_roles?: string | null;
  prior_team_history?: string | null;
  faceit_level?: number | null;
  faceit_elo?: number | null;
  fortnite_pr?: number | null;
  fortnite_kd?: number | null;
  fortnite_total_kills?: number | null;
  fortnite_playtime_hours?: number | null;
  fortnite_wins?: number | null;
  tournament_experience?: string | null;
  tournament_experience_details?: string | null;
  tracker_url?: string | null;
  gsp?: number | null;
  regional_rank?: string | null;
  ranked_wins?: number | null;
  years_played?: number | null;
  legend_peak_rank?: number | null;
  preferred_format?: string | null;
  other_card_games?: string | null;
  lounge_rating?: number | null;
  preferred_title?: string | null;
  controller_type?: string | null;
  playstyle?: string | null;
  preferred_tracks?: string | null;
  best_wins?: string | null;
  characters?: string | null;
};

type RecruitDetailResponse = {
  application: ApplicationData;
  availability: AvailabilityData;
  profiles?: ProfileData[];
  rankings?: RankingDetail[];
  current_ranking?: RankingDetail | null;
  review?: {
    status?: RecruitReviewStatus;
    notes?: string | null;
    label_reason?: string | null;
    labeled_at?: string | null;
    reviewer_user_id?: number | null;
    reviewer_username?: string | null;
  };
};

function prettyKey(key: string): string {
  return key.replace(/_/g, " ").replace(/\b\w/g, (m) => m.toUpperCase());
}

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

function parseBackendTimestamp(value?: string): Date | null {
  if (!value) return null;
  const trimmed = value.trim();
  const hasTimezone = /[zZ]$|[+-]\d{2}:\d{2}$/.test(trimmed);
  const normalized = hasTimezone ? trimmed : `${trimmed}Z`;
  const parsed = new Date(normalized);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function formatTimestampLocal(value?: string): string {
  const parsed = parseBackendTimestamp(value);
  if (!parsed) return "N/A";
  return parsed.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "N/A";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "number") return Number.isInteger(value) ? String(value) : value.toFixed(2);
  if (Array.isArray(value)) return value.join(", ");
  return String(value);
}

function KeyValueSection({ title, data }: { title: string; data?: Record<string, unknown> }) {
  const entries = Object.entries(data || {});
  return (
    <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
      <h3 className="text-base font-medium">{title}</h3>
      {entries.length === 0 ? (
        <p className="mt-3 text-sm text-neutral-500">No data available.</p>
      ) : (
        <div className="mt-3 grid gap-2 md:grid-cols-2">
          {entries.map(([key, value]) => (
            <div key={key} className="rounded-lg border border-neutral-800 bg-neutral-900/50 px-3 py-2 text-sm">
              <p className="text-xs uppercase tracking-wide text-neutral-500">{prettyKey(key)}</p>
              <p className="mt-1 text-neutral-100">{formatValue(value)}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function RecruitDetailPage() {
  const params = useParams();
  const router = useRouter();
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const [data, setData] = useState<RecruitDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [status, setStatus] = useState<RecruitReviewStatus>("NEW");
  const [labelReason, setLabelReason] = useState("");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("au_admin_token");
    if (!token) {
      router.push("/admin/login");
      return;
    }

    (async () => {
      setLoading(true);
      setLoadError(null);
      try {
        const res = await fetch(`${apiUrl}/api/v1/admin/recruit/${params.id}`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (res.status === 401 || res.status === 403) {
          localStorage.removeItem("au_admin_token");
          localStorage.removeItem("au_admin_role");
          localStorage.removeItem("au_admin_username");
          router.push("/admin/login");
          return;
        }

        if (res.status === 404) {
          setData(null);
          setLoadError("Recruit not found. It may have been deleted.");
          return;
        }

        if (!res.ok) {
          setData(null);
          setLoadError(`Failed to load recruit (${res.status}).`);
          return;
        }

        const result = await res.json();
        setData(result);
        setStatus((result.review?.status as RecruitReviewStatus) || "NEW");
        setLabelReason(result.review?.label_reason || "");
        setNotes(result.review?.notes || "");
      } catch {
        setData(null);
        setLoadError("Failed to load recruit.");
      } finally {
        setLoading(false);
      }
    })();
  }, [apiUrl, params.id, router]);

  async function saveStatus() {
    const token = localStorage.getItem("au_admin_token");
    if (!token) return;

    setSaving(true);
    try {
      const res = await fetch(`${apiUrl}/api/v1/admin/recruit/${params.id}/status`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          status,
          label_reason: labelReason.trim() ? labelReason.trim() : null,
        }),
      });

      if (res.ok) {
        const payload = (await res.json()) as {
          status?: RecruitReviewStatus;
          label_reason?: string | null;
          labeled_at?: string | null;
          reviewer_user_id?: number | null;
          reviewer_username?: string | null;
        };

        setData((prev) => {
          if (!prev) return prev;
          return {
            ...prev,
            review: {
              ...prev.review,
              status: payload.status || status,
              label_reason: payload.label_reason ?? null,
              labeled_at: payload.labeled_at ?? null,
              reviewer_user_id: payload.reviewer_user_id ?? null,
              reviewer_username: payload.reviewer_username ?? null,
            },
          };
        });
      }
    } finally {
      setSaving(false);
    }
  }

  async function saveNotes() {
    const token = localStorage.getItem("au_admin_token");
    if (!token) return;

    setSaving(true);
    try {
      await fetch(`${apiUrl}/api/v1/admin/recruit/${params.id}/notes`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ notes }),
      });
    } finally {
      setSaving(false);
    }
  }

  const ranking: RankingDetail | null =
    data?.current_ranking || (Array.isArray(data?.rankings) && data.rankings.length > 0 ? data.rankings[0] : null);

  const components = useMemo(() => {
    const obj = ranking?.explanation_json?.components;
    if (!obj) return [] as Array<{ name: string; raw: number; weight: number; contribution: number }>;
    return Object.entries(obj)
      .map(([name, value]) => ({
        name,
        raw: typeof value.raw === "number" ? value.raw : 0,
        weight: typeof value.weight === "number" ? value.weight : 0,
        contribution: typeof value.contribution === "number" ? value.contribution : 0,
      }))
      .sort((a, b) => b.contribution - a.contribution);
  }, [ranking]);

  const characterList =
    data?.profiles?.[0]?.characters && typeof data.profiles[0].characters === "string"
      ? data.profiles[0].characters.split(",").map((c: string) => c.trim()).filter(Boolean)
      : [];

  const bestWinsList =
    data?.profiles?.[0]?.best_wins && typeof data.profiles[0].best_wins === "string"
      ? data.profiles[0].best_wins.split(",").map((w: string) => w.trim()).filter(Boolean)
      : [];

  const isSmashProfile =
    data?.profiles?.[0]?.gsp != null ||
    !!data?.profiles?.[0]?.regional_rank ||
    !!data?.profiles?.[0]?.best_wins ||
    !!data?.profiles?.[0]?.characters;

  if (loading) {
    return <div className="p-6 text-neutral-400">Loading...</div>;
  }

  if (!data) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-semibold">Recruit Detail</h1>
        <p className="mt-2 text-sm text-red-400">{loadError || "Recruit not found."}</p>
        <Link
          href="/admin"
          className="mt-4 inline-flex rounded-lg border border-neutral-700 bg-neutral-900 px-4 py-2 text-sm text-neutral-200 transition hover:bg-neutral-800"
        >
          Back to Admin
        </Link>
      </div>
    );
  }

  const app = data.application;
  const availability = data.availability;
  const profile = data.profiles?.[0];
  const recruitGameSlug = profile?.game_slug || (isSmashProfile ? "smash" : null);
  const scoreBand = getScoreBand(ranking?.score, recruitGameSlug);
  const scoreBandLegend = getScoreBandLegend(recruitGameSlug);
  const usesSmashBands = usesSmashScoreBands(recruitGameSlug);
  const review = data.review;
  const reviewerDisplay = review?.reviewer_username || (review?.reviewer_user_id ? `User #${review.reviewer_user_id}` : "N/A");

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">
          {app.first_name} {app.last_name}
        </h1>
        <p className="text-neutral-400">Email: {app.email}</p>
        <p className="text-neutral-400">Discord: {app.discord}</p>
        <p className="text-sm text-neutral-500">Submitted: {formatTimestampLocal(app.created_at)}</p>
      </div>

      <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
        <h2 className="text-lg font-medium">
          {isSmashProfile ? "Smash Scouting Profile" : "Game Profile"}
        </h2>

        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div className="space-y-2 text-sm">
            <p>IGN / BattleTag: {profile?.ign || "N/A"}</p>
            {profile?.epic_games_name && <p>Epic Games Name: {profile.epic_games_name}</p>}
            <p>Current Rank: {profile?.current_rank_label || "N/A"}</p>
            <p>Peak Rank: {profile?.peak_rank_label || "N/A"}</p>
            <p>Primary Role / Main Focus: {profile?.primary_role || "N/A"}</p>
            <p>Secondary Role / Extra Info: {profile?.secondary_role || "N/A"}</p>
            {profile?.cs2_roles && <p>CS2 Additional Roles: {profile.cs2_roles}</p>}
            <p>Tournament Experience: {profile?.tournament_experience || "N/A"}</p>
            {profile?.tournament_experience_details && (
              <p>Tournament Experience Details: {profile.tournament_experience_details}</p>
            )}
            {profile?.tracker_url ? (
              <p>
                Tracker:{" "}
                <a href={profile.tracker_url} target="_blank" rel="noreferrer" className="text-blue-400 underline">
                  Open Link
                </a>
              </p>
            ) : (
              <p>Tracker: N/A</p>
            )}
          </div>

          <div className="space-y-2 text-sm">
            {profile?.faceit_level != null && <p>Faceit Level: {profile.faceit_level}</p>}
            {profile?.faceit_elo != null && <p>Faceit ELO: {profile.faceit_elo}</p>}
            {profile?.prior_team_history && <p>Prior Team History: {profile.prior_team_history}</p>}
            {profile?.fortnite_pr != null && <p>Fortnite PR: {profile.fortnite_pr}</p>}
            {profile?.fortnite_kd != null && <p>Fortnite K/D: {profile.fortnite_kd}</p>}
            {profile?.fortnite_total_kills != null && <p>Total Kills: {profile.fortnite_total_kills}</p>}
            {profile?.fortnite_playtime_hours != null && <p>Playtime (Hours): {profile.fortnite_playtime_hours}</p>}
            {profile?.fortnite_wins != null && <p>Wins: {profile.fortnite_wins}</p>}
            {profile?.gsp != null && <p>GSP: {profile.gsp}</p>}
            {profile?.regional_rank && <p>Regional Rank: {profile.regional_rank}</p>}
            {profile?.ranked_wins != null && <p>Ranked Wins: {profile.ranked_wins}</p>}
            {profile?.years_played != null && <p>Years Played: {profile.years_played}</p>}
            {profile?.legend_peak_rank != null && <p>Legend Peak Rank: {profile.legend_peak_rank}</p>}
            {profile?.preferred_format && <p>Preferred Format: {profile.preferred_format}</p>}
            {profile?.other_card_games && <p>Other Card Games: {profile.other_card_games}</p>}
            {profile?.lounge_rating != null && <p>Lounge Rating: {profile.lounge_rating}</p>}
            {profile?.preferred_title && <p>Preferred Title: {profile.preferred_title}</p>}
            {profile?.controller_type && <p>Controller Type: {profile.controller_type}</p>}
            {profile?.playstyle && <p>Playstyle: {profile.playstyle}</p>}
            {profile?.preferred_tracks && <p>Preferred Tracks / Notes: {profile.preferred_tracks}</p>}
          </div>
        </div>

        {characterList.length > 0 && (
          <div className="mt-6">
            <h3 className="text-sm font-medium text-neutral-300">Characters Played</h3>
            <div className="mt-2 flex flex-wrap gap-2">
              {characterList.map((char: string) => (
                <span key={char} className="rounded-full border border-neutral-700 bg-neutral-900 px-3 py-1 text-xs">
                  {char}
                </span>
              ))}
            </div>
          </div>
        )}

        {bestWinsList.length > 0 && (
          <div className="mt-6">
            <h3 className="text-sm font-medium text-neutral-300">Best Wins</h3>
            <div className="mt-2 flex flex-wrap gap-2">
              {bestWinsList.map((win: string) => (
                <span key={win} className="rounded-full border border-neutral-700 bg-neutral-900 px-3 py-1 text-xs">
                  {win}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
        <h2 className="text-lg font-medium">Availability</h2>
        <div className="mt-3 space-y-2 text-sm">
          <p>Hours/Week: {availability?.hours_per_week}</p>
          <p>Weeknights: {availability?.weeknights_available ? "Yes" : "No"}</p>
          <p>Weekends: {availability?.weekends_available ? "Yes" : "No"}</p>
        </div>
      </div>

      <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
        <h2 className="text-lg font-medium">Recruit Ranking</h2>

        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <p className="text-sm text-neutral-400">Overall Score</p>
            <p className="mt-1 text-3xl font-semibold">{ranking?.score ?? "N/A"}</p>
            {scoreBand && (
              <div className="mt-2">
                <span
                  className={`inline-flex rounded-full border px-2 py-0.5 text-xs font-medium ${scoreBand.badgeClassName}`}
                >
                  {scoreBand.label}
                </span>
                <p className="mt-2 text-sm text-neutral-300">{scoreBand.coachGuidance}</p>
              </div>
            )}
            <div className="mt-3 rounded-lg border border-neutral-800 bg-neutral-900/40 p-3">
              <p className="text-xs uppercase tracking-wide text-neutral-500">Coach triage playbook</p>
              <p className="mt-1 text-xs text-neutral-400">
                Use score bands to prioritize review order. Coaches make final decisions using gameplay fit, notes,
                and current team needs.
              </p>
              <div className="mt-2 flex flex-wrap gap-2 text-xs text-neutral-300">
                {scoreBandLegend.map((item) => (
                  <span
                    key={`${item.label}-${item.range}`}
                    className="rounded-full border border-neutral-700 bg-neutral-900 px-2 py-1"
                  >
                    {item.label}: {item.range}
                  </span>
                ))}
              </div>
              {usesSmashBands && (
                <p className="mt-2 text-xs text-amber-300">Smash intentionally uses lower score bands.</p>
              )}
            </div>
            <p className="mt-2 text-sm text-neutral-400">
              Scoring Method: <span className="text-white">{ranking?.scoring_method || "N/A"}</span>
            </p>
            <p className="mt-1 text-sm text-neutral-400">
              Model/Version: <span className="text-white">{ranking?.model_version || "N/A"}</span>
            </p>
            <p className="mt-1 text-sm text-neutral-400">
              Scored At:{" "}
              <span className="text-white">{formatTimestampLocal(ranking?.scored_at)}</span>
            </p>
            <p className="mt-3 text-sm text-neutral-400">
              Status: <span className="text-white">{status || review?.status || "NEW"}</span>
            </p>
            <p className="mt-1 text-sm text-neutral-400">
              Labeled At: <span className="text-white">{formatTimestampLocal(review?.labeled_at || undefined)}</span>
            </p>
            <p className="mt-1 text-sm text-neutral-400">
              Labeled By: <span className="text-white">{reviewerDisplay}</span>
            </p>
            <p className="mt-1 text-sm text-neutral-400">
              Label Reason: <span className="text-white">{review?.label_reason || "N/A"}</span>
            </p>
          </div>

          <div>
            <p className="text-sm text-neutral-400">Weighted Breakdown</p>
            {components.length === 0 ? (
              <p className="mt-2 text-sm text-neutral-500">No breakdown data available.</p>
            ) : (
              <div className="mt-2 overflow-x-auto rounded-lg border border-neutral-800">
                <table className="w-full text-sm">
                  <thead className="bg-neutral-900 text-neutral-400">
                    <tr>
                      <th className="px-3 py-2 text-left font-medium">Component</th>
                      <th className="px-3 py-2 text-right font-medium">Raw</th>
                      <th className="px-3 py-2 text-right font-medium">Weight</th>
                      <th className="px-3 py-2 text-right font-medium">Contribution</th>
                    </tr>
                  </thead>
                  <tbody>
                    {components.map((component) => (
                      <tr key={component.name} className="border-t border-neutral-800">
                        <td className="px-3 py-2">{prettyKey(component.name)}</td>
                        <td className="px-3 py-2 text-right">{component.raw.toFixed(2)}</td>
                        <td className="px-3 py-2 text-right">{component.weight.toFixed(2)}</td>
                        <td className="px-3 py-2 text-right font-medium">{component.contribution.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>

      <KeyValueSection title="Inputs Used" data={ranking?.raw_inputs_json} />
      <KeyValueSection title="Normalized Features" data={ranking?.normalized_features_json} />

      <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
        <h2 className="text-lg font-medium">Coach Review</h2>

        <div className="mt-4 space-y-4">
          <div>
            <label className="text-sm text-neutral-400">Status</label>
            <select
              className="mt-1 w-full rounded-lg border border-neutral-800 bg-neutral-900 p-2"
              value={status}
              onChange={(e) => setStatus(e.target.value as RecruitReviewStatus)}
            >
              {REVIEW_STATUS_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
            <label className="mt-3 block text-sm text-neutral-400">Label Reason (Optional)</label>
            <input
              className="mt-1 w-full rounded-lg border border-neutral-800 bg-neutral-900 p-2"
              value={labelReason}
              onChange={(e) => setLabelReason(e.target.value)}
              placeholder="Reason for this status/label"
            />
            <button onClick={saveStatus} className="mt-2 rounded-lg bg-white px-4 py-2 text-black" disabled={saving}>
              Save Status
            </button>
          </div>

          <div>
            <label className="text-sm text-neutral-400">Coach Notes</label>
            <textarea
              className="mt-1 min-h-[120px] w-full rounded-lg border border-neutral-800 bg-neutral-900 p-2"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
            <button onClick={saveNotes} className="mt-2 rounded-lg bg-white px-4 py-2 text-black" disabled={saving}>
              Save Notes
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
