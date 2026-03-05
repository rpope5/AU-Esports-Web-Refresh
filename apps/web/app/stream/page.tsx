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

  const conferences = ["ECAC", "GLEC", "NECC", "CKL", "PlayVS", "CCL"];

  const [currentConfIndex, setCurrentConfIndex] = useState(0);
  const [matches, setMatches] = useState<any[]>([]);
  const [matchStart, setMatchStart] = useState(0);

  const [channel, setChannel] = useState("ashlandesports");
  const [isLive, setIsLive] = useState(false);

  const toggleStream = () => {
    setChannel((prev) =>
      prev === "ashlandesports" ? "ashlandesports2" : "ashlandesports"
    );
  };

  useEffect(() => {
    const checkLiveStatus = async () => {
      try {
        const res = await fetch(
          "https://decapi.me/twitch/uptime/ashlandesports"
        );
        const text = await res.text();

        if (text.includes("offline")) {
          setIsLive(false);
        } else {
          setIsLive(true);
        }
      } catch (error) {
        setIsLive(false);
      }
    };

    checkLiveStatus();
    const interval = setInterval(checkLiveStatus, 60000);
    return () => clearInterval(interval);
  }, []);

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
    setMatchStart((s) =>
      Math.min(Math.max(0, matches.length - matchesToShow), s + 1)
    );

  useEffect(() => {
    const id = setInterval(() => {
      setCurrentConfIndex((i) => i + 1);
    }, 3000);

    return () => clearInterval(id);
  }, []);

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="match-bar">
        <button className="match-arrow" onClick={prevMatches} disabled={matchStart === 0}>
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
            className="w-20 h-20 object-contain"
          />

          <div className="flex items-center gap-3">
            <h1 className="title">Ashland University Esports</h1>

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

      <div className="w-full min-h-screen flex flex-col items-center justify-center gap-6">
        <div className="w-3/4 max-w-5xl aspect-video">
          <iframe
            src={`https://player.twitch.tv/?channel=${channel}&parent=localhost`}
            allowFullScreen
            className="w-full h-full rounded-lg"
          />
        </div>

        <button
  onClick={toggleStream}
  className="px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg font-semibold"
>
  {channel === "ashlandesports"
    ? "Switch to ashlandesports2"
    : "Switch to ashlandesports"}
</button>
      </div>
    </div>
  );
}