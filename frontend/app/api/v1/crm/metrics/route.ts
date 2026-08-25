import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    total_clients: 12,
    active_deals: 8,
    pipeline_value: 48500,
    monthly_recurring_revenue: 14200,
    conversion_rate: 34.2,
    closed_won_count: 5,
  });
}
