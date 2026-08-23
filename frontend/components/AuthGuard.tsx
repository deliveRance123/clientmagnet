"use client";

import React, { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";

const AUTH_ROUTES = ["/login", "/register"];

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  const isAuthRoute = AUTH_ROUTES.includes(pathname);
  const isRootLanding = pathname === "/";

  useEffect(() => {
    if (!loading) {
      // If user is logged in and visits login or register, redirect to CRM
      if (user && isAuthRoute) {
        router.replace("/crm");
      }
      // If user is not logged in and visits a protected route, redirect to login
      else if (!user && !isAuthRoute && !isRootLanding) {
        router.replace("/login");
      }
    }
  }, [user, loading, isAuthRoute, isRootLanding, router]);

  // 1. Public Auth Pages (Login, Register) render immediately
  if (isAuthRoute) {
    return <div className="min-h-screen bg-slate-950 text-white">{children}</div>;
  }

  // 2. Root Landing Page renders immediately
  if (isRootLanding) {
    if (user) {
      // Logged-in user on root -> Dashboard layout
      return (
        <div className="flex min-h-screen bg-slate-50 overflow-x-hidden">
          <Sidebar />
          <div className="flex flex-1 flex-col w-full md:pl-64 transition-all duration-200 min-w-0">
            <Header />
            <main className="flex-1 pt-24 pb-12 px-4 sm:px-6 md:px-8 max-w-7xl w-full mx-auto min-w-0">{children}</main>
          </div>
        </div>
      );
    }
    // Unauthenticated visitor on root -> Full Landing Page
    return <div className="min-h-screen bg-slate-950 text-white selection:bg-sky-500 selection:text-white">{children}</div>;
  }

  // 3. Protected Dashboard Pages: show loading skeleton only while resolving user state
  if (loading) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-slate-950 text-white">
        <div className="flex flex-col items-center gap-4">
          <div className="relative h-16 w-16 flex-shrink-0 animate-pulse">
            <img
              src="/favicon.svg"
              alt="Client Magnet"
              width={64}
              height={64}
              style={{ width: "64px", height: "64px", maxWidth: "64px", maxHeight: "64px" }}
              className="h-16 w-16 drop-shadow-[0_0_20px_rgba(56,189,248,0.5)]"
            />
          </div>
          <div className="text-center">
            <h1 className="text-lg font-bold tracking-tight text-white">Client Magnet</h1>
            <p className="text-xs text-sky-400 font-medium mt-0.5">Connecting workspace...</p>
          </div>
        </div>
      </div>
    );
  }

  // 4. If unauthenticated on protected route
  if (!user) {
    return null;
  }

  // 5. Protected Application Dashboard layout
  return (
    <div className="flex min-h-screen bg-slate-50 overflow-x-hidden">
      <Sidebar />
      <div className="flex flex-1 flex-col w-full md:pl-64 transition-all duration-200 min-w-0">
        <Header />
        <main className="flex-1 pt-24 pb-12 px-4 sm:px-6 md:px-8 max-w-7xl w-full mx-auto min-w-0">{children}</main>
      </div>
    </div>
  );
}
