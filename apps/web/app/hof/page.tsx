"use client";
import { useState, useEffect } from "react";
import Image from 'next/image'
import Link from 'next/link'
import TopActivityFeedBar from "../components/TopActivityFeedBar";

export default function Home() {
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

      <main className="px-10 py-10">
        <h2 className="text-4xl text-center font-bold mb-8">Hall of Fame</h2>
        <p className="text-center text-lg mb-8">Celebrating our National Championship Teams</p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

          <div className="bg-[#FFC72C] p-6 rounded-lg text-center text-black">
            <h3 className="text-2xl font-bold mb-4">2025 National Champions- PlayVS - Hearthstone</h3>
            <div className="mb-4">
              <Image src="/Hearthstone1.jpg" alt="2025 Hearthstone Championship Team" width={300} height={200} className="rounded-lg mb-2 mx-auto" />
              <p className="text-sm text-gray-700">Championship Team</p>
            </div>
            <div className="mb-4">
              <Image src="/images/valorant-logo.png" alt="Trophy" width={150} height={150} className="rounded-lg mx-auto" />
            </div>
            <p className="text-black text-lg font-semibold">Championship Year: 2025</p>
          </div>
          
          <div className="bg-[#5C068C] p-6 rounded-lg text-center text-white">
            <h3 className="text-2xl font-bold mb-4">2025 National Champions - NECC - Counter Strike 2</h3>
            <div className="mb-4">
              <Image src="/CS2.jpg" alt="2025 CS2 Championship Team" width={300} height={200} className="rounded-lg mb-2 mx-auto" />
              <p className="text-sm text-white-700">Championship Team</p>
            </div>
            <div className="mb-4">
              <Image src="/images/overwatch-logo.png" alt="Trophy" width={150} height={150} className="rounded-lg mx-auto" />
            </div>
            <p className="text-white text-lg font-semibold">Championship Year: 2025</p>
          </div>
          
          <div className="bg-[#FFC72C] p-6 rounded-lg text-center text-black">
            <h3 className="text-2xl font-bold mb-4">2025 National Champions - ECAC - Hearthstone</h3>
            <div className="mb-4">
              <Image src="/Hearthstone2.jpg" alt="2025 Hearthstone Championship Team" width={300} height={200} className="rounded-lg mb-2 mx-auto" />
              <p className="text-sm text-gray-700">Championship Team</p>
            </div>
            <div className="mb-4">
              <Image src="/images/rocket-league-logo.png" alt="Trophy" width={150} height={150} className="rounded-lg mx-auto" />
            </div>
            <p className="text-black text-lg font-semibold">Championship Year: 2025</p>
          </div>
        </div>
      </main>
    </div>
  );
}
