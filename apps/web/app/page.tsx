"use client";
import { useState, useEffect } from "react";
import Image from 'next/image'

export default function Home() {
  const pages = ["Home", "Roster", "Schedule", "News", "Stream", "Recruitment", "Facility", "Support"];

  const conferences = [
    "ECAC",
    "GLEC",
    "NECC",
    "CKL",
    "PlayVS",
    "CCL"
  ];
  const [currentConfIndec, setCurrentConfIndec] = useState(0);
  const [selectedConf, setSelectedConf] = useState<string | null>(null);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentConfIndec((prevIndex) => (prevIndex + 1) % conferences.length);
    }, 3000); // Change every 3 seconds
    return () => clearInterval(timer);
  }, [conferences.length]);

  return (
    <div className="min-hscreen bg-black text-white">
      {/*Header*/}
      <header className="w-full bg-gray-900 text-white px-8 py-4 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <Image src="/Eagle.png" alt="Ashland Eagle Logo" width={40} height={40} className="w-10 h-10 object-contain" />
          <h1 className="text-2xl font-bold">Ashland Esports</h1>
        </div>
        <nav className="flex gap-6">
          {pages.map((page) => (
            <button key={page} className="hover:underline">
              {page}
            </button>
          ))}p
        </nav>
      </header>

      <main className="flex justify-between items-start px-10 py-10 gap-6">
        <div className="w-[20%] flex flex-col items-center text-white">
          <div className="text-xl mb-4">Leauges</div>
          <button
            onClick={() => setSelectedConf(conferences[currentConfIndec])}
            className="text=2x1 font-bold hover:text-red-500 transition"
            >
            {conferences[currentConfIndec]}
            </button>
        </div>
      </main>
    </div>
  );
}
