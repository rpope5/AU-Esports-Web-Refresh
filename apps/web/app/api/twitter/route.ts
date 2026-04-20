import { NextResponse } from "next/server";

type RssItem = {
  title?: string;
  pubDate?: string;
  link?: string;
};

type RssFeedResponse = {
  items?: RssItem[];
};

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const requestedLimit = Number.parseInt(searchParams.get("limit") || "6", 10);
    const limit = Number.isNaN(requestedLimit) ? 6 : Math.min(Math.max(requestedLimit, 1), 12);

    const res = await fetch(
      "https://api.rss2json.com/v1/api.json?rss_url=https://nitter.net/AshlandEsports/rss"
    );

    const data: RssFeedResponse = await res.json();
    const allItems = data.items ?? [];
    const recentItems = [...allItems]
      .sort((a, b) => {
        const aTime = a.pubDate ? new Date(a.pubDate).getTime() : 0;
        const bTime = b.pubDate ? new Date(b.pubDate).getTime() : 0;
        return bTime - aTime;
      })
      .slice(0, limit);

    const tweets = recentItems.map((item: RssItem) => {
      const match = item.link?.match(/status\/(\d+)/);

      let twitterLink = "https://twitter.com/AshlandEsports";
      if (match?.[1]) {
        twitterLink = `https://twitter.com/AshlandEsports/status/${match[1]}`;
      }

      return {
        title: item.title ?? "",
        pubDate: item.pubDate,
        link: twitterLink,
      };
    });

    return NextResponse.json({
      items: tweets,
      hasMore: false,
    });
  } catch {
    return NextResponse.json({ items: [], hasMore: false });
  }
}
