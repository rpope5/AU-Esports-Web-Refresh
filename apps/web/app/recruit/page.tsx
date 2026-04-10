"use client";

import { useState, useEffect, useMemo } from "react";
import Image from "next/image";
import Link from "next/link";

type GameSlug = "valorant" | "cs2" | "fortnite" | "r6" | "rocket-league" | "overwatch" | "cod" | "hearthstone" | "smash" | "mario-kart";

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
  epic_games_name: string;
  fortnite_pr: string;
  fortnite_kd: string;
  fortnite_total_kills: string;
  fortnite_playtime_hours: string;
  fortnite_wins: string;
  faceit_level: string;
  faceit_elo: string;
  cs2_roles: string;
  prior_team_history: string;
  ign: string;
  current_rank_label: string;
  peak_rank_label: string;
  primary_role: string;
  secondary_role: string;
  tracker_url: string;
  team_experience: boolean;
  scrim_experience: boolean;
  tournament_experience: string;
  tournament_experience_details: string;
  ranked_wins: string;
  years_played: string;
  legend_peak_rank: string;
  preferred_format: string;
  other_card_games: string;
  gsp: string;
  regional_rank: string;
  best_wins: string;
  characters: string;
  lounge_rating: string;
  preferred_title: string;
  controller_type: string;
  playstyle: string;
  preferred_tracks: string;
};

type Match = {
  id: number;
  ourTeam: string;
  opponent: string;
  game: string;
  time: string;
};

const graduationYears = Array.from({ length: 7 }, (_, i) => String(new Date().getFullYear() + i));

