import { NextRequest, NextResponse } from "next/server";
import { sendOTPEmail } from "@/lib/email-otp";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { email } = body;
    if (!email) {
      return NextResponse.json({ detail: "Email is required." }, { status: 400 });
    }

    const result = await sendOTPEmail(email, "password_reset");
    return NextResponse.json({
      success: true,
      message: `Password reset code sent to ${email}.`,
      expires_in_seconds: 600,
    });
  } catch (err: any) {
    return NextResponse.json({ detail: err.message || "Failed to process request." }, { status: 500 });
  }
}
