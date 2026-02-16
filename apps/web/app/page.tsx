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
  const conferenceImages = [
    '/Hub/ECAC.svg',
    '/Hub/GLEC.svg',
    '/Hub/NECC.svg',
    '/Hub/CKL.svg',
    '/Hub/PlayVS.svg',
    '/Hub/CCL.svg',
  ];
  const [currentConfIndex, setCurrentConfIndex] = useState(0);
  const [selectedConf, setSelectedConf] = useState<string | null>(null);

  const prev = () => {
    setCurrentConfIndex((prevIndex) => (prevIndex === 0 ? conferences.length - 1 : prevIndex - 1));
  };

  const next = () => {
    setCurrentConfIndex((prevIndex) => (prevIndex === conferences.length - 1 ? 0 : prevIndex + 1));
  };

  // Autoplay vertical carousel
  useEffect(() => {
    const id = setInterval(() => {
      setCurrentConfIndex((i) => (i === conferences.length - 1 ? 0 : i + 1));
    }, 3000);
    return () => clearInterval(id);
  }, [conferences.length]);

  return (
    <div className="min-hscreen bg-black text-white">
      {/*Header*/}
      <header className="w-full bg-[#5C068C] text-white px-8 py-4 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <Image src="/Eagle.png" alt="Ashland Eagle Logo" width={40} height={40} className="w-10 h-10 object-contain" />
          <h1 className="text-2xl font-Gotham-Bold">Ashland Esports</h1>
        </div>
        <nav className="flex gap-6">
          {pages.map((page) => (
            <button key={page} className="hover:underline">
              {page}
            </button>
          ))}
        </nav>
      </header>

      <main className="flex justify-between items-start px-10 py-10 gap-6">
        <aside className="w-[20%] flex flex-col items-center text-white">
          <div className="text-xl mb-4">Leages</div>

          <div className="w-full flex flex-col items-center gap-2">

            <div className="overflow-hidden w-full h-36">
              <div
                className="transition-transform duration-700 relative"
                style={{ transform: `translateY(-${currentConfIndex * 9}rem)` }}
              >
                {conferences.map((conf, idx) => {
                  const isActive = idx === currentConfIndex;
                  return (
                    <div
                      key={`${conf}-${idx}`}
                      onClick={() => setSelectedConf(conf)}
                      className={`w-full h-36 flex flex-col items-center justify-center text-lg cursor-pointer transition-opacity duration-500 ${isActive ? 'opacity-100' : 'opacity-0 pointer-events-none'} ${selectedConf === conf ? 'bg-gray-700 font-semibold' : ''}`}
                    >
                        <span className="mb-3 text-white text-lg font-medium">{conf}</span>
                        <Image src={conferenceImages[idx]} alt={`${conf} logo`} width={112} height={112} className="w-28 h-28 object-contain" />
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </aside>

        <div className="w-[60%]">
          <video
            src="/AshlandEsports.mp4"
            autoPlay
            loop
            muted
            className="w-full h-full object-cover rounded-lg"
          />
        </div>

        <div className="w-[20%] h-[500px]">
          <iframe
            src=""
            className="w-full h-full px-4 py-2 border-2 border-gray-700 rounded-lg"
          />
        </div>
      </main>
    </div>
  );
}