const pages = [
  "Home",
  "Roster",
  "Schedule",
  "News",
  "Stream",
  "Recruitment",
  "Facility",
  "Support",
  "Hall of Fame",
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
  "Hall of Fame": "/hof",
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

const rocketLeagueRoles = [
  "Striker",
  "Third Man",
  "Support",
  "Flex",
];

const overwatchRoles = [
  "Tank",
  "DPS",
  "Support",
  "Flex",
];

const codRoles = [
  "SMG",
  "AR",
  "Flex",
  "Main AR",
  "OBJ",
  "Slayer",
  "Role Player",
];

const hearthstoneClasses = [
  "Death Knight",
  "Demon Hunter",
  "Druid",
  "Hunter",
  "Mage",
  "Paladin",
  "Priest",
  "Rogue",
  "Shaman",
  "Warlock",
  "Warrior",
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

const rocketLeagueRanks = [
  "Bronze",
  "Silver",
  "Gold",
  "Platinum",
  "Diamond",
  "Champion",
  "Grand Champion",
  "Supersonic Legend",
];

const overwatchRanks = [
  "Bronze",
  "Silver",
  "Gold",
  "Platinum",
  "Diamond",
  "Master",
  "Grandmaster",
  "Top 500",
];

const codRanks = [
  "Bronze",
  "Silver",
  "Gold",
  "Platinum",
  "Diamond",
  "Crimson",
  "Iridescent",
  "Top 250",
];

const hearthstoneRanks = [
  ...Array.from({ length: 5 }, (_, i) => `Bronze ${5 - i}`),
  ...Array.from({ length: 10 }, (_, i) => `Silver ${10 - i}`),
  ...Array.from({ length: 10 }, (_, i) => `Gold ${10 - i}`),
  ...Array.from({ length: 10 }, (_, i) => `Platinum ${10 - i}`),
  ...Array.from({ length: 10 }, (_, i) => `Diamond ${10 - i}`),
  "Legend",
];

const smashCharacters = [
  "Mario",
  "Donkey Kong",
  "Link",
  "Samus",
  "Dark Samus",
  "Yoshi",
  "Kirby",
  "Fox",
  "Pikachu",
  "Luigi",
  "Ness",
  "Captain Falcon",
  "Jigglypuff",
  "Peach",
  "Daisy",
  "Bowser",
  "Ice Climbers",
  "Sheik",
  "Zelda",
  "Dr. Mario",
  "Pichu",
  "Falco",
  "Marth",
  "Lucina",
  "Young Link",
  "Ganondorf",
  "Mewtwo",
  "Roy",
  "Chrom",
  "Mr. Game & Watch",
  "Meta Knight",
  "Pit",
  "Dark Pit",
  "Zero Suit Samus",
  "Wario",
  "Snake",
  "Ike",
  "Pokémon Trainer",
  "Diddy Kong",
  "Lucas",
  "Sonic",
  "King Dedede",
  "Olimar",
  "Lucario",
  "R.O.B.",
  "Toon Link",
  "Wolf",
  "Villager",
  "Mega Man",
  "Wii Fit Trainer",
  "Rosalina & Luma",
  "Little Mac",
  "Greninja",
  "Mii Brawler",
  "Mii Swordfighter",
  "Mii Gunner",
  "Palutena",
  "Pac-Man",
  "Robin",
  "Shulk",
  "Bowser Jr.",
  "Duck Hunt",
  "Ryu",
  "Ken",
  "Cloud",
  "Corrin",
  "Bayonetta",
  "Inkling",
  "Ridley",
  "Simon",
  "Richter",
  "King K. Rool",
  "Isabelle",
  "Incineroar",
  "Piranha Plant",

  // DLC Fighters Pass 1
  "Joker",
  "Hero",
  "Banjo & Kazooie",
  "Terry",
  "Byleth",

  // DLC Fighters Pass 2
  "Min Min",
  "Steve",
  "Sephiroth",
  "Pyra/Mythra",
  "Kazuya",
  "Sora"
];

const marioKartTitles = [
  "Mario Kart 8 Deluxe",
  "Mario Kart World",
  "Both",
];

const marioKartPlaystyles = [
  "Front-runner",
  "Bagging",
  "Support",
  "Flex",
];

const marioKartControllers = [
  "Joy-Con",
  "Pro Controller",
  "GameCube Controller",
  "Other",
];
const marioKartTournamentDetailLevels = new Set(["local", "regional", "national"]);

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
    epic_games_name: "",
    fortnite_pr: "",
    fortnite_kd: "",
    fortnite_total_kills: "",
    fortnite_playtime_hours: "",
    fortnite_wins: "",
    faceit_level: "",
    faceit_elo: "",
    cs2_roles: "",
    prior_team_history: "",
    ign: "",
    current_rank_label: "",
    peak_rank_label: "",
    primary_role: "",
    secondary_role: "",
    tracker_url: "",
    team_experience: false,
    scrim_experience: false,
    tournament_experience: "none",
    tournament_experience_details: "",

    ranked_wins: "",
    years_played: "",
    legend_peak_rank: "",
    preferred_format: "",
    other_card_games: "",

    gsp: "",
    regional_rank: "",
    best_wins: "",
    characters: "",

    lounge_rating: "",
    preferred_title: "",
    controller_type: "",
    playstyle: "",
    preferred_tracks: "",
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
  if (form.game_slug === "r6") return r6Roles;
  if (form.game_slug === "rocket-league") return rocketLeagueRoles;
  if (form.game_slug === "overwatch") return overwatchRoles;
  if (form.game_slug === "cod") return codRoles;
  if (form.game_slug === "hearthstone") return hearthstoneClasses;
  if (form.game_slug === "mario-kart") return marioKartPlaystyles;
  return [];
}, [form.game_slug]);

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function updateTournamentExperience(value: string) {
    setForm((prev) => ({
      ...prev,
      tournament_experience: value,
      tournament_experience_details:
        prev.game_slug === "mario-kart" && !marioKartTournamentDetailLevels.has(value)
          ? ""
          : prev.tournament_experience_details,
    }));
  }

  function resetGameFields(game: GameSlug) {
    setForm((prev) => ({
      ...prev,
      game_slug: game,
      fortnite_mode: "",
      epic_games_name: "",
      fortnite_pr: "",
      fortnite_kd: "",
      fortnite_total_kills: "",
      fortnite_playtime_hours: "",
      fortnite_wins: "",
      faceit_level: "",
      faceit_elo: "",
      cs2_roles: "",
      prior_team_history: "",
      ign: "",
      current_rank_label: "",
      peak_rank_label: "",
      primary_role: "",
      secondary_role: "",
      tracker_url: "",
      team_experience: false,
      scrim_experience: false,
      tournament_experience: "none",
      tournament_experience_details: "",

      ranked_wins: "",
      years_played: "",
      legend_peak_rank: "",
      preferred_format: game === "hearthstone" ? "Standard" : "",
      other_card_games: "",

      gsp: "",
      regional_rank: "",
      best_wins: "",
      characters: "",

      lounge_rating: "",
      preferred_title: "",
      controller_type: "",
      playstyle: "",
      preferred_tracks: "",
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
          ign: form.game_slug === "smash" ? null : form.ign || null,
          fortnite_mode:
            form.game_slug === "fortnite" ? form.fortnite_mode : null,
          epic_games_name:
            form.game_slug === "fortnite" ? form.epic_games_name || null : null,
          fortnite_pr:
            form.game_slug === "fortnite" && form.fortnite_pr
              ? Number(form.fortnite_pr)
              : null,
          fortnite_kd:
            form.game_slug === "fortnite" && form.fortnite_kd
              ? Number(form.fortnite_kd)
              : null,
          fortnite_total_kills:
            form.game_slug === "fortnite" && form.fortnite_total_kills
              ? Number(form.fortnite_total_kills)
              : null,
          fortnite_playtime_hours:
            form.game_slug === "fortnite" && form.fortnite_playtime_hours
              ? Number(form.fortnite_playtime_hours)
              : null,
          fortnite_wins:
            form.game_slug === "fortnite" && form.fortnite_wins
              ? Number(form.fortnite_wins)
              : null,
          faceit_level:
            form.game_slug === "cs2" && form.faceit_level
              ? Number(form.faceit_level)
              : null,
          faceit_elo:
            form.game_slug === "cs2" && form.faceit_elo
              ? Number(form.faceit_elo)
              : null,
          cs2_roles:
            form.game_slug === "cs2" ? form.cs2_roles || null : null,
          prior_team_history:
            form.game_slug === "cs2" ? form.prior_team_history || null : null,
          current_rank_label:
            form.game_slug === "smash" ? null : form.current_rank_label || null,
          peak_rank_label:
            form.game_slug === "smash" ? null : form.peak_rank_label || null,
          primary_role:
            form.game_slug === "smash" ? null : form.primary_role || null,
          secondary_role:
            form.game_slug === "smash" ? null : form.secondary_role || null,
          tracker_url: form.tracker_url || null,
          team_experience: form.team_experience,
          scrim_experience: form.scrim_experience,
          tournament_experience: form.tournament_experience,
          tournament_experience_details:
            form.game_slug === "mario-kart" &&
            marioKartTournamentDetailLevels.has(form.tournament_experience)
              ? form.tournament_experience_details || null
              : null,

          ranked_wins: form.ranked_wins ? Number(form.ranked_wins) : null,
          years_played: form.years_played ? Number(form.years_played) : null,
          legend_peak_rank: form.legend_peak_rank
            ? Number(form.legend_peak_rank)
            : null,
          preferred_format: form.game_slug === "hearthstone" ? "Standard" : null,
          other_card_games: form.other_card_games || null,

          gsp: form.gsp ? Number(form.gsp) : null,
          regional_rank: form.regional_rank || null,
          best_wins: form.best_wins || null,
          characters: form.characters || null,

          lounge_rating: form.lounge_rating ? Number(form.lounge_rating) : null,
          preferred_title: form.preferred_title || null,
          controller_type: form.controller_type || null,
          playstyle: form.playstyle || null,
          preferred_tracks: form.preferred_tracks || null,
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
        `Application submitted successfully.`
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
        epic_games_name: "",
        fortnite_pr: "",
        fortnite_kd: "",
        fortnite_total_kills: "",
        fortnite_playtime_hours: "",
        fortnite_wins: "",
        faceit_level: "",
        faceit_elo: "",
        cs2_roles: "",
        prior_team_history: "",
        ign: "",
        current_rank_label: "",
        peak_rank_label: "",
        primary_role: "",
        secondary_role: "",
        tracker_url: "",
        team_experience: false,
        scrim_experience: false,
        tournament_experience: "none",
        tournament_experience_details: "",

        ranked_wins: "",
        years_played: "",
        legend_peak_rank: "",
        preferred_format: "",
        other_card_games: "",

        gsp: "",
        regional_rank: "",
        best_wins: "",
        characters: "",
      }));
    } catch (e: any) {
      setErr(e?.message || "Submission failed");
    } finally {
      setLoading(false);
    }
  }
