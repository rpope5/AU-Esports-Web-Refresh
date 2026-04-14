"use client";

import { useEffect, useMemo, useState } from "react";

type CalendarEvent = {
  id: number;
  name: string;
  time: string;
  game: string | null;
  created_at: string;
  updated_at: string;
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

function dateKey(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function formatEventTime(raw: string): string {
  const parsed = new Date(raw);
  if (Number.isNaN(parsed.getTime())) return raw;
  return parsed.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export default function ScheduleCalendar() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const [currentMonth, setCurrentMonth] = useState(() => startOfMonth(new Date()));
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeEvent, setActiveEvent] = useState<CalendarEvent | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    const monthStart = startOfMonth(currentMonth);
    const monthEnd = endOfMonth(currentMonth);

    const loadEvents = async () => {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams({
          start: monthStart.toISOString(),
          end: monthEnd.toISOString(),
        });
        const response = await fetch(`${apiUrl}/api/v1/schedule/events?${params.toString()}`, {
          signal: controller.signal,
        });
        if (!response.ok) {
          const body = await response.text();
          throw new Error(body || "Failed to load schedule events");
        }
        const data = (await response.json()) as CalendarEvent[];
        setEvents(Array.isArray(data) ? data : []);
      } catch (err: unknown) {
        if (err instanceof DOMException && err.name === "AbortError") return;
        setEvents([]);
        setError(err instanceof Error ? err.message : "Failed to load schedule events");
      } finally {
        setLoading(false);
      }
    };

    loadEvents();
    return () => controller.abort();
  }, [apiUrl, currentMonth]);

  const eventsByDay = useMemo(() => {
    const map = new Map<string, CalendarEvent[]>();
    for (const event of events) {
      const parsed = new Date(event.time);
      if (Number.isNaN(parsed.getTime())) continue;
      const key = dateKey(parsed);
      const bucket = map.get(key) || [];
      bucket.push(event);
      map.set(key, bucket);
    }
    for (const [, bucket] of map) {
      bucket.sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime());
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

  const prevMonth = () =>
    setCurrentMonth((prev) => new Date(prev.getFullYear(), prev.getMonth() - 1, 1));
  const nextMonth = () =>
    setCurrentMonth((prev) => new Date(prev.getFullYear(), prev.getMonth() + 1, 1));

  return (
    <section className="mx-auto w-full max-w-7xl px-4 py-8 md:px-8">
      <div className="rounded-lg border border-[#FFC72C]/40 bg-[#111111] p-4 md:p-6">
        <div className="mb-4 flex items-center justify-between gap-3">
          <button
            type="button"
            onClick={prevMonth}
            className="rounded border border-[#FFC72C]/60 px-3 py-1 text-sm text-[#FFC72C] transition hover:bg-[#FFC72C]/10"
            aria-label="Previous month"
          >
            Prev
          </button>
          <h2 className="text-xl font-semibold text-white">{monthLabel}</h2>
          <button
            type="button"
            onClick={nextMonth}
            className="rounded border border-[#FFC72C]/60 px-3 py-1 text-sm text-[#FFC72C] transition hover:bg-[#FFC72C]/10"
            aria-label="Next month"
          >
            Next
          </button>
        </div>

        <div className="mb-2 grid grid-cols-7 gap-1 text-center text-xs font-semibold uppercase tracking-wide text-[#FFC72C]/90 md:text-sm">
          {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
            <div key={day} className="py-2">
              {day}
            </div>
          ))}
        </div>

        {loading ? (
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

        {!loading && error && (
          <p className="mt-4 text-sm text-red-300">Could not load schedule events: {error}</p>
        )}
      </div>

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
                {activeEvent.name}
              </h3>
              <button
                type="button"
                onClick={() => setActiveEvent(null)}
                className="rounded border border-[#FFC72C]/60 px-2 py-1 text-xs text-[#FFC72C] hover:bg-[#FFC72C]/10"
              >
                Close
              </button>
            </div>
            <div className="space-y-2 text-sm">
              <p>
                <span className="font-semibold text-[#FFC72C]">Time:</span> {formatEventTime(activeEvent.time)}
              </p>
              <p>
                <span className="font-semibold text-[#FFC72C]">Game:</span>{" "}
                {activeEvent.game && activeEvent.game.trim() ? activeEvent.game : "N/A"}
              </p>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
