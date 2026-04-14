"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";

function TwitterFeed() {
  const [tweets, setTweets] = useState<any[]>([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);

  const loadTweets = async (nextPage: number) => {
    if (loading) return;

    setLoading(true);

    try {
      const res = await fetch(`/api/twitter?page=${nextPage}`);
      const data = await res.json();

      if (data.items) {
        setTweets((prev) => [...prev, ...data.items]);
        setHasMore(data.hasMore);
      }
    } catch {}

    setLoading(false);
  };

  useEffect(() => {
    loadTweets(1);
  }, []);

  useEffect(() => {
    const handleScroll = () => {
      const el = document.getElementById("twitter-scroll");
      if (!el || loading || !hasMore) return;

      if (el.scrollTop + el.clientHeight >= el.scrollHeight - 50) {
        const nextPage = page + 1;
        setPage(nextPage);
        loadTweets(nextPage);
      }
    };

    const el = document.getElementById("twitter-scroll");
    el?.addEventListener("scroll", handleScroll);

    return () => el?.removeEventListener("scroll", handleScroll);
  }, [page, loading, hasMore]);

  return (
    <div className="twitter-box h-[500px] w-[250px] border-2 border-gray-700 rounded-md overflow-hidden p-3">
      <h2 className="text-[#FFC72C] font-bold mb-2 text-center">
        Latest Posts
      </h2>

      <div
        id="twitter-scroll"
        className="flex flex-col gap-3 overflow-y-auto h-[440px] pr-1"
      >
        {tweets.length === 0 && !loading && (
          <p className="text-gray-400 text-sm text-center">Loading...</p>
        )}

        {tweets.map((tweet, index) => (
          <div key={index} className="border-b border-gray-700 pb-2">
            <p
              className="text-sm"
              dangerouslySetInnerHTML={{ __html: tweet.title }}
            />

            <div className="flex justify-between items-center mt-2">
              <a
                href={tweet.link}
                target="_blank"
                rel="noreferrer"
                className="text-[#FFC72C] text-xs hover:underline"
              >
                View Post →
              </a>

              {tweet.pubDate && (
                <span className="text-gray-500 text-xs">
                  {new Date(tweet.pubDate).toLocaleDateString()}
                </span>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <p className="text-gray-400 text-xs text-center">
            Loading more...
          </p>
        )}

        {!hasMore && tweets.length > 0 && (
          <p className="text-gray-500 text-xs text-center">
            No more posts
          </p>
        )}
      </div>
    </div>
  );
}

export default function Home() {
  const pages = [
    "Home",
    "Roster",
    "Schedule",
    "News",
    "Stream",
    "Recruitment",
    "Facility",
    "Support",
    "Hall of Fame",
  ];

  const pageMap: Record<string, string> = {
    Home: "/",
    Roster: "/roster",
    Schedule: "/schedule",
    News: "/news",
    Stream: "/stream",
    Recruitment: "/recruit",
    Facility: "/facility",
    Support: "/support",
    "Hall of Fame": "/hof",
  };

  const conferences = ["ECAC","GLEC","NECC","CKL","PlayVS","CCL"];
  const conferenceImages = [
    "/ECAC.png","/GLEC.png","/NECC.jpg","/CKL.png","/PlayVS.jpg","/CCL.jpg",
  ];

  const displayConferences = [...conferences, ...conferences, ...conferences, ...conferences];
  const displayImages = [...conferenceImages, ...conferenceImages, ...conferenceImages, ...conferenceImages];

  const [currentConfIndex, setCurrentConfIndex] = useState(0);
  const [selectedConf, setSelectedConf] = useState<string | null>(null);
  const [isLive, setIsLive] = useState(false);
  const [matches, setMatches] = useState<any[]>([]);

  useEffect(() => {
    const tryLoad = async () => {
      try {
        const res = await fetch("/data/matches.json");
        if (!res.ok) throw new Error("failed");
        const data = await res.json();
        if (Array.isArray(data) && data.length) setMatches(data);
      } catch {}
    };
    tryLoad();
  }, []);

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

  useEffect(() => {
    const id = setInterval(() => {
      setCurrentConfIndex((prevIndex) => (prevIndex + 1) % displayConferences.length);
    }, 3000);

    return () => clearInterval(id);
  }, [displayConferences.length]);

  const [matchStart, setMatchStart] = useState(0);
  const matchesToShow = 5;

  const prevMatches = () => setMatchStart((s) => Math.max(0, s - 1));
  const nextMatches = () =>
    setMatchStart((s) =>
      Math.min(Math.max(0, matches.length - matchesToShow), s + 1)
    );

  return (
    <div className="min-h-screen bg-black text-white">

      <div className="match-bar">
        <button onClick={prevMatches} disabled={matchStart === 0}>&larr;</button>

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
            <h1
              className="title title-3d text-lg md:text-2xl font-bold tracking-wide"
              style={{ textShadow: "1px 1px #333" }}
            >
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
          {pages.map((page) => (
            <Link key={page} href={pageMap[page] || "/"} className="relative group">
              {page}
              <span className="absolute left-0 -bottom-1 w-0 h-[2px] bg-[#FFC72C] transition-all duration-300 group-hover:w-full"></span>
            </Link>
          ))}
        </nav>

      </header>

      <div className="w-full h-[2px] bg-gradient-to-r from-transparent via-[#FFC72C] to-transparent opacity-70"></div>

      <main className="flex justify-between items-start px-10 py-10 gap-6">

        <aside className="leagues-aside">
          <div className="text-xl mb-4">Leagues</div>

          <div className="league-carousel overflow-hidden h-48">
            <div
              className="carousel-track"
              style={{ transform: `translateY(-${currentConfIndex * 12}rem)` }}
            >
              {displayConferences.map((conf, idx) => (
                <div
                  key={`${conf}-${idx}`}
                  onClick={() => setSelectedConf(conferences[idx % conferences.length])}
                  className={`league-card h-48 ${selectedConf === conf ? "selected" : ""}`}
                >
                  <span className="mb-3 text-black text-lg font-Gotham-Bold">
                    {conf}
                  </span>
                  <Image
                    src={displayImages[idx]}
                    alt={conf}
                    width={112}
                    height={112}
                    className="w-28 h-28 object-contain"
                  />
                </div>
              ))}
            </div>
          </div>
        </aside>

        <div className="main-content">
          <div className="video-container">
            <video
              src="/CS2.mp4"
              autoPlay
              loop
              muted
              className="w-full h-full object-cover rounded-lg"
            />
          </div>

          <div className="jersey-box">
            <h2>Get Your Jersey</h2>
            <p>Show your support for Ashland Esports</p>

            <div className="flex justify-between items-center mt-4">
              <a
                href="https://critapparel.com/collections/ashland-university?_pos=1&_psq=Ashla&_ss=e&_v=1.0"
                className="shop-btn"
              >
                <img src="/crit.png" className="w-40" />
              </a>

              <a
                href="https://theinfiniteinc.com/collections/e-sports/products/ashland-university-original-e-sports-jersey"
                className="shop-btn-alt"
              >
                <img src="/jersey.png" className="w-40" />
              </a>
            </div>
          </div>
        </div>

        <TwitterFeed />

      </main>
    </div>
  );
}