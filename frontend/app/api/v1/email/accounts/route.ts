import { NextRequest, NextResponse } from "next/server";

let memoryEmailAccounts: any[] = [
  {
    id: "em_acc_1",
    email_address: "joshuaoguntegbe200@gmail.com",
    provider: "gmail",
    sender_name: "Client Magnet Team",
    is_active: true,
    created_at: new Date().toISOString(),
  },
];

export async function GET() {
  return NextResponse.json(memoryEmailAccounts);
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const newAcc = {
      id: `em_acc_${Math.random().toString(36).substring(2, 7)}`,
      email_address: body.email_address || "joshuaoguntegbe200@gmail.com",
      provider: body.provider || "gmail",
      sender_name: body.sender_name || "Client Magnet",
      is_active: true,
      created_at: new Date().toISOString(),
    };
    memoryEmailAccounts = [newAcc, ...memoryEmailAccounts];
    return NextResponse.json(newAcc, { status: 201 });
  } catch (e: any) {
    return NextResponse.json({ detail: e.message || "Failed to connect email" }, { status: 400 });
  }
}
