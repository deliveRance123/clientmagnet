"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { Lock, Mail, Eye, EyeOff, ArrowRight, AlertCircle, ArrowLeft, KeyRound, CheckCircle2, ShieldCheck } from "lucide-react";

export default function LoginPage() {
  const [authMode, setAuthMode] = useState<"password" | "otp">("password");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [otpCode, setOtpCode] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [isSendingOtp, setIsSendingOtp] = useState(false);
  const [otpSent, setOtpSent] = useState(false);
  const [resendCountdown, setResendCountdown] = useState(0);

  // Forgot password modal states
  const [showForgotModal, setShowForgotModal] = useState(false);
  const [forgotEmail, setForgotEmail] = useState("");
  const [forgotOtp, setForgotOtp] = useState("");
  const [forgotNewPassword, setForgotNewPassword] = useState("");
  const [forgotStep, setForgotStep] = useState<"email" | "otp_and_pass">("email");
  const [forgotError, setForgotError] = useState<string | null>(null);
  const [forgotSuccess, setForgotSuccess] = useState<string | null>(null);
  const [forgotLoading, setForgotLoading] = useState(false);

  const { login, loginWithOTP, sendOTP, forgotPassword, resetPasswordWithOTP, initiateGoogleLogin } = useAuth();
  const router = useRouter();

  // Resend cooldown timer
  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (resendCountdown > 0) {
      timer = setTimeout(() => setResendCountdown(resendCountdown - 1), 1000);
    }
    return () => clearTimeout(timer);
  }, [resendCountdown]);

  const handleGoogleSignIn = async () => {
    setError(null);
    setIsGoogleLoading(true);
    try {
      await initiateGoogleLogin();
    } catch (err) {
      setError("Failed to initialize Google Sign-In. Please try again.");
      setIsGoogleLoading(false);
    }
  };

  const handleSendLoginOtp = async () => {
    if (!email.trim()) {
      setError("Please enter your work email first.");
      return;
    }
    setError(null);
    setSuccessMsg(null);
    setIsSendingOtp(true);
    const res = await sendOTP(email.trim(), "login");
    setIsSendingOtp(false);

    if (res.success) {
      setOtpSent(true);
      setResendCountdown(60);
      setSuccessMsg(res.message || "Verification code sent to your email.");
    } else {
      setError(res.error || "Failed to send verification code.");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    setIsSubmitting(true);

    if (authMode === "password") {
      const res = await login(email.trim(), password);
      setIsSubmitting(false);

      if (res.success) {
        router.push("/");
      } else {
        setError(res.error || "Invalid email or password. Please verify your credentials.");
      }
    } else {
      // OTP Login
      if (!otpCode.trim()) {
        setError("Please enter the 6-digit verification code sent to your email.");
        setIsSubmitting(false);
        return;
      }
      const res = await loginWithOTP(email.trim(), otpCode.trim());
      setIsSubmitting(false);

      if (res.success) {
        router.push("/");
      } else {
        setError(res.error || "Invalid verification code. Please check your email.");
      }
    }
  };

  // Forgot password flow
  const handleForgotSendCode = async () => {
    if (!forgotEmail.trim()) {
      setForgotError("Please enter your registered email address.");
      return;
    }
    setForgotError(null);
    setForgotSuccess(null);
    setForgotLoading(true);
    const res = await forgotPassword(forgotEmail.trim());
    setForgotLoading(false);

    if (res.success) {
      setForgotStep("otp_and_pass");
      setForgotSuccess(res.message || "Verification code sent.");
    } else {
      setForgotError(res.error || "Failed to send reset code.");
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setForgotError(null);
    setForgotSuccess(null);

    if (forgotNewPassword.length < 8) {
      setForgotError("Password must be at least 8 characters long.");
      return;
    }

    setForgotLoading(true);
    const res = await resetPasswordWithOTP({
      email: forgotEmail.trim(),
      otp: forgotOtp.trim(),
      new_password: forgotNewPassword,
    });
    setForgotLoading(false);

    if (res.success) {
      setForgotSuccess("Password reset successfully! You can now sign in.");
      setTimeout(() => {
        setShowForgotModal(false);
        setForgotStep("email");
        setSuccessMsg("Password reset successfully! Please sign in with your new password.");
      }, 1500);
    } else {
      setForgotError(res.error || "Password reset failed. Please check your code.");
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-slate-950 px-4 py-12 sm:px-6 lg:px-8 overflow-hidden">
      {/* Dynamic Background Glows */}
      <div className="absolute -top-40 -left-40 h-96 w-96 rounded-full bg-sky-500/15 blur-3xl pointer-events-none" />
      <div className="absolute -bottom-40 -right-40 h-96 w-96 rounded-full bg-indigo-500/15 blur-3xl pointer-events-none" />

      <div className="relative w-full max-w-md space-y-6">
        {/* Back to Landing Page navigation */}
        <div>
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-xs font-bold text-slate-400 hover:text-sky-400 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" /> Back to Landing Page
          </Link>
        </div>

        {/* Brand Header */}
        <div className="text-center">
          <Link href="/" className="inline-block group">
            <img
              src="/favicon.svg"
              alt="Client Magnet"
              width={56}
              height={56}
              style={{ width: "56px", height: "56px", maxWidth: "56px", maxHeight: "56px" }}
              className="h-14 w-14 mx-auto drop-shadow-[0_0_15px_rgba(56,189,248,0.5)] group-hover:scale-105 transition-transform"
            />
          </Link>
          <h2 className="mt-4 text-3xl font-extrabold tracking-tight text-white">
            Client Magnet
          </h2>
          <p className="mt-2 text-sm text-slate-400">
            Sign in to access your multi-user outreach dashboard
          </p>
        </div>

        {/* Auth Card */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-8 shadow-2xl backdrop-blur-xl">
          {error && (
            <div className="mb-6 flex items-center gap-3 rounded-lg border border-red-500/30 bg-red-500/10 p-3.5 text-sm text-red-400">
              <AlertCircle className="h-5 w-5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {successMsg && (
            <div className="mb-6 flex items-center gap-3 rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3.5 text-sm text-emerald-400">
              <CheckCircle2 className="h-5 w-5 flex-shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          {/* Google Sign-In Button */}
          <button
            type="button"
            onClick={handleGoogleSignIn}
            disabled={isGoogleLoading || isSubmitting}
            className="flex w-full items-center justify-center gap-3 rounded-xl border border-slate-700 bg-slate-800/80 py-3 text-sm font-semibold text-white shadow-md transition duration-200 hover:bg-slate-700/80 hover:border-slate-600 active:scale-[0.99] disabled:opacity-50"
          >
            {isGoogleLoading ? (
              <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-sky-400 border-t-transparent" />
            ) : (
              <svg className="h-5 w-5" viewBox="0 0 24 24">
                <path
                  fill="#EA4335"
                  d="M12 5c1.6 0 3 .6 4.1 1.7l3.1-3.1C17.3 1.8 14.8 1 12 1 7.5 1 3.7 3.6 1.9 7.3l3.7 2.9C6.5 7.3 9 5 12 5z"
                />
                <path
                  fill="#4285F4"
                  d="M23.5 12.3c0-.8-.1-1.6-.2-2.3H12v4.5h6.5c-.3 1.5-1.1 2.8-2.4 3.7l3.7 2.9c2.2-2 3.7-5 3.7-8.8z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.6 14.8c-.2-.7-.4-1.5-.4-2.3s.2-1.6.4-2.3L1.9 7.3C.7 9.7 0 12.3 0 15.1s.7 5.4 1.9 7.8l3.7-2.9z"
                />
                <path
                  fill="#34A853"
                  d="M12 23.5c3.2 0 6-1.1 8-3l-3.7-2.9c-1.1.7-2.5 1.2-4.3 1.2-3 0-5.5-2.3-6.4-5.2L1.9 16.5C3.7 20.2 7.5 23.5 12 23.5z"
                />
              </svg>
            )}
            <span>{isGoogleLoading ? "Connecting to Google..." : "Continue with Google"}</span>
          </button>

          {/* Divider */}
          <div className="relative my-6 text-center">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-800" />
            </div>
            <span className="relative bg-slate-900 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Or sign in with email
            </span>
          </div>

          {/* Auth Mode Toggle Tabs */}
          <div className="mb-6 grid grid-cols-2 gap-1 rounded-xl bg-slate-800/60 p-1 border border-slate-700/50">
            <button
              type="button"
              onClick={() => {
                setAuthMode("password");
                setError(null);
                setSuccessMsg(null);
              }}
              className={`flex items-center justify-center gap-2 rounded-lg py-2 text-xs font-semibold transition ${
                authMode === "password"
                  ? "bg-sky-500 text-white shadow"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Lock className="h-3.5 w-3.5" /> Password
            </button>
            <button
              type="button"
              onClick={() => {
                setAuthMode("otp");
                setError(null);
                setSuccessMsg(null);
              }}
              className={`flex items-center justify-center gap-2 rounded-lg py-2 text-xs font-semibold transition ${
                authMode === "otp"
                  ? "bg-sky-500 text-white shadow"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <ShieldCheck className="h-3.5 w-3.5" /> Email OTP Code
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Email Field */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                Work Email
              </label>
              <div className="relative mt-2">
                <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-slate-400">
                  <Mail className="h-4 w-4" />
                </span>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  className="w-full rounded-lg border border-slate-700 bg-slate-800/80 py-2.5 pl-10 pr-4 text-sm text-white placeholder-slate-500 outline-none transition duration-200 focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
                />
              </div>
            </div>

            {/* Password Mode Fields */}
            {authMode === "password" && (
              <div>
                <div className="flex items-center justify-between">
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                    Password
                  </label>
                  <button
                    type="button"
                    onClick={() => {
                      setForgotEmail(email);
                      setForgotError(null);
                      setForgotSuccess(null);
                      setForgotStep("email");
                      setShowForgotModal(true);
                    }}
                    className="text-xs font-medium text-sky-400 hover:text-sky-300 transition-colors"
                  >
                    Forgot password?
                  </button>
                </div>
                <div className="relative mt-2">
                  <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-slate-400">
                    <Lock className="h-4 w-4" />
                  </span>
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full rounded-lg border border-slate-700 bg-slate-800/80 py-2.5 pl-10 pr-10 text-sm text-white placeholder-slate-500 outline-none transition duration-200 focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 flex items-center pr-3 text-slate-400 hover:text-slate-200"
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
            )}

            {/* OTP Mode Fields */}
            {authMode === "otp" && (
              <div>
                <div className="flex items-center justify-between">
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                    6-Digit Verification Code
                  </label>
                  <button
                    type="button"
                    onClick={handleSendLoginOtp}
                    disabled={isSendingOtp || resendCountdown > 0 || !email.trim()}
                    className="text-xs font-medium text-sky-400 hover:text-sky-300 disabled:opacity-50 transition-colors"
                  >
                    {isSendingOtp
                      ? "Sending..."
                      : resendCountdown > 0
                      ? `Resend in ${resendCountdown}s`
                      : otpSent
                      ? "Resend Code"
                      : "Send Code"}
                  </button>
                </div>
                <div className="relative mt-2">
                  <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-slate-400">
                    <KeyRound className="h-4 w-4" />
                  </span>
                  <input
                    type="text"
                    required
                    maxLength={6}
                    value={otpCode}
                    onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ""))}
                    placeholder="123456"
                    className="w-full rounded-lg border border-slate-700 bg-slate-800/80 py-2.5 pl-10 pr-4 text-sm tracking-widest font-mono text-white placeholder-slate-500 outline-none transition duration-200 focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
                  />
                </div>
                <p className="mt-1.5 text-[11px] text-slate-400">
                  Click &quot;Send Code&quot; to receive a 6-digit OTP via email.
                </p>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="mt-6 flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-sky-500 to-indigo-600 py-3 text-sm font-semibold text-white shadow-lg shadow-sky-500/25 transition duration-200 hover:from-sky-400 hover:to-indigo-500 active:scale-[0.99] disabled:opacity-50"
            >
              {isSubmitting ? (
                <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              ) : (
                <>
                  {authMode === "password" ? "Sign In to Dashboard" : "Verify & Sign In"}
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>
        </div>

        {/* Footer Link */}
        <p className="text-center text-sm text-slate-400">
          Don&apos;t have an account yet?{" "}
          <Link
            href="/register"
            className="font-semibold text-sky-400 hover:text-sky-300 underline underline-offset-4"
          >
            Create account
          </Link>
        </p>
      </div>

      {/* Forgot Password Modal */}
      {showForgotModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <KeyRound className="h-5 w-5 text-sky-400" /> Reset Password
              </h3>
              <button
                type="button"
                onClick={() => setShowForgotModal(false)}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            {forgotError && (
              <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-400 flex items-center gap-2">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                <span>{forgotError}</span>
              </div>
            )}

            {forgotSuccess && (
              <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-emerald-400 flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 flex-shrink-0" />
                <span>{forgotSuccess}</span>
              </div>
            )}

            {forgotStep === "email" ? (
              <div className="space-y-4">
                <p className="text-xs text-slate-400">
                  Enter your email address and we will send you a 6-digit verification code to reset your password.
                </p>
                <div>
                  <label className="block text-xs font-semibold text-slate-300">Work Email</label>
                  <input
                    type="email"
                    required
                    value={forgotEmail}
                    onChange={(e) => setForgotEmail(e.target.value)}
                    placeholder="name@company.com"
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-800 py-2 px-3 text-sm text-white outline-none focus:border-sky-500"
                  />
                </div>
                <button
                  type="button"
                  onClick={handleForgotSendCode}
                  disabled={forgotLoading || !forgotEmail.trim()}
                  className="w-full rounded-lg bg-sky-500 py-2.5 text-sm font-semibold text-white shadow hover:bg-sky-400 disabled:opacity-50"
                >
                  {forgotLoading ? "Sending Code..." : "Send Reset Code"}
                </button>
              </div>
            ) : (
              <form onSubmit={handleResetPassword} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300">6-Digit Code</label>
                  <input
                    type="text"
                    required
                    maxLength={6}
                    value={forgotOtp}
                    onChange={(e) => setForgotOtp(e.target.value.replace(/\D/g, ""))}
                    placeholder="123456"
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-800 py-2 px-3 text-sm font-mono tracking-widest text-white outline-none focus:border-sky-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300">New Password</label>
                  <input
                    type="password"
                    required
                    value={forgotNewPassword}
                    onChange={(e) => setForgotNewPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-800 py-2 px-3 text-sm text-white outline-none focus:border-sky-500"
                  />
                  <span className="text-[11px] text-slate-500">Must be at least 8 characters.</span>
                </div>
                <button
                  type="submit"
                  disabled={forgotLoading}
                  className="w-full rounded-lg bg-sky-500 py-2.5 text-sm font-semibold text-white shadow hover:bg-sky-400 disabled:opacity-50"
                >
                  {forgotLoading ? "Resetting..." : "Save New Password"}
                </button>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
