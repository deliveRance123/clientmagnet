import { NextRequest, NextResponse } from "next/server";
import { verifyOTPCode } from "@/lib/email-otp";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { email, otp } = body;

    if (!email || !otp) {
      return NextResponse.json({ detail: "Email and OTP code are required." }, { status: 400 });
    }

    const otpRes = verifyOTPCode(email, otp, "login");
    if (!otpRes.success) {
      const regRes = verifyOTPCode(email, otp, "registration");
      if (!regRes.success) {
        return NextResponse.json({ detail: otpRes.message }, { status: 400 });
      }
    }

    const userId = "usr_" + Math.random().toString(36).substring(2, 11);
    const token = "cm_jwt_" + Buffer.from(`${userId}:${email}:${Date.now()}`).toString("base64");

    const user = {
      id: userId,
      email: email.trim().toLowerCase(),
      full_name: email.split("@")[0],
      company_name: null,
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
    return NextResponse.json({ detail: err.message || "OTP login failed." }, { status: 500 });
  }
}
