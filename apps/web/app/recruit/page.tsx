"use client";

import { useState, useEffect, useMemo } from "react";
import Image from "next/image";
import Link from "next/link";

type GameSlug = "valorant" | "cs2" | "fortnite" | "r6";

type FormState = {
  first_name: string;
  last_name: string;
  email: string;
  discord: string;
  current_school: string;
  graduation_year: string;
  preferred_contact: string;
  hours_per_week: string;
  weeknights_available: boolean;
  weekends_available: boolean;
  game_slug: GameSlug;
  fortnite_mode: string;
  ign: string;
  current_rank_label: string;
  peak_rank_label: string;
  primary_role: string;
  secondary_role: string;
  tracker_url: string;
  team_experience: boolean;
  scrim_experience: boolean;
  tournament_experience: string;
};

type Match = {
  id: number;
  ourTeam: string;
  opponent: string;
  game: string;
  time: string;
};

const pages = [
  "Home",
  "Roster",
  "Schedule",
  "News",
  "Stream",
  "Recruitment",
  "Facility",
  "Support",
];

const pageMap: Record<string, string> = {
  Home: "/",
  Roster: "/roster",
  Schedule: "/schedule",
  News: "/news",
  Stream: "/stream",
  Recruitment: "/recruit",
  Facility: "/facility",
  Support: "/support",
};

const valorantRoles = [
  "Duelist",
  "Initiator",
  "Controller",
  "Sentinel",
  "IGL",
  "Flex",
];

const cs2Roles = [
  "Entry",
  "AWPer",
  "IGL",
  "Lurker",
  "Support",
  "Flex",
];

const fortniteRoles = [
  "IGL",
  "Fragger",
  "Support",
  "Flex",
];

const r6Roles = [
  "Entry",
  "Support",
  "Flex",
  "IGL",
  "Anchor",
  "Roamer",
];

const valorantRanks = [
  "Iron 1",
  "Iron 2",
  "Iron 3",
  "Bronze 1",
  "Bronze 2",
  "Bronze 3",
  "Silver 1",
  "Silver 2",
  "Silver 3",
  "Gold 1",
  "Gold 2",
  "Gold 3",
  "Platinum 1",
  "Platinum 2",
  "Platinum 3",
  "Diamond 1",
  "Diamond 2",
  "Diamond 3",
  "Ascendant 1",
  "Ascendant 2",
  "Ascendant 3",
  "Immortal 1",
  "Immortal 2",
  "Immortal 3",
  "Radiant",
];

const cs2RankExamples = [
  "Premier 18500",
  "Faceit 7",
  "LEM",
  "Global Elite",
];

const fortniteRanks = [
  "Bronze",
  "Silver",
  "Gold",
  "Platinum",
  "Diamond",
  "Elite",
  "Champion",
  "Unreal",
];

const r6Ranks = [
  "Copper",
  "Bronze",
  "Silver",
  "Gold",
  "Platinum",
  "Emerald",
  "Diamond",
  "Champion",
];

