"use client";

import { useEffect, useMemo, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import Header from "../components/Header";

type Match = {
  id: number;
  ourTeam: string;
  opponent: string;
  game: string;
  time: string;
};

type Announcement = {
  id: number;
  title: string;
  body: string;
  image_url: string | null;
  created_at: string;
  updated_at: string | null;
};

const DEFAULT_NEWS_PLACEHOLDER = "/images/esports-news-placeholder.jpg";

function resolveAnnouncementImage(imageUrl: string | null, apiUrl: string): string {
  if (!imageUrl || !imageUrl.trim()) return DEFAULT_NEWS_PLACEHOLDER;
  if (imageUrl.startsWith("http://") || imageUrl.startsWith("https://")) return imageUrl;
  if (imageUrl.startsWith("/uploads")) return `${apiUrl}${imageUrl}`;
  if (imageUrl.startsWith("/")) return imageUrl;
  return `${apiUrl}/${imageUrl}`;
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

  const [matches, setMatches] = useState<Match[]>([]);
  const [matchStart, setMatchStart] = useState(0);
  const matchesToShow = 5;
  const [isLive, setIsLive] = useState(false);

  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [loadingNews, setLoadingNews] = useState(true);
  const [newsError, setNewsError] = useState<string | null>(null);
  const [expandedAnnouncementIds, setExpandedAnnouncementIds] = useState<Record<number, boolean>>({});

  useEffect(() => {
    const tryLoadMatches = async () => {
      try {
        const resX = await fetch("/data/matches.xlsx");
        if (resX.ok) {
          const buffer = await resX.arrayBuffer();
          const XLSX = await import("xlsx").catch(() => null);
          if (!XLSX) throw new Error("xlsx not available");
          const wb = XLSX.read(buffer, { type: "array" });
          const sheetName = wb.SheetNames[0];
          const ws = wb.Sheets[sheetName];
          const raw = XLSX.utils.sheet_to_json(ws, { defval: "" });
          if (Array.isArray(raw) && raw.length) {
            const pickString = (
              row: Record<string, unknown>,
              ...keys: string[]
            ): string | undefined => {
              for (const key of keys) {
                const value = row[key];
                if (typeof value === "string" && value.trim()) return value;
              }
              return undefined;
            };

            const parsed: Match[] = raw.map((row, index) => {
              const record = row as Record<string, unknown>;
              return {
                id: Number(record.id) || index + 1,
                ourTeam: pickString(record, "ourTeam", "OurTeam", "Team") || "Ashland",
                opponent: pickString(record, "opponent", "Opponent", "Opp") || "",
                game: pickString(record, "game", "Game", "Platform") || "",
                time: pickString(record, "time", "Time", "datetime") || "",
              };
            });
            setMatches(parsed);
            return;
          }
        }
      } catch {
        // Best-effort data loading. Falls through to CSV/JSON.
      }

      try {
        const resC = await fetch("/data/matches.csv");
        if (resC.ok) {
          const txt = await resC.text();
          const rows = txt.trim().split("\n").map((row) => row.split(","));
          const headers = rows.shift() || [];
          const parsed: Match[] = rows.map((cols, index) => {
            const obj: Record<string, string> = {};
            headers.forEach((header, headerIndex) => {
              obj[header.trim()] = cols[headerIndex] ? cols[headerIndex].trim() : "";
            });
            return {
              id: Number(obj.id) || index + 1,
              ourTeam: obj.ourTeam || obj.OurTeam || "Ashland",
              opponent: obj.opponent || obj.Opponent || "",
              game: obj.game || obj.Game || "",
              time: obj.time || obj.Time || "",
            };
          });
          if (parsed.length) {
            setMatches(parsed);
            return;
          }
        }
      } catch {
        // Best-effort data loading. Falls through to JSON.
      }

      try {
        const response = await fetch("/data/matches.json");
        if (!response.ok) throw new Error("Failed to load JSON matches");
        const data = await response.json();
        if (Array.isArray(data) && data.length) {
          setMatches(data as Match[]);
        }
      } catch {
        setMatches([]);
      }
    };

    tryLoadMatches();
  }, []);

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

  const featuredAnnouncement = useMemo(() => announcements[0] ?? null, [announcements]);
  const archiveAnnouncements = useMemo(() => announcements.slice(1), [announcements]);
  const toggleArchiveAnnouncement = (announcementId: number) => {
    setExpandedAnnouncementIds((current) => ({
      ...current,
      [announcementId]: !current[announcementId],
    }));
  };

  const prevMatches = () => setMatchStart((current) => Math.max(0, current - 1));
  const nextMatches = () =>
    setMatchStart((current) => Math.min(Math.max(0, matches.length - matchesToShow), current + 1));

  return (
    <div className="min-h-screen bg-black text-white">
    
          <div className="grid grid-cols-3 items-center w-full px-4">
    
            <div className="justify-self-start">
              <Header />
            </div>
    
            <div className="justify-self-center">
              <div className="match-bar inline-flex items-center">
                <button onClick={prevMatches} disabled={matchStart === 0}>
                  &larr;
                </button>
    
                <div className="match-list">
                  {matches.slice(matchStart, matchStart + matchesToShow).map((m) => (
                    <div className="match-item" key={m.id}>
                      <div className="match-teams">
                        <span className="team-name">{m.ourTeam}</span>
                        <span className="versus">vs</span>
                        <span className="team-opponent">{m.opponent}</span>
                      </div>
                      <div className="match-game">{m.game}</div>
                      <div className="match-time">{m.time}</div>
                    </div>
                  ))}
                </div>
    
                <button
                  onClick={nextMatches}
                  disabled={matchStart >= matches.length - matchesToShow}
                >
                  &rarr;
                </button>
              </div>
            </div>
    
            <div />
    
          </div>

      <header className="site-header flex flex-col items-center justify-between gap-4 p-4 md:flex-row">
        <div className="flex items-center gap-2">
          <Image
            src="/Eagles (2).png"
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
                <span className="text-sm text-neutral-400">{archiveAnnouncements.length} past posts</span>
              </div>

              {archiveAnnouncements.length === 0 ? (
                <p className="mt-4 text-sm text-neutral-400">
                  No archived posts yet. New announcements will appear here after the latest post.
                </p>
              ) : (
                <div className="mt-4 grid items-start gap-4 md:grid-cols-2">
                  {archiveAnnouncements.map((item) => {
                    const isExpanded = Boolean(expandedAnnouncementIds[item.id]);
                    const announcementBodyId = `archive-announcement-body-${item.id}`;

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
