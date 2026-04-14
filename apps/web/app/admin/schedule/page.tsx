"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

type CalendarEvent = {
  id: number;
  name: string;
  time: string;
  game: string | null;
  created_at: string;
  updated_at: string;
};

type AdminUser = {
  username: string;
  role: string;
};

function startOfMonth(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), 1);
}

function endOfMonth(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth() + 1, 0, 23, 59, 59, 999);
}

function startOfWeek(date: Date): Date {
  const copy = new Date(date);
  copy.setDate(copy.getDate() - copy.getDay());
  copy.setHours(0, 0, 0, 0);
  return copy;
}

function endOfWeek(date: Date): Date {
  const copy = new Date(date);
  copy.setDate(copy.getDate() + (6 - copy.getDay()));
  copy.setHours(23, 59, 59, 999);
  return copy;
}

function parseBackendTimestamp(rawValue: string): Date | null {
  const trimmed = rawValue?.trim();
  if (!trimmed) return null;
  const hasTimezone = /[zZ]$|[+-]\d{2}:\d{2}$/.test(trimmed);
  const normalized = hasTimezone ? trimmed : `${trimmed}Z`;
  const parsed = new Date(normalized);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function dateKey(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function formatEventTime(rawValue: string): string {
  const parsed = parseBackendTimestamp(rawValue);
  if (!parsed) return rawValue;
  return parsed.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function toDateTimeLocalValue(rawValue: string): string {
  const parsed = parseBackendTimestamp(rawValue);
  if (!parsed) return "";

  const year = parsed.getFullYear();
  const month = String(parsed.getMonth() + 1).padStart(2, "0");
  const day = String(parsed.getDate()).padStart(2, "0");
  const hour = String(parsed.getHours()).padStart(2, "0");
  const minute = String(parsed.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day}T${hour}:${minute}`;
}

function localInputToIso(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    throw new Error("Please provide a valid date and time.");
  }
  return parsed.toISOString();
}

export default function AdminSchedulePage() {
  const router = useRouter();
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const [me, setMe] = useState<AdminUser | null>(null);
  const [isSessionReady, setIsSessionReady] = useState(false);
  const [currentMonth, setCurrentMonth] = useState(() => startOfMonth(new Date()));
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loadingEvents, setLoadingEvents] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [activeEvent, setActiveEvent] = useState<CalendarEvent | null>(null);

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createName, setCreateName] = useState("");
  const [createTime, setCreateTime] = useState("");
  const [createGame, setCreateGame] = useState("");
  const [creating, setCreating] = useState(false);

  const [isEditingEvent, setIsEditingEvent] = useState(false);
  const [editName, setEditName] = useState("");
  const [editTime, setEditTime] = useState("");
  const [editGame, setEditGame] = useState("");
  const [updating, setUpdating] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const clearSessionAndRedirect = useCallback(() => {
    localStorage.removeItem("au_admin_token");
    localStorage.removeItem("au_admin_role");
    localStorage.removeItem("au_admin_username");
    router.push("/admin/login");
  }, [router]);

  const getAdminToken = useCallback((): string | null => {
    const token = localStorage.getItem("au_admin_token");
    if (!token) {
      router.push("/admin/login");
      return null;
    }
    return token;
  }, [router]);

  const loadEvents = useCallback(async () => {
    if (!isSessionReady) return;
    const token = getAdminToken();
    if (!token) return;

    setLoadingEvents(true);
    setError(null);
    try {
      const monthStart = startOfMonth(currentMonth);
      const monthEnd = endOfMonth(currentMonth);
      const params = new URLSearchParams({
        start: monthStart.toISOString(),
        end: monthEnd.toISOString(),
      });

      const response = await fetch(`${apiUrl}/api/v1/admin/schedule/events?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.status === 401 || response.status === 403) {
        clearSessionAndRedirect();
        return;
      }

      if (!response.ok) {
        const body = await response.text();
        throw new Error(body || "Failed to load schedule events");
      }

      const data = (await response.json()) as CalendarEvent[];
      setEvents(Array.isArray(data) ? data : []);
    } catch (err: unknown) {
      setEvents([]);
      setError(err instanceof Error ? err.message : "Failed to load schedule events");
    } finally {
      setLoadingEvents(false);
    }
  }, [apiUrl, clearSessionAndRedirect, currentMonth, getAdminToken, isSessionReady]);

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
        if (!response.ok) {
          clearSessionAndRedirect();
          return;
        }
        const data = (await response.json()) as AdminUser;
        setMe(data);
        setIsSessionReady(true);
      } catch {
        clearSessionAndRedirect();
      }
    };

    void init();
  }, [apiUrl, clearSessionAndRedirect, router]);

  useEffect(() => {
    void loadEvents();
  }, [loadEvents]);

  useEffect(() => {
    if (!activeEvent) return;
    setIsEditingEvent(false);
    setEditName(activeEvent.name);
    setEditTime(toDateTimeLocalValue(activeEvent.time));
    setEditGame(activeEvent.game ?? "");
  }, [activeEvent]);

  const eventsByDay = useMemo(() => {
    const map = new Map<string, CalendarEvent[]>();
    for (const event of events) {
      const parsed = parseBackendTimestamp(event.time);
      if (!parsed) continue;
      const key = dateKey(parsed);
      const bucket = map.get(key) || [];
      bucket.push(event);
      map.set(key, bucket);
    }

    for (const [, bucket] of map) {
      bucket.sort((a, b) => {
        const aTime = parseBackendTimestamp(a.time)?.getTime() ?? 0;
        const bTime = parseBackendTimestamp(b.time)?.getTime() ?? 0;
        return aTime - bTime;
      });
    }

    return map;
  }, [events]);

  const monthLabel = useMemo(
    () =>
      currentMonth.toLocaleString(undefined, {
        month: "long",
        year: "numeric",
      }),
    [currentMonth],
  );

  const calendarDays = useMemo(() => {
    const first = startOfWeek(startOfMonth(currentMonth));
    const last = endOfWeek(endOfMonth(currentMonth));
    const days: Date[] = [];
    const cursor = new Date(first);
    while (cursor <= last) {
      days.push(new Date(cursor));
      cursor.setDate(cursor.getDate() + 1);
    }
    return days;
  }, [currentMonth]);

  async function handleCreateEvent(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSuccess(null);

    const token = getAdminToken();
    if (!token) return;

    const cleanName = createName.trim();
    if (!cleanName) {
      setError("Event name is required.");
      return;
    }

    setCreating(true);
    try {
      const response = await fetch(`${apiUrl}/api/v1/admin/schedule/events`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: cleanName,
          time: localInputToIso(createTime),
          game: createGame.trim() ? createGame.trim() : null,
        }),
      });

      if (response.status === 401 || response.status === 403) {
        clearSessionAndRedirect();
        return;
      }

      if (!response.ok) {
        const body = await response.text();
        throw new Error(body || "Failed to create event");
      }

      setShowCreateModal(false);
      setCreateName("");
      setCreateTime("");
      setCreateGame("");
      setSuccess("Event created.");
      await loadEvents();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create event");
    } finally {
      setCreating(false);
    }
  }

  async function handleUpdateEvent() {
    if (!activeEvent) return;

    setError(null);
    setSuccess(null);
    const token = getAdminToken();
    if (!token) return;

    const cleanName = editName.trim();
    if (!cleanName) {
      setError("Event name is required.");
      return;
    }

    setUpdating(true);
    try {
      const response = await fetch(`${apiUrl}/api/v1/admin/schedule/events/${activeEvent.id}`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: cleanName,
          time: localInputToIso(editTime),
          game: editGame.trim() ? editGame.trim() : null,
        }),
      });

      if (response.status === 401 || response.status === 403) {
        clearSessionAndRedirect();
        return;
      }

      if (!response.ok) {
        const body = await response.text();
        throw new Error(body || "Failed to update event");
      }

      const updated = (await response.json()) as CalendarEvent;
      setActiveEvent(updated);
      setIsEditingEvent(false);
      setSuccess("Event updated.");
      await loadEvents();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update event");
    } finally {
      setUpdating(false);
    }
  }

  async function handleDeleteEvent() {
    if (!activeEvent) return;

    const shouldDelete = window.confirm("Delete this event permanently?");
    if (!shouldDelete) return;

    setError(null);
    setSuccess(null);
    const token = getAdminToken();
    if (!token) return;

    setDeleting(true);
    try {
      const response = await fetch(`${apiUrl}/api/v1/admin/schedule/events/${activeEvent.id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.status === 401 || response.status === 403) {
        clearSessionAndRedirect();
        return;
      }

      if (response.status !== 204) {
        const body = await response.text();
        throw new Error(body || "Failed to delete event");
      }

      setActiveEvent(null);
      setIsEditingEvent(false);
      setSuccess("Event deleted.");
      await loadEvents();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to delete event");
    } finally {
      setDeleting(false);
    }
  }

  const prevMonth = () =>
    setCurrentMonth((prev) => new Date(prev.getFullYear(), prev.getMonth() - 1, 1));
  const nextMonth = () =>
    setCurrentMonth((prev) => new Date(prev.getFullYear(), prev.getMonth() + 1, 1));

  return (
    <div className="p-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Schedule Calendar Admin</h1>
          <p className="mt-1 text-sm text-neutral-400">
            {me ? `Signed in as ${me.username} - ${me.role}` : "Loading session..."}
          </p>
        </div>
        <Link
          href="/admin"
          className="rounded-lg border border-neutral-800 bg-neutral-950 px-4 py-2 text-sm hover:border-neutral-700"
        >
          Back to Admin
        </Link>
      </div>

      <section className="mx-auto mt-6 w-full max-w-7xl rounded-lg border border-[#FFC72C]/40 bg-[#111111] p-4 md:p-6">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <button
            type="button"
            onClick={prevMonth}
            className="rounded border border-[#FFC72C]/60 px-3 py-1 text-sm text-[#FFC72C] transition hover:bg-[#FFC72C]/10"
            aria-label="Previous month"
          >
            Prev
          </button>

          <h2 className="text-xl font-semibold text-white">{monthLabel}</h2>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={nextMonth}
              className="rounded border border-[#FFC72C]/60 px-3 py-1 text-sm text-[#FFC72C] transition hover:bg-[#FFC72C]/10"
              aria-label="Next month"
            >
              Next
            </button>
            <button
              type="button"
              onClick={() => {
                setShowCreateModal(true);
                setActiveEvent(null);
                setCreateName("");
                setCreateTime("");
                setCreateGame("");
              }}
              className="rounded border border-[#FFC72C] bg-[#5C068C]/80 px-3 py-1 text-sm font-medium text-white transition hover:bg-[#5C068C]"
            >
              Create Event
            </button>
          </div>
        </div>

        <div className="mb-2 grid grid-cols-7 gap-1 text-center text-xs font-semibold uppercase tracking-wide text-[#FFC72C]/90 md:text-sm">
          {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
            <div key={day} className="py-2">
              {day}
            </div>
          ))}
        </div>

        {loadingEvents ? (
          <div className="rounded border border-dashed border-[#FFC72C]/30 py-10 text-center text-sm text-gray-300">
            Loading calendar...
          </div>
        ) : (
          <div className="grid grid-cols-7 gap-1">
            {calendarDays.map((day) => {
              const inMonth = day.getMonth() === currentMonth.getMonth();
              const dayEvents = eventsByDay.get(dateKey(day)) || [];
              return (
                <div
                  key={day.toISOString()}
                  className={`min-h-[7.5rem] rounded border p-2 ${
                    inMonth
                      ? "border-[#FFC72C]/20 bg-black"
                      : "border-[#5C068C]/20 bg-black/60 text-gray-500"
                  }`}
                >
                  <div className="mb-2 text-xs font-semibold text-[#FFC72C] md:text-sm">{day.getDate()}</div>
                  <div className="space-y-1">
                    {dayEvents.map((event) => (
                      <button
                        key={event.id}
                        type="button"
                        onClick={() => setActiveEvent(event)}
                        className="block w-full truncate rounded bg-[#5C068C]/70 px-2 py-1 text-left text-xs text-white transition hover:bg-[#5C068C] focus:outline-none focus:ring-2 focus:ring-[#FFC72C]"
                        title={event.name}
                      >
                        {event.name}
                      </button>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {error && <p className="mt-4 text-sm text-red-300">{error}</p>}
        {success && <p className="mt-4 text-sm text-emerald-300">{success}</p>}
      </section>

      {showCreateModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="create-event-title"
          onClick={() => setShowCreateModal(false)}
        >
          <div
            className="w-full max-w-md rounded-lg border border-[#FFC72C]/50 bg-[#151515] p-5 text-white shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 id="create-event-title" className="text-lg font-semibold text-[#FFC72C]">
              Create Event
            </h3>
            <form className="mt-4 space-y-3" onSubmit={handleCreateEvent}>
              <div>
                <label className="text-sm text-neutral-300">Event Name</label>
                <input
                  className="mt-1 w-full rounded border border-neutral-700 bg-black p-2 text-sm text-white"
                  value={createName}
                  onChange={(e) => setCreateName(e.target.value)}
                  placeholder="Event name"
                  required
                />
              </div>
              <div>
                <label className="text-sm text-neutral-300">Time</label>
                <input
                  className="mt-1 w-full rounded border border-neutral-700 bg-black p-2 text-sm text-white"
                  type="datetime-local"
                  value={createTime}
                  onChange={(e) => setCreateTime(e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="text-sm text-neutral-300">Game (Optional)</label>
                <input
                  className="mt-1 w-full rounded border border-neutral-700 bg-black p-2 text-sm text-white"
                  value={createGame}
                  onChange={(e) => setCreateGame(e.target.value)}
                  placeholder="e.g. Valorant"
                />
              </div>
              <div className="flex items-center justify-end gap-2 pt-1">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="rounded border border-[#FFC72C]/60 px-3 py-1 text-sm text-[#FFC72C] hover:bg-[#FFC72C]/10"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="rounded border border-[#FFC72C] bg-[#5C068C]/80 px-3 py-1 text-sm font-medium text-white hover:bg-[#5C068C] disabled:opacity-60"
                >
                  {creating ? "Creating..." : "Create"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {activeEvent && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="calendar-event-title"
          onClick={() => setActiveEvent(null)}
        >
          <div
            className="w-full max-w-md rounded-lg border border-[#FFC72C]/50 bg-[#151515] p-5 text-white shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-3 flex items-start justify-between gap-3">
              <h3 id="calendar-event-title" className="text-lg font-semibold text-[#FFC72C]">
                {isEditingEvent ? "Edit Event" : activeEvent.name}
              </h3>
              <button
                type="button"
                onClick={() => setActiveEvent(null)}
                className="rounded border border-[#FFC72C]/60 px-2 py-1 text-xs text-[#FFC72C] hover:bg-[#FFC72C]/10"
              >
                Close
              </button>
            </div>

            {isEditingEvent ? (
              <div className="space-y-3">
                <div>
                  <label className="text-sm text-neutral-300">Event Name</label>
                  <input
                    className="mt-1 w-full rounded border border-neutral-700 bg-black p-2 text-sm text-white"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label className="text-sm text-neutral-300">Time</label>
                  <input
                    className="mt-1 w-full rounded border border-neutral-700 bg-black p-2 text-sm text-white"
                    type="datetime-local"
                    value={editTime}
                    onChange={(e) => setEditTime(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label className="text-sm text-neutral-300">Game (Optional)</label>
                  <input
                    className="mt-1 w-full rounded border border-neutral-700 bg-black p-2 text-sm text-white"
                    value={editGame}
                    onChange={(e) => setEditGame(e.target.value)}
                  />
                </div>
              </div>
            ) : (
              <div className="space-y-2 text-sm">
                <p>
                  <span className="font-semibold text-[#FFC72C]">Time:</span> {formatEventTime(activeEvent.time)}
                </p>
                <p>
                  <span className="font-semibold text-[#FFC72C]">Game:</span>{" "}
                  {activeEvent.game && activeEvent.game.trim() ? activeEvent.game : "N/A"}
                </p>
              </div>
            )}

            <div className="mt-5 flex flex-wrap gap-2">
              {isEditingEvent ? (
                <>
                  <button
                    type="button"
                    onClick={() => void handleUpdateEvent()}
                    disabled={updating || deleting}
                    className="rounded border border-[#FFC72C] bg-[#5C068C]/80 px-3 py-1 text-sm font-medium text-white hover:bg-[#5C068C] disabled:opacity-60"
                  >
                    {updating ? "Saving..." : "Save"}
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsEditingEvent(false)}
                    disabled={updating || deleting}
                    className="rounded border border-[#FFC72C]/60 px-3 py-1 text-sm text-[#FFC72C] hover:bg-[#FFC72C]/10"
                  >
                    Cancel
                  </button>
                </>
              ) : (
                <button
                  type="button"
                  onClick={() => setIsEditingEvent(true)}
                  disabled={updating || deleting}
                  className="rounded border border-[#FFC72C]/60 px-3 py-1 text-sm text-[#FFC72C] hover:bg-[#FFC72C]/10 disabled:opacity-60"
                >
                  Edit Event
                </button>
              )}

              <button
                type="button"
                onClick={() => void handleDeleteEvent()}
                disabled={updating || deleting}
                className="rounded border border-red-700 px-3 py-1 text-sm text-red-300 hover:bg-red-950/50 disabled:opacity-60"
              >
                {deleting ? "Deleting..." : "Delete Event"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