export default function RecruitPage() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const [form, setForm] = useState<FormState>({
    first_name: "",
    last_name: "",
    email: "",
    discord: "",
    current_school: "",
    graduation_year: "",
    preferred_contact: "discord",
    hours_per_week: "",
    weeknights_available: true,
    weekends_available: false,
    game_slug: "valorant",
    fortnite_mode: "",
    ign: "",
    current_rank_label: "",
    peak_rank_label: "",
    primary_role: "",
    secondary_role: "",
    tracker_url: "",
    team_experience: false,
    scrim_experience: false,
    tournament_experience: "none",
  });

  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const [matches, setMatches] = useState<Match[]>([]);
  const [matchStart, setMatchStart] = useState(0);
  const matchesToShow = 5;

  const roleOptions = useMemo(() => {
  if (form.game_slug === "valorant") return valorantRoles;
  if (form.game_slug === "cs2") return cs2Roles;
  if (form.game_slug === "fortnite") return fortniteRoles;
  return r6Roles;
}, [form.game_slug]);

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function resetGameFields(game: GameSlug) {
    setForm((prev) => ({
      ...prev,
      game_slug: game,
      fortnite_mode: "",
      ign: "",
      current_rank_label: "",
      peak_rank_label: "",
      primary_role: "",
      secondary_role: "",
      tracker_url: "",
      team_experience: false,
      scrim_experience: false,
      tournament_experience: "none",
    }));
  }

  useEffect(() => {
    const tryLoad = async () => {
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
            const parsed: Match[] = raw.map((r: any, i: number) => ({
              id: Number(r.id) || i + 1,
              ourTeam: r.ourTeam ?? r.OurTeam ?? r.Team ?? "Ashland",
              opponent: r.opponent ?? r.Opponent ?? r.Opp ?? "",
              game: r.game ?? r.Game ?? r.Platform ?? "",
              time: r.time ?? r.Time ?? r.datetime ?? "",
            }));
            setMatches(parsed);
            return;
          }
        }
      } catch {}

      try {
        const resC = await fetch("/data/matches.csv");
        if (resC.ok) {
          const txt = await resC.text();
          const rows = txt.trim().split("\n").map((r) => r.split(","));
          const headers = rows.shift() || [];

          const parsed: Match[] = rows.map((cols, i) => {
            const obj: Record<string, string> = {};
            headers.forEach((h, idx) => {
              obj[h.trim()] = cols[idx] ? cols[idx].trim() : "";
            });

            return {
              id: Number(obj.id) || i + 1,
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
      } catch {}

      try {
        const r = await fetch("/data/matches.json");
        if (!r.ok) throw new Error("failed");
        const data = await r.json();
        if (Array.isArray(data) && data.length) {
          setMatches(data);
        }
      } catch {}
    };

    tryLoad();
  }, []);

  const prevMatches = () => {
    setMatchStart((s) => Math.max(0, s - 1));
  };

  const nextMatches = () => {
    setMatchStart((s) =>
      Math.min(Math.max(0, matches.length - matchesToShow), s + 1)
    );
  };

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setSuccess(null);
    setLoading(true);

    try {
      const payload = {
        first_name: form.first_name,
        last_name: form.last_name,
        email: form.email,
        discord: form.discord,
        current_school: form.current_school || null,
        graduation_year: form.graduation_year
          ? Number(form.graduation_year)
          : null,
        preferred_contact: form.preferred_contact || null,
        availability: {
          hours_per_week: Number(form.hours_per_week),
          weeknights_available: form.weeknights_available,
          weekends_available: form.weekends_available,
        },
        game_slug: form.game_slug,
        profile: {
          ign: form.ign,
          fortnite_mode:
            form.game_slug === "fortnite" ? form.fortnite_mode : null,
          current_rank_label: form.current_rank_label,
          peak_rank_label: form.peak_rank_label || null,
          primary_role: form.primary_role,
          secondary_role: form.secondary_role || null,
          tracker_url: form.tracker_url || null,
          team_experience: form.team_experience,
          scrim_experience: form.scrim_experience,
          tournament_experience: form.tournament_experience,
        },
      };

      const res = await fetch(`${apiUrl}/api/v1/recruit/apply`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const text = await res.text();

      if (!res.ok) {
        throw new Error(text || "Failed to submit application");
      }

      const data = JSON.parse(text);

      setSuccess(
        `Application submitted successfully. Current score: ${data.score}`
      );

      setForm((prev) => ({
        ...prev,
        first_name: "",
        last_name: "",
        email: "",
        discord: "",
        current_school: "",
        graduation_year: "",
        preferred_contact: "discord",
        hours_per_week: "",
        weeknights_available: true,
        weekends_available: false,
        fortnite_mode: "",
        ign: "",
        current_rank_label: "",
        peak_rank_label: "",
        primary_role: "",
        secondary_role: "",
        tracker_url: "",
        team_experience: false,
        scrim_experience: false,
        tournament_experience: "none",
      }));
    } catch (e: any) {
      setErr(e?.message || "Submission failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="match-bar">
        <button
          className="match-arrow"
          onClick={prevMatches}
          aria-label="Previous matches"
          disabled={matchStart === 0}
        >
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
          className="match-arrow"
          onClick={nextMatches}
          aria-label="Next matches"
          disabled={matchStart >= matches.length - matchesToShow}
        >
          &rarr;
        </button>
      </div>

      <header className="site-header">
        <div className="flex items-center gap-2">
          <Image
            src="/Eagles (2).png"
            alt="Ashland Eagle Logo"
            width={90}
            height={90}
            className="h-20 w-20 object-contain"
          />
          <h1 className="title">Ashland University Esports</h1>
        </div>

        <nav className="nav-buttons">
          {pages.map((page) => {
            const href = pageMap[page] || "/";
            return (
              <Link key={page} href={href} className="hover:underline">
                {page}
              </Link>
            );
          })}
        </nav>
      </header>

      <main className="mx-auto max-w-5xl px-6 pb-12 pt-8">
        <div className="mb-6">
          <h2 className="text-3xl font-semibold">Recruitment</h2>
          <p className="mt-2 text-sm text-neutral-400">
            Submit your information to be considered for the AU Esports program.
          </p>
        </div>

        <form onSubmit={onSubmit} className="space-y-8">
          <section className="rounded-2xl border border-neutral-800 bg-neutral-950 p-5">
            <h3 className="text-xl font-medium">Basic Information</h3>

            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <Input
                label="First Name"
                value={form.first_name}
                onChange={(v) => update("first_name", v)}
                required
              />
              <Input
                label="Last Name"
                value={form.last_name}
                onChange={(v) => update("last_name", v)}
                required
              />
              <Input
                label="Email"
                type="email"
                value={form.email}
                onChange={(v) => update("email", v)}
                required
              />
              <Input
                label="Discord"
                value={form.discord}
                onChange={(v) => update("discord", v)}
                required
              />
              <Input
                label="Current School"
                value={form.current_school}
                onChange={(v) => update("current_school", v)}
              />
              <Input
                label="Graduation Year"
                value={form.graduation_year}
                onChange={(v) => update("graduation_year", v)}
              />

              <div>
                <label className="text-sm text-neutral-300">
                  Preferred Contact
                </label>
                <select
                  className="mt-1 w-full rounded-lg border border-neutral-800 bg-neutral-900 p-2"
                  value={form.preferred_contact}
                  onChange={(e) => update("preferred_contact", e.target.value)}
                >
                  <option value="discord">Discord</option>
                  <option value="email">Email</option>
                </select>
              </div>
            </div>
          </section>

          <section className="rounded-2xl border border-neutral-800 bg-neutral-950 p-5">
            <h3 className="text-xl font-medium">Availability</h3>

            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <Input
                label="Hours per Week"
                value={form.hours_per_week}
                onChange={(v) => update("hours_per_week", v)}
                required
              />

              <div className="flex flex-col gap-3 pt-6">
                <label className="flex items-center gap-2 text-sm text-neutral-300">
                  <input
                    type="checkbox"
                    checked={form.weeknights_available}
                    onChange={(e) =>
                      update("weeknights_available", e.target.checked)
                    }
                  />
                  Available on weeknights
                </label>

                <label className="flex items-center gap-2 text-sm text-neutral-300">
                  <input
                    type="checkbox"
                    checked={form.weekends_available}
                    onChange={(e) =>
                      update("weekends_available", e.target.checked)
                    }
                  />
                  Available on weekends
                </label>
              </div>
            </div>
          </section>

          <section className="rounded-2xl border border-neutral-800 bg-neutral-950 p-5">
            <h3 className="text-xl font-medium">Game Selection</h3>

            <div className="mt-4">
              <label className="text-sm text-neutral-300">Game</label>
              <select
                className="mt-1 w-full rounded-lg border border-neutral-800 bg-neutral-900 p-2"
                value={form.game_slug}
                onChange={(e) =>
                  resetGameFields(e.target.value as GameSlug)
                }
              >
                <option value="valorant">Valorant</option>
                <option value="cs2">Counter-Strike 2</option>
                <option value="fortnite">Fortnite</option>
                <option value="r6">Rainbow Six Siege</option>
              </select>
            </div>

            <div className="mt-6 grid gap-4 md:grid-cols-2">
              {form.game_slug === "fortnite" && (
                <div>
                  <label className="text-sm text-neutral-300">Fortnite Mode</label>
                  <select
                    className="mt-1 w-full rounded-lg border border-neutral-800 bg-neutral-900 p-2"
                    value={form.fortnite_mode}
                    onChange={(e) => update("fortnite_mode", e.target.value)}
                    required
                  >
                    <option value="">Select a mode</option>
                    <option value="builds">Builds</option>
                    <option value="zero_builds">Zero Builds</option>
                  </select>
                </div>
              )}
              <Input
                label="In-Game Name"
                value={form.ign}
                onChange={(v) => update("ign", v)}
                required
              />

              <div>
                <label className="text-sm text-neutral-300">Current Rank</label>

                {form.game_slug === "valorant" ? (
                  <select
                    className="mt-1 w-full rounded-lg border border-neutral-800 bg-neutral-900 p-2"
                    value={form.current_rank_label}
                    onChange={(e) =>
                      update("current_rank_label", e.target.value)
                    }
                    required
                  >
                    <option value="">Select a rank</option>
                    {valorantRanks.map((rank) => (
                      <option key={rank} value={rank}>
                        {rank}
                      </option>
                    ))}
                  </select>
                ) : form.game_slug === "fortnite" ? (
                  <select
                    className="mt-1 w-full rounded-lg border border-neutral-800 bg-neutral-900 p-2"
                    value={form.current_rank_label}
                    onChange={(e) => update("current_rank_label", e.target.value)}
                    required
                  >
                    <option value="">Select a rank</option>
                    {fortniteRanks.map((rank) => (
                      <option key={rank} value={rank}>
                        {rank}
                      </option>
                    ))}
                  </select>
                ) : form.game_slug === "r6" ? (
                  <select
                   className="mt-1 w-full rounded-lg border border-neutral-800 bg-neutral-900 p-2"
                   value={form.current_rank_label}
                   onChange={(e) => update("current_rank_label", e.target.value)}
                   required
                  >
                    <option value="">Select a rank</option>
                    {r6Ranks.map((rank) => (
                      <option key={rank} value={rank}>
                        {rank}
                      </option>
                    ))}
                  </select>
                ) : (
                  <>
                    <input
                      className="mt-1 w-full rounded-lg border border-neutral-800 bg-neutral-900 p-2"
                      value={form.current_rank_label}
                      onChange={(e) =>
                        update("current_rank_label", e.target.value)
                      }
                      placeholder="Example: Faceit 7 or Premier 18500"
                      required
                    />
                    <p className="mt-1 text-xs text-neutral-500">
                      Examples: {cs2RankExamples.join(", ")}
                    </p>
                  </>
                )}
              </div>

              <Input
                label="Peak Rank"
                value={form.peak_rank_label}
                onChange={(v) => update("peak_rank_label", v)}
              />

              <div>
                <label className="text-sm text-neutral-300">Primary Role</label>
                <select
                  className="mt-1 w-full rounded-lg border border-neutral-800 bg-neutral-900 p-2"
                  value={form.primary_role}
                  onChange={(e) => update("primary_role", e.target.value)}
                  required
                >
                  <option value="">Select a role</option>
                  {roleOptions.map((role) => (
                    <option key={role} value={role}>
                      {role}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-sm text-neutral-300">
                  Secondary Role
                </label>
                <select
                  className="mt-1 w-full rounded-lg border border-neutral-800 bg-neutral-900 p-2"
                  value={form.secondary_role}
                  onChange={(e) => update("secondary_role", e.target.value)}
                >
                  <option value="">Select a role</option>
                  {roleOptions.map((role) => (
                    <option key={role} value={role}>
                      {role}
                    </option>
                  ))}
                </select>
              </div>

              <Input
                label="Tracker / Profile URL"
                value={form.tracker_url}
                onChange={(v) => update("tracker_url", v)}
              />

              <div>
                <label className="text-sm text-neutral-300">
                  Tournament Experience
                </label>
                <select
                  className="mt-1 w-full rounded-lg border border-neutral-800 bg-neutral-900 p-2"
                  value={form.tournament_experience}
                  onChange={(e) =>
                    update("tournament_experience", e.target.value)
                  }
                >
                  <option value="none">None</option>
                  <option value="local">Local</option>
                  <option value="regional">Regional</option>
                  <option value="national">National</option>
                </select>
              </div>

              <div className="flex flex-col gap-3 pt-6">
                <label className="flex items-center gap-2 text-sm text-neutral-300">
                  <input
                    type="checkbox"
                    checked={form.team_experience}
                    onChange={(e) =>
                      update("team_experience", e.target.checked)
                    }
                  />
                  Team experience
                </label>

                <label className="flex items-center gap-2 text-sm text-neutral-300">
                  <input
                    type="checkbox"
                    checked={form.scrim_experience}
                    onChange={(e) =>
                      update("scrim_experience", e.target.checked)
                    }
                  />
                  Scrim experience
                </label>
              </div>
            </div>
          </section>

          <div className="flex flex-col gap-3">
            <button
              type="submit"
              disabled={loading}
              className="rounded-xl bg-white px-5 py-3 font-medium text-black disabled:opacity-60"
            >
              {loading ? "Submitting..." : "Submit Application"}
            </button>

            

            {err && (
              <div className="whitespace-pre-wrap rounded-lg border border-red-700 bg-red-950 p-3 text-sm text-red-300">
                {err}
              </div>
            )}
          </div>
        </form>
      </main>
    </div>
  );
}

function Input({
  label,
  value,
  onChange,
  required = false,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  type?: string;
}) {
  return (
    <div>
      <label className="text-sm text-neutral-300">{label}</label>
      <input
        className="mt-1 w-full rounded-lg border border-neutral-800 bg-neutral-900 p-2"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required={required}
        type={type}
      />
    </div>
  );
}