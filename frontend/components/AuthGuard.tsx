"use client";

import React, { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";

const AUTH_AUTH_ROUTES = ["/login", "/register"];

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  const isAuthRoute = AUTH_AUTH_ROUTES.includes(pathname);
  const isRootLanding = pathname === "/";

  useEffect(() => {
    if (!loading) {
      // If user is logged in and visits login or register, redirect to CRM
      if (user && isAuthRoute) {
        router.replace("/crm");
      }
      // If user is not logged in and visits a protected route (not root or auth route), redirect to login
      else if (!user && !isAuthRoute && !isRootLanding) {
        router.replace("/login");
      }
    }
  }, [user, loading, isAuthRoute, isRootLanding, router]);

  // Loading skeleton with official logo
  if (loading) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-slate-950 text-white">
        <div className="flex flex-col items-center gap-4">
          <div className="relative h-16 w-16 animate-pulse">
            <img
              src="/favicon.svg"
              alt="Client Magnet"
              className="h-16 w-16 drop-shadow-[0_0_20px_rgba(56,189,248,0.5)]"
            />
          </div>
          <div className="text-center">
            <h1 className="text-lg font-bold tracking-tight text-white">Client Magnet</h1>
            <p className="text-xs text-sky-400 font-medium mt-0.5">Accelerating engine...</p>
          </div>
        </div>
      </div>
    );
  }

  // Unauthenticated user trying to access private route (redirecting to /login)
  if (!user && !isAuthRoute && !isRootLanding) {
    return null;
  }

  // Authenticated user on login/register (redirecting to /crm)
  if (user && isAuthRoute) {
    return null;
  }

  // Public standalone layout (Login, Register)
  if (isAuthRoute) {
    return <div className="min-h-screen bg-slate-950">{children}</div>;
  }

  // Root Landing Page for unauthenticated visitors -> Full width modern landing page
  if (isRootLanding && !user) {
    return <div className="min-h-screen bg-slate-950 text-white selection:bg-sky-500 selection:text-white">{children}</div>;
  }

  // Protected Application Dashboard layout -> Responsive Desktop / Mobile Layout
  return (
    <div className="flex min-h-screen bg-slate-50 overflow-x-hidden">
      <Sidebar />
      <div className="flex flex-1 flex-col w-full md:pl-64 transition-all duration-200 min-w-0">
        <Header />
        <main className="flex-1 p-3.5 sm:p-6 md:p-8 max-w-7xl w-full mx-auto min-w-0">{children}</main>
      </div>
    </div>
  );
}
