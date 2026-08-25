import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  const searchParams = req.nextUrl.searchParams;
  const redirectUri = searchParams.get("redirect_uri") || "http://localhost:3000/auth/callback";
  const state = Math.random().toString(36).substring(2);

  const googleClientId = process.env.GOOGLE_CLIENT_ID;
  if (googleClientId && process.env.GOOGLE_CLIENT_SECRET && process.env.USE_MOCK_GOOGLE_AUTH !== "true") {
    const scopes = encodeURIComponent("openid email profile");
    const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${googleClientId}&redirect_uri=${encodeURIComponent(
      redirectUri
    )}&response_type=code&scope=${scopes}&access_type=offline&prompt=consent&state=${state}`;
    return NextResponse.json({ authorization_url: authUrl, state });
  }

  // Mock / instant callback
  const mockUrl = `${redirectUri}?code=mock_google_auth_code_${Math.random().toString(36).substring(2, 8)}&state=${state}`;
  return NextResponse.json({ authorization_url: mockUrl, state });
}
