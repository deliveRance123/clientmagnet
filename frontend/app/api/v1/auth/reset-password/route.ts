import { NextRequest, NextResponse } from "next/server";
import { verifyOTPCode } from "@/lib/email-otp";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { email, otp, new_password } = body;

    if (!email || !otp || !new_password) {
      return NextResponse.json({ detail: "Email, OTP code, and new password are required." }, { status: 400 });
    }

    if (new_password.length < 8) {
      return NextResponse.json({ detail: "Password must be at least 8 characters long." }, { status: 422 });
    }

    const otpRes = verifyOTPCode(email, otp, "password_reset");
    if (!otpRes.success) {
      return NextResponse.json({ detail: otpRes.message }, { status: 400 });
    }

    return NextResponse.json({ message: "Password has been reset successfully. You may now sign in." });
  } catch (err: any) {
    return NextResponse.json({ detail: err.message || "Failed to reset password." }, { status: 500 });
  }
}
