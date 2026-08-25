import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest, { params }: { params: { platform: string } }) {
  const platform = params.platform;
  const redirectUri = req.nextUrl.searchParams.get("redirect_uri") || "http://localhost:3000/social";
  const state = Math.random().toString(36).substring(2);

  // Return connected state callback
  const mockAuthUrl = `${redirectUri}?platform=${platform}&status=success&state=${state}`;

  return NextResponse.json({
    authorization_url: mockAuthUrl,
    state,
  });
}
