"use client";
import { useState, useEffect } from "react";
import Image from 'next/image'
import Link from 'next/link'
import { link } from "fs";

export default function Home() {
  const pages = ["Home", "Roster", "Schedule", "News", "Stream", "Recruitment", "Facility", "Support"];

  const pageMap: { [key: string]: string } = {
    "Home": "/",
    "Roster": "/roster",
    "Schedule": "/schedule",
    "News": "/news",
    "Stream": "/stream",
    "Recruitment": "/recruit",
    "Facility": "/facility",
    "Support": "/support"
  };

  const conferences = [
    "ECAC",
    "GLEC",
    "NECC",
    "CKL",
    "PlayVS",
    "CCL"
  ];
  const conferenceImages = [
    '/ECAC.jpg',
    '/GLEC.jpg',
    '/NECC.jpg',
    '/CKL.png',
    '/PlayVS.jpg',
    '/CCL.jpg',
  ];
  
  const displayConferences = [...conferences, ...conferences, ...conferences, ...conferences,...conferences, ...conferences, ...conferences, ...conferences,...conferences, ...conferences, ...conferences];
  const displayImages = [...conferenceImages, ...conferenceImages, ...conferenceImages, ...conferenceImages,...conferenceImages, ...conferenceImages, ...conferenceImages, ...conferenceImages,...conferenceImages, ...conferenceImages, ...conferenceImages];
  
  const [currentConfIndex, setCurrentConfIndex] = useState(0);
  const [selectedConf, setSelectedConf] = useState<string | null>(null);

  const [matches, setMatches] = useState<any[]>([]);
  useEffect(() => {

    const tryLoad = async () => {
      try {
        const resX = await fetch('/data/matches.xlsx');
        if (resX.ok) {
          const buffer = await resX.arrayBuffer();
          const XLSX = await import('xlsx' as any).catch(() => null);
          if (!XLSX) throw new Error('xlsx not available');
          const wb = XLSX.read(buffer, { type: 'array' });
          const sheetName = wb.SheetNames[0];
          const ws = wb.Sheets[sheetName];
          const raw = XLSX.utils.sheet_to_json(ws, { defval: '' });
          if (Array.isArray(raw) && raw.length) {
            const parsed = raw.map((r: any, i: number) => ({
              id: r.id ?? i + 1,
              ourTeam: r.ourTeam ?? r.OurTeam ?? r.Team ?? 'Ashland',
              opponent: r.opponent ?? r.Opponent ?? r.Opp ?? '',
              game: r.game ?? r.Game ?? r.Platform ?? '',
              time: r.time ?? r.Time ?? r.datetime ?? ''
            }));
            setMatches(parsed);
            return;
          }
        }
      } catch (e) {}

      try {
        const resC = await fetch('/data/matches.csv');
        if (resC.ok) {
          const txt = await resC.text();
          const rows = txt.trim().split('\n').map((r) => r.split(','));
          const headers = rows.shift() || [];
          const parsed = rows.map((cols, i) => {
            const obj: any = {};
            headers.forEach((h, idx) => { obj[h.trim()] = cols[idx] ? cols[idx].trim() : ''; });
            return {
              id: Number(obj.id) || i + 1,
              ourTeam: obj.ourTeam || obj.OurTeam || 'Ashland',
              opponent: obj.opponent || obj.Opponent || '',
              game: obj.game || obj.Game || '',
              time: obj.time || obj.Time || ''
            };
          });
          if (parsed.length) { setMatches(parsed); return; }
        }
      } catch (e) {}

      try {
        const r = await fetch('/data/matches.json');
        if (!r.ok) throw new Error('failed');
        const data = await r.json();
        if (Array.isArray(data) && data.length) setMatches(data);
      } catch (e) {}
    };
    tryLoad();
  }, []);

  const [matchStart, setMatchStart] = useState(0);
  const matchesToShow = 5;
  const prevMatches = () => setMatchStart((s) => Math.max(0, s - 1));
  const nextMatches = () => setMatchStart((s) => Math.min(Math.max(0, matches.length - matchesToShow), s + 1));

  const prev = () => {
    setCurrentConfIndex((prevIndex) => (prevIndex === 0 ? displayConferences.length - 1 : prevIndex - 1));
  };

  const next = () => {
    setCurrentConfIndex((prevIndex) => prevIndex + 1);
  };

  useEffect(() => {
    if (currentConfIndex >= conferences.length * 10) {
      setCurrentConfIndex(0);
    }
  }, [currentConfIndex]);

  useEffect(() => {
    const id = setInterval(() => {
      setCurrentConfIndex((i) => i + 1);
    }, 3000);
    return () => clearInterval(id);
  }, []);

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

  
  const [showSupportModal, setShowSupportModal] = useState(false);

  return (
    <div className="min-hscreen bg-black text-white">
      <div className="match-bar">
        <button className="match-arrow" onClick={prevMatches} aria-label="Previous matches" disabled={matchStart === 0}>&larr;</button>
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
        <button className="match-arrow" onClick={nextMatches} aria-label="Next matches" disabled={matchStart >= matches.length - matchesToShow}>&rarr;</button>
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
              style={{ textShadow: "1px 1px #333" }}>
              Ashland University Esports
            </h1>

            {isLive && (
              <div className="flex items-center gap-2">
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#FFC72C] opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-[#FFC72C]"></span>
                </span>
                <span className="text-[#FFC72C] text-sm font-semibold">LIVE</span>
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
      </div>
      );
}