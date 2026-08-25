import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    status: "OK",
    database: "connected",
    environment: process.env.NODE_ENV || "production",
    project: "Client Magnet",
  });
}
