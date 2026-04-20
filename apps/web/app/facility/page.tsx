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

  const facilityPhotos = [
    { src: '/fac5.png', alt: 'Main facility overview' },
    { src: '/fac1.png', alt: 'Training area with monitors' },
    { src: '/fac2.png', alt: 'Team practice session' },
    { src: '/fac3.png', alt: 'Event space with fans' },
    { src: '/fac4.png', alt: 'Community tournament setup' },
  ];

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

      <section className="facility-gallery-container px-4 py-10 md:px-8 lg:px-12">
        <div className="max-w-6xl mx-auto">
          <div className="mb-6">
            <p className="text-sm uppercase tracking-[0.4em] text-[#FFC72C] mb-2">Facility Gallery</p>
            <h2 className="text-3xl md:text-4xl font-bold">Ashland Esports Gaming Arena</h2>            
          </div>

          <div className="space-y-6">
            <div className="w-full h-52 md:h-60 overflow-hidden rounded-[1.25rem] bg-slate-900 glow-outline hover:h-64 md:hover:h-72 transition-all duration-300">
              <Image
                src={facilityPhotos[0].src}
                alt={facilityPhotos[0].alt}
                width={1200}
                height={600}
                className="object-cover w-full h-full"
              />
            </div>
            <div className="grid grid-cols-2 gap-6">
              {facilityPhotos.slice(1).map((photo) => (
                <div key={photo.src} className="h-52 md:h-72 overflow-hidden rounded-[1.25rem] bg-slate-900 glow-outline-purple hover:scale-105 transition-all duration-300">
                  <Image
                    src={photo.src}
                    alt={photo.alt}
                    width={600}
                    height={720}
                    className="object-cover w-full h-full"
                  />
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
      </div>
      );
}
