import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { topic, platform, tone } = body;

    const selectedPlatform = (platform || "linkedin").toLowerCase();
    const selectedTone = tone || "Professional & Inspiring";

    const captions: Record<string, string> = {
      linkedin: `🚀 Scaling your client acquisition shouldn't require 40 hours of manual cold DMing every week.\n\nHere is how top-performing agencies are automating discovery and qualifying high-intent buyers on autopilot:\n\n1️⃣ Monitor real-time B2B job feeds\n2️⃣ Score lead intent with AI\n3️⃣ Send value-first, consultative messages\n\nWhat is your biggest bottleneck in signing clients right now? Let's discuss below. 👇\n\n#B2BGrowth #LeadGeneration #ClientAcquisition #AgencyScaling`,
      x: `Most agencies spend 80% of their time finding leads and only 20% delivering value.\n\nFlip the ratio. ⚡\n\nUse AI to score buying intent, automate qualification, and close deals in 1/3 the time.\n\n#AgencyLife #BuildInPublic #AIOutreach`,
      meta: `Looking to take your client pipeline to the next level? 🧲\n\nDiscover high-paying freelance projects and automate your outreach with Client Magnet.\n\n👉 Click the link in bio to start acquiring clients today! #FreelanceTips #AgencyGrowth`,
      tiktok: `Stop cold calling like it's 2010. ❌ Here is how to get high-ticket clients sent directly to your inbox every morning! 📈✨ #ClientMagnet #FreelanceHacks #AgencyOwner`,
    };

    return NextResponse.json({
      caption: captions[selectedPlatform] || captions.linkedin,
      platform: selectedPlatform,
      tone: selectedTone,
      hashtags: ["#LeadGen", "#ClientMagnet", "#AgencyGrowth"],
    });
  } catch (e: any) {
    return NextResponse.json({ detail: e.message || "Failed to generate caption" }, { status: 500 });
  }
}
