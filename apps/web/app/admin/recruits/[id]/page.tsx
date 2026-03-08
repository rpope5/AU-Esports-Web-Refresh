"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

export default function RecruitDetailPage() {
  const params = useParams();
  const router = useRouter();
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const [data, setData] = useState<any>(null);

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

      setData(await res.json());
    })();
  }, [apiUrl, params.id, router]);

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
    </div>
  );
}