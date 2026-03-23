"use client";
import { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";

export default function Home() {
  const pages = ["Home", "Roster", "Schedule", "News", "Stream", "Recruitment", "Facility", "Support"];

  const pageMap: { [key: string]: string } = {
    Home: "/",
    Roster: "/roster",
    Schedule: "/schedule",
    News: "/news",
    Stream: "/stream",
    Recruitment: "/recruit",
    Facility: "/facility",
    Support: "/support",
  };

  const [matches, setMatches] = useState<any[]>([]);
  const [matchStart, setMatchStart] = useState(0);
  const [channel, setChannel] = useState("ashlandesports");
  const [isLive, setIsLive] = useState(false);

  const toggleStream = () => {
    setChannel((prev) =>
      prev === "ashlandesports" ? "ashlandesports2" : "ashlandesports"
    );
  };

  const parent =
    typeof window !== "undefined" ? window.location.hostname : "localhost";

  useEffect(() => {
    const checkLiveStatus = async () => {
      try {
        const res = await fetch(`https://decapi.me/twitch/uptime/${channel}`);
        const text = await res.text();
        setIsLive(!text.includes("offline"));
      } catch {
        setIsLive(false);
      }
    };

    checkLiveStatus();
    const interval = setInterval(checkLiveStatus, 60000);
    return () => clearInterval(interval);
  }, [channel]);

  const matchesToShow = 5;

  useEffect(() => {
    const tryLoad = async () => {
      try {
        const res = await fetch("/data/matches.json");
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data)) setMatches(data);
        }
      } catch {}
    };

    tryLoad();
  }, []);

  const prevMatches = () => setMatchStart((s) => Math.max(0, s - 1));
  const nextMatches = () =>
    setMatchStart((s) => Math.min(Math.max(0, matches.length - matchesToShow), s + 1));

  useEffect(() => {
  const checkLiveStatus = async () => {
  try { const res = await fetch( "https://decapi.me/twitch/uptime/ashlandesports" ); 
    const text = await res.text(); 
    if (text.includes("offline")) { 
      setIsLive(false); } 
      else { setIsLive(true); } 
    } catch (error) { setIsLive(false); } }
    ; checkLiveStatus(); 
    const interval = setInterval(checkLiveStatus, 60000); 
    return () => clearInterval(interval); }, []);
  return (
    <div className="min-h-screen bg-black text-white">

      <div className="match-bar flex items-center justify-center gap-2 overflow-x-auto px-2">
        <button className="match-arrow" onClick={prevMatches} disabled={matchStart === 0}>
          &larr;
        </button>

        <div className="match-list flex gap-3 overflow-x-auto">
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

            <h1 className="title title-3d text-lg md:text-2xl font-bold tracking-wide"
  style={{ textShadow: "1px 1px #333"}}>
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

      <div className="w-full flex flex-col items-center gap-4 md:gap-6 px-4 py-6">

        <div className="w-full max-w-5xl aspect-video">

          <iframe
            src={`https://player.twitch.tv/?channel=${channel}&parent=${parent}`}
            allow="autoplay; fullscreen"
            allowFullScreen
            className="w-full h-full rounded-lg"
          />

        </div>

        <button
          onClick={toggleStream}
          className="px-4 py-2 md:px-6 md:py-3 bg-purple-600 hover:bg-purple-700 rounded-lg font-semibold text-sm md:text-base"
        >
          {channel === "ashlandesports"
            ? "Switch to ashlandesports2"
            : "Switch to ashlandesports"}
        </button>

      </div>

    </div>
  );
}