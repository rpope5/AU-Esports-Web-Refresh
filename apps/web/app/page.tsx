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
    '/ECAC.jpg',
    '/GLEC.jpg',
    '/NECC.jpg',
    '/CKL.jpg',
    '/PlayVS.jpg',
    '/CCL.jpg',
  ];
  
  
  const displayConferences = [...conferences, ...conferences, ...conferences, ...conferences,...conferences, ...conferences, ...conferences, ...conferences,...conferences, ...conferences, ...conferences];
  const displayImages = [...conferenceImages, ...conferenceImages, ...conferenceImages, ...conferenceImages,...conferenceImages, ...conferenceImages, ...conferenceImages, ...conferenceImages,...conferenceImages, ...conferenceImages, ...conferenceImages];
  
  const [currentConfIndex, setCurrentConfIndex] = useState(0);
  const [selectedConf, setSelectedConf] = useState<string | null>(null);

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

  return (
    <div className="min-hscreen bg-white text-black">
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
        <aside className="w-[20%] flex flex-col items-center text-black">
          <div className="text-xl mb-4">Leagues</div>

          <div className="w-full flex flex-col items-center gap-2">

            <div className="overflow-hidden w-full h-[36rem] bg-[#FFC72C] rounded-lg">
              <div
                className="transition-transform duration-700 relative"
                style={{ transform: `translateY(-${currentConfIndex * 12}rem)` }}
              >
                {displayConferences.map((conf, idx) => (
                  <div
                    key={`${conf}-${idx}`}
                    onClick={() => setSelectedConf(conferences[idx % conferences.length])}
                    className={`w-full h-48 flex flex-col items-center justify-center text-lg cursor-pointer transition-colors duration-200 hover:bg-[#5C068C] ${selectedConf === conf ? 'bg-[#5C068C] text-white font-semibold' : ''}`}
                  >
                    <span className="mb-3 text-black text-lg font-Gotham-Bold">{conf}</span>
                    <Image src={displayImages[idx]} alt={`${conf} logo`} width={112} height={112} className="w-28 h-28 object-contain" />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </aside>

        <div className="w-[60%] h-[500px] border-2 border-gray-700 rounded-lg overflow-hidden">
          <video
            src="/AshlandEsports.mp4"
            autoPlay
            loop
            muted
            className="w-full h-full object-cover rounded-lg"
          />
        </div>

        <div className="w-[20%] h-[650px]">
          <iframe
            src=""
            className="w-full h-full px-4 py-2 border-2 border-gray-700 rounded-lg"
          />
        </div>
      </main>
    </div>
  );
}
