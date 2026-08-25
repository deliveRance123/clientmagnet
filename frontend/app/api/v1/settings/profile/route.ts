import { NextRequest, NextResponse } from "next/server";

let memoryProfile: any = {
  full_name: "Client Magnet Founder",
  company_name: "Client Magnet Growth",
  business_description: "Automated high-intent client acquisition and multi-channel outreach engine.",
  business_website: "https://clientmagnet-1.onrender.com",
  portfolio_links_json: "[]",
  preferred_tone: "Professional & Consultative",
  default_signature: "Best regards,\nClient Magnet Team",
  business_intro: "We help growing businesses automate client acquisition and scale revenue.",
  preferred_cta: "Would you be open to a 10-minute discovery chat this week?",
  notify_new_lead: true,
  notify_new_reply: true,
  notify_follow_up_due: true,
  notify_post_failed: true,
  notify_account_warning: true,
};

export async function GET() {
  return NextResponse.json(memoryProfile);
}

export async function PUT(req: NextRequest) {
  try {
    const body = await req.json();
    memoryProfile = { ...memoryProfile, ...body };
    return NextResponse.json(memoryProfile);
  } catch (e: any) {
    return NextResponse.json({ detail: e.message || "Failed to update profile" }, { status: 400 });
  }
}
