"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { clearAdminStorage, formatRoleLabel, parseAdminSession, type AdminSession } from "../_lib/session";

type ScheduleStatus = "pending" | "published" | "rejected" | "archived";
type CreateWorkflowAction = "publish" | "submit_for_approval";
type TransitionAction = "submit" | "approve" | "reject" | "archive";

type CalendarEvent = {
  id: number;
  name: string;
  time: string;
  game_slug: string | null;
  game_name: string | null;
  status: ScheduleStatus;
  created_by_username: string | null;
  approved_by_username: string | null;
  rejected_by_username: string | null;
  submitted_at: string | null;
  approved_at: string | null;
  rejected_at: string | null;
  archived_at: string | null;
};

type GameOption = { slug: string; name: string };
const ALL_GAME_OPTIONS: GameOption[] = [
  { slug: "valorant", name: "Valorant" },
  { slug: "cs2", name: "Counter-Strike 2" },
  { slug: "fortnite", name: "Fortnite" },
  { slug: "r6", name: "Rainbow Six Siege" },
  { slug: "rocket-league", name: "Rocket League" },
  { slug: "overwatch", name: "Overwatch" },
  { slug: "cod", name: "Call of Duty" },
  { slug: "hearthstone", name: "Hearthstone" },
  { slug: "smash", name: "Super Smash Bros. Ultimate" },
  { slug: "mario-kart", name: "Mario Kart" },
];

