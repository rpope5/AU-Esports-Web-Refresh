"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";

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
};

type AvailabilityData = {
  hours_per_week?: number;
  weeknights_available?: boolean;
  weekends_available?: boolean;
};

type ProfileData = {
  ign?: string | null;
  current_rank_label?: string | null;
  peak_rank_label?: string | null;
  primary_role?: string | null;
  secondary_role?: string | null;
  tournament_experience?: string | null;
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
  review?: { status?: string; notes?: string | null };
};

function prettyKey(key: string): string {
  return key.replace(/_/g, " ").replace(/\b\w/g, (m) => m.toUpperCase());
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
  const [status, setStatus] = useState("");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("au_admin_token");
    if (!token) {
      router.push("/admin/login");
      return;
    }

    (async () => {
      const res = await fetch(`${apiUrl}/api/v1/admin/recruit/${params.id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        router.push("/admin/login");
        return;
      }

      const result = await res.json();
      setData(result);
      setStatus(result.review?.status || "NEW");
      setNotes(result.review?.notes || "");
    })();
  }, [apiUrl, params.id, router]);

  async function saveStatus() {
    const token = localStorage.getItem("au_admin_token");
    if (!token) return;

    setSaving(true);
    try {
      await fetch(`${apiUrl}/api/v1/admin/recruit/${params.id}/status`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ status }),
      });
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

  if (!data) {
    return <div className="p-6 text-neutral-400">Loading...</div>;
  }

  const app = data.application;
  const availability = data.availability;
  const profile = data.profiles?.[0];
  const review = data.review;

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">
          {app.first_name} {app.last_name}
        </h1>
        <p className="text-neutral-400">{app.email}</p>
        <p className="text-neutral-400">{app.discord}</p>
      </div>

      <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
        <h2 className="text-lg font-medium">
          {isSmashProfile ? "Smash Scouting Profile" : "Game Profile"}
        </h2>

        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div className="space-y-2 text-sm">
            <p>IGN / BattleTag: {profile?.ign || "N/A"}</p>
            <p>Current Rank: {profile?.current_rank_label || "N/A"}</p>
            <p>Peak Rank: {profile?.peak_rank_label || "N/A"}</p>
            <p>Primary Role / Main Focus: {profile?.primary_role || "N/A"}</p>
            <p>Secondary Role / Extra Info: {profile?.secondary_role || "N/A"}</p>
            <p>Tournament Experience: {profile?.tournament_experience || "N/A"}</p>
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
            <p className="mt-2 text-sm text-neutral-400">
              Scoring Method: <span className="text-white">{ranking?.scoring_method || "N/A"}</span>
            </p>
            <p className="mt-1 text-sm text-neutral-400">
              Model/Version: <span className="text-white">{ranking?.model_version || "N/A"}</span>
            </p>
            <p className="mt-1 text-sm text-neutral-400">
              Scored At:{" "}
              <span className="text-white">
                {ranking?.scored_at ? new Date(ranking.scored_at).toLocaleString() : "N/A"}
              </span>
            </p>
            <p className="mt-3 text-sm text-neutral-400">
              Status: <span className="text-white">{review?.status || "NEW"}</span>
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
              onChange={(e) => setStatus(e.target.value)}
            >
              <option value="NEW">NEW</option>
              <option value="REVIEWED">REVIEWED</option>
              <option value="CONTACTED">CONTACTED</option>
              <option value="TRYOUT">TRYOUT</option>
              <option value="ACCEPTED">ACCEPTED</option>
              <option value="REJECTED">REJECTED</option>
            </select>
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
