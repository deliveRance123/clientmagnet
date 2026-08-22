import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";
import AuthGuard from "@/components/AuthGuard";

export const metadata: Metadata = {
  title: "Client Magnet - Global Client Discovery & CRM Platform",
  description: "AI-powered client acquisition, automated lead discovery, visual CRM pipeline, and omnichannel outreach for modern businesses.",
  icons: {
    icon: [
      { url: "/favicon.svg", type: "image/svg+xml" },
      { url: "/icon.svg", type: "image/svg+xml" },
    ],
    apple: [
      { url: "/favicon.svg", type: "image/svg+xml" },
    ],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full">
      <body className="h-full antialiased font-sans text-slate-900 bg-slate-50">
        <AuthProvider>
          <AuthGuard>{children}</AuthGuard>
        </AuthProvider>
      </body>
    </html>
  );
}
