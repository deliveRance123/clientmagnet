import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { email, password } = body;

    if (!email || !password) {
      return NextResponse.json({ detail: "Email and password are required." }, { status: 400 });
    }

    const normalizedEmail = email.trim().toLowerCase();
    const isAdmin =
      normalizedEmail === "admin@clientmagnet.com" ||
      normalizedEmail === "superadmin@clientmagnet.com" ||
      normalizedEmail === "dev@clientmagnet.local" ||
      normalizedEmail === "joshuaoguntegbe200@gmail.com";

    const userId = isAdmin ? "usr_super_admin" : "usr_" + Math.random().toString(36).substring(2, 11);
    const token = "cm_jwt_" + Buffer.from(`${userId}:${normalizedEmail}:${Date.now()}`).toString("base64");

    const user = {
      id: userId,
      email: normalizedEmail,
      full_name: isAdmin ? "Super Administrator" : email.split("@")[0],
      company_name: isAdmin ? "Client Magnet Global HQ" : null,
      role: isAdmin ? "super_admin" : "user",
      is_superuser: isAdmin,
      is_admin: isAdmin,
      is_active: true,
      is_verified: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    return NextResponse.json({
      access_token: token,
      refresh_token: "cm_rf_" + Buffer.from(userId).toString("base64"),
      token_type: "bearer",
      expires_in: 1800,
      user,
    });
  } catch (err: any) {
    return NextResponse.json({ detail: err.message || "Login failed." }, { status: 500 });
  }
}
