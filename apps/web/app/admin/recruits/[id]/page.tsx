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
        <h2 className="text-lg font-medium">Valorant Profile</h2>
        <div className="mt-3 space-y-2 text-sm">
          <p>IGN: {profile?.ign}</p>
          <p>Current Rank: {profile?.current_rank_label}</p>
          <p>Peak Rank: {profile?.peak_rank_label || "N/A"}</p>
          <p>Primary Role: {profile?.primary_role}</p>
          <p>Secondary Role: {profile?.secondary_role || "N/A"}</p>
          <p>Tournament Experience: {profile?.tournament_experience}</p>
          <p>Tracker: {profile?.tracker_url || "N/A"}</p>
        </div>
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
        <h2 className="text-lg font-medium">Ranking</h2>
        <div className="mt-3 space-y-2 text-sm">
          <p>Score: {ranking?.score ?? "N/A"}</p>
          <pre className="mt-3 overflow-x-auto rounded-lg bg-black/30 p-3 text-xs">
            {JSON.stringify(ranking?.explanation_json, null, 2)}
          </pre>
          <p>Status: {review?.status}</p>
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