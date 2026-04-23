"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import TopActivityFeedBar from "./components/TopActivityFeedBar";

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
    <div className="flex w-full flex-col">
      <h2 className="mb-2 text-center text-3xl font-bold text-[#FFC72C] md:text-4xl">
        Latest Posts
      </h2>
      <div className="twitter-box flex h-[26rem] w-full min-w-0 flex-col overflow-hidden rounded-md border-2 border-[#FFC72C] p-3 sm:h-[30rem] lg:h-[34rem] xl:h-[37.5rem]">

        <div
          id="twitter-scroll"
          className="flex min-h-0 flex-1 flex-col gap-3 overflow-x-hidden overflow-y-auto pr-1"
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

              <div className="mt-2 flex items-center justify-between">
                <a
                  href={tweet.link}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs text-[#FFC72C] hover:underline"
                >
                  View Post -&gt;
                </a>

                {tweet.pubDate && (
                  <span className="text-xs text-gray-500">
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

  const conferences = ["ECAC", "GLEC", "NECC", "CKL", "PlayVS", "CCL"];
  const conferenceImages = [
    "/ECAC.png",
    "/GLEC.png",
    "/NECC.png",
    "/CKL.png",
    "/PlayVS.jpg",
    "/CCL.png",
  ];

  const displayConferences = [
    ...conferences,
    ...conferences,
    ...conferences,
    ...conferences,
  ];

  const displayImages = [
    ...conferenceImages,
    ...conferenceImages,
    ...conferenceImages,
    ...conferenceImages,
  ];

  const [currentConfIndex, setCurrentConfIndex] = useState(0);
  const [selectedConf, setSelectedConf] = useState<string | null>(null);
  const [isLive, setIsLive] = useState(false);

  useEffect(() => {
    const checkLiveStatus = async () => {
      try {
        const res = await fetch(
          "https://decapi.me/twitch/uptime/ashlandesports"
        );
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
      setCurrentConfIndex(
        (prevIndex) => (prevIndex + 1) % displayConferences.length
      );
    }, 3000);

    return () => clearInterval(id);
  }, [displayConferences.length]);

  return (
    <div className="min-h-screen bg-black text-white">
      <TopActivityFeedBar />

      <header className="site-header flex flex-col items-center justify-between gap-4 p-4 md:flex-row">

        <div className="flex items-center gap-2">
          <Image
            src="/Eagle.png"
            alt="Ashland Eagle Logo"
            width={90}
            height={90}
            className="h-14 w-14 object-contain md:h-20 md:w-20"
          />

          <div className="flex min-w-0 flex-wrap items-center gap-2 sm:gap-3">
            <h1 className="title title-3d text-lg font-bold leading-tight tracking-wide md:text-2xl">
              Ashland University Esports
            </h1>

            {isLive && (
              <div className="flex items-center gap-2">
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#FFC72C] opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-[#FFC72C]"></span>
                </span>
                <span className="text-sm font-semibold text-[#FFC72C]">
                  LIVE
                </span>
              </div>
            )}
          </div>
        </div>

        <nav className="nav-buttons flex flex-wrap justify-center gap-4 text-sm md:gap-6 md:text-base">
          {pages.map((page) => (
            <Link key={page} href={pageMap[page] || "/"} className="relative group">
              {page}
              <span className="absolute left-0 -bottom-1 w-0 h-[2px] bg-[#FFC72C] transition-all duration-300 group-hover:w-full"></span>
            </Link>
          ))}
        </nav>

      </header>

      <div className="w-full h-[2px] bg-gradient-to-r from-transparent via-[#FFC72C] to-transparent opacity-70"></div>

      <main className="mx-auto w-full max-w-[1500px] px-4 py-8 sm:px-6 lg:px-8">
        <div className="grid items-start gap-6 md:grid-cols-[minmax(0,1fr)_minmax(220px,300px)] xl:grid-cols-[minmax(180px,220px)_minmax(0,1fr)_minmax(260px,320px)]">
          <div className="main-content order-1 md:row-span-2 xl:order-2 xl:row-span-1">
            <div className="video-container">
              <video
                src="/CS2.mp4"
                autoPlay
                loop
                muted
                className="h-full w-full rounded-lg object-cover"
              />
            </div>

            <div className="jersey-box">
              <h2>Get Your Jersey</h2>
              <p>Show your support for Ashland Esports</p>

              <div className="mt-4 flex w-full flex-col items-center gap-4 sm:flex-row sm:justify-center sm:gap-6">
                <a
                  href="https://critapparel.com/collections/ashland-university?_pos=1&_psq=Ashla&_ss=e&_v=1.0"
                  className="shop-btn"
                >
                  <img src="/crit.png" alt="Crit Apparel shop" className="w-40 max-w-full" />
                </a>

                <a
                  href="https://theinfiniteinc.com/collections/e-sports/products/ashland-university-original-e-sports-jersey"
                  className="shop-btn-alt"
                >
                  <img src="/jersey.png" alt="Ashland jersey shop" className="w-40 max-w-full" />
                </a>
              </div>
            </div>
          </div>

          <div className="order-2 md:col-start-2 md:row-start-2 xl:order-3 xl:col-start-3 xl:row-start-1">
            <TwitterFeed />
          </div>

          <aside className="leagues-aside order-3 md:col-start-2 md:row-start-1 xl:order-1 xl:col-start-1">
            <div className="mb-4 text-3xl md:text-4xl">Leagues</div>

            <div className="league-carousel overflow-hidden">
            <div
              className="carousel-track"
              style={{ transform: `translateY(-${currentConfIndex * 12}rem)` }}
            >
              {displayConferences.map((conf, idx) => (
                <div
                  key={`${conf}-${idx}`}
                  onClick={() =>
                    setSelectedConf(conferences[idx % conferences.length])
                  }
                  className={`league-card ${selectedConf === conf ? "selected" : ""}`}
                >
                  <span className="mb-3 text-lg font-Gotham-Bold text-black">
                    {conf}
                  </span>
                  <Image
                    src={displayImages[idx]}
                    alt={conf}
                    width={112}
                    height={112}
                    className="h-28 w-28 object-contain"
                  />
                </div>
              ))}
            </div>
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
}
