"use client";

import { useEffect, useMemo, useState } from "react";
import Image from "next/image";
import Link from "next/link";

import StaffCard from "@/components/StaffCard";
import TopActivityFeedBar from "../components/TopActivityFeedBar";
import { StaffCategory, StaffProfileSummary } from "@/types/StaffProfile";

const CATEGORY_LABELS: Record<StaffCategory, string> = {
  coach: "Coaches",
  captain: "Captains",
  faculty: "Faculty",
  advisor: "Advisors",
  staff: "Staff",
  other: "Other",
};

const CATEGORY_ORDER: StaffCategory[] = ["coach", "captain", "faculty", "advisor", "staff", "other"];

type FilterOption = {
  value: string;
  label: string;
};

function normalizeScopeLabel(raw: string): string {
  const trimmed = raw.trim();
  return trimmed || "All Teams";
}

export default function StaffPage() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const pages = ["Home", "Roster", "Staff", "Schedule", "News", "Stream", "Recruitment", "Facility", "Support", "Hall of Fame"];

  const pageMap: { [key: string]: string } = {
    Home: "/",
    Roster: "/roster",
    Staff: "/staff",
    Schedule: "/schedule",
    News: "/news",
    Stream: "/stream",
    Recruitment: "/recruit",
    Facility: "/facility",
    Support: "/support",
    "Hall of Fame": "/hof",
  };

  const [profiles, setProfiles] = useState<StaffProfileSummary[]>([]);
  const [isLive, setIsLive] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [selectedGame, setSelectedGame] = useState<string>("all");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    const load = async () => {
      try {
        const response = await fetch(`${apiUrl}/api/v1/staff`);
        if (!response.ok) throw new Error("Failed to load staff profiles.");
        const payload = (await response.json()) as StaffProfileSummary[];
        if (!cancelled) {
          setProfiles(Array.isArray(payload) ? payload : []);
        }
      } catch {
        if (!cancelled) {
          setProfiles([]);
          setError("Failed to load staff profiles.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void load();
    return () => {
      cancelled = true;
    };
  }, [apiUrl]);

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

  const categoryOptions = useMemo<FilterOption[]>(() => {
    const seen = new Set<string>();
    const options: FilterOption[] = [{ value: "all", label: "All Categories" }];
    for (const category of CATEGORY_ORDER) {
      if (!profiles.some((profile) => profile.category === category)) continue;
      if (seen.has(category)) continue;
      seen.add(category);
      options.push({ value: category, label: CATEGORY_LABELS[category] });
    }
    return options;
  }, [profiles]);

  const gameOptions = useMemo<FilterOption[]>(() => {
    const seen = new Set<string>();
    const options: FilterOption[] = [{ value: "all", label: "All Teams" }];
    for (const profile of profiles) {
      const scopes = Array.isArray(profile.game_scope) ? profile.game_scope : [];
      for (const scope of scopes) {
        const normalized = normalizeScopeLabel(scope);
        const key = normalized.toLowerCase();
        if (seen.has(key)) continue;
        seen.add(key);
        options.push({ value: normalized, label: normalized });
      }
    }
    return options.sort((a, b) => {
      if (a.value === "all") return -1;
      if (b.value === "all") return 1;
      return a.label.localeCompare(b.label);
    });
  }, [profiles]);

  const filteredProfiles = useMemo(() => {
    return profiles.filter((profile) => {
      const categoryMatch = selectedCategory === "all" || profile.category === selectedCategory;
      const gameMatch =
        selectedGame === "all" ||
        (Array.isArray(profile.game_scope) &&
          profile.game_scope.some((scope) => normalizeScopeLabel(scope).toLowerCase() === selectedGame.toLowerCase()));
      return categoryMatch && gameMatch;
    });
  }, [profiles, selectedCategory, selectedGame]);

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
            <h1 className="title title-3d text-lg font-bold tracking-wide md:text-2xl" style={{ textShadow: "1px 1px #333" }}>
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

      <main className="mx-auto w-full max-w-6xl px-6 pb-16 pt-8">
        <section className="mb-7">
          <p className="text-xs uppercase tracking-[0.3em] text-[#FFC72C]/90">Program Leadership</p>
          <h2 className="mt-2 text-3xl font-bold md:text-4xl">Staff &amp; Leadership</h2>
          <p className="mt-3 max-w-3xl text-sm text-neutral-300 md:text-base">
            Meet the coaches, captains, advisors, and staff members supporting Ashland University Esports.
          </p>
        </section>

        <section className="mb-6 grid w-full max-w-3xl gap-4 md:grid-cols-2">
          <label className="text-sm text-gray-200">
            <span className="mb-2 block font-medium">Filter by category</span>
            <select
              className="w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
              value={selectedCategory}
              onChange={(event) => setSelectedCategory(event.target.value)}
            >
              {categoryOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="text-sm text-gray-200">
            <span className="mb-2 block font-medium">Filter by team scope</span>
            <select
              className="w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
              value={selectedGame}
              onChange={(event) => setSelectedGame(event.target.value)}
            >
              {gameOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </section>

        {error && (
          <section className="mb-6 rounded-xl border border-red-700 bg-red-900/20 px-6 py-4 text-sm text-red-200">
            {error}
          </section>
        )}

        {loading ? (
          <section className="rounded-xl border border-gray-700 bg-gray-900/60 px-6 py-10 text-center text-sm text-gray-300">
            Loading staff profiles...
          </section>
        ) : filteredProfiles.length === 0 ? (
          <section className="rounded-xl border border-gray-700 bg-gray-900/60 px-6 py-10 text-center text-sm text-gray-300">
            Staff profiles will appear here soon.
          </section>
        ) : (
          <section className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3">
            {filteredProfiles.map((profile) => (
              <StaffCard key={profile.id} profile={profile} />
            ))}
          </section>
        )}
      </main>
    </div>
  );
}
