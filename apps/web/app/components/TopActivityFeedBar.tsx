"use client";

import { useEffect, useMemo, useState } from "react";

import Header from "./Header";
import { fetchSiteActivityFeed, type SiteActivityFeedItem } from "@/lib/siteActivityFeed";

function resolveVisibleCount(viewportWidth: number): number {
  if (viewportWidth >= 1750) return 6;
  if (viewportWidth >= 1400) return 5;
  if (viewportWidth >= 1200) return 4;
  if (viewportWidth >= 900) return 3;
  if (viewportWidth >= 640) return 2;
  return 1;
}

function parseItemTime(item: SiteActivityFeedItem): Date | null {
  if (!item.startsAt) return null;
  const parsed = new Date(item.startsAt);
  if (Number.isNaN(parsed.getTime())) return null;
  return parsed;
}

function localDayStartMs(date: Date): number {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
}

function resolveInitialWindowStart(items: SiteActivityFeedItem[], visibleCount: number): number {
  if (!items.length) return 0;

  const now = new Date();
  const nowMs = now.getTime();
  const todayStart = localDayStartMs(now);
  const tomorrowStart = todayStart + 24 * 60 * 60 * 1000;

  const withTimes = items
    .map((item, index) => ({ index, time: parseItemTime(item) }))
    .filter((entry): entry is { index: number; time: Date } => entry.time !== null);

  if (!withTimes.length) return 0;

  const firstToday = withTimes.find((entry) => {
    const ms = entry.time.getTime();
    return ms >= todayStart && ms < tomorrowStart;
  });

  const referenceEntry =
    firstToday ??
    withTimes.reduce((best, current) => {
      const bestMs = best.time.getTime();
      const currentMs = current.time.getTime();
      const bestDiff = Math.abs(bestMs - nowMs);
      const currentDiff = Math.abs(currentMs - nowMs);

      if (currentDiff < bestDiff) return current;
      if (currentDiff > bestDiff) return best;

      const bestIsFuture = bestMs >= nowMs;
      const currentIsFuture = currentMs >= nowMs;
      if (currentIsFuture && !bestIsFuture) return current;
      if (!currentIsFuture && bestIsFuture) return best;

      return current.index < best.index ? current : best;
    });

  const referenceDayStart = localDayStartMs(referenceEntry.time);
  const dayStartIndex = withTimes.find((entry) => localDayStartMs(entry.time) === referenceDayStart)?.index ?? 0;
  const maxStartIndex = Math.max(0, items.length - visibleCount);
  return Math.min(dayStartIndex, maxStartIndex);
}

export default function TopActivityFeedBar() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const [items, setItems] = useState<SiteActivityFeedItem[]>([]);
  const [hasLoadedOnce, setHasLoadedOnce] = useState(false);
  const [manualStartIndex, setManualStartIndex] = useState<number | null>(null);
  const [visibleCount, setVisibleCount] = useState(5);

  useEffect(() => {
    const updateVisibleCount = () => {
      setVisibleCount(resolveVisibleCount(window.innerWidth));
    };
    updateVisibleCount();
    window.addEventListener("resize", updateVisibleCount);
    return () => window.removeEventListener("resize", updateVisibleCount);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    const loadFeed = async () => {
      try {
        const feedItems = await fetchSiteActivityFeed(apiUrl, { signal: controller.signal });
        if (!controller.signal.aborted) {
          setItems(feedItems);
        }
      } catch {
        if (!controller.signal.aborted) {
          setItems([]);
        }
      } finally {
        if (!controller.signal.aborted) {
          setHasLoadedOnce(true);
        }
      }
    };

    void loadFeed();

    const interval = window.setInterval(() => {
      void loadFeed();
    }, 60000);

    return () => {
      controller.abort();
      window.clearInterval(interval);
    };
  }, [apiUrl]);

  const maxStartIndex = Math.max(0, items.length - visibleCount);
  const autoStartIndex = useMemo(() => resolveInitialWindowStart(items, visibleCount), [items, visibleCount]);
  const rawStartIndex = manualStartIndex ?? autoStartIndex;
  const clampedStartIndex = Math.min(Math.max(0, rawStartIndex), maxStartIndex);
  const loading = !hasLoadedOnce;

  const visibleItems = useMemo(
    () => items.slice(clampedStartIndex, clampedStartIndex + visibleCount),
    [items, clampedStartIndex, visibleCount],
  );

  const canMoveLeft = clampedStartIndex > 0;
  const canMoveRight = clampedStartIndex < maxStartIndex;
  const prevItems = () => setManualStartIndex(Math.max(0, clampedStartIndex - 1));
  const nextItems = () => setManualStartIndex(Math.min(maxStartIndex, clampedStartIndex + 1));

  return (
    <div className="w-full bg-black px-3 py-2 sm:px-4">
      <div className="mx-auto flex w-full max-w-[1500px] flex-col gap-2 md:flex-row md:items-center md:justify-between md:gap-4 xl:grid xl:grid-cols-[minmax(160px,1fr)_minmax(0,980px)_minmax(160px,1fr)] xl:items-center">
        <div className="md:flex-shrink-0 xl:justify-self-start">
          <Header />
        </div>

        <div className="min-w-0 w-full md:max-w-[980px] md:flex-1 xl:col-start-2 xl:max-w-none">
          <div className="match-bar">
            <button
              type="button"
              className="match-arrow shrink-0"
              onClick={prevItems}
              disabled={!canMoveLeft}
              aria-label="Show earlier items"
            >
              &larr;
            </button>

            <div className="min-w-0 flex-1 overflow-hidden">
              <div className="match-list">
                {loading ? (
                  <div className="match-item">
                    <div className="match-teams">
                      <span className="team-name">Loading activity...</span>
                    </div>
                    <div className="match-game">Please wait</div>
                    <div className="match-time">Refreshing schedule events</div>
                  </div>
                ) : visibleItems.length > 0 ? (
                  visibleItems.map((item) => {
                    const subtitle = item.subtitle || "Scheduled event";

                    return (
                      <div className="match-item" key={item.id} title={item.title}>
                        <div className="match-teams">
                          <span className="team-name match-title">{item.title}</span>
                        </div>
                        <div className="match-game">{subtitle}</div>
                        <div className="match-time">{item.displayDate}</div>
                      </div>
                    );
                  })
                ) : (
                  <div className="match-item">
                    <div className="match-teams">
                      <span className="team-name">No schedule events yet</span>
                    </div>
                    <div className="match-game">Schedule feed</div>
                    <div className="match-time">Check back soon</div>
                  </div>
                )}
              </div>
            </div>

            <button
              type="button"
              className="match-arrow shrink-0"
              onClick={nextItems}
              disabled={!canMoveRight}
              aria-label="Show later items"
            >
              &rarr;
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
