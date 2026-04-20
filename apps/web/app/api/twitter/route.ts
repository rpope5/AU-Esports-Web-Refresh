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
    const page = parseInt(searchParams.get("page") || "1");
    const limit = 5;

    const res = await fetch(
      "https://api.rss2json.com/v1/api.json?rss_url=https://nitter.net/AshlandEsports/rss"
    );

    const data: RssFeedResponse = await res.json();
    const allItems = data.items ?? [];

    const start = (page - 1) * limit;
    const end = start + limit;

    const tweets = allItems.slice(start, end).map((item: RssItem) => {
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
      hasMore: end < allItems.length,
    });
  } catch {
    return NextResponse.json({ items: [], hasMore: false });
  }
}