const [isLive, setIsLive] = useState(false);

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
  return (
    <div className="min-h-screen bg-black text-white recruit-dropdown-theme">
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

      <header className="site-header flex flex-col md:flex-row items-center justify-between p-4 gap-4">

        <div className="flex items-center gap-2">
          <Image
            src="/Eagles (2).png"
            alt="Ashland Eagle Logo"
            width={90}
            height={90}
            className="w-14 h-14 md:w-20 md:h-20 object-contain"
          />

          <div className="flex items-center gap-3">
            <h1
              className="title title-3d text-lg md:text-2xl font-bold tracking-wide"
              style={{ textShadow: "1px 1px #333" }}
            >
              Ashland University Esports
            </h1>

            {isLive && (
              <div className="flex items-center gap-2">
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#FFC72C] opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-[#FFC72C]"></span>
                </span>

                <span className="text-[#FFC72C] text-sm font-semibold">
                  LIVE
                </span>
              </div>
            )}
          </div>
        </div>

        <nav className="nav-buttons flex flex-wrap justify-center gap-6 text-sm md:text-base">
          {pages.map((page) => {
            const href = pageMap[page] || "/";

            return (
              <Link key={page} href={href} className="relative group">
                {page}
                <span className="absolute left-0 -bottom-1 w-0 h-[2px] bg-[#FFC72C] transition-all duration-300 group-hover:w-full"></span>
              </Link>
            );
          })}
        </nav>

      </header>
      <div className="w-full h-[2px] bg-gradient-to-r from-transparent via-[#FFC72C] to-transparent opacity-70"></div>
      <main className="mx-auto max-w-5xl px-6 pb-12 pt-8">
        <div className="mb-8 rounded-xl bg-gradient-to-r from-[#5C068C] to-[#7a1a9f] p-6 border border-[#FFC72C]/30">
          <h2 className="text-4xl font-bold text-[#FFC72C]">Recruitment</h2>
          <p className="mt-3 text-sm text-neutral-200">
            Submit your information to be considered for the AU Esports program.
            We have opportunities for scholarships through our athletics department!
          </p>
        </div>

        <form onSubmit={onSubmit} className="space-y-8">
          <section className="rounded-2xl border-2 border-[#FFC72C] bg-neutral-950 p-6 shadow-lg shadow-[#5C068C]/20">
            <h3 className="text-xl font-semibold text-[#FFC72C]">Basic Information</h3>

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
              <div>
                <label className="text-sm font-medium text-[#FFC72C]">Graduation Year</label>
                <select
                  className="mt-1 w-full rounded-lg border border-[#FFC72C]/30 bg-neutral-900/50 p-3 text-white focus:border-[#FFC72C]/80 focus:outline-none focus:ring-1 focus:ring-[#FFC72C]/50 transition-colors"
                  value={form.graduation_year}
                  onChange={(e) => update("graduation_year", e.target.value)}
                >
                  <option value="">Select graduation year</option>
                  {graduationYears.map((year) => (
                    <option key={year} value={year}>
                      {year}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-[#FFC72C]">
                  Preferred Contact
                </label>
                <select
                  className="mt-1 w-full rounded-lg border border-[#FFC72C]/30 bg-neutral-900/50 p-3 text-white focus:border-[#FFC72C]/80 focus:outline-none focus:ring-1 focus:ring-[#FFC72C]/50 transition-colors"
                  value={form.preferred_contact}
                  onChange={(e) => update("preferred_contact", e.target.value)}
                >
                  <option value="discord">Discord</option>
                  <option value="email">Email</option>
                </select>
              </div>
            </div>
          </section>

          <section className="rounded-2xl border-2 border-[#FFC72C] bg-neutral-950 p-6 shadow-lg shadow-[#5C068C]/20">
            <h3 className="text-xl font-semibold text-[#FFC72C]">Availability</h3>

            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <Input
                label="Hours per Week"
                value={form.hours_per_week}
                onChange={(v) => update("hours_per_week", v)}
                required
                type="number"
                min={1}
                max={40}
              />

              <div className="flex flex-col gap-3 pt-6">
                <label className="flex items-center gap-2 text-sm text-[#FFC72C] hover:text-[#FFD947] transition-colors">
                  <input
                    type="checkbox"
                    checked={form.weeknights_available}
                    onChange={(e) =>
                      update("weeknights_available", e.target.checked)
                    }
                  />
                  Available on weeknights
                </label>

                <label className="flex items-center gap-2 text-sm text-[#FFC72C] hover:text-[#FFD947] transition-colors">
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

          <section className="rounded-2xl border-2 border-[#FFC72C] bg-neutral-950 p-6 shadow-lg shadow-[#5C068C]/20">
            <h3 className="text-xl font-semibold text-[#FFC72C]">Game Selection</h3>

            <div className="mt-4">
              <label className="text-sm font-medium text-[#FFC72C]">Game</label>
              <select
                className="mt-1 w-full rounded-lg border border-[#FFC72C]/30 bg-neutral-900/50 p-3 text-white focus:border-[#FFC72C]/80 focus:outline-none focus:ring-1 focus:ring-[#FFC72C]/50 transition-colors"
                value={form.game_slug}
                onChange={(e) =>
                  resetGameFields(e.target.value as GameSlug)
                }
              >
                <option value="valorant">Valorant</option>
                <option value="cs2">Counter-Strike 2</option>
                <option value="fortnite">Fortnite</option>
                <option value="r6">Rainbow Six Siege</option>
                <option value="rocket-league">Rocket League</option>
                <option value="overwatch">Overwatch</option>
                <option value="cod">Call of Duty</option>
                <option value="hearthstone">Hearthstone</option>
                <option value="smash">Super Smash Bros. Ultimate</option>
                <option value="mario-kart">Mario Kart</option>
              </select>
            </div>
            {form.game_slug === "hearthstone" && (
              <div className="mt-6 grid gap-4 md:grid-cols-2">
                <Input
                  label="Ranked Wins"
                  value={form.ranked_wins}
                  onChange={(v) => update("ranked_wins", v)}
                  type="number"
                  min={0}
                  max={50000}
                />

                <Input
                  label="Years Played"
                  value={form.years_played}
                  onChange={(v) => update("years_played", v)}
                  type="number"
                  min={0}
                  max={30}
                />

                <Input
                  label="Legend Peak Rank (if applicable)"
                  value={form.legend_peak_rank}
                  onChange={(v) => update("legend_peak_rank", v)}
                  type="number"
                  min={1}
                  max={50000}
                />

                <div>
                  <label className="text-sm font-medium text-[#FFC72C]">Preferred Format</label>
                  <input
                    className="mt-1 w-full rounded-lg border border-[#FFC72C]/30 bg-neutral-900/50 p-3 text-white focus:border-[#FFC72C]/80 focus:outline-none focus:ring-1 focus:ring-[#FFC72C]/50 transition-colors"
                    value="Standard"
                    disabled
                  />
                </div>

                <Input
                  label="Favorite Meta Deck"
                  value={form.secondary_role}
                  onChange={(v) => update("secondary_role", v)}
                />

                <Input
                  label="Other Card Games Played"
                  value={form.other_card_games}
                  onChange={(v) => update("other_card_games", v)}
                />
              </div>
            )}
            {form.game_slug === "mario-kart" && (
              <div className="mt-6 grid gap-4 md:grid-cols-2">
                <Input
                  label="Lounge Rating"
                  value={form.lounge_rating}
                  onChange={(v) => update("lounge_rating", v)}
                  type="number"
                  min={0}
                  max={10000}
                />

                <div>
                  <label className="text-sm font-medium text-[#FFC72C]">Preferred Title</label>
                  <select
                    className="mt-1 w-full rounded-lg border border-[#FFC72C]/30 bg-neutral-900/50 p-3 text-white focus:border-[#FFC72C]/80 focus:outline-none focus:ring-1 focus:ring-[#FFC72C]/50 transition-colors"
                    value={form.preferred_title}
                    onChange={(e) => update("preferred_title", e.target.value)}
                  >
                    <option value="">Select a title</option>
                    {marioKartTitles.map((title) => (
                      <option key={title} value={title}>
                        {title}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-sm font-medium text-[#FFC72C]">Controller Type</label>
                  <select
                    className="mt-1 w-full rounded-lg border border-[#FFC72C]/30 bg-neutral-900/50 p-3 text-white focus:border-[#FFC72C]/80 focus:outline-none focus:ring-1 focus:ring-[#FFC72C]/50 transition-colors"
                    value={form.controller_type}
                    onChange={(e) => update("controller_type", e.target.value)}
                  >
                    <option value="">Select a controller</option>
                    {marioKartControllers.map((controller) => (
                      <option key={controller} value={controller}>
                        {controller}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-sm font-medium text-[#FFC72C]">Playstyle</label>
                  <select
                    className="mt-1 w-full rounded-lg border border-[#FFC72C]/30 bg-neutral-900/50 p-3 text-white focus:border-[#FFC72C]/80 focus:outline-none focus:ring-1 focus:ring-[#FFC72C]/50 transition-colors"
                    value={form.playstyle}
                    onChange={(e) => {
                      update("playstyle", e.target.value);
                      update("primary_role", e.target.value);
                    }}
                  >
                    <option value="">Select a playstyle</option>
                    {marioKartPlaystyles.map((style) => (
                      <option key={style} value={style}>
                        {style}
                      </option>
                    ))}
                  </select>
                </div>

                <Input
                  label="Preferred Tracks / Notes"
                  value={form.preferred_tracks}
                  onChange={(v) => update("preferred_tracks", v)}
                />
              </div>
            )}
            {form.game_slug === "smash" && (
              <div className="mt-6">
                <label className="text-sm font-medium text-[#FFC72C]">Characters Played</label>
                <div className="mt-2 grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                  {smashCharacters.map((char) => (
                    <label key={char} className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={form.characters?.includes(char)}
                        onChange={(e) => {
                          const current = form.characters ? form.characters.split(",") : [];
                          if (e.target.checked) {
                            update("characters", [...current, char].join(","));
                          } else {
                            update(
                              "characters",
                              current.filter((c) => c !== char).join(",")
                            );
                          }
                        }}
                      />
                      {char}
                    </label>
                  ))}
                </div>
              </div>
            )}
            {form.game_slug === "smash" && (
              <div className="grid gap-4 md:grid-cols-2">
                <Input
                  label="GSP"
                  value={form.gsp}
                  onChange={(v) => update("gsp", v)}
                  type="number"
                />

                <Input
                  label="Regional Ranking"
                  value={form.regional_rank}
                  onChange={(v) => update("regional_rank", v)}
                />

                <Input
                  label="Best Wins (comma separated)"
                  value={form.best_wins}
                  onChange={(v) => update("best_wins", v)}
                />

                <Input
                  label="SmashersApp / Tracker Link"
                  value={form.tracker_url}
                  onChange={(v) => update("tracker_url", v)}
                />
              </div>
            )}

            {(form.game_slug === "mario-kart" || form.game_slug === "smash") && (
              <div className="mt-6 grid gap-4 md:grid-cols-2">
                <div>
                  <label className="text-sm font-medium text-[#FFC72C]">
                    Tournament Experience
                  </label>
                  <select
                    className="mt-1 w-full rounded-lg border border-[#FFC72C]/30 bg-neutral-900/50 p-3 text-white focus:border-[#FFC72C]/80 focus:outline-none focus:ring-1 focus:ring-[#FFC72C]/50 transition-colors"
                    value={form.tournament_experience}
                    onChange={(e) => updateTournamentExperience(e.target.value)}
                  >
                    <option value="none">None</option>
                    <option value="local">Local</option>
                    <option value="regional">Regional</option>
                    <option value="national">National</option>
                  </select>
                </div>

                {form.game_slug === "mario-kart" &&
                  marioKartTournamentDetailLevels.has(form.tournament_experience) && (
                    <div className="md:col-span-2">
                      <label className="text-sm font-medium text-[#FFC72C]">
                        Explain your tournament experience
                      </label>
                      <textarea
                        className="mt-1 min-h-[120px] w-full rounded-lg border border-[#FFC72C]/30 bg-neutral-900/50 p-3 text-white placeholder-neutral-500 focus:border-[#FFC72C]/80 focus:outline-none focus:ring-1 focus:ring-[#FFC72C]/50 transition-colors"
                        value={form.tournament_experience_details}
                        onChange={(e) =>
                          update("tournament_experience_details", e.target.value)
                        }
                        placeholder="Examples: events attended, placements, regions competed in, notable experience."
                      />
                      <p className="mt-1 text-xs text-neutral-500">
                        Share events attended, placements, regions competed in, and notable experience.
                      </p>
                    </div>
                  )}

                <div className="flex flex-col gap-3 pt-6">
                  <label className="flex items-center gap-2 text-sm text-[#FFC72C] hover:text-[#FFD947] transition-colors">
                    <input
                      type="checkbox"
                      checked={form.team_experience}
                      onChange={(e) =>
                        update("team_experience", e.target.checked)
                      }
                    />
                    Team experience
                  </label>

                  <label className="flex items-center gap-2 text-sm text-[#FFC72C] hover:text-[#FFD947] transition-colors">
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
            )}

            {form.game_slug !== "mario-kart" && form.game_slug !== "smash" && (
              <div className="mt-6 grid gap-4 md:grid-cols-2">
                {form.game_slug === "fortnite" && (
                  <div>
                    <label className="text-sm font-medium text-[#FFC72C]">Fortnite Mode</label>
                    <select
                      className="mt-1 w-full rounded-lg border border-[#FFC72C]/30 bg-neutral-900/50 p-3 text-white focus:border-[#FFC72C]/80 focus:outline-none focus:ring-1 focus:ring-[#FFC72C]/50 transition-colors"
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
                {form.game_slug === "fortnite" && (
                  <>
                    <Input
                      label="Epic Games Name"
                      value={form.epic_games_name}
                      onChange={(v) => update("epic_games_name", v)}
                    />
                    <Input
                      label="Fortnite PR (Tracker)"
                      value={form.fortnite_pr}
                      onChange={(v) => update("fortnite_pr", v)}
                      type="number"
                      min={0}
                    />
                    <Input
                      label="Fortnite K/D"
                      value={form.fortnite_kd}
                      onChange={(v) => update("fortnite_kd", v)}
                      type="number"
                      min={0}
                    />
                    <Input
                      label="Total Kills"
                      value={form.fortnite_total_kills}
                      onChange={(v) => update("fortnite_total_kills", v)}
                      type="number"
                      min={0}
                    />
                    <Input
                      label="Playtime (Hours)"
                      value={form.fortnite_playtime_hours}
                      onChange={(v) => update("fortnite_playtime_hours", v)}
                      type="number"
                      min={0}
                    />
                    <Input
                      label="Wins"
                      value={form.fortnite_wins}
                      onChange={(v) => update("fortnite_wins", v)}
                      type="number"
                      min={0}
                    />
                  </>
                )}
                <Input
                  label="In-Game Name"
                  value={form.ign}
                  onChange={(v) => update("ign", v)}
                  required
                />

                <div>
                  <label className="text-sm font-medium text-[#FFC72C]">Current Rank</label>

                  {form.game_slug === "valorant" ? (
                    <select
                      className="mt-1 w-full rounded-lg border border-[#FFC72C]/30 bg-neutral-900/50 p-3 text-white focus:border-[#FFC72C]/80 focus:outline-none focus:ring-1 focus:ring-[#FFC72C]/50 transition-colors"
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
                      className="mt-1 w-full rounded-lg border border-[#FFC72C]/30 bg-neutral-900/50 p-3 text-white focus:border-[#FFC72C]/80 focus:outline-none focus:ring-1 focus:ring-[#FFC72C]/50 transition-colors"
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
                    className="mt-1 w-full rounded-lg border border-[#FFC72C]/30 bg-neutral-900/50 p-3 text-white focus:border-[#FFC72C]/80 focus:outline-none focus:ring-1 focus:ring-[#FFC72C]/50 transition-colors"
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

                  ) : form.game_slug === "rocket-league" ? (
                    <select
                    className="mt-1 w-full rounded-lg border border-[#FFC72C]/30 bg-neutral-900/50 p-3 text-white focus:border-[#FFC72C]/80 focus:outline-none focus:ring-1 focus:ring-[#FFC72C]/50 transition-colors"
                    value={form.current_rank_label}
                    onChange={(e) => update("current_rank_label", e.target.value)}
                    required
                    >
                      <option value="">Select a rank</option>
                      {rocketLeagueRanks.map((rank) => (
                        <option key={rank} value={rank}>
                          {rank}
                        </option>
                      ))}
                    </select>

                  ) : form.game_slug === "overwatch" ? (
                    <select
                      className="mt-1 w-full rounded-lg border border-[#FFC72C]/30 bg-neutral-900/50 p-3 text-white focus:border-[#FFC72C]/80 focus:outline-none focus:ring-1 focus:ring-[#FFC72C]/50 transition-colors"
                      value={form.current_rank_label}
                      onChange={(e) => update("current_rank_label", e.target.value)}
                      required
                    >
                      <option value="">Select a rank</option>
                        {overwatchRanks.map((rank) => (
                          <option key={rank} value={rank}>
                            {rank}
                          </option>
                        ))}
                      </select>

                  ) : form.game_slug === "cod" ? (
                    <select
                      className="mt-1 w-full rounded-lg border border-[#FFC72C]/30 bg-neutral-900/50 p-3 text-white focus:border-[#FFC72C]/80 focus:outline-none focus:ring-1 focus:ring-[#FFC72C]/50 transition-colors"
                      value={form.current_rank_label}
                      onChange={(e) => update("current_rank_label", e.target.value)}
                      required
                    >
                      <option value="">Select a rank</option>
                      {codRanks.map((rank) => (
                        <option key={rank} value={rank}>
                          {rank}
                        </option>
                      ))}
                    </select>

                  ) : form.game_slug === "hearthstone" ? (
                    <select
                      className="mt-1 w-full rounded-lg border border-[#FFC72C]/30 bg-neutral-900/50 p-3 text-white focus:border-[#FFC72C]/80 focus:outline-none focus:ring-1 focus:ring-[#FFC72C]/50 transition-colors"
                      value={form.current_rank_label}
                      onChange={(e) => update("current_rank_label", e.target.value)}
                      required
                    >
                      <option value="">Select a rank</option>
                      {hearthstoneRanks.map((rank) => (
                        <option key={rank} value={rank}>
                          {rank}
                        </option>
                      ))}
                    </select>
                    
                  ) : (
                    <>
                    <input
                      className="mt-1 w-full rounded-lg border border-[#FFC72C]/30 bg-neutral-900/50 p-3 text-white placeholder-neutral-500 focus:border-[#FFC72C]/80 focus:outline-none focus:ring-1 focus:ring-[#FFC72C]/50 transition-colors"
                      value={form.current_rank_label}
                        onChange={(e) =>
                          update("current_rank_label", e.target.value)
                        }
                        placeholder="Example: Global Elite or Premier 18500"
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
                {form.game_slug === "cs2" && (
                  <>
                    <Input
                      label="Faceit Level (1-10)"
                      value={form.faceit_level}
                      onChange={(v) => update("faceit_level", v)}
                      type="number"
                      min={1}
                      max={10}
                    />
                    <Input
                      label="Faceit ELO"
                      value={form.faceit_elo}
                      onChange={(v) => update("faceit_elo", v)}
                      type="number"
                      min={0}
                    />
                    <Input
                      label="CS2 Roles (Additional)"
                      value={form.cs2_roles}
                      onChange={(v) => update("cs2_roles", v)}
                    />
                    <Input
                      label="Prior Team History"
                      value={form.prior_team_history}
                      onChange={(v) => update("prior_team_history", v)}
                    />
                  </>
                )}

                  <>
                    <div>
                      <label className="text-sm font-medium text-[#FFC72C]">Primary Role</label>
                      <select
                        className="mt-1 w-full rounded-lg border border-[#FFC72C]/30 bg-neutral-900/50 p-3 text-white focus:border-[#FFC72C]/80 focus:outline-none focus:ring-1 focus:ring-[#FFC72C]/50 transition-colors"
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
                      <label className="text-sm font-medium text-[#FFC72C]">
                        Secondary Role
                      </label>
                      <select
                        className="mt-1 w-full rounded-lg border border-[#FFC72C]/30 bg-neutral-900/50 p-3 text-white focus:border-[#FFC72C]/80 focus:outline-none focus:ring-1 focus:ring-[#FFC72C]/50 transition-colors"
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
                  </>
                

                <Input
                  label="Tracker / Profile URL"
                  value={form.tracker_url}
                  onChange={(v) => update("tracker_url", v)}
                />

                <div>
                  <label className="text-sm font-medium text-[#FFC72C]">
                    Tournament Experience
                  </label>
                  <select
                    className="mt-1 w-full rounded-lg border border-[#FFC72C]/30 bg-neutral-900/50 p-3 text-white focus:border-[#FFC72C]/80 focus:outline-none focus:ring-1 focus:ring-[#FFC72C]/50 transition-colors"
                    value={form.tournament_experience}
                    onChange={(e) => updateTournamentExperience(e.target.value)}
                  >
                    <option value="none">None</option>
                    <option value="local">Local</option>
                    <option value="regional">Regional</option>
                    <option value="national">National</option>
                  </select>
                </div>

                <div className="flex flex-col gap-3 pt-6">
                  <label className="flex items-center gap-2 text-sm text-[#FFC72C] hover:text-[#FFD947] transition-colors">
                    <input
                      type="checkbox"
                      checked={form.team_experience}
                      onChange={(e) =>
                        update("team_experience", e.target.checked)
                      }
                    />
                    Team experience
                  </label>

                  <label className="flex items-center gap-2 text-sm text-[#FFC72C] hover:text-[#FFD947] transition-colors">
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
            )}
          </section>

          <div className="flex flex-col gap-3">
            <button
              type="submit"
              disabled={loading}
              className="rounded-xl bg-gradient-to-r from-[#FFC72C] to-[#FFD947] px-6 py-3 font-bold text-[#5C068C] hover:shadow-lg hover:shadow-[#FFC72C]/50 disabled:opacity-60 transition-all duration-200"
            >
              {loading ? "Submitting..." : "Submit Application"}
            </button>

            

            {err && (
              <div className="whitespace-pre-wrap rounded-lg border border-red-700 bg-red-950 p-3 text-sm text-red-300">
                {err}
              </div>
            )}
            {success && (
              <div className="whitespace-pre-wrap rounded-lg border border-[#FFC72C] bg-[#5C068C]/30 p-3 text-sm text-[#FFC72C]">
                {success}
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
  min,
  max,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  type?: string;
  min?: number;
  max?: number;
}) {
  return (
    <div>
      <label className="text-sm font-medium text-[#FFC72C]">{label}</label>
      <input
        className="mt-1 w-full rounded-lg border border-[#FFC72C]/30 bg-neutral-900/50 p-3 text-white placeholder-neutral-500 focus:border-[#FFC72C]/80 focus:outline-none focus:ring-1 focus:ring-[#FFC72C]/50 transition-colors"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required={required}
        type={type}
        min={min}
        max={max}
      />
    </div>
  );
}
