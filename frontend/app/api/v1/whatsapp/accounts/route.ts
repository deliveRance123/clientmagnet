import { NextRequest, NextResponse } from "next/server";

let memoryWhatsAppAccounts: any[] = [
  {
    id: "wa_acc_1",
    phone_number: "+1 (555) 019-2834",
    phone_number_id: "phone_num_id_99201",
    business_account_id: "waba_id_881920",
    account_name: "Client Magnet Cloud API",
    status: "connected",
    is_active: true,
    created_at: new Date().toISOString(),
  },
];

export async function GET() {
  return NextResponse.json(memoryWhatsAppAccounts);
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const newAcc = {
      id: `wa_acc_${Math.random().toString(36).substring(2, 7)}`,
      phone_number: body.phone_number || "+1 (555) 019-2834",
      phone_number_id: body.phone_number_id || "phone_num_id_99201",
      business_account_id: body.business_account_id || "waba_id_881920",
      account_name: body.account_name || "Client Magnet Outreach WhatsApp",
      status: "connected",
      is_active: true,
      created_at: new Date().toISOString(),
    };
    memoryWhatsAppAccounts = [newAcc, ...memoryWhatsAppAccounts];
    return NextResponse.json(newAcc, { status: 201 });
  } catch (e: any) {
    return NextResponse.json({ detail: e.message || "Failed to connect WhatsApp" }, { status: 400 });
  }
}
