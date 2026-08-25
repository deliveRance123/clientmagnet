import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    pipeline_stages: [
      { stage: "Lead Discovered", count: 24, value: 72000 },
      { stage: "AI Contacted", count: 18, value: 54000 },
      { stage: "Discovery Call", count: 9, value: 31500 },
      { stage: "Proposal Sent", count: 6, value: 24000 },
      { stage: "Closed Won", count: 5, value: 22500 },
    ],
    monthly_growth: [
      { month: "Jan", revenue: 8400, leads: 14 },
      { month: "Feb", revenue: 11200, leads: 22 },
      { month: "Mar", revenue: 14200, leads: 31 },
    ],
  });
}
