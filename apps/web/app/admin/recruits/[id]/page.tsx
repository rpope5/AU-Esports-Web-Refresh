"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

export default function RecruitDetailPage() {
  const params = useParams();
  const router = useRouter();
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const [data, setData] = useState<any>(null);
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
      const res = await fetch(
        `${apiUrl}/api/v1/admin/recruit/${params.id}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

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

  if (!data) {
    return <div className="p-6 text-neutral-400">Loading...</div>;
  }

  const app = data.application;
  const availability = data.availability;
  const profile = data.profiles?.[0];
  const ranking = data.rankings?.[0];
  const review = data.review;

  const characterList =
    profile?.characters
      ? profile.characters.split(",").map((c: string) => c.trim()).filter(Boolean)
      : [];

  const bestWinsList =
    profile?.best_wins
      ? profile.best_wins.split(",").map((w: string) => w.trim()).filter(Boolean)
      : [];

  const isSmashProfile =
    profile?.gsp != null ||
    !!profile?.regional_rank ||
    !!profile?.best_wins ||
    !!profile?.characters;

  const extraFields = [
    profile?.ranked_wins != null
      ? { label: "Ranked Wins", value: profile.ranked_wins }
      : null,
    profile?.years_played != null
      ? { label: "Years Played", value: profile.years_played }
      : null,
    profile?.legend_peak_rank != null
      ? { label: "Legend Peak Rank", value: profile.legend_peak_rank }
      : null,
    profile?.preferred_format
      ? { label: "Preferred Format", value: profile.preferred_format }
      : null,
    profile?.other_card_games
      ? { label: "Other Card Games", value: profile.other_card_games }
      : null,

  ].filter(
    (field): field is { label: string; value: string | number } => field !== null
  );

  

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
                <a
                  href={profile.tracker_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-blue-400 underline"
                >
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
            {profile?.legend_peak_rank != null && (
              <p>Legend Peak Rank: {profile.legend_peak_rank}</p>
            )}
            {profile?.preferred_format && (
              <p>Preferred Format: {profile.preferred_format}</p>
            )}
            {profile?.other_card_games && (
              <p>Other Card Games: {profile.other_card_games}</p>
            )}
          </div>
          {profile?.lounge_rating != null && <p>Lounge Rating: {profile.lounge_rating}</p>}
          {profile?.preferred_title && <p>Preferred Title: {profile.preferred_title}</p>}
          {profile?.controller_type && <p>Controller Type: {profile.controller_type}</p>}
          {profile?.playstyle && <p>Playstyle: {profile.playstyle}</p>}
          {profile?.preferred_tracks && <p>Preferred Tracks / Notes: {profile.preferred_tracks}</p>}
        </div>

        {characterList.length > 0 && (
          <div className="mt-6">
            <h3 className="text-sm font-medium text-neutral-300">Characters Played</h3>
            <div className="mt-2 flex flex-wrap gap-2">
              {characterList.map((char: string) => (
                <span
                  key={char}
                  className="rounded-full border border-neutral-700 bg-neutral-900 px-3 py-1 text-xs"
                >
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
                <span
                  key={win}
                  className="rounded-full border border-neutral-700 bg-neutral-900 px-3 py-1 text-xs"
                >
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
            <p className="mt-3 text-sm text-neutral-400">
              Status: <span className="text-white">{review?.status || "NEW"}</span>
            </p>
          </div>

          <div>
            <p className="text-sm text-neutral-400">Scoring Breakdown</p>
            <pre className="mt-2 overflow-x-auto rounded-lg bg-black/30 p-3 text-xs">
              {JSON.stringify(ranking?.explanation_json, null, 2)}
            </pre>
          </div>
        </div>
      </div>

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
      <button
        onClick={saveStatus}
        className="mt-2 rounded-lg bg-white px-4 py-2 text-black"
        disabled={saving}
      >
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
      <button
        onClick={saveNotes}
        className="mt-2 rounded-lg bg-white px-4 py-2 text-black"
        disabled={saving}
      >
        Save Notes
      </button>
    </div>
  </div>
</div>
    </div>
  );
}

