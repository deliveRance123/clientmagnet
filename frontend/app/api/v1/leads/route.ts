import { NextRequest, NextResponse } from "next/server";

let memoryLeads: any[] = [
  {
    id: "lead_1",
    name: "Alexander Vance",
    email: "alexander@vanceholdings.com",
    company: "Vance Growth Partners",
    source: "LinkedIn Discovery",
    status: "replied",
    intent_score: 94,
    lead_score: 92,
    intent_summary: "Actively seeking multi-channel outreach infrastructure for B2B acquisition.",
    created_at: new Date(Date.now() - 3600000 * 4).toISOString(),
  },
  {
    id: "lead_2",
    name: "Elena Rostova",
    email: "elena@rostovacapital.io",
    company: "Rostova Capital",
    source: "Google Places AI",
    status: "contacted",
    intent_score: 89,
    lead_score: 88,
    intent_summary: "Expanding SaaS portfolio and requested automated client acquisition workflow.",
    created_at: new Date(Date.now() - 3600000 * 12).toISOString(),
  },
  {
    id: "lead_3",
    name: "Marcus Sterling",
    email: "marcus@sterlingmedia.co",
    company: "Sterling Media Group",
    source: "X (Twitter) Inbound",
    status: "discovered",
    intent_score: 85,
    lead_score: 84,
    intent_summary: "Looking to replace manual cold outreach with AI qualification agent.",
    created_at: new Date(Date.now() - 3600000 * 24).toISOString(),
  },
];

export async function GET() {
  return NextResponse.json(memoryLeads);
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const newLead = {
      id: `lead_${Math.random().toString(36).substring(2, 7)}`,
      name: body.name || "New Prospect",
      email: body.email || "prospect@example.com",
      company: body.company || "Enterprise Lead",
      source: body.source || "Manual Entry",
      status: body.status || "discovered",
      intent_score: body.intent_score || 88,
      lead_score: body.lead_score || 85,
      intent_summary: body.intent_summary || "Qualified high-intent enterprise lead.",
      created_at: new Date().toISOString(),
    };
    memoryLeads = [newLead, ...memoryLeads];
    return NextResponse.json(newLead, { status: 201 });
  } catch (e: any) {
    return NextResponse.json({ detail: e.message || "Failed to create lead" }, { status: 400 });
  }
}
