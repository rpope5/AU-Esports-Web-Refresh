export type SiteActivityItemType = "schedule";

type ScheduleEventApi = {
  id: number;
  name: string;
  time: string;
  game: string | null;
  game_slug: string | null;
  game_name: string | null;
  status: "pending" | "published" | "rejected" | "archived";
  created_at: string;
  updated_at: string;
};

export type SiteActivityFeedItem = {
  id: string;
  itemType: SiteActivityItemType;
  title: string;
  subtitle: string | null;
  startsAt: string | null;
  publishedAt: string | null;
  displayDate: string;
  sortDate: string;
  href: string;
};

type FetchSiteActivityOptions = {
  signal?: AbortSignal;
};

function trimTrailingSlashes(value: string): string {
  return value.replace(/\/+$/, "");
}

function parseApiDate(rawValue: string | null | undefined): Date | null {
  if (!rawValue) return null;
  const hasTimezone = /[zZ]$|[+-]\d{2}:\d{2}$/.test(rawValue);
  const parsed = new Date(hasTimezone ? rawValue : `${rawValue}Z`);
  if (Number.isNaN(parsed.getTime())) return null;
  return parsed;
}

function formatDisplayDate(rawValue: string | null | undefined): string {
  const parsed = parseApiDate(rawValue);
  if (!parsed) return "Date TBD";
  return parsed.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function normalizeScheduleItems(scheduleItems: ScheduleEventApi[]): SiteActivityFeedItem[] {
  return scheduleItems
    .filter((item) => item.status === "published")
    .map((item) => ({
      id: `schedule-${item.id}`,
      itemType: "schedule",
      title: item.name,
      subtitle: item.game_name || item.game || "Scheduled event",
      startsAt: item.time,
      publishedAt: null,
      displayDate: formatDisplayDate(item.time),
      sortDate: item.time,
      href: "/schedule",
    }));
}

function sortSiteActivity(items: SiteActivityFeedItem[]): SiteActivityFeedItem[] {
  return [...items].sort((a, b) => {
    const aTime = parseApiDate(a.sortDate)?.getTime() ?? Number.NaN;
    const bTime = parseApiDate(b.sortDate)?.getTime() ?? Number.NaN;

    if (Number.isNaN(aTime) && Number.isNaN(bTime)) return a.id.localeCompare(b.id);
    if (Number.isNaN(aTime)) return 1;
    if (Number.isNaN(bTime)) return -1;

    // Strict chronological order so past dates never appear after later future dates.
    const timeDiff = aTime - bTime;
    if (timeDiff !== 0) return timeDiff;
    return a.id.localeCompare(b.id);
  });
}

export async function fetchSiteActivityFeed(
  apiUrl: string,
  options: FetchSiteActivityOptions = {},
): Promise<SiteActivityFeedItem[]> {
  const rootApiUrl = trimTrailingSlashes(apiUrl);
  const scheduleUrl = `${rootApiUrl}/api/v1/schedule/events`;

  const [scheduleResult] = await Promise.allSettled([fetch(scheduleUrl, { signal: options.signal })]);

  const normalizedItems: SiteActivityFeedItem[] = [];

  if (scheduleResult.status === "fulfilled" && scheduleResult.value.ok) {
    const scheduleData = (await scheduleResult.value.json()) as ScheduleEventApi[];
    if (Array.isArray(scheduleData)) {
      normalizedItems.push(...normalizeScheduleItems(scheduleData));
    }
  }

  return sortSiteActivity(normalizedItems);
}
