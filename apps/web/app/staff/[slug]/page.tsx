"use client";

import { useEffect, useMemo, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useParams } from "next/navigation";

import { resolveContentImageUrl } from "@/lib/contentImages";
import TopActivityFeedBar from "../../components/TopActivityFeedBar";
import { StaffProfileDetail } from "@/types/StaffProfile";

const CATEGORY_LABELS: Record<string, string> = {
  coach: "Coach",
  captain: "Captain",
  faculty: "Faculty",
  advisor: "Advisor",
  staff: "Staff",
  other: "Other",
};

function normalizeEmailHref(email: string): string | null {
  const trimmed = email.trim();
  if (!trimmed || !trimmed.includes("@")) return null;
  return `mailto:${encodeURIComponent(trimmed)}`;
}

function resolveStaffImage(imageUrl: string | null, apiUrl: string): string {
  return resolveContentImageUrl(imageUrl, apiUrl, "staff");
}

function renderBulletSection(title: string, items: string[]) {
  if (!Array.isArray(items) || items.length === 0) return null;
  return (
    <section className="rounded-xl border border-gray-800 bg-gray-950/80 p-5">
      <h3 className="text-lg font-semibold text-[#FFC72C]">{title}</h3>
      <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-relaxed text-gray-200 md:text-base">
        {items.map((item, index) => (
          <li key={`${title}-${index}`}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

export default function StaffDetailPage() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const params = useParams<{ slug: string }>();
  const slug = typeof params?.slug === "string" ? params.slug : "";

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

  const [profile, setProfile] = useState<StaffProfileDetail | null>(null);
  const [isLive, setIsLive] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!slug) {
      setError("Staff profile not found.");
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    const load = async () => {
      try {
        const response = await fetch(`${apiUrl}/api/v1/staff/${encodeURIComponent(slug)}`);
        if (!response.ok) {
          throw new Error(response.status === 404 ? "Staff profile not found." : "Failed to load staff profile.");
        }
        const payload = (await response.json()) as StaffProfileDetail;
        if (!cancelled) setProfile(payload);
      } catch (err: unknown) {
        if (!cancelled) {
          setProfile(null);
          if (err instanceof Error) setError(err.message);
          else setError("Failed to load staff profile.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void load();
    return () => {
      cancelled = true;
    };
  }, [apiUrl, slug]);

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

  const emailHref = useMemo(() => {
    if (!profile?.email) return null;
    return normalizeEmailHref(profile.email);
  }, [profile?.email]);

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

      <main className="mx-auto w-full max-w-5xl px-6 pb-16 pt-8">
        <Link href="/staff" className="inline-flex items-center text-sm font-medium text-[#FFC72C] hover:text-[#ffd65e]">
          &larr; Back to Staff
        </Link>

        {loading ? (
          <section className="mt-6 rounded-xl border border-gray-700 bg-gray-900/60 px-6 py-10 text-center text-sm text-gray-300">
            Loading staff profile...
          </section>
        ) : error ? (
          <section className="mt-6 rounded-xl border border-red-700 bg-red-900/20 px-6 py-10 text-center text-sm text-red-200">
            {error}
          </section>
        ) : !profile ? (
          <section className="mt-6 rounded-xl border border-gray-700 bg-gray-900/60 px-6 py-10 text-center text-sm text-gray-300">
            Staff profile not found.
          </section>
        ) : (
          <div className="mt-6 space-y-6">
            <section className="rounded-2xl border border-gray-700 bg-gray-900/80 p-6 shadow-lg">
              <div className="flex flex-col gap-6 md:flex-row md:items-start">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={resolveStaffImage(profile.image_url, apiUrl)}
                  alt={profile.full_name}
                  className="h-40 w-40 rounded-full border border-gray-600 object-cover"
                />

                <div className="min-w-0 flex-1">
                  <p className="text-xs uppercase tracking-[0.25em] text-[#FFC72C]">
                    {CATEGORY_LABELS[profile.category] || "Staff"}
                  </p>
                  <h2 className="mt-2 text-3xl font-bold">{profile.full_name}</h2>
                  <p className="mt-2 text-lg font-semibold text-gray-200">{profile.title}</p>

                  <div className="mt-4 flex flex-wrap gap-2">
                    {(profile.game_scope || []).map((scope) => (
                      <span key={scope} className="rounded-full border border-gray-600 px-3 py-1 text-xs text-gray-200">
                        {scope}
                      </span>
                    ))}
                  </div>

                  <div className="mt-5 space-y-2 text-sm text-gray-200">
                    {emailHref && profile.email && (
                      <p>
                        <span className="font-semibold text-white">Email:</span>{" "}
                        <a href={emailHref} className="text-[#FFC72C] hover:text-[#ffd65e]">
                          {profile.email}
                        </a>
                      </p>
                    )}
                    {profile.phone && (
                      <p>
                        <span className="font-semibold text-white">Phone:</span> {profile.phone}
                      </p>
                    )}
                    {profile.year_label && (
                      <p>
                        <span className="font-semibold text-white">Year:</span> {profile.year_label}
                      </p>
                    )}
                    {profile.previous_college && (
                      <p>
                        <span className="font-semibold text-white">Previous College:</span> {profile.previous_college}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </section>

            {renderBulletSection("At Ashland University", profile.bio_at_ashland)}
            {renderBulletSection("Before Ashland University", profile.bio_before_ashland)}
            {renderBulletSection("Additional Notes & Responsibilities", profile.responsibilities)}
          </div>
        )}
      </main>
    </div>
  );
}
