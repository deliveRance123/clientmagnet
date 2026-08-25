"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import {
  Lock,
  Mail,
  User,
  Building,
  Eye,
  EyeOff,
  ArrowRight,
  AlertCircle,
  CheckCircle2,
  ArrowLeft,
  KeyRound,
  ShieldCheck,
} from "lucide-react";

export default function RegisterPage() {
  const [fullName, setFullName] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [otpCode, setOtpCode] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [isSendingOtp, setIsSendingOtp] = useState(false);
  const [otpSent, setOtpSent] = useState(false);
  const [resendCountdown, setResendCountdown] = useState(0);

  const { register, sendOTP, initiateGoogleLogin } = useAuth();
  const router = useRouter();

  // Resend cooldown timer
  React.useEffect(() => {
    let timer: NodeJS.Timeout;
    if (resendCountdown > 0) {
      timer = setTimeout(() => setResendCountdown(resendCountdown - 1), 1000);
    }
    return () => clearTimeout(timer);
  }, [resendCountdown]);

  const handleGoogleSignUp = async () => {
    setError(null);
    setIsGoogleLoading(true);
    try {
      await initiateGoogleLogin();
    } catch (err) {
      setError("Failed to initialize Google Sign-In. Please try again.");
      setIsGoogleLoading(false);
    }
  };

  const handleSendRegisterOtp = async () => {
    if (!email.trim()) {
      setError("Please enter your work email first.");
      return;
    }
    setError(null);
    setSuccessMsg(null);
    setIsSendingOtp(true);
    const res = await sendOTP(email.trim(), "registration");
    setIsSendingOtp(false);

    if (res.success) {
      setOtpSent(true);
      setResendCountdown(60);
      setSuccessMsg(res.message || "6-digit verification code sent to your email.");
    } else {
      setError(res.error || "Failed to send verification code.");
    }
  };

  // Password strength calculations
  const passwordChecks = useMemo(() => {
    return {
      length: password.length >= 8,
      upper: /[A-Z]/.test(password),
      lower: /[a-z]/.test(password),
      number: /[0-9]/.test(password),
    };
  }, [password]);

  const strengthScore = useMemo(() => {
    let score = 0;
    if (passwordChecks.length) score++;
    if (passwordChecks.upper) score++;
    if (passwordChecks.lower) score++;
    if (passwordChecks.number) score++;
    return score;
  }, [passwordChecks]);

  const strengthLabel = useMemo(() => {
    if (password.length === 0) return "";
    if (strengthScore <= 2) return "Weak";
    if (strengthScore === 3) return "Moderate";
    return "Strong";
  }, [strengthScore, password]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("Passwords do not match. Please verify.");
      return;
    }

    if (strengthScore < 4) {
      setError("Please ensure your password meets all complexity requirements (at least 8 chars, 1 uppercase, 1 lowercase, 1 number).");
      return;
    }

    setIsSubmitting(true);

    const res = await register({
      email: email.trim(),
      password,
      full_name: fullName.trim() || undefined,
      company_name: companyName.trim() || undefined,
      otp: otpCode.trim() || undefined,
    });

    setIsSubmitting(false);

    if (res.success) {
      router.push("/");
    } else {
      setError(res.error || "Registration failed. Please check your details.");
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-slate-950 px-4 py-12 sm:px-6 lg:px-8 overflow-hidden">
      {/* Dynamic Background Glows */}
      <div className="absolute -top-40 -right-40 h-96 w-96 rounded-full bg-sky-500/15 blur-3xl pointer-events-none" />
      <div className="absolute -bottom-40 -left-40 h-96 w-96 rounded-full bg-indigo-500/15 blur-3xl pointer-events-none" />

      <div className="relative w-full max-w-lg space-y-6">
        {/* Back to Landing Page */}
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
            Create Your Account
          </h2>
          <p className="mt-2 text-sm text-slate-400">
            Start acquiring high-intent clients with dedicated multi-user isolation
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

          {/* Google Sign-Up Button */}
          <button
            type="button"
            onClick={handleGoogleSignUp}
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
            <span>{isGoogleLoading ? "Connecting to Google..." : "Sign up with Google"}</span>
          </button>

          {/* Divider */}
          <div className="relative my-6 text-center">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-800" />
            </div>
            <span className="relative bg-slate-900 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Or register with email
            </span>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Name and Company Row */}
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                  Full Name
                </label>
                <div className="relative mt-1.5">
                  <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-slate-400">
                    <User className="h-4 w-4" />
                  </span>
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Jane Doe"
                    className="w-full rounded-lg border border-slate-700 bg-slate-800/80 py-2.5 pl-10 pr-3 text-sm text-white placeholder-slate-500 outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                  Company Name <span className="text-slate-500 font-normal">(Opt)</span>
                </label>
                <div className="relative mt-1.5">
                  <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-slate-400">
                    <Building className="h-4 w-4" />
                  </span>
                  <input
                    type="text"
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    placeholder="Acme Growth"
                    className="w-full rounded-lg border border-slate-700 bg-slate-800/80 py-2.5 pl-10 pr-3 text-sm text-white placeholder-slate-500 outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
                  />
                </div>
              </div>
            </div>

            {/* Email Field */}
            <div>
              <div className="flex items-center justify-between">
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                  Work Email
                </label>
                <button
                  type="button"
                  onClick={handleSendRegisterOtp}
                  disabled={isSendingOtp || resendCountdown > 0 || !email.trim()}
                  className="text-xs font-medium text-sky-400 hover:text-sky-300 disabled:opacity-50 transition-colors"
                >
                  {isSendingOtp
                    ? "Sending OTP..."
                    : resendCountdown > 0
                    ? `Resend in ${resendCountdown}s`
                    : otpSent
                    ? "Resend Code"
                    : "Send Email OTP Code"}
                </button>
              </div>
              <div className="relative mt-1.5">
                <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-slate-400">
                  <Mail className="h-4 w-4" />
                </span>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="jane@company.com"
                  className="w-full rounded-lg border border-slate-700 bg-slate-800/80 py-2.5 pl-10 pr-4 text-sm text-white placeholder-slate-500 outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
                />
              </div>
            </div>

            {/* OTP Field (Shown if OTP was requested or user wants to verify) */}
            {otpSent && (
              <div className="rounded-xl border border-sky-500/30 bg-sky-500/5 p-3.5 space-y-1.5 animate-fadeIn">
                <div className="flex items-center justify-between">
                  <label className="block text-xs font-semibold text-sky-400 flex items-center gap-1.5">
                    <KeyRound className="h-3.5 w-3.5" /> 6-Digit Email Verification Code
                  </label>
                  <span className="text-[11px] text-slate-400">Expires in 10 mins</span>
                </div>
                <input
                  type="text"
                  maxLength={6}
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ""))}
                  placeholder="123456"
                  className="w-full rounded-lg border border-sky-500/50 bg-slate-800 py-2 pl-3 pr-3 text-sm font-mono tracking-widest text-white outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-400"
                />
                <p className="text-[11px] text-slate-400">
                  Check your inbox for the code sent from {email || "your email"}.
                </p>
              </div>
            )}

            {/* Password & Confirm Row */}
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                  Password
                </label>
                <div className="relative mt-1.5">
                  <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-slate-400">
                    <Lock className="h-4 w-4" />
                  </span>
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full rounded-lg border border-slate-700 bg-slate-800/80 py-2.5 pl-10 pr-9 text-sm text-white placeholder-slate-500 outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 flex items-center pr-3 text-slate-400 hover:text-slate-200"
                  >
                    {showPassword ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                  Confirm Password
                </label>
                <div className="relative mt-1.5">
                  <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-slate-400">
                    <Lock className="h-4 w-4" />
                  </span>
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full rounded-lg border border-slate-700 bg-slate-800/80 py-2.5 pl-10 pr-4 text-sm text-white placeholder-slate-500 outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
                  />
                </div>
              </div>
            </div>

            {/* Password Strength Meter */}
            {password.length > 0 && (
              <div className="rounded-lg bg-slate-800/50 p-3 border border-slate-700/50 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400">Password Strength:</span>
                  <span
                    className={`font-semibold ${
                      strengthScore <= 2
                        ? "text-red-400"
                        : strengthScore === 3
                        ? "text-amber-400"
                        : "text-emerald-400"
                    }`}
                  >
                    {strengthLabel}
                  </span>
                </div>
                <div className="grid grid-cols-4 gap-1.5">
                  {[1, 2, 3, 4].map((step) => (
                    <div
                      key={step}
                      className={`h-1.5 rounded-full transition-all duration-300 ${
                        step <= strengthScore
                          ? strengthScore <= 2
                            ? "bg-red-500"
                            : strengthScore === 3
                            ? "bg-amber-500"
                            : "bg-emerald-500"
                          : "bg-slate-700"
                      }`}
                    />
                  ))}
                </div>
                <div className="grid grid-cols-2 gap-1 pt-1 text-[11px] text-slate-400">
                  <div className={`flex items-center gap-1 ${passwordChecks.length ? "text-emerald-400" : ""}`}>
                    <CheckCircle2 className="h-3 w-3" /> At least 8 characters
                  </div>
                  <div className={`flex items-center gap-1 ${passwordChecks.upper ? "text-emerald-400" : ""}`}>
                    <CheckCircle2 className="h-3 w-3" /> Uppercase letter
                  </div>
                  <div className={`flex items-center gap-1 ${passwordChecks.lower ? "text-emerald-400" : ""}`}>
                    <CheckCircle2 className="h-3 w-3" /> Lowercase letter
                  </div>
                  <div className={`flex items-center gap-1 ${passwordChecks.number ? "text-emerald-400" : ""}`}>
                    <CheckCircle2 className="h-3 w-3" /> Number included
                  </div>
                </div>
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
                  Complete Registration
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>
        </div>

        {/* Footer Link */}
        <p className="text-center text-sm text-slate-400">
          Already registered?{" "}
          <Link
            href="/login"
            className="font-semibold text-sky-400 hover:text-sky-300 underline underline-offset-4"
          >
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
