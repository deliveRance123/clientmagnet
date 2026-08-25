import { NextRequest, NextResponse } from "next/server";

let memoryServices: any[] = [
  {
    id: "srv_1",
    name: "Enterprise Client Acquisition Engine",
    description: "Multi-channel automated discovery, AI qualification, and personalized outreach infrastructure.",
    category: "Lead Generation & Outreach",
    price_min: 2500,
    price_max: 7500,
    target_audience: "B2B SaaS, Agency Founders, Consultancies",
    is_active: true,
    created_at: new Date().toISOString(),
  },
  {
    id: "srv_2",
    name: "AI WhatsApp Inbound & Qualification Agent",
    description: "Official WhatsApp Cloud API conversational agent that qualifies inbound prospects 24/7.",
    category: "AI Automation",
    price_min: 1500,
    price_max: 4000,
    target_audience: "E-commerce, Real Estate, Service Providers",
    is_active: true,
    created_at: new Date().toISOString(),
  },
];

export async function GET() {
  return NextResponse.json(memoryServices);
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const newService = {
      id: `srv_${Math.random().toString(36).substring(2, 7)}`,
      name: body.name || "Custom Client Solution",
      description: body.description || "Tailored high-converting B2B outreach package.",
      category: body.category || "Consulting",
      price_min: body.price_min || 1000,
      price_max: body.price_max || 5000,
      target_audience: body.target_audience || "Enterprise Clients",
      is_active: true,
      created_at: new Date().toISOString(),
    };
    memoryServices = [newService, ...memoryServices];
    return NextResponse.json(newService, { status: 201 });
  } catch (e: any) {
    return NextResponse.json({ detail: e.message || "Failed to create service" }, { status: 400 });
  }
}
