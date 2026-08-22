"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import {
  createFollowUp,
  getFollowUps,
  getLeads,
  recommendFollowUps,
  updateFollowUp,
} from "@/lib/api";
import {
  FollowUpItem,
  Lead,
} from "@/types";
import {
  Clock,
  Sparkles,
  Calendar,
  CheckCircle2,
  AlertCircle,
  Plus,
  Loader2,
  Search,
  Check,
  XCircle,
  ArrowRight,
  User,
  Mail,
  Phone,
  RefreshCw,
  Edit3,
} from "lucide-react";

export default function FollowUpsPage() {
  const { token } = useAuth();

  // State
  const [activeTab, setActiveTab] = useState<"due_today" | "upcoming" | "overdue" | "all" | "completed">("due_today");
  const [followUps, setFollowUps] = useState<FollowUpItem[]>([]);
  const [leads, setLeads] = useState<Lead[]>([]);

  const [loading, setLoading] = useState(true);
  const [actionBusy, setActionBusy] = useState(false);
  const [scanningAI, setScanningAI] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Create Follow-up Modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedLeadId, setSelectedLeadId] = useState("");
  const [channel, setChannel] = useState("email");
  const [scheduledTime, setScheduledTime] = useState("");
  const [notes, setNotes] = useState("");
  const [messageDraft, setMessageDraft] = useState("");

  // Load Data
  const loadData = async () => {
    if (!token) return;
    try {
      setLoading(true);
      setErrorMsg(null);

      const [followUpsData, leadsData] = await Promise.all([
        getFollowUps(token, {
          due: activeTab === "all" || activeTab === "completed" ? undefined : activeTab,
          status: activeTab === "completed" ? "Sent" : undefined,
        }).catch(() => []),
        getLeads(token).catch(() => []),
      ]);

      setFollowUps(followUpsData);
      setLeads(leadsData);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load follow-ups.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [token, activeTab]);

  // AI Recommendation Scan
  const handleScanRecommendations = async () => {
    if (!token) return;
    try {
      setScanningAI(true);
      setErrorMsg(null);
      const res = await recommendFollowUps(token);
      setSuccessMsg(res.message);
      await loadData();
    } catch (err: any) {
      setErrorMsg(err.message || "Recommendation scan failed.");
    } finally {
      setScanningAI(false);
    }
  };

  // Create Follow-Up
  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !selectedLeadId || !scheduledTime) return;

    try {
      setActionBusy(true);
      setErrorMsg(null);
      await createFollowUp(token, {
        lead_id: selectedLeadId,
        channel,
        scheduled_time: new Date(scheduledTime).toISOString(),
        notes: notes.trim() || undefined,
        message_draft: messageDraft.trim() || undefined,
      });

      setSuccessMsg("Follow-up scheduled successfully!");
      setShowCreateModal(false);
      setSelectedLeadId("");
      setNotes("");
      setMessageDraft("");
      await loadData();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to schedule follow-up.");
    } finally {
      setActionBusy(false);
    }
  };

  // Mark Completed / Sent
  const handleMarkSent = async (id: string) => {
    if (!token) return;
    try {
      setActionBusy(true);
      await updateFollowUp(token, id, { status: "Sent" });
      setSuccessMsg("Follow-up marked as sent.");
      await loadData();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to update status.");
    } finally {
      setActionBusy(false);
    }
  };

  // Cancel Follow-Up
  const handleCancel = async (id: string) => {
    if (!token) return;
    if (!confirm("Cancel this follow-up?")) return;
    try {
      setActionBusy(true);
      await updateFollowUp(token, id, { status: "Cancelled" });
      setSuccessMsg("Follow-up cancelled.");
      await loadData();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to cancel follow-up.");
    } finally {
      setActionBusy(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <Clock className="h-7 w-7 text-indigo-600" />
            Follow-Up Management Hub
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Track, schedule, and execute timely prospect follow-ups with Gemini AI recommendations.
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={handleScanRecommendations}
            disabled={scanningAI}
            className="inline-flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-indigo-600 to-sky-600 px-4 py-2 text-xs font-bold text-white shadow-sm hover:from-indigo-500 hover:to-sky-500 disabled:opacity-50 transition"
          >
            {scanningAI ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Sparkles className="h-3.5 w-3.5" />}
            Scan & Recommend Follow-Ups
          </button>

          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-1.5 rounded-xl bg-slate-900 px-4 py-2 text-xs font-bold text-white hover:bg-slate-800 shadow-sm"
          >
            <Plus className="h-4 w-4" />
            Schedule Follow-Up
          </button>
        </div>
      </div>

      {/* Notifications */}
      {successMsg && (
        <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-xs font-semibold text-emerald-800 animate-in fade-in">
          <CheckCircle2 className="h-4 w-4 text-emerald-600 flex-shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {errorMsg && (
        <div className="flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs font-semibold text-rose-800 animate-in fade-in">
          <AlertCircle className="h-4 w-4 text-rose-600 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Tabs */}
      <div className="flex items-center gap-1 rounded-xl bg-slate-100 p-1 w-fit">
        <button
          onClick={() => setActiveTab("due_today")}
          className={`rounded-lg px-3.5 py-1.5 text-xs font-bold transition ${
            activeTab === "due_today" ? "bg-white text-indigo-700 shadow-xs" : "text-slate-600 hover:text-slate-900"
          }`}
        >
          Due Today
        </button>
        <button
          onClick={() => setActiveTab("upcoming")}
          className={`rounded-lg px-3.5 py-1.5 text-xs font-bold transition ${
            activeTab === "upcoming" ? "bg-white text-indigo-700 shadow-xs" : "text-slate-600 hover:text-slate-900"
          }`}
        >
          Upcoming
        </button>
        <button
          onClick={() => setActiveTab("overdue")}
          className={`rounded-lg px-3.5 py-1.5 text-xs font-bold transition ${
            activeTab === "overdue" ? "bg-white text-indigo-700 shadow-xs" : "text-slate-600 hover:text-slate-900"
          }`}
        >
          Overdue
        </button>
        <button
          onClick={() => setActiveTab("all")}
          className={`rounded-lg px-3.5 py-1.5 text-xs font-bold transition ${
            activeTab === "all" ? "bg-white text-indigo-700 shadow-xs" : "text-slate-600 hover:text-slate-900"
          }`}
        >
          All Active
        </button>
        <button
          onClick={() => setActiveTab("completed")}
          className={`rounded-lg px-3.5 py-1.5 text-xs font-bold transition ${
            activeTab === "completed" ? "bg-white text-indigo-700 shadow-xs" : "text-slate-600 hover:text-slate-900"
          }`}
        >
          Completed
        </button>
      </div>

      {/* Follow-Ups List */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
        {loading ? (
          <div className="text-center py-12 text-xs text-slate-400">
            <Loader2 className="h-5 w-5 animate-spin mx-auto mb-2 text-indigo-500" />
            Loading follow-up tasks...
          </div>
        ) : followUps.length === 0 ? (
          <div className="text-center py-12 text-xs text-slate-400">
            <Calendar className="h-8 w-8 mx-auto mb-2 text-slate-300" />
            No follow-ups found in this view.
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {followUps.map((fu) => (
              <div key={fu.id} className="py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="rounded bg-indigo-50 px-2 py-0.5 text-[10px] font-bold uppercase text-indigo-700">
                      {fu.channel}
                    </span>
                    <h4 className="font-bold text-xs text-slate-900">
                      {fu.lead_name || "Lead"} {fu.lead_company ? `(${fu.lead_company})` : ""}
                    </h4>
                    {fu.recommended_by_ai && (
                      <span className="rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-semibold text-amber-800 border border-amber-200 flex items-center gap-1">
                        <Sparkles className="h-3 w-3 text-amber-600" /> Gemini Recommendation
                      </span>
                    )}
                    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600">
                      {fu.status}
                    </span>
                  </div>

                  <p className="text-xs text-slate-600">
                    {fu.notes || fu.message_draft || "Scheduled follow-up reminder"}
                  </p>

                  <div className="flex items-center gap-2 text-[11px] text-slate-400">
                    <Clock className="h-3 w-3" />
                    <span>Scheduled for: <strong>{new Date(fu.scheduled_time).toLocaleString()}</strong></span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 self-start sm:self-auto">
                  {fu.status !== "Sent" && fu.status !== "Cancelled" && (
                    <>
                      <button
                        onClick={() => handleMarkSent(fu.id)}
                        disabled={actionBusy}
                        className="inline-flex items-center gap-1 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-emerald-700 shadow-xs"
                      >
                        <Check className="h-3.5 w-3.5" /> Mark Sent
                      </button>
                      <button
                        onClick={() => handleCancel(fu.id)}
                        disabled={actionBusy}
                        className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-rose-600 hover:bg-rose-50"
                      >
                        Cancel
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-xs animate-in fade-in">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl border border-slate-100 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900 text-sm">Schedule Follow-Up</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-3.5">
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Target Lead *</label>
                <select
                  required
                  value={selectedLeadId}
                  onChange={(e) => setSelectedLeadId(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 p-2.5 text-xs font-semibold outline-none focus:border-indigo-500"
                >
                  <option value="">-- Select Lead --</option>
                  {leads.map((l) => (
                    <option key={l.id} value={l.id}>
                      {l.name} ({l.company || l.email || "No company"})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <label className="text-xs font-bold text-slate-700 block mb-1">Channel *</label>
                  <select
                    value={channel}
                    onChange={(e) => setChannel(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 p-2.5 text-xs font-semibold outline-none"
                  >
                    <option value="email">Email</option>
                    <option value="whatsapp">WhatsApp</option>
                    <option value="linkedin">LinkedIn</option>
                    <option value="x">X / Twitter</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-bold text-slate-700 block mb-1">Date & Time *</label>
                  <input
                    type="datetime-local"
                    required
                    value={scheduledTime}
                    onChange={(e) => setScheduledTime(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 p-2 text-xs outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Notes / Instructions</label>
                <input
                  type="text"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="e.g. Inquire about their Figma wireframes review"
                  className="w-full rounded-xl border border-slate-200 p-2.5 text-xs outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Message Draft (Optional)</label>
                <textarea
                  rows={3}
                  value={messageDraft}
                  onChange={(e) => setMessageDraft(e.target.value)}
                  placeholder="Draft copy to send on the scheduled date..."
                  className="w-full rounded-xl border border-slate-200 p-2.5 text-xs outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionBusy || !selectedLeadId || !scheduledTime}
                  className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-bold text-white hover:bg-indigo-700 shadow-sm"
                >
                  {actionBusy ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Clock className="h-3.5 w-3.5" />}
                  Confirm Follow-Up
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
