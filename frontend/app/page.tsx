"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { getLeadStatsSummary, getLeads, getServices } from "@/lib/api";
import { Lead, LeadStatsSummary, Service } from "@/types";
import {
  Users,
  Layers,
  Sparkles,
  ArrowRight,
  TrendingUp,
  ShieldCheck,
  CheckCircle2,
  Plus,
  Briefcase,
  Share2,
  MessageSquare,
  Mail,
  FileText,
  Settings as SettingsIcon,
  UserCheck,
  Target,
  Trophy,
  Zap,
  Globe,
  Bot,
  Palette,
  Layout,
  Lock,
  Database,
  Search,
  Check,
  Star,
  Flame,
  BarChart3,
  Send,
  Smartphone,
  ChevronRight,
} from "lucide-react";

export default function HomePage() {
  const { user, token } = useAuth();

  // If user is authenticated, render the SaaS Dashboard
  if (user) {
    return <AuthenticatedDashboard token={token} user={user} />;
  }

  // If user is not authenticated, render the public Landing Page
  return <PublicLandingPage />;
}

/* ========================================================================== */
/* 1. PUBLIC MARKETING LANDING PAGE                                           */
/* ========================================================================== */
function PublicLandingPage() {
  // Interactive lead simulator state
  const [selectedDemoService, setSelectedDemoService] = useState<
    "web" | "graphics" | "bot"
  >("web");
  const [simulatedScore, setSimulatedScore] = useState(94);
  const [isSimulating, setIsSimulating] = useState(false);

  const demoScenarios = {
    web: {
      title: "Fintech Startup - Full SaaS Platform Redesign",
      source: "LINKEDIN POST",
      detectedNeed: "Next.js 14, Tailwind CSS, Stripe integration, & PostgreSQL portal",
      matchedService: "Website Design & Development",
      budget: "$5,000 - $8,000",
      score: 95,
      urgency: "HIGH",
    },
    graphics: {
      title: "E-Commerce Brand - Complete Visual Identity & 3D Assets",
      source: "REMOTE JOB BOARD",
      detectedNeed: "Brand guidelines, Figma UI kit, product packaging & social templates",
      matchedService: "Graphics & Brand Identity Design",
      budget: "$3,200 fixed",
      score: 89,
      urgency: "MEDIUM",
    },
    bot: {
      title: "Logistics Enterprise - Automated Customer Support & Lead Routing Bot",
      source: "INBOUND WHATSAPP / API",
      detectedNeed: "FastAPI, Meta WhatsApp Cloud API integration, CRM webhooks",
      matchedService: "Bot & Automation Development",
      budget: "$4,500 - $6,000",
      score: 98,
      urgency: "VERY HIGH",
    },
  };

  const currentDemo = demoScenarios[selectedDemoService];

  const triggerSimulate = (svcKey: "web" | "graphics" | "bot") => {
    setIsSimulating(true);
    setSelectedDemoService(svcKey);
    setTimeout(() => {
      setSimulatedScore(demoScenarios[svcKey].score);
      setIsSimulating(false);
    }, 300);
  };

  return (
    <div className="relative min-h-screen bg-slate-950 text-slate-100 overflow-x-hidden font-sans">
      {/* Dynamic Background Ambient Gradients */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[600px] bg-gradient-to-b from-sky-500/15 via-indigo-500/10 to-transparent blur-3xl pointer-events-none -z-10" />
      <div className="absolute top-1/3 -left-48 w-96 h-96 rounded-full bg-sky-600/10 blur-[120px] pointer-events-none -z-10" />
      <div className="absolute top-2/3 -right-48 w-96 h-96 rounded-full bg-indigo-600/10 blur-[120px] pointer-events-none -z-10" />

      {/* -------------------------------------------------------------------- */}
      {/* Navigation Header                                                    */}
      {/* -------------------------------------------------------------------- */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-slate-950/80 border-b border-slate-800/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="relative h-10 w-10">
              <img
                src="/favicon.svg"
                alt="Client Magnet"
                className="h-10 w-10 drop-shadow-[0_0_12px_rgba(56,189,248,0.5)] transition-transform group-hover:scale-105"
              />
            </div>
            <div>
              <span className="text-lg font-black tracking-tight text-white flex items-center gap-1.5">
                Client Magnet
                <span className="inline-flex items-center rounded-full bg-sky-500/20 px-2 py-0.5 text-[10px] font-bold text-sky-300 border border-sky-500/30">
                  v2.0
                </span>
              </span>
              <p className="text-[10px] text-slate-400 font-medium">Global Client Discovery & CRM</p>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-8 text-sm font-semibold text-slate-300">
            <a href="#features" className="hover:text-sky-400 transition-colors">
              Features
            </a>
            <a href="#simulator" className="hover:text-sky-400 transition-colors">
              Live Demo
            </a>
            <a href="#pipeline" className="hover:text-sky-400 transition-colors">
              CRM Pipeline
            </a>
            <a href="#services" className="hover:text-sky-400 transition-colors">
              Supported Services
            </a>
            <a href="#pricing" className="hover:text-sky-400 transition-colors">
              Pricing
            </a>
          </nav>

          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="px-4 py-2 text-sm font-bold text-slate-300 hover:text-white transition-colors"
            >
              Sign In
            </Link>
            <Link
              href="/register"
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 px-5 py-2.5 text-sm font-bold text-white shadow-lg shadow-sky-500/25 hover:from-sky-400 hover:to-blue-500 active:scale-95 transition"
            >
              Get Started Free <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </header>

      {/* -------------------------------------------------------------------- */}
      {/* Hero Section                                                         */}
      {/* -------------------------------------------------------------------- */}
      <section className="relative pt-16 pb-20 md:pt-24 md:pb-32 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <div className="inline-flex items-center gap-2 rounded-full bg-slate-900/90 border border-sky-500/30 px-4 py-1.5 text-xs font-bold text-sky-400 shadow-inner mb-6 backdrop-blur-md">
          <Zap className="h-3.5 w-3.5 text-sky-400 animate-pulse" />
          <span>The Intelligent Client Discovery & CRM Operating System</span>
        </div>

        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-white max-w-4xl mx-auto leading-tight">
          Turn Global Freelance Opportunities into{" "}
          <span className="bg-gradient-to-r from-sky-400 via-blue-400 to-indigo-400 bg-clip-text text-transparent">
            High-Paying Clients
          </span>{" "}
          Automatically.
        </h1>

        <p className="mt-6 text-base sm:text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed">
          Discover verified freelance opportunities tailored to your services, score client intent with Gemini AI, communicate across WhatsApp & Email, and close deals in a visual 9-stage CRM.
        </p>

        <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
          <Link
            href="/register"
            className="inline-flex items-center gap-2.5 rounded-2xl bg-gradient-to-r from-sky-500 via-blue-600 to-indigo-600 px-8 py-4 text-base font-bold text-white shadow-xl shadow-sky-500/20 hover:opacity-95 active:scale-95 transition"
          >
            <Sparkles className="h-5 w-5" />
            Start Acquiring Clients Free
          </Link>
          <a
            href="#simulator"
            className="inline-flex items-center gap-2 rounded-2xl bg-slate-900/90 border border-slate-800 px-7 py-4 text-base font-bold text-slate-300 hover:bg-slate-800 hover:text-white transition"
          >
            Explore Interactive Demo <ChevronRight className="h-4 w-4" />
          </a>
        </div>

        {/* Security & Architecture Badges */}
        <div className="mt-12 flex flex-wrap items-center justify-center gap-6 text-xs font-semibold text-slate-400">
          <span className="flex items-center gap-1.5">
            <ShieldCheck className="h-4 w-4 text-sky-400" />
            Argon2id + AES-256 Security
          </span>
          <span className="flex items-center gap-1.5">
            <Database className="h-4 w-4 text-indigo-400" />
            Pure PostgreSQL (Zero Secondary DB)
          </span>
          <span className="flex items-center gap-1.5">
            <Lock className="h-4 w-4 text-emerald-400" />
            100% Tenant Isolated
          </span>
          <span className="flex items-center gap-1.5">
            <Globe className="h-4 w-4 text-blue-400" />
            Official Platform APIs & OAuth
          </span>
        </div>
      </section>

      {/* -------------------------------------------------------------------- */}
      {/* Interactive Lead Discovery & AI Scoring Simulator                   */}
      {/* -------------------------------------------------------------------- */}
      <section id="simulator" className="py-16 bg-slate-900/50 border-y border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-12">
            <h2 className="text-xs font-black uppercase tracking-widest text-sky-400">
              Live Opportunity Scout Simulator
            </h2>
            <p className="mt-2 text-3xl font-black text-white">
              See How Client Magnet Automatically Matches & Scores Leads
            </p>
            <p className="mt-2 text-sm text-slate-400">
              Select one of your core service tracks below to simulate live discovery and Gemini AI intent analysis.
            </p>

            {/* Service Filter Tabs */}
            <div className="mt-6 flex flex-wrap justify-center gap-3">
              <button
                onClick={() => triggerSimulate("web")}
                className={`inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-bold transition ${
                  selectedDemoService === "web"
                    ? "bg-sky-500 text-white shadow-md shadow-sky-500/20"
                    : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                }`}
              >
                <Layout className="h-4 w-4" /> 1. Website Design
              </button>
              <button
                onClick={() => triggerSimulate("graphics")}
                className={`inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-bold transition ${
                  selectedDemoService === "graphics"
                    ? "bg-sky-500 text-white shadow-md shadow-sky-500/20"
                    : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                }`}
              >
                <Palette className="h-4 w-4" /> 2. Graphics Design
              </button>
              <button
                onClick={() => triggerSimulate("bot")}
                className={`inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-bold transition ${
                  selectedDemoService === "bot"
                    ? "bg-sky-500 text-white shadow-md shadow-sky-500/20"
                    : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                }`}
              >
                <Bot className="h-4 w-4" /> 3. Bot / Automation
              </button>
            </div>
          </div>

          {/* Simulated Lead Card Display */}
          <div className="max-w-4xl mx-auto rounded-3xl border border-slate-700 bg-slate-900 p-6 md:p-8 shadow-2xl shadow-sky-500/5">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
              <div>
                <div className="flex items-center gap-2">
                  <span className="rounded-md bg-sky-500/20 px-2.5 py-0.5 text-[11px] font-bold text-sky-300 border border-sky-500/30">
                    {currentDemo.source}
                  </span>
                  <span className="rounded-md bg-emerald-500/20 px-2.5 py-0.5 text-[11px] font-bold text-emerald-300 border border-emerald-500/30">
                    URGENCY: {currentDemo.urgency}
                  </span>
                </div>
                <h3 className="mt-2 text-xl font-bold text-white">{currentDemo.title}</h3>
              </div>

              {/* Score Meter */}
              <div className="flex items-center gap-4 bg-slate-950/80 rounded-2xl p-4 border border-slate-800">
                <div className="text-right">
                  <div className="text-xs font-bold text-slate-400">Gemini Intent Score</div>
                  <div className="text-2xl font-black text-sky-400">
                    {isSimulating ? "..." : `${simulatedScore}%`}
                  </div>
                </div>
                <div className="h-12 w-12 rounded-full border-4 border-sky-500 flex items-center justify-center bg-sky-500/10">
                  <Flame className="h-5 w-5 text-sky-400" />
                </div>
              </div>
            </div>

            <div className="mt-6 grid gap-4 md:grid-cols-2">
              <div className="space-y-3">
                <div>
                  <div className="text-xs font-bold text-slate-400">Detected Client Need:</div>
                  <div className="text-sm font-semibold text-slate-200 mt-0.5">
                    {currentDemo.detectedNeed}
                  </div>
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-400">Estimated Budget:</div>
                  <div className="text-sm font-bold text-emerald-400 mt-0.5">
                    {currentDemo.budget}
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <div>
                  <div className="text-xs font-bold text-slate-400">Matched Active Service:</div>
                  <div className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-500/20 px-3 py-1 text-xs font-bold text-indigo-300 border border-indigo-500/30 mt-0.5">
                    <CheckCircle2 className="h-3.5 w-3.5 text-indigo-400" />
                    {currentDemo.matchedService}
                  </div>
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-400">Recommended Next Step:</div>
                  <div className="text-xs text-slate-300 mt-0.5">
                    Generate AI consultative email draft and transition stage to <span className="font-bold text-sky-400">QUALIFIED</span>.
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-8 pt-6 border-t border-slate-800 flex flex-wrap items-center justify-between gap-4">
              <span className="text-xs text-slate-400">
                🔒 Duplicate checks and tenant isolation validated in PostgreSQL.
              </span>
              <Link
                href="/register"
                className="inline-flex items-center gap-2 rounded-xl bg-sky-500 px-5 py-2.5 text-xs font-bold text-white hover:bg-sky-400 active:scale-95 transition"
              >
                Claim This Pipeline Workflow <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* -------------------------------------------------------------------- */}
      {/* 5 Core Feature Pillars                                               */}
      {/* -------------------------------------------------------------------- */}
      <section id="features" className="py-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-xs font-black uppercase tracking-widest text-sky-400">
            Enterprise Architecture
          </h2>
          <p className="mt-2 text-3xl sm:text-4xl font-black text-white">
            Built for Serious Freelancers & Agencies
          </p>
          <p className="mt-3 text-sm text-slate-400">
            Everything you need to discover, qualify, outreach, and retain clients without external SaaS chaos.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {/* Feature 1 */}
          <div className="rounded-3xl border border-slate-800 bg-slate-900/60 p-8 hover:border-sky-500/50 transition duration-200 flex flex-col justify-between">
            <div>
              <div className="h-12 w-12 rounded-2xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400 mb-6">
                <Globe className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-bold text-white">Global Opportunity Discovery</h3>
              <p className="mt-2 text-sm text-slate-400 leading-relaxed">
                Connect multiple legitimate job boards, RSS feeds, and manual CSV imports with automatic deduplication and HTML stripping.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-800 text-xs font-bold text-sky-400 flex items-center gap-1">
              Normalized Schema <ArrowRight className="h-3 w-3" />
            </div>
          </div>

          {/* Feature 2 */}
          <div className="rounded-3xl border border-slate-800 bg-slate-900/60 p-8 hover:border-indigo-500/50 transition duration-200 flex flex-col justify-between">
            <div>
              <div className="h-12 w-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-6">
                <BarChart3 className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-bold text-white">9-Stage Visual CRM Pipeline</h3>
              <p className="mt-2 text-sm text-slate-400 leading-relaxed">
                Track deals from NEW through WON/LOST. Non-destructively convert closed deals into permanent Client retainers.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-800 text-xs font-bold text-indigo-400 flex items-center gap-1">
              Lead $\to$ Client Conversion <ArrowRight className="h-3 w-3" />
            </div>
          </div>

          {/* Feature 3 */}
          <div className="rounded-3xl border border-slate-800 bg-slate-900/60 p-8 hover:border-emerald-500/50 transition duration-200 flex flex-col justify-between">
            <div>
              <div className="h-12 w-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mb-6">
                <MessageSquare className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-bold text-white">Omnichannel Unified Inbox</h3>
              <p className="mt-2 text-sm text-slate-400 leading-relaxed">
                Centralize messaging across Gmail, Meta WhatsApp Cloud API, and social accounts with Gemini AI reply suggestions.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-800 text-xs font-bold text-emerald-400 flex items-center gap-1">
              Zero Bulk Spam Policy <ArrowRight className="h-3 w-3" />
            </div>
          </div>

          {/* Feature 4 */}
          <div className="rounded-3xl border border-slate-800 bg-slate-900/60 p-8 hover:border-purple-500/50 transition duration-200 flex flex-col justify-between">
            <div>
              <div className="h-12 w-12 rounded-2xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 mb-6">
                <Share2 className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-bold text-white">Social Studio & Scheduler</h3>
              <p className="mt-2 text-sm text-slate-400 leading-relaxed">
                Draft content, generate platform-specific captions and hashtags with AI, and schedule posts across X, LinkedIn, and Meta.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-800 text-xs font-bold text-purple-400 flex items-center gap-1">
              Official OAuth 2.0 <ArrowRight className="h-3 w-3" />
            </div>
          </div>

          {/* Feature 5 */}
          <div className="rounded-3xl border border-slate-800 bg-slate-900/60 p-8 hover:border-amber-500/50 transition duration-200 flex flex-col justify-between">
            <div>
              <div className="h-12 w-12 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 mb-6">
                <TrendingUp className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-bold text-white">PostgreSQL Business Analytics</h3>
              <p className="mt-2 text-sm text-slate-400 leading-relaxed">
                Real-time conversion funnels (Lead $\to$ Qualified $\to$ Replied $\to$ Won) and service ROI computed directly via pure SQL queries.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-800 text-xs font-bold text-amber-400 flex items-center gap-1">
              Zero External DB Dependency <ArrowRight className="h-3 w-3" />
            </div>
          </div>

          {/* Feature 6 */}
          <div className="rounded-3xl border border-slate-800 bg-slate-900/60 p-8 hover:border-rose-500/50 transition duration-200 flex flex-col justify-between">
            <div>
              <div className="h-12 w-12 rounded-2xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400 mb-6">
                <ShieldCheck className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-bold text-white">Military-Grade Security</h3>
              <p className="mt-2 text-sm text-slate-400 leading-relaxed">
                Argon2id password hashing, AES-256 Fernet credential encryption at rest, rate-limited auth, and tenant-isolated data queries.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-800 text-xs font-bold text-rose-400 flex items-center gap-1">
              Production Audited <ArrowRight className="h-3 w-3" />
            </div>
          </div>
        </div>
      </section>

      {/* -------------------------------------------------------------------- */}
      {/* Visual Pipeline Showcase                                             */}
      {/* -------------------------------------------------------------------- */}
      <section id="pipeline" className="py-20 bg-slate-900/40 border-t border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-14">
            <h2 className="text-xs font-black uppercase tracking-widest text-sky-400">
              Deal Flow Pipeline
            </h2>
            <p className="mt-2 text-3xl font-black text-white">
              The 9-Stage High-Conversion Funnel
            </p>
            <p className="mt-2 text-sm text-slate-400">
              Never lose track of a prospect. Move leads seamlessly from first discovery to closed client.
            </p>
          </div>

          <div className="grid grid-cols-3 sm:grid-cols-5 lg:grid-cols-9 gap-3">
            {[
              { stage: "NEW", desc: "Just discovered", color: "border-sky-500/40 bg-sky-500/10 text-sky-300" },
              { stage: "QUALIFIED", desc: "Budget & Fit", color: "border-blue-500/40 bg-blue-500/10 text-blue-300" },
              { stage: "CONTACTED", desc: "Outreach sent", color: "border-indigo-500/40 bg-indigo-500/10 text-indigo-300" },
              { stage: "REPLIED", desc: "In discussion", color: "border-purple-500/40 bg-purple-500/10 text-purple-300" },
              { stage: "INTERESTED", desc: "Positive intent", color: "border-emerald-500/40 bg-emerald-500/10 text-emerald-300" },
              { stage: "DISCOVERY", desc: "Call / Scope", color: "border-cyan-500/40 bg-cyan-500/10 text-cyan-300" },
              { stage: "PROPOSAL", desc: "Quote delivered", color: "border-amber-500/40 bg-amber-500/10 text-amber-300" },
              { stage: "NEGOTIATION", desc: "Contract final", color: "border-orange-500/40 bg-orange-500/10 text-orange-300" },
              { stage: "WON DEAL", desc: "Converted Client", color: "border-emerald-400 bg-emerald-500/20 text-emerald-300" },
            ].map((st, i) => (
              <div
                key={st.stage}
                className={`rounded-2xl border p-4 text-center ${st.color} flex flex-col justify-between`}
              >
                <div>
                  <div className="text-[10px] font-black text-slate-400 mb-1">0{i + 1}</div>
                  <div className="text-xs font-black tracking-tight">{st.stage}</div>
                </div>
                <div className="text-[10px] text-slate-400 mt-3 font-medium">{st.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* -------------------------------------------------------------------- */}
      {/* Transparent Pricing Plans                                            */}
      {/* -------------------------------------------------------------------- */}
      <section id="pricing" className="py-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-14">
          <h2 className="text-xs font-black uppercase tracking-widest text-sky-400">
            Simple Pricing
          </h2>
          <p className="mt-2 text-3xl font-black text-white">Start Free, Scale as You Win Deals</p>
          <p className="mt-2 text-sm text-slate-400">
            No credit card required. Upgrade anytime for higher discovery limits and automated scheduling.
          </p>
        </div>

        <div className="grid gap-8 lg:grid-cols-3 max-w-5xl mx-auto">
          {/* Starter Plan */}
          <div className="rounded-3xl border border-slate-800 bg-slate-900/60 p-8 flex flex-col justify-between">
            <div>
              <h3 className="text-lg font-bold text-white">Free Starter</h3>
              <p className="text-xs text-slate-400 mt-1">Perfect for solo freelancers getting started.</p>
              <div className="mt-6 flex items-baseline gap-1">
                <span className="text-4xl font-black text-white">$0</span>
                <span className="text-xs text-slate-400 font-semibold">/forever</span>
              </div>

              <ul className="mt-8 space-y-3 text-xs text-slate-300">
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-sky-400" /> Up to 50 active leads
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-sky-400" /> 3 configured services catalog
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-sky-400" /> 9-Stage Visual CRM Pipeline
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-sky-400" /> Manual & CSV lead import
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-sky-400" /> Basic PostgreSQL analytics
                </li>
              </ul>
            </div>

            <Link
              href="/register"
              className="mt-8 block w-full rounded-2xl bg-slate-800 py-3 text-center text-xs font-bold text-white hover:bg-slate-700 transition"
            >
              Get Started Free
            </Link>
          </div>

          {/* Growth Plan (Popular) */}
          <div className="relative rounded-3xl border-2 border-sky-500 bg-gradient-to-b from-slate-900 to-slate-950 p-8 flex flex-col justify-between shadow-2xl shadow-sky-500/10">
            <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 rounded-full bg-sky-500 px-4 py-1 text-[10px] font-black uppercase text-white tracking-wider">
              Most Popular
            </div>

            <div>
              <h3 className="text-lg font-bold text-white">Growth Agency</h3>
              <p className="text-xs text-slate-400 mt-1">For active freelancers & small agencies.</p>
              <div className="mt-6 flex items-baseline gap-1">
                <span className="text-4xl font-black text-white">$29</span>
                <span className="text-xs text-slate-400 font-semibold">/month</span>
              </div>

              <ul className="mt-8 space-y-3 text-xs text-slate-300">
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-sky-400" /> Unlimited active leads & clients
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-sky-400" /> Gemini AI intent scoring & analysis
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-sky-400" /> Unified Inbox (Gmail + WhatsApp)
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-sky-400" /> Social Studio & automated post scheduler
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-sky-400" /> Full conversion funnel analytics
                </li>
              </ul>
            </div>

            <Link
              href="/register"
              className="mt-8 block w-full rounded-2xl bg-gradient-to-r from-sky-500 to-blue-600 py-3 text-center text-xs font-bold text-white shadow-lg shadow-sky-500/25 hover:opacity-95 transition"
            >
              Start 14-Day Free Trial
            </Link>
          </div>

          {/* Enterprise Scale */}
          <div className="rounded-3xl border border-slate-800 bg-slate-900/60 p-8 flex flex-col justify-between">
            <div>
              <h3 className="text-lg font-bold text-white">Enterprise Scale</h3>
              <p className="text-xs text-slate-400 mt-1">High volume teams & customized workflows.</p>
              <div className="mt-6 flex items-baseline gap-1">
                <span className="text-4xl font-black text-white">$79</span>
                <span className="text-xs text-slate-400 font-semibold">/month</span>
              </div>

              <ul className="mt-8 space-y-3 text-xs text-slate-300">
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-sky-400" /> Multi-account team seats
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-sky-400" /> Priority background worker queue
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-sky-400" /> Custom RSS & webhook lead sources
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-sky-400" /> Dedicated database connection pooling
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-sky-400" /> 24/7 SLA & priority onboarding
                </li>
              </ul>
            </div>

            <Link
              href="/register"
              className="mt-8 block w-full rounded-2xl bg-slate-800 py-3 text-center text-xs font-bold text-white hover:bg-slate-700 transition"
            >
              Contact Sales
            </Link>
          </div>
        </div>
      </section>

      {/* -------------------------------------------------------------------- */}
      {/* Final Call to Action Banner                                          */}
      {/* -------------------------------------------------------------------- */}
      <section className="py-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-sky-600 via-blue-600 to-indigo-700 p-10 md:p-14 text-center shadow-2xl shadow-sky-500/20">
          <h2 className="text-3xl sm:text-4xl font-black text-white max-w-2xl mx-auto leading-tight">
            Ready to Magnetize High-Ticket Freelance Clients?
          </h2>
          <p className="mt-4 text-sm sm:text-base text-sky-100 max-w-xl mx-auto">
            Set up your services catalog in 2 minutes and start matching qualified prospects immediately.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-4">
            <Link
              href="/register"
              className="inline-flex items-center gap-2 rounded-2xl bg-white px-8 py-3.5 text-sm font-bold text-sky-700 shadow-xl hover:bg-sky-50 active:scale-95 transition"
            >
              Create Free Account <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/login"
              className="inline-flex items-center gap-2 rounded-2xl bg-sky-800/40 border border-white/20 px-6 py-3.5 text-sm font-bold text-white hover:bg-sky-800/60 transition"
            >
              Sign In to Existing Account
            </Link>
          </div>
        </div>
      </section>

      {/* -------------------------------------------------------------------- */}
      {/* Footer                                                               */}
      {/* -------------------------------------------------------------------- */}
      <footer className="border-t border-slate-900 bg-slate-950 py-12 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <img src="/favicon.svg" alt="Client Magnet" className="h-6 w-6" />
            <span className="font-bold text-slate-300">Client Magnet Platform</span>
            <span>&copy; {new Date().getFullYear()} All rights reserved.</span>
          </div>

          <div className="flex items-center gap-6">
            <Link href="/login" className="hover:text-slate-300 transition-colors">
              Login
            </Link>
            <Link href="/register" className="hover:text-slate-300 transition-colors">
              Register
            </Link>
            <a href="#features" className="hover:text-slate-300 transition-colors">
              Architecture
            </a>
            <a href="#pricing" className="hover:text-slate-300 transition-colors">
              Pricing
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}

/* ========================================================================== */
/* 2. AUTHENTICATED SaaS DASHBOARD                                            */
/* ========================================================================== */
function AuthenticatedDashboard({ token, user }: { token: string | null; user: any }) {
  const [stats, setStats] = useState<LeadStatsSummary>({
    total_leads: 0,
    new_leads: 0,
    qualified_leads: 0,
    interested_leads: 0,
    won_clients: 0,
  });
  const [recentLeads, setRecentLeads] = useState<Lead[]>([]);
  const [services, setServices] = useState<Service[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboardData() {
      if (!token) return;
      try {
        setLoading(true);
        const [statsData, leadsData, servicesData] = await Promise.all([
          getLeadStatsSummary(token),
          getLeads(token, { sort_by: "created_at", sort_dir: "desc" }),
          getServices(token),
        ]);
        setStats(statsData);
        setRecentLeads(leadsData.slice(0, 5));
        setServices(servicesData);
      } catch (err) {
        console.error("Error loading dashboard data:", err);
      } finally {
        setLoading(false);
      }
    }

    loadDashboardData();
  }, [token]);

  const displayName = user?.full_name || user?.email?.split("@")[0] || "User";

  const statCards = [
    {
      title: "Total Leads",
      value: stats.total_leads,
      icon: Users,
      color: "text-blue-600 bg-blue-50 border-blue-100",
      description: "All pipeline prospects",
    },
    {
      title: "New Leads",
      value: stats.new_leads,
      icon: Sparkles,
      color: "text-sky-600 bg-sky-50 border-sky-100",
      description: "Uncontacted inquiries",
    },
    {
      title: "Qualified Leads",
      value: stats.qualified_leads,
      icon: Target,
      color: "text-indigo-600 bg-indigo-50 border-indigo-100",
      description: "Fit & high intent verified",
    },
    {
      title: "Interested Leads",
      value: stats.interested_leads,
      icon: UserCheck,
      color: "text-emerald-600 bg-emerald-50 border-emerald-100",
      description: "In active conversation",
    },
    {
      title: "Won Clients",
      value: stats.won_clients,
      icon: Trophy,
      color: "text-amber-600 bg-amber-50 border-amber-100",
      description: "Converted & closed deals",
    },
  ];

  const moduleSections = [
    { title: "CRM Pipeline", count: "9-Stage Kanban", icon: BarChart3, href: "/crm", color: "text-sky-500 bg-sky-50" },
    { title: "Business Analytics", count: "Conversion Funnels", icon: TrendingUp, href: "/analytics", color: "text-blue-500 bg-blue-50" },
    { title: "Leads Discovery", count: `${stats.total_leads} prospects`, icon: Users, href: "/leads", color: "text-indigo-500 bg-indigo-50" },
    { title: "Clients Directory", count: `${stats.won_clients} won retainers`, icon: Briefcase, href: "/clients", color: "text-emerald-500 bg-emerald-50" },
    { title: "Unified Inbox", count: "Gmail + WhatsApp", icon: MessageSquare, href: "/messages", color: "text-purple-500 bg-purple-50" },
    { title: "Social Content Studio", count: "Drafts & Scheduler", icon: Share2, href: "/content", color: "text-pink-500 bg-pink-50" },
    { title: "Services Catalog", count: `${services.length} active offerings`, icon: Layers, href: "/services", color: "text-amber-500 bg-amber-50" },
    { title: "Platform Settings", count: "Profile & Keys", icon: SettingsIcon, href: "/settings", color: "text-slate-500 bg-slate-100" },
  ];

  return (
    <div className="space-y-8">
      {/* Dynamic Welcome Hero Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-sky-600 via-sky-500 to-indigo-600 p-8 text-white shadow-xl shadow-sky-500/10">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full bg-white/15 px-3 py-1 text-xs font-semibold backdrop-blur-md">
              <ShieldCheck className="h-3.5 w-3.5 text-sky-200" />
              Isolated PostgreSQL Environment Active
            </div>
            <h1 className="mt-3 text-3xl md:text-4xl font-black tracking-tight">
              Welcome back, {displayName}!
            </h1>
            <p className="mt-2 text-sm text-sky-100 max-w-xl leading-relaxed">
              Your client acquisition command center is connected. Manage your services catalog, track deal stages, and close leads.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Link
              href="/crm"
              className="inline-flex items-center gap-2 rounded-2xl bg-white px-5 py-2.5 text-sm font-bold text-sky-700 shadow-md hover:bg-sky-50 active:scale-95 transition"
            >
              <BarChart3 className="h-4 w-4" />
              Open CRM Pipeline
            </Link>
            <Link
              href="/leads"
              className="inline-flex items-center gap-2 rounded-2xl bg-white/15 px-4 py-2.5 text-sm font-bold text-white backdrop-blur-md border border-white/20 hover:bg-white/25 active:scale-95 transition"
            >
              <Plus className="h-4 w-4" />
              Import Lead
            </Link>
          </div>
        </div>

        <div className="absolute -right-16 -top-16 h-72 w-72 rounded-full bg-white/10 blur-3xl pointer-events-none" />
      </div>

      {/* PostgreSQL Dashboard Summary Statistics */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-sky-600" />
            Live Pipeline Performance
          </h2>
          <span className="text-xs font-semibold text-slate-400">PostgreSQL Aggregated</span>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {statCards.map((card) => {
            const Icon = card.icon;
            return (
              <div
                key={card.title}
                className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:shadow-md"
              >
                <div className="flex items-center justify-between">
                  <span className={`rounded-xl p-2.5 border ${card.color}`}>
                    <Icon className="h-5 w-5" />
                  </span>
                  <span className="text-2xl font-black text-slate-900">
                    {loading ? "..." : card.value}
                  </span>
                </div>
                <h3 className="mt-4 text-xs font-bold text-slate-500 uppercase tracking-wider">
                  {card.title}
                </h3>
                <p className="text-[11px] text-slate-400 mt-0.5">{card.description}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recent Leads & Services Summary */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Recent Leads (2 cols) */}
        <div className="lg:col-span-2 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <div>
              <h3 className="font-bold text-slate-900">Recent Pipeline Inquiries</h3>
              <p className="text-xs text-slate-400 mt-0.5">Top latest leads in your pipeline</p>
            </div>
            <Link
              href="/crm"
              className="text-xs font-bold text-sky-600 hover:text-sky-700 flex items-center gap-1"
            >
              View Kanban <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          {loading ? (
            <div className="py-12 text-center text-sm text-slate-400">
              Loading recent leads...
            </div>
          ) : recentLeads.length === 0 ? (
            <div className="py-12 text-center">
              <p className="text-sm font-semibold text-slate-700">No leads recorded yet</p>
              <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                Discover or import leads to start matching high-intent prospects to your services.
              </p>
              <Link
                href="/leads"
                className="mt-4 inline-flex items-center gap-1.5 rounded-xl bg-sky-50 px-4 py-2 text-xs font-bold text-sky-700 hover:bg-sky-100 transition"
              >
                <Plus className="h-3.5 w-3.5" /> Add Lead
              </Link>
            </div>
          ) : (
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-600">
                <thead>
                  <tr className="border-b border-slate-100 text-xs font-bold uppercase text-slate-400">
                    <th className="py-2.5">Name</th>
                    <th className="py-2.5">Matched Service</th>
                    <th className="py-2.5">Intent Score</th>
                    <th className="py-2.5">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {recentLeads.map((lead) => (
                    <tr key={lead.id} className="hover:bg-slate-50/50 transition-colors">
                      <td className="py-3 font-semibold text-slate-900">
                        <Link href={`/leads/${lead.id}`} className="hover:text-sky-600 transition-colors">
                          {lead.name}
                        </Link>
                        {lead.company && <span className="block text-[11px] text-slate-400">{lead.company}</span>}
                      </td>
                      <td className="py-3 text-xs">
                        {lead.matched_service ? (
                          <span className="inline-flex items-center gap-1 rounded-md bg-sky-50 px-2 py-0.5 font-semibold text-sky-700">
                            {lead.matched_service.name}
                          </span>
                        ) : (
                          <span className="text-slate-400 italic">Unmatched</span>
                        )}
                      </td>
                      <td className="py-3">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-slate-700">{lead.intent_score}</span>
                          <div className="h-1.5 w-12 rounded-full bg-slate-100">
                            <div
                              className="h-full rounded-full bg-sky-500"
                              style={{ width: `${Math.min(100, Math.max(0, lead.intent_score))}%` }}
                            />
                          </div>
                        </div>
                      </td>
                      <td className="py-3">
                        <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-bold text-slate-700">
                          {lead.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Services Widget (1 col) */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <h3 className="font-bold text-slate-900">Active Services</h3>
              <Link
                href="/services"
                className="text-xs font-bold text-sky-600 hover:text-sky-700 flex items-center gap-1"
              >
                Manage <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>

            <div className="mt-4 space-y-3">
              {services.length === 0 ? (
                <p className="text-xs text-slate-400 italic py-4 text-center">No services created yet.</p>
              ) : (
                services.slice(0, 4).map((svc) => (
                  <div
                    key={svc.id}
                    className="flex items-center justify-between rounded-xl bg-slate-50 p-3 border border-slate-100"
                  >
                    <div>
                      <h4 className="text-xs font-bold text-slate-800">{svc.name}</h4>
                      {svc.pricing && <span className="text-[11px] text-emerald-600 font-medium">{svc.pricing}</span>}
                    </div>
                    <span
                      className={`h-2 w-2 rounded-full ${svc.is_active ? "bg-emerald-500" : "bg-slate-300"}`}
                      title={svc.is_active ? "Active" : "Inactive"}
                    />
                  </div>
                ))
              )}
            </div>
          </div>

          <Link
            href="/services"
            className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white py-2.5 text-xs font-bold text-slate-700 hover:bg-slate-50 transition"
          >
            <Plus className="h-3.5 w-3.5" /> Configure Services
          </Link>
        </div>
      </div>

      {/* Platform Navigation Grid */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-bold text-slate-900 tracking-tight">Platform Command Navigation</h2>
          <span className="text-xs text-slate-400">All Modules Enabled</span>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
          {moduleSections.map((mod) => {
            const Icon = mod.icon;
            return (
              <Link
                key={mod.title}
                href={mod.href}
                className="group rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition-all duration-200 hover:border-sky-300 hover:shadow-md"
              >
                <div className="flex items-center justify-between">
                  <span className={`rounded-xl p-2.5 ${mod.color}`}>
                    <Icon className="h-5 w-5" />
                  </span>
                  <ArrowRight className="h-4 w-4 text-slate-300 transition-transform duration-200 group-hover:translate-x-1 group-hover:text-sky-500" />
                </div>
                <h3 className="mt-4 font-bold text-slate-900 group-hover:text-sky-600 transition-colors">
                  {mod.title}
                </h3>
                <p className="mt-0.5 text-xs text-slate-400">{mod.count}</p>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
