"use client";
import { useState, useEffect, useMemo } from "react";
import Image from 'next/image'
import Link from 'next/link'
import { Player } from "@/types/Player";
import { GameOption } from "@/types/GameOption";
import { LegacyRosterDetail, LegacyRosterListItem } from "@/types/LegacyRoster";
import { ALL_GAMES_FILTER_VALUE, deriveGameOptions, filterPlayerByGame } from "@/lib/rosterFilters";
import RosterGrid from "@/components/RosterGrid";
import TopActivityFeedBar from "../components/TopActivityFeedBar";

export default function Home() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const pages = ["Home", "Roster", "Staff", "Schedule", "News", "Stream", "Recruitment", "Facility", "Support", "Hall of Fame"];

  const pageMap: { [key: string]: string } = {
    "Home": "/",
    "Roster": "/roster",
    "Staff": "/staff",
    "Schedule": "/schedule",
    "News": "/news",
    "Stream": "/stream",
    "Recruitment": "/recruit",
    "Facility": "/facility",
    "Support": "/support",
    "Hall of Fame": "/hof"
  };

  const [players, setPlayers] = useState<Player[]>([]);
  const [games, setGames] = useState<GameOption[]>([]);
  const [selectedGameSlug, setSelectedGameSlug] = useState<string>(ALL_GAMES_FILTER_VALUE);
  const [legacyRosters, setLegacyRosters] = useState<LegacyRosterListItem[]>([]);
  const [legacyDetailsBySlug, setLegacyDetailsBySlug] = useState<Record<string, LegacyRosterDetail>>({});
  const [selectedRoster, setSelectedRoster] = useState<string>("current");
  const [loadingCurrentRoster, setLoadingCurrentRoster] = useState<boolean>(true);
  const [loadingSelectedLegacy, setLoadingSelectedLegacy] = useState<boolean>(false);
  const [currentRosterError, setCurrentRosterError] = useState<string | null>(null);
  const [legacyRosterError, setLegacyRosterError] = useState<string | null>(null);

