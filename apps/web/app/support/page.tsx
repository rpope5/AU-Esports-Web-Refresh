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

  <div className="flex justify-center mt-16 z-40 pointer-events-none">
  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-5xl auto-rows-fr">

    <div className="pointer-events-auto bg-[#5C068C] rounded-xl p-6 flex flex-col items-center justify-center text-center h-full">
      <p className="text-white text-lg md:text-xl font-semibold">
        Support Ashland Esports!<br />
        With the Ashland University Day of Giving<br />
        you can help us grow our program, support our players, and compete at the highest level.
      </p>
      <Link
  href="https://www.givecampus.com/campaigns/8374/donations/new?designation=esports&"
  target="_blank"
>
  <button className="mt-4 bg-[#FFC72C] text-black font-semibold px-6 py-3 rounded-full shadow-lg hover:bg-yellow-400 transition">
    Support
  </button>
</Link>
    </div>

    <div className="pointer-events-auto bg-[#FFC72C] rounded-xl p-6 flex items-center justify-center text-center text-black h-full">
      <p className="font-semibold">
        Donations will be used to fund travel for LANs, purchase new equipment, and support our players in their competitive journey.
      </p>
    </div>

    <div className="pointer-events-auto bg-[#FFC72C] rounded-xl p-6 flex items-center justify-center text-center text-black h-full">
      <p className="font-semibold">
        Developed by the AUEsportDevs<br />
        Built to support players, fans, and the future of collegiate esports.
      </p>
    </div>

    <div className="pointer-events-auto bg-[#5C068C] rounded-xl p-6 flex items-center justify-center text-center text-white h-full">
      <p className="font-semibold">
        Thank you for your support!<br />
        
      </p>
    </div>

  </div>
</div>

    </div>
  );
}
