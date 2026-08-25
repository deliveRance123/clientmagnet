import { NextRequest, NextResponse } from "next/server";
import { verifyOTPCode } from "@/lib/email-otp";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { email, password, full_name, company_name, otp } = body;

    if (!email || !password) {
      return NextResponse.json({ detail: "Email and password are required." }, { status: 400 });
    }

    if (password.length < 8) {
      return NextResponse.json({ detail: "Password must be at least 8 characters long." }, { status: 422 });
    }

    if (otp) {
      const otpRes = verifyOTPCode(email, otp, "registration");
      if (!otpRes.success) {
        return NextResponse.json({ detail: otpRes.message }, { status: 400 });
      }
    }

    const userId = "usr_" + Math.random().toString(36).substring(2, 11);
    const token = "cm_jwt_" + Buffer.from(`${userId}:${email}:${Date.now()}`).toString("base64");

    const user = {
      id: userId,
      email: email.trim().toLowerCase(),
      full_name: full_name?.trim() || "Client Magnet User",
      company_name: company_name?.trim() || null,
      is_active: true,
      is_verified: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    return NextResponse.json(
      {
        access_token: token,
        refresh_token: "cm_rf_" + Buffer.from(userId).toString("base64"),
        token_type: "bearer",
        expires_in: 1800,
        user,
      },
      { status: 201 }
    );
  } catch (err: any) {
    return NextResponse.json({ detail: err.message || "Registration failed." }, { status: 500 });
  }
}
