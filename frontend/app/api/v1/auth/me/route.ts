import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  const authHeader = req.headers.get("authorization");
  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  const token = authHeader.substring(7);
  let email = "user@clientmagnet.com";
  let userId = "usr_1";

  try {
    if (token.startsWith("cm_jwt_")) {
      const decoded = Buffer.from(token.replace("cm_jwt_", ""), "base64").toString("utf-8");
      const parts = decoded.split(":");
      if (parts.length >= 2) {
        userId = parts[0];
        email = parts[1];
      }
    }
  } catch (e) {}

  return NextResponse.json({
    id: userId,
    email,
    full_name: email.split("@")[0],
    company_name: null,
    is_active: true,
    is_verified: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  });
}
