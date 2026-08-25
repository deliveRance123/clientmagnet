import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    total_leads: 24,
    high_intent_leads: 11,
    contacted_leads: 8,
    replied_leads: 5,
    converted_leads: 3,
    average_intent_score: 87.4,
  });
}
