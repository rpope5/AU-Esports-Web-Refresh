import { NextResponse } from "next/server";

export async function GET() {
  try {
    const accessToken = process.env.INSTAGRAM_ACCESS_TOKEN;
    const userId = process.env.INSTAGRAM_USER_ID;

    const res = await fetch(
      `https://graph.facebook.com/v18.0/${userId}/media?fields=id,caption,media_url,permalink&access_token=${accessToken}`
    );

    const data = await res.json();

    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: "Failed to fetch Instagram" }, { status: 500 });
  }
}