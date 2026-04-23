"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { clearAdminStorage, formatRoleLabel, parseAdminSession, type AdminSession } from "../_lib/session";

type ScheduleStatus = "pending" | "published" | "rejected" | "archived";
type CreateWorkflowAction = "publish" | "submit_for_approval";
type TransitionAction = "submit" | "approve" | "reject" | "archive";
type Meridiem = "AM" | "PM";

type CalendarEvent = {
  id: number;
  name: string;
  time: string;
  game_slug: string | null;
  game_name: string | null;
  game: string | null;
  status: ScheduleStatus;
  created_by_username: string | null;
  approved_by_username: string | null;
  rejected_by_username: string | null;
  submitted_at: string | null;
  approved_at: string | null;
  rejected_at: string | null;
  archived_at: string | null;
};

type GameOption = {
  id: number;
  slug: string;
  name: string;
};

type GameScopeOption = {
  value: string;
  label: string;
};

type TimeSelection = {
  hour: string;
  minute: string;
  period: Meridiem | "";
};

type EditFormState = {
  name: string;
  date: string;
  hour: string;
  minute: string;
  period: Meridiem | "";
  gameScope: string;
};

type SelectOption = {
  value: string;
  label: string;
};

type CalendarCell = {
  dateValue: string;
  dayNumber: number;
  inCurrentMonth: boolean;
};

const GENERAL_SCOPE_VALUE = "__general__";
const WEEKDAY_LABELS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function pad2(value: number): string {
  return String(value).padStart(2, "0");
}

function parseApiDate(raw: string): Date | null {
  const hasTimezone = /[zZ]$|[+-]\d{2}:\d{2}$/.test(raw);
  const parsed = new Date(hasTimezone ? raw : `${raw}Z`);
  if (Number.isNaN(parsed.getTime())) return null;
  return parsed;
}

