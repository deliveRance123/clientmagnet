"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import {
  getUserBusinessProfile,
  updateUserBusinessProfile,
} from "@/lib/api";
import { UserBusinessProfile } from "@/types";
import {
  User,
  Building,
  Mail,
  CheckCircle2,
  AlertCircle,
  Shield,
  Key,
  Share2,
  Sparkles,
  Bell,
  Globe,
  Link2,
  Loader2,
  Check,
  Smartphone,
  Layers,
} from "lucide-react";

export default function SettingsPage() {
  const { user, token, updateProfile } = useAuth();

  const [activeTab, setActiveTab] = useState<"profile" | "business" | "ai" | "notifications" | "connections">("profile");

  // State
  const [profile, setProfile] = useState<UserBusinessProfile>({
    full_name: "",
    company_name: "",
    business_description: "",
    business_website: "",
    portfolio_links_json: "",
    preferred_tone: "Professional & Consultative",
    default_signature: "",
    business_intro: "",
    preferred_cta: "Would you be open to a 10-minute discovery chat this week?",
    notify_new_lead: true,
    notify_new_reply: true,
    notify_follow_up_due: true,
    notify_post_failed: true,
    notify_account_warning: true,
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    async function loadProfile() {
      if (!token) return;
      try {
        setLoading(true);
        const data = await getUserBusinessProfile(token);
        setProfile(data);
      } catch (err: any) {
        // Fallback to local user
        if (user) {
          setProfile((prev) => ({
            ...prev,
            full_name: user.full_name || "",
            company_name: user.company_name || "",
          }));
        }
      } finally {
        setLoading(false);
      }
    }
    loadProfile();
  }, [token, user]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;

    setSaving(true);
    setSuccessMessage(null);
    setErrorMessage(null);

    try {
      const updated = await updateUserBusinessProfile(token, profile);
      setProfile(updated);
      await updateProfile({
        full_name: updated.full_name || "",
        company_name: updated.company_name || "",
      });
      setSuccessMessage("Settings updated successfully!");
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to update settings.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Account & Platform Settings</h1>
        <p className="text-xs text-slate-500 mt-1">
          Manage your personal profile, business context, AI drafting preferences, notifications, and integration channels.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 gap-2 overflow-x-auto">
        <button
          onClick={() => setActiveTab("profile")}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold border-b-2 whitespace-nowrap transition ${
            activeTab === "profile"
              ? "border-indigo-600 text-indigo-600"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <User className="h-4 w-4" /> Personal Profile
        </button>

        <button
          onClick={() => setActiveTab("business")}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold border-b-2 whitespace-nowrap transition ${
            activeTab === "business"
              ? "border-indigo-600 text-indigo-600"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <Building className="h-4 w-4" /> Business Profile
        </button>

        <button
          onClick={() => setActiveTab("ai")}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold border-b-2 whitespace-nowrap transition ${
            activeTab === "ai"
              ? "border-indigo-600 text-indigo-600"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <Sparkles className="h-4 w-4" /> AI & Outreach Preferences
        </button>

        <button
          onClick={() => setActiveTab("notifications")}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold border-b-2 whitespace-nowrap transition ${
            activeTab === "notifications"
              ? "border-indigo-600 text-indigo-600"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <Bell className="h-4 w-4" /> Notifications
        </button>

        <button
          onClick={() => setActiveTab("connections")}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold border-b-2 whitespace-nowrap transition ${
            activeTab === "connections"
              ? "border-indigo-600 text-indigo-600"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <Share2 className="h-4 w-4" /> Connected Accounts
        </button>
      </div>

      {/* Notifications */}
      {successMessage && (
        <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-xs font-semibold text-emerald-800 animate-in fade-in">
          <CheckCircle2 className="h-4 w-4 text-emerald-600 flex-shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      {errorMessage && (
        <div className="flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs font-semibold text-rose-800 animate-in fade-in">
          <AlertCircle className="h-4 w-4 text-rose-600 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Tab 1: Personal Profile */}
      {activeTab === "profile" && (
        <form onSubmit={handleSave} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
          <h3 className="font-bold text-slate-900 text-sm border-b border-slate-100 pb-3">Personal Account Information</h3>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Full Name</label>
              <input
                type="text"
                value={profile.full_name || ""}
                onChange={(e) => setProfile({ ...profile, full_name: e.target.value })}
                placeholder="John Doe"
                className="w-full rounded-xl border border-slate-200 p-2.5 text-xs outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Registered Email (Tenant Identifier)</label>
              <input
                type="email"
                disabled
                value={user?.email || ""}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 p-2.5 text-xs text-slate-400 cursor-not-allowed"
              />
            </div>
          </div>

          <div className="pt-2 flex justify-end">
            <button
              type="submit"
              disabled={saving}
              className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-5 py-2 text-xs font-bold text-white hover:bg-indigo-700 shadow-sm"
            >
              {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Check className="h-3.5 w-3.5" />}
              Save Profile
            </button>
          </div>
        </form>
      )}

      {/* Tab 2: Business Profile */}
      {activeTab === "business" && (
        <form onSubmit={handleSave} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
          <h3 className="font-bold text-slate-900 text-sm border-b border-slate-100 pb-3">Agency & Business Information</h3>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Agency / Company Name</label>
              <input
                type="text"
                value={profile.company_name || ""}
                onChange={(e) => setProfile({ ...profile, company_name: e.target.value })}
                placeholder="Magnet Digital Solutions"
                className="w-full rounded-xl border border-slate-200 p-2.5 text-xs outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Website URL</label>
              <input
                type="url"
                value={profile.business_website || ""}
                onChange={(e) => setProfile({ ...profile, business_website: e.target.value })}
                placeholder="https://example.com"
                className="w-full rounded-xl border border-slate-200 p-2.5 text-xs outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-bold text-slate-700 block mb-1">Business Description & Value Proposition</label>
            <textarea
              rows={3}
              value={profile.business_description || ""}
              onChange={(e) => setProfile({ ...profile, business_description: e.target.value })}
              placeholder="We help online businesses scale with high-converting web design, custom graphics, and workflow automations."
              className="w-full rounded-xl border border-slate-200 p-2.5 text-xs outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="text-xs font-bold text-slate-700 block mb-1">Portfolio & Case Study Links (JSON or comma-separated)</label>
            <input
              type="text"
              value={profile.portfolio_links_json || ""}
              onChange={(e) => setProfile({ ...profile, portfolio_links_json: e.target.value })}
              placeholder="https://dribbble.com/myagency, https://github.com/myagency"
              className="w-full rounded-xl border border-slate-200 p-2.5 text-xs outline-none focus:border-indigo-500"
            />
          </div>

          <div className="pt-2 flex justify-end">
            <button
              type="submit"
              disabled={saving}
              className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-5 py-2 text-xs font-bold text-white hover:bg-indigo-700 shadow-sm"
            >
              {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Check className="h-3.5 w-3.5" />}
              Save Business Details
            </button>
          </div>
        </form>
      )}

      {/* Tab 3: AI & Communication Preferences */}
      {activeTab === "ai" && (
        <form onSubmit={handleSave} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
          <h3 className="font-bold text-slate-900 text-sm border-b border-slate-100 pb-3">AI Intelligence & Tone Settings</h3>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Preferred Communication Tone</label>
              <select
                value={profile.preferred_tone || "Professional & Consultative"}
                onChange={(e) => setProfile({ ...profile, preferred_tone: e.target.value })}
                className="w-full rounded-xl border border-slate-200 p-2.5 text-xs font-semibold outline-none focus:border-indigo-500"
              >
                <option value="Professional & Consultative">Professional & Consultative</option>
                <option value="Casual & Friendly">Casual & Friendly</option>
                <option value="Direct & Outcome-Oriented">Direct & Outcome-Oriented</option>
                <option value="Creative & Enthusiastic">Creative & Enthusiastic</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Preferred Call-To-Action (CTA)</label>
              <input
                type="text"
                value={profile.preferred_cta || ""}
                onChange={(e) => setProfile({ ...profile, preferred_cta: e.target.value })}
                placeholder="Would you be open to a 10-minute discovery chat this week?"
                className="w-full rounded-xl border border-slate-200 p-2.5 text-xs outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-bold text-slate-700 block mb-1">Standard Business Intro Sentence</label>
            <input
              type="text"
              value={profile.business_intro || ""}
              onChange={(e) => setProfile({ ...profile, business_intro: e.target.value })}
              placeholder="I help growing brands automate their outreach and upgrade their web presence."
              className="w-full rounded-xl border border-slate-200 p-2.5 text-xs outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="text-xs font-bold text-slate-700 block mb-1">Default Email / Message Signature</label>
            <textarea
              rows={3}
              value={profile.default_signature || ""}
              onChange={(e) => setProfile({ ...profile, default_signature: e.target.value })}
              placeholder="Best regards,&#10;John Doe&#10;Founder | Magnet Digital"
              className="w-full rounded-xl border border-slate-200 p-2.5 text-xs outline-none focus:border-indigo-500"
            />
          </div>

          <div className="pt-2 flex justify-end">
            <button
              type="submit"
              disabled={saving}
              className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-5 py-2 text-xs font-bold text-white hover:bg-indigo-700 shadow-sm"
            >
              {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Check className="h-3.5 w-3.5" />}
              Save AI Preferences
            </button>
          </div>
        </form>
      )}

      {/* Tab 4: Notification Toggles */}
      {activeTab === "notifications" && (
        <form onSubmit={handleSave} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
          <h3 className="font-bold text-slate-900 text-sm border-b border-slate-100 pb-3">Notification Preferences</h3>

          <div className="space-y-3 divide-y divide-slate-100">
            <div className="pt-2 flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-slate-900 block">New Lead Discovered</span>
                <span className="text-[11px] text-slate-500">Receive in-app alerts when high-intent opportunities are discovered</span>
              </div>
              <input
                type="checkbox"
                checked={profile.notify_new_lead ?? true}
                onChange={(e) => setProfile({ ...profile, notify_new_lead: e.target.checked })}
                className="h-4 w-4 rounded text-indigo-600 accent-indigo-600"
              />
            </div>

            <div className="pt-3 flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-slate-900 block">Prospect Replies</span>
                <span className="text-[11px] text-slate-500">Notify immediately when an email or WhatsApp message is received</span>
              </div>
              <input
                type="checkbox"
                checked={profile.notify_new_reply ?? true}
                onChange={(e) => setProfile({ ...profile, notify_new_reply: e.target.checked })}
                className="h-4 w-4 rounded text-indigo-600 accent-indigo-600"
              />
            </div>

            <div className="pt-3 flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-slate-900 block">Follow-Up Reminders</span>
                <span className="text-[11px] text-slate-500">Alert when scheduled prospect follow-ups are due</span>
              </div>
              <input
                type="checkbox"
                checked={profile.notify_follow_up_due ?? true}
                onChange={(e) => setProfile({ ...profile, notify_follow_up_due: e.target.checked })}
                className="h-4 w-4 rounded text-indigo-600 accent-indigo-600"
              />
            </div>

            <div className="pt-3 flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-slate-900 block">Social Post Status</span>
                <span className="text-[11px] text-slate-500">Alert if a scheduled post fails to publish</span>
              </div>
              <input
                type="checkbox"
                checked={profile.notify_post_failed ?? true}
                onChange={(e) => setProfile({ ...profile, notify_post_failed: e.target.checked })}
                className="h-4 w-4 rounded text-indigo-600 accent-indigo-600"
              />
            </div>

            <div className="pt-3 flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-slate-900 block">Account Re-authentication Warnings</span>
                <span className="text-[11px] text-slate-500">Alert if an OAuth token expires or requires re-authorization</span>
              </div>
              <input
                type="checkbox"
                checked={profile.notify_account_warning ?? true}
                onChange={(e) => setProfile({ ...profile, notify_account_warning: e.target.checked })}
                className="h-4 w-4 rounded text-indigo-600 accent-indigo-600"
              />
            </div>
          </div>

          <div className="pt-3 flex justify-end">
            <button
              type="submit"
              disabled={saving}
              className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-5 py-2 text-xs font-bold text-white hover:bg-indigo-700 shadow-sm"
            >
              {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Check className="h-3.5 w-3.5" />}
              Save Notifications
            </button>
          </div>
        </form>
      )}

      {/* Tab 5: Connected Accounts Hub */}
      {activeTab === "connections" && (
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm flex flex-col justify-between space-y-4">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <Mail className="h-5 w-5 text-indigo-600" />
                <h4 className="font-bold text-sm text-slate-900">Google Gmail</h4>
              </div>
              <p className="text-xs text-slate-500">Connect Google OAuth to send approved outreach drafts and sync threads.</p>
            </div>
            <Link
              href="/email"
              className="inline-flex items-center justify-center rounded-xl bg-indigo-600 px-4 py-2 text-xs font-bold text-white hover:bg-indigo-700 shadow-xs"
            >
              Manage Gmail →
            </Link>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm flex flex-col justify-between space-y-4">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <Smartphone className="h-5 w-5 text-emerald-600" />
                <h4 className="font-bold text-sm text-slate-900">Meta WhatsApp</h4>
              </div>
              <p className="text-xs text-slate-500">Official Cloud API integration for direct messaging and webhook reception.</p>
            </div>
            <Link
              href="/whatsapp"
              className="inline-flex items-center justify-center rounded-xl bg-emerald-600 px-4 py-2 text-xs font-bold text-white hover:bg-emerald-700 shadow-xs"
            >
              Manage WhatsApp →
            </Link>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm flex flex-col justify-between space-y-4">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <Share2 className="h-5 w-5 text-sky-600" />
                <h4 className="font-bold text-sm text-slate-900">Social Accounts</h4>
              </div>
              <p className="text-xs text-slate-500">Authorize Meta, X (Twitter), LinkedIn, and TikTok channels.</p>
            </div>
            <Link
              href="/social"
              className="inline-flex items-center justify-center rounded-xl bg-sky-600 px-4 py-2 text-xs font-bold text-white hover:bg-sky-700 shadow-xs"
            >
              Manage Socials →
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
