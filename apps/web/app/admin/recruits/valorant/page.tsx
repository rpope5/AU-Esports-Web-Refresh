"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

type Recruit = {
  application_id: number;
  first_name: string;
  last_name: string;
  email: string;
  discord: string;
  graduation_year: number | null;
  current_school: string | null;
  ign: string;
  current_rank_label: string;
  primary_role: string;
  secondary_role: string | null;
  tracker_url: string | null;
  score: number | null;
  status: string;
};

export default function ValorantRecruitListPage() {
  const router = useRouter();
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const [recruits, setRecruits] = useState<Recruit[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("au_admin_token");
    if (!token) {
      router.push("/admin/login");
      return;
    }

    (async () => {
      const res = await fetch(`${apiUrl}/api/v1/admin/recruits/game/valorant`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (res.status === 401 || res.status === 403) {
        localStorage.removeItem("au_admin_token");
        router.push("/admin/login");
        return;
      }

      if (!res.ok) {
        const text = await res.text();
        console.error("Failed to load recruits:", res.status, text);
        setLoading(false);
        return;
      }

      const data = await res.json();
      setRecruits(data);
      setLoading(false);
    })();
  }, [apiUrl, router]);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold">Valorant Recruits</h1>

      {loading ? (
        <p className="mt-4 text-neutral-400">Loading...</p>
      ) : recruits.length === 0 ? (
        <p className="mt-4 text-neutral-400">No recruits yet.</p>
      ) : (
        <div className="mt-6 grid gap-4">
          {recruits.map((r) => (
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
                    {r.ign} • {r.current_rank_label} • {r.primary_role}
                    {r.secondary_role ? ` / ${r.secondary_role}` : ""}
                  </p>
                  <p className="mt-1 text-sm text-neutral-500">
                    {r.current_school || "Unknown school"} • Class of{" "}
                    {r.graduation_year ?? "N/A"}
                  </p>
                </div>

                <div className="text-right">
                  <div className="text-sm text-neutral-400">Score</div>
                  <div className="text-2xl font-semibold">
                    {r.score ?? "--"}
                  </div>
                  <div className="mt-1 text-xs uppercase tracking-wide text-neutral-500">
                    {r.status}
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}