function toLocalDateValue(date: Date): string {
  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}`;
}

function parseDateValue(raw: string): Date | null {
  const [yearRaw, monthRaw, dayRaw] = raw.split("-");
  const year = Number(yearRaw);
  const month = Number(monthRaw);
  const day = Number(dayRaw);
  if (!Number.isInteger(year) || !Number.isInteger(month) || !Number.isInteger(day)) return null;
  if (month < 1 || month > 12 || day < 1 || day > 31) return null;
  const parsed = new Date(year, month - 1, day);
  if (Number.isNaN(parsed.getTime())) return null;
  return parsed;
}

function getLocalTimeSelection(date: Date): TimeSelection {
  const hour24 = date.getHours();
  const period: Meridiem = hour24 >= 12 ? "PM" : "AM";
  const hour12 = hour24 % 12 || 12;
  return {
    hour: String(hour12),
    minute: pad2(date.getMinutes()),
    period,
  };
}

function toIsoUtcFromParts(
  dateValue: string,
  hourValue: string,
  minuteValue: string,
  periodValue: Meridiem | "",
): string | null {
  const parsedDate = parseDateValue(dateValue);
  if (!parsedDate) return null;

  const hour12 = Number(hourValue);
  const minute = Number(minuteValue);
  if (!Number.isInteger(hour12) || hour12 < 1 || hour12 > 12) return null;
  if (!Number.isInteger(minute) || minute < 0 || minute > 59) return null;
  if (periodValue !== "AM" && periodValue !== "PM") return null;

  let hour24 = hour12 % 12;
  if (periodValue === "PM") hour24 += 12;

  const parsed = new Date(
    parsedDate.getFullYear(),
    parsedDate.getMonth(),
    parsedDate.getDate(),
    hour24,
    minute,
    0,
    0,
  );
  if (Number.isNaN(parsed.getTime())) return null;
  return parsed.toISOString();
}

function formatDate(raw: string | null | undefined): string {
  if (!raw) return "N/A";
  const parsed = parseApiDate(raw);
  if (!parsed) return "N/A";
  return parsed.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

function formatSelectedDateLabel(dateValue: string): string {
  const parsed = parseDateValue(dateValue);
  if (!parsed) return "Pick a date";
  return parsed.toLocaleDateString(undefined, { dateStyle: "medium" });
}

function formatScopeLabel(item: CalendarEvent): string {
  return item.game_name || item.game || item.game_slug || "General";
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

function canPublish(session: AdminSession | null): boolean {
  return session?.role === "coach" || session?.role === "head_coach" || session?.role === "admin";
}

function normalizeGameScopeValue(gameSlug: string | null | undefined): string {
  const normalized = (gameSlug || "").trim();
  return normalized || GENERAL_SCOPE_VALUE;
}

function toLocalDateAndTimeFromApi(raw: string): { date: string; time: TimeSelection } {
  const parsed = parseApiDate(raw);
  if (!parsed) {
    return { date: "", time: { hour: "", minute: "", period: "" } };
  }
  return { date: toLocalDateValue(parsed), time: getLocalTimeSelection(parsed) };
}

function monthLabel(monthCursor: Date): string {
  return monthCursor.toLocaleDateString(undefined, { month: "long", year: "numeric" });
}

function buildCalendarCells(monthCursor: Date): CalendarCell[] {
  const month = monthCursor.getMonth();
  const year = monthCursor.getFullYear();
  const firstDay = new Date(year, month, 1).getDay();
  const daysInCurrentMonth = new Date(year, month + 1, 0).getDate();
  const daysInPrevMonth = new Date(year, month, 0).getDate();

  const cells: CalendarCell[] = [];

  for (let i = 0; i < 42; i += 1) {
    if (i < firstDay) {
      const day = daysInPrevMonth - firstDay + i + 1;
      const date = new Date(year, month - 1, day);
      cells.push({
        dateValue: toLocalDateValue(date),
        dayNumber: day,
        inCurrentMonth: false,
      });
      continue;
    }

    if (i >= firstDay + daysInCurrentMonth) {
      const day = i - (firstDay + daysInCurrentMonth) + 1;
      const date = new Date(year, month + 1, day);
      cells.push({
        dateValue: toLocalDateValue(date),
        dayNumber: day,
        inCurrentMonth: false,
      });
      continue;
    }

    const day = i - firstDay + 1;
    const date = new Date(year, month, day);
    cells.push({
      dateValue: toLocalDateValue(date),
      dayNumber: day,
      inCurrentMonth: true,
    });
  }

  return cells;
}

function useDismissibleLayer(open: boolean, onClose: () => void) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) return;

    const onPointerDown = (event: MouseEvent) => {
      const target = event.target as Node;
      if (containerRef.current && !containerRef.current.contains(target)) {
        onClose();
      }
    };

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };

    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open, onClose]);

  return containerRef;
}

function CalendarIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      className="h-4 w-4"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
      <line x1="16" y1="2" x2="16" y2="6" />
      <line x1="8" y1="2" x2="8" y2="6" />
      <line x1="3" y1="10" x2="21" y2="10" />
    </svg>
  );
}

function ChevronDownIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      className="h-4 w-4"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="6 9 12 15 18 9" />
    </svg>
  );
}

function ChevronLeftIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      className="h-4 w-4"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="15 18 9 12 15 6" />
    </svg>
  );
}

function ChevronRightIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      className="h-4 w-4"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="9 18 15 12 9 6" />
    </svg>
  );
}

function DatePickerField({
  value,
  onChange,
  disabled = false,
  placeholder = "Pick a date",
}: {
  value: string;
  onChange: (nextValue: string) => void;
  disabled?: boolean;
  placeholder?: string;
}) {
  const [open, setOpen] = useState(false);
  const [monthCursor, setMonthCursor] = useState(() => parseDateValue(value) || new Date());
  const containerRef = useDismissibleLayer(open, () => setOpen(false));

  useEffect(() => {
    if (!open) return;
    setMonthCursor(parseDateValue(value) || new Date());
  }, [open, value]);

  const selectedLabel = value ? formatSelectedDateLabel(value) : placeholder;
  const todayValue = toLocalDateValue(new Date());
  const cells = useMemo(() => buildCalendarCells(monthCursor), [monthCursor]);

  return (
    <div className="relative" ref={containerRef}>
      <button
        type="button"
        disabled={disabled}
        onClick={() => setOpen((prev) => !prev)}
        className="flex w-full items-center justify-between rounded border border-neutral-700 bg-black px-3 py-2 text-left text-sm text-neutral-100 transition hover:border-neutral-500 disabled:opacity-60"
      >
        <span className={`inline-flex items-center gap-2 ${value ? "text-neutral-100" : "text-neutral-400"}`}>
          <CalendarIcon />
          <span>{selectedLabel}</span>
        </span>
        <ChevronDownIcon />
      </button>

      {open && (
        <div className="absolute left-0 z-50 mt-2 w-[19rem] rounded-xl border border-neutral-700 bg-neutral-950 p-3 shadow-2xl">
          <div className="mb-2 flex items-center justify-between">
            <button
              type="button"
              onClick={() => setMonthCursor((prev) => new Date(prev.getFullYear(), prev.getMonth() - 1, 1))}
              className="rounded border border-neutral-700 p-1 text-neutral-200 hover:border-neutral-500"
              aria-label="Previous month"
            >
              <ChevronLeftIcon />
            </button>
            <div className="text-sm font-medium text-neutral-100">{monthLabel(monthCursor)}</div>
            <button
              type="button"
              onClick={() => setMonthCursor((prev) => new Date(prev.getFullYear(), prev.getMonth() + 1, 1))}
              className="rounded border border-neutral-700 p-1 text-neutral-200 hover:border-neutral-500"
              aria-label="Next month"
            >
              <ChevronRightIcon />
            </button>
          </div>

          <div className="mb-1 grid grid-cols-7 text-center text-[11px] uppercase tracking-wide text-neutral-500">
            {WEEKDAY_LABELS.map((day) => (
              <span key={day} className="py-1">
                {day}
              </span>
            ))}
          </div>

          <div className="grid grid-cols-7 gap-1">
            {cells.map((cell) => {
              const isSelected = value === cell.dateValue;
              const isToday = todayValue === cell.dateValue;
              return (
                <button
                  key={cell.dateValue}
                  type="button"
                  onClick={() => {
                    onChange(cell.dateValue);
                    setOpen(false);
                  }}
                  className={[
                    "rounded px-1 py-1.5 text-center text-sm transition",
                    cell.inCurrentMonth ? "text-neutral-100" : "text-neutral-500",
                    isSelected ? "bg-emerald-900/50 text-emerald-100 ring-1 ring-emerald-600" : "hover:bg-neutral-800",
                    isToday && !isSelected ? "ring-1 ring-neutral-600" : "",
                  ].join(" ")}
                >
                  {cell.dayNumber}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

function CustomSelect({
  value,
  options,
  onValueChange,
  placeholder,
  disabled = false,
}: {
  value: string;
  options: SelectOption[];
  onValueChange: (nextValue: string) => void;
  placeholder: string;
  disabled?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const containerRef = useDismissibleLayer(open, () => setOpen(false));

  const activeLabel = options.find((option) => option.value === value)?.label || placeholder;

  return (
    <div className="relative" ref={containerRef}>
      <button
        type="button"
        disabled={disabled}
        onClick={() => setOpen((prev) => !prev)}
        className="flex w-full items-center justify-between rounded border border-neutral-700 bg-black px-3 py-2 text-sm text-neutral-100 transition hover:border-neutral-500 disabled:opacity-60"
      >
        <span className={value ? "text-neutral-100" : "text-neutral-400"}>{activeLabel}</span>
        <ChevronDownIcon />
      </button>

      {open && (
        <div className="absolute left-0 z-50 mt-2 max-h-52 w-full overflow-y-auto rounded-xl border border-neutral-700 bg-neutral-950 p-1 shadow-2xl">
          {options.map((option) => {
            const selected = option.value === value;
            return (
              <button
                key={option.value}
                type="button"
                onClick={() => {
                  onValueChange(option.value);
                  setOpen(false);
                }}
                className={[
                  "w-full rounded px-2 py-1.5 text-left text-sm transition",
                  selected ? "bg-emerald-900/40 text-emerald-100" : "text-neutral-100 hover:bg-neutral-800",
                ].join(" ")}
              >
                {option.label}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

function TimePickerField({
  hourValue,
  minuteValue,
  periodValue,
  onHourChange,
  onMinuteChange,
  onPeriodChange,
  disabled = false,
}: {
  hourValue: string;
  minuteValue: string;
  periodValue: Meridiem | "";
  onHourChange: (nextValue: string) => void;
  onMinuteChange: (nextValue: string) => void;
  onPeriodChange: (nextValue: Meridiem) => void;
  disabled?: boolean;
}) {
  const hourOptions = useMemo<SelectOption[]>(
    () => Array.from({ length: 12 }, (_, index) => ({ value: String(index + 1), label: String(index + 1) })),
    [],
  );
  const minuteOptions = useMemo<SelectOption[]>(
    () => Array.from({ length: 60 }, (_, index) => ({ value: pad2(index), label: pad2(index) })),
    [],
  );
  const periodOptions = useMemo<SelectOption[]>(() => [{ value: "AM", label: "AM" }, { value: "PM", label: "PM" }], []);

  return (
    <div className="grid grid-cols-3 gap-2">
      <CustomSelect
        value={hourValue}
        options={hourOptions}
        onValueChange={onHourChange}
        placeholder="Hour"
        disabled={disabled}
      />
      <CustomSelect
        value={minuteValue}
        options={minuteOptions}
        onValueChange={onMinuteChange}
        placeholder="Minute"
        disabled={disabled}
      />
      <CustomSelect
        value={periodValue}
        options={periodOptions}
        onValueChange={(nextValue) => onPeriodChange(nextValue as Meridiem)}
        placeholder="AM/PM"
        disabled={disabled}
      />
    </div>
  );
}

export default function AdminSchedulePage() {
  const router = useRouter();
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const [session, setSession] = useState<AdminSession | null>(null);
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [allGames, setAllGames] = useState<GameOption[]>([]);
  const [statusFilter, setStatusFilter] = useState<"all" | ScheduleStatus>("all");

  const [name, setName] = useState("");
  const [scheduleDate, setScheduleDate] = useState("");
  const [scheduleHour, setScheduleHour] = useState("");
  const [scheduleMinute, setScheduleMinute] = useState("");
  const [schedulePeriod, setSchedulePeriod] = useState<Meridiem | "">("");
  const [gameScope, setGameScope] = useState("");

  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState<EditFormState>({
    name: "",
    date: "",
    hour: "",
    minute: "",
    period: "",
    gameScope: "",
  });

  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingGames, setLoadingGames] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [creating, setCreating] = useState(false);

  const canManageSchedule = Boolean(session?.permissions.can_manage_schedule);
  const canDeleteSchedule = Boolean(session?.permissions.can_delete_schedule);
  const canUseGeneralScope = Boolean(session?.has_global_game_access);

  const availableGames = useMemo(() => {
    if (!session) return [];
    if (session.has_global_game_access) return allGames;
    return allGames.filter((game) => session.allowed_game_slugs.includes(game.slug));
  }, [allGames, session]);

  const baseScopeOptions = useMemo<GameScopeOption[]>(() => {
    const options = availableGames.map((game) => ({
      value: game.slug,
      label: game.name,
    }));
    if (canUseGeneralScope) {
      options.unshift({
        value: GENERAL_SCOPE_VALUE,
        label: "General (site-wide)",
      });
    }
    return options;
  }, [availableGames, canUseGeneralScope]);

  const editScopeOptions = useMemo<GameScopeOption[]>(() => {
    const options = [...baseScopeOptions];
    if (editingId !== null && editForm.gameScope && !options.some((option) => option.value === editForm.gameScope)) {
      options.unshift({
        value: editForm.gameScope,
        label: `${editForm.gameScope} (current)`,
      });
    }
    return options;
  }, [baseScopeOptions, editForm.gameScope, editingId]);

  useEffect(() => {
    if (baseScopeOptions.length === 0) {
      if (gameScope !== "") setGameScope("");
      return;
    }
    if (!gameScope || !baseScopeOptions.some((option) => option.value === gameScope)) {
      setGameScope(baseScopeOptions[0].value);
    }
  }, [baseScopeOptions, gameScope]);

  useEffect(() => {
    if (editingId === null) return;
    if (!editScopeOptions.some((option) => option.value === editForm.gameScope)) {
      setEditForm((prev) => ({
        ...prev,
        gameScope: editScopeOptions[0]?.value || "",
      }));
    }
  }, [editForm.gameScope, editScopeOptions, editingId]);

  const clearSessionAndRedirect = useCallback(() => {
    clearAdminStorage();
    router.push("/admin/login");
  }, [router]);

  const getToken = useCallback(() => {
    const token = localStorage.getItem("au_admin_token");
    if (!token) router.push("/admin/login");
    return token;
  }, [router]);

  const loadGames = useCallback(async () => {
    setLoadingGames(true);
    try {
      const response = await fetch(`${apiUrl}/api/v1/games`);
      if (!response.ok) throw new Error("Failed to load canonical games");
      const data = (await response.json()) as GameOption[];
      setAllGames(Array.isArray(data) ? data : []);
    } catch {
      setAllGames([]);
    } finally {
      setLoadingGames(false);
    }
  }, [apiUrl]);

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
    void loadGames();
  }, [apiUrl, clearSessionAndRedirect, loadGames, router]);

  useEffect(() => {
    void loadEvents();
  }, [loadEvents]);

  async function createScheduleItem(action: CreateWorkflowAction): Promise<void> {
    const token = getToken();
    if (!token) return;
    setError(null);
    setSuccess(null);

    const cleanName = name.trim();
    const timeIso = toIsoUtcFromParts(scheduleDate, scheduleHour, scheduleMinute, schedulePeriod);
    if (!cleanName || !scheduleDate || !scheduleHour || !scheduleMinute || !schedulePeriod || !timeIso || !gameScope) {
      setError("Name, date/time, and game scope are required.");
      return;
    }
    if (gameScope === GENERAL_SCOPE_VALUE && !canUseGeneralScope) {
      setError("Only staff with global game access can create General schedule items.");
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
          name: cleanName,
          time: timeIso,
          game_slug: gameScope === GENERAL_SCOPE_VALUE ? null : gameScope,
          workflow_action: action,
        }),
      });
      if (response.status === 401) {
        clearSessionAndRedirect();
        return;
      }
      if (!response.ok) throw new Error((await response.text()) || "Failed to create schedule item");

      setName("");
      setScheduleDate("");
      setScheduleHour("");
      setScheduleMinute("");
      setSchedulePeriod("");
      setSuccess(action === "publish" ? "Schedule item published." : "Schedule item submitted for approval.");
      await loadEvents();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create schedule item");
    } finally {
      setCreating(false);
    }
  }

  function startEditing(item: CalendarEvent): void {
    const local = toLocalDateAndTimeFromApi(item.time);
    setEditingId(item.id);
    setEditForm({
      name: item.name,
      date: local.date,
      hour: local.time.hour,
      minute: local.time.minute,
      period: local.time.period,
      gameScope: normalizeGameScopeValue(item.game_slug),
    });
    setError(null);
    setSuccess(null);
  }

  function cancelEditing(): void {
    setEditingId(null);
    setEditForm({
      name: "",
      date: "",
      hour: "",
      minute: "",
      period: "",
      gameScope: "",
    });
  }

  async function saveEdit(item: CalendarEvent): Promise<void> {
    const token = getToken();
    if (!token) return;

    const cleanName = editForm.name.trim();
    const timeIso = toIsoUtcFromParts(editForm.date, editForm.hour, editForm.minute, editForm.period);
    if (
      !cleanName ||
      !editForm.date ||
      !editForm.hour ||
      !editForm.minute ||
      !editForm.period ||
      !timeIso ||
      !editForm.gameScope
    ) {
      setError("Name, date/time, and game scope are required for edits.");
      return;
    }
    if (editForm.gameScope === GENERAL_SCOPE_VALUE && !canUseGeneralScope) {
      setError("Only staff with global game access can set General schedule scope.");
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
          time: timeIso,
          game_slug: editForm.gameScope === GENERAL_SCOPE_VALUE ? null : editForm.gameScope,
        }),
      });
      if (response.status === 401) {
        clearSessionAndRedirect();
        return;
      }
      if (!response.ok) throw new Error((await response.text()) || "Failed to edit schedule item");
      setSuccess("Schedule item updated.");
      cancelEditing();
      await loadEvents();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to edit schedule item");
    } finally {
      setBusyId(null);
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
      if (editingId === eventId) cancelEditing();
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
          <p className="mt-1 text-sm text-neutral-400">
            Pick a date from the calendar popover and set a time with explicit hour/minute/AM-PM controls.
          </p>

          <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <label className="block">
              <span className="mb-1 block text-xs text-neutral-400">Name</span>
              <input
                className="w-full rounded border border-neutral-700 bg-black p-2 text-sm"
                placeholder="Name"
                value={name}
                onChange={(event) => setName(event.target.value)}
              />
            </label>

            <label className="block">
              <span className="mb-1 block text-xs text-neutral-400">Date</span>
              <DatePickerField value={scheduleDate} onChange={setScheduleDate} />
            </label>

            <label className="block xl:col-span-1">
              <span className="mb-1 block text-xs text-neutral-400">Time</span>
              <TimePickerField
                hourValue={scheduleHour}
                minuteValue={scheduleMinute}
                periodValue={schedulePeriod}
                onHourChange={setScheduleHour}
                onMinuteChange={setScheduleMinute}
                onPeriodChange={setSchedulePeriod}
              />
            </label>

            <label className="block">
              <span className="mb-1 block text-xs text-neutral-400">Game Scope</span>
              <select
                className="w-full rounded border border-neutral-700 bg-black p-2 text-sm"
                value={gameScope}
                onChange={(event) => setGameScope(event.target.value)}
                disabled={loadingGames || baseScopeOptions.length === 0}
              >
                {baseScopeOptions.length === 0 ? (
                  <option value="">{loadingGames ? "Loading scopes..." : "No game scope available"}</option>
                ) : (
                  baseScopeOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))
                )}
              </select>
            </label>
          </div>

          {!canUseGeneralScope && (
            <p className="mt-2 text-xs text-neutral-500">
              General scope is reserved for staff with global game access.
            </p>
          )}

          <div className="mt-3 flex flex-wrap gap-2">
            {canPublish(session) && (
              <button
                className="rounded border border-emerald-700/80 bg-emerald-950/30 px-3 py-1 text-sm text-emerald-100 disabled:opacity-60"
                disabled={creating}
                onClick={() => void createScheduleItem("publish")}
              >
                {creating ? "Publishing..." : "Publish"}
              </button>
            )}
            <button
              className="rounded border border-amber-700/80 bg-amber-950/30 px-3 py-1 text-sm text-amber-100 disabled:opacity-60"
              disabled={creating}
              onClick={() => void createScheduleItem("submit_for_approval")}
            >
              {creating ? "Submitting..." : "Submit for Approval"}
            </button>
            <select
              className="rounded border border-neutral-700 bg-black px-2 py-1 text-sm"
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value as "all" | ScheduleStatus)}
            >
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
              const isEditing = editingId === item.id;
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
                    <div className="min-w-0 flex-1">
                      {!isEditing ? (
                        <>
                          <h3 className="text-lg font-semibold">{item.name}</h3>
                          <p className="text-sm text-neutral-400">
                            {formatDate(item.time)} | {formatScopeLabel(item)}
                          </p>
                        </>
                      ) : (
                        <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-4">
                          <label className="block">
                            <span className="mb-1 block text-xs text-neutral-400">Name</span>
                            <input
                              className="w-full rounded border border-neutral-700 bg-black p-2 text-sm"
                              value={editForm.name}
                              onChange={(event) => setEditForm((prev) => ({ ...prev, name: event.target.value }))}
                            />
                          </label>

                          <label className="block">
                            <span className="mb-1 block text-xs text-neutral-400">Date</span>
                            <DatePickerField
                              value={editForm.date}
                              onChange={(nextDate) => setEditForm((prev) => ({ ...prev, date: nextDate }))}
                              disabled={busy}
                            />
                          </label>

                          <label className="block">
                            <span className="mb-1 block text-xs text-neutral-400">Time</span>
                            <TimePickerField
                              hourValue={editForm.hour}
                              minuteValue={editForm.minute}
                              periodValue={editForm.period}
                              onHourChange={(nextHour) => setEditForm((prev) => ({ ...prev, hour: nextHour }))}
                              onMinuteChange={(nextMinute) => setEditForm((prev) => ({ ...prev, minute: nextMinute }))}
                              onPeriodChange={(nextPeriod) => setEditForm((prev) => ({ ...prev, period: nextPeriod }))}
                              disabled={busy}
                            />
                          </label>

                          <label className="block">
                            <span className="mb-1 block text-xs text-neutral-400">Game Scope</span>
                            <select
                              className="w-full rounded border border-neutral-700 bg-black p-2 text-sm"
                              value={editForm.gameScope}
                              onChange={(event) => setEditForm((prev) => ({ ...prev, gameScope: event.target.value }))}
                            >
                              {editScopeOptions.map((option) => (
                                <option key={option.value} value={option.value}>
                                  {option.label}
                                </option>
                              ))}
                            </select>
                          </label>
                        </div>
                      )}

                      <div className="mt-2 flex flex-wrap gap-2 text-xs">
                        <span className={`rounded-full border px-2 py-0.5 ${statusClass(item.status)}`}>{statusLabel(item.status)}</span>
                        <span className="rounded-full border border-neutral-700 px-2 py-0.5 text-neutral-300">
                          Created by: {item.created_by_username || "Unknown"}
                        </span>
                        {item.approved_by_username && (
                          <span className="rounded-full border border-neutral-700 px-2 py-0.5 text-neutral-300">
                            Approved by: {item.approved_by_username}
                          </span>
                        )}
                        {item.rejected_by_username && (
                          <span className="rounded-full border border-neutral-700 px-2 py-0.5 text-neutral-300">
                            Rejected by: {item.rejected_by_username}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      {canEdit && !isEditing && (
                        <button
                          className="rounded border border-neutral-700 bg-neutral-900 px-2 py-1 text-xs text-neutral-100 disabled:opacity-60"
                          disabled={busy}
                          onClick={() => startEditing(item)}
                        >
                          {busy ? "Working..." : "Edit"}
                        </button>
                      )}
                      {isEditing && (
                        <>
                          <button
                            className="rounded border border-emerald-700/80 bg-emerald-950/30 px-2 py-1 text-xs text-emerald-100 disabled:opacity-60"
                            disabled={busy}
                            onClick={() => void saveEdit(item)}
                          >
                            {busy ? "Saving..." : "Save"}
                          </button>
                          <button
                            className="rounded border border-neutral-700 bg-neutral-900 px-2 py-1 text-xs text-neutral-100 disabled:opacity-60"
                            disabled={busy}
                            onClick={cancelEditing}
                          >
                            Cancel
                          </button>
                        </>
                      )}
                      {!isEditing && canSubmit && (
                        <button
                          className="rounded border border-amber-700/80 bg-amber-950/30 px-2 py-1 text-xs text-amber-100 disabled:opacity-60"
                          disabled={busy}
                          onClick={() => void transition(item.id, "submit")}
                        >
                          {busy ? "Working..." : "Submit"}
                        </button>
                      )}
                      {!isEditing && canApprove && (
                        <button
                          className="rounded border border-emerald-700/80 bg-emerald-950/30 px-2 py-1 text-xs text-emerald-100 disabled:opacity-60"
                          disabled={busy}
                          onClick={() => void transition(item.id, "approve")}
                        >
                          {busy ? "Working..." : "Approve"}
                        </button>
                      )}
                      {!isEditing && canReject && (
                        <button
                          className="rounded border border-red-700/80 bg-red-950/30 px-2 py-1 text-xs text-red-100 disabled:opacity-60"
                          disabled={busy}
                          onClick={() => void transition(item.id, "reject")}
                        >
                          {busy ? "Working..." : "Reject"}
                        </button>
                      )}
                      {!isEditing && canArchive && (
                        <button
                          className="rounded border border-neutral-700 bg-neutral-900 px-2 py-1 text-xs text-neutral-100 disabled:opacity-60"
                          disabled={busy}
                          onClick={() => void transition(item.id, "archive")}
                        >
                          {busy ? "Working..." : "Archive"}
                        </button>
                      )}
                      {!isEditing && canDeleteSchedule && (
                        <button
                          className="rounded border border-red-700 px-2 py-1 text-xs text-red-300 disabled:opacity-60"
                          disabled={busy}
                          onClick={() => void removeEvent(item.id)}
                        >
                          {busy ? "Working..." : "Delete"}
                        </button>
                      )}
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
