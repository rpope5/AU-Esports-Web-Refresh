"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { clearAdminStorage } from "../_lib/session";

export default function AdminLoginPage() {
  const router = useRouter();
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setLoading(true);

    try {
      const res = await fetch(`${apiUrl}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username,
          password,
        }),
      });

      if (!res.ok) throw new Error(await res.text());

      const data = await res.json();
      clearAdminStorage();
      localStorage.setItem("au_admin_token", data.access_token);
      localStorage.setItem("au_admin_role", data.role);
      localStorage.setItem("au_admin_username", data.username);

      router.push("/admin");
    } catch (err: unknown) {
      setErr(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-md rounded-2xl border border-neutral-800 bg-neutral-950 p-6">
        <h1 className="text-2xl font-semibold">Admin Login</h1>

        <form className="mt-6 space-y-4" onSubmit={onSubmit}>
          <div>
            <label className="text-sm text-neutral-300">Username</label>
            <input
              className="mt-1 w-full rounded-lg bg-neutral-900 border border-neutral-800 p-2"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
            />
          </div>

          <div>
            <label className="text-sm text-neutral-300">Password</label>
            <input
              className="mt-1 w-full rounded-lg bg-neutral-900 border border-neutral-800 p-2"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </div>

          <button
            className="w-full rounded-lg bg-white text-black py-2 font-medium disabled:opacity-60"
            disabled={loading}
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>

          {err && (
            <p className="text-sm text-red-400 whitespace-pre-wrap">{err}</p>
          )}
        </form>
      </div>
    </div>
  );
}
