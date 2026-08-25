import { NextRequest, NextResponse } from "next/server";
import { sendOTPEmail } from "@/lib/email-otp";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { email, purpose } = body;
    if (!email) {
      return NextResponse.json({ detail: "Email is required." }, { status: 400 });
    }

    const result = await sendOTPEmail(email, purpose || "registration");
    if (!result.success) {
      return NextResponse.json({ detail: result.message }, { status: 400 });
    }

    return NextResponse.json({
      success: true,
      message: result.message,
      expires_in_seconds: 600,
    });
  } catch (err: any) {
    return NextResponse.json({ detail: err.message || "Failed to send OTP." }, { status: 500 });
  }
}
