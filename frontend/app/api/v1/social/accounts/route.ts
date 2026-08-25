import { NextRequest, NextResponse } from "next/server";

let memorySocialAccounts: any[] = [
  {
    id: "soc_meta_1",
    platform: "meta",
    account_name: "Client Magnet Official",
    account_id: "meta_page_1029384",
    status: "active",
    connected_at: new Date().toISOString(),
    token_expires_at: new Date(Date.now() + 60 * 86400000).toISOString(),
    is_valid: true,
  },
  {
    id: "soc_x_1",
    platform: "x",
    account_name: "@ClientMagnetAI",
    account_id: "x_user_88291",
    status: "active",
    connected_at: new Date().toISOString(),
    token_expires_at: new Date(Date.now() + 90 * 86400000).toISOString(),
    is_valid: true,
  },
  {
    id: "soc_linkedin_1",
    platform: "linkedin",
    account_name: "Client Magnet Agency",
    account_id: "li_org_492019",
    status: "active",
    connected_at: new Date().toISOString(),
    token_expires_at: new Date(Date.now() + 60 * 86400000).toISOString(),
    is_valid: true,
  },
  {
    id: "soc_tiktok_1",
    platform: "tiktok",
    account_name: "@clientmagnet",
    account_id: "tt_user_11029",
    status: "active",
    connected_at: new Date().toISOString(),
    token_expires_at: new Date(Date.now() + 30 * 86400000).toISOString(),
    is_valid: true,
  },
];

export async function GET() {
  return NextResponse.json(memorySocialAccounts);
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const newAccount = {
      id: `soc_${body.platform || "meta"}_${Math.random().toString(36).substring(2, 7)}`,
      platform: body.platform,
      account_name: body.account_name || `${body.platform} Connected Account`,
      account_id: body.account_id || `acc_${Math.random().toString(36).substring(2, 8)}`,
      status: "active",
      connected_at: new Date().toISOString(),
      token_expires_at: new Date(Date.now() + 60 * 86400000).toISOString(),
      is_valid: true,
    };
    memorySocialAccounts = [newAccount, ...memorySocialAccounts.filter((a) => a.platform !== body.platform)];
    return NextResponse.json(newAccount, { status: 201 });
  } catch (e: any) {
    return NextResponse.json({ detail: e.message || "Failed to connect account" }, { status: 400 });
  }
}

export async function DELETE(req: NextRequest) {
  const searchParams = req.nextUrl.searchParams;
  const platform = searchParams.get("platform");
  const id = searchParams.get("id");
  if (id) {
    memorySocialAccounts = memorySocialAccounts.filter((a) => a.id !== id);
  } else if (platform) {
    memorySocialAccounts = memorySocialAccounts.filter((a) => a.platform !== platform);
  }
  return NextResponse.json({ success: true, message: "Account disconnected successfully" });
}
