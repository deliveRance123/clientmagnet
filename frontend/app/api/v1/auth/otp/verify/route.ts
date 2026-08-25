import { NextRequest, NextResponse } from "next/server";
import { verifyOTPCode } from "@/lib/email-otp";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { email, otp, purpose } = body;
    if (!email || !otp) {
      return NextResponse.json({ detail: "Email and OTP code are required." }, { status: 400 });
    }

    const result = verifyOTPCode(email, otp, purpose || "registration");
    if (!result.success) {
      return NextResponse.json({ detail: result.message }, { status: 400 });
    }

    return NextResponse.json({
      success: true,
      message: result.message,
    });
  } catch (err: any) {
    return NextResponse.json({ detail: err.message || "Failed to verify OTP." }, { status: 500 });
  }
}
