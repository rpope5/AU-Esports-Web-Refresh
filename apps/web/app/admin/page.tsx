"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function AdminHome() {
  const router = useRouter();
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const [me, setMe] = useState<any>(null);

  useEffect(() => {
    const token = localStorage.getItem("au_admin_token");
    if (!token) {
      router.push("/admin/login");
      return;
    }

    (async () => {
      const res = await fetch(`${apiUrl}/api/v1/admin/whoami`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        localStorage.removeItem("au_admin_token");
        router.push("/admin/login");
        return;
      }

      setMe(await res.json());
    })();
  }, [apiUrl, router]);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold">Admin Portal</h1>
      {me ? (
        <div className="mt-4 rounded-xl border border-neutral-800 bg-neutral-950 p-4">
          <div className="text-sm text-neutral-400">Signed in as</div>
          <div className="mt-1 font-mono">{me.email || me.username}</div>
          <div className="mt-1 text-sm">Role: {me.role}</div>
        </div>
      ) : (
        <p className="mt-4 text-neutral-400">Loading...</p>
      )}
    </div>
  );
}