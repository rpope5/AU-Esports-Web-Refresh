"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import TopActivityFeedBar from "../components/TopActivityFeedBar";
import { getContentPlaceholder, resolveContentImageUrl } from "@/lib/contentImages";
import archiveFilterUtils from "./archiveFilterUtils";

type Announcement = {
  id: number;
  title: string;
  body: string;
  image_url: string | null;
  game_slug?: string | null;
  game_name?: string | null;
  game_slugs?: string[];
  game_names?: string[];
  is_general?: boolean;
  created_at: string;
  updated_at: string | null;
};

type GameOption = {
  id: number;
  slug: string;
  name: string;
};

type ArchiveFilter = "all" | "general" | string;
type ArchiveSort = "newest" | "oldest";

const DEFAULT_NEWS_PLACEHOLDER = getContentPlaceholder("announcement");
const {
  ALL_ARCHIVE_FILTER,
  GENERAL_ARCHIVE_FILTER,
  NEWEST_ARCHIVE_SORT,
  OLDEST_ARCHIVE_SORT,
  filterAndSortArchiveAnnouncements,
  getAnnouncementGameSlugs,
  normalizeArchiveFilterParam,
  normalizeArchiveSortParam,
} = archiveFilterUtils;

function resolveAnnouncementImage(imageUrl: string | null, apiUrl: string): string {
  return resolveContentImageUrl(imageUrl, apiUrl, "announcement");
}

