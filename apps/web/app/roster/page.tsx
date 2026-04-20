"use client";
import { useState, useEffect, useMemo } from "react";
import Image from 'next/image'
import Link from 'next/link'
import { Player } from "@/types/Player";
import { GameOption } from "@/types/GameOption";
import RosterGrid from "@/components/RosterGrid";
import TopActivityFeedBar from "../components/TopActivityFeedBar";

export default function Home() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const pages = ["Home", "Roster", "Schedule", "News", "Stream", "Recruitment", "Facility", "Support", "Hall of Fame"];

  const pageMap: { [key: string]: string } = {
    "Home": "/",
    "Roster": "/roster",
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
  const [selectedGameSlug, setSelectedGameSlug] = useState<string>("all");

useEffect(() => {
  Promise.all([
    fetch(`${apiUrl}/api/v1/roster`),
    fetch(`${apiUrl}/api/v1/games`),
  ])
    .then(async ([rosterRes, gamesRes]) => {
      if (!rosterRes.ok) throw new Error("Failed to load roster");
      const rosterData = await rosterRes.json();
      setPlayers(Array.isArray(rosterData) ? rosterData : []);

      if (gamesRes.ok) {
        const gamesData = await gamesRes.json();
        setGames(Array.isArray(gamesData) ? gamesData : []);
      } else {
        setGames([]);
      }
    })
    .catch(() => console.error("Failed to load roster data"));
}, [apiUrl]);

  const gameOptions = useMemo(() => {
    if (games.length > 0) return games;

    const bySlug = new Map<string, GameOption>();
    for (const player of players) {
      const slug = player.primary_game_slug;
      const name = player.primary_game_name || player.game;
      if (!slug || !name || bySlug.has(slug)) continue;
      bySlug.set(slug, { id: -1, slug, name });
    }
    return Array.from(bySlug.values()).sort((a, b) => a.name.localeCompare(b.name));
  }, [games, players]);

  const filteredPlayers = useMemo(() => {
    if (selectedGameSlug === "all") return players;
    return players.filter((player) => {
      if (player.primary_game_slug === selectedGameSlug) return true;
      return Array.isArray(player.secondary_game_slugs) && player.secondary_game_slugs.includes(selectedGameSlug);
    });
  }, [players, selectedGameSlug]);

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
            src="/Eagles (2).png"
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

      <div className="mx-auto mb-6 w-full max-w-sm px-6">
        <label htmlFor="roster-game-filter" className="mb-2 block text-sm font-medium text-gray-200">
          Filter by game
        </label>
        <select
          id="roster-game-filter"
          className="w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
          value={selectedGameSlug}
          onChange={(event) => setSelectedGameSlug(event.target.value)}
        >
          <option value="all">All Games</option>
          {gameOptions.map((game) => (
            <option key={game.slug} value={game.slug}>
              {game.name}
            </option>
          ))}
        </select>
      </div>

      {filteredPlayers.length > 0 ? (
        <RosterGrid players={filteredPlayers} />
      ) : (
        <div className="mx-6 mb-16 rounded-xl border border-gray-700 bg-gray-900/60 px-6 py-10 text-center text-sm text-gray-300">
          No roster members for this game yet.
        </div>
      )}
    </div>
  );
}
