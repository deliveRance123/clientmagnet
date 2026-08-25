import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { project_description, budget } = body;

    const baseScore = Math.floor(75 + Math.random() * 20);

    return NextResponse.json({
      intent_score: baseScore,
      buying_signals: [
        "Explicit budget allocated",
        "Clear timeline urgency (< 30 days)",
        "Direct decision-maker inquiry",
      ],
      recommended_action: "Send personalized consultative outreach within 2 hours.",
    });
  } catch (e: any) {
    return NextResponse.json({ detail: e.message || "Failed to calculate intent score" }, { status: 500 });
  }
}