function formatPostedDate(rawValue: string): string {
  const hasTimezone = /[zZ]$|[+-]\d{2}:\d{2}$/.test(rawValue);
  const normalized = hasTimezone ? rawValue : `${rawValue}Z`;
  const parsed = new Date(normalized);
  if (Number.isNaN(parsed.getTime())) return "Unknown date";
  return parsed.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function getScopeLabels(item: Announcement, gameNameBySlug: Map<string, string>): string[] {
  const labels: string[] = [];
  if (item.is_general) labels.push("General");

  if (Array.isArray(item.game_names) && item.game_names.length > 0) {
    labels.push(...item.game_names);
  } else if (item.game_name) {
    labels.push(item.game_name);
  } else {
    const gameSlugs = getAnnouncementGameSlugs(item);
    labels.push(...gameSlugs.map((slug: string) => gameNameBySlug.get(slug) || slug));
  }

  const seen = new Set<string>();
  const deduped: string[] = [];
  for (const rawLabel of labels) {
    const trimmed = rawLabel.trim();
    if (!trimmed) continue;
    const key = trimmed.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    deduped.push(key === "general" ? "General" : trimmed);
  }
  return deduped;
}

export default function NewsPage() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const pages = ["Home", "Roster", "Schedule", "News", "Stream", "Recruitment", "Facility", "Support", "Hall of Fame"];
  const pageMap: Record<string, string> = {
    Home: "/",
    Roster: "/roster",
    Schedule: "/schedule",
    News: "/news",
    Stream: "/stream",
    Recruitment: "/recruit",
    Facility: "/facility",
    Support: "/support",
    "Hall of Fame": "/hof",
  };

  const [isLive, setIsLive] = useState(false);

  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [games, setGames] = useState<GameOption[]>([]);
  const [loadingNews, setLoadingNews] = useState(true);
  const [newsError, setNewsError] = useState<string | null>(null);
  const [archiveFilter, setArchiveFilter] = useState<ArchiveFilter>(ALL_ARCHIVE_FILTER);
  const [archiveSort, setArchiveSort] = useState<ArchiveSort>(NEWEST_ARCHIVE_SORT);
  const [expandedAnnouncementIds, setExpandedAnnouncementIds] = useState<Record<number, boolean>>({});

  useEffect(() => {
    const checkLiveStatus = async () => {
      try {
        const res = await fetch("https://decapi.me/twitch/uptime/ashlandesports");
        const text = await res.text();
        setIsLive(!text.includes("offline"));
      } catch {
        setIsLive(false);
      }
    };

    checkLiveStatus();
    const interval = setInterval(checkLiveStatus, 60000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const loadAnnouncements = async () => {
      setLoadingNews(true);
      setNewsError(null);
      try {
        const response = await fetch(`${apiUrl}/api/v1/news?limit=50`);
        if (!response.ok) {
          const responseText = await response.text();
          throw new Error(responseText || "Failed to load announcements");
        }
        const data = (await response.json()) as Announcement[];
        setAnnouncements(Array.isArray(data) ? data : []);
      } catch (e: unknown) {
        setNewsError(e instanceof Error ? e.message : "Failed to load announcements");
      } finally {
        setLoadingNews(false);
      }
    };

    loadAnnouncements();
  }, [apiUrl]);

  useEffect(() => {
    const loadGames = async () => {
      try {
        const response = await fetch(`${apiUrl}/api/v1/games`);
        if (!response.ok) throw new Error("Failed to load canonical games");
        const data = (await response.json()) as GameOption[];
        setGames(Array.isArray(data) ? data : []);
      } catch {
        setGames([]);
      }
    };

    void loadGames();
  }, [apiUrl]);

  const canonicalGameSlugs = useMemo(() => games.map((game) => game.slug), [games]);

  const syncArchiveControlsFromUrl = useCallback(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const nextFilter = normalizeArchiveFilterParam(params.get("filter"), canonicalGameSlugs) as ArchiveFilter;
    const nextSort = normalizeArchiveSortParam(params.get("sort")) as ArchiveSort;

    setArchiveFilter((current) => (current === nextFilter ? current : nextFilter));
    setArchiveSort((current) => (current === nextSort ? current : nextSort));
  }, [canonicalGameSlugs]);

  useEffect(() => {
    syncArchiveControlsFromUrl();
  }, [syncArchiveControlsFromUrl]);

  useEffect(() => {
    if (typeof window === "undefined") return undefined;
    const handlePopState = () => syncArchiveControlsFromUrl();
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, [syncArchiveControlsFromUrl]);

  const updateArchiveControls = useCallback(
    (nextFilter: ArchiveFilter, nextSort: ArchiveSort) => {
      setArchiveFilter(nextFilter);
      setArchiveSort(nextSort);

      if (typeof window === "undefined") return;
      const params = new URLSearchParams(window.location.search);
      if (nextFilter === ALL_ARCHIVE_FILTER) {
        params.delete("filter");
      } else {
        params.set("filter", nextFilter);
      }

      if (nextSort === NEWEST_ARCHIVE_SORT) {
        params.delete("sort");
      } else {
        params.set("sort", nextSort);
      }

      const query = params.toString();
      const nextPath = query ? `${window.location.pathname}?${query}` : window.location.pathname;
      window.history.replaceState(window.history.state, "", nextPath);
    },
    [],
  );

  const featuredAnnouncement = useMemo(() => announcements[0] ?? null, [announcements]);
  const archiveAnnouncements = useMemo(() => announcements.slice(1), [announcements]);
  const gameNameBySlug = useMemo(() => {
    const map = new Map<string, string>();
    for (const game of games) map.set(game.slug, game.name);
    return map;
  }, [games]);
  const archiveFilterOptions = useMemo(
    () => [
      { value: ALL_ARCHIVE_FILTER, label: "All" },
      { value: GENERAL_ARCHIVE_FILTER, label: "General" },
      ...games.map((game) => ({ value: game.slug, label: game.name })),
    ],
    [games],
  );
  const visibleArchiveAnnouncements = useMemo(
    () =>
      filterAndSortArchiveAnnouncements(
        archiveAnnouncements,
        archiveFilter,
        archiveSort,
      ) as Announcement[],
    [archiveAnnouncements, archiveFilter, archiveSort],
  );
  const toggleArchiveAnnouncement = (announcementId: number) => {
    setExpandedAnnouncementIds((current) => ({
      ...current,
      [announcementId]: !current[announcementId],
    }));
  };

  return (
    <div className="min-h-screen bg-black text-white">
      <TopActivityFeedBar />

      <header className="site-header flex flex-col items-center justify-between gap-4 p-4 md:flex-row">
        <div className="flex items-center gap-2">
          <Image
            src="/Eagle.png"
            alt="Ashland Eagle Logo"
            width={90}
            height={90}
            className="h-14 w-14 object-contain md:h-20 md:w-20"
          />
          <div className="flex items-center gap-3">
            <h1
              className="title title-3d text-lg font-bold tracking-wide md:text-2xl"
              style={{ textShadow: "1px 1px #333" }}
            >
              Ashland University Esports
            </h1>
            {isLive && (
              <div className="flex items-center gap-2">
                <span className="relative flex h-3 w-3">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#FFC72C] opacity-75" />
                  <span className="relative inline-flex h-3 w-3 rounded-full bg-[#FFC72C]" />
                </span>
                <span className="text-sm font-semibold text-[#FFC72C]">LIVE</span>
              </div>
            )}
          </div>
        </div>

        <nav className="nav-buttons flex flex-wrap justify-center gap-6 text-sm md:text-base">
          {pages.map((page) => (
            <Link key={page} href={pageMap[page] || "/"} className="relative group">
              {page}
              <span className="absolute -bottom-1 left-0 h-[2px] w-0 bg-[#FFC72C] transition-all duration-300 group-hover:w-full" />
            </Link>
          ))}
        </nav>
      </header>

      <div className="h-[2px] w-full bg-gradient-to-r from-transparent via-[#FFC72C] to-transparent opacity-70" />

      <main className="mx-auto w-full max-w-6xl px-4 pb-14 pt-8 md:px-8">
        <section className="mb-7">
          <p className="text-xs uppercase tracking-[0.3em] text-[#FFC72C]/90">Official Updates</p>
          <h2 className="mt-2 text-3xl font-bold md:text-4xl">News & Announcements</h2>
          <p className="mt-3 max-w-3xl text-sm text-neutral-300 md:text-base">
            Stay up to date with the latest Ashland University Esports results, roster updates, and
            program announcements.
          </p>
        </section>

        {loadingNews ? (
          <section className="rounded-2xl border border-neutral-800 bg-neutral-950 p-6">
            <p className="text-neutral-300">Loading announcements...</p>
          </section>
        ) : newsError ? (
          <section className="rounded-2xl border border-red-800 bg-red-950/40 p-6">
            <p className="text-red-300">Could not load announcements: {newsError}</p>
          </section>
        ) : !featuredAnnouncement ? (
          <section className="overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-950">
            <div className="relative h-[340px]">
              <div
                className="absolute inset-0 bg-cover bg-center opacity-60"
                style={{ backgroundImage: `url("${DEFAULT_NEWS_PLACEHOLDER}")` }}
              />
              <div className="absolute inset-0 bg-gradient-to-r from-black/90 via-black/70 to-black/50" />
              <div className="relative z-10 flex h-full flex-col justify-end p-6">
                <p className="text-xs uppercase tracking-[0.25em] text-[#FFC72C]">Latest Announcement</p>
                <h3 className="mt-2 text-2xl font-bold md:text-3xl">No announcements posted yet</h3>
                <p className="mt-3 max-w-2xl text-sm text-neutral-300 md:text-base">
                  The coaching staff has not published announcements yet. Check back soon for team news.
                </p>
              </div>
            </div>
          </section>
        ) : (
          <>
            <section className="overflow-hidden rounded-2xl border border-[#FFC72C]/30 bg-neutral-950 shadow-[0_18px_50px_rgba(0,0,0,0.35)]">
              <div className="relative min-h-[420px]">
                <div
                  className="absolute inset-0 bg-cover bg-center"
                  style={{
                    backgroundImage: `url("${resolveAnnouncementImage(
                      featuredAnnouncement.image_url,
                      apiUrl,
                    )}")`,
                  }}
                />
                <div className="absolute inset-0 bg-gradient-to-r from-black/90 via-black/75 to-black/60" />
                <div className="relative z-10 flex min-h-[420px] flex-col justify-end p-6 md:p-10">
                  <p className="text-xs uppercase tracking-[0.25em] text-[#FFC72C]">Latest Announcement</p>
                  <h3 className="mt-2 max-w-3xl text-3xl font-bold leading-tight md:text-4xl">
                    {featuredAnnouncement.title}
                  </h3>
                  <p className="mt-2 text-sm text-neutral-300">
                    Posted {formatPostedDate(featuredAnnouncement.created_at)}
                  </p>
                  
                  <p className="mt-5 max-w-3xl whitespace-pre-line text-sm leading-relaxed text-neutral-100 md:text-base">
                    {featuredAnnouncement.body}
                  </p>
                </div>
              </div>
            </section>

            <section className="mt-8">
              <div className="flex items-center justify-between gap-3">
                <h3 className="text-2xl font-semibold">Archive</h3>
                <span className="text-sm text-neutral-400">
                  {visibleArchiveAnnouncements.length} of {archiveAnnouncements.length} past posts
                </span>
              </div>

              <div className="mt-4 rounded-xl border border-neutral-800 bg-neutral-950 p-4">
                <div className="grid gap-3 md:grid-cols-2">
                  <label className="flex flex-col gap-1 text-sm text-neutral-300">
                    <span>Filter by scope</span>
                    <select
                      className="rounded-lg border border-neutral-700 bg-black/50 px-3 py-2 text-sm text-white"
                      value={archiveFilter}
                      onChange={(event) => updateArchiveControls(event.target.value, archiveSort)}
                    >
                      {archiveFilterOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="flex flex-col gap-1 text-sm text-neutral-300">
                    <span>Sort archive</span>
                    <select
                      className="rounded-lg border border-neutral-700 bg-black/50 px-3 py-2 text-sm text-white"
                      value={archiveSort}
                      onChange={(event) =>
                        updateArchiveControls(archiveFilter, event.target.value as ArchiveSort)
                      }
                    >
                      <option value={NEWEST_ARCHIVE_SORT}>Newest first</option>
                      <option value={OLDEST_ARCHIVE_SORT}>Oldest first</option>
                    </select>
                  </label>
                </div>
              </div>

              {archiveAnnouncements.length === 0 ? (
                <p className="mt-4 text-sm text-neutral-400">
                  No archived posts yet. New announcements will appear here after the latest post.
                </p>
              ) : visibleArchiveAnnouncements.length === 0 ? (
                <div className="mt-4 rounded-xl border border-neutral-800 bg-neutral-950 p-4 text-sm text-neutral-300">
                  <p>No archived announcements match the selected filter.</p>
                  <button
                    type="button"
                    className="mt-3 text-sm text-[#FFC72C] transition-colors hover:text-[#ffd65e]"
                    onClick={() => updateArchiveControls(ALL_ARCHIVE_FILTER, NEWEST_ARCHIVE_SORT)}
                  >
                    Reset to All / Newest
                  </button>
                </div>
              ) : (
                <div className="mt-4 grid items-start gap-4 md:grid-cols-2">
                  {visibleArchiveAnnouncements.map((item) => {
                    const isExpanded = Boolean(expandedAnnouncementIds[item.id]);
                    const announcementBodyId = `archive-announcement-body-${item.id}`;
                    const scopeLabels = getScopeLabels(item, gameNameBySlug);

                    return (
                      <article
                        key={item.id}
                        className="self-start overflow-hidden rounded-xl border border-neutral-800 bg-neutral-950"
                      >
                        <div className="p-4">
                          <p className="text-xs uppercase tracking-wide text-[#FFC72C]">
                            {formatPostedDate(item.created_at)}
                          </p>
                          <h4 className="mt-2 text-xl font-semibold">{item.title}</h4>
                          {scopeLabels.length > 0 && (
                            <p className="mt-1 text-xs uppercase tracking-wide text-neutral-400">
                              {scopeLabels.join(" | ")}
                            </p>
                          )}
                          <button
                            type="button"
                            className="mt-3 text-sm text-neutral-300 transition-colors hover:text-white"
                            aria-expanded={isExpanded}
                            aria-controls={announcementBodyId}
                            onClick={() => toggleArchiveAnnouncement(item.id)}
                          >
                            {isExpanded ? "Hide full announcement" : "Read full announcement"}
                          </button>
                          {isExpanded && (
                            <div id={announcementBodyId} className="mt-4">
                              <div className="h-44 w-full overflow-hidden rounded-lg bg-black">
                                {/* eslint-disable-next-line @next/next/no-img-element */}
                                <img
                                  src={resolveAnnouncementImage(item.image_url, apiUrl)}
                                  alt={item.title}
                                  className="h-full w-full object-cover opacity-85"
                                />
                              </div>
                              <p className="mt-3 whitespace-pre-line text-sm text-neutral-300">
                                {item.body}
                              </p>
                            </div>
                          )}
                        </div>
                      </article>
                    );
                  })}
                </div>
              )}
            </section>
          </>
        )}
      </main>
    </div>
  );
}