useEffect(() => {
  let cancelled = false;
  setLoadingCurrentRoster(true);
  setCurrentRosterError(null);

  const load = async () => {
    try {
      const [rosterRes, gamesRes] = await Promise.all([
        fetch(`${apiUrl}/api/v1/roster`),
        fetch(`${apiUrl}/api/v1/games`),
      ]);

      if (!rosterRes.ok) throw new Error("Failed to load current roster.");
      const rosterData = await rosterRes.json();
      if (!cancelled) {
        setPlayers(Array.isArray(rosterData) ? rosterData : []);
      }

      if (gamesRes.ok) {
        const gamesData = await gamesRes.json();
        if (!cancelled) {
          setGames(Array.isArray(gamesData) ? gamesData : []);
        }
      } else if (!cancelled) {
        setGames([]);
      }
    } catch {
      if (!cancelled) {
        setCurrentRosterError("Failed to load current roster.");
      }
    } finally {
      if (!cancelled) {
        setLoadingCurrentRoster(false);
      }
    }
  };

  void load();
  return () => {
    cancelled = true;
  };
}, [apiUrl]);

  useEffect(() => {
    let cancelled = false;
    setLegacyRosterError(null);

    const loadLegacyRosters = async () => {
      try {
        const response = await fetch(`${apiUrl}/api/v1/legacy-rosters`);
        if (!response.ok) {
          throw new Error("Failed to load legacy rosters.");
        }
        const payload = await response.json();
        if (!cancelled) {
          setLegacyRosters(Array.isArray(payload) ? payload : []);
        }
      } catch {
        if (!cancelled) {
          setLegacyRosters([]);
          setLegacyRosterError("Legacy rosters are currently unavailable.");
        }
      }
    };

    void loadLegacyRosters();
    return () => {
      cancelled = true;
    };
  }, [apiUrl]);

  useEffect(() => {
    if (selectedRoster === "current") {
      setLegacyRosterError(null);
      return;
    }
    if (legacyDetailsBySlug[selectedRoster]) return;

    let cancelled = false;
    setLoadingSelectedLegacy(true);
    setLegacyRosterError(null);

    const loadSelectedLegacyRoster = async () => {
      try {
        const response = await fetch(`${apiUrl}/api/v1/legacy-rosters/${selectedRoster}`);
        if (!response.ok) {
          throw new Error("Failed to load selected legacy roster.");
        }
        const payload = (await response.json()) as LegacyRosterDetail;
        if (!cancelled) {
          setLegacyDetailsBySlug((prev) => ({ ...prev, [selectedRoster]: payload }));
        }
      } catch {
        if (!cancelled) {
          setLegacyRosterError("Failed to load selected legacy roster.");
        }
      } finally {
        if (!cancelled) {
          setLoadingSelectedLegacy(false);
        }
      }
    };

    void loadSelectedLegacyRoster();
    return () => {
      cancelled = true;
    };
  }, [apiUrl, legacyDetailsBySlug, selectedRoster]);

  const activePlayers = useMemo(() => {
    if (selectedRoster === "current") return players;
    const detail = legacyDetailsBySlug[selectedRoster];
    if (!detail || !Array.isArray(detail.players)) return [];
    return detail.players;
  }, [legacyDetailsBySlug, players, selectedRoster]);

  const gameOptions = useMemo(() => {
    return deriveGameOptions(games, activePlayers);
  }, [activePlayers, games]);

  const filteredPlayers = useMemo(() => {
    return activePlayers.filter((player) => filterPlayerByGame(player, selectedGameSlug));
  }, [activePlayers, selectedGameSlug]);

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
   <div className="min-h-screen bg-black text-white">
      <TopActivityFeedBar />

      <header className="site-header flex flex-col md:flex-row items-center justify-between p-4 gap-4">
        <div className="flex items-center gap-2">
          <Image
            src="/Eagle.png"
            alt="Ashland Eagle Logo"
            width={90}
            height={90}
            className="w-14 h-14 md:w-20 md:h-20 object-contain"
          />

          <div className="flex items-center gap-3">
            <h1 className="title title-3d text-lg md:text-2xl font-bold tracking-wide" style={{ textShadow: "1px 1px #333"}}>
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

      <div className="text-4xl py-8 text-center font-Gotham-Bold">Team Roster</div>

      <div className="mx-auto mb-6 grid w-full max-w-3xl gap-4 px-6 md:grid-cols-2">
        <div>
          <label htmlFor="roster-selector" className="mb-2 block text-sm font-medium text-gray-200">
            Roster
          </label>
          <select
            id="roster-selector"
            className="w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
            value={selectedRoster}
            onChange={(event) => setSelectedRoster(event.target.value)}
          >
            <option value="current">Current Roster</option>
            {legacyRosters.map((roster) => (
              <option key={roster.slug} value={roster.slug}>
                {roster.name}
              </option>
            ))}
          </select>
        </div>

        <div>
        <label htmlFor="roster-game-filter" className="mb-2 block text-sm font-medium text-gray-200">
          Filter by game
        </label>
        <select
          id="roster-game-filter"
          className="w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
          value={selectedGameSlug}
          onChange={(event) => setSelectedGameSlug(event.target.value)}
        >
          <option value={ALL_GAMES_FILTER_VALUE}>All Games</option>
          {gameOptions.map((game) => (
            <option key={game.slug} value={game.slug}>
              {game.name}
            </option>
          ))}
        </select>
      </div>
      </div>

      {currentRosterError && (
        <div className="mx-6 mb-6 rounded-xl border border-red-700 bg-red-900/20 px-6 py-4 text-sm text-red-200">
          {currentRosterError}
        </div>
      )}
      {legacyRosterError && (
        <div className="mx-6 mb-6 rounded-xl border border-amber-700 bg-amber-900/20 px-6 py-4 text-sm text-amber-200">
          {legacyRosterError}
        </div>
      )}

      {loadingCurrentRoster || loadingSelectedLegacy ? (
        <div className="mx-6 mb-16 rounded-xl border border-gray-700 bg-gray-900/60 px-6 py-10 text-center text-sm text-gray-300">
          Loading roster...
        </div>
      ) : filteredPlayers.length > 0 ? (
        <RosterGrid players={filteredPlayers} />
      ) : (
        <div className="mx-6 mb-16 rounded-xl border border-gray-700 bg-gray-900/60 px-6 py-10 text-center text-sm text-gray-300">
          No roster members for this game yet.
        </div>
      )}
    </div>
  );
}
