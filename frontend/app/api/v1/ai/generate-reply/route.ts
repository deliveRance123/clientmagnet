import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { lead_name, context, channel } = body;

    const name = lead_name || "there";
    const selectedChannel = (channel || "email").toLowerCase();

    let draft = "";
    if (selectedChannel === "whatsapp") {
      draft = `Hi ${name}! 👋 Noticed your team is looking to upgrade your outreach workflows. We specialize in automated client acquisition engines. Would you be open to a quick 5-min WhatsApp chat this week to explore if we can help?`;
    } else {
      draft = `Hi ${name},\n\nI came across your recent project requirements and noticed you're looking for a reliable partner to scale your client acquisition.\n\nWe recently helped a similar agency increase their qualified pipeline by 34% using automated intent scoring and consultative outreach.\n\nWould you be open to a brief 10-minute discovery call this Thursday at 2 PM to explore potential synergies?\n\nBest regards,\nClient Magnet Team`;
    }

    return NextResponse.json({
      suggested_reply: draft,
      tone: "Consultative & Value-First",
      channel: selectedChannel,
    });
  } catch (e: any) {
    return NextResponse.json({ detail: e.message || "Failed to generate reply" }, { status: 500 });
  }
}