function formatDate(raw: string | null | undefined): string {
  if (!raw) return "N/A";
  const hasTimezone = /[zZ]$|[+-]\d{2}:\d{2}$/.test(raw);
  const parsed = new Date(hasTimezone ? raw : `${raw}Z`);
  if (Number.isNaN(parsed.getTime())) return "N/A";
  return parsed.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

function statusClass(status: ScheduleStatus): string {
  if (status === "pending") return "border-amber-700/70 bg-amber-950/30 text-amber-200";
  if (status === "published") return "border-emerald-700/70 bg-emerald-950/30 text-emerald-200";
  if (status === "rejected") return "border-red-700/70 bg-red-950/30 text-red-200";
  return "border-neutral-700 bg-neutral-900 text-neutral-300";
}

function statusLabel(status: ScheduleStatus): string {
  if (status === "pending") return "Pending Approval";
  if (status === "published") return "Published";
  if (status === "rejected") return "Rejected";
  return "Archived";
}

function toLocalInputValue(raw: string): string {
  const hasTimezone = /[zZ]$|[+-]\d{2}:\d{2}$/.test(raw);
  const parsed = new Date(hasTimezone ? raw : `${raw}Z`);
  if (Number.isNaN(parsed.getTime())) return "";
  const year = parsed.getFullYear();
  const month = String(parsed.getMonth() + 1).padStart(2, "0");
  const day = String(parsed.getDate()).padStart(2, "0");
  const hour = String(parsed.getHours()).padStart(2, "0");
  const minute = String(parsed.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day}T${hour}:${minute}`;
}

function canPublish(session: AdminSession | null): boolean {
  return session?.role === "coach" || session?.role === "head_coach" || session?.role === "admin";
}

export default function AdminSchedulePage() {
  const router = useRouter();
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const [session, setSession] = useState<AdminSession | null>(null);
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [statusFilter, setStatusFilter] = useState<"all" | ScheduleStatus>("all");
  const [name, setName] = useState("");
  const [time, setTime] = useState("");
  const [gameSlug, setGameSlug] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [creating, setCreating] = useState(false);

  const canManageSchedule = Boolean(session?.permissions.can_manage_schedule);
  const canDeleteSchedule = Boolean(session?.permissions.can_delete_schedule);

  const availableGames = useMemo(() => {
    if (!session) return [];
    if (session.has_global_game_access) return ALL_GAME_OPTIONS;
    return ALL_GAME_OPTIONS.filter((game) => session.allowed_game_slugs.includes(game.slug));
  }, [session]);

  useEffect(() => {
    if (!gameSlug && availableGames.length > 0) {
      setGameSlug(availableGames[0].slug);
    }
  }, [availableGames, gameSlug]);

  const clearSessionAndRedirect = useCallback(() => {
    clearAdminStorage();
    router.push("/admin/login");
  }, [router]);

  const getToken = useCallback(() => {
    const token = localStorage.getItem("au_admin_token");
    if (!token) router.push("/admin/login");
    return token;
  }, [router]);

  const loadEvents = useCallback(async () => {
    if (!canManageSchedule) {
      setLoading(false);
      return;
    }

    const token = getToken();
    if (!token) return;

    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ limit: "500" });
      if (statusFilter !== "all") params.set("status", statusFilter);

      const response = await fetch(`${apiUrl}/api/v1/admin/schedule/events?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.status === 401) {
        clearSessionAndRedirect();
        return;
      }
      if (response.status === 403) {
        setEvents([]);
        setError("You do not have permission to manage schedule items.");
        return;
      }
      if (!response.ok) throw new Error((await response.text()) || "Failed to load schedule items");

      const data = (await response.json()) as CalendarEvent[];
      setEvents(Array.isArray(data) ? data : []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load schedule items");
    } finally {
      setLoading(false);
    }
  }, [apiUrl, canManageSchedule, clearSessionAndRedirect, getToken, statusFilter]);

  useEffect(() => {
    const token = localStorage.getItem("au_admin_token");
    if (!token) {
      router.push("/admin/login");
      return;
    }

    const init = async () => {
      try {
        const response = await fetch(`${apiUrl}/api/v1/admin/whoami`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (response.status === 401) {
          clearSessionAndRedirect();
          return;
        }
        if (!response.ok) throw new Error(await response.text());
        setSession(parseAdminSession(await response.json()));
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to initialize session");
      }
    };

    void init();
  }, [apiUrl, clearSessionAndRedirect, router]);

  useEffect(() => {
    void loadEvents();
  }, [loadEvents]);

  async function createScheduleItem(action: CreateWorkflowAction): Promise<void> {
    const token = getToken();
    if (!token) return;
    setError(null);
    setSuccess(null);

    if (!name.trim() || !time || !gameSlug) {
      setError("Name, date/time, and game are required.");
      return;
    }
    if (session?.role === "captain" && action === "publish") {
      setError("Captains can only submit schedule items for approval.");
      return;
    }

    setCreating(true);
    try {
      const response = await fetch(`${apiUrl}/api/v1/admin/schedule/events`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name.trim(),
          time: new Date(time).toISOString(),
          game_slug: gameSlug,
          workflow_action: action,
        }),
      });
      if (response.status === 401) {
        clearSessionAndRedirect();
        return;
      }
      if (!response.ok) throw new Error((await response.text()) || "Failed to create schedule item");

      setName("");
      setTime("");
      setSuccess(action === "publish" ? "Schedule item published." : "Schedule item submitted for approval.");
      await loadEvents();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create schedule item");
    } finally {
      setCreating(false);
    }
  }

  async function transition(eventId: number, action: TransitionAction): Promise<void> {
    const token = getToken();
    if (!token) return;
    setBusyId(eventId);
    setError(null);
    setSuccess(null);
    try {
      const route =
        action === "submit"
          ? `${apiUrl}/api/v1/admin/schedule/events/${eventId}/submit`
          : action === "approve"
            ? `${apiUrl}/api/v1/admin/schedule/events/${eventId}/approve`
            : action === "reject"
              ? `${apiUrl}/api/v1/admin/schedule/events/${eventId}/reject`
              : `${apiUrl}/api/v1/admin/schedule/events/${eventId}/archive`;

      const response = await fetch(route, { method: "POST", headers: { Authorization: `Bearer ${token}` } });
      if (response.status === 401) {
        clearSessionAndRedirect();
        return;
      }
      if (!response.ok) throw new Error((await response.text()) || "Failed to change schedule state");

      setSuccess("Schedule item updated.");
      await loadEvents();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to change schedule state");
    } finally {
      setBusyId(null);
    }
  }

  async function editEvent(item: CalendarEvent): Promise<void> {
    const token = getToken();
    if (!token) return;

    const nextName = window.prompt("Schedule item name", item.name);
    if (nextName === null) return;
    const nextTimeInput = window.prompt(
      "Date/time (local, YYYY-MM-DDTHH:mm)",
      toLocalInputValue(item.time),
    );
    if (nextTimeInput === null) return;
    const nextGameSlug = window.prompt("Game slug", item.game_slug || gameSlug);
    if (nextGameSlug === null) return;

    const cleanName = nextName.trim();
    const cleanGameSlug = nextGameSlug.trim();
    if (!cleanName || !nextTimeInput.trim() || !cleanGameSlug) {
      setError("Name, date/time, and game slug are required for edits.");
      return;
    }

    const parsed = new Date(nextTimeInput.trim());
    if (Number.isNaN(parsed.getTime())) {
      setError("Invalid date/time format.");
      return;
    }

    setBusyId(item.id);
    setError(null);
    setSuccess(null);
    try {
      const response = await fetch(`${apiUrl}/api/v1/admin/schedule/events/${item.id}`, {
        method: "PATCH",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({
          name: cleanName,
          time: parsed.toISOString(),
          game_slug: cleanGameSlug,
        }),
      });
      if (response.status === 401) {
        clearSessionAndRedirect();
        return;
      }
      if (!response.ok) throw new Error((await response.text()) || "Failed to edit schedule item");
      setSuccess("Schedule item updated.");
      await loadEvents();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to edit schedule item");
    } finally {
      setBusyId(null);
    }
  }

  async function removeEvent(eventId: number): Promise<void> {
    const token = getToken();
    if (!token) return;
    if (!window.confirm("Delete this schedule item permanently?")) return;
    setBusyId(eventId);
    try {
      const response = await fetch(`${apiUrl}/api/v1/admin/schedule/events/${eventId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.status === 401) {
        clearSessionAndRedirect();
        return;
      }
      if (response.status !== 204) throw new Error((await response.text()) || "Failed to delete schedule item");
      setSuccess("Schedule item deleted.");
      await loadEvents();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to delete schedule item");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Schedule Workflow Admin</h1>
          <p className="mt-1 text-sm text-neutral-400">
            {session ? `Signed in as ${session.username} - ${formatRoleLabel(session.role)}` : "Loading session..."}
          </p>
        </div>
        <Link href="/admin" className="rounded-lg border border-neutral-800 bg-neutral-950 px-4 py-2 text-sm hover:border-neutral-700">
          Back to Admin
        </Link>
      </div>

      {canManageSchedule && (
        <section className="mt-6 rounded-2xl border border-neutral-800 bg-neutral-950 p-5">
          <h2 className="text-xl font-medium">Submit Schedule Item</h2>
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <input className="rounded border border-neutral-700 bg-black p-2 text-sm" placeholder="Name" value={name} onChange={(event) => setName(event.target.value)} />
            <input className="rounded border border-neutral-700 bg-black p-2 text-sm" type="datetime-local" value={time} onChange={(event) => setTime(event.target.value)} />
            <select className="rounded border border-neutral-700 bg-black p-2 text-sm" value={gameSlug} onChange={(event) => setGameSlug(event.target.value)}>
              {availableGames.map((game) => (
                <option key={game.slug} value={game.slug}>{game.name}</option>
              ))}
            </select>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {canPublish(session) && (
              <button className="rounded border border-emerald-700/80 bg-emerald-950/30 px-3 py-1 text-sm text-emerald-100 disabled:opacity-60" disabled={creating} onClick={() => void createScheduleItem("publish")}>
                {creating ? "Publishing..." : "Publish"}
              </button>
            )}
            <button className="rounded border border-amber-700/80 bg-amber-950/30 px-3 py-1 text-sm text-amber-100 disabled:opacity-60" disabled={creating} onClick={() => void createScheduleItem("submit_for_approval")}>
              {creating ? "Submitting..." : "Submit for Approval"}
            </button>
            <select className="rounded border border-neutral-700 bg-black px-2 py-1 text-sm" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as "all" | ScheduleStatus)}>
              <option value="all">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="published">Published</option>
              <option value="rejected">Rejected</option>
              <option value="archived">Archived</option>
            </select>
          </div>
        </section>
      )}

      {error && <p className="mt-4 text-sm text-red-400">{error}</p>}
      {success && <p className="mt-4 text-sm text-emerald-400">{success}</p>}

      <section className="mt-6 rounded-2xl border border-neutral-800 bg-neutral-950 p-5">
        <h2 className="text-xl font-medium">Schedule Items</h2>
        {loading ? (
          <p className="mt-4 text-sm text-neutral-400">Loading schedule items...</p>
        ) : (
          <div className="mt-4 grid gap-3">
            {events.map((item) => {
              const busy = busyId === item.id;
              const canSubmit = session?.role === "captain" && item.created_by_username === session.username && item.status === "pending";
              const canEdit =
                (session?.role === "coach" || session?.role === "head_coach" || session?.role === "admin") ||
                (session?.role === "captain" && item.created_by_username === session.username && item.status === "pending");
              const canApprove = canPublish(session) && item.status !== "published";
              const canReject = canPublish(session) && item.status === "pending";
              const canArchive = canPublish(session) && item.status === "published";
              return (
                <article key={item.id} className="rounded-xl border border-neutral-800 bg-black/60 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h3 className="text-lg font-semibold">{item.name}</h3>
                      <p className="text-sm text-neutral-400">{formatDate(item.time)} | {item.game_name || item.game_slug || "Unknown game"}</p>
                      <div className="mt-2 flex flex-wrap gap-2 text-xs">
                        <span className={`rounded-full border px-2 py-0.5 ${statusClass(item.status)}`}>{statusLabel(item.status)}</span>
                        <span className="rounded-full border border-neutral-700 px-2 py-0.5 text-neutral-300">Created by: {item.created_by_username || "Unknown"}</span>
                        {item.approved_by_username && <span className="rounded-full border border-neutral-700 px-2 py-0.5 text-neutral-300">Approved by: {item.approved_by_username}</span>}
                        {item.rejected_by_username && <span className="rounded-full border border-neutral-700 px-2 py-0.5 text-neutral-300">Rejected by: {item.rejected_by_username}</span>}
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {canEdit && <button className="rounded border border-neutral-700 bg-neutral-900 px-2 py-1 text-xs text-neutral-100 disabled:opacity-60" disabled={busy} onClick={() => void editEvent(item)}>{busy ? "Working..." : "Edit"}</button>}
                      {canSubmit && <button className="rounded border border-amber-700/80 bg-amber-950/30 px-2 py-1 text-xs text-amber-100 disabled:opacity-60" disabled={busy} onClick={() => void transition(item.id, "submit")}>{busy ? "Working..." : "Submit"}</button>}
                      {canApprove && <button className="rounded border border-emerald-700/80 bg-emerald-950/30 px-2 py-1 text-xs text-emerald-100 disabled:opacity-60" disabled={busy} onClick={() => void transition(item.id, "approve")}>{busy ? "Working..." : "Approve"}</button>}
                      {canReject && <button className="rounded border border-red-700/80 bg-red-950/30 px-2 py-1 text-xs text-red-100 disabled:opacity-60" disabled={busy} onClick={() => void transition(item.id, "reject")}>{busy ? "Working..." : "Reject"}</button>}
                      {canArchive && <button className="rounded border border-neutral-700 bg-neutral-900 px-2 py-1 text-xs text-neutral-100 disabled:opacity-60" disabled={busy} onClick={() => void transition(item.id, "archive")}>{busy ? "Working..." : "Archive"}</button>}
                      {canDeleteSchedule && <button className="rounded border border-red-700 px-2 py-1 text-xs text-red-300 disabled:opacity-60" disabled={busy} onClick={() => void removeEvent(item.id)}>{busy ? "Working..." : "Delete"}</button>}
                    </div>
                  </div>
                </article>
              );
            })}
            {!events.length && <p className="text-sm text-neutral-400">No schedule items found for this filter.</p>}
          </div>
        )}
      </section>
    </div>
  );
}
