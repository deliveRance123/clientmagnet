"use client";

import React, { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { resilientFetch } from "@/lib/api-config";
import Link from "next/link";
import { AlertCircle, ArrowLeft, CheckCircle2 } from "lucide-react";

function AuthCallbackContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { loginWithGoogle, setDirectAuth } = useAuth();

  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function handleOAuth() {
      const code = searchParams.get("code");
      const state = searchParams.get("state");
      const token = searchParams.get("token");
      const error = searchParams.get("error");
      const errorDescription = searchParams.get("error_description");

      if (error) {
        if (isMounted) {
          setStatus("error");
          setErrorMessage(errorDescription || error || "Google authorization was cancelled or failed.");
        }
        return;
      }

      // If backend already issued JWT token directly in redirect
      if (token) {
        try {
          const res = await resilientFetch("/auth/me", {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          });
          if (res.ok) {
            const user = await res.json();
            if (isMounted) {
              setDirectAuth(token, user);
              setStatus("success");
              setTimeout(() => {
                router.push("/");
              }, 800);
              return;
            }
          }
        } catch (err) {
          console.warn("Failed to fetch user with direct token:", err);
        }
      }

      // Standard OAuth code exchange flow
      if (code) {
        try {
          const redirectUri = typeof window !== "undefined"
            ? `${window.location.origin}/auth/callback`
            : "http://localhost:3000/auth/callback";

          const result = await loginWithGoogle({
            code,
            state: state || undefined,
            redirect_uri: redirectUri,
          });

          if (result.success) {
            if (isMounted) {
              setStatus("success");
              setTimeout(() => {
                router.push("/");
              }, 800);
            }
          } else {
            if (isMounted) {
              setStatus("error");
              setErrorMessage(result.error || "Google Sign-In verification failed. Please try again.");
            }
          }
        } catch (err) {
          if (isMounted) {
            setStatus("error");
            setErrorMessage("An unexpected error occurred during Google Sign-In.");
          }
        }
        return;
      }

      // Fallback mock flow if code or token not provided
      if (isMounted) {
        setStatus("error");
        setErrorMessage("No authorization credentials received from Google. Please try logging in again.");
      }
    }

    handleOAuth();

    return () => {
      isMounted = false;
    };
  }, [searchParams, router, loginWithGoogle, setDirectAuth]);

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-slate-950 px-4 py-12 sm:px-6 lg:px-8 overflow-hidden">
      {/* Background Glows */}
      <div className="absolute -top-40 -left-40 h-96 w-96 rounded-full bg-sky-500/15 blur-3xl pointer-events-none" />
      <div className="absolute -bottom-40 -right-40 h-96 w-96 rounded-full bg-indigo-500/15 blur-3xl pointer-events-none" />

      <div className="relative w-full max-w-md space-y-6">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-8 shadow-2xl backdrop-blur-xl text-center">
          {status === "loading" && (
            <div className="space-y-4 py-6">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-sky-500/10 border border-sky-500/30">
                <span className="h-6 w-6 animate-spin rounded-full border-2 border-sky-400 border-t-transparent" />
              </div>
              <h3 className="text-lg font-bold text-white">
                Authenticating with Google...
              </h3>
              <p className="text-xs text-slate-400">
                Verifying your credentials and preparing your dashboard session.
              </p>
            </div>
          )}

          {status === "success" && (
            <div className="space-y-4 py-6">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                <CheckCircle2 className="h-8 w-8" />
              </div>
              <h3 className="text-lg font-bold text-white">
                Authentication Successful!
              </h3>
              <p className="text-xs text-slate-400">
                Redirecting you to your dashboard...
              </p>
            </div>
          )}

          {status === "error" && (
            <div className="space-y-5 py-4">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400">
                <AlertCircle className="h-8 w-8" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">
                  Google Sign-In Failed
                </h3>
                <p className="mt-2 text-xs text-red-400 bg-red-500/10 border border-red-500/20 p-3 rounded-lg">
                  {errorMessage}
                </p>
              </div>

              <div className="pt-2">
                <Link
                  href="/login"
                  className="inline-flex items-center justify-center gap-2 w-full rounded-lg bg-slate-800 hover:bg-slate-700 py-2.5 text-xs font-semibold text-white transition border border-slate-700"
                >
                  <ArrowLeft className="h-4 w-4" /> Return to Login
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-slate-950">
          <span className="h-8 w-8 animate-spin rounded-full border-2 border-sky-400 border-t-transparent" />
        </div>
      }
    >
      <AuthCallbackContent />
    </Suspense>
  );
}